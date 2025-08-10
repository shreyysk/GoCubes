#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visualizer module for Rubik Ultimate Solver

This module provides 2D and 3D visualization of the Rubik's Cube.
"""

import logging
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum

# Module metadata
__all__ = [
    'Cube3DWidget',
    'Cube2DWidget',
    'AnimationController',
    'ColorScheme',
    'initialize_visualizer',
    'create_3d_scene',
    'create_2d_view',
]

# Default color schemes
COLOR_SCHEMES = {
    'standard': {
        'U': '#FFFFFF',  # White
        'D': '#FFFF00',  # Yellow  
        'F': '#00FF00',  # Green
        'B': '#0000FF',  # Blue
        'R': '#FF0000',  # Red
        'L': '#FFA500',  # Orange
        'X': '#808080',  # Unknown/Gray
    },
    'blind': {
        'U': '#FFFFFF',  # White
        'D': '#000000',  # Black
        'F': '#4B7C4B',  # Dark Green
        'B': '#4B4B7C',  # Dark Blue
        'R': '#7C4B4B',  # Dark Red
        'L': '#7C7C4B',  # Dark Yellow
        'X': '#606060',  # Gray
    },
    'high_contrast': {
        'U': '#FFFFFF',  # White
        'D': '#000000',  # Black
        'F': '#00FF00',  # Bright Green
        'B': '#0000FF',  # Bright Blue
        'R': '#FF0000',  # Bright Red
        'L': '#FF00FF',  # Magenta
        'X': '#808080',  # Gray
    },
    'pastel': {
        'U': '#FFF5E6',  # Cream
        'D': '#FFFACD',  # Lemon
        'F': '#E6FFE6',  # Mint
        'B': '#E6E6FF',  # Lavender
        'R': '#FFE6E6',  # Pink
        'L': '#FFDAB9',  # Peach
        'X': '#D3D3D3',  # Light Gray
    },
}

# Animation settings
ANIMATION_SPEED_SLOW = 1000    # milliseconds
ANIMATION_SPEED_NORMAL = 500
ANIMATION_SPEED_FAST = 200
ANIMATION_SPEED_INSTANT = 0

# Display modes
class DisplayMode(Enum):
    """Display mode options"""
    NORMAL = "normal"
    EXPLODED = "exploded"
    TRANSPARENT = "transparent"
    WIREFRAME = "wireframe"
    STICKERS_ONLY = "stickers_only"


class ViewAngle(Enum):
    """Predefined view angles"""
    FRONT = "front"
    BACK = "back"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    ISOMETRIC = "isometric"
    CUSTOM = "custom"


# Logger
logger = logging.getLogger(__name__)


def initialize_visualizer():
    """Initialize the visualizer module"""
    logger.info("Initializing visualizer module")
    
    # Check for 3D dependencies
    try:
        from PyQt5.QtWidgets import QOpenGLWidget
        from OpenGL.GL import glClearColor
        logger.info("OpenGL support available")
    except ImportError:
        logger.warning("OpenGL not available - 3D visualization limited")
    
    # Check for other visualization dependencies
    try:
        import numpy as np
        from PIL import Image
        logger.info("Visualization dependencies verified")
    except ImportError as e:
        logger.error(f"Missing visualization dependency: {e}")
        raise
    
    logger.info("Visualizer module initialized successfully")


def create_3d_scene(cube_state: List[str]) -> 'Cube3DWidget':
    """
    Create a 3D visualization scene
    
    Args:
        cube_state: 54-element list of face colors
        
    Returns:
        3D widget instance
    """
    from .cube_3d import Cube3DWidget
    
    widget = Cube3DWidget()
    widget.set_cube_state(cube_state)
    
    return widget


def create_2d_view(cube_state: List[str]) -> 'Cube2DWidget':
    """
    Create a 2D visualization view
    
    Args:
        cube_state: 54-element list of face colors
        
    Returns:
        2D widget instance
    """
    from .cube_2d import Cube2DWidget
    
    widget = Cube2DWidget()
    widget.set_cube_state(cube_state)
    
    return widget


def get_color_rgb(face: str, scheme: str = 'standard') -> Tuple[int, int, int]:
    """
    Get RGB color for a face
    
    Args:
        face: Face identifier
        scheme: Color scheme name
        
    Returns:
        RGB tuple (0-255)
    """
    hex_color = COLOR_SCHEMES.get(scheme, COLOR_SCHEMES['standard']).get(face, '#808080')
    
    # Convert hex to RGB
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_color_hex(face: str, scheme: str = 'standard') -> str:
    """
    Get hex color for a face
    
    Args:
        face: Face identifier
        scheme: Color scheme name
        
    Returns:
        Hex color string
    """
    return COLOR_SCHEMES.get(scheme, COLOR_SCHEMES['standard']).get(face, '#808080')


def interpolate_color(color1: Tuple[int, int, int], 
                      color2: Tuple[int, int, int], 
                      factor: float) -> Tuple[int, int, int]:
    """
    Interpolate between two colors
    
    Args:
        color1: Start color RGB
        color2: End color RGB
        factor: Interpolation factor (0-1)
        
    Returns:
        Interpolated color RGB
    """
    return tuple(int(c1 + (c2 - c1) * factor) for c1, c2 in zip(color1, color2))


def create_gradient(start_color: str, end_color: str, steps: int = 10) -> List[str]:
    """
    Create a color gradient
    
    Args:
        start_color: Start color (hex)
        end_color: End color (hex)
        steps: Number of gradient steps
        
    Returns:
        List of hex colors
    """
    # Convert hex to RGB
    start_rgb = get_color_rgb('U', 'standard')  # Dummy, would parse hex
    end_rgb = get_color_rgb('D', 'standard')    # Dummy, would parse hex
    
    gradient = []
    for i in range(steps):
        factor = i / (steps - 1) if steps > 1 else 0
        rgb = interpolate_color(start_rgb, end_rgb, factor)
        hex_color = '#{:02x}{:02x}{:02x}'.format(*rgb)
        gradient.append(hex_color)
    
    return gradient


class VisualizationConfig:
    """Configuration for visualization"""
    
    def __init__(self):
        self.color_scheme = 'standard'
        self.animation_speed = ANIMATION_SPEED_NORMAL
        self.show_labels = True
        self.show_axes = False
        self.show_grid = False
        self.anti_aliasing = True
        self.shadows = True
        self.reflections = False
        self.display_mode = DisplayMode.NORMAL
        self.view_angle = ViewAngle.ISOMETRIC
        self.zoom_level = 1.0
        self.rotation = [30, -45, 0]  # x, y, z rotation
        self.background_color = '#F0F0F0'
        self.sticker_gap = 0.1
        self.cube_size = 3
        self.explode_distance = 0.2
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'color_scheme': self.color_scheme,
            'animation_speed': self.animation_speed,
            'show_labels': self.show_labels,
            'show_axes': self.show_axes,
            'show_grid': self.show_grid,
            'anti_aliasing': self.anti_aliasing,
            'shadows': self.shadows,
            'reflections': self.reflections,
            'display_mode': self.display_mode.value,
            'view_angle': self.view_angle.value,
            'zoom_level': self.zoom_level,
            'rotation': self.rotation,
            'background_color': self.background_color,
            'sticker_gap': self.sticker_gap,
            'cube_size': self.cube_size,
            'explode_distance': self.explode_distance,
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Load from dictionary"""
        self.color_scheme = data.get('color_scheme', 'standard')
        self.animation_speed = data.get('animation_speed', ANIMATION_SPEED_NORMAL)
        self.show_labels = data.get('show_labels', True)
        self.show_axes = data.get('show_axes', False)
        self.show_grid = data.get('show_grid', False)
        self.anti_aliasing = data.get('anti_aliasing', True)
        self.shadows = data.get('shadows', True)
        self.reflections = data.get('reflections', False)
        
        display_mode = data.get('display_mode', 'normal')
        self.display_mode = DisplayMode(display_mode)
        
        view_angle = data.get('view_angle', 'isometric')
        self.view_angle = ViewAngle(view_angle)
        
        self.zoom_level = data.get('zoom_level', 1.0)
        self.rotation = data.get('rotation', [30, -45, 0])
        self.background_color = data.get('background_color', '#F0F0F0')
        self.sticker_gap = data.get('sticker_gap', 0.1)
        self.cube_size = data.get('cube_size', 3)
        self.explode_distance = data.get('explode_distance', 0.2)


