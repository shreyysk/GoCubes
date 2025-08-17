#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Helper utilities for the Rubik's Cube solver
"""

from typing import List, Dict

def calculate_move_metrics(moves: List[str]) -> Dict[str, int]:
    """
    Calculate various metrics for a move sequence
    
    Args:
        moves: List of move notations
        
    Returns:
        Dictionary with metrics (htm, qtm, stm, rotations)
    """
    metrics = {
        'htm': 0,      # Half Turn Metric
        'qtm': 0,      # Quarter Turn Metric  
        'stm': 0,      # Slice Turn Metric
        'rotations': 0  # Cube rotations
    }
    
    for move in moves:
        if not move:
            continue
            
        # HTM: Every move counts as 1
        metrics['htm'] += 1
        
        # Parse move
        face = move[0].upper()
        
        # QTM: Count quarter turns
        if move.endswith('2'):
            metrics['qtm'] += 2
        else:
            metrics['qtm'] += 1
            
        # STM: Slice moves count differently
        if face in 'MES':
            metrics['stm'] += 2
        elif face.islower():  # Wide moves
            metrics['stm'] += 1
        else:
            metrics['stm'] += 1
            
        # Count rotations
        if face in 'XYZ':
            metrics['rotations'] += 1
            
    return metrics