#!/usr/bin/env python3
"""Test if the server is configured correctly"""

import sys
import os

# Test imports
try:
    from app import create_app
    from database import db
    print("✓ App imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test app creation
try:
    app = create_app('development')
    print("✓ App created successfully")
except Exception as e:
    print(f"✗ App creation error: {e}")
    sys.exit(1)

# Test database
try:
    with app.app_context():
        db.create_all()
        print("✓ Database initialized")
except Exception as e:
    print(f"✗ Database error: {e}")
    sys.exit(1)

print("\n✅ All tests passed! You can run the server with:")
print("   python app.py")