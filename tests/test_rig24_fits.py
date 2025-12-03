#!/usr/bin/env python3
"""
Test FITS analysis on Rig24_Imaging data
"""

import sys
import os
import json
import numpy as np

# Custom JSON encoder to handle numpy types
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

# Add the enhanced analyzer to path
sys.path.append('src/monitor/enhanced')

try:
    from fits_analyzer import EnhancedFITSAnalyzer
    print("✓ EnhancedFITSAnalyzer imported successfully")
    
    # Get first FITS file from Rig24
    import glob
    fits_files = glob.glob("/Volumes/Rig24_Imaging/**/*.fits", recursive=True)
    
    if not fits_files:
        fits_files = glob.glob("/Volumes/Rig24_Imaging/**/*.fit", recursive=True)
    
    if fits_files:
        print(f"\nFound {len(fits_files)} FITS files on Rig24_Imaging")
        print("Testing first 3 files...\n")
        
        for i, test_file in enumerate(fits_files[:3]):
            print(f"{'='*70}")
            print(f"FILE {i+1}: {os.path.basename(test_file)}")
            print(f"{'='*70}")
            
            try:
                analyzer = EnhancedFITSAnalyzer(test_file)
                report = analyzer.generate_report()
                
                # Basic info
                info = report['file_info']
                print(f"\n📊 BASIC INFO")
                print(f"  Object: {info['object']}")
                print(f"  Filter: {info['filter']}")
                print(f"  Dimensions: {info['dimensions']}")
                print(f"  Exposure: {info['exposure_from_header']}s")
                
                analysis = report['analysis']
                
                # Saturation analysis
                sat = analysis['saturation_analysis']
                print(f"\n⚠️ SATURATION ANALYSIS")
                print(f"  Max pixel value: {sat['max_value']:.0f} ADU")
                print(f"  Saturation level: {sat['saturation_level']:.0f} ADU")
                print(f"  Pixels near saturation (95-100%): {sat['near_saturated_pixels']} ({sat['near_saturated_percent']:.4f}%)")
                print(f"  Pixels highly saturated (80-95%): {sat['high_saturation_pixels']} ({sat['high_saturation_percent']:.4f}%)")
                print(f"  Severity: {sat['severity']}")
                print(f"  Likely hot pixels: {sat['likely_hot_pixels']}")
                
                # Exposure analysis
                print(f"\n⏱️ EXPOSURE ANALYSIS")
                print(f"  Current: {analysis['current_exposure']}s")
                print(f"  Recommended: {analysis['recommended_exposure']:.0f}s")
                print(f"  Factor: {analysis['exposure_factor']:.2f}x")
                print(f"  Reason: {analysis['optimization_reason']}")
                
                # SNR analysis
                snr = analysis['snr_metrics']
                print(f"\n📈 SIGNAL-TO-NOISE")
                print(f"  Background SNR: {snr['snr_background']:.1f}")
                print(f"  Faint object (3σ) SNR: {snr['snr_faint_object']:.1f}")
                print(f"  Moderate object (10σ) SNR: {snr['snr_moderate_object']:.1f}")
                
                # Sky brightness
                sky = analysis['sky_brightness']
                print(f"\n🌌 SKY BRIGHTNESS")
                if sky['mag_per_arcsec2'] is not None:
                    print(f"  {sky['mag_per_arcsec2']:.1f} mag/arcsec²")
                print(f"  {sky['electrons_per_pixel']:.0f} e-/pixel")
                print(f"  {sky['electrons_per_second_per_pixel']:.2f} e-/s/pixel")
                
                # SHO recommendation
                sho = analysis['sho_recommendation']
                print(f"\n🎨 SHO RECOMMENDATIONS")
                print(f"  SII/OIII adjustment: {sho['adjustment_factor']:.2f}x")
                print(f"  Recommended for SII/OIII: {sho['recommended_exposure']:.0f}s")
                
                # Noise regime
                noise = analysis['noise_regime']
                print(f"\n🎚️ NOISE REGIME")
                print(f"  Read noise: {noise['read_noise']:.1f} e-")
                print(f"  Sky noise: {noise['sky_noise']:.1f} e-")
                print(f"  Sky rate: {noise['sky_rate_electrons_per_second']:.2f} e-/s/pixel")
                print(f"  Read noise dominant: {noise['read_noise_dominant']}")
                print(f"  Optimal sub length: {analysis['optimal_sub_length']:.0f}s")
                
                # Image stats
                stats = analysis['image_stats']
                print(f"\n📊 IMAGE STATISTICS")
                print(f"  Mean: {stats['mean']:.1f}")
                print(f"  Median: {stats['median']:.1f}")
                print(f"  Std dev: {stats['std']:.1f}")
                print(f"  Sources detected: {stats['num_sources_detected']}")
                
                # Recommendations
                print(f"\n💡 RECOMMENDATIONS")
                for j, rec in enumerate(report['recommendations'], 1):
                    print(f"  {j}. {rec}")
                
                # Save report
                report_file = f"{os.path.splitext(os.path.basename(test_file))[0]}_analysis.json"
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2, cls=NumpyEncoder)
                print(f"\n💾 Report saved to: {report_file}")
                
            except Exception as e:
                print(f"\n❌ Error analyzing file: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"\n{'='*70}")
        print(f"Test completed on {min(3, len(fits_files))} files")
        print(f"Total files available: {len(fits_files)}")
        print(f"{'='*70}")
        
    else:
        print("\nNo FITS files found on Rig24_Imaging")
        
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\nMake sure dependencies are installed:")
    print("pip install numpy astropy photutils scipy")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
