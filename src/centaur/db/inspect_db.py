from __future__ import annotations

from centaur.db.session import get_session
from centaur.db.models import Rig, Frame


def list_rigs():
    """Return a list of all rigs in the DB."""
    with get_session() as session:
        return session.query(Rig).all()


def list_frames(limit: int = 20):
    """Return the most recent frames."""
    with get_session() as session:
        return (
            session.query(Frame)
            .order_by(Frame.id.desc())
            .limit(limit)
            .all()
        )


def frames_by_rig(rig_key: str, limit: int = 20):
    """Return frames for a specific rig."""
    with get_session() as session:
        return (
            session.query(Frame)
            .join(Rig)
            .filter(Rig.rig_key == rig_key)
            .order_by(Frame.id.desc())
            .limit(limit)
            .all()
        )


def summary():
    """Print a simple human-readable summary of the DB contents."""
    with get_session() as session:
        rig_count = session.query(Rig).count()
        frame_count = session.query(Frame).count()

        rigs = session.query(Rig).all()

        print("---- Centaur Parting DB Summary ----")
        print(f"Total rigs:   {rig_count}")
        print(f"Total frames: {frame_count}")

        for rig in rigs:
            frames = (
                session.query(Frame)
                .filter(Frame.rig_id == rig.id)
                .count()
            )
            print(f"  - {rig.rig_key}: {frames} frames")
        print("-------------------------------------")

