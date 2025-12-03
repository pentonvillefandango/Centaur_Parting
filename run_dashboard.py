#!/usr/bin/env python3
"""
Entry point for Centaur Parting Dashboard
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from dashboard.main import SimpleDashboard
    dashboard_class = SimpleDashboard
except ImportError:
    try:
        from dashboard.main import AstroDashboard
        dashboard_class = AstroDashboard
    except ImportError:
        from dashboard.main import SimpleDashboard
        dashboard_class = SimpleDashboard

if __name__ == "__main__":
    print("Starting Centaur Parting...")
    dashboard = dashboard_class()
    dashboard.run()
