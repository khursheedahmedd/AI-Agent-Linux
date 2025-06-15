from typing import List, Dict
import os
from rich.console import Console
from openai import OpenAI

console = Console()

class LLM:
    """LLM class for handling language model interactions."""
    
    def __init__(self, model: str = "meta-llama/llama-3.1-8b-instruct", temperature: float = 0.7, max_tokens: int = 1000):
        """Initialize the LLM with the specified model and parameters."""
        # Get API key from environment
        api_key = os.getenv("NOVITA_API_KEY")
        if not api_key:
            raise ValueError("NOVITA_API_KEY environment variable not set")
        
        try:
            # Initialize Novita client
            self.client = OpenAI(
                base_url="https://api.novita.ai/v3/openai",
                api_key=api_key
            )
            self.model = model
            self.temperature = temperature
            self.max_tokens = max_tokens
            
            # Test the client
            test_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                temperature=0.1,
                max_tokens=10
            )
            
        except Exception as e:
            console.print(f"[bold red]Error initializing LLM client: {str(e)}[/bold red]")
            raise

    def invoke_chat(self, system_prompt: str, user_query: str, chat_history: List[Dict[str, str]] = None) -> str:
        """Invoke the LLM with a chat-style prompt."""
        try:
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add chat history if provided
            if chat_history:
                for msg in chat_history:
                    messages.append(msg)
            
            # Add the current user query
            messages.append({"role": "user", "content": user_query})
            
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
                    
                    # Validate the content
                    if not content or content.isspace():
                        return ""
                        
                    # Check for JSON-like content
                    if content.strip().startswith('{') or content.strip().startswith('['):
                        try:
                            import json
                            parsed = json.loads(content)
                            if isinstance(parsed, dict) and "content" in parsed:
                                content = parsed["content"]
                            elif isinstance(parsed, list) and len(parsed) > 0:
                                content = parsed[0]
                        except json.JSONDecodeError:
                            pass
                    
                    return content
                else:
                    return ""
                    
            except Exception as e:
                console.print(f"[bold red]Error getting response from LLM: {str(e)}[/bold red]")
                return ""
                
        except Exception as e:
            console.print(f"[bold red]Error in invoke_chat: {str(e)}[/bold red]")
            return "" 