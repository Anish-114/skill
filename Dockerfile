# ==========================================
# Stage 1: Build Modern React Frontend
# ==========================================
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Copy dependency manifests
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm install

# Copy frontend source code
COPY frontend/ ./

# Build static production assets
RUN npm run build

# ==========================================
# Stage 2: Production Backend & Serving
# ==========================================
FROM python:3.11-slim

# Prevent interactive prompts and Python output buffering
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
    PORT=7860

# Install essential system build tools and runtime utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set up non-root user required by Hugging Face Spaces (UID 1000)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /app

# Install Python backend dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Pre-cache Sentence-Transformers embedding model into image layer
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy backend application source
COPY backend/ /app/backend/

# Copy compiled frontend SPA assets from Stage 1 into backend static directory
COPY --from=frontend-builder /app/frontend/dist /app/backend/app/static

# Initialize database schema and pre-populate verified seed opportunities
WORKDIR /app/backend
RUN python -m app.db.init_db

# Ensure runtime user has full read/write permissions to /app and database file
RUN chown -R user:user /app && \
    chmod -R 775 /app

# Switch to Hugging Face non-root user
USER user

# Hugging Face Spaces default port
EXPOSE 7860

# Launch Uvicorn production server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
