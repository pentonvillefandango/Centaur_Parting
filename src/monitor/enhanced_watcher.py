#!/usr/bin/env python3
"""
Enhanced Centaur Parting FITS Watcher
- By default ignores existing files (only watches for NEW files)
- Can process existing files with --process-existing flag
- Generates comprehensive summary report when finished
"""

import time
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import numpy as np
import hashlib

# Custom JSON encoder
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super(NumpyEncoder, self).default(obj)

# Import enhanced analyzer
sys.path.append(os.path.join(os.path.dirname(__file__), 'enhanced'))
from fits_analyzer import EnhancedFITSAnalyzer

class EnhancedPollingWatcher:
    def __init__(self, watch_path="/Volumes/Rig24_Imaging", poll_interval=10, output_dir=None):
        self.watch_path = Path(watch_path)
        self.poll_interval = poll_interval
        
        # Use local directory for analysis output
        if output_dir:
            self.analysis_dir = Path(output_dir)
        else:
            # Default: create in project directory
            project_root = Path(__file__).parent.parent.parent
            self.analysis_dir = project_root / "Centaur_Analysis"
        
        self.analysis_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Track processed files - NEW: empty by default
        self.processed_files = set()
        self.file_hashes = {}
        
        # Store analysis results for final summary
        self.all_analyses = []
        
        logging.info(f"🔭 Enhanced Centaur Parting Watcher")
        logging.info(f"📁 Watching: {self.watch_path}")
        logging.info(f"💾 Analysis: {self.analysis_dir}")
        logging.info(f"⏱️ Poll interval: {self.poll_interval}s")
        
        # Check if watch path exists
        if not self.watch_path.exists():
            logging.error(f"❌ Watch path does not exist: {self.watch_path}")
            logging.error("Please mount Rig24_Imaging or specify a different path")
    
    def setup_logging(self):
        """Setup logging to file and console"""
        log_file = self.analysis_dir / "centaur_watcher.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def get_file_hash(self, file_path):
        """Get hash of file to detect changes"""
        try:
            # Quick hash using size and modification time
            stat = file_path.stat()
            return f"{stat.st_size}_{stat.st_mtime}"
        except:
            return None
    
    def find_fits_files(self, recursive=True):
        """Find all FITS files in watch path"""
        fits_files = []
        
        if not self.watch_path.exists():
            return fits_files
        
        # Look for FITS files
        for ext in ['.fits', '.fit', '.FITS', '.FIT']:
            pattern = f"**/*{ext}" if recursive else f"*{ext}"
            try:
                for file_path in self.watch_path.glob(pattern):
                    if file_path.is_file():
                        fits_files.append(file_path)
            except Exception as e:
                logging.error(f"Error scanning for {ext} files: {e}")
        
        return sorted(fits_files)
    
    def find_new_fits_files(self):
        """Find only NEW FITS files (not previously processed)"""
        new_files = []
        
        if not self.watch_path.exists():
            return new_files
        
        # Look for FITS files
        for ext in ['.fits', '.fit', '.FITS', '.FIT']:
            pattern = f"**/*{ext}"
            try:
                for file_path in self.watch_path.glob(pattern):
                    if file_path.is_file():
                        file_hash = self.get_file_hash(file_path)
                        file_str = str(file_path)
                        
                        # Check if file is new (not in processed files)
                        if file_str not in self.processed_files:
                            new_files.append(file_path)
                            self.processed_files.add(file_str)
                            self.file_hashes[file_str] = file_hash
            except Exception as e:
                logging.error(f"Error scanning for {ext} files: {e}")
        
        return new_files
    
    def analyze_fits_file(self, file_path):
        """Analyze a FITS file and generate report"""
        try:
            file_str = str(file_path)
            filename = os.path.basename(file_str)
            logging.info(f"📊 Analyzing: {filename}")
            
            # Analyze the file
            analyzer = EnhancedFITSAnalyzer(file_str)
            report = analyzer.generate_report()
            
            # Add file path to report
            report['file_info']['full_path'] = file_str
            
            # Create filename-safe version
            safe_name = filename.replace(' ', '_').replace(':', '-')
            report_filename = f"{Path(safe_name).stem}_centaur_analysis.json"
            report_path = self.analysis_dir / report_filename
            
            # Save detailed report
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, cls=NumpyEncoder)
            
            logging.info(f"💾 Report saved: {report_path.name}")
            
            # Store for final summary
            self.all_analyses.append(report)
            
            # Also create a simple summary file
            self.create_individual_summary(file_path, report)
            
            return report
            
        except Exception as e:
            logging.error(f"❌ Error analyzing {filename}: {str(e)}")
            import traceback
            logging.debug(traceback.format_exc())
            return None
    
    def create_individual_summary(self, file_path, report):
        """Create individual text summary"""
        safe_name = os.path.basename(str(file_path)).replace(' ', '_').replace(':', '-')
        summary_file = self.analysis_dir / f"{Path(safe_name).stem}_summary.txt"
        
        with open(summary_file, 'w') as f:
            f.write(f"{'='*60}\n")
            f.write(f"Centaur Parting - FITS Analysis Summary\n")
            f.write(f"{'='*60}\n\n")
            
            info = report['file_info']
            f.write(f"FILE: {info['filename']}\n")
            f.write(f"OBJECT: {info['object']}\n")
            f.write(f"FILTER: {info['filter']}\n")
            f.write(f"DIMENSIONS: {info['dimensions']}\n")
            f.write(f"EXPOSURE: {info['exposure_from_header']}s\n\n")
            
            analysis = report['analysis']
            
            # Saturation
            sat = analysis['saturation_analysis']
            f.write(f"SATURATION ANALYSIS:\n")
            f.write(f"  Max value: {sat['max_value']:.0f} ADU\n")
            f.write(f"  Saturation level: {sat['saturation_level']:.0f} ADU\n")
            f.write(f"  Near-saturated pixels: {sat['near_saturated_pixels']} ({sat['near_saturated_percent']:.4f}%)\n")
            f.write(f"  Severity: {sat['severity']}\n")
            f.write(f"  Hot pixels: {sat['likely_hot_pixels']}\n\n")
            
            # Exposure
            f.write(f"EXPOSURE OPTIMIZATION:\n")
            f.write(f"  Current: {analysis['current_exposure']}s\n")
            f.write(f"  Recommended: {analysis['recommended_exposure']:.0f}s\n")
            f.write(f"  Factor: {analysis['exposure_factor']:.2f}x\n")
            f.write(f"  Optimal sub length: {analysis['optimal_sub_length']:.0f}s\n\n")
            
            # SNR
            snr = analysis['snr_metrics']
            f.write(f"SIGNAL-TO-NOISE:\n")
            f.write(f"  Background SNR: {snr['snr_background']:.1f}\n")
            f.write(f"  Faint object SNR: {snr['snr_faint_object']:.1f}\n")
            f.write(f"  Moderate object SNR: {snr['snr_moderate_object']:.1f}\n\n")
            
            # Sky
            sky = analysis['sky_brightness']
            if sky['mag_per_arcsec2'] is not None:
                f.write(f"SKY BRIGHTNESS:\n")
                f.write(f"  {sky['mag_per_arcsec2']:.1f} mag/arcsec²\n")
                f.write(f"  {sky['electrons_per_pixel']:.0f} e-/pixel\n")
                f.write(f"  {sky['electrons_per_second_per_pixel']:.2f} e-/s/pixel\n\n")
            
            # SHO
            sho = analysis['sho_recommendation']
            if sho['adjustment_factor'] < 1.0:
                f.write(f"SHO RECOMMENDATION:\n")
                f.write(f"  SII/OIII adjustment: {sho['adjustment_factor']:.2f}x\n")
                f.write(f"  Recommended exposure: {sho['recommended_exposure']:.0f}s\n\n")
            
            # Recommendations
            f.write(f"RECOMMENDATIONS:\n")
            for i, rec in enumerate(report['recommendations'], 1):
                f.write(f"  {i}. {rec}\n")
            
            f.write(f"\n{'='*60}\n")
            f.write(f"Generated: {report['timestamp']}\n")
            f.write(f"Analyzer: {report['analyzer_version']}\n")
            f.write(f"{'='*60}\n")
    
    def create_comprehensive_summary(self):
        """Create comprehensive summary report of all analyses"""
        if not self.all_analyses:
            logging.warning("No analyses to summarize")
            return
        
        summary_file = self.analysis_dir / "COMPREHENSIVE_SUMMARY.md"
        
        with open(summary_file, 'w') as f:
            f.write("# Centaur Parting - Comprehensive FITS Analysis Summary\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n")
            f.write(f"**Total Files Analyzed:** {len(self.all_analyses)}\n")
            f.write(f"**Watcher Version:** 1.0\n\n")
            
            # Summary statistics
            f.write("## 📊 Summary Statistics\n\n")
            
            # Group by filter
            filters = {}
            exposures = []
            sky_mags = []
            recommendations = []
            
            for report in self.all_analyses:
                filter_name = report['file_info']['filter']
                if filter_name not in filters:
                    filters[filter_name] = []
                filters[filter_name].append(report)
                
                analysis = report['analysis']
                exposures.append(analysis['current_exposure'])
                
                sky_mag = analysis['sky_brightness'].get('mag_per_arcsec2')
                if sky_mag is not None:
                    sky_mags.append(sky_mag)
                
                recommendations.extend(report['recommendations'])
            
            # Filter breakdown
            f.write("### Filter Breakdown\n")
            f.write("| Filter | Files | Avg Exposure | Recommended SHO |\n")
            f.write("|--------|-------|--------------|-----------------|\n")
            
            for filter_name, reports in filters.items():
                avg_exposure = np.mean([r['analysis']['current_exposure'] for r in reports])
                sho_rec = np.mean([r['analysis']['sho_recommendation']['recommended_exposure'] for r in reports])
                
                f.write(f"| {filter_name} | {len(reports)} | {avg_exposure:.0f}s | {sho_rec:.0f}s |\n")
            
            f.write("\n")
            
            # Exposure statistics
            if exposures:
                f.write(f"**Exposure Statistics:**\n")
                f.write(f"- Average: {np.mean(exposures):.0f}s\n")
                f.write(f"- Range: {min(exposures):.0f}s to {max(exposures):.0f}s\n")
                f.write(f"- Median: {np.median(exposures):.0f}s\n\n")
            
            # Sky brightness statistics
            if sky_mags:
                f.write(f"**Sky Brightness Statistics:**\n")
                f.write(f"- Average: {np.mean(sky_mags):.1f} mag/arcsec²\n")
                f.write(f"- Range: {min(sky_mags):.1f} to {max(sky_mags):.1f} mag/arcsec²\n\n")
            
            # Common recommendations
            f.write("## 💡 Common Recommendations\n\n")
            from collections import Counter
            rec_counter = Counter(recommendations)
            
            f.write("| Recommendation | Frequency |\n")
            f.write("|----------------|-----------|\n")
            for rec, count in rec_counter.most_common(10):
                f.write(f"| {rec} | {count} |\n")
            
            f.write("\n")
            
            # File-by-file summary
            f.write("## 📁 File-by-File Analysis\n\n")
            f.write("| File | Object | Filter | Exposure | Sky Brightness | Key Recommendation |\n")
            f.write("|------|--------|--------|----------|----------------|-------------------|\n")
            
            for report in self.all_analyses[:50]:  # First 50 files
                info = report['file_info']
                analysis = report['analysis']
                
                filename = info['filename'][:30] + "..." if len(info['filename']) > 30 else info['filename']
                object_name = info['object'][:15] if info['object'] != 'Unknown' else 'N/A'
                filter_name = info['filter']
                exposure = analysis['current_exposure']
                
                sky_mag = analysis['sky_brightness'].get('mag_per_arcsec2')
                sky_display = f"{sky_mag:.1f}" if sky_mag else "N/A"
                
                # Get first recommendation
                key_rec = report['recommendations'][0][:50] + "..." if report['recommendations'] else "N/A"
                
                f.write(f"| {filename} | {object_name} | {filter_name} | {exposure:.0f}s | {sky_display} | {key_rec} |\n")
            
            if len(self.all_analyses) > 50:
                f.write(f"\n*... and {len(self.all_analyses) - 50} more files*\n")
            
            # Detailed analysis table
            f.write("\n## 🔍 Detailed Analysis\n\n")
            f.write("| File | SNR (Bkg) | SNR (Faint) | Saturation | Optimal Sub |\n")
            f.write("|------|-----------|-------------|------------|-------------|\n")
            
            for report in self.all_analyses[:20]:  # First 20 detailed
                info = report['file_info']
                analysis = report['analysis']
                
                filename = info['filename'][:20] + "..." if len(info['filename']) > 20 else info['filename']
                snr_bkg = analysis['snr_metrics']['snr_background']
                snr_faint = analysis['snr_metrics']['snr_faint_object']
                
                sat = analysis['saturation_analysis']
                saturation_display = f"{sat['near_saturated_percent']:.3f}%"
                if sat['severity'] != "NONE":
                    saturation_display += " ⚠️"
                
                optimal_sub = analysis['optimal_sub_length']
                
                f.write(f"| {filename} | {snr_bkg:.1f} | {snr_faint:.1f} | {saturation_display} | {optimal_sub:.0f}s |\n")
        
        logging.info(f"📋 Comprehensive summary saved: {summary_file}")
        return summary_file
    
    def process_existing_files(self, max_files=None, ignore_existing=False):
        """Process existing FITS files"""
        if ignore_existing:
            logging.info("Ignoring existing files as requested")
            return 0
        
        logging.info("Looking for existing FITS files...")
        existing_files = self.find_fits_files()
        
        if not existing_files:
            logging.info("No FITS files found to process")
            return 0
        
        # Filter out already processed files
        files_to_process = []
        for file_path in existing_files:
            file_str = str(file_path)
            if file_str not in self.processed_files:
                files_to_process.append(file_path)
        
        if max_files:
            files_to_process = files_to_process[:max_files]
        
        if files_to_process:
            logging.info(f"Found {len(files_to_process)} files to process ({len(existing_files)} total, {len(existing_files)-len(files_to_process)} already processed)")
            
            success_count = 0
            for i, file_path in enumerate(files_to_process):
                logging.info(f"[{i+1}/{len(files_to_process)}] Processing {os.path.basename(str(file_path))}...")
                result = self.analyze_fits_file(file_path)
                if result:
                    success_count += 1
            
            logging.info(f"✅ Processed {success_count}/{len(files_to_process)} files successfully")
            return success_count
        else:
            logging.info("All existing files have already been processed")
            return 0
    
    def run_continuous(self, ignore_existing=True):
        """Run continuous monitoring - IGNORES existing files by default"""
        logging.info("Starting continuous monitoring...")
        
        if ignore_existing:
            logging.info("⚠️  Ignoring existing files - only watching for NEW files")
            # Mark all existing files as processed
            existing_files = self.find_fits_files()
            for file_path in existing_files:
                self.processed_files.add(str(file_path))
            logging.info(f"Marked {len(existing_files)} existing files as already processed")
        else:
            logging.info("Processing existing files first...")
            self.process_existing_files(ignore_existing=False)
        
        logging.info("👁️  Now watching for NEW FITS files...")
        logging.info("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Check for new files
                new_files = self.find_new_fits_files()
                
                if new_files:
                    logging.info(f"🔍 Found {len(new_files)} NEW FITS file(s)")
                    for file_path in new_files:
                        self.analyze_fits_file(file_path)
                    
                    # Create/update summary after new files
                    self.create_comprehensive_summary()
                else:
                    # Only log occasionally when no files found
                    if int(time.time()) % 300 == 0:  # Every 5 minutes
                        logging.info("No new files found...")
                
                # Wait for next poll
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logging.info("\n👋 Watcher stopped by user")
            # Create final summary
            if self.all_analyses:
                self.create_comprehensive_summary()
        except Exception as e:
            logging.error(f"💥 Watcher error: {str(e)}")
            # Create summary before exiting
            if self.all_analyses:
                self.create_comprehensive_summary()
            raise

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Enhanced Centaur Parting FITS Watcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process existing files and create summary
  python enhanced_watcher.py --process-existing --max-files 10
  
  # Watch for NEW files only (ignore existing)
  python enhanced_watcher.py --continuous
  
  # Watch for NEW files and process existing first
  python enhanced_watcher.py --continuous --process-existing-first
  
  # Specify custom output directory
  python enhanced_watcher.py --process-existing --output ./my_analysis
        """
    )
    
    parser.add_argument('--path', default='/Volumes/Rig24_Imaging',
                       help='Path to watch for FITS files (default: /Volumes/Rig24_Imaging)')
    parser.add_argument('--output', default=None,
                       help='Output directory for analysis results')
    parser.add_argument('--interval', type=int, default=10,
                       help='Polling interval in seconds (default: 10)')
    
    # Processing modes
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--process-existing', action='store_true',
                      help='Process existing FITS files and exit')
    group.add_argument('--continuous', action='store_true',
                      help='Run continuous monitoring (ignores existing files by default)')
    
    # Options
    parser.add_argument('--max-files', type=int, default=None,
                       help='Maximum number of files to process (for testing)')
    parser.add_argument('--process-existing-first', action='store_true',
                       help='When using --continuous, process existing files first')
    
    args = parser.parse_args()
    
    # Create watcher
    watcher = EnhancedPollingWatcher(
        watch_path=args.path,
        poll_interval=args.interval,
        output_dir=args.output
    )
    
    # Run based on arguments
    if args.process_existing:
        # Process existing files and exit
        count = watcher.process_existing_files(max_files=args.max_files, ignore_existing=False)
        if count > 0:
            watcher.create_comprehensive_summary()
        print(f"\n✅ Processing complete. Check {watcher.analysis_dir} for results.")
        
    elif args.continuous:
        # Run continuous monitoring
        watcher.run_continuous(ignore_existing=not args.process_existing_first)
        
    else:
        # Default: show help
        print(f"\nEnhanced Centaur Parting FITS Analyzer")
        print(f"{'='*60}")
        print(f"Analysis output: {watcher.analysis_dir}")
        print(f"\nUse one of these commands:")
        print(f"  --process-existing       : Process existing files and exit")
        print(f"  --continuous            : Watch for NEW files only")
        print(f"  --continuous --process-existing-first : Process existing, then watch")
        print(f"\nAdd --max-files N to limit processing for testing")
        print(f"Add --output DIR to specify output directory")

if __name__ == "__main__":
    main()
