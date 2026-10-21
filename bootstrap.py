#!/usr/bin/env python3
"""Bootstrap a repository with shared engineering guidance and optional library tooling."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
from bootstrap_repository import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
