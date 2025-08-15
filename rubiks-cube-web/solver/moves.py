"""
This module handles move notation, sequences, and transformations.
"""

import random

def generate_scramble(length=20):
    """
    Generates a random, valid scramble of a given length.
    Ensures that no move is the same as the previous move.
    """
    moves = ["U", "D", "L", "R", "F", "B"]
    modifiers = ["", "'", "2"]
    scramble = []
    last_move = None
    
    while len(scramble) < length:
        move = random.choice(moves)
        if move == last_move:
            continue
        
        # Avoid redundant move sequences like L R L
        if len(scramble) > 1 and move == scramble[-2] and moves.index(last_move) // 2 == moves.index(move) // 2:
            continue

        modifier = random.choice(modifiers)
        scramble.append(move + modifier)
        last_move = move
        
    return " ".join(scramble)

def simplify_moves(moves):
    """
    Simplifies a list of moves by cancelling out redundant turns.
    Example: ["U", "U"] -> ["U2"], ["U", "U'"] -> []
    """
    if not moves:
        return []

    # This is a basic simplifier. A more advanced one would be needed for complex commutators.
    simplified = []
    i = 0
    while i < len(moves):
        move = moves[i]
        if i + 1 < len(moves) and moves[i+1][0] == move[0]:
            # Combine or cancel with the next move
            m1 = move
            m2 = moves[i+1]
            
            val1 = 1 if len(m1) == 1 else (2 if m1[1] == '2' else 3)
            val2 = 1 if len(m2) == 1 else (2 if m2[1] == '2' else 3)
            
            total = (val1 + val2) % 4
            
            if total == 1: simplified.append(move[0])
            elif total == 2: simplified.append(move[0] + "2")
            elif total == 3: simplified.append(move[0] + "'")
            # if total is 0, they cancel, so we add nothing.
            
            i += 2 # Skip the next move
        else:
            simplified.append(move)
            i += 1
    
    return simplified