"""Run the application smoke workflows from source."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from photostudio.smoke import main
if __name__ == "__main__":
    raise SystemExit(main())