def calculate_sticker_positions(face: str, size: int = 3) -> List[Tuple[float, float, float]]:
    """
    Calculate 3D positions for stickers on a face
    
    Args:
        face: Face identifier
        size: Cube size (3 for 3x3x3)
        
    Returns:
        List of (x, y, z) positions
    """
    positions = []
    half_size = size / 2.0
    sticker_size = 1.0 / size
    
    for row in range(size):
        for col in range(size):
            # Calculate base position
            x = (col - half_size + 0.5) * sticker_size
            y = (half_size - row - 0.5) * sticker_size
            z = half_size
            
            # Adjust based on face
            if face == 'U':
                pos = (x, half_size, -y)
            elif face == 'D':
                pos = (x, -half_size, y)
            elif face == 'F':
                pos = (x, y, half_size)
            elif face == 'B':
                pos = (-x, y, -half_size)
            elif face == 'R':
                pos = (half_size, y, x)
            elif face == 'L':
                pos = (-half_size, y, -x)
            else:
                pos = (x, y, z)
            
            positions.append(pos)
    
    return positions


def generate_cube_mesh(size: int = 3) -> Dict[str, Any]:
    """
    Generate 3D mesh data for a cube
    
    Args:
        size: Cube size
        
    Returns:
        Mesh data dictionary
    """
    mesh = {
        'vertices': [],
        'faces': [],
        'normals': [],
        'uvs': [],
        'colors': []
    }
    
    # Generate vertices for each cubie
    cubie_size = 1.0 / size
    half_size = size / 2.0
    
    for x in range(size):
        for y in range(size):
            for z in range(size):
                # Skip internal cubies for larger cubes
                if size > 3 and 0 < x < size-1 and 0 < y < size-1 and 0 < z < size-1:
                    continue
                
                # Calculate cubie center
                cx = (x - half_size + 0.5) * cubie_size
                cy = (y - half_size + 0.5) * cubie_size
                cz = (z - half_size + 0.5) * cubie_size
                
                # Add vertices for this cubie
                # (8 vertices per cubie)
                for dx in [-0.5, 0.5]:
                    for dy in [-0.5, 0.5]:
                        for dz in [-0.5, 0.5]:
                            mesh['vertices'].append([
                                cx + dx * cubie_size,
                                cy + dy * cubie_size,
                                cz + dz * cubie_size
                            ])
    
    # Generate faces (triangles)
    # Each cubie has 6 faces, each face has 2 triangles
    # ... (implementation would continue)
    
    return mesh


