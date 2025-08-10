#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cube scanner main class

This module coordinates the scanning process and manages face detection.
"""

import cv2
import numpy as np
import logging
import time
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass, field

from .color_detection import ColorDetector
from .calibration import Calibration
from utils.constants import *

logger = logging.getLogger(__name__)


class ScanState(Enum):
    """Scanning states"""
    IDLE = "idle"
    DETECTING = "detecting"
    CAPTURING = "capturing"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class FaceData:
    """Data for a scanned face"""
    name: str
    colors: List[str] = field(default_factory=list)
    timestamp: float = 0.0
    confidence: float = 0.0
    image: Optional[np.ndarray] = None


class CubeScanner:
    """Main cube scanner class"""
    
    def __init__(self, camera_index: int = 0):
        """
        Initialize cube scanner
        
        Args:
            camera_index: Index of camera to use
        """
        self.camera_index = camera_index
        self.cap = None
        self.state = ScanState.IDLE
        
        # Color detector
        self.color_detector = ColorDetector()
        self.calibration = Calibration()
        
        # Scanning data
        self.faces = {}
        self.current_face = None
        self.face_order = ['U', 'R', 'F', 'D', 'L', 'B']
        
        # Detection parameters
        self.min_contours = 9
        self.detection_threshold = 30
        self.stability_frames = 5
        self.stable_count = 0
        
        # Frame buffers
        self.frame_buffer = []
        self.color_buffer = []
        self.buffer_size = 10
        
        # Statistics
        self.scan_start_time = 0
        self.face_scan_times = {}
        
    def start(self) -> bool:
        """
        Start the scanner
        
        Returns:
            True if started successfully
        """
        try:
            # Open camera
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                logger.error(f"Cannot open camera {self.camera_index}")
                self.state = ScanState.ERROR
                return False
                
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_DEFAULT_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_DEFAULT_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, CAMERA_DEFAULT_FPS)
            
            # Load calibration if exists
            if self.calibration.load():
                self.color_detector.set_calibration(self.calibration.get_colors())
                logger.info("Calibration loaded")
                
            self.state = ScanState.DETECTING
            self.scan_start_time = time.time()
            
            logger.info(f"Scanner started with camera {self.camera_index}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start scanner: {e}")
            self.state = ScanState.ERROR
            return False
            
    def stop(self):
        """Stop the scanner"""
        if self.cap:
            self.cap.release()
            self.cap = None
            
        self.state = ScanState.IDLE
        logger.info("Scanner stopped")
        
    def scan_face(self, face_name: str) -> Optional[List[str]]:
        """
        Scan a single face
        
        Args:
            face_name: Name of face to scan (U, R, F, D, L, B)
            
        Returns:
            List of color codes if successful, None otherwise
        """
        if self.state == ScanState.ERROR:
            logger.error("Scanner in error state")
            return None
            
        self.current_face = face_name
        self.state = ScanState.DETECTING
        self.stable_count = 0
        self.color_buffer.clear()
        
        logger.info(f"Scanning face {face_name}")
        face_start_time = time.time()
        
        # Detection loop
        while self.state == ScanState.DETECTING:
            frame = self.capture_frame()
            if frame is None:
                continue
                
            # Detect cube
            contours = self.detect_cube(frame)
            
            if len(contours) == self.min_contours:
                # Extract colors
                colors = self.extract_colors(frame, contours)
                
                if colors:
                    # Add to buffer
                    self.color_buffer.append(colors)
                    
                    # Check stability
                    if self.is_stable():
                        # Get final colors
                        final_colors = self.get_stable_colors()
                        
                        # Validate
                        if self.validate_face(final_colors):
                            # Store face data
                            face_data = FaceData(
                                name=face_name,
                                colors=final_colors,
                                timestamp=time.time(),
                                confidence=self.calculate_confidence(),
                                image=frame.copy()
                            )
                            self.faces[face_name] = face_data
                            
                            # Update statistics
                            self.face_scan_times[face_name] = time.time() - face_start_time
                            
                            logger.info(f"Face {face_name} scanned successfully in {self.face_scan_times[face_name]:.2f}s")
                            
                            self.state = ScanState.IDLE
                            return final_colors
                            
        return None
        
    def scan_cube(self) -> Optional[Dict[str, List[str]]]:
        """
        Scan complete cube
        
        Returns:
            Dictionary of face colors if successful, None otherwise
        """
        logger.info("Starting full cube scan")
        
        cube_data = {}
        
        for face in self.face_order:
            # Prompt user to show face
            logger.info(f"Please show face {face}")
            
            # Wait for user to position cube
            self.wait_for_movement()
            
            # Scan face
            colors = self.scan_face(face)
            
            if colors:
                cube_data[face] = colors
            else:
                logger.error(f"Failed to scan face {face}")
                return None
                
        # Validate complete cube
        if self.validate_cube(cube_data):
            total_time = time.time() - self.scan_start_time
            logger.info(f"Cube scanned successfully in {total_time:.2f}s")
            
            self.state = ScanState.COMPLETE
            return cube_data
        else:
            logger.error("Invalid cube configuration")
            self.state = ScanState.ERROR
            return None
            
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a frame from camera
        
        Returns:
            Frame if successful, None otherwise
        """
        if not self.cap or not self.cap.isOpened():
            return None
            
        ret, frame = self.cap.read()
        
        if ret:
            # Add to frame buffer
            if len(self.frame_buffer) >= self.buffer_size:
                self.frame_buffer.pop(0)
            self.frame_buffer.append(frame)
            
            return frame
        else:
            logger.warning("Failed to capture frame")
            return None
            
    def detect_cube(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect cube in frame
        
        Args:
            frame: Input frame
            
        Returns:
            List of contour bounding rectangles
        """
        # Find contours
        contours = self.color_detector.find_contours(frame)
        
        # Filter for 3x3 grid
        if len(contours) >= 9:
            contours = self.find_3x3_grid(contours)
            
        return contours
        
    def find_3x3_grid(self, contours: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        Find 3x3 grid from contours
        
        Args:
            contours: List of contour bounding rectangles
            
        Returns:
            Sorted list of 9 contours forming grid
        """
        if len(contours) < 9:
            return []
            
        # Find center contour (should have 8 neighbors)
        best_grid = []
        
        for i, c1 in enumerate(contours):
            x1, y1, w1, h1 = c1
            cx1, cy1 = x1 + w1/2, y1 + h1/2
            
            neighbors = []
            
            # Find neighbors
            for j, c2 in enumerate(contours):
                if i == j:
                    continue
                    
                x2, y2, w2, h2 = c2
                cx2, cy2 = x2 + w2/2, y2 + h2/2
                
                # Calculate distance
                dist = np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
                
                # Check if neighbor (within 2x the average size)
                avg_size = (w1 + h1 + w2 + h2) / 4
                if dist < 2 * avg_size:
                    neighbors.append((j, dist))
                    
            # If this has 8 neighbors, it's likely the center
            if len(neighbors) == 8:
                # Get the 9 contours (center + 8 neighbors)
                grid_indices = [i] + [n[0] for n in neighbors]
                grid = [contours[idx] for idx in grid_indices]
                
                # Sort grid
                grid = self.sort_grid(grid)
                
                if len(grid) == 9:
                    best_grid = grid
                    break
                    
        return best_grid
        
    def sort_grid(self, contours: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        Sort 3x3 grid of contours
        
        Args:
            contours: Unsorted contours
            
        Returns:
            Sorted contours (left-to-right, top-to-bottom)
        """
        if len(contours) != 9:
            return contours
            
        # Sort by Y coordinate first (rows)
        contours.sort(key=lambda c: c[1])
        
        # Sort each row by X coordinate
        sorted_grid = []
        for i in range(0, 9, 3):
            row = sorted(contours[i:i+3], key=lambda c: c[0])
            sorted_grid.extend(row)
            
        return sorted_grid
        
    def extract_colors(self, frame: np.ndarray, contours: List[Tuple[int, int, int, int]]) -> List[str]:
        """
        Extract colors from contours
        
        Args:
            frame: Input frame
            contours: List of contour bounding rectangles
            
        Returns:
            List of color codes
        """
        colors = []
        
        for x, y, w, h in contours:
            # Extract ROI with margin
            margin = 5
            roi = frame[y+margin:y+h-margin, x+margin:x+w-margin]
            
            if roi.size == 0:
                colors.append('X')  # Unknown
                continue
                
            # Get dominant color
            bgr = self.color_detector.get_dominant_color(roi)
            
            # Get color name
            color_name = self.color_detector.get_closest_color_name(bgr)
            
            # Convert to notation
            color_code = COLOR_TO_NOTATION.get(color_name, 'X')
            colors.append(color_code)
            
        return colors
        
    def is_stable(self) -> bool:
        """
        Check if color detection is stable
        
        Returns:
            True if stable, False otherwise
        """
        if len(self.color_buffer) < self.stability_frames:
            return False
            
        # Check if last N frames have same colors
        recent = self.color_buffer[-self.stability_frames:]
        
        for i in range(1, len(recent)):
            if recent[i] != recent[0]:
                return False
                
        return True
        
    def get_stable_colors(self) -> List[str]:
        """
        Get stable colors from buffer
        
        Returns:
            Most common colors from buffer
        """
        if not self.color_buffer:
            return []
            
        # Get most recent stable colors
        return self.color_buffer[-1]
        
    def validate_face(self, colors: List[str]) -> bool:
        """
        Validate face colors
        
        Args:
            colors: List of 9 color codes
            
        Returns:
            True if valid, False otherwise
        """
        # Check count
        if len(colors) != 9:
            return False
            
        # Check for unknowns
        if 'X' in colors:
            return False
            
        # Check center color is valid
        center = colors[4]
        if center not in COLOR_TO_NOTATION.values():
            return False
            
        return True
        
    def validate_cube(self, cube_data: Dict[str, List[str]]) -> bool:
        """
        Validate complete cube
        
        Args:
            cube_data: Dictionary of face colors
            
        Returns:
            True if valid, False otherwise
        """
        # Check all faces present
        if set(cube_data.keys()) != set(self.face_order):
            return False
            
        # Count colors
        color_count = {}
        for colors in cube_data.values():
            for color in colors:
                color_count[color] = color_count.get(color, 0) + 1
                
        # Check each color appears exactly 9 times
        for color in COLOR_TO_NOTATION.values():
            if color_count.get(color, 0) != 9:
                logger.error(f"Color {color} appears {color_count.get(color, 0)} times, expected 9")
                return False
                
        # Check center colors are unique
        centers = set()
        for colors in cube_data.values():
            center = colors[4]
            if center in centers:
                logger.error(f"Duplicate center color: {center}")
                return False
            centers.add(center)
            
        return True
        
    def calculate_confidence(self) -> float:
        """
        Calculate scanning confidence
        
        Returns:
            Confidence score (0-1)
        """
        if not self.color_buffer:
            return 0.0
            
        # Base confidence on stability
        stable_ratio = min(len(self.color_buffer) / self.buffer_size, 1.0)
        
        # TODO: Add more confidence factors
        # - Color detection confidence
        # - Contour quality
        # - Lighting conditions
        
        return stable_ratio
        
    def wait_for_movement(self, timeout: float = 5.0):
        """
        Wait for cube movement to stop
        
        Args:
            timeout: Maximum wait time in seconds
        """
        start_time = time.time()
        prev_frame = None
        stable_frames = 0
        required_stable = 10
        
        while time.time() - start_time < timeout:
            frame = self.capture_frame()
            
            if frame is None:
                continue
                
            if prev_frame is not None:
                # Calculate frame difference
                diff = cv2.absdiff(frame, prev_frame)
                diff_sum = np.sum(diff)
                
                # Check if stable
                if diff_sum < 100000:  # Threshold for stability
                    stable_frames += 1
                else:
                    stable_frames = 0
                    
                if stable_frames >= required_stable:
                    logger.debug("Movement stopped")
                    return
                    
            prev_frame = frame
            
        logger.warning("Movement detection timeout")
        
    def auto_calibrate(self) -> bool:
        """
        Auto-calibrate colors from a solved cube
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting auto-calibration")
        
        # Scan solved cube
        cube_data = self.scan_cube()
        
        if not cube_data:
            logger.error("Failed to scan cube for calibration")
            return False
            
        # Extract center colors as reference
        calibration_data = {}
        
        for face, colors in cube_data.items():
            center_color = colors[4]
            
            # Map face to expected color
            expected_color = FACE_NOTATION[face]
            
            # Get all stickers of this color
            samples = []
            for f, cols in cube_data.items():
                for i, c in enumerate(cols):
                    if c == center_color:
                        # Get the actual BGR value from stored frame
                        if f in self.faces and self.faces[f].image is not None:
                            # Extract color from image
                            # TODO: Get actual BGR values
                            pass
                            
        # Update calibration
        # self.calibration.set_colors(calibration_data)
        # self.calibration.save()
        
        logger.info("Auto-calibration complete")
        return True
        
    def get_statistics(self) -> Dict[str, any]:
        """
        Get scanning statistics
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_time': time.time() - self.scan_start_time if self.scan_start_time else 0,
            'faces_scanned': len(self.faces),
            'face_times': self.face_scan_times,
            'state': self.state.value,
            'confidence': self.calculate_confidence()
        }
        
        # Add per-face statistics
        for face_name, face_data in self.faces.items():
            stats[f'face_{face_name}_confidence'] = face_data.confidence
            
        return stats
        
    def reset(self):
        """Reset scanner state"""
        self.faces.clear()
        self.current_face = None
        self.frame_buffer.clear()
        self.color_buffer.clear()
        self.stable_count = 0
        self.face_scan_times.clear()
        self.state = ScanState.IDLE
        
        logger.info("Scanner reset")
        
    def export_scan_data(self, filepath: str):
        """
        Export scan data to file
        
        Args:
            filepath: Path to export file
        """
        import json
        
        export_data = {
            'timestamp': time.time(),
            'faces': {},
            'statistics': self.get_statistics()
        }
        
        for face_name, face_data in self.faces.items():
            export_data['faces'][face_name] = {
                'colors': face_data.colors,
                'timestamp': face_data.timestamp,
                'confidence': face_data.confidence
            }
            
        try:
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Scan data exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export scan data: {e}")