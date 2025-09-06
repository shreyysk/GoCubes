#!/usr/bin/env python3
"""
Hybrid 3D + 2D Manual Editor for Rubik's Cube Scanner
Automatically launches when camera detection produces invalid state
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import collections
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import time
from rubik_solver import utils
import signal

# Valid cube constraints
VALID_EDGES = {
    frozenset({'white', 'green'}), frozenset({'white', 'red'}),
    frozenset({'white', 'blue'}), frozenset({'white', 'orange'}),
    frozenset({'yellow', 'green'}), frozenset({'yellow', 'red'}),
    frozenset({'yellow', 'blue'}), frozenset({'yellow', 'orange'}),
    frozenset({'green', 'red'}), frozenset({'green', 'orange'}),
    frozenset({'blue', 'red'}), frozenset({'blue', 'orange'})
}

VALID_CORNERS = {
    frozenset({'white', 'red', 'green'}), frozenset({'white', 'red', 'blue'}),
    frozenset({'white', 'orange', 'blue'}), frozenset({'white', 'orange', 'green'}),
    frozenset({'yellow', 'green', 'orange'}), frozenset({'yellow', 'green', 'red'}),
    frozenset({'yellow', 'red', 'blue'}), frozenset({'yellow', 'orange', 'blue'})
}


class Cube3DViewer:
    """3D cube visualization using pygame"""
    
    def __init__(self, parent_editor):
        self.editor = parent_editor
        self.running = False
        self.thread = None
        
    def start(self):
        """Start 3D viewer in separate thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run_viewer)
            self.thread.daemon = True
            self.thread.start()
    
    def stop(self):
        """Stop 3D viewer"""
        self.running = False
        
    def run_viewer(self):
        """Run the 3D viewer window"""
        pygame.init()
        display = (600, 500)
        pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("3D Cube Preview - Drag to rotate")
        
        gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -5)
        glEnable(GL_DEPTH_TEST)
        
        rotation_x = 0
        rotation_y = 0
        mouse_down = False
        last_pos = (0, 0)
        
        clock = pygame.time.Clock()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mouse_down = True
                        last_pos = pygame.mouse.get_pos()
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        mouse_down = False
                elif event.type == pygame.MOUSEMOTION:
                    if mouse_down:
                        x, y = pygame.mouse.get_pos()
                        dx = x - last_pos[0]
                        dy = y - last_pos[1]
                        rotation_x += dy * 0.5
                        rotation_y += dx * 0.5
                        last_pos = (x, y)
            
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glPushMatrix()
            glRotatef(rotation_x, 1, 0, 0)
            glRotatef(rotation_y, 0, 1, 0)
            
            self.draw_cube()
            
            glPopMatrix()
            pygame.display.flip()
            clock.tick(30)
        
        pygame.quit()
    
    def draw_cube(self):
        """Draw the 3D cube with current colors"""
        # FIX: Copy face data to prevent threading race conditions
        # The main editor thread modifies self.editor.faces while this thread reads it.
        faces = self.editor.copy_faces(self.editor.faces)
        
        # Define cube vertices
        vertices = [
            [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],  # Front (0,1,2,3)
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1]  # Back (4,5,6,7)
        ]
        
        # Face definitions with sticker positions and their 3D corners.
        # This mapping ensures the 2D net correctly maps to the 3D preview without mirroring.
        face_defs = {
            'green':  {'normal': [0, 0, 1],  'corners': [3, 2, 1, 0]},   # Front
            'blue':   {'normal': [0, 0, -1], 'corners': [6, 7, 4, 5]},   # Back
            'red':    {'normal': [1, 0, 0],  'corners': [2, 6, 5, 1]},   # Right
            'orange': {'normal': [-1, 0, 0], 'corners': [7, 3, 0, 4]},   # Left
            'white':  {'normal': [0, 1, 0],  'corners': [7, 6, 2, 3]},   # Top
            'yellow': {'normal': [0, -1, 0], 'corners': [0, 1, 5, 4]}    # Bottom
        }
        
        color_map = {
            'white': (1.0, 1.0, 1.0),
            'yellow': (1.0, 1.0, 0.0),
            'red': (1.0, 0.0, 0.0),
            'orange': (1.0, 0.5, 0.0),
            'green': (0.0, 1.0, 0.0),
            'blue': (0.0, 0.0, 1.0),
            None: (0.3, 0.3, 0.3)
        }
        
        # Helper for linear interpolation
        def lerp(a, b, t):
            return [a[k] + (b[k] - a[k]) * t for k in range(3)]
        
        # Helper for bilinear interpolation to find points on a face
        def bilinear(p00, p10, p01, p11, u, v):
            p0 = lerp(p00, p10, u)
            p1 = lerp(p01, p11, u)
            return lerp(p0, p1, v)
            
        # Draw each face
        for face_name, face_def in face_defs.items():
            corners_idx = face_def['corners']
            face_data = faces.get(face_name, [[None]*3 for _ in range(3)])
            
            # Get the 3D coordinates of the face's corner vertices
            v0 = vertices[corners_idx[0]] # Top-Left
            v1 = vertices[corners_idx[1]] # Top-Right
            v2 = vertices[corners_idx[2]] # Bottom-Right
            v3 = vertices[corners_idx[3]] # Bottom-Left
            
            # Draw the 9 stickers for this face
            glBegin(GL_QUADS)
            for i in range(3): # row
                for j in range(3): # col
                    color = face_data[i][j]
                    glColor3fv(color_map.get(color, (0.3, 0.3, 0.3)))
                    
                    # Calculate UV coordinates for this sticker on the face
                    u_start = j / 3.0
                    u_end = (j + 1) / 3.0
                    v_start = i / 3.0
                    v_end = (i + 1) / 3.0
                    
                    # Get the 4 corner points of the current sticker
                    p1 = bilinear(v0, v1, v3, v2, u_start, v_start)
                    p2 = bilinear(v0, v1, v3, v2, u_end, v_start)
                    p3 = bilinear(v0, v1, v3, v2, u_end, v_end)
                    p4 = bilinear(v0, v1, v3, v2, u_start, v_end)
                    
                    # Scale down slightly for gaps between stickers (aesthetic)
                    scale = 0.95
                    center = bilinear(v0, v1, v3, v2, (u_start+u_end)/2, (v_start+v_end)/2)
                    
                    # Draw scaled sticker quadrilateral
                    for p in [p1, p2, p3, p4]:
                        scaled = [center[k] + (p[k] - center[k]) * scale for k in range(3)]
                        glVertex3fv(scaled)
            
            glEnd()
            
            # Draw black lines between stickers
            glColor3fv((0, 0, 0))
            glLineWidth(2.0)
            glBegin(GL_LINES)
            
            # Draw horizontal lines
            for i in range(4):
                v_interp = i / 3.0
                p1 = bilinear(v0, v1, v3, v2, 0.0, v_interp)
                p2 = bilinear(v0, v1, v3, v2, 1.0, v_interp)
                glVertex3fv(p1)
                glVertex3fv(p2)
            
            # Draw vertical lines
            for j in range(4):
                u_interp = j / 3.0
                p1 = bilinear(v0, v1, v3, v2, u_interp, 0.0)
                p2 = bilinear(v0, v1, v3, v2, u_interp, 1.0)
                glVertex3fv(p1)
                glVertex3fv(p2)
            
            glEnd()


