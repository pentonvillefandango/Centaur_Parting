#!/usr/bin/env python3
"""
Launch Centaur Parting GUI
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

if __name__ == "__main__":
    from web.app import app
    
    print("=" * 60)
    print("Centaur Parting - Astrophotography Analysis GUI")
    print("=" * 60)
    print()
    print("Starting web dashboard...")
    print("Open your browser to: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print()
    
    # Run with waitress for production, or Flask dev server for development
    if '--production' in sys.argv:
        from waitress import serve
        serve(app, host='0.0.0.0', port=5000)
    else:
        app.run(debug=True, host='0.0.0.0', port=5000)
