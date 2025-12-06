from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from centaur.db.models import Analysis, Frame, Rig
from centaur.db.session import get_session


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

# Project root: same idea as in db/session.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXPORT_ROOT = PROJECT_ROOT / "Centaur_Analysis"


def ensure_export_root() -> Path:
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    return EXPORT_ROOT


# ---------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------

def _datetime_to_iso(dt_obj: Optional[datetime]) -> Optional[str]:
    if dt_obj is None:
        return None
    return dt_obj.isoformat()


def frame_to_dict(frame: Frame) -> dict:
    """
    Convert a Frame (and its Analysis, if present) to a JSON-serialisable dict.
    """
    rig_key = frame.rig.rig_key if frame.rig is not None else None

    base = {
        "id": frame.id,
        "rig_key": rig_key,
        "file_name": frame.file_name,
        "file_path": frame.file_path,
        "target_name": frame.target_name,
        "frame_type": frame.frame_type,
        "filter_raw": frame.filter_raw,
        "filter": frame.filter,
        "exposure_s": frame.exposure_s,
        "binning": frame.binning,
        "sensor_temp_c": frame.sensor_temp_c,
        "gain": frame.gain,
        "offset": frame.offset,
        "camera": frame.camera,
        "telescope": frame.telescope,
        "focal_length_mm": frame.focal_length_mm,
        "pixel_size_um": frame.pixel_size_um,
        "ra_deg": frame.ra_deg,
        "dec_deg": frame.dec_deg,
        "captured_at_utc": _datetime_to_iso(frame.captured_at_utc),
        "created_at_utc": _datetime_to_iso(frame.created_at_utc),
        "raw_header": frame.raw_header_json,
    }

    if frame.analysis is not None:
        a = frame.analysis
        base["analysis"] = {
            "severity": a.severity,
            "recommended_exposure_s": a.recommended_exposure_s,
            "recommendation_text": a.recommendation_text,
            "sky_brightness_mag_per_arcsec2": a.sky_brightness_mag_per_arcsec2,
            "background_snr": a.background_snr,
            "faint_object_snr": a.faint_object_snr,
            "median_adu": a.median_adu,
            "fwhm_px": a.fwhm_px,
            "eccentricity": a.eccentricity,
            "star_count": a.star_count,
            "saturation_fraction": a.saturation_fraction,
            "noise_regime": a.noise_regime,
            "raw_analysis": a.raw_analysis_json,
            "created_at_utc": _datetime_to_iso(a.created_at_utc),
        }
    else:
        base["analysis"] = None

    return base


# ---------------------------------------------------------------------
# Core export functions
# ---------------------------------------------------------------------

def export_frames_to_json(
    frames_data: list[dict],
    out_path: str | Path,
) -> Path:
    """
    Write already-serialised frame dicts to a JSON file.

    frames_data should be a list of dicts, e.g. [frame_to_dict(f) for f in frames].
    """
    ensure_export_root()

    out_path = Path(out_path)
    if not out_path.is_absolute():
        out_path = EXPORT_ROOT / out_path

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(frames_data, f, indent=2)

    print(f"[export] Wrote {len(frames_data)} frames to {out_path}")
    return out_path
    print(f"[export] Wrote {len(frames_list)} frames to {out_path}")
    return out_path


def export_frames_for_rig(
    rig_key: str,
    limit: Optional[int] = None,
    out_filename: Optional[str] = None,
) -> Path:
    """
    Export frames for a specific rig to JSON.

    If out_filename is not provided, a sensible default is used, e.g.:
        Centaur_Analysis/HeartRig_frames.json
    """
    ensure_export_root()

    if out_filename is None:
        out_filename = f"{rig_key}_frames.json"

    from sqlalchemy.orm import joinedload

    with get_session() as session:
        query = (
            session.query(Frame)
            .join(Rig)
            .options(
                joinedload(Frame.rig),
                joinedload(Frame.analysis),
            )
            .filter(Rig.rig_key == rig_key)
            .order_by(Frame.id.asc())
        )
        if limit is not None:
            query = query.limit(limit)

        frames = query.all()
        frames_data = [frame_to_dict(f) for f in frames]

    return export_frames_to_json(frames_data, out_filename)

def export_frames_for_target(
    target_name: str,
    limit: Optional[int] = None,
    out_filename: Optional[str] = None,
) -> Path:
    """
    Export frames for a specific target (OBJECT header) to JSON.
    """
    ensure_export_root()

    safe_target = target_name.replace(" ", "_")
    if out_filename is None:
        out_filename = f"target_{safe_target}_frames.json"

    from sqlalchemy.orm import joinedload

    with get_session() as session:
        query = (
            session.query(Frame)
            .options(
                joinedload(Frame.rig),
                joinedload(Frame.analysis),
            )
            .filter(Frame.target_name == target_name)
            .order_by(Frame.id.asc())
        )
        if limit is not None:
            query = query.limit(limit)

        frames = query.all()
        frames_data = [frame_to_dict(f) for f in frames]

    return export_frames_to_json(frames_data, out_filename)

# ---------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export Centaur Parting frames and analysis to JSON in Centaur_Analysis/."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--rig",
        dest="rig_key",
        help="Rig key to export frames for (e.g. HeartRig).",
    )
    group.add_argument(
        "--target",
        dest="target_name",
        help="Target name (OBJECT) to export frames for.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of frames to export.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Optional output JSON filename (relative to Centaur_Analysis/).",
    )

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.rig_key:
        export_frames_for_rig(
            rig_key=args.rig_key,
            limit=args.limit,
            out_filename=args.out,
        )
    elif args.target_name:
        export_frames_for_target(
            target_name=args.target_name,
            limit=args.limit,
            out_filename=args.out,
        )
    else:
        parser.error("You must provide either --rig or --target")


if __name__ == "__main__":
    main()

