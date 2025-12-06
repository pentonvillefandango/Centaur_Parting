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
    Boolean,
    # remove: datetime,
    # remove: relationship,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship, declarative_base

from centaur.db.session import Base

# ============================================================
# RIG
# ============================================================
class Rig(Base):
    __tablename__ = "rig"

    id = Column(Integer, primary_key=True)
    rig_key = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)

    created_at_utc = Column(DateTime, default=dt.datetime.utcnow)

    frames = relationship("Frame", back_populates="rig")


# ============================================================
# FRAME
# ============================================================
class Frame(Base):
    __tablename__ = "frame"

    id = Column(Integer, primary_key=True)
    rig_id = Column(Integer, ForeignKey("rig.id"), nullable=False)

    # path info
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)

    # FITS header metadata
    frame_type = Column(String, nullable=True)
    filter = Column(String, nullable=True)
    exposure_s = Column(Float, nullable=True)
    temperature_c = Column(Float, nullable=True)
    binning = Column(Integer, nullable=True)

    created_at_utc = Column(DateTime, default=dt.datetime.utcnow)
    fits_timestamp_utc = Column(DateTime, nullable=True)

    rig = relationship("Rig", back_populates="frames")
    analysis = relationship("Analysis", uselist=False, back_populates="frame")


# ============================================================
# ANALYSIS
# ============================================================
class Analysis(Base):
    __tablename__ = "analysis"

    frame_id = Column(Integer, ForeignKey("frame.id"), primary_key=True)

    # sky quality metrics
    sky_brightness_mag_per_arcsec2 = Column(Float, nullable=True)
    background_snr = Column(Float, nullable=True)
    faint_object_snr = Column(Float, nullable=True)

    # raw metrics
    median_adu = Column(Float, nullable=True)
    fwhm_px = Column(Float, nullable=True)
    eccentricity = Column(Float, nullable=True)
    star_count = Column(Integer, nullable=True)
    saturation_fraction = Column(Float, nullable=True)

    # classification
    noise_regime = Column(String, nullable=True)
    severity = Column(String, nullable=True)

    # recommended exposure
    recommended_exposure_s = Column(Float, nullable=True)
    recommendation_text = Column(Text, nullable=True)

    raw_analysis_json = Column(Text, nullable=True)

    created_at_utc = Column(DateTime, default=dt.datetime.utcnow)

    frame = relationship("Frame", back_populates="analysis")


# ============================================================
# OPTICAL PROFILE (learned thresholds)
# ============================================================
class OpticalProfile(Base):
    __tablename__ = "optical_profile"

    id = Column(Integer, primary_key=True)
    profile_key = Column(String, unique=True, nullable=False)

    scope = Column(String, nullable=True)
    camera = Column(String, nullable=True)
    optics = Column(String, nullable=True)

    # focal_length_mm comes from fits filename or user override
    focal_length_mm = Column(Float, nullable=True)

    created_at_utc = Column(DateTime, nullable=False, default=dt.datetime.utcnow)

    thresholds = relationship("ProfileThreshold", back_populates="profile")


# ============================================================
# THRESHOLDS PER METRIC
# ============================================================
class ProfileThreshold(Base):
    __tablename__ = "profile_threshold"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("optical_profile.id"), nullable=False)

    metric = Column(String, nullable=False)   # e.g. "fwhm_px", "eccentricity"
    warn_min = Column(Float, nullable=True)
    warn_max = Column(Float, nullable=True)
    crit_min = Column(Float, nullable=True)
    crit_max = Column(Float, nullable=True)

    created_at_utc = Column(DateTime, nullable=False, default=dt.datetime.utcnow)

    profile = relationship("OpticalProfile", back_populates="thresholds")

