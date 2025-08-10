#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
3D Cube visualization widget

This module provides OpenGL-based 3D visualization of the Rubik's Cube.
"""

import numpy as np
import logging
import math
from typing import List, Tuple, Optional, Dict, Any

from PyQt5.QtWidgets import QOpenGLWidget, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QMatrix4x4, QVector3D, QQuaternion, QColor

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    logging.warning("OpenGL not available - 3D visualization disabled")

from visualizer import COLOR_SCHEMES, DisplayMode, ViewAngle

logger = logging.getLogger(__name__)


class Cube3DWidget(QOpenGLWidget if OPENGL_AVAILABLE else QWidget):
    """3D visualization widget for Rubik's Cube"""
    
    # Signals
    move_started = pyqtSignal(str)
    move_completed = pyqtSignal(str)
    rotation_changed = pyqtSignal(float, float, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Cube state (54 stickers)
        self.cube_state = ['U'] * 9 + ['R'] * 9 + ['F'] * 9 + ['D'] * 9 + ['L'] * 9 + ['B'] * 9
        
        # Display settings
        self.color_scheme = 'standard'
        self.display_mode = DisplayMode.NORMAL
        self.show_labels = False
        self.show_axes = False
        self.anti_aliasing = True
        self.sticker_gap = 0.9  # Size of stickers (0-1)
        
        # Camera/view settings
        self.zoom = 5.0
        self.rotation_x = 30.0
        self.rotation_y = -45.0
        self.rotation_z = 0.0
        self.camera_distance = 10.0
        
        # Animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.current_animation = None
        self.animation_progress = 0.0
        self.animation_speed = 500  # milliseconds
        
        # Mouse control
        self.last_mouse_pos = QPoint()
        self.mouse_pressed = False
        
        # OpenGL resources
        self.initialized = False
        self.vbo = None
        self.vao = None
        self.shader_program = None
        
        # Face definitions for 3x3x3 cube
        self.face_positions = self._generate_face_positions()
        
    def _generate_face_positions(self) -> Dict[str, List[Tuple[float, float, float]]]:
        """Generate 3D positions for all stickers"""
        positions = {}
        
        # Size of each sticker
        size = 0.9
        gap = 0.05
        
        # Generate positions for each face
        for face_idx, face in enumerate(['U', 'R', 'F', 'D', 'L', 'B']):
            face_positions = []
            
            for row in range(3):
                for col in range(3):
                    # Calculate position within face
                    x = (col - 1) * (size + gap)
                    y = (1 - row) * (size + gap)
                    z = 1.5
                    
                    # Transform based on face
                    if face == 'U':  # Top
                        pos = (x, z, y)
                    elif face == 'D':  # Bottom
                        pos = (x, -z, -y)
                    elif face == 'F':  # Front
                        pos = (x, y, z)
                    elif face == 'B':  # Back
                        pos = (-x, y, -z)
                    elif face == 'R':  # Right
                        pos = (z, y, -x)
                    elif face == 'L':  # Left
                        pos = (-z, y, x)
                    else:
                        pos = (x, y, z)
                    
                    face_positions.append(pos)
            
            positions[face] = face_positions
        
        return positions
    
    def initializeGL(self):
        """Initialize OpenGL"""
        if not OPENGL_AVAILABLE:
            return
        
        try:
            # Set clear color
            glClearColor(0.9, 0.9, 0.9, 1.0)
            
            # Enable depth testing
            glEnable(GL_DEPTH_TEST)
            glDepthFunc(GL_LESS)
            
            # Enable anti-aliasing
            if self.anti_aliasing:
                glEnable(GL_MULTISAMPLE)
                glEnable(GL_LINE_SMOOTH)
                glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
            
            # Enable lighting
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            
            # Set light properties
            glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 5.0, 5.0, 1.0])
            glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
            glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.7, 0.7, 0.7, 1.0])
            glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
            
            # Material properties
            glMaterialfv(GL_FRONT, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
            glMaterialf(GL_FRONT, GL_SHININESS, 32.0)
            
            self.initialized = True
            logger.info("OpenGL initialized successfully")
            
        except Exception as e:
            logger.error(f"OpenGL initialization failed: {e}")
            self.initialized = False
    
    def resizeGL(self, width: int, height: int):
        """Handle widget resize"""
        if not OPENGL_AVAILABLE or not self.initialized:
            return
        
        # Set viewport
        glViewport(0, 0, width, height)
        
        # Set projection matrix
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        aspect = width / height if height > 0 else 1.0
        gluPerspective(45.0, aspect, 0.1, 100.0)
        
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        """Paint the OpenGL scene"""
        if not OPENGL_AVAILABLE or not self.initialized:
            return
        
        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set up modelview matrix
        glLoadIdentity()
        
        # Move camera back
        glTranslatef(0.0, 0.0, -self.camera_distance)
        
        # Apply rotations
        glRotatef(self.rotation_x, 1.0, 0.0, 0.0)
        glRotatef(self.rotation_y, 0.0, 1.0, 0.0)
        glRotatef(self.rotation_z, 0.0, 0.0, 1.0)
        
        # Apply animation transformation if active
        if self.current_animation:
            self._apply_animation_transform()
        
        # Draw the cube
        self._draw_cube()
        
        # Draw axes if enabled
        if self.show_axes:
            self._draw_axes()
        
        # Draw labels if enabled
        if self.show_labels:
            self._draw_labels()
    
    def _draw_cube(self):
        """Draw the Rubik's Cube"""
        # Draw black cube body first
        glColor3f(0.0, 0.0, 0.0)
        self._draw_cube_body()
        
        # Draw stickers
        face_order = ['U', 'R', 'F', 'D', 'L', 'B']
        sticker_idx = 0
        
        for face in face_order:
            positions = self.face_positions[face]
            
            for i, pos in enumerate(positions):
                # Get sticker color
                color_code = self.cube_state[sticker_idx]
                color_hex = COLOR_SCHEMES[self.color_scheme].get(color_code, '#808080')
                color = QColor(color_hex)
                
                # Set color
                glColor3f(color.redF(), color.greenF(), color.blueF())
                
                # Draw sticker
                glPushMatrix()
                glTranslatef(*pos)
                
                # Determine sticker orientation
                if face in ['U', 'D']:
                    self._draw_sticker_horizontal(face == 'D')
                elif face in ['F', 'B']:
                    self._draw_sticker_front_back(face == 'B')
                else:  # R, L
                    self._draw_sticker_side(face == 'L')
                
                glPopMatrix()
                
                sticker_idx += 1
    
    def _draw_cube_body(self):
        """Draw the black cube body"""
        size = 1.5
        
        glBegin(GL_QUADS)
        
        # Front face
        glNormal3f(0.0, 0.0, 1.0)
        glVertex3f(-size, -size, size)
        glVertex3f(size, -size, size)
        glVertex3f(size, size, size)
        glVertex3f(-size, size, size)
        
        # Back face
        glNormal3f(0.0, 0.0, -1.0)
        glVertex3f(-size, -size, -size)
        glVertex3f(-size, size, -size)
        glVertex3f(size, size, -size)
        glVertex3f(size, -size, -size)
        
        # Top face
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(-size, size, -size)
        glVertex3f(-size, size, size)
        glVertex3f(size, size, size)
        glVertex3f(size, size, -size)
        
        # Bottom face
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(-size, -size, -size)
        glVertex3f(size, -size, -size)
        glVertex3f(size, -size, size)
        glVertex3f(-size, -size, size)
        
        # Right face
        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(size, -size, -size)
        glVertex3f(size, size, -size)
        glVertex3f(size, size, size)
        glVertex3f(size, -size, size)
        
        # Left face
        glNormal3f(-1.0, 0.0, 0.0)
        glVertex3f(-size, -size, -size)
        glVertex3f(-size, -size, size)
        glVertex3f(-size, size, size)
        glVertex3f(-size, size, -size)
        
        glEnd()
    
    def _draw_sticker_horizontal(self, flip: bool = False):
        """Draw a horizontal sticker (top/bottom face)"""
        size = self.sticker_gap * 0.4
        y = 0.01 if not flip else -0.01
        
        glBegin(GL_QUADS)
        
        if flip:
            glNormal3f(0.0, -1.0, 0.0)
            glVertex3f(-size, y, size)
            glVertex3f(size, y, size)
            glVertex3f(size, y, -size)
            glVertex3f(-size, y, -size)
        else:
            glNormal3f(0.0, 1.0, 0.0)
            glVertex3f(-size, y, -size)
            glVertex3f(size, y, -size)
            glVertex3f(size, y, size)
            glVertex3f(-size, y, size)
        
        glEnd()
    
    def _draw_sticker_front_back(self, flip: bool = False):
        """Draw a front/back face sticker"""
        size = self.sticker_gap * 0.4
        z = 0.01 if not flip else -0.01
        
        glBegin(GL_QUADS)
        
        if flip:
            glNormal3f(0.0, 0.0, -1.0)
            glVertex3f(size, -size, z)
            glVertex3f(-size, -size, z)
            glVertex3f(-size, size, z)
            glVertex3f(size, size, z)
        else:
            glNormal3f(0.0, 0.0, 1.0)
            glVertex3f(-size, -size, z)
            glVertex3f(size, -size, z)
            glVertex3f(size, size, z)
            glVertex3f(-size, size, z)
        
        glEnd()
    
    def _draw_sticker_side(self, flip: bool = False):
        """Draw a side face sticker (left/right)"""
        size = self.sticker_gap * 0.4
        x = -0.01 if flip else 0.01
        
        glBegin(GL_QUADS)
        
        if flip:
            glNormal3f(-1.0, 0.0, 0.0)
            glVertex3f(x, -size, size)
            glVertex3f(x, -size, -size)
            glVertex3f(x, size, -size)
            glVertex3f(x, size, size)
        else:
            glNormal3f(1.0, 0.0, 0.0)
            glVertex3f(x, -size, -size)
            glVertex3f(x, -size, size)
            glVertex3f(x, size, size)
            glVertex3f(x, size, -size)
        
        glEnd()
    
    def _draw_axes(self):
        """Draw coordinate axes"""
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        
        glBegin(GL_LINES)
        
        # X axis (red)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(3.0, 0.0, 0.0)
        
        # Y axis (green)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 3.0, 0.0)
        
        # Z axis (blue)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 3.0)
        
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    def _draw_labels(self):
        """Draw face labels"""
        # This would use bitmap fonts or textures to draw labels
        # Simplified implementation
        pass
    
    def _apply_animation_transform(self):
        """Apply transformation for current animation"""
        if not self.current_animation:
            return
        
        anim_type = self.current_animation['type']
        progress = self.current_animation['progress']
        
        if anim_type == 'move':
            move = self.current_animation['move']
            angle = self._get_move_angle(move, progress)
            axis = self._get_move_axis(move)
            
            # Apply rotation for the move
            if axis == 'x':
                glRotatef(angle, 1.0, 0.0, 0.0)
            elif axis == 'y':
                glRotatef(angle, 0.0, 1.0, 0.0)
            elif axis == 'z':
                glRotatef(angle, 0.0, 0.0, 1.0)
    
    def _get_move_angle(self, move: str, progress: float) -> float:
        """Get rotation angle for a move"""
        base_angle = 90.0
        
        if '2' in move:
            base_angle = 180.0
        elif "'" in move:
            base_angle = -90.0
        
        return base_angle * progress
    
    def _get_move_axis(self, move: str) -> str:
        """Get rotation axis for a move"""
        face = move[0]
        
        if face in ['U', 'D', 'E', 'y']:
            return 'y'
        elif face in ['R', 'L', 'M', 'x']:
            return 'x'
        elif face in ['F', 'B', 'S', 'z']:
            return 'z'
        
        return 'y'
    
    def set_cube_state(self, state: List[str]):
        """Set the cube state"""
        if len(state) != 54:
            logger.warning(f"Invalid state length: {len(state)}")
            return
        
        self.cube_state = state.copy()
        self.update()
    
    def set_color_scheme(self, scheme: str):
        """Set color scheme"""
        if scheme in COLOR_SCHEMES:
            self.color_scheme = scheme
            self.update()
    
    def set_display_mode(self, mode: DisplayMode):
        """Set display mode"""
        self.display_mode = mode
        self.update()
    
    def animate_move(self, move: str):
        """Animate a cube move"""
        self.current_animation = {
            'type': 'move',
            'move': move,
            'progress': 0.0,
            'start_time': 0
        }
        
        self.move_started.emit(move)
        self.animation_timer.start(16)  # ~60 FPS
    
    def update_animation(self):
        """Update animation state"""
        if not self.current_animation:
            self.animation_timer.stop()
            return
        
        # Update progress
        self.current_animation['progress'] += 16.0 / self.animation_speed
        
        if self.current_animation['progress'] >= 1.0:
            # Animation complete
            self.current_animation['progress'] = 1.0
            move = self.current_animation.get('move', '')
            
            # Apply the move to the state
            self._apply_move_to_state(move)
            
            self.current_animation = None
            self.animation_timer.stop()
            self.move_completed.emit(move)
        
        self.update()
    
    def _apply_move_to_state(self, move: str):
        """Apply a move to the cube state"""
        # This would update self.cube_state based on the move
        # Implementation depends on move notation
        pass
    
    def reset_view(self):
        """Reset camera to default view"""
        self.rotation_x = 30.0
        self.rotation_y = -45.0
        self.rotation_z = 0.0
        self.camera_distance = 10.0
        self.update()
    
    def set_view_angle(self, angle: ViewAngle):
        """Set predefined view angle"""
        angles = {
            ViewAngle.FRONT: (0, 0, 0),
            ViewAngle.BACK: (0, 180, 0),
            ViewAngle.TOP: (90, 0, 0),
            ViewAngle.BOTTOM: (-90, 0, 0),
            ViewAngle.LEFT: (0, 90, 0),
            ViewAngle.RIGHT: (0, -90, 0),
            ViewAngle.ISOMETRIC: (30, -45, 0)
        }
        
        if angle in angles:
            self.rotation_x, self.rotation_y, self.rotation_z = angles[angle]
            self.update()
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.LeftButton:
            self.mouse_pressed = True
            self.last_mouse_pos = event.pos()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self.mouse_pressed = False
    
    def mouseMoveEvent(self, event):
        """Handle mouse movement for rotation"""
        if not self.mouse_pressed:
            return
        
        # Calculate mouse delta
        delta = event.pos() - self.last_mouse_pos
        self.last_mouse_pos = event.pos()
        
        # Update rotation
        self.rotation_y += delta.x() * 0.5
        self.rotation_x += delta.y() * 0.5
        
        # Emit signal
        self.rotation_changed.emit(self.rotation_x, self.rotation_y, self.rotation_z)
        
        self.update()
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zoom"""
        delta = event.angleDelta().y()
        
        # Adjust camera distance
        self.camera_distance *= 1.0 - delta / 1000.0
        self.camera_distance = max(5.0, min(30.0, self.camera_distance))
        
        self.update()
    
    def keyPressEvent(self, event):
        """Handle keyboard input"""
        key = event.key()
        
        # Rotation controls
        if key == Qt.Key_Left:
            self.rotation_y -= 5
        elif key == Qt.Key_Right:
            self.rotation_y += 5
        elif key == Qt.Key_Up:
            self.rotation_x -= 5
        elif key == Qt.Key_Down:
            self.rotation_x += 5
        elif key == Qt.Key_Q:
            self.rotation_z -= 5
        elif key == Qt.Key_E:
            self.rotation_z += 5
        
        # Zoom controls
        elif key == Qt.Key_Plus or key == Qt.Key_Equal:
            self.camera_distance *= 0.9
        elif key == Qt.Key_Minus:
            self.camera_distance *= 1.1
        
        # Reset view
        elif key == Qt.Key_R:
            self.reset_view()
        
        self.update()
    
    def export_image(self, filepath: str):
        """Export current view as image"""
        pixmap = self.grab()
        pixmap.save(filepath)
        logger.info(f"Exported 3D view to {filepath}")