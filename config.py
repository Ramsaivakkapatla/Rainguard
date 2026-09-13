import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "rainguard.db"
)

APP_NAME = "RainGuard"

DEBUG = True