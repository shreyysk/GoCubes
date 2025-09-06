import math
import json
import os

class Colors:
    def __init__(self):
        # Default color palette (BGR format for OpenCV)
        self.prominent_color_palette = {
            'red': (0, 0, 255),       # Pure red in BGR
            'orange': (0, 165, 255),   # Orange in BGR
            'blue': (255, 0, 0),       # Pure blue in BGR
            'green': (0, 255, 0),      # Pure green in BGR
            'white': (255, 255, 255),  # White
            'yellow': (0, 255, 255)    # Yellow in BGR
        }
        
        # Try to load calibrated colors from file
        try:
            # FIX: Use os.path.join for cross-platform compatibility
            colors_path = os.path.join('resources', 'colors.json')
            if os.path.exists(colors_path):
                with open(colors_path, 'r') as f:
                    loaded_colors = json.load(f)
                    
                    # Convert lists back to tuples for consistency
                    for color_name, color_value in loaded_colors.items():
                        if isinstance(color_value, list):
                            self.prominent_color_palette[color_name] = tuple(color_value)
                        else:
                            self.prominent_color_palette[color_name] = color_value
                    
                    print(f"✅ Loaded calibrated colors from {colors_path}")
            else:
                print("ℹ️ No calibration file found, using default colors")
                print("   Run with -c flag to calibrate colors for your cube")
        except Exception as e:
            print(f"⚠️ Error loading colors: {e}")
            print("   Using default color values")
    
    def update_prominent_color(self, color, new_color):
        """Update a color in the palette"""
        # Ensure it's stored as tuple
        if isinstance(new_color, list):
            new_color = tuple(new_color)
        self.prominent_color_palette[color] = new_color
    
    def get_color_bgr(self, color_name):
        """Get BGR color value for a given color name"""
        return self.prominent_color_palette.get(color_name.lower(), (128, 128, 128))


# Instructions for each face (updated for standard cube)
instructions = {
    'white': "Center: White, Bottom: Green, Top: Blue",
    'yellow': "Center: Yellow, Bottom: Blue, Top: Green",
    'green': "Center: Green, Bottom: Yellow, Top: White",
    'blue': "Center: Blue, Bottom: White, Top: Yellow",
    'red': "Center: Red, Bottom: Yellow, Top: White",
    'orange': "Center: Orange, Bottom: Yellow, Top: White"
}


def bgr2lab(inputColor):
    """Convert BGR color to LAB color space for better color comparison"""
    # Handle both tuple and list inputs
    if isinstance(inputColor, list):
        inputColor = tuple(inputColor)
    
    # Convert BGR to RGB first
    r, g, b = inputColor[2], inputColor[1], inputColor[0]
    
    # Normalize RGB values
    rgb = [r/255.0, g/255.0, b/255.0]
    
    # Apply gamma correction
    for i in range(3):
        if rgb[i] > 0.04045:
            rgb[i] = ((rgb[i] + 0.055) / 1.055) ** 2.4
        else:
            rgb[i] = rgb[i] / 12.92
        rgb[i] *= 100
    
    # Convert RGB to XYZ
    x = rgb[0] * 0.4124 + rgb[1] * 0.3576 + rgb[2] * 0.1805
    y = rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722
    z = rgb[0] * 0.0193 + rgb[1] * 0.1192 + rgb[2] * 0.9505
    
    # Normalize XYZ (D65 illuminant)
    x /= 95.047
    y /= 100.000
    z /= 108.883
    
    # Convert XYZ to LAB
    xyz = [x, y, z]
    for i in range(3):
        if xyz[i] > 0.008856:
            xyz[i] = xyz[i] ** (1/3)
        else:
            xyz[i] = (7.787 * xyz[i]) + (16/116)
    
    # Calculate LAB values
    L = (116 * xyz[1]) - 16
    a = 500 * (xyz[0] - xyz[1])
    b = 200 * (xyz[1] - xyz[2])
    
    return [round(L, 4), round(a, 4), round(b, 4)]


