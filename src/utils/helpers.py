#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Helper functions for various operations

This module contains utility functions used throughout the application.
"""

import numpy as np
import logging
import hashlib
import re
from typing import List, Tuple, Optional, Dict, Any, Union
from pathlib import Path
import json
import csv

logger = logging.getLogger(__name__)


def numpy_to_qimage(array: np.ndarray) -> 'QImage':
    """
    Convert numpy array to QImage
    
    Args:
        array: Numpy array (BGR or RGB)
        
    Returns:
        QImage object
    """
    from PyQt5.QtGui import QImage
    
    if array.ndim == 2:
        # Grayscale
        height, width = array.shape
        bytes_per_line = width
        return QImage(array.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
    elif array.ndim == 3:
        # Color
        height, width, channels = array.shape
        bytes_per_line = channels * width
        
        if channels == 3:
            # Convert BGR to RGB if needed
            if array.dtype == np.uint8:
                return QImage(array.data, width, height, bytes_per_line, QImage.Format_RGB888)
        elif channels == 4:
            return QImage(array.data, width, height, bytes_per_line, QImage.Format_RGBA8888)
    
    return QImage()


def qimage_to_numpy(qimage: 'QImage') -> np.ndarray:
    """
    Convert QImage to numpy array
    
    Args:
        qimage: QImage object
        
    Returns:
        Numpy array
    """
    width = qimage.width()
    height = qimage.height()
    
    ptr = qimage.bits()
    ptr.setsize(qimage.byteCount())
    
    arr = np.array(ptr).reshape(height, width, 4)  # RGBA
    return arr[:, :, :3]  # Return RGB only


def calculate_hash(data: Union[str, bytes]) -> str:
    """
    Calculate SHA256 hash of data
    
    Args:
        data: Data to hash
        
    Returns:
        Hex hash string
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    return hashlib.sha256(data).hexdigest()


