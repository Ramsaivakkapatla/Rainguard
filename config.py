import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Database configuration (environment variable with safe default)
DEFAULT_DB = BASE_DIR / "data" / "rainguard.db"
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", str(DEFAULT_DB)))

APP_NAME = "RainGuard"

# Environment and debug settings
FLASK_ENV = os.environ.get("FLASK_ENV", "production")
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "t")

# Session & Security
SECRET_KEY = os.environ.get("SECRET_KEY", "rainguard-dev-local-secret-change-in-prod")
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() in ("true", "1", "t")