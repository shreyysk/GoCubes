#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Image processing utilities for cube face detection
"""

import cv2
import numpy as np
from PIL import Image
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

def process_cube_image(images: Dict[str, Image.Image]) -> Dict[str, List[str]]:
    """
    Process cube face images and detect colors
    
    Args:
        images: Dictionary mapping face names to PIL Images
        
    Returns:
        Dictionary with face names as keys and lists of 9 color codes
    """
    # Define reference colors in BGR format
    reference_colors = {
        'W': np.array([255, 255, 255]),  # White
        'Y': np.array([0, 255, 255]),    # Yellow
        'R': np.array([0, 0, 255]),      # Red
        'O': np.array([0, 165, 255]),    # Orange
        'G': np.array([0, 255, 0]),      # Green
        'B': np.array([255, 0, 0])       # Blue
    }
    
    cube_state = {}
    
    for face_name, img in images.items():
        # Convert PIL to OpenCV format
        opencv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Detect the 9 stickers
        colors = detect_face_colors(opencv_img, reference_colors)
        cube_state[face_name] = colors
        
    # Validate the detected state
    if not validate_cube_state(cube_state):
        raise ValueError("Invalid cube state detected. Please check the images.")
        
    return cube_state

def detect_face_colors(image: np.ndarray, 
                       reference_colors: Dict[str, np.ndarray]) -> List[str]:
    """
    Detect 9 sticker colors from a cube face image
    """
    # Apply preprocessing for better color detection
    image = cv2.GaussianBlur(image, (5, 5), 0)
    
    h, w = image.shape[:2]
    grid_size = 3
    cell_h = h // grid_size
    cell_w = w // grid_size
    
    colors = []
    for row in range(grid_size):
        for col in range(grid_size):
            # Extract cell region with smaller margin for better sampling
            margin = min(cell_h, cell_w) // 5
            y1 = row * cell_h + margin
            y2 = (row + 1) * cell_h - margin
            x1 = col * cell_w + margin
            x2 = (col + 1) * cell_w - margin
            
            cell = image[y1:y2, x1:x2]
            avg_color = cv2.mean(cell)[:3]
            detected_color = classify_color(np.array(avg_color), reference_colors)
            colors.append(detected_color)
            
    return colors

def classify_color(bgr_color: np.ndarray, 
                   reference_colors: Dict[str, np.ndarray]) -> str:
    """
    Classify a BGR color to nearest reference color
    """
    min_distance = float('inf')
    best_match = 'W'
    
    for color_code, ref_color in reference_colors.items():
        # Calculate Euclidean distance
        distance = np.linalg.norm(bgr_color - ref_color)
        
        if distance < min_distance:
            min_distance = distance
            best_match = color_code
            
    return best_match

def validate_cube_state(cube_state: Dict[str, List[str]]) -> bool:
    """
    Validate that the cube state is physically possible
    """
    # Count occurrences of each color
    color_count = {}
    
    for face, colors in cube_state.items():
        if len(colors) != 9:
            return False
            
        for color in colors:
            color_count[color] = color_count.get(color, 0) + 1
            
    # Each color should appear exactly 9 times
    expected_colors = {'W', 'Y', 'R', 'O', 'G', 'B'}
    
    if set(color_count.keys()) != expected_colors:
        return False
        
    for color in expected_colors:
        if color_count.get(color, 0) != 9:
            return False
            
    return True