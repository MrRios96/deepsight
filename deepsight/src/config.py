from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

SQLITE_PATH = DATA_DIR / "relational" / "media.db"
CHROMA_PATH = DATA_DIR / "vector"

SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
CHROMA_PATH.mkdir(parents=True, exist_ok=True)