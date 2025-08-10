#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main entry point for Rubik Ultimate Solver

This module initializes and runs the main application.
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import Qt modules
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont

# Import application modules
from gui import MainWindow
from utils.constants import *
from utils.helpers import check_dependencies, setup_logging
import __init__ as app_init

# Configure logging
logger = logging.getLogger(__name__)


class SplashScreen(QSplashScreen):
    """Custom splash screen with loading progress"""
    
    def __init__(self):
        super().__init__()
        
        # Load splash image
        splash_path = Path(__file__).parent.parent / 'assets' / 'icons' / 'splash.png'
        if not splash_path.exists():
            # Create a default splash screen if image doesn't exist
            pixmap = QPixmap(600, 400)
            pixmap.fill(Qt.darkGray)
        else:
            pixmap = QPixmap(str(splash_path))
        
        self.setPixmap(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Set font for messages
        font = QFont("Arial", 10)
        self.setFont(font)
        
    def show_message(self, message: str):
        """Show a message on the splash screen"""
        self.showMessage(
            message,
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.white
        )
        QApplication.processEvents()


class InitializationThread(QThread):
    """Thread for application initialization"""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def run(self):
        """Run initialization tasks"""
        try:
            # Initialize application
            self.progress.emit("Initializing application...")
            app_init.initialize()
            
            # Check dependencies
            self.progress.emit("Checking dependencies...")
            missing = check_dependencies()
            if missing:
                self.finished.emit(False, f"Missing dependencies: {', '.join(missing)}")
                return
            
            # Load configuration
            self.progress.emit("Loading configuration...")
            from __init__ import config
            config.load_config()
            
            # Initialize scanner module
            self.progress.emit("Initializing camera module...")
            from scanner import initialize_scanner
            initialize_scanner()
            
            # Initialize solver module
            self.progress.emit("Loading solving algorithms...")
            from solver import initialize_solver
            initialize_solver()
            
            # Initialize visualizer
            self.progress.emit("Setting up 3D visualization...")
            from visualizer import initialize_visualizer
            initialize_visualizer()
            
            # Load translations
            self.progress.emit("Loading translations...")
            from utils.translator import Translator
            translator = Translator()
            translator.load_translations()
            
            # Cache pruning tables if needed
            if config.get('solver.pruning_tables.generate_on_start', False):
                self.progress.emit("Generating pruning tables...")
                from data.pruning_tables import generate_all_tables
                generate_all_tables()
            
            self.progress.emit("Ready!")
            self.finished.emit(True, "Initialization complete")
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            self.finished.emit(False, str(e))


class RubikUltimateApp:
    """Main application class"""
    
    def __init__(self, args):
        self.args = args
        self.app = None
        self.window = None
        self.splash = None
        self.init_thread = None
        
    def run(self):
        """Run the application"""
        # Create Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(APP_NAME)
        self.app.setOrganizationName(ORGANIZATION)
        
        # Set application style
        self._set_style()
        
        # Show splash screen
        if not self.args.no_splash:
            self.splash = SplashScreen()
            self.splash.show()
            
            # Start initialization in background
            self.init_thread = InitializationThread()
            self.init_thread.progress.connect(self._on_init_progress)
            self.init_thread.finished.connect(self._on_init_finished)
            self.init_thread.start()
        else:
            # Initialize directly without splash
            self._initialize_and_show()
        
        # Run the application
        return self.app.exec_()
    
    def _set_style(self):
        """Set application style and theme"""
        from __init__ import config
        theme = config.get('interface.theme', 'dark')
        
        if theme == 'dark':
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
        
        # Load custom stylesheet if exists
        style_path = Path(__file__).parent.parent / 'assets' / 'styles' / 'style.qss'
        if style_path.exists():
            with open(style_path, 'r') as f:
                self.app.setStyleSheet(f.read())
    
    def _apply_dark_theme(self):
        """Apply dark theme to application"""
        dark_style = """
        QMainWindow {
            background-color: #2b2b2b;
        }
        QWidget {
            background-color: #3c3c3c;
            color: #ffffff;
        }
        QPushButton {
            background-color: #4a4a4a;
            border: 1px solid #5a5a5a;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #5a5a5a;
        }
        QPushButton:pressed {
            background-color: #3a3a3a;
        }
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #2b2b2b;
            border: 1px solid #5a5a5a;
            padding: 3px;
            border-radius: 3px;
        }
        QMenuBar {
            background-color: #2b2b2b;
        }
        QMenuBar::item:selected {
            background-color: #4a4a4a;
        }
        QMenu {
            background-color: #3c3c3c;
            border: 1px solid #5a5a5a;
        }
        QMenu::item:selected {
            background-color: #4a4a4a;
        }
        QToolBar {
            background-color: #3c3c3c;
            border: none;
        }
        QStatusBar {
            background-color: #2b2b2b;
        }
        """
        self.app.setStyleSheet(dark_style)
    
    def _apply_light_theme(self):
        """Apply light theme to application"""
        light_style = """
        QMainWindow {
            background-color: #f0f0f0;
        }
        QWidget {
            background-color: #ffffff;
            color: #000000;
        }
        QPushButton {
            background-color: #e0e0e0;
            border: 1px solid #c0c0c0;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        QPushButton:pressed {
            background-color: #b0b0b0;
        }
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            border: 1px solid #c0c0c0;
            padding: 3px;
            border-radius: 3px;
        }
        """
        self.app.setStyleSheet(light_style)
    
    def _on_init_progress(self, message: str):
        """Handle initialization progress"""
        if self.splash:
            self.splash.show_message(message)
        logger.info(message)
    
    def _on_init_finished(self, success: bool, message: str):
        """Handle initialization completion"""
        if not success:
            if self.splash:
                self.splash.close()
            QMessageBox.critical(
                None,
                "Initialization Error",
                f"Failed to initialize application:\n{message}"
            )
            self.app.quit()
            return
        
        # Close splash screen
        if self.splash:
            QTimer.singleShot(500, self.splash.close)
        
        # Show main window
        QTimer.singleShot(600, self._show_main_window)
    
    def _initialize_and_show(self):
        """Initialize application and show main window (no splash)"""
        try:
            app_init.initialize()
            self._show_main_window()
        except Exception as e:
            QMessageBox.critical(
                None,
                "Initialization Error",
                f"Failed to initialize application:\n{e}"
            )
            sys.exit(1)
    
    def _show_main_window(self):
        """Create and show the main window"""
        self.window = MainWindow()
        
        # Handle command line arguments
        if self.args.scan:
            self.window.start_scanning()
        elif self.args.file:
            self.window.load_file(self.args.file)
        elif self.args.scramble:
            self.window.set_scramble(self.args.scramble)
        
        # Show window
        if self.args.fullscreen:
            self.window.showFullScreen()
        else:
            self.window.show()
        
        # Auto solve if requested
        if self.args.auto_solve:
            QTimer.singleShot(1000, self.window.solve_cube)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Rubik Ultimate Solver - Complete cube solving solution',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        '-s', '--scan',
        action='store_true',
        help='Start with webcam scanning mode'
    )
    input_group.add_argument(
        '-f', '--file',
        type=str,
        metavar='FILE',
        help='Load scramble from file'
    )
    input_group.add_argument(
        'scramble',
        nargs='?',
        help='Scramble sequence (e.g., "R U R\' U\'")'
    )
    
    # Display options
    parser.add_argument(
        '--fullscreen',
        action='store_true',
        help='Start in fullscreen mode'
    )
    parser.add_argument(
        '--no-splash',
        action='store_true',
        help='Skip splash screen'
    )
    
    # Solver options
    parser.add_argument(
        '-a', '--algorithm',
        choices=['kociemba', 'thistlethwaite', 'optimal'],
        default='kociemba',
        help='Solving algorithm to use'
    )
    parser.add_argument(
        '--auto-solve',
        action='store_true',
        help='Automatically solve after loading'
    )
    
    # Other options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'{APP_NAME} v{app_init.__version__}'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else (
        logging.INFO if args.verbose else logging.WARNING
    )
    setup_logging(log_level)
    
    # Log startup
    logger.info(f"Starting {APP_NAME} v{app_init.__version__}")
    logger.debug(f"Arguments: {args}")
    
    # Set algorithm preference
    if args.algorithm:
        from __init__ import config
        config.set('solver.default_algorithm', args.algorithm)
    
    try:
        # Create and run application
        app = RubikUltimateApp(args)
        return_code = app.run()
        
        # Log shutdown
        logger.info(f"Shutting down {APP_NAME}")
        return return_code
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        
        # Show error dialog if possible
        try:
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Fatal Error",
                f"A fatal error occurred:\n\n{e}\n\nPlease check the log file for details."
            )
        except:
            print(f"Fatal error: {e}", file=sys.stderr)
        
        return 1


