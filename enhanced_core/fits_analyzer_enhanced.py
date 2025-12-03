import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
import photutils
from photutils import CircularAperture, aperture_photometry, CircularAnnulus
import warnings
import os
from datetime import datetime

class FITSEnhancedAnalyzer:
    def __init__(self, fits_path, aperture_radius=15, sky_inner=25, sky_outer=40):
        self.fits_path = fits_path
        self.data = None
        self.header = None
        self.aperture_radius = aperture_radius
        self.sky_inner = sky_inner
        self.sky_outer = sky_outer
        self._load_fits()
        self.snr = None
        self.sky_brightness = None
        self.fwhm = None
        self.background_stats = None
    
    def _load_fits(self):
        try:
            with fits.open(self.fits_path) as hdul:
                self.data = hdul[0].data.astype(float)
                self.header = hdul[0].header
                if self.data is None and len(hdul) > 1:
                    self.data = hdul[1].data.astype(float)
        except Exception as e:
            raise ValueError(f"Failed to load FITS file: {str(e)}")
    
    def _create_circular_mask(self, shape, center, radius):
        y, x = np.ogrid[:shape[0], :shape[1]]
        dist_from_center = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        return dist_from_center <= radius
    
    def _create_annulus_mask(self, shape, center, inner_radius, outer_radius):
        y, x = np.ogrid[:shape[0], :shape[1]]
        dist_from_center = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        return (dist_from_center >= inner_radius) & (dist_from_center <= outer_radius)
    
    def _find_brightest_source(self, data):
        from photutils import detect_threshold, detect_sources
        threshold = detect_threshold(data, nsigma=3.0)
        segm = detect_sources(data, threshold, npixels=10)
        if segm is None or segm.nlabels == 0:
            return None
        from scipy import ndimage
        centers = ndimage.center_of_mass(data, labels=segm.data, index=range(1, segm.nlabels+1))
        brightest_idx = np.argmax([np.max(data[segm.data == i]) for i in range(1, segm.nlabels+1)])
        return (centers[brightest_idx][1], centers[brightest_idx][0])
    
    def calculate_snr_advanced(self, position=None, detect_sources=True):
        data_clean = self.data - np.median(self.data)
        
        if position is None and detect_sources:
            position = self._find_brightest_source(data_clean)
        
        if position is None:
            raise ValueError("No position provided and source detection failed")
        
        snr_metrics = {
            'simple': self._calculate_simple_snr(data_clean, position),
            'aperture': self._calculate_aperture_snr(data_clean, position),
        }
        
        weights = {'simple': 0.6, 'aperture': 0.4}
        self.snr = sum(snr_metrics[m] * weights[m] for m in snr_metrics)
        
        return {
            'snr_final': self.snr,
            'snr_methods': snr_metrics,
            'position': position,
            'recommended_exposure': self._recommend_exposure()
        }
    
    def _calculate_simple_snr(self, data, position):
        x, y = int(position[0]), int(position[1])
        
        source_mask = self._create_circular_mask(data.shape, position, self.aperture_radius)
        source_flux = np.sum(data[source_mask])
        source_area = np.sum(source_mask)
        
        sky_mask = self._create_annulus_mask(data.shape, position, self.sky_inner, self.sky_outer)
        sky_values = data[sky_mask]
        
        sky_mean, sky_median, sky_std = sigma_clipped_stats(sky_values, sigma=3.0)
        
        net_source_flux = source_flux - (sky_mean * source_area)
        
        read_noise = self.header.get('RDNOISE', 10.0)
        exposure_time = self.header.get('EXPTIME', 1.0)
        dark_current = self.header.get('DARKCURR', 0.0) * exposure_time
        
        source_noise = np.sqrt(abs(net_source_flux))
        sky_noise = np.sqrt(abs(sky_mean) * source_area)
        read_noise_term = read_noise**2 * source_area
        dark_noise = dark_current * source_area
        
        total_noise = np.sqrt(source_noise**2 + sky_noise**2 + read_noise_term + dark_noise)
        
        return net_source_flux / total_noise if total_noise > 0 else 0
    
    def _calculate_aperture_snr(self, data, position):
        positions = [(position[0], position[1])]
        apertures = CircularAperture(positions, r=self.aperture_radius)
        annulus_apertures = CircularAnnulus(positions, r_in=self.sky_inner, r_out=self.sky_outer)
        
        phot_table = aperture_photometry(data, apertures)
        bkg_phot_table = aperture_photometry(data, annulus_apertures)
        
        bkg_mean = bkg_phot_table['aperture_sum'][0] / annulus_apertures.area
        source_flux = phot_table['aperture_sum'][0] - (bkg_mean * apertures.area)
        error = np.sqrt(abs(source_flux) + (apertures.area * abs(bkg_mean)))
        
        return source_flux / error if error > 0 else 0
    
    def calculate_sky_brightness(self, method='median_sigma_clipped'):
        from photutils import detect_sources
        
        threshold = np.median(self.data) + 3 * np.std(self.data)
        try:
            segm = detect_sources(self.data, threshold, npixels=10)
            source_mask = segm.data > 0
        except:
            source_mask = np.zeros_like(self.data, dtype=bool)
        
        masked_data = np.ma.masked_array(self.data, mask=source_mask)
        background_level = sigma_clipped_stats(masked_data, sigma=3.0)[1]
        
        gain = self.header.get('GAIN', 1.0)
        pixel_scale = self.header.get('PIXSCALE', 1.0)
        exposure_time = self.header.get('EXPTIME', 1.0)
        
        sky_adu = float(background_level)
        sky_electrons = sky_adu * gain
        sky_rate = sky_electrons / exposure_time if exposure_time > 0 else sky_electrons
        
        zero_point = self.header.get('MAGZPT', 25.0)
        if pixel_scale > 0:
            area_per_pixel = pixel_scale**2
            sky_mag_per_arcsec2 = zero_point - 2.5 * np.log10(sky_rate / area_per_pixel)
        else:
            sky_mag_per_arcsec2 = None
        
        self.sky_brightness = {
            'adu_per_pixel': sky_adu,
            'electrons_per_pixel': sky_electrons,
            'electrons_per_second_per_pixel': sky_rate,
            'mag_per_arcsec2': sky_mag_per_arcsec2,
            'method': method
        }
        
        return self.sky_brightness
    
    def _recommend_exposure(self):
        if self.snr is None:
            return {"error": "SNR not calculated"}
        
        current_exposure = self.header.get('EXPTIME', 1.0)
        target_snr = 100.0
        
        if self.snr > 0:
            required_exposure = current_exposure * (target_snr / self.snr)**2
        else:
            required_exposure = current_exposure * 4
        
        saturation_level = self.header.get('SATURATE', 65535)
        max_value = np.max(self.data)
        saturation_warning = max_value > 0.9 * saturation_level
        
        read_noise = self.header.get('RDNOISE', 10.0)
        sky_e = self.sky_brightness['electrons_per_pixel'] if self.sky_brightness else 1.0
        sky_noise = np.sqrt(sky_e)
        read_noise_dominant = read_noise > sky_noise
        
        optimal_sub = self._calculate_optimal_sub_length()
        
        return {
            'current_exposure': current_exposure,
            'current_snr': float(self.snr),
            'recommended_exposure': float(required_exposure),
            'exposure_factor': float(required_exposure / current_exposure),
            'saturation_warning': saturation_warning,
            'max_value_adu': float(max_value),
            'saturation_level': float(saturation_level),
            'read_noise_dominant': read_noise_dominant,
            'optimal_sub_length': optimal_sub,
            'sky_limited': not read_noise_dominant
        }
    
    def _calculate_optimal_sub_length(self):
        read_noise = self.header.get('RDNOISE', 10.0)
        gain = self.header.get('GAIN', 1.0)
        
        if self.sky_brightness:
            sky_rate = self.sky_brightness.get('electrons_per_second_per_pixel', 1.0)
        else:
            sky_rate = 1.0
        
        if sky_rate <= 0:
            return 60.0
        
        optimal_t = (read_noise**2) / sky_rate
        optimal_t = max(10.0, min(optimal_t, 600.0))
        
        return optimal_t
    
    def generate_analysis_report(self):
        snr_analysis = self.calculate_snr_advanced()
        sky_analysis = self.calculate_sky_brightness()
        exposure_rec = self._recommend_exposure()
        
        mean, median, std = sigma_clipped_stats(self.data, sigma=3.0)
        
        report = {
            'file_info': {
                'filename': os.path.basename(self.fits_path),
                'dimensions': self.data.shape,
                'exposure_time': self.header.get('EXPTIME', 'Unknown'),
                'filter': self.header.get('FILTER', 'Unknown'),
                'object': self.header.get('OBJECT', 'Unknown')
            },
            'snr_analysis': snr_analysis,
            'sky_brightness': sky_analysis,
            'exposure_recommendations': exposure_rec,
            'quality_metrics': {
                'image_mean': float(mean),
                'image_median': float(median),
                'image_std': float(std),
                'dynamic_range': float(np.max(self.data) / std) if std > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return report
