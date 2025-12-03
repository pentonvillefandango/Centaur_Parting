import sys
sys.path.append('.')
from enhanced_core.fits_analyzer_enhanced import FITSEnhancedAnalyzer
import json

def test_analyzer():
    print("Testing Enhanced FITS Analyzer")
    print("=" * 50)
    
    test_file = "test.fits"
    
    if not os.path.exists(test_file):
        print(f"Test file {test_file} not found.")
        print("Creating a dummy FITS file for testing...")
        from astropy.io import fits
        import numpy as np
        
        data = np.random.normal(1000, 100, (1024, 1024))
        data[500:520, 500:520] = 5000
        
        hdu = fits.PrimaryHDU(data)
        hdu.header['EXPTIME'] = 60.0
        hdu.header['GAIN'] = 0.8
        hdu.header['RDNOISE'] = 9.0
        hdu.header['SATURATE'] = 65000
        hdu.header['OBJECT'] = 'TEST_STAR'
        hdu.header['FILTER'] = 'L'
        
        hdu.writeto(test_file, overwrite=True)
        print(f"Created dummy FITS file: {test_file}")
    
    try:
        analyzer = FITSEnhancedAnalyzer(test_file)
        print(f"Loaded FITS file: {test_file}")
        print(f"Image dimensions: {analyzer.data.shape}")
        print(f"Exposure time: {analyzer.header.get('EXPTIME', 'Unknown')}s")
        
        report = analyzer.generate_analysis_report()
        
        print("\nAnalysis Results:")
        print(f"SNR: {report['snr_analysis']['snr_final']:.2f}")
        print(f"Sky Brightness: {report['sky_brightness']['mag_per_arcsec2']:.2f} mag/arcsec²")
        
        rec = report['exposure_recommendations']
        print(f"\nExposure Recommendations:")
        print(f"Current exposure: {rec['current_exposure']}s")
        print(f"Recommended exposure: {rec['recommended_exposure']:.1f}s")
        print(f"Exposure factor: {rec['exposure_factor']:.2f}x")
        print(f"Saturation warning: {rec['saturation_warning']}")
        print(f"Optimal sub length: {rec['optimal_sub_length']:.1f}s")
        print(f"Sky limited: {rec['sky_limited']}")
        
        output_file = "test_analysis_report.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nFull report saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import os
    test_analyzer()
