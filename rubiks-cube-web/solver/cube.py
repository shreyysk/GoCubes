"""
Rubik's Cube representation and manipulation.
"""

import copy

class Color:
    """Color constants for the cube's state."""
    WHITE = 'W'
    YELLOW = 'Y'
    RED = 'R'
    ORANGE = 'O'
    GREEN = 'G'
    BLUE = 'B'

class Face:
    """Integer indices for each face for easier array access."""
    UP = 0
    DOWN = 1
    FRONT = 2
    BACK = 3
    LEFT = 4
    RIGHT = 5

class Cube:
    """
    Represents a 3x3x3 Rubik's cube.
    The cube is an array of 6 faces, each with 9 sticker colors.
    """
    
    def __init__(self):
        """Initializes the cube in a solved state."""
        self.reset()
    
    def reset(self):
        """Resets the cube to its solved state."""
        self.faces = [
            [Color.WHITE] * 9,   # 0: UP
            [Color.YELLOW] * 9,  # 1: DOWN
            [Color.RED] * 9,     # 2: FRONT
            [Color.ORANGE] * 9,  # 3: BACK
            [Color.GREEN] * 9,   # 4: LEFT
            [Color.BLUE] * 9     # 5: RIGHT
        ]
    
    def get_state(self) -> dict:
        """Returns the current state of the cube as a dictionary."""
        return {
            'up': self.faces[Face.UP][:],
            'down': self.faces[Face.DOWN][:],
            'front': self.faces[Face.FRONT][:],
            'back': self.faces[Face.BACK][:],
            'left': self.faces[Face.LEFT][:],
            'right': self.faces[Face.RIGHT][:]
        }
    
    def set_state(self, state: dict):
        """Sets the cube's state from a dictionary."""
        self.faces[Face.UP] = state['up'][:]
        self.faces[Face.DOWN] = state['down'][:]
        self.faces[Face.FRONT] = state['front'][:]
        self.faces[Face.BACK] = state['back'][:]
        self.faces[Face.LEFT] = state['left'][:]
        self.faces[Face.RIGHT] = state['right'][:]
    
    def copy(self):
        """Creates a deep copy of the cube."""
        new_cube = Cube()
        new_cube.faces = copy.deepcopy(self.faces)
        return new_cube
    
    def is_solved(self) -> bool:
        """Checks if the cube is in the solved state."""
        for face in self.faces:
            if not all(sticker == face[4] for sticker in face):
                return False
        return True
    
    def rotate_face_clockwise(self, face_index: int):
        """Rotates the stickers on a single face 90 degrees clockwise."""
        face = self.faces[face_index]
        self.faces[face_index] = [
            face[6], face[3], face[0],
            face[7], face[4], face[1],
            face[8], face[5], face[2]
        ]
    
    def rotate_face_counter_clockwise(self, face_index: int):
        """Rotates the stickers on a single face 90 degrees counter-clockwise."""
        face = self.faces[face_index]
        self.faces[face_index] = [
            face[2], face[5], face[8],
            face[1], face[4], face[7],
            face[0], face[3], face[6]
        ]

    # --- Standard Move Implementations ---

    def move_F(self):
        self.rotate_face_clockwise(Face.FRONT)
        temp = [self.faces[Face.UP][6], self.faces[Face.UP][7], self.faces[Face.UP][8]]
        self.faces[Face.UP][6], self.faces[Face.UP][7], self.faces[Face.UP][8] = self.faces[Face.LEFT][8], self.faces[Face.LEFT][5], self.faces[Face.LEFT][2]
        self.faces[Face.LEFT][2], self.faces[Face.LEFT][5], self.faces[Face.LEFT][8] = self.faces[Face.DOWN][0], self.faces[Face.DOWN][1], self.faces[Face.DOWN][2]
        self.faces[Face.DOWN][0], self.faces[Face.DOWN][1], self.faces[Face.DOWN][2] = self.faces[Face.RIGHT][6], self.faces[Face.RIGHT][3], self.faces[Face.RIGHT][0]
        self.faces[Face.RIGHT][0], self.faces[Face.RIGHT][3], self.faces[Face.RIGHT][6] = temp[0], temp[1], temp[2]

    def move_B(self):
        self.rotate_face_clockwise(Face.BACK)
        temp = [self.faces[Face.UP][0], self.faces[Face.UP][1], self.faces[Face.UP][2]]
        self.faces[Face.UP][0], self.faces[Face.UP][1], self.faces[Face.UP][2] = self.faces[Face.RIGHT][2], self.faces[Face.RIGHT][5], self.faces[Face.RIGHT][8]
        self.faces[Face.RIGHT][2], self.faces[Face.RIGHT][5], self.faces[Face.RIGHT][8] = self.faces[Face.DOWN][8], self.faces[Face.DOWN][7], self.faces[Face.DOWN][6]
        self.faces[Face.DOWN][6], self.faces[Face.DOWN][7], self.faces[Face.DOWN][8] = self.faces[Face.LEFT][0], self.faces[Face.LEFT][3], self.faces[Face.LEFT][6]
        self.faces[Face.LEFT][0], self.faces[Face.LEFT][3], self.faces[Face.LEFT][6] = temp[2], temp[1], temp[0]

    def move_U(self):
        self.rotate_face_clockwise(Face.UP)
        temp = self.faces[Face.FRONT][0:3]
        self.faces[Face.FRONT][0:3] = self.faces[Face.RIGHT][0:3]
        self.faces[Face.RIGHT][0:3] = self.faces[Face.BACK][0:3]
        self.faces[Face.BACK][0:3] = self.faces[Face.LEFT][0:3]
        self.faces[Face.LEFT][0:3] = temp

    def move_D(self):
        self.rotate_face_clockwise(Face.DOWN)
        temp = self.faces[Face.FRONT][6:9]
        self.faces[Face.FRONT][6:9] = self.faces[Face.LEFT][6:9]
        self.faces[Face.LEFT][6:9] = self.faces[Face.BACK][6:9]
        self.faces[Face.BACK][6:9] = self.faces[Face.RIGHT][6:9]
        self.faces[Face.RIGHT][6:9] = temp
        
    def move_L(self):
        self.rotate_face_clockwise(Face.LEFT)
        temp = [self.faces[Face.UP][0], self.faces[Face.UP][3], self.faces[Face.UP][6]]
        self.faces[Face.UP][0], self.faces[Face.UP][3], self.faces[Face.UP][6] = self.faces[Face.BACK][8], self.faces[Face.BACK][5], self.faces[Face.BACK][2]
        self.faces[Face.BACK][2], self.faces[Face.BACK][5], self.faces[Face.BACK][8] = self.faces[Face.DOWN][6], self.faces[Face.DOWN][3], self.faces[Face.DOWN][0]
        self.faces[Face.DOWN][0], self.faces[Face.DOWN][3], self.faces[Face.DOWN][6] = self.faces[Face.FRONT][0], self.faces[Face.FRONT][3], self.faces[Face.FRONT][6]
        self.faces[Face.FRONT][0], self.faces[Face.FRONT][3], self.faces[Face.FRONT][6] = temp[0], temp[1], temp[2]

    def move_R(self):
        self.rotate_face_clockwise(Face.RIGHT)
        temp = [self.faces[Face.UP][2], self.faces[Face.UP][5], self.faces[Face.UP][8]]
        self.faces[Face.UP][2], self.faces[Face.UP][5], self.faces[Face.UP][8] = self.faces[Face.FRONT][2], self.faces[Face.FRONT][5], self.faces[Face.FRONT][8]
        self.faces[Face.FRONT][2], self.faces[Face.FRONT][5], self.faces[Face.FRONT][8] = self.faces[Face.DOWN][2], self.faces[Face.DOWN][5], self.faces[Face.DOWN][8]
        self.faces[Face.DOWN][2], self.faces[Face.DOWN][5], self.faces[Face.DOWN][8] = self.faces[Face.BACK][6], self.faces[Face.BACK][3], self.faces[Face.BACK][0]
        self.faces[Face.BACK][0], self.faces[Face.BACK][3], self.faces[Face.BACK][6] = temp[2], temp[1], temp[0]

    def execute_move(self, move: str):
        """Executes a single move given in standard notation."""
        if move == "F": self.move_F()
        elif move == "F'": self.move_F(); self.move_F(); self.move_F()
        elif move == "F2": self.move_F(); self.move_F()
        elif move == "B": self.move_B()
        elif move == "B'": self.move_B(); self.move_B(); self.move_B()
        elif move == "B2": self.move_B(); self.move_B()
        elif move == "U": self.move_U()
        elif move == "U'": self.move_U(); self.move_U(); self.move_U()
        elif move == "U2": self.move_U(); self.move_U()
        elif move == "D": self.move_D()
        elif move == "D'": self.move_D(); self.move_D(); self.move_D()
        elif move == "D2": self.move_D(); self.move_D()
        elif move == "L": self.move_L()
        elif move == "L'": self.move_L(); self.move_L(); self.move_L()
        elif move == "L2": self.move_L(); self.move_L()
        elif move == "R": self.move_R()
        elif move == "R'": self.move_R(); self.move_R(); self.move_R()
        elif move == "R2": self.move_R(); self.move_R()
        # Whole cube rotations (x, y, z)
        elif move == "x": self.move_R(); self.move_L(); self.move_L(); self.move_L() # Simplified x rotation
        elif move == "y": self.move_U(); self.move_D(); self.move_D(); self.move_D() # Simplified y rotation
        elif move == "z": self.move_F(); self.move_B(); self.move_B(); self.move_B() # Simplified z rotation
        elif move == "x'": self.move_R(); self.move_R(); self.move_R(); self.move_L()
        elif move == "y'": self.move_U(); self.move_U(); self.move_U(); self.move_D()
        elif move == "z'": self.move_F(); self.move_F(); self.move_F(); self.move_B()
        elif move == "x2": self.execute_move("x"); self.execute_move("x")
        elif move == "y2": self.execute_move("y"); self.execute_move("y")
        elif move == "z2": self.execute_move("z"); self.execute_move("z")