#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Run script for Rubik Ultimate Solver
"""

import sys
import os

# Get the directory of this script
root_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(root_dir, 'src')

# Add src to path
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Set up environment
os.chdir(root_dir)

def main():
    """Main entry point"""
    # Import here after path is set
    from PyQt5.QtWidgets import QApplication
    
    # Import with absolute imports from src
    from gui import MainWindow
    
    app = QApplication(sys.argv)
    app.setApplicationName("Rubik Ultimate Solver")
    app.setOrganizationName("Rubik Ultimate Team")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()