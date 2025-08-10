#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cube model representation

This module implements the cube state representation and manipulation.
"""

import numpy as np
import logging
from typing import List, Dict, Tuple, Optional, Any
from copy import deepcopy
from enum import Enum

logger = logging.getLogger(__name__)


class Face(Enum):
    """Cube faces"""
    UP = 'U'
    DOWN = 'D'
    FRONT = 'F'
    BACK = 'B'
    RIGHT = 'R'
    LEFT = 'L'


class Color(Enum):
    """Cube colors"""
    WHITE = 'W'
    YELLOW = 'Y'
    RED = 'R'
    ORANGE = 'O'
    GREEN = 'G'
    BLUE = 'B'
    UNKNOWN = 'X'


class CubeModel:
    """
    Rubik's Cube model representation
    
    The cube is represented as a 54-element array:
    - Indices 0-8: Up face
    - Indices 9-17: Right face
    - Indices 18-26: Front face
    - Indices 27-35: Down face
    - Indices 36-44: Left face
    - Indices 45-53: Back face
    
    Each face is numbered:
    0 1 2
    3 4 5
    6 7 8
    """
    
    def __init__(self):
        """Initialize a solved cube"""
        self.reset()
        
        # Face indices
        self.face_indices = {
            'U': list(range(0, 9)),
            'R': list(range(9, 18)),
            'F': list(range(18, 27)),
            'D': list(range(27, 36)),
            'L': list(range(36, 45)),
            'B': list(range(45, 54))
        }
        
        # Move definitions (clockwise rotations)
        self.move_definitions = self._init_move_definitions()
        
        # History for undo/redo
        self.history = []
        self.history_index = -1
        
    def reset(self):
        """Reset to solved state"""
        self.state = [
            'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U',  # Up (white)
            'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R',  # Right (red)
            'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F',  # Front (green)
            'D', 'D', 'D', 'D', 'D', 'D', 'D', 'D', 'D',  # Down (yellow)
            'L', 'L', 'L', 'L', 'L', 'L', 'L', 'L', 'L',  # Left (orange)
            'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B',  # Back (blue)
        ]
        
    def clear(self):
        """Clear all colors"""
        self.state = ['X'] * 54
        
    def _init_move_definitions(self) -> Dict[str, List[Tuple[int, int]]]:
        """Initialize move cycle definitions"""
        return {
            # Up face clockwise
            'U': [
                # Face rotation
                (0, 2), (2, 8), (8, 6), (6, 0),
                (1, 5), (5, 7), (7, 3), (3, 1),
                # Adjacent faces
                (9, 45), (45, 36), (36, 18), (18, 9),
                (10, 46), (46, 37), (37, 19), (19, 10),
                (11, 47), (47, 38), (38, 20), (20, 11)
            ],
            
            # Down face clockwise
            'D': [
                # Face rotation
                (27, 29), (29, 35), (35, 33), (33, 27),
                (28, 32), (32, 34), (34, 30), (30, 28),
                # Adjacent faces
                (24, 15), (15, 51), (51, 42), (42, 24),
                (25, 16), (16, 52), (52, 43), (43, 25),
                (26, 17), (17, 53), (53, 44), (44, 26)
            ],
            
            # Front face clockwise
            'F': [
                # Face rotation
                (18, 20), (20, 26), (26, 24), (24, 18),
                (19, 23), (23, 25), (25, 21), (21, 19),
                # Adjacent faces
                (6, 11), (11, 29), (29, 36), (36, 6),
                (7, 14), (14, 28), (28, 39), (39, 7),
                (8, 17), (17, 27), (27, 42), (42, 8)
            ],
            
            # Back face clockwise
            'B': [
                # Face rotation
                (45, 47), (47, 53), (53, 51), (51, 45),
                (46, 50), (50, 52), (52, 48), (48, 46),
                # Adjacent faces
                (2, 38), (38, 33), (33, 15), (15, 2),
                (1, 41), (41, 34), (34, 12), (12, 1),
                (0, 44), (44, 35), (35, 9), (9, 0)
            ],
            
            # Right face clockwise
            'R': [
                # Face rotation
                (9, 11), (11, 17), (17, 15), (15, 9),
                (10, 14), (14, 16), (16, 12), (12, 10),
                # Adjacent faces
                (2, 20), (20, 29), (29, 47), (47, 2),
                (5, 23), (23, 32), (32, 50), (50, 5),
                (8, 26), (26, 35), (35, 53), (53, 8)
            ],
            
            # Left face clockwise
            'L': [
                # Face rotation
                (36, 38), (38, 44), (44, 42), (42, 36),
                (37, 41), (41, 43), (43, 39), (39, 37),
                # Adjacent faces
                (0, 45), (45, 27), (27, 18), (18, 0),
                (3, 48), (48, 30), (30, 21), (21, 3),
                (6, 51), (51, 33), (33, 24), (24, 6)
            ]
        }
        
    def get_state(self) -> List[str]:
        """Get current cube state"""
        return self.state.copy()
        
    def set_state(self, state: List[str]):
        """Set cube state"""
        if len(state) != 54:
            raise ValueError("State must have 54 elements")
        self.state = state.copy()
        self._add_to_history()
        
    def get_face_colors(self, face: str) -> List[str]:
        """
        Get colors of a face
        
        Args:
            face: Face name (U, R, F, D, L, B)
            
        Returns:
            List of 9 color codes
        """
        if face not in self.face_indices:
            raise ValueError(f"Invalid face: {face}")
            
        indices = self.face_indices[face]
        return [self.state[i] for i in indices]
        
    def set_face_colors(self, face: str, colors: List[str]):
        """
        Set colors of a face
        
        Args:
            face: Face name
            colors: List of 9 color codes
        """
        if face not in self.face_indices:
            raise ValueError(f"Invalid face: {face}")
            
        if len(colors) != 9:
            raise ValueError("Face must have 9 colors")
            
        indices = self.face_indices[face]
        for i, color in zip(indices, colors):
            self.state[i] = color
            
        self._add_to_history()
        
    def get_sticker(self, face: str, position: int) -> str:
        """
        Get color of a specific sticker
        
        Args:
            face: Face name
            position: Position on face (0-8)
            
        Returns:
            Color code
        """
        if face not in self.face_indices:
            raise ValueError(f"Invalid face: {face}")
            
        if position < 0 or position > 8:
            raise ValueError(f"Invalid position: {position}")
            
        index = self.face_indices[face][position]
        return self.state[index]
        
    def set_sticker(self, face: str, position: int, color: str):
        """
        Set color of a specific sticker
        
        Args:
            face: Face name
            position: Position on face (0-8)
            color: Color code
        """
        if face not in self.face_indices:
            raise ValueError(f"Invalid face: {face}")
            
        if position < 0 or position > 8:
            raise ValueError(f"Invalid position: {position}")
            
        index = self.face_indices[face][position]
        self.state[index] = color
        self._add_to_history()
        
    def apply_move(self, move: str):
        """
        Apply a move to the cube
        
        Args:
            move: Move notation (e.g., 'U', "U'", 'U2')
        """
        if not move:
            return
            
        # Parse move
        face = move[0]
        if face not in 'URFDLB':
            raise ValueError(f"Invalid move: {move}")
            
        # Determine rotation count
        if len(move) == 1:
            rotations = 1
        elif move[1] == "'":
            rotations = 3  # Counter-clockwise = 3 clockwise
        elif move[1] == "2":
            rotations = 2
        else:
            raise ValueError(f"Invalid move: {move}")
            
        # Apply rotations
        for _ in range(rotations):
            self._rotate_face(face)
            
        self._add_to_history()
        
    def _rotate_face(self, face: str):
        """
        Rotate a face clockwise
        
        Args:
            face: Face to rotate
        """
        if face not in self.move_definitions:
            raise ValueError(f"Invalid face: {face}")
            
        # Get cycle definitions
        cycles = self.move_definitions[face]
        
        # Create new state
        new_state = self.state.copy()
        
        # Apply cycles (groups of 4)
        i = 0
        while i < len(cycles):
            # 4-cycle: a -> b -> c -> d -> a
            a, b = cycles[i]
            c, d = cycles[i+1]
            e, f = cycles[i+2]
            g, h = cycles[i+3]
            
            new_state[b] = self.state[a]
            new_state[d] = self.state[c]
            new_state[f] = self.state[e]
            new_state[h] = self.state[g]
            
            i += 4
            
        self.state = new_state
        
    def apply_sequence(self, sequence: str):
        """
        Apply a sequence of moves
        
        Args:
            sequence: Space-separated move sequence
        """
        moves = sequence.strip().split()
        for move in moves:
            if move:
                self.apply_move(move)
                
    def to_string(self) -> str:
        """
        Convert cube to string representation
        
        Returns:
            54-character string
        """
        return ''.join(self.state)
        
    def from_string(self, cube_string: str):
        """
        Load cube from string representation
        
        Args:
            cube_string: 54-character string
        """
        if len(cube_string) != 54:
            raise ValueError("Cube string must have 54 characters")
            
        self.state = list(cube_string)
        self._add_to_history()
        
    def is_solved(self) -> bool:
        """Check if cube is solved"""
        for face in self.face_indices:
            colors = self.get_face_colors(face)
            if len(set(colors)) != 1:
                return False
        return True
        
    def is_complete(self) -> bool:
        """Check if all stickers are filled"""
        return 'X' not in self.state
        
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate cube configuration
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check completeness
        if not self.is_complete():
            return False, "Cube is not complete"
            
        # Count colors
        color_count = {}
        for color in self.state:
            color_count[color] = color_count.get(color, 0) + 1
            
        # Check each color appears exactly 9 times
        expected_colors = set('URFDLB')
        for color in expected_colors:
            if color_count.get(color, 0) != 9:
                return False, f"Color {color} appears {color_count.get(color, 0)} times, expected 9"
                
        # Check for unexpected colors
        if set(color_count.keys()) != expected_colors:
            unexpected = set(color_count.keys()) - expected_colors
            return False, f"Unexpected colors: {unexpected}"
            
        # Check center colors are all different
        centers = []
        for face in self.face_indices:
            center = self.get_sticker(face, 4)
            if center in centers:
                return False, f"Duplicate center color: {center}"
            centers.append(center)
            
        # TODO: Add more sophisticated validation (solvability check)
        
        return True, None
        
    def get_color_positions(self, color: str) -> List[int]:
        """
        Get all positions of a color
        
        Args:
            color: Color code
            
        Returns:
            List of indices
        """
        positions = []
        for i, c in enumerate(self.state):
            if c == color:
                positions.append(i)
        return positions
        
    def copy(self) -> 'CubeModel':
        """Create a copy of the cube"""
        new_cube = CubeModel()
        new_cube.state = self.state.copy()
        return new_cube
        
    def _add_to_history(self):
        """Add current state to history"""
        # Remove any states after current index
        self.history = self.history[:self.history_index + 1]
        
        # Add current state
        self.history.append(self.state.copy())
        self.history_index += 1
        
        # Limit history size
        max_history = 100
        if len(self.history) > max_history:
            self.history = self.history[-max_history:]
            self.history_index = len(self.history) - 1
            
    def undo(self) -> bool:
        """
        Undo last action
        
        Returns:
            True if successful
        """
        if self.history_index > 0:
            self.history_index -= 1
            self.state = self.history[self.history_index].copy()
            return True
        return False
        
    def redo(self) -> bool:
        """
        Redo last undone action
        
        Returns:
            True if successful
        """
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.state = self.history[self.history_index].copy()
            return True
        return False
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get cube statistics"""
        stats = {
            'is_solved': self.is_solved(),
            'is_complete': self.is_complete(),
            'color_counts': {},
            'face_uniformity': {}
        }
        
        # Count colors
        for color in self.state:
            stats['color_counts'][color] = stats['color_counts'].get(color, 0) + 1
            
        # Check face uniformity
        for face in self.face_indices:
            colors = self.get_face_colors(face)
            unique_colors = len(set(colors))
            stats['face_uniformity'][face] = {
                'unique_colors': unique_colors,
                'is_uniform': unique_colors == 1
            }
            
        return stats
        
    def to_notation_string(self) -> str:
        """
        Convert to standard notation string
        
        Returns:
            String in format "UF UR UB UL DF DR DB DL FR FL BR BL UFR URB UBL ULF DRF DFL DLB DBR"
        """
        # This would convert to standard cubie notation
        # Implementation depends on specific notation requirements
        pass
        
    def __str__(self) -> str:
        """String representation"""
        return self.to_string()
        
    def __repr__(self) -> str:
        """Debug representation"""
        return f"CubeModel(state='{self.to_string()}')"
        
    def visualize_2d(self) -> str:
        """
        Create 2D ASCII visualization
        
        Returns:
            ASCII art representation
        """
        lines = []
        
        # Up face
        lines.append("      " + " ".join(self.state[0:3]))
        lines.append("      " + " ".join(self.state[3:6]))
        lines.append("      " + " ".join(self.state[6:9]))
        lines.append("")
        
        # Middle row (L, F, R, B)
        for i in range(3):
            row = ""
            row += " ".join(self.state[36 + i*3:36 + i*3 + 3]) + "  "  # Left
            row += " ".join(self.state[18 + i*3:18 + i*3 + 3]) + "  "  # Front
            row += " ".join(self.state[9 + i*3:9 + i*3 + 3]) + "  "   # Right
            row += " ".join(self.state[45 + i*3:45 + i*3 + 3])        # Back
            lines.append(row)
        lines.append("")
        
        # Down face
        lines.append("      " + " ".join(self.state[27:30]))
        lines.append("      " + " ".join(self.state[30:33]))
        lines.append("      " + " ".join(self.state[33:36]))
        
        return "\n".join(lines)