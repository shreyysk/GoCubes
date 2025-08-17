from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class CubeState(db.Model):
    """Model for storing cube states submitted to the solver."""
    __tablename__ = 'cube_states'
    
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.Text, nullable=False)  # JSON representation of cube state
    solution = db.Column(db.Text)               # The solution moves
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # Add index
    session_id = db.Column(db.String(100), index=True)  # Add index
    state_hash = db.Column(db.String(64), index=True, unique=False)  # Add hash for faster lookups
    
    def get_state_dict(self):
        """Gets the cube state as a Python dictionary."""
        try:
            return json.loads(self.state) if self.state else None
        except json.JSONDecodeError:
            return None
    
    def set_state_dict(self, state_dict):
        """Sets the cube state from a Python dictionary."""
        # Validate state_dict structure
        if not isinstance(state_dict, dict):
            raise ValueError("State must be a dictionary")
        
        # Validate expected keys
        expected_faces = {'up', 'down', 'front', 'back', 'left', 'right'}
        if not all(face in state_dict for face in expected_faces):
            raise ValueError("Invalid cube state structure")
            
        # Validate each face has 9 stickers
        for face, stickers in state_dict.items():
            if not isinstance(stickers, list) or len(stickers) != 9:
                raise ValueError(f"Face {face} must have exactly 9 stickers")
                
        self.state = json.dumps(state_dict)
