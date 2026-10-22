#!/usr/bin/env python3
"""Update an existing consumer to the latest published engineering-standards release."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
from update_standards import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