def export_to_obj(cube_state: List[str], filepath: str):
    """
    Export cube to OBJ file format
    
    Args:
        cube_state: Cube state
        filepath: Output file path
    """
    mesh = generate_cube_mesh()
    
    with open(filepath, 'w') as f:
        # Write vertices
        for vertex in mesh['vertices']:
            f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")
        
        # Write normals
        for normal in mesh['normals']:
            f.write(f"vn {normal[0]} {normal[1]} {normal[2]}\n")
        
        # Write faces
        for face in mesh['faces']:
            f.write(f"f {face[0]} {face[1]} {face[2]}\n")
    
    logger.info(f"Exported cube to {filepath}")


def export_to_png(widget: Any, filepath: str):
    """
    Export visualization to PNG image
    
    Args:
        widget: Visualization widget
        filepath: Output file path
    """
    try:
        from PyQt5.QtGui import QPixmap
        
        # Grab widget content
        pixmap = widget.grab()
        
        # Save to file
        pixmap.save(filepath)
        
        logger.info(f"Exported image to {filepath}")
        
    except Exception as e:
        logger.error(f"Failed to export image: {e}")


class AnimationController:
    """Controls cube animations"""
    
    def __init__(self):
        self.animations = []
        self.current_animation = None
        self.is_playing = False
        self.speed = ANIMATION_SPEED_NORMAL
        self.on_complete = None
        
    def add_move_animation(self, move: str, duration: Optional[int] = None):
        """Add a move animation"""
        if duration is None:
            duration = self.speed
            
        animation = {
            'type': 'move',
            'move': move,
            'duration': duration,
            'progress': 0.0
        }
        
        self.animations.append(animation)
        
    def add_rotation_animation(self, axis: str, angle: float, duration: Optional[int] = None):
        """Add a rotation animation"""
        if duration is None:
            duration = self.speed
            
        animation = {
            'type': 'rotation',
            'axis': axis,
            'angle': angle,
            'duration': duration,
            'progress': 0.0
        }
        
        self.animations.append(animation)
        
    def play(self):
        """Start playing animations"""
        self.is_playing = True
        
        if self.animations and not self.current_animation:
            self.current_animation = self.animations.pop(0)
            
    def pause(self):
        """Pause animations"""
        self.is_playing = False
        
    def stop(self):
        """Stop and reset animations"""
        self.is_playing = False
        self.current_animation = None
        self.animations.clear()
        
    def update(self, delta_time: float) -> bool:
        """
        Update animation state
        
        Args:
            delta_time: Time since last update (ms)
            
        Returns:
            True if animation is active
        """
        if not self.is_playing or not self.current_animation:
            return False
            
        # Update progress
        self.current_animation['progress'] += delta_time / self.current_animation['duration']
        
        # Check if complete
        if self.current_animation['progress'] >= 1.0:
            self.current_animation['progress'] = 1.0
            
            # Move to next animation
            if self.animations:
                self.current_animation = self.animations.pop(0)
            else:
                self.current_animation = None
                self.is_playing = False
                
                if self.on_complete:
                    self.on_complete()
                    
        return True
        
    def get_interpolation_factor(self) -> float:
        """Get current animation interpolation factor"""
        if not self.current_animation:
            return 0.0
            
        # Apply easing function
        t = self.current_animation['progress']
        
        # Smooth step (ease in/out)
        return t * t * (3.0 - 2.0 * t)
        
    def set_speed(self, speed: int):
        """Set animation speed"""
        self.speed = speed
        
    def clear(self):
        """Clear all animations"""
        self.animations.clear()
        self.current_animation = None


# Import main classes
# Import main classes - only import what exists
from visualizer.cube_3d import Cube3DWidget
from visualizer.cube_2d import Cube2DWidget
try:
    from visualizer.animation import MoveAnimator
except ImportError:
    logger.warning("Animation module not available")
    MoveAnimator = None
    
try:
    from visualizer.renderer import CubeRenderer
except ImportError:
    logger.warning("Renderer module not available")
    CubeRenderer = None

logger.info("Visualizer module loaded")