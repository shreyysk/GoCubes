#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Move sequence optimizer

This module optimizes move sequences by removing redundancies and combining moves.
"""

import logging
from typing import List, Dict, Tuple, Optional, Set
from collections import deque
import re

logger = logging.getLogger(__name__)


class MoveOptimizer:
    """Optimizes move sequences"""
    
    def __init__(self):
        """Initialize optimizer"""
        # Opposite face pairs
        self.opposites = {
            'U': 'D', 'D': 'U',
            'F': 'B', 'B': 'F',
            'R': 'L', 'L': 'R',
            'M': 'M', 'E': 'E', 'S': 'S',
            'x': 'x', 'y': 'y', 'z': 'z'
        }
        
        # Parallel faces (can be reordered)
        self.parallel_pairs = [
            ('U', 'D'), ('F', 'B'), ('R', 'L')
        ]
        
        # Face groups for wide moves
        self.wide_equivalents = {
            'u': ['U', "E'"], "u'": ["U'", 'E'], 'u2': ['U2', 'E2'],
            'd': ['D', 'E'], "d'": ["D'", "E'"], 'd2': ['D2', 'E2'],
            'r': ['R', "M'"], "r'": ["R'", 'M'], 'r2': ['R2', 'M2'],
            'l': ['L', 'M'], "l'": ["L'", "M'"], 'l2': ['L2', 'M2'],
            'f': ['F', 'S'], "f'": ["F'", "S'"], 'f2': ['F2', 'S2'],
            'b': ['B', "S'"], "b'": ["B'", 'S'], 'b2': ['B2', 'S2']
        }
        
    def optimize(self, moves: List[str]) -> List[str]:
        """
        Optimize a move sequence
        
        Args:
            moves: List of moves
            
        Returns:
            Optimized move list
        """
        if not moves:
            return []
            
        # Apply multiple optimization passes
        optimized = moves.copy()
        
        # Keep optimizing until no more changes
        changed = True
        passes = 0
        max_passes = 10
        
        while changed and passes < max_passes:
            original_length = len(optimized)
            
            # Apply optimization techniques
            optimized = self._combine_same_face(optimized)
            optimized = self._cancel_opposites(optimized)
            optimized = self._reorder_parallel(optimized)
            optimized = self._simplify_wide_moves(optimized)
            optimized = self._remove_redundant_rotations(optimized)
            
            changed = len(optimized) < original_length
            passes += 1
            
        logger.debug(f"Optimized {len(moves)} moves to {len(optimized)} in {passes} passes")
        
        return optimized
        
    def _combine_same_face(self, moves: List[str]) -> List[str]:
        """
        Combine consecutive moves on the same face
        
        Examples:
        - U U -> U2
        - U U' -> (removed)
        - U2 U -> U'
        - U2 U2 -> (removed)
        """
        if len(moves) < 2:
            return moves
            
        result = []
        i = 0
        
        while i < len(moves):
            if i == len(moves) - 1:
                result.append(moves[i])
                break
                
            current = self._parse_move(moves[i])
            next_move = self._parse_move(moves[i + 1])
            
            if current[0] == next_move[0]:  # Same face
                # Combine turns
                total_turns = (current[1] + next_move[1]) % 4
                
                if total_turns == 0:
                    # Moves cancel out
                    i += 2
                elif total_turns == 1:
                    result.append(current[0])
                    i += 2
                elif total_turns == 2:
                    result.append(current[0] + '2')
                    i += 2
                else:  # total_turns == 3
                    result.append(current[0] + "'")
                    i += 2
            else:
                result.append(moves[i])
                i += 1
                
        return result
        
    def _cancel_opposites(self, moves: List[str]) -> List[str]:
        """
        Cancel out inverse moves
        
        Example: R U R' U' R U' R' -> U' (after reordering)
        """
        result = []
        skip_next = False
        
        for i in range(len(moves)):
            if skip_next:
                skip_next = False
                continue
                
            if i < len(moves) - 1:
                current = moves[i]
                next_move = moves[i + 1]
                
                if self._are_inverse(current, next_move):
                    skip_next = True
                    continue
                    
            result.append(moves[i])
            
        return result
        
    def _reorder_parallel(self, moves: List[str]) -> List[str]:
        """
        Reorder parallel face moves for better optimization
        
        Example: R U L U' -> R L U U' -> R L (after cancellation)
        """
        if len(moves) < 2:
            return moves
            
        result = []
        i = 0
        
        while i < len(moves):
            if i >= len(moves) - 1:
                result.append(moves[i])
                i += 1
                continue
                
            current = self._parse_move(moves[i])
            
            # Look ahead for parallel moves
            j = i + 1
            while j < len(moves) and j < i + 4:  # Look ahead up to 3 moves
                next_move = self._parse_move(moves[j])
                
                if self._are_parallel(current[0], next_move[0]):
                    # Can reorder these moves
                    # Check if reordering helps
                    if self._should_reorder(moves[i:j+1]):
                        # Swap moves
                        result.append(moves[j])
                        result.extend(moves[i:j])
                        i = j + 1
                        break
                elif current[0] == next_move[0]:
                    # Same face, stop looking
                    break
                    
                j += 1
            else:
                result.append(moves[i])
                i += 1
                
        return result
        
    def _simplify_wide_moves(self, moves: List[str]) -> List[str]:
        """
        Simplify wide move combinations
        
        Example: R M' -> r
        """
        result = []
        i = 0
        
        while i < len(moves):
            if i >= len(moves) - 1:
                result.append(moves[i])
                i += 1
                continue
                
            # Check for wide move patterns
            combined = self._try_combine_to_wide(moves[i], moves[i + 1])
            
            if combined:
                result.append(combined)
                i += 2
            else:
                result.append(moves[i])
                i += 1
                
        return result
        
    def _remove_redundant_rotations(self, moves: List[str]) -> List[str]:
        """
        Remove redundant cube rotations
        
        Example: x x' -> (removed)
        """
        result = []
        
        for i, move in enumerate(moves):
            if i < len(moves) - 1:
                if self._are_inverse(move, moves[i + 1]):
                    if move[0] in 'xyz':
                        # Skip both rotation and its inverse
                        continue
                        
            result.append(move)
            
        return result
        
    def _parse_move(self, move: str) -> Tuple[str, int]:
        """
        Parse move into face and turn count
        
        Args:
            move: Move string
            
        Returns:
            Tuple of (face, turns)
        """
        if not move:
            return '', 0
            
        face = move[0]
        
        if len(move) == 1:
            turns = 1
        elif move[-1] == '2':
            turns = 2
        elif move[-1] == "'":
            turns = 3
        else:
            turns = 1
            
        return face, turns
        
    def _are_inverse(self, move1: str, move2: str) -> bool:
        """Check if two moves are inverses"""
        p1 = self._parse_move(move1)
        p2 = self._parse_move(move2)
        
        if p1[0] != p2[0]:
            return False
            
        # Check if turns sum to 4 (full rotation)
        return (p1[1] + p2[1]) % 4 == 0 and p1[1] != 2  # U2 U2 should combine, not cancel
        
    def _are_parallel(self, face1: str, face2: str) -> bool:
        """Check if two faces are parallel (opposite)"""
        return self.opposites.get(face1) == face2
        
    def _should_reorder(self, moves: List[str]) -> bool:
        """
        Determine if reordering moves would be beneficial
        
        Args:
            moves: Subsequence of moves to consider
            
        Returns:
            True if reordering would help optimization
        """
        if len(moves) < 2:
            return False
            
        # Simple heuristic: reorder if it brings same faces together
        faces = [self._parse_move(m)[0] for m in moves]
        
        # Count same face pairs after reordering
        original_pairs = sum(1 for i in range(len(faces)-1) if faces[i] == faces[i+1])
        
        # Simulate reordering (move last to second position)
        reordered = faces[:1] + faces[-1:] + faces[1:-1]
        reordered_pairs = sum(1 for i in range(len(reordered)-1) 
                             if reordered[i] == reordered[i+1])
        
        return reordered_pairs > original_pairs
        
    def _try_combine_to_wide(self, move1: str, move2: str) -> Optional[str]:
        """
        Try to combine two moves into a wide move
        
        Args:
            move1: First move
            move2: Second move
            
        Returns:
            Combined wide move or None
        """
        # Check for patterns like R M' -> r
        patterns = {
            ('R', "M'"): 'r',
            ("R'", 'M'): "r'",
            ('R2', 'M2'): 'r2',
            ('L', 'M'): 'l',
            ("L'", "M'"): "l'",
            ('L2', 'M2'): 'l2',
            ('U', "E'"): 'u',
            ("U'", 'E'): "u'",
            ('U2', 'E2'): 'u2',
            ('D', 'E'): 'd',
            ("D'", "E'"): "d'",
            ('D2', 'E2'): 'd2',
            ('F', 'S'): 'f',
            ("F'", "S'"): "f'",
            ('F2', 'S2'): 'f2',
            ('B', "S'"): 'b',
            ("B'", 'S'): "b'",
            ('B2', 'S2'): 'b2',
        }
        
        return patterns.get((move1, move2))
        
    def optimize_for_speed(self, moves: List[str]) -> List[str]:
        """
        Optimize for execution speed (finger tricks)
        
        Args:
            moves: Move list
            
        Returns:
            Speed-optimized moves
        """
        # Prefer certain move combinations for finger tricks
        result = moves.copy()
        
        # Replace slow patterns with faster ones
        speed_replacements = {
            "F R U' R' U' R U R' F'": "F (R U R' U')3 F'",  # Triple sexy
            "R' F R F'": "R' F R F'",  # Sledgehammer (already good)
            "R U R' U'": "R U R' U'",  # Sexy move (already good)
        }
        
        # This would require pattern matching in the sequence
        # Simplified implementation
        
        return result
        
    def optimize_for_moves(self, moves: List[str]) -> List[str]:
        """
        Optimize for minimum move count
        
        Args:
            moves: Move list
            
        Returns:
            Move-count optimized sequence
        """
        # Try all optimization techniques aggressively
        optimized = moves.copy()
        
        # Apply all optimizations multiple times
        for _ in range(5):
            prev_length = len(optimized)
            
            optimized = self._combine_same_face(optimized)
            optimized = self._cancel_opposites(optimized)
            optimized = self._reorder_parallel(optimized)
            optimized = self._simplify_wide_moves(optimized)
            optimized = self._remove_redundant_rotations(optimized)
            optimized = self._merge_slices(optimized)
            
            if len(optimized) == prev_length:
                break
                
        return optimized
        
    def _merge_slices(self, moves: List[str]) -> List[str]:
        """
        Merge slice moves where possible
        
        Example: M M -> M2
        """
        if len(moves) < 2:
            return moves
            
        result = []
        i = 0
        
        while i < len(moves):
            if i >= len(moves) - 1:
                result.append(moves[i])
                i += 1
                continue
                
            current = self._parse_move(moves[i])
            next_move = self._parse_move(moves[i + 1])
            
            # Check if both are slice moves on same axis
            if current[0] in 'MES' and current[0] == next_move[0]:
                total_turns = (current[1] + next_move[1]) % 4
                
                if total_turns == 0:
                    i += 2  # Cancel out
                elif total_turns == 1:
                    result.append(current[0])
                    i += 2
                elif total_turns == 2:
                    result.append(current[0] + '2')
                    i += 2
                else:  # total_turns == 3
                    result.append(current[0] + "'")
                    i += 2
            else:
                result.append(moves[i])
                i += 1
                
        return result
        
    def analyze_efficiency(self, moves: List[str]) -> Dict[str, any]:
        """
        Analyze the efficiency of a move sequence
        
        Args:
            moves: Move list
            
        Returns:
            Efficiency metrics
        """
        metrics = {
            'original_length': len(moves),
            'optimized_length': 0,
            'reduction_percentage': 0,
            'same_face_sequences': 0,
            'parallel_moves': 0,
            'cancellable_pairs': 0,
            'finger_trick_friendly': 0,
            'regrips_needed': 0
        }
        
        # Optimize and compare
        optimized = self.optimize(moves)
        metrics['optimized_length'] = len(optimized)
        
        if len(moves) > 0:
            metrics['reduction_percentage'] = (
                (len(moves) - len(optimized)) / len(moves) * 100
            )
        
        # Count patterns
        for i in range(len(moves) - 1):
            current = self._parse_move(moves[i])
            next_move = self._parse_move(moves[i + 1])
            
            if current[0] == next_move[0]:
                metrics['same_face_sequences'] += 1
                
            if self._are_parallel(current[0], next_move[0]):
                metrics['parallel_moves'] += 1
                
            if self._are_inverse(moves[i], moves[i + 1]):
                metrics['cancellable_pairs'] += 1
                
        # Count finger-trick friendly patterns
        friendly_patterns = [
            "R U R' U'",  # Sexy move
            "R' F R F'",  # Sledgehammer
            "U R U' R'",  # Reverse sexy
            "R U2 R'",    # Common trigger
        ]
        
        sequence = ' '.join(moves)
        for pattern in friendly_patterns:
            metrics['finger_trick_friendly'] += sequence.count(pattern)
            
        # Estimate regrips (simplified)
        last_hand = None
        for move in moves:
            face = move[0]
            
            if face in 'RL':
                hand = 'right'
            elif face in 'L':
                hand = 'left'
            elif face in 'FM':
                hand = 'both'
            else:
                hand = last_hand
                
            if last_hand and hand != last_hand and hand != 'both':
                metrics['regrips_needed'] += 1
                
            last_hand = hand
            
        return metrics