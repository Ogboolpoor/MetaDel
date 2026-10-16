"""`python -m metadel` launches the GUI."""

import sys

from .app.main_window import main

if __name__ == "__main__":
    sys.exit(main())
