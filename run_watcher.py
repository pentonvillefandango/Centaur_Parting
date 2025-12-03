#!/usr/bin/env python3
import sys
sys.path.append('.')
from enhanced_core.watcher_integration import start_watcher

if __name__ == "__main__":
    watch_path = "/Volumes/Rig24_Imaging"
    print(f"Starting enhanced FITS watcher on {watch_path}")
    print("Press Ctrl+C to stop")
    start_watcher(watch_path)
