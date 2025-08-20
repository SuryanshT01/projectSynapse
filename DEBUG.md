# Project Synapse - Debug & Development Guide 🛠️

This guide contains practical debugging information, working configurations, and solutions to common issues encountered during development and deployment.

---

## 📋 Table of Contents

1. [Working Environment Variables](#working-environment-variables)
2. [Docker Commands (Tested)](#docker-commands-tested)
3. [Local Development Setup](#local-development-setup)
4. [Common Issues & Fixes](#common-issues--fixes)
5. [Performance Debugging](#performance-debugging)
6. [API Testing Commands](#api-testing-commands)
7. [Container Debugging](#container-debugging)

---

## 🔧 Working Environment Variables

### **Demo .env File (Project Root)**
```env
# Project Synapse - Unified Environment Configuration
# This file contains all environment variables for both frontend and backend

# =============================================================================
# FRONTEND CONFIGURATION
# =============================================================================

# Adobe PDF Embed API Client ID
# Get your client ID from: https://www.adobe.com/go/dcsdks_credentials
VITE_ADOBE_CLIENT_ID="296f789cf0a74034a5a751feea611ab1"

# Backend API URL
VITE_API_URL=http://localhost:8000

# =============================================================================
# BACKEND CONFIGURATION
# =============================================================================

# LLM Configuration
LLM_PROVIDER="gemini"
# For Gemini, you need to set up Google Application Credentials.
# For local dev, i have used an API key instead:
GOOGLE_API_KEY="AIzaSyBFxkwdiVV0pYxTjCvztqxTpNmLpTU-Klo"
GEMINI_MODEL="gemini-2.5-flash" 

# TTS (Text-to-Speech) Configuration
TTS_PROVIDER="azure"
AZURE_TTS_KEY="5bnemDkUQOsIXJRYusFCEKx2nhAAzLE1k7fNtwW3HxjZ6w6nvqV4JQQJ99BHACfhMk5XJ3w3AAAAACOGiAdH"
AZURE_TTS_ENDPOINT="https://surya-meinv28c-swedencentral.cognitiveservices.azure.com"
AZURE_TTS_DEPLOYMENT="tts"
AZURE_TTS_API_VERSION="2024-08-01-preview"
AZURE_TTS_VOICE="alloy"

# =============================================================================
# DEVELOPMENT NOTES
# =============================================================================
# This file is for local development. In production, these will be passed by the docker run command.
```

### **Frontend .env File (frontend/.env)**
```env
# Adobe PDF Embed API Client ID
VITE_ADOBE_CLIENT_ID="296f789cf0a74034a5a751feea611ab1"

# Backend API URL - Local Development
VITE_API_URL=http://localhost:8000

# Development Mode
NODE_ENV=development
```

---

## 🐳 Docker Commands (Tested)

### **1. Build Commands**
```bash
# Standard build (recommended)
docker build -t projectsynapse .

# Platform-specific build (for evaluation)
docker build --platform linux/amd64 -t projectsynapse .

# Build with no cache (if issues)
docker build --no-cache -t projectsynapse .

# Check build time
time docker build -t projectsynapse .
```

### **2. Run Commands (Working)**

#### **Basic Run (Local Development)**
```bash
docker run -d --name projectsynapse-container -p 8080:8080 projectsynapse
```

#### **With Environment Variables (Adobe Evaluation Format)**
```bash
docker run -d \
  --name projectsynapse-eval \
  -p 8080:8080 \
  -e ADOBE_EMBED_API_KEY="296f789cf0a74034a5a751feea611ab1" \
  -e LLM_PROVIDER="gemini" \
  -e GOOGLE_API_KEY="AIzaSyBFxkwdiVV0pYxTjCvztqxTpNmLpTU-Klo" \
  -e GEMINI_MODEL="gemini-2.5-flash" \
  -e TTS_PROVIDER="azure" \
  -e AZURE_TTS_KEY="5bnemDkUQOsIXJRYusFCEKx2nhAAzLE1k7fNtwW3HxjZ6w6nvqV4JQQJ99BHACfhMk5XJ3w3AAAAACOGiAdH" \
  -e AZURE_TTS_ENDPOINT="https://surya-meinv28c-swedencentral.cognitiveservices.azure.com" \
  projectsynapse
```

#### **With Credentials File Mount**
```bash
docker run -d \
  --name projectsynapse-creds \
  -p 8080:8080 \
  -v /path/to/credentials:/credentials \
  -e ADOBE_EMBED_API_KEY="296f789cf0a74034a5a751feea611ab1" \
  -e LLM_PROVIDER="gemini" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/credentials/service-account.json" \
  -e GEMINI_MODEL="gemini-2.5-flash" \
  -e TTS_PROVIDER="azure" \
  -e AZURE_TTS_KEY="your_key_here" \
  -e AZURE_TTS_ENDPOINT="your_endpoint_here" \
  projectsynapse
```

### **3. Container Management**
```bash
# Check running containers
docker ps

# View logs
docker logs projectsynapse-container

# Follow logs in real-time
docker logs -f projectsynapse-container

# Stop and remove
docker stop projectsynapse-container && docker rm projectsynapse-container

# Clean up all containers
docker stop $(docker ps -q) && docker rm $(docker ps -aq)

# Check container health
docker exec projectsynapse-container curl -f http://localhost:8080/api/health
```

---

## 💻 Local Development Setup

### **1. Backend Setup**
```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt')"

# Run development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **2. Frontend Setup**
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### **3. Testing the Setup**
```bash
# Test backend API
curl http://localhost:8000/api/health

# Test frontend access
curl http://localhost:5173

# Test API from frontend
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query_text": "test query"}'
```

---

## 🐛 Common Issues & Fixes

### **Issue 1: Docker Build Failures**

**Symptoms:**
- Build timeouts
- Package installation errors
- Out of disk space

**Solutions:**
```bash
# Clean Docker cache
docker system prune -a

# Increase Docker memory (Docker Desktop)
# Settings > Resources > Memory: 8GB+

# Use multi-core build
docker build --build-arg BUILDKIT_INLINE_CACHE=1 -t projectsynapse .

# Check disk space
df -h
```

### **Issue 2: Environment Variables Not Loading**

**Symptoms:**
- 500 Internal Server Error
- "API key not found" errors
- TTS/LLM not working

**Solutions:**
```bash
# Check if .env exists
ls -la .env

# Verify container environment
docker exec projectsynapse-container env | grep -E "(GOOGLE|AZURE|ADOBE)"

# Check entrypoint script execution
docker logs projectsynapse-container | grep "Environment variables"

# Rebuild with environment debug
docker exec projectsynapse-container cat /app/.env
```

**Fix: Entrypoint Script Issue**
If environment variables are empty, the entrypoint script might be overwriting them:
```bash
# Check entrypoint logs
docker logs projectsynapse-container | head -20

# Verify original .env preservation
docker exec projectsynapse-container cat /app/.env.original
```

### **Issue 3: Frontend Not Loading**

**Symptoms:**
- 404 errors for frontend routes
- Swagger docs showing instead of React app
- Static files not found

**Solutions:**
```bash
# Check static files are present
docker exec projectsynapse-container ls -la /app/frontend/dist/

# Verify SPA routing in main.py
docker exec projectsynapse-container grep -A 10 "serve_spa" /app/backend/main.py

# Test direct file access
curl http://localhost:8080/index.html
```

### **Issue 4: PDF Files Not Available**

**Symptoms:**
- "PDF not available for this section" errors
- Analysis failed messages
- Empty document library

**Solutions:**
```bash
# Check if data folder is included
docker exec projectsynapse-container ls -la /app/backend/data/

# Verify uploads directory
docker exec projectsynapse-container ls -la /app/backend/data/uploads/

# Check .dockerignore settings
cat .dockerignore | grep -E "(data|uploads)"

# Rebuild with data included
# Ensure .dockerignore allows backend/data/uploads/
```

### **Issue 5: API Timeout Issues**

**Symptoms:**
- Slow response times
- Gateway timeouts
- LLM/TTS request failures

**Solutions:**
```bash
# Check container resources
docker stats projectsynapse-container

# Increase timeout in nginx/proxy
# Add to docker run: --health-timeout=30s

# Test API endpoints individually
curl -w "%{time_total}" http://localhost:8080/api/health

# Check for memory issues
docker exec projectsynapse-container free -h
```

---

## 📊 Performance Debugging

### **Build Performance**
```bash
# Time the build process
time docker build -t projectsynapse .

# Analyze layer sizes
docker history projectsynapse --format "table {{.CreatedBy}}\t{{.Size}}"

# Check for layer caching
docker build --no-cache -t projectsynapse-nocache .
```

### **Runtime Performance**
```bash
# Monitor container resources
docker stats --no-stream

# Check application logs for performance
docker logs projectsynapse-container | grep -E "(INFO|WARNING|ERROR)"

# Test API response times
curl -o /dev/null -s -w "%{time_total}\n" http://localhost:8080/api/health
```

### **Memory Usage Analysis**
```bash
# Check Python memory usage
docker exec projectsynapse-container python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().used / 1024**3:.2f}GB')
print(f'Available: {psutil.virtual_memory().available / 1024**3:.2f}GB')
"

# Check FAISS index size
docker exec projectsynapse-container ls -lh /app/backend/data/index.faiss
```

---

## 🧪 API Testing Commands

### **Health Check**
```bash
curl -X GET http://localhost:8080/api/health
```

### **Document Upload Test**
```bash
# Upload a test PDF
curl -X POST http://localhost:8080/api/upload \
  -F "files=@test-document.pdf" \
  -H "Accept: application/json"
```

### **Search Query Test**
```bash
# Test semantic search
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "machine learning algorithms"
  }'
```

### **Insights Generation Test**
```bash
# Test AI insights
curl -X POST http://localhost:8080/api/insights \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "neural networks",
    "related_snippets": ["Deep learning is a subset of machine learning"]
  }'
```

### **Audio Podcast Test**
```bash
# Test TTS generation (this will take time)
curl -X POST http://localhost:8080/api/podcast \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "artificial intelligence",
    "related_snippets": ["AI is transforming industries"]
  }' \
  --max-time 60
```

---

## 🔍 Container Debugging

### **Access Container Shell**
```bash
# Get shell access
docker exec -it projectsynapse-container bash

# Check file permissions
docker exec projectsynapse-container ls -la /app/

# Check Python environment
docker exec projectsynapse-container python --version
docker exec projectsynapse-container pip list
```

### **Debugging Python Issues**
```bash
# Test Python imports
docker exec projectsynapse-container python -c "
import torch
import sentence_transformers
import faiss
print('All imports successful')
"

# Check NLTK data
docker exec projectsynapse-container python -c "
import nltk
print(nltk.data.path)
"

# Test FAISS functionality
docker exec projectsynapse-container python -c "
import faiss
print(f'FAISS version: {faiss.__version__}')
"
```

### **Network Debugging**
```bash
# Check port binding
netstat -tulpn | grep 8080

# Test internal connectivity
docker exec projectsynapse-container curl http://localhost:8080/api/health

# Check container network
docker network ls
docker inspect projectsynapse-container | grep NetworkMode
```

---

## 🚨 Emergency Fixes

### **Quick Container Reset**
```bash
#!/bin/bash
# emergency-reset.sh
echo "Stopping and removing containers..."
docker stop $(docker ps -q) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

echo "Rebuilding image..."
docker build --no-cache -t projectsynapse .

echo "Starting fresh container..."
docker run -d --name projectsynapse-fresh -p 8080:8080 projectsynapse

echo "Checking health..."
sleep 10
curl http://localhost:8080/api/health
```

### **Environment Debug Script**
```bash
#!/bin/bash
# debug-env.sh
echo "=== Environment Debug ==="
echo "Container status:"
docker ps | grep projectsynapse

echo "Environment variables:"
docker exec projectsynapse-container env | grep -E "(GOOGLE|AZURE|ADOBE|LLM|TTS)"

echo ".env file contents:"
docker exec projectsynapse-container cat /app/.env

echo "File permissions:"
docker exec projectsynapse-container ls -la /app/

echo "Application logs:"
docker logs projectsynapse-container --tail 20
```

---

## 📝 Development Notes

### **Working Configurations Tested:**
- ✅ Docker build time: ~13 minutes (with cache: ~30 seconds)
- ✅ Image size: ~3.57GB
- ✅ Container startup: ~15 seconds
- ✅ API response time: <1 second
- ✅ Frontend load time: <2 seconds
- ✅ Environment variables: All working
- ✅ PDF processing: Functional
- ✅ Audio generation: Working (2-5 minutes)

### **Environment Variables Priority:**
1. Docker environment variables (highest)
2. Original .env file values (fallback)
3. Default values in code (lowest)

### **Critical Files to Monitor:**
- `/app/.env` - Runtime environment
- `/app/backend/data/` - Document storage
- `/app/frontend/dist/` - Built frontend
- `/app/entrypoint.sh` - Startup script

---

## 🤝 Support

If you encounter issues not covered here:

1. **Check logs**: `docker logs container-name`
2. **Verify environment**: `docker exec container env`
3. **Test API endpoints**: Use curl commands above
4. **Check file permissions**: `docker exec container ls -la /app/`
5. **Rebuild clean**: `docker build --no-cache`

**Last Updated**: August 20, 2025  
**Tested On**: Docker Desktop, Linux x86_64, 16GB RAM
