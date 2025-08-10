#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Webcam interface for cube scanning

This module handles webcam capture and display for the scanner.
"""

import cv2
import numpy as np
import logging
from typing import Optional, Tuple, List, Callable
from pathlib import Path

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QMutex, QMutexLocker
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont

from .color_detection import ColorDetector
from utils.constants import *
from utils.helpers import numpy_to_qimage

logger = logging.getLogger(__name__)


class CameraThread(QThread):
    """Thread for camera capture"""
    
    frame_ready = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, camera_index: int = 0):
        super().__init__()
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False
        self.mutex = QMutex()
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 30
        
    def run(self):
        """Run camera capture loop"""
        try:
            # Open camera
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                self.error_occurred.emit(f"Cannot open camera {self.camera_index}")
                return
                
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            self.is_running = True
            
            while self.is_running:
                with QMutexLocker(self.mutex):
                    if not self.is_running:
                        break
                        
                ret, frame = self.cap.read()
                
                if ret:
                    # Emit frame
                    self.frame_ready.emit(frame.copy())
                else:
                    self.error_occurred.emit("Failed to read frame")
                    
                # Small delay to control frame rate
                self.msleep(int(1000 / self.fps))
                
        except Exception as e:
            logger.error(f"Camera thread error: {e}")
            self.error_occurred.emit(str(e))
            
        finally:
            if self.cap:
                self.cap.release()
                
    def stop(self):
        """Stop camera capture"""
        with QMutexLocker(self.mutex):
            self.is_running = False
            
    def set_camera_index(self, index: int):
        """Change camera index"""
        self.camera_index = index
        
    def set_resolution(self, width: int, height: int):
        """Set camera resolution"""
        self.frame_width = width
        self.frame_height = height
        
        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def detect_available_cameras(self):
        """Detect available cameras"""
        import cv2
        available_cameras = []
        
        # Check first 5 camera indices
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        
        if not available_cameras:
            logger.warning("No cameras detected")
            return [0]  # Default to camera 0
        
        return available_cameras

class WebcamWidget(QWidget):
    """Widget for webcam display and cube scanning"""
    
    frame_processed = pyqtSignal(np.ndarray)
    face_captured = pyqtSignal(str, list)  # face_name, colors
    scan_completed = pyqtSignal(dict)  # all faces
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Camera thread
        self.camera_thread = None
        self.is_camera_active = False
        
        # Current frame
        self.current_frame = None
        self.display_frame = None
        
        # Color detector
        self.color_detector = ColorDetector()
        
        # Scanning state
        self.scanning_mode = False
        self.calibration_mode = False
        self.current_face = 'U'
        self.captured_faces = {}
        
        # Detection state
        self.preview_colors = [None] * 9
        self.snapshot_colors = [None] * 9
        self.average_color_buffer = [[] for _ in range(9)]
        self.contours = []
        

        
        # UI elements
        self.setup_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
    
    def detect_available_cameras(self):
        """Detect available cameras"""
        import cv2
        available_cameras = []
        
        # Check first 5 camera indices
        for i in range(5):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    available_cameras.append(i)
                    cap.release()
            except:
                pass
        
        if not available_cameras:
            logger.warning("No cameras detected, defaulting to camera 0")
            return [0]  # Default to camera 0
        
        logger.info(f"Detected cameras: {available_cameras}")
        return available_cameras
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout()
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Camera selection
        control_layout.addWidget(QLabel("Camera:"))
        self.camera_combo = QComboBox()
        # Replace the camera combo setup with:
        available_cameras = self.detect_available_cameras()
        self.camera_combo.clear()
        for cam_idx in available_cameras:
            self.camera_combo.addItem(f"Camera {cam_idx}")
        self.camera_combo.currentIndexChanged.connect(self.on_camera_changed)
        control_layout.addWidget(self.camera_combo)
        
        # Start/Stop button
        self.start_stop_btn = QPushButton("Start Camera")
        self.start_stop_btn.clicked.connect(self.toggle_camera)
        control_layout.addWidget(self.start_stop_btn)
        
        # Calibration button
        self.calibration_btn = QPushButton("Calibration")
        self.calibration_btn.setCheckable(True)
        self.calibration_btn.toggled.connect(self.toggle_calibration)
        control_layout.addWidget(self.calibration_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Video display
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("border: 1px solid black; background-color: black;")
        self.video_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.video_label)
        
        # Face selection
        face_layout = QHBoxLayout()
        face_layout.addWidget(QLabel("Current Face:"))
        
        self.face_combo = QComboBox()
        self.face_combo.addItems(['Up (U)', 'Right (R)', 'Front (F)', 
                                  'Down (D)', 'Left (L)', 'Back (B)'])
        self.face_combo.currentIndexChanged.connect(self.on_face_changed)
        face_layout.addWidget(self.face_combo)
        
        # Capture button
        self.capture_btn = QPushButton("Capture Face (Space)")
        self.capture_btn.clicked.connect(self.capture_face)
        face_layout.addWidget(self.capture_btn)
        
        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_scan)
        face_layout.addWidget(self.reset_btn)
        
        face_layout.addStretch()
        layout.addLayout(face_layout)
        
        # Status
        self.status_label = QLabel("Camera not started")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def toggle_camera(self):
        """Start or stop the camera"""
        if self.is_camera_active:
            self.stop_camera()
        else:
            self.start_camera()
            
    def start_camera(self):
        """Start camera capture"""
        if self.is_camera_active:
            return
            
        try:
            # Create and start camera thread
            camera_index = self.camera_combo.currentIndex()
            self.camera_thread = CameraThread(camera_index)
            self.camera_thread.frame_ready.connect(self.process_frame)
            self.camera_thread.error_occurred.connect(self.on_camera_error)
            self.camera_thread.start()
            
            # Update UI
            self.is_camera_active = True
            self.start_stop_btn.setText("Stop Camera")
            self.capture_btn.setEnabled(True)
            self.calibration_btn.setEnabled(True)
            self.status_label.setText("Camera running")
            
            # Start update timer
            self.update_timer.start(30)  # 30ms for ~33 FPS
            
            logger.info(f"Camera {camera_index} started")
            
        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            self.status_label.setText(f"Error: {e}")
            
    def stop_camera(self):
        """Stop camera capture"""
        if not self.is_camera_active:
            return
            
        try:
            # Stop update timer
            self.update_timer.stop()
            
            # Stop camera thread
            if self.camera_thread:
                self.camera_thread.stop()
                self.camera_thread.wait(2000)  # Wait max 2 seconds
                self.camera_thread = None
                
            # Clear display
            self.video_label.clear()
            self.video_label.setText("Camera stopped")
            
            # Update UI
            self.is_camera_active = False
            self.start_stop_btn.setText("Start Camera")
            self.capture_btn.setEnabled(False)
            self.calibration_btn.setEnabled(False)
            self.status_label.setText("Camera stopped")
            
            logger.info("Camera stopped")
            
        except Exception as e:
            logger.error(f"Error stopping camera: {e}")
            
    def on_camera_changed(self, index):
        """Handle camera selection change"""
        if self.is_camera_active:
            # Restart with new camera
            self.stop_camera()
            self.start_camera()
            
    def on_camera_error(self, error_msg):
        """Handle camera error"""
        logger.error(f"Camera error: {error_msg}")
        self.status_label.setText(f"Camera error: {error_msg}")
        self.stop_camera()
        
    def process_frame(self, frame):
        """Process a frame from the camera"""
        self.current_frame = frame
        
        # Create display frame
        self.display_frame = frame.copy()
        
        # Detect cube if in scanning mode
        if self.scanning_mode or self.calibration_mode:
            self.detect_cube()
            
        # Draw overlays
        self.draw_overlays()
        
        # Emit processed frame
        self.frame_processed.emit(self.display_frame)
        
    def detect_cube(self):
        """Detect cube in current frame"""
        if self.current_frame is None:
            return
            
        # Convert to grayscale
        gray = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY)
        
        # Apply blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 30, 60)
        
        # Dilation
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        dilated = cv2.dilate(edges, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter and sort contours
        self.contours = self.filter_cube_contours(contours)
        
        if len(self.contours) == 9:
            # Update preview colors
            self.update_preview_colors()
            
    def filter_cube_contours(self, contours):
        """Filter contours to find cube stickers"""
        filtered = []
        
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check size
            if w < CONTOUR_AREA_MIN or w > CONTOUR_AREA_MAX:
                continue
            if h < CONTOUR_AREA_MIN or h > CONTOUR_AREA_MAX:
                continue
                
            # Check aspect ratio
            aspect_ratio = w / float(h)
            if aspect_ratio < CONTOUR_ASPECT_RATIO_MIN or aspect_ratio > CONTOUR_ASPECT_RATIO_MAX:
                continue
                
            # Check if approximately square
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, CONTOUR_APPROXIMATION * peri, True)
            
            if len(approx) == 4:
                filtered.append((x, y, w, h))
                
        # Sort contours if we found 9
        if len(filtered) >= 9:
            # Find the 3x3 grid
            filtered = self.find_3x3_grid(filtered)
            
        return filtered[:9]  # Return max 9 contours
        
    def find_3x3_grid(self, contours):
        """Find and sort 3x3 grid of contours"""
        if len(contours) < 9:
            return contours
            
        # Sort by y coordinate (top to bottom)
        contours.sort(key=lambda c: c[1])
        
        # Split into 3 rows
        rows = []
        for i in range(0, min(9, len(contours)), 3):
            row = sorted(contours[i:i+3], key=lambda c: c[0])  # Sort by x
            rows.extend(row)
            
        return rows
        
    def update_preview_colors(self):
        """Update preview colors from detected contours"""
        if len(self.contours) != 9:
            return
            
        for i, (x, y, w, h) in enumerate(self.contours):
            # Extract ROI
            roi = self.current_frame[y+5:y+h-5, x+5:x+w-5]
            
            if roi.size == 0:
                continue
                
            # Get dominant color
            color = self.color_detector.get_dominant_color(roi)
            
            # Update average buffer
            if len(self.average_color_buffer[i]) >= 8:
                self.average_color_buffer[i].pop(0)
            self.average_color_buffer[i].append(color)
            
            # Calculate average color
            if len(self.average_color_buffer[i]) > 0:
                avg_color = np.mean(self.average_color_buffer[i], axis=0)
                self.preview_colors[i] = tuple(map(int, avg_color))
                
    def draw_overlays(self):
        """Draw overlays on display frame"""
        if self.display_frame is None:
            return
            
        # Draw contours
        if len(self.contours) == 9:
            for i, (x, y, w, h) in enumerate(self.contours):
                # Draw rectangle
                cv2.rectangle(self.display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Draw sticker number
                cv2.putText(self.display_frame, str(i+1), (x+5, y+20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                           
        # Draw guide square in center
        h, w = self.display_frame.shape[:2]
        size = 200
        x1, y1 = w//2 - size//2, h//2 - size//2
        x2, y2 = w//2 + size//2, h//2 + size//2
        
        cv2.rectangle(self.display_frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        
        # Draw instructions
        text = f"Scanning face: {self.current_face}"
        cv2.putText(self.display_frame, text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                   
        if len(self.contours) == 9:
            cv2.putText(self.display_frame, "Press SPACE to capture", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(self.display_frame, f"Detected: {len(self.contours)}/9 stickers", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                       
    def update_display(self):
        """Update the display with current frame"""
        if self.display_frame is not None:
            # Convert to QImage
            height, width, channel = self.display_frame.shape
            bytes_per_line = 3 * width
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(self.display_frame, cv2.COLOR_BGR2RGB)
            
            # Create QImage
            q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            # Scale to fit label
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Display
            self.video_label.setPixmap(scaled_pixmap)
            
    def toggle_calibration(self, checked):
        """Toggle calibration mode"""
        self.calibration_mode = checked
        
        if checked:
            self.scanning_mode = False
            self.status_label.setText("Calibration mode - Show each face color")
        else:
            self.scanning_mode = True
            self.status_label.setText("Scanning mode")
            
    def on_face_changed(self, index):
        """Handle face selection change"""
        faces = ['U', 'R', 'F', 'D', 'L', 'B']
        self.current_face = faces[index]
        
        # Clear average buffer for new face
        self.average_color_buffer = [[] for _ in range(9)]
        
    def capture_face(self):
        """Capture current face colors"""
        if len(self.preview_colors) != 9 or None in self.preview_colors:
            self.status_label.setText("Cannot capture - no valid detection")
            return
            
        # Convert colors to notation
        colors = []
        for color_bgr in self.preview_colors:
            color_name = self.color_detector.get_closest_color_name(color_bgr)
            color_code = COLOR_TO_NOTATION.get(color_name, 'X')
            colors.append(color_code)
            
        # Store captured face
        self.captured_faces[self.current_face] = colors
        self.snapshot_colors = self.preview_colors.copy()
        
        # Emit signal
        self.face_captured.emit(self.current_face, colors)
        
        # Update status
        captured_count = len(self.captured_faces)
        self.status_label.setText(f"Face {self.current_face} captured ({captured_count}/6)")
        
        # Auto-advance to next face
        if captured_count < 6:
            current_index = self.face_combo.currentIndex()
            if current_index < 5:
                self.face_combo.setCurrentIndex(current_index + 1)
        else:
            # All faces captured
            self.status_label.setText("All faces captured!")
            self.scan_completed.emit(self.captured_faces)
            
    def reset_scan(self):
        """Reset the scanning process"""
        self.captured_faces = {}
        self.preview_colors = [None] * 9
        self.snapshot_colors = [None] * 9
        self.average_color_buffer = [[] for _ in range(9)]
        self.contours = []
        
        self.face_combo.setCurrentIndex(0)
        self.status_label.setText("Scan reset")
        
    def update_calibration(self, calibration):
        """Update color detector calibration"""
        self.color_detector.set_calibration(calibration)
        self.status_label.setText("Calibration updated")
        
    def get_captured_cube(self):
        """Get the captured cube data"""
        return self.captured_faces
        
    def set_scanning_mode(self, enabled):
        """Enable or disable scanning mode"""
        self.scanning_mode = enabled
        
    def save_snapshot(self, filepath):
        """Save current frame to file"""
        if self.current_frame is not None:
            cv2.imwrite(str(filepath), self.current_frame)
            logger.info(f"Snapshot saved to {filepath}")
            
    def closeEvent(self, event):
        """Handle widget close"""
        self.stop_camera()
        event.accept()