#!/usr/bin/env python3
"""Run the SciENcv Biosketch Creator application."""

import os
import sys

# Ensure we're in the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ.setdefault('FLASK_APP', 'app')
os.environ.setdefault('FLASK_ENV', 'development')

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("SciENcv Biosketch Creator")
    print("=" * 60)
    print("\nStarting development server...")
    print("Open http://localhost:5000 in your browser\n")

    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )
