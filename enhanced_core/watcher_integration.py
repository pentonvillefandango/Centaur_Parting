import os
import time
import json
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from enhanced_core.fits_analyzer_enhanced import FITSEnhancedAnalyzer

class FITSWatcher(FileSystemEventHandler):
    def __init__(self, watch_path, analysis_output_dir="analysis_results"):
        self.watch_path = watch_path
        self.analysis_output_dir = analysis_output_dir
        
        os.makedirs(analysis_output_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(analysis_output_dir, 'watcher.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.fits', '.fit')):
            self.logger.info(f"New FITS file detected: {event.src_path}")
            self.analyze_fits_file(event.src_path)
    
    def analyze_fits_file(self, fits_path):
        try:
            self.logger.info(f"Starting analysis of {fits_path}")
            
            analyzer = FITSEnhancedAnalyzer(fits_path)
            report = analyzer.generate_analysis_report()
            
            output_filename = os.path.basename(fits_path).replace('.fits', '.json')
            output_path = os.path.join(self.analysis_output_dir, output_filename)
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"Analysis saved to {output_path}")
            
            recommendations = self._generate_actionable_recommendations(report)
            
            self.logger.info("RECOMMENDATIONS:")
            for key, value in recommendations.items():
                self.logger.info(f"  {key}: {value}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error analyzing {fits_path}: {str(e)}")
            return None
    
    def _generate_actionable_recommendations(self, report):
        rec = report['exposure_recommendations']
        sky = report['sky_brightness']
        
        recommendations = {
            'action': 'continue',
            'adjustments': []
        }
        
        if rec.get('saturation_warning', False):
            recommendations['action'] = 'adjust'
            recommendations['adjustments'].append({
                'type': 'exposure',
                'reason': 'Saturation detected',
                'adjustment': f"Reduce exposure time by factor {1/rec['exposure_factor']:.2f}"
            })
        
        if rec['exposure_factor'] > 1.5:
            recommendations['action'] = 'adjust'
            recommendations['adjustments'].append({
                'type': 'exposure',
                'reason': f"Low SNR ({rec['current_snr']:.1f})",
                'adjustment': f"Increase exposure to {rec['recommended_exposure']:.1f}s"
            })
        elif rec['exposure_factor'] < 0.67:
            recommendations['action'] = 'adjust'
            recommendations['adjustments'].append({
                'type': 'exposure',
                'reason': f"High SNR ({rec['current_snr']:.1f}) - could shorten exposure",
                'adjustment': f"Consider reducing to {rec['recommended_exposure']:.1f}s"
            })
        
        sky_brightness = sky.get('mag_per_arcsec2')
        if sky_brightness and sky_brightness < 19.0:
            recommendations['adjustments'].append({
                'type': 'filter',
                'reason': f'Bright sky ({sky_brightness:.1f} mag/arcsec²)',
                'adjustment': 'Consider narrowband filter or wait for darker skies'
            })
        
        optimal_sub = rec.get('optimal_sub_length', 60)
        current_exp = rec['current_exposure']
        
        if abs(optimal_sub - current_exp) > 30:
            recommendations['adjustments'].append({
                'type': 'sub_length',
                'reason': 'Sub-optimal sub-exposure length',
                'adjustment': f'Optimal sub length: {optimal_sub:.1f}s'
            })
        
        return recommendations

def start_watcher(watch_path="/Volumes/Rig24_Imaging"):
    event_handler = FITSWatcher(watch_path)
    observer = Observer()
    observer.schedule(event_handler, watch_path, recursive=True)
    
    print(f"Starting FITS watcher on {watch_path}")
    print(f"Analysis results will be saved to: {event_handler.analysis_output_dir}")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
