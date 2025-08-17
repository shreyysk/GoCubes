#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kociemba two-phase algorithm solver

This module implements the Kociemba algorithm for solving Rubik's Cube.
"""
import logging
import time
from typing import Optional, Dict, List, Any

try:
    import kociemba
    KOCIEMBA_AVAILABLE = True
except ImportError:
    KOCIEMBA_AVAILABLE = False
    logging.warning("Kociemba module not installed. Install with: pip install kociemba")

logger = logging.getLogger(__name__)


class KociembaSolver:
    """
    Kociemba two-phase algorithm solver. This class serves as a wrapper
    for the 'kociemba' library, providing a consistent interface for the application.
    """
    
    def __init__(self):
        """Initialize Kociemba solver."""
        if not KOCIEMBA_AVAILABLE:
            raise ImportError("The 'kociemba' library is required for this solver. Please run 'pip install kociemba'.")
            
        self.name = "Kociemba"
        self.description = "Two-phase algorithm (optimal for 20 moves or less)"
        
        # Statistics
        self.last_solve_time = 0
        self.total_solves = 0
        self.total_time = 0
        
    def solve(self, cube_string: str) -> str:
        """
        Solve the cube using the Kociemba algorithm.
        
        Args:
            cube_string: A 54-character string representing the cube's state,
                         using face initials (U, R, F, D, L, B).
            
        Returns:
            A solution string with space-separated moves.
            
        Raises:
            RuntimeError: If the solving process fails.
        """
        start_time = time.time()
        
        try:
            # The kociemba library solves the cube from the given state to the solved state.
            solution = kociemba.solve(cube_string)
            
            # Update statistics
            self.last_solve_time = time.time() - start_time
            self.total_solves += 1
            self.total_time += self.last_solve_time
            
            logger.info(f"Solved in {self.last_solve_time:.3f}s with {len(solution.split())} moves")
            
            return solution
            
        except Exception as e:
            logger.error(f"Kociemba solve failed: {e}")
            # The library raises an exception for unsolvable states.
            raise ValueError(f"The provided cube state is unsolvable. Error: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get solver statistics."""
        stats = {
            'name': self.name,
            'total_solves': self.total_solves,
            'total_time': self.total_time,
            'average_time': self.total_time / self.total_solves if self.total_solves > 0 else 0,
            'last_solve_time': self.last_solve_time,
        }
        return stats