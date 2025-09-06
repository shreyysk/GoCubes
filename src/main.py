#!/usr/bin/env python3
import sys
import cv2
import time
import argparse
import collections
import numpy as np
from predict import predicted_color
from draw import draw_2d_cube_state
import helpers
from rubik_solver import utils
from PyCube import PyCube
import calibrate
import copy

# Import the hybrid editor
try:
    from hybrid_editor import launch_hybrid_editor
    HYBRID_EDITOR_AVAILABLE = True
except ImportError:
    HYBRID_EDITOR_AVAILABLE = False
    print("Warning: hybrid_editor not found, manual fixing disabled")

# =============================================================================
# ## ENHANCED RUBIK SCANNER WITH HYBRID EDITOR
# =============================================================================

# Valid edges on a standard cube
VALID_EDGES = {
    frozenset({'white', 'green'}), frozenset({'white', 'red'}),
    frozenset({'white', 'blue'}), frozenset({'white', 'orange'}),
    frozenset({'yellow', 'green'}), frozenset({'yellow', 'red'}),
    frozenset({'yellow', 'blue'}), frozenset({'yellow', 'orange'}),
    frozenset({'green', 'red'}), frozenset({'green', 'orange'}),
    frozenset({'blue', 'red'}), frozenset({'blue', 'orange'})
}

# Valid corners
VALID_CORNERS = {
    frozenset({'white', 'red', 'green'}), frozenset({'white', 'red', 'blue'}),
    frozenset({'white', 'orange', 'blue'}), frozenset({'white', 'orange', 'green'}),
    frozenset({'yellow', 'green', 'orange'}), frozenset({'yellow', 'green', 'red'}),
    frozenset({'yellow', 'red', 'blue'}), frozenset({'yellow', 'orange', 'blue'})
}