def validate_cube_string(cube_string: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a cube string representation
    
    Args:
        cube_string: 54-character cube string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check length
    if len(cube_string) != 54:
        return False, f"Invalid length: {len(cube_string)} (expected 54)"
    
    # Check character counts
    char_count = {}
    for char in cube_string:
        char_count[char] = char_count.get(char, 0) + 1
    
    # Should have exactly 9 of each face
    for face in 'URFDLB':
        count = char_count.get(face, 0)
        if count != 9:
            return False, f"Face {face} appears {count} times (expected 9)"
    
    # Check for invalid characters
    valid_chars = set('URFDLB')
    invalid_chars = set(cube_string) - valid_chars
    if invalid_chars:
        return False, f"Invalid characters: {invalid_chars}"
    
    return True, None


def rotate_list(lst: List, n: int) -> List:
    """
    Rotate a list by n positions
    
    Args:
        lst: List to rotate
        n: Number of positions (positive = right, negative = left)
        
    Returns:
        Rotated list
    """
    if not lst:
        return lst
    
    n = n % len(lst)
    return lst[-n:] + lst[:-n]


def chunk_list(lst: List, size: int) -> List[List]:
    """
    Split list into chunks
    
    Args:
        lst: List to split
        size: Chunk size
        
    Returns:
        List of chunks
    """
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def flatten_list(lst: List[List]) -> List:
    """
    Flatten nested list
    
    Args:
        lst: Nested list
        
    Returns:
        Flattened list
    """
    return [item for sublist in lst for item in sublist]


def transpose_matrix(matrix: List[List]) -> List[List]:
    """
    Transpose a 2D matrix
    
    Args:
        matrix: 2D list
        
    Returns:
        Transposed matrix
    """
    return list(map(list, zip(*matrix)))


def rotate_matrix_clockwise(matrix: List[List]) -> List[List]:
    """
    Rotate a 2D matrix 90 degrees clockwise
    
    Args:
        matrix: 2D list
        
    Returns:
        Rotated matrix
    """
    return [list(row) for row in zip(*matrix[::-1])]


def rotate_matrix_counter_clockwise(matrix: List[List]) -> List[List]:
    """
    Rotate a 2D matrix 90 degrees counter-clockwise
    
    Args:
        matrix: 2D list
        
    Returns:
        Rotated matrix
    """
    return [list(row) for row in zip(*matrix)][::-1]


def parse_move_sequence(sequence: str) -> List[str]:
    """
    Parse a move sequence string
    
    Args:
        sequence: Move sequence (e.g., "R U R' U'")
        
    Returns:
        List of individual moves
    """
    # Handle various apostrophe styles
    sequence = sequence.replace("'", "'").replace("'", "'")
    
    # Split by whitespace
    moves = sequence.strip().split()
    
    # Validate each move
    valid_pattern = re.compile(r"^[UDFRBLMESxyz][2']?$", re.IGNORECASE)
    valid_moves = [move for move in moves if valid_pattern.match(move)]
    
    return valid_moves


def format_move_sequence(moves: List[str], group_size: int = 5) -> str:
    """
    Format a move sequence for display
    
    Args:
        moves: List of moves
        group_size: Number of moves per group
        
    Returns:
        Formatted string
    """
    if not moves:
        return ""
    
    # Group moves
    groups = chunk_list(moves, group_size)
    
    # Join groups with extra space
    return "  ".join(" ".join(group) for group in groups)


def calculate_move_metrics(moves: List[str]) -> Dict[str, int]:
    """
    Calculate various metrics for a move sequence
    
    Args:
        moves: List of moves
        
    Returns:
        Dictionary of metrics
    """
    metrics = {
        'total_moves': len(moves),
        'quarter_turns': 0,
        'half_turns': 0,
        'slice_moves': 0,
        'rotations': 0,
        'htm': 0,  # Half Turn Metric
        'qtm': 0,  # Quarter Turn Metric
        'stm': 0,  # Slice Turn Metric
    }
    
    for move in moves:
        if not move:
            continue
        
        face = move[0].upper()
        
        # Count move types
        if '2' in move:
            metrics['half_turns'] += 1
            metrics['qtm'] += 2
        else:
            metrics['quarter_turns'] += 1
            metrics['qtm'] += 1
        
        if face in 'MES':
            metrics['slice_moves'] += 1
            metrics['stm'] += 2
        elif face in 'XYZ':
            metrics['rotations'] += 1
        else:
            metrics['stm'] += 1
        
        # HTM: all moves count as 1
        metrics['htm'] += 1
    
    return metrics


def save_scramble(scramble: str, filepath: str):
    """
    Save scramble to file
    
    Args:
        scramble: Scramble string
        filepath: Output file path
    """
    try:
        with open(filepath, 'w') as f:
            f.write(scramble)
        logger.info(f"Scramble saved to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save scramble: {e}")


def load_scramble(filepath: str) -> Optional[str]:
    """
    Load scramble from file
    
    Args:
        filepath: Input file path
        
    Returns:
        Scramble string or None
    """
    try:
        with open(filepath, 'r') as f:
            scramble = f.read().strip()
        logger.info(f"Scramble loaded from {filepath}")
        return scramble
    except Exception as e:
        logger.error(f"Failed to load scramble: {e}")
        return None


def save_solution(solution: Dict[str, Any], filepath: str):
    """
    Save solution to file
    
    Args:
        solution: Solution dictionary
        filepath: Output file path
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(solution, f, indent=2)
        logger.info(f"Solution saved to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save solution: {e}")


def load_solution(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load solution from file
    
    Args:
        filepath: Input file path
        
    Returns:
        Solution dictionary or None
    """
    try:
        with open(filepath, 'r') as f:
            solution = json.load(f)
        logger.info(f"Solution loaded from {filepath}")
        return solution
    except Exception as e:
        logger.error(f"Failed to load solution: {e}")
        return None


def export_to_csv(data: List[Dict[str, Any]], filepath: str):
    """
    Export data to CSV file
    
    Args:
        data: List of dictionaries
        filepath: Output file path
    """
    if not data:
        logger.warning("No data to export")
        return
    
    try:
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"Data exported to {filepath}")
    except Exception as e:
        logger.error(f"Failed to export to CSV: {e}")


def import_from_csv(filepath: str) -> Optional[List[Dict[str, Any]]]:
    """
    Import data from CSV file
    
    Args:
        filepath: Input file path
        
    Returns:
        List of dictionaries or None
    """
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        logger.info(f"Data imported from {filepath}")
        return data
    except Exception as e:
        logger.error(f"Failed to import from CSV: {e}")
        return None


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.0f}μs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:05.2f}"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:05.2f}"


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value between min and max
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))