class HybridCubeEditor:
    """Main editor window with 2D net and controls"""
    
    def __init__(self, scanned_faces=None, confidence_scores=None):
        self.root = tk.Tk()
        self.root.title("Fix Your Rubik's Cube")
        self.root.state('zoomed')
        
        # FEATURE: Bind Escape key to close the editor window
        self.root.bind('<Escape>', self.close_editor)
        
        # FEATURE: Handle Ctrl+C from the command line to close gracefully
        signal.signal(signal.SIGINT, self.handle_ctrl_c)
        
        # Color definitions
        self.colors = {
            'white': '#FFFFFF',
            'yellow': '#FFFF00', 
            'red': '#FF0000',
            'orange': '#FFA500',
            'green': '#00FF00',
            'blue': '#0000FF'
        }
        
        # Initialize faces from scanned data
        if scanned_faces:
            self.faces = self.convert_scanned_faces(scanned_faces)
            self.original_faces = self.copy_faces(self.faces)
        else:
            self.faces = self.create_empty_cube()
            self.original_faces = self.copy_faces(self.faces)
            
        self.confidence = confidence_scores or {}
        self.selected_color = 'white'
        self.problem_pieces = []
        self.solution = None # Initialize solution attribute
        
        # 3D viewer
        self.viewer_3d = Cube3DViewer(self)
        
        # Setup UI
        self.setup_ui()
        
        # Analyze problems
        self.analyze_problems()
        
        # Start 3D viewer
        self.viewer_3d.start()

    def handle_ctrl_c(self, signum, frame):
        """Signal handler for Ctrl+C from terminal."""
        print("\nCtrl+C detected, closing editor...")
        self.close_editor()

    def close_editor(self, event=None):
        """Handles closing the editor window, ensuring no solution is returned."""
        self.solution = None
        self.root.quit()
        
    def convert_scanned_faces(self, scanned_faces):
        """Convert Face objects to simple dict"""
        result = {}
        for name, face_obj in scanned_faces.items():
            if face_obj.scanned and face_obj.face:
                result[name] = [row[:] for row in face_obj.face]
            else:
                result[name] = [[None]*3 for _ in range(3)]
                result[name][1][1] = name
        return result
    
    def copy_faces(self, faces):
        """Deep copy faces dict"""
        return {name: [row[:] for row in face] for name, face in faces.items()}
    
    def create_empty_cube(self):
        """Create cube with only centers set"""
        faces = {}
        for name in ['white', 'yellow', 'red', 'orange', 'green', 'blue']:
            faces[name] = [[None]*3 for _ in range(3)]
            faces[name][1][1] = name
        return faces
    
    def setup_ui(self):
        """Create the main UI"""
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header, text="🔧 Almost there! Just need to fix a few stickers", 
                 font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left: 2D Net
        left_frame = ttk.LabelFrame(main_frame, text="2D Cube Net - Click stickers to fix", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        self.canvas = tk.Canvas(left_frame, width=700, height=600, bg='#f0f0f0')
        self.canvas.pack()
        
        # Middle: Problems & Status
        middle_frame = ttk.Frame(main_frame)
        middle_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Problem list
        prob_frame = ttk.LabelFrame(middle_frame, text="Issues Found", padding="10")
        prob_frame.pack(fill=tk.BOTH, expand=True)
        
        self.problem_text = tk.Text(prob_frame, width=35, height=15, font=('Courier', 10))
        self.problem_text.pack()
        
        # Color selector
        color_frame = ttk.LabelFrame(middle_frame, text="Select Color to Paint", padding="5")
        color_frame.pack(fill=tk.X, pady=10)
        
        color_grid = ttk.Frame(color_frame)
        color_grid.pack()
        
        for i, (color, hex_color) in enumerate(self.colors.items()):
            btn = tk.Button(color_grid, text=color.upper(), bg=hex_color,
                          width=12, height=2, relief=tk.RAISED,
                          command=lambda c=color: self.select_color(c))
            btn.grid(row=i//2, column=i%2, padx=2, pady=2)
            if color == self.selected_color:
                btn.config(relief=tk.SUNKEN, borderwidth=3)
            setattr(self, f'btn_{color}', btn)
        
        # Right: Actions & Status
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Status
        status_frame = ttk.LabelFrame(right_frame, text="Color Count", padding="10")
        status_frame.pack(fill=tk.X)
        
        self.status_labels = {}
        for color in self.colors:
            frame = ttk.Frame(status_frame)
            frame.pack(fill=tk.X)
            ttk.Label(frame, text=f"{color.title()}:").pack(side=tk.LEFT, padx=5)
            label = ttk.Label(frame, text="0/9", font=('Arial', 10, 'bold'))
            label.pack(side=tk.LEFT)
            self.status_labels[color] = label
        
        # Actions
        action_frame = ttk.LabelFrame(right_frame, text="Actions", padding="10")
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="🔄 Auto-Fix Issues",
                  command=self.auto_fix).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="✅ Validate Cube",
                  command=self.validate_full).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="↩️ Undo Last Change",
                  command=self.undo_last).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="🔄 Reset to Scanned",
                  command=self.reset_to_original).pack(fill=tk.X, pady=2)
        
        ttk.Separator(action_frame).pack(fill=tk.X, pady=10)
        
        self.solve_btn = ttk.Button(action_frame, text="🎯 SOLVE CUBE",
                                   command=self.solve_cube)
        self.solve_btn.pack(fill=tk.X, pady=5)
        
        # Instructions
        inst_frame = ttk.LabelFrame(right_frame, text="Quick Guide", padding="10")
        inst_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        instructions = """1. Red borders = problem stickers
2. Click a color, then click stickers
3. Centers are locked (always correct)
4. Use Auto-Fix for quick solutions
5. 3D view updates live
6. Green = all issues fixed!"""
        
        ttk.Label(inst_frame, text=instructions, justify=tk.LEFT).pack()
        
        # Initial draw
        self.draw_net()
        self.update_status()
    
    def select_color(self, color):
        """Select painting color"""
        self.selected_color = color
        # Update button appearances
        for c in self.colors:
            btn = getattr(self, f'btn_{c}')
            if c == color:
                btn.config(relief=tk.SUNKEN, borderwidth=3)
            else:
                btn.config(relief=tk.RAISED, borderwidth=1)
    
    def draw_net(self):
        """Draw the 2D cube net"""
        self.canvas.delete("all")
        
        # Layout positions
        positions = {
            'white': (1, 0),
            'orange': (0, 1),
            'green': (1, 1),
            'red': (2, 1),
            'blue': (3, 1),
            'yellow': (1, 2)
        }
        
        cell_size = 50
        face_size = cell_size * 3
        # FIX: Reduced offsets and gaps to ensure all faces fit on the canvas
        offset_x = 50
        offset_y = 80
        gap = 15
        
        for face_name, (fx, fy) in positions.items():
            face = self.faces[face_name]
            base_x = offset_x + fx * (face_size + gap)
            base_y = offset_y + fy * (face_size + gap)
            
            # Face label
            self.canvas.create_text(base_x + face_size//2, base_y - 15,
                                   text=face_name.upper(), 
                                   font=('Arial', 12, 'bold'),
                                   fill=self.colors[face_name])
            
            # Draw stickers
            for i in range(3):
                for j in range(3):
                    x = base_x + j * cell_size
                    y = base_y + i * cell_size
                    
                    color = face[i][j] if face[i][j] else 'gray'
                    fill_color = self.colors.get(color, 'gray')
                    
                    # Check if this is a problem piece
                    is_problem = self.is_problem_sticker(face_name, i, j)
                    border_color = '#FF0000' if is_problem else 'black'
                    border_width = 4 if is_problem else 2
                    
                    # Draw rectangle
                    rect = self.canvas.create_rectangle(
                        x, y, x + cell_size, y + cell_size,
                        fill=fill_color, outline=border_color, 
                        width=border_width,
                        tags=f"{face_name}_{i}_{j}"
                    )
                    
                    # Make clickable (except centers)
                    if not (i == 1 and j == 1):
                        self.canvas.tag_bind(rect, '<Button-1>',
                                           lambda e, fn=face_name, r=i, c=j: self.sticker_clicked(fn, r, c))
                        # Add hover effect
                        self.canvas.tag_bind(rect, '<Enter>',
                                           lambda e, r=rect: self.canvas.itemconfig(r, width=5))
                        self.canvas.tag_bind(rect, '<Leave>',
                                           lambda e, r=rect, w=border_width: self.canvas.itemconfig(r, width=w))
                    else:
                        # Mark center
                        self.canvas.create_text(x + cell_size//2, y + cell_size//2,
                                               text="●", font=('Arial', 16))
    
    def is_problem_sticker(self, face_name, row, col):
        """Check if a sticker is part of a problem piece"""
        for prob in self.problem_pieces:
            if prob['face'] == face_name and prob['row'] == row and prob['col'] == col:
                return True
        return False
    
    def sticker_clicked(self, face_name, row, col):
        """Handle sticker click"""
        # Store for undo
        self.last_change = (face_name, row, col, self.faces[face_name][row][col])
        
        # Apply new color
        self.faces[face_name][row][col] = self.selected_color
        
        # Update displays
        self.draw_net()
        self.update_status()
        self.analyze_problems()
    
    def undo_last(self):
        """Undo last change"""
        if hasattr(self, 'last_change'):
            face, row, col, old_color = self.last_change
            self.faces[face][row][col] = old_color
            self.draw_net()
            self.update_status()
            self.analyze_problems()
    
    def reset_to_original(self):
        """Reset to originally scanned state"""
        if messagebox.askyesno("Reset", "Reset to original scanned state?"):
            self.faces = self.copy_faces(self.original_faces)
            self.draw_net()
            self.update_status()
            self.analyze_problems()
    
    def update_status(self):
        """Update color counts"""
        counts = collections.Counter()
        for face in self.faces.values():
            for row in face:
                for color in row:
                    if color:
                        counts[color] += 1
        
        for color in self.colors:
            count = counts.get(color, 0)
            text = f"{count}/9"
            label = self.status_labels[color]
            label.config(text=text)
            
            if count == 9:
                label.config(foreground='green')
            elif count > 9:
                label.config(foreground='red')
            else:
                label.config(foreground='orange')
    
    def analyze_problems(self):
        """Find and display problems"""
        self.problem_pieces = []
        problems = []
        
        # Check color counts
        counts = collections.Counter()
        for face in self.faces.values():
            for row in face:
                for color in row:
                    if color:
                        counts[color] += 1
        
        for color in ['white', 'yellow', 'red', 'orange', 'green', 'blue']:
            count = counts.get(color, 0)
            if count != 9:
                problems.append(f"❌ {color}: {count}/9 stickers")
        
        # FIX: Added a comprehensive edge validation to prevent solver errors
        # This checks for duplicates, missing edges, and impossible edges.
        all_edges = self.get_edges()
        if len(all_edges) != 12:
            problems.append(f"❌ Found {len(all_edges)}/12 edges. Check for unpainted stickers.")
        else:
            edge_counts = collections.Counter(all_edges)
            
            # Check for duplicate edges
            if len(edge_counts) < 12:
                for edge, count in edge_counts.items():
                    if count > 1:
                        problems.append(f"❌ Duplicate edge: {'-'.join(edge)}")
                        # Mark the problem pieces
                        indices = [i for i, e in enumerate(all_edges) if e == edge]
                        for i in indices:
                            self.mark_edge_as_problem(i)
            
            # Check for impossible or missing edges
            found_edge_set = set(all_edges)
            if found_edge_set != VALID_EDGES:
                impossible = found_edge_set - VALID_EDGES
                if impossible:
                    for edge in impossible:
                        problems.append(f"❌ Impossible edge: {'-'.join(edge)}")
                        indices = [i for i, e in enumerate(all_edges) if e == edge]
                        for i in indices:
                           self.mark_edge_as_problem(i)

                missing = VALID_EDGES - found_edge_set
                if missing:
                    problems.append(f"❌ {len(missing)} edge(s) are missing.")

        # Update problem display
        self.problem_text.delete(1.0, tk.END)
        if problems:
            self.problem_text.insert(1.0, "\n".join(problems))
            self.solve_btn.config(text="⚠️ SOLVE (Issues Present)")
        else:
            self.problem_text.insert(1.0, "✅ All issues fixed!\n\nCube is valid and ready to solve!")
            self.solve_btn.config(text="✅ SOLVE CUBE")
    
    def mark_edge_as_problem(self, edge_index):
        """Mark edge stickers as problems"""
        edge_positions = [
            [('white', 2, 1), ('green', 0, 1)],    # U-F
            [('white', 1, 2), ('red', 0, 1)],      # U-R
            [('white', 0, 1), ('blue', 0, 1)],     # U-B
            [('white', 1, 0), ('orange', 0, 1)],   # U-L
            [('yellow', 0, 1), ('green', 2, 1)],   # D-F
            [('yellow', 1, 2), ('red', 2, 1)],     # D-R
            [('yellow', 2, 1), ('blue', 2, 1)],    # D-B
            [('yellow', 1, 0), ('orange', 2, 1)],  # D-L
            [('green', 1, 2), ('red', 1, 0)],      # F-R
            [('green', 1, 0), ('orange', 1, 2)],   # F-L
            [('blue', 1, 2), ('red', 1, 2)],       # B-R
            [('blue', 1, 0), ('orange', 1, 0)],    # B-L
        ]
        
        if 0 <= edge_index < len(edge_positions):
            for face, row, col in edge_positions[edge_index]:
                self.problem_pieces.append({'face': face, 'row': row, 'col': col})
    
    def get_edges(self):
        """Extract all edges"""
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
        """Attempt automatic fixes"""
        # Count colors
        counts = collections.Counter()
        positions = []
        
        for face_name, face in self.faces.items():
            for i in range(3):
                for j in range(3):
                    if not (i == 1 and j == 1):  # Skip centers
                        color = face[i][j]
                        if color:
                            counts[color] += 1
                            positions.append((face_name, i, j, color))
        
        # Find imbalances
        over = [(c, n) for c, n in counts.items() if n > 8]
        under = [(c, n) for c, n in counts.items() if n < 8]
        
        fixed = False
        
        if over and under:
            # Try to fix by swapping
            for over_color, over_count in over:
                for under_color, under_count in under:
                    swaps = min(over_count - 8, 8 - under_count)
                    swapped = 0
                    
                    # Find invalid edges with these colors
                    edges = self.get_edges()
                    for i, edge in enumerate(edges):
                        if edge not in VALID_EDGES and over_color in edge:
                            # Try replacing with under_color
                            for face_name, i, j, color in positions:
                                if color == over_color and swapped < swaps:
                                    self.faces[face_name][i][j] = under_color
                                    swapped += 1
                                    fixed = True
                                    break
        
        if fixed:
            self.draw_net()
            self.update_status()
            self.analyze_problems()
            messagebox.showinfo("Auto-Fix", "Applied automatic fixes!")
        else:
            messagebox.showinfo("Auto-Fix", "No obvious fixes found. Try manual correction.")
    
    def validate_full(self):
        """Full validation"""
        errors = []
        
        # Color counts
        counts = collections.Counter()
        for face in self.faces.values():
            for row in face:
                for color in row:
                    if color:
                        counts[color] += 1
        
        for color in ['white', 'yellow', 'red', 'orange', 'green', 'blue']:
            count = counts.get(color, 0)
            if count != 9:
                errors.append(f"Color count for {color} is {count} (should be 9).")

        # Edges
        edges = self.get_edges()
        if len(edges) != 12:
            errors.append(f"Found {len(edges)}/12 edges. Some are missing.")
        
        for edge in edges:
            if edge not in VALID_EDGES:
                errors.append(f"Invalid edge: {'-'.join(edge)}")

        # (Corner validation could be added here for completeness)

        if not errors:
            messagebox.showinfo("Validation", "Success! The cube configuration is valid.")
        else:
            messagebox.showerror("Validation Failed", "The cube is invalid:\n\n- " + "\n- ".join(errors))

    def solve_cube(self):
        """Convert cube to string, solve, and close the editor."""
        # Final validation before solving
        counts = collections.Counter(c for face in self.faces.values() for row in face for c in row if c)
        if any(count != 9 for count in counts.values()):
            if not messagebox.askyesno("Warning", "Cube state is invalid (color counts are wrong). Solve anyway?"):
                return
        
        # The solver expects lowercase color characters (w, r, g, etc.)
        
        # 1. Map to get the face name from the URFDLB character (for correct ordering)
        face_char_to_name_map = {
            'U': 'white', 'R': 'red', 'F': 'green',
            'D': 'yellow', 'L': 'orange', 'B': 'blue'
        }
        
        # 2. Map to get the solver's color character from the sticker's color name
        color_name_to_char_map = {
            'white': 'w', 'yellow': 'y', 'green': 'g',
            'blue': 'b', 'red': 'r', 'orange': 'o'
        }
        
        try:
            cube_string_list = []
            # The Kociemba solver requires the faces in URFDLB order
            # The standard color scheme is U-White, R-Red, F-Green, D-Yellow, L-Orange, B-Blue
            for face_char in "URFDLB":
                face_name = face_char_to_name_map[face_char]
                
                # Append the colors of that face to the list
                for row in self.faces[face_name]:
                    for sticker_color in row:
                        if sticker_color is None:
                            # Handle case where a sticker might be unassigned
                            messagebox.showerror("Solver Error", "One or more stickers have not been assigned a color.")
                            return
                        # Map the color name (e.g., 'white') to its character (e.g., 'w')
                        cube_string_list.append(color_name_to_char_map[sticker_color])
            
            cube_string = "".join(cube_string_list)
            
            print(f"Generated Kociemba string: {cube_string}")
            
            # Solve the cube
            self.solution = " ".join(utils.solve(cube_string, 'Kociemba'))
            
            messagebox.showinfo("Solution Found!", f"Solution:\n{self.solution}")
            self.root.quit() # End the mainloop
            
        except Exception as e:
            messagebox.showerror("Solver Error", f"Could not solve the cube.\n\nError: {e}\n\nPlease double-check your colors.")


