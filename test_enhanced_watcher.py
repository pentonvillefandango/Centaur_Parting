#!/usr/bin/env python3
"""
Test the enhanced watcher with existing FITS files
"""

import sys
import os
sys.path.append('src/monitor')

# Try to import the enhanced analyzer
try:
    from enhanced.fits_analyzer import EnhancedFITSAnalyzer
    print("✓ EnhancedFITSAnalyzer imported successfully")
    
    # Test with a real FITS file if available
    test_dirs = [
        "/Volumes/Rig24_Imaging",
        ".",
        "test_data"
    ]
    
    fits_found = False
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            for ext in ['.fits', '.fit', '.FITS', '.FIT']:
                import glob
                files = glob.glob(f"{test_dir}/*{ext}")
                if files:
                    print(f"\nFound FITS files in {test_dir}:")
                    for f in files[:2]:  # Test first 2
                        print(f"  Testing: {os.path.basename(f)}")
                        try:
                            analyzer = EnhancedFITSAnalyzer(f)
                            report = analyzer.generate_report()
                            print(f"    ✓ Analysis successful")
                            print(f"    SNR: {report['analysis']['snr']:.1f}")
                            print(f"    Sky: {report['analysis']['sky_brightness'].get('mag_per_arcsec2', 'N/A'):.1f} mag/arcsec²")
                            fits_found = True
                        except Exception as e:
                            print(f"    ✗ Error: {str(e)}")
                    break
    
    if not fits_found:
        print("\nNo FITS files found for testing.")
        print("To test with real data:")
        print("1. Mount your imaging rig at /Volumes/Rig24_Imaging")
        print("2. Or place FITS files in the current directory")
        print("3. Run: python src/monitor/enhanced_polling_watcher.py --test")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure dependencies are installed:")
    print("  pip install numpy astropy photutils scipy")
