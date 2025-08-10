#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main GUI window for Rubik Ultimate Solver

This module implements the main application window with all UI components.
"""

import sys
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

# Qt imports
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QGroupBox, QSplitter, QMenuBar, QMenu,
    QAction, QToolBar, QStatusBar, QMessageBox, QFileDialog,
    QComboBox, QSpinBox, QCheckBox, QSlider, QTabWidget,
    QListWidget, QTextEdit, QDockWidget, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QStyle,
    QGraphicsView, QGraphicsScene, QApplication, QDialog  # <-- Add QDialog here
)

from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, pyqtSlot, QThread, 
    QSize, QPoint, QRect, QPropertyAnimation, QEasingCurve
)
from PyQt5.QtGui import (
    QIcon, QPixmap, QFont, QPalette, QColor,
    QKeySequence, QPainter, QBrush, QPen
)

# Import application modules
# Import application modules - add error handling
try:
    from scanner.webcam import WebcamWidget
    from scanner.cube_scanner import CubeScanner
    from visualizer.cube_3d import Cube3DWidget
    from visualizer.cube_2d import Cube2DWidget
    from solver.cube_model import CubeModel
    from solver.kociemba_solver import KociembaSolver
    from solver.thistlethwaite import ThistlethwaiteSolver
    from utils.constants import *
    from utils.helpers import format_time, validate_scramble
    from utils.translator import tr
except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
    raise

import logging
logger = logging.getLogger(__name__)


class SolutionPanel(QWidget):
    """Panel for displaying and controlling the solution"""
    
    move_selected = pyqtSignal(int)
    play_clicked = pyqtSignal()
    speed_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.solution = []
        self.current_move = -1
        self.is_playing = False
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout()
        
        # Solution info
        info_layout = QHBoxLayout()
        self.info_label = QLabel(tr("No solution"))
        self.move_count_label = QLabel(tr("Moves: 0"))
        self.time_label = QLabel(tr("Time: 0.00s"))
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        info_layout.addWidget(self.move_count_label)
        info_layout.addWidget(self.time_label)
        layout.addLayout(info_layout)
        
        # Move list
        self.move_list = QListWidget()
        self.move_list.setFlow(QListWidget.LeftToRight)
        self.move_list.setWrapping(True)
        self.move_list.setResizeMode(QListWidget.Adjust)
        self.move_list.currentRowChanged.connect(self.on_move_selected)
        layout.addWidget(self.move_list)
        
        # Playback controls
        controls_layout = QHBoxLayout()
        
        self.first_btn = QPushButton("⏮")
        self.first_btn.setToolTip(tr("First move"))
        self.first_btn.clicked.connect(self.go_first)
        
        self.prev_btn = QPushButton("⏪")
        self.prev_btn.setToolTip(tr("Previous move"))
        self.prev_btn.clicked.connect(self.go_previous)
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setToolTip(tr("Play/Pause"))
        self.play_btn.clicked.connect(self.toggle_play)
        
        self.next_btn = QPushButton("⏩")
        self.next_btn.setToolTip(tr("Next move"))
        self.next_btn.clicked.connect(self.go_next)
        
        self.last_btn = QPushButton("⏭")
        self.last_btn.setToolTip(tr("Last move"))
        self.last_btn.clicked.connect(self.go_last)
        
        controls_layout.addWidget(self.first_btn)
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.next_btn)
        controls_layout.addWidget(self.last_btn)
        
        # Speed control
        controls_layout.addStretch()
        controls_layout.addWidget(QLabel(tr("Speed:")))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(100, 2000)
        self.speed_slider.setValue(500)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(300)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        controls_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("500ms")
        controls_layout.addWidget(self.speed_label)
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
        self.update_controls()
        
    def set_solution(self, solution: List[str], time_taken: float = 0):
        """Set the solution to display"""
        self.solution = solution
        self.current_move = -1
        self.is_playing = False
        
        # Update info
        self.info_label.setText(tr("Solution found"))
        self.move_count_label.setText(tr("Moves: {}").format(len(solution)))
        self.time_label.setText(tr("Time: {:.2f}s").format(time_taken))
        
        # Update move list
        self.move_list.clear()
        for move in solution:
            self.move_list.addItem(move)
        
        self.update_controls()
        
    def clear_solution(self):
        """Clear the current solution"""
        self.solution = []
        self.current_move = -1
        self.is_playing = False
        self.move_list.clear()
        self.info_label.setText(tr("No solution"))
        self.move_count_label.setText(tr("Moves: 0"))
        self.time_label.setText(tr("Time: 0.00s"))
        self.update_controls()
        
    def update_controls(self):
        """Update control button states"""
        has_solution = len(self.solution) > 0
        
        self.first_btn.setEnabled(has_solution and self.current_move > 0)
        self.prev_btn.setEnabled(has_solution and self.current_move > 0)
        self.play_btn.setEnabled(has_solution)
        self.next_btn.setEnabled(has_solution and self.current_move < len(self.solution) - 1)
        self.last_btn.setEnabled(has_solution and self.current_move < len(self.solution) - 1)
        
        if self.is_playing:
            self.play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶")
            
    def on_move_selected(self, index):
        """Handle move selection"""
        if index >= 0 and index < len(self.solution):
            self.current_move = index
            self.move_selected.emit(index)
            self.update_controls()
            
    def go_first(self):
        """Go to first move"""
        if self.solution:
            self.move_list.setCurrentRow(0)
            
    def go_previous(self):
        """Go to previous move"""
        if self.current_move > 0:
            self.move_list.setCurrentRow(self.current_move - 1)
            
    def go_next(self):
        """Go to next move"""
        if self.current_move < len(self.solution) - 1:
            self.move_list.setCurrentRow(self.current_move + 1)
            
    def go_last(self):
        """Go to last move"""
        if self.solution:
            self.move_list.setCurrentRow(len(self.solution) - 1)
            
    def toggle_play(self):
        """Toggle play/pause"""
        self.is_playing = not self.is_playing
        self.update_controls()
        self.play_clicked.emit()
        
    def on_speed_changed(self, value):
        """Handle speed slider change"""
        self.speed_label.setText(f"{value}ms")
        self.speed_changed.emit(value)


class CubeEditWidget(QWidget):
    """Widget for editing cube colors"""
    
    cube_changed = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cube_model = CubeModel()
        self.selected_color = 'white'
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout()
        
        # Color palette
        palette_group = QGroupBox(tr("Color Palette"))
        palette_layout = QHBoxLayout()
        
        self.color_buttons = {}
        colors = ['white', 'yellow', 'red', 'orange', 'green', 'blue']
        color_values = {
            'white': '#FFFFFF',
            'yellow': '#FFFF00',
            'red': '#FF0000',
            'orange': '#FFA500',
            'green': '#00FF00',
            'blue': '#0000FF'
        }
        
        for color in colors:
            btn = QPushButton()
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(f"background-color: {color_values[color]}; border: 2px solid black;")
            btn.clicked.connect(lambda checked, c=color: self.select_color(c))
            self.color_buttons[color] = btn
            palette_layout.addWidget(btn)
            
        palette_group.setLayout(palette_layout)
        layout.addWidget(palette_group)
        
        # Face selection
        face_group = QGroupBox(tr("Edit Face"))
        face_layout = QGridLayout()
        
        self.face_combo = QComboBox()
        self.face_combo.addItems(['Up (U)', 'Right (R)', 'Front (F)', 'Down (D)', 'Left (L)', 'Back (B)'])
        self.face_combo.currentIndexChanged.connect(self.on_face_changed)
        face_layout.addWidget(QLabel(tr("Face:")), 0, 0)
        face_layout.addWidget(self.face_combo, 0, 1)
        
        # Face grid editor
        self.face_grid = QGridLayout()
        self.sticker_buttons = []
        
        for row in range(3):
            row_buttons = []
            for col in range(3):
                btn = QPushButton()
                btn.setFixedSize(50, 50)
                btn.clicked.connect(lambda checked, r=row, c=col: self.edit_sticker(r, c))
                self.face_grid.addWidget(btn, row, col)
                row_buttons.append(btn)
            self.sticker_buttons.append(row_buttons)
            
        face_layout.addLayout(self.face_grid, 1, 0, 1, 2)
        face_group.setLayout(face_layout)
        layout.addWidget(face_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton(tr("Reset"))
        self.reset_btn.clicked.connect(self.reset_cube)
        
        self.clear_btn = QPushButton(tr("Clear"))
        self.clear_btn.clicked.connect(self.clear_cube)
        
        self.validate_btn = QPushButton(tr("Validate"))
        self.validate_btn.clicked.connect(self.validate_cube)
        
        action_layout.addWidget(self.reset_btn)
        action_layout.addWidget(self.clear_btn)
        action_layout.addWidget(self.validate_btn)
        layout.addLayout(action_layout)
        
        self.setLayout(layout)
        self.select_color('white')
        self.update_face_display()
        
    def select_color(self, color):
        """Select a color for editing"""
        self.selected_color = color
        
        # Update button borders
        for c, btn in self.color_buttons.items():
            if c == color:
                btn.setStyleSheet(btn.styleSheet().replace("border: 2px solid black;", "border: 4px solid blue;"))
            else:
                btn.setStyleSheet(btn.styleSheet().replace("border: 4px solid blue;", "border: 2px solid black;"))
                
    def on_face_changed(self, index):
        """Handle face selection change"""
        self.update_face_display()
        
    def update_face_display(self):
        """Update the face grid display"""
        face_map = ['U', 'R', 'F', 'D', 'L', 'B']
        face = face_map[self.face_combo.currentIndex()]
        
        colors = self.cube_model.get_face_colors(face)
        color_values = {
            'W': '#FFFFFF',
            'Y': '#FFFF00',
            'R': '#FF0000',
            'O': '#FFA500',
            'G': '#00FF00',
            'B': '#0000FF',
            'X': '#808080'  # Unknown/empty
        }
        
        for row in range(3):
            for col in range(3):
                color_code = colors[row * 3 + col]
                color = color_values.get(color_code, '#808080')
                self.sticker_buttons[row][col].setStyleSheet(f"background-color: {color};")
                
    def edit_sticker(self, row, col):
        """Edit a sticker color"""
        face_map = ['U', 'R', 'F', 'D', 'L', 'B']
        face = face_map[self.face_combo.currentIndex()]
        
        color_map = {
            'white': 'W',
            'yellow': 'Y',
            'red': 'R',
            'orange': 'O',
            'green': 'G',
            'blue': 'B'
        }
        
        position = row * 3 + col
        self.cube_model.set_sticker(face, position, color_map[self.selected_color])
        self.update_face_display()
        self.cube_changed.emit(self.cube_model)
        
    def reset_cube(self):
        """Reset cube to solved state"""
        self.cube_model.reset()
        self.update_face_display()
        self.cube_changed.emit(self.cube_model)
        
    def clear_cube(self):
        """Clear all cube colors"""
        self.cube_model.clear()
        self.update_face_display()
        self.cube_changed.emit(self.cube_model)
        
    def validate_cube(self):
        """Validate the cube configuration"""
        is_valid, error = self.cube_model.validate()
        
        if is_valid:
            QMessageBox.information(self, tr("Valid"), tr("Cube configuration is valid!"))
        else:
            QMessageBox.warning(self, tr("Invalid"), tr("Cube configuration is invalid:\n{}").format(error))
            
    def set_cube_model(self, cube_model):
        """Set the cube model"""
        self.cube_model = cube_model
        self.update_face_display()


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.cube_model = CubeModel()
        self.scanner = None
        self.solver = None
        self.current_solution = []
        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self.play_next_move)
        
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.load_settings()
        
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel - Scanner/Editor
        left_panel = QTabWidget()
        
        # Scanner tab
        self.webcam_widget = WebcamWidget()
        self.webcam_widget.frame_processed.connect(self.on_frame_processed)
        self.webcam_widget.face_captured.connect(self.on_face_captured)
        left_panel.addTab(self.webcam_widget, tr("Scanner"))
        
        # Editor tab
        self.editor_widget = CubeEditWidget()
        self.editor_widget.cube_changed.connect(self.on_cube_changed)
        left_panel.addTab(self.editor_widget, tr("Editor"))
        
        main_layout.addWidget(left_panel, 1)
        
        # Center panel - Visualization
        center_panel = QTabWidget()
        
        # 3D view
        self.cube_3d = Cube3DWidget()
        center_panel.addTab(self.cube_3d, tr("3D View"))
        
        # 2D view
        self.cube_2d = Cube2DWidget()
        center_panel.addTab(self.cube_2d, tr("2D View"))
        
        main_layout.addWidget(center_panel, 2)
        
        # Right panel - Solution
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Solver controls
        solver_group = QGroupBox(tr("Solver"))
        solver_layout = QGridLayout()
        
        solver_layout.addWidget(QLabel(tr("Algorithm:")), 0, 0)
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(['Kociemba', 'Thistlethwaite', 'Optimal'])
        solver_layout.addWidget(self.algorithm_combo, 0, 1)
        
        self.solve_btn = QPushButton(tr("Solve"))
        self.solve_btn.clicked.connect(self.solve_cube)
        solver_layout.addWidget(self.solve_btn, 1, 0, 1, 2)
        
        solver_group.setLayout(solver_layout)
        right_layout.addWidget(solver_group)
        
        # Solution panel
        self.solution_panel = SolutionPanel()
        self.solution_panel.move_selected.connect(self.on_move_selected)
        self.solution_panel.play_clicked.connect(self.on_play_clicked)
        self.solution_panel.speed_changed.connect(self.on_speed_changed)
        right_layout.addWidget(self.solution_panel)
        
        # Scramble controls
        scramble_group = QGroupBox(tr("Scramble"))
        scramble_layout = QVBoxLayout()
        
        self.scramble_input = QTextEdit()
        self.scramble_input.setMaximumHeight(60)
        scramble_layout.addWidget(self.scramble_input)
        
        scramble_btn_layout = QHBoxLayout()
        
        self.apply_scramble_btn = QPushButton(tr("Apply"))
        self.apply_scramble_btn.clicked.connect(self.apply_scramble)
        
        self.random_scramble_btn = QPushButton(tr("Random"))
        self.random_scramble_btn.clicked.connect(self.generate_random_scramble)
        
        self.clear_scramble_btn = QPushButton(tr("Clear"))
        self.clear_scramble_btn.clicked.connect(self.clear_scramble)
        
        scramble_btn_layout.addWidget(self.apply_scramble_btn)
        scramble_btn_layout.addWidget(self.random_scramble_btn)
        scramble_btn_layout.addWidget(self.clear_scramble_btn)
        scramble_layout.addLayout(scramble_btn_layout)
        
        scramble_group.setLayout(scramble_layout)
        right_layout.addWidget(scramble_group)
        
        right_layout.addStretch()
        main_layout.addWidget(right_panel, 1)
        
    def setup_menu(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu(tr("&File"))
        
        new_action = QAction(tr("&New"), self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_cube)
        file_menu.addAction(new_action)
        
        open_action = QAction(tr("&Open..."), self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction(tr("&Save..."), self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(tr("E&xit"), self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu(tr("&Edit"))
        
        undo_action = QAction(tr("&Undo"), self)
        undo_action.setShortcut(QKeySequence.Undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction(tr("&Redo"), self)
        redo_action.setShortcut(QKeySequence.Redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        copy_action = QAction(tr("&Copy Scramble"), self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_scramble)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction(tr("&Paste Scramble"), self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste_scramble)
        edit_menu.addAction(paste_action)
        
        # View menu
        view_menu = menubar.addMenu(tr("&View"))
        
        fullscreen_action = QAction(tr("&Fullscreen"), self)
        fullscreen_action.setShortcut(QKeySequence.FullScreen)
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Tools menu
        tools_menu = menubar.addMenu(tr("&Tools"))
        
        calibrate_action = QAction(tr("&Calibrate Colors"), self)
        calibrate_action.setShortcut("F8")
        calibrate_action.triggered.connect(self.calibrate_colors)
        tools_menu.addAction(calibrate_action)
        
        settings_action = QAction(tr("&Settings..."), self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu(tr("&Help"))
        
        help_action = QAction(tr("&Help"), self)
        help_action.setShortcut(QKeySequence.HelpContents)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction(tr("&About"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        """Setup the toolbar"""
        toolbar = self.addToolBar(tr("Main"))
        toolbar.setMovable(False)
        
        # Add actions
        new_action = toolbar.addAction(self.style().standardIcon(QStyle.SP_FileIcon), tr("New"))
        new_action.triggered.connect(self.new_cube)
        
        open_action = toolbar.addAction(self.style().standardIcon(QStyle.SP_DirOpenIcon), tr("Open"))
        open_action.triggered.connect(self.open_file)
        
        save_action = toolbar.addAction(self.style().standardIcon(QStyle.SP_DriveFDIcon), tr("Save"))
        save_action.triggered.connect(self.save_file)
        
        toolbar.addSeparator()
        
        scan_action = toolbar.addAction(tr("Scan"))
        scan_action.triggered.connect(self.start_scanning)
        
        solve_action = toolbar.addAction(tr("Solve"))
        solve_action.triggered.connect(self.solve_cube)
        
        toolbar.addSeparator()
        
        reset_action = toolbar.addAction(tr("Reset"))
        reset_action.triggered.connect(self.reset_cube)
        
    def setup_statusbar(self):
        """Setup the status bar"""
        self.statusbar = self.statusBar()
        
        # Add permanent widgets
        self.status_label = QLabel(tr("Ready"))
        self.statusbar.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress_bar)
        
        self.camera_status = QLabel(tr("Camera: Off"))
        self.statusbar.addPermanentWidget(self.camera_status)
        
    def load_settings(self):
        """Load application settings"""
        from utils import config
        
        # Load window geometry
        geometry = config.get('window.geometry')
        if geometry:
            self.restoreGeometry(geometry)
            
        # Load other settings
        algorithm = config.get('solver.default_algorithm', 'kociemba')
        index = {'kociemba': 0, 'thistlethwaite': 1, 'optimal': 2}.get(algorithm, 0)
        self.algorithm_combo.setCurrentIndex(index)
        
    def save_settings(self):
        """Save application settings"""
        from utils import config
        
        # Save window geometry
        config.set('window.geometry', self.saveGeometry())
        
        # Save other settings
        algorithms = ['kociemba', 'thistlethwaite', 'optimal']
        config.set('solver.default_algorithm', algorithms[self.algorithm_combo.currentIndex()])
        
        config.save()
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.save_settings()
        
        if self.webcam_widget:
            self.webcam_widget.stop_camera()
            
        event.accept()
        
    # Slot implementations
    def new_cube(self):
        """Create a new cube"""
        self.cube_model.reset()
        self.update_visualization()
        self.solution_panel.clear_solution()
        self.scramble_input.clear()
        self.status_label.setText(tr("New cube created"))
        
    def open_file(self):
        """Open a scramble file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            tr("Open Scramble"),
            "",
            tr("Text Files (*.txt);;All Files (*.*)")
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    scramble = f.read().strip()
                self.scramble_input.setPlainText(scramble)
                self.apply_scramble()
                self.status_label.setText(tr("Loaded: {}").format(Path(filename).name))
            except Exception as e:
                QMessageBox.critical(self, tr("Error"), tr("Failed to load file:\n{}").format(e))
                
    def save_file(self):
        """Save the current solution"""
        if not self.current_solution:
            QMessageBox.information(self, tr("Info"), tr("No solution to save"))
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self,
            tr("Save Solution"),
            "",
            tr("Text Files (*.txt);;All Files (*.*)")
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("Scramble:\n")
                    f.write(self.scramble_input.toPlainText() + "\n\n")
                    f.write("Solution:\n")
                    f.write(" ".join(self.current_solution) + "\n")
                self.status_label.setText(tr("Saved: {}").format(Path(filename).name))
            except Exception as e:
                QMessageBox.critical(self, tr("Error"), tr("Failed to save file:\n{}").format(e))
                
    def start_scanning(self):
        """Start webcam scanning"""
        self.webcam_widget.start_camera()
        self.camera_status.setText(tr("Camera: On"))
        
    def solve_cube(self):
        """Solve the current cube"""
        # Validate cube first
        is_valid, error = self.cube_model.validate()
        if not is_valid:
            QMessageBox.warning(self, tr("Invalid Cube"), tr("Cannot solve:\n{}").format(error))
            return
            
        # Get algorithm
        algorithms = ['kociemba', 'thistlethwaite', 'optimal']
        algorithm = algorithms[self.algorithm_combo.currentIndex()]
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(tr("Solving..."))
        
        # Solve in thread
        self.solve_thread = SolveThread(self.cube_model, algorithm)
        self.solve_thread.finished.connect(self.on_solve_finished)
        self.solve_thread.start()
        
    def on_solve_finished(self, solution, time_taken):
        """Handle solve completion"""
        self.progress_bar.setVisible(False)
        if solution:
            self.current_solution = solution
            self.solution_panel.set_solution(solution, time_taken)
            self.status_label.setText(tr("Solved in {:.2f}s - {} moves").format(time_taken, len(solution)))
        else:
            QMessageBox.critical(self, tr("Error"), tr("Failed to find solution"))
            self.status_label.setText(tr("Solve failed"))
            
    def reset_cube(self):
        """Reset the cube to solved state"""
        self.cube_model.reset()
        self.update_visualization()
        self.solution_panel.clear_solution()
        self.status_label.setText(tr("Cube reset"))
        
    def apply_scramble(self):
        """Apply the scramble from input"""
        scramble = self.scramble_input.toPlainText().strip()
        
        if not scramble:
            QMessageBox.information(self, tr("Info"), tr("Please enter a scramble"))
            return
            
        if not validate_scramble(scramble):
            QMessageBox.warning(self, tr("Invalid"), tr("Invalid scramble notation"))
            return
            
        # Reset and apply scramble
        self.cube_model.reset()
        moves = scramble.split()
        
        for move in moves:
            self.cube_model.apply_move(move)
            
        self.update_visualization()
        self.solution_panel.clear_solution()
        self.status_label.setText(tr("Scramble applied: {} moves").format(len(moves)))
        
    def generate_random_scramble(self):
        """Generate a random scramble"""
        from solver.moves import generate_random_scramble
        
        length = 25  # Default scramble length
        scramble = generate_random_scramble(length)
        self.scramble_input.setPlainText(scramble)
        self.apply_scramble()
        
    def clear_scramble(self):
        """Clear the scramble input"""
        self.scramble_input.clear()
        
    def copy_scramble(self):
        """Copy scramble to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.scramble_input.toPlainText())
        self.status_label.setText(tr("Scramble copied"))
        
    def paste_scramble(self):
        """Paste scramble from clipboard"""
        clipboard = QApplication.clipboard()
        self.scramble_input.setPlainText(clipboard.text())
        
    def toggle_fullscreen(self, checked):
        """Toggle fullscreen mode"""
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()
            
    def calibrate_colors(self):
        """Open color calibration dialog"""
        from scanner.calibration import CalibrationDialog
        
        dialog = CalibrationDialog(self)
        if dialog.exec_():
            # Update color detection with new calibration
            self.webcam_widget.update_calibration(dialog.get_calibration())
            self.status_label.setText(tr("Color calibration updated"))
            
    def show_settings(self):
        """Show settings dialog"""
        from dialogs.settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(self)
        if dialog.exec_():
            # Apply new settings
            self.load_settings()
            self.status_label.setText(tr("Settings updated"))
            
    def show_help(self):
        """Show help dialog"""
        QMessageBox.information(
            self,
            tr("Help"),
            tr("Rubik Ultimate Solver\n\n"
               "1. Use Scanner tab to scan your cube with webcam\n"
               "2. Or use Editor tab to manually input colors\n"
               "3. Click Solve to find the solution\n"
               "4. Use playback controls to see the solution\n\n"
               "Keyboard Shortcuts:\n"
               "Space - Capture face (scanner)\n"
               "Enter - Solve cube\n"
               "Arrow keys - Navigate solution")
        )
        
    def show_about(self):
        """Show about dialog"""
        __version__ = "1.0.0"  # Or import from a proper location
        
        QMessageBox.about(
            self,
            tr("About"),
            tr("Rubik Ultimate Solver v{}\n\n"
               "A comprehensive Rubik's Cube solver with:\n"
               "- Webcam scanning\n"
               "- Multiple solving algorithms\n"
               "- 3D visualization\n\n"
               "Created with Python, OpenCV, and PyQt5").format(__version__)
        )
        
    def on_frame_processed(self, frame):
        """Handle processed frame from webcam"""
        # Frame is already displayed in WebcamWidget
        pass
        
    def on_face_captured(self, face, colors):
        """Handle captured face from scanner"""
        # Update cube model with captured colors
        face_map = {'U': 0, 'R': 1, 'F': 2, 'D': 3, 'L': 4, 'B': 5}
        
        if face in face_map:
            for i, color in enumerate(colors):
                self.cube_model.set_sticker(face, i, color)
                
            self.update_visualization()
            self.status_label.setText(tr("Face {} captured").format(face))
            
            # Check if all faces captured
            if self.cube_model.is_complete():
                self.status_label.setText(tr("All faces captured - ready to solve"))
                
    def on_cube_changed(self, cube_model):
        """Handle cube model changes from editor"""
        self.cube_model = cube_model
        self.update_visualization()
        
    def update_visualization(self):
        """Update the cube visualization"""
        self.cube_3d.set_cube_state(self.cube_model.get_state())
        self.cube_2d.set_cube_state(self.cube_model.get_state())
        
    def on_move_selected(self, index):
        """Handle move selection from solution panel"""
        if index >= 0 and index < len(self.current_solution):
            # Reset cube and apply moves up to selected index
            self.cube_model.reset()
            
            # Apply scramble first
            scramble = self.scramble_input.toPlainText().strip()
            if scramble:
                for move in scramble.split():
                    self.cube_model.apply_move(move)
                    
            # Apply solution moves up to selected index
            for i in range(index + 1):
                self.cube_model.apply_move(self.current_solution[i])
                
            self.update_visualization()
            
    def on_play_clicked(self):
        """Handle play/pause button click"""
        if self.solution_panel.is_playing:
            # Start playing
            self.play_timer.start(self.solution_panel.speed_slider.value())
        else:
            # Stop playing
            self.play_timer.stop()
            
    def on_speed_changed(self, speed):
        """Handle animation speed change"""
        if self.play_timer.isActive():
            self.play_timer.setInterval(speed)
            
    def play_next_move(self):
        """Play the next move in solution"""
        current = self.solution_panel.current_move
        
        if current < len(self.current_solution) - 1:
            self.solution_panel.go_next()
        else:
            # Reached end, stop playing
            self.solution_panel.is_playing = False
            self.solution_panel.update_controls()
            self.play_timer.stop()
            
    def keyPressEvent(self, event):
        """Handle key press events"""
        key = event.key()
        
        if key == Qt.Key_Space:
            # Capture face in scanner mode
            if self.webcam_widget.isVisible():
                self.webcam_widget.capture_face()
                
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            # Solve cube
            self.solve_cube()
            
        elif key == Qt.Key_Left:
            # Previous move
            self.solution_panel.go_previous()
            
        elif key == Qt.Key_Right:
            # Next move
            self.solution_panel.go_next()
            
        elif key == Qt.Key_Home:
            # First move
            self.solution_panel.go_first()
            
        elif key == Qt.Key_End:
            # Last move
            self.solution_panel.go_last()
            
        else:
            super().keyPressEvent(event)


class SolveThread(QThread):
    """Thread for solving the cube"""
    
    finished = pyqtSignal(list, float)
    
    def __init__(self, cube_model, algorithm):
        super().__init__()
        self.cube_model = cube_model
        self.algorithm = algorithm
        
    def run(self):
        """Run the solver"""
        try:
            start_time = time.time()
            
            if self.algorithm == 'kociemba':
                solver = KociembaSolver()
            elif self.algorithm == 'thistlethwaite':
                solver = ThistlethwaiteSolver()
            else:
                # Optimal solver (placeholder)
                solver = KociembaSolver()
                
            # Get cube string representation
            cube_string = self.cube_model.to_string()
            
            # Solve
            solution = solver.solve(cube_string)
            
            # Parse solution
            if solution:
                moves = solution.strip().split()
                time_taken = time.time() - start_time
                self.finished.emit(moves, time_taken)
            else:
                self.finished.emit([], 0)
                
        except Exception as e:
            logger.error(f"Solve failed: {e}", exc_info=True)
            self.finished.emit([], 0)


class CalibrationDialog(QDialog):
    """Dialog for color calibration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Color Calibration"))
        self.setModal(True)
        self.calibration = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            tr("Place each face of a solved cube in front of the camera\n"
               "and click 'Capture' to calibrate colors.")
        )
        layout.addWidget(instructions)
        
        # Color grid
        grid = QGridLayout()
        
        self.color_samples = {}
        colors = ['White', 'Yellow', 'Red', 'Orange', 'Green', 'Blue']
        
        for i, color in enumerate(colors):
            label = QLabel(tr(color))
            sample = QLabel()
            sample.setFixedSize(50, 50)
            sample.setStyleSheet("background-color: gray; border: 1px solid black;")
            
            capture_btn = QPushButton(tr("Capture"))
            capture_btn.clicked.connect(lambda checked, c=color.lower(): self.capture_color(c))
            
            grid.addWidget(label, i, 0)
            grid.addWidget(sample, i, 1)
            grid.addWidget(capture_btn, i, 2)
            
            self.color_samples[color.lower()] = sample
            
        layout.addLayout(grid)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton(tr("Reset"))
        self.reset_btn.clicked.connect(self.reset_calibration)
        
        self.ok_btn = QPushButton(tr("OK"))
        self.ok_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton(tr("Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def capture_color(self, color):
        """Capture color from camera"""
        # This would capture from the camera
        # For now, just use placeholder
        import random
        
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        
        self.calibration[color] = (r, g, b)
        self.color_samples[color].setStyleSheet(
            f"background-color: rgb({r},{g},{b}); border: 1px solid black;"
        )
        
    def reset_calibration(self):
        """Reset calibration to defaults"""
        self.calibration = {}
        for color, sample in self.color_samples.items():
            sample.setStyleSheet("background-color: gray; border: 1px solid black;")
            
    def get_calibration(self):
        """Get the calibration data"""
        return self.calibration


class SettingsDialog(QDialog):
    """Settings dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Settings"))
        self.setModal(True)
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout()
        
        # Tab widget
        tabs = QTabWidget()
        
        # General tab
        general_widget = self.create_general_tab()
        tabs.addTab(general_widget, tr("General"))
        
        # Scanner tab
        scanner_widget = self.create_scanner_tab()
        tabs.addTab(scanner_widget, tr("Scanner"))
        
        # Solver tab
        solver_widget = self.create_solver_tab()
        tabs.addTab(solver_widget, tr("Solver"))
        
        # Visualization tab
        visual_widget = self.create_visual_tab()
        tabs.addTab(visual_widget, tr("Visualization"))
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.restore_btn = QPushButton(tr("Restore Defaults"))
        self.restore_btn.clicked.connect(self.restore_defaults)
        
        self.ok_btn = QPushButton(tr("OK"))
        self.ok_btn.clicked.connect(self.save_and_accept)
        
        self.cancel_btn = QPushButton(tr("Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.restore_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def create_general_tab(self):
        """Create general settings tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        # Language
        self.language_combo = QComboBox()
        self.language_combo.addItems(['English', 'Spanish', 'French', 'German', 'Chinese'])
        layout.addRow(tr("Language:"), self.language_combo)
        
        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['Dark', 'Light', 'Auto'])
        layout.addRow(tr("Theme:"), self.theme_combo)
        
        # Auto save
        self.auto_save_check = QCheckBox(tr("Auto save solutions"))
        layout.addRow(self.auto_save_check)
        
        # Sound
        self.sound_check = QCheckBox(tr("Enable sound effects"))
        layout.addRow(self.sound_check)
        
        widget.setLayout(layout)
        return widget
        
    def create_scanner_tab(self):
        """Create scanner settings tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        # Camera
        self.camera_combo = QComboBox()
        # Change to only add Camera 0 (or detect available cameras):
        self.camera_combo.addItems([f"Camera {i}" for i in range(1)])  # Only Camera 0
        layout.addRow(tr("Camera:"), self.camera_combo)
        
        # Detection threshold
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(10, 100)
        layout.addRow(tr("Detection Threshold:"), self.threshold_spin)
        
        # Auto detect
        self.auto_detect_check = QCheckBox(tr("Auto detect cube"))
        layout.addRow(self.auto_detect_check)
        
        widget.setLayout(layout)
        return widget
        
    def create_solver_tab(self):
        """Create solver settings tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        # Max depth
        self.max_depth_spin = QSpinBox()
        self.max_depth_spin.setRange(10, 50)
        layout.addRow(tr("Max Depth:"), self.max_depth_spin)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setSuffix(" s")
        layout.addRow(tr("Timeout:"), self.timeout_spin)
        
        # Use pruning
        self.pruning_check = QCheckBox(tr("Use pruning tables"))
        layout.addRow(self.pruning_check)
        
        widget.setLayout(layout)
        return widget
        
    def create_visual_tab(self):
        """Create visualization settings tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        # Animation speed
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(100, 2000)
        layout.addRow(tr("Animation Speed:"), self.speed_slider)
        
        # Show labels
        self.labels_check = QCheckBox(tr("Show face labels"))
        layout.addRow(self.labels_check)
        
        # Anti-aliasing
        self.aa_check = QCheckBox(tr("Enable anti-aliasing"))
        layout.addRow(self.aa_check)
        
        widget.setLayout(layout)
        return widget
        
    def load_settings(self):
        """Load current settings"""
        from __init__ import config
        
        # Load values from config
        self.threshold_spin.setValue(config.get('scanner.detection_threshold', 30))
        self.max_depth_spin.setValue(config.get('solver.algorithms.kociemba.max_depth', 25))
        self.speed_slider.setValue(config.get('visualization.animation_speed', 500))
        
    def save_and_accept(self):
        """Save settings and close"""
        from __init__ import config
        
        # Save values to config
        config.set('scanner.detection_threshold', self.threshold_spin.value())
        config.set('solver.algorithms.kociemba.max_depth', self.max_depth_spin.value())
        config.set('visualization.animation_speed', self.speed_slider.value())
        
        config.save()
        self.accept()
        
    def restore_defaults(self):
        """Restore default settings"""
        self.threshold_spin.setValue(30)
        self.max_depth_spin.setValue(25)
        self.speed_slider.setValue(500)