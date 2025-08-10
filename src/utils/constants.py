#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Constants and configuration values

This module contains all constant values used throughout the application.
"""

# Application info
APP_NAME = "Rubik Ultimate Solver"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Rubik Ultimate Team"
APP_WEBSITE = "https://github.com/yourusername/rubik-ultimate"
APP_LICENSE = "MIT"

# File extensions
SCRAMBLE_EXTENSION = ".scramble"
SOLUTION_EXTENSION = ".solution"
CUBE_STATE_EXTENSION = ".cube"
SESSION_EXTENSION = ".session"

# Cube constants
CUBE_SIZE = 3  # 3x3x3 cube
FACES_COUNT = 6
STICKERS_PER_FACE = 9
TOTAL_STICKERS = 54
CUBIES_COUNT = 26  # 8 corners + 12 edges + 6 centers

# Face notation
FACES = ['U', 'R', 'F', 'D', 'L', 'B']
FACE_NAMES = {
    'U': 'Up',
    'D': 'Down',
    'F': 'Front',
    'B': 'Back',
    'R': 'Right',
    'L': 'Left'
}

# Color mapping
FACE_COLORS = {
    'U': 'white',
    'D': 'yellow',
    'F': 'green',
    'B': 'blue',
    'R': 'red',
    'L': 'orange'
}

COLOR_CODES = {
    'white': 'W',
    'yellow': 'Y',
    'green': 'G',
    'blue': 'B',
    'red': 'R',
    'orange': 'O',
    'unknown': 'X'
}

# RGB color values
COLOR_RGB = {
    'white': (255, 255, 255),
    'yellow': (255, 255, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'red': (255, 0, 0),
    'orange': (255, 165, 0),
    'black': (0, 0, 0),
    'gray': (128, 128, 128)
}

# Hex color values
COLOR_HEX = {
    'white': '#FFFFFF',
    'yellow': '#FFFF00',
    'green': '#00FF00',
    'blue': '#0000FF',
    'red': '#FF0000',
    'orange': '#FFA500',
    'black': '#000000',
    'gray': '#808080'
}

# Move notation
BASIC_MOVES = ['U', 'D', 'F', 'B', 'R', 'L']
MOVE_MODIFIERS = ['', "'", '2']
ALL_BASIC_MOVES = [
    'U', "U'", 'U2',
    'D', "D'", 'D2',
    'F', "F'", 'F2',
    'B', "B'", 'B2',
    'R', "R'", 'R2',
    'L', "L'", 'L2'
]

# Wide moves (lowercase)
WIDE_MOVES = [
    'u', "u'", 'u2',
    'd', "d'", 'd2',
    'f', "f'", 'f2',
    'b', "b'", 'b2',
    'r', "r'", 'r2',
    'l', "l'", 'l2'
]

# Slice moves
SLICE_MOVES = [
    'M', "M'", 'M2',  # Middle (between L and R)
    'E', "E'", 'E2',  # Equatorial (between U and D)
    'S', "S'", 'S2'   # Standing (between F and B)
]

# Rotation moves
ROTATION_MOVES = [
    'x', "x'", 'x2',  # Rotate around R axis
    'y', "y'", 'y2',  # Rotate around U axis
    'z', "z'", 'z2'   # Rotate around F axis
]

# All valid moves
ALL_MOVES = ALL_BASIC_MOVES + WIDE_MOVES + SLICE_MOVES + ROTATION_MOVES

# Move opposites
MOVE_OPPOSITES = {
    'U': 'D', 'D': 'U',
    'F': 'B', 'B': 'F',
    'R': 'L', 'L': 'R',
    'M': 'M', 'E': 'E', 'S': 'S',
    'x': 'x', 'y': 'y', 'z': 'z'
}

# Commutator notation
COMMUTATORS = {
    'sexy_move': "R U R' U'",
    'sledgehammer': "R' F R F'",
    'niklas': "R U' L' U R' U' L U",
    'sune': "R U R' U R U2 R'",
    'antisune': "R U2 R' U' R U' R'",
}

# Algorithm categories
ALGORITHM_CATEGORIES = {
    'OLL': 'Orientation of Last Layer',
    'PLL': 'Permutation of Last Layer',
    'F2L': 'First Two Layers',
    'Cross': 'Cross',
    'Basic': 'Basic Algorithms'
}

# Scanner constants
CAMERA_DEFAULT_INDEX = 0
CAMERA_DEFAULT_WIDTH = 640
CAMERA_DEFAULT_HEIGHT = 480
CAMERA_DEFAULT_FPS = 30

# Color detection thresholds
COLOR_THRESHOLD_MIN = 10
COLOR_THRESHOLD_MAX = 100
COLOR_THRESHOLD_DEFAULT = 30

# Contour detection
CONTOUR_AREA_MIN = 30
CONTOUR_AREA_MAX = 60
CONTOUR_ASPECT_RATIO_MIN = 0.8
CONTOUR_ASPECT_RATIO_MAX = 1.2
CONTOUR_APPROXIMATION = 0.1

# Solver constants
MAX_SOLVE_TIME = 60.0  # seconds
MAX_SOLUTION_LENGTH = 100  # moves
DEFAULT_ALGORITHM = 'kociemba'

# Kociemba specific
KOCIEMBA_MAX_DEPTH = 24
KOCIEMBA_TIMEOUT = 10.0

# Thistlethwaite specific
THISTLETHWAITE_PHASE_DEPTHS = [7, 10, 13, 15]

# Visualization constants
DEFAULT_COLOR_SCHEME = 'standard'
DEFAULT_ANIMATION_SPEED = 500  # milliseconds
DEFAULT_STICKER_SIZE = 40  # pixels
DEFAULT_CAMERA_DISTANCE = 10.0
DEFAULT_ROTATION = (30, -45, 0)  # x, y, z

# Animation speeds
ANIMATION_SPEED_INSTANT = 0
ANIMATION_SPEED_FAST = 200
ANIMATION_SPEED_NORMAL = 500
ANIMATION_SPEED_SLOW = 1000

# View angles
VIEW_ANGLES = {
    'front': (0, 0, 0),
    'back': (0, 180, 0),
    'top': (90, 0, 0),
    'bottom': (-90, 0, 0),
    'left': (0, 90, 0),
    'right': (0, -90, 0),
    'isometric': (30, -45, 0)
}

# UI Constants
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 800
SIDEBAR_WIDTH = 300
TOOLBAR_HEIGHT = 40
STATUSBAR_HEIGHT = 25

# Theme colors
THEME_COLORS = {
    'dark': {
        'background': '#2b2b2b',
        'foreground': '#ffffff',
        'primary': '#4a9eff',
        'secondary': '#ff9f4a',
        'success': '#4aff4a',
        'warning': '#ffff4a',
        'error': '#ff4a4a'
    },
    'light': {
        'background': '#ffffff',
        'foreground': '#2b2b2b',
        'primary': '#0066cc',
        'secondary': '#ff6600',
        'success': '#00cc00',
        'warning': '#ffcc00',
        'error': '#cc0000'
    }
}

# Font settings
FONT_FAMILY = 'Arial'
FONT_SIZE_SMALL = 10
FONT_SIZE_NORMAL = 12
FONT_SIZE_LARGE = 14
FONT_SIZE_XLARGE = 16

# File paths
DATA_DIR = '~/.rubik_ultimate/data'
CONFIG_DIR = '~/.rubik_ultimate/config'
CACHE_DIR = '~/.rubik_ultimate/cache'
LOG_DIR = '~/.rubik_ultimate/logs'
RESOURCE_DIR = 'resources'

# Resource files
ICON_FILE = 'icon.png'
LOGO_FILE = 'logo.png'
SPLASH_FILE = 'splash.png'
SOUND_DIR = 'sounds'

# Sound files
SOUND_MOVE = 'move.wav'
SOUND_SOLVE = 'solve.wav'
SOUND_ERROR = 'error.wav'
SOUND_SUCCESS = 'success.wav'

# Keyboard shortcuts
SHORTCUTS = {
    'new': 'Ctrl+N',
    'open': 'Ctrl+O',
    'save': 'Ctrl+S',
    'save_as': 'Ctrl+Shift+S',
    'quit': 'Ctrl+Q',
    'undo': 'Ctrl+Z',
    'redo': 'Ctrl+Y',
    'copy': 'Ctrl+C',
    'paste': 'Ctrl+V',
    'solve': 'F5',
    'scan': 'F6',
    'reset': 'F7',
    'help': 'F1',
    'fullscreen': 'F11',
    'preferences': 'Ctrl+,'
}

# Status messages
STATUS_MESSAGES = {
    'ready': 'Ready',
    'scanning': 'Scanning cube...',
    'solving': 'Finding solution...',
    'solved': 'Solution found!',
    'error': 'An error occurred',
    'invalid_cube': 'Invalid cube configuration',
    'no_camera': 'No camera detected',
    'camera_error': 'Camera error',
    'save_success': 'File saved successfully',
    'load_success': 'File loaded successfully'
}

# Error messages
ERROR_MESSAGES = {
    'invalid_scramble': 'Invalid scramble notation',
    'invalid_state': 'Invalid cube state',
    'solve_failed': 'Failed to find solution',
    'file_not_found': 'File not found',
    'permission_denied': 'Permission denied',
    'unknown_error': 'An unknown error occurred'
}

# Supported languages
LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'it': 'Italiano',
    'pt': 'Português',
    'ru': 'Русский',
    'ja': '日本語',
    'zh': '中文',
    'ko': '한국어'
}

# Performance settings
MAX_UNDO_HISTORY = 100
MAX_RECENT_FILES = 10
AUTOSAVE_INTERVAL = 60  # seconds
CACHE_SIZE_MB = 100
MAX_LOG_SIZE_MB = 10

# Network settings
UPDATE_CHECK_URL = "https://api.github.com/repos/yourusername/rubik-ultimate/releases/latest"
FEEDBACK_URL = "https://github.com/yourusername/rubik-ultimate/issues"
DOCUMENTATION_URL = "https://github.com/yourusername/rubik-ultimate/wiki"

# Debug settings
DEBUG_MODE = False
VERBOSE_LOGGING = False
SHOW_FPS = False
PROFILE_PERFORMANCE = False

# Validation patterns
SCRAMBLE_PATTERN = r"^([UDFRBL]'?2?\s*)+$"
COLOR_PATTERN = r"^[WYGBRO]{54}$"
MOVE_PATTERN = r"^[UDFRBLMESxyz]'?2?$"

# Mathematical constants
PI = 3.14159265359
SQRT2 = 1.41421356237
SQRT3 = 1.73205080757

# Cube geometry
CUBIE_SIZE = 1.0
STICKER_MARGIN = 0.1
CUBE_ROTATION_SPEED = 90.0  # degrees per second

# Scoring weights (for pattern recognition)
EDGE_WEIGHT = 1.0
CORNER_WEIGHT = 2.0
CENTER_WEIGHT = 0.5

# Algorithm metrics
HTM_WEIGHT = 1.0  # Half Turn Metric
QTM_WEIGHT = 0.8  # Quarter Turn Metric
STM_WEIGHT = 0.9  # Slice Turn Metric
ETM_WEIGHT = 1.1  # Execution Turn Metric

# Competition standards
WCA_SCRAMBLE_LENGTH = 25
WCA_INSPECTION_TIME = 15  # seconds
WCA_TIME_PENALTY = 2  # seconds

# Export formats
EXPORT_FORMATS = {
    'txt': 'Text File',
    'json': 'JSON File',
    'csv': 'CSV File',
    'html': 'HTML File',
    'pdf': 'PDF Document',
    'png': 'PNG Image',
    'jpg': 'JPEG Image',
    'svg': 'SVG Image',
    'gif': 'GIF Animation',
    'mp4': 'MP4 Video'
}

# Import formats
IMPORT_FORMATS = {
    'txt': 'Text File',
    'json': 'JSON File',
    'csv': 'CSV File',
    'scramble': 'Scramble File',
    'cube': 'Cube State File'
}

# Cube patterns (for testing/demos)
PATTERNS = {
    'solved': 'UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB',
    'checkerboard': 'URURURURUFBFBFBFBFRLRLRLRLRDBDBDBDBDLFLFLFLFLBLBLBLBLB',
    'cross': 'UUUUUUUUURWRWRWRWRFGFGFGFGFDYDYDYDYDLOLOLOLOLBBBBBBBBB',
    'dots': 'WUWUWUWUWRYRYRYRYRGBGBGBGBGYDYDYDYDYDOOOOOOOOBWBWBWBWB',
    'superflip': 'UBULURUFUFULFRFDFDFDLDRDBDBUBRBLBLFUFLBRFDLDRUBFLURBLD'
}

# Statistics tracking
STATS_TO_TRACK = [
    'total_solves',
    'total_time',
    'best_time',
    'worst_time',
    'average_time',
    'best_moves',
    'worst_moves',
    'average_moves',
    'success_rate',
    'algorithm_usage'
]