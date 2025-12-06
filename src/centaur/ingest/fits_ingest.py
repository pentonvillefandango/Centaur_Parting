from __future__ import annotations

from pathlib import Path

from centaur.db.models import Frame, Rig
from centaur.db.session import get_session


def get_or_create_rig(rig_key: str, display_name: str | None = None) -> Rig:
    """
    Look up a Rig by rig_key, or create it if it doesn't exist yet.

    For now we just store rig_key + display_name.
    """
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
            session.flush()  # assign rig.id

        return rig


def ingest_header_stub(fits_path: str, rig_key: str) -> None:
    """
    TEMPORARY STUB.

    This will eventually:
      - read the FITS header
      - normalise key fields (filter, exposure, etc.)
      - create a Frame row in the DB

    Right now it:
      - ensures the Rig exists
      - creates a Frame with just file_path and file_name
    """
    path = Path(fits_path).resolve()

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

        # Avoid duplicates
        existing = (
            session.query(Frame)
            .filter(Frame.file_path == str(path))
            .one_or_none()
        )
        if existing:
            print(f"[ingest_header_stub] Frame already exists for {path}")
            return

        frame = Frame(
            rig_id=rig.id,
            file_name=path.name,
            file_path=str(path),
        )
        session.add(frame)

    print(f"[ingest_header_stub] Ingested placeholder Frame for {path} under rig {rig_key}")

