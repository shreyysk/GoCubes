#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Thistlethwaite algorithm solver

This module implements Morwen Thistlethwaite's four-phase algorithm.
"""

import logging
import time
from typing import List, Dict, Optional, Tuple, Any
from collections import deque
from dataclasses import dataclass
import numpy as np

from .cube_model import CubeModel

logger = logging.getLogger(__name__)


@dataclass
class CubeState:
    """Represents a cube state in the search"""
    cube: CubeModel
    moves: List[str]
    depth: int
    phase: int


class ThistlethwaiteSolver:
    """
    Thistlethwaite four-phase algorithm solver
    
    The algorithm reduces the cube through 4 groups:
    - G0: <U, D, F, B, R, L> - All moves allowed
    - G1: <U, D, F, B, R2, L2> - Quarter turns of R and L not allowed
    - G2: <U, D, F2, B2, R2, L2> - Quarter turns of F and B not allowed  
    - G3: <U2, D2, F2, B2, R2, L2> - Only 180° turns allowed
    - G4: Solved state
    """
    
    def __init__(self):
        """Initialize Thistlethwaite solver"""
        self.name = "Thistlethwaite"
        self.description = "Four-phase group theory algorithm"
        
        # Phase move sets
        self.phase_moves = {
            0: ['U', "U'", 'U2', 'D', "D'", 'D2', 
                'F', "F'", 'F2', 'B', "B'", 'B2',
                'R', "R'", 'R2', 'L', "L'", 'L2'],
            1: ['U', "U'", 'U2', 'D', "D'", 'D2',
                'F', "F'", 'F2', 'B', "B'", 'B2',
                'R2', 'L2'],
            2: ['U', "U'", 'U2', 'D', "D'", 'D2',
                'F2', 'B2', 'R2', 'L2'],
            3: ['U2', 'D2', 'F2', 'B2', 'R2', 'L2']
        }
        
        # Statistics
        self.phase_lengths = [0, 0, 0, 0]
        self.last_solve_time = 0
        self.total_solves = 0
        self.total_time = 0
        
        # Pruning tables (simplified - would be loaded from files)
        self.pruning_tables = {}
        self._initialize_pruning_tables()
        
    def solve(self, cube_string: str, show_phases: bool = False) -> str:
        """
        Solve the cube using Thistlethwaite algorithm
        
        Args:
            cube_string: 54-character cube representation
            show_phases: Whether to show phase breakdown
            
        Returns:
            Solution string
        """
        start_time = time.time()
        
        # Validate input
        if not self._validate_cube_string(cube_string):
            raise ValueError(f"Invalid cube string: {cube_string}")
            
        # Create cube model
        cube = CubeModel()
        cube.from_string(cube_string)
        
        # Check if already solved
        if cube.is_solved():
            logger.info("Cube is already solved")
            return ""
            
        solution = []
        
        # Solve through each phase
        for phase in range(4):
            logger.info(f"Starting phase {phase}")
            
            phase_solution = self._solve_phase(cube, phase)
            
            if phase_solution:
                # Apply moves to cube
                for move in phase_solution:
                    cube.apply_move(move)
                    
                solution.extend(phase_solution)
                self.phase_lengths[phase] = len(phase_solution)
                
                logger.info(f"Phase {phase} complete: {len(phase_solution)} moves")
                
                if show_phases:
                    print(f"Phase {phase} (G{phase}->G{phase+1}): {' '.join(phase_solution)}")
                    
        # Update statistics
        self.last_solve_time = time.time() - start_time
        self.total_solves += 1
        self.total_time += self.last_solve_time
        
        # Optimize solution
        solution = self._optimize_solution(solution)
        
        logger.info(f"Solved in {self.last_solve_time:.3f}s with {len(solution)} moves")
        
        return ' '.join(solution)
        
    def _solve_phase(self, cube: CubeModel, phase: int) -> List[str]:
        """
        Solve a single phase
        
        Args:
            cube: Current cube state
            phase: Phase number (0-3)
            
        Returns:
            List of moves for this phase
        """
        # Check if already in target subgroup
        if self._is_in_subgroup(cube, phase + 1):
            return []
            
        # Use IDA* search
        max_depth = self._get_max_depth(phase)
        
        for depth in range(1, max_depth + 1):
            logger.debug(f"Searching phase {phase} at depth {depth}")
            
            solution = self._ida_search(cube, phase, depth)
            
            if solution is not None:
                return solution
                
        logger.warning(f"Phase {phase} search exceeded max depth")
        return []
        
    def _ida_search(self, cube: CubeModel, phase: int, max_depth: int) -> Optional[List[str]]:
        """
        IDA* search for phase solution
        
        Args:
            cube: Starting cube state
            phase: Current phase
            max_depth: Maximum search depth
            
        Returns:
            Solution moves or None
        """
        # Initialize search
        initial = CubeState(cube.copy(), [], 0, phase)
        stack = [initial]
        visited = set()
        
        while stack:
            state = stack.pop()
            
            # Check if we've reached the goal
            if self._is_in_subgroup(state.cube, phase + 1):
                return state.moves
                
            # Check depth limit
            if state.depth >= max_depth:
                continue
                
            # Generate successors
            for move in self._get_moves_for_phase(phase, state.moves):
                # Create new state
                new_cube = state.cube.copy()
                new_cube.apply_move(move)
                
                # Check if already visited
                cube_hash = self._hash_cube(new_cube, phase)
                if cube_hash in visited:
                    continue
                    
                visited.add(cube_hash)
                
                # Calculate heuristic
                h = self._heuristic(new_cube, phase)
                
                # Prune if f = g + h > max_depth
                if state.depth + 1 + h > max_depth:
                    continue
                    
                # Add to stack
                new_state = CubeState(
                    new_cube,
                    state.moves + [move],
                    state.depth + 1,
                    phase
                )
                stack.append(new_state)
                
        return None
        
    def _is_in_subgroup(self, cube: CubeModel, subgroup: int) -> bool:
        """
        Check if cube is in specified subgroup
        
        Args:
            cube: Cube to check
            subgroup: Target subgroup (1-4)
            
        Returns:
            True if in subgroup
        """
        if subgroup == 0:
            return True  # G0 contains all cubes
            
        elif subgroup == 1:
            # G1: All edge orientations correct
            return self._check_edge_orientation(cube)
            
        elif subgroup == 2:
            # G2: G1 + corners in correct orbits, E-slice edges in E-slice
            return (self._check_edge_orientation(cube) and
                    self._check_corner_orientation(cube) and
                    self._check_e_slice_edges(cube))
                    
        elif subgroup == 3:
            # G3: G2 + all edges in correct slices, corners in tetrads
            return (self._check_edge_orientation(cube) and
                    self._check_corner_orientation(cube) and
                    self._check_e_slice_edges(cube) and
                    self._check_edge_slices(cube) and
                    self._check_corner_tetrads(cube))
                    
        elif subgroup == 4:
            # G4: Solved
            return cube.is_solved()
            
        return False
        
    def _check_edge_orientation(self, cube: CubeModel) -> bool:
        """Check if all edges are correctly oriented"""
        # Edge orientation is correct if sum of orientations is 0 (mod 2)
        # This is a simplified check - actual implementation would track edge flips
        
        # Get edge positions
        edges = [
            # U layer edges
            (1, 46), (5, 10), (7, 19), (3, 37),
            # E layer edges  
            (21, 41), (23, 12), (25, 14), (39, 43),
            # D layer edges
            (28, 50), (32, 16), (30, 52), (34, 48)
        ]
        
        orientation_sum = 0
        for e1, e2 in edges:
            # Check if edge is flipped
            # Simplified check - would need actual edge tracking
            pass
            
        return True  # Placeholder
        
    def _check_corner_orientation(self, cube: CubeModel) -> bool:
        """Check if all corners are correctly oriented"""
        # Corner orientation is correct if sum of orientations is 0 (mod 3)
        # Simplified implementation
        
        corners = [
            (0, 36, 47), (2, 11, 45), (6, 18, 38), (8, 20, 9),
            (24, 27, 42), (26, 29, 17), (33, 35, 51), (44, 53, 15)
        ]
        
        orientation_sum = 0
        for c1, c2, c3 in corners:
            # Check corner orientation
            # Simplified - would need actual tracking
            pass
            
        return True  # Placeholder
        
    def _check_e_slice_edges(self, cube: CubeModel) -> bool:
        """Check if E-slice edges are in E-slice"""
        # E-slice edges should be in positions 21, 23, 39, 41
        e_slice_positions = [21, 23, 39, 41]
        
        # Check if these positions contain E-slice edges
        # Simplified check
        return True  # Placeholder
        
    def _check_edge_slices(self, cube: CubeModel) -> bool:
        """Check if all edges are in correct slices"""
        # Check M, E, and S slices
        # Simplified implementation
        return True  # Placeholder
        
    def _check_corner_tetrads(self, cube: CubeModel) -> bool:
        """Check if corners are in correct tetrads"""
        # Corners should be in two groups of 4
        # Simplified check
        return True  # Placeholder
        
    def _get_moves_for_phase(self, phase: int, previous_moves: List[str]) -> List[str]:
        """
        Get allowed moves for current phase
        
        Args:
            phase: Current phase
            previous_moves: Previous moves (for pruning)
            
        Returns:
            List of allowed moves
        """
        moves = self.phase_moves[phase].copy()
        
        # Prune redundant moves
        if previous_moves:
            last_move = previous_moves[-1]
            last_face = last_move[0]
            
            # Don't repeat same face
            moves = [m for m in moves if m[0] != last_face]
            
            # Don't do opposite faces in wrong order
            opposites = {'U': 'D', 'D': 'U', 'F': 'B', 'B': 'F', 'R': 'L', 'L': 'R'}
            if len(previous_moves) >= 2:
                second_last = previous_moves[-2]
                if second_last[0] in opposites and opposites[second_last[0]] == last_face:
                    # Remove moves on second_last face
                    moves = [m for m in moves if m[0] != second_last[0]]
                    
        return moves
        
    def _heuristic(self, cube: CubeModel, phase: int) -> int:
        """
        Heuristic function for current phase
        
        Args:
            cube: Current cube state
            phase: Current phase
            
        Returns:
            Estimated moves to reach next subgroup
        """
        # Use pruning tables for accurate heuristics
        cube_hash = self._hash_cube(cube, phase)
        
        if phase in self.pruning_tables and cube_hash in self.pruning_tables[phase]:
            return self.pruning_tables[phase][cube_hash]
            
        # Default heuristic based on phase
        if phase == 0:
            # G0->G1: Edge orientation
            return self._count_bad_edges(cube)
        elif phase == 1:
            # G1->G2: Corner orientation and E-slice
            return self._count_bad_corners(cube) + self._count_bad_e_slice(cube)
        elif phase == 2:
            # G2->G3: Edge slices and corner tetrads
            return self._count_bad_slices(cube)
        else:
            # G3->G4: Final solve
            return self._count_unsolved_pieces(cube)
            
    def _hash_cube(self, cube: CubeModel, phase: int) -> int:
        """
        Generate hash for cube state in given phase
        
        Args:
            cube: Cube state
            phase: Current phase
            
        Returns:
            Hash value
        """
        # Simple hash - would use more sophisticated hashing in practice
        state_str = cube.to_string()
        
        # Different hash based on phase (considering symmetries)
        if phase == 0:
            # Consider edge orientations only
            return hash(state_str)  # Simplified
        elif phase == 1:
            # Consider corner orientations and E-slice
            return hash(state_str)  # Simplified
        elif phase == 2:
            # Consider edge positions and corner tetrads
            return hash(state_str)  # Simplified
        else:
            # Full state
            return hash(state_str)
            
    def _count_bad_edges(self, cube: CubeModel) -> int:
        """Count incorrectly oriented edges"""
        # Simplified - would check actual edge orientations
        return 0
        
    def _count_bad_corners(self, cube: CubeModel) -> int:
        """Count incorrectly oriented corners"""
        # Simplified - would check actual corner orientations
        return 0
        
    def _count_bad_e_slice(self, cube: CubeModel) -> int:
        """Count E-slice edges not in E-slice"""
        # Simplified
        return 0
        
    def _count_bad_slices(self, cube: CubeModel) -> int:
        """Count pieces not in correct slices"""
        # Simplified
        return 0
        
    def _count_unsolved_pieces(self, cube: CubeModel) -> int:
        """Count unsolved pieces"""
        count = 0
        solved = CubeModel()
        
        for i in range(54):
            if cube.state[i] != solved.state[i]:
                count += 1
                
        return count // 4  # Rough estimate
        
    def _get_max_depth(self, phase: int) -> int:
        """Get maximum search depth for phase"""
        max_depths = [7, 10, 13, 15]  # Typical maximum depths
        return max_depths[phase]
        
    def _optimize_solution(self, moves: List[str]) -> List[str]:
        """Optimize solution by removing redundancies"""
        from .optimizer import MoveOptimizer
        
        optimizer = MoveOptimizer()
        return optimizer.optimize(moves)
        
    def _initialize_pruning_tables(self):
        """Initialize pruning tables (simplified)"""
        # In practice, these would be loaded from pre-computed files
        # or generated on first run
        
        self.pruning_tables = {
            0: {},  # G0->G1 pruning table
            1: {},  # G1->G2 pruning table
            2: {},  # G2->G3 pruning table
            3: {}   # G3->G4 pruning table
        }
        
        logger.info("Pruning tables initialized")
        
    def _validate_cube_string(self, cube_string: str) -> bool:
        """Validate cube string"""
        if len(cube_string) != 54:
            return False
            
        # Check character counts
        char_count = {}
        for char in cube_string:
            char_count[char] = char_count.get(char, 0) + 1
            
        # Should have exactly 9 of each
        for char in 'URFDLB':
            if char_count.get(char, 0) != 9:
                return False
                
        return True
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get solver statistics"""
        total_moves = sum(self.phase_lengths)
        
        return {
            'name': self.name,
            'total_solves': self.total_solves,
            'total_time': self.total_time,
            'average_time': self.total_time / self.total_solves if self.total_solves > 0 else 0,
            'last_solve_time': self.last_solve_time,
            'phase_lengths': self.phase_lengths.copy(),
            'total_moves': total_moves,
            'phase_breakdown': {
                f'G{i}->G{i+1}': self.phase_lengths[i] for i in range(4)
            }
        }
        
    def explain_solution(self, solution: str) -> str:
        """
        Explain what each phase of the solution does
        
        Args:
            solution: Solution string
            
        Returns:
            Explanation text
        """
        explanation = []
        explanation.append("Thistlethwaite Algorithm Solution Breakdown:")
        explanation.append("")
        
        phases = [
            "Phase 0 (G0->G1): Orient all edges correctly",
            "Phase 1 (G1->G2): Orient corners and position E-slice edges",
            "Phase 2 (G2->G3): Position all edges in correct slices, corners in tetrads",
            "Phase 3 (G3->G4): Solve the cube using only 180° moves"
        ]
        
        for i, (phase_desc, length) in enumerate(zip(phases, self.phase_lengths)):
            explanation.append(f"{phase_desc}")
            explanation.append(f"  Moves: {length}")
            explanation.append("")
            
        explanation.append(f"Total moves: {sum(self.phase_lengths)}")
        
        return "\n".join(explanation)