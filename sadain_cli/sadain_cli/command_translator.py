from typing import Dict, List
from .os_detection import OSDetector
import os

class CommandTranslator:
    def __init__(self):
        self.os_type, self.shell_type = OSDetector.get_os_info()
        
        # Command mappings for different OSes
        self.command_mappings: Dict[str, Dict[str, str]] = {
            'windows': {
                'powershell': {
                    'ls': 'Get-ChildItem',
                    'cat': 'Get-Content',
                    'grep': 'Select-String',
                    'find': 'Get-ChildItem -Recurse',
                    'rm': 'Remove-Item',
                    'cp': 'Copy-Item',
                    'mv': 'Move-Item',
                    'pwd': 'Get-Location',
                    'echo': 'Write-Output'
                },
                'cmd': {
                    'ls': 'dir',
                    'cat': 'type',
                    'grep': 'findstr',
                    'find': 'dir /s /b',
                    'rm': 'del',
                    'cp': 'copy',
                    'mv': 'move',
                    'pwd': 'cd',
                    'echo': 'echo'
                }
            },
            'macos': {
                'bash': {},  # Most commands are the same as Linux
                'zsh': {}    # Most commands are the same as Linux
            },
            'linux': {
                'bash': {},  # Original commands
                'zsh': {}    # Original commands
            }
        }

    def translate_command(self, command: str) -> str:
        """Translate a command based on the current OS."""
        os_type, shell_type = OSDetector.get_os_info()
        
        # Handle file creation commands
        if 'cat >' in command and '<<' in command and 'EOF' in command:
            # Extract the file path and content
            lines = command.strip().split('\n')
            if len(lines) >= 3:
                file_path = lines[0].split('cat >')[1].split('<<')[0].strip()
                content_lines = []
                in_content = False
                
                for line in lines[1:]:
                    if line.strip().endswith("<< 'EOF'"):
                        in_content = True
                        continue
                    elif line.strip() == "EOF":
                        in_content = False
                        continue
                    elif in_content:
                        content_lines.append(line)
                
                content = '\n'.join(content_lines).strip()
                
                # Create the command with proper escaping
                if os_type == 'windows':
                    # For Windows, use PowerShell
                    return f'Set-Content -Path "{file_path}" -Value @"{content}"@'
                else:
                    # For Unix-like systems, use heredoc
                    return f"cat > '{file_path}' << 'EOF'\n{content}\nEOF"
        
        # Handle other commands based on OS
        if os_type == 'windows':
            # Translate Unix commands to PowerShell
            if command.startswith('rm '):
                return f'Remove-Item -Path "{command[3:]}" -Force'
            elif command.startswith('mkdir '):
                return f'New-Item -Path "{command[6:]}" -ItemType Directory -Force'
            elif command.startswith('touch '):
                return f'New-Item -Path "{command[6:]}" -ItemType File -Force'
        else:
            # Keep Unix commands as is
            return command

    def translate_file_creation(self, filename: str, content: str) -> str:
        """
        Translates file creation commands based on OS and shell type.
        """
        if self.os_type == 'windows':
            if self.shell_type == 'powershell':
                return f'Set-Content -Path "{filename}" -Value "{content}" -Encoding UTF8'
            else:  # cmd
                return f'echo {content} > {filename}'
        else:  # Linux or macOS
            return f'cat > {filename} << \'EOF\'\n{content}\nEOF'

    def translate_file_deletion(self, filename: str) -> str:
        """
        Translates file deletion commands based on OS and shell type.
        """
        if self.os_type == 'windows':
            if self.shell_type == 'powershell':
                return f'Remove-Item -Path "{filename}" -Force'
            else:  # cmd
                return f'del {filename}'
        else:  # Linux or macOS
            return f'rm {filename}'

    def translate_file_append(self, filename: str, content: str) -> str:
        """
        Translates file append commands based on OS and shell type.
        """
        # Properly escape the filename for shell safety
        escaped_filename = f'"{filename}"'
        
        if self.os_type == 'windows':
            if self.shell_type == 'powershell':
                return f'Add-Content -Path {escaped_filename} -Value "{content}" -Encoding UTF8'
            else:  # cmd
                return f'echo {content} >> {escaped_filename}'
        else:  # Linux or macOS
            return f'echo "{content}" >> {escaped_filename}'

    def get_safe_commands(self) -> List[str]:
        """
        Returns a list of safe commands for the current OS and shell.
        """
        if self.os_type == 'windows':
            if self.shell_type == 'powershell':
                return ['Get-ChildItem', 'Get-Content', 'Get-Location', 'Get-Process']
            else:  # cmd
                return ['dir', 'type', 'cd', 'echo']
        else:  # Linux or macOS
            return ['ls', 'cat', 'pwd', 'echo', 'grep', 'find'] 