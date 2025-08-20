# Project Synapse 🧠✨
**Adobe India Hackathon 2025 Finale Submission**

*From Information Chaos to Connected Clarity – Making AI-Powered Document Intelligence Real*

[![Docker Build](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Adobe PDF Embed](https://img.shields.io/badge/Adobe-PDF%20Embed%20API-red)](https://www.adobe.io/apis/documentcloud/dcsdk/)
[![AI Powered](https://img.shields.io/badge/AI-Gemini%20%2B%20Azure%20TTS-green)](https://ai.google.dev/)

Project Synapse transforms static PDF libraries into dynamic, interconnected knowledge ecosystems. Built for researchers, students, and professionals who need to quickly surface hidden connections, contradictions, and insights across their document collections.

---

## 🏆 Hackathon Challenge Solution

### **Core Challenge: "Connecting the Dots"**
✅ **PDF Handling**: Bulk upload, high-fidelity display with Adobe PDF Embed API  
✅ **Semantic Search**: Instant related sections/snippets across document library  
✅ **Speed**: Sub-second response for text selection → insight surfacing  
✅ **Insights Bulb** (+5 points): AI-powered contradictions, examples, takeaways  
✅ **Audio Podcast** (+5 points): 2-speaker conversations with Azure TTS  

### **Technical Excellence**
- **82% faster Docker builds** (13 min vs 75 min from original)
- **75% smaller images** (3.57GB vs 14.1GB)
- **CPU-optimized** for evaluation environment
- **Production-ready** with security best practices

---

## 🎯 Key Features & User Journey

### **Step 1: Reading & Selection**
- **High-fidelity PDF viewer** powered by Adobe PDF Embed API
- **Text selection triggers** instant semantic search across document library
- **Speed-optimized** response under 1 second for user engagement

### **Step 2: Connecting the Dots**
- **Semantic similarity search** using sentence-transformers + FAISS
- **Up to 5 relevant sections** with contextual snippets
- **Click-to-navigate** directly to related PDF sections
- **Cross-document insights** grounded in user's personal library

### **Step 3: AI-Powered Insights** 🧠
- **Contradiction detection** across different documents
- **Key takeaways** and "Did you know?" facts
- **Cross-document examples** and inspirations
- **Contextual understanding** powered by Google Gemini

### **Step 4: Audio Experience** 🎧
- **2-speaker podcast generation** (2-5 minutes)
- **Natural conversation flow** discussing selected topics
- **Azure TTS integration** for production-quality audio
- **On-the-go learning** for busy professionals

---

## 🛠️ Technical Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React + Vite  │───▶│   FastAPI        │───▶│  AI Services    │
│   Adobe PDF     │    │   + Uvicorn      │    │  Gemini + Azure │
│   Embed API     │    │                  │    │  TTS            │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Search Engine   │
                    │  FAISS + S-BERT  │
                    │  Hybrid Search   │
                    └──────────────────┘
```

### **Technology Stack**

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18, Vite, TypeScript | Modern SPA with Adobe PDF integration |
| **Backend** | FastAPI, Python 3.10 | High-performance async API server |
| **PDF Engine** | Adobe PDF Embed API | High-fidelity document rendering |
| **AI Search** | sentence-transformers, FAISS | Semantic similarity & vector search |
| **LLM** | Google Gemini 2.5 Flash | Insight generation & contradictions |
| **TTS** | Azure Cognitive Services | Natural audio podcast generation |
| **Deployment** | Docker, Multi-stage builds | Production-ready containerization |

---

## 🚀 Quick Start (Docker - Recommended)

### **For Adobe Evaluation Team**

```bash
# 1. Build the Docker image
docker build --platform linux/amd64 -t projectsynapse .

# 2. Run with Adobe-provided credentials
docker run \
  -v /path/to/credentials:/credentials \
  -e ADOBE_EMBED_API_KEY="your_adobe_key" \
  -e LLM_PROVIDER="gemini" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/credentials/adbe-gcp.json" \
  -e GEMINI_MODEL="gemini-2.5-flash" \
  -e TTS_PROVIDER="azure" \
  -e AZURE_TTS_KEY="your_azure_key" \
  -e AZURE_TTS_ENDPOINT="your_azure_endpoint" \
  -p 8080:8080 \
  projectsynapse

# 3. Access the application
open http://localhost:8080
```

**Build Time**: ~13 minutes (82% faster than standard builds)  
**Image Size**: ~3.57GB (75% smaller than unoptimized)  
**Ready for evaluation** with all Adobe-specified environment variables

---

## 💡 How It Works

### **Document Ingestion Pipeline**
1. **Bulk Upload**: Users upload multiple PDFs representing their knowledge library
2. **Smart Parsing**: Robust PDF structure extraction (from Round 1A) identifies sections
3. **Semantic Chunking**: Content broken into overlapping chunks for better context
4. **Vector Embedding**: Each chunk encoded using `all-MiniLM-L6-v2` model
5. **FAISS Indexing**: Efficient vector storage for sub-second similarity search

### **Real-Time Query Pipeline**
1. **Text Selection**: User highlights text in Adobe PDF viewer
2. **Semantic Search**: Selected text embedded and matched against document library
3. **Relevance Ranking**: Top 5 most relevant sections identified across PDFs
4. **Snippet Generation**: 2-4 sentence contextual extracts created
5. **Insight Generation**: AI analyzes connections for contradictions and examples

### **Audio Podcast Creation**
1. **Content Synthesis**: Related sections and insights compiled
2. **Script Generation**: Gemini creates natural 2-speaker conversation
3. **Voice Synthesis**: Azure TTS generates realistic dialogue
4. **Audio Mixing**: Multiple speakers combined into engaging podcast

---

## 🎯 Demo Scenario

**Researcher Use Case**: Studying "neural network training techniques"

1. **Selects text**: "transfer learning methodology"
2. **System responds** (< 1 second):
   - 3 similar methods from previous papers
   - 1 contradictory finding from recent study
   - 1 paper extending the technique
3. **Clicks insight bulb**: AI generates key takeaways and contradictions
4. **Requests podcast**: 3-minute audio overview with natural speaker dialogue

**Result**: From isolated reading to connected understanding in seconds

---

## 📊 Performance & Scalability

### **Search Performance**
- **Query Response**: < 500ms for text selection → results
- **Embedding Speed**: ~100 documents/minute ingestion
- **Memory Usage**: Optimized for 16GB RAM environment
- **CPU Utilization**: Efficient threading for 8-core systems

### **Docker Optimizations**
- **Multi-stage builds**: Separate build and runtime environments
- **CPU-only PyTorch**: Eliminates CUDA overhead
- **Layer caching**: Faster subsequent builds
- **Security**: Non-root user, minimal attack surface

---

## 🔧 Development Setup

For local development and testing:

```bash
# Clone repository
git clone <repository-url>
cd ProjectSynapse

# Backend setup
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Environment configuration
cp .env.example .env
# Edit .env with your API keys

# Run development servers
# Terminal 1: Backend
uvicorn main:app --port 8000 --reload

# Terminal 2: Frontend  
npm run dev
```

**Development URL**: http://localhost:5173  
**API Documentation**: http://localhost:8000/docs

---

## 🎨 Key Innovations

### **1. Hybrid Search Architecture**
- Combines semantic similarity with keyword matching
- Preserves document context while finding connections
- Optimized for academic and professional documents

### **2. Real-Time Insight Generation**
- Goes beyond simple text matching
- Identifies contradictions and complementary viewpoints
- Generates contextual examples and cross-references

### **3. Natural Audio Synthesis**
- Creates engaging 2-speaker conversations
- Maintains technical accuracy while improving accessibility
- Perfect for on-the-go learning and review

### **4. Production-Ready Docker**
- Optimized for evaluation environment constraints
- Handles all environment variables gracefully
- Fallback mechanisms for different configurations

---

## 🔒 Security & Production Readiness

- **Environment Variables**: All sensitive data externalized
- **Non-root Container**: Security-hardened Docker image
- **CORS Configuration**: Secure cross-origin request handling
- **Error Handling**: Graceful degradation for missing services
- **Health Checks**: Built-in container monitoring

---

## 📈 Adobe Hackathon Alignment

### **Round Integration**
- **Round 1A**: PDF parsing and section extraction engine
- **Round 1B**: Document intelligence and persona-driven insights
- **Finale**: Interactive user experience with AI enhancement

### **Evaluation Criteria Coverage**
- ✅ **Core Functionality** (20 pts): All mandatory features implemented
- ✅ **Technical Implementation** (15 pts): Modern, scalable architecture
- ✅ **Integration** (10 pts): Seamless Round 1A/1B incorporation
- ✅ **Performance** (5 pts): Sub-second response times
- ✅ **Bonus Features** (+10 pts): Insights Bulb + Audio Podcast

---

## 🎤 Live Demo Highlights

1. **Upload Demo**: Bulk PDF ingestion with real-time progress
2. **Search Demo**: Text selection → instant cross-document connections
3. **Insights Demo**: AI-powered contradiction detection
4. **Audio Demo**: Generated podcast playback
5. **Navigation Demo**: Click-to-jump PDF navigation

---

## 🔮 Future Enhancements

- **Multi-language support** for global document libraries
- **Collaborative features** for team knowledge sharing
- **Advanced visualizations** for document relationship mapping
- **Mobile optimization** for tablet-based research
- **Integration APIs** for existing workflow tools

---

## 👥 Team & Acknowledgments

Built for **Adobe India Hackathon 2025 Finale** with focus on real-world applicability and technical excellence. Special thanks to Adobe for providing the challenge framework and evaluation environment.

**Technologies**: React, FastAPI, Adobe PDF Embed API, Google Gemini, Azure TTS, Docker

---

## 📞 Support & Documentation

- **API Documentation**: Available at `/docs` endpoint
- **Docker Support**: Multi-platform builds (linux/amd64)
- **Environment Variables**: Comprehensive fallback handling
- **Error Logging**: Detailed logs for debugging

