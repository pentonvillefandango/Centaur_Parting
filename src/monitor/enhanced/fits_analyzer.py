import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
import photutils
from photutils import detect_sources
import os
from datetime import datetime
import warnings

class EnhancedFITSAnalyzer:
    def __init__(self, fits_path):
        self.fits_path = fits_path
        self.data = None
        self.header = None
        self._load_fits()
    
    def _load_fits(self):
        try:
            with fits.open(self.fits_path) as hdul:
                self.data = hdul[0].data.astype(float)
                self.header = hdul[0].header
                if self.data is None and len(hdul) > 1:
                    self.data = hdul[1].data.astype(float)
        except Exception as e:
            raise ValueError(f"Failed to load FITS file: {str(e)}")
    
    def analyze_saturation(self):
        """Detailed saturation analysis"""
        saturation_level = self.header.get('SATURATE', 65535)
        
        # Find max value
        max_value = float(np.max(self.data))
        
        # Count pixels at different saturation levels
        total_pixels = self.data.size
        
        # Near saturation (95-100%)
        near_sat_mask = self.data >= 0.95 * saturation_level
        near_sat_count = int(np.sum(near_sat_mask))
        near_sat_percent = float(near_sat_count / total_pixels * 100)
        
        # Highly saturated (80-95%)
        high_sat_mask = (self.data >= 0.80 * saturation_level) & (self.data < 0.95 * saturation_level)
        high_sat_count = int(np.sum(high_sat_mask))
        high_sat_percent = float(high_sat_count / total_pixels * 100)
        
        # Check if these are isolated hot pixels or real saturation
        # Hot pixels are usually isolated, saturation affects larger areas
        hot_pixel_like = False
        if near_sat_count > 0:
            # Check if saturated pixels are clustered or isolated
            from scipy import ndimage
            labeled, num_features = ndimage.label(near_sat_mask)
            if num_features > 0:
                # Get size of each saturated region
                region_sizes = [np.sum(labeled == i) for i in range(1, num_features + 1)]
                avg_region_size = np.mean(region_sizes)
                # If average region size is small (< 10 pixels), likely hot pixels
                hot_pixel_like = avg_region_size < 10
        
        # Calculate overall saturation percentage
        saturation_percent = float(max_value / saturation_level * 100) if saturation_level > 0 else 0
        
        # Determine saturation severity
        if near_sat_percent > 1.0:  # More than 1% of pixels near saturation
            severity = "HIGH"
            warning = True
        elif near_sat_percent > 0.1:  # More than 0.1% of pixels near saturation
            severity = "MODERATE"
            warning = True
        elif max_value >= saturation_level:  # At least one pixel at max
            severity = "MINOR (hot pixels)"
            warning = hot_pixel_like  # Only warn if not hot-pixel-like
        else:
            severity = "NONE"
            warning = False
        
        return {
            'max_value': max_value,
            'saturation_level': float(saturation_level),
            'max_percentage': saturation_percent,
            'near_saturated_pixels': near_sat_count,
            'near_saturated_percent': near_sat_percent,
            'high_saturation_pixels': high_sat_count,
            'high_saturation_percent': high_sat_percent,
            'severity': severity,
            'warning': bool(warning),
            'likely_hot_pixels': bool(hot_pixel_like),
            'total_pixels': total_pixels
        }
    
    def calculate_background_stats(self):
        """Calculate background statistics with careful source masking"""
        # First get saturation info to handle hot pixels
        sat_info = self.analyze_saturation()
        
        # Create initial mask for very bright pixels
        if sat_info['near_saturated_pixels'] > 0:
            # Mask near-saturated pixels for background calculation
            saturation_level = sat_info['saturation_level']
            hot_pixel_mask = self.data >= 0.90 * saturation_level
        else:
            hot_pixel_mask = np.zeros_like(self.data, dtype=bool)
        
        # Detect astronomical sources (not hot pixels)
        try:
            # Use sigma-clipped median for better threshold
            median = np.median(self.data[~hot_pixel_mask]) if np.any(~hot_pixel_mask) else np.median(self.data)
            std = np.std(self.data[~hot_pixel_mask]) if np.any(~hot_pixel_mask) else np.std(self.data)
            
            threshold_value = median + 5 * std  # Higher threshold to avoid noise
            segm = detect_sources(self.data, threshold_value, npixels=5)
            
            if segm:
                source_mask = segm.data > 0
                # Combine with hot pixel mask
                combined_mask = source_mask | hot_pixel_mask
            else:
                combined_mask = hot_pixel_mask
        except:
            combined_mask = hot_pixel_mask
        
        # Get background pixels
        background_data = self.data[~combined_mask]
        
        # If too few background pixels, use all non-hot-pixel data
        if len(background_data) < 1000:
            background_data = self.data[~hot_pixel_mask]
            if len(background_data) < 1000:
                background_data = self.data.flatten()
        
        # Calculate robust background statistics
        bg_mean, bg_median, bg_std = sigma_clipped_stats(background_data, sigma=3.0, maxiters=5)
        
        # Count actual astronomical sources (excluding hot pixels)
        try:
            # Lower threshold for source counting
            threshold_value = bg_median + 3 * bg_std
            segm = detect_sources(self.data, threshold_value, npixels=5)
            num_sources = int(np.sum(segm.data > 0)) if segm else 0
        except:
            num_sources = 0
        
        return float(bg_mean), float(bg_median), float(bg_std), num_sources
    
    def calculate_snr_metrics(self, bg_mean, bg_std):
        """Calculate various SNR metrics"""
        # SNR of background (background mean / background std)
        snr_background = bg_mean / bg_std if bg_std > 0 else 0
        
        # Estimate SNR for different signal levels
        # Faint signal: 3σ above background
        faint_signal = bg_mean + 3 * bg_std
        snr_faint = (faint_signal - bg_mean) / bg_std if bg_std > 0 else 0
        
        # Moderate signal: 10σ above background
        moderate_signal = bg_mean + 10 * bg_std
        snr_moderate = (moderate_signal - bg_mean) / bg_std if bg_std > 0 else 0
        
        return {
            'snr_background': float(snr_background),
            'snr_faint_object': float(snr_faint),      # 3σ object
            'snr_moderate_object': float(snr_moderate), # 10σ object
            'background_mean': float(bg_mean),
            'background_std': float(bg_std),
            'faint_signal_level': float(faint_signal),
            'moderate_signal_level': float(moderate_signal)
        }
    
    def calculate_sky_brightness(self, bg_median):
        """Calculate sky brightness metrics"""
        gain = float(self.header.get('GAIN', 1.0))
        pixel_scale = float(self.header.get('PIXSCALE', 0.0))
        exposure_time = float(self.header.get('EXPTIME', 0.0))
        
        # Try to get exposure from filename if not in header
        if exposure_time == 0:
            import os
            filename = os.path.basename(self.fits_path)
            parts = filename.split('_')
            if len(parts) > 7 and 's' in parts[7]:
                try:
                    exposure_time = float(parts[7].replace('s', ''))
                except:
                    pass
        
        # Convert to electrons
        sky_electrons = bg_median * gain
        sky_rate = sky_electrons / exposure_time if exposure_time > 0 else sky_electrons
        
        # Calculate magnitude per arcsec²
        zero_point = float(self.header.get('MAGZPT', 25.0))
        sky_mag = None
        
        if pixel_scale > 0:
            area_per_pixel = pixel_scale**2
            if sky_rate > 0:
                sky_mag = zero_point - 2.5 * np.log10(sky_rate / area_per_pixel)
        elif 'FOCALLEN' in self.header and 'XPIXSZ' in self.header:
            # Calculate pixel scale from focal length and pixel size
            focal_length = float(self.header['FOCALLEN'])  # mm
            pixel_size = float(self.header['XPIXSZ'])      # microns
            if focal_length > 0 and pixel_size > 0:
                pixel_scale = 206.265 * pixel_size / focal_length  # arcsec/pixel
                area_per_pixel = pixel_scale**2
                if sky_rate > 0:
                    sky_mag = zero_point - 2.5 * np.log10(sky_rate / area_per_pixel)
        
        return {
            'adu_per_pixel': float(bg_median),
            'electrons_per_pixel': float(sky_electrons),
            'electrons_per_second_per_pixel': float(sky_rate),
            'mag_per_arcsec2': float(sky_mag) if sky_mag is not None else None,
            'exposure_time_used': float(exposure_time),
            'gain': float(gain),
            'pixel_scale': float(pixel_scale) if pixel_scale > 0 else None
        }
    
    def analyze_for_exposure_optimization(self):
        """Main analysis for exposure optimization"""
        # Get saturation analysis
        saturation = self.analyze_saturation()
        
        # Get background statistics
        bg_mean, bg_median, bg_std, num_sources = self.calculate_background_stats()
        
        # Calculate SNR metrics
        snr_metrics = self.calculate_snr_metrics(bg_mean, bg_std)
        
        # Calculate sky brightness
        sky = self.calculate_sky_brightness(bg_median)
        
        # Get current exposure
        current_exposure = sky['exposure_time_used']
        
        # Exposure recommendation logic
        if saturation['warning'] and saturation['severity'] in ["HIGH", "MODERATE"]:
            # Image has significant saturation - reduce exposure
            if saturation['near_saturated_percent'] > 1.0:
                # Severe saturation - reduce significantly
                reduction_factor = 0.5
            else:
                # Moderate saturation - reduce moderately
                reduction_factor = 0.7
            
            required_exposure = current_exposure * reduction_factor
            reason = "saturation"
            
        else:
            # No significant saturation - optimize for SNR
            target_snr = 10.0  # Aim for SNR=10 for good faint detail
            
            if snr_metrics['snr_moderate_object'] > 0:
                required_exposure = current_exposure * (target_snr / snr_metrics['snr_moderate_object'])**2
                reason = "snr_optimization"
            else:
                required_exposure = current_exposure  # Keep as is
                reason = "default"
        
        # Apply reasonable bounds
        required_exposure = max(30.0, min(required_exposure, 600.0))  # 30s to 10min
        
        # Calculate optimal sub length (when sky noise ≈ read noise)
        read_noise = float(self.header.get('RDNOISE', 10.0))
        sky_rate = sky['electrons_per_second_per_pixel']
        
        if sky_rate > 0:
            optimal_sub = (read_noise**2) / sky_rate
            optimal_sub = max(60.0, min(optimal_sub, 300.0))  # 1-5 minutes for Ha
        else:
            optimal_sub = 180.0  # Default 3 minutes for Ha
        
        # Image quality metrics
        mean, median, std = sigma_clipped_stats(self.data, sigma=3.0)
        
        # Calculate noise regime
        sky_e = sky['electrons_per_pixel']
        sky_noise = float(np.sqrt(sky_e)) if sky_e > 0 else 0
        read_noise_dominant = bool(read_noise > sky_noise) if sky_e > 0 else True
        
        # Determine if exposure should be adjusted for SHO
        # For SHO imaging, shorter exposures often work better
        filter_type = str(self.header.get('FILTER', '')).upper()
        if any(f in filter_type for f in ['HA', 'SII', 'OIII']):
            # Narrowband - can use shorter exposures
            sho_adjustment = 0.6  # SHO typically 60% of Ha exposure
            sho_recommended = required_exposure * sho_adjustment
        else:
            sho_adjustment = 1.0
            sho_recommended = required_exposure
        
        return {
            'saturation_analysis': saturation,
            'snr_metrics': snr_metrics,
            'sky_brightness': sky,
            'current_exposure': current_exposure,
            'recommended_exposure': float(required_exposure),
            'exposure_factor': float(required_exposure / current_exposure) if current_exposure > 0 else 1.0,
            'optimization_reason': reason,
            'optimal_sub_length': float(optimal_sub),
            'sho_recommendation': {
                'adjustment_factor': float(sho_adjustment),
                'recommended_exposure': float(sho_recommended),
                'note': 'For SII/OIII with same sky conditions'
            },
            'image_stats': {
                'mean': float(mean),
                'median': float(median),
                'std': float(std),
                'num_sources_detected': num_sources
            },
            'noise_regime': {
                'read_noise': read_noise,
                'sky_noise': sky_noise,
                'read_noise_dominant': read_noise_dominant,
                'sky_rate_electrons_per_second': float(sky_rate)
            }
        }
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        import os
        
        # Extract basic info from filename
        filename = os.path.basename(self.fits_path)
        parts = filename.split('_')
        
        # Perform analysis
        analysis = self.analyze_for_exposure_optimization()
        
        # Generate actionable recommendations
        recommendations = []
        
        # Saturation analysis
        sat = analysis['saturation_analysis']
        if sat['warning']:
            if sat['severity'] == "HIGH":
                recommendations.append(f"⚠️ SATURATION: {sat['near_saturated_percent']:.3f}% of pixels near saturation")
                recommendations.append(f"   Reduce exposure to {analysis['recommended_exposure']:.0f}s (currently {analysis['current_exposure']}s)")
            elif sat['severity'] == "MODERATE":
                recommendations.append(f"Note: {sat['near_saturated_percent']:.3f}% of pixels near saturation")
                if sat['likely_hot_pixels']:
                    recommendations.append("   Likely hot pixels, not object saturation")
            elif sat['severity'].startswith("MINOR"):
                recommendations.append(f"Note: Few hot pixels detected ({sat['near_saturated_count']} pixels)")
                if not sat['likely_hot_pixels']:
                    recommendations.append("   Consider dark frame calibration")
        else:
            recommendations.append("✓ No significant saturation detected")
        
        # Exposure recommendations
        factor = analysis['exposure_factor']
        if factor > 2.0:
            recommendations.append(f"Significantly increase exposure to {analysis['recommended_exposure']:.0f}s")
        elif factor > 1.2:
            recommendations.append(f"Consider increasing exposure to {analysis['recommended_exposure']:.0f}s")
        elif factor < 0.5:
            recommendations.append(f"Significantly decrease exposure to {analysis['recommended_exposure']:.0f}s")
        elif factor < 0.8:
            recommendations.append(f"Consider decreasing exposure to {analysis['recommended_exposure']:.0f}s")
        else:
            recommendations.append(f"Exposure time is good: {analysis['current_exposure']}s")
        
        # SHO recommendations
        sho = analysis['sho_recommendation']
        if sho['adjustment_factor'] < 1.0:
            recommendations.append(f"For SII/OIII: {sho['recommended_exposure']:.0f}s ({sho['adjustment_factor']:.1f}x Ha)")
        
        # Sub-exposure optimization
        current_sub = analysis['current_exposure']
        optimal_sub = analysis['optimal_sub_length']
        if abs(current_sub - optimal_sub) > 60:
            recommendations.append(f"Optimal sub length: {optimal_sub:.0f}s (currently {current_sub}s)")
        
        # Sky brightness
        sky_mag = analysis['sky_brightness'].get('mag_per_arcsec2')
        if sky_mag is not None:
            if sky_mag < 19.0:
                recommendations.append(f"Bright sky ({sky_mag:.1f} mag/arcsec²)")
            elif sky_mag > 21.0:
                recommendations.append(f"Dark sky ({sky_mag:.1f} mag/arcsec²)")
        
        # Noise regime
        if analysis['noise_regime']['read_noise_dominant']:
            recommendations.append("Read-noise limited. Longer subs would help.")
        else:
            recommendations.append("Sky-noise limited. Good exposure.")
        
        # Build final report
        report = {
            'file_info': {
                'filename': filename,
                'dimensions': list(self.data.shape),
                'filter': str(self.header.get('FILTER', parts[4] if len(parts) > 4 else 'Unknown')),
                'object': str(self.header.get('OBJECT', parts[0] if len(parts) > 0 else 'Unknown')),
                'exposure_from_header': float(self.header.get('EXPTIME', 0)) or 'Unknown',
                'gain': float(self.header.get('GAIN', 0)) or 'Unknown',
                'saturation_level': float(self.header.get('SATURATE', 0)) or 'Unknown'
            },
            'analysis': analysis,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat(),
            'analyzer_version': '1.2'
        }
        
        return report
