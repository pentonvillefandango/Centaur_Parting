from __future__ import annotations

from pathlib import Path
from typing import Optional

from astropy.io import fits

from centaur.db.models import Frame, Rig
from centaur.db.session import get_session


# ---------------------------------------------------------------------
# Filter normalisation
# ---------------------------------------------------------------------
FILTER_MAP = {
    "ha": "Ha",
    "halpha": "Ha",
    "h-alpha": "Ha",
    "hα": "Ha",
    "ha7nm": "Ha",

    "oiii": "OIII",
    "o3": "OIII",

    "sii": "SII",
    "s2": "SII",

    "l": "L",
    "lum": "L",
    "luminance": "L",

    "r": "R",
    "red": "R",

    "g": "G",
    "green": "G",

    "b": "B",
    "blue": "B",
}


def normalise_filter(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    key = raw.lower().replace("-", "").replace("_", "")
    return FILTER_MAP.get(key, raw)


# ---------------------------------------------------------------------
# Rig helper
# ---------------------------------------------------------------------
def get_or_create_rig(rig_key: str, display_name: str | None = None) -> Rig:
    if display_name is None:
        display_name = rig_key

    with get_session() as session:
        rig = (
            session.query(Rig)
            .filter(Rig.rig_key == rig_key)
            .one_or_none()
        )

        if rig is None:
            rig = Rig(rig_key=rig_key, display_name=display_name)
            session.add(rig)
            session.flush()

        return rig


# ---------------------------------------------------------------------
# FITS ingestion
# ---------------------------------------------------------------------
def ingest_fits_header(fits_path: str, rig_key: str) -> None:
    """
    Read FITS header fields and create a Frame entry in the DB.
    """

    path = Path(fits_path).resolve()

    # 1) Read FITS header
    try:
        with fits.open(path) as hdul:
            hdr = hdul[0].header
    except Exception as e:
        print(f"[ingest] ERROR reading FITS: {path} -> {e}")
        return

    # Extract raw fields safely
    filter_raw = hdr.get("FILTER")
    filter_norm = normalise_filter(filter_raw)

    exposure = hdr.get("EXPTIME")
    frame_type = hdr.get("IMAGETYP")
    target = hdr.get("OBJECT")

    gain = hdr.get("GAIN")
    offset = hdr.get("OFFSET")

    temp = hdr.get("SENSORTEMP", hdr.get("CCD-TEMP"))
    binning = hdr.get("XBINNING", hdr.get("BINNING"))

    camera = hdr.get("INSTRUME") or hdr.get("CAMERA")
    telescope = hdr.get("TELESCOP")
    focal_length = hdr.get("FOCALLEN")
    pixel_size = hdr.get("PIXSIZE") or hdr.get("XPIXSZ")

    ra = hdr.get("RA")
    dec = hdr.get("DEC")

    # 2) Ensure the rig exists
    with get_session() as session:
        rig = (
            session.query(Rig)
            .filter(Rig.rig_key == rig_key)
            .one_or_none()
        )
        if rig is None:
            rig = Rig(rig_key=rig_key, display_name=rig_key)
            session.add(rig)
            session.flush()

        # 3) Avoid duplicate rows
        existing = (
            session.query(Frame)
            .filter(Frame.file_path == str(path))
            .one_or_none()
        )
        if existing:
            print(f"[ingest] Frame already exists for {path}")
            return

        # 4) Create Frame record
        frame = Frame(
            rig_id=rig.id,
            file_name=path.name,
            file_path=str(path),

            target_name=target,
            frame_type=frame_type,

            filter_raw=filter_raw,
            filter=filter_norm,

            exposure_s=exposure,
            binning=str(binning) if binning is not None else None,
            sensor_temp_c=temp,
            gain=gain,
            offset=offset,

            camera=camera,
            telescope=telescope,
            focal_length_mm=focal_length,
            pixel_size_um=pixel_size,

            ra_deg=float(ra) if ra else None,
            dec_deg=float(dec) if dec else None,

            raw_header_json=dict(hdr),
        )

        session.add(frame)

    print(f"[ingest] Ingested Frame: {path} (filter={filter_norm})")

