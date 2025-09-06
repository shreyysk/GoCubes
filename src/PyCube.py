""" PyCube
Author: Michael King

Based and modified from original version found at:
http://stackoverflow.com/questions/30745703/rotating-a-cube-using-quaternions-in-pyopengl
"""
import sys
import copy
from quat import *
from geometry import *

import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *
import signal

moves = ''

class PyCube:
    def __init__(self):
        pygame.init()
        self.width = 800
        self.height = 600

        self.initial_pos = False

        # Handle Ctrl+C from the command line to close gracefully
        signal.signal(signal.SIGINT, self.handle_ctrl_c)

        self.moves_info = {
            'U': 'Turn UP face 90 degrees clockwise',
            'U\'': 'Turn UP face 90 degrees counterclockwise',
            'D': 'Turn DOWN face 90 degrees clockwise',
            'D\'': 'Turn DOWN face 90 degrees counterclockwise',
            'L': 'Turn LEFT face 90 degrees clockwise',
            'L\'': 'Turn LEFT face 90 degrees counterclockwise',
            'R': 'Turn RIGHT face 90 degrees clockwise',
            'R\'': 'Turn RIGHT face 90 degrees counterclockwise',
            'F': 'Turn FRONT face 90 degrees clockwise',
            'F\'': 'Turn FRONT face 90 degrees counterclockwise',
            'B': 'Turn BACK face 90 degrees clockwise',
            'B\'': 'Turn BACK face 90 degrees counterclockwise',
        }
        
        white = (255, 255, 255)
        green = (0, 255, 0)
        blue = (0, 0, 128)

        self.movements = []
        self.reverse_moves = {
            'U': 'U\'', 'U\'': 'U',
            'D': 'D\'', 'D\'': 'D',
            'L': 'L\'', 'L\'': 'L',
            'R': 'R\'', 'R\'': 'R',
            'F': 'F\'', 'F\'': 'F',
            'B': 'B\'', 'B\'': 'B',
        }
        self.last_moves = []
        self.display_surface = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        # MODIFICATION: Changed window caption
        pygame.display.set_caption('PyCube')

        self.font = pygame.font.Font('freesansbold.ttf', 32)
        self.text = self.font.render('', True, green, blue)
        self.textRect = self.text.get_rect()
        self.textRect.center = (self.width // 2, self.height // 2)

        # MODIFICATION: Changed background color to white
        glClearColor(1, 1, 1, 0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (self.width / self.height), 0.5, 40)
        glTranslatef(0.0, 0.0, -17.5)
        padding(0.3)

    def handle_ctrl_c(self, signum, frame):
        """Signal handler for Ctrl+C to quit gracefully."""
        print("\nCtrl+C detected, closing visualizer...")
        pygame.quit()
        quit()

    def create_window(self, width, height):
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL | RESIZABLE)
        gluPerspective(45, (width / height), 0.5, 40)
        
    def reverse(self, moves):
        result = []
        moves = moves[::-1]
        for i in moves:
            try:
                result.append(self.reverse_moves[i])
            except KeyError:
                if len(i) > 1 and i[1] == '2':
                    result.append(i[0])
                    result.append(i[0])
                else:
                    result.append(i) # Should not happen with valid input
            
        self._reverse = True
        return result

    def run(self, movements):
        movements = [str(i) for i in movements]
        _save_moves = copy.deepcopy(movements)
        self.movements = self.reverse(movements)
        
        global moves
        
        pad_toggle = False
        inc_x = 0
        inc_y = 0
        accum = (1, 0, 0, 0)
        zoom = 1

        def update():
            pygame.mouse.get_rel()
            rot_x = normalize(axisangle_to_q((1.0, 0.0, 0.0), inc_x))
            rot_y = normalize(axisangle_to_q((0.0, 1.0, 0.0), inc_y))
            nonlocal accum
            accum = q_mult(accum, rot_x)
            accum = q_mult(accum, rot_y)
            glMatrixMode(GL_MODELVIEW)
            glLoadMatrixf(q_to_mat4(accum))
            glScalef(zoom, zoom, zoom)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.draw_cube()
            pygame.display.flip()

        while True:
            self.display_surface.blit(self.text, self.textRect)
            update()
    
            theta_inc = 7
            theta = pi / 2 / theta_inc
            
            event = pygame.event.wait() # Wait for an event
            
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if self._reverse:
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
                self._reverse = False # Only post once

            if event.type == pygame.KEYDOWN:
                # Enable quit on 'q' or 'ESC'
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    pygame.quit()
                    quit()

                move = None
                reverse = False
                
                # Add Right Arrow for next move
                if event.key == pygame.K_RETURN or event.key == pygame.K_RIGHT:
                    if not self.movements:
                        print("Solution complete!")
                        continue
                    move_str = self.movements.pop(0)
                    self.last_moves.append(move_str)
                    if len(move_str) > 1 and move_str[1] == '\'':
                        move = move_str[0]
                        reverse = True
                    else:
                        move = move_str
                
                # Add Left Arrow for previous move
                elif event.key == pygame.K_BACKSPACE or event.key == pygame.K_LEFT:
                    if not self.last_moves:
                        print("No moves to undo.")
                        continue
                    last_move_str = self.last_moves.pop(-1)
                    self.movements.insert(0, last_move_str)
                    move_str = self.reverse_moves[last_move_str]
                    
                    if len(move_str) > 1 and move_str[1] == '\'':
                        move = move_str[0]
                        reverse = True
                    else:
                        move = move_str
                        
                if move:
                    full_move_str = move
                    if reverse:
                        full_move_str += '\''
                    
                    sys.stdout.write(f"{full_move_str} - {self.moves_info[full_move_str]}\n")
                    
                    if move =='F':
                        angle = -theta if not reverse else theta
                        for x in range(theta_inc):
                            for piece in center_pieces[0:1] + edge_pieces[0] + edge_pieces[1] + corner_pieces:
                                if all(v[2] > 0 for v in piece):
                                    for i in range(8): piece[i] = z_rot(piece[i], angle)
                            update()

                    if move =='L':
                        angle = theta if not reverse else -theta
                        for x in range(theta_inc):
                            for piece in center_pieces[1:2] + edge_pieces[1] + edge_pieces[2] + corner_pieces:
                                if all(v[0] < 0 for v in piece):
                                    for i in range(8): piece[i] = x_rot(piece[i], angle)
                            update()

                    if move =='B':
                        angle = theta if not reverse else -theta
                        for x in range(theta_inc):
                            for piece in center_pieces[2:3] + edge_pieces[0] + edge_pieces[1] + corner_pieces:
                                if all(v[2] < 0 for v in piece):
                                    for i in range(8): piece[i] = z_rot(piece[i], angle)
                            update()
                    
                    if move =='R':
                        angle = -theta if not reverse else theta
                        for x in range(theta_inc):
                            for piece in center_pieces[3:4] + edge_pieces[1] + edge_pieces[2] + corner_pieces:
                                if all(v[0] > 0 for v in piece):
                                    for i in range(8): piece[i] = x_rot(piece[i], angle)
                            update()

                    if move =='U':
                        angle = -theta if not reverse else theta
                        for x in range(theta_inc):
                            for piece in center_pieces[4:5] + edge_pieces[0] + edge_pieces[2] + corner_pieces:
                                if all(v[1] > 0 for v in piece):
                                    for i in range(8): piece[i] = y_rot(piece[i], angle)
                            update()

                    if move =='D':
                        angle = theta if not reverse else -theta
                        for x in range(theta_inc):
                            for piece in center_pieces[5:6] + edge_pieces[0] + edge_pieces[2] + corner_pieces:
                                if all(v[1] < 0 for v in piece):
                                    for i in range(8): piece[i] = y_rot(piece[i], angle)
                            update()

                if event.key == pygame.K_SPACE:
                    inc_x, inc_y, zoom = 0, 0, 1
                    accum = (1, 0, 0, 0)
    
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4 and zoom < 1.6: zoom += 0.05
                if event.button == 5 and zoom > 0.3: zoom -= 0.05
            
            if pygame.mouse.get_pressed()[0] == 1:
                (tmp_x, tmp_y) = pygame.mouse.get_rel()
                inc_x, inc_y = -tmp_y * pi / 450, -tmp_x * pi / 450
            else:
                inc_x, inc_y = 0, 0

            sys.stdout.flush()

    def draw_cube(self):
        glLineWidth(GLfloat(6.0))
        glBegin(GL_LINES)
        glColor3fv((0.0, 0.0, 0.0))
        for piece in center_pieces + corner_pieces:
            for edge in cube_edges:
                for vertex in edge: glVertex3fv(piece[vertex])
        for axis in edge_pieces:
            for piece in axis:
                for edge in cube_edges:
                    for vertex in edge: glVertex3fv(piece[vertex])
        glEnd()
        self.draw_stickers()

    def draw_stickers(self):
        glBegin(GL_QUADS)
        # Draw center piece stickers
        for i, (color, surface) in enumerate(zip(cube_colors, cube_surfaces)):
            glColor3fv(color)
            for vertex in surface:
                glVertex3fv(center_pieces[i][vertex])

        # Draw edge piece stickers
        for color, surface, face in zip(cube_colors, cube_surfaces, edges):
            glColor3fv(color)
            for piece in face:
                for vertex in surface:
                    glVertex3fv(edge_pieces[piece[0]][piece[1]][vertex])

        # Draw black inner sides of edge pieces
        edge_black_pat = [[0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5]]
        glColor3fv((0, 0, 0))
        for i in range(len(edge_black_pat)):
            for face in edge_black_pat[i]:
                for piece in edge_pieces[i]:
                    for vertex in cube_surfaces[face]:
                        glVertex3fv(piece[vertex])

        # Define sticker color patterns for corners
        corner_color_pat = [
            [0, 1, 5], [0, 1, 4], [0, 3, 4], [0, 3, 5],
            [2, 1, 5], [2, 1, 4], [2, 3, 4], [2, 3, 5],
        ]
        # Draw corner piece stickers
        for i, color_faces in enumerate(corner_color_pat):
            for face_idx in color_faces:
                glColor3fv(cube_colors[face_idx])
                for vertex in cube_surfaces[face_idx]:
                    glVertex3fv(corner_pieces[i][vertex])

        glEnd()

    def draw_axis(self):
        glLineWidth(GLfloat(1.0))
        glBegin(GL_LINES)
        for color, axis in zip(axis_colors, axes):
            glColor3fv(color)
            for point in axis:
                glVertex3fv(axis_verts[point])
        glEnd()