def enhanced_color_prediction(frame, contour, colors_obj, debug=False):
    """Enhanced color detection with multiple methods"""
    x, y, w, h = contour
    
    # Method 1: Center sampling
    center_x, center_y = x + w//2, y + h//2
    
    # Method 2: Multiple point sampling
    margin = max(3, min(w, h) // 5)
    sample_points = [
        (center_x, center_y),
        (x + margin, y + margin),
        (x + w - margin, y + margin),
        (x + margin, y + h - margin),
        (x + w - margin, y + h - margin),
    ]
    
    all_predictions = []
    all_distances = {}
    
    for px, py in sample_points:
        if 0 <= px < frame.shape[1] and 0 <= py < frame.shape[0]:
            color_bgr = frame[py, px].tolist()
            
            # Calculate distances to all colors
            converted = helpers.bgr2lab(color_bgr)
            distances = {}
            
            for color_name, ref_bgr in colors_obj.prominent_color_palette.items():
                dist = helpers.ciede2000(converted, helpers.bgr2lab(ref_bgr))
                distances[color_name] = dist
                
                if color_name not in all_distances:
                    all_distances[color_name] = []
                all_distances[color_name].append(dist)
            
            # Get best match for this point
            best = min(distances.items(), key=lambda x: x[1])
            all_predictions.append(best[0])
    
    if not all_predictions:
        # Fallback to center only
        color_bgr = frame[center_y, center_x].tolist()
        return predicted_color(color_bgr, colors_obj), 0.5
    
    # Calculate final prediction using voting + average distance
    vote_counts = collections.Counter(all_predictions)
    
    # Calculate average distance for each color
    avg_distances = {}
    for color, dists in all_distances.items():
        avg_distances[color] = sum(dists) / len(dists) if dists else float('inf')
    
    # Combine voting and distance
    best_color = None
    best_score = float('inf')
    
    for color in vote_counts:
        vote_penalty = (len(all_predictions) - vote_counts[color]) * 10
        total_score = avg_distances[color] + vote_penalty
        
        if total_score < best_score:
            best_score = total_score
            best_color = color
    
    # Calculate confidence
    confidence = vote_counts[best_color] / len(all_predictions)
    if avg_distances[best_color] < 20:  # Very close match
        confidence = min(1.0, confidence + 0.2)
    elif avg_distances[best_color] > 40:  # Poor match
        confidence *= 0.7
    
    if debug:
        print(f"  Detection: {best_color} (conf={confidence:.2f}, dist={avg_distances[best_color]:.1f})")
        # FIX: Add flush to ensure debug output is displayed immediately
        sys.stdout.flush()
    
    return best_color, confidence


def get_edge_list_from_faces(faces):
    """Extract edges with proper error handling"""
    try:
        u = faces['white'].face
        d = faces['yellow'].face
        f = faces['green'].face
        b = faces['blue'].face
        r = faces['red'].face
        l = faces['orange'].face
        
        # Check for None values
        for name, face in [('white', u), ('yellow', d), ('green', f), 
                          ('blue', b), ('red', r), ('orange', l)]:
            if face is None or any(None in row for row in face):
                print(f"Warning: {name} face contains None values")
                return []
        
        edges = [
            frozenset([str(u[2][1]), str(f[0][1])]) if u[2][1] and f[0][1] else frozenset(),
            frozenset([str(u[1][2]), str(r[0][1])]) if u[1][2] and r[0][1] else frozenset(),
            frozenset([str(u[0][1]), str(b[0][1])]) if u[0][1] and b[0][1] else frozenset(),
            frozenset([str(u[1][0]), str(l[0][1])]) if u[1][0] and l[0][1] else frozenset(),
            frozenset([str(d[0][1]), str(f[2][1])]) if d[0][1] and f[2][1] else frozenset(),
            frozenset([str(d[1][2]), str(r[2][1])]) if d[1][2] and r[2][1] else frozenset(),
            frozenset([str(d[2][1]), str(b[2][1])]) if d[2][1] and b[2][1] else frozenset(),
            frozenset([str(d[1][0]), str(l[2][1])]) if d[1][0] and l[2][1] else frozenset(),
            frozenset([str(f[1][2]), str(r[1][0])]) if f[1][2] and r[1][0] else frozenset(),
            frozenset([str(f[1][0]), str(l[1][2])]) if f[1][0] and l[1][2] else frozenset(),
            frozenset([str(b[1][2]), str(r[1][2])]) if b[1][2] and r[1][2] else frozenset(),
            frozenset([str(b[1][0]), str(l[1][0])]) if b[1][0] and l[1][0] else frozenset(),
        ]
        
        # Filter out empty sets and sets with only one element
        valid_edges = [e for e in edges if len(e) == 2]
        return valid_edges
        
    except Exception as e:
        print(f"Error extracting edges: {e}")
        return []


def validate_cube_quick(faces):
    """Quick validation check for main scanning loop"""
    # Check color counts
    color_counts = collections.Counter()
    for face_name, face in faces.items():
        if face.scanned:
            for row in face.face:
                for color in row:
                    if color:
                        color_counts[color] += 1
    
    # Each color should appear exactly 9 times
    for color in ['white', 'yellow', 'red', 'orange', 'green', 'blue']:
        if color_counts.get(color, 0) != 9:
            return False
    
    # Check edges
    edges = get_edge_list_from_faces(faces)
    if len(edges) != 12:
        return False
        
    edge_counts = collections.Counter(edges)
    if len(edge_counts) < 12:
        return False

    if set(edges) != VALID_EDGES:
        return False
        
    return True


def diagnose_cube_detailed(faces):
    """Detailed diagnostic with specific error locations"""
    print("\n" + "="*50)
    print("          CUBE DIAGNOSTIC SUMMARY")
    print("="*50)
    
    # Check centers
    centers_ok = True
    for name in faces:
        center = faces[name].face[1][1]
        if center != name:
            print(f"  ❌ Wrong center on {name} face (is {center})")
            centers_ok = False
    
    if centers_ok:
        print("  ✅ All centers correct")
    
    # Color counts
    color_counts = collections.Counter()
    for face_name, face in faces.items():
        for row in face.face:
            for color in row:
                if color:
                    color_counts[color] += 1
    
    color_issues = []
    for color in ['white', 'yellow', 'red', 'orange', 'green', 'blue']:
        count = color_counts.get(color, 0)
        if count != 9:
            color_issues.append(f"{color}: {count}/9")
    
    if color_issues:
        print(f"  ❌ Color imbalances: {', '.join(color_issues)}")
    else:
        print("  ✅ All colors have exactly 9 stickers")
    
    # Edge analysis
    edges = get_edge_list_from_faces(faces)
    valid_edges = sum(1 for e in edges if e in VALID_EDGES and len(e) == 2)
    invalid_edges = [e for e in edges if e not in VALID_EDGES]
    
    print(f"  📊 Edges: {valid_edges}/12 valid")
    if invalid_edges and len(invalid_edges) <= 3:
        for edge in invalid_edges[:3]:
            if len(edge) == 2:
                colors = list(edge)
                print(f"     Invalid edge: {colors[0]}-{colors[1]}")
    
    print("="*50)
    
    return valid_edges == 12 and not color_issues


class Face:
    def __init__(self, name, class_colors):
        self.class_colors = class_colors
        self.face = [[None, None, None],
                     [None, None, None],
                     [None, None, None]]
        self.raw_face = []
        self.name = name
        self.scanned = False
        self.confidence_scores = []

        self.instructions = {
            'white': "WHITE center, GREEN on bottom edge",
            'yellow': "YELLOW center, GREEN on top edge",
            'green': "GREEN center, WHITE on top edge",
            'blue': "BLUE center, WHITE on bottom edge",
            'red': "RED center, WHITE on top edge",
            'orange': "ORANGE center, WHITE on top edge"
        }

        self.colors = {"White": (255, 255, 255), "Yellow": (0, 255, 255),
                       "Orange": (0, 165, 255), "Red": (0, 0, 255),
                       "Green": (0, 255, 0), "Blue": (255, 0, 0)}

    def find_contours(self, dilatedFrame):
        contours, hierarchy = cv2.findContours(dilatedFrame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        final_contours = []
        
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.1 * perimeter, True)
            if len(approx) == 4:
                area = cv2.contourArea(contour)
                (x, y, w, h) = cv2.boundingRect(approx)
                ratio = w / float(h)
                
                if (0.5 <= ratio <= 1.5 and 
                    w >= 20 and h >= 20 and 
                    area >= 300):
                    final_contours.append((x, y, w, h))
        
        if len(final_contours) < 9:
            return final_contours
        
        # Find 3x3 grid
        found = False
        best_group = []
        
        for i, base in enumerate(final_contours):
            bx, by, bw, bh = base
            bcx, bcy = bx + bw/2, by + bh/2
            
            group = [base]
            avg_size = (bw + bh) / 2
            
            # Find 8 neighbors
            for other in final_contours:
                if other == base:
                    continue
                ox, oy, ow, oh = other
                ocx, ocy = ox + ow/2, oy + oh/2
                
                # Check if within 3x3 grid distance
                dx = abs(ocx - bcx)
                dy = abs(ocy - bcy)
                
                if dx < avg_size * 2.5 and dy < avg_size * 2.5:
                    group.append(other)
            
            if len(group) == 9:
                best_group = group
                found = True
                break
        
        if not found:
            return []
        
        # Sort contours into 3x3 grid
        final_contours = best_group
        
        # Sort all contours from top-to-bottom based on their y-coordinate
        final_contours.sort(key=lambda c: c[1])
        
        # Slice the sorted list into three distinct rows
        top_row = final_contours[0:3]
        middle_row = final_contours[3:6]
        bottom_row = final_contours[6:9]
        
        # Sort each row from left-to-right based on their x-coordinate
        top_row.sort(key=lambda c: c[0])
        middle_row.sort(key=lambda c: c[0])
        bottom_row.sort(key=lambda c: c[0])
        
        # Combine the sorted rows into the final, correctly ordered list
        return top_row + middle_row + bottom_row

    def draw_contours(self, frame, contours):
        for index, (x, y, w, h) in enumerate(contours):
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
            
            # Draw grid position
            row = index // 3
            col = index % 3
            cv2.putText(frame, f"{row},{col}", (x + 5, y + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        return frame

    def scan(self, cap, wanted_color, faces):
        stable_detections = 0
        required_stable = 4
        last_state = None
        min_confidence = 0.7
        
        print(f"  Scanning for {wanted_color} center...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Preprocessing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (7, 7), 0)
            edges = cv2.Canny(blur, 30, 90)
            kernel = np.ones((5, 5), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=2)
            
            contours = self.find_contours(dilated)
            frame = self.draw_contours(frame, contours)
            
            # Instructions
            cv2.putText(frame, self.instructions[wanted_color], (10, 470),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                       self.colors[wanted_color.capitalize()], 2)
            
            if len(contours) == 9:
                colors_list = []
                confidences = []
                
                for contour in contours:
                    color, conf = enhanced_color_prediction(frame, contour, self.class_colors)
                    colors_list.append(color)
                    confidences.append(conf)
                
                center = colors_list[4]
                avg_conf = sum(confidences) / len(confidences)
                
                if center == wanted_color and avg_conf >= min_confidence:
                    state = ''.join(colors_list)
                    if state == last_state:
                        stable_detections += 1
                    else:
                        stable_detections = 0
                        last_state = state
                    
                    status = f"✓ Detected! Stability: {stable_detections}/{required_stable}"
                    cv2.putText(frame, status, (200, 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    if stable_detections >= required_stable:
                        # Save face
                        self.face = []
                        for i in range(3):
                            row = []
                            for j in range(3):
                                row.append(colors_list[i * 3 + j])
                            self.face.append(row)
                        
                        self.raw_face = [list(row) for row in self.face]
                        self.confidence_scores = confidences
                        self.scanned = True
                        
                        print(f"    ✅ Captured (confidence: {avg_conf:.2f})")
                        return False
                else:
                    stable_detections = 0
                    if center != wanted_color:
                        msg = f"Wrong center: {center}"
                        cv2.putText(frame, msg, (200, 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    else:
                        msg = f"Low confidence: {avg_conf:.2f}"
                        cv2.putText(frame, msg, (200, 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            else:
                cv2.putText(frame, f"Found {len(contours)}/9", (200, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            image = draw_2d_cube_state(frame, faces)
            cv2.imshow('Rubik Scanner', image)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):
                sys.exit()
            elif key == 8 or key == 127:  # Backspace
                return True


def all_scanned(faces):
    return all(face.scanned for face in faces.values())


def launch_cube(solution):
    cube = PyCube()
    moves = []
    for m in solution:
        m = str(m)
        if len(m) > 1 and m[1] == '2':
            moves.extend([m[0], m[0]])
        else:
            moves.append(m)
    cube.run(moves)


def main_execution_loop(args, colors):
    """Contains the main logic for one full scan-to-solve cycle."""
    # Initialize faces for a fresh scan
    faces = {
        'white': Face('white', colors), 'yellow': Face('yellow', colors),
        'green': Face('green', colors), 'blue': Face('blue', colors),
        'red': Face('red', colors), 'orange': Face('orange', colors),
    }
    
    scan_order = ["white", "yellow", "green", "blue", "red", "orange"]
    idx = 0
    
    cap = cv2.VideoCapture(0)
    
    try:
        if not cap.isOpened():
            print("❌ Cannot open camera")
            return 'fail'
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("\n📷 Camera ready!")
        print("Tips: Good lighting, hold steady, wait for green checkmark\n")
        
        while not all_scanned(faces):
            current = scan_order[idx]
            print(f"\n📋 Face {idx + 1}/6: {current.upper()}")
            
            if faces[current].scan(cap, current, faces):
                if idx > 0:
                    idx -= 1
                    # Reset the face we are going back to
                    faces[scan_order[idx]] = Face(scan_order[idx], colors)
            else:
                idx += 1
    finally:
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
    
    print("\n✅ All faces scanned!")
    
    # Validation and Solving
    solution = None
    valid = validate_cube_quick(faces)
    
    if not valid:
        diagnose_cube_detailed(faces)
        
        if HYBRID_EDITOR_AVAILABLE:
            print("\n🔧 Launching hybrid editor to fix issues...")
            all_confidence = {name: f.confidence_scores for name, f in faces.items() if f.scanned}
            solution = launch_hybrid_editor(faces, all_confidence)
            
            if not solution:
                print("\n❌ Editing cancelled or no solution was found.")
                return 'fail' # Indicate failure to the main loop
        else:
            print("\n⚠️ Cube configuration invalid. Run with hybrid_editor.py for manual correction.")
            return 'fail'
    
    # If the cube was initially valid or was fixed by the editor, attempt to solve
    if valid or solution:
        if solution: # If solution came from editor, use it
            print(f"\n✅ Solution from editor: {solution}")
            print(f"   Steps: {len(solution.split())}")
            print("\n🎮 Launching visualization...")
            launch_cube(solution)
            return 'success'

        # Build cube string for solver if scanned cube was valid
        color_map = {"white": "w", "yellow": "y", "green": "g",
                     "blue": "b", "red": "r", "orange": "o"}
        solver_order = ['white', 'red', 'green', 'yellow', 'orange', 'blue']
        
        try:
            cube_parts = [color_map[color] for name in solver_order for row in faces[name].face for color in row]
            cube_string = "".join(cube_parts)
            
            print("\n🧩 Solving...")
            solution = utils.solve(cube_string, 'Kociemba')
            print(f"✅ Solution: {solution}")
            print(f"   Steps: {len(solution.split())}")
            
            print("\n🎮 Launching visualization...")
            launch_cube(solution)
            return 'success'
        except Exception as e:
            print(f"\n❌ Solver Error: {e}")
            if HYBRID_EDITOR_AVAILABLE:
                print("\n🔧 Solver failed. Launching editor for manual correction...")
                solution = launch_hybrid_editor(faces)
                if solution:
                    print(f"\n✅ Solution from editor: {solution}")
                    launch_cube(solution)
                    return 'success'
            return 'fail'
    return 'fail'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--calibrate", action='store_true')
    parser.add_argument("-d", "--debug", action='store_true')
    parser.add_argument("-m", "--manual", action='store_true', 
                       help="Skip scanning and go directly to manual editor")
    args = parser.parse_args()
    
    print("🎲 Rubik's Cube Scanner v3.0 with Hybrid Editor")
    print("="*50)
    
    colors = helpers.Colors()
    
    if args.calibrate:
        print("🎨 Starting color calibration...")
        calibrate.run(colors)
    
    if args.manual and HYBRID_EDITOR_AVAILABLE:
        print("\n📝 Launching manual editor...")
        solution = launch_hybrid_editor(None)
        if solution:
            print(f"\n✅ Solution: {solution}")
            print("\n🎮 Launching visualization...")
            launch_cube(solution)
        sys.exit(0)
    
    # Main restart loop
    while True:
        result = main_execution_loop(args, colors)
        
        if result == 'success':
            prompt_text = "\nScan another cube? (y/n): "
        else:
            prompt_text = "\nWould you like to restart the scanning process? (y/n): "
            
        restart = input(prompt_text).lower()
        if restart != 'y':
            print("Exiting program.")
            break