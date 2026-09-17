# Project Synapse Resume and Interview Handbook

This is your prep kit for putting Project Synapse on your resume and defending it in interviews. It covers pitches, resume bullets, an architecture talk track, design trade-offs, numbers to remember, the project's honest gaps, and about 95 interview questions with model answers based on the actual code.

Companion docs: [HANDBOOK.md](HANDBOOK.md) (concepts and theory) and [RUNBOOK.md](RUNBOOK.md) (setup and deployment).

> **Golden rule: never claim anything the code doesn't do.** An interviewer who digs will find the mismatch. §9 lists every gap between the README and the code, with a way to talk about each one confidently. "Here's the trade-off I made, and here's how I'd fix it" beats overclaiming every time.

## Contents

0. [How to prepare](#0-how-to-prepare)
1. [Project fact sheet](#1-project-fact-sheet)
2. [Who built what](#2-who-built-what)
3. [Pitches](#3-pitches)
4. [Resume bullets](#4-resume-bullets)
5. [Architecture talk track](#5-architecture-talk-track)
6. [Deep-dive briefs](#6-deep-dive-briefs)
7. [Design decisions and trade-offs](#7-design-decisions-and-trade-offs)
8. [Numbers to remember](#8-numbers-to-remember)
9. [Honest gaps and how to talk about them](#9-honest-gaps-and-how-to-talk-about-them)
10. [Interview Q&A bank](#10-interview-qa-bank)
11. [Whiteboard drills](#11-whiteboard-drills)
12. [Code to write from memory](#12-code-to-write-from-memory)
13. [Questions to ask the interviewer](#13-questions-to-ask-the-interviewer)
14. [Last-hour cheat sheet](#14-last-hour-cheat-sheet)

---

## 0. How to prepare

| When | Do this |
|---|---|
| 1 week before | Run the app end to end ([RUNBOOK](RUNBOOK.md)). Read [HANDBOOK](HANDBOOK.md) Parts 1–3, then §5–§9 of this document. |
| 3 days before | Say the pitches (§3) out loud and time them. Draw the architecture (§5) from memory. Do the whiteboard drills (§11). |
| 1–2 days before | Answer the §10 questions out loud without looking. Mark the weak ones and reread the matching HANDBOOK sections. Rehearse two STAR stories (§10 M). |
| 1 hour before | Review §14 (cheat sheet) and §8 (numbers). |

**Tip:** have a 60-second demo ready, either a screen recording or the images in `screenshots/`, in case the interviewer asks to see it.

---

## 1. Project fact sheet

| Field | Value |
|---|---|
| Name | Project Synapse: "From information chaos to connected clarity" |
| Context | Adobe Hackathon 2025, "Connecting the Dots" challenge (Round 1A → Round 1B → Finale) |
| Team | 2 people. Git history shows Suryansh Tripathi (you) with 22 commits and Reetika with 10 |
| Timeline | About 6 days of building, 15–20 Aug 2025, with README polish in Sep 2025 |
| One-liner | While you read a PDF and highlight text, it finds related sections across your PDF library, generates AI insights, and narrates an audio summary |
| Core technique | Hybrid retrieval (dense embeddings + BM25) combined with RRF → RAG with Gemini → text-to-speech |
| Backend | Python 3.10, FastAPI, Uvicorn, sentence-transformers (all-MiniLM-L6-v2), FAISS, rank-bm25, PyMuPDF, NLTK, LangChain with Gemini 2.5 Flash, Azure OpenAI TTS, pydub |
| Frontend | React 18, TypeScript, Vite, React Router, Tailwind with shadcn/ui, Adobe PDF Embed API |
| Deployment | One Docker image: 3-stage build, non-root user, health check, port 8080 |
| Code size | About 1.7k lines of backend Python and about 2.2k lines of app TypeScript/TSX (not counting the generated `ui/` components) |
| Endpoints | 6: health, ingest, related-sections, pdf, insights, podcast |
| Outcome | ⟨fill in: finalist / rank / judges' feedback⟩ |

---

## 2. Who built what

Interviewers often ask *"What exactly did YOU do?"* The table below is based on commit authorship. Commits are only a proxy (for example, pair-programmed work shows under one name), so adjust it to what really happened.

| Area | Commits | Author |
|---|---|---|
| Backend foundation: FastAPI routes, config, processing, search (FAISS), generation, parser v1 (from Round 1A), first Dockerfile | `68c9897` | **You** |
| Adobe PDF Embed API integration: viewer component, SDK hook, typings, reader flow, working text selection | `9106dc9`, `064936d`, `d7edfaa` | **You** |
| Hybrid search: BM25 + RRF + PDF links | `252bd68` | **You** |
| Related-sections API connected to the UI | `d99b663` | **You** |
| LLM integration and prompts | `15b1f6e`, `faabe02` | **You** |
| TTS service, podcast API and sidebar UI, Azure TTS fix | `4f83c37`, `010da25`, `8663f3e` | **You** |
| One root `.env` shared by frontend and backend (Vite `envDir`) | `4913e6c` | **You** |
| Docker optimization, `.dockerignore`, `entrypoint.sh`, SPA serving in `main.py`, DEBUG.md, README, screenshots | `c15177c`, `4dd5ea7`, `8b5176b` | **You** |
| Frontend scaffold: React/Vite/shadcn app, HomePage, sidebars, History page | `72017ee` | Reetika |
| Library upload wired to `/api/ingest` | `6ccdf52` | Reetika |
| PDF processing rewrite ("better chunks"): heading heuristic and chunk settings | `b9d15de` | Reetika |
| Jump-to-page navigation with `gotoLocation` | `5a632bf` | Reetika |
| Content-Security-Policy updates | `47ee665` | Reetika |

**How to say it:** *"We were a team of two. I owned the backend and AI side, meaning retrieval and the LLM and TTS integrations, plus the Adobe viewer integration and the Docker deployment. My teammate built the React scaffold, the upload flow and page navigation, and rewrote the PDF parser to produce better chunks."*

---

## 3. Pitches

### 3.1 The 30-second pitch

> "Project Synapse is an AI reading assistant for PDF libraries that I co-built in a six-day Adobe hackathon. When you highlight a passage in a PDF, it instantly finds the most related sections across all your other documents. It does that with hybrid search: sentence-transformer embeddings in FAISS plus BM25 keyword search, merged with Reciprocal Rank Fusion. Then it uses Gemini to generate grounded insights, like key points and contradictions, and narrates a short audio summary with Azure OpenAI text-to-speech. I built the retrieval engine, the AI integrations and the Docker deployment."

### 3.2 The 90-second pitch (problem → solution → how → engineering)

> "**Problem:** researchers and students keep libraries of PDFs, but Ctrl+F only finds exact words in one file. You can't easily see where else an idea appears, or whether another paper contradicts it.
>
> **Solution:** Synapse makes what you're reading the search query. You open a PDF in Adobe's embedded viewer and highlight some text. A sidebar shows the five most related sections from your library, AI insights and an audio summary, and clicking a result opens that PDF at the right section.
>
> **How it works:** on upload, a background task parses each PDF with PyMuPDF, splits it into sections by detecting headings, and cuts each section into overlapping five-sentence chunks. Every chunk is embedded with all-MiniLM-L6-v2 into a FAISS index and also indexed with BM25. When you select text, we run both searches, combine the rankings with Reciprocal Rank Fusion, and return the top sections. Those snippets go into prompts for Gemini 2.5 Flash, which is a RAG pipeline, and the podcast script goes through Azure OpenAI TTS.
>
> **Engineering:** a FastAPI backend with background ingestion and LLM and TTS calls moved onto a thread pool, a React and TypeScript frontend, and a single Docker image built in three stages. Installing CPU-only PyTorch first cut our build from about 75 minutes to 13, and the image from 14 GB to 3.6."

### 3.3 The 5-minute walkthrough (with a whiteboard)

| Time | Section | Key points |
|---|---|---|
| 0:00–0:30 | Problem | Information is scattered across PDFs; keyword search misses ideas; the hackathon theme was "Connecting the Dots" |
| 0:30–1:10 | Demo flow | Upload library → open PDF → select text → related sections → insights → audio → click to jump |
| 1:10–2:10 | Architecture | Draw §5. Two pipelines: ingestion (in the background) and query (on each selection). One FastAPI process keeps the model and indexes in memory |
| 2:10–3:20 | Retrieval deep dive | Chunking (5 sentences, overlap 1, inside sections) → MiniLM 384-dimension normalized vectors → FAISS flat L2 (equivalent to cosine for unit vectors) + BM25 → top 20 from each → RRF with k=60 at section level → top 5 |
| 3:20–4:00 | AI layer | RAG prompt design (role, delimiters, a template that includes contradictions), temperature 0.5, output cleanup and fallbacks; podcast script → TTS |
| 4:00–4:30 | Engineering | Background tasks, `run_in_threadpool`, a lock around index writes, AbortController, multi-stage Docker with CPU-only torch |
| 4:30–5:00 | Reflection | What I'd improve: citations, re-ranking, an evaluation set, async fixes, job status, authentication, lock files |

---

## 4. Resume bullets

**Rules:** start with a strong verb, name the technique, and include a number you can defend. Pick the 3–4 bullets that fit the role.

### ML / AI engineer
- Built a **hybrid retrieval engine** for a PDF knowledge assistant, combining all-MiniLM-L6-v2 embeddings in **FAISS** with **BM25** keyword scoring through **Reciprocal Rank Fusion** at section level, to return the top 5 related sections across a user's library from a text selection.
- Implemented a **RAG** layer on **Gemini 2.5 Flash** (LangChain) that turns retrieved snippets into structured insights (key points, contradictions and gaps, takeaways) and a narrated audio summary via **Azure OpenAI TTS**, with output sanitization, length control and fallbacks.
- Co-designed the ingestion pipeline (PyMuPDF extraction → heading-based sections → overlapping 5-sentence windows → dense + sparse indexes saved to disk), running as non-blocking background tasks. *(Co-designed: your teammate rewrote the parser and chunking for the finale.)*

### Backend engineer
- Developed a **FastAPI** service with 6 endpoints for PDF ingestion, hybrid search, LLM insights, audio generation and PDF streaming; ran indexing as **background tasks** and moved blocking LLM and TTS calls onto a **thread pool**.
- Managed shared in-memory search state (FAISS, BM25, metadata) with **lock-protected writes** and on-disk persistence, configured through environment variables (pydantic-settings) with swappable TTS providers (Azure / GCP / local).
- **Containerized** the full stack with a **3-stage Docker build** (Node build → Python dependencies → slim non-root runtime with a health check); installing CPU-only PyTorch first cut build time from **~75 to ~13 min** and image size from **14.1 GB to 3.57 GB**.

### Full-stack
- Integrated the **Adobe PDF Embed API** into a **React + TypeScript** app: a text selection triggers a related-sections → insights → audio pipeline, results link straight into the source PDFs, and outdated requests are cancelled with **AbortController**.
- Add one retrieval bullet and the Docker bullet from above.

### One-liner, for a crowded resume
- **Project Synapse** (Adobe Hackathon 2025): AI PDF reading assistant with hybrid semantic + keyword search (FAISS, BM25, RRF), Gemini-powered insights and TTS audio summaries. FastAPI, React/TypeScript, Docker.

### Skills line
Python, FastAPI, React, TypeScript, sentence-transformers, FAISS, BM25, RAG, LangChain, Gemini, Azure OpenAI, Docker, WSL/Linux.

### Which numbers are safe to quote

| Number | Source | Safe to quote? |
|---|---|---|
| Build 75 → 13 min; image 14.1 → 3.57 GB | README, measured during the hackathon | **Yes**, if you can explain how it was measured (`time docker build`, `docker images`) and why (CUDA vs CPU torch wheels). Also know that today's unpinned dependencies undo it (§9) |
| Top 5 results, 5-sentence chunks, k=60, 384 dimensions | The code | **Yes** |
| "< 500 ms per query", "sub-second", "~100 docs/min" | README claims, never measured in the repo | **Only after you measure them** (RUNBOOK §10 has a curl timing command). Until then, say "fast enough to feel instant on a personal library" |

---

## 5. Architecture talk track

**Draw this:**

```
                ┌──────────────────────────────┐
  User ───────► │ React SPA + Adobe PDF viewer │
                └──────────────┬───────────────┘
                               │ REST /api/*
                ┌──────────────▼───────────────┐
                │ FastAPI (Uvicorn, 1 process) │
                │  in RAM: MiniLM · FAISS ·    │
                │          BM25 · metadata     │
                └──┬────────────┬───────────┬──┘
                   │            │           │
            ┌──────▼─────┐ ┌────▼─────┐ ┌───▼──────────┐
            │ disk:      │ │ Gemini   │ │ Azure OpenAI │
            │ PDFs +     │ │ 2.5 Flash│ │ TTS          │
            │ index files│ └──────────┘ └──────────────┘
            └────────────┘
```

**While you draw, say:**

1. "Users upload PDFs. FastAPI saves them and returns right away, while a **background task** parses, chunks, embeds and indexes each one."
2. "Everything search needs lives in **RAM in one process**: the MiniLM model, the FAISS index, BM25 and the chunk metadata. It's saved to three files on disk."
3. "Reading happens in **Adobe's PDF Embed API**. Its selection-end event gives us the text the user highlighted."
4. "That text is the query. We embed it and take FAISS's top 20, tokenize it and take BM25's top 20, **fuse the two lists with RRF** at section level, and return the top 5 with links."
5. "The frontend sends those snippets to `/insights`, which is a RAG prompt to Gemini, and then to `/podcast`, where Gemini writes a script and Azure OpenAI TTS voices it."
6. "Clicking a result fetches that PDF from `/api/pdf` and jumps to the section's page."
7. "In production it's **one Docker container**: FastAPI serves both the API and the built React app on port 8080."

---

## 6. Deep-dive briefs

Short, dense answers for when the interviewer digs in. Each one links to the full explanation in the HANDBOOK.

### 6.1 Hybrid retrieval and RRF
- **Why hybrid?** Dense search catches paraphrases but can blur exact terms. BM25 catches names, acronyms and codes but misses synonyms.
- **How it works:** FAISS top 20 and BM25 top 20 → RRF with `score = Σ 1/(60 + rank)` → keep the top 10 → remove duplicates by (document, section) → return the top 5.
- **The subtle part:** the fusion key is `(doc_name, section_title, page)`, so **several chunks from the same section add up**. That rewards sections with several relevant chunks.
- **Example:** rank 1 in FAISS plus rank 3 in BM25 gives 1/61 + 1/63 = **0.0323**.
- **Weak spots:** BM25 returns zero-score results, the tokenizer is naive, there's no re-ranking, and the section you're reading can match itself.
- Full explanation: [HANDBOOK §2.10](HANDBOOK.md#210-hybrid-search-and-reciprocal-rank-fusion-rrf).

### 6.2 Embeddings and FAISS
- **The model:** all-MiniLM-L6-v2 has 6 layers and about 22M parameters, produces 384-dimension vectors with mean pooling and **L2 normalization**, and takes at most 256 word pieces.
- **The index:** `IndexFlatL2`, meaning exact search. For unit vectors, ‖a−b‖² = 2 − 2cos(a, b), so it ranks exactly like cosine similarity.
- **Mapping IDs to text:** FAISS IDs are just positions, and `METADATA[i]` holds the text for vector i.
- **Memory:** about 1.5 KB per vector.
- **Scaling path:** IVF/HNSW or a vector database.
- Full explanation: [HANDBOOK §2.6–2.8](HANDBOOK.md#26-transformers-bert-sentence-bert-and-all-minilm-l6-v2).

### 6.3 Chunking and parsing
- **Parsing:** PyMuPDF gives text blocks. A block is a heading if its font name contains "Bold", it has 1–29 words, has no bullet, and doesn't end with punctuation.
- **Sections:** the text between two headings forms one section.
- **Chunks:** Punkt splits sentences, then a 5-sentence window moves forward 4 sentences at a time, so neighbouring chunks overlap by one.
- **History:** in Round 1A this was a LightGBM classifier with OCR. Your teammate replaced it with the heuristic.
- **Limits:** PDFs without bold headings produce 0 chunks, scanned PDFs aren't handled, and pages are 0-based.
- Full explanation: [HANDBOOK §2.2–2.4](HANDBOOK.md#22-document-structure-headings-and-sections).

### 6.4 RAG and prompts
- **Retrieve:** the top 5 snippets.
- **Augment:** a prompt with a role, clearly delimited SELECTED TEXT and numbered RELATED CONTENT, and a markdown template (quick insights, key points, critical notes about contradictions and gaps, takeaways, connections).
- **Generate:** Gemini 2.5 Flash at temperature 0.5.
- **Guards:** an empty-snippet short-circuit, an empty-response check, and markdown stripping, length caps and a fallback script for the podcast.
- **Weaknesses:** no citations or source labels, and the prompt allows "your own knowledge".
- Full explanation: [HANDBOOK §2.11–2.12](HANDBOOK.md#211-retrieval-augmented-generation-rag).

### 6.5 Podcast and TTS
- **Script:** Gemini writes 300–500 words, which are cleaned and capped at about 2,000 characters.
- **Voice:** the script goes to Azure OpenAI's `tts` deployment over REST with voice `nova`, and comes back as an MP3.
- **Delivery:** the MP3 is returned as `audio/mpeg` and deleted after 5 minutes.
- **Providers:** azure, gcp or local (espeak-ng).
- **Honest detail:** it's a **single narrator**, not the two speakers the README describes. A two-speaker design would tag speaker turns, synthesize each turn in a different voice, and stitch them together with pydub.
- Full explanation: [HANDBOOK §2.13](HANDBOOK.md#213-text-to-speech-and-the-podcast).

### 6.6 Concurrency
- **Ingestion:** BackgroundTasks runs after the response is sent, on the thread pool, one file after another.
- **Podcast:** runs through `run_in_threadpool`.
- **Index writes:** protected by a `threading.Lock`.
- **Be honest:** `/insights` and `/related-sections` do blocking work inside `async def`, which stalls the event loop.
- **Scaling limit:** state lives in a single process, so multiple workers would each hold a different index.
- Full explanation: [HANDBOOK §2.14](HANDBOOK.md#214-backend-engineering-concepts).

### 6.7 Docker
- **Three stages:** a Node stage builds the frontend, a Python builder installs dependencies (CPU torch first), and a slim runtime image runs the app.
- **Runtime hardening:** non-root user, HEALTHCHECK, and an entrypoint that ends with `exec uvicorn`.
- **Env gotcha:** a baked-in `.env` overrides `docker run -e`.
- **The lesson:** unpinned sentence-transformers now forces a newer torch from PyPI (the CUDA build), which undoes the optimization. Lock your dependencies.
- Full explanation: [RUNBOOK §7](RUNBOOK.md#7-how-the-build-and-deployment-work).

### 6.8 Adobe PDF Embed integration
1. Load `viewer.js` and wait for the `adobe_dc_view_sdk.ready` event.
2. Create `new AdobeDC.View({clientId, divId})`.
3. Register a callback for `PREVIEW_SELECTION_END` with `enableFilePreviewEvents: true`, **before** showing the file.
4. Call `previewFile` with the file as an ArrayBuffer.
5. Call `getAPIs()` to get `getSelectedContent()` and `gotoLocation(page)`. Pages are **1-based** there, while the backend stores them 0-based, which causes an off-by-one bug.

Full explanation: [HANDBOOK §2.15](HANDBOOK.md#215-frontend-concepts).

---

## 7. Design decisions and trade-offs

| Decision | Why (hackathon context) | Trade-off / risk | What I'd do at scale |
|---|---|---|---|
| Local all-MiniLM-L6-v2 embeddings | Fast on CPU (the evaluation machine had no GPU), small, free, and documents never leave the machine | English-centric, 256-token limit, lower quality than bigger models | Benchmark bge / e5 / API embeddings on an evaluation set |
| FAISS `IndexFlatL2` inside the process | No infrastructure, exact results, easy to ship in one container | No deletes, no filters, single-process state, non-atomic saves | A vector database (pgvector / Qdrant) with ANN search and metadata filters |
| Hybrid search (dense + BM25) | Users select both concepts and exact terms | Two indexes to maintain; BM25 is rebuilt on every upload | A search engine with native hybrid search (OpenSearch / Elasticsearch) |
| Reciprocal Rank Fusion | Needs no score normalization and no tuning | Throws away score magnitudes | Tuned weighted fusion or learned ranking once labeled data exists |
| Fusion keyed by section | Rewards sections with several matching chunks; matches the UI, which shows sections | A long section can dominate | Normalize by chunk count, or cap each section's contribution |
| 5-sentence windows inside sections | Precise, fits the model, never crosses a topic boundary | Arbitrary size; page is the heading's page | Tune on an evaluation set; store each chunk's own page |
| Bold-font heading heuristic instead of LightGBM | Simpler, fewer failure points, good on well-formatted PDFs | Misses non-bold headings; no OCR | Heuristic plus ML fallback plus OCR; layout-aware parsing |
| FastAPI BackgroundTasks for ingestion | Upload returns instantly, with nothing extra to run | No status, no retry, lost on crash, competes with the API for CPU | A task queue (Celery / RQ / Arq) with workers and a job status API |
| Global in-memory state protected by a lock | Very fast queries, simple code | Can't run multiple workers or replicas | Move state to external stores; keep API servers stateless |
| Gemini 2.5 Flash at temperature 0.5 | Fast and cheap; the evaluation setup provided Gemini credentials | Some hallucination risk | Lower temperature for insights, citations, groundedness evaluation |
| Thin LangChain wrapper as the single LLM gateway | Easy to swap providers | An extra dependency for a single call | Keep the gateway pattern; add retries, timeouts, streaming, tracing |
| Azure OpenAI TTS with a provider switch | Good voices; local fallback when there are no credentials | Network latency and cost; 30-second timeout | Stream audio; synthesize per paragraph in parallel; cache results |
| Single-narrator podcast | One TTS call, so the demo is reliable | Less engaging than two voices | A two-speaker script with per-turn voices, stitched with pydub |
| Sequential frontend calls | Simplest orchestration | Podcast waits for insights; one failure blocks the next step | Run insights and podcast in parallel after retrieval; stream; make audio on-demand |
| One container serving both the SPA and the API | Same origin (no CORS), one port, simple evaluation | Frontend and backend can't be scaled separately | CDN for static files, separate API service |
| CPU-only torch in a multi-stage Docker build | Faster build, much smaller image | Easy to break by dependency drift | Lock files and CI rebuilds |
| `.env` baked into the image at build time | Worked out of the box for the evaluators | Secrets inside the image; `-e` can't override them | Inject secrets at runtime or from a secrets manager |

---

## 8. Numbers to remember

| What | Value |
|---|---|
| Embedding model | all-MiniLM-L6-v2: 6 layers, ~22M parameters, ~90 MB |
| Vector size | 384 float32 numbers, L2-normalized (~1.5 KB each) |
| Model input limit | 256 word pieces |
| Chunking | 5 sentences, overlap 1 (window moves 4 sentences); sections with fewer than 5 words are skipped |
| Heading rule | Font name contains "bold", 1–29 words, no bullet, no ending `. ? ! ,` |
| FAISS index | `IndexFlatL2` (exact); `faiss_score` is squared L2, so cosine ≈ 1 − score/2 |
| BM25 | `BM25Okapi`: k1 = 1.5, b = 0.75, ε = 0.25; tokenizer is `lower().split()` |
| Retrieval depth | 20 per retriever (`TOP_K_SEARCH` 10 × 2) → top 10 after fusion → deduplicated → `MAX_RESULTS` 5 |
| RRF | k = 60; key = (doc_name, section_title, page) |
| Selection trigger | More than 10 characters |
| LLM | Gemini 2.5 Flash, temperature 0.5, called through LangChain `ChatGoogleGenerativeAI` |
| Podcast script | Targets 300–500 words; < 100 characters → fallback script; > 2,000 → cut to ≤ 1,800 |
| TTS | Azure OpenAI `tts` over REST, voice `nova`, 30 s timeout; file deleted after 300 s; must be > 1 KB |
| OpenAI TTS input limit | 4,096 characters per request |
| API | 6 endpoints; port 8000 in dev, 8080 in Docker; the Vite dev server also uses 8080 |
| Docker | node:18-alpine → python:3.10-slim builder → python:3.10-slim runtime; user `app`; HEALTHCHECK every 30 s |
| Build results (hackathon) | ~75 → ~13 min; 14.1 → 3.57 GB |
| Pinned versions | Python 3.10, torch 2.1.2 (CPU), numpy 1.26.4, langchain 0.3.27, langchain-google-genai 2.0.10 |
| Team and timeline | 2 people, ~6 days (15–20 Aug 2025) |

---

## 9. Honest gaps and how to talk about them

The formula for each answer: **acknowledge → explain the constraint → state the impact → give the fix.**

**1. The podcast has one narrator, but the README says "2 speakers".**
> "The shipped version is a single narrator. We scoped it down so the demo would be reliable: one TTS call instead of stitching many clips together. A two-speaker version would have the LLM write tagged speaker turns, synthesize each turn with a different voice in parallel, and join them with pydub."

**2. The LightGBM model is in the repo but isn't used.**
> "In Round 1A we classified headings with LightGBM. For the finale my teammate replaced it with a bold-font heuristic that gave cleaner sections on our documents. The model files are left over. The trade-off is robustness on unusual layouts, and I'd bring the classifier back as a fallback."

**3. The performance claims were never benchmarked.**
> "Retrieval is all in-memory with no network calls, so it feels instant on a personal library, but we never ran formal benchmarks. The LLM and TTS steps take seconds. I'd instrument each stage and report p50 and p95 before claiming numbers."

(Better still: measure it yourself with the RUNBOOK §10 command, and then quote the real number.)

**4. The History page and the library panels are mock data.**
> "Those screens were designed but not connected to the backend in the hackathon window. The working path is upload → read → select → results → navigate."

**5. Page navigation is off by one.**
> "PyMuPDF numbers pages from 0 and Adobe's `gotoLocation` numbers them from 1, so the jump lands a page early. It's a one-line fix: add 1 when we store the page."

**6. There are no automated tests.**
> "We tested manually with sample PDF collections, used curl smoke tests, and wrote standalone scripts to check the Gemini and Azure connections. With more time I'd add pytest unit tests for chunking and RRF, API tests with mocked LLM and TTS, and a retrieval evaluation set."

**7. Security shortcuts.**
> "It was built as a local demo: CORS allows every origin, there's no authentication, and secrets are baked into the image. We also committed keys to git history once and removed them later, which means the keys have to be rotated. Removing them from the file isn't enough. For production I'd inject secrets at runtime, add auth and a CORS allow-list, validate paths and uploads, and turn on secret scanning."

**8. Blocking calls inside async endpoints.**
> "`/podcast` uses `run_in_threadpool`, but `/insights` calls the synchronous Gemini client inside an `async def`, which blocks the event loop. The fix is a plain `def` endpoint, `run_in_threadpool`, or `ainvoke`."

**9. The build is no longer reproducible.**
> "sentence-transformers isn't pinned. Its current release requires torch 2.2 or newer, so pip replaces our CPU-only torch 2.1.2 with the CUDA build and undoes the optimization. I checked this with a pip dry-run. The lesson is to lock every dependency and rebuild in CI."

**10. Parts your teammate owned.**
> Say "we" or "my teammate" for the parser rewrite, the frontend scaffold and the navigation. Interviewers value accurate ownership.

---

## 10. Interview Q&A bank

Answers are written so you can say them out loud. Know the idea behind each one; don't memorize the wording.

### A. Overview and motivation

**Q1. Tell me about Project Synapse.**
Give the 90-second pitch (§3.2). End with a hook the interviewer can follow up on: *"Technically, the most interesting part was the hybrid retrieval. Happy to go deeper there."*

**Q2. What problem does it solve, and for whom?**
It's for people who work from many PDFs: researchers, students, analysts, lawyers. Their pain points:
1. Related information is scattered across many files.
2. Ctrl+F finds exact words in one file, not ideas across files.
3. Contradictions and connections are easy to miss.
4. There's no time to re-read everything.

Synapse brings related content to the moment of reading. The text you select becomes the query, results appear next to the document, and an audio summary helps you review on the go.

**Q3. Walk me through the architecture.**
Use the §5 talk track. Mention:
- the two pipelines (ingestion and query);
- one process holding the indexes in memory;
- the three external services: Hugging Face for the model download, Gemini, and Azure OpenAI TTS;
- deployment as a single container.

**Q4. What was your role?**
Use the §2 wording. I owned the backend and AI side (retrieval, LLM, TTS), the Adobe viewer integration and the Docker deployment. My teammate owned the React scaffold, the upload flow, the parser rewrite and page navigation.

**Q5. What was the hardest technical challenge?**
Pick the one you actually lived through:
- **Reliable text selection in Adobe's viewer.** Selection events only fire if you turn them on with `enableFilePreviewEvents: true` and listen for `PREVIEW_SELECTION_END`. The callback has to be registered *before* `previewFile`. The viewer APIs only exist after the preview promise resolves. Reading `getSelectedContent()` immediately sometimes returned nothing, so we added a short delay. A minimum length filters out accidental clicks.
- **Retrieval quality.** Semantic search alone missed exact terms such as names and acronyms, and BM25 alone missed paraphrases. RRF combined the two without having to tune score scales.
- **Docker build time and size.** The default PyTorch install pulled in CUDA libraries. Installing the CPU-only build first, plus a multi-stage build, took the build from 75 to 13 minutes and the image from 14.1 to 3.57 GB.

**Q6. What would you do with two more weeks?**
In priority order:
1. **Quality:** citations in the prompts, cross-encoder re-ranking, excluding the current document, a retrieval evaluation set.
2. **Correctness:** remove blocking calls from async endpoints, fix the page off-by-one, add ingestion job status.
3. **Product:** a real two-speaker podcast, insights and podcast in parallel with streaming, markdown rendering, a real history page.
4. **Production:** authentication, a CORS allow-list, secrets supplied at runtime, locked dependencies, tests and CI.

**Q7. How did you test it?**
Be honest. We tested manually with sample PDF collections, ran curl smoke tests, used the Swagger UI, and wrote standalone scripts for the external services: `test_tts.py` for Azure, and `chat_with_llm.py` for Gemini. The Docker health check covered basic liveness. There were no automated tests; that was a hackathon trade-off. I'd add pytest unit tests for chunking, RRF and the heading rules, FastAPI TestClient tests with Gemini and TTS mocked, a retrieval evaluation set, and Playwright end-to-end tests.

### B. Embeddings and semantic search

**Q8. What is an embedding?**
A fixed-length list of numbers that represents the meaning of a piece of text. The model is trained so that texts with similar meanings end up close together. In Synapse, every chunk and every query becomes a 384-dimension unit vector from all-MiniLM-L6-v2, so "vehicle upkeep" can match "car maintenance" even though they share no words.

**Q9. Why all-MiniLM-L6-v2?**
1. It runs fast on a CPU, and the evaluation environment had no GPU (the Dockerfile tunes thread counts for 8 CPUs).
2. It's small: about 22M parameters, around 90 MB, 384 dimensions. That means a small index and quick encoding.
3. Its semantic similarity is strong for its size; it was contrastively trained on about 1B sentence pairs.
4. It has no per-call cost, and document text isn't sent to a third party for embedding.
5. It outputs normalized vectors, so L2 search ranks exactly like cosine.

The trade-offs: it's English-centric, input is capped at 256 tokens, and quality is below larger models or embedding APIs.

**Q10. What's the model's input limit, and how does chunking account for it?**
256 word pieces; anything longer is cut off. Chunks are 5 sentences, roughly 80–150 words or 100–200 word pieces, so most fit. If a chunk has very long sentences, only its first 256 tokens shape the vector, but the full text is still stored and shown to the user.

**Q11. Bi-encoder vs cross-encoder: when do you use each?**
- **Bi-encoder:** encodes the query and the documents separately, so document vectors can be computed ahead of time. It scales to large collections and is used for first-stage retrieval. This is what Synapse uses.
- **Cross-encoder:** reads the query and a document together. It judges relevance more accurately but needs a model run for every pair, so it's only practical for re-ranking a short list.

A classic upgrade: retrieve 20 candidates with hybrid search, then re-rank them with `cross-encoder/ms-marco-MiniLM-L-6-v2` and keep the top 5.

**Q12. How would you improve retrieval quality?**
1. First, build an evaluation set (queries with their relevant sections) and measure Recall@5, MRR and nDCG, so every change is backed by data.
2. Add cross-encoder re-ranking.
3. Try stronger or domain-specific embedding models (bge, e5, gte).
4. Improve BM25 tokenization (strip punctuation, stem words, drop stop words) and discard zero-score hits.
5. Exclude the section or document currently being read.
6. Tune the chunk size, overlap and RRF k.
7. Rewrite long selections into shorter queries, for example by extracting key phrases or asking the LLM.

**Q13. Your FAISS index uses L2 distance. Shouldn't it be cosine?**
For unit-length vectors they give the same ranking, because ‖a−b‖² = 2 − 2cos(a, b). all-MiniLM-L6-v2 ends with a Normalize layer, so its vectors have length 1, and flat L2 search returns the same order as cosine. With a model that doesn't normalize, I'd set `normalize_embeddings=True` and use `IndexFlatIP`; the inner product equals cosine for unit vectors.

**Q14. What does `faiss_score` mean in your API?**
It's the squared L2 distance from `IndexFlatL2`. Lower is better, and it ranges from 0 to 4 for unit vectors. Cosine similarity is 1 − score/2, so a score of 0.62 means a cosine of about 0.69. It's returned for transparency; the ranking itself comes from RRF.

**Q15. How would you support non-English PDFs?**
1. Switch to a multilingual embedding model, such as `paraphrase-multilingual-MiniLM-L12-v2` (also 384 dimensions) or multilingual-e5.
2. Detect each document's language and use language-aware tokenizers for BM25 and sentence splitting.
3. Re-index everything.
4. Tell the LLM to answer in the user's language.

**Q16. Why not use an embedding API, like OpenAI's or Gemini's?**
- **Local model:** no per-call cost, no network latency or rate limits during ingestion, works offline once downloaded, and document text stays local for embedding.
- **API embeddings:** often better quality and no model to host, but they add cost, latency, vendor lock-in, and data leaving the machine.

For a CPU-only hackathon with private documents, local was the right call. At scale I'd benchmark both on an evaluation set.

### C. FAISS and vector storage

**Q17. What is FAISS, and why not use a vector database?**
FAISS is Meta's C++/Python library for fast similarity search over dense vectors. It's an index, not a server. For a hackathon with a personal library, FAISS plus JSON metadata inside the app meant no infrastructure, a single container, and near-instant search. A vector database (Qdrant, Weaviate, Milvus, pgvector) adds persistence, create/update/delete, metadata filters, concurrency and replication. You need those for multiple users or instances, not for a single-user demo.

**Q18. Which FAISS index did you use, and what's its complexity?**
`IndexFlatL2(384)`, which is exact brute-force search.
- **Query cost:** O(N·d), comparing the query with every vector; it's SIMD/BLAS-optimized.
- **Memory:** O(N·d), about 1.5 KB per chunk.
- **Other properties:** no training step and 100% recall.

For thousands up to a few hundred thousand chunks, it's effectively instant on a CPU.

**Q19. When would you move to IVF or HNSW? Explain both.**
When exact search gets too slow or too memory-hungry, roughly at millions of vectors or with tight latency budgets.
- **IVF:** groups vectors into `nlist` clusters with k-means, then searches only the `nprobe` clusters closest to the query. It needs training, and `nprobe` trades recall for speed. It's often paired with PQ (IVF-PQ) to compress vectors.
- **HNSW:** a layered proximity graph searched greedily from the top layer down. It gives excellent recall and latency with no training, but uses more memory and handles deletes poorly.

In both cases, benchmark recall@k against latency on real data before choosing.

**Q20. How do you map FAISS results back to text?**
FAISS returns integer IDs, which are simply the order in which vectors were inserted. A parallel Python list, `METADATA`, holds each chunk's details at the same position: the i-th vector's document name, section, page and text are in `METADATA[i]`, and its BM25 tokens are in `TOKENIZED_CORPUS[i]`. All three lists are appended in one locked operation and saved together, so the IDs always line up. `IndexIDMap` would allow explicit IDs instead.

**Q21. How is the index persisted, and what could go wrong?**
After each PDF, while holding a lock, the app writes `index.faiss` with `faiss.write_index` and dumps `metadata.json` and `metadata_bm25.json`. On startup it loads them back. The risks:
1. The writes aren't atomic, so a crash mid-write can corrupt a file or leave the three out of sync.
2. Rewriting everything for every document costs time in proportion to the total size.
3. Multiple processes writing at once would overwrite each other.

The fixes: write to temporary files and swap them in atomically with `os.replace`, version the snapshots, batch the writes, or move to a store with transactions.

**Q22. How would you delete or update a document?**
It isn't supported today. The options:
1. Rebuild the index without that document's chunks. Simple, and fine at small scale.
2. Use `IndexIDMap2` with stable IDs, so `remove_ids` works without shifting positions, and store metadata by ID (a dict or SQLite) rather than by list position. BM25 gets rebuilt either way.
3. Move to a vector database with native deletes and upserts.

I'd also hash file contents, so re-uploading a document replaces it instead of duplicating it.

**Q23. How much memory does the index use?**
- **Vectors:** 384 × 4 bytes = 1,536 bytes each, so about 15 MB for 10k chunks and about 1.5 GB for 1M.
- **Metadata in RAM:** the chunk text dominates, roughly 1 KB per chunk.
- **BM25 structures.**
- **The model:** about 90 MB of weights plus PyTorch's runtime overhead.

### D. BM25, hybrid search, RRF

**Q24. Explain BM25 and its parameters.**
BM25 is a bag-of-words ranking function. For each query term it multiplies the term's IDF (how rare it is across chunks) by a term-frequency factor that saturates and is adjusted for chunk length.
- **k1 = 1.5** controls saturation: each extra occurrence of a word adds less.
- **b = 0.75** controls length normalization, so long chunks don't win just by being long.

In rank_bm25's `BM25Okapi`, IDF = ln((N − n + 0.5) / (n + 0.5)), and any negative IDF is raised to 0.25 × the average IDF.

**Q25. Why hybrid search instead of semantic search alone?**
The two methods fail in different ways. Dense embeddings capture paraphrases but can blur exact tokens: product names, error codes, acronyms, numbers, rare jargon. BM25 nails exact terms but misses synonyms. Users select arbitrary text, sometimes a concept and sometimes a specific term, so combining both is more robust than either one.

**Q26. What is RRF, and why k = 60?**
Reciprocal Rank Fusion scores each result as score(d) = Σ 1/(k + rank) over every ranked list that contains d. It uses only positions, so no score normalization is needed. k = 60 comes from Cormack et al. (SIGIR 2009). It flattens the differences between top ranks (1/61 vs 1/62), so agreement between retrievers matters more than one list's favourite. It works well without tuning.

**Q27. Why not a weighted sum of scores?**
FAISS distances (0 to 4, lower is better) and BM25 scores (unbounded, higher is better, scale depends on the query) aren't comparable. A weighted sum needs per-query normalization, such as min-max or z-score, plus a tuned weight, which is fragile without an evaluation set. RRF needs neither. With labeled data, a tuned weighted combination or a learned fusion could beat RRF.

**Q28. Walk me through your fusion code. Is anything subtle?**
The dense list is processed first, then the sparse list, and each item adds 1/(60 + rank) to its key.
- **The subtle part:** the key is `(doc_name, section_title, page)`, which identifies a *section*, not a chunk. When several chunks from the same section match, their scores add up, so that section rises.
- **Stored payload:** each key keeps the first occurrence, and dense results come first. A section found by both retrievers therefore shows its FAISS score, with the BM25 score left null.
- **Quirks worth fixing:** `sparse_rank` gets overwritten with the last (worst) sparse rank, and BM25 still contributes candidates whose score is zero.

**Q29. How do you get from candidates to the final 5?**
1. `TOP_K_SEARCH = 10`, so `search_similar_chunks(query, 20)` runs.
2. FAISS returns its top 20 and BM25 its top 20.
3. RRF fuses the two lists, and the first 10 are kept.
4. Each result gets `pdf_available` and `pdf_url`.
5. Duplicates by (doc_name, section_title) are removed, keeping the highest RRF score.
6. The list is sorted and cut to `MAX_RESULTS = 5`.

Fetching more than needed and trimming later leaves room for fusion and deduplication.

**Q30. Compute an RRF score: a section is rank 1 in FAISS and rank 4 in BM25.**
1/61 + 1/64 = 0.01639 + 0.01563 = **0.03202**. For comparison, rank 1 in FAISS alone scores 0.01639, so agreement between the two retrievers nearly doubles the score.

**Q31. What's weak about your BM25 setup?**
- Tokenization is just `lower().split()`, so punctuation stays attached ("learning," doesn't match "learning"), there's no stemming ("train" vs "training"), and stop words aren't removed.
- It returns the top k even when their scores are 0, which adds noise to fusion.
- The whole index is rebuilt on every upload, because rank_bm25 can't add documents incrementally.
- Scoring loops over every chunk for each query term, so long selections cost more.

Fixes: a regex tokenizer with stemming, keeping only results with `score > 0`, and at scale a proper search engine such as Elasticsearch, OpenSearch, Tantivy or SQLite FTS5.

### E. Chunking and PDF parsing

**Q32. How do you chunk, and why 5 sentences with an overlap of 1?**
For each section: normalize whitespace, split into sentences with NLTK Punkt, then slide a 5-sentence window forward 4 sentences at a time.
- **Why 5 sentences?** About 80–150 words is specific enough for precise embeddings, carries enough context to be a useful LLM snippet, and usually stays within MiniLM's 256-token limit.
- **Why overlap by 1?** It preserves context across chunk boundaries.
- **Other details:** sections under 5 words are skipped. Sentence-based windows never cut a sentence in half, unlike fixed character windows.

**Q33. Why chunk inside sections rather than across the whole document?**
So that a chunk never mixes two topics, and every chunk inherits a clean section title and page number for display and navigation. It also makes section-level fusion and deduplication possible.

**Q34. How do you detect headings? What are the failure modes?**
A text block counts as a heading if:
- a span's font name contains "bold",
- it has no bullet character,
- it has 1–29 words, and
- it doesn't end with `.`, `?`, `!` or `,`.

The content between two consecutive headings, ordered by page and then vertical position, becomes the section. Failure modes:
- Headings whose font name doesn't contain "Bold" (bold set by flags, or headings distinguished only by size) are missed.
- PDFs with no bold text produce zero chunks.
- Bold phrases inside paragraphs become fake headings.
- Text before the first heading is dropped.
- Multi-column layouts can get interleaved.
- Scanned PDFs have no text layer at all.

**Q35. The repo has a LightGBM model. What happened to it?**
In Round 1A, a LightGBM classifier detected headings using features of each text block: font size relative to the document median, boldness, word count, capitalization and title case, numbering patterns, normalized position and width, and spacing above. Tesseract OCR handled scanned pages. For the finale, the parser was rewritten as a simpler bold-font heuristic that produced cleaner sections on the target documents. The model files remain but are never loaded. According to git history, my teammate did that rewrite.

If they ask why: fewer dependencies and failure points, faster, and good enough for well-formatted PDFs. The cost is robustness on unusual layouts, so I'd bring the classifier back as a fallback.

**Q36. How would you handle scanned PDFs, tables and multi-column layouts?**
- **Scanned PDFs:** detect pages with little or no text layer and run OCR on them, with Tesseract as in Round 1A or a cloud OCR / Document AI service.
- **Tables:** detect them with PyMuPDF's table finder, Camelot or pdfplumber, convert them to markdown or CSV text before chunking, and keep captions as context.
- **Multi-column layouts:** order blocks by column (cluster the x-coordinates) before reading them, or use a layout-aware parser.
- **Fallback:** when no headings are found, create page-level chunks.

**Q37. What metadata do you store for each chunk, and why?**
| Field | Why it's stored |
|---|---|
| `doc_id` | A UUID for each upload |
| `doc_name` | Used to fetch the PDF through `/api/pdf` |
| `document_title` | The document's title |
| `section_title` | Shown in the UI; part of the fusion and deduplication key |
| `page` | Used to jump to the right place |
| `chunk_text` | Shown as the snippet and sent to the LLM |

Everything is stored in `metadata.json`, in the same order as the FAISS vectors.

### F. LLM and RAG

**Q38. What is RAG, and how does Synapse implement it?**
Retrieval-Augmented Generation means retrieving relevant context, adding it to the prompt, and then generating. It grounds an LLM in private, up-to-date data without fine-tuning, and it reduces hallucination. In Synapse:
- **Retrieval** is hybrid search over the user's PDFs.
- **Augmentation** puts the top 5 snippets, numbered, into the prompt alongside the selected text.
- **Generation** is Gemini 2.5 Flash writing structured insights or a podcast script.

**Q39. Walk me through the insights prompt.**
1. **Role:** "expert document analyst".
2. **Clearly delimited inputs:** SELECTED TEXT, then RELATED CONTENT with numbered snippets.
3. **A fixed markdown template:** Quick insights, Key points, Critical notes (contradictions, gaps, unanswered questions, risks), Actionable takeaways, Connections.
4. **A footer:** "analysis based on N related sections".

Temperature is 0.5. If there are no snippets, it returns a message without calling the LLM. If the LLM returns an empty response, it raises an error, which becomes HTTP 500.

**Q40. How do you reduce hallucinations, and what's still weak?**
- **Done:** grounding in retrieved snippets, a constrained output structure, and a moderate temperature.
- **Weak:** the prompt invites "your own knowledge", snippets carry no source labels so the model can't cite them, and nothing verifies the claims.
- **Improvements:** label snippets [1]–[5] with document and page and require citations; instruct the model to say when the documents don't support something; separate "from your documents" from "general context"; lower the temperature for insights; verify claims afterwards with an LLM judge or NLI; show sources in the UI.

**Q41. How are contradictions detected?**
By the LLM, through an explicit instruction in the "Critical Notes" section to list contradictions and gaps between the selected text and the related snippets. There's no separate classifier. A more rigorous approach would run an NLI cross-encoder, such as `cross-encoder/nli-deberta-v3-base`, over each (selected text, snippet) pair to get contradiction probabilities, then have the LLM explain the flagged pairs with citations.

**Q42. Why Gemini 2.5 Flash, and why temperature 0.5?**
- **Flash:** fast and cheap with a large context window, which suits interactive latency and a hackathon budget. The evaluation setup also provided Gemini credentials.
- **0.5:** balances readable, varied prose (important for a natural-sounding podcast script) against consistency. For strictly factual insights I'd go lower, around 0.1–0.3.

**Q43. Why LangChain? Would you keep it?**
It gave a provider-agnostic chat interface (the hackathon's sample code supported several LLM providers) and message types with very little code. We only use a thin wrapper around `ChatGoogleGenerativeAI.invoke`. I'd keep the single `chat_with_llm` gateway pattern, but either call the provider SDK directly to cut dependencies, or use LangChain more fully if we add streaming, retries, structured output and tracing.

**Q44. How would you stream insights to the UI?**
- **Backend:** return a `StreamingResponse` (or Server-Sent Events) from an async generator that yields tokens from `llm.astream(...)`.
- **Frontend:** `fetch`, then read chunks with `response.body.getReader()`, decode them and append to state (or use `EventSource` with SSE).

Perceived latency drops to the time until the first token. Keep the AbortController so closing the panel cancels the stream, and check `request.is_disconnected()` on the server.

**Q45. How would you evaluate insight quality?**
1. Build a small benchmark: selected passages, their retrieved snippets, and reference judgments.
2. Measure:
   - **faithfulness** (are the claims supported by the snippets?),
   - **relevance**,
   - **coverage** of real contradictions.
3. Choose methods: human rubric scoring, an LLM judge with a clear rubric (validated against human labels), and RAG metrics such as RAGAS (faithfulness, answer relevancy, context precision and recall).
4. Evaluate retrieval separately (Recall@k, MRR), so you know which stage is failing.
5. Track regressions whenever prompts or models change.

**Q46. How do you control LLM cost and latency?**
- **Already in place:** only the top 5 snippets go into the prompt; a Flash model; the script is capped at about 2,000 characters; no LLM call when there are no snippets; the podcast runs in a thread pool.
- **Next steps:**
  - cache results by a hash of the selected text plus the snippets;
  - generate the podcast only on request instead of for every selection;
  - run insights and the podcast in parallel after retrieval;
  - stream responses;
  - set max output tokens and timeouts;
  - limit Gemini 2.5's thinking budget where quality allows;
  - rate-limit each user.

**Q47. What about prompt injection from PDF content?**
PDF text goes straight into prompts, so a document could contain something like "ignore previous instructions". The impact here is limited, because the model has no tools and its output is only displayed, but it could mislead the user. Mitigations:
- delimit untrusted content and tell the model to treat it as data;
- strip obvious instruction patterns;
- never give the model tools or actions over untrusted input without guardrails;
- show sources so users can verify.

**Q48. What happens if the LLM call fails?**
- **Insights:** the exception becomes HTTP 500, the UI shows "Analysis Failed", and the rest of the flow stops.
- **Podcast:** script generation catches the error and uses a canned fallback script, so audio is still generated, just generic.
- **Improvements:** retry with backoff on transient errors (429, 5xx), show clearer messages, and let the podcast step run independently of insights.

### G. TTS and the podcast

**Q49. Explain the podcast pipeline end to end.**
1. The frontend POSTs the selected text and snippets to `/api/podcast`.
2. The endpoint runs `generate_podcast_audio` in a thread pool.
3. Gemini writes a first-person script of 300–500 words.
4. The code strips markdown and enforces 100–2,000 characters, using a fallback script if needed.
5. `generate_audio` calls Azure OpenAI TTS (`/openai/deployments/tts/audio/speech`, voice `nova`) and saves an MP3.
6. The file size is checked (must be over 1 KB).
7. A FileResponse returns it as `audio/mpeg`, and a background thread deletes the file after 5 minutes.
8. The browser turns the response blob into an object URL for an `<audio>` player.

**Q50. Is it really a two-speaker podcast?**
No. Answer honestly: the shipped version has a single narrator. We simplified it for a reliable demo, and the README overstates it. A two-speaker version would:
1. prompt for a dialogue with HOST and GUEST tags, as JSON or one turn per line;
2. parse the turns;
3. synthesize each turn in a different voice (for example `nova` and `onyx`), in parallel to save time;
4. stitch them together with pydub, adding short silences between turns;
5. export one MP3, capping total characters to control cost.

**Q51. Why cap the script at about 2,000 characters?**
1. About 300 words is roughly 2 minutes of audio, which is right for a quick summary.
2. The OpenAI TTS endpoint accepts at most 4,096 characters per request.
3. TTS latency and cost grow with length, and the call has a 30-second timeout.

Truncation tries to end at a sentence boundary.

**Q52. What if TTS isn't configured?**
`TTS_PROVIDER` selects the provider: `azure`, `gcp` or `local`. In Docker, the entrypoint switches to `local` (espeak-ng plus ffmpeg) when Azure credentials are missing. If a provider fails, the endpoint returns 503 with a TTS-specific message and the UI shows "Text-to-speech service is currently unavailable".

**Q53. How are temporary audio files cleaned up? Any problems?**
Each response schedules a background task that starts a daemon thread, sleeps 300 seconds, then deletes the file.

Problems:
- one sleeping thread per request;
- files survive if the process restarts before cleanup runs;
- an unused cleanup helper contains a bug (`os.time()`).

Better options: stream the bytes directly without saving them, store audio in object storage with a TTL or lifecycle rule, or run a single periodic cleanup job.

### H. Backend and concurrency

**Q54. Why FastAPI?**
- It supports async and needs very little boilerplate.
- Pydantic validation comes straight from type hints.
- It generates OpenAPI docs at `/docs` automatically, which helped a team integrating frontend and backend in parallel.
- BackgroundTasks and thread-pool helpers are built in.
- It's a natural fit for Python ML code.

**Q55. How does ingestion avoid blocking the upload request?**
The endpoint only saves the files, schedules `process_and_index_pdf` with BackgroundTasks, and returns. Once the response has been sent, Starlette runs each synchronous task in the thread pool, one after another for that request.
- **Trade-offs:** no progress or status, no retries, work is lost on a crash, and it runs in the same process as the API, so embedding competes for CPU.
- **In production:** a task queue (Celery, RQ or Arq with Redis), dedicated workers, and a job status endpoint.

**Q56. Explain `async def` vs `def` in FastAPI. Any issues in your code?**
- `async def` endpoints run on the event loop, so any blocking call inside one stalls the whole server.
- `def` endpoints run in a thread pool automatically, and `run_in_threadpool` offloads blocking work from async code.

In Synapse, `/podcast` correctly uses `run_in_threadpool`. But `/insights` calls the synchronous Gemini client inside `async def`, and `/related-sections` runs embedding and BM25 inline. Both block the event loop while they run, so other requests, even health checks, wait. The fix: declare them with `def`, wrap the work in `run_in_threadpool`, or use async clients (`llm.ainvoke`).

**Q57. How do you keep the shared index consistent?**
One `threading.Lock` wraps the whole write: the FAISS add, the metadata extend, the BM25 corpus extend, the BM25 rebuild, and writing the three files. Concurrent ingestion threads can't interleave. Embedding happens before the lock is taken, which keeps the critical section short.

Reads don't take the lock, so there's a tiny window where a search could see a new vector before its metadata is added (a possible IndexError). Fixes: add the metadata before the vectors, use a read-write lock, or swap in immutable snapshots.

**Q58. What happens if you run 4 Uvicorn workers?**
You get four processes, each loading its own model and in-memory index.
- An upload handled by worker 2 updates only worker 2's memory (and writes the files).
- The other workers serve stale results until they restart.
- Concurrent writes from different workers can overwrite each other's files.
- Memory use roughly multiplies by the number of workers.

The fix is to move state out of the process: a vector database or search service shared by stateless API workers, plus a single ingestion worker.

**Q59. How would you add ingestion progress or status?**
1. Give each uploaded file a job ID.
2. Store its status in Redis or a database: queued → parsing → embedding → indexed or failed, with the chunk count and any error.
3. Return the job IDs in the ingest response.
4. Expose `GET /api/jobs/{id}` for polling, or push updates over SSE or WebSocket.
5. Show progress in the UI.

With a task queue, the worker updates the status as it goes.

**Q60. How does one server serve both the API and the React app?**
The API router is mounted under `/api` first. If `frontend/dist` exists, `main.py` registers a catch-all GET route:
- `api/...` paths that didn't match anything get a 404;
- paths with a file extension are served from `dist` (JS, CSS, assets);
- every other path returns `index.html`, so React Router handles `/reader` and `/history`.

Frontend and API share an origin, so no CORS is needed in production. One caveat I'd fix: the catch-all joins the raw path without normalizing it. It should check that the resolved path stays inside `dist`, or use `StaticFiles` instead.

**Q61. Explain CORS and your configuration.**
Browsers block reading responses from a different origin unless the server sends `Access-Control-Allow-*` headers. In development the UI (localhost:8080) and the API (localhost:8000) are different origins, so the backend enables `CORSMiddleware` with `allow_origins=["*"]` and all methods and headers. That's fine locally, but too permissive for production, because any website could call the API from a user's browser. In production, serve both from the same origin (as the Docker setup does) or use an explicit allow-list.

**Q62. How is configuration managed?**
- **Shared file:** a single `.env` at the project root, read by both frontend and backend.
- **Backend:** a pydantic-settings `Settings` class holds paths, chunk sizes and top-k, with defaults that environment variables can override, and is cached with `@lru_cache`. python-dotenv loads the API keys into `os.environ` for the LLM and TTS scripts.
- **Frontend:** Vite exposes `VITE_*` variables at build time.
- **Docker:** the entrypoint merges the baked-in values with the runtime environment, fills in defaults and applies the TTS fallback.
- **Weaknesses:** the baked `.env` takes precedence over `docker run -e`, and the secrets live inside the image. I'd switch to runtime-only secrets.

**Q63. How do you cancel work when the user makes a new selection?**
- **Frontend:** each request has an AbortController stored in a ref. A new selection, closing the panel or unmounting aborts in-flight fetches and resets the loading state, so stale responses never overwrite new results.
- **Backend:** nothing is cancelled; the LLM and TTS calls keep running. I'd check `await request.is_disconnected()` between steps, or model generation as cancellable jobs.

**Q64. What does `@lru_cache` on `get_settings` do?**
It memoizes the function. The `Settings` object, which reads environment variables and `.env`, is created once and the same instance is returned everywhere. That avoids re-reading files and acts as a simple singleton. The downside: changes to `.env` need a restart (or `cache_clear()`).

### I. Frontend and Adobe

**Q65. How does text selection trigger the analysis?**
1. The viewer registers an EVENT_LISTENER callback for `PREVIEW_SELECTION_END`, with `enableFilePreviewEvents: true`, before calling `previewFile`.
2. When the event fires, it waits 50 ms and calls `apis.getSelectedContent()`. (The APIs object is obtained once the preview promise resolves.)
3. If the text is longer than 10 characters, `ReaderView.startAnalysisFlow` aborts previous requests, opens the sidebar, and runs related-sections → insights → podcast.

**Q66. How does click-to-navigate work? Any bugs?**
1. Clicking a result fetches `/api/pdf/<doc_name>` as a blob and wraps it in a File.
2. That file becomes the current document, together with the target page.
3. The `PDFViewer` is keyed by document name, so it remounts.
4. After `getAPIs()`, it calls `gotoLocation(page)`.

The bug: pages are stored 0-based (PyMuPDF's `enumerate`) while Adobe's `gotoLocation` is 1-based, and the code skips page 0. So jumps land one page early, first-page sections don't move at all, and the card shows the 0-based page. The fix is `page + 1`.

**Q67. Why are the three calls sequential? What's better?**
Insights and the podcast both need the related snippets, so related-sections must run first. Running insights before the podcast was just the simplest orchestration. But the two are independent of each other, so they should run in parallel after retrieval (`Promise.allSettled`), each with its own loading and error state. Then a failed insights call wouldn't block the audio. Better still: stream the insights, and generate the podcast only on demand to save cost.

**Q68. How do environment variables work in Vite, and why does it matter for Docker?**
- Only `VITE_`-prefixed variables are exposed, through `import.meta.env`, and they're replaced with literal values at build time.
- Vite reads the root `.env` (`envDir: "../"`).
- In Docker the frontend is built during `docker build`, so the Adobe client ID and the API URL are frozen into the image. Changing them requires a rebuild; `docker run -e` has no effect.
- The API URL was hardcoded to `http://localhost:8080`, which breaks on any other host or port. Relative `/api` URLs would fix that.

**Q69. What's the Content-Security-Policy for?**
It's a meta-tag allow-list telling the browser which origins may supply scripts, frames, workers, styles, fonts, images, media and network connections.
- `self`.
- `*.adobe.com` and `*.adobe.io`, because the Embed SDK loads scripts, iframes and workers from Adobe.
- `localhost`, for the API in development.
- `blob:` and `data:`, for the viewer and the audio.

It limits the damage from injected scripts. It does allow `'unsafe-inline'` and `'unsafe-eval'`, probably for the SDK, which weakens it.

**Q70. Why pass the PDF to Adobe as an ArrayBuffer instead of a URL?**
In the "read" flow, the user picks a local file that never touches the server, so there's no URL to give. For library documents, the app fetches `/api/pdf/...` and reuses the same File code path. This also avoids Adobe having to fetch URLs from localhost or across origins, and keeps a single code path. The trade-off is that the whole PDF sits in browser memory.

**Q71. Which parts of the UI are placeholders?**
The History page, the left Library/Contents sidebar and the Library dropdown all use hardcoded mock data. There's also unused scaffold code: `ModalPrompt`, `AdobeTest`, and a separate SDK hook. The working path is Home upload → Reader → selection sidebar → navigation. If asked, say it plainly: "Those were designed but not wired to the backend in the hackathon window."

### J. Docker and deployment

**Q72. Walk me through the Dockerfile.**
It has three stages.
1. **`node:18-alpine`:** copy `package*.json` and `.env`, run `npm ci`, copy the source, set `VITE_API_URL` to `localhost:8080`, run `vite build` to produce `dist`.
2. **`python:3.10-slim` with compilers:** install CPU-only torch first, then numpy/scipy/sklearn, sentence-transformers, faiss-cpu, the web stack, LangChain/Gemini, pandas/LightGBM/rank-bm25, PyMuPDF/NLTK, the audio libraries, and NLTK's punkt data. Each group gets its own layer so it can be cached.
3. **`python:3.10-slim` runtime:** install runtime tools with apt (ffmpeg, espeak-ng, tesseract, poppler, curl); set environment variables (unbuffered logs, `PYTHONPATH`, 8 BLAS threads); create a non-root user; copy in the site-packages, backend, `dist`, `.env` and entrypoint; add a HEALTHCHECK on `/api/health`, `EXPOSE 8080`, and the `ENTRYPOINT`.

**Q73. How did you cut build time and image size?**
The big win: on Linux, `pip install torch` pulls the CUDA build and gigabytes of NVIDIA libraries. Installing torch from PyTorch's CPU wheel index first means later packages see torch as already installed. On top of that:
- a multi-stage build, so compilers, Node and `node_modules` never reach the final image;
- `--no-cache-dir` for pip;
- dependency layers ordered before the source code, so they stay cached.

At the time, that took the build from about 75 to about 13 minutes and the image from 14.1 to 3.57 GB.

**Q74. Why multi-stage builds?**
Build tools (Node, the npm cache, gcc, header files) are needed to build but not to run. Separate stages let the final image copy only the artifacts. The result is a smaller image, faster pulls and a smaller attack surface, all from one Dockerfile.

**Q75. Why a non-root user and a health check?**
- **Non-root user:** if the app is compromised, the attacker doesn't get root inside the container. It's defense in depth.
- **Health check:** Docker probes `/api/health` every 30 seconds and marks the container healthy or unhealthy, so orchestrators can restart it or route traffic around it. Because Uvicorn only accepts connections after the model has loaded, "healthy" also means "ready".

**Q76. What does `entrypoint.sh` do, and why `exec`?**
It runs these steps in order:
1. Back up the baked `.env` and source it.
2. Rewrite `/app/.env` with defaults for any missing keys (Gemini model, TTS settings, API URL).
3. Switch TTS to local if the Azure credentials are missing.
4. Log which credentials exist.
5. Create the data directories.
6. Run `exec uvicorn ...`.

`exec` replaces the shell process, so Uvicorn becomes PID 1 and receives the SIGTERM from `docker stop`, letting it shut down gracefully. A shell running as PID 1 wouldn't forward that signal.

**Q77. How are secrets handled, and what would you change?**
Today, the root `.env` with the API keys is copied into the image and even printed during the build. At runtime the entrypoint sources that baked file, which overrides any `docker run -e` values for the same keys. I would:
- keep backend secrets out of the build entirely (only public `VITE_` values at build time, or load config at runtime);
- inject secrets at runtime with `-e`, `--env-file` or a secrets manager (Azure Key Vault, AWS or GCP Secret Manager);
- use BuildKit secrets if anything is genuinely needed during the build;
- never `cat` secrets in a build step;
- make runtime values take precedence.

The keys that were once committed to git history also need rotating.

**Q78. If you rebuilt the image today, would you get the same result?**
No, and it's a good lesson. `sentence-transformers` isn't pinned. A pip dry-run showed that its current release requires torch ≥ 2.2, so pip replaces the pinned CPU torch 2.1.2 with the newest torch from PyPI, which is the CUDA build on Linux. That silently undoes the optimization. Current transformers also requires torch ≥ 2.5. The fix is to install the latest CPU torch and pin everything with a lock file (a `pip freeze` from a good build, pip-tools, or `uv lock`), then rebuild in CI regularly to catch drift.

**Q79. How would you deploy this to the cloud?**
Push the image to a registry (ACR, ECR or Artifact Registry) from CI and run it on a container service such as Azure Container Apps, Cloud Run, ECS/Fargate or App Service. It would need:
- **Persistent storage.** The index and PDFs can't live in the container's filesystem. A mounted volume works short-term; better is object storage for PDFs plus a managed vector database.
- **Secrets** from a secrets manager.
- **At least one warm instance**, with the model baked into the image to avoid downloading it on cold start.
- **Relative API URLs.**
- **HTTPS.**
- **The production domain** registered in the Adobe credential.
- **Authentication.**
- **A single replica** until state is moved out of the process.

**Q80. Why bind to `0.0.0.0` and use port 8080?**
Inside a container, `127.0.0.1` only accepts connections from within that container. `0.0.0.0` listens on every interface, so Docker's port mapping can reach the app. Port 8080 is the conventional alternative HTTP port, and the hackathon guidelines required it (there's a comment saying so in the Dockerfile).

**Q81. Any cold-start issues?**
Yes. Every new container downloads all-MiniLM-L6-v2 (about 90 MB) from Hugging Face at startup, which needs internet access and delays readiness. The index is also loaded into RAM. Fixes: download the model into the image during `docker build` (set `HF_HOME`), keep a warm instance, and load indexes lazily or from a fast store.

### K. Scaling and system design

**Q82. How would you scale Synapse to millions of chunks and many users?**
- **Storage:** PDFs in object storage, metadata in Postgres, vectors in a vector database (pgvector, Qdrant or Milvus) with HNSW or IVF-PQ, and keyword search in OpenSearch or Elasticsearch (or one store that does hybrid search natively).
- **Ingestion:** upload → queue (Kafka, SQS or Redis) → autoscaled workers that embed in batches (on GPU if needed) → idempotent upserts keyed by content hash, plus a job status API.
- **Serving:** stateless FastAPI replicas behind a load balancer; query embedding in-process or through a small model service; retrieval → re-ranking → a streaming LLM call; caching for embeddings and LLM outputs.
- **Multi-tenancy:** a `tenant_id` on every document and vector, filtered search, and authentication and authorization.
- **Reliability and cost:** rate limits, timeouts, retries and circuit breakers on LLM and TTS calls; podcasts generated on demand; observability for per-stage latency, token usage and errors.

**Q83. Design per-user (multi-tenant) libraries.**
1. Every document and chunk carries an `owner_id`, and optionally a `workspace_id`.
2. Enforce ownership at query time with metadata filters in the vector database and the search engine. Never trust the client.
3. Choose a layout:
   - **shared collections with filters:** efficient for many small tenants;
   - **per-tenant collections or namespaces:** better isolation and easy deletion for large tenants.
4. Authenticate requests (OAuth or JWT), authorize access to documents in `/api/pdf`, and scope caches by tenant.
5. Deleting a user removes their vectors, metadata and files, which also covers GDPR.

**Q84. How would you cut end-to-end latency?**
Measure each stage first. Then:
- run insights and the podcast in parallel after retrieval;
- stream the insights tokens;
- make the podcast on-demand, or pre-generate its script while the user reads;
- move blocking calls off the event loop;
- cache query embeddings and LLM outputs;
- cap prompt size and output tokens;
- reduce Gemini 2.5's "thinking" where that's acceptable;
- synthesize TTS paragraph by paragraph in parallel and stream the audio;
- keep indexes warm;
- switch to ANN search only if retrieval itself becomes the bottleneck.

**Q85. What would you cache?**
- **Query embeddings:** hash of the text → vector.
- **Retrieval results:** hash of query + index version.
- **Insights and podcast outputs:** hash of query + snippet IDs + prompt version + model, invalidated when the library changes.
- **Generated audio:** in object storage with a TTL.
- **The model:** inside the image.

Use Redis for the hot caches.

**Q86. What would you monitor?**
- **Latency** per endpoint (p50, p95, p99), broken down by stage: embed, FAISS, BM25, fusion, LLM, TTS.
- **Error rates** by type, such as LLM 429 and 5xx responses and TTS failures.
- **Ingestion:** throughput, queue depth, failures, and chunks per document (0 chunks points to a parsing problem).
- **Token usage and cost.**
- **Index size and memory.**
- **Retrieval quality signals,** such as click-through on related sections.
- **Health and readiness.**

Tools: structured logs, OpenTelemetry traces, Prometheus and Grafana, and LLM tracing such as LangSmith.

**Q87. How would you test and evaluate the system?**
- **Unit tests:** `chunk_text` (overlap and edge cases), RRF (hand-computed scores and ties), the heading rules, prompt building.
- **API tests:** FastAPI TestClient with a fixture PDF and mocked Gemini and TTS, asserting response schemas and error codes.
- **Retrieval evaluation:** labeled queries scored with Recall@5, MRR and nDCG; compare dense-only, BM25-only and hybrid; tune chunking and k.
- **LLM evaluation:** a faithfulness and relevance rubric, an LLM judge validated against human labels, and a regression suite that runs when prompts change.
- **Frontend:** component tests with Vitest and React Testing Library, plus Playwright end-to-end tests with the Adobe viewer either mocked or using a real key in staging.
- **Load tests:** Locust or k6 against related-sections and ingestion.

### L. Security

**Q88. What are the main security issues, and how would you fix them?**

| Issue | Fix |
|---|---|
| Secrets baked into the image and printed during the build | Supply secrets at runtime |
| Keys committed to git history | Rotate them, purge the history, turn on secret scanning |
| No authentication; CORS set to `*` | Add authentication, an origin allow-list and rate limiting |
| The catch-all static route joins an unnormalized path, a possible path traversal that could expose `/app/.env` | Check that the resolved real path stays inside `dist`, or use `StaticFiles` |
| Upload filenames aren't sanitized; no size or type checks | Use `basename` or UUID filenames, enforce size limits, check the file's magic bytes |
| Prompt injection through PDFs | Treat PDF text as data; give the model no tools |
| Unpinned dependencies | Lock files plus vulnerability scanning (pip-audit, npm audit, image scanning) |

On the positive side, the `/api/pdf` endpoint already validates filenames, and the container runs as a non-root user.

**Q89. You found API keys in your git history. What do you do?**
1. Treat them as compromised and revoke and regenerate them with each provider right away. That's the real fix; rewriting history doesn't un-leak a secret that's already been pushed.
2. Purge the history (`git filter-repo` or BFG), force-push, and have collaborators re-clone.
3. Turn on GitHub secret scanning and push protection, and add a pre-commit hook (gitleaks).
4. Keep only a `.env.example` with placeholder values in the repo.
5. Check the providers' usage logs for abuse.

In Synapse, commit `4dd5ea7` put keys in `DEBUG.md`. They were later removed from the file but are still in the history, so rotating them is the action item.

**Q90. How would you secure file uploads?**
- **Authenticate** the user.
- **Enforce a maximum size,** streaming to disk in chunks and rejecting anything over the limit.
- **Validate the type** by magic bytes (`%PDF-`), not just the extension.
- **Generate filenames on the server** (UUIDs) and keep the original name as metadata.
- **Store files** outside any web-served directory (or in object storage), with per-user access checks.
- **Parse untrusted PDFs** in an isolated worker with timeouts and memory limits, and keep PyMuPDF updated.
- **Optionally scan** for malware.
- **Rate-limit** uploads.

### M. Behavioral (STAR stories)

> The stories below were reconstructed from the code and the commit history. **Replace the details with what really happened,** such as what you tried first and how long it took. Specific, true details are what make a story convincing.

**Q91. Tell me about a difficult bug you fixed.**
- **Situation:** the Adobe PDF viewer rendered documents, but highlighting text did nothing, and selection was the trigger for the entire product.
- **Task:** get the selected text reliably into React so the analysis flow could start.
- **Action:** I dug into the Embed API docs and experimented:
  - selection events are file-preview events that must be enabled and listened for explicitly (`PREVIEW_SELECTION_END` with `enableFilePreviewEvents`);
  - I registered the callback before `previewFile`;
  - I captured the viewer APIs only after the preview promise resolved;
  - I added a short delay before `getSelectedContent`, because the selection wasn't always ready when the event fired;
  - I added a minimum length to ignore accidental clicks.

  (Commits `9106dc9` → `064936d` → `d7edfaa`, 16–18 Aug.)
- **Result:** selection-driven analysis worked end to end and became the entry point for search, insights and audio.

**Alternative story (Azure TTS):** I wrote a small standalone script, `test_tts.py`, to isolate the REST call: deployment path, api-version, the api-key header and the body shape. Once it worked in isolation, I made the app's code match that exact working format (commit `8663f3e`, "azure tts fixed; podcast feature now working correctly").

**Q92. Tell me about a trade-off you made under time pressure.**
Structure the answer as: constraint → options considered → decision → what it cost → what you'd do with more time.
- **Podcast:** we aimed for a two-speaker conversation but shipped a single narrator: one TTS call instead of stitching many together, so fewer things could break before the demo. Be clear that it's a cut-down version, and explain the two-speaker design.
- **Storage:** FAISS and JSON inside the app instead of a vector database. No infrastructure, one container, fast. We accepted no deletes, no filters and single-process state, and documented how to scale it up.

**Q93. How did you collaborate and split the work?**
We were two people. I owned the backend and AI side (retrieval, LLM, TTS), plus the Adobe viewer integration and Docker. My teammate owned the React scaffold, the upload UI, the parser rewrite and navigation. We integrated through API contracts: for example, the `/api/ingest` multipart field name `files`, and the `RelatedSection` shape mirrored in `types/analysis.ts`. We merged frequently (several merges between 18 and 20 Aug) and moved all configuration into one root `.env` so both apps read the same keys.

**Q94. What did you learn from this project?**
1. Hybrid retrieval is worth it. Each method covers the other's blind spots, and RRF makes combining them easy.
2. LLM output needs guardrails: cleaning, length checks and fallbacks.
3. Async Python is easy to misuse. One blocking call in an async endpoint stalls the whole server.
4. Reproducibility matters. Unpinned dependencies later undid our Docker optimization.
5. Secrets hygiene matters. Removing a key from a file doesn't remove it from git history.
6. Cut scope hard for a demo, but be honest about what you cut.

**Q95. What are you most proud of?**
Pick one and be specific:
- **The hybrid retrieval engine:** section-level RRF that rewards sections with several matching chunks, fast enough to feel instant on a personal library (measure it before quoting a number).
- **The Docker optimization:** diagnosing that the CUDA torch wheels were the cost, and cutting build time by about 80%.

### N. Rapid-fire

| Question | Short answer |
|---|---|
| Embedding model? | all-MiniLM-L6-v2: 384 dimensions, ~22M parameters, 256 tokens max, normalized output |
| FAISS index type? | `IndexFlatL2`, exact search |
| Why is L2 okay? | Unit vectors: ‖a−b‖² = 2 − 2cos |
| BM25 library and parameters? | rank_bm25 `BM25Okapi`, k1 = 1.5, b = 0.75 |
| Fusion method? | RRF, k = 60, keyed by (doc, section, page), scores add up |
| Candidates per retriever? | 20 → top 10 after fusion → deduplicated → 5 |
| Chunking? | 5 sentences, overlap 1, NLTK Punkt, within sections |
| Heading detection? | Bold font name, 1–29 words, no bullet, no ending punctuation |
| LLM? | Gemini 2.5 Flash via LangChain, temperature 0.5 |
| Contradiction detection? | A prompt instruction; no separate model |
| TTS? | Azure OpenAI `tts` over REST, voice `nova`; local espeak-ng fallback |
| Podcast length? | 300–500 words, capped at ~2,000 characters |
| One speaker or two? | One (be honest) |
| How ingestion runs? | FastAPI BackgroundTasks in the thread pool, plus `threading.Lock` |
| Why `run_in_threadpool`? | LLM and TTS calls block; keep the event loop free |
| Where data is stored? | `backend/data/`: `uploads/`, `index.faiss`, `metadata.json`, `metadata_bm25.json` |
| How the SPA is served? | A catch-all route returns `index.html`; API lives under `/api` |
| Selection trigger? | Adobe `PREVIEW_SELECTION_END` → `getSelectedContent`, more than 10 characters |
| Navigation? | `/api/pdf` blob → File → `gotoLocation` (1-based; off-by-one bug) |
| Cancelling requests? | AbortController (browser side only) |
| Docker stages? | Node build → Python builder → slim runtime |
| Build numbers? | ~75 → ~13 min; 14.1 → 3.57 GB (at hackathon time) |
| Why is `exec` in the entrypoint? | Uvicorn becomes PID 1 and receives SIGTERM |
| Biggest security issue? | Secrets in the image and in git history; no authentication |
| Biggest improvement? | Citations, re-ranking and an evaluation set |

---

## 11. Whiteboard drills

**Drill 1: Draw the architecture in 2 minutes.**
Reproduce §5 from memory, including the two pipelines and the three external services.

**Drill 2: Fuse these two lists with RRF (k = 60), treating each item as its own key.**
Dense: [A, B, C]. Sparse: [C, D, A].

<details>
<summary>Answer</summary>

- A = 1/61 + 1/63 = 0.01639 + 0.01587 = **0.03226**
- C = 1/63 + 1/61 = **0.03226** (exactly ties with A)
- B = 1/62 = **0.01613**
- D = 1/62 = **0.01613** (ties with B)

Order: **A, C, B, D**. Ties keep the order in which items were first seen, because the dense list is processed first and the sort is stable.
</details>

**Drill 3: Chunk windows.**
For 11 sentences, write the windows for size 5 with overlap 1, then for size 5 with overlap 2.

<details>
<summary>Answer</summary>

- Overlap 1 (step 4): [s0–s4], [s4–s8], [s8–s10]
- Overlap 2 (step 3): [s0–s4], [s3–s7], [s6–s10]
</details>

**Drill 4: Prove that L2 distance and cosine similarity rank unit vectors identically.**

<details>
<summary>Answer</summary>

‖a−b‖² = ‖a‖² + ‖b‖² − 2a·b = 1 + 1 − 2cos(a, b) = 2 − 2cos(a, b). This decreases as cosine increases, so the smallest distance is always the highest similarity.
</details>

**Drill 5: BM25 IDF with N = 10 chunks.**
Compute the IDF of a word that appears in 1 chunk and of one that appears in 9.

<details>
<summary>Answer</summary>

- In 1 chunk: ln(9.5 / 1.5) = ln(6.33) ≈ **1.85**
- In 9 chunks: ln(1.5 / 9.5) ≈ **−1.85**. That's negative, so it's raised to the small floor of 0.25 × the average IDF.
</details>

**Drill 6: Draw the sequence diagram.**
Selection → related-sections → insights → podcast → click to navigate, labelling each endpoint and each external call (Gemini, Azure).

**Drill 7: Estimate the memory for 250,000 chunks in a flat index.**

<details>
<summary>Answer</summary>

250,000 × 384 × 4 bytes = 384,000,000 bytes, about **384 MB** of vectors. Add the metadata (≈ 250 MB of text) and the model.
</details>

---

## 12. Code to write from memory

**Sentence-window chunking:**

```python
from nltk.tokenize import sent_tokenize

def chunk_text(text: str, chunk_size: int = 5, overlap: int = 1) -> list[str]:
    sentences = sent_tokenize(" ".join(text.split()))
    step = max(chunk_size - overlap, 1)
    chunks, start = [], 0
    while start < len(sentences):
        end = start + chunk_size
        chunks.append(" ".join(sentences[start:end]))
        if end >= len(sentences):
            break
        start += step
    return chunks
```

**Reciprocal Rank Fusion at section level (simplified):**

```python
def rrf(dense: list[dict], sparse: list[dict], k: int = 60) -> list[dict]:
    scores, first_seen = {}, {}
    for results in (dense, sparse):
        for rank, r in enumerate(results, start=1):
            key = (r["doc_name"], r["section_title"], r["page"])
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            first_seen.setdefault(key, r)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)   # stable for ties
    return [dict(first_seen[key], rrf_score=score) for key, score in ranked]
```

**Embeddings, FAISS and BM25:**

```python
import faiss, numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.IndexFlatL2(model.get_sentence_embedding_dimension())   # 384
metadata: list[dict] = []

vectors = model.encode(chunks, convert_to_numpy=True)                 # (n, 384) float32, unit length
index.add(vectors)
metadata.extend(chunk_metadata)                                        # same order as the vectors

q = model.encode([query], convert_to_numpy=True)
distances, ids = index.search(q, 20)
dense = [dict(metadata[i], faiss_score=float(d)) for d, i in zip(distances[0], ids[0]) if i != -1]

bm25 = BM25Okapi([c.lower().split() for c in chunks])                  # k1=1.5, b=0.75
scores = bm25.get_scores(query.lower().split())
sparse = [dict(metadata[i], bm25_score=float(scores[i])) for i in np.argsort(scores)[::-1][:20]]
```

**FastAPI: a background task, and moving blocking work off the event loop:**

```python
@router.post("/ingest")
async def ingest(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    for f in files:
        path = os.path.join(UPLOAD_DIR, os.path.basename(f.filename))   # basename: the safer version
        with open(path, "wb") as out:
            shutil.copyfileobj(f.file, out)
        background_tasks.add_task(process_and_index_pdf, pdf_path=path, doc_name=f.filename)
    return {"message": f"Processing started for {len(files)} documents"}

@router.post("/podcast")
async def podcast(req: InsightsRequest):
    path = await run_in_threadpool(generate_podcast_audio, req.query_text, req.related_snippets)
    return FileResponse(path, media_type="audio/mpeg")
```

---

## 13. Questions to ask the interviewer

- How does your team evaluate retrieval and LLM quality before shipping a change?
- What does your search or RAG stack look like: vector database, hybrid search, re-ranking?
- How do you manage LLM cost and latency in production?
- How do AI features go from prototype to production here?
- What would success in this role look like in the first 90 days?

---

## 14. Last-hour cheat sheet

```
WHAT      Select text in a PDF → top-5 related sections from your library → Gemini insights → narrated MP3 → click to jump
CONTEXT   Adobe Hackathon 2025 "Connecting the Dots" · team of 2 · ~6 days (15–20 Aug 2025)
MY PART   FastAPI backend · hybrid search (FAISS+BM25+RRF) · Gemini + Azure TTS · Adobe viewer & selection · Docker
TEAMMATE  React scaffold · upload UI · parser rewrite ("better chunks") · gotoLocation navigation · CSP

INGEST    PyMuPDF blocks → bold-font headings → sections → 5-sentence windows (overlap 1) → MiniLM 384-d (normalized)
          → FAISS IndexFlatL2 + BM25Okapi (k1 1.5, b 0.75) + metadata.json   ·   BackgroundTasks + threading.Lock
QUERY     embed → FAISS top 20 ─┐
          tokens → BM25 top 20 ─┴→ RRF k=60, key=(doc, section, page), scores add → top 10 → dedupe → top 5
WHY L2    MiniLM normalizes → ‖a−b‖² = 2 − 2cos → same ranking as cosine
RAG       role + delimited selected text + numbered snippets + markdown template (key points, contradictions, takeaways)
          Gemini 2.5 Flash via LangChain, temperature 0.5 · no snippets → no LLM call
PODCAST   Gemini script 300–500 words → cleaned, ≤2,000 chars → Azure OpenAI tts (voice nova) → MP3 → deleted after 300 s
          SINGLE narrator (the README says 2 speakers: be honest, explain the 2-voice design)
FRONTEND  React + TS + Vite · Adobe: PREVIEW_SELECTION_END → getSelectedContent → gotoLocation (1-based → off-by-one bug)
          related → insights → podcast run sequentially · AbortController cancels on the browser side only
DOCKER    node:18-alpine → python:3.10-slim builder (CPU torch first) → slim runtime · non-root · HEALTHCHECK · :8080
          75→13 min, 14.1→3.57 GB at hackathon time · today unpinned sentence-transformers pulls CUDA torch → lock files

GAPS      no tests · blocking calls in async endpoints · page off-by-one · mock History UI · CORS * + no auth
          secrets baked into image & in git history · single-process state · performance claims unmeasured
NEXT      citations · cross-encoder re-rank · eval set (Recall@5/MRR) · job status · parallel + streaming
          vector DB + queue workers · auth · runtime secrets · lock dependencies · tests + CI
```
