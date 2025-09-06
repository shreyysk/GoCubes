import cv2
import numpy as np
import copy
def draw_2d_cube_state(image, faces):
    """
    We're gonna display the visualization like so:
                -----
                | Y Y Y |
                | Y Y Y |
                | Y Y Y |
        -----   -----   -----   -----
        | B B B | R R R | G G G | O O O |
        | B B B | R R R | G G G | O O O |
        | B B B | R R R | G G G | O O O |
        -----   -----   -----   -----
                | W W W |
                | W W W |
                | W W W |
                -----
    """
    grid = {
        'white' : [1, 2],
        'orange': [3, 1],
        'green' : [2, 1],
        'red'   : [1, 1],
        'blue'  : [0, 1],
        'yellow': [1, 0],
    }
    color_map = {
        'white' : (255, 255, 255),
        'orange': (0, 165, 255),
        'green' : (0, 255, 0),
        'red'   : (0, 0, 255),
        'blue'  : (255, 0, 0),
        'yellow': (0, 255, 255),
        None: (0, 0, 0) # Default color
    }

    cube_simple = np.zeros((3,4),dtype=object)
    for face in faces.values():
        cube_simple[grid[face.name][1],grid[face.name][0]] = face.face
    
    # Draw a 4x3 grid for the cube layout
    for face_name in grid:
        x = grid[face_name][0]
        y = grid[face_name][1]
        face_matrix = cube_simple[y][x]

        # BUG FIX: Check if face_matrix is not None before iterating
        # This prevents a crash when a face has not been scanned yet.
        if face_matrix is not None:
            # If scanned, draw the 3x3 stickers with their detected colors
            for j in range(3):
                for k in range(3):
                    color = face_matrix[j][k]
                    # Draw sticker color
                    if color is not None:
                        cv2.rectangle(image, (x*100+k*33, y*100+j*33), (x*100+k*33+33, y*100+j*33+33), color_map[color], -1)
                    # Draw black border for the sticker
                    cv2.rectangle(image, (x*100+k*33, y*100+j*33), (x*100+k*33+33, y*100+j*33+33), (0,0,0), 1)
        else:
            # If not scanned, draw an empty gray grid as a placeholder
            for j in range(3):
                for k in range(3):
                    cv2.rectangle(image, (x*100+k*33, y*100+j*33), (x*100+k*33+33, y*100+j*33+33), (128,128,128), 1)
                    
    return image