def lerp(a: float, b: float, t: float) -> float:
    """
    Linear interpolation
    
    Args:
        a: Start value
        b: End value
        t: Interpolation factor (0-1)
        
    Returns:
        Interpolated value
    """
    return a + (b - a) * t


def smooth_step(t: float) -> float:
    """
    Smooth step function (ease in/out)
    
    Args:
        t: Input value (0-1)
        
    Returns:
        Smoothed value
    """
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def ease_in_out_cubic(t: float) -> float:
    """
    Cubic ease in/out function
    
    Args:
        t: Input value (0-1)
        
    Returns:
        Eased value
    """
    if t < 0.5:
        return 4 * t * t * t
    else:
        p = 2 * t - 2
        return 1 + p * p * p / 2


def normalize_angle(angle: float) -> float:
    """
    Normalize angle to [-180, 180] range
    
    Args:
        angle: Angle in degrees
        
    Returns:
        Normalized angle
    """
    angle = angle % 360
    if angle > 180:
        angle -= 360
    return angle


def angle_difference(angle1: float, angle2: float) -> float:
    """
    Calculate shortest difference between two angles
    
    Args:
        angle1: First angle in degrees
        angle2: Second angle in degrees
        
    Returns:
        Difference in degrees (-180 to 180)
    """
    diff = angle2 - angle1
    return normalize_angle(diff)


def quaternion_to_euler(q: Tuple[float, float, float, float]) -> Tuple[float, float, float]:
    """
    Convert quaternion to Euler angles
    
    Args:
        q: Quaternion (w, x, y, z)
        
    Returns:
        Euler angles (x, y, z) in degrees
    """
    import math
    
    w, x, y, z = q
    
    # Roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    
    # Pitch (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)
    else:
        pitch = math.asin(sinp)
    
    # Yaw (z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    
    # Convert to degrees
    return (
        math.degrees(roll),
        math.degrees(pitch),
        math.degrees(yaw)
    )


def euler_to_quaternion(euler: Tuple[float, float, float]) -> Tuple[float, float, float, float]:
    """
    Convert Euler angles to quaternion
    
    Args:
        euler: Euler angles (x, y, z) in degrees
        
    Returns:
        Quaternion (w, x, y, z)
    """
    import math
    
    # Convert to radians
    roll = math.radians(euler[0])
    pitch = math.radians(euler[1])
    yaw = math.radians(euler[2])
    
    # Calculate quaternion
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    
    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    
    return (w, x, y, z)


def create_backup(filepath: str) -> bool:
    """
    Create backup of file
    
    Args:
        filepath: File to backup
        
    Returns:
        True if successful
    """
    try:
        import shutil
        from datetime import datetime
        
        source = Path(filepath)
        if not source.exists():
            return False
        
        # Create backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = source.parent / f"{source.stem}_backup_{timestamp}{source.suffix}"
        
        # Copy file
        shutil.copy2(source, backup)
        
        logger.info(f"Backup created: {backup}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False


def restore_backup(backup_path: str, target_path: str) -> bool:
    """
    Restore file from backup
    
    Args:
        backup_path: Backup file path
        target_path: Target file path
        
    Returns:
        True if successful
    """
    try:
        import shutil
        
        shutil.copy2(backup_path, target_path)
        logger.info(f"Restored from backup: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to restore backup: {e}")
        return False


def get_file_info(filepath: str) -> Dict[str, Any]:
    """
    Get file information
    
    Args:
        filepath: File path
        
    Returns:
        File information dictionary
    """
    path = Path(filepath)
    
    if not path.exists():
        return {}
    
    import datetime
    
    stat = path.stat()
    
    return {
        'name': path.name,
        'path': str(path.absolute()),
        'size': stat.st_size,
        'size_formatted': format_file_size(stat.st_size),
        'created': datetime.datetime.fromtimestamp(stat.st_ctime),
        'modified': datetime.datetime.fromtimestamp(stat.st_mtime),
        'is_file': path.is_file(),
        'is_directory': path.is_dir(),
        'extension': path.suffix
    }


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