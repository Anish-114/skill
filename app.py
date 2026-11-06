import spaces
import gradio as gr
import os
import sys
import uvicorn

@spaces.GPU
def check_gpu():
    return "GPU Active"

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

if "app" in sys.modules and not hasattr(sys.modules["app"], "__path__"):
    del sys.modules["app"]

from app.main import app as fastapi_app

with gr.Blocks(title="SkillBridge AI") as demo:
    gr.Markdown("# SkillBridge AI Backend & Frontend Active")
    btn = gr.Button("Ping GPU")
    lbl = gr.Label()
    btn.click(fn=check_gpu, outputs=lbl)

# Mount Gradio onto the primary FastAPI app
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
