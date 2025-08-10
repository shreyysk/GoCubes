#!/usr/bin/env python3
"""Test script to identify import issues"""

import sys
import os

# Add src to path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_dir)

print(f"Testing all imports step by step...\n")

try:
    print("1. Testing utils...")
    from utils import config
    print("   ✓ config imported")
    
    print("\n2. Testing GUI...")
    from gui import MainWindow
    print("   ✓ MainWindow imported")
    
    print("\n3. Testing PyQt5...")
    from PyQt5.QtWidgets import QApplication
    print("   ✓ QApplication imported")
    
    print("\n4. Creating QApplication...")
    app = QApplication(sys.argv)
    print("   ✓ QApplication created")
    
    print("\n5. Creating MainWindow...")
    window = MainWindow()
    print("   ✓ MainWindow created")
    
    print("\n✅ All tests passed! The app should work now.")
    print("\nTry running: python run.py")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()