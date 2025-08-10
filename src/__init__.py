#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rubik Ultimate Solver - A comprehensive Rubik's Cube solving application
"""

__version__ = "1.0.0"
__author__ = "Rubik Ultimate Team"
__license__ = "MIT"

# Application metadata
APP_NAME = "Rubik Ultimate Solver"
APP_VERSION = __version__
APP_AUTHOR = __author__

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info(f"Initializing {APP_NAME} v{__version__}")

__all__ = ['APP_NAME', 'APP_VERSION', 'APP_AUTHOR']