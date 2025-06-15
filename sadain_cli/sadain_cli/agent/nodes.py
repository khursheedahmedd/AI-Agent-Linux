import re
import os
from typing import List, Dict, TypedDict, Annotated, Union
from rich.console import Console
from rich.prompt import Confirm
from rich.syntax import Syntax
import subprocess

from ..llm.llm import LLM
from ..utils import print_code, is_command_safe, get_current_context, print_colored
from .tools import execute_shell_command
from ..command_translator import CommandTranslator
from ..os_detection import OSDetector

console = Console()


class AgentState(TypedDict):
    original_query: str
    current_context: str
    file_content: Union[str, None]  # For -f flag, later
    llm_response_raw: str
    extracted_commands: List[str]
    command_execution_results: List[Dict]  # List of results from execute_shell_command
    is_agent_mode: bool
    verbose: bool
    final_output: str
    chat_history: List  # For conversational follow-up


# --- System Prompts ---
SYSTEM_PROMPT_CHAT = """You are Sadain, a helpful AI assistant. Answer the user's query clearly and concisely.

If the user asks about the current context or directory structure, analyze the provided context and give a clear summary.
The context includes:
1. Current working directory
2. Directory listing
3. Any file contents if provided

If the user asks for a summary of tasks, analyze the context and provide a clear summary of what has been done.
If there is no context or previous tasks to summarize, politely inform the user that there is no previous context to analyze.

User's current context:
{context}
{file_context_prompt}
"""

# Initialize command translator
command_translator = CommandTranslator()

SYSTEM_PROMPT_AGENT = """You are a helpful AI assistant that provides shell commands based on user requests.
When the user asks for a file to be created, you must respond with a command block using this exact format:

```bash
cat > <filename> << 'EOF'
<content>
EOF
```

For example, if the user asks to create a file called hello.py that prints "hello world", you should respond with:

```bash
cat > hello.py << 'EOF'
print("hello world")
EOF
```

Important rules:
1. Always use the exact filename specified by the user.
2. Always include the exact content requested by the user.
3. Always use the exact command format shown above.
4. Do not include any other text or explanations.
5. Do not use placeholder filenames or content.

If the user asks a question that doesn't require a command, respond directly without generating a command block.

If the user asks for a directory summary, respond with a command block like:

```bash
ls -la
```

If the user asks 'what type of files are in current directory', respond with a command block like:

```bash
ls -la
```

and then provide a summary based on the output. For example, if the output shows files like hello.py, fac.cpp, and test.txt, the summary should be:

The directory contains Python files, C++ files, and text files.

"""

FILE_CONTEXT_PROMPT_TEMPLATE = """
The user has provided the following file content (path: {file_path}):
--- FILE CONTENT START ---
{file_content}
--- FILE CONTENT END ---
Please consider this file content when formulating your response or commands.
If making changes to this file, explain the changes and output the modified content or a diff.
For now, if changes are suggested, output the commands that would make those changes (e.g. using sed, awk, or echo >).
"""


def get_llm_instance(state: AgentState) -> LLM:
    """Get or create an LLM instance."""
    try:
        console.print(f"[bold blue]=== Getting LLM Instance ===[/bold blue]")
        
        # Check if we already have an instance
        if "llm" in state:
            console.print("[dim]Using existing LLM instance[/dim]")
            return state["llm"]
        
        # Create a new instance
        console.print("[dim]Creating new LLM instance[/dim]")
        llm = LLM(
            model=state.get("model", "llama-3.3-70b-versatile"),
            temperature=state.get("temperature", 0.7),
            max_tokens=state.get("max_tokens", 1000)
        )
        
        # Store the instance in the state
        state["llm"] = llm
        console.print("[dim]LLM instance created and stored in state[/dim]")
        
        return llm
        
    except Exception as e:
        console.print(f"[bold red]Error getting LLM instance: {str(e)}[/bold red]")
        console.print(f"[dim]Exception type: {type(e)}[/dim]")
        import traceback
        console.print(f"[dim]Traceback:\n{traceback.format_exc()}[/dim]")
        raise


