import typer
from typing_extensions import Annotated
from rich.console import Console
from rich.panel import Panel
import os
import sys
from typing import Optional, Tuple
from rich.prompt import Confirm, Prompt
import tempfile
import subprocess
import warnings
from dotenv import load_dotenv

from .agent.graph import create_agent_graph, AgentState
from .utils import get_current_context, print_colored
from .config import load_api_key # To ensure API key is checked early
from .agent.nodes import (
    generate_initial_response,
    parse_commands,
    execute_parsed_commands,
    format_final_output,
)
from .voice_handler import handle_voice_mode, VoiceHandler
from .command_history import CommandHistory

# Suppress urllib3 warnings
warnings.filterwarnings('ignore', category=Warning, module='urllib3')

app = typer.Typer(
    name="sadain",
    help="A terminal-based AI assistant powered by LangGraph and LLMs.",
    add_completion=False
)
console = Console()

# Load environment variables
load_dotenv()

# Ensure API key is loaded/checked at module import
# This is a bit eager, could be moved to on_command_run
try:
    _ = load_api_key() 
except Exception as e:
    console.print(f"[bold red]Initialization Error: Could not load API key. {e}[/bold red]")
    # Optionally exit or disable features

def parse_file_path(ctx: typer.Context, param: typer.CallbackParam, value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    
    # If the value is quoted, return it as is
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    
    # Try to find the file path in the remaining arguments
    args = ctx.args
    if not args:
        return value
    
    # Look for the file path in the remaining arguments
    potential_path = []
    for arg in args:
        if arg.startswith('-'):
            break
        potential_path.append(arg)
    
    if potential_path:
        reconstructed_path = ' '.join(potential_path)
        if os.path.exists(reconstructed_path):
            # Remove the file path parts from the remaining arguments
            for part in potential_path:
                if part in args:
                    args.remove(part)
            return reconstructed_path
    
    return value

@app.command()
def main(
    content: str = typer.Argument(None, help="Content to process"),
    agent_mode: bool = typer.Option(False, "-a", "--agent", help="Run in agent mode"),
    use_context: bool = typer.Option(True, "-c", "--context", help="Use context from current directory"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose output"),
    voice_mode: bool = typer.Option(False, "--voice", help="Enable voice mode"),
    undo: bool = typer.Option(False, "--undo", help="Undo the last executed command"),
    history: bool = typer.Option(False, "--history", help="Show command history")
) -> None:
    """Main entry point for the Sadain CLI."""
    try:
        # Initialize command history
        command_history = CommandHistory()
        
        # Handle history command
        if history:
            history_entries = command_history.get_history()
            if history_entries:
                console.print("[bold blue]Command History:[/bold blue]")
                for i, entry in enumerate(history_entries, 1):
                    console.print(f"\n[bold cyan]Entry {i}:[/bold cyan]")
                    console.print(f"[dim]Command:[/dim] {entry['command']}")
                    console.print(f"[dim]Timestamp:[/dim] {entry['timestamp']}")
                    if 'result' in entry:
                        console.print(f"[dim]Result:[/dim] {entry['result']}")
            else:
                console.print("[yellow]No command history available[/yellow]")
            return
        
        # Handle undo command
        if undo:
            last_command = command_history.undo_last_command()
            if last_command:
                console.print("[bold blue]Undoing last command...[/bold blue]")
                console.print(f"[dim]Command: {last_command['command']}[/dim]")
                
                # Handle file creation undo
                if 'cat >' in last_command['command'] and '<<' in last_command['command']:
                    try:
                        # Extract file path from the command
                        command_lines = last_command['command'].strip().split('\n')
                        file_path = command_lines[0].split('cat >')[1].split('<<')[0].strip()
                        
                        # Remove quotes if present
                        file_path = file_path.strip('"\'')
                        
                        # Get absolute path if relative
                        if not os.path.isabs(file_path):
                            file_path = os.path.join(os.getcwd(), file_path)
                        
                        console.print(f"[dim]Attempting to remove file: {file_path}[/dim]")
                        
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            console.print(f"[green]Successfully removed file: {file_path}[/green]")
                        else:
                            console.print(f"[yellow]File not found: {file_path}[/yellow]")
                    except Exception as e:
                        console.print(f"[red]Error undoing file creation: {str(e)}[/red]")
                else:
                    # For other commands, we can't automatically undo
                    console.print("[yellow]Note: Automatic undo is only supported for file creation commands[/yellow]")
            else:
                console.print("[yellow]No commands to undo[/yellow]")
            return
        
        # Initialize voice handler if needed
        voice_handler = None
        if voice_mode:
            voice_handler = VoiceHandler()
            while True:
                # Get voice command
                command = handle_voice_mode()
                if not command:
                    return
                
                # Process the command
                content = command
                break
        
        # Get current directory context if requested
        current_context = ""
        if use_context:
            current_dir = os.getcwd()
            console.print(f"[dim]Current directory: {current_dir}[/dim]")
            
            # Get directory contents
            try:
                dirs = []
                files = []
                for item in os.listdir(current_dir):
                    full_path = os.path.join(current_dir, item)
                    if os.path.isdir(full_path):
                        dirs.append(item)
                    else:
                        files.append(item)
                
                # Format directory contents
                current_context = f"Current Directory (PWD):\n{current_dir}\nDirectory Contents:\n"
                if dirs:
                    current_context += "\nDirectories:\n" + "\n".join(f"- {d}" for d in sorted(dirs))
                if files:
                    current_context += "\nFiles:\n" + "\n".join(f"- {f}" for f in sorted(files))
                
                console.print("[dim]Context loaded successfully[/dim]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load directory context: {str(e)}[/yellow]")
        
        # Initialize state
        initial_state = {
            "original_query": content,
            "current_context": current_context,
            "file_content": "",
            "file_path": "",
            "llm_response_raw": "",
            "extracted_commands": [],
            "command_execution_results": [],
            "is_agent_mode": agent_mode,
            "verbose": verbose,
            "final_output": "",
            "commands": []
        }
        
        # Create and run the graph
        try:
            graph = create_agent_graph()
            final_state = graph.invoke(initial_state)
            
            # Store command in history if commands were executed
            if final_state.get("command_execution_results"):
                for result in final_state["command_execution_results"]:
                    command_history.add_command(result["command"], result)
            
            # Format and display the final output
            if agent_mode:
                # Extract file creation information
                for result in final_state.get("command_execution_results", []):
                    if 'cat >' in result["command"] and '<<' in result["command"]:
                        try:
                            command_lines = result["command"].strip().split('\n')
                            file_path = command_lines[0].split('cat >')[1].split('<<')[0].strip()
                            file_path = file_path.strip('"\'')
                            if not os.path.isabs(file_path):
                                file_path = os.path.join(os.getcwd(), file_path)
                            console.print(f"[green]File created successfully: {file_path}[/green]")
                            if voice_mode:
                                voice_handler.speak_response(f"File created successfully at {file_path}")
                        except Exception as e:
                            console.print(f"[yellow]Command executed, but could not extract file path: {str(e)}[/yellow]")
                    else:
                        console.print(f"[green]Command executed successfully[/green]")
                        if voice_mode:
                            voice_handler.speak_response("Command executed successfully")
            else:
                response = final_state.get("llm_response_raw", "No response generated")
                console.print("\n[bold green]Response:[/bold green]")
                console.print(response)
                if voice_mode:
                    voice_handler.speak_response(response)
                
        except Exception as e:
            error_msg = f"Error during execution: {str(e)}"
            console.print(f"[bold red]{error_msg}[/bold red]")
            if voice_mode:
                voice_handler.speak_response(error_msg)
            raise typer.Exit(1)
            
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        console.print(f"[bold red]{error_msg}[/bold red]")
        if voice_mode:
            voice_handler.speak_response(error_msg)
        raise typer.Exit(1)

def execute_command(command: str, shell: str) -> Tuple[int, str, str]:
    """Execute a command in the specified shell."""
    try:
        # Create a temporary file for the command
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
            temp_file.write(f"#!/bin/{shell}\n{command}")
            temp_file_path = temp_file.name
        
        # Make the temporary file executable
        os.chmod(temp_file_path, 0o755)
        
        # Execute the temporary file
        process = subprocess.Popen(
            [f"/bin/{shell}", temp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        return process.returncode, stdout, stderr
    except Exception as e:
        return 1, "", str(e)

def create_file_with_content(file_path: str, content: str) -> bool:
    """Create a file with the specified content."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Split the content into lines and remove any EOF markers
        lines = content.strip().split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip() != 'EOF':
                cleaned_lines.append(line)
        
        # Join the lines back together
        cleaned_content = '\n'.join(cleaned_lines).strip()
        
        # Write the content to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        return True
    except Exception as e:
        print(f"Error creating file: {str(e)}")
        return False

def execute_parsed_commands(state: AgentState) -> AgentState:
    """Execute the parsed commands and update the state."""
    if not state["extracted_commands"]:
        return state
    
    results = []
    for command in state["extracted_commands"]:
        if state["verbose"]:
            print_colored(f"Executing command: {command}", "blue")
        
        try:
            # Process the command using our new function
            process_command(command, "zsh" if sys.platform == "darwin" else "bash")
            
            # Add the result to our state
            results.append({
                "command": command,
                "status": "executed"
            })
        except Exception as e:
            results.append({
                "command": command,
                "status": "failed",
                "error": str(e)
            })
    
    state["command_execution_results"] = results
    return state

def process_command(command: str, shell: str) -> None:
    """Process a command and execute it."""
    # Check if it's a file creation command
    if "cat >" in command and "<< 'EOF'" in command:
        try:
            # Extract the file path and content
            parts = command.split("<< 'EOF'")
            if len(parts) != 2:
                print("Invalid command format")
                return
            
            # Get the current working directory
            cwd = os.getcwd()
            
            # Extract and clean the file path
            file_path = parts[0].replace("cat >", "").strip()
            # If the path is relative, make it absolute using the current working directory
            if not os.path.isabs(file_path):
                file_path = os.path.join(cwd, file_path)
            
            content = parts[1].strip()
            
            # Create the file with content
            if create_file_with_content(file_path, content):
                print(f"Successfully created file: {file_path}")
            else:
                print("Failed to create file")
        except Exception as e:
            print(f"Error processing command: {str(e)}")
        return
    
    # For other commands, execute them directly
    try:
        returncode, stdout, stderr = execute_command(command, shell)
        
        if returncode == 0:
            print("Command executed successfully")
            if stdout:
                print(f"Output: {stdout}")
        else:
            print(f"Command failed with exit code: {returncode}")
            if stderr:
                print(f"Error: {stderr}")
    except Exception as e:
        print(f"Error executing command: {str(e)}")

if __name__ == "__main__":
    app()