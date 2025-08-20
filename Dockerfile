# Optimized Dockerfile for Project Synapse - Adobe Hackathon 2025
# Multi-stage build optimized for CPU-only deployment

# --- Stage 1: Build the React Frontend ---
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files and install dependencies
COPY frontend/package*.json ./

# Copy the main project .env file to the parent directory (where Vite expects it)
COPY .env /app/.env

RUN npm ci

# Copy frontend source code
COPY frontend/. ./

# Update the API URL in the project root .env file for Docker deployment  
RUN sed -i 's|VITE_API_URL=.*|VITE_API_URL=http://localhost:8080|' /app/.env

# Ensure environment variables are available during build
RUN cat /app/.env

# Build the production-ready static files
RUN npm run build

# --- Stage 2: Python Dependencies Builder (CPU-Optimized) ---
FROM python:3.10-slim AS python-builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build dependencies for Python packages
    gcc \
    g++ \
    python3-dev \
    build-essential \
    # Required for some packages
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create pip configuration for better reliability and higher timeouts
RUN mkdir -p /etc/pip && \
    echo "[global]" > /etc/pip/pip.conf && \
    echo "timeout = 600" >> /etc/pip/pip.conf && \
    echo "retries = 5" >> /etc/pip/pip.conf && \
    echo "trusted-host = pypi.org files.pythonhosted.org pypi.python.org" >> /etc/pip/pip.conf

WORKDIR /app

# Copy Python requirements
COPY backend/requirements.txt ./backend/
COPY backend/requirements-core.txt ./backend/

# Upgrade pip first with extended timeout
RUN pip install --no-cache-dir --upgrade pip --timeout=300

# CRITICAL: Install PyTorch CPU-only FIRST to prevent CUDA downloads
# This is the key optimization that saves ~60 minutes of build time
# Using compatible versions with sentence-transformers
RUN pip install --no-cache-dir --timeout=600 --retries=5 \
    torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 \
    --index-url https://download.pytorch.org/whl/cpu

# Install NumPy and core scientific packages (sentence-transformers dependencies)
RUN pip install --no-cache-dir --timeout=300 --retries=5 \
    numpy==1.26.4 \
    scipy \
    scikit-learn==1.3.2

# Now install sentence-transformers - it will use the CPU-only PyTorch we just installed
RUN pip install --no-cache-dir --timeout=600 --retries=5 \
    sentence-transformers

# Install FAISS CPU (already optimized for CPU-only)
RUN pip install --no-cache-dir --timeout=300 --retries=3 \
    faiss-cpu

# Install core web framework packages
RUN pip install --no-cache-dir --timeout=300 --retries=3 \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    python-dotenv \
    pydantic-settings \
    requests \
    anyio

# Install LangChain packages (for AI functionality)
RUN pip install --no-cache-dir --timeout=600 --retries=5 \
    langchain==0.3.27 \
    langchain-google-genai==2.0.10 \
    langchain-openai==0.3.29 \
    langchain-community==0.3.27 \
    google-generativeai==0.8.5

# Install data processing packages (including the critical rank-bm25)
RUN pip install --no-cache-dir --timeout=300 --retries=3 \
    pandas==2.1.4 \
    joblib==1.3.2 \
    lightgbm==4.1.0 \
    rank-bm25==0.2.2

# Install PDF and document processing packages
RUN pip install --no-cache-dir --timeout=300 --retries=3 \
    PyMuPDF \
    pytesseract \
    nltk

# Install audio processing packages
RUN pip install --no-cache-dir --timeout=300 --retries=3 \
    pydub \
    azure-cognitiveservices-speech \
    google-cloud-texttospeech==2.27.0

# Download required NLTK data
RUN python -c "import nltk; nltk.download('punkt', download_dir='/usr/local/share/nltk_data')" && \
    python -c "import nltk; nltk.download('punkt_tab', download_dir='/usr/local/share/nltk_data')" || true

# --- Stage 3: Final Production Image (Runtime-only) ---
FROM python:3.10-slim AS production

# Install only runtime system dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PDF processing dependencies
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    # Audio processing dependencies
    ffmpeg \
    # Local TTS dependencies (fallback option)
    espeak-ng \
    # Utility tools
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
# CPU-specific optimizations for numpy/scipy
ENV OMP_NUM_THREADS=8
ENV MKL_NUM_THREADS=8
ENV OPENBLAS_NUM_THREADS=8
# Optimize for hackathon CPU environment (8 CPUs, 16GB RAM)
ENV NUMBA_NUM_THREADS=8

# Create application user for security
RUN useradd --create-home --shell /bin/bash app

# Create necessary directories with proper permissions
RUN mkdir -p /app/backend/data/temp_audio && \
    mkdir -p /app/backend/data/uploads && \
    mkdir -p /app/frontend/dist && \
    chown -R app:app /app

# Copy Python packages from builder stage (this includes all our optimized dependencies)
COPY --from=python-builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin
COPY --from=python-builder /usr/local/share/nltk_data /usr/local/share/nltk_data

# Copy the entire backend source code
COPY --chown=app:app backend/ ./backend/

# Copy the main project .env file to the app root (for backend access)
COPY --chown=app:app .env ./

# Copy the built frontend static files from the frontend-builder stage
COPY --from=frontend-builder --chown=app:app /app/frontend/dist ./frontend/dist

# Copy entrypoint script
COPY --chown=app:app entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Switch to application user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Expose port 8080 as required by hackathon guidelines
EXPOSE 8080

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]