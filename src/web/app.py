"""
Centaur Parting Web Dashboard
Flask-based GUI for FITS analysis monitoring
"""

from flask import Flask, render_template, jsonify, request, send_file
import os
import sys
from pathlib import Path
import json
from datetime import datetime
import threading
import time
import hashlib

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import our existing analyzer
from monitor.enhanced.fits_analyzer import EnhancedFITSAnalyzer
from monitor.enhanced_polling_watcher import EnhancedPollingWatcher

app = Flask(__name__)
app.config['SECRET_KEY'] = 'centaur-parting-secret-key'
app.config['ANALYSIS_DIR'] = Path.cwd() / 'Centaur_Analysis'
app.config['WATCH_PATH'] = '/Volumes/Rig24_Imaging'

# Create analysis directory if it doesn't exist
app.config['ANALYSIS_DIR'].mkdir(exist_ok=True)

def extract_equipment_from_header(header):
    """Extract equipment information from FITS header"""
    equipment = {
        'telescope': str(header.get('TELESCOP', 'Unknown')).strip(),
        'camera': str(header.get('INSTRUME', 'Unknown')).strip(),
        'filter': str(header.get('FILTER', 'Unknown')).strip(),
        'focal_length': header.get('FOCALLEN'),
        'f_ratio': header.get('FOCRATIO'),
        'pixel_size': header.get('XPIXSZ'),
        'gain': header.get('GAIN'),
        'offset': header.get('OFFSET'),
        'temperature': header.get('CCD-TEMP'),
        'site_lat': header.get('SITELAT'),
        'site_long': header.get('SITELONG'),
    }
    
    # Create rig identifier
    camera_short = equipment['camera'].split()[0] if equipment['camera'] != 'Unknown' else 'Unknown'
    telescope_short = equipment['telescope'].split()[0] if equipment['telescope'] != 'Unknown' else 'Unknown'
    equipment['rig'] = f"{camera_short}/{telescope_short}"
    
    return equipment

DARK_LIBRARY = [0.2, 2, 5, 10, 15, 20, 30, 45, 60, 75, 90, 
                120, 150, 180, 240, 300, 360, 420]

def round_to_dark_library(exposure):
    """Round exposure to nearest available dark frame"""
    if exposure <= DARK_LIBRARY[0]:
        return DARK_LIBRARY[0]
    if exposure >= DARK_LIBRARY[-1]:
        return DARK_LIBRARY[-1]
    
    # Find closest available exposure
    closest = min(DARK_LIBRARY, key=lambda x: abs(x - exposure))
    
    # Round up to ensure sufficient signal
    for dark_exp in sorted(DARK_LIBRARY):
        if dark_exp >= exposure:
            return dark_exp
    
    return closest

