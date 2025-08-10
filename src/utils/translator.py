#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Translation and internationalization support

This module handles multi-language support for the application.
"""

import json
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class Translator:
    """Handles application translations"""
    
    _instance = None
    _translations = {}
    _current_language = 'en'
    _fallback_language = 'en'
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_translations()
        return cls._instance
    
    def _load_translations(self):
        """Load all available translations"""
        translations_dir = self._get_translations_dir()
        
        if not translations_dir.exists():
            logger.warning(f"Translations directory not found: {translations_dir}")
            self._create_default_translations()
            return
        
        # Load all translation files
        for file in translations_dir.glob("*.json"):
            lang_code = file.stem
            
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    self._translations[lang_code] = json.load(f)
                logger.info(f"Loaded translation: {lang_code}")
            except Exception as e:
                logger.error(f"Failed to load translation {lang_code}: {e}")
    
    def _get_translations_dir(self) -> Path:
        """Get translations directory path"""
        # Try multiple locations
        locations = [
            Path(__file__).parent.parent.parent / 'translations',
            Path.cwd() / 'translations',
            Path.home() / '.rubik_ultimate' / 'translations',
        ]
        
        for location in locations:
            if location.exists():
                return location
        
        # Return first location as default
        return locations[0]
    
    def _create_default_translations(self):
        """Create default English translations"""
        self._translations['en'] = {
            # Common
            'app_name': 'Rubik Ultimate Solver',
            'ok': 'OK',
            'cancel': 'Cancel',
            'apply': 'Apply',
            'close': 'Close',
            'yes': 'Yes',
            'no': 'No',
            'save': 'Save',
            'load': 'Load',
            'reset': 'Reset',
            'clear': 'Clear',
            'help': 'Help',
            'about': 'About',
            'settings': 'Settings',
            'preferences': 'Preferences',
            
            # Menu items
            'file': 'File',
            'edit': 'Edit',
            'view': 'View',
            'tools': 'Tools',
            'window': 'Window',
            'new': 'New',
            'open': 'Open...',
            'save_as': 'Save As...',
            'export': 'Export...',
            'import': 'Import...',
            'quit': 'Quit',
            'undo': 'Undo',
            'redo': 'Redo',
            'copy': 'Copy',
            'paste': 'Paste',
            'cut': 'Cut',
            'select_all': 'Select All',
            
            # Scanner
            'scanner': 'Scanner',
            'scan_face': 'Scan Face',
            'scan_cube': 'Scan Cube',
            'capture': 'Capture',
            'camera': 'Camera',
            'start_camera': 'Start Camera',
            'stop_camera': 'Stop Camera',
            'calibration': 'Calibration',
            'calibrate_colors': 'Calibrate Colors',
            'detection_threshold': 'Detection Threshold',
            'face_captured': 'Face {} captured',
            'all_faces_captured': 'All faces captured!',
            
            # Solver
            'solver': 'Solver',
            'solve': 'Solve',
            'solving': 'Solving...',
            'solution': 'Solution',
            'solution_found': 'Solution found!',
            'no_solution': 'No solution',
            'algorithm': 'Algorithm',
            'moves': 'Moves',
            'time': 'Time',
            'scramble': 'Scramble',
            'apply_scramble': 'Apply Scramble',
            'random_scramble': 'Random Scramble',
            'validate': 'Validate',
            'optimize': 'Optimize',
            
            # Visualization
            'visualization': 'Visualization',
            '3d_view': '3D View',
            '2d_view': '2D View',
            'animation': 'Animation',
            'play': 'Play',
            'pause': 'Pause',
            'stop': 'Stop',
            'speed': 'Speed',
            'color_scheme': 'Color Scheme',
            'show_labels': 'Show Labels',
            'show_axes': 'Show Axes',
            'reset_view': 'Reset View',
            
            # Cube states
            'solved': 'Solved',
            'scrambled': 'Scrambled',
            'invalid': 'Invalid',
            'incomplete': 'Incomplete',
            
            # Faces
            'face_up': 'Up',
            'face_down': 'Down',
            'face_front': 'Front',
            'face_back': 'Back',
            'face_right': 'Right',
            'face_left': 'Left',
            
            # Colors
            'white': 'White',
            'yellow': 'Yellow',
            'red': 'Red',
            'orange': 'Orange',
            'green': 'Green',
            'blue': 'Blue',
            
            # Status messages
            'ready': 'Ready',
            'loading': 'Loading...',
            'saving': 'Saving...',
            'processing': 'Processing...',
            'error': 'Error',
            'warning': 'Warning',
            'success': 'Success',
            'failed': 'Failed',
            
            # Error messages
            'error_invalid_cube': 'Invalid cube configuration',
            'error_invalid_scramble': 'Invalid scramble notation',
            'error_no_camera': 'No camera detected',
            'error_camera_access': 'Cannot access camera',
            'error_solve_failed': 'Failed to find solution',
            'error_file_not_found': 'File not found',
            'error_save_failed': 'Failed to save file',
            'error_load_failed': 'Failed to load file',
            
            # Info messages
            'info_cube_solved': 'The cube is already solved',
            'info_solution_optimal': 'This is an optimal solution',
            'info_calibration_complete': 'Calibration complete',
            'info_file_saved': 'File saved successfully',
            'info_file_loaded': 'File loaded successfully',
            
            # Tooltips
            'tooltip_scan': 'Scan cube using camera',
            'tooltip_solve': 'Find solution for current cube',
            'tooltip_reset': 'Reset cube to solved state',
            'tooltip_scramble': 'Apply random scramble',
            'tooltip_play': 'Play solution animation',
            'tooltip_speed': 'Adjust animation speed',
            
            # Dialog titles
            'dialog_error': 'Error',
            'dialog_warning': 'Warning',
            'dialog_info': 'Information',
            'dialog_confirm': 'Confirm',
            'dialog_save': 'Save File',
            'dialog_open': 'Open File',
            
            # Units
            'seconds': 'seconds',
            'milliseconds': 'ms',
            'moves_unit': 'moves',
            'fps': 'FPS',
            'degrees': 'degrees',
            
            # Formats
            'format_time': '{:.2f}s',
            'format_moves': '{} moves',
            'format_solution': 'Solution: {} moves in {:.2f}s',
            'format_progress': '{}/{}',
        }
    
    def set_language(self, language: str):
        """
        Set current language
        
        Args:
            language: Language code (e.g., 'en', 'es', 'fr')
        """
        if language in self._translations:
            self._current_language = language
            logger.info(f"Language set to: {language}")
        else:
            logger.warning(f"Language not available: {language}")
    
    def get_language(self) -> str:
        """Get current language code"""
        return self._current_language
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages"""
        languages = {}
        
        for code in self._translations.keys():
            # Get language name from translations
            name = self._translations[code].get('language_name', code.upper())
            languages[code] = name
        
        return languages
    
    def translate(self, key: str, **kwargs) -> str:
        """
        Translate a key to current language
        
        Args:
            key: Translation key
            **kwargs: Format arguments
            
        Returns:
            Translated string
        """
        # Try current language
        if self._current_language in self._translations:
            translations = self._translations[self._current_language]
            if key in translations:
                text = translations[key]
                
                # Apply format arguments
                if kwargs:
                    try:
                        text = text.format(**kwargs)
                    except:
                        pass
                
                return text
        
        # Try fallback language
        if self._fallback_language in self._translations:
            translations = self._translations[self._fallback_language]
            if key in translations:
                text = translations[key]
                
                # Apply format arguments
                if kwargs:
                    try:
                        text = text.format(**kwargs)
                    except:
                        pass
                
                return text
        
        # Return key if translation not found
        logger.debug(f"Translation not found for key: {key}")
        return key
    
    def add_translation(self, language: str, key: str, value: str):
        """
        Add or update a translation
        
        Args:
            language: Language code
            key: Translation key
            value: Translation value
        """
        if language not in self._translations:
            self._translations[language] = {}
        
        self._translations[language][key] = value
    
    def save_translations(self):
        """Save all translations to files"""
        translations_dir = self._get_translations_dir()
        translations_dir.mkdir(parents=True, exist_ok=True)
        
        for lang_code, translations in self._translations.items():
            file_path = translations_dir / f"{lang_code}.json"
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(translations, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved translation: {lang_code}")
            except Exception as e:
                logger.error(f"Failed to save translation {lang_code}: {e}")
    
    def load_translation_file(self, filepath: str) -> bool:
        """
        Load translation from file
        
        Args:
            filepath: Path to translation file
            
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get language code from file or data
            lang_code = Path(filepath).stem
            
            if 'language_code' in data:
                lang_code = data['language_code']
            
            self._translations[lang_code] = data
            logger.info(f"Loaded translation from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load translation: {e}")
            return False
    
    def export_translation(self, language: str, filepath: str) -> bool:
        """
        Export translation to file
        
        Args:
            language: Language code
            filepath: Output file path
            
        Returns:
            True if successful
        """
        if language not in self._translations:
            logger.error(f"Language not found: {language}")
            return False
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._translations[language], f, indent=2, ensure_ascii=False)
            logger.info(f"Exported translation to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export translation: {e}")
            return False
    
    def get_missing_keys(self, language: str) -> list:
        """
        Get missing translation keys for a language
        
        Args:
            language: Language code
            
        Returns:
            List of missing keys
        """
        if language not in self._translations:
            return []
        
        # Compare with fallback language
        fallback_keys = set(self._translations.get(self._fallback_language, {}).keys())
        language_keys = set(self._translations[language].keys())
        
        missing = fallback_keys - language_keys
        
        return list(missing)
    
    def get_translation_completeness(self, language: str) -> float:
        """
        Get translation completeness percentage
        
        Args:
            language: Language code
            
        Returns:
            Completeness percentage (0-100)
        """
        if language not in self._translations:
            return 0.0
        
        fallback_count = len(self._translations.get(self._fallback_language, {}))
        
        if fallback_count == 0:
            return 100.0
        
        language_count = len(self._translations[language])
        
        return (language_count / fallback_count) * 100.0


# Global translator instance
translator = Translator()


def tr(key: str, **kwargs) -> str:
    """
    Convenience function for translation
    
    Args:
        key: Translation key
        **kwargs: Format arguments
        
    Returns:
        Translated string
    """
    return translator.translate(key, **kwargs)


def set_language(language: str):
    """Set application language"""
    translator.set_language(language)


def get_language() -> str:
    """Get current language"""
    return translator.get_language()


def get_available_languages() -> Dict[str, str]:
    """Get available languages"""
    return translator.get_available_languages()


# Sample translations for other languages
SAMPLE_TRANSLATIONS = {
    'es': {
        'language_name': 'Español',
        'app_name': 'Solucionador de Rubik Ultimate',
        'solve': 'Resolver',
        'solution': 'Solución',
        'moves': 'Movimientos',
        'time': 'Tiempo',
        'scanner': 'Escáner',
        'camera': 'Cámara',
        'settings': 'Configuración',
        'help': 'Ayuda',
        'about': 'Acerca de',
    },
    
    'fr': {
        'language_name': 'Français',
        'app_name': 'Solveur Rubik Ultimate',
        'solve': 'Résoudre',
        'solution': 'Solution',
        'moves': 'Mouvements',
        'time': 'Temps',
        'scanner': 'Scanner',
        'camera': 'Caméra',
        'settings': 'Paramètres',
        'help': 'Aide',
        'about': 'À propos',
    },
    
    'de': {
        'language_name': 'Deutsch',
        'app_name': 'Rubik Ultimate Löser',
        'solve': 'Lösen',
        'solution': 'Lösung',
        'moves': 'Züge',
        'time': 'Zeit',
        'scanner': 'Scanner',
        'camera': 'Kamera',
        'settings': 'Einstellungen',
        'help': 'Hilfe',
        'about': 'Über',
    },
    
    'ja': {
        'language_name': '日本語',
        'app_name': 'ルービックアルティメットソルバー',
        'solve': '解く',
        'solution': '解法',
        'moves': '手数',
        'time': '時間',
        'scanner': 'スキャナー',
        'camera': 'カメラ',
        'settings': '設定',
        'help': 'ヘルプ',
        'about': '約',
    },
    
    'zh': {
        'language_name': '中文',
        'app_name': '魔方终极解算器',
        'solve': '解决',
        'solution': '解法',
        'moves': '步数',
        'time': '时间',
        'scanner': '扫描仪',
        'camera': '相机',
        'settings': '设置',
        'help': '帮助',
        'about': '关于',
    },
}


def create_sample_translations():
    """Create sample translation files"""
    for lang_code, translations in SAMPLE_TRANSLATIONS.items():
        translator._translations[lang_code] = translations
    
    translator.save_translations()
    logger.info("Sample translations created")