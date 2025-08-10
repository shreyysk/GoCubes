#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Color detection algorithms for cube scanning

This module implements various color detection methods including CIEDE2000.
"""

import cv2
import numpy as np
import logging
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


@dataclass
class ColorSample:
    """Represents a color sample"""
    bgr: Tuple[int, int, int]
    lab: Tuple[float, float, float]
    name: str
    confidence: float = 0.0


class ColorDetector:
    """Main color detection class"""
    
    def __init__(self, calibration: Optional[Dict[str, Tuple[int, int, int]]] = None):
        """
        Initialize color detector
        
        Args:
            calibration: Optional color calibration data
        """
        # Default color palette (BGR format)
        self.default_colors = {
            'white': (255, 255, 255),
            'yellow': (0, 255, 255),
            'red': (0, 0, 255),
            'orange': (0, 165, 255),
            'green': (0, 255, 0),
            'blue': (255, 0, 0)
        }
        
        # Use calibration if provided, otherwise use defaults
        self.color_palette = calibration if calibration else self.default_colors.copy()
        
        # Pre-calculate LAB values for palette
        self.palette_lab = {}
        for name, bgr in self.color_palette.items():
            self.palette_lab[name] = self.bgr_to_lab(bgr)
            
        # Detection parameters
        self.detection_method = 'CIEDE2000'  # or 'EUCLIDEAN', 'DELTA_E_1976'
        self.confidence_threshold = 0.7
        
    def set_calibration(self, calibration: Dict[str, Tuple[int, int, int]]):
        """Update color calibration"""
        self.color_palette = calibration.copy()
        
        # Recalculate LAB values
        self.palette_lab = {}
        for name, bgr in self.color_palette.items():
            self.palette_lab[name] = self.bgr_to_lab(bgr)
            
    def get_dominant_color(self, roi: np.ndarray) -> Tuple[int, int, int]:
        """
        Get dominant color from a region of interest
        
        Args:
            roi: Region of interest (BGR image)
            
        Returns:
            BGR tuple of dominant color
        """
        if roi.size == 0:
            return (0, 0, 0)
            
        # Method 1: K-means clustering
        if self.detection_method == 'KMEANS':
            return self._get_dominant_kmeans(roi)
        # Method 2: Mean color
        else:
            return self._get_dominant_mean(roi)
            
    def _get_dominant_kmeans(self, roi: np.ndarray) -> Tuple[int, int, int]:
        """Get dominant color using K-means clustering"""
        try:
            # Reshape image to be a list of pixels
            pixels = roi.reshape((-1, 3))
            pixels = np.float32(pixels)
            
            # Apply K-means
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
            k = 1  # Single dominant color
            _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Get the dominant color
            dominant = centers[0].astype(int)
            return tuple(dominant)
            
        except Exception as e:
            logger.error(f"K-means failed: {e}")
            return self._get_dominant_mean(roi)
            
    def _get_dominant_mean(self, roi: np.ndarray) -> Tuple[int, int, int]:
        """Get dominant color using mean"""
        # Calculate mean color
        mean_color = cv2.mean(roi)[:3]
        return tuple(map(int, mean_color))
        
    def get_closest_color(self, bgr: Tuple[int, int, int]) -> ColorSample:
        """
        Get the closest color from palette
        
        Args:
            bgr: BGR color tuple
            
        Returns:
            ColorSample with closest match
        """
        if self.detection_method == 'CIEDE2000':
            return self._get_closest_ciede2000(bgr)
        elif self.detection_method == 'DELTA_E_1976':
            return self._get_closest_delta_e_1976(bgr)
        else:
            return self._get_closest_euclidean(bgr)
            
    def get_closest_color_name(self, bgr: Tuple[int, int, int]) -> str:
        """Get just the color name of closest match"""
        return self.get_closest_color(bgr).name
        
    def _get_closest_euclidean(self, bgr: Tuple[int, int, int]) -> ColorSample:
        """Get closest color using Euclidean distance in BGR space"""
        min_distance = float('inf')
        closest_name = 'white'
        
        for name, palette_bgr in self.color_palette.items():
            # Calculate Euclidean distance
            distance = np.sqrt(
                (bgr[0] - palette_bgr[0]) ** 2 +
                (bgr[1] - palette_bgr[1]) ** 2 +
                (bgr[2] - palette_bgr[2]) ** 2
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_name = name
                
        # Calculate confidence (inverse of distance, normalized)
        max_distance = np.sqrt(3 * 255 ** 2)  # Maximum possible distance
        confidence = 1.0 - (min_distance / max_distance)
        
        return ColorSample(
            bgr=self.color_palette[closest_name],
            lab=self.palette_lab[closest_name],
            name=closest_name,
            confidence=confidence
        )
        
    def _get_closest_delta_e_1976(self, bgr: Tuple[int, int, int]) -> ColorSample:
        """Get closest color using Delta E 1976 (CIE76) in LAB space"""
        lab = self.bgr_to_lab(bgr)
        
        min_distance = float('inf')
        closest_name = 'white'
        
        for name, palette_lab in self.palette_lab.items():
            # Calculate Delta E 1976
            distance = self.delta_e_1976(lab, palette_lab)
            
            if distance < min_distance:
                min_distance = distance
                closest_name = name
                
        # Calculate confidence
        max_distance = 100.0  # Approximate maximum Delta E
        confidence = max(0, 1.0 - (min_distance / max_distance))
        
        return ColorSample(
            bgr=self.color_palette[closest_name],
            lab=self.palette_lab[closest_name],
            name=closest_name,
            confidence=confidence
        )
        
    def _get_closest_ciede2000(self, bgr: Tuple[int, int, int]) -> ColorSample:
        """Get closest color using CIEDE2000 algorithm"""
        lab = self.bgr_to_lab(bgr)
        
        min_distance = float('inf')
        closest_name = 'white'
        
        for name, palette_lab in self.palette_lab.items():
            # Calculate CIEDE2000 distance
            distance = self.ciede2000(lab, palette_lab)
            
            if distance < min_distance:
                min_distance = distance
                closest_name = name
                
        # Calculate confidence
        max_distance = 100.0  # Approximate maximum CIEDE2000
        confidence = max(0, 1.0 - (min_distance / max_distance))
        
        return ColorSample(
            bgr=self.color_palette[closest_name],
            lab=self.palette_lab[closest_name],
            name=closest_name,
            confidence=confidence
        )
        
    def bgr_to_lab(self, bgr: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """
        Convert BGR to LAB color space
        
        Args:
            bgr: BGR color tuple (0-255)
            
        Returns:
            LAB color tuple
        """
        # Convert BGR to RGB
        rgb = (bgr[2], bgr[1], bgr[0])
        
        # Normalize RGB values
        r, g, b = [x / 255.0 for x in rgb]
        
        # Apply gamma correction
        r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
        g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
        b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92
        
        # Convert to XYZ (D65 illuminant)
        x = (r * 0.4124564 + g * 0.3575761 + b * 0.1804375) * 100
        y = (r * 0.2126729 + g * 0.7151522 + b * 0.0721750) * 100
        z = (r * 0.0193339 + g * 0.1191920 + b * 0.9503041) * 100
        
        # Normalize for D65 illuminant
        x /= 95.047
        y /= 100.000
        z /= 108.883
        
        # Apply transformation
        fx = x ** (1/3) if x > 0.008856 else (7.787 * x + 16/116)
        fy = y ** (1/3) if y > 0.008856 else (7.787 * y + 16/116)
        fz = z ** (1/3) if z > 0.008856 else (7.787 * z + 16/116)
        
        # Calculate LAB values
        l = 116 * fy - 16
        a = 500 * (fx - fy)
        b = 200 * (fy - fz)
        
        return (l, a, b)
        
    def delta_e_1976(self, lab1: Tuple[float, float, float], 
                     lab2: Tuple[float, float, float]) -> float:
        """
        Calculate Delta E 1976 (CIE76) color difference
        
        Args:
            lab1: First LAB color
            lab2: Second LAB color
            
        Returns:
            Delta E value
        """
        dl = lab1[0] - lab2[0]
        da = lab1[1] - lab2[1]
        db = lab1[2] - lab2[2]
        
        return math.sqrt(dl*dl + da*da + db*db)
        
    def ciede2000(self, lab1: Tuple[float, float, float], 
                  lab2: Tuple[float, float, float]) -> float:
        """
        Calculate CIEDE2000 color difference
        
        This is the most perceptually uniform color difference formula.
        
        Args:
            lab1: First LAB color
            lab2: Second LAB color
            
        Returns:
            Delta E 2000 value
        """
        # Unpack LAB values
        l1, a1, b1 = lab1
        l2, a2, b2 = lab2
        
        # Calculate C and h
        c1 = math.sqrt(a1*a1 + b1*b1)
        c2 = math.sqrt(a2*a2 + b2*b2)
        c_avg = (c1 + c2) / 2
        
        # Calculate G
        c7 = c_avg ** 7
        c25_7 = 6103515625  # 25^7
        g = 0.5 * (1 - math.sqrt(c7 / (c7 + c25_7)))
        
        # Calculate a'
        a1_prime = a1 * (1 + g)
        a2_prime = a2 * (1 + g)
        
        # Calculate C' and h'
        c1_prime = math.sqrt(a1_prime*a1_prime + b1*b1)
        c2_prime = math.sqrt(a2_prime*a2_prime + b2*b2)
        
        h1_prime = math.atan2(b1, a1_prime)
        h2_prime = math.atan2(b2, a2_prime)
        
        # Convert to degrees
        h1_prime = math.degrees(h1_prime)
        h2_prime = math.degrees(h2_prime)
        
        # Ensure h' is between 0 and 360
        if h1_prime < 0:
            h1_prime += 360
        if h2_prime < 0:
            h2_prime += 360
            
        # Calculate deltas
        delta_l_prime = l2 - l1
        delta_c_prime = c2_prime - c1_prime
        
        # Calculate delta h'
        if c1_prime * c2_prime == 0:
            delta_h_prime = 0
        elif abs(h2_prime - h1_prime) <= 180:
            delta_h_prime = h2_prime - h1_prime
        elif h2_prime - h1_prime > 180:
            delta_h_prime = h2_prime - h1_prime - 360
        else:
            delta_h_prime = h2_prime - h1_prime + 360
            
        # Calculate delta H'
        delta_H_prime = 2 * math.sqrt(c1_prime * c2_prime) * math.sin(math.radians(delta_h_prime / 2))
        
        # Calculate averages
        l_avg_prime = (l1 + l2) / 2
        c_avg_prime = (c1_prime + c2_prime) / 2
        
        # Calculate h_avg_prime
        if c1_prime * c2_prime == 0:
            h_avg_prime = h1_prime + h2_prime
        elif abs(h1_prime - h2_prime) <= 180:
            h_avg_prime = (h1_prime + h2_prime) / 2
        elif h1_prime + h2_prime < 360:
            h_avg_prime = (h1_prime + h2_prime + 360) / 2
        else:
            h_avg_prime = (h1_prime + h2_prime - 360) / 2
            
        # Calculate T
        t = (1 - 0.17 * math.cos(math.radians(h_avg_prime - 30)) +
             0.24 * math.cos(math.radians(2 * h_avg_prime)) +
             0.32 * math.cos(math.radians(3 * h_avg_prime + 6)) -
             0.20 * math.cos(math.radians(4 * h_avg_prime - 63)))
             
        # Calculate RT
        delta_theta = 30 * math.exp(-((h_avg_prime - 275) / 25) ** 2)
        c_avg_prime_7 = c_avg_prime ** 7
        rc = 2 * math.sqrt(c_avg_prime_7 / (c_avg_prime_7 + c25_7))
        rt = -rc * math.sin(math.radians(2 * delta_theta))
        
        # Calculate SL, SC, SH
        sl = 1 + (0.015 * (l_avg_prime - 50) ** 2) / math.sqrt(20 + (l_avg_prime - 50) ** 2)
        sc = 1 + 0.045 * c_avg_prime
        sh = 1 + 0.015 * c_avg_prime * t
        
        # Calculate final Delta E 2000
        kl = kc = kh = 1  # Parametric factors (usually 1)
        
        delta_e = math.sqrt(
            (delta_l_prime / (kl * sl)) ** 2 +
            (delta_c_prime / (kc * sc)) ** 2 +
            (delta_H_prime / (kh * sh)) ** 2 +
            rt * (delta_c_prime / (kc * sc)) * (delta_H_prime / (kh * sh))
        )
        
        return delta_e
        
    def find_contours(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Find cube sticker contours in image
        
        Args:
            image: Input image (BGR)
            
        Returns:
            List of (x, y, w, h) bounding rectangles
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 30, 90)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours
        filtered = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 500 or area > 5000:  # Filter by area
                continue
                
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check aspect ratio
            aspect_ratio = w / float(h)
            if aspect_ratio < 0.7 or aspect_ratio > 1.3:
                continue
                
            # Check if approximately square
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            if len(approx) >= 4 and len(approx) <= 6:
                filtered.append((x, y, w, h))
                
        return filtered
        
    def validate_colors(self, colors: List[Tuple[int, int, int]]) -> bool:
        """
        Validate that detected colors make sense for a cube face
        
        Args:
            colors: List of 9 BGR colors
            
        Returns:
            True if valid, False otherwise
        """
        if len(colors) != 9:
            return False
            
        # Check that center color (index 4) is one of the 6 cube colors
        center_color = self.get_closest_color_name(colors[4])
        if center_color not in self.color_palette:
            return False
            
        # Check that we don't have too many different colors
        unique_colors = set()
        for color in colors:
            color_name = self.get_closest_color_name(color)
            unique_colors.add(color_name)
            
        # A valid face should have at most 6 different colors
        if len(unique_colors) > 6:
            return False
            
        return True
        
    def auto_calibrate(self, sample_colors: Dict[str, List[Tuple[int, int, int]]]) -> Dict[str, Tuple[int, int, int]]:
        """
        Auto-calibrate colors from sample data
        
        Args:
            sample_colors: Dictionary mapping color names to list of sample BGR values
            
        Returns:
            Calibrated color palette
        """
        calibrated = {}
        
        for color_name, samples in sample_colors.items():
            if len(samples) == 0:
                # Use default if no samples
                calibrated[color_name] = self.default_colors.get(color_name, (128, 128, 128))
            else:
                # Calculate mean color
                mean_color = np.mean(samples, axis=0)
                calibrated[color_name] = tuple(map(int, mean_color))
                
        return calibrated
        
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast for better color detection
        
        Args:
            image: Input image (BGR)
            
        Returns:
            Enhanced image
        """
        # Convert to LAB
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Split channels
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels
        enhanced_lab = cv2.merge([l, a, b])
        
        # Convert back to BGR
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        return enhanced