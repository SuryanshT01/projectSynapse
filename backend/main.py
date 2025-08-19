# backend/main.py
import logging
import os
from fastapi import FastAPI
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

@app.get("/")
def read_root():
    return {"message": "Welcome to Project Synapse Backend"}


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
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    logging.warning(
        "No static directory found. Skipping mount. "
        "Create backend/static or build frontend into frontend/dist to serve UI."
    )