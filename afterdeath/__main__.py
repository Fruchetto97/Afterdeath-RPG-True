"""Entry point: ``python -m afterdeath`` (also used by the PyInstaller build)."""

import sys

from afterdeath import paths
from afterdeath.main_menu import main

if __name__ == "__main__":
    # The windowed .exe has no console: keep the game's log in the player's data folder
    if paths.IS_FROZEN and sys.stdout is None:
        log_file = open(paths.USER_DATA_DIR / "afterdeath.log", "w", encoding="utf-8", buffering=1)
        sys.stdout = sys.stderr = log_file
    main()
