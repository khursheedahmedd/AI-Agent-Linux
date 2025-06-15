import platform
import os
from typing import Tuple

class OSDetector:
    @staticmethod
    def get_os_info() -> Tuple[str, str]:
        """
        Returns a tuple of (os_type, shell_type)
        os_type can be: 'windows', 'macos', 'linux'
        shell_type can be: 'powershell', 'cmd', 'bash', 'zsh', 'unknown'
        """
        # Detect OS
        system = platform.system().lower()
        if system == 'windows':
            os_type = 'windows'
        elif system == 'darwin':
            os_type = 'macos'
        else:
            os_type = 'linux'

        # Detect shell
        if os_type == 'windows':
            if os.environ.get('ComSpec', '').endswith('powershell.exe'):
                shell_type = 'powershell'
            else:
                shell_type = 'cmd'
        else:
            shell = os.environ.get('SHELL', '').lower()
            if 'zsh' in shell:
                shell_type = 'zsh'
            elif 'bash' in shell:
                shell_type = 'bash'
            else:
                shell_type = 'unknown'

        return os_type, shell_type

    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows"""
        return platform.system().lower() == 'windows'

    @staticmethod
    def is_macos() -> bool:
        """Check if running on macOS"""
        return platform.system().lower() == 'darwin'

    @staticmethod
    def is_linux() -> bool:
        """Check if running on Linux"""
        return platform.system().lower() == 'linux' 