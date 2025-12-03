"""
Based on pentonvillefandango/cp-astrowatcher working watcher
"""

import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Callable, List
from datetime import datetime

logger = logging.getLogger(__name__)

class CustomHandler(FileSystemEventHandler):
    """Handler based on your working cp-astrowatcher"""
    
    def __init__(self, callback: Callable[[Path], None], extensions: List[str] = None):
        super().__init__()
        self.callback = callback
        self.extensions = extensions or ['.fits', '.fit', '.fts', '.fz']
        logger.info(f"CustomHandler initialized for extensions: {self.extensions}")
    
    def on_created(self, event):
        """Called when a file or directory is created"""
        if not event.is_directory:
            self.process_event(event.src_path, "created")
    
    def on_moved(self, event):
        """Called when a file or directory is moved/renamed"""
        if not event.is_directory:
            self.process_event(event.dest_path, "moved")
    
    def process_event(self, path: str, event_type: str):
        """Process file system event"""
        filepath = Path(path)
        
        # Check if it's a FITS file
        if filepath.suffix.lower() in self.extensions:
            logger.info(f"{event_type.upper()}: {filepath.name}")
            
            # Wait to ensure file is fully written (especially on network drives)
            time.sleep(1)
            
            # Check if file exists and has size
            if filepath.exists():
                try:
                    file_size = filepath.stat().st_size
                    if file_size > 0:
                        logger.info(f"  Size: {file_size:,} bytes")
                        self.callback(filepath)
                    else:
                        logger.warning(f"  File is empty: {filepath}")
                except Exception as e:
                    logger.error(f"  Error checking file: {e}")
            else:
                logger.warning(f"  File no longer exists: {filepath}")

class ReliableFolderWatcher:
    """Reliable watcher based on your working implementation"""
    
    def __init__(self, watch_paths: List[str], 
                 on_new_file: Callable[[Path], None],
                 recursive: bool = True):
        self.watch_paths = [Path(p) for p in watch_paths]
        self.on_new_file = on_new_file
        self.recursive = recursive
        self.observer = Observer()
        self.running = False
        
        # Validate paths
        for path in self.watch_paths:
            if not path.exists():
                logger.warning(f"Watch path does not exist: {path}")
                # Don't create on read-only mount
    
    def start(self):
        """Start watching"""
        if self.running:
            return
        
        logger.info(f"Starting reliable watcher on {len(self.watch_paths)} paths")
        logger.info(f"Recursive: {self.recursive}")
        
        for watch_path in self.watch_paths:
            if watch_path.exists():
                try:
                    # Use your working handler pattern
                    handler = CustomHandler(self.on_new_file)
                    self.observer.schedule(handler, str(watch_path), recursive=self.recursive)
                    logger.info(f"✅ Watching: {watch_path}")
                    
                    # List initial files for debugging
                    fits_count = len(list(watch_path.rglob("*.fit*")))
                    logger.info(f"  Found {fits_count} existing FITS files")
                    
                except Exception as e:
                    logger.error(f"Failed to watch {watch_path}: {e}")
            else:
                logger.error(f"❌ Cannot watch, path doesn't exist: {watch_path}")
        
        try:
            self.observer.start()
            self.running = True
            logger.info("🎯 Watcher started successfully")
        except Exception as e:
            logger.error(f"Failed to start observer: {e}")
    
    def stop(self):
        """Stop watching"""
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
            logger.info("Watcher stopped")
    
    def run(self):
        """Run watcher (blocking)"""
        self.start()
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()

# Test based on your working pattern
def test():
    print("Testing Reliable Watcher (based on cp-astrowatcher)")
    print("=" * 60)
    
    # Use your exact path
    watch_path = "/Volumes/Rig24_Imaging"
    
    def callback(filepath: Path):
        print(f"\n" + "=" * 50)
        print(f"✅ CALLBACK: {filepath.name}")
        print(f"   Path: {filepath}")
        print(f"   Size: {filepath.stat().st_size:,} bytes")
        print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 50)
    
    watcher = ReliableFolderWatcher([watch_path], callback, recursive=True)
    
    print(f"\nWatching: {watch_path}")
    print("Recursive: True")
    print("\nStart your imaging PC script now...")
    print("Press Ctrl+C to stop\n")
    
    watcher.run()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test()
