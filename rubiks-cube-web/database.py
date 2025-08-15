from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class CubeState(db.Model):
    """Model for storing cube states submitted to the solver."""
    __tablename__ = 'cube_states'
    
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.Text, nullable=False)  # JSON representation of cube state
    solution = db.Column(db.Text)              # The solution moves
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100))
    
    def get_state_dict(self):
        """Gets the cube state as a Python dictionary."""
        return json.loads(self.state) if self.state else None
    
    def set_state_dict(self, state_dict):
        """Sets the cube state from a Python dictionary."""
        self.state = json.dumps(state_dict)