class DashboardManager:
    """Manages the dashboard state and data"""
    def __init__(self):
        self.watcher = None
        self.watcher_thread = None
        self.watcher_running = False
        self.analyses = []  # Will only contain NEW files analyzed AFTER watcher started
        self.processed_files = set()  # Track all files that have been processed
        self.show_only_new_files = True  # Only show files processed after watcher start
        
        # When dashboard starts, mark all existing files as "already seen"
        self.initialize_processed_files()
    
    def initialize_processed_files(self):
        """Mark all existing FITS files as already processed (to ignore them initially)"""
        watch_path = Path(app.config['WATCH_PATH'])
        if watch_path.exists():
            print(f"Initializing processed files from: {watch_path}")
            file_count = 0
            for ext in ['.fits', '.fit', '.FITS', '.FIT']:
                for file_path in watch_path.rglob(f'*{ext}'):
                    if file_path.is_file():
                        # Create a unique identifier for the file
                        file_hash = self.get_file_hash(file_path)
                        self.processed_files.add(file_hash)
                        file_count += 1
            print(f"Marked {file_count} existing files as already processed")
        else:
            print(f"WARNING: Watch path does not exist: {watch_path}")
    
    def get_file_hash(self, file_path):
        """Create a hash for a file (size + mtime)"""
        try:
            stat = file_path.stat()
            return f"{file_path.name}_{stat.st_size}_{stat.st_mtime}"
        except:
            return f"{file_path.name}"
    
    def is_new_file(self, file_path):
        """Check if a file is new (not in processed_files)"""
        file_hash = self.get_file_hash(file_path)
        return file_hash not in self.processed_files
    
    def mark_file_processed(self, file_path):
        """Mark a file as processed"""
        file_hash = self.get_file_hash(file_path)
        self.processed_files.add(file_hash)
    
    def load_existing_analyses(self):
        """Load analysis files from analysis directory"""
        analysis_files = list(app.config['ANALYSIS_DIR'].glob('*_centaur_analysis.json'))
        self.analyses = []
        
        for file_path in analysis_files:
            try:
                with open(file_path, 'r') as f:
                    analysis = json.load(f)
                    analysis['file_path'] = str(file_path)
                    analysis['summary_file'] = str(file_path).replace('.json', '.txt')
                    
                    # Only add if it's a "new" file (processed after watcher start)
                    # We'll filter based on whether show_only_new_files is True
                    self.analyses.append(analysis)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        # Sort by timestamp (newest first)
        self.analyses.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def find_analysis_by_filename(self, filename):
        """Find analysis by filename"""
        for analysis in self.analyses:
            if analysis['file_info']['filename'] == filename:
                return analysis
        return None
    
    def start_watcher(self):
        """Start the file watcher in a background thread - only processes NEW files"""
        if not self.watcher_running:
            self.watcher_running = True
            self.show_only_new_files = True  # Enable new-files-only mode
            
            def watcher_target():
                poll_count = 0
                while self.watcher_running:
                    try:
                        poll_count += 1
                        print(f"\n{'='*60}")
                        print(f"Watcher Poll #{poll_count} - {datetime.now().strftime('%H:%M:%S')}")
                        print(f"Checking path: {app.config['WATCH_PATH']}")
                        print(f"Processed files cache size: {len(self.processed_files)}")
                        
                        # Find NEW FITS files (not previously processed)
                        watch_path = Path(app.config['WATCH_PATH'])
                        
                        if not watch_path.exists():
                            print(f"ERROR: Watch path does not exist: {watch_path}")
                            print("Make sure the volume is mounted")
                            time.sleep(30)
                            continue
                        
                        print(f"Watch path exists. Starting recursive search...")
                        
                        new_files_found = []
                        files_checked = 0
                        total_fits_files = 0
                        
                        # DEBUG: List directories in watch path
                        try:
                            dirs = list(watch_path.iterdir())
                            print(f"Found {len(dirs)} items in root directory")
                            for item in dirs[:5]:  # Show first 5 items
                                print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
                            if len(dirs) > 5:
                                print(f"  ... and {len(dirs) - 5} more items")
                        except Exception as e:
                            print(f"Error listing directory: {e}")
                        
                        # Search for FITS files with multiple patterns
                        file_patterns = ['*.fits', '*.fit', '*.FITS', '*.FIT']
                        
                        for pattern in file_patterns:
                            try:
                                for file_path in watch_path.rglob(pattern):
                                    files_checked += 1
                                    if file_path.is_file():
                                        total_fits_files += 1
                                        if self.is_new_file(file_path):
                                            print(f"  NEW: {file_path.relative_to(watch_path)}")
                                            new_files_found.append(file_path)
                            except Exception as e:
                                print(f"Error searching for pattern {pattern}: {e}")
                        
                        print(f"Search complete: Checked {files_checked} items, found {total_fits_files} FITS files, {len(new_files_found)} new files")
                        
                        # Process new files
                        if new_files_found:
                            print(f"\nProcessing {len(new_files_found)} new files...")
                            for file_path in new_files_found[:5]:  # Limit to 5 files per poll to avoid overload
                                try:
                                    print(f"  Analyzing: {file_path.name}")
                                    analyzer = EnhancedFITSAnalyzer(str(file_path))
                                    report = analyzer.generate_report()
                                    
                                    # Save the report
                                    safe_name = file_path.name.replace(' ', '_').replace(':', '-')
                                    report_filename = f"{Path(safe_name).stem}_centaur_analysis.json"
                                    report_path = app.config['ANALYSIS_DIR'] / report_filename
                                    
                                    with open(report_path, 'w') as f:
                                        json.dump(report, f, indent=2)
                                    
                                    # Also create summary file
                                    summary_file = report_path.with_suffix('.txt')
                                    self.create_summary_file(file_path, report, summary_file)
                                    
                                    # Mark as processed
                                    self.mark_file_processed(file_path)
                                    
                                    # Add to analyses list
                                    report['file_path'] = str(report_path)
                                    report['summary_file'] = str(summary_file)
                                    self.analyses.insert(0, report)  # Add at beginning
                                    
                                    print(f"    ✓ Success: {file_path.name}")
                                    
                                except Exception as e:
                                    print(f"    ✗ Error analyzing {file_path.name}: {e}")
                        
                        # Keep only recent analyses to avoid memory issues
                        if len(self.analyses) > 100:
                            self.analyses = self.analyses[:100]
                        
                        print(f"{'='*60}\n")
                        time.sleep(10)  # Poll every 10 seconds
                        
                    except Exception as e:
                        print(f"Watcher error: {e}")
                        import traceback
                        traceback.print_exc()
                        time.sleep(30)  # Wait longer on error
            
            self.watcher_thread = threading.Thread(target=watcher_target)
            self.watcher_thread.daemon = True
            self.watcher_thread.start()
            print("Watcher thread started with enhanced debugging")
            return True
        return False
    
    def create_summary_file(self, file_path, report, summary_path):
        """Create a summary text file for an analysis"""
        try:
            with open(summary_path, 'w') as f:
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
                
                # Recommendations
                f.write(f"RECOMMENDATIONS:\n")
                for i, rec in enumerate(report['recommendations'], 1):
                    f.write(f"  {i}. {rec}\n")
                
                f.write(f"\n{'='*60}\n")
                f.write(f"Generated: {report['timestamp']}\n")
                f.write(f"Analyzer: {report['analyzer_version']}\n")
                f.write(f"{'='*60}\n")
        except Exception as e:
            print(f"Error creating summary file: {e}")
    
    def stop_watcher(self):
        """Stop the file watcher"""
        print("Stopping watcher...")
        self.watcher_running = False
        if self.watcher_thread:
            self.watcher_thread.join(timeout=5)
        self.watcher_thread = None
        self.watcher = None
        print("Watcher stopped")
    
    def get_display_analyses(self):
        """Get analyses to display (respects show_only_new_files setting)"""
        if self.show_only_new_files:
            # Only return analyses from when watcher is running
            # Since we only add to self.analyses when watcher is processing new files,
            # all analyses in self.analyses are "new"
            return self.analyses
        else:
            # Return all analyses (including pre-existing ones)
            # This would require loading all analysis files
            all_analyses = []
            analysis_files = list(app.config['ANALYSIS_DIR'].glob('*_centaur_analysis.json'))
            for file_path in analysis_files:
                try:
                    with open(file_path, 'r') as f:
                        analysis = json.load(f)
                        analysis['file_path'] = str(file_path)
                        analysis['summary_file'] = str(file_path).replace('.json', '.txt')
                        all_analyses.append(analysis)
                except:
                    pass
            return sorted(all_analyses, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def get_stats(self):
        """Get dashboard statistics"""
        display_analyses = self.get_display_analyses()
        
        stats = {
            'total_analyses': len(display_analyses),
            'by_filter': {},
            'by_object': {},
            'recent_analyses': display_analyses[:10],
            'watcher_running': self.watcher_running,
            'show_only_new_files': self.show_only_new_files,
        }
        
        # Count by filter
        for analysis in display_analyses:
            filter_name = analysis['file_info'].get('filter', 'Unknown')
            stats['by_filter'][filter_name] = stats['by_filter'].get(filter_name, 0) + 1
            
            object_name = analysis['file_info'].get('object', 'Unknown')
            stats['by_object'][object_name] = stats['by_object'].get(object_name, 0) + 1
        
        return stats

# Initialize dashboard manager
dashboard = DashboardManager()

@app.route('/')
def index():
    """Main dashboard page"""
    stats = dashboard.get_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/api/analyses')
def get_analyses():
    """Get analyses for display (respects new-files-only mode)"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    display_analyses = dashboard.get_display_analyses()
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return jsonify({
        'analyses': display_analyses[start:end],
        'total': len(display_analyses),
        'page': page,
        'per_page': per_page,
        'pages': (len(display_analyses) + per_page - 1) // per_page,
        'watcher_running': dashboard.watcher_running,
        'show_only_new_files': dashboard.show_only_new_files,
    })

@app.route('/api/analysis/<filename>')
def get_analysis(filename):
    """Get analysis for a specific file"""
    try:
        # Decode URL-encoded filename
        from urllib.parse import unquote
        filename = unquote(filename)
        
        # First, try to find in display analyses
        display_analyses = dashboard.get_display_analyses()
        for analysis in display_analyses:
            if analysis['file_info']['filename'] == filename:
                return jsonify(analysis)
        
        # If not found in display analyses, check all analysis files
        analysis_files = list(app.config['ANALYSIS_DIR'].glob('*_centaur_analysis.json'))
        for file_path in analysis_files:
            try:
                with open(file_path, 'r') as f:
                    analysis = json.load(f)
                    if analysis['file_info']['filename'] == filename:
                        return jsonify(analysis)
            except:
                continue
        
        return jsonify({'error': 'Analysis not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_dashboard_stats():
    """Get dashboard statistics"""
    return jsonify(dashboard.get_stats())

@app.route('/api/watcher/start')
def start_watcher():
    """Start the file watcher"""
    try:
        success = dashboard.start_watcher()
        if success:
            return jsonify({
                'status': 'started', 
                'message': 'Watcher started. Only NEW files will be analyzed and displayed.',
                'watcher_running': True
            })
        else:
            return jsonify({
                'status': 'already_running', 
                'message': 'Watcher is already running',
                'watcher_running': True
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watcher/stop')
def stop_watcher():
    """Stop the file watcher"""
    try:
        dashboard.stop_watcher()
        return jsonify({
            'status': 'stopped', 
            'message': 'Watcher stopped',
            'watcher_running': False
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watcher/status')
def watcher_status():
    """Get watcher status"""
    return jsonify({
        'watcher_running': dashboard.watcher_running,
        'show_only_new_files': dashboard.show_only_new_files,
        'total_new_files': len(dashboard.analyses),
        'total_processed_files': len(dashboard.processed_files)
    })

@app.route('/api/process/manual/<filename>')
def process_file_manual(filename):
    """Manually process a specific file (even if it's an existing file)"""
    try:
        from urllib.parse import unquote
        filename = unquote(filename)
        
        watch_path = Path(app.config['WATCH_PATH'])
        file_path = None
        
        # Search for the file
        for ext in ['.fits', '.fit', '.FITS', '.FIT']:
            matches = list(watch_path.rglob(f'*{filename}*{ext}'))
            if matches:
                file_path = matches[0]
                break
        
        if not file_path or not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Analyze the file
        analyzer = EnhancedFITSAnalyzer(str(file_path))
        report = analyzer.generate_report()
        
        # Save the report
        safe_name = file_path.name.replace(' ', '_').replace(':', '-')
        report_filename = f"{Path(safe_name).stem}_centaur_analysis.json"
        report_path = app.config['ANALYSIS_DIR'] / report_filename
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Create summary
        summary_file = report_path.with_suffix('.txt')
        dashboard.create_summary_file(file_path, report, summary_file)
        
        # Mark as processed and add to analyses
        dashboard.mark_file_processed(file_path)
        report['file_path'] = str(report_path)
        report['summary_file'] = str(summary_file)
        dashboard.analyses.insert(0, report)
        
        return jsonify({
            'status': 'processed',
            'message': f'File {filename} analyzed successfully',
            'analysis': report
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Centaur Parting Web Dashboard")
    print(f"Analysis Directory: {app.config['ANALYSIS_DIR']}")
    print(f"Watch Path: {app.config['WATCH_PATH']}")
    print(f"Current Working Directory: {Path.cwd()}")
    print("=" * 60)
    
    # Check if watch path exists
    watch_path = Path(app.config['WATCH_PATH'])
    if watch_path.exists():
        print(f"✓ Watch path exists: {watch_path}")
        print(f"  Permissions: {oct(watch_path.stat().st_mode)[-3:]}")
    else:
        print(f"✗ WARNING: Watch path does not exist: {watch_path}")
        print("  Make sure the volume is mounted before starting the watcher")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
