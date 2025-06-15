import os
import platform
from pathlib import Path
from typing import Optional

def get_os_type() -> str:
    """Determine the operating system type."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"

def load_os_prompt() -> Optional[str]:
    """Load the appropriate system prompt based on the OS."""
    try:
        # Get the OS type
        os_type = get_os_type()
        
        # Get the path to the prompts directory
        current_dir = Path(__file__).parent
        prompts_dir = current_dir / "prompts"
        
        # Construct the path to the OS-specific prompt file
        prompt_file = prompts_dir / f"{os_type}.md"
        
        # Check if the file exists
        if not prompt_file.exists():
            print(f"Warning: No prompt file found for {os_type}")
            return None
            
        # Read and return the prompt content
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
            
    except Exception as e:
        print(f"Error loading OS prompt: {str(e)}")
        return None

def get_system_prompt() -> str:
    """Get the system prompt, falling back to a default if OS-specific one isn't available."""
    # Try to load OS-specific prompt
    prompt = load_os_prompt()
    
    # If no OS-specific prompt is available, use a generic one
    if not prompt:
        prompt = """You are an expert terminal assistant. Your goal is to understand the user's request
and provide ONE or MORE shell commands to achieve it.

If the user asks a question that doesn't require a command, answer it directly.

IMPORTANT FORMATTING:
If you provide shell commands, enclose EACH command in its own triple backticks block, like this:
```bash
echo "This is one command"
ls -la
```

If you need to explain something or ask for clarification, do so outside of the backtick blocks.
Do not add any conversational fluff before or after the command blocks if commands are the primary output.
Just provide the commands."""
    
    return prompt 