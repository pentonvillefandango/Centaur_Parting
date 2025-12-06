from __future__ import annotations

from pathlib import Path
from typing import Iterable

from centaur.ingest.fits_ingest import ingest_fits_header


def find_fits_files(root: str | Path, recursive: bool = True) -> list[Path]:
    """
    Find FITS files under a root directory.

    If recursive=True, will walk all subdirectories.
    """
    root_path = Path(root).resolve()
    patterns = ("*.fits", "*.fit")
    files: list[Path] = []

    if recursive:
        for pattern in patterns:
            files.extend(root_path.rglob(pattern))
    else:
        for pattern in patterns:
            files.extend(root_path.glob(pattern))

    return sorted(files)


def bulk_ingest_directory(root: str | Path, rig_key: str, recursive: bool = True) -> None:
    """
    Ingest all FITS files under `root` for the given rig_key.
    Uses ingest_fits_header for each file, which will avoid duplicates.
    """
    root_path = Path(root).resolve()
    files = find_fits_files(root_path, recursive=recursive)

    if not files:
        print(f"[bulk_ingest] No FITS files found under {root_path}")
        return

    print(f"[bulk_ingest] Found {len(files)} FITS files under {root_path}")
    for i, f in enumerate(files, start=1):
        print(f"[bulk_ingest] ({i}/{len(files)}) {f}")
        ingest_fits_header(str(f), rig_key)