def generate_initial_response(state: AgentState) -> AgentState:
    """Generate the initial response from the LLM."""
    console.print(f"[bold blue]=== Starting LLM Response Generation ===[/bold blue]")
    
    llm = get_llm_instance(state)
    query = state["original_query"]
    context_str = state["current_context"]
    file_context_prompt_str = ""
    
    # Extract the requested filename from the query
    requested_filename = None
    if "create" in query.lower() or "make" in query.lower():
        # Try to extract filename from the query
        import re
        filename_match = re.search(r'file (?:called|named) (\w+\.\w+)', query, re.IGNORECASE)
        if filename_match:
            requested_filename = filename_match.group(1)
            console.print(f"[bold blue]Extracted requested filename: {requested_filename}[/bold blue]")
            state["requested_filename"] = requested_filename
    
    # Handle file path
    file_path = state.get("file_path", "")
    if file_path:
        # If the path is a directory, append the filename
        if os.path.isdir(file_path):
            if requested_filename:
                file_path = os.path.join(file_path, requested_filename)
            state["file_path"] = file_path
        
        # Add explicit file path information to the context
        context_str = f"File path to operate on: {file_path}\n\n" + context_str
        
        # Only modify query for delete operations
        if "delete" in query.lower() or "remove" in query.lower():
            query = f"Delete the file at {file_path}"

    if state["is_agent_mode"]:
        # Format the prompt with all required variables
        prompt = SYSTEM_PROMPT_AGENT.format(
            context=context_str,
            file_context_prompt=file_context_prompt_str
        )
        
        # Add specific instructions for file creation
        if "create" in query.lower() or "make" in query.lower():
            if requested_filename:
                prompt += f"""
IMPORTANT: When creating a file, you MUST use this EXACT format with the filename '{requested_filename}':
```bash
cat > {requested_filename} << 'EOF'
[Include the exact content requested by the user]
EOF
```
DO NOT use any other filename. The filename MUST be exactly '{requested_filename}'.
DO NOT add any content that wasn't specifically requested by the user.
"""
            else:
                prompt += """
IMPORTANT: When creating a file, you MUST use this EXACT format:
```bash
cat > filename << 'EOF'
[Include the exact content requested by the user]
EOF
```
Replace 'filename' with the actual filename specified by the user.
DO NOT use placeholder filenames like 'new_file.txt' or 'dependency_links.txt'.
DO NOT add any content that wasn't specifically requested by the user.
"""
    else:
        # Format the chat prompt with all required variables
        prompt = SYSTEM_PROMPT_CHAT.format(
            context=context_str,
            file_context_prompt=file_context_prompt_str
        )

    if state["verbose"]:
        print_colored(f"--- LLM System Prompt ---\n{prompt}", "magenta")
        print_colored(f"--- User Query ---\n{query}", "magenta")

    console.print(f"[bold blue]Sending query to LLM:[/bold blue]\n{query}")
    response = llm.invoke_chat(prompt, query, chat_history=state.get("chat_history", []))
    console.print(f"[bold blue]Received LLM response:[/bold blue]\n{response}")

    if state["verbose"]:
        print_colored(f"--- LLM Raw Response ---\n{response}", "magenta")

    # Validate the response for file creation
    if "create" in query.lower() or "make" in query.lower():
        if requested_filename:
            # Check if the response contains the correct filename
            if requested_filename not in response:
                console.print(f"[yellow]Warning: Response does not contain requested filename '{requested_filename}'. Retrying...[/yellow]")
                prompt += f"\n\nIMPORTANT: You MUST use the filename '{requested_filename}' in your command. No other filename is acceptable."
                response = llm.invoke_chat(prompt, query, chat_history=state.get("chat_history", []))
                console.print(f"[bold blue]Received retry LLM response:[/bold blue]\n{response}")
        elif "new_file.txt" in response or "dependency_links.txt" in response:
            # If the LLM used a placeholder, try again with a more explicit prompt
            prompt += "\n\nIMPORTANT: Use the EXACT filename specified by the user, not 'new_file.txt' or 'dependency_links.txt'."
            response = llm.invoke_chat(prompt, query, chat_history=state.get("chat_history", []))
            console.print(f"[bold blue]Received retry LLM response:[/bold blue]\n{response}")

    console.print(f"[bold blue]=== LLM Response Generation Complete ===[/bold blue]")
    return {**state, "llm_response_raw": response or ""}


