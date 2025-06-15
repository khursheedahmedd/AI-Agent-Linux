import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class CommandHistory:
    """Manages command history for the Sadain CLI."""
    
    def __init__(self, history_file: str = ".sadain_history"):
        """Initialize command history.
        
        Args:
            history_file: Path to the history file
        """
        self.history_file = history_file
        self.history: List[Dict] = []
        self._load_history()
    
    def _load_history(self) -> None:
        """Load command history from file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load history: {str(e)}")
            self.history = []
    
    def _save_history(self) -> None:
        """Save command history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save history: {str(e)}")
    
    def add_command(self, command: str, result: Optional[Dict] = None) -> None:
        """Add a command to history.
        
        Args:
            command: The command that was executed
            result: Optional result of the command execution
        """
        entry = {
            "command": command,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result": result
        }
        self.history.append(entry)
        self._save_history()
    
    def get_last_command(self) -> Optional[Dict]:
        """Get the last executed command.
        
        Returns:
            The last command entry or None if history is empty
        """
        return self.history[-1] if self.history else None
    
    def undo_last_command(self) -> Optional[Dict]:
        """Remove and return the last command from history.
        
        Returns:
            The last command entry or None if history is empty
        """
        if not self.history:
            return None
        last_command = self.history.pop()
        self._save_history()
        return last_command
    
    def get_history(self) -> List[Dict]:
        """Get all command history entries.
        
        Returns:
            List of command history entries
        """
        return self.history
    
    def clear_history(self) -> None:
        """Clear all command history."""
        self.history = []
        self._save_history() 