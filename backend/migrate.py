"""
Run Alembic migrations programmatically.

Usage:
    python migrate.py
"""

import subprocess
import sys


def main():
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=False,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
