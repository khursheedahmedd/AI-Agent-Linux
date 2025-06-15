from typing import List, Dict
import os
from rich.console import Console
import groq

console = Console()

class LLM:
    """LLM class for handling language model interactions."""
    
    def __init__(self, model: str = "llama-3.3-70b-versatile", temperature: float = 0.7, max_tokens: int = 1000):
        """Initialize the LLM with the specified model and parameters."""
        console.print(f"[bold blue]=== Initializing LLM Client ===[/bold blue]")
        console.print(f"[dim]Model: {model}[/dim]")
        console.print(f"[dim]Temperature: {temperature}[/dim]")
        console.print(f"[dim]Max tokens: {max_tokens}[/dim]")
        
        # Get API key from environment
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        console.print("[dim]API key found[/dim]")
        
        try:
            # Initialize Groq client
            self.client = groq.Client(api_key=api_key)
            self.model = model
            self.temperature = temperature
            self.max_tokens = max_tokens
            
            # Test the client
            console.print("[dim]Testing LLM client...[/dim]")
            test_response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Use the correct model name
                messages=[{"role": "user", "content": "Hello"}],
                temperature=0.1,
                max_tokens=10
            )
            console.print("[green]LLM client initialized successfully[/green]")
            
        except Exception as e:
            console.print(f"[bold red]Error initializing LLM client: {str(e)}[/bold red]")
            console.print(f"[dim]Exception type: {type(e)}[/dim]")
            import traceback
            console.print(f"[dim]Traceback:\n{traceback.format_exc()}[/dim]")
            raise

    def invoke_chat(self, system_prompt: str, user_query: str, chat_history: List[Dict[str, str]] = None) -> str:
        """Invoke the LLM with a chat-style prompt."""
        try:
            console.print(f"[bold blue]=== Starting LLM Invocation ===[/bold blue]")
            console.print(f"[dim]System prompt:\n{system_prompt}[/dim]")
            console.print(f"[dim]User query:\n{user_query}[/dim]")
            
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add chat history if provided
            if chat_history:
                console.print(f"[dim]Adding {len(chat_history)} messages from chat history[/dim]")
                for msg in chat_history:
                    messages.append(msg)
            
            # Add the current user query
            messages.append({"role": "user", "content": user_query})
            
            console.print("[dim]Sending request to LLM...[/dim]")
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                # Extract the response content
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    console.print(f"[bold blue]Raw LLM response content:[/bold blue]\n{content}")
                    
                    # Validate the content
                    if not content or content.isspace():
                        console.print("[yellow]Warning: Empty response from LLM[/yellow]")
                        return ""
                        
                    # Check for JSON-like content
                    if content.strip().startswith('{') or content.strip().startswith('['):
                        console.print("[yellow]Warning: Response appears to be JSON, attempting to extract content[/yellow]")
                        try:
                            import json
                            parsed = json.loads(content)
                            if isinstance(parsed, dict) and "content" in parsed:
                                content = parsed["content"]
                            elif isinstance(parsed, list) and len(parsed) > 0:
                                content = parsed[0]
                        except json.JSONDecodeError:
                            console.print("[yellow]Warning: Failed to parse JSON response[/yellow]")
                    
                    return content
                else:
                    console.print("[red]No response content received from LLM[/red]")
                    return ""
                    
            except Exception as api_error:
                console.print(f"[bold red]Error in LLM API call: {str(api_error)}[/bold red]")
                console.print(f"[dim]Exception type: {type(api_error)}[/dim]")
                import traceback
                console.print(f"[dim]Traceback:\n{traceback.format_exc()}[/dim]")
                raise
                
        except Exception as e:
            console.print(f"[bold red]Error in LLM invocation: {str(e)}[/bold red]")
            console.print(f"[dim]Exception type: {type(e)}[/dim]")
            import traceback
            console.print(f"[dim]Traceback:\n{traceback.format_exc()}[/dim]")
            raise 