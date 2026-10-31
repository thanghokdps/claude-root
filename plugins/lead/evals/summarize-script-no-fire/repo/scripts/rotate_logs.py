"""Compress logs older than 7 days and delete archives older than 30 days."""
import gzip
import shutil
import sys
import time
from pathlib import Path

DAY = 86400


def rotate(log_dir):
    now = time.time()
    for path in Path(log_dir).glob("*.log"):
        if now - path.stat().st_mtime > 7 * DAY:
            with path.open("rb") as src, gzip.open(f"{path}.gz", "wb") as dst:
                shutil.copyfileobj(src, dst)
            path.unlink()
    for archive in Path(log_dir).glob("*.log.gz"):
        if now - archive.stat().st_mtime > 30 * DAY:
            archive.unlink()


if __name__ == "__main__":
    rotate(sys.argv[1] if len(sys.argv) > 1 else "logs")
