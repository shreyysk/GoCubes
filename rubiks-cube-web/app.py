import os
import uuid
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from PIL import Image

# --- Local Imports ---
# Import the configuration and database objects
from config import config
from database import db, CubeState

# Import the strong logic for the solver and image processor
from solver.cube import Cube
from solver.solver import CubeSolver
from solver.moves import generate_scramble
from utils.image_processor import process_cube_image

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO)

def create_app(config_name='default'):
    """
    Application factory to create and configure the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Make the python 'zip' function available in the Jinja2 templates
    app.jinja_env.globals.update(zip=zip)

    # Create upload folder if it doesn't exist
    with app.app_context():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        db.create_all()

    # --- Session Management ---
    @app.before_request
    def manage_session():
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            session.permanent = True

    # --- Frontend Routes ---
    @app.route('/')
    def index():
        """Serves the home page."""
        return render_template('index.html')

    @app.route('/solver')
    def solver_page():
        """Serves the main solver page."""
        # These variables are required by solver.html to render the upload boxes
        scan_order = ['up', 'right', 'front', 'down', 'left', 'back']
        scan_face_names = [
            'Up (White)', 'Right (Blue)', 'Front (Red)',
            'Down (Yellow)', 'Left (Green)', 'Back (Orange)'
        ]
        return render_template(
            'solver.html',
            scanOrder=scan_order,
            scanFaceNames=scan_face_names
        )

    # --- API Endpoints ---
    @app.route('/api/scramble', methods=['GET'])
    def get_scramble():
        """Generates and returns a random scramble."""
        scramble = generate_scramble()
        return jsonify({'scramble': scramble})

    @app.route('/api/solve', methods=['POST'])
    def solve_from_state():
        """Solves a cube from a given JSON state."""
        try:
            data = request.json
            if not data or 'state' not in data:
                return jsonify({'error': 'Invalid request: Cube state missing.'}), 400
            
            cube = Cube()
            cube.set_state(data['state'])
            solver = CubeSolver(cube)
            solution = solver.solve()

            # Log the solved state to the database
            state_log = CubeState(session_id=session.get('session_id'))
            state_log.set_state_dict(data['state'])
            state_log.solution = ' '.join(solution)
            db.session.add(state_log)
            db.session.commit()

            return jsonify({
                'success': True,
                'solution': solution,
                'move_count': len(solution)
            })
        except (ValueError, KeyError) as e:
            app.logger.warning(f"Bad request to /api/solve: {e}")
            return jsonify({'error': f"Invalid cube state provided. {e}"}), 400
        except Exception as e:
            app.logger.error(f"Error in /api/solve: {e}", exc_info=True)
            return jsonify({'error': 'An internal server error occurred.'}), 500

    @app.route('/api/solve/image', methods=['POST'])
    def solve_from_images():
        """Processes 6 cube face images and returns a solution."""
        try:
            images = {}
            faces = ['up', 'down', 'front', 'back', 'left', 'right']
            
            for face in faces:
                if face in request.files:
                    file = request.files[face]
                    if file and allowed_file(file.filename):
                        images[face] = Image.open(file.stream)

            if len(images) != 6:
                return jsonify({'error': 'Please provide valid images for all 6 faces.'}), 400

            # Process images (includes validation and solvability check)
            cube_state = process_cube_image(images)

            # Solve the detected state
            cube = Cube()
            cube.set_state(cube_state)
            solver = CubeSolver(cube)
            solution = solver.solve()

            return jsonify({
                'success': True,
                'state': cube_state, # Return the detected state for user correction
                'solution': solution,
                'move_count': len(solution)
            })
        except ValueError as e:
            app.logger.warning(f"Image processing error: {e}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            app.logger.error(f"Error in /api/solve/image: {e}", exc_info=True)
            return jsonify({'error': 'An internal error occurred while processing images.'}), 500

    # --- Helper Function ---
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    return app

if __name__ == '__main__':
    app = create_app('default')
    # Set debug=True to see detailed errors during development
    app.run(host='0.0.0.0', port=5000, debug=True)