#!/usr/bin/env python3
"""
Enhanced Rubik's Cube Scanner with Interactive Manual Editor
Combines automatic scanning with manual correction capability
"""

import sys
import cv2
import time
import argparse
import collections
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from predict import predicted_color
from draw import draw_2d_cube_state
import helpers
from rubik_solver import utils
from PyCube import PyCube
import calibrate


# Valid cube constraints
VALID_EDGES = {
    frozenset({'white', 'green'}), frozenset({'white', 'red'}),
    frozenset({'white', 'blue'}), frozenset({'white', 'orange'}),
    frozenset({'yellow', 'green'}), frozenset({'yellow', 'red'}),
    frozenset({'yellow', 'blue'}), frozenset({'yellow', 'orange'}),
    frozenset({'green', 'red'}), frozenset({'green', 'orange'}),
    frozenset({'blue', 'red'}), frozenset({'blue', 'orange'})
}


class CubeEditor:
    """Interactive cube editor with 2D and 3D visualization"""
    
    def __init__(self, initial_faces=None):
        self.root = tk.Tk()
        self.root.title("Rubik's Cube Manual Editor")
        self.root.geometry("1200x800")
        
        # Color mapping
        self.colors = {
            'white': '#FFFFFF',
            'yellow': '#FFFF00',
            'red': '#FF0000',
            'orange': '#FFA500',
            'green': '#00FF00',
            'blue': '#0000FF'
        }
        
        # Initialize faces (use scanned data or empty)
        if initial_faces:
            self.faces = self.convert_faces_to_dict(initial_faces)
        else:
            self.faces = self.initialize_empty_cube()
        
        self.selected_color = 'white'
        self.setup_ui()
        
        # 3D visualization thread
        self.visualization_thread = None
        self.viz_running = False
        
    def convert_faces_to_dict(self, scanned_faces):
        """Convert scanned Face objects to simple dict"""
        result = {}
        for name, face_obj in scanned_faces.items():
            if face_obj.scanned:
                result[name] = [row[:] for row in face_obj.face]
            else:
                # Initialize with center color correct
                result[name] = [[None]*3 for _ in range(3)]
                result[name][1][1] = name
        return result
    
    def initialize_empty_cube(self):
        """Create empty cube with correct centers"""
        faces = {}
        for name in ['white', 'yellow', 'red', 'orange', 'green', 'blue']:
            faces[name] = [[None]*3 for _ in range(3)]
            faces[name][1][1] = name  # Set center
        return faces
    
    def setup_ui(self):
        """Setup the UI components"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Left panel - 2D cube net
        left_frame = ttk.LabelFrame(main_frame, text="2D Cube Net", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        self.canvas = tk.Canvas(left_frame, width=600, height=600, bg='lightgray')
        self.canvas.pack()
        
        # Draw the cube net
        self.draw_cube_net()
        
        # Right panel - Controls
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Color selector
        color_frame = ttk.LabelFrame(right_frame, text="Select Color", padding="10")
        color_frame.pack(fill=tk.X, pady=5)
        
        for color in self.colors:
            btn = tk.Button(color_frame, text=color.upper(), bg=self.colors[color],
                          width=15, height=2,
                          command=lambda c=color: self.select_color(c))
            btn.pack(pady=2)
        
        # Status display
        status_frame = ttk.LabelFrame(right_frame, text="Cube Status", padding="10")
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_text = tk.Text(status_frame, height=10, width=30)
        self.status_text.pack()
        
        # Action buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Validate Cube",
                  command=self.validate_cube).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Auto-Fix Common Issues",
                  command=self.auto_fix).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Show 3D View",
                  command=self.show_3d_view).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Solve Cube",
                  command=self.solve_cube).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Reset",
                  command=self.reset_cube).pack(fill=tk.X, pady=2)
        
        # Instructions
        inst_frame = ttk.LabelFrame(right_frame, text="Instructions", padding="10")
        inst_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        instructions = """1. Click a color on the right
2. Click stickers to change them
3. Centers are locked (correct)
4. Validate to check errors
5. Auto-Fix for common issues
6. Solve when ready"""
        
        ttk.Label(inst_frame, text=instructions, justify=tk.LEFT).pack()
        
        self.update_status()
    
    def draw_cube_net(self):
        """Draw the 2D cube net on canvas"""
        self.canvas.delete("all")
        self.sticker_buttons = {}
        
        # Net layout positions
        positions = {
            'white': (1, 0),   # Top
            'orange': (0, 1),  # Left
            'green': (1, 1),   # Center
            'red': (2, 1),     # Right
            'blue': (3, 1),    # Far right
            'yellow': (1, 2),  # Bottom
        }
        
        cell_size = 40
        face_size = cell_size * 3
        offset_x = 100
        offset_y = 50
        
        for face_name, (fx, fy) in positions.items():
            face = self.faces[face_name]
            base_x = offset_x + fx * (face_size + 20)
            base_y = offset_y + fy * (face_size + 20)
            
            # Draw face label
            self.canvas.create_text(base_x + face_size//2, base_y - 10,
                                   text=face_name.upper(), font=("Arial", 12, "bold"))
            
            # Draw stickers
            for i in range(3):
                for j in range(3):
                    x = base_x + j * cell_size
                    y = base_y + i * cell_size
                    
                    color = face[i][j] if face[i][j] else 'gray'
                    fill_color = self.colors.get(color, 'gray')
                    
                    # Create rectangle
                    rect = self.canvas.create_rectangle(
                        x, y, x + cell_size, y + cell_size,
                        fill=fill_color, outline='black', width=2,
                        tags=f"{face_name}_{i}_{j}"
                    )
                    
                    # Make it clickable (except centers)
                    if not (i == 1 and j == 1):  # Not center
                        self.canvas.tag_bind(rect, '<Button-1>',
                                           lambda e, fn=face_name, r=i, c=j: self.sticker_clicked(fn, r, c))
                    else:
                        # Mark center with a dot
                        self.canvas.create_oval(
                            x + cell_size//2 - 3, y + cell_size//2 - 3,
                            x + cell_size//2 + 3, y + cell_size//2 + 3,
                            fill='black'
                        )
    
    def select_color(self, color):
        """Select active color for painting"""
        self.selected_color = color
        self.update_status()
    
    def sticker_clicked(self, face_name, row, col):
        """Handle sticker click - change color"""
        self.faces[face_name][row][col] = self.selected_color
        self.draw_cube_net()
        self.update_status()
    
    def update_status(self):
        """Update status display"""
        self.status_text.delete(1.0, tk.END)
        
        # Count colors
        color_counts = collections.Counter()
        for face in self.faces.values():
            for row in face:
                for color in row:
                    if color:
                        color_counts[color] += 1
        
        status = f"Selected: {self.selected_color.upper()}\n\n"
        status += "Color Counts:\n"
        for color in ['white', 'yellow', 'red', 'orange', 'green', 'blue']:
            count = color_counts.get(color, 0)
            mark = "✓" if count == 9 else "✗"
            status += f"{color:7s}: {count:2d}/9 {mark}\n"
        
        self.status_text.insert(1.0, status)
    
    def validate_cube(self):
        """Validate cube configuration"""
        errors = []
        
        # Check color counts
        color_counts = collections.Counter()
        for face in self.faces.values():
            for row in face:
                for color in row:
                    if color:
                        color_counts[color] += 1
        
        for color in ['white', 'yellow', 'red', 'orange', 'green', 'blue']:
            count = color_counts.get(color, 0)
            if count != 9:
                errors.append(f"{color}: {count}/9 stickers")
        
        # Check edges
        edges = self.get_edges()
        invalid_edges = [e for e in edges if e not in VALID_EDGES]
        if invalid_edges:
            errors.append(f"{len(invalid_edges)} invalid edges")
        
        if errors:
            messagebox.showwarning("Validation Failed", 
                                 "Issues found:\n" + "\n".join(errors))
        else:
            messagebox.showinfo("Validation Passed", 
                              "Cube configuration is valid!")
        
        return len(errors) == 0
    
    def get_edges(self):
        """Extract edge pieces from current configuration"""
        u = self.faces['white']
        d = self.faces['yellow']
        f = self.faces['green']
        b = self.faces['blue']
        r = self.faces['red']
        l = self.faces['orange']
        
        edges = [
            frozenset([u[2][1], f[0][1]]) if u[2][1] and f[0][1] else set(),
            frozenset([u[1][2], r[0][1]]) if u[1][2] and r[0][1] else set(),
            frozenset([u[0][1], b[0][1]]) if u[0][1] and b[0][1] else set(),
            frozenset([u[1][0], l[0][1]]) if u[1][0] and l[0][1] else set(),
            frozenset([d[0][1], f[2][1]]) if d[0][1] and f[2][1] else set(),
            frozenset([d[1][2], r[2][1]]) if d[1][2] and r[2][1] else set(),
            frozenset([d[2][1], b[2][1]]) if d[2][1] and b[2][1] else set(),
            frozenset([d[1][0], l[2][1]]) if d[1][0] and l[2][1] else set(),
            frozenset([f[1][2], r[1][0]]) if f[1][2] and r[1][0] else set(),
            frozenset([f[1][0], l[1][2]]) if f[1][0] and l[1][2] else set(),
            frozenset([b[1][2], r[1][2]]) if b[1][2] and r[1][2] else set(),
            frozenset([b[1][0], l[1][0]]) if b[1][0] and l[1][0] else set(),
        ]
        
        return [e for e in edges if len(e) == 2]
    
    def auto_fix(self):
        """Attempt to fix common issues"""
        # Count colors
        color_counts = collections.Counter()
        positions = []
        
        for face_name, face in self.faces.items():
            for i in range(3):
                for j in range(3):
                    if not (i == 1 and j == 1):  # Skip centers
                        color = face[i][j]
                        if color:
                            color_counts[color] += 1
                            positions.append((face_name, i, j, color))
        
        # Find imbalances
        over = [(c, n) for c, n in color_counts.items() if n > 8]
        under = [(c, n) for c, n in color_counts.items() if n < 8]
        
        if over and under:
            # Simple swap strategy
            for over_color, over_count in over:
                for under_color, under_count in under:
                    swaps_needed = min(over_count - 8, 8 - under_count)
                    swapped = 0
                    
                    for face_name, i, j, color in positions:
                        if color == over_color and swapped < swaps_needed:
                            self.faces[face_name][i][j] = under_color
                            swapped += 1
            
            self.draw_cube_net()
            self.update_status()
            messagebox.showinfo("Auto-Fix", "Applied automatic fixes")
        else:
            messagebox.showinfo("Auto-Fix", "No obvious issues to fix")
    
    def show_3d_view(self):
        """Launch 3D visualization in separate window"""
        # This would launch a pygame window with 3D cube
        messagebox.showinfo("3D View", "3D visualization would appear here\n(Requires pygame window)")
    
    def solve_cube(self):
        """Attempt to solve the cube"""
        if not self.validate_cube():
            if not messagebox.askyesno("Invalid Cube", 
                                      "Cube is invalid. Try to solve anyway?"):
                return
        
        # Convert to cube string
        cube_string = self.get_cube_string()
        
        try:
            solution = utils.solve(cube_string, 'Kociemba')
            
            # Show solution window
            sol_window = tk.Toplevel(self.root)
            sol_window.title("Solution Found!")
            sol_window.geometry("400x500")
            
            text = tk.Text(sol_window, wrap=tk.WORD)
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text.insert(tk.END, f"Solution: {solution}\n\n")
            text.insert(tk.END, f"Number of moves: {len(solution.split())}\n\n")
            text.insert(tk.END, "Step by step:\n")
            
            for i, move in enumerate(solution.split(), 1):
                text.insert(tk.END, f"{i:3d}. {move}\n")
            
            ttk.Button(sol_window, text="Launch 3D Animation",
                      command=lambda: self.launch_pycube(solution)).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Solve Failed", f"Could not solve cube:\n{str(e)}")
    
    def get_cube_string(self):
        """Convert current state to cube string"""
        color_map = {'white': 'w', 'yellow': 'y', 'red': 'r',
                     'orange': 'o', 'green': 'g', 'blue': 'b'}
        
        # URFDLB order
        order = ['white', 'red', 'green', 'yellow', 'orange', 'blue']
        result = []
        
        for face_name in order:
            for row in self.faces[face_name]:
                for color in row:
                    if color:
                        result.append(color_map[color])
                    else:
                        result.append('w')  # Default
        
        return ''.join(result)
    
    def launch_pycube(self, solution):
        """Launch PyCube visualization"""
        cube = PyCube()
        moves = []
        for move in solution.split():
            if len(move) > 1 and move[1] == '2':
                moves.extend([move[0], move[0]])
            else:
                moves.append(move)
        cube.run(moves)
    
    def reset_cube(self):
        """Reset to initial state"""
        if messagebox.askyesno("Reset", "Reset all changes?"):
            self.faces = self.initialize_empty_cube()
            self.draw_cube_net()
            self.update_status()
    
    def run(self):
        """Start the editor"""
        self.root.mainloop()


class Face:
    """Face scanning class (unchanged from original)"""
    def __init__(self, name, class_colors):
        self.class_colors = class_colors
        self.face = [[None, None, None],
                     [None, None, None],
                     [None, None, None]]
        self.name = name
        self.scanned = False
        self.confidence_scores = []
        
        self.instructions = {
            'white': "WHITE center, GREEN on bottom",
            'yellow': "YELLOW center, GREEN on top",
            'green': "GREEN center, WHITE on top",
            'blue': "BLUE center, WHITE on bottom",
            'red': "RED center, WHITE on top",
            'orange': "ORANGE center, WHITE on top"
        }
        
        self.colors = {"White": (255, 255, 255), "Yellow": (0, 255, 255),
                       "Orange": (0, 165, 255), "Red": (0, 0, 255),
                       "Green": (0, 255, 0), "Blue": (255, 0, 0)}
    
    # ... (rest of Face class methods remain the same)


def enhanced_color_prediction(frame, contour, colors_obj):
    """Enhanced color detection"""
    x, y, w, h = contour
    
    # Sample center
    center_x, center_y = x + w//2, y + h//2
    color_bgr = frame[center_y, center_x].tolist()
    
    # Get prediction
    prediction = predicted_color(color_bgr, colors_obj)
    
    # Simple confidence based on color distance
    lab_color = helpers.bgr2lab(color_bgr)
    ref_lab = helpers.bgr2lab(colors_obj.prominent_color_palette[prediction])
    distance = helpers.ciede2000(lab_color, ref_lab)
    
    confidence = max(0, 1 - (distance / 100))
    
    return prediction, confidence


def main():
    """Main entry point with scanner and manual editor"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--calibrate", action='store_true',
                       help="Calibrate colors before scanning")
    parser.add_argument("-m", "--manual", action='store_true',
                       help="Skip scanning, go directly to manual editor")
    args = parser.parse_args()
    
    print("🎲 Rubik's Cube Scanner with Manual Editor")
    print("="*50)
    
    colors = helpers.Colors()
    
    if args.calibrate:
        print("🎨 Starting color calibration...")
        calibrate.run(colors)
    
    if args.manual:
        # Direct to manual editor
        print("\n📝 Launching manual editor...")
        editor = CubeEditor()
        editor.run()
        return
    
    # Initialize faces for scanning
    faces = {
        'white': Face('white', colors),
        'yellow': Face('yellow', colors),
        'green': Face('green', colors),
        'blue': Face('blue', colors),
        'red': Face('red', colors),
        'orange': Face('orange', colors),
    }
    
    # Scanning logic here (simplified for brevity)
    print("\n📷 Starting camera scanning...")
    print("(Scanning code would go here)")
    
    # After scanning attempt
    print("\n⚠️ Scanning complete but validation failed")
    print("Launching manual editor to fix issues...")
    
    # Launch editor with scanned data
    editor = CubeEditor(initial_faces=faces)
    editor.run()


if __name__ == "__main__":
    main()