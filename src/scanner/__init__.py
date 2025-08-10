#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scanner module for Rubik Ultimate Solver

This module handles webcam-based cube scanning and color detection.
"""

import logging
from typing import Tuple, List, Optional, Dict, Any
import numpy as np

# Module metadata
__all__ = [
    'CubeScanner',
    'WebcamWidget',
    'ColorDetector',
    'Calibration',
    'initialize_scanner',
    'scan_cube',
    'detect_colors',
]

# Constants
CAMERA_DEFAULT_INDEX = 0
CAMERA_DEFAULT_WIDTH = 640
CAMERA_DEFAULT_HEIGHT = 480
CAMERA_DEFAULT_FPS = 30

# Color detection thresholds
COLOR_THRESHOLD_MIN = 10
COLOR_THRESHOLD_MAX = 100
COLOR_THRESHOLD_DEFAULT = 30

# Contour detection parameters
CONTOUR_AREA_MIN = 30
CONTOUR_AREA_MAX = 60
CONTOUR_ASPECT_RATIO_MIN = 0.8
CONTOUR_ASPECT_RATIO_MAX = 1.2
CONTOUR_APPROXIMATION = 0.1

# Sticker detection parameters
STICKERS_PER_FACE = 9
STICKER_ROWS = 3
STICKER_COLS = 3

# Color names and default values (BGR format for OpenCV)
DEFAULT_COLORS = {
    'white': (255, 255, 255),
    'yellow': (0, 255, 255),
    'red': (0, 0, 255),
    'orange': (0, 165, 255),
    'green': (0, 255, 0),
    'blue': (255, 0, 0)
}

# Face notation
FACE_NOTATION = {
    'U': 'white',   # Up
    'D': 'yellow',  # Down
    'F': 'green',   # Front
    'B': 'blue',    # Back
    'R': 'red',     # Right
    'L': 'orange'   # Left
}

# Color notation mapping
COLOR_TO_NOTATION = {
    'white': 'W',
    'yellow': 'Y',
    'red': 'R',
    'orange': 'O',
    'green': 'G',
    'blue': 'B'
}

NOTATION_TO_COLOR = {v: k for k, v in COLOR_TO_NOTATION.items()}

# Logger
logger = logging.getLogger(__name__)


class ScannerError(Exception):
    """Base exception for scanner module"""
    pass


class CameraError(ScannerError):
    """Exception raised for camera-related errors"""
    pass


class ColorDetectionError(ScannerError):
    """Exception raised for color detection errors"""
    pass


class CalibrationError(ScannerError):
    """Exception raised for calibration errors"""
    pass


def initialize_scanner():
    """Initialize the scanner module"""
    logger.info("Initializing scanner module")
    
    # Check for camera availability
    try:
        import cv2
        
        # Test camera access
        cap = cv2.VideoCapture(CAMERA_DEFAULT_INDEX)
        if not cap.isOpened():
            logger.warning("No camera found at default index")
        else:
            cap.release()
            logger.info("Camera found and accessible")
            
    except ImportError:
        logger.error("OpenCV not installed")
        raise ImportError("OpenCV is required for scanner module")
    
    # Check for other dependencies
    try:
        import numpy as np
        from PIL import Image
        logger.info("Scanner dependencies verified")
    except ImportError as e:
        logger.error(f"Missing scanner dependency: {e}")
        raise
    
    logger.info("Scanner module initialized successfully")


def scan_cube(camera_index: int = CAMERA_DEFAULT_INDEX) -> Dict[str, List[str]]:
    """
    Scan a complete cube using the camera
    
    Args:
        camera_index: Index of the camera to use
        
    Returns:
        Dictionary mapping face names to list of color codes
        
    Raises:
        CameraError: If camera cannot be accessed
        ScannerError: If scanning fails
    """
    from .cube_scanner import CubeScanner
    
    scanner = CubeScanner(camera_index)
    
    try:
        # Start scanning
        scanner.start()
        
        # Scan all faces
        faces = {}
        for face in ['U', 'R', 'F', 'D', 'L', 'B']:
            logger.info(f"Scanning face {face}")
            colors = scanner.scan_face(face)
            faces[face] = colors
            
        logger.info("Cube scanning completed successfully")
        return faces
        
    except Exception as e:
        logger.error(f"Scanning failed: {e}")
        raise ScannerError(f"Failed to scan cube: {e}")
        
    finally:
        scanner.stop()


def detect_colors(
    image: np.ndarray,
    calibration: Optional[Dict[str, Tuple[int, int, int]]] = None
) -> List[str]:
    """
    Detect colors in a cube face image
    
    Args:
        image: Input image as numpy array (BGR format)
        calibration: Optional color calibration data
        
    Returns:
        List of 9 color codes for the face
        
    Raises:
        ColorDetectionError: If color detection fails
    """
    from .color_detection import ColorDetector
    
    detector = ColorDetector(calibration)
    
    try:
        # Find cube contours
        contours = detector.find_contours(image)
        
        if len(contours) != 9:
            raise ColorDetectionError(f"Expected 9 stickers, found {len(contours)}")
        
        # Extract colors
        colors = []
        for contour in contours:
            color = detector.get_dominant_color(image, contour)
            color_name = detector.get_closest_color(color)
            colors.append(COLOR_TO_NOTATION[color_name])
            
        return colors
        
    except Exception as e:
        logger.error(f"Color detection failed: {e}")
        raise ColorDetectionError(f"Failed to detect colors: {e}")


def validate_face_colors(colors: List[str]) -> bool:
    """
    Validate that a face has exactly 9 colors
    
    Args:
        colors: List of color codes
        
    Returns:
        True if valid, False otherwise
    """
    if len(colors) != 9:
        return False
        
    # Check that all colors are valid
    valid_colors = set(COLOR_TO_NOTATION.values())
    for color in colors:
        if color not in valid_colors:
            return False
            
    return True


def validate_cube_colors(faces: Dict[str, List[str]]) -> Tuple[bool, Optional[str]]:
    """
    Validate that a complete cube has valid colors
    
    Args:
        faces: Dictionary mapping face names to color lists
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check all faces present
    required_faces = {'U', 'D', 'F', 'B', 'R', 'L'}
    if set(faces.keys()) != required_faces:
        return False, "Missing faces"
    
    # Check each face has 9 stickers
    for face, colors in faces.items():
        if len(colors) != 9:
            return False, f"Face {face} has {len(colors)} stickers, expected 9"
    
    # Count total colors
    color_count = {}
    for colors in faces.values():
        for color in colors:
            color_count[color] = color_count.get(color, 0) + 1
    
    # Check we have exactly 9 of each color
    for color in COLOR_TO_NOTATION.values():
        if color_count.get(color, 0) != 9:
            return False, f"Color {color} appears {color_count.get(color, 0)} times, expected 9"
    
    # Check center colors are all different
    centers = []
    for face, colors in faces.items():
        center = colors[4]  # Center is index 4
        if center in centers:
            return False, f"Duplicate center color: {center}"
        centers.append(center)
    
    return True, None


