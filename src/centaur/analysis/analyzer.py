from __future__ import annotations

import numpy as np
from pathlib import Path
from astropy.io import fits
from datetime import datetime
from typing import Optional

from centaur.db.session import get_session
from centaur.db.models import Frame, Analysis

try:
    import sep  # type: ignore[import]
except ImportError:  # graceful degrade if not installed
    sep = None


# ---------------------------------------------------------------------
# Basic pixel metrics (Phase 1)
# ---------------------------------------------------------------------

def compute_star_metrics(img: np.ndarray) -> dict:
    """
    Use SEP to detect stars and derive:
      - star_count
      - typical FWHM in pixels
      - typical eccentricity (0 = round, >0 more elongated)

    Returns dict with keys: star_count, fwhm_px, eccentricity.
    Any value may be None if SEP is not available or detection fails.
    """
    if sep is None:
        # Library not installed; we keep the system working without star metrics.
        return {
            "star_count": None,
            "fwhm_px": None,
            "eccentricity": None,
        }

    # Ensure float32 and C-contiguous for SEP
    data = np.ascontiguousarray(img.astype(np.float32))

    # Estimate and subtract background
    bkg = sep.Background(data)
    data_sub = data - bkg

    # Detection threshold: 3-sigma above background RMS (tunable later)
    thresh = 3.0 * bkg.globalrms

    try:
        objects, _ = sep.extract(
            data_sub,
            thresh,
            err=bkg.globalrms,
            minarea=5,   # minimum number of connected pixels
        )
    except Exception:
        # If SEP chokes on something weird, fail gracefully
        return {
            "star_count": None,
            "fwhm_px": None,
            "eccentricity": None,
        }

    if objects is None or len(objects) == 0:
        return {
            "star_count": 0,
            "fwhm_px": None,
            "eccentricity": None,
        }

    star_count = int(len(objects))

    # a, b are semi-major / semi-minor axes, in pixels
    a = objects["a"]
    b = objects["b"]

    # Guard against weird zero/negative values
    valid = (a > 0) & (b > 0)
    if not np.any(valid):
        return {
            "star_count": star_count,
            "fwhm_px": None,
            "eccentricity": None,
        }

    a = a[valid]
    b = b[valid]

    # Approximate FWHM from second moments:
    # FWHM ~ 2.3548 * sqrt(a * b)
    fwhm_est = 2.3548 * np.sqrt(a * b)
    # Robust typical FWHM: median
    fwhm_px = float(np.median(fwhm_est))

    # Eccentricity: e = sqrt(1 - (b/a)^2), ensure a >= b
    major = np.maximum(a, b)
    minor = np.minimum(a, b)
    ecc = np.sqrt(1.0 - (minor / major) ** 2)
    eccentricity = float(np.median(ecc))

    return {
        "star_count": star_count,
        "fwhm_px": fwhm_px,
        "eccentricity": eccentricity,
    }




def analyze_frame_pixels(img: np.ndarray) -> dict:
    """
    Compute statistics from a 2D image.

    Phase 1: median/mean/std/saturation.
    Phase 2: star metrics (count, FWHM, eccentricity) via SEP.
    """
    # Ensure float
    img = img.astype(np.float32)

    # Basic statistics
    median_adu = float(np.median(img))
    mean_adu = float(np.mean(img))
    std_adu = float(np.std(img))

    # Saturation fraction (how many pixels are near max value)
    max_val = np.max(img)
    saturation_level = 0.99 * max_val if max_val > 0 else max_val
    saturated_pixels = np.sum(img >= saturation_level) if max_val > 0 else 0
    total_pixels = img.size if img.size > 0 else 1
    saturation_fraction = float(saturated_pixels / total_pixels)

    # Star metrics (may return None values if SEP missing or fails)
    star_metrics = compute_star_metrics(img)

    metrics = {
        "median_adu": median_adu,
        "mean_adu": mean_adu,
        "std_adu": std_adu,
        "saturation_fraction": saturation_fraction,
        "star_count": star_metrics["star_count"],
        "fwhm_px": star_metrics["fwhm_px"],
        "eccentricity": star_metrics["eccentricity"],
    }

    return metrics

# ---------------------------------------------------------------------
# FITS-level analyzer (Phase 1)
# ---------------------------------------------------------------------

def analyze_fits_file(path: str | Path) -> dict:
    """
    Load a FITS file, extract the primary image, and compute metrics.
    """
    path = Path(path)
    with fits.open(path) as hdul:
        img = hdul[0].data
        if img is None:
            raise ValueError(f"No pixel data found in FITS file: {path}")

        # 2D only — later we can handle RGB or multi-extension FITS
        if img.ndim != 2:
            raise ValueError(f"Expected 2D image data, got shape {img.shape}")

        metrics = analyze_frame_pixels(img)

    return metrics


# ---------------------------------------------------------------------
# Store analysis in DB
# ---------------------------------------------------------------------

def store_analysis_for_frame(frame_id: int) -> Analysis:
    """
    Load a Frame from DB, analyze its FITS file, and create or update its Analysis row.

    - If an Analysis already exists for this frame_id, it is updated.
    - If none exists, a new Analysis row is created.
    """
    with get_session() as session:
        frame: Frame = session.query(Frame).filter(Frame.id == frame_id).one()

        metrics = analyze_fits_file(frame.file_path)

        # Check for existing Analysis row for this frame
        analysis: Optional[Analysis] = (
            session.query(Analysis)
            .filter(Analysis.frame_id == frame.id)
            .one_or_none()
        )

        if analysis is None:
            analysis = Analysis(
                frame_id=frame.id,
                created_at_utc=datetime.utcnow(),
            )
            session.add(analysis)

        # Update common fields (these may change if we re-run analysis)
        analysis.severity = "OK"  # placeholder — real severity engine later
        analysis.recommended_exposure_s = None
        analysis.recommendation_text = None
        analysis.sky_brightness_mag_per_arcsec2 = None
        analysis.background_snr = None
        analysis.faint_object_snr = None
        analysis.median_adu = metrics["median_adu"]
        analysis.fwhm_px = metrics.get("fwhm_px")
        analysis.eccentricity = metrics.get("eccentricity")
        analysis.star_count = metrics.get("star_count")
        analysis.saturation_fraction = metrics["saturation_fraction"]
        analysis.noise_regime = None
        analysis.raw_analysis_json = metrics
        # We could add an updated_at_utc later if we want to track re-runs.

        session.commit()
        session.refresh(analysis)

        print(f"[analysis] Stored Analysis for Frame {frame_id}: median={metrics['median_adu']:.2f}")
        return analysis

