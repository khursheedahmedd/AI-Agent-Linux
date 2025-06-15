import os
import subprocess
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text

console = Console()

# Basic safety check keywords (very simplistic, needs improvement)
DANGEROUS_COMMAND_PATTERNS = [
    "rm -rf", "sudo", "mkfs", "> /dev/sd", "dd if=", ":(){:|:&};:",
    "mv /", "chmod 000", "chown root"
]
# Commands generally considered read-only (simplistic)
READ_ONLY_COMMANDS_START = ["ls", "cat", "grep", "find", "pwd", "git status", "git diff", "man", "echo"]

def get_current_context(max_history: int = 10, max_dir_depth: int = 1) -> str:
    """Gathers context from the current terminal environment."""
    context_parts = []
    
    # PWD
    pwd = os.getcwd()
    context_parts.append(f"Current Directory (PWD):\n{pwd}\n")

    # Directory Structure (simple ls for now, tree is better but might not be installed)
    try:
        # Using ls instead of tree for wider compatibility by default
        # For more detail, 'tree -L {max_dir_depth} -a' would be good if 'tree' is available.
        # Here, we list current directory contents.
        dir_listing = subprocess.check_output(["ls", "-ap"], cwd=pwd, text=True, stderr=subprocess.STDOUT)
        context_parts.append(f"Directory Listing (ls -ap):\n{dir_listing}\n")
    except Exception as e:
        context_parts.append(f"Could not get directory listing: {e}\n")

    # Command History (very basic, needs shell-specific integration for real history)
    # This is a placeholder; real history needs shell hooks or reading history files.
    # context_parts.append("Command History (Recent N):\n# (Placeholder for actual history integration)\n")
    
    return "".join(context_parts)

def print_colored(text, color):
    try:
        # Only use markup if color is a valid Rich tag
        console.print(f"[{color}]{text}[/{color}]")
    except Exception:
        # Fallback: print without markup if color is invalid
        console.print(text)

def print_code(code: str, language: str = "bash"):
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)

def is_command_safe(command: str) -> bool:
    """
    Very basic safety check for a command.
    Returns True if likely read-only, False if potentially destructive or needs confirmation.
    """
    command_lower = command.lower().strip()
    if not command_lower:
        return True # Empty command is safe

    for pattern in DANGEROUS_COMMAND_PATTERNS:
        if pattern in command_lower:
            return False
            
    # Check if it starts with a known read-only command and doesn't have obvious write operations
    is_read_only_start = any(command_lower.startswith(ro_cmd) for ro_cmd in READ_ONLY_COMMANDS_START)
    
    # Simplistic check for redirection that writes, or pipes to dangerous commands
    if is_read_only_start:
        if ">" in command and ">>" not in command_lower and not command_lower.split(">",1)[1].strip().startswith("/dev/null"): # Simple output redirection
            return False # Writing to a new file might be ok, but let's be cautious
        if "|" in command: # If piping, check the subsequent commands
            parts = command_lower.split("|")
            for part in parts[1:]:
                if not any(part.strip().startswith(ro_cmd) for ro_cmd in READ_ONLY_COMMANDS_START):
                    # If any part of the pipe isn't clearly read-only, ask.
                    # This is very naive, e.g. `ls | dangerous_script`
                    if not is_command_safe_recursive_pipe(part.strip()):
                        return False
        return True # If it starts read-only and no obvious write ops found

    return False 

def is_command_safe_recursive_pipe(command_part: str) -> bool:
    """Helper for checking piped commands recursively."""
    if any(command_part.startswith(ro_cmd) for ro_cmd in READ_ONLY_COMMANDS_START):
        # Further checks for this part could be added here if needed
        return True
    return False

# if __name__ == '__main__':
#     print_colored("This is a test of colored output.", "green")
#     print_code("echo 'Hello World'\nls -l", "bash")
#     print("\n--- Context ---")
#     print(get_current_context())
#     print("\n--- Safety Check ---")
#     print(f"ls -l: {is_command_safe('ls -l')}")
#     print(f"cat file.txt: {is_command_safe('cat file.txt')}")
#     print(f"rm -rf /: {is_command_safe('rm -rf /')}")
#     print(f"sudo apt update: {is_command_safe('sudo apt update')}")
#     print(f"echo 'hi' > file.txt: {is_command_safe('echo \"hi\" > file.txt')}")  # Should be False
#     print(f"git status: {is_command_safe('git status')}")
#     print(f"find . -name '*.py' | grep 'class': {is_command_safe('find . -name \"*.py\" | grep \"class\"')}")  # Should be True
#     print(f"find . -name '*.py' | xargs rm: {is_command_safe('find . -name \"*.py\" | xargs rm')}")  # Should be False
