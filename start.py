#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Startup script for Rubik Ultimate Solver
"""

import sys
import os

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(root_dir, 'src')
sys.path.insert(0, src_dir)
os.chdir(root_dir)

# Configure imports for all modules
import importlib

def configure_module_imports():
    """Configure all module imports to use absolute paths"""
    # This ensures all modules can find each other
    os.environ['PYTHONPATH'] = src_dir
    
configure_module_imports()

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    
    # High DPI support
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Rubik Ultimate Solver")
    
    # Now import and create main window
    from gui import MainWindow
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())