#!/usr/bin/env python3
"""
Rubik's Cube Debugger - Helps diagnose and fix scanned cube configurations
"""

import sys
import json
import numpy as np
from collections import Counter

# Valid cube constraints
VALID_EDGES = {
    frozenset({'white', 'green'}), frozenset({'white', 'red'}),
    frozenset({'white', 'blue'}), frozenset({'white', 'orange'}),
    frozenset({'yellow', 'green'}), frozenset({'yellow', 'red'}),
    frozenset({'yellow', 'blue'}), frozenset({'yellow', 'orange'}),
    frozenset({'green', 'red'}), frozenset({'green', 'orange'}),
    frozenset({'blue', 'red'}), frozenset({'blue', 'orange'})
}

VALID_CORNERS = {
    frozenset({'white', 'red', 'green'}), frozenset({'white', 'red', 'blue'}),
    frozenset({'white', 'orange', 'blue'}), frozenset({'white', 'orange', 'green'}),
    frozenset({'yellow', 'green', 'orange'}), frozenset({'yellow', 'green', 'red'}),
    frozenset({'yellow', 'red', 'blue'}), frozenset({'yellow', 'orange', 'blue'})
}


def load_test_cube():
    """Load a test cube configuration"""
    # Based on your output, reconstructing the scanned faces
    return {
        'white': [
            ['white', 'red', 'green'],
            ['white', 'white', 'yellow'],
            ['orange', 'white', 'white']
        ],
        'yellow': [
            ['blue', 'green', 'green'],
            ['orange', 'yellow', 'red'],
            ['orange', 'blue', 'blue']
        ],
        'green': [
            ['orange', 'blue', 'yellow'],
            ['yellow', 'green', 'green'],
            ['white', 'green', 'green']
        ],
        'blue': [
            ['white', 'green', 'red'],
            ['blue', 'blue', 'yellow'],
            ['red', 'red', 'red']
        ],
        'red': [
            ['red', 'orange', 'yellow'],
            ['orange', 'red', 'orange'],
            ['blue', 'yellow', 'orange']
        ],
        'orange': [
            ['green', 'yellow', 'red'],
            ['white', 'orange', 'blue'],
            ['white', 'white', 'yellow']
        ]
    }


def analyze_cube(cube_dict):
    """Comprehensive cube analysis"""
    print("\n" + "="*60)
    print("                CUBE ANALYSIS REPORT")
    print("="*60)
    
    # 1. Color distribution
    print("\n1. COLOR DISTRIBUTION:")
    print("-" * 30)
    color_counts = Counter()
    for face_name, face in cube_dict.items():
        for row in face:
            for color in row:
                color_counts[color] += 1
    
    for color in ['white', 'yellow', 'red', 'orange', 'green', 'blue']:
        count = color_counts[color]
        status = "✅" if count == 9 else "❌"
        print(f"  {color:8s}: {count:2d}/9 {status}")
    
    # 2. Center analysis
    print("\n2. CENTER STICKERS:")
    print("-" * 30)
    centers = {}
    for face_name, face in cube_dict.items():
        center = face[1][1]
        centers[face_name] = center
        correct = "✅" if center == face_name else "❌"
        print(f"  {face_name:8s} face center: {center:8s} {correct}")
    
    # 3. Edge analysis
    print("\n3. EDGE PIECES:")
    print("-" * 30)
    edges = extract_edges(cube_dict)
    edge_counts = Counter(edges)
    
    valid_count = 0
    invalid_edges = []
    duplicate_edges = []
    
    for edge, count in edge_counts.items():
        if edge in VALID_EDGES:
            if count == 1:
                valid_count += 1
            else:
                duplicate_edges.append((edge, count))
        else:
            invalid_edges.append(edge)
    
    print(f"  Valid edges: {valid_count}/12")
    if duplicate_edges:
        print("  Duplicates:")
        for edge, count in duplicate_edges:
            print(f"    {set(edge)} appears {count} times")
    if invalid_edges:
        print("  Invalid combinations:")
        for edge in invalid_edges:
            print(f"    {set(edge)}")
    
    # 4. Corner analysis
    print("\n4. CORNER PIECES:")
    print("-" * 30)
    corners = extract_corners(cube_dict)
    valid_corners = [c for c in corners if c in VALID_CORNERS]
    invalid_corners = [c for c in corners if c not in VALID_CORNERS]
    
    print(f"  Valid corners: {len(valid_corners)}/8")
    if invalid_corners:
        print("  Invalid combinations:")
        for corner in invalid_corners:
            print(f"    {set(corner)}")
    
    # 5. Suggested fixes
    print("\n5. SUGGESTED FIXES:")
    print("-" * 30)
    suggest_fixes(cube_dict, color_counts)
    
    print("\n" + "="*60)


def extract_edges(cube):
    """Extract all 12 edges from cube"""
    u = cube['white']
    d = cube['yellow']
    f = cube['green']
    b = cube['blue']
    r = cube['red']
    l = cube['orange']
    
    edges = [
        frozenset([u[2][1], f[0][1]]),  # UF
        frozenset([u[1][2], r[0][1]]),  # UR
        frozenset([u[0][1], b[0][1]]),  # UB
        frozenset([u[1][0], l[0][1]]),  # UL
        frozenset([d[0][1], f[2][1]]),  # DF
        frozenset([d[1][2], r[2][1]]),  # DR
        frozenset([d[2][1], b[2][1]]),  # DB
        frozenset([d[1][0], l[2][1]]),  # DL
        frozenset([f[1][2], r[1][0]]),  # FR
        frozenset([f[1][0], l[1][2]]),  # FL
        frozenset([b[1][2], r[1][2]]),  # BR
        frozenset([b[1][0], l[1][0]]),  # BL
    ]
    return edges


