#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilities module for Rubik Ultimate Solver

This module provides common utilities and helper functions.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import json
import os
from pathlib import Path

# Module metadata
__all__ = [
    'Config',
    'Logger',
    'Timer',
    'format_time',
    'validate_scramble',
    'parse_config',
    'save_config',
    'ensure_directory',
    'get_resource_path',
]

# Logger
logger = logging.getLogger(__name__)


class Config:
    """Configuration manager"""
    
    _instance = None
    _config = {}
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from file"""
        config_file = self._get_config_file()
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    self._config = json.load(f)
                logger.info(f"Configuration loaded from {config_file}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                self._config = self._get_default_config()
        else:
            self._config = self._get_default_config()
            self._save_config()
    
    def _save_config(self):
        """Save configuration to file"""
        config_file = self._get_config_file()
        
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            
            logger.info(f"Configuration saved to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _get_config_file(self) -> Path:
        """Get configuration file path"""
        home = Path.home()
        return home / '.rubik_ultimate' / 'config.json'
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'version': '1.0.0',
            'language': 'en',
            'theme': 'dark',
            
            'scanner': {
                'camera_index': 0,
                'resolution': [640, 480],
                'fps': 30,
                'detection_threshold': 30,
                'auto_detect': True,
                'calibration_file': 'default.json'
            },
            
            'solver': {
                'default_algorithm': 'kociemba',
                'max_time': 10.0,
                'use_pruning': True,
                'algorithms': {
                    'kociemba': {
                        'max_depth': 24,
                        'timeout': 10.0
                    },
                    'thistlethwaite': {
                        'phase_depths': [7, 10, 13, 15]
                    }
                }
            },
            
            'visualization': {
                'color_scheme': 'standard',
                'animation_speed': 500,
                'show_labels': True,
                'show_axes': False,
                'anti_aliasing': True,
                'shadows': True,
                'default_view': 'isometric'
            },
            
            'ui': {
                'window_geometry': None,
                'recent_files': [],
                'max_recent_files': 10,
                'auto_save': True,
                'sound_enabled': True
            },
            
            'advanced': {
                'debug_mode': False,
                'log_level': 'INFO',
                'performance_mode': False,
                'gpu_acceleration': True
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Dot-separated key path (e.g., 'solver.default_algorithm')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value
        
        Args:
            key: Dot-separated key path
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to parent
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set value
        config[keys[-1]] = value
    
    def save(self):
        """Save configuration to file"""
        self._save_config()
    
    def reset(self):
        """Reset to default configuration"""
        self._config = self._get_default_config()
        self._save_config()
    
    def export(self, filepath: str):
        """Export configuration to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Configuration exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export config: {e}")
    
    def import_config(self, filepath: str):
        """Import configuration from file"""
        try:
            with open(filepath, 'r') as f:
                imported = json.load(f)
            
            # Merge with current config
            self._merge_config(imported)
            self._save_config()
            
            logger.info(f"Configuration imported from {filepath}")
        except Exception as e:
            logger.error(f"Failed to import config: {e}")
    
    def _merge_config(self, imported: Dict[str, Any]):
        """Merge imported configuration"""
        def merge_dict(target, source):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    merge_dict(target[key], value)
                else:
                    target[key] = value
        
        merge_dict(self._config, imported)


