#!/usr/bin/env python3

# Imports
import sys
import cv2
import numpy as np
import json
import os
from functools import partial
from numpy import mean

# Import helpers
try:
    import helpers
except ImportError:
    print("Warning: helpers module not found")
    pass

COLORS = {"White": (255, 255, 255), "Yellow": (0, 255, 255), 
          "Orange": (0, 165, 255), "Red": (0, 0, 255), 
          "Green": (0, 255, 0), "Blue": (255, 0, 0)}

def getLimits(window_name):
    min_b = cv2.getTrackbarPos('min B', window_name)
    min_g = cv2.getTrackbarPos('min G', window_name)
    min_r = cv2.getTrackbarPos('min R', window_name)

    max_b = cv2.getTrackbarPos('max B', window_name)
    max_g = cv2.getTrackbarPos('max G', window_name)
    max_r = cv2.getTrackbarPos('max R', window_name)

    min_val = np.array([min_b, min_g, min_r], np.uint8)
    max_val = np.array([max_b, max_g, max_r], np.uint8)

    return min_val, max_val

def onTrackbar(val):
    pass  # Required for trackbar creation

def mouseClick(event, x, y, flags, param, window_name, img_dict):
    if event == cv2.EVENT_LBUTTONDOWN:
        image = img_dict['image']
        if 0 <= y < image.shape[0] and 0 <= x < image.shape[1]:
            b, g, r = image[y, x]
        
            # Adaptive range based on click
            range_val = 25  # Reduced from 30 for tighter color selection
            
            min_b = max(0, b - range_val)
            max_b = min(255, b + range_val)
            min_g = max(0, g - range_val)
            max_g = min(255, g + range_val)
            min_r = max(0, r - range_val)
            max_r = min(255, r + range_val)

            limits = {'min B': min_b, 'max B': max_b, 
                     'min G': min_g, 'max G': max_g, 
                     'min R': min_r, 'max R': max_r}

            for limit_name, limit_val in limits.items():
                cv2.setTrackbarPos(limit_name, window_name, limit_val)

