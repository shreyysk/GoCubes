#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
2D Cube visualization widget

This module provides a flat 2D representation of the Rubik's Cube.
"""

import logging
from typing import List, Tuple, Optional, Dict, Any

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath

from visualizer import COLOR_SCHEMES

logger = logging.getLogger(__name__)


class Cube2DWidget(QWidget):
    """2D flat visualization of Rubik's Cube"""
    
    # Signals
    sticker_clicked = pyqtSignal(str, int)  # face, position
    face_rotated = pyqtSignal(str, int)    # face, direction
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Cube state (54 stickers)
        self.cube_state = ['U'] * 9 + ['R'] * 9 + ['F'] * 9 + ['D'] * 9 + ['L'] * 9 + ['B'] * 9
        
        # Display settings
        self.color_scheme = 'standard'
        self.show_labels = True
        self.show_indices = False
        self.highlight_last_move = False
        self.sticker_size = 40
        self.gap_size = 2
        self.face_gap = 10
        
        # Layout mode
        self.layout_mode = 'cross'  # 'cross' or 'strip'
        
        # Animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animating_face = None
        self.animation_angle = 0
        self.animation_target = 0
        
        # Interaction
        self.hovering_sticker = None
        self.selected_stickers = []
        self.last_move_stickers = []
        
        # Set minimum size
        self.setMinimumSize(600, 450)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
    def paintEvent(self, event):
        """Paint the 2D cube representation"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Clear background
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        if self.layout_mode == 'cross':
            self._draw_cross_layout(painter)
        else:
            self._draw_strip_layout(painter)
            
        # Draw hover effect
        if self.hovering_sticker is not None:
            self._draw_hover_effect(painter)
            
        # Draw selection
        if self.selected_stickers:
            self._draw_selection(painter)
            
    def _draw_cross_layout(self, painter):
        """
        Draw cube in cross/net layout:
              U
            L F R B
              D
        """
        # Calculate positions for each face
        face_size = self.sticker_size * 3 + self.gap_size * 2
        
        positions = {
            'U': (face_size + self.face_gap, 0),
            'L': (0, face_size + self.face_gap),
            'F': (face_size + self.face_gap, face_size + self.face_gap),
            'R': (2 * (face_size + self.face_gap), face_size + self.face_gap),
            'B': (3 * (face_size + self.face_gap), face_size + self.face_gap),
            'D': (face_size + self.face_gap, 2 * (face_size + self.face_gap))
        }
        
        # Draw each face
        face_order = ['U', 'R', 'F', 'D', 'L', 'B']
        sticker_idx = 0
        
        for face in face_order:
            x, y = positions[face]
            
            # Draw face background
            painter.fillRect(x - 5, y - 5, 
                           face_size + 10, face_size + 10,
                           QColor(0, 0, 0))
            
            # Draw face label if enabled
            if self.show_labels:
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.setFont(QFont("Arial", 12, QFont.Bold))
                painter.drawText(int(x + face_size/2 - 5), int(y - 10), face)
            
            # Apply animation rotation if this face is animating
            if self.animating_face == face:
                painter.save()
                center = QPoint(x + face_size/2, y + face_size/2)
                painter.translate(center)
                painter.rotate(self.animation_angle)
                painter.translate(-center)
            
            # Draw stickers
            for row in range(3):
                for col in range(3):
                    sticker_x = x + col * (self.sticker_size + self.gap_size)
                    sticker_y = y + row * (self.sticker_size + self.gap_size)
                    
                    # Get sticker color
                    color_code = self.cube_state[sticker_idx]
                    color = self._get_color(color_code)
                    
                    # Check if this sticker should be highlighted
                    is_highlighted = sticker_idx in self.last_move_stickers
                    
                    # Draw sticker
                    self._draw_sticker(painter, sticker_x, sticker_y, 
                                     color, sticker_idx, is_highlighted)
                    
                    sticker_idx += 1
            
            # Restore painter if animating
            if self.animating_face == face:
                painter.restore()
                
    def _draw_strip_layout(self, painter):
        """
        Draw cube in strip layout:
        U R F D L B
        """
        face_size = self.sticker_size * 3 + self.gap_size * 2
        y = 50
        
        face_order = ['U', 'R', 'F', 'D', 'L', 'B']
        sticker_idx = 0
        
        for i, face in enumerate(face_order):
            x = i * (face_size + self.face_gap) + 10
            
            # Draw face background
            painter.fillRect(x - 5, y - 5,
                           face_size + 10, face_size + 10,
                           QColor(0, 0, 0))
            
            # Draw face label
            if self.show_labels:
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.setFont(QFont("Arial", 12, QFont.Bold))
                painter.drawText(int(x + face_size/2 - 5), int(y - 10), face)
            
            # Draw stickers
            for row in range(3):
                for col in range(3):
                    sticker_x = x + col * (self.sticker_size + self.gap_size)
                    sticker_y = y + row * (self.sticker_size + self.gap_size)
                    
                    color_code = self.cube_state[sticker_idx]
                    color = self._get_color(color_code)
                    
                    is_highlighted = sticker_idx in self.last_move_stickers
                    
                    self._draw_sticker(painter, sticker_x, sticker_y,
                                     color, sticker_idx, is_highlighted)
                    
                    sticker_idx += 1
                    
    def _draw_sticker(self, painter, x: int, y: int, color: QColor, 
                     index: int, highlighted: bool = False):
        """Draw a single sticker"""
        # Draw sticker background
        if highlighted and self.highlight_last_move:
            # Draw highlight border
            painter.setPen(QPen(QColor(255, 215, 0), 3))
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(x - 2, y - 2,
                                   self.sticker_size + 4,
                                   self.sticker_size + 4,
                                   5, 5)
        
        # Draw sticker
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(x, y, 
                              self.sticker_size, self.sticker_size,
                              3, 3)
        
        # Draw index if enabled
        if self.show_indices:
            painter.setPen(QPen(self._get_text_color(color), 1))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(int(x + 2), int(y + 12), str(index))
            
    def _draw_hover_effect(self, painter):
        """Draw hover effect on sticker"""
        if self.hovering_sticker is None:
            return
            
        # Get sticker position
        x, y = self._get_sticker_position(self.hovering_sticker)
        
        if x is not None and y is not None:
            # Draw hover border
            painter.setPen(QPen(QColor(100, 100, 255), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(x - 1, y - 1,
                                   self.sticker_size + 2,
                                   self.sticker_size + 2,
                                   4, 4)
            
    def _draw_selection(self, painter):
        """Draw selection indicators"""
        for sticker_idx in self.selected_stickers:
            x, y = self._get_sticker_position(sticker_idx)
            
            if x is not None and y is not None:
                # Draw selection border
                painter.setPen(QPen(QColor(255, 100, 100), 3))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(x - 2, y - 2,
                                       self.sticker_size + 4,
                                       self.sticker_size + 4,
                                       5, 5)
                
    def _get_color(self, color_code: str) -> QColor:
        """Get QColor for a color code"""
        hex_color = COLOR_SCHEMES[self.color_scheme].get(color_code, '#808080')
        return QColor(hex_color)
        
    def _get_text_color(self, bg_color: QColor) -> QColor:
        """Get contrasting text color for background"""
        # Calculate luminance
        r, g, b = bg_color.red(), bg_color.green(), bg_color.blue()
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # Return black or white based on luminance
        return QColor(0, 0, 0) if luminance > 0.5 else QColor(255, 255, 255)
        
    def _get_sticker_position(self, index: int) -> Tuple[Optional[int], Optional[int]]:
        """Get pixel position of a sticker by index"""
        if index < 0 or index >= 54:
            return None, None
            
        # Determine face and position within face
        face_idx = index // 9
        face_pos = index % 9
        row = face_pos // 3
        col = face_pos % 3
        
        face_size = self.sticker_size * 3 + self.gap_size * 2
        
        if self.layout_mode == 'cross':
            face_positions = {
                0: (face_size + self.face_gap, 0),  # U
                1: (2 * (face_size + self.face_gap), face_size + self.face_gap),  # R
                2: (face_size + self.face_gap, face_size + self.face_gap),  # F
                3: (face_size + self.face_gap, 2 * (face_size + self.face_gap)),  # D
                4: (0, face_size + self.face_gap),  # L
                5: (3 * (face_size + self.face_gap), face_size + self.face_gap),  # B
            }
            
            if face_idx in face_positions:
                face_x, face_y = face_positions[face_idx]
                x = face_x + col * (self.sticker_size + self.gap_size)
                y = face_y + row * (self.sticker_size + self.gap_size)
                return x, y
                
        else:  # strip layout
            face_x = face_idx * (face_size + self.face_gap) + 10
            face_y = 50
            x = face_x + col * (self.sticker_size + self.gap_size)
            y = face_y + row * (self.sticker_size + self.gap_size)
            return x, y
            
        return None, None
        
    def _get_sticker_at_pos(self, pos: QPoint) -> Optional[int]:
        """Get sticker index at mouse position"""
        for i in range(54):
            x, y = self._get_sticker_position(i)
            
            if x is not None and y is not None:
                rect = QRect(x, y, self.sticker_size, self.sticker_size)
                if rect.contains(pos):
                    return i
                    
        return None
        
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
            
    def set_layout_mode(self, mode: str):
        """Set layout mode ('cross' or 'strip')"""
        if mode in ['cross', 'strip']:
            self.layout_mode = mode
            self.update()
            
    def highlight_move(self, move: str):
        """Highlight stickers affected by a move"""
        self.last_move_stickers = self._get_move_stickers(move)
        self.update()
        
    def _get_move_stickers(self, move: str) -> List[int]:
        """Get sticker indices affected by a move"""
        face = move[0]
        
        # Map face to sticker indices
        face_map = {
            'U': list(range(0, 9)),
            'R': list(range(9, 18)),
            'F': list(range(18, 27)),
            'D': list(range(27, 36)),
            'L': list(range(36, 45)),
            'B': list(range(45, 54)),
        }
        
        if face in face_map:
            return face_map[face]
            
        # Handle slice moves
        if face == 'M':
            return [1, 4, 7, 19, 22, 25, 28, 31, 34, 46, 49, 52]
        elif face == 'E':
            return [3, 4, 5, 12, 13, 14, 21, 22, 23, 39, 40, 41]
        elif face == 'S':
            return [1, 4, 7, 10, 13, 16, 28, 31, 34, 37, 40, 43]
            
        return []
        
    def animate_move(self, move: str):
        """Animate a cube move"""
        face = move[0]
        
        if face in 'URFDLB':
            self.animating_face = face
            self.animation_angle = 0
            
            # Determine target angle
            if '2' in move:
                self.animation_target = 180
            elif "'" in move:
                self.animation_target = -90
            else:
                self.animation_target = 90
                
            self.animation_timer.start(16)  # ~60 FPS
            
    def update_animation(self):
        """Update animation state"""
        if self.animating_face is None:
            self.animation_timer.stop()
            return
            
        # Update angle
        step = 5 if abs(self.animation_target) == 90 else 10
        
        if self.animation_target > 0:
            self.animation_angle = min(self.animation_angle + step, self.animation_target)
        else:
            self.animation_angle = max(self.animation_angle - step, self.animation_target)
            
        # Check if complete
        if abs(self.animation_angle) >= abs(self.animation_target):
            self.animating_face = None
            self.animation_angle = 0
            self.animation_timer.stop()
            
        self.update()
        
    def mouseMoveEvent(self, event):
        """Handle mouse movement"""
        # Update hover sticker
        old_hover = self.hovering_sticker
        self.hovering_sticker = self._get_sticker_at_pos(event.pos())
        
        if old_hover != self.hovering_sticker:
            self.update()
            
    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.LeftButton:
            sticker = self._get_sticker_at_pos(event.pos())
            
            if sticker is not None:
                # Determine face and position
                face_idx = sticker // 9
                face_pos = sticker % 9
                faces = ['U', 'R', 'F', 'D', 'L', 'B']
                
                if face_idx < len(faces):
                    self.sticker_clicked.emit(faces[face_idx], face_pos)
                    
                # Toggle selection
                if event.modifiers() & Qt.ControlModifier:
                    if sticker in self.selected_stickers:
                        self.selected_stickers.remove(sticker)
                    else:
                        self.selected_stickers.append(sticker)
                else:
                    self.selected_stickers = [sticker]
                    
                self.update()
                
        elif event.button() == Qt.RightButton:
            # Clear selection
            self.selected_stickers.clear()
            self.update()
            
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        delta = event.angleDelta().y()
        
        # Adjust sticker size
        if delta > 0:
            self.sticker_size = min(self.sticker_size + 2, 80)
        else:
            self.sticker_size = max(self.sticker_size - 2, 20)
            
        self.update()
        
    def keyPressEvent(self, event):
        """Handle keyboard input"""
        key = event.key()
        
        # Toggle display options
        if key == Qt.Key_L:
            self.show_labels = not self.show_labels
        elif key == Qt.Key_I:
            self.show_indices = not self.show_indices
        elif key == Qt.Key_H:
            self.highlight_last_move = not self.highlight_last_move
        elif key == Qt.Key_Space:
            # Toggle layout mode
            self.layout_mode = 'strip' if self.layout_mode == 'cross' else 'cross'
            
        self.update()
        
    def export_image(self, filepath: str):
        """Export current view as image"""
        from PyQt5.QtGui import QPixmap
        
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        pixmap.save(filepath)
        
        logger.info(f"Exported 2D view to {filepath}")
        
    def print_state(self):
        """Print cube state to console"""
        print("\nCube State (2D Layout):")
        print("=" * 40)
        
        # Print in net format
        faces = ['U', 'R', 'F', 'D', 'L', 'B']
        
        for face_idx, face in enumerate(faces):
            print(f"\n{face} face:")
            start = face_idx * 9
            
            for row in range(3):
                row_start = start + row * 3
                row_colors = self.cube_state[row_start:row_start + 3]
                print("  " + " ".join(row_colors))