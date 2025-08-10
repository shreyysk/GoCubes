#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Import fixer for the application
"""

import sys
import os

# Add src directory to path
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

def setup_imports():
    """Setup import paths"""
    return src_dir