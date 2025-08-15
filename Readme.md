# Project Synapse 🧠

**From Information Chaos to Connected Clarity.**

Project Synapse is a full-stack web application designed for the Adobe India Hackathon 2025 Finale. It transforms a static library of PDF documents into a dynamic, interconnected knowledge base. By leveraging semantic search and generative AI, it acts as a "second brain" for researchers, students, and professionals, helping them surface hidden connections, discover contradictions, and synthesize information effortlessly.

![Project Synapse Demo]

---

## ✨ Key Features

* **Instant Semantic Search**: Select text in any document and instantly see related sections and snippets from your entire library.
* **AI-Powered Insights Bulb**: Go beyond simple search. Generate deep insights, including contradictions, key takeaways, and illustrative examples from related content.
* **On-Demand Audio Podcast**: Transform your findings into a two-speaker audio overview, perfect for learning on the go.
* **High-Fidelity PDF Viewer**: A smooth, interactive PDF reading experience powered by the Adobe PDF Embed API.
* **Bulk Document Ingestion**: Easily upload your entire document library for processing and indexing.

---

## 🛠️ Technical Architecture & Stack

Project Synapse is built on a modern, decoupled architecture, containerized with Docker for easy deployment and evaluation.

* **Frontend**: A responsive Single-Page Application built with **React** and **Vite**.
* **Backend**: A high-performance, asynchronous API server built with **FastAPI** (Python).
* **AI & Search**:
    * **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` for fast and effective text encoding.
    * **Vector Store**: `FAISS` (Facebook AI Similarity Search) for efficient in-memory similarity search.
    * **Generative AI**: `Google Gemini` for generating insights and podcast scripts.
    * **Text-to-Speech**: `Azure TTS` for creating natural-sounding audio.

| Component             | Technology                                       | Purpose                                            |
| --------------------- | ------------------------------------------------ | -------------------------------------------------- |
| **Frontend** | React, Vite, Axios                               | User Interface and Interaction                     |
| **Backend** | FastAPI, Uvicorn                                 | API Server, Business Logic                         |
| **PDF Rendering** | Adobe PDF Embed API                              | High-fidelity document display & text selection    |
| **Vector Search** | FAISS, Sentence-Transformers                     | Core semantic search engine                        |
| **AI Insights** | Google Gemini API                                | Generating contradictions, summaries, etc.         |
| **Audio Generation** | Azure TTS API, Pydub                             | Creating and concatenating podcast audio           |
| **Containerization** | Docker                                           | Unified deployment for evaluation                  |

---

## 🚀 Getting Started

You can run Project Synapse either locally for development or using the provided Docker container for production/evaluation.

### Prerequisites

* Git
* Docker Desktop
* Node.js (v18+) and npm
* Python (v3.10+)

### Local Development

**1. Clone the Repository**
```bash
git clone <your-repo-url>
cd ProjectSynapse
```

**2. Backend Setup**
```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
python -m nltk.downloader punkt

# Create a .env file and add your API keys
cp .env.example .env 
# Now, edit backend/.env with your keys
```

**3. Frontend Setup**
```bash
# Navigate to the frontend directory
cd ../frontend

# Install dependencies
npm install

# Create a .env file from the example
cp .env.example .env
# Now, edit frontend/.env with your Adobe Embed API Key
```

**4. Run the Application**
* **Terminal 1 (Backend)**:
    ```bash
    cd backend
    source .venv/bin/activate
    uvicorn main:app --port 8000 --reload
    ```
* **Terminal 2 (Frontend)**:
    ```bash
    cd frontend
    npm run dev
    ```
* Open your browser and navigate to **http://localhost:5173**.

### Docker (For Evaluation)

The entire application is containerized for simple, one-command execution.

**1. Build the Docker Image**
From the root `ProjectSynapse` directory, run:
```bash
docker build --platform linux/amd64 -t yourimageidentifier .
```

**2. Run the Docker Container**
Execute the following command, replacing placeholders with your actual keys and paths. This command passes all necessary configurations as environment variables.
```bash
docker run -p 8080:8080 \
  -v /path/to/credentials:/credentials \
  -e ADOBE_EMBED_API_KEY="your_adobe_key" \
  -e LLM_PROVIDER="gemini" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/credentials/adbe-gcp.json" \
  -e GEMINI_MODEL="gemini-1.5-flash-latest" \
  -e TTS_PROVIDER="azure" \
  -e AZURE_TTS_KEY="your_azure_tts_key" \
  -e AZURE_TTS_ENDPOINT="your_azure_tts_endpoint" \
  yourimageidentifier
```
The application will be accessible at **http://localhost:8080**.

---

## ⚙️ How It Works

### Ingestion Pipeline
1.  **Upload**: User uploads multiple PDFs via the web interface.
2.  **Sectioning**: The backend uses the robust PDF structure extraction logic from Round 1A to parse documents into logical sections (headings + content).
3.  **Chunking**: Each section's content is broken down into smaller, overlapping semantic chunks.
4.  **Embedding**: Each chunk is converted into a numerical vector using a Sentence-Transformer model.
5.  **Indexing**: The vectors and their associated metadata (document name, section, page) are stored in a FAISS index on disk.

### Query Pipeline
1.  **Selection**: The user selects a piece of text in the PDF viewer.
2.  **API Call**: The frontend captures the selected text and sends it to the backend's query endpoint.
3.  **Vector Search**: The backend embeds the query text and uses FAISS to find the most semantically similar chunks from the index.
4.  **Insight Generation**: The results are used to power the "Insights Bulb" and "Podcast Mode" by crafting detailed prompts for the Gemini and Azure TTS APIs.
5.  **Display**: The final connections and generated content are sent back to the frontend and displayed in the sidebar.