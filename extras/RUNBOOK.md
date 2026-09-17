# Project Synapse Runbook

How to set up, run, deploy, verify and troubleshoot Project Synapse on **Windows with WSL2 (Ubuntu)**, and how the build, deployment and code flow work.

Companion docs: [HANDBOOK.md](HANDBOOK.md) (concepts and theory) and [RESUME_HANDBOOK.md](RESUME_HANDBOOK.md) (interview prep).

> **Where this information comes from.** Everything here was worked out by reading the code: `Dockerfile`, `entrypoint.sh`, `backend/` and `frontend/`. Where `Readme.md` or `DEBUG.md` disagree with the code, this runbook follows the code; [§12](#12-docs-vs-code) lists the differences. Two version facts were checked against PyPI on 2026-09-16: the torch pin problem ([§7.9](#79-known-issue-the-cpu-only-torch-pin-no-longer-holds)), and that `@app.on_event` still works on current FastAPI. The full app wasn't run end to end while this was written.

## Contents

0. [TL;DR](#0-tldr)
1. [What you are running](#1-what-you-are-running)
2. [Dependencies](#2-dependencies)
3. [The .env file](#3-the-env-file)
4. [Set up WSL2 on Windows](#4-set-up-wsl2-on-windows)
5. [Run locally for development](#5-run-locally-for-development)
6. [Run with Docker](#6-run-with-docker)
7. [How the build and deployment work](#7-how-the-build-and-deployment-work)
8. [How the code works at runtime](#8-how-the-code-works-at-runtime)
9. [API reference](#9-api-reference)
10. [Verification checklist](#10-verification-checklist)
11. [Troubleshooting](#11-troubleshooting)
12. [Docs vs code](#12-docs-vs-code)
13. [Security notes](#13-security-notes)
14. [Command cheat sheet](#14-command-cheat-sheet)

---

## 0. TL;DR

Both ways of running the app need a filled-in **`.env` file in the project root** first ([§3](#3-the-env-file)). Run everything from an Ubuntu (WSL) terminal.

**Local development** uses two terminals, both starting in the project root:

```bash
# Terminal 1: backend API on :8000 (must start from the project root)
source backend/.venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend

# Terminal 2: frontend dev server on :8080
cd frontend && npm run dev
# Then open http://localhost:8080 in your Windows browser
```

**Docker** runs everything in one container on :8080:

```bash
docker build -t projectsynapse .
docker run -d --name synapse -p 8080:8080 -v synapse-data:/app/backend/data projectsynapse
# Then open http://localhost:8080
```

The first-time setup (WSL, Python, Node, Docker) is in [§4](#4-set-up-wsl2-on-windows) to [§6](#6-run-with-docker).

---

## 1. What you are running

```
Windows browser
  React single-page app  +  Adobe PDF Embed viewer (viewer.js loaded from Adobe's CDN)
     │  HTTP /api/*
     ▼
FastAPI app on Uvicorn (one Python process, running in WSL or in the Docker container)
  ├─ /api/ingest ............. save PDFs → parse → chunk → embed → index   (runs in the background)
  ├─ /api/related-sections ... hybrid search: FAISS (meaning) + BM25 (keywords), fused with RRF → top 5
  ├─ /api/insights ........... Gemini writes insights from the top snippets
  ├─ /api/podcast ............ Gemini writes a script → Azure OpenAI TTS → MP3
  ├─ /api/pdf/{file} ......... returns an uploaded PDF (used to jump to a related section)
  └─ /api/health ............. health check for Docker
  In RAM:  all-MiniLM-L6-v2 model, FAISS index, BM25 index, chunk metadata
  On disk: backend/data/uploads/*.pdf, index.faiss, metadata.json, metadata_bm25.json

Outbound calls:  Hugging Face Hub (model download, first start only) · Google Gemini API · Azure OpenAI
```

**Ports:**

| Mode | Frontend | Backend |
|---|---|---|
| Local development | Vite dev server on `http://localhost:8080` | Uvicorn on `http://localhost:8000` |
| Docker | Served by FastAPI on `http://localhost:8080` | Same process and port, `http://localhost:8080/api/*` |

> Both modes use port 8080, so don't run the Vite dev server and the Docker container at the same time.

---

## 2. Dependencies

### 2.1 External services and keys

| Service | What Synapse uses it for | Environment variables | Required? | What happens without it |
|---|---|---|---|---|
| **Adobe PDF Embed API** | Shows PDFs in the browser, fires the text-selection event, jumps to pages | `VITE_ADOBE_CLIENT_ID` (read at **build** time); `ADOBE_EMBED_API_KEY` (same value, only for parity with the hackathon setup) | **Yes** | The reader shows "VITE_ADOBE_CLIENT_ID is not configured.", so you get no viewer, no selection, and no features |
| **Google Gemini** (LLM) | Writes the insights and the podcast script | `LLM_PROVIDER=gemini`, `GOOGLE_API_KEY`, `GEMINI_MODEL` | Yes, for the AI features | Related sections still work. The UI shows "Failed to generate insights." and stops, so the podcast step is never reached |
| **Azure OpenAI**, `tts` model | Turns the podcast script into an MP3 | `TTS_PROVIDER=azure`, `AZURE_TTS_KEY`, `AZURE_TTS_ENDPOINT`, `AZURE_TTS_DEPLOYMENT`, `AZURE_TTS_API_VERSION`, `AZURE_TTS_VOICE` | Only for the podcast | The podcast fails with HTTP 503. Use `TTS_PROVIDER=local` instead |
| **Hugging Face Hub** | Downloads `all-MiniLM-L6-v2` (~90 MB) the first time the backend starts | none | Internet on first start | The backend crashes at startup |
| **Adobe CDN** (`acrobatservices.adobe.com`) | The browser downloads the viewer script | none | Yes | "Failed to load Adobe SDK." |
| Google Cloud TTS *(optional)* | Alternative voice | `TTS_PROVIDER=gcp`, plus `GOOGLE_API_KEY` or `GOOGLE_APPLICATION_CREDENTIALS`; optional `GCP_TTS_VOICE`, `GCP_TTS_LANGUAGE` | No | n/a |
| espeak-ng *(optional, runs locally)* | Free, offline, robotic-sounding voice | `TTS_PROVIDER=local`; optional `ESPEAK_VOICE`, `ESPEAK_SPEED` | No | n/a |

### 2.2 Is there a database?

**There is no database server**: no PostgreSQL, MongoDB, Redis or hosted vector database. The "database" is a set of files in `backend/data/`, loaded into RAM when the backend starts:

| File | Contents | Written by |
|---|---|---|
| `uploads/*.pdf` | The original PDFs, served back to the viewer | `POST /api/ingest` |
| `index.faiss` | FAISS vector index: 384 numbers for every text chunk | `add_chunks_to_index` in [search.py](../backend/app/core/search.py#L233-L278) |
| `metadata.json` | One JSON object per chunk (document name, section title, page, chunk text), in the **same order** as the vectors | same function |
| `metadata_bm25.json` | Lower-cased word lists of every chunk, for BM25 keyword search | same function |

Row *i* of the FAISS index matches entry *i* in both JSON files. **Always delete or restore the three index files together.**

### 2.3 Where does OpenAI come in?

Only through **Azure OpenAI**. The podcast voice is OpenAI's `tts` model, deployed inside **your Azure OpenAI resource** and called over REST ([generate_audio.py](../backend/app/scripts/generate_audio.py#L52-L105)):

```
POST {AZURE_TTS_ENDPOINT}/openai/deployments/{AZURE_TTS_DEPLOYMENT}/audio/speech?api-version={AZURE_TTS_API_VERSION}
header  api-key: {AZURE_TTS_KEY}
body    {"model": "<deployment>", "input": "<script>", "voice": "nova"}
```

- You do **not** need an `OPENAI_API_KEY`. The LLM is Gemini.
- `langchain-openai` and `azure-cognitiveservices-speech` are installed but never imported.
- "Azure TTS" in this project is **not** the "Azure AI Speech" service; that's a different product with a different API.

### 2.4 System packages

| Package | Why | Needed for local development? |
|---|---|---|
| Python **3.10**, venv, pip, dev headers | Runtime; Docker uses `python:3.10-slim` | Yes |
| build-essential, libffi-dev | Compiling any Python package that has no prebuilt wheel | Recommended |
| Node.js 18+ and npm | Frontend (Docker uses `node:18-alpine`) | Yes |
| git, curl | Getting the code; health checks and API tests | Yes |
| ffmpeg | pydub uses it to encode MP3 for local TTS | Only if `TTS_PROVIDER=local` |
| espeak-ng | Local TTS engine | Only if `TTS_PROVIDER=local` |
| tesseract-ocr, poppler-utils | OCR tools; installed in Docker, but the current code never calls them | No |

### 2.5 Python packages

From [requirements.txt](../backend/requirements.txt) and the [Dockerfile](../Dockerfile#L59-L119):

| Package | Role in Synapse | Actually used? |
|---|---|---|
| fastapi | Web framework and API | ✅ |
| uvicorn[standard] | ASGI server (also brings httptools, uvloop, and watchfiles for `--reload`) | ✅ |
| python-multipart | Parses multipart file uploads, needed for `UploadFile` | ✅ |
| pydantic-settings | `Settings` loaded from environment variables or `.env` | ✅ |
| python-dotenv | `load_dotenv()` copies `.env` into `os.environ` | ✅ |
| sentence-transformers | Loads and runs `all-MiniLM-L6-v2` | ✅ |
| torch (CPU build) | Runs the neural network | ✅ (through sentence-transformers) |
| torchvision, torchaudio | Installed by the Dockerfile only | ❌ |
| faiss-cpu | Vector index | ✅ |
| rank-bm25 | BM25 keyword scoring | ✅ |
| numpy | Arrays: embeddings, sorting | ✅ |
| scipy, scikit-learn | Dependencies of sentence-transformers and LightGBM | Indirectly |
| PyMuPDF (`fitz`) | Extracts text blocks, fonts and positions from PDFs | ✅ |
| nltk | Splits text into sentences (Punkt) for chunking | ✅ |
| pandas, joblib, lightgbm | Imported by the parser for the old Round 1A model, which is never loaded | Imported only |
| pytesseract (+ Pillow) | OCR; imported but never called | ❌ |
| langchain, langchain-google-genai, google-generativeai | Gemini calls | ✅ |
| langchain-openai, langchain-community | Never imported | ❌ |
| requests | REST calls for Azure and GCP TTS | ✅ |
| pydub | Converts WAV to MP3 for local TTS | ✅ (local TTS) |
| azure-cognitiveservices-speech | Azure Speech SDK; never imported | ❌ |
| google-cloud-texttospeech | GCP TTS with a service account (`TTS_PROVIDER=gcp`) | Optional |
| anyio | Async utilities (a Starlette dependency) | Indirectly |

### 2.6 Frontend packages

From [package.json](../frontend/package.json): React 18 and react-dom, react-router-dom 6, TypeScript 5, Vite 5 with `@vitejs/plugin-react-swc`, Tailwind CSS 3 with tailwindcss-animate, shadcn/ui components (about 25 `@radix-ui/*` packages, class-variance-authority, clsx, tailwind-merge), lucide-react icons, sonner toasts, and @tanstack/react-query (provider only). The Adobe PDF Embed SDK is **not** an npm package: the browser loads it at runtime from `https://acrobatservices.adobe.com/view-sdk/viewer.js`.

### 2.7 How to get each credential

**Adobe PDF Embed API client ID** (free)
1. Open Adobe's credential page, <https://www.adobe.com/go/dcsdks_credentials> (the same link the frontend README uses), and sign in with a free Adobe account.
2. Create credentials for the **PDF Embed API**, and set the **application domain** to `localhost`.
3. Copy the **Client ID** into `VITE_ADOBE_CLIENT_ID`, and the same value into `ADOBE_EMBED_API_KEY`.
- The client ID is public by design (it's visible in the browser's JavaScript), but it only works on its registered domain. Always open the app at `http://localhost:<port>`. `127.0.0.1` and the WSL IP address count as different domains.

**Google Gemini API key**
1. Open <https://aistudio.google.com>, choose **Get API key**, then **Create API key**.
2. Put the key in `GOOGLE_API_KEY`.
3. Set `GEMINI_MODEL=gemini-2.5-flash`. If Google has since retired that model, use a current "Flash" model name from AI Studio's model list.
- The code only supports `LLM_PROVIDER=gemini`, and it **requires `GOOGLE_API_KEY`**. A service-account JSON file (`GOOGLE_APPLICATION_CREDENTIALS`) is ignored by the LLM code.
- If `GEMINI_MODEL` isn't set, the code falls back to `gemini-1.5-flash`, which is outdated. **Always set it.**

**Azure OpenAI TTS**
1. In the Azure portal, create an **Azure OpenAI** resource in a region that offers a TTS model.
2. In the Azure AI Foundry portal (previously Azure OpenAI Studio), go to **Deployments** and deploy the `tts` model (or `tts-hd`). Name the deployment `tts`, or set `AZURE_TTS_DEPLOYMENT` to whatever name you chose.
3. On the resource's **Keys and Endpoint** page, copy **KEY 1** into `AZURE_TTS_KEY` and the endpoint into `AZURE_TTS_ENDPOINT`. The endpoint looks like `https://<name>.openai.azure.com`; don't include a trailing slash.
4. Check your credentials with `python backend/test_tts.py` ([§10](#10-verification-checklist)).
- If `tts` isn't available to you, deploy a newer speech model that uses the same `/audio/speech` endpoint and voices (for example `gpt-4o-mini-tts`) and point `AZURE_TTS_DEPLOYMENT` at it. This likely works unchanged.
- If Azure rejects `2024-08-01-preview`, set `AZURE_TTS_API_VERSION` to a newer version listed in the Azure OpenAI docs.
- **No Azure account?** Set `TTS_PROVIDER=local`. It uses espeak-ng: robotic, but free.

---

## 3. The .env file

There's **one** `.env` file, in the **project root**, shared by the frontend and the backend. The repo has no `.env.example` (despite what the README says), so create it from this template:

```dotenv
# ===================== Project Synapse .env (project root) =====================
# Rules: KEY=value, no quotes, no spaces around "=", comments on their own line, Linux (LF) line endings.

# ---- Frontend (Vite). Baked into the JavaScript at build/dev-start time ----
# Adobe PDF Embed API client ID, registered for the domain "localhost"
VITE_ADOBE_CLIENT_ID=your_adobe_client_id
# Where the browser sends API calls:
#   local development (Vite :8080 + FastAPI :8000)  -> http://localhost:8000
#   Docker (the Dockerfile rewrites this to http://localhost:8080 anyway)
VITE_API_URL=http://localhost:8000

# ---- Adobe (only for parity with the hackathon setup; the backend never calls Adobe) ----
ADOBE_EMBED_API_KEY=your_adobe_client_id

# ---- LLM: Google Gemini ----
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# ---- Text-to-speech: azure | gcp | local ----
TTS_PROVIDER=azure
AZURE_TTS_KEY=your_azure_openai_key
AZURE_TTS_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_TTS_DEPLOYMENT=tts
AZURE_TTS_API_VERSION=2024-08-01-preview
AZURE_TTS_VOICE=alloy
```

**Who reads `.env`, and when:**

| Reader | How | When | To apply a change |
|---|---|---|---|
| Vite (frontend) | `envDir: "../"` in [vite.config.ts](../frontend/vite.config.ts) exposes only `VITE_*` variables, written into the JavaScript | When `npm run dev` starts, at `npm run build`, and during `docker build` | Restart `npm run dev`, or rebuild the Docker image |
| Backend `Settings` | pydantic-settings, `env_file=".env"`, relative to the **working directory** | When the app is imported | Restart uvicorn |
| Backend `os.getenv` (LLM and TTS keys) | `load_dotenv()` in [main.py](../backend/main.py#L12) and [generate_audio.py](../backend/app/scripts/generate_audio.py#L10-L15), which searches upward for `.env` | When the app is imported | Restart uvicorn |
| `entrypoint.sh` (Docker only) | `source /app/.env.original`, then rewrites `/app/.env` | Container start | See [§7.8](#78-environment-variable-precedence) |

> **Tips**
> - Create `.env` **inside WSL** (with `nano` or VS Code connected to WSL). A file saved by Windows Notepad can have CRLF line endings, which put an invisible `\r` at the end of every key.
> - `.env` is in `.gitignore`. Never commit it.
> - Consider saving a copy with placeholder values as `.env.example` for next time.

---

## 4. Set up WSL2 on Windows

### 4.1 Install WSL2 and Ubuntu 22.04

Open **PowerShell as Administrator**:

```powershell
wsl --install -d Ubuntu-22.04
```

Restart Windows if asked. Then open **"Ubuntu 22.04"** from the Start menu and create a Linux username and password. Back in PowerShell:

```powershell
wsl --update
wsl -l -v          # Ubuntu-22.04 must show VERSION 2
# If it shows 1:
wsl --set-version Ubuntu-22.04 2
```

**Why Ubuntu 22.04?** It ships **Python 3.10**, the same version as the Docker image, so local development behaves like the container.

**Already on Ubuntu 24.04 or newer** (Python 3.12+)? Create a Python 3.10 virtual environment with `uv` instead of `python3 -m venv` in step 5.2:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # then open a new terminal
cd ~/projects/projectSynapse
uv venv --python 3.10 --seed backend/.venv          # --seed installs pip into the venv
```

After that, follow §5.2 from `source backend/.venv/bin/activate` onward.

### 4.2 (Optional) Give WSL more memory

Building the Docker image, installing PyTorch and loading the model all use a lot of memory. On Windows, create `C:\Users\Suryansh.Tripathi\.wslconfig`:

```ini
[wsl2]
memory=8GB
processors=4
swap=8GB
```

Then run `wsl --shutdown` in PowerShell and reopen Ubuntu.

### 4.3 Install system packages

In the Ubuntu terminal:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl build-essential \
  python3-venv python3-pip python3-dev libffi-dev \
  ffmpeg espeak-ng
python3 --version        # expect: Python 3.10.x
```

### 4.4 Install Node.js

Use nvm (Node Version Manager):

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 22
node -v && npm -v
```

Vite 5 runs on Node 18, 20 and 22. The Docker build uses Node 18.

### 4.5 Get the code into the Linux filesystem

```bash
git config --global core.autocrlf input        # keep LF line endings in files you commit from WSL
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/SuryanshT01/projectSynapse.git
cd projectSynapse
```

**Why `~/projects` and not `/mnt/c/Users/...`?**
- The Linux filesystem is many times faster for `npm install`, `pip` and the Docker build context.
- File watching (Vite hot reload, `uvicorn --reload`) works reliably there.
- You avoid CRLF and permission surprises. A CRLF `entrypoint.sh` breaks the container.

You can still browse the files from Windows Explorer at `\\wsl.localhost\Ubuntu-22.04\home\<your-linux-user>\projects\projectSynapse`.

**Alternative: copy your existing Windows copy.**

```bash
cp -r /mnt/c/Users/Suryansh.Tripathi/Desktop/projectSynapse ~/projects/
cd ~/projects/projectSynapse
grep -c $'\r' entrypoint.sh      # must print 0. If not:  sed -i 's/\r$//' entrypoint.sh
```

(The Windows copy currently has LF endings, but Windows git has `core.autocrlf=true`, so future checkouts made on Windows could convert them to CRLF.)

### 4.6 Open the project in VS Code

Install the **WSL** extension in VS Code on Windows. Then, in the Ubuntu terminal:

```bash
cd ~/projects/projectSynapse && code .
```

VS Code reopens connected to WSL, and its terminals run in Ubuntu.

### 4.7 How networking works between Windows and WSL

A server started inside WSL on `0.0.0.0:PORT` or `localhost:PORT` can be opened from your Windows browser at `http://localhost:PORT`, because WSL2 forwards localhost. **Always use `localhost`**: the Adobe client ID is tied to that domain, and the page's Content-Security-Policy only allows API calls to `http://localhost:*`.

---

## 5. Run locally for development

All commands start from the project root, `~/projects/projectSynapse`.

### 5.1 Create .env

```bash
cd ~/projects/projectSynapse
nano .env       # paste the template from §3, fill in the keys, keep VITE_API_URL=http://localhost:8000
```

### 5.2 Install the backend

```bash
cd ~/projects/projectSynapse
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

# 1) CPU-only PyTorch FIRST, the same trick the Dockerfile uses.
#    Without this, pip installs the CUDA build of torch plus several GB of nvidia-* packages.
#    Don't pin torch==2.1.2 here: current sentence-transformers needs torch>=2.2,
#    so pip would replace it with the CUDA build from PyPI (see §7.9).
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 2) Everything else
pip install -r backend/requirements.txt

# 3) Sanity check
python -c "import torch, sentence_transformers, faiss, rank_bm25, fitz, langchain_google_genai; print('torch', torch.__version__, '| CUDA:', torch.cuda.is_available())"
```

Expected output: `torch 2.x.x+cpu | CUDA: False`, with no import errors.

**Why is the venv in `backend/.venv`?** `.dockerignore` excludes `backend/.venv/`, so the venv never gets sent to Docker builds, and `.gitignore` already ignores `.venv/`.

### 5.3 Download NLTK data

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

You need both. [processing.py](../backend/app/core/processing.py#L23-L26) checks for `punkt` when it's imported and crashes if it's missing, and newer NLTK uses `punkt_tab` to split sentences. If `punkt_tab` is missing, every PDF fails to index, and the only sign is a message in the server log.

### 5.4 Start the backend

```bash
cd ~/projects/projectSynapse                # the project ROOT, not backend/
source backend/.venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend
```

**Why from the root, and why `backend.main:app`?**
- The code imports `backend.app...`, so Python must be able to see the `backend` package.
- The data paths (`backend/data/...`) are relative to the working directory.
- pydantic-settings reads `./.env`.

The README's `cd backend && uvicorn main:app` fails with `ModuleNotFoundError: No module named 'backend'`. `--reload-dir backend` keeps the auto-reloader from watching `frontend/node_modules`.

The log should look roughly like this. The first start also downloads the model.

```
WARNING - No static directory found. Skipping mount. ...        ← normal in development
INFO:     Waiting for application startup.
INFO - Loading hybrid search engine...
INFO - SentenceTransformer model 'all-MiniLM-L6-v2' loaded.
WARNING - FAISS index or metadata not found. Initializing new indices.   ← first run only
INFO - Search engine loaded successfully.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Deprecation warnings such as "`on_event is deprecated`" are harmless.

Check it's up:

```bash
curl http://localhost:8000/api/health      # {"status":"healthy","service":"Project Synapse API","version":"1.0.0"}
```

The Swagger UI is at <http://localhost:8000/docs>.

### 5.5 Start the frontend

In a **second terminal**:

```bash
cd ~/projects/projectSynapse/frontend
npm ci              # or: npm install
npm run dev
```

Vite prints `Local: http://localhost:8080/`. The README says 5173, but [vite.config.ts](../frontend/vite.config.ts) sets the port to 8080.

### 5.6 Use the app

1. Open **<http://localhost:8080>** in your Windows browser.
2. **Add PDFs to Library** → choose several PDFs. You'll see *"Processing started in background for N documents."* Watch the backend terminal for `Successfully indexed X chunks from <file>`, or for a warning.
3. **Upload PDF to Read** → choose one PDF. This file only opens in your browser; it is **not** indexed. If you also want it to show up in search results, add it to the library too.
4. **Select some text** (more than 10 characters). The sidebar fills in three stages: **Related Content** (fast), **AI Insights** (a few seconds), then **Audio Summary** (slower).
5. **Click a related section** to open that library PDF and jump near its page. It lands one page early; see [§11](#11-troubleshooting).

For best results:
- Use PDFs whose headings are **bold**, meaning the font name contains "Bold". Those index well; PDFs without them produce 0 chunks.
- Scanned (image-only) PDFs aren't indexed at all.
- The PDF opened with "Upload PDF to Read" lives only in the browser's navigation state. If you refresh `/reader` and see "No PDF Available", go back to Home and choose it again.

### 5.7 Production-like run without Docker

This serves the built React app from FastAPI on a single port, the same way the container does:

```bash
cd ~/projects/projectSynapse
sed -i 's|^VITE_API_URL=.*|VITE_API_URL=http://localhost:8080|' .env
(cd frontend && npm run build)                         # creates frontend/dist
source backend/.venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8080    # stop the Vite dev server first, since it uses 8080
```

Open <http://localhost:8080>. The backend now logs `Mounting static files from: .../frontend/dist`.

To go back to development mode: set `VITE_API_URL` back to `http://localhost:8000`, and delete `frontend/dist` (`rm -rf frontend/dist`) if you don't want the backend serving an old build.

### 5.8 Reset the library

Stop the backend first, then:

```bash
cd ~/projects/projectSynapse
rm -f backend/data/index.faiss backend/data/metadata.json backend/data/metadata_bm25.json
rm -rf backend/data/uploads/* data/temp_audio/*
```

Start the backend again and re-upload your PDFs. Do this whenever you change `CHUNK_SIZE`, `CHUNK_OVERLAP` or `EMBEDDING_MODEL_NAME`.

---

## 6. Run with Docker

### 6.1 Get Docker working inside WSL

**Option A (recommended): Docker Desktop for Windows.** It's already installed on this machine.
1. Start Docker Desktop.
2. Open **Settings → General** and make sure **"Use the WSL 2 based engine"** is ticked.
3. Open **Settings → Resources → WSL integration**, turn on **Ubuntu-22.04**, and click **Apply & restart**.
4. In Ubuntu:
   ```bash
   docker version
   docker run --rm hello-world
   ```

**Option B: Docker Engine inside Ubuntu, without Docker Desktop.**

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER      # then close and reopen the terminal
sudo service docker start          # only needed if systemd isn't enabled in WSL
docker run --rm hello-world
```

Use one option or the other, not both.

**Disk space:** allow about 15 GB for base images, pip layers, the final image and build cache. Docker Desktop keeps its data on your C: drive.

### 6.2 Pre-build checklist

- [ ] **`.env` exists in the project root.** The build fails without it (`COPY .env`). It must contain `VITE_ADOBE_CLIENT_ID`, because the frontend is built inside Docker. Decide now whether the backend keys go into `.env` (simple) or are passed at runtime ([§6.7](#67-passing-secrets-at-runtime-instead)).
- [ ] **LF line endings**: `grep -c $'\r' .env entrypoint.sh` must show `:0` for both files.
- [ ] **No stale local index.** `.dockerignore` excludes `backend/data/uploads/` but **not** `index.faiss` or `metadata*.json`. If you've run the app locally, the image would ship an index whose PDFs are missing, and clicking a section would show "PDF not available". Clear it:
  ```bash
  rm -f backend/data/index.faiss backend/data/metadata.json backend/data/metadata_bm25.json
  ```
- [ ] *(Recommended)* Apply the torch fix from [§7.9](#79-known-issue-the-cpu-only-torch-pin-no-longer-holds) if you want the small, CPU-only image the README describes.
- [ ] Enough disk space: `df -h ~`.

### 6.3 Build the image

```bash
cd ~/projects/projectSynapse
docker build -t projectsynapse .
# Full, un-collapsed logs:   docker build --progress=plain -t projectsynapse .
# Only on ARM machines (e.g. Apple Silicon) building for x86:  add --platform linux/amd64
```

- The first build takes 10–20+ minutes, mostly downloading. Rebuilds after code-only changes are much faster, because the dependency layers are cached.
- The build log **prints your `.env`** (the `RUN cat /app/.env` step). Don't share build logs.
- Check the size with `docker images projectsynapse`. The README says 3.57 GB; without the §7.9 fix, expect it to be several GB larger.

### 6.4 Run the container

```bash
docker run -d --name synapse \
  -p 8080:8080 \
  -v synapse-data:/app/backend/data \
  projectsynapse
```

| Flag | Why |
|---|---|
| `-d --name synapse` | Run in the background under a name you can refer to |
| `-p 8080:8080` | **Keep the host port 8080.** The frontend was built to call `http://localhost:8080`, so mapping any other host port breaks its API calls |
| `-v synapse-data:/app/backend/data` | A named volume, so uploaded PDFs and the index survive `docker rm` and rebuilds |

### 6.5 Verify

```bash
docker logs -f synapse                                        # Ctrl+C stops following
curl -s http://localhost:8080/api/health                      # {"status":"healthy",...}
docker inspect --format '{{.State.Health.Status}}' synapse    # starting → healthy
```

The entrypoint should print something like:

```
=========================================
Project Synapse - Adobe Hackathon 2025
=========================================
Configuring runtime environment...
Environment variables configured:
- LLM_PROVIDER: gemini
- GEMINI_MODEL: gemini-2.5-flash
- TTS_PROVIDER: azure
- Azure TTS credentials provided            ← or "... not provided, using local TTS"
- Using Google API key for authentication
=========================================
Starting Project Synapse on port 8080...
```

Uvicorn's startup logs follow. On the **first start of a new container**, the model (~90 MB) is downloaded before `Application startup complete`, so give it a minute. This needs internet access.

Then open **<http://localhost:8080>** in your Windows browser.

### 6.6 Day-2 commands

| Task | Command |
|---|---|
| Follow logs | `docker logs -f synapse` |
| Stop / start | `docker stop synapse` / `docker start synapse` |
| Open a shell inside | `docker exec -it synapse bash` |
| See the runtime env file (**shows secrets**) | `docker exec synapse cat /app/.env` |
| List the indexed data | `docker exec synapse ls -la /app/backend/data /app/backend/data/uploads` |
| Resource usage | `docker stats synapse` |
| Remove the container (data stays in the volume) | `docker rm -f synapse` |
| Wipe the library | `docker rm -f synapse && docker volume rm synapse-data` |
| Redeploy after code changes | `docker build -t projectsynapse . && docker rm -f synapse && docker run -d --name synapse -p 8080:8080 -v synapse-data:/app/backend/data projectsynapse` |
| Restart automatically after reboots | add `--restart unless-stopped` to `docker run` |
| Free disk space | `docker system df`, then `docker builder prune` and `docker image prune` |

### 6.7 Passing secrets at runtime instead

With the simple approach, the backend keys go into `.env` before the build, so they end up **inside the image**. That's fine on your own machine, but **never push that image to a registry**. The cleaner approach:

1. Before building, keep **only** the frontend values in `.env`:
   ```dotenv
   VITE_ADOBE_CLIENT_ID=your_adobe_client_id
   VITE_API_URL=http://localhost:8080
   ```
2. Keep the backend secrets in a file **outside the repo**, for example `~/secrets/synapse.env`:
   ```dotenv
   LLM_PROVIDER=gemini
   GOOGLE_API_KEY=...
   GEMINI_MODEL=gemini-2.5-flash
   TTS_PROVIDER=azure
   AZURE_TTS_KEY=...
   AZURE_TTS_ENDPOINT=https://your-resource-name.openai.azure.com
   AZURE_TTS_DEPLOYMENT=tts
   AZURE_TTS_API_VERSION=2024-08-01-preview
   AZURE_TTS_VOICE=alloy
   ```
3. Build, then run with the secrets file:
   ```bash
   docker build -t projectsynapse .
   docker run -d --name synapse -p 8080:8080 -v synapse-data:/app/backend/data \
     --env-file ~/secrets/synapse.env projectsynapse
   ```

Docker `--env-file` format: one `KEY=value` per line, **no quotes** (quotes become part of the value), no `export`.

> **Why not simply add `-e KEY=...` on top of a full `.env`?** When a key exists in the baked `.env`, **the baked value wins** over `docker run -e`. [§7.8](#78-environment-variable-precedence) explains why.

### 6.8 The Adobe evaluation command, explained

The README's run command:

```bash
docker run \
  -v /path/to/credentials:/credentials \                              # mounts a folder containing a GCP service-account JSON
  -e ADOBE_EMBED_API_KEY="..." \                                      # no effect on the already-built frontend
  -e LLM_PROVIDER="gemini" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/credentials/adbe-gcp.json" \    # ignored by the LLM code
  -e GEMINI_MODEL="gemini-2.5-flash" \
  -e TTS_PROVIDER="azure" \
  -e AZURE_TTS_KEY="..." -e AZURE_TTS_ENDPOINT="..." \
  -p 8080:8080 projectsynapse
```

What it actually needs in order to work:
1. **`-e GOOGLE_API_KEY=...`.** Without it, insights fail, and a podcast requested directly would use a generic fallback script.
2. The **Adobe client ID must already be in `.env` at build time** as `VITE_ADOBE_CLIENT_ID`.
3. None of the keys passed with `-e` should also appear in the baked `.env` ([§7.8](#78-environment-variable-precedence)).

The service-account JSON is only used with `TTS_PROVIDER=gcp` when no `GOOGLE_API_KEY` is set.

---

## 7. How the build and deployment work

### 7.1 Build time vs run time

```
BUILD TIME:  docker build
  Stage 1  frontend-builder   node:18-alpine
           copy package*.json + .env → npm ci → copy src → set VITE_API_URL=http://localhost:8080 → vite build
           output: /app/frontend/dist   (VITE_* values now fixed inside the JS)
  Stage 2  python-builder     python:3.10-slim + compilers
           pip: torch (CPU) → numpy/scipy/sklearn → sentence-transformers → faiss-cpu → web stack
                → langchain + Gemini → pandas/joblib/lightgbm/rank-bm25 → PyMuPDF/pytesseract/nltk
                → pydub/azure-speech/gcloud-tts;  NLTK punkt + punkt_tab
           output: /usr/local/lib/python3.10/site-packages, /usr/local/bin, /usr/local/share/nltk_data
  Stage 3  production         python:3.10-slim (no compilers, no Node)
           apt: tesseract, poppler, ffmpeg, espeak-ng, curl  ·  user "app"  ·  data dirs
           copy site-packages + bin + nltk_data (stage 2) · backend/ · .env · dist (stage 1) · entrypoint.sh
           USER app · HEALTHCHECK /api/health · EXPOSE 8080 · ENTRYPOINT entrypoint.sh

RUN TIME:  docker run
  entrypoint.sh → back up .env → source it → rewrite /app/.env with defaults → TTS fallback
               → create data dirs → exec uvicorn backend.main:app --host 0.0.0.0 --port 8080
  uvicorn → import backend.main → startup: load MiniLM (download on first run), FAISS, BM25
          → serve /api/* and the React app on :8080
```

### 7.2 Dockerfile walkthrough

Line numbers refer to [Dockerfile](../Dockerfile).

| Lines | Instruction | What it does and why |
|---|---|---|
| 5 | `FROM node:18-alpine AS frontend-builder` | A small Node image used only to build the UI; Node isn't in the final image |
| 10 | `COPY frontend/package*.json ./` | Copies the manifests **before** the source, so the `npm ci` layer is reused until dependencies change |
| 13 | `COPY .env /app/.env` | Puts the root `.env` where Vite's `envDir: "../"` looks (`/app`). **The build fails if `.env` doesn't exist** |
| 15 | `RUN npm ci` | Clean install that exactly matches `package-lock.json` |
| 18 | `COPY frontend/. ./` | Copies the source (`node_modules` is excluded by `.dockerignore`) |
| 21 | `RUN sed ... VITE_API_URL=http://localhost:8080` | In the container, the UI and API share one origin on port 8080 |
| 24 | `RUN cat /app/.env` | Debug leftover that **prints your secrets into the build log** |
| 27 | `RUN npm run build` | `vite build` → `dist/`, with `import.meta.env.VITE_*` replaced by literal values |
| 30 | `FROM python:3.10-slim AS python-builder` | Stage for installing Python packages |
| 33–41 | apt: gcc, g++, python3-dev, build-essential, libffi-dev | Compilers for any package without a prebuilt wheel; they stay in this stage |
| 44–48 | `/etc/pip/pip.conf`: timeout 600, retries 5, trusted hosts | Survive slow or flaky networks during big downloads |
| 53–54 | `COPY backend/requirements*.txt` | Copied, but **never installed from**; each `RUN` below lists its packages explicitly |
| 57 | Upgrade pip | |
| 62–64 | `torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2` from `download.pytorch.org/whl/cpu` | **The key optimization**: CPU wheels instead of CUDA. Overridden today; see §7.9 |
| 67–70 | `numpy==1.26.4`, scipy, `scikit-learn==1.3.2` | Scientific base, installed first so later packages reuse it |
| 73–74 | `sentence-transformers` (not pinned) | Embedding model library; today it forces a newer torch (§7.9) |
| 77–78 | `faiss-cpu` | Vector index |
| 81–88 | fastapi, uvicorn[standard], python-multipart, python-dotenv, pydantic-settings, requests, anyio | Web stack |
| 91–96 | langchain 0.3.27, langchain-google-genai 2.0.10, langchain-openai 0.3.29, langchain-community 0.3.27, google-generativeai 0.8.5 | LLM libraries (pinned) |
| 99–103 | pandas 2.1.4, joblib 1.3.2, lightgbm 4.1.0, rank-bm25 0.2.2 | Parser imports, and BM25 |
| 106–109 | PyMuPDF, pytesseract, nltk | PDF text and sentence splitting |
| 112–115 | pydub, azure-cognitiveservices-speech, google-cloud-texttospeech 2.27.0 | Audio |
| 118–119 | Download NLTK `punkt` and `punkt_tab` to `/usr/local/share/nltk_data` | Tokenizer data; `|| true` means a failed download is **silently ignored** |
| 122 | `FROM python:3.10-slim AS production` | Clean runtime base |
| 125–137 | apt: tesseract-ocr(+eng), poppler-utils, ffmpeg, espeak-ng, curl | ffmpeg and espeak-ng for local TTS; curl for HEALTHCHECK; tesseract and poppler are unused |
| 142–150 | `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `PYTHONPATH=/app`, `OMP/MKL/OPENBLAS/NUMBA_NUM_THREADS=8` | No `.pyc` files; logs appear immediately; `import backend...` resolves; thread counts tuned for the 8-CPU evaluation machine |
| 153 | `useradd --create-home app` | A non-root user, for security |
| 156–159 | `mkdir` data dirs, `chown -R app:app /app` | Writable by `app` |
| 162–164 | `COPY --from=python-builder` site-packages, `/usr/local/bin`, nltk_data | Only the installed results, no compilers |
| 167 | `COPY backend/` | Backend source |
| 170 | `COPY .env ./` | Runtime config **baked into the image** |
| 173 | `COPY --from=frontend-builder /app/frontend/dist` | Built UI |
| 176–177 | Copy `entrypoint.sh` and `chmod +x` | Git stores it as non-executable (mode 100644), so this is needed |
| 180 | `USER app` | Stop running as root |
| 183–184 | `HEALTHCHECK` every 30 s (timeout 10 s, start period 5 s, 3 retries) → `curl -f /api/health` | `docker ps` shows healthy or unhealthy |
| 187 | `EXPOSE 8080` | Documentation only; `-p` actually publishes the port |
| 190 | `ENTRYPOINT ["/app/entrypoint.sh"]` | Startup script |

### 7.3 What .dockerignore keeps out

[.dockerignore](../.dockerignore) excludes `.git/`, `*.md` (at the root), `frontend/node_modules/`, `frontend/dist/`, `backend/.venv/`, `__pycache__`, `backend/data/uploads/`, `backend/data/temp_audio/`, the root `data/`, IDE and OS files, logs, and anything matching `**/*test*` (for example `backend/test_tts.py`).

It does **not** exclude:
- `.env`, which the build needs;
- `backend/data/index.faiss` or `metadata*.json`, which is why you should clear a local index before building ([§6.2](#62-pre-build-checklist)).

### 7.4 entrypoint.sh walkthrough

[entrypoint.sh](../entrypoint.sh) runs these steps in order:

1. `set -e`: stop on the first error.
2. Copy `/app/.env` to `/app/.env.original`.
3. `source /app/.env.original`: every `KEY=value` line becomes a shell variable. **This overwrites any variable of the same name that was passed with `docker run -e`.**
4. Rewrite `/app/.env` using `${VAR:-default}` for a fixed list of keys, with these defaults: `LLM_PROVIDER=gemini`, `GEMINI_MODEL=gemini-2.5-flash`, `TTS_PROVIDER=azure`, `AZURE_TTS_DEPLOYMENT=tts`, `AZURE_TTS_API_VERSION=2024-08-01-preview`, `AZURE_TTS_VOICE=alloy`, `VITE_API_URL=http://localhost:8080`. `ADOBE_EMBED_API_KEY` and `VITE_ADOBE_CLIENT_ID` fill in for each other. Any **other** keys, such as `ESPEAK_VOICE` or `GCP_TTS_VOICE`, are dropped from the file; pass those with `-e`.
5. If `AZURE_TTS_KEY` or `AZURE_TTS_ENDPOINT` is empty, `sed` sets `TTS_PROVIDER=local` in `/app/.env`.
6. Log whether Google credentials were found.
7. Create `/app/backend/data/{temp_audio,uploads}` and `chmod 755` them.
8. `exec uvicorn backend.main:app --host 0.0.0.0 --port 8080 --log-level info`. `exec` replaces the shell with Uvicorn, making it process ID 1, so `docker stop`'s SIGTERM reaches it and it shuts down cleanly.

### 7.5 What happens when the container boots

1. Uvicorn imports `backend.main`. The working directory is `/app` and `PYTHONPATH=/app`.
2. The imports run in a chain:
   - `routes.py` loads `Settings` from `/app/.env` and creates `backend/data/uploads`.
   - `processing.py` checks for NLTK punkt, found in `/usr/local/share/nltk_data`.
   - `search.py` imports faiss and sentence-transformers.
   - `generation.py` creates `backend/data/temp_audio`.
   - `generate_audio.py` runs `load_dotenv()`, which copies values from `/app/.env` into the process environment.
3. `main.py` sets up logging, creates the FastAPI app with CORS `*`, and mounts the `/api` router. It then finds `/app/frontend/dist` and registers the SPA catch-all route.
4. The startup event runs `load_search_engine()`:
   - It downloads `all-MiniLM-L6-v2` into `/home/app/.cache/huggingface` on first start, or loads it from cache.
   - If `index.faiss` and `metadata.json` exist in the volume, it loads them and rebuilds BM25 from `metadata_bm25.json`.
   - Otherwise it starts with an empty `IndexFlatL2(384)`.
5. Uvicorn binds `0.0.0.0:8080` and starts accepting requests. HEALTHCHECK then turns `healthy`.

### 7.6 How requests are routed inside the container

| Request | Handled by |
|---|---|
| `/api/health`, `/api/ingest`, `/api/related-sections`, `/api/pdf/{file}`, `/api/insights`, `/api/podcast` | API router ([routes.py](../backend/app/api/routes.py)) |
| `/docs`, `/redoc`, `/openapi.json` | FastAPI's built-in docs, registered before the catch-all |
| Paths containing a dot, e.g. `/assets/index-3f2a.js` | Catch-all route serves the file from `/app/frontend/dist` |
| `/`, `/reader`, `/history`, or any other path | Catch-all returns `index.html`; React Router shows the page in the browser |
| Any other `/api/...` path | 404 |

### 7.7 Where data lives

| Data | Local path (from the project root) | Container path | Survives `docker rm`? |
|---|---|---|---|
| Uploaded PDFs | `backend/data/uploads/` | `/app/backend/data/uploads/` | Only with the `synapse-data` volume |
| FAISS index | `backend/data/index.faiss` | `/app/backend/data/index.faiss` | Only with the volume |
| Chunk metadata | `backend/data/metadata.json` | `/app/backend/data/metadata.json` | Only with the volume |
| BM25 corpus | `backend/data/metadata_bm25.json` | `/app/backend/data/metadata_bm25.json` | Only with the volume |
| Podcast MP3s (deleted about 5 minutes after being served) | `data/temp_audio/` | `/app/data/temp_audio/` | No |
| Embedding model cache | `~/.cache/huggingface/` | `/home/app/.cache/huggingface/` | No (downloaded again for each new container) |
| Runtime env | `.env` | `/app/.env` and `/app/.env.original` | Baked into the image |

### 7.8 Environment variable precedence

| Kind of variable | Examples | Read when | How to change it |
|---|---|---|---|
| Frontend (compiled into JavaScript) | `VITE_ADOBE_CLIENT_ID`, `VITE_API_URL` | Development: when `npm run dev` starts. Docker: at `docker build` | Development: restart Vite. Docker: **rebuild the image** (`-e` has no effect) |
| Backend | `GOOGLE_API_KEY`, `GEMINI_MODEL`, `TTS_PROVIDER`, `AZURE_TTS_*` | When the process starts (`load_dotenv`), then read on each call | Development: edit `.env` and restart uvicorn. Docker: see the rules below |

**Rules in Docker:**
1. The key is in the **baked `.env`** → the baked value wins, **even over `docker run -e`**, because the entrypoint `source`s the file after Docker has set the environment.
2. The key is **not** in the baked `.env` → the `-e` or `--env-file` value is used.
3. The key is in neither → the entrypoint default applies if there is one, otherwise the default in the code.
4. `TTS_PROVIDER` passed with `-e` stays as given, even when the Azure credentials are missing. The automatic `local` fallback only changes the file, and `load_dotenv` never overwrites a variable that already exists.

**Rules in local development:** real shell environment variables (`export GOOGLE_API_KEY=...`) win over `.env`, because python-dotenv doesn't override existing variables. pydantic-settings behaves the same way for the path and chunk settings.

Example of the Docker trap:

```
baked .env:     GOOGLE_API_KEY=old-key
docker run -e GOOGLE_API_KEY=new-key ...
entrypoint:     source /app/.env.original   → GOOGLE_API_KEY becomes "old-key"
result:         the app uses old-key
```

### 7.9 Known issue: the CPU-only torch pin no longer holds

**What was checked (2026-09-16).** A `pip install --dry-run sentence-transformers` was run against an installed `torch 2.1.2`, which is exactly what the Dockerfile does at lines 62–74. pip resolved to **sentence-transformers 6.0.1** and **transformers 5.17.0**, and **replaced torch with 2.14.0** from PyPI. Two current requirements cause this:
- sentence-transformers now declares `torch>=2.2`.
- transformers 5 turns PyTorch off below version 2.5 ("Disabling PyTorch because PyTorch >= 2.5 is required").

The dry-run ran on Windows with Python 3.14, but these requirements apply on every platform.

**Effect on the Docker build.**
- On Linux, PyPI's default torch is the **CUDA build**, which pulls in several GB of `nvidia-*` libraries. The build gets slower and the image much bigger, so the README's "13 minutes / 3.57 GB" no longer holds.
- pip prints a dependency-conflict error for `torchvision 0.16.2` / `torchaudio 2.1.2`. It's harmless, because the code never imports either.
- The app should still run, on the CPU.

**Fix.** Edit Dockerfile lines 62–64 to install the latest CPU build, without torchvision or torchaudio:

```dockerfile
RUN pip install --no-cache-dir --timeout=600 --retries=5 \
    torch --index-url https://download.pytorch.org/whl/cpu
```

**Keep builds reproducible from now on.** After a successful build, freeze the exact versions:

```bash
docker run --rm --entrypoint pip projectsynapse freeze > backend/requirements.lock
```

Install from that lock file in the Dockerfile and in local setup. The lesson: unpinned dependencies make yesterday's optimized build today's slow build.

---

## 8. How the code works at runtime

This is a short version. [HANDBOOK Part 3](HANDBOOK.md#part-3-end-to-end-flows) covers every step in detail.

**A. Upload to library** (HomePage → `POST /api/ingest`)
1. The browser sends a multipart form with the field `files`.
2. [routes.py](../backend/app/api/routes.py#L62-L88) checks each file ends in `.pdf`, saves it to `backend/data/uploads/<name>`, schedules `process_and_index_pdf` as a background task, and **responds immediately**.
3. After the response is sent, a thread-pool worker handles one file at a time:
   - [pdf_parser_1a.py](../backend/app/core/pdf_parser_1a.py) extracts PyMuPDF text blocks, treats **bold** short blocks as headings, and groups the text between headings into sections.
   - [processing.py](../backend/app/core/processing.py) skips sections under 5 words and splits the rest into windows of 5 sentences with 1 overlapping, each with metadata (document, section title, page, text).
   - [search.py](../backend/app/core/search.py#L233-L278) embeds the chunks with MiniLM. Under a lock, it adds them to FAISS, the metadata list and the BM25 corpus, rebuilds BM25, and writes the three files.

**B. Select text** (Adobe `PREVIEW_SELECTION_END` → `POST /api/related-sections`)
1. Only selections longer than 10 characters trigger analysis. Any previous requests are aborted.
2. Search runs in both indexes: FAISS returns the top 20 chunks by meaning, and BM25 the top 20 by keywords.
3. **Reciprocal Rank Fusion** (k = 60), keyed by (document, section, page), merges the lists. The top 10 get PDF links, duplicates of the same (document, section) are removed, and the top 5 are returned.

**C. Insights** (`POST /api/insights` with the selected text and the 5 snippets)
1. The prompt contains a role, the selected text, the numbered snippets and a markdown template: key points, contradictions and gaps, takeaways, connections.
2. Gemini 2.5 Flash (temperature 0.5, via LangChain) answers, and the response is `{"insights_text": markdown}`.

**D. Podcast** (`POST /api/podcast`, runs in the thread pool)
1. Gemini writes a first-person script of 300–500 words. The code strips markdown and caps the length at about 2000 characters, using a canned script if generation fails.
2. Azure OpenAI TTS (voice `nova`) produces the MP3, which is returned as `audio/mpeg`.
3. The file is deleted after 5 minutes.
4. The browser plays the returned blob in an `<audio>` element.

**E. Click a related section**
1. `GET /api/pdf/<doc_name>` returns the PDF as a blob, which becomes a new `File` in the viewer.
2. `gotoLocation(page)` jumps to the page. Pages are stored 0-based while Adobe counts from 1, so the jump lands one page early.

---

## 9. API reference

Set the base URL once in your shell:

```bash
BASE=http://localhost:8000      # local development
# BASE=http://localhost:8080    # Docker
```

**`GET /api/health`**

```bash
curl -s $BASE/api/health
# {"status":"healthy","service":"Project Synapse API","version":"1.0.0"}
```

**`POST /api/ingest`**: multipart form, field `files`, one or more PDFs.

```bash
curl -s -X POST $BASE/api/ingest -F "files=@/path/to/a.pdf" -F "files=@/path/to/b.pdf"
# {"message":"Processing started in background for 2 documents.",
#  "filenames":["a.pdf","b.pdf"],
#  "note":"Documents will be indexed for both semantic (FAISS) and keyword (BM25) search"}
```

- If any file isn't a `.pdf`, the response is `400` and nothing in that request gets indexed.
- Indexing finishes later. Watch the logs for `Successfully indexed N chunks from a.pdf`.

**`POST /api/related-sections`**: body `{"query_text": "..."}`.

```bash
curl -s -X POST $BASE/api/related-sections -H "Content-Type: application/json" \
  -d '{"query_text": "transfer learning methodology"}'
```

```json
[
  {
    "doc_name": "paper-a.pdf",
    "section_title": "Transfer Learning",
    "page": 2,
    "snippet": "Transfer learning reuses a model trained on a large dataset...",
    "rrf_score": 0.0481,
    "faiss_score": 0.62,
    "bm25_score": null,
    "dense_rank": 1,
    "sparse_rank": 3,
    "pdf_available": true,
    "pdf_url": "/api/pdf/paper-a.pdf"
  }
]
```

How to read the fields:
- Up to 5 items are returned; an empty library gives `[]`.
- `page` is **0-based**.
- `faiss_score` is the squared L2 distance: lower is better, and cosine similarity ≈ 1 − score/2.
- For a section found by both FAISS and BM25, only `faiss_score` is filled in; `bm25_score` stays null.
- `rrf_score` is missing when only one retriever returned results.

**`GET /api/pdf/{filename}`**

```bash
curl -s -o out.pdf "$BASE/api/pdf/paper-a.pdf"            # URL-encode spaces: My%20File.pdf
```

Returns 400 if the name contains `..`, `/` or `\`, or isn't a PDF, and 404 if the file doesn't exist.

**`POST /api/insights`**: body `{"query_text": "...", "related_snippets": ["...", "..."]}`.

```bash
curl -s -X POST $BASE/api/insights -H "Content-Type: application/json" \
  -d '{"query_text": "transfer learning", "related_snippets": ["Transfer learning reuses pretrained models.", "Fine-tuning adapts the last layers."]}'
# {"insights_text":"## 🎯 **QUICK INSIGHTS**\n• ..."}
```

An empty `related_snippets` list returns a "Not enough related content…" message without calling Gemini. On an LLM failure: `500 {"detail":"Failed to generate insights"}`.

**`POST /api/podcast`**: same body as insights; returns `audio/mpeg`.

```bash
curl -s -X POST $BASE/api/podcast -H "Content-Type: application/json" \
  -d '{"query_text": "transfer learning", "related_snippets": ["Transfer learning reuses pretrained models."]}' \
  --output podcast.mp3 --max-time 180
ls -lh podcast.mp3        # should be well over 1 KB
```

Errors:
- `503` when the message mentions Azure or TTS (a provider problem).
- `500` otherwise.
- If Gemini fails, the podcast still succeeds, but with a **generic** fallback script.

**Swagger UI:** `$BASE/docs`

---

## 10. Verification checklist

Run these from the project root with the venv active (`source backend/.venv/bin/activate`).

| # | Check | Command | Expected |
|---|---|---|---|
| 1 | Python stack imports | `python -c "import torch, sentence_transformers, faiss, fitz, rank_bm25; print(torch.__version__)"` | A version ending in `+cpu` and no errors |
| 2 | NLTK data | `python -c "import nltk; nltk.data.find('tokenizers/punkt'); nltk.data.find('tokenizers/punkt_tab'); print('ok')"` | `ok` |
| 3 | Gemini key and model | `python backend/app/scripts/chat_with_llm.py` | `LLM Response: ... Paris ...` |
| 4 | Azure TTS credentials | `python backend/test_tts.py` | `✅ Azure OpenAI TTS setup successful!` and `./test_audio.mp3` is created |
| 5 | Any TTS provider | `python backend/app/scripts/generate_audio.py` | `✅ <PROVIDER> TTS test successful` and `test_output_<provider>.mp3` |
| 6 | Backend health | `curl -s $BASE/api/health` | `"status":"healthy"` |
| 7 | Ingest | `curl -s -X POST $BASE/api/ingest -F "files=@sample.pdf"`, then check the logs | `Successfully indexed N chunks` |
| 8 | Index on disk | the inspection snippet below | Vectors = metadata rows = BM25 docs |
| 9 | Search | `curl` to related-sections ([§9](#9-api-reference)) | A non-empty JSON array |
| 10 | Insights | `curl` to insights | `insights_text` with markdown |
| 11 | Podcast | `curl` to podcast, `--output podcast.mp3` | An MP3 you can play |
| 12 | UI | Browser → upload → read → select → click | Cards, insights and audio appear; the PDF jumps |

Check 8, inspecting the index:

```bash
python - <<'EOF'
import faiss, json
idx  = faiss.read_index("backend/data/index.faiss")
meta = json.load(open("backend/data/metadata.json"))
bm25 = json.load(open("backend/data/metadata_bm25.json"))["tokenized_corpus"]
print("vectors:", idx.ntotal, "| dim:", idx.d, "| metadata:", len(meta), "| bm25:", len(bm25))
print("documents:", sorted({m["doc_name"] for m in meta}))
EOF
```

(Check 5 writes MP3 files to the directory you run it from; delete them afterwards.)

**Measure latency** before quoting any numbers:

```bash
curl -o /dev/null -s -w "related-sections: %{time_total}s\n" -X POST $BASE/api/related-sections \
  -H "Content-Type: application/json" -d '{"query_text":"your test phrase"}'
```

---

## 11. Troubleshooting

Each problem is listed as **symptom**, then **cause**, then **fix**.

### Setup and installation

**`ModuleNotFoundError: No module named 'backend'`**
- **Cause:** uvicorn was started inside `backend/`.
- **Fix:** from the project root, run `uvicorn backend.main:app ...`.

**pip downloads huge `nvidia-*` packages**
- **Cause:** torch came from PyPI instead of the CPU index.
- **Fix:** `pip uninstall -y torch` then `pip install torch --index-url https://download.pytorch.org/whl/cpu`, then reinstall the requirements.

**Startup crashes with a `LookupError` mentioning `punkt`**
- **Cause:** NLTK data is missing.
- **Fix:** download both `punkt` and `punkt_tab` ([§5.3](#53-download-nltk-data)).

**Logs say "Disabling PyTorch because PyTorch >= X is required", or "requires the PyTorch library but it was not found"**
- **Cause:** torch is too old for the installed transformers.
- **Fix:** install the latest CPU torch (§5.2). For Docker, apply [§7.9](#79-known-issue-the-cpu-only-torch-pin-no-longer-holds).

**`pip install -r backend/requirements.txt` fails to build a package**
- **Cause:** the Python version is wrong (for example 3.12+ with older pins), or build tools are missing.
- **Fix:** use Python 3.10 (Ubuntu 22.04 or `uv venv --python 3.10`), and `sudo apt install build-essential python3-dev libffi-dev`.

**`npm ci` fails with "package.json and package-lock.json are not in sync"**
- **Cause:** the lockfile has drifted from `package.json`.
- **Fix:** in `frontend/`, run `npm install` (this updates the lockfile), then `npm ci` or rebuild.

**npm or pip is very slow, or file watching doesn't work**
- **Cause:** the project is under `/mnt/c/...`.
- **Fix:** move it to `~/projects` ([§4.5](#45-get-the-code-into-the-linux-filesystem)).

**Vite fails to bind to `::`**
- **Cause:** IPv6 isn't available in WSL.
- **Fix:** `npm run dev -- --host 0.0.0.0`.

**"Port 8080 already in use"**
- **Cause:** the Docker container, or another Vite instance, is using 8080.
- **Fix:** `docker stop synapse`, or run `npm run dev -- --port 5173`. Adobe still works on localhost, and the page's CSP allows any localhost port. To find the process: `ss -ltnp | grep 8080`.

### In the UI

**"VITE_ADOBE_CLIENT_ID is not configured."**
- **Cause:** the key was missing when Vite started, or when the image was built.
- **Fix:** add it to the **root** `.env`, then restart `npm run dev` or rebuild the image.

**Blank viewer, or an Adobe "invalid client ID" / domain error**
- **Cause:** the credential's domain doesn't match the host in the address bar.
- **Fix:** register the credential for `localhost` and open `http://localhost:PORT`, not `127.0.0.1`.

**"Failed to load Adobe SDK."**
- **Cause:** `acrobatservices.adobe.com` is blocked (no internet, VPN, proxy or ad-blocker).
- **Fix:** allow the domain, or try a different network.

**Upload shows "Upload failed: Failed to fetch"**
- **Cause:** the backend isn't running, `VITE_API_URL` is wrong, or a CORS or CSP rule is blocking the request.
- **Fix:** check `curl localhost:8000/api/health`. Development needs `VITE_API_URL=http://localhost:8000`; restart Vite after editing `.env`.

**Upload works, but you always see "No related sections found."**
- **Cause:** (a) indexing is still running or failed; (b) the PDF has no bold headings or is scanned, so 0 chunks were created ("No meaningful text chunks were extracted"); (c) the selection was 10 characters or fewer.
- **Fix:** read the backend logs, and try a PDF that has bold headings.

**"PDF not available for this section."**
- **Cause:** the index references a PDF that isn't in `uploads/`. This happens with a stale index baked into the Docker image, or when uploads were deleted.
- **Fix:** reset the library (all three index files plus uploads) and upload the PDFs again ([§5.8](#58-reset-the-library), [§6.2](#62-pre-build-checklist)).

**Clicking a section lands one page early, or doesn't move for first-page sections**
- **Cause:** a known off-by-one: pages are stored 0-based, but Adobe's `gotoLocation` counts from 1.
- **Fix:** a code fix is needed. Send `page + 1` from the backend, or add 1 before calling `gotoLocation`.

**"Analysis Failed: Failed to generate insights."**
- **Cause:** a Gemini problem: the key is missing or invalid, the model name is retired (404), or you're over quota (429).
- **Fix:** read the backend traceback and run `python backend/app/scripts/chat_with_llm.py`. If the key and model are definitely valid, the pinned 2025-era Gemini SDKs (`langchain-google-genai 2.0.10`, `google-generativeai 0.8.5`) may be too old for current models; upgrading them means changing code and dependencies.

**"Text-to-speech service is currently unavailable…" (HTTP 503)**
- **Cause:** one of the Azure settings is wrong: key, endpoint (check for a trailing slash), deployment name, or API version.
- **Fix:** run `python backend/test_tts.py`; the backend log also prints Azure's response text. Or set `TTS_PROVIDER=local`.

**The podcast plays but sounds generic and doesn't mention your documents**
- **Cause:** script generation with Gemini failed, so the canned fallback script was used.
- **Fix:** fix Gemini (see "Failed to generate insights" above).

**The podcast takes a long time**
- **Cause:** by design, it runs after the related sections and insights have finished, and it involves an LLM call plus TTS (up to a 30 s timeout).
- **Fix:** wait. To speed it up, change the frontend to run insights and the podcast in parallel.

**Local TTS errors: "espeak-ng is not installed", "Failed to convert WAV to MP3", or "Failed to read voice"**
- **Cause:** espeak-ng or ffmpeg is missing. Or espeak doesn't accept the OpenAI voice name `nova` that generation.py passes.
- **Fix:** `sudo apt install espeak-ng ffmpeg`. If the voice name is rejected, change the `voice="nova"` argument for the local provider.

**Insights show raw `##` and `**` characters**
- **Cause:** the UI doesn't render markdown.
- **Fix:** expected behaviour. Rendering it would need a UI change such as adding react-markdown.

### Docker

**Build fails with `"/.env": not found`**
- **Cause:** there's no `.env` in the project root.
- **Fix:** create it ([§3](#3-the-env-file)).

**Build is very slow, or the image is huge**
- **Cause:** the torch pin is overridden and the CUDA build gets installed ([§7.9](#79-known-issue-the-cpu-only-torch-pin-no-longer-holds)).
- **Fix:** apply the §7.9 Dockerfile fix.

**pip timeouts during the build**
- **Cause:** a slow or unreliable network.
- **Fix:** run the build again; finished layers are cached. Check your VPN or proxy.

**Container exits immediately with `exec /app/entrypoint.sh: no such file or directory`**
- **Cause:** `entrypoint.sh` has CRLF line endings.
- **Fix:** `sed -i 's/\r$//' entrypoint.sh`, rebuild, and consider adding a `.gitattributes` file containing `*.sh text eol=lf`.

**Container is stuck in `starting`, or becomes `unhealthy`**
- **Cause:** the model is still downloading, or it can't download (no internet), or the app crashed.
- **Fix:** read `docker logs synapse`.

**The UI loads, but every API call fails**
- **Cause:** the container is published on a different host port (for example `-p 3000:8080`), but the frontend calls `http://localhost:8080`.
- **Fix:** use `-p 8080:8080`.

**You changed keys with `-e`, but nothing changed**
- **Cause:** the same keys are in the baked `.env`, and the baked values win ([§7.8](#78-environment-variable-precedence)).
- **Fix:** rebuild with an updated `.env`, or remove those keys from `.env` and use `--env-file` ([§6.7](#67-passing-secrets-at-runtime-instead)).

**You changed the Adobe key, but the viewer still uses the old one**
- **Cause:** `VITE_*` values are compiled in during the build.
- **Fix:** rebuild the image.

**Uploaded data disappeared after `docker rm`**
- **Cause:** no volume was mounted.
- **Fix:** add `-v synapse-data:/app/backend/data`.

**Build is `Killed`, or WSL freezes**
- **Cause:** WSL ran out of memory.
- **Fix:** raise the limits in `.wslconfig` ([§4.2](#42-optional-give-wsl-more-memory)) and run `wsl --shutdown`.

**`docker: command not found` inside WSL**
- **Cause:** Docker Desktop's WSL integration is off.
- **Fix:** enable it for Ubuntu-22.04 ([§6.1](#61-get-docker-working-inside-wsl)).

**`permission denied ... docker.sock`**
- **Cause:** you're using Docker Engine in WSL, and your user isn't in the `docker` group.
- **Fix:** `sudo usermod -aG docker $USER`, then reopen the terminal.

**Keys look right but authentication still fails (401/403)**
- **Cause:** `.env` has CRLF line endings, so each value ends with an invisible `\r`.
- **Fix:** `sed -i 's/\r$//' .env`, then rebuild or restart.

---

## 12. Docs vs code

| Where | What it says | What the code actually does |
|---|---|---|
| README, development setup | `cd backend && uvicorn main:app --port 8000` | Run from the root: `uvicorn backend.main:app --port 8000` |
| README | `cp .env.example .env` | There's no `.env.example`; use the template in [§3](#3-the-env-file) |
| README | Development URL `http://localhost:5173` | Vite runs on **8080** |
| README | Docker run with only `GOOGLE_APPLICATION_CREDENTIALS` | The LLM needs `GOOGLE_API_KEY` |
| README | "2-speaker podcast", "Azure Cognitive Services TTS" | One narrator; Azure **OpenAI** `tts` over REST |
| README | "13 min build, 3.57 GB image" | True at hackathon time; dependency drift undoes it today ([§7.9](#79-known-issue-the-cpu-only-torch-pin-no-longer-holds)) |
| DEBUG.md | `POST /api/upload`, `POST /api/query` | The endpoints are `/api/ingest` and `/api/related-sections` |
| DEBUG.md | `nltk.download('punkt')` | You also need `punkt_tab` |
| DEBUG.md | "Docker environment variables (highest priority)" | A key in the baked `.env` overrides `docker run -e` |
| frontend/README.md | Put `.env` in `frontend/`; `setup-env.sh`; `TROUBLESHOOTING.md` | Vite reads the **root** `.env`; the script and file don't exist |

---

## 13. Security notes

1. **Rotate exposed keys.** Commit `4dd5ea7` (DEBUG.md, Aug 20 2025) contained what look like a real **Google API key** and a real **Azure TTS key and endpoint**. Commit `56e2837` removed them from the file, but they're **still in the git history**, and the repo has a GitHub remote. Revoke and regenerate both keys, in Google AI Studio and in the Azure portal. Purging the history (with `git filter-repo`) is optional; rotating the keys is what actually protects you. `DEBUG.md` also still shows an Adobe client ID; that's low risk, since client IDs are public and tied to a domain.
2. **Your `.env` is inside the image** (`COPY .env`), and the build log prints it (`RUN cat /app/.env`). Don't push the image to a public registry or share build logs. Prefer passing secrets at runtime ([§6.7](#67-passing-secrets-at-runtime-instead)).
3. **No authentication, and CORS allows `*`.** Anyone who can reach the port, and any website open in your browser, can upload files and spend your Gemini and Azure quota. Run the app only on localhost, or put it behind authentication.
4. **Likely path traversal in the SPA catch-all route.** [main.py](../backend/main.py#L71-L75) joins the raw request path onto the `dist` folder without normalizing it. You can check this against your own container:
   ```bash
   curl --path-as-is -s http://localhost:8080/../../.env
   ```
   If that prints your keys, the hole is real. The fix: resolve `os.path.realpath(file_path)` and serve the file only if it's still inside `static_dir`, or use Starlette's `StaticFiles`.
5. **Upload file names aren't sanitized** ([routes.py](../backend/app/api/routes.py#L74)). Use `os.path.basename` or a generated UUID name, add a size limit, and check that the file starts with `%PDF-`.
6. **Prompt injection.** Text inside a PDF goes straight into the LLM prompt. The impact is limited, because the model only produces text, but don't treat its output as trusted.

---

## 14. Command cheat sheet

```bash
# ---------- Setup (once) ----------
wsl --install -d Ubuntu-22.04                                                          # PowerShell (Admin)
sudo apt update && sudo apt install -y git curl build-essential python3-venv python3-pip python3-dev libffi-dev ffmpeg espeak-ng
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash && source ~/.bashrc && nvm install 22
mkdir -p ~/projects && cd ~/projects && git clone https://github.com/SuryanshT01/projectSynapse.git && cd projectSynapse
nano .env                                                                              # template in §3

# ---------- Backend (from the project root) ----------
python3 -m venv backend/.venv && source backend/.venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install -r backend/requirements.txt
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend

# ---------- Frontend ----------
cd frontend && npm ci && npm run dev                                                   # http://localhost:8080

# ---------- Checks ----------
curl -s localhost:8000/api/health
python backend/app/scripts/chat_with_llm.py      # Gemini
python backend/test_tts.py                       # Azure TTS

# ---------- Reset the library ----------
rm -f backend/data/index.faiss backend/data/metadata.json backend/data/metadata_bm25.json && rm -rf backend/data/uploads/*

# ---------- Docker ----------
docker build -t projectsynapse .
docker run -d --name synapse -p 8080:8080 -v synapse-data:/app/backend/data projectsynapse
docker logs -f synapse
docker exec -it synapse bash
docker rm -f synapse && docker volume rm synapse-data                                  # wipe everything
```
