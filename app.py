import spaces

@spaces.GPU(duration=10)
def predict():
    return "ready"

# Execute once at module load for static detection
try:
    predict()
except Exception:
    pass

import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

if "app" in sys.modules and not hasattr(sys.modules["app"], "__path__"):
    del sys.modules["app"]

from app.main import app as fastapi_app
import gradio as gr

with gr.Blocks(title="SkillBridge AI") as demo:
    btn = gr.Button("Status")
    out = gr.Textbox()
    btn.click(fn=predict, outputs=out)

app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")
