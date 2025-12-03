#!/usr/bin/env python3
import sys
sys.path.append('.')
from enhanced_core.fits_analyzer_enhanced import FITSEnhancedAnalyzer
import numpy as np
from astropy.io import fits
import json
import os

def create_realistic_test_fits(filename="realistic_test.fits"):
    """Create a more realistic FITS file for testing"""
    print("Creating realistic test FITS file...")
    
    # Image dimensions
    width, height = 2048, 2048
    
    # Create realistic background (sky glow)
    background = np.random.normal(500, 50, (height, width))
    
    # Add some realistic stars (Gaussian profiles)
    data = background.copy()
    
    # Add a bright star
    y, x = 1000, 1000
    yy, xx = np.ogrid[:height, :width]
    distance = np.sqrt((xx - x)**2 + (yy - y)**2)
    star_profile = 10000 * np.exp(-distance**2 / (2 * 5**2))  # FWHM ~ 12px
    data += star_profile
    
    # Add a few fainter stars
    for i in range(5):
        y_star = np.random.randint(200, height-200)
        x_star = np.random.randint(200, width-200)
        distance = np.sqrt((xx - x_star)**2 + (yy - y_star)**2)
        brightness = np.random.uniform(1000, 5000)
        fwhm = np.random.uniform(3, 8)
        star = brightness * np.exp(-distance**2 / (2 * fwhm**2))
        data += star
    
    # Add some read noise
    read_noise = np.random.normal(0, 9.0, (height, width))
    data += read_noise
    
    # Add Poisson noise (shot noise)
    data = np.random.poisson(data)
    
    # Create FITS header with realistic values
    hdu = fits.PrimaryHDU(data.astype(np.float32))
    
    # Add realistic header information
    hdu.header['EXPTIME'] = 300.0  # 5 minute exposure
    hdu.header['GAIN'] = 0.8       # Common astro camera gain
    hdu.header['RDNOISE'] = 9.0    # Read noise in electrons
    hdu.header['SATURATE'] = 50000 # Saturation level
    hdu.header['PIXSCALE'] = 0.55  # arcsec/pixel (typical for many scopes)
    hdu.header['OBJECT'] = 'M42'   # Orion Nebula
    hdu.header['FILTER'] = 'Ha'    # Hydrogen-alpha filter
    hdu.header['INSTRUME'] = 'ASI2600MM'
    hdu.header['TELESCOP'] = 'RASA8'
    hdu.header['AIRMASS'] = 1.2
    hdu.header['MAGZPT'] = 25.0    # Zero point for magnitude calculation
    
    # Save the file
    hdu.writeto(filename, overwrite=True)
    print(f"Created realistic test FITS: {filename}")
    print(f"  Dimensions: {width}x{height}")
    print(f"  Exposure: {hdu.header['EXPTIME']}s")
    print(f"  Gain: {hdu.header['GAIN']} e-/ADU")
    print(f"  Read noise: {hdu.header['RDNOISE']} e-")
    return filename

def test_with_realistic_data():
    print("\n" + "="*60)
    print("Testing with Realistic Astrophotography Data")
    print("="*60)
    
    test_file = "realistic_test.fits"
    
    # Remove old test file if it exists
    if os.path.exists(test_file):
        os.remove(test_file)
    
    # Create realistic test file
    test_file = create_realistic_test_fits(test_file)
    
    try:
        # Analyze the file
        analyzer = FITSEnhancedAnalyzer(test_file)
        
        print(f"\nAnalyzing {test_file}...")
        print(f"Image dimensions: {analyzer.data.shape}")
        print(f"Exposure time: {analyzer.header.get('EXPTIME', 'Unknown')}s")
        print(f"Filter: {analyzer.header.get('FILTER', 'Unknown')}")
        print(f"Object: {analyzer.header.get('OBJECT', 'Unknown')}")
        
        # Generate analysis report
        report = analyzer.generate_analysis_report()
        
        print("\n" + "-"*40)
        print("ANALYSIS RESULTS")
        print("-"*40)
        
        # SNR results
        snr_info = report['snr_analysis']
        print(f"\nSNR Analysis:")
        print(f"  Final SNR: {snr_info['snr_final']:.1f}")
        print(f"  Simple method SNR: {snr_info['snr_methods']['simple']:.1f}")
        print(f"  Aperture method SNR: {snr_info['snr_methods']['aperture']:.1f}")
        
        # Sky brightness
        sky_info = report['sky_brightness']
        print(f"\nSky Brightness:")
        print(f"  ADU per pixel: {sky_info['adu_per_pixel']:.1f}")
        print(f"  Electrons per pixel: {sky_info['electrons_per_pixel']:.1f}")
        print(f"  Mag/arcsec²: {sky_info.get('mag_per_arcsec2', 'N/A'):.1f}")
        
        # Exposure recommendations
        rec = report['exposure_recommendations']
        print(f"\nExposure Recommendations:")
        print(f"  Current exposure: {rec['current_exposure']}s")
        print(f"  Current SNR: {rec['current_snr']:.1f}")
        print(f"  Recommended exposure: {rec['recommended_exposure']:.0f}s")
        print(f"  Exposure factor: {rec['exposure_factor']:.2f}x")
        
        # Recommendations based on factor
        if rec['exposure_factor'] > 2.0:
            print(f"  RECOMMENDATION: Increase exposure significantly")
        elif rec['exposure_factor'] > 1.2:
            print(f"  RECOMMENDATION: Consider increasing exposure")
        elif rec['exposure_factor'] < 0.8:
            print(f"  RECOMMENDATION: Consider decreasing exposure")
        else:
            print(f"  RECOMMENDATION: Current exposure is good")
        
        print(f"  Saturation warning: {rec['saturation_warning']}")
        print(f"  Optimal sub length: {rec['optimal_sub_length']:.0f}s")
        print(f"  Sky limited: {rec['sky_limited']}")
        
        # Quality metrics
        quality = report['quality_metrics']
        print(f"\nImage Quality:")
        print(f"  Mean: {quality['image_mean']:.1f}")
        print(f"  Median: {quality['image_median']:.1f}")
        print(f"  Std dev: {quality['image_std']:.1f}")
        print(f"  Dynamic range: {quality['dynamic_range']:.1f}")
        
        # Save detailed report
        output_file = "realistic_analysis_report.json"
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
    test_with_realistic_data()