def cli_mode():
    """Command line interface mode (no GUI)"""
    import json
    from solver import CubeSolver
    
    parser = argparse.ArgumentParser(description='Rubik CLI Solver')
    parser.add_argument('scramble', help='Scramble sequence')
    parser.add_argument('-a', '--algorithm', default='kociemba')
    parser.add_argument('-g', '--group', action='store_true', help='Show subgroup breakdown')
    parser.add_argument('-j', '--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # Create solver
    solver = CubeSolver()
    
    # Solve cube
    solution = solver.solve_from_scramble(args.scramble, args.algorithm)
    
    if args.json:
        print(json.dumps(solution, indent=2))
    else:
        print(f"Solution: {solution['solution']}")
        print(f"Move count: {solution['move_count']}")
        print(f"Time: {solution['time']:.3f}s")
        
        if args.group and 'subgroups' in solution:
            print("\nSubgroup breakdown:")
            for i, subgroup in enumerate(solution['subgroups']):
                print(f"  G{i}: {subgroup}")


if __name__ == '__main__':
    # Check if running in CLI mode
    if len(sys.argv) > 1 and sys.argv[1] == 'cli':
        sys.argv.pop(1)  # Remove 'cli' from arguments
        sys.exit(cli_mode())
    else:
        sys.exit(main())