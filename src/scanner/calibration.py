#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Color calibration for cube scanning

This module handles color calibration for different lighting conditions.
"""

import cv2
import numpy as np
import json
import logging
from typing import Dict, Tuple, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import time

logger = logging.getLogger(__name__)


@dataclass
class CalibrationData:
    """Calibration data structure"""
    colors: Dict[str, Tuple[int, int, int]]  # BGR values
    timestamp: float
    lighting_conditions: str = "unknown"
    camera_index: int = 0
    notes: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CalibrationData':
        """Create from dictionary"""
        return cls(**data)


class Calibration:
    """Color calibration manager"""
    
    def __init__(self):
        """Initialize calibration manager"""
        self.current_calibration = None
        self.calibration_path = Path.home() / '.rubik_ultimate' / 'calibration'
        self.calibration_path.mkdir(parents=True, exist_ok=True)
        
        # Default calibration file
        self.default_file = self.calibration_path / 'default.json'
        
        # Calibration samples
        self.color_samples = {
            'white': [],
            'yellow': [],
            'red': [],
            'orange': [],
            'green': [],
            'blue': []
        }
        
        # Calibration state
        self.is_calibrating = False
        self.current_color = None
        self.samples_per_color = 20
        
    def load(self, filepath: Optional[str] = None) -> bool:
        """
        Load calibration from file
        
        Args:
            filepath: Path to calibration file (None for default)
            
        Returns:
            True if loaded successfully
        """
        if filepath is None:
            filepath = self.default_file
        else:
            filepath = Path(filepath)
            
        if not filepath.exists():
            logger.warning(f"Calibration file not found: {filepath}")
            return False
            
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            # Convert color tuples
            if 'colors' in data:
                for color, values in data['colors'].items():
                    data['colors'][color] = tuple(values)
                    
            self.current_calibration = CalibrationData.from_dict(data)
            logger.info(f"Calibration loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load calibration: {e}")
            return False
            
    def save(self, filepath: Optional[str] = None) -> bool:
        """
        Save calibration to file
        
        Args:
            filepath: Path to save file (None for default)
            
        Returns:
            True if saved successfully
        """
        if self.current_calibration is None:
            logger.warning("No calibration to save")
            return False
            
        if filepath is None:
            filepath = self.default_file
        else:
            filepath = Path(filepath)
            
        try:
            # Convert to dict
            data = self.current_calibration.to_dict()
            
            # Convert color tuples to lists for JSON
            if 'colors' in data:
                data['colors'] = {k: list(v) for k, v in data['colors'].items()}
                
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Calibration saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save calibration: {e}")
            return False
            
    def get_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """
        Get current calibration colors
        
        Returns:
            Dictionary of color BGR values
        """
        if self.current_calibration:
            return self.current_calibration.colors.copy()
        else:
            # Return default colors
            return {
                'white': (255, 255, 255),
                'yellow': (0, 255, 255),
                'red': (0, 0, 255),
                'orange': (0, 165, 255),
                'green': (0, 255, 0),
                'blue': (255, 0, 0)
            }
            
    def set_colors(self, colors: Dict[str, Tuple[int, int, int]]):
        """
        Set calibration colors
        
        Args:
            colors: Dictionary of color BGR values
        """
        self.current_calibration = CalibrationData(
            colors=colors,
            timestamp=time.time()
        )
        
    def start_calibration(self):
        """Start calibration process"""
        self.is_calibrating = True
        self.color_samples = {color: [] for color in self.color_samples}
        self.current_color = None
        logger.info("Calibration started")
        
    def stop_calibration(self):
        """Stop calibration process"""
        self.is_calibrating = False
        self.current_color = None
        logger.info("Calibration stopped")
        
    def add_sample(self, color_name: str, bgr: Tuple[int, int, int]):
        """
        Add a color sample
        
        Args:
            color_name: Name of the color
            bgr: BGR color value
        """
        if color_name not in self.color_samples:
            logger.warning(f"Unknown color: {color_name}")
            return
            
        self.color_samples[color_name].append(bgr)
        
        logger.debug(f"Added sample for {color_name}: {bgr}")
        
    def calculate_calibration(self) -> Dict[str, Tuple[int, int, int]]:
        """
        Calculate calibration from samples
        
        Returns:
            Calibrated color values
        """
        calibrated = {}
        
        for color_name, samples in self.color_samples.items():
            if len(samples) == 0:
                # Use default
                calibrated[color_name] = self.get_colors()[color_name]
            else:
                # Calculate mean
                mean_color = np.mean(samples, axis=0)
                calibrated[color_name] = tuple(map(int, mean_color))
                
                logger.info(f"Calibrated {color_name}: {calibrated[color_name]} from {len(samples)} samples")
                
        return calibrated
        
    def finalize_calibration(self, lighting: str = "unknown", notes: str = "") -> bool:
        """
        Finalize and save calibration
        
        Args:
            lighting: Lighting conditions description
            notes: Additional notes
            
        Returns:
            True if successful
        """
        # Calculate calibration
        colors = self.calculate_calibration()
        
        # Create calibration data
        self.current_calibration = CalibrationData(
            colors=colors,
            timestamp=time.time(),
            lighting_conditions=lighting,
            notes=notes
        )
        
        # Save to default file
        return self.save()
        
    def calibrate_from_image(self, image: np.ndarray, 
                            reference_positions: Dict[str, List[Tuple[int, int]]]) -> Dict[str, Tuple[int, int, int]]:
        """
        Calibrate from a reference image
        
        Args:
            image: Reference image with known colors
            reference_positions: Dictionary mapping color names to list of (x, y) positions
            
        Returns:
            Calibrated colors
        """
        calibrated = {}
        
        for color_name, positions in reference_positions.items():
            samples = []
            
            for x, y in positions:
                # Extract color at position (with small region)
                region = image[max(0, y-5):y+5, max(0, x-5):x+5]
                
                if region.size > 0:
                    mean_color = cv2.mean(region)[:3]
                    samples.append(mean_color)
                    
            if samples:
                # Calculate mean of samples
                mean_color = np.mean(samples, axis=0)
                calibrated[color_name] = tuple(map(int, mean_color))
            else:
                # Use default
                calibrated[color_name] = self.get_colors()[color_name]
                
        return calibrated
        
    def auto_white_balance(self, image: np.ndarray) -> np.ndarray:
        """
        Apply auto white balance to image
        
        Args:
            image: Input image (BGR)
            
        Returns:
            White balanced image
        """
        # Simple gray world assumption
        avg_b = np.mean(image[:, :, 0])
        avg_g = np.mean(image[:, :, 1])
        avg_r = np.mean(image[:, :, 2])
        
        avg_gray = (avg_b + avg_g + avg_r) / 3
        
        # Calculate scaling factors
        scale_b = avg_gray / avg_b if avg_b > 0 else 1
        scale_g = avg_gray / avg_g if avg_g > 0 else 1
        scale_r = avg_gray / avg_r if avg_r > 0 else 1
        
        # Apply scaling
        balanced = image.copy()
        balanced[:, :, 0] = np.clip(balanced[:, :, 0] * scale_b, 0, 255)
        balanced[:, :, 1] = np.clip(balanced[:, :, 1] * scale_g, 0, 255)
        balanced[:, :, 2] = np.clip(balanced[:, :, 2] * scale_r, 0, 255)
        
        return balanced.astype(np.uint8)
        
    def apply_color_correction(self, image: np.ndarray, 
                              source_colors: Dict[str, Tuple[int, int, int]],
                              target_colors: Optional[Dict[str, Tuple[int, int, int]]] = None) -> np.ndarray:
        """
        Apply color correction to match target colors
        
        Args:
            image: Input image
            source_colors: Detected colors in image
            target_colors: Target colors to match (None for calibrated colors)
            
        Returns:
            Color corrected image
        """
        if target_colors is None:
            target_colors = self.get_colors()
            
        # Build color transformation matrix
        source_points = []
        target_points = []
        
        for color_name in source_colors:
            if color_name in target_colors:
                source_points.append(source_colors[color_name])
                target_points.append(target_colors[color_name])
                
        if len(source_points) < 3:
            logger.warning("Not enough color points for correction")
            return image
            
        source_points = np.array(source_points, dtype=np.float32)
        target_points = np.array(target_points, dtype=np.float32)
        
        # Calculate affine transformation
        # This is a simplified approach - could use more sophisticated methods
        transform = cv2.estimateAffine2D(source_points, target_points)[0]
        
        if transform is not None:
            # Apply transformation
            corrected = cv2.transform(image.reshape(-1, 1, 3), transform)
            corrected = corrected.reshape(image.shape)
            corrected = np.clip(corrected, 0, 255).astype(np.uint8)
            return corrected
        else:
            return image
            
    def validate_calibration(self) -> Tuple[bool, str]:
        """
        Validate current calibration
        
        Returns:
            Tuple of (is_valid, message)
        """
        if self.current_calibration is None:
            return False, "No calibration loaded"
            
        colors = self.current_calibration.colors
        
        # Check all colors present
        required_colors = {'white', 'yellow', 'red', 'orange', 'green', 'blue'}
        if set(colors.keys()) != required_colors:
            return False, "Missing required colors"
            
        # Check color values are valid
        for color_name, bgr in colors.items():
            if len(bgr) != 3:
                return False, f"Invalid BGR values for {color_name}"
                
            for value in bgr:
                if not (0 <= value <= 255):
                    return False, f"Invalid color value for {color_name}: {value}"
                    
        # Check colors are distinguishable
        # Calculate minimum distance between colors
        min_distance = float('inf')
        color_list = list(colors.values())
        
        for i in range(len(color_list)):
            for j in range(i + 1, len(color_list)):
                distance = np.linalg.norm(
                    np.array(color_list[i]) - np.array(color_list[j])
                )
                min_distance = min(min_distance, distance)
                
        if min_distance < 30:  # Threshold for distinguishability
            return False, f"Colors too similar (min distance: {min_distance:.1f})"
            
        return True, "Calibration valid"
        
    def export_calibration(self, filepath: str):
        """
        Export calibration with additional metadata
        
        Args:
            filepath: Export file path
        """
        if self.current_calibration is None:
            logger.warning("No calibration to export")
            return
            
        export_data = {
            'calibration': self.current_calibration.to_dict(),
            'metadata': {
                'version': '1.0.0',
                'exported': time.time(),
                'samples': {k: len(v) for k, v in self.color_samples.items()}
            }
        }
        
        # Convert colors to lists
        if 'colors' in export_data['calibration']:
            export_data['calibration']['colors'] = {
                k: list(v) for k, v in export_data['calibration']['colors'].items()
            }
            
        try:
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Calibration exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export calibration: {e}")
            
    def import_calibration(self, filepath: str) -> bool:
        """
        Import calibration from export file
        
        Args:
            filepath: Import file path
            
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            if 'calibration' not in data:
                logger.error("Invalid calibration file format")
                return False
                
            cal_data = data['calibration']
            
            # Convert color lists to tuples
            if 'colors' in cal_data:
                cal_data['colors'] = {k: tuple(v) for k, v in cal_data['colors'].items()}
                
            self.current_calibration = CalibrationData.from_dict(cal_data)
            
            logger.info(f"Calibration imported from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import calibration: {e}")
            return False
            
    def get_presets(self) -> List[str]:
        """
        Get list of available calibration presets
        
        Returns:
            List of preset names
        """
        presets = []
        
        # Look for preset files
        for file in self.calibration_path.glob("*.json"):
            if file.stem != 'default':
                presets.append(file.stem)
                
        return presets
        
    def load_preset(self, preset_name: str) -> bool:
        """
        Load a calibration preset
        
        Args:
            preset_name: Name of preset
            
        Returns:
            True if successful
        """
        preset_file = self.calibration_path / f"{preset_name}.json"
        return self.load(preset_file)
        
    def save_preset(self, preset_name: str) -> bool:
        """
        Save current calibration as preset
        
        Args:
            preset_name: Name for preset
            
        Returns:
            True if successful
        """
        preset_file = self.calibration_path / f"{preset_name}.json"
        return self.save(preset_file)