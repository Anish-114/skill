import spaces

@spaces.GPU
def _init_hf_gpu():
    return True

import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

if "app" in sys.modules and not hasattr(sys.modules["app"], "__path__"):
    del sys.modules["app"]

from app.main import app as fastapi_app
import gradio as gr

demo = gr.Blocks()
with demo:
    gr.Markdown("# SkillBridge AI Live")

app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")