def ciede2000(Lab_1, Lab_2):
    """
    Calculate CIEDE2000 color difference between two LAB colors.
    Lower values mean more similar colors.
    """
    C_25_7 = 6103515625  # 25**7
    
    L1, a1, b1 = Lab_1[0], Lab_1[1], Lab_1[2]
    L2, a2, b2 = Lab_2[0], Lab_2[1], Lab_2[2]
    
    # Calculate chroma
    C1 = math.sqrt(a1**2 + b1**2)
    C2 = math.sqrt(a2**2 + b2**2)
    C_ave = (C1 + C2) / 2
    
    # Calculate G adjustment
    G = 0.5 * (1 - math.sqrt(C_ave**7 / (C_ave**7 + C_25_7)))
    
    # Adjust a* values
    a1_ = (1 + G) * a1
    a2_ = (1 + G) * a2
    b1_ = b1
    b2_ = b2
    
    # Calculate new chroma values
    C1_ = math.sqrt(a1_**2 + b1_**2)
    C2_ = math.sqrt(a2_**2 + b2_**2)
    
    # Calculate hue angles
    if b1_ == 0 and a1_ == 0:
        h1_ = 0
    elif a1_ >= 0:
        h1_ = math.atan2(b1_, a1_)
    else:
        h1_ = math.atan2(b1_, a1_) + 2 * math.pi
    
    if b2_ == 0 and a2_ == 0:
        h2_ = 0
    elif a2_ >= 0:
        h2_ = math.atan2(b2_, a2_)
    else:
        h2_ = math.atan2(b2_, a2_) + 2 * math.pi
    
    # Calculate differences
    dL_ = L2 - L1
    dC_ = C2_ - C1_
    dh_ = h2_ - h1_
    
    if C1_ * C2_ == 0:
        dh_ = 0
    elif dh_ > math.pi:
        dh_ -= 2 * math.pi
    elif dh_ < -math.pi:
        dh_ += 2 * math.pi
    
    dH_ = 2 * math.sqrt(C1_ * C2_) * math.sin(dh_ / 2)
    
    # Calculate averages
    L_ave = (L1 + L2) / 2
    C_ave = (C1_ + C2_) / 2
    
    # Calculate average hue
    _dh = abs(h1_ - h2_)
    _sh = h1_ + h2_
    C1C2 = C1_ * C2_
    
    if _dh <= math.pi and C1C2 != 0:
        h_ave = (h1_ + h2_) / 2
    elif _dh > math.pi and _sh < 2 * math.pi and C1C2 != 0:
        h_ave = (h1_ + h2_) / 2 + math.pi
    elif _dh > math.pi and _sh >= 2 * math.pi and C1C2 != 0:
        h_ave = (h1_ + h2_) / 2 - math.pi
    else:
        h_ave = h1_ + h2_
    
    # Calculate T
    T = (1 - 0.17 * math.cos(h_ave - math.pi / 6) +
         0.24 * math.cos(2 * h_ave) +
         0.32 * math.cos(3 * h_ave + math.pi / 30) -
         0.20 * math.cos(4 * h_ave - 63 * math.pi / 180))
    
    # Calculate rotation term
    h_ave_deg = h_ave * 180 / math.pi
    if h_ave_deg < 0:
        h_ave_deg += 360
    elif h_ave_deg > 360:
        h_ave_deg -= 360
    
    dTheta = 30 * math.exp(-(((h_ave_deg - 275) / 25)**2))
    
    # Calculate RC and RT
    R_C = 2 * math.sqrt(C_ave**7 / (C_ave**7 + C_25_7))
    R_T = -math.sin(dTheta * math.pi / 90) * R_C
    
    # Calculate SL, SC, SH
    Lm50s = (L_ave - 50)**2
    S_L = 1 + 0.015 * Lm50s / math.sqrt(20 + Lm50s)
    S_C = 1 + 0.045 * C_ave
    S_H = 1 + 0.015 * C_ave * T
    
    # Calculate final color difference
    k_L = k_C = k_H = 1  # Weighting factors
    
    f_L = dL_ / (k_L * S_L)
    f_C = dC_ / (k_C * S_C)
    f_H = dH_ / (k_H * S_H)
    
    dE_00 = math.sqrt(f_L**2 + f_C**2 + f_H**2 + R_T * f_C * f_H)
    
    return dE_00


def color_distance_bgr(color1, color2):
    """
    Calculate color distance between two BGR colors.
    Returns CIEDE2000 distance (lower = more similar)
    """
    lab1 = bgr2lab(color1)
    lab2 = bgr2lab(color2)
    return ciede2000(lab1, lab2)


def get_closest_color(bgr_color, color_palette):
    """
    Find the closest color in the palette to the given BGR color.
    Returns (color_name, distance)
    """
    lab_color = bgr2lab(bgr_color)
    distances = []
    
    for color_name, palette_bgr in color_palette.items():
        palette_lab = bgr2lab(palette_bgr)
        distance = ciede2000(lab_color, palette_lab)
        distances.append((color_name, distance))
    
    # Sort by distance and return closest
    distances.sort(key=lambda x: x[1])
    return distances[0]


# Validation helper for cube configuration
def validate_face_colors(face_matrix):
    """
    Validate that a face has valid color distribution.
    Returns (is_valid, message)
    """
    if not face_matrix or len(face_matrix) != 3:
        return False, "Invalid face structure"
    
    # Check dimensions
    for row in face_matrix:
        if len(row) != 3:
            return False, "Invalid row size"
    
    # Check center color
    center = face_matrix[1][1]
    if center not in ['white', 'yellow', 'red', 'orange', 'green', 'blue']:
        return False, f"Invalid center color: {center}"
    
    return True, "Valid face"