"""
Image processing utilities for detecting Rubik's cube colors from images.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from PIL import Image

# Color ranges in HSV for cube detection
COLOR_RANGES = {
    'W': {  # White
        'lower': np.array([0, 0, 200]),
        'upper': np.array([180, 30, 255])
    },
    'Y': {  # Yellow
        'lower': np.array([20, 100, 100]),
        'upper': np.array([30, 255, 255])
    },
    'R': {  # Red (two ranges for wraparound)
        'lower': np.array([0, 100, 100]),
        'upper': np.array([10, 255, 255]),
        'lower2': np.array([170, 100, 100]),
        'upper2': np.array([180, 255, 255])
    },
    'O': {  # Orange
        'lower': np.array([10, 100, 100]),
        'upper': np.array([20, 255, 255])
    },
    'G': {  # Green
        'lower': np.array([40, 100, 100]),
        'upper': np.array([80, 255, 255])
    },
    'B': {  # Blue
        'lower': np.array([100, 100, 100]),
        'upper': np.array([130, 255, 255])
    }
}

def process_cube_image(images: Dict[str, Image.Image]) -> Dict[str, List[str]]:
    """
    Process cube face images and extract colors.
    """
    cube_state = {}
    
    for face_name, pil_image in images.items():
        opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        colors = detect_face_colors(opencv_image, face_name)
        cube_state[face_name.lower()] = colors
    
    is_valid, error_msg = validate_cube_state(cube_state)
    if not is_valid:
        raise ValueError(f"Invalid cube state detected: {error_msg}")
    
    return cube_state

def detect_face_colors(image: np.ndarray, face_name: str) -> List[str]:
    processed = preprocess_image(image)
    grid_points = find_cube_grid(processed)
    
    if grid_points is None:
        grid_points = create_uniform_grid(image.shape)
    
    colors = extract_colors_from_grid(image, grid_points)
    return colors

def preprocess_image(image: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    lab = cv2.cvtColor(blurred, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    return enhanced

def find_cube_grid(image: np.ndarray) -> Optional[List[Tuple[int, int]]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    squares = []
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        
        if len(approx) == 4 and cv2.contourArea(approx) > 100:
            x, y, w, h = cv2.boundingRect(approx)
            if 0.8 <= float(w) / h <= 1.2:
                squares.append((x, y, w, h))
    
    if len(squares) >= 9:
        squares.sort(key=lambda s: s[2] * s[3], reverse=True)
        grid_squares = squares[:9] # Simplified grid finding
        grid_points = [(s[0] + s[2] // 2, s[1] + s[3] // 2) for s in grid_squares]
        return sort_grid_points(grid_points)
    return None

def create_uniform_grid(shape: Tuple[int, int, int]) -> List[Tuple[int, int]]:
    height, width = shape[:2]
    margin_x, margin_y = width // 6, height // 6
    cell_width = (width - 2 * margin_x) // 3
    cell_height = (height - 2 * margin_y) // 3
    
    return [
        (margin_x + col * cell_width + cell_width // 2, margin_y + row * cell_height + cell_height // 2)
        for row in range(3) for col in range(3)
    ]

def sort_grid_points(points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if len(points) != 9:
        return points
    
    # Sort by y-coordinate to group into rows, then by x-coordinate within rows
    y_sorted = sorted(points, key=lambda p: p[1])
    rows = [sorted(y_sorted[i:i+3], key=lambda p: p[0]) for i in range(0, 9, 3)]
    return [p for row in rows for p in row]

def extract_colors_from_grid(image: np.ndarray, grid_points: List[Tuple[int, int]]) -> List[str]:
    colors = []
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    for x, y in grid_points:
        region_size = 20
        x1, y1 = max(0, x - region_size // 2), max(0, y - region_size // 2)
        x2, y2 = min(image.shape[1], x + region_size // 2), min(image.shape[0], y + region_size // 2)
        
        region = hsv_image[y1:y2, x1:x2]
        avg_color = np.mean(region.reshape(-1, 3), axis=0).astype(int)
        colors.append(detect_color(avg_color))
    return colors

def detect_color(hsv_value: np.ndarray) -> str:
    for color_code, ranges in COLOR_RANGES.items():
        if color_code == 'R':
            if (np.all(hsv_value >= ranges['lower']) and np.all(hsv_value <= ranges['upper'])) or \
               (np.all(hsv_value >= ranges['lower2']) and np.all(hsv_value <= ranges['upper2'])):
                return color_code
        elif np.all(hsv_value >= ranges['lower']) and np.all(hsv_value <= ranges['upper']):
            return color_code
    return 'W'

def validate_cube_state(cube_state: Dict[str, List[str]]) -> Tuple[bool, str]:
    """Validate color counts and mathematical solvability."""
    color_counts = {'W': 0, 'Y': 0, 'R': 0, 'O': 0, 'G': 0, 'B': 0}
    
    for face in ['up', 'down', 'front', 'back', 'left', 'right']:
        face_colors = cube_state.get(face)
        if not face_colors or len(face_colors) != 9:
            return False, f"Face '{face}' is missing or incomplete."
        for color in face_colors:
            color_counts[color] += 1
    
    for color, count in color_counts.items():
        if count != 9:
            return False, f"Incorrect sticker count for color {color}. Expected 9, found {count}."
    
    if len({cube_state[face][4] for face in cube_state}) != 6:
        return False, "Duplicate center piece colors detected."

    return is_solvable(cube_state)

def is_solvable(state: Dict[str, List[str]]) -> Tuple[bool, str]:
    """Checks if a cube state is solvable using parity rules."""
    
    # --- Define piece locations and reference orientations ---
    face_map = {'up':'W', 'down':'Y', 'front':'R', 'back':'O', 'left':'G', 'right':'B'}

    EDGES = {
        'UF': (('up', 7), ('front', 1)), 'UR': (('up', 5), ('right', 1)),
        'UB': (('up', 1), ('back', 1)), 'UL': (('up', 3), ('left', 1)),
        'DF': (('down', 1), ('front', 7)), 'DR': (('down', 5), ('right', 7)),
        'DB': (('down', 7), ('back', 7)), 'DL': (('down', 3), ('left', 7)),
        'FR': (('front', 5), ('right', 3)), 'FL': (('front', 3), ('left', 5)),
        'BR': (('back', 3), ('right', 5)), 'BL': (('back', 5), ('left', 3)),
    }
    CORNERS = {
        'UFR': (('up', 8), ('front', 2), ('right', 2)), 'URB': (('up', 2), ('right', 0), ('back', 0)),
        'UBL': (('up', 0), ('back', 2), ('left', 0)), 'ULF': (('up', 6), ('left', 2), ('front', 0)),
        'DFR': (('down', 2), ('front', 8), ('right', 6)), 'DRB': (('down', 8), ('right', 8), ('back', 6)),
        'DBL': (('down', 6), ('back', 8), ('left', 6)), 'DLF': (('down', 0), ('left', 8), ('front', 6)),
    }

    # --- 1. Edge Orientation Check ---
    edge_flip = 0
    for piece_locs in EDGES.values():
        c1_loc, c2_loc = piece_locs
        color1 = state[c1_loc[0]][c1_loc[1]]
        color2 = state[c2_loc[0]][c2_loc[1]]
        
        if color1 in 'WY':
            if c1_loc[0] not in ['up', 'down']: edge_flip += 1
        elif color2 in 'WY':
            if c2_loc[0] not in ['up', 'down']: edge_flip += 1
        elif color1 in 'RO':
            if c1_loc[0] not in ['front', 'back']: edge_flip += 1
        elif color2 in 'RO':
            if c2_loc[0] not in ['front', 'back']: edge_flip += 1
            
    if edge_flip % 2 != 0:
        return False, "Invalid edge orientation parity (odd number of flipped edges)."

    # --- 2. Corner Orientation Check ---
    corner_twist = 0
    for piece_locs in CORNERS.values():
        c1_loc, c2_loc, c3_loc = piece_locs
        color1 = state[c1_loc[0]][c1_loc[1]]
        
        if color1 in 'WY': pass
        elif state[c2_loc[0]][c2_loc[1]] in 'WY': corner_twist += 1
        elif state[c3_loc[0]][c3_loc[1]] in 'WY': corner_twist += 2
    
    if corner_twist % 3 != 0:
        return False, "Invalid corner orientation parity (twist is not a multiple of 3)."

    # --- 3. Permutation Parity Check ---
    def count_swaps(item_list):
        visited = [False] * len(item_list)
        cycles = 0
        for i in range(len(item_list)):
            if not visited[i]:
                cycles += 1
                j = i
                while not visited[j]:
                    visited[j] = True
                    j = item_list[j]
        return len(item_list) - cycles

    def get_piece_from_colors(colors, piece_db):
        color_set = frozenset(colors)
        for name, solved_locs in piece_db.items():
            solved_colors = frozenset(face_map[loc[0]] for loc in solved_locs)
            if color_set == solved_colors: return name
        return None

    edge_perm_map = {name: get_piece_from_colors([state[l[0]][l[1]] for l in locs], EDGES) for name, locs in EDGES.items()}
    corner_perm_map = {name: get_piece_from_colors([state[l[0]][l[1]] for l in locs], CORNERS) for name, locs in CORNERS.items()}

    edge_order = list(EDGES.keys())
    corner_order = list(CORNERS.keys())
    
    edge_perm = [edge_order.index(edge_perm_map[name]) for name in edge_order]
    corner_perm = [corner_order.index(corner_perm_map[name]) for name in corner_order]

    if (count_swaps(edge_perm) % 2) != (count_swaps(corner_perm) % 2):
        return False, "Invalid permutation parity (edge and corner parities do not match)."

    return True, "Cube is valid and solvable."