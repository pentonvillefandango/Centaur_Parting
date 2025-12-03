#!/usr/bin/env python3
import sys
sys.path.append('.')
from enhanced_core.fits_analyzer_enhanced import FITSEnhancedAnalyzer
import glob
import os
import json

def find_and_test_fits():
    # Check common astrophotography directories
    test_paths = [
        "/Volumes/Rig24_Imaging",
        ".",
        "test_data",
        os.path.expanduser("~/Astro")
    ]
    
    for path in test_paths:
        if os.path.exists(path):
            print(f"\nChecking {path}...")
            fits_files = glob.glob(f"{path}/*.fits") + glob.glob(f"{path}/*.fit")
            if fits_files:
                print(f"Found {len(fits_files)} FITS files")
                for i, fits_file in enumerate(fits_files[:2]):  # Test first 2
                    print(f"\n{i+1}. Testing: {os.path.basename(fits_file)}")
                    try:
                        analyzer = FITSEnhancedAnalyzer(fits_file)
                        report = analyzer.generate_analysis_report()
                        
                        rec = report['exposure_recommendations']
                        print(f"   Exposure: {rec['current_exposure']}s")
                        print(f"   SNR: {rec['current_snr']:.1f}")
                        print(f"   Sky: {report['sky_brightness'].get('mag_per_arcsec2', 'N/A'):.1f} mag/arcsec²")
                        print(f"   Rec exposure: {rec['recommended_exposure']:.0f}s")
                        print(f"   Factor: {rec['exposure_factor']:.2f}x")
                        
                        # Simple recommendation
                        if rec['exposure_factor'] > 1.5:
                            print(f"   ACTION: Increase exposure time")
                        elif rec['exposure_factor'] < 0.67:
                            print(f"   ACTION: Decrease exposure time")
                        else:
                            print(f"   ACTION: Good exposure")
                        
                        # Save report
                        report_file = os.path.basename(fits_file).replace('.fits', '_report.json')
                        with open(report_file, 'w') as f:
                            json.dump(report, f, indent=2)
                        print(f"   Report saved: {report_file}")
                        
                    except Exception as e:
                        print(f"   Error: {str(e)}")
                return True
    
    print("\nNo FITS files found in common locations.")
    print("Try mounting your imaging rig or placing FITS files in the current directory.")
    return False

if __name__ == "__main__":
    find_and_test_fits()