def get_color_statistics(faces: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Get statistics about the scanned colors
    
    Args:
        faces: Dictionary mapping face names to color lists
        
    Returns:
        Dictionary with color statistics
    """
    stats = {
        'total_stickers': 0,
        'color_counts': {},
        'face_centers': {},
        'complete': False
    }
    
    # Count colors
    for face, colors in faces.items():
        stats['total_stickers'] += len(colors)
        
        # Get center color
        if len(colors) >= 5:
            stats['face_centers'][face] = colors[4]
        
        # Count each color
        for color in colors:
            stats['color_counts'][color] = stats['color_counts'].get(color, 0) + 1
    
    # Check if complete
    stats['complete'] = (
        stats['total_stickers'] == 54 and
        all(count == 9 for count in stats['color_counts'].values())
    )
    
    return stats


def create_color_map(calibration: Dict[str, Tuple[int, int, int]]) -> Dict[str, np.ndarray]:
    """
    Create a color map from calibration data
    
    Args:
        calibration: Dictionary mapping color names to BGR tuples
        
    Returns:
        Dictionary mapping color names to numpy arrays
    """
    color_map = {}
    
    for color_name, bgr_tuple in calibration.items():
        color_map[color_name] = np.array(bgr_tuple, dtype=np.uint8)
        
    return color_map


def save_calibration(calibration: Dict[str, Tuple[int, int, int]], filepath: str):
    """
    Save calibration data to file
    
    Args:
        calibration: Calibration data
        filepath: Path to save file
    """
    import json
    
    try:
        with open(filepath, 'w') as f:
            json.dump(calibration, f, indent=2)
        logger.info(f"Calibration saved to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save calibration: {e}")
        raise CalibrationError(f"Failed to save calibration: {e}")


def load_calibration(filepath: str) -> Dict[str, Tuple[int, int, int]]:
    """
    Load calibration data from file
    
    Args:
        filepath: Path to calibration file
        
    Returns:
        Calibration data
    """
    import json
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Convert lists to tuples
        calibration = {}
        for color, values in data.items():
            calibration[color] = tuple(values)
            
        logger.info(f"Calibration loaded from {filepath}")
        return calibration
        
    except Exception as e:
        logger.error(f"Failed to load calibration: {e}")
        raise CalibrationError(f"Failed to load calibration: {e}")


def get_default_calibration() -> Dict[str, Tuple[int, int, int]]:
    """
    Get default color calibration
    
    Returns:
        Default calibration data
    """
    return DEFAULT_COLORS.copy()


class ColorSpace:
    """Color space conversion utilities"""
    
    @staticmethod
    def bgr_to_rgb(bgr: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Convert BGR to RGB"""
        return (bgr[2], bgr[1], bgr[0])
    
    @staticmethod
    def rgb_to_bgr(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Convert RGB to BGR"""
        return (rgb[2], rgb[1], rgb[0])
    
    @staticmethod
    def bgr_to_hsv(bgr: np.ndarray) -> np.ndarray:
        """Convert BGR to HSV"""
        import cv2
        bgr_array = np.array([[bgr]], dtype=np.uint8)
        hsv = cv2.cvtColor(bgr_array, cv2.COLOR_BGR2HSV)
        return hsv[0][0]
    
    @staticmethod
    def hsv_to_bgr(hsv: np.ndarray) -> np.ndarray:
        """Convert HSV to BGR"""
        import cv2
        hsv_array = np.array([[hsv]], dtype=np.uint8)
        bgr = cv2.cvtColor(hsv_array, cv2.COLOR_HSV2BGR)
        return bgr[0][0]
    
    @staticmethod
    def bgr_to_lab(bgr: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """Convert BGR to LAB color space"""
        # Convert BGR to RGB first
        rgb = ColorSpace.bgr_to_rgb(bgr)
        
        # Normalize RGB values
        r, g, b = [x / 255.0 for x in rgb]
        
        # Apply gamma correction
        r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
        g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
        b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92
        
        # Convert to XYZ
        x = (r * 0.4124 + g * 0.3576 + b * 0.1805) * 100
        y = (r * 0.2126 + g * 0.7152 + b * 0.0722) * 100
        z = (r * 0.0193 + g * 0.1192 + b * 0.9505) * 100
        
        # Normalize for D65 illuminant
        x /= 95.047
        y /= 100.000
        z /= 108.883
        
        # Apply transformation
        x = x ** (1/3) if x > 0.008856 else (7.787 * x + 16/116)
        y = y ** (1/3) if y > 0.008856 else (7.787 * y + 16/116)
        z = z ** (1/3) if z > 0.008856 else (7.787 * z + 16/116)
        
        # Calculate LAB values
        l = 116 * y - 16
        a = 500 * (x - y)
        b = 200 * (y - z)
        
        return (l, a, b)


# Import main classes
try:
    from scanner.cube_scanner import CubeScanner
    from scanner.webcam import WebcamWidget
    from scanner.color_detection import ColorDetector
    from scanner.calibration import Calibration
except ImportError:
    # Fallback to relative imports if absolute fails
    try:
        from .cube_scanner import CubeScanner
        from .webcam import WebcamWidget
        from .color_detection import ColorDetector
        from .calibration import Calibration
    except ImportError as e:
        logger.error(f"Failed to import scanner components: {e}")

logger.info("Scanner module loaded")