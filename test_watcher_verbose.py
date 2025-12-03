import sys
import os
from pathlib import Path
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from monitor.folder_watcher import FolderWatcher

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("VERBOSE WATCHER - Shows all events")
    print("=" * 60)
    
    WATCH_PATH = "/Volumes/Rig24_Imaging"
    
    def on_new_file(filepath: Path):
        print(f"\n" + "=" * 60)
        print(f"🎯 FILE DETECTED CALLBACK FIRED!")
        print(f"📄 File: {filepath.name}")
        print(f"📁 Path: {filepath}")
        print(f"📏 Size: {filepath.stat().st_size:,} bytes")
        print(f"🕐 Time: {time.ctime()}")
        print("=" * 60 + "\n")
    
    print(f"\nWatching: {WATCH_PATH}")
    print("Will show ALL file system events (even non-FITS files)")
    print("\nStart your imaging PC script now...")
    print("Press Ctrl+C to stop\n")
    
    watcher = FolderWatcher([WATCH_PATH], on_new_file, recursive=True)
    
    try:
        watcher.run_forever()
    except KeyboardInterrupt:
        print("\n\nStopped by user")

if __name__ == "__main__":
    main()