class Logger:
    """Logging utilities"""
    
    @staticmethod
    def setup_logging(level: str = 'INFO', log_file: Optional[str] = None):
        """
        Setup logging configuration
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
        """
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level))
        root_logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
                logger.info(f"Logging to file: {log_file}")
            except Exception as e:
                logger.error(f"Failed to setup file logging: {e}")
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get logger instance"""
        return logging.getLogger(name)


class Timer:
    """Simple timer for performance measurement"""
    
    def __init__(self):
        """Initialize timer"""
        self.times = {}
        
    def start(self, name: str = 'default'):
        """Start timer"""
        import time
        self.times[name] = time.time()
        
    def stop(self, name: str = 'default') -> float:
        """
        Stop timer and return elapsed time
        
        Args:
            name: Timer name
            
        Returns:
            Elapsed time in seconds
        """
        import time
        
        if name not in self.times:
            return 0.0
            
        elapsed = time.time() - self.times[name]
        del self.times[name]
        
        return elapsed
        
    def lap(self, name: str = 'default') -> float:
        """
        Get lap time without stopping
        
        Args:
            name: Timer name
            
        Returns:
            Elapsed time in seconds
        """
        import time
        
        if name not in self.times:
            return 0.0
            
        return time.time() - self.times[name]
        
    def reset(self, name: str = 'default'):
        """Reset timer"""
        if name in self.times:
            del self.times[name]
            
    def reset_all(self):
        """Reset all timers"""
        self.times.clear()


def format_time(seconds: float) -> str:
    """
    Format time in seconds to readable string
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def validate_scramble(scramble: str) -> bool:
    """
    Validate scramble notation
    
    Args:
        scramble: Scramble string
        
    Returns:
        True if valid
    """
    if not scramble:
        return False
        
    valid_moves = set([
        'U', "U'", 'U2', 'D', "D'", 'D2',
        'F', "F'", 'F2', 'B', "B'", 'B2',
        'R', "R'", 'R2', 'L', "L'", 'L2',
        'M', "M'", 'M2', 'E', "E'", 'E2',
        'S', "S'", 'S2', 'x', "x'", 'x2',
        'y', "y'", 'y2', 'z', "z'", 'z2',
        'u', "u'", 'u2', 'd', "d'", 'd2',
        'r', "r'", 'r2', 'l', "l'", 'l2',
        'f', "f'", 'f2', 'b', "b'", 'b2'
    ])
    
    moves = scramble.strip().split()
    
    # Check each move
    for move in moves:
        if move not in valid_moves:
            return False
            
    # Check for consecutive same face moves
    for i in range(1, len(moves)):
        if moves[i][0] == moves[i-1][0]:
            return False
            
    return True


def parse_config(config_str: str) -> Dict[str, Any]:
    """
    Parse configuration string
    
    Args:
        config_str: Configuration in JSON or key=value format
        
    Returns:
        Parsed configuration dictionary
    """
    # Try JSON first
    try:
        return json.loads(config_str)
    except:
        pass
        
    # Try key=value format
    config = {}
    
    for line in config_str.strip().split('\n'):
        line = line.strip()
        
        if not line or line.startswith('#'):
            continue
            
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Try to parse value
            try:
                value = json.loads(value)
            except:
                # Keep as string
                pass
                
            # Set nested keys
            keys = key.split('.')
            current = config
            
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
                
            current[keys[-1]] = value
            
    return config


def save_config(config: Dict[str, Any], filepath: str):
    """
    Save configuration to file
    
    Args:
        config: Configuration dictionary
        filepath: Output file path
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")


def ensure_directory(path: str) -> Path:
    """
    Ensure directory exists
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_resource_path(resource: str) -> Path:
    """
    Get path to resource file
    
    Args:
        resource: Resource name
        
    Returns:
        Path to resource
    """
    # Check multiple locations
    locations = [
        Path(__file__).parent.parent / 'resources' / resource,
        Path.cwd() / 'resources' / resource,
        Path.home() / '.rubik_ultimate' / 'resources' / resource,
    ]
    
    for location in locations:
        if location.exists():
            return location
            
    # Return first location as default
    return locations[0]


def get_data_directory() -> Path:
    """Get application data directory"""
    data_dir = Path.home() / '.rubik_ultimate' / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_cache_directory() -> Path:
    """Get application cache directory"""
    cache_dir = Path.home() / '.rubik_ultimate' / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def clear_cache():
    """Clear application cache"""
    cache_dir = get_cache_directory()
    
    try:
        import shutil
        shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Cache cleared")
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")


def get_application_info() -> Dict[str, str]:
    """Get application information"""
    from __init__ import __version__, APP_NAME, APP_AUTHOR
    
    return {
        'name': APP_NAME,
        'version': __version__,
        'author': APP_AUTHOR,
        'python_version': get_python_version(),
        'platform': get_platform_info(),
        'qt_version': get_qt_version(),
    }


def get_python_version() -> str:
    """Get Python version"""
    import sys
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_platform_info() -> str:
    """Get platform information"""
    import platform
    return f"{platform.system()} {platform.release()}"


def get_qt_version() -> str:
    """Get Qt version"""
    try:
        from PyQt5.QtCore import QT_VERSION_STR
        return QT_VERSION_STR
    except:
        return "Unknown"


# Import submodules
from utils.constants import *
from utils.helpers import *
from utils.translator import Translator, tr

# Initialize configuration
config = Config()

logger.info("Utils module loaded")