def extract_corners(cube):
    """Extract all 8 corners from cube"""
    u = cube['white']
    d = cube['yellow']
    f = cube['green']
    b = cube['blue']
    r = cube['red']
    l = cube['orange']
    
    corners = [
        frozenset([u[2][2], f[0][2], r[0][0]]),  # UFR
        frozenset([u[0][2], r[0][2], b[0][0]]),  # URB
        frozenset([u[0][0], b[0][2], l[0][0]]),  # UBL
        frozenset([u[2][0], l[0][2], f[0][0]]),  # ULF
        frozenset([d[0][0], f[2][0], l[2][2]]),  # DFL
        frozenset([d[0][2], r[2][0], f[2][2]]),  # DFR
        frozenset([d[2][2], b[2][0], r[2][2]]),  # DRB
        frozenset([d[2][0], l[2][0], b[2][2]]),  # DBL
    ]
    return corners


def suggest_fixes(cube, color_counts):
    """Suggest potential fixes based on common issues"""
    
    # Check for color imbalances
    over_colors = [c for c, count in color_counts.items() if count > 9]
    under_colors = [c for c, count in color_counts.items() if count < 9]
    
    if over_colors and under_colors:
        print(f"  • Color imbalance detected:")
        print(f"    Too many: {over_colors}")
        print(f"    Too few: {under_colors}")
        print(f"    → Likely misidentification between these colors")
    
    # Check for wrong centers
    for face_name, face in cube.items():
        center = face[1][1]
        if center != face_name:
            print(f"  • Wrong center on {face_name} face (is {center})")
            print(f"    → Need to rotate or re-scan this face")
    
    # Common color confusion pairs
    confusion_pairs = [
        ('red', 'orange'),
        ('blue', 'green'),
        ('white', 'yellow')
    ]
    
    for c1, c2 in confusion_pairs:
        c1_count = color_counts[c1]
        c2_count = color_counts[c2]
        if abs(c1_count - 9) == abs(c2_count - 9) and c1_count != 9:
            print(f"  • Possible {c1}/{c2} confusion")
            print(f"    → Recalibrate these colors")


def try_auto_fix(cube):
    """Attempt automatic fixes"""
    print("\n6. ATTEMPTING AUTO-FIX:")
    print("-" * 30)
    
    fixed_cube = {}
    for face_name in cube:
        fixed_cube[face_name] = [row[:] for row in cube[face_name]]
    
    # Fix 1: Ensure centers are correct
    for face_name in fixed_cube:
        fixed_cube[face_name][1][1] = face_name
        print(f"  Fixed center of {face_name} face")
    
    # Fix 2: Try to balance colors
    color_counts = Counter()
    positions = []
    
    for face_name, face in fixed_cube.items():
        for i in range(3):
            for j in range(3):
                if not (i == 1 and j == 1):  # Skip centers
                    color = face[i][j]
                    color_counts[color] += 1
                    positions.append((face_name, i, j, color))
    
    # Find swappable positions
    over_colors = [(c, count) for c, count in color_counts.items() if count > 8]
    under_colors = [(c, count) for c, count in color_counts.items() if count < 8]
    
    if over_colors and under_colors:
        print(f"  Attempting color swaps...")
        # This is a simplified fix - real implementation would be more sophisticated
        for over_c, over_count in over_colors:
            for under_c, under_count in under_colors:
                swaps_needed = min(over_count - 8, 8 - under_count)
                swapped = 0
                
                for face_name, i, j, color in positions:
                    if color == over_c and swapped < swaps_needed:
                        fixed_cube[face_name][i][j] = under_c
                        swapped += 1
                
                if swapped > 0:
                    print(f"    Swapped {swapped} {over_c} → {under_c}")
    
    return fixed_cube


def cube_to_string(cube, order=['white', 'red', 'green', 'yellow', 'orange', 'blue']):
    """Convert cube to Kociemba string format"""
    color_map = {
        'white': 'w', 'yellow': 'y', 'green': 'g',
        'blue': 'b', 'red': 'r', 'orange': 'o'
    }
    
    result = []
    for face_name in order:
        for row in cube[face_name]:
            for color in row:
                result.append(color_map.get(color, 'w'))
    
    return ''.join(result)


def main():
    print("🔍 RUBIK'S CUBE DEBUGGER")
    print("This tool helps diagnose and fix cube scanning issues")
    
    # Load test cube
    cube = load_test_cube()
    
    # Analyze original
    print("\n📋 ANALYZING SCANNED CUBE...")
    analyze_cube(cube)
    
    # Try auto-fix
    fixed = try_auto_fix(cube)
    
    print("\n📋 ANALYZING FIXED CUBE...")
    analyze_cube(fixed)
    
    # Generate cube strings
    original_string = cube_to_string(cube)
    fixed_string = cube_to_string(fixed)
    
    print("\n7. CUBE STRINGS:")
    print("-" * 30)
    print(f"  Original: {original_string}")
    print(f"  Fixed:    {fixed_string}")
    
    # Validate strings
    print("\n8. STRING VALIDATION:")
    print("-" * 30)
    for s, label in [(original_string, "Original"), (fixed_string, "Fixed")]:
        print(f"  {label}:")
        valid = True
        for c in 'wygbro':
            count = s.count(c)
            if count != 9:
                print(f"    {c}: {count}/9 ❌")
                valid = False
        if valid:
            print(f"    All colors correct! ✅")


if __name__ == "__main__":
    main()