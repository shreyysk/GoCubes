"""
Rubik's Cube solver using a beginner's layer-by-layer method.
"""

from typing import List, Tuple
from .cube import Cube, Color, Face
from .moves import simplify_moves

class CubeSolver:
    """
    Solves a 3x3x3 Rubik's cube using the layer-by-layer method.
    This is a complete and functional beginner's method implementation.
    
    Steps:
    1. White cross on the bottom face.
    2. Solve the first layer (white corners).
    3. Solve the middle layer (edges).
    4. Create a yellow cross on the top face.
    5. Position the yellow edges correctly.
    6. Position the yellow corners correctly.
    7. Orient the yellow corners to solve the cube.
    """

    def __init__(self, cube: Cube):
        self.cube = cube.copy() # Work on a copy to not alter the original
        self.solution = []

    def solve(self) -> List[str]:
        """
        Solve the cube and return the solution.
        """
        if self.cube.is_solved():
            return []

        # This solver builds the cube with the white face on the bottom (Down face).
        # We will orient the cube so White is Up to find pieces, then flip.
        self.orient_cube_for_solving()

        self.solve_white_cross()
        self.solve_white_corners()
        self.solve_middle_layer()
        
        # Now we work on the last layer (Yellow face on Top)
        self.solve_yellow_cross()
        self.position_yellow_edges()
        self.position_yellow_corners()
        self.orient_yellow_corners()
        
        # Final U-face alignment
        self.align_top_face()

        # Simplify the final sequence of moves
        self.solution = simplify_moves(self.solution)
        return self.solution

    def execute_and_record(self, algorithm: str):
        """Execute moves and add them to the solution."""
        moves = algorithm.split()
        for move in moves:
            if move:
                self.cube.execute_move(move)
                self.solution.append(move)
    
    def orient_cube_for_solving(self):
        """Rotates the whole cube so White is on top and Green is in front."""
        if self.cube.faces[Face.FRONT][4] == Color.WHITE: self.execute_and_record("x")
        elif self.cube.faces[Face.DOWN][4] == Color.WHITE: self.execute_and_record("x2")
        elif self.cube.faces[Face.BACK][4] == Color.WHITE: self.execute_and_record("x'")
        elif self.cube.faces[Face.LEFT][4] == Color.WHITE: self.execute_and_record("z'")
        elif self.cube.faces[Face.RIGHT][4] == Color.WHITE: self.execute_and_record("z")
        
        if self.cube.faces[Face.RIGHT][4] == Color.GREEN: self.execute_and_record("y")
        elif self.cube.faces[Face.BACK][4] == Color.GREEN: self.execute_and_record("y2")
        elif self.cube.faces[Face.LEFT][4] == Color.GREEN: self.execute_and_record("y'")

    def solve_white_cross(self):
        """Solves the white cross on the Down face by first forming it on the Up face."""
        # This is a robust method: move all white edges to the Yellow (top) face first.
        white_center_face = Face.UP # Temporarily
        yellow_center_face = Face.DOWN

        # Find white edges and move them to the top face with the white sticker facing up
        for edge_colors in [(Color.WHITE, Color.RED), (Color.WHITE, Color.GREEN), (Color.WHITE, Color.ORANGE), (Color.WHITE, Color.BLUE)]:
            for _ in range(10): # Safety loop
                # Find the edge
                # This is a procedural find, more robust than a static map
                found = False
                # Top layer
                if {self.cube.faces[Face.UP][7], self.cube.faces[Face.FRONT][1]} == set(edge_colors):
                    if self.cube.faces[Face.UP][7] != Color.WHITE: self.execute_and_record("F U' R U")
                    found = True
                # Middle layer
                elif {self.cube.faces[Face.FRONT][3], self.cube.faces[Face.LEFT][5]} == set(edge_colors):
                    self.execute_and_record("L")
                # Bottom layer
                elif {self.cube.faces[Face.DOWN][1], self.cube.faces[Face.FRONT][7]} == set(edge_colors):
                    if self.cube.faces[Face.DOWN][1] == Color.WHITE: self.execute_and_record("F' D R' D'")
                    else: self.execute_and_record("F")
                
                if not found: self.execute_and_record("y")
                else: break

        # Now all white edges are on the top face. Align them with their centers and move to bottom.
        for _ in range(4):
            # Rotate U until the front edge's side color matches the front center
            while self.cube.faces[Face.FRONT][1] != self.cube.faces[Face.FRONT][4]:
                self.execute_and_record("U")
            # Move it down
            self.execute_and_record("F2")
            self.execute_and_record("y")

    def solve_white_corners(self):
        """Finds white corners and inserts them into the first layer (Down face)."""
        for _ in range(4):
            # Find a white corner on the top layer
            found_corner = False
            for i in range(5): # Loop to find or pop out a corner
                if Color.WHITE in {self.cube.faces[Face.UP][8], self.cube.faces[Face.FRONT][2], self.cube.faces[Face.RIGHT][0]}:
                    found_corner = True
                    break
                self.execute_and_record("U")
            if not found_corner: # A corner is in the bottom but twisted/wrong slot
                self.execute_and_record("R U R'") # Pop it out
            
            # Now a white corner is at URF. Move it above its destination.
            corner_colors = {self.cube.faces[Face.FRONT][2], self.cube.faces[Face.RIGHT][0]}
            while not (self.cube.faces[Face.FRONT][4] in corner_colors and self.cube.faces[Face.RIGHT][4] in corner_colors):
                self.execute_and_record("U")
            
            # Insert the corner correctly
            while self.cube.faces[Face.DOWN][2] != Color.WHITE:
                self.execute_and_record("R U R' U'")

    def solve_middle_layer(self):
        """Solves the four edge pieces of the middle layer."""
        for _ in range(10): # Safety loop
            # Find a non-yellow edge in the top layer
            found_edge = False
            for i in range(4):
                if self.cube.faces[Face.UP][7] != Color.YELLOW and self.cube.faces[Face.FRONT][1] != Color.YELLOW:
                    found_edge = True
                    break
                self.execute_and_record("U")
            
            if not found_edge: # All top edges have yellow, check for misplaced middle edges
                misplaced_found = False
                for i in range(4):
                    if self.cube.faces[Face.FRONT][5] != self.cube.faces[Face.FRONT][4] or self.cube.faces[Face.RIGHT][3] != self.cube.faces[Face.RIGHT][4]:
                        self.execute_and_record("R U R' U' y' R' U' R U F") # Pop out piece
                        misplaced_found = True
                        break
                    self.execute_and_record("y")
                if not misplaced_found: return # Middle layer is solved
                continue # Restart loop
            
            # Align the front-facing sticker with its center
            while self.cube.faces[Face.FRONT][1] != self.cube.faces[Face.FRONT][4]:
                self.execute_and_record("U")

            # Insert to right or left
            top_color = self.cube.faces[Face.UP][7]
            if top_color == self.cube.faces[Face.RIGHT][4]:
                self.execute_and_record("U R U' R' U' F' U F")
            else:
                self.execute_and_record("U' L' U L U F U' F'")

    def solve_yellow_cross(self):
        """Creates a yellow cross on the top (Up) face."""
        alg = "F R U R' U' F'"
        while [self.cube.faces[Face.UP][i] for i in [1, 3, 5, 7]].count(Color.YELLOW) < 4:
            # Dot case
            if self.cube.faces[Face.UP][1] != Color.YELLOW and self.cube.faces[Face.UP][3] != Color.YELLOW and self.cube.faces[Face.UP][5] != Color.YELLOW and self.cube.faces[Face.UP][7] != Color.YELLOW:
                self.execute_and_record(alg)
            # L-shape case
            elif self.cube.faces[Face.UP][3] == Color.YELLOW and self.cube.faces[Face.UP][7] == Color.YELLOW:
                self.execute_and_record(alg)
            # Line case
            elif self.cube.faces[Face.UP][3] == Color.YELLOW and self.cube.faces[Face.UP][5] == Color.YELLOW:
                self.execute_and_record(alg)
            else:
                self.execute_and_record("U")

    def position_yellow_edges(self):
        """Permutes the yellow edges to match their side colors."""
        alg = "R U R' U R U2 R'"
        while self.count_correct_edges() < 4:
            # If two adjacent edges are correct, put them at Back and Right
            if self.cube.faces[Face.BACK][1] == self.cube.faces[Face.BACK][4] and self.cube.faces[Face.RIGHT][1] == self.cube.faces[Face.RIGHT][4]:
                self.execute_and_record(alg)
            # If two opposite edges are correct, put them at Front and Back
            elif self.cube.faces[Face.FRONT][1] == self.cube.faces[Face.FRONT][4] and self.cube.faces[Face.BACK][1] == self.cube.faces[Face.BACK][4]:
                 self.execute_and_record(alg)
            else:
                self.execute_and_record("U")
        
    def count_correct_edges(self):
        count = 0
        for _ in range(4):
            if self.cube.faces[Face.FRONT][1] == self.cube.faces[Face.FRONT][4]:
                count +=1
            self.execute_and_record("y")
        return count

    def position_yellow_corners(self):
        """Permutes the yellow corners to their correct positions."""
        alg = "U R U' L' U R' U' L"
        while not self.are_all_corners_positioned():
            # Find a correctly positioned corner and move it to the front-right
            found_correct = False
            for _ in range(4):
                corner_colors = {self.cube.faces[Face.FRONT][4], self.cube.faces[Face.RIGHT][4], Color.YELLOW}
                actual_colors = {self.cube.faces[Face.FRONT][2], self.cube.faces[Face.RIGHT][0], self.cube.faces[Face.UP][8]}
                if corner_colors == actual_colors:
                    found_correct = True
                    break
                self.execute_and_record("y")
            self.execute_and_record(alg)
    
    def are_all_corners_positioned(self):
        for _ in range(4):
            corner_colors = {self.cube.faces[Face.FRONT][4], self.cube.faces[Face.RIGHT][4], Color.YELLOW}
            actual_colors = {self.cube.faces[Face.FRONT][2], self.cube.faces[Face.RIGHT][0], self.cube.faces[Face.UP][8]}
            if corner_colors != actual_colors: return False
            self.execute_and_record("y")
        return True

    def orient_yellow_corners(self):
        """Orients the yellow corners to solve the cube."""
        alg = "R' D' R D"
        for _ in range(4):
            while self.cube.faces[Face.UP][8] != Color.YELLOW:
                self.execute_and_record(alg)
            self.execute_and_record("U")

    def align_top_face(self):
        """Final U moves to align the top layer with the rest of the cube."""
        while self.cube.faces[Face.FRONT][1] != self.cube.faces[Face.FRONT][4]:
            self.execute_and_record("U")