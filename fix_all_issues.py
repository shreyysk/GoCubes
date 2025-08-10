#!/usr/bin/env python3
"""Fix all remaining issues"""

import os

def fix_files():
    # Fix cube_2d.py
    cube2d_path = os.path.join('src', 'visualizer', 'cube_2d.py')
    if os.path.exists(cube2d_path):
        with open(cube2d_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix all float to int conversions for drawText
        content = content.replace(
            'painter.drawText(x + face_size/2 - 5, y - 10, face)',
            'painter.drawText(int(x + face_size/2 - 5), int(y - 10), face)'
        )
        content = content.replace(
            'painter.drawText(x + 2, y + 12, str(index))',
            'painter.drawText(int(x + 2), int(y + 12), str(index))'
        )
        
        with open(cube2d_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Fixed {cube2d_path}")
    
    # Fix webcam.py camera detection
    webcam_path = os.path.join('src', 'scanner', 'webcam.py')
    if os.path.exists(webcam_path):
        with open(webcam_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Change camera range from 3 to 1
        content = content.replace(
            'self.camera_combo.addItems([f"Camera {i}" for i in range(3)])',
            'self.camera_combo.addItems([f"Camera {i}" for i in range(1)])'
        )
        
        with open(webcam_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Fixed {webcam_path}")
    
    print("\n✅ All fixes applied!")
    print("Now run: python run.py")

if __name__ == '__main__':
    fix_files()