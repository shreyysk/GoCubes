import os
import uuid
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, generate_csrf
from PIL import Image
from flask import Flask, render_template, request, jsonify, session
from functools import lru_cache
import hashlib   

# --- Local Imports ---
# Import the configuration and database objects
from config import config
from database import db, CubeState

# Import the new, robust solver and its cube model
from cube_model import CubeModel
from kociemba_solver import KociembaSolver
# The 'moves' file is now a standalone utility for generating scrambles
from moves import generate_random_scramble as generate_scramble 
from utils.image_processor import process_cube_image

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO)

@lru_cache(maxsize=128)
def cached_solve(kociemba_string):
    """Cache solved states to avoid recomputation"""
    solver = KociembaSolver()
    solution = solver.solve(kociemba_string)
    return solution  # Return the solution, not the solver.solve result directly

def create_app(config_name='default'):
    """
    Application factory to create and configure the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    CORS(app)
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    
    # Configure CSRF settings
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit
    app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']
    app.config['WTF_CSRF_FIELD_NAME'] = 'csrf_token'
    app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']

    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )

    # Exempt API endpoints from CSRF if needed for external access
    csrf.exempt('/api/scramble')
    # Make the python 'zip' function available in the Jinja2 templates
    app.jinja_env.globals.update(zip=zip)
    # Make CSRF token available in templates
    app.jinja_env.globals['csrf_token'] = generate_csrf

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
            session.modified = True

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
    @limiter.limit("10 per minute")
    def solve_from_state():
        """Solves a cube from a given JSON state using the Kociemba solver."""
        try:
            data = request.json
            if not data or 'state' not in data:
                return jsonify({'error': 'Invalid request: Cube state missing.'}), 400

            # Validate and process cube state
            try:
                cube = CubeModel()
                cube.from_web_format(data['state'])

                # Additional validation
                is_valid, error_msg = cube.validate()
                if not is_valid:
                    return jsonify({'error': f'Invalid cube state: {error_msg}'}), 400

                kociemba_string = cube.to_string()
            except (ValueError, KeyError) as e:
                app.logger.warning(f"Invalid cube state: {e}")
                return jsonify({'error': str(e)}), 400

            # Try Kociemba solver first, then fallback
            solution_str = None
            solver_used = "kociemba"
            
            try:
                # Try cached solution first
                state_hash = hashlib.md5(kociemba_string.encode()).hexdigest()
                solution_str = cached_solve(kociemba_string)
            except Exception as e:
                app.logger.warning(f"Kociemba solver failed: {e}")
                # Fallback to basic solver
                try:
                    from basic_solver import BasicSolver
                    basic = BasicSolver()
                    solution_str = basic.solve(cube)
                    solver_used = "basic"
                except:
                    return jsonify({
                        'error': 'No solver available. Please install kociemba: pip install kociemba',
                        'fallback': True
                    }), 500
            
            if solution_str:
                solution_list = solution_str.split()
            else:
                solution_list = []

            # Log the solved state to the database
            try:
                state_log = CubeState(session_id=session.get('session_id', 'anonymous'))
                state_log.set_state_dict(data['state'])
                state_log.solution = solution_str
                state_log.state_hash = state_hash if 'state_hash' in locals() else None
                db.session.add(state_log)
                db.session.commit()
            except Exception as db_error:
                db.session.rollback()
                app.logger.error(f"Database error: {db_error}")

            return jsonify({
                'success': True,
                'solution': solution_list,
                'move_count': len(solution_list),
                'solver': solver_used
            })
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
                        images[face] = Image.open(file.stream).convert('RGB')

            if len(images) != 6:
                return jsonify({'error': 'Please provide valid images for all 6 faces.'}), 400

            # Process images to detect colors and validate the state
            cube_state_web_format = process_cube_image(images)

            # --- Solve the detected state using the new solver ---
            cube = CubeModel()
            cube.from_web_format(cube_state_web_format)
            kociemba_string = cube.to_string()

            solver = KociembaSolver()
            solution_str = solver.solve(kociemba_string)
            solution_list = solution_str.split()

            return jsonify({
                'success': True,
                'state': cube_state_web_format, # Return the detected state for user correction
                'solution': solution_list,
                'move_count': len(solution_list)
            })
        except ValueError as e:
            # This will catch errors from process_cube_image or from_web_format
            app.logger.warning(f"Image processing or cube state validation error: {e}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            app.logger.error(f"Error in /api/solve/image: {e}", exc_info=True)
            return jsonify({'error': 'An internal error occurred while processing images.'}), 500

    # --- Helper Function ---
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', 
                               error_code=404,
                               error_title='Page Not Found',
                               error_message='The page you are looking for does not exist.'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('error.html',
                               error_code=500,
                               error_title='Internal Server Error',
                               error_message='Something went wrong. Please try again later.'), 500
    
    @app.errorhandler(413)
    def too_large_error(error):
        return render_template('error.html',
                               error_code=413,
                               error_title='File Too Large',
                               error_message='The uploaded file is too large. Maximum size is 16MB.'), 413

    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    app.run(host='0.0.0.0', port=5000, debug=False)