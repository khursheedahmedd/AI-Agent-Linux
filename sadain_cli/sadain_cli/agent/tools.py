import subprocess
import os
from rich.console import Console
from ..os_detection import OSDetector
from ..command_translator import CommandTranslator
from typing import Dict, Any

console = Console()
command_translator = CommandTranslator()

def get_powershell_path():
    """Get the full path to PowerShell executable."""
    # Common PowerShell paths
    possible_paths = [
        r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
        r"C:\Windows\System32\powershell.exe",
        r"C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
            
    return "powershell.exe"  # Fallback to PATH

def execute_shell_command(command: str) -> Dict[str, Any]:
    """Execute a shell command and return the result."""
    try:
        console.print(f"[bold blue]=== Executing Shell Command ===[/bold blue]")
        console.print(f"[dim]Command: {command}[/dim]")
        
        # Check if this is a file creation command
        if 'cat >' in command and '<<' in command and 'EOF' in command:
            console.print("[dim]Detected file creation command[/dim]")
            
            # Split the command into lines
            lines = command.strip().split('\n')
            if len(lines) < 3:
                raise ValueError("Invalid file creation command format")
            
            # Get the file path from the first line
            file_path = lines[0].split('cat >')[1].split('<<')[0].strip()
            console.print(f"[dim]File path: {file_path}[/dim]")
            
            # Extract content between heredoc markers
            content_lines = []
            in_heredoc = False
            for line in lines[1:]:
                if line.strip() == 'EOF':
                    in_heredoc = False
                    continue
                elif line.strip().endswith("<< 'EOF'"):
                    in_heredoc = True
                    continue
                elif in_heredoc:
                    content_lines.append(line)
            
            content = '\n'.join(content_lines).strip()
            console.print(f"[dim]Content to write:\n{content}[/dim]")
            
            # Create the file
            try:
                with open(file_path, 'w') as f:
                    f.write(content)
                console.print(f"[green]File {file_path} created successfully[/green]")
                return {
                    "status": "success",
                    "file_path": file_path,
                    "content": content
                }
            except Exception as e:
                console.print(f"[bold red]Error creating file: {str(e)}[/bold red]")
                raise
        
        # For other commands, use subprocess
        console.print("[dim]Executing command with subprocess[/dim]")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except Exception as e:
        console.print(f"[bold red]Error executing command: {str(e)}[/bold red]")
        console.print(f"[dim]Exception type: {type(e)}[/dim]")
        import traceback
        console.print(f"[dim]Traceback:\n{traceback.format_exc()}[/dim]")
        raise

if __name__ == "__main__":
    # Test commands for different OSes
    os_type, shell_type = OSDetector.get_os_info()
    console.print(f"Running on {os_type} with {shell_type} shell")
    
    # Test basic commands
    test_commands = [
        "ls -la",
        "echo 'Hello Sadain'",
        "pwd"
    ]
    
    for cmd in test_commands:
        res = execute_shell_command(cmd)
        console.print(f"\nCommand: {cmd}")
        console.print(f"Translated: {res['executed_command']}")
        console.print(f"STDOUT:\n{res['stdout']}")
        console.print(f"STDERR:\n{res['stderr']}")
        console.print(f"RETURNCODE: {res['returncode']}")