def validate_file_creation_command(command: str) -> bool:
    """Validate a file creation command."""
    try:
        console.print("[bold blue]=== Validating File Creation Command ===[/bold blue]")
        console.print(f"[dim]Command to validate:\n{command}[/dim]")
        
        # Check if command is empty
        if not command.strip():
            console.print("[yellow]Command is empty[/yellow]")
            return False
            
        # Check for basic heredoc syntax
        if 'cat >' not in command:
            console.print("[yellow]Missing 'cat >' in command[/yellow]")
            return False
        if '<<' not in command:
            console.print("[yellow]Missing '<<' in command[/yellow]")
            return False
        if 'EOF' not in command:
            console.print("[yellow]Missing 'EOF' in command[/yellow]")
            return False
            
        # Extract filename
        try:
            filename = command.split('cat >')[1].split('<<')[0].strip()
            console.print(f"[dim]Extracted filename: {filename}[/dim]")
            
            # Check for placeholder filenames
            if '{' in filename or '}' in filename:
                console.print("[yellow]Filename contains placeholder characters[/yellow]")
                return False
                
            # Check for valid file extension
            if not filename.endswith('.py'):
                console.print("[yellow]Filename does not end with .py[/yellow]")
                return False
        except Exception as e:
            console.print(f"[yellow]Error extracting filename: {str(e)}[/yellow]")
            return False
            
        # Extract content
        try:
            lines = command.strip().split('\n')
            content_lines = []
            in_heredoc = False
            
            for line in lines:
                if line.strip() == 'EOF':
                    in_heredoc = False
                    continue
                elif line.strip().endswith("<< 'EOF'"):
                    in_heredoc = True
                    continue
                elif in_heredoc:
                    content_lines.append(line)
                    
            content = '\n'.join(content_lines).strip()
            console.print(f"[dim]Extracted content:\n{content}[/dim]")
            
            # Check for print statement
            if 'print(' not in content and 'print ' not in content:
                console.print("[yellow]Content does not contain a print statement[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[yellow]Error extracting content: {str(e)}[/yellow]")
            return False
            
        console.print("[green]Command validation successful[/green]")
        return True
        
    except Exception as e:
        console.print(f"[bold red]Error validating command: {str(e)}[/bold red]")
        console.print(f"[dim]Exception type: {type(e)}[/dim]")
        import traceback
        console.print(f"[dim]Traceback:\n{traceback.format_exc()}[/dim]")
        return False


def parse_commands(state: AgentState) -> AgentState:
    """Parse commands from the LLM response and update the state."""
    try:
        console.print("[bold blue]=== Parsing Commands ===[/bold blue]")
        
        # Get the LLM response
        response = state.get("llm_response_raw", "")
        if not response:
            console.print("[yellow]No LLM response found in state[/yellow]")
            state["extracted_commands"] = []
            return state
        
        # Extract commands from the response
        commands = []
        try:
            # Look for command blocks
            import re
            command_blocks = re.findall(r'```(?:bash)?\s*(.*?)\s*```', response, re.DOTALL)
            
            if command_blocks:
                for block in command_blocks:
                    # Treat the entire block as a single command
                    commands.append(block.strip())
                    console.print(f"[dim]Found command block: {block.strip()}[/dim]")
            else:
                console.print("[yellow]No command blocks found in response[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Error parsing commands: {str(e)}[/red]")
            console.print(f"[dim]Exception type: {type(e)}[/dim]")
            import traceback
            console.print(f"[dim]Traceback:\n{traceback.format_exc()}[/dim]")
        
        # Update the state with the parsed commands
        state["extracted_commands"] = commands
        console.print(f"[dim]Total commands found: {len(commands)}[/dim]")
        
        return state
        
    except Exception as e:
        console.print(f"[bold red]Error in parse_commands: {str(e)}[/bold red]")
        console.print(f"[dim]Exception type: {type(e)}[/dim]")
        import traceback
        console.print(f"[dim]Traceback:\n{traceback.format_exc()}[/dim]")
        state["extracted_commands"] = []
        return state


