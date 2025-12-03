#!/usr/bin/env python3
import sys
sys.path.append('.')
from enhanced_core.fits_analyzer_enhanced import FITSEnhancedAnalyzer
import glob

def quick_test_directory(directory="."):
    fits_files = glob.glob(f"{directory}/*.fits") + glob.glob(f"{directory}/*.fit")
    
    if not fits_files:
        print(f"No FITS files found in {directory}")
        return
    
    print(f"Found {len(fits_files)} FITS files")
    
    for i, fits_file in enumerate(fits_files[:3]):
        print(f"\n{i+1}. Analyzing: {fits_file}")
        try:
            analyzer = FITSEnhancedAnalyzer(fits_file)
            report = analyzer.generate_analysis_report()
            
            rec = report['exposure_recommendations']
            print(f"   SNR: {report['snr_analysis']['snr_final']:.1f}")
            print(f"   Sky: {report['sky_brightness'].get('mag_per_arcsec2', 'N/A'):.1f} mag/arcsec²")
            print(f"   Rec exposure: {rec['recommended_exposure']:.0f}s (current: {rec['current_exposure']}s)")
            print(f"   Action: {'ADJUST' if rec['exposure_factor'] > 1.2 or rec['exposure_factor'] < 0.8 else 'CONTINUE'}")
            
        except Exception as e:
            print(f"   Error: {str(e)}")

if __name__ == "__main__":
    import sys
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    quick_test_directory(directory)
