# backend/main.py
import logging
import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import router as api_router
from backend.app.core.search import load_search_engine

load_dotenv()


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="Project Synapse API")

# Add CORS middleware to allow frontend to communicate with the backend
# This is crucial for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    """
    On application startup, load the ML model and search index.
    """
    logging.info("Application starting up...")
    load_search_engine()
    logging.info("Search engine loaded successfully.")

app.include_router(api_router, prefix="/api")


# Mount the static files directory where the React build output will be placed.
# The 'html=True' argument makes it serve index.html for the root path.
# This MUST come AFTER the API router to ensure '/api' routes are not overwritten.
# Determine candidate static dirs (dev vs build)
cwd = os.getcwd()
candidates = [
    os.path.join(cwd, "backend", "static"),   # runtime expected path
    os.path.join(cwd, "frontend", "dist"),    # if you build frontend locally
    os.path.join(cwd, "frontend", "build"),   # alternate build folder
]

static_dir = next((p for p in candidates if os.path.isdir(p)), None)
if static_dir:
    logging.info(f"Mounting static files from: {static_dir}")
    
    # Custom handler for SPA routing - serve index.html for non-API routes
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        from fastapi.responses import FileResponse
        import os
        
        # If it's an API route, let FastAPI handle it normally
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        
        # For static assets (CSS, JS, images), serve them directly
        if "." in path:  # Files with extensions
            file_path = os.path.join(static_dir, path)
            if os.path.exists(file_path):
                return FileResponse(file_path)
            raise HTTPException(status_code=404, detail="Not Found")
        
        # For all other routes (SPA routes), serve index.html
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend not found")
    
else:
    logging.warning(
        "No static directory found. Skipping mount. "
        "Create backend/static or build frontend into frontend/dist to serve UI."
    )