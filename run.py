"""Convenience launcher: `python run.py` opens the MetaDel window."""

import sys

from metadel.app.main_window import main

if __name__ == "__main__":
    sys.exit(main())
