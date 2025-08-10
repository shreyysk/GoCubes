#!/usr/bin/env python3
"""
Fix specific import issues in the project
"""

import os

def fix_file(filepath, replacements):
    """Fix imports in a specific file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for old, new in replacements:
        content = content.replace(old, new)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    return False

def main():
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    
    # Define specific fixes for each file
    fixes = {
        'scanner/cube_scanner.py': [
            ('from ..utils.constants import *', 'from utils.constants import *'),
        ],
        'visualizer/cube_3d.py': [
            ('from . import COLOR_SCHEMES, DisplayMode, ViewAngle', 
             'from visualizer import COLOR_SCHEMES, DisplayMode, ViewAngle'),
        ],
        'visualizer/cube_2d.py': [
            ('from . import COLOR_SCHEMES', 'from visualizer import COLOR_SCHEMES'),
        ],
        'solver/__init__.py': [
            ('from .data.pruning_tables import initialize_tables',
             'from solver.data.pruning_tables import initialize_tables'),
        ],
        'utils/__init__.py': [
            ('from .constants import *', 'from utils.constants import *'),
            ('from .helpers import *', 'from utils.helpers import *'),
            ('from .translator import Translator, tr', 'from utils.translator import Translator, tr'),
        ],
    }
    
    fixed_count = 0
    for relative_path, replacements in fixes.items():
        filepath = os.path.join(src_dir, relative_path)
        if os.path.exists(filepath):
            if fix_file(filepath, replacements):
                fixed_count += 1
        else:
            print(f"File not found: {filepath}")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == '__main__':
    main()