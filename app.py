import os
import sys

# Ensure backend folder is the primary search path for internal 'app' imports
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Clear any cached collision of root app.py
if "app" in sys.modules and not hasattr(sys.modules["app"], "__path__"):
    del sys.modules["app"]

from app.main import app
import gradio as gr

demo = gr.mount_gradio_app(app, gr.Blocks(title="SkillBridge AI"), path="/gradio")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
