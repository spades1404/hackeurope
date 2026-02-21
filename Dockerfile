# Multi-stage build for backend + frontend

# ── Stage 1: Build Frontend ──────────────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Backend + Serve Frontend ────────────────────────
FROM python:3.12-slim
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/
COPY data/ ./data/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Create data directories
RUN mkdir -p /app/db /app/generated_docs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f http://localhost:8000/health || exit 1

# Start
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
