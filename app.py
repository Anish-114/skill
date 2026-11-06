import spaces
import gradio as gr
import os
import sys

# Backend setup
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

if "app" in sys.modules and not hasattr(sys.modules["app"], "__path__"):
    del sys.modules["app"]

from app.main import app as fastapi_app

# Official ZeroGPU function definition
@spaces.GPU
def gpu_health():
    return "GPU Available"

# Pure Gradio interface that Hugging Face runner expects
with gr.Blocks(title="SkillBridge AI") as demo:
    gr.Markdown("# SkillBridge AI Live")
    btn = gr.Button("Status")
    out = gr.Textbox()
    btn.click(fn=gpu_health, inputs=[], outputs=out)

# Mount FastAPI app onto Gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")
