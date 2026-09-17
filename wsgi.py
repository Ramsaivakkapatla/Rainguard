"""
WSGI entry point for RainGuard production server.
Used by Gunicorn, uWSGI, Waitress, and cloud platforms.
"""

import os
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    app.run(host=host, port=port)