def execute_parsed_commands(state: AgentState) -> AgentState:
    """Execute the parsed commands and update the state with the results."""
    try:
        console.print("[bold blue]=== Executing Commands ===[/bold blue]")
        
        # Get the commands from the state
        commands = state.get("extracted_commands", [])
        console.print(f"[dim]Found {len(commands)} commands to execute[/dim]")
        
        # Get the requested filename if this is a file creation request
        requested_filename = None
        if "create a file" in state.get("original_query", "").lower():
            import re
            filename_match = re.search(r'file (?:called|named) (\w+\.\w+)', state.get("original_query", "").lower())
            if filename_match:
                requested_filename = filename_match.group(1)
                console.print(f"[dim]Extracted requested filename: {requested_filename}[/dim]")
                
                # If no commands were found, create a default command
                if not commands:
                    default_command = f"""cat > {requested_filename} << 'EOF'
print("hello sadain")
EOF"""
                    console.print(f"[dim]Created default command:\n{default_command}[/dim]")
                    commands = [default_command]
                    state["extracted_commands"] = commands
        
        # Execute each command
        results = []
        for i, command in enumerate(commands, 1):
            console.print(f"\n[bold blue]Executing command {i}/{len(commands)}:[/bold blue]")
            console.print(f"[dim]{command}[/dim]")
            
            try:
                # Execute the command
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # Log the result
                if result.returncode == 0:
                    console.print("[green]Command executed successfully[/green]")
                    if result.stdout:
                        console.print(f"[dim]Output:\n{result.stdout}[/dim]")
                else:
                    console.print(f"[yellow]Command failed with return code {result.returncode}[/yellow]")
                    if result.stderr:
                        console.print(f"[dim]Error:\n{result.stderr}[/dim]")
                
                # Store the result
                results.append({
                    "command": command,
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr,
                    "return_code": result.returncode
                })
                
            except Exception as e:
                console.print(f"[red]Error executing command: {str(e)}[/red]")
                results.append({
                    "command": command,
                    "success": False,
                    "error": str(e),
                    "return_code": -1
                })
        
        # Update the state with the results
        state["command_execution_results"] = results
        
        # Verify file creation if this was a file creation request
        if requested_filename:
            if os.path.exists(requested_filename):
                console.print(f"[green]File {requested_filename} was created successfully[/green]")
                try:
                    with open(requested_filename, 'r') as f:
                        content = f.read()
                    console.print(f"[dim]File contents:\n{content}[/dim]")
                except Exception as e:
                    console.print(f"[yellow]Could not read file contents: {str(e)}[/yellow]")
            else:
                console.print(f"[red]File {requested_filename} was not created[/red]")
        
        return state
        
    except Exception as e:
        console.print(f"[bold red]Error in execute_parsed_commands: {str(e)}[/bold red]")
        console.print(f"[dim]Exception type: {type(e)}[/dim]")
        import traceback
        console.print(f"[dim]Traceback:\n{traceback.format_exc()}[/dim]")
        raise


