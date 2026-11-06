import os
import sys
import gradio as gr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Prevent root app.py from shadowing backend.app for internal imports
import backend.app
sys.modules["app"] = backend.app

from backend.app.main import app

# Mount FastAPI app onto Gradio
demo = gr.mount_gradio_app(app, gr.Blocks(), path="/gradio")

# Ensure demo has launch() helper if returned as a FastAPI application
if not hasattr(demo, "launch"):
    def _launch(server_name="0.0.0.0", server_port=7860, prevent_thread_lock=False, **kwargs):
        import uvicorn
        uvicorn.run(demo, host=server_name, port=server_port)
    demo.launch = _launch

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    # Using demo.launch ensures Hugging Face's Gradio SDK keeps the web process permanently alive
    demo.launch(server_name="0.0.0.0", server_port=port, prevent_thread_lock=False)
