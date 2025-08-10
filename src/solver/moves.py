#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Move definitions and manipulation

This module handles move notation, sequences, and transformations.
"""

import random
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MoveType(Enum):
    """Types of moves"""
    BASIC = "basic"           # Single face turn
    WIDE = "wide"            # Wide turn (two layers)
    SLICE = "slice"          # Middle slice
    ROTATION = "rotation"    # Whole cube rotation


@dataclass
class Move:
    """Represents a single move"""
    face: str               # Face or axis (U, R, F, D, L, B, M, E, S, x, y, z)
    turns: int             # Number of quarter turns (1, 2, or 3)
    wide: bool = False     # Whether it's a wide move
    
    def __str__(self) -> str:
        """Convert to standard notation"""
        notation = self.face
        
        if self.wide and self.face in 'URFDLB':
            notation = self.face.lower()
            
        if self.turns == 2:
            notation += '2'
        elif self.turns == 3:
            notation += "'"
            
        return notation
    
    @classmethod
    def from_string(cls, move_str: str) -> 'Move':
        """Create Move from notation string"""
        if not move_str:
            raise ValueError("Empty move string")
            
        # Parse the move
        face = move_str[0].upper()
        wide = move_str[0].islower()
        
        # Handle special notations
        if face == 'M':  # Middle slice
            face = 'M'
            wide = False
        elif face == 'E':  # Equatorial slice
            face = 'E'
            wide = False
        elif face == 'S':  # Standing slice
            face = 'S'
            wide = False
        elif face in 'XYZ':  # Rotations
            wide = False
            
        # Parse turns
        if len(move_str) == 1:
            turns = 1
        elif move_str[-1] == '2':
            turns = 2
        elif move_str[-1] == "'":
            turns = 3
        else:
            turns = 1
            
        return cls(face=face, turns=turns, wide=wide)
    
    def inverse(self) -> 'Move':
        """Get inverse of this move"""
        inverse_turns = (4 - self.turns) % 4
        if inverse_turns == 0:
            inverse_turns = 2  # 180° is its own inverse
            
        return Move(face=self.face, turns=inverse_turns, wide=self.wide)
    
    def is_opposite_face(self, other: 'Move') -> bool:
        """Check if moves are on opposite faces"""
        opposites = {
            'U': 'D', 'D': 'U',
            'F': 'B', 'B': 'F',
            'R': 'L', 'L': 'R'
        }
        return opposites.get(self.face) == other.face


class MoveSequence:
    """Represents a sequence of moves"""
    
    def __init__(self, moves: Optional[List[Move]] = None):
        """Initialize move sequence"""
        self.moves = moves if moves else []
        
    def __str__(self) -> str:
        """Convert to notation string"""
        return ' '.join(str(move) for move in self.moves)
    
    def __len__(self) -> int:
        """Get number of moves"""
        return len(self.moves)
    
    def __getitem__(self, index: int) -> Move:
        """Get move at index"""
        return self.moves[index]
    
    def __iter__(self):
        """Iterate over moves"""
        return iter(self.moves)
    
    @classmethod
    def from_string(cls, sequence_str: str) -> 'MoveSequence':
        """Create sequence from notation string"""
        if not sequence_str:
            return cls()
            
        move_strs = sequence_str.strip().split()
        moves = [Move.from_string(m) for m in move_strs if m]
        
        return cls(moves)
    
    def append(self, move: Move):
        """Add move to sequence"""
        self.moves.append(move)
        
    def extend(self, moves: List[Move]):
        """Add multiple moves"""
        self.moves.extend(moves)
        
    def inverse(self) -> 'MoveSequence':
        """Get inverse sequence"""
        inverse_moves = [move.inverse() for move in reversed(self.moves)]
        return MoveSequence(inverse_moves)
    
    def optimize(self) -> 'MoveSequence':
        """Optimize sequence by removing redundancies"""
        from .optimizer import MoveOptimizer
        optimizer = MoveOptimizer()
        
        move_strs = [str(move) for move in self.moves]
        optimized_strs = optimizer.optimize(move_strs)
        
        return MoveSequence.from_string(' '.join(optimized_strs))
    
    def get_metrics(self) -> Dict[str, int]:
        """Calculate move metrics"""
        metrics = {
            'htm': 0,   # Half Turn Metric
            'qtm': 0,   # Quarter Turn Metric
            'stm': 0,   # Slice Turn Metric
            'etm': 0,   # Execution Turn Metric
            'atm': 0,   # Axis Turn Metric
        }
        
        for move in self.moves:
            # HTM: Every move counts as 1
            metrics['htm'] += 1
            
            # QTM: Count quarter turns
            metrics['qtm'] += move.turns if move.turns != 3 else 1
            
            # STM: Slice moves count differently
            if move.face in 'MES':
                metrics['stm'] += 2  # Slice = 2 face moves
            elif move.wide:
                metrics['stm'] += 1  # Wide moves same as regular
            else:
                metrics['stm'] += 1
                
            # ETM: Execution time (simplified)
            metrics['etm'] += 1
            
            # ATM: Axis turn metric
            if move.face in 'URFDLB':
                metrics['atm'] += 1
            elif move.face in 'MES':
                metrics['atm'] += 2
            elif move.face in 'xyz':
                metrics['atm'] += 3
                
        return metrics


# Standard move sets
BASIC_MOVES = ["U", "U'", "U2", "D", "D'", "D2",
               "F", "F'", "F2", "B", "B'", "B2",
               "R", "R'", "R2", "L", "L'", "L2"]

WIDE_MOVES = ["u", "u'", "u2", "d", "d'", "d2",
              "f", "f'", "f2", "b", "b'", "b2",
              "r", "r'", "r2", "l", "l'", "l2"]

SLICE_MOVES = ["M", "M'", "M2", "E", "E'", "E2", "S", "S'", "S2"]

ROTATION_MOVES = ["x", "x'", "x2", "y", "y'", "y2", "z", "z'", "z2"]

ALL_MOVES = BASIC_MOVES + WIDE_MOVES + SLICE_MOVES + ROTATION_MOVES


def parse_move(move_str: str) -> Tuple[str, int]:
    """
    Parse a move string into face and rotation
    
    Args:
        move_str: Move notation string
        
    Returns:
        Tuple of (face, turns)
    """
    move = Move.from_string(move_str)
    return move.face, move.turns


def inverse_move(move_str: str) -> str:
    """
    Get inverse of a move
    
    Args:
        move_str: Move notation
        
    Returns:
        Inverse move notation
    """
    move = Move.from_string(move_str)
    return str(move.inverse())


def inverse_sequence(sequence: str) -> str:
    """
    Get inverse of a move sequence
    
    Args:
        sequence: Space-separated moves
        
    Returns:
        Inverse sequence
    """
    seq = MoveSequence.from_string(sequence)
    return str(seq.inverse())


def generate_random_scramble(length: int = 25, 
                           move_set: Optional[List[str]] = None) -> str:
    """
    Generate a random scramble
    
    Args:
        length: Number of moves
        move_set: Allowed moves (default: basic moves)
        
    Returns:
        Scramble string
    """
    if move_set is None:
        move_set = BASIC_MOVES
        
    scramble = []
    last_face = None
    second_last_face = None
    
    for _ in range(length):
        # Filter out invalid moves
        valid_moves = move_set.copy()
        
        # Don't repeat same face
        if last_face:
            valid_moves = [m for m in valid_moves if not m.startswith(last_face)]
            
        # Don't do opposite faces in wrong order
        if second_last_face and last_face:
            opposites = {'U': 'D', 'D': 'U', 'F': 'B', 'B': 'F', 'R': 'L', 'L': 'R'}
            if opposites.get(second_last_face) == last_face:
                valid_moves = [m for m in valid_moves 
                             if not m.startswith(second_last_face)]
                
        # Choose random move
        move = random.choice(valid_moves)
        scramble.append(move)
        
        # Update history
        second_last_face = last_face
        last_face = move[0]
        
    return ' '.join(scramble)


def simplify_sequence(sequence: str) -> str:
    """
    Simplify a move sequence
    
    Args:
        sequence: Move sequence
        
    Returns:
        Simplified sequence
    """
    seq = MoveSequence.from_string(sequence)
    return str(seq.optimize())


def expand_wide_moves(sequence: str) -> str:
    """
    Expand wide moves to basic moves
    
    Args:
        sequence: Move sequence with wide moves
        
    Returns:
        Equivalent sequence with only basic moves
    """
    expansions = {
        'u': ["U", "E'"],
        "u'": ["U'", "E"],
        'u2': ["U2", "E2"],
        'd': ["D", "E"],
        "d'": ["D'", "E'"],
        'd2': ["D2", "E2"],
        'r': ["R", "M'"],
        "r'": ["R'", "M"],
        'r2': ["R2", "M2"],
        'l': ["L", "M"],
        "l'": ["L'", "M'"],
        'l2': ["L2", "M2"],
        'f': ["F", "S"],
        "f'": ["F'", "S'"],
        'f2': ["F2", "S2"],
        'b': ["B", "S'"],
        "b'": ["B'", "S"],
        'b2': ["B2", "S2"],
    }
    
    moves = sequence.split()
    expanded = []
    
    for move in moves:
        if move.lower() in expansions:
            expanded.extend(expansions[move.lower()])
        else:
            expanded.append(move)
            
    return ' '.join(expanded)


def convert_to_slice_moves(sequence: str) -> str:
    """
    Convert sequence to use slice moves where possible
    
    Args:
        sequence: Move sequence
        
    Returns:
        Sequence with slice moves
    """
    # This would analyze the sequence and replace patterns with slice moves
    # For example: R L' -> M
    # Implementation would be more complex
    return sequence


def count_moves(sequence: str, metric: str = 'htm') -> int:
    """
    Count moves using specified metric
    
    Args:
        sequence: Move sequence
        metric: Metric to use (htm, qtm, stm, etm, atm)
        
    Returns:
        Move count
    """
    seq = MoveSequence.from_string(sequence)
    metrics = seq.get_metrics()
    
    return metrics.get(metric, 0)


def is_valid_scramble(scramble: str) -> bool:
    """
    Check if scramble is valid
    
    Args:
        scramble: Scramble string
        
    Returns:
        True if valid
    """
    try:
        moves = scramble.split()
        
        for move in moves:
            Move.from_string(move)
            
        # Check for redundancies
        for i in range(1, len(moves)):
            if moves[i][0] == moves[i-1][0]:
                return False  # Same face twice in a row
                
        return True
        
    except:
        return False


def validate_scramble(scramble: str) -> bool:
    """Alias for is_valid_scramble"""
    return is_valid_scramble(scramble)


def commutator(sequence1: str, sequence2: str) -> str:
    """
    Create commutator [A, B] = A B A' B'
    
    Args:
        sequence1: First sequence (A)
        sequence2: Second sequence (B)
        
    Returns:
        Commutator sequence
    """
    seq1 = MoveSequence.from_string(sequence1)
    seq2 = MoveSequence.from_string(sequence2)
    
    result = MoveSequence()
    result.extend(seq1.moves)
    result.extend(seq2.moves)
    result.extend(seq1.inverse().moves)
    result.extend(seq2.inverse().moves)
    
    return str(result)


def conjugate(setup: str, algorithm: str) -> str:
    """
    Create conjugate A B A'
    
    Args:
        setup: Setup moves (A)
        algorithm: Algorithm (B)
        
    Returns:
        Conjugate sequence
    """
    setup_seq = MoveSequence.from_string(setup)
    algo_seq = MoveSequence.from_string(algorithm)
    
    result = MoveSequence()
    result.extend(setup_seq.moves)
    result.extend(algo_seq.moves)
    result.extend(setup_seq.inverse().moves)
    
    return str(result)


# Common algorithms
ALGORITHMS = {
    # PLL algorithms
    'T_perm': "R U R' U' R' F R2 U' R' U' R U R' F'",
    'Y_perm': "F R U' R' U' R U R' F' R U R' U' R' F R F'",
    'U_perm_a': "R U' R U R U R U' R' U' R2",
    'U_perm_b': "R2 U R U R' U' R' U' R' U R'",
    'H_perm': "M2 U M2 U2 M2 U M2",
    'Z_perm': "M2 U M2 U M' U2 M2 U2 M'",
    
    # OLL algorithms
    'sune': "R U R' U R U2 R'",
    'antisune': "R U2 R' U' R U' R'",
    
    # F2L triggers
    'sexy_move': "R U R' U'",
    'sledgehammer': "R' F R F'",
    
    # Basic patterns
    'checkerboard': "M2 E2 S2",
    'cube_in_cube': "F L F U' R U F2 L2 U' L' B D' B' L2 U",
}


def apply_algorithm(cube_state: str, algorithm_name: str) -> str:
    """
    Apply a named algorithm to cube state
    
    Args:
        cube_state: Current cube state
        algorithm_name: Name of algorithm
        
    Returns:
        New cube state
    """
    if algorithm_name not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: {algorithm_name}")
        
    from .cube_model import CubeModel
    
    cube = CubeModel()
    cube.from_string(cube_state)
    cube.apply_sequence(ALGORITHMS[algorithm_name])
    
    return cube.to_string()