# Dockerfile

# --- Stage 1: Build the React Frontend ---
    FROM node:18-alpine AS frontend-builder

    WORKDIR /app/frontend
    
    # Copy package files and install dependencies
    COPY frontend/package*.json ./
    RUN npm install
    
    # Copy the rest of the frontend source code
    COPY frontend/. ./
    
    # Build the production-ready static files
    RUN npm run build
    
    # --- Stage 2: Build the Python Backend and Final Image ---
    FROM python:3.10-slim
    
    WORKDIR /app
    
    # Set environment variables for Python
    ENV PYTHONDONTWRITEBYTECODE 1
    ENV PYTHONUNBUFFERED 1
    
    # Copy requirements from the backend folder
    COPY backend/requirements.txt .
    
    # Install Python dependencies
    RUN pip install --no-cache-dir --upgrade pip -r requirements.txt
    
    # Download NLTK data required for sentence tokenization
    RUN python -m nltk.downloader punkt
    
    # Copy the entire backend source code
    COPY backend ./backend
    
    # Copy the built frontend static files from the 'frontend-builder' stage
    # This is the key step to combine both parts.
    COPY --from=frontend-builder /app/frontend/dist ./backend/static
    
    # Expose the port the app will run on
    EXPOSE 8080
    
    # The command to run the Uvicorn server for the FastAPI app
    CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]