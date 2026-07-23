"""Browse files under the data/ directory."""
import os
from typing import Optional, List

from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/data", tags=["data"])

DATA_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
)


def _list_dir(rel_path: str) -> List[dict]:
    """List files and directories under a given relative path.

    Returns items sorted: directories first, then files.
    """
    full_path = os.path.normpath(os.path.join(DATA_ROOT, rel_path))
    # Security: don't allow escaping data/
    if not full_path.startswith(os.path.normpath(DATA_ROOT)):
        return []

    if not os.path.isdir(full_path):
        return []

    items = []
    with os.scandir(full_path) as it:
        for entry in it:
            items.append({
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
                "path": os.path.join(rel_path, entry.name).replace("\\", "/"),
                "size": entry.stat().st_size if entry.is_file() else None,
            })

    # Directory first, then files, sorted alphabetically
    items.sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"]))
    return items


@router.get("/files")
async def list_data_files(path: str = Query(default="", description="Relative path under data/")):
    """List files and directories under the data/ directory."""
    normalized = path.lstrip("/").lstrip("\\")
    items = _list_dir(normalized)
    return {
        "path": normalized,
        "items": items,
    }