def run(colors_class):
    """Run color calibration interface"""
    # Create windows
    name_segmented = 'Segmented View'
    name_original = 'Camera Feed - Click on Color'
    cv2.namedWindow(name_segmented, cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow(name_original, cv2.WINDOW_AUTOSIZE)

    # Initial trackbar values
    limits = {'B': {'max': 200, 'min': 100}, 
              'G': {'max': 200, 'min': 100}, 
              'R': {'max': 200, 'min': 100}}

    trackbars = {'min B': limits['B']['min'], 'max B': limits['B']['max'],
                 'min G': limits['G']['min'], 'max G': limits['G']['max'],
                 'min R': limits['R']['min'], 'max R': limits['R']['max']}

    for tb_name, tb_val in trackbars.items():
        cv2.createTrackbar(tb_name, name_segmented, tb_val, 255, onTrackbar)

    # Open camera
    capture = cv2.VideoCapture(0)
    if not capture.isOpened():
        print("ERROR: Cannot open camera")
        sys.exit(1)

    try:
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        ret, image = capture.read()
        if not ret:
            print("ERROR: Cannot read from camera")
            capture.release()
            sys.exit(1)
        
        img_dict = {'image': image}

        # Position windows
        cv2.moveWindow(name_original, 100, 0)
        cv2.moveWindow(name_segmented, image.shape[1] + 120, 0)

        # Mouse callback for color picking
        cv2.setMouseCallback(name_original, partial(mouseClick, 
                            window_name=name_segmented, img_dict=img_dict))

        # Color calibration order (scan order matches cube scanning)
        colors = {"W": "White", "Y": "Yellow", "G": "Green", 
                  "B": "Blue", "R": "Red", "O": "Orange"}
        color_order = ["W", "Y", "G", "B", "R", "O"]
        color_idx = 0
        
        # Store calibrated colors
        calibrated_colors = {}
        
        print("\n" + "="*50)
        print("         COLOR CALIBRATION MODE")
        print("="*50)
        print("Instructions:")
        print("  1. Show the Rubik's cube face with the color")
        print("  2. Click on the color in the camera feed")
        print("  3. Adjust thresholds if needed")
        print("  4. Press 'w' or ENTER to save")
        print("  5. Press 'q' or ESC to cancel")
        print("  6. Press Ctrl+C in terminal to force quit")
        print("="*50 + "\n")
        
        while color_idx < len(color_order):
            color_key = color_order[color_idx]
            color_name = colors[color_key]
            
            # Read frame
            ret, image = capture.read()
            if not ret:
                print("ERROR: Camera read error")
                break
                
            img_dict['image'] = image
            
            # Display instructions
            instruction = f"Calibrating {color_name} - Click on {color_name} sticker"
            cv2.putText(image, instruction, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLORS[color_name], 2)
            cv2.putText(image, "Press 'w'/ENTER to save, 'q'/ESC to cancel", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show progress
            progress = f"Progress: {color_idx}/{len(color_order)}"
            cv2.putText(image, progress, (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow(name_original, image)

            # Create mask based on current thresholds
            min_val, max_val = getLimits(name_segmented)
            image_thresholded = cv2.inRange(image, min_val, max_val)
            
            # Show detection count
            num_pixels = cv2.countNonZero(image_thresholded)
            detection_text = f"Detected pixels: {num_pixels}"
            cv2.putText(image_thresholded, detection_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, 255, 1)
            
            cv2.imshow(name_segmented, image_thresholded)

            # Handle keyboard input
            key = cv2.waitKey(10) & 0xFF

            if key == ord('w') or key == 13:  # 'w' or ENTER - save color
                min_list = min_val.tolist()
                max_list = max_val.tolist()
                
                # Calculate average color (for display and detection)
                avg_b = int(mean([min_list[0], max_list[0]]))
                avg_g = int(mean([min_list[1], max_list[1]]))
                avg_r = int(mean([min_list[2], max_list[2]]))
                average_bgr = (avg_b, avg_g, avg_r)
                
                # Store as list (JSON compatible)
                calibrated_colors[color_name.lower()] = list(average_bgr)
                
                print(f"SAVED {color_name}: BGR{average_bgr}")
                color_idx += 1
                
                if color_idx == len(color_order):
                    # All colors calibrated - save to file
                    colors_class.prominent_color_palette = calibrated_colors
                    
                    # Ensure directory exists
                    if not os.path.exists('resources'):
                        os.makedirs('resources')
                    
                    # Save as JSON
                    with open('resources/colors.json', 'w') as f:
                        json.dump(calibrated_colors, f, indent=2)
                    
                    print("\n" + "="*50)
                    print("Calibration Complete!")
                    print(f"   Saved to: resources/colors.json")
                    print("="*50)
                    break

            elif key == ord('q') or key == 27:  # 'q' or ESC - cancel
                print("\nCalibration cancelled")
                break
            
            elif key == ord('r'):  # 'r' - reset current color
                # Reset trackbars to default
                for tb_name, tb_val in trackbars.items():
                    cv2.setTrackbarPos(tb_name, name_segmented, tb_val)
                print(f"↻ Reset {color_name} thresholds")
    finally:
        # FEATURE: Ensure camera is released and windows are closed on exit
        if capture.isOpened():
            capture.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    print("Running color calibration standalone...")
    
    # Check if helpers module is available
    if 'helpers' in sys.modules:
        colors_obj = helpers.Colors()
        run(colors_obj)
    else:
        # Create a minimal Colors class for standalone operation
        class MinimalColors:
            def __init__(self):
                self.prominent_color_palette = {
                    'red': [0, 0, 255],
                    'orange': [0, 165, 255],
                    'blue': [255, 0, 0],
                    'green': [0, 255, 0],
                    'white': [255, 255, 255],
                    'yellow': [0, 255, 255]
                }
        
        colors_obj = MinimalColors()
        run(colors_obj)