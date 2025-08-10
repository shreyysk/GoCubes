import os

def fix_cube_2d():
    filepath = os.path.join('src', 'visualizer', 'cube_2d.py')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix all drawText calls
    for i, line in enumerate(lines):
        if 'painter.drawText' in line and 'face_size' in line:
            # Fix the specific line
            if 'x + face_size/2 - 5, y - 10' in line:
                lines[i] = '                painter.drawText(int(x + face_size/2 - 5), int(y - 10), face)\n'
            elif 'x + 2, y + 12' in line:
                lines[i] = '            painter.drawText(int(x + 2), int(y + 12), str(index))\n'
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"Fixed drawText calls in {filepath}")

if __name__ == '__main__':
    fix_cube_2d()