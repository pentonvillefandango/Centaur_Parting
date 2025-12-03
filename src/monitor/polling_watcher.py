"""
Polling-based folder watcher for SMB/network drives
Checks directory every few seconds for new files
"""

import time
import logging
from pathlib import Path
from typing import Callable, List, Set
from datetime import datetime

logger = logging.getLogger(__name__)

class PollingFolderWatcher:
    """
    Polling-based watcher that checks for new files at regular intervals
    Works on any filesystem (SMB, NFS, local, etc.)
    """
    
    def __init__(self, watch_paths: List[str], 
                 on_new_file: Callable[[Path], None],
                 poll_interval: int = 2,
                 file_extensions: List[str] = None):
        """
        Args:
            watch_paths: List of paths to watch
            on_new_file: Callback when new file is found
            poll_interval: How often to check (seconds)
            file_extensions: File extensions to watch
        """
        self.watch_paths = [Path(p) for p in watch_paths]
        self.on_new_file = on_new_file
        self.poll_interval = poll_interval
        self.extensions = file_extensions or ['.fits', '.fit', '.fts', '.fz']
        self.running = False
        
        # Track known files to detect new ones
        self.known_files: Set[Path] = set()
        
        # Validate paths
        for path in self.watch_paths:
            if not path.exists():
                logger.warning(f"Watch path does not exist: {path}")
    
    def _scan_for_files(self, path: Path) -> Set[Path]:
        """Recursively scan for FITS files"""
        files = set()
        
        try:
            # Recursive glob for all FITS extensions
            for ext in self.extensions:
                for filepath in path.rglob(f"*{ext}"):
                    if filepath.is_file():
                        files.add(filepath.resolve())
        except Exception as e:
            logger.error(f"Error scanning {path}: {e}")
        
        return files
    
    def _check_for_new_files(self):
        """Check all watch paths for new files"""
        for watch_path in self.watch_paths:
            if not watch_path.exists():
                continue
            
            # Get current files
            current_files = self._scan_for_files(watch_path)
            
            # Find new files (in current but not in known)
            new_files = current_files - self.known_files
            
            # Process new files
            for filepath in new_files:
                try:
                    # Wait a bit to ensure file is complete
                    time.sleep(0.5)
                    
                    # Check file size
                    file_size = filepath.stat().st_size
                    
                    if file_size > 100:  # Minimum reasonable size for FITS
                        logger.info(f"New file found via polling: {filepath.name}")
                        logger.info(f"  Size: {file_size:,} bytes")
                        self.on_new_file(filepath)
                    else:
                        logger.warning(f"File too small, may be incomplete: {filepath}")
                        
                except Exception as e:
                    logger.error(f"Error processing {filepath}: {e}")
            
            # Update known files
            self.known_files.update(new_files)
            
            # Log stats occasionally
            if len(new_files) > 0:
                logger.info(f"Found {len(new_files)} new files in {watch_path}")
    
    def start(self):
        """Start polling"""
        if self.running:
            return
        
        logger.info(f"Starting polling watcher on {len(self.watch_paths)} paths")
        logger.info(f"Poll interval: {self.poll_interval} seconds")
        logger.info(f"Watching extensions: {self.extensions}")
        
        # Initial scan to establish baseline
        for watch_path in self.watch_paths:
            if watch_path.exists():
                initial_files = self._scan_for_files(watch_path)
                self.known_files.update(initial_files)
                logger.info(f"  {watch_path}: {len(initial_files)} existing files")
            else:
                logger.error(f"Path doesn't exist: {watch_path}")
        
        self.running = True
        logger.info("Polling watcher started")
    
    def stop(self):
        """Stop polling"""
        self.running = False
        logger.info("Polling watcher stopped")
    
    def run(self):
        """Run polling loop (blocking)"""
        self.start()
        
        try:
            poll_count = 0
            while self.running:
                # Check every N polls to reduce logging noise
                if poll_count % 10 == 0:
                    logger.debug(f"Poll #{poll_count + 1}...")
                
                self._check_for_new_files()
                time.sleep(self.poll_interval)
                poll_count += 1
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()

# Simple test
def test_polling_watcher():
    """Test the polling watcher"""
    print("Polling Folder Watcher Test")
    print("=" * 60)
    
    # Use your actual path
    watch_path = "/Volumes/Rig24_Imaging"
    
    def callback(filepath: Path):
        print(f"\n" + "=" * 50)
        print(f"🎯 NEW FILE DETECTED (via polling)")
        print(f"📄 File: {filepath.name}")
        print(f"📁 Full path: {filepath}")
        print(f"📏 Size: {filepath.stat().st_size:,} bytes")
        print(f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 50)
    
    print(f"\nWatching: {watch_path}")
    print(f"Polling every 2 seconds")
    print(f"Will scan ALL subdirectories recursively")
    print("\nStart your imaging PC script now...")
    print("Files should appear within 2-4 seconds")
    print("Press Ctrl+C to stop\n")
    
    watcher = PollingFolderWatcher(
        watch_paths=[watch_path],
        on_new_file=callback,
        poll_interval=2,
        file_extensions=['.fits', '.fit', '.fts', '.fz']
    )
    
    watcher.run()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test_polling_watcher()
