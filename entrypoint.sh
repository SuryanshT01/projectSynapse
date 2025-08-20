#!/bin/bash

# entrypoint.sh - Runtime environment configuration for Project Synapse

set -e

echo "========================================="
echo "Project Synapse - Adobe Hackathon 2025"
echo "========================================="
echo "Configuring runtime environment..."

# Preserve original .env file and add runtime overrides
# Backup original .env if it exists
if [ -f "/app/.env" ]; then
    cp /app/.env /app/.env.original
fi

# Read original values from .env file if they exist
if [ -f "/app/.env.original" ]; then
    source /app/.env.original
fi

# Create runtime .env file with original values and Docker overrides
cat > /app/.env << ENVFILE
# Runtime environment configuration
ADOBE_EMBED_API_KEY=${ADOBE_EMBED_API_KEY:-${VITE_ADOBE_CLIENT_ID:-}}
LLM_PROVIDER=${LLM_PROVIDER:-gemini}
GOOGLE_API_KEY=${GOOGLE_API_KEY:-${GOOGLE_API_KEY:-}}
GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS:-}
GEMINI_MODEL=${GEMINI_MODEL:-gemini-2.5-flash}
TTS_PROVIDER=${TTS_PROVIDER:-azure}
AZURE_TTS_KEY=${AZURE_TTS_KEY:-${AZURE_TTS_KEY:-}}
AZURE_TTS_ENDPOINT=${AZURE_TTS_ENDPOINT:-${AZURE_TTS_ENDPOINT:-}}
AZURE_TTS_DEPLOYMENT=${AZURE_TTS_DEPLOYMENT:-tts}
AZURE_TTS_API_VERSION=${AZURE_TTS_API_VERSION:-2024-08-01-preview}
AZURE_TTS_VOICE=${AZURE_TTS_VOICE:-alloy}

# Frontend environment variables
VITE_ADOBE_CLIENT_ID=${ADOBE_EMBED_API_KEY:-${VITE_ADOBE_CLIENT_ID:-}}
VITE_API_URL=http://localhost:8080
ENVFILE

echo "Environment variables configured:"
echo "- LLM_PROVIDER: ${LLM_PROVIDER:-gemini}"
echo "- GEMINI_MODEL: ${GEMINI_MODEL:-gemini-2.5-flash}"
echo "- TTS_PROVIDER: ${TTS_PROVIDER:-local}"

# Fallback to local TTS if Azure credentials are not provided
if [ -z "${AZURE_TTS_KEY}" ] || [ -z "${AZURE_TTS_ENDPOINT}" ]; then
    echo "- Azure TTS credentials not provided, using local TTS"
    sed -i 's/TTS_PROVIDER=.*/TTS_PROVIDER=local/' /app/.env
else
    echo "- Azure TTS credentials provided"
fi

# Handle GOOGLE_APPLICATION_CREDENTIALS if provided
if [ -n "${GOOGLE_APPLICATION_CREDENTIALS}" ] && [ -f "${GOOGLE_APPLICATION_CREDENTIALS}" ]; then
    echo "- Google credentials file found at ${GOOGLE_APPLICATION_CREDENTIALS}"
elif [ -n "${GOOGLE_API_KEY}" ]; then
    echo "- Using Google API key for authentication"
else
    echo "- No Google credentials provided"
fi

# Ensure data directories exist with proper permissions
mkdir -p /app/backend/data/temp_audio
mkdir -p /app/backend/data/uploads
chmod -R 755 /app/backend/data

echo "========================================="
echo "Starting Project Synapse on port 8080..."
echo "Application will be available at:"
echo "http://localhost:8080"
echo "========================================="

# Start the application
exec uvicorn backend.main:app --host 0.0.0.0 --port 8080 --log-level info
