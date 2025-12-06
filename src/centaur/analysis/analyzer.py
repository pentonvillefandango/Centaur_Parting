from __future__ import annotations

import numpy as np
from pathlib import Path
from astropy.io import fits
from datetime import datetime
from typing import Optional

from centaur.db.session import get_session
from centaur.db.models import Frame, Analysis


# ---------------------------------------------------------------------
# Basic pixel metrics (Phase 1)
# ---------------------------------------------------------------------

def analyze_frame_pixels(img: np.ndarray) -> dict:
    """
    Compute basic statistics from a 2D image.

    This is Phase 1 of the analyzer — simple metrics that are fast and safe.
    Later we will add FWHM, star detection, eccentricity, etc.
    """
    # Ensure float
    img = img.astype(np.float32)

    # Basic statistics
    median_adu = float(np.median(img))
    mean_adu = float(np.mean(img))
    std_adu = float(np.std(img))

    # Saturation fraction (how many pixels are near max 16-bit value)
    # You can tune this threshold later.
    max_val = np.max(img)
    saturation_level = 0.99 * max_val
    saturated_pixels = np.sum(img >= saturation_level)
    total_pixels = img.size
    saturation_fraction = float(saturated_pixels / total_pixels)

    # Placeholder star count — we add real detection in Phase 2
    star_count = None

    return {
        "median_adu": median_adu,
        "mean_adu": mean_adu,
        "std_adu": std_adu,
        "saturation_fraction": saturation_fraction,
        "star_count": star_count,
    }


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
        analysis.fwhm_px = None         # Phase 2
        analysis.eccentricity = None    # Phase 2
        analysis.star_count = metrics["star_count"]
        analysis.saturation_fraction = metrics["saturation_fraction"]
        analysis.noise_regime = None
        analysis.raw_analysis_json = metrics
        # We could add an updated_at_utc later if we want to track re-runs.

        session.commit()
        session.refresh(analysis)

        print(f"[analysis] Stored Analysis for Frame {frame_id}: median={metrics['median_adu']:.2f}")
        return analysis

