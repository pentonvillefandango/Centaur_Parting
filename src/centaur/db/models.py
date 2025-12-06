from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from centaur.db.session import Base


class Rig(Base):
    """
    A logical data source (watched share / folder).

    IMPORTANT:
    - A Rig is *not* the telescope+camera combination.
    - A single rig (share) may contain data from multiple scopes/cameras.
    - Camera/scope etc. are stored per Frame (from the FITS header).
    """

    __tablename__ = "rigs"

    id = Column(Integer, primary_key=True)
    rig_key = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)

    # Optional notes for humans (e.g. "Rig24 imaging SSD on MacBook")
    notes = Column(Text)

    frames = relationship("Frame", back_populates="rig")

    def __repr__(self) -> str:
        return f"<Rig rig_key={self.rig_key!r}>"


class Frame(Base):
    """
    One FITS file on disk + header-level information.

    - 'filter_raw' is exactly what was in the FITS header.
    - 'filter' is the normalised filter key we will use in queries/GUI.
    - The full header is preserved in raw_header_json so new metrics
      can be derived later without re-reading the FITS file.
    """

    __tablename__ = "frames"

    id = Column(Integer, primary_key=True)

    rig_id = Column(Integer, ForeignKey("rigs.id"), nullable=False, index=True)
    rig = relationship("Rig", back_populates="frames")

    # File identity
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False, unique=True)

    # Basic header-derived metadata
    target_name = Column(String(200), index=True)
    frame_type = Column(String(50), index=True)  # LIGHT, FLAT, DARK, etc.

    # Filter handling
    filter_raw = Column(String(200))             # as in FITS header
    filter = Column(String(100), index=True)     # normalised key: Ha, OIII, L, R, G, B, etc.

    exposure_s = Column(Float)
    binning = Column(String(20))
    sensor_temp_c = Column(Float)
    gain = Column(Float)
    offset = Column(Float)

    # Optional telescope / camera metadata (from header if present)
    camera = Column(String(200))
    telescope = Column(String(200))
    focal_length_mm = Column(Float)
    pixel_size_um = Column(Float)

    ra_deg = Column(Float)
    dec_deg = Column(Float)

    # When the exposure happened (if we can infer), otherwise when ingested
    captured_at_utc = Column(DateTime, index=True)
    created_at_utc = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    # Complete FITS header as JSON for future use
    raw_header_json = Column(JSON)

    # One-to-one relationship with Analysis (metrics)
    analysis = relationship(
        "Analysis",
        back_populates="frame",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Frame id={self.id} file_name={self.file_name!r}>"


class Analysis(Base):
    """
    Derived metrics from the image data (cp-astrowatcher-style),
    plus severity and recommendations.

    Most frequently-used metrics are individual columns to make
    querying and plotting easy, but the full analysis dict is
    also stored in raw_analysis_json for flexibility.
    """

    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True)

    frame_id = Column(Integer, ForeignKey("frames.id"), unique=True, index=True)
    frame = relationship("Frame", back_populates="analysis")

    # Metrics
    sky_brightness_mag_per_arcsec2 = Column(Float)
    background_snr = Column(Float)
    faint_object_snr = Column(Float)
    median_adu = Column(Float)
    fwhm_px = Column(Float)
    eccentricity = Column(Float)
    star_count = Column(Integer)
    saturation_fraction = Column(Float)
    noise_regime = Column(String(100))

    # Recommendations / status
    severity = Column(String(20), index=True)  # OK, WARN, CRITICAL
    recommended_exposure_s = Column(Float)
    recommendation_text = Column(Text)

    # Full analysis dict (everything the analyzer computed)
    raw_analysis_json = Column(JSON)

    created_at_utc = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Analysis frame_id={self.frame_id} severity={self.severity!r}>"
