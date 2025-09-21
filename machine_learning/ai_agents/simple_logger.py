"""
Simple, failsafe file-based logging for AI agents.
This is used alongside regular logging to ensure we never lose debug information.
"""

import os
from datetime import datetime
import json
from typing import Any, Optional

class SimpleLogger:
    """
    Dead simple file-based logger that always works.
    Writes to a file in the logs directory with timestamps.
    """
    
    def __init__(self, name: str = "ai_agents", log_dir: Optional[str] = None):
        self.name = name
        if log_dir is None:
            # Default to logs directory at project root
            log_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                "logs"
            )
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, f"{name}_simple.log")
        
        # Ensure log directory exists
        try:
            os.makedirs(log_dir, exist_ok=True)
        except:
            # If we can't even create the directory, use current directory
            self.log_file = f"{name}_simple.log"
    
    def _write(self, level: str, message: str, data: Optional[Any] = None):
        """Write a log entry to file. Never fails."""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] [{level}] [{self.name}] {message}"
            
            # Add data if provided
            if data is not None:
                try:
                    if isinstance(data, (dict, list)):
                        data_str = json.dumps(data, indent=2)
                    else:
                        data_str = str(data)
                    log_entry += f"\n    DATA: {data_str}"
                except:
                    log_entry += f"\n    DATA: {repr(data)}"
            
            # Write to file
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
                f.flush()  # Ensure it's written immediately
        except:
            # Absolute failsafe - try to at least print
            try:
                print(f"[SIMPLE_LOG] {level}: {message}")
            except:
                pass
    
    def info(self, message: str, data: Optional[Any] = None):
        """Log info message"""
        self._write("INFO", message, data)
    
    def error(self, message: str, data: Optional[Any] = None):
        """Log error message"""
        self._write("ERROR", message, data)
    
    def debug(self, message: str, data: Optional[Any] = None):
        """Log debug message"""
        self._write("DEBUG", message, data)
    
    def warning(self, message: str, data: Optional[Any] = None):
        """Log warning message"""
        self._write("WARNING", message, data)
    
    def critical(self, message: str, data: Optional[Any] = None):
        """Log critical message"""
        self._write("CRITICAL", message, data)


# Global instance for easy access
simple_log = SimpleLogger("ai_agents")


def log_alongside(logger, level: str, message: str, data: Optional[Any] = None):
    """
    Helper function to log to both regular logger and simple logger.
    
    Usage:
        log_alongside(self.logger, "info", "Processing query", {"query": query})
    """
    # Log to regular logger first
    if logger and hasattr(logger, level):
        getattr(logger, level)(message)
    
    # Then log to simple logger
    getattr(simple_log, level)(message, data)
