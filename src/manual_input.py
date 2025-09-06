#!/usr/bin/env python3
"""
Manual Rubik's Cube Input Tool
For when automatic scanning fails
"""

import sys
from rubik_solver import utils

def get_face_colors(face_name):
    """Get colors for a single face"""
    color_map = {
        'w': 'white', 'y': 'yellow', 
        'r': 'red', 'o': 'orange',
        'g': 'green', 'b': 'blue'
    }
    
    print(f"\nEnter {face_name.upper()} face:")
    print("Use: w=white, y=yellow, r=red, o=orange, g=green, b=blue")
    print("Enter 9 characters (3 rows of 3), e.g.: 'wwwwwwwww' for all white")
    print(f"Note: Center must be {face_name[0]}")
    
    while True:
        face_str = input(f"{face_name}: ").lower().strip()
        
        # Validate input
        if len(face_str) != 9:
            print(f"❌ Need exactly 9 characters, got {len(face_str)}")
            continue
        
        if not all(c in 'wyrogb' for c in face_str):
            print("❌ Invalid characters. Use only: w y r o g b")
            continue
        
        # Check center
        center = face_str[4]
        expected = face_name[0]
        if center != expected:
            print(f"❌ Center must be '{expected}' for {face_name} face, got '{center}'")
            continue
        
        # Display the face
        print("\nYou entered:")
        for i in range(3):
            row = face_str[i*3:(i+1)*3]
            print("  " + " ".join(color_map[c][:3].upper() for c in row))
        
        confirm = input("Correct? (y/n): ").lower()
        if confirm == 'y':
            return face_str
        print("Let's try again...")


def validate_cube_string(cube_str):
    """Validate the complete cube string"""
    print("\n" + "="*40)
    print("VALIDATION:")
    
    # Check length
    if len(cube_str) != 54:
        print(f"❌ Wrong length: {len(cube_str)} (should be 54)")
        return False
    
    # Check color counts
    valid = True
    for color in 'wyrogb':
        count = cube_str.count(color)
        status = "✅" if count == 9 else "❌"
        color_name = {
            'w': 'white', 'y': 'yellow', 'r': 'red',
            'o': 'orange', 'g': 'green', 'b': 'blue'
        }[color]
        print(f"  {color_name:7s}: {count}/9 {status}")
        if count != 9:
            valid = False
    
    print("="*40)
    return valid


def main():
    print("🎲 MANUAL RUBIK'S CUBE INPUT")
    print("="*40)
    print("\nThis tool helps you manually input your cube state")
    print("when automatic scanning doesn't work.\n")
    
    print("IMPORTANT: Hold your cube with:")
    print("  • WHITE on top (Up face)")
    print("  • GREEN facing you (Front face)")
    print("\nWe'll input faces in this order:")
    print("  1. Up (white)")
    print("  2. Right (red)")
    print("  3. Front (green)")
    print("  4. Down (yellow)")
    print("  5. Left (orange)")
    print("  6. Back (blue)")
    
    input("\nPress ENTER when ready...")
    
    # Get each face
    faces = []
    face_names = ['white', 'red', 'green', 'yellow', 'orange', 'blue']
    
    for i, name in enumerate(face_names):
        print(f"\n--- Face {i+1}/6 ---")
        face = get_face_colors(name)
        faces.append(face)
    
    # Combine into cube string
    cube_string = ''.join(faces)
    
    print("\n" + "="*40)
    print("COMPLETE CUBE STRING:")
    print(cube_string)
    
    # Validate
    if not validate_cube_string(cube_string):
        print("\n❌ Invalid cube configuration!")
        print("Please check your input and try again.")
        sys.exit(1)
    
    # Try to solve
    print("\n🧩 Attempting to solve...")
    try:
        solution = utils.solve(cube_string, 'Kociemba')
        print(f"\n✅ SOLUTION FOUND!")
        print(f"Moves: {solution}")
        print(f"Total steps: {len(solution.split())}")
        
        print("\n📝 How to execute:")
        print("Hold cube with WHITE on top, GREEN facing you")
        print("Then perform these moves:")
        
        moves = solution.split()
        for i, move in enumerate(moves, 1):
            print(f"  {i:2d}. {move}")
        
        # Save solution
        with open("solution.txt", "w") as f:
            f.write(f"Cube: {cube_string}\n")
            f.write(f"Solution: {solution}\n")
            f.write(f"Steps: {len(moves)}\n\n")
            f.write("Moves:\n")
            for i, move in enumerate(moves, 1):
                f.write(f"{i:2d}. {move}\n")
        
        print("\n✅ Solution saved to 'solution.txt'")
        
    except Exception as e:
        print(f"\n❌ SOLVE FAILED: {e}")
        print("\nPossible issues:")
        print("  1. Cube is in an impossible state")
        print("  2. Input errors (colors in wrong positions)")
        print("  3. Physical cube has been disassembled incorrectly")
        
        print("\nDebug info:")
        print(f"Cube string: {cube_string}")
        
        # Offer to save for debugging
        save = input("\nSave cube string for debugging? (y/n): ")
        if save.lower() == 'y':
            with open("failed_cube.txt", "w") as f:
                f.write(cube_string)
            print("Saved to 'failed_cube.txt'")


if __name__ == "__main__":
    main()