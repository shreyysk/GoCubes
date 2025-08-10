#!/usr/bin/env python3
"""Fix webcam issues"""

import os

def add_detect_cameras_method():
    webcam_path = os.path.join('src', 'scanner', 'webcam.py')
    
    with open(webcam_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find where to insert the method (before setup_ui)
    insert_index = -1
    for i, line in enumerate(lines):
        if 'def setup_ui(self):' in line:
            insert_index = i
            break
    
    if insert_index > 0:
        # Check if method already exists
        method_exists = any('def detect_available_cameras' in line for line in lines)
        
        if not method_exists:
            # Add the method
            method_code = '''    def detect_available_cameras(self):
        """Detect available cameras"""
        import cv2
        available_cameras = []
        
        # Check first 5 camera indices
        for i in range(5):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    available_cameras.append(i)
                    cap.release()
            except:
                pass
        
        if not available_cameras:
            logger.warning("No cameras detected, defaulting to camera 0")
            return [0]  # Default to camera 0
        
        logger.info(f"Detected cameras: {available_cameras}")
        return available_cameras
    
'''
            lines.insert(insert_index, method_code)
            
            with open(webcam_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f"✓ Added detect_available_cameras method to {webcam_path}")
        else:
            print(f"✓ Method already exists in {webcam_path}")
    else:
        print(f"✗ Could not find setup_ui method in {webcam_path}")
        print("  Falling back to simple fix...")
        
        # Simple fix - just replace the problematic line
        with open(webcam_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace(
            'available_cameras = self.detect_available_cameras()',
            '# available_cameras = self.detect_available_cameras()\n        available_cameras = [0]'
        )
        
        with open(webcam_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Applied simple fix to {webcam_path}")

if __name__ == '__main__':
    add_detect_cameras_method()
    print("\nNow run: python run.py")