#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Animation support for cube moves
"""

import logging
from typing import List, Dict, Optional, Callable
from PyQt5.QtCore import QTimer, QObject, pyqtSignal

logger = logging.getLogger(__name__)


class MoveAnimator(QObject):
    """Handles move animations"""
    
    animation_started = pyqtSignal(str)
    animation_finished = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self.current_move = None
        self.progress = 0.0
        self.speed = 500  # ms
        
    def animate(self, move: str):
        """Start animating a move"""
        self.current_move = move
        self.progress = 0.0
        self.animation_started.emit(move)
        self.timer.start(16)  # 60 FPS
        
    def _update(self):
        """Update animation progress"""
        if not self.current_move:
            self.timer.stop()
            return
            
        self.progress += 16.0 / self.speed
        
        if self.progress >= 1.0:
            self.progress = 1.0
            move = self.current_move
            self.current_move = None
            self.timer.stop()
            self.animation_finished.emit(move)