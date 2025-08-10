#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Solver module for Rubik Ultimate Solver

This module implements various solving algorithms for the Rubik's Cube.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import time

# Module metadata
__all__ = [
    'CubeSolver',
    'KociembaSolver',
    'ThistlethwaiteSolver',
    'CubeModel',
    'Move',
    'MoveSequence',
    'initialize_solver',
    'solve_cube',
    'validate_cube_string',
    'optimize_solution',
]

# Constants
SOLVED_STATE = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"

# Move definitions
BASIC_MOVES = ['U', 'D', 'F', 'B', 'R', 'L']
MOVE_OPPOSITES = {
    'U': 'D', 'D': 'U',
    'F': 'B', 'B': 'F',
    'R': 'L', 'L': 'R'
}

# Face indices
FACE_INDICES = {
    'U': list(range(0, 9)),
    'R': list(range(9, 18)),
    'F': list(range(18, 27)),
    'D': list(range(27, 36)),
    'L': list(range(36, 45)),
    'B': list(range(45, 54))
}

# Logger
logger = logging.getLogger(__name__)


class SolverError(Exception):
    """Base exception for solver module"""
    pass


class InvalidCubeError(SolverError):
    """Exception raised for invalid cube configurations"""
    pass


class SolveTimeoutError(SolverError):
    """Exception raised when solving times out"""
    pass


class Algorithm(Enum):
    """Solving algorithms"""
    KOCIEMBA = "kociemba"
    THISTLETHWAITE = "thistlethwaite"
    OPTIMAL = "optimal"
    BEGINNER = "beginner"
    CFOP = "cfop"
    ROUX = "roux"
    ZZ = "zz"


def initialize_solver():
    """Initialize the solver module"""
    logger.info("Initializing solver module")
    
    # Check for solver dependencies
    try:
        import kociemba
        logger.info("Kociemba solver available")
    except ImportError:
        logger.warning("Kociemba module not installed")
    
    # Initialize pruning tables if needed
    from solver.data.pruning_tables import initialize_tables
    initialize_tables()
    
    logger.info("Solver module initialized successfully")


def solve_cube(cube_string: str, algorithm: str = 'kociemba', **kwargs) -> Dict[str, Any]:
    """
    Solve a cube using specified algorithm
    
    Args:
        cube_string: 54-character string representation of cube
        algorithm: Algorithm to use
        **kwargs: Additional algorithm-specific parameters
        
    Returns:
        Dictionary containing solution and metadata
        
    Raises:
        InvalidCubeError: If cube string is invalid
        SolveTimeoutError: If solving times out
        SolverError: For other solving errors
    """
    # Validate cube string
    if not validate_cube_string(cube_string):
        raise InvalidCubeError(f"Invalid cube string: {cube_string}")
    
    # Check if already solved
    if cube_string == SOLVED_STATE:
        return {
            'solution': '',
            'moves': [],
            'move_count': 0,
            'time': 0.0,
            'algorithm': algorithm,
            'already_solved': True
        }
    
    start_time = time.time()
    
    # Select solver
    if algorithm == 'kociemba':
        from .kociemba_solver import KociembaSolver
        solver = KociembaSolver()
    elif algorithm == 'thistlethwaite':
        from .thistlethwaite import ThistlethwaiteSolver
        solver = ThistlethwaiteSolver()
    else:
        raise SolverError(f"Unknown algorithm: {algorithm}")
    
    # Solve
    try:
        solution = solver.solve(cube_string, **kwargs)
        
        # Parse solution
        moves = solution.strip().split() if solution else []
        
        result = {
            'solution': solution,
            'moves': moves,
            'move_count': len(moves),
            'time': time.time() - start_time,
            'algorithm': algorithm,
            'already_solved': False
        }
        
        # Add algorithm-specific data
        if hasattr(solver, 'get_statistics'):
            result['statistics'] = solver.get_statistics()
        
        logger.info(f"Cube solved with {algorithm}: {len(moves)} moves in {result['time']:.3f}s")
        return result
        
    except Exception as e:
        logger.error(f"Solving failed: {e}")
        raise SolverError(f"Failed to solve cube: {e}")


def validate_cube_string(cube_string: str) -> bool:
    """
    Validate a cube string representation
    
    Args:
        cube_string: 54-character string
        
    Returns:
        True if valid, False otherwise
    """
    # Check length
    if len(cube_string) != 54:
        return False
    
    # Check character counts
    char_count = {}
    for char in cube_string:
        char_count[char] = char_count.get(char, 0) + 1
    
    # Should have exactly 9 of each face
    valid_chars = set('URFDLB')
    for char in valid_chars:
        if char_count.get(char, 0) != 9:
            return False
    
    # Check for invalid characters
    if set(cube_string) != valid_chars:
        return False
    
    return True


def optimize_solution(moves: List[str]) -> List[str]:
    """
    Optimize a move sequence by removing redundancies
    
    Args:
        moves: List of moves
        
    Returns:
        Optimized move list
    """
    if not moves:
        return []
    
    from .optimizer import MoveOptimizer
    optimizer = MoveOptimizer()
    return optimizer.optimize(moves)


def parse_scramble(scramble: str) -> List[str]:
    """
    Parse a scramble string into move list
    
    Args:
        scramble: Scramble string
        
    Returns:
        List of moves
    """
    # Handle various formats
    scramble = scramble.strip()
    
    # Replace common variations
    scramble = scramble.replace("'", "'")
    scramble = scramble.replace("'", "'")
    scramble = scramble.replace("2", "2")
    
    # Split into moves
    moves = scramble.split()
    
    # Validate moves
    valid_moves = []
    for move in moves:
        if validate_move(move):
            valid_moves.append(normalize_move(move))
    
    return valid_moves


def validate_move(move: str) -> bool:
    """
    Validate a single move
    
    Args:
        move: Move string
        
    Returns:
        True if valid
    """
    if not move:
        return False
    
    # Check base move
    if move[0] not in 'URFDLB':
        return False
    
    # Check modifier
    if len(move) == 1:
        return True
    elif len(move) == 2:
        return move[1] in ["'", '2']
    else:
        return False


def normalize_move(move: str) -> str:
    """
    Normalize move notation
    
    Args:
        move: Move string
        
    Returns:
        Normalized move
    """
    if not move:
        return ""
    
    # Ensure proper apostrophe
    move = move.replace("'", "'")
    move = move.replace("'", "'")
    
    return move


def apply_move_to_string(cube_string: str, move: str) -> str:
    """
    Apply a move to a cube string
    
    Args:
        cube_string: Current cube state
        move: Move to apply
        
    Returns:
        New cube state
    """
    from .cube_model import CubeModel
    
    cube = CubeModel()
    cube.from_string(cube_string)
    cube.apply_move(move)
    
    return cube.to_string()


def apply_scramble_to_string(cube_string: str, scramble: str) -> str:
    """
    Apply a scramble to a cube string
    
    Args:
        cube_string: Current cube state
        scramble: Scramble string
        
    Returns:
        New cube state
    """
    moves = parse_scramble(scramble)
    
    for move in moves:
        cube_string = apply_move_to_string(cube_string, move)
    
    return cube_string


def get_cube_from_colors(faces: Dict[str, List[str]]) -> str:
    """
    Convert face colors to cube string
    
    Args:
        faces: Dictionary mapping face names to color lists
        
    Returns:
        54-character cube string
    """
    # Standard order: URFDLB
    face_order = ['U', 'R', 'F', 'D', 'L', 'B']
    
    cube_string = ""
    for face in face_order:
        if face in faces:
            cube_string += ''.join(faces[face])
    
    return cube_string


def get_move_count(solution: str) -> int:
    """
    Get move count from solution string
    
    Args:
        solution: Solution string
        
    Returns:
        Number of moves
    """
    if not solution:
        return 0
    
    moves = solution.strip().split()
    return len(moves)


def calculate_metrics(solution: str) -> Dict[str, int]:
    """
    Calculate various metrics for a solution
    
    Args:
        solution: Solution string
        
    Returns:
        Dictionary of metrics
    """
    moves = solution.strip().split() if solution else []
    
    metrics = {
        'htm': 0,  # Half Turn Metric
        'qtm': 0,  # Quarter Turn Metric
        'stm': 0,  # Slice Turn Metric
        'etm': 0,  # Execution Turn Metric
    }
    
    for move in moves:
        if not move:
            continue
        
        # HTM: All moves count as 1
        metrics['htm'] += 1
        
        # QTM: 180° moves count as 2
        if '2' in move:
            metrics['qtm'] += 2
        else:
            metrics['qtm'] += 1
        
        # STM: Slice moves count differently
        # (simplified - would need more complex logic)
        metrics['stm'] += 1
        
        # ETM: Execution time metric
        # (simplified - would need timing data)
        metrics['etm'] += 1
    
    return metrics


class SolverStatistics:
    """Statistics tracker for solving"""
    
    def __init__(self):
        self.total_solves = 0
        self.total_time = 0.0
        self.total_moves = 0
        self.algorithm_usage = {}
        self.solve_times = []
        self.move_counts = []
        
    def add_solve(self, algorithm: str, time: float, moves: int):
        """Add a solve to statistics"""
        self.total_solves += 1
        self.total_time += time
        self.total_moves += moves
        
        self.algorithm_usage[algorithm] = self.algorithm_usage.get(algorithm, 0) + 1
        self.solve_times.append(time)
        self.move_counts.append(moves)
        
    def get_average_time(self) -> float:
        """Get average solve time"""
        if self.total_solves == 0:
            return 0.0
        return self.total_time / self.total_solves
    
    def get_average_moves(self) -> float:
        """Get average move count"""
        if self.total_solves == 0:
            return 0.0
        return self.total_moves / self.total_solves
    
    def get_best_time(self) -> float:
        """Get best solve time"""
        if not self.solve_times:
            return 0.0
        return min(self.solve_times)
    
    def get_best_moves(self) -> int:
        """Get best move count"""
        if not self.move_counts:
            return 0
        return min(self.move_counts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_solves': self.total_solves,
            'total_time': self.total_time,
            'total_moves': self.total_moves,
            'average_time': self.get_average_time(),
            'average_moves': self.get_average_moves(),
            'best_time': self.get_best_time(),
            'best_moves': self.get_best_moves(),
            'algorithm_usage': self.algorithm_usage
        }


# Global statistics instance
statistics = SolverStatistics()


class CubeSolver:
    """Main solver interface"""
    
    def __init__(self):
        self.algorithms = {}
        self._load_algorithms()
        
    def _load_algorithms(self):
        """Load available algorithms"""
        try:
            from .kociemba_solver import KociembaSolver
            self.algorithms['kociemba'] = KociembaSolver
        except ImportError:
            logger.warning("Kociemba solver not available")
        
        try:
            from .thistlethwaite import ThistlethwaiteSolver
            self.algorithms['thistlethwaite'] = ThistlethwaiteSolver
        except ImportError:
            logger.warning("Thistlethwaite solver not available")
    
    def solve(self, cube_string: str, algorithm: str = 'kociemba', **kwargs) -> str:
        """
        Solve a cube
        
        Args:
            cube_string: Cube state string
            algorithm: Algorithm to use
            **kwargs: Algorithm-specific parameters
            
        Returns:
            Solution string
        """
        if algorithm not in self.algorithms:
            raise SolverError(f"Algorithm {algorithm} not available")
        
        solver_class = self.algorithms[algorithm]
        solver = solver_class()
        
        return solver.solve(cube_string, **kwargs)
    
    def solve_from_scramble(self, scramble: str, algorithm: str = 'kociemba', **kwargs) -> Dict[str, Any]:
        """
        Solve from a scramble
        
        Args:
            scramble: Scramble string
            algorithm: Algorithm to use
            **kwargs: Algorithm-specific parameters
            
        Returns:
            Solution dictionary
        """
        # Apply scramble to solved cube
        cube_string = apply_scramble_to_string(SOLVED_STATE, scramble)
        
        # Solve
        result = solve_cube(cube_string, algorithm, **kwargs)
        result['scramble'] = scramble
        
        return result
    
    def get_available_algorithms(self) -> List[str]:
        """Get list of available algorithms"""
        return list(self.algorithms.keys())


# Import main classes
try:
    from solver.cube_model import CubeModel
    from solver.kociemba_solver import KociembaSolver
    from solver.thistlethwaite import ThistlethwaiteSolver
    from solver.moves import Move, MoveSequence
    from solver.optimizer import MoveOptimizer
except ImportError:
    # Fallback to relative imports
    try:
        from .cube_model import CubeModel
        from .kociemba_solver import KociembaSolver
        from .thistlethwaite import ThistlethwaiteSolver
        from .moves import Move, MoveSequence
        from .optimizer import MoveOptimizer
    except ImportError as e:
        logger.error(f"Failed to import solver components: {e}")

logger.info("Solver module loaded")