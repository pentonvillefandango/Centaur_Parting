"""
Centaur Parting - FITS Analyzer
Analyzes astrophotography FITS files and extracts metrics
"""

from pathlib import Path
import numpy as np
from typing import Dict, Any, Optional, Tuple, List  # Added List here
import logging

# Try to import astronomy libraries
try:
    from astropy.io import fits
    from astropy.stats import sigma_clipped_stats
    import sep
    HAS_ASTROPY = True
except ImportError as e:
    print(f"Warning: Astronomy libraries not available: {e}")
    print("Install with: pip install astropy sep")
    HAS_ASTROPY = False

logger = logging.getLogger(__name__)

class FitsAnalyzer:
    """Analyzes FITS files for astrophotography metrics"""
    
    def __init__(self):
        if not HAS_ASTROPY:
            raise ImportError("Required astronomy libraries not installed")
        
    def analyze_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Analyze a single FITS file and return metrics
        
        Returns:
            Dictionary containing all extracted metrics and metadata
        """
        try:
            # Open FITS file
            with fits.open(filepath) as hdul:
                # Get primary header
                header = hdul[0].header
                
                # Get image data (handle different FITS formats)
                if len(hdul) > 0:
                    data = hdul[0].data
                    if data is None and len(hdul) > 1:
                        data = hdul[1].data  # Try extension 1
                else:
                    raise ValueError("No data found in FITS file")
                
                # Ensure data is 2D
                if data is None:
                    raise ValueError("No image data in FITS file")
                if data.ndim != 2:
                    # Try to extract 2D data from 3D (color) FITS
                    if data.ndim == 3:
                        data = data[0, :, :]  # Take first channel
                    else:
                        raise ValueError(f"Unsupported data dimensions: {data.ndim}")
                
                # Extract metadata from header
                metadata = self._extract_metadata(header)
                
                # Calculate image metrics
                metrics = self._calculate_metrics(data, metadata)
                
                # Combine results
                result = {
                    'filepath': str(filepath),
                    'filename': filepath.name,
                    'metadata': metadata,
                    'metrics': metrics,
                    'analysis_success': True,
                    'error_message': None
                }
                
                logger.info(f"Analyzed {filepath.name}: HFR={metrics['hfr']:.2f}, "
                          f"stars={metrics['star_count']}, SNR={metrics['snr_estimate']:.1f}")
                
                return result
                
        except Exception as e:
            error_msg = f"Error analyzing {filepath}: {str(e)}"
            logger.error(error_msg)
            return {
                'filepath': str(filepath),
                'filename': filepath.name,
                'metadata': {},
                'metrics': {},
                'analysis_success': False,
                'error_message': error_msg
            }
    
    def _extract_metadata(self, header) -> Dict[str, Any]:
        """Extract metadata from FITS header"""
        metadata = {}
        
        # Standard FITS keywords for astrophotography
        standard_keys = [
            'EXPTIME', 'EXPOSURE',  # Exposure time
            'FILTER', 'FILT',       # Filter
            'GAIN',                 # Camera gain
            'CCD-TEMP', 'SET-TEMP', 'TEMPERAT',  # Temperature
            'INSTRUME', 'TELESCOP', # Equipment
            'OBJECT', 'OBJNAME',    # Target name
            'RA', 'DEC',            # Coordinates
            'DATE-OBS',             # Observation date/time
            'IMAGETYP',             # Image type (light, dark, flat, bias)
            'XBINNING', 'YBINNING', # Binning
        ]
        
        for key in standard_keys:
            if key in header:
                metadata[key.lower()] = header[key]
        
        # Try to get filter from filename if not in header
        if 'filter' not in metadata and 'object' in metadata:
            # Simple filter detection from object name
            obj = str(metadata.get('object', '')).upper()
            if 'LUM' in obj or 'L' in obj:
                metadata['filter'] = 'Lum'
            elif 'RED' in obj or 'R' in obj:
                metadata['filter'] = 'Red'
            elif 'GREEN' in obj or 'G' in obj:
                metadata['filter'] = 'Green'
            elif 'BLUE' in obj or 'B' in obj:
                metadata['filter'] = 'Blue'
            elif 'HA' in obj or 'H-ALPHA' in obj:
                metadata['filter'] = 'Ha'
            elif 'OIII' in obj:
                metadata['filter'] = 'OIII'
            elif 'SII' in obj:
                metadata['filter'] = 'SII'
        
        # Ensure exposure time is float
        if 'exptime' in metadata:
            try:
                metadata['exptime'] = float(metadata['exptime'])
            except (ValueError, TypeError):
                metadata['exptime'] = 0.0
        
        return metadata
    
    def _calculate_metrics(self, data: np.ndarray, metadata: Dict) -> Dict[str, Any]:
        """Calculate image quality metrics"""
        metrics = {}
        
        # 1. Basic statistics
        mean, median, std = sigma_clipped_stats(data, sigma=3.0)
        metrics['background_mean'] = float(mean)
        metrics['background_median'] = float(median)
        metrics['background_std'] = float(std)
        metrics['data_min'] = float(data.min())
        metrics['data_max'] = float(data.max())
        
        # 2. Detect stars using SEP (Source Extraction and Photometry)
        try:
            # Background subtraction for star detection
            bkg = sep.Background(data)
            data_sub = data - bkg
            
            # Detect sources (stars)
            sources = sep.extract(data_sub, thresh=2.0, minarea=5)
            
            if len(sources) > 0:
                metrics['star_count'] = int(len(sources))
                
                # 3. Calculate HFR (Half Flux Radius) - measure of star focus
                if 'flux' in sources.dtype.names and 'a' in sources.dtype.names:
                    # Sort by brightness
                    bright_sources = sources[sources['flux'] > np.percentile(sources['flux'], 50)]
                    if len(bright_sources) > 10:
                        # Use top 10% brightest stars for HFR calculation
                        bright_sources = bright_sources[bright_sources['flux'] > 
                                                       np.percentile(bright_sources['flux'], 90)]
                    
                    if len(bright_sources) > 0:
                        # Calculate average HFR
                        hfr_values = 1.5 * bright_sources['a']  # Approximation: HFR ≈ 1.5 * semimajor axis
                        metrics['hfr'] = float(np.median(hfr_values))
                        metrics['hfr_std'] = float(np.std(hfr_values))
                        
                        # Star shape metrics
                        metrics['star_eccentricity'] = float(np.mean(bright_sources['b'] / bright_sources['a']))
                    else:
                        metrics['hfr'] = 0.0
                        metrics['hfr_std'] = 0.0
                        metrics['star_eccentricity'] = 0.0
                else:
                    metrics['star_count'] = 0
                    metrics['hfr'] = 0.0
            else:
                metrics['star_count'] = 0
                metrics['hfr'] = 0.0
                
        except Exception as e:
            logger.warning(f"Star detection failed: {e}")
            metrics['star_count'] = 0
            metrics['hfr'] = 0.0
        
        # 4. Estimate SNR (Signal-to-Noise Ratio)
        try:
            # Simple SNR estimation: (peak signal - background) / noise
            if metrics['star_count'] > 0:
                # Use brightest star flux
                peak_flux = np.max(sources['flux']) if 'flux' in sources.dtype.names else 0
                snr = peak_flux / metrics['background_std'] if metrics['background_std'] > 0 else 0
                metrics['snr_estimate'] = float(snr)
            else:
                # Estimate from overall image statistics
                signal = metrics['data_max'] - metrics['background_median']
                metrics['snr_estimate'] = float(signal / metrics['background_std']) if metrics['background_std'] > 0 else 0
        except:
            metrics['snr_estimate'] = 0.0
        
        # 5. Image quality flags
        metrics['has_trailing'] = metrics.get('star_eccentricity', 0) < 0.7 if 'star_eccentricity' in metrics else False
        metrics['is_overexposed'] = metrics['data_max'] >= 0.9 * np.iinfo(data.dtype).max if data.dtype.kind in 'ui' else False
        metrics['is_underexposed'] = metrics['background_std'] < 10  # Very low noise suggests underexposure
        
        return metrics
    
    def get_suggestions(self, metadata: Dict, metrics: Dict) -> List[str]:
        """Generate suggestions based on metrics"""
        suggestions = []
        
        filter_type = metadata.get('filter', '').lower()
        exposure = metadata.get('exptime', 0)
        hfr = metrics.get('hfr', 0)
        snr = metrics.get('snr_estimate', 0)
        star_count = metrics.get('star_count', 0)
        
        # Focus suggestions
        if hfr > 4.0:
            suggestions.append("Poor focus detected - consider refocusing")
        elif hfr > 3.0:
            suggestions.append("Focus is acceptable but could be improved")
        
        # Exposure suggestions
        if filter_type in ['ha', 'oiii', 'sii']:  # Narrowband
            if exposure < 300 and snr < 10:
                suggestions.append("Consider increasing narrowband exposure to 300s+")
        else:  # Broadband (Lum, RGB)
            if exposure < 60 and snr < 15:
                suggestions.append("Consider increasing exposure time for better SNR")
            elif exposure > 300 and metrics.get('is_overexposed', False):
                suggestions.append("Exposure might be too long - stars are saturated")
        
        # Guiding/tracking suggestions
        if metrics.get('has_trailing', False):
            suggestions.append("Star trailing detected - check guiding/tracking")
        
        # Cloud/conditions suggestions
        if star_count < 10:
            suggestions.append("Very few stars detected - check for clouds or focus issues")
        
        # SNR suggestions
        if snr < 5:
            suggestions.append("Very low SNR - consider longer exposure or better conditions")
        elif snr > 20:
            suggestions.append("Excellent SNR - consider reducing exposure if stars are saturated")
        
        return suggestions

# Simple test function
def test_analyzer():
    """Test the analyzer with a dummy file or real FITS file"""
    analyzer = FitsAnalyzer()
    
    print("FITS Analyzer Test")
    print("=" * 50)
    
    # Check if we can create analyzer
    print("✓ Analyzer created successfully")
    print(f"✓ Astronomy libraries available: {HAS_ASTROPY}")
    
    # You can add a test with one of your FITS files later
    # Example:
    # result = analyzer.analyze_file(Path("/path/to/your/file.fits"))
    # print(result)

if __name__ == "__main__":
    test_analyzer()
