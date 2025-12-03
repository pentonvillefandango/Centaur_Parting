#!/usr/bin/env python3
"""
Enhanced polling watcher with FITS analysis for exposure optimization
Based on existing polling_watcher.py with added SNR and sky brightness analysis
"""

import time
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add enhanced analyzer to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'enhanced'))
from fits_analyzer import EnhancedFITSAnalyzer

class EnhancedPollingWatcher:
    def __init__(self, watch_path="/Volumes/Rig24_Imaging", poll_interval=5):
        """
        Enhanced watcher that analyzes FITS files for exposure optimization
        
        Args:
            watch_path: Path to watch for new FITS files
            poll_interval: How often to check for new files (seconds)
        """
        self.watch_path = Path(watch_path)
        self.poll_interval = poll_interval
        self.analysis_output = self.watch_path / "analysis_results"
        self.analysis_output.mkdir(exist_ok=True)
        
        # Track processed files
        self.processed_files = set()
        
        # Setup logging
        self.setup_logging()
        
        logging.info(f"Enhanced polling watcher initialized on {watch_path}")
        logging.info(f"Analysis results will be saved to {self.analysis_output}")
    
    def setup_logging(self):
        """Configure logging"""
        log_file = self.analysis_output / "enhanced_watcher.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def scan_for_new_files(self):
        """Scan watch directory for new FITS files"""
        new_files = []
        
        # Look for FITS files
        for ext in ['.fits', '.fit', '.FITS', '.FIT']:
            for file_path in self.watch_path.glob(f"**/*{ext}"):
                if file_path.is_file() and str(file_path) not in self.processed_files:
                    new_files.append(file_path)
        
        return new_files
    
    def analyze_fits_file(self, file_path):
        """Analyze a FITS file and generate optimization report"""
        try:
            logging.info(f"Analyzing: {file_path.name}")
            
            # Initialize analyzer
            analyzer = EnhancedFITSAnalyzer(str(file_path))
            
            # Generate report
            report = analyzer.generate_report()
            
            # Save report as JSON
            report_filename = f"{file_path.stem}_analysis.json"
            report_path = self.analysis_output / report_filename
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logging.info(f"Analysis saved to {report_path}")
            
            # Log key recommendations
            self.log_recommendations(file_path.name, report)
            
            # Mark as processed
            self.processed_files.add(str(file_path))
            
            return report
            
        except Exception as e:
            logging.error(f"Error analyzing {file_path}: {str(e)}")
            return None
    
    def log_recommendations(self, filename, report):
        """Log key recommendations from analysis"""
        analysis = report.get('analysis', {})
        recs = report.get('recommendations', [])
        
        logging.info(f"=== RECOMMENDATIONS for {filename} ===")
        logging.info(f"SNR: {analysis.get('snr', 0):.1f}")
        logging.info(f"Sky: {analysis.get('sky_brightness', {}).get('mag_per_arcsec2', 'N/A'):.1f} mag/arcsec²")
        logging.info(f"Current exposure: {analysis.get('current_exposure', 0)}s")
        logging.info(f"Recommended exposure: {analysis.get('recommended_exposure', 0):.0f}s")
        
        for i, rec in enumerate(recs, 1):
            logging.info(f"{i}. {rec}")
        
        logging.info("=" * 50)
    
    def process_existing_files(self):
        """Process any existing FITS files on startup"""
        logging.info("Processing existing FITS files...")
        existing_files = self.scan_for_new_files()
        
        if existing_files:
            logging.info(f"Found {len(existing_files)} existing FITS files")
            for file_path in existing_files:
                self.analyze_fits_file(file_path)
        else:
            logging.info("No existing FITS files found")
    
    def run(self):
        """Main watcher loop"""
        logging.info("Starting enhanced polling watcher...")
        logging.info(f"Watching: {self.watch_path}")
        logging.info(f"Poll interval: {self.poll_interval}s")
        logging.info("Press Ctrl+C to stop")
        
        # Process any existing files first
        self.process_existing_files()
        
        try:
            while True:
                # Scan for new files
                new_files = self.scan_for_new_files()
                
                if new_files:
                    logging.info(f"Found {len(new_files)} new FITS file(s)")
                    for file_path in new_files:
                        self.analyze_fits_file(file_path)
                
                # Wait before next poll
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logging.info("Watcher stopped by user")
        except Exception as e:
            logging.error(f"Watcher error: {str(e)}")
            raise

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced FITS polling watcher with exposure optimization')
    parser.add_argument('--path', default='/Volumes/Rig24_Imaging',
                       help='Path to watch for FITS files')
    parser.add_argument('--interval', type=int, default=5,
                       help='Polling interval in seconds')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: analyze existing files and exit')
    
    args = parser.parse_args()
    
    watcher = EnhancedPollingWatcher(args.path, args.interval)
    
    if args.test:
        # Test mode: analyze existing files and exit
        watcher.process_existing_files()
        print("\nTest complete. Check the analysis_results directory for reports.")
    else:
        # Run continuous watcher
        watcher.run()

if __name__ == '__main__':
    main()
