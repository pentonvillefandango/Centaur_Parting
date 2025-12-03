import sys
import os
from pathlib import Path
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from monitor.folder_watcher import FolderWatcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("Centaur Parting - Rig24 Imaging Monitor")
    print("=" * 60)
    
    WATCH_PATH = "/Volumes/Rig24_Imaging"
    watch_path = Path(WATCH_PATH)
    
    print(f"\nTarget path: {WATCH_PATH}")
    
    if not watch_path.exists():
        print(f"ERROR: Path does not exist: {WATCH_PATH}")
        return
    
    print(f"Path exists!")
    
    try:
        sample_files = list(watch_path.glob("*"))
        print(f"Readable! Found {len(sample_files)} files/folders")
    except Exception as e:
        print(f"Cannot read directory: {e}")
        return
    
    fits_files = list(watch_path.rglob("*.fit*"))
    print(f"\nFound {len(fits_files)} existing FITS files (including subdirectories)")
    
    def on_new_file(filepath: Path):
        print(f"\nNEW FITS FILE DETECTED!")
        print(f"   File: {filepath.name}")
        print(f"   Path: {filepath.relative_to(watch_path)}")
        print(f"   Size: {filepath.stat().st_size:,} bytes")
        print(f"   Time: {time.ctime()}")
        
        if filepath.stat().st_size < 100:
            print("   Warning: File very small, might be incomplete")
        else:
            print("   File size looks reasonable")
    
    print(f"\n" + "=" * 60)
    print("Starting folder watcher...")
    print("Will monitor for new .fits, .fit, .fts, .fz files")
    print("RECURSIVE: Will watch all subdirectories")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")
    
    watcher = FolderWatcher([WATCH_PATH], on_new_file, recursive=True)
    
    try:
        watcher.run_forever()
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        logger.error(f"Watcher error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