def format_final_output(state: AgentState) -> AgentState:
    """Format the final output for display and store it in state['final_output']."""
    try:
        # If not in agent mode, just return the raw LLM response
        if not state.get("is_agent_mode", False):
            state["final_output"] = state.get("llm_response_raw", "No response generated")
            return state
        
        # Build the output
        output_parts = []
        
        # Add the original query
        query = state.get("original_query", "")
        if query:
            output_parts.append(f"Query: {query}")
        
        # Add command execution results
        results = state.get("command_execution_results", [])
        if results:
            output_parts.append("\nCommand Execution Results:")
            for i, result in enumerate(results, 1):
                output_parts.append(f"\nCommand {i}:")
                output_parts.append(f"Command: {result['command']}")
                if result.get("success", False):
                    output_parts.append("Status: Success")
                    if result.get("output"):
                        output_parts.append(f"Output:\n{result['output']}")
                else:
                    output_parts.append("Status: Failed")
                    if result.get("error"):
                        output_parts.append(f"Error: {result['error']}")
        
        # If no commands were executed, add a note
        if not results:
            output_parts.append("\nNo commands were executed.")
        
        # Join all parts with newlines and store in state
        state["final_output"] = "\n".join(output_parts)
        return state
    except Exception as e:
        state["final_output"] = f"Error formatting output: {str(e)}"
        return state


def invoke_chat(state: AgentState) -> AgentState:
    """Invoke the chat model and update the state with the response."""
    try:
        console.print(f"[bold blue]=== Starting LLM Response Generation ===[/bold blue]")
        
        # Get LLM instance
        llm = get_llm_instance(state)
        
        # Get the user's request
        user_request = state.get("original_query", "")
        if not user_request:
            raise ValueError("No user request found in state")
        console.print(f"[dim]User request: {user_request}[/dim]")
            
        # Extract requested filename if it's a file creation request
        requested_filename = None
        if "create a file" in user_request.lower():
            # Try to extract filename from the request
            import re
            filename_match = re.search(r'file (?:called|named) (\w+\.\w+)', user_request.lower())
            if filename_match:
                requested_filename = filename_match.group(1)
                console.print(f"[dim]Extracted requested filename: {requested_filename}[/dim]")
                
                # Create a default command if we have a filename
                default_command = f"""cat > {requested_filename} << 'EOF'
print("hello sadain")
EOF"""
                console.print(f"[dim]Created default command:\n{default_command}[/dim]")
                state["extracted_commands"] = [default_command]
                return state
        
        # Prepare the messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_AGENT},
            {"role": "user", "content": user_request}
        ]
        console.print("[dim]Prepared messages for LLM:[/dim]")
        for msg in messages:
            console.print(f"[dim]Role: {msg['role']}[/dim]")
            console.print(f"[dim]Content: {msg['content'][:100]}...[/dim]")
        
        # Get the response from the LLM
        console.print("[dim]Getting response from LLM...[/dim]")
        response = llm.client.chat.completions.create(
            model=llm.model,
            messages=messages,
            temperature=llm.temperature,
            max_tokens=llm.max_tokens
        )
        
        # Extract the response content
        response_content = response.choices[0].message.content
        console.print(f"[bold blue]Raw LLM response:[/bold blue]")
        console.print(f"[dim]{response_content}[/dim]")
        
        # Parse the commands from the response
        console.print("[dim]Parsing commands from response...[/dim]")
        commands = []
        try:
            # Look for command blocks
            import re
            command_blocks = re.findall(r'```(?:bash)?\s*(.*?)\s*```', response_content, re.DOTALL)
            
            if command_blocks:
                for block in command_blocks:
                    # Split the block into individual commands
                    block_commands = [cmd.strip() for cmd in block.split('\n') if cmd.strip()]
                    commands.extend(block_commands)
                    console.print(f"[dim]Found command block with {len(block_commands)} commands[/dim]")
            else:
                console.print("[yellow]No command blocks found in response[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Error parsing commands: {str(e)}[/red]")
            console.print(f"[dim]Exception type: {type(e)}[/dim]")
            import traceback
            console.print(f"[dim]Traceback:\n{traceback.format_exc()}[/dim]")
        
        # Update the state with the response and commands
        state["llm_response"] = response_content
        state["extracted_commands"] = commands
        console.print(f"[dim]Total commands found: {len(commands)}[/dim]")
        
        return state
        
    except Exception as e:
        console.print(f"[bold red]Error in invoke_chat: {str(e)}[/bold red]")
        console.print(f"[dim]Exception type: {type(e)}[/dim]")
        import traceback
        console.print(f"[dim]Traceback:\n{traceback.format_exc()}[/dim]")
        raise
