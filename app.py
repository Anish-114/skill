import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Prevent root app.py from shadowing backend.app for internal imports
import backend.app
sys.modules["app"] = backend.app

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    # Pass app as import string so uvicorn manages its lifecycle and event loops cleanly
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
    )