def launch_hybrid_editor(scanned_faces=None, confidence_scores=None):
    """Main function to create and run the editor, called from main.py."""
    editor = HybridCubeEditor(scanned_faces, confidence_scores)
    editor.root.mainloop()
    
    # After mainloop ends, stop the 3D viewer thread and destroy the window
    editor.viewer_3d.stop()
    editor.root.destroy()
    
    return editor.solution


if __name__ == '__main__':
    # This allows testing the editor directly without running the scanner
    print("Running hybrid editor in standalone test mode...")
    
    class DummyFace:
        def __init__(self, name):
            self.scanned = True
            self.name = name
            self.face = [[name]*3 for _ in range(3)]

    # Create a dummy solved-state cube for testing
    dummy_faces = {name: DummyFace(name) for name in ['white', 'yellow', 'red', 'orange', 'green', 'blue']}
    
    # Create a test cube state that's intentionally invalid or scrambled
    test_scanned_faces = {
        'white': [
            ['white', 'orange', 'red'],
            ['white', 'white', 'white'],
            ['white', 'blue', 'green']
        ],
        'yellow': [
            ['yellow', 'green', 'yellow'],
            ['red', 'yellow', 'orange'],
            ['yellow', 'blue', 'yellow']
        ],
        'green': [
            ['orange', 'white', 'green'],
            ['red', 'green', 'blue'],
            ['red', 'yellow', 'white']
        ],
        'blue': [
            ['green', 'orange', 'red'],
            ['yellow', 'blue', 'white'],
            ['blue', 'orange', 'red']
        ],
        'red': [
            ['blue', 'yellow', 'orange'],
            ['green', 'red', 'white'],
            ['orange', 'red', 'green']
        ],
        'orange': [
            ['white', 'blue', 'green'],
            ['orange', 'orange', 'red'],
            ['yellow', 'blue', 'red']
        ],
    }
    # Manually set the centers for the dummy faces
    for face_name, face_data in test_scanned_faces.items():
        if face_data[1][1] is None:
            face_data[1][1] = face_name


    class DummyScannedFace:
        def __init__(self, name, face_data):
            self.scanned = True
            self.face = face_data
            self.name = name
            
    scanned_faces_objects = {name: DummyScannedFace(name, data) for name, data in test_scanned_faces.items()}

    solution = launch_hybrid_editor(scanned_faces_objects)
    
    if solution is not None:
        print(f"Editor closed. Solution: '{solution}'")
    else:
        print("Editor closed without a solution.")