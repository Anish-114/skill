import spaces

@spaces.GPU
def check_gpu():
    return "ZeroGPU engine is active and ready."

import os
import sys
from pathlib import Path

# Setup backend directory on sys.path
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Clear any single-file shadowing of 'app'
if "app" in sys.modules and not hasattr(sys.modules["app"], "__path__"):
    del sys.modules["app"]

from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import gradio as gr
import uvicorn

from app.main import app
from app.api.v1 import api_v1_router

# Existing API routers under /api (as well as /api/v1)
app.include_router(api_v1_router, prefix="/api")

# Gradio Blocks demo directly referencing the @spaces.GPU function
with gr.Blocks(title="SkillBridge AI") as demo:
    gr.Markdown("# SkillBridge AI Platform")
    status_btn = gr.Button("Check GPU Status")
    status_output = gr.Textbox(label="Status")
    status_btn.click(fn=check_gpu, inputs=[], outputs=status_output)

# Mount Gradio app onto FastAPI
app = gr.mount_gradio_app(app, demo, path="/gradio")

# Serve React build from backend/app/static computed from Path(__file__)
static_dir = Path(__file__).resolve().parent / "backend" / "app" / "static"
index_html = static_dir / "index.html"
assets_dir = static_dir / "assets"

if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

@app.get("/", include_in_schema=False)
def serve_spa_root():
    if index_html.exists():
        return FileResponse(str(index_html))
    return {"message": "SkillBridge AI API & Gradio Active", "docs": "/docs", "gradio": "/gradio"}

# SPA fallback registered last (excluding /api and /gradio)
@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa_fallback(full_path: str):
    if (
        full_path.startswith("api/")
        or full_path.startswith("gradio/")
        or full_path in ["health", "docs", "openapi.json", "redoc"]
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource Not Found")

    file_path = static_dir / full_path
    if file_path.is_file():
        return FileResponse(str(file_path))

    if index_html.exists():
        return FileResponse(str(index_html))

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page Not Found")

if __name__ == "__main__":
    # launch() call nahi hota, isliye spaces ka startup hook fire nahi hota.
    # Wahi startup report yahan manually bhej rahe hain (sirf ZeroGPU par ye function hota hai).
    import spaces.zero as _zero
    if hasattr(_zero, "startup"):
        _zero.startup()

    uvicorn.run(app, host="0.0.0.0", port=7860)
