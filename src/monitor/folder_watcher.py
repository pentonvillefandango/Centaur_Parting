import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Callable, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class FitsFileHandler(FileSystemEventHandler):
    def __init__(self, on_new_file: Callable[[Path], None], 
                 file_extensions: List[str] = None):
        self.on_new_file = on_new_file
        self.file_extensions = file_extensions or ['.fits', '.fit', '.fts', '.fz']
    
    def on_created(self, event):
        if not event.is_directory:
            filepath = Path(event.src_path)
            if self._is_fits_file(filepath):
                logger.info(f"New file detected: {filepath.name}")
                time.sleep(0.5)
                self.on_new_file(filepath)
    
    def on_moved(self, event):
        if not event.is_directory:
            filepath = Path(event.dest_path)
            if self._is_fits_file(filepath):
                logger.info(f"File moved to: {filepath.name}")
                time.sleep(0.5)
                self.on_new_file(filepath)
    
    def _is_fits_file(self, filepath: Path) -> bool:
        return filepath.suffix.lower() in self.file_extensions

class FolderWatcher:
    def __init__(self, watch_paths: List[str], 
                 on_new_file: Callable[[Path], None],
                 recursive: bool = True):
        self.watch_paths = [Path(p) for p in watch_paths]
        self.on_new_file = on_new_file
        self.recursive = recursive
        self.observer = Observer()
        self.running = False
        
        for path in self.watch_paths:
            if not path.exists():
                logger.warning(f"Watch path does not exist: {path}")
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path}")
    
    def start(self):
        if self.running:
            logger.warning("Watcher already running")
            return
        
        logger.info(f"Starting folder watcher on {len(self.watch_paths)} paths")
        logger.info(f"Recursive watching: {self.recursive}")
        
        for watch_path in self.watch_paths:
            if watch_path.exists():
                event_handler = FitsFileHandler(self.on_new_file)
                self.observer.schedule(event_handler, str(watch_path), recursive=self.recursive)
                logger.info(f"Watching: {watch_path}")
                if self.recursive:
                    logger.info(f"  (including all subdirectories)")
            else:
                logger.error(f"Cannot watch, path doesn't exist: {watch_path}")
        
        self.observer.start()
        self.running = True
        logger.info("Folder watcher started successfully")
    
    def stop(self):
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
            logger.info("Folder watcher stopped")
    
    def run_forever(self, check_interval: int = 1):
        self.start()
        try:
            while self.running:
                time.sleep(check_interval)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()

def test_watcher():
    import sys
    
    print("Folder Watcher Test")
    print("=" * 50)
    
    test_paths = []
    
    current_dir = Path.cwd()
    test_dir = current_dir / "test_watch"
    test_dir.mkdir(exist_ok=True)
    test_paths.append(str(test_dir))
    
    print(f"Test directory: {test_dir}")
    print("\nThe watcher will monitor for new .fits files.")
    print("To test:")
    print(f"1. Copy a FITS file to: {test_dir}")
    print("2. Or create a dummy file: touch test.fits")
    print("3. Press Ctrl+C to stop\n")
    
    def test_callback(filepath: Path):
        print(f"New file detected: {filepath}")
        print(f"   Size: {filepath.stat().st_size} bytes")
        print(f"   Modified: {datetime.fromtimestamp(filepath.stat().st_mtime)}")
    
    watcher = FolderWatcher(test_paths, test_callback, recursive=True)
    
    try:
        watcher.run_forever()
    except KeyboardInterrupt:
        print("\nTest stopped by user")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test_watcher()
