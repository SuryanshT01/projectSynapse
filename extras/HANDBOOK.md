# Project Synapse Handbook

The theory book for Project Synapse. It covers every concept, term and flow in the project, starting from zero, and ties each one to the code that uses it.

Companion docs: [RUNBOOK.md](RUNBOOK.md) (setup, running, deployment, troubleshooting) and [RESUME_HANDBOOK.md](RESUME_HANDBOOK.md) (interview prep).

---

## How to read this handbook

- **Part 1** gives you the whole picture in about 10 minutes.
- **Part 2** explains each concept by answering the same questions: *What is it? Why is it needed? How does Synapse use it, and where in the code? What are its limits?*
- **Part 3** follows every user action from start to finish, one step at a time.
- **Part 4** is reference material: data formats, settings and an A–Z glossary.
- **Part 5** is a reality check. It compares the README's claims with the code, then lists known limitations, improvement ideas and a self-quiz.

Code links point to files in this repo. Line numbers match commit `56e2837`.

## Contents

- [Part 1: The big picture](#part-1-the-big-picture)
  - [1.1 The problem](#11-the-problem)
  - [1.2 What the app does](#12-what-the-app-does)
  - [1.3 The two pipelines](#13-the-two-pipelines)
  - [1.4 Architecture and tech stack](#14-architecture-and-tech-stack)
  - [1.5 Repository map](#15-repository-map)
  - [1.6 Concept-to-flow map](#16-concept-to-flow-map)
- [Part 2: Concepts](#part-2-concepts)
  - [2.1 PDFs and text extraction (PyMuPDF)](#21-pdfs-and-text-extraction-pymupdf)
  - [2.2 Document structure: headings and sections](#22-document-structure-headings-and-sections)
  - [2.3 Tokens and tokenization](#23-tokens-and-tokenization)
  - [2.4 Chunking](#24-chunking)
  - [2.5 Embeddings and vector space](#25-embeddings-and-vector-space)
  - [2.6 Transformers, BERT, Sentence-BERT and all-MiniLM-L6-v2](#26-transformers-bert-sentence-bert-and-all-minilm-l6-v2)
  - [2.7 Measuring similarity: cosine, dot product, L2](#27-measuring-similarity-cosine-dot-product-l2)
  - [2.8 Vector search, FAISS and vector databases](#28-vector-search-faiss-and-vector-databases)
  - [2.9 Keyword search: TF-IDF and BM25](#29-keyword-search-tf-idf-and-bm25)
  - [2.10 Hybrid search and Reciprocal Rank Fusion (RRF)](#210-hybrid-search-and-reciprocal-rank-fusion-rrf)
  - [2.11 Retrieval-Augmented Generation (RAG)](#211-retrieval-augmented-generation-rag)
  - [2.12 LLMs, prompts, Gemini and LangChain](#212-llms-prompts-gemini-and-langchain)
  - [2.13 Text-to-speech and the podcast](#213-text-to-speech-and-the-podcast)
  - [2.14 Backend engineering concepts](#214-backend-engineering-concepts)
  - [2.15 Frontend concepts](#215-frontend-concepts)
  - [2.16 DevOps concepts: Docker and WSL](#216-devops-concepts-docker-and-wsl)
- [Part 3: End-to-end flows](#part-3-end-to-end-flows)
- [Part 4: Reference](#part-4-reference)
- [Part 5: Reality check](#part-5-reality-check)

---

# Part 1: The big picture

## 1.1 The problem

Say you have a library of PDFs: research papers, reports, study notes. While reading one, you want answers to questions like these:

- *Where else in my documents is this discussed?*
- *Does anything I've read contradict this?*
- *What are the key takeaways?*

Doing that by hand means opening files and pressing Ctrl+F. That only finds **exact words** in **one file**. It can't find the same **idea** written in different words.

Project Synapse was built for the **Adobe Hackathon 2025 "Connecting the Dots"** challenge, which had several rounds:

| Round | Goal | What remains in this repo |
|---|---|---|
| 1A | Extract a PDF's structure: title, headings and page numbers | [pdf_parser_1a.py](../backend/app/core/pdf_parser_1a.py), rewritten as a simpler heuristic for the finale, plus the old LightGBM model files |
| 1B | Persona-driven document intelligence: find the most relevant sections across many PDFs | The idea of retrieval at the section level |
| Finale | An interactive reading app built on the Adobe PDF Embed API, with related sections, an "insights bulb" and audio | This whole app |

## 1.2 What the app does

1. **Build a library.** You upload PDFs, and the server indexes them in the background.
2. **Read.** You open a PDF in Adobe's viewer.
3. **Select text.** You highlight any passage longer than 10 characters.
4. **Connect the dots.** Up to 5 related sections from your library appear in a sidebar.
5. **Get insights.** Gemini writes key points, contradictions or gaps, takeaways and connections.
6. **Listen.** A narrated audio summary (MP3) is generated.
7. **Jump.** Clicking a related section opens that PDF at the page where the section starts.

## 1.3 The two pipelines

The whole system comes down to two pipelines:

```
INGESTION PIPELINE  (runs once per uploaded PDF, in the background)

  PDF
   └─► PyMuPDF text blocks
        └─► heading detection
             └─► sections (heading + body text)
                  └─► sentence chunks (5 sentences, 1 overlapping)
                       ├─► MiniLM embeddings (384 numbers each) ──► FAISS index      (index.faiss)
                       ├─► lower-cased word lists ────────────────► BM25 corpus      (metadata_bm25.json)
                       └─► doc name, section title, page, text ──► metadata list    (metadata.json)


QUERY PIPELINE  (runs every time you select text)

  selected text
   ├─► embed with MiniLM ──► FAISS: top 20 closest chunks ──┐
   └─► split into words ───► BM25:  top 20 keyword matches ─┴─► Reciprocal Rank Fusion
                                                                  └─► top 10 ─► dedupe ─► top 5 sections
                                                                                          │
         ┌────────────────────────────────────────────────────────────────────────────────┤
         ▼                                                                                ▼
  Gemini + insights prompt ─► markdown insights       Gemini + podcast prompt ─► script ─► Azure OpenAI TTS ─► MP3
```

This pattern is **Retrieval-Augmented Generation (RAG)**. The system retrieves the most relevant pieces of *your* documents, then hands them to a large language model to generate something useful.

## 1.4 Architecture and tech stack

```
Browser
  React 18 + TypeScript single-page app, built with Vite
  Adobe PDF Embed API viewer (script loaded from Adobe's CDN)
     │
     │  HTTP  /api/*
     ▼
FastAPI app on Uvicorn  (one Python process)
  ├── api/routes.py ............ HTTP endpoints
  ├── core/processing.py ....... PDF → sections → chunks
  ├── core/pdf_parser_1a.py .... PDF text blocks → headings → sections
  ├── core/search.py ........... MiniLM model, FAISS, BM25, RRF  (all kept in RAM)
  └── core/generation.py ....... insight and podcast prompts
        ├── scripts/chat_with_llm.py ....► Google Gemini API      (insights, podcast script)
        └── scripts/generate_audio.py ...► Azure OpenAI TTS REST  (MP3)  |  or GCP TTS  |  or local espeak-ng

Disk:  backend/data/uploads/*.pdf, index.faiss, metadata.json, metadata_bm25.json
In Docker, the same FastAPI process also serves the built React files on port 8080.
```

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, React Router, Tailwind CSS, shadcn/ui (Radix), lucide icons |
| PDF viewing | Adobe PDF Embed API (View SDK) |
| Backend | Python 3.10, FastAPI, Uvicorn, Pydantic, pydantic-settings, python-dotenv |
| PDF parsing | PyMuPDF (`fitz`), NLTK Punkt |
| Semantic search | sentence-transformers (`all-MiniLM-L6-v2`), PyTorch (CPU), FAISS (`IndexFlatL2`) |
| Keyword search | rank-bm25 (`BM25Okapi`) |
| Fusion | Reciprocal Rank Fusion, hand-written |
| LLM | Google Gemini 2.5 Flash through LangChain (`langchain-google-genai`) |
| Text-to-speech | Azure OpenAI `tts` model over REST; Google Cloud TTS or espeak-ng as alternatives; pydub + ffmpeg |
| Deployment | Docker multi-stage build, a bash entrypoint, one container on port 8080 |

## 1.5 Repository map

```
projectSynapse/
├── backend/
│   ├── main.py                        FastAPI app: CORS, startup (loads search engine), /api router, serves React build
│   ├── requirements.txt               Python dependencies for local development
│   ├── requirements-core.txt          not used by the Dockerfile (leftover)
│   ├── test_tts.py                    standalone check of Azure TTS credentials
│   └── app/
│       ├── api/routes.py              all HTTP endpoints
│       ├── core/config.py             Settings: paths, chunk size, top-k (from environment or .env)
│       ├── core/pdf_parser_1a.py      PDF → title + sections (bold-heading heuristic)
│       ├── core/processing.py         sections → sentence chunks → index
│       ├── core/search.py             embeddings, FAISS, BM25, RRF, saving to disk
│       ├── core/generation.py         insights and podcast orchestration (the prompts)
│       ├── scripts/chat_with_llm.py   Gemini through LangChain
│       ├── scripts/generate_audio.py  TTS providers: azure | gcp | local
│       └── models/*.joblib            Round 1A LightGBM classifier (no longer used)
├── frontend/
│   ├── vite.config.ts                 dev server on port 8080; reads ../.env
│   ├── index.html                     Content-Security-Policy allowing Adobe + localhost
│   └── src/
│       ├── App.tsx                    routes: /  /reader  /history
│       ├── components/HomePage.tsx            upload to library / open a PDF to read
│       ├── pages/ReaderView.tsx               runs the analysis flow
│       ├── components/AdobePDFViewer.tsx      Adobe SDK: render, selection event, gotoLocation
│       ├── components/TextSelectionSidebar.tsx related content / insights / audio UI
│       ├── pages/HistoryPage.tsx, components/LibrarySidebar.tsx, RightSidebar.tsx   mock data only
│       └── components/ui/*                    shadcn/ui component library (generated)
├── Dockerfile, entrypoint.sh, .dockerignore
├── Readme.md, DEBUG.md, screenshots/
└── extras/                            these guides
```

## 1.6 Concept-to-flow map

This table shows where each concept is used. The columns are the flows described in Part 3.

| Concept | Ingest | Search | Insights | Podcast | Navigate | Deploy |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| PyMuPDF text extraction | ✓ | | | | | |
| Heading heuristic, sections | ✓ | | | | | |
| NLTK Punkt sentence splitting | ✓ | | | | | NLTK data baked into the image |
| Chunking | ✓ | | | | | |
| sentence-transformers / MiniLM | encode chunks | encode query | | | | model downloaded at startup |
| FAISS | add | search | | | | index.faiss on disk |
| BM25 | rebuild | score | | | | metadata_bm25.json on disk |
| Reciprocal Rank Fusion | | ✓ | | | | |
| RAG / LLM (Gemini) | | | ✓ | script | | `GOOGLE_API_KEY` |
| TTS (Azure OpenAI) | | | | ✓ | | `AZURE_TTS_*` |
| Adobe PDF Embed API | | selection event | | | gotoLocation | `VITE_ADOBE_CLIENT_ID` at build time |
| BackgroundTasks, threading.Lock | ✓ | | | | | |
| run_in_threadpool | | | | ✓ | | |
| AbortController | | ✓ | ✓ | ✓ | | |
| Docker, entrypoint, env vars | | | | | | ✓ |

---

# Part 2: Concepts

## 2.1 PDFs and text extraction (PyMuPDF)

**What it is.** A PDF isn't stored as paragraphs and headings. It's a list of drawing instructions, something like: *"draw these characters in font Helvetica-Bold, size 14, at x=72, y=90."* Usually nothing says *"this is a heading."* Any structure has to be **inferred** from fonts, sizes and positions.

**PyMuPDF**, imported as `fitz`, is a fast Python binding for the MuPDF engine. Calling `page.get_text("dict")` returns a nested structure:

```
page
└── blocks[]          type 0 = text, type 1 = image; bbox = (x0, y0, x1, y1)
    └── lines[]
        └── spans[]   a run of text with a single style: text, font ("Arial-BoldMT"), size, flags, bbox
```

Coordinates are measured in **points** (1/72 inch). The origin is the **top-left** corner and y grows **downward**, so a smaller `y0` means higher up the page.

**How Synapse uses it.**
- [`extract_text_blocks`](../backend/app/core/pdf_parser_1a.py#L72-L88) opens the PDF and loops over its pages with `enumerate`, which gives **0-based page numbers**. It keeps only text blocks that aren't empty and tags each with `page_num`.
- [`normalize_text`](../backend/app/core/pdf_parser_1a.py#L28-L31) replaces ligature characters (`ﬀ`, `ﬁ`, `ﬂ` become `ff`, `fi`, `fl`) and collapses whitespace. Without this, "ﬁnance" wouldn't match "finance".

**Limits.**
- **Scanned PDFs** are images with no text layer, so nothing gets extracted.
- **Multi-column layouts** are ordered by vertical position, so text from two columns can get interleaved.

## 2.2 Document structure: headings and sections

**What it is.** A **section** is a heading plus the body text under it, up to the next heading. The **outline** is the ordered list of sections. Sections do two jobs: they give each chunk a readable label (such as "Transfer Learning, page 3"), and they keep chunks from mixing text from different topics.

**How Synapse detects headings.** [`is_heading`](../backend/app/core/pdf_parser_1a.py#L93-L124) treats a text block as a heading only when **all** of these are true:

1. At least one span's **font name contains "bold"** (for example `Arial-BoldMT`).
2. It doesn't contain the bullet character `•`.
3. It has **1 to 29 words**.
4. It doesn't end with `.`, `?`, `!` or `,`. Sentences end that way; headings usually don't.

After that:
- [`clean_heading_text`](../backend/app/core/pdf_parser_1a.py#L45-L50) strips leading numbering ("2.1 ") and trailing page numbers ("Introduction 4").
- [`associate_content_to_headings`](../backend/app/core/pdf_parser_1a.py#L126-L150) collects, for each heading, every non-heading block that comes after it and before the next heading. It compares page number first, then vertical position.
- The **title** is the text of the first heading. The first heading gets level `H1` and all later ones get `H2`. Search never uses these levels.
- The parser returns `{"title": "...", "outline": [{"level", "text", "page", "content"}, ...]}`.

**Round 1A history: the LightGBM model.** The first backend commit had a 930-line parser that **classified** blocks with a LightGBM model. It used these per-block features:

| Feature group | Features |
|---|---|
| Font | `font_size_ratio` (block font size ÷ document median size), `is_bold` |
| Content | `word_count`, `is_all_caps`, `is_title_case`, `is_form_field`, `is_numbered_list`, `is_page_number` |
| Layout | `x_position_norm`, `y_position_norm`, `block_width_norm`, `block_height`, `space_above` |

That parser also ran **OCR** with Tesseract on scanned pages and filtered out headers, footers and tables. For the finale, a later commit ("processing improved better chunks") rewrote it as the bold-font heuristic above. `StructurePredictor` and `models/*.joblib` are still in the repo, but [`extract_structure_from_pdf`](../backend/app/core/pdf_parser_1a.py#L155-L190) never creates a `StructurePredictor`. Its `model_path` and `encoder_path` arguments go unused.

Terms from that history:
- **LightGBM**: Microsoft's gradient-boosted decision tree library. It builds many small trees, each one correcting the mistakes of the ones before, and it works well on tabular features like these.
- **Label encoder**: converts class names (`H1`, `H2`, `Body_Text`) to integers for the model, and back again.
- **joblib**: a library that saves Python objects, such as a trained model, to disk and loads them back.
- **OCR (Optical Character Recognition)**: turns an image of text into actual text. Tesseract is a popular open-source OCR engine, and `pytesseract` is its Python wrapper. Both are still installed, but the current code never calls them.

**Limits of the heuristic.**
- Headings that are bold only through a style flag (without "Bold" in the font name), or that stand out only by size, are **missed**.
- A PDF with **no bold text** produces zero sections, which means zero chunks, and the document is **not searchable at all**.
- Text **before the first heading** is dropped.
- A bold phrase inside a paragraph can be mistaken for a heading.

## 2.3 Tokens and tokenization

"Token" means different things in different parts of this project:

| Kind | Tool | Example | Used for |
|---|---|---|---|
| Sentence | NLTK Punkt `sent_tokenize` | "Dr. Smith trained it. It worked." gives 2 sentences, because Punkt knows "Dr." doesn't end one | Chunking |
| Word (for BM25) | `text.lower().split()` | "Transfer learning, explained" gives `["transfer", "learning,", "explained"]` | Keyword search |
| Subword (inside the model) | WordPiece tokenizer in MiniLM | "embeddings" gives `em`, `##bed`, `##ding`, `##s` | Input to the embedding model (maximum 256) |
| LLM token | Gemini's tokenizer | about 4 characters of English on average | Prompt and response size, billing |

**NLTK and Punkt.** NLTK (Natural Language Toolkit) is a classic Python library for language processing. **Punkt** is its unsupervised sentence-boundary model (Kiss & Strunk, 2006). It has learned common abbreviations and how sentences start, so it doesn't split at "e.g." or "Fig. 3". It needs downloaded data files: `punkt`, which [processing.py](../backend/app/core/processing.py#L23-L26) checks for when it's imported, and `punkt_tab`, which newer NLTK versions use.

**Note:** the BM25 tokenizer keeps punctuation, so `"learning,"` and `"learning"` count as different words. It also does no stemming and doesn't remove stop words. That's simple, but it loses information.

## 2.4 Chunking

**What it is.** Chunking means splitting long text into smaller, self-contained pieces called **chunks**. Each chunk is indexed and retrieved on its own.

**Why it's needed.**
1. **Model input limits.** MiniLM reads at most 256 word pieces; anything beyond that is cut off.
2. **Precision.** A single vector for a 10-page section is a blurry average. Small chunks match precisely.
3. **LLM budget.** The prompt should contain only the most relevant pieces, which saves cost and time and keeps the model focused.
4. **Pointing to a location.** A result can point to a specific place in a document.

**Common strategies:**
- **Fixed size**: every N characters or tokens.
- **Sentence-based**: groups of whole sentences.
- **Recursive**: split by paragraph, then sentence, then word, until pieces are small enough.
- **Semantic**: split where the meaning shifts.
- **Structure-aware**: respect headings and sections.

Synapse combines **structure-aware** splitting with **sentence windows**.

**How Synapse chunks.** See [`chunk_text`](../backend/app/core/processing.py#L29-L46) and [`process_and_index_pdf`](../backend/app/core/processing.py#L48-L99).
1. Skip any section whose content has fewer than 5 words.
2. Normalize whitespace and split the text into sentences with Punkt.
3. Slide a window of `CHUNK_SIZE = 5` sentences, moving forward by `CHUNK_SIZE − CHUNK_OVERLAP = 4` sentences each time. Neighbouring chunks share 1 sentence.
4. Attach metadata to each chunk and add it to the index.

Worked example: a section with 11 sentences, `s0` to `s10`:

```
chunk 1:  s0  s1  s2  s3  s4
chunk 2:                  s4  s5  s6  s7  s8
chunk 3:                                  s8  s9  s10
```

The loop stops as soon as a window reaches the last sentence. If the overlap were set to be at least the chunk size, the window would advance by 1 instead, so it can't loop forever.

**Why the overlap?** A sentence often depends on the one before it, such as *"This approach cut errors by 30%."* Overlap keeps that context available when a chunk boundary falls between the two.

**Chunks never cross section boundaries,** so every chunk carries a clean section title and page.

| Smaller chunks (1–2 sentences) | Larger chunks (10+ sentences) |
|---|---|
| Very precise matches | Blurrier embeddings |
| Little context for the LLM | More context |
| More vectors to store and search | May go past the 256-token model limit |

Five sentences is roughly 80–150 words, or about 100–200 word pieces, which usually fits under MiniLM's limit. If a chunk is longer, the embedding ignores the tail, but the full text is still stored and shown.

**Metadata for each chunk,** stored in `metadata.json`. The comments are added here for explanation; real JSON has none.

```jsonc
{
  "doc_id": "2f1c…",                    // random UUID created for each upload
  "doc_name": "paper-a.pdf",            // file name, used to fetch the PDF later
  "document_title": "Deep Transfer Learning",
  "section_title": "Transfer Learning",
  "page": 2,                            // 0-based page where the section's heading is
  "chunk_text": "Transfer learning reuses a model trained on…"
}
```

**Limits.**
- `page` is the page of the **heading**, not necessarily the page the chunk is on.
- Uploading the same file again adds duplicate chunks, because each upload gets a new `doc_id`.

## 2.5 Embeddings and vector space

**What it is.** An **embedding** is a list of numbers (a **vector**) that represents the *meaning* of a piece of text. The model is trained so that texts with similar meanings get vectors pointing in similar directions.

Imagine a simplified 2-D version:

```
   ▲
   │    • "how to service your vehicle"
   │   • "car maintenance tips"
   │
   │                          • "banana bread recipe"
   └────────────────────────────────────────────►
```

In Synapse the vectors have **384 dimensions**. No single number means anything on its own; the meaning is in the overall direction.

**Dense vs sparse vectors.** Embeddings are **dense**: all 384 numbers carry information. Keyword representations are **sparse**: one slot per vocabulary word, and almost all of them are zero. Semantic search uses dense vectors; BM25 uses sparse ones.

**Why it matters.** Semantic search can find *"vehicle upkeep"* when you selected *"car maintenance"*, even though the two phrases share no words.

## 2.6 Transformers, BERT, Sentence-BERT and all-MiniLM-L6-v2

**Transformer.** The neural network architecture behind modern NLP (Vaswani et al., 2017). Its core operation is **self-attention**: every token looks at every other token to build a representation that depends on context. That's how "bank" near "river" ends up different from "bank" near "loan".

**BERT.** An **encoder-only** transformer, pretrained by hiding words and learning to predict them. It outputs one vector per token. Raw BERT isn't good at judging whether two sentences are similar. Running a model over every pair of texts would also be far too slow for search.

**Sentence-BERT (SBERT).** Reimers & Gurevych (2019) fine-tuned BERT-style models in a **siamese** (bi-encoder) setup. Each text is encoded **independently** into a single vector, and training makes the cosine similarity between vectors reflect how similar the meanings are. You encode your library once, then compare each new query using cheap vector maths.

| Bi-encoder (what Synapse uses) | Cross-encoder |
|---|---|
| Encodes the query and each document separately | Reads the (query, document) pair together |
| Document vectors are computed ahead of time, so searching thousands is fast | Must run the model for every pair, so it's slow |
| Slightly less accurate | More accurate, so it's used to **re-rank** a short list |

**all-MiniLM-L6-v2** is the model Synapse uses (`EMBEDDING_MODEL_NAME` in [config.py](../backend/app/core/config.py#L21)). According to the model's `modules.json` on Hugging Face, its pipeline is:

```
text → WordPiece tokens (max 256) → MiniLM transformer (6 layers, hidden size 384) → mean pooling → L2 normalization → 384-number unit vector
```

- **MiniLM** is a small model **distilled** from a larger one. In knowledge distillation, a small "student" model learns to imitate a big "teacher". The result has about 22 million parameters, is about 90 MB, and runs fast on a CPU.
- **Mean pooling** averages all the token vectors (ignoring padding) into one vector for the whole text.
- **Normalization** scales the vector to length 1. This makes L2 distance and cosine similarity produce the same ranking (see §2.7).
- It was fine-tuned on about 1 billion sentence pairs with a **contrastive** objective, which pulls matching pairs together and pushes others apart.
- It's focused on English, and input longer than 256 word pieces is truncated.

**The sentence-transformers library** wraps all of this:
- `SentenceTransformer("all-MiniLM-L6-v2")` downloads `sentence-transformers/all-MiniLM-L6-v2` from the **Hugging Face Hub** the first time and caches it in `~/.cache/huggingface`. Public models need no account.
- `model.encode(texts, convert_to_numpy=True)` returns a NumPy array of shape `(n, 384)` with type float32.
- `model.get_sentence_embedding_dimension()` returns 384. Synapse uses this to create an empty FAISS index.

**PyTorch** is the deep-learning framework that actually runs the model. Synapse uses the **CPU-only** build, which has no NVIDIA CUDA libraries, because it runs on machines without a GPU.

**How Synapse uses it.** The model is loaded once at startup by [`load_search_engine`](../backend/app/core/search.py#L29-L76) into the global variable `MODEL`. It encodes chunks during ingestion ([`add_chunks_to_index`](../backend/app/core/search.py#L233-L278)) and encodes the selected text for every query ([`search_faiss`](../backend/app/core/search.py#L152-L171)).

## 2.7 Measuring similarity: cosine, dot product, L2

For two vectors **a** and **b**:

| Measure | Formula | Meaning |
|---|---|---|
| Dot product | a·b = Σ aᵢbᵢ | Bigger means more similar, but it also grows with vector length |
| Cosine similarity | a·b / (‖a‖ ‖b‖) | Compares direction only: 1 = same direction, 0 = unrelated, −1 = opposite |
| Euclidean (L2) distance | ‖a − b‖ = √Σ(aᵢ − bᵢ)² | Smaller means more similar |

**The key identity.** For vectors of length 1, which is what MiniLM produces:

```
‖a − b‖²  =  ‖a‖² + ‖b‖² − 2·(a·b)  =  1 + 1 − 2·cos(a, b)  =  2 − 2·cos(a, b)
```

So ranking by **smallest squared L2 distance** gives exactly the same order as ranking by **highest cosine similarity**. That's why Synapse can use FAISS's `IndexFlatL2` and still get cosine-quality results.

**Worked example** with 2-D unit vectors: a = (1, 0), b = (0.8, 0.6), c = (0, 1).
- cos(a, b) = 0.8, and ‖a − b‖² = 0.2² + 0.6² = 0.40, which equals 2 − 2(0.8). ✓
- cos(a, c) = 0, and ‖a − c‖² = 1 + 1 = 2.0, which equals 2 − 0. ✓

By either measure, b is the vector closer to a.

**In the API response,** `faiss_score` is this **squared L2 distance**. Lower is better, and for unit vectors it ranges from 0 to 4. To convert it: `cosine = 1 − faiss_score / 2`. For example, a score of 0.62 means a cosine similarity of 0.69.

## 2.8 Vector search, FAISS and vector databases

**Nearest-neighbour search** means: given a query vector, find the k stored vectors closest to it.

- **Exact search** (also called flat or brute force) compares the query with every stored vector. The cost grows with N × d (number of vectors × dimensions). It always finds the true top k.
- **Approximate nearest neighbour (ANN)** search organizes the vectors in advance so most comparisons can be skipped. It's much faster at millions of vectors, but it can occasionally miss a true neighbour (recall below 100%). Common types:
  - **IVF (inverted file):** group vectors into `nlist` clusters with k-means, then search only the `nprobe` clusters nearest the query. Needs a training step.
  - **HNSW (Hierarchical Navigable Small World):** a layered graph that you walk from coarse to fine neighbours. Very fast with high recall, but uses more memory.
  - **PQ (product quantization):** compresses each vector into a short code to save memory, losing some precision.

**FAISS** (Facebook AI Similarity Search, from Meta AI) is a C++ library with Python bindings that implements all of these, on CPU or GPU. It's an **index library, not a database server.**

**How Synapse uses FAISS** (all in [search.py](../backend/app/core/search.py)):

| Operation | Code | Notes |
|---|---|---|
| Create | `faiss.IndexFlatL2(384)` | Exact search, no training needed |
| Add | `INDEX.add(embeddings)` | Vectors get IDs 0, 1, 2, … in the order they're added |
| Search | `distances, ids = INDEX.search(query_vec, top_k)` | Returns squared L2 distances; an ID of −1 means there were fewer than k vectors |
| Count | `INDEX.ntotal` | Number of stored vectors |
| Save / load | `faiss.write_index` / `faiss.read_index`, file `backend/data/index.faiss` | The whole file is rewritten after each PDF |

**The alignment rule.** FAISS stores only numbers. To know *which text* vector #17 came from, Synapse keeps a Python list `METADATA` in which `METADATA[17]` describes the same chunk. Likewise, `TOKENIZED_CORPUS[17]` holds its word list for BM25. All three are appended in the same order, under a lock, and saved together. If they ever get out of step, for example because you deleted just one of the files, searches return the wrong text.

**Memory maths.** A flat index stores raw float32 numbers: 384 × 4 bytes ≈ 1.5 KB per chunk. So 10,000 chunks take about 15 MB, and 1 million chunks about 1.5 GB.

**A vector database** is a service built around vector search. On top of search, it gives you persistence, updates and deletes, **metadata filtering** (such as "only documents belonging to user X"), safe concurrent access, replication and backups. Examples: Qdrant, Weaviate, Milvus, Pinecone, Chroma, pgvector (a PostgreSQL extension), and the k-NN feature of OpenSearch or Elasticsearch.

**Synapse's "vector database"** is hand-built and runs in a single process: a FAISS index, JSON metadata files and in-memory Python lists. For a hackathon this was a good choice: no infrastructure to run, fast, and easy to ship in one container. What it lacks:
- updating or deleting documents,
- filters (such as "leave out the PDF I'm currently reading"),
- safe access from more than one process,
- atomic (all-or-nothing) writes.

**When to switch.** A flat FAISS index works well up to roughly a few hundred thousand chunks on one machine. Beyond that, or once you need per-user filters and several API servers, move to an ANN index or a real vector database.

## 2.9 Keyword search: TF-IDF and BM25

**Sparse retrieval** treats a document as a "bag of words" and scores documents by the query words they contain.

**The TF-IDF idea:**
- **TF (term frequency):** a word that appears often in a chunk says more about that chunk.
- **IDF (inverse document frequency):** a word that appears in only a few chunks is more informative. "faiss" tells you far more than "the".

**BM25** ("Best Matching 25", from the Okapi search system) improves on TF-IDF by capping the effect of repetition and adjusting for chunk length:

```
score(D, Q) = Σ over query words q:   IDF(q) · f(q,D)·(k1 + 1) / ( f(q,D) + k1·(1 − b + b·|D| / avgdl) )
```

- `f(q,D)`: how many times word q appears in chunk D
- `|D|`: the chunk's length in words; `avgdl`: the average chunk length
- **k1 = 1.5** (the rank-bm25 default) controls **saturation**: the 10th repeat of a word adds much less than the 2nd.
- **b = 0.75** controls **length normalization**, so long chunks don't win just by being long.
- IDF in rank-bm25's `BM25Okapi` is `ln((N − n(q) + 0.5) / (n(q) + 0.5))`, where N is the number of chunks and n(q) is how many chunks contain q. A word found in more than half the chunks would get a negative IDF, so the library replaces it with a small positive floor (ε = 0.25 × the average IDF).

**IDF example** with N = 3 chunks:
- "faiss" appears in 1 chunk: ln(2.5 / 1.5) ≈ **0.51**, so it's informative.
- "the" appears in all 3: ln(0.5 / 3.5) ≈ **−1.95**, which becomes the small floor, so it gets almost no weight.

**How Synapse uses BM25** ([search.py](../backend/app/core/search.py)):
- Each chunk goes through [`tokenize_text`](../backend/app/core/search.py#L84-L87) (lower-case, then split on whitespace) and is appended to `TOKENIZED_CORPUS`.
- After every PDF, `BM25Okapi(TOKENIZED_CORPUS)` is **rebuilt from scratch**. The library can't add documents incrementally, because IDF depends on the whole corpus. The word lists are saved to `metadata_bm25.json`.
- For a query, `BM25_INDEX.get_scores(query_tokens)` scores **every** chunk, and `np.argsort` picks the top k.

**Strengths:** exact names, acronyms, numbers, error codes and rare jargon.
**Weaknesses:** no understanding of synonyms or paraphrases; sensitive to punctuation in this setup; and it returns k results even when every score is 0 (no words in common at all).

## 2.10 Hybrid search and Reciprocal Rank Fusion (RRF)

**Why combine the two kinds of search:**

| Query or situation | Dense (embeddings) | Sparse (BM25) |
|---|:-:|:-:|
| Same idea, different words: "vehicle upkeep" vs "car maintenance" | ✅ | ❌ |
| Exact terms: "ResNet-50", "GDPR Article 17", "ERR_42" | ⚠️ can blur | ✅ |
| Rare jargon the model never saw in training | ⚠️ | ✅ |
| A long passage of natural language | ✅ | ⚠️ noisy |

Combining them gives you the strengths of both.

**The fusion problem.** FAISS returns distances (0 to 4, lower is better). BM25 returns unbounded scores (higher is better, on a scale that depends on the query and the corpus). Adding them together directly is meaningless, and normalizing and weighting them takes tuning.

**Reciprocal Rank Fusion** ignores the raw scores and uses only each result's **position** in each list:

```
RRF(d) = Σ over each ranked list r that contains d:   1 / (k + rank_r(d))        (ranks start at 1)
```

- **k = 60** comes from Cormack, Clarke & Büttcher (SIGIR 2009). It shrinks the gap between rank 1 and rank 2, so a result that several lists **agree** on counts for more than one list's single top pick.
- It needs no training and no score normalization, and it holds up well in practice.

**How Synapse implements it.** Several details in [`reciprocal_rank_fusion`](../backend/app/core/search.py#L89-L150) matter:
1. Each retriever returns up to **20** candidates. The next subsection explains where 20 comes from.
2. The fusion key is `(doc_name, section_title, page)`, which identifies a **section, not a chunk**. When several chunks from the same section appear, their contributions **add up**, so sections with several matching chunks get a boost.
3. For each key, the stored result is the **first one seen**. The dense list is processed first, so for a section found by both retrievers, `faiss_score` is filled in and `bm25_score` is null.
4. `dense_rank` records the first position in the dense list. `sparse_rank` is overwritten by the **last** position seen in the sparse list, which is a minor quirk.
5. Results are sorted by fused score, highest first.
6. If one retriever returns nothing, the other's list is returned unchanged, without an `rrf_score`.

**Worked example.**

Dense (FAISS) ranking:

| Rank | Chunk from section |
|---|---|
| 1 | **S1** = paper-A, "Transfer Learning" (p. 3) |
| 2 | **S2** = paper-B, "Fine-tuning" (p. 5) |
| 3 | **S1** (a different chunk of the same section) |
| 4 | **S3** = paper-C, "Domain Adaptation" (p. 2) |

Sparse (BM25) ranking:

| Rank | Chunk from section |
|---|---|
| 1 | **S3** |
| 2 | **S4** = paper-A, "Methodology" (p. 1) |
| 3 | **S1** |

Fused scores with k = 60:

| Section | Contributions | RRF score | Final rank |
|---|---|---|---|
| S1 | 1/61 + 1/63 (dense) + 1/63 (sparse) | 0.0164 + 0.0159 + 0.0159 = **0.0481** | 1 |
| S3 | 1/64 (dense) + 1/61 (sparse) | 0.0156 + 0.0164 = **0.0320** | 2 |
| S2 | 1/62 (dense) | **0.0161** | 3 |
| S4 | 1/62 (sparse) | **0.0161** | 4 (ties with S2; the stable sort keeps S2 first because it was seen first) |

What the example shows: S1 wins because two of its chunks matched on meaning *and* BM25 agreed. S3 moves above S2 because **both** retrievers found it.

**From the fused list to the 5 cards you see.** See [`search_with_pdf_links`](../backend/app/core/search.py#L295-L325) and [the route](../backend/app/api/routes.py#L90-L150):

```
TOP_K_SEARCH = 10
search_similar_chunks(query, 10 × 2 = 20)  → FAISS top 20 + BM25 top 20 → RRF → fused list
results[:10]                                → add pdf_available and pdf_url (/api/pdf/<file>)
dedupe by (doc_name, section_title)         → keep the entry with the highest rrf_score
sort by score, keep MAX_RESULTS = 5         → HTTP response
```

## 2.11 Retrieval-Augmented Generation (RAG)

**What it is.** A pattern for getting an LLM to answer from *your* data:
1. **Retrieve** relevant passages from a knowledge base.
2. **Augment** the prompt by adding those passages.
3. **Generate** the answer with the LLM.

**Why it's needed.** An LLM doesn't know your private PDFs, only knows things up to its training cutoff, and can **hallucinate**, meaning it confidently makes things up. Giving it real passages **grounds** its output. This is also cheaper and easier to keep current than fine-tuning a model on your documents.

**Synapse is a RAG system:**

| RAG step | In Synapse |
|---|---|
| Knowledge base | Your uploaded PDFs, as chunks in FAISS and BM25 |
| Retrieve | Hybrid search returns snippets from the top 5 sections |
| Augment | The snippets are numbered and inserted into the insights and podcast prompts |
| Generate | Gemini 2.5 Flash writes markdown insights or a podcast script |

The query is simply the selected text; there's no separate question. The frontend sends the 5 snippets back to the backend with the next request (as `related_snippets`), so `/insights` and `/podcast` don't search again.

**Where grounding is weak today:**
- The insights prompt explicitly invites the model to add *"your own knowledge"*.
- Snippets are sent **without document names or pages**, so the model can't cite its sources.
- Nothing checks whether each claim is actually supported by the snippets.

## 2.12 LLMs, prompts, Gemini and LangChain

**LLM (large language model).** A transformer trained to predict the next token on huge amounts of text, then tuned to follow instructions. The settings that matter here:
- **Context window:** how many tokens of prompt plus answer the model can handle at once.
- **Temperature:** how random the output is. 0 is the most predictable; higher values vary more. Synapse uses **0.5**, a middle setting.
- **System vs user messages:** the system message sets the role and rules; the user message carries the actual task.

**Gemini 2.5 Flash** is Google's fast, low-cost Gemini model. It's chosen with `GEMINI_MODEL` and accessed with an API key from Google AI Studio (`GOOGLE_API_KEY`). The 2.5 models "think" before answering by default. That improves quality but adds delay.

**LangChain** is a framework that puts one interface in front of many LLM providers, and adds chains, retrievers and agents. Synapse uses only its thinnest layer, in [chat_with_llm.py](../backend/app/scripts/chat_with_llm.py#L13-L74):

```python
llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key,
                             temperature=0.5, convert_system_message_to_human=True)
response = llm.invoke([HumanMessage(content=prompt)])   # a SystemMessage is added first if one is given
return response.content
```

- This function is the **single gateway** for every LLM call, and it rejects any `LLM_PROVIDER` other than `gemini`.
- `convert_system_message_to_human` merges a system message into the user's turn, for compatibility.
- A new client is created for every call, and the call is **synchronous**, so it blocks until Gemini answers.
- `langchain-openai` and `langchain-community` are installed but never imported. They're left over from the multi-provider sample code.

**Prompt engineering in Synapse.**

*The insights prompt* ([`generate_insights`](../backend/app/core/generation.py#L26-L83)):

| Technique | How the prompt uses it |
|---|---|
| Role prompting | "You are an expert document analyst…" |
| Clear delimiters | **SELECTED TEXT:** … and **RELATED CONTENT:** Snippet 1…N |
| Output template | Fixed markdown sections with placeholder bullets |
| Breaking the task into parts | Quick insights → key points → critical notes (contradictions, gaps, risks) → actionable takeaways → connections |
| Showing its basis | "Analysis based on: N related sections" |

It returns `{"insights_text": "<markdown>"}`. If there are no snippets, it returns a friendly message without calling the LLM at all. The "contradiction detection" feature **is** this instruction; no separate model detects contradictions.

*The podcast script prompt* ([`_generate_podcast_script`](../backend/app/core/generation.py#L139-L202)) asks for a conversational script in the first person: a warm greeting, an explanation, examples from the context, connections and takeaways. It targets 300–500 words (about 2–3 minutes spoken) with no special formatting, and includes up to 5 snippets labelled "Source N".

*Checking the output.* LLM output can't be trusted to follow instructions, so the code checks it:
- It strips markdown (`**`, `##`, `* `) so the TTS voice doesn't read symbols aloud.
- If the script is under 100 characters, it's replaced with a canned fallback script.
- If it's over 2000 characters, it's cut to 1800, ending at the last full stop when that full stop comes after character 1500.
- If any error occurs, the fallback script is used. The podcast still "works", but it's generic.

**Hallucination** is when the model states something its input doesn't support. Ways to reduce it: grounding with RAG, telling the model to say when something isn't in the documents, requiring citations, lowering the temperature, and verifying claims afterwards. Synapse does grounding and a structured format; the rest are possible improvements.

**Prompt injection** is when text inside a PDF tries to hijack the model, such as *"ignore previous instructions…"*. Synapse only displays the model's text and never lets it take actions, so the worst outcome is misleading output.

## 2.13 Text-to-speech and the podcast

**TTS (text-to-speech)** converts text into spoken audio. Modern neural TTS voices sound natural.

**Azure OpenAI TTS** is the default provider. It's OpenAI's `tts` model hosted in your own Azure OpenAI resource. In Azure you create a **deployment**, which is your named instance of a model, and then call it over REST. See [`_generate_azure_tts`](../backend/app/scripts/generate_audio.py#L52-L105):

```
POST {AZURE_TTS_ENDPOINT}/openai/deployments/{AZURE_TTS_DEPLOYMENT}/audio/speech?api-version={AZURE_TTS_API_VERSION}
Headers:  api-key: {AZURE_TTS_KEY}
          Content-Type: application/json
Body:     {"model": "tts", "input": "<script>", "voice": "nova"}
Response: 200 OK, and the body is the MP3 audio
```

- Available voices: alloy, echo, fable, onyx, nova, shimmer. An invalid voice falls back to alloy.
- The request times out after 30 seconds. The OpenAI TTS API accepts at most 4096 characters of input, which is another reason the script is capped at 2000.
- This is **not** the "Azure AI Speech" service. `azure-cognitiveservices-speech` is installed but never used.

**Choosing a provider** with `TTS_PROVIDER` ([`generate_audio`](../backend/app/scripts/generate_audio.py#L17-L50)):

| Value | Engine | Requires |
|---|---|---|
| `azure` | Azure OpenAI TTS over REST | `AZURE_TTS_KEY`, `AZURE_TTS_ENDPOINT`, plus deployment, API version and voice |
| `gcp` | Google Cloud Text-to-Speech, via REST with an API key or the client library with a service account | `GOOGLE_API_KEY` or `GOOGLE_APPLICATION_CREDENTIALS`; default voice `en-US-Neural2-F` |
| `local` | The `espeak-ng` command writes a WAV file, then `pydub` + `ffmpeg` convert it to MP3 | `espeak-ng` and `ffmpeg` installed; sounds robotic but is free and works offline |

In Docker, [entrypoint.sh](../entrypoint.sh#L48-L54) switches to `local` automatically when the Azure credentials are missing. This only takes effect if `TTS_PROVIDER` wasn't passed with `docker run -e`.

**pydub and ffmpeg.** pydub is a simple audio-editing library for loading, joining and exporting audio. It calls **ffmpeg** in the background to encode MP3.

**The podcast pipeline** ([`generate_podcast_audio`](../backend/app/core/generation.py#L86-L137)):

```
query + up to 5 snippets
 └─► Gemini writes a script (cleaned, length-capped; fallback script on failure)
      └─► generate_audio(script, "podcast_<uuid>.mp3", voice="nova")
           └─► check the file is larger than 1 KB
                └─► FileResponse(audio/mpeg), plus a background thread that deletes the file after 5 minutes
                     └─► browser: response.blob() → URL.createObjectURL(blob) → <audio controls>
```

Audio files are written to `<project root>/data/temp_audio/` by [`_ensure_temp_audio_dir`](../backend/app/core/generation.py#L224-L234). generation.py also creates a `backend/data/temp_audio/` folder, but nothing uses it.

**One narrator, not two speakers.** The README describes a conversation between two speakers. The code produces **one narrator** with `voice="nova"`, and its docstring says "single-narrator… simplified version for reliable hackathon demo". A two-speaker version would:
1. Prompt for a dialogue with speaker tags (`HOST:` / `GUEST:`).
2. Split the script into lines.
3. Synthesize each line with a different voice (for example `nova` and `onyx`).
4. Join the clips with pydub, adding short silences between them.
5. Export a single MP3.

## 2.14 Backend engineering concepts

**API, REST and JSON.** The frontend talks to the backend over HTTP. `GET` fetches data and `POST` sends it. Request and response bodies are JSON, except file uploads, which use a multipart body.

**FastAPI.** A Python web framework built on Starlette and Pydantic. You write endpoint functions with type hints, and FastAPI validates the input, converts the output to JSON and generates interactive OpenAPI documentation at `/docs`.

**Pydantic models** ([routes.py](../backend/app/api/routes.py#L39-L60)) define the data shapes:
- `QueryRequest {query_text: str}` is the body for `/related-sections`.
- `InsightsRequest {query_text: str, related_snippets: List[str]}` is the body for `/insights` and `/podcast`.
- `RelatedSection {doc_name, section_title, page, snippet, rrf_score?, faiss_score?, bm25_score?, dense_rank?, sparse_rank?, pdf_available, pdf_url?}` is the response model. A request with the wrong shape is rejected automatically with HTTP 422.

**ASGI and Uvicorn.** ASGI is the standard interface between asynchronous Python web apps and web servers. **Uvicorn** is the ASGI server: it listens on the port and runs an **event loop**. By default it runs **one worker process**, which matters because the search index lives in that one process's memory.

**`async def` vs `def`: the event-loop rule.**
- An `async def` endpoint runs **on the event loop**. If it calls something slow that blocks (heavy CPU work, `requests`, a synchronous SDK), the whole server waits until it finishes.
- A plain `def` endpoint is run by FastAPI in a **thread pool**, which keeps the event loop free.
- `run_in_threadpool(func, ...)` lets an `async` endpoint hand blocking work to the thread pool.

In Synapse:
- `/podcast` correctly uses `run_in_threadpool`.
- `/insights` makes the blocking Gemini call directly inside `async def`.
- `/related-sections` runs the embedding and BM25 scoring directly.

The last two block the event loop while they run, which is a known area to improve.

**BackgroundTasks.** Work scheduled to run **after** the response has been sent. [`/ingest`](../backend/app/api/routes.py#L62-L88) saves the files, schedules `process_and_index_pdf` for each one and returns immediately. Starlette runs synchronous task functions in the thread pool, **one after another** for a given request. There's no job status, no retry and no persistence, so if the server stops partway through, the remaining work is lost.

**Global in-memory state.** `MODEL`, `INDEX`, `BM25_INDEX`, `TOKENIZED_CORPUS` and `METADATA` are module-level globals loaded at startup, so queries never touch the disk. The downside: with several Uvicorn workers or several containers, each would have its own copy, and the copies would drift apart after uploads.

**Thread safety.** Ingestion tasks run in threads. [`add_chunks_to_index`](../backend/app/core/search.py#L252-L276) therefore wraps the whole update in a `threading.Lock`: append to FAISS, the metadata and the BM25 corpus, rebuild BM25, and write all 3 files. Searches don't take the lock, so there's a tiny window where a search can see a vector whose metadata hasn't been appended yet.

**Configuration** ([config.py](../backend/app/core/config.py)):
- `Settings(BaseSettings)` from **pydantic-settings**. Each field can be overridden by an environment variable or by the `.env` file in the **current working directory**; otherwise it uses its default.
- `@lru_cache` on `get_settings()` means the settings object is created once and shared everywhere (a simple singleton).
- **python-dotenv**'s `load_dotenv()`, called in main.py and generate_audio.py, copies `.env` into `os.environ` for code that uses `os.getenv` (the LLM and TTS keys). It searches upward from the file that calls it, and by default it never overwrites a variable that's already set.

**CORS (cross-origin resource sharing).** Browsers stop a page from reading responses from a different **origin** (scheme + host + port) unless the server allows it. In development the page runs on `localhost:8080` and the API on `localhost:8000`, which are different origins, so the backend adds `CORSMiddleware(allow_origins=["*"], …)`. In Docker both are served from `localhost:8080`, so CORS isn't needed there. `"*"` is convenient, but it lets **any** website open in your browser call the API.

**Startup hook.** `@app.on_event("startup")` runs `load_search_engine()` before the server accepts any request. Newer FastAPI versions prefer a "lifespan" function; `on_event` still works but logs a deprecation warning.

**Serving the React app with an SPA fallback** ([main.py](../backend/main.py#L49-L87)). If `frontend/dist` (or `backend/static`, or `frontend/build`) exists under the working directory, main.py registers a catch-all `GET /{path}` route **after** the API routes. It handles requests like this:
- Paths starting with `api/` get a 404, since real API routes have already matched earlier.
- Paths containing a dot are served as files from `dist` (JavaScript, CSS, images).
- Everything else (`/`, `/reader`, `/history`) gets `index.html`, and React Router shows the right page in the browser.

`/docs`, `/redoc` and `/openapi.json` still work because FastAPI registered them first.

**Input validation and path traversal.** A path traversal attack uses `..` in a file name to reach files outside the intended folder. [`GET /api/pdf/{filename}`](../backend/app/api/routes.py#L152-L184) rejects names containing `..`, `/` or `\`, so a request for `../../.env` fails. The SPA catch-all route and the upload file name **don't** have this protection (see Part 5).

**Logging.** Standard Python `logging` at INFO level. Docker sets `PYTHONUNBUFFERED=1` so log lines appear in `docker logs` immediately.

## 2.15 Frontend concepts

**SPA (single-page application).** The browser loads one HTML page and a JavaScript bundle once. Moving between "pages" happens in JavaScript, without reloading.

**React.** The UI is built from **components** (functions that return JSX) and **state**. Synapse uses these hooks:

| Hook | What Synapse uses it for |
|---|---|
| `useState` | Selected text, related sections, insights, podcast URL, loading and error flags |
| `useEffect` | Loading the Adobe SDK; setting up the viewer again when the file or target page changes; cleaning up on unmount |
| `useCallback` | Keeping handler functions stable when passed to children (`onTextSelection`, `onSectionClick`) |
| `useRef` | Holding the Adobe view and API objects and the AbortControllers without causing re-renders |

**TypeScript.** JavaScript with types, such as `RelatedSection` and `Insights`, plus typings for the Adobe SDK in `types/adobe.d.ts`. Strict mode is turned off in this project.

**Vite.**
- **Dev server** (`npm run dev`) with hot module replacement, so edits show up instantly. [vite.config.ts](../frontend/vite.config.ts) sets it to **port 8080** and all network interfaces (`host: "::"`).
- **Production build** (`npm run build`) bundles and minifies the app into `frontend/dist`, with a content hash in each file name.
- **Environment variables.** Only variables starting with `VITE_` reach browser code, through `import.meta.env.VITE_*`, and they're **replaced with literal text at build time**. `envDir: "../"` makes Vite read the `.env` in the project root. As a result, changing `VITE_ADOBE_CLIENT_ID` or `VITE_API_URL` requires restarting the dev server or rebuilding (for Docker, rebuilding the image).

**React Router.** The routes are `/` (HomePage), `/reader` (ReaderView), `/history` (HistoryPage), and `*` (NotFound). "Upload PDF to Read" passes the chosen `File` object in the navigation state: `navigate('/reader', { state: { uploadedFile } })`. The file stays in browser memory. It is **not** uploaded or indexed.

**UI toolkit.** Tailwind CSS provides utility classes. shadcn/ui provides components (accordion, dropdown, dialog and so on) that are copied into the project and built on Radix UI. Icons come from lucide-react. The project started from a Vite + React + shadcn template, which explains why `components/ui/` contains about 50 components and why some files are unused: `pages/Index.tsx`, `ModalPrompt.tsx`, `AdobeTest.tsx` and `hooks/useAdobeViewSDK.ts`. `@tanstack/react-query` has its provider set up, but data is fetched with plain `fetch`.

**Adobe PDF Embed API** ([AdobePDFViewer.tsx](../frontend/src/components/AdobePDFViewer.tsx)). A free JavaScript SDK from Adobe that renders PDFs with Acrobat quality inside a `<div>`. The viewer uses it in six steps:
1. **Load the SDK.** Insert `<script src="https://acrobatservices.adobe.com/view-sdk/viewer.js">` and wait for the `adobe_dc_view_sdk.ready` event.
2. **Create a view.** `new AdobeDC.View({ clientId, divId: "adobe-dc-view" })`. The client ID comes from `VITE_ADOBE_CLIENT_ID` and only works on the **domain it was registered for**, such as `localhost`.
3. **Listen for selections.** `registerCallback(CallbackType.EVENT_LISTENER, handler, { listenOn: [FilePreviewEvents.PREVIEW_SELECTION_END], enableFilePreviewEvents: true })`. This is registered **before** the file is shown.
4. **Show the file.** `previewFile({ content: { promise: Promise.resolve(arrayBuffer) }, metaData: { fileName } }, { embedMode: "SIZED_CONTAINER", defaultViewMode: "FIT_WIDTH" })`. The PDF's bytes come from the in-memory `File`, not from a URL. The embed modes are FULL_WINDOW (the default), SIZED_CONTAINER (fits inside a box; used here), IN_LINE (scrolls with the page) and LIGHTBOX (an overlay).
5. **Get the APIs.** `adobeViewer.getAPIs()` gives `apis.getSelectedContent()`, which returns `{ type: "text", data: "…" }`, and `apis.gotoLocation(pageNumber)`, which jumps to a page. Page numbers here are **1-based**: the first page is 1.
6. When a selection ends, the handler waits 50 ms, reads the selected text and calls `onTextSelection(text)`.

**Running the analysis** ([`startAnalysisFlow`](../frontend/src/pages/ReaderView.tsx#L71-L199) in ReaderView.tsx). When the selected text is longer than 10 characters:

```
cancel any previous requests → open the sidebar and clear old results
→ POST /api/related-sections {query_text}                     → show the cards
→ POST /api/insights  {query_text, related_snippets}          → show the insights
→ POST /api/podcast   {query_text, related_snippets}  → blob → object URL → audio player
```

The three steps run **strictly in order**. If insights fail, the podcast is never requested.

**AbortController.** A browser API that cancels a `fetch` in progress. Synapse keeps one per request in a `useRef`. A new selection, closing the sidebar or leaving the page calls `abort()`. This only cancels the **browser's** side: the backend keeps generating, and keeps paying for, the LLM or TTS call.

**Files, Blobs and object URLs.**
- `File` and `Blob` hold binary data in the browser.
- `file.arrayBuffer()` gives the raw bytes, which are passed to Adobe.
- `response.blob()` gives the audio or PDF bytes from a response.
- `URL.createObjectURL(blob)` creates a temporary `blob:` URL that can go in `<audio src>`, and `URL.revokeObjectURL` releases it.

**FormData and multipart uploads.** HomePage adds every selected file under the field name `files` and POSTs them to `/api/ingest`. This matches `files: List[UploadFile]` in FastAPI, which needs the `python-multipart` package.

**Click-to-navigate** ([`handleSectionClick`](../frontend/src/pages/ReaderView.tsx#L209-L231)):
1. Fetch `/api/pdf/<doc_name>` and turn the blob into a `new File(...)`.
2. Make it the current file.
3. `key={currentDocName}` on `<PDFViewer>` forces a fresh viewer.
4. After `getAPIs()`, call `gotoLocation(targetPage)` if `targetPage > 0`.

**Content-Security-Policy (CSP)** ([index.html](../frontend/index.html#L15-L25)). A browser allow-list of where scripts, frames, workers, fonts, images, media and network requests may come from. Synapse allows `'self'`, `*.adobe.com`, `*.adobe.io` and `http://localhost:*`, plus `blob:` and `data:` where the viewer and audio need them. Anything else, such as calling an API on a different host, is blocked by the browser.

**Mock UI.** The History page, the Library sidebar and the Library dropdown show **hardcoded sample data**. They're design placeholders and aren't connected to the backend.

## 2.16 DevOps concepts: Docker and WSL

**Container vs virtual machine.** A virtual machine emulates a whole computer, including its own operating-system kernel. A container is an isolated group of processes that shares the host's Linux kernel, so it's lighter and starts faster.

**Image, layer and container.** An **image** is a read-only template built from a Dockerfile. Each instruction (`RUN`, `COPY`, …) adds a **layer**. A **container** is a running instance of an image, with a thin writable layer on top that's deleted along with the container.

**Build context and .dockerignore.** `docker build .` sends the whole folder to the builder. `.dockerignore` excludes things like `node_modules`, `.venv`, `.git`, uploads and `*.md`, which keeps builds fast and images clean.

**Layer caching.** If an instruction and its inputs haven't changed, Docker reuses the cached layer instead of running it again. That's why the Dockerfile copies `package*.json` **before** the rest of the source: the dependency install is reused when only code changes. It's also why Python packages are installed in separate `RUN` groups.

**Multi-stage builds.** One Dockerfile can have several `FROM` stages, and later stages copy only the outputs they need (`COPY --from=…`). In Synapse:
1. A **Node stage** builds the frontend.
2. A **Python builder stage** installs packages, with compilers available.
3. A slim **runtime stage** receives only the installed packages, the built `dist/` folder and the source code.

The compilers, Node and download caches are all left behind.

**CPU-only PyTorch.** On Linux, `pip install torch` from PyPI installs the CUDA (NVIDIA GPU) build, which pulls in several GB of GPU libraries. Installing first from `https://download.pytorch.org/whl/cpu` gets a much smaller CPU build. With today's package versions, pip replaces the Dockerfile's pinned `torch==2.1.2` and undoes this saving. [RUNBOOK §7.9](RUNBOOK.md#79-known-issue-the-cpu-only-torch-pin-no-longer-holds) explains the problem and the fix.

**Non-root user.** `useradd app` followed by `USER app` means that if the app were compromised, the attacker wouldn't be root inside the container.

**HEALTHCHECK.** Docker regularly runs `curl -f http://localhost:8080/api/health`. The result shows as `healthy` or `unhealthy` in `docker ps`, and orchestration tools can restart unhealthy containers.

**ENTRYPOINT and exec.** `ENTRYPOINT ["/app/entrypoint.sh"]` runs a startup script. Its last line, `exec uvicorn …`, **replaces** the shell process with Uvicorn. Uvicorn becomes process ID 1, so it receives the SIGTERM signal from `docker stop` and can shut down cleanly.

**Build-time vs run-time configuration.** `VITE_*` values are compiled into the JavaScript during `docker build`. Backend values are read when the container starts. Any secret baked in at build time ends up **inside the image**, where anyone who has the image can read it.

**Ports.** `EXPOSE 8080` only documents the port. `docker run -p 8080:8080` actually publishes it (host port : container port). Uvicorn listens on `0.0.0.0` so connections from outside the container reach it.

**Volumes.** Data written inside a container disappears when the container is removed. A named volume (`-v synapse-data:/app/backend/data`) keeps uploads and index files when the container is recreated.

**`--platform linux/amd64`.** Forces an x86-64 image. You need this when building on an ARM machine (such as Apple Silicon) for an x86 server.

**WSL2 (Windows Subsystem for Linux).** Runs a real Linux kernel inside a lightweight virtual machine that's integrated with Windows.
- A Linux server listening on `localhost:PORT` can be opened from a Windows browser at `http://localhost:PORT`.
- Files in the Linux filesystem (`~/…`) are fast. Files under `/mnt/c/…` (the Windows drive) are slow and can have Windows line-ending (CRLF) problems.
- Docker Desktop's WSL2 backend also runs the Docker engine inside WSL.

---

# Part 3: End-to-end flows

## 3.1 Boot: starting the backend

```
uvicorn backend.main:app          (working directory = project root)
│
├─ import backend.main
│   ├─ import app.api.routes
│   │   ├─ get_settings()  → reads ./.env; creates backend/data/uploads
│   │   ├─ import core.processing → NLTK checks for punkt (crashes if missing)
│   │   │     └─ import core.pdf_parser_1a  (PyMuPDF, joblib, pandas, pytesseract)
│   │   ├─ import core.search → faiss, sentence_transformers, rank_bm25 (globals still empty)
│   │   └─ import core.generation → creates backend/data/temp_audio
│   │         ├─ import scripts.chat_with_llm   (LangChain Gemini)
│   │         └─ import scripts.generate_audio  → load_dotenv()
│   ├─ load_dotenv(); configure logging; create FastAPI app; add CORS "*"
│   ├─ include router under /api
│   └─ does frontend/dist exist? → register the SPA catch-all route
│
└─ startup event → load_search_engine()
    ├─ SentenceTransformer("all-MiniLM-L6-v2")      (downloads on first run)
    ├─ index.faiss and metadata.json exist? → load both; if metadata_bm25.json exists → BM25Okapi(corpus)
    └─ otherwise → empty IndexFlatL2(384) and empty lists
→ "Application startup complete" → requests are accepted
```

## 3.2 Ingestion: "Add PDFs to Library"

```
Browser (HomePage)
  │  POST /api/ingest   multipart: files=<pdf1>, files=<pdf2>, …
  ▼
routes.ingest_documents
  │  for each file: is it a .pdf? (if not → 400 and stop)
  │                 save to backend/data/uploads/<filename>
  │                 background_tasks.add_task(process_and_index_pdf, …)
  │  return 200 {"message": "Processing started in background for N documents.", …}
  ▼
Browser shows the message                      (the response has been sent)
                                                    │
Thread pool: process_and_index_pdf(pdf) ◄───────────┘   one file after another
  ├─ extract_structure_from_pdf → text blocks → headings → sections
  ├─ for each section with ≥ 5 words: chunk_text(size 5, overlap 1) + metadata
  └─ add_chunks_to_index(chunks, metadatas)
       ├─ MODEL.encode(chunks)  → (n, 384) float32
       ├─ tokenize each chunk for BM25
       └─ with index_lock:
            INDEX.add → METADATA.extend → TOKENIZED_CORPUS.extend → rebuild BM25
            → write index.faiss, metadata.json, metadata_bm25.json
  log: "Successfully indexed N chunks from <file>"
```

Notes:
- The UI never learns when indexing has finished. Watch the server logs.
- If one file in the batch isn't a PDF, the request returns 400 and **all** of that batch's background tasks are dropped. Files saved before the bad one stay on disk, unindexed.
- Errors during processing are logged but never shown in the UI.

## 3.3 Selecting text: related sections

```
Adobe viewer ─ PREVIEW_SELECTION_END ─► getSelectedContent() ─► "selected text"  (must be > 10 characters)
ReaderView.startAnalysisFlow
  └─ POST /api/related-sections  {"query_text": "..."}
       routes.get_related_sections
         └─ search_with_pdf_links(query, top_k = 10)
              └─ search_similar_chunks(query, 20)
                   ├─ search_faiss: encode query → INDEX.search(20) → METADATA[id] + faiss_score
                   ├─ search_bm25:  lower().split() → get_scores → top 20 by argsort → METADATA[i] + bm25_score
                   └─ reciprocal_rank_fusion  (section-level keys, k = 60)
              └─ first 10 → pdf_available, pdf_url = "/api/pdf/<doc>"
         └─ dedupe by (doc_name, section_title) → sort by rrf_score → first 5 → List[RelatedSection]
  ◄─ JSON → "Related Content" cards in the sidebar  (document, "Page N • section", snippet)
```

Speed: most of the time goes on embedding the query on the CPU and scoring every chunk with BM25. There are no network calls, so it's fast for a personal library. If the PDF you're reading is also in the library, its own section will usually be the top match.

## 3.4 Insights

```
ReaderView ─ POST /api/insights  {"query_text": "...", "related_snippets": [up to 5 snippets]}
routes.get_insights → generate_insights
  ├─ no snippets → {"insights_text": "Not enough related content…"}   (Gemini is not called)
  └─ build the prompt (role + selected text + numbered snippets + markdown template)
     → chat_with_llm → ChatGoogleGenerativeAI(gemini-2.5-flash, temperature 0.5).invoke
     → {"insights_text": "<markdown>"}
◄─ the "AI Insights" section shows the text as-is (markdown symbols stay visible)
On error → HTTP 500 "Failed to generate insights" → the UI shows "Analysis Failed" and the flow stops
```

## 3.5 Podcast

```
ReaderView ─ POST /api/podcast  {"query_text": "...", "related_snippets": [...]}
routes.get_podcast → run_in_threadpool(generate_podcast_audio)
  ├─ _generate_podcast_script → Gemini → clean up + cap length   (fallback script on failure)
  ├─ generate_audio(script, data/temp_audio/podcast_<uuid>.mp3, voice="nova")
  │     └─ TTS_PROVIDER: azure (REST) | gcp | local (espeak-ng → ffmpeg)
  ├─ does the file exist, and is it larger than 1 KB?
  └─ FileResponse(audio/mpeg) + background thread: sleep 300 s, then delete the file
◄─ blob → URL.createObjectURL → <audio controls>
If the error message mentions "Azure" or "TTS" → HTTP 503 → UI: "Text-to-speech service is currently unavailable…"
```

## 3.6 Clicking a related section

```
click a card → handleSectionClick(section)
  ├─ pdf_available is false → error "PDF not available for this section."
  └─ GET /api/pdf/<doc_name>   (file name checked for .., / and \)  → PDF bytes
     → new File → setUploadedFile, setCurrentDocName, setTargetPage(section.page)
     → <PDFViewer key={docName}> mounts again → previewFile(new bytes)
     → getAPIs() → if targetPage > 0: gotoLocation(targetPage)
```

**Page-number mismatch.** The backend's page numbers start at 0; Adobe's start at 1. So the jump lands **one page before** the section. Sections on the first page (page 0) don't jump at all, and the card also shows the 0-based number. The fix is to use `page + 1`.

## 3.7 Docker build and boot, in brief

- **Build:** the Node stage runs `vite build` with `.env` → the Python builder stage runs the pip installs → the runtime image gets the system tools, installed packages, backend code, `dist`, `.env` and entrypoint, plus a non-root user and a health check.
- **Boot:** the entrypoint merges environment variables and writes `/app/.env` → falls back to local TTS if needed → runs `exec uvicorn backend.main:app --port 8080`. From there it's the same boot as §3.1, except that `frontend/dist` exists, so the React app is served on the same port.

For the full walkthrough, see [RUNBOOK §7](RUNBOOK.md#7-how-the-build-and-deployment-work).

---

# Part 4: Reference

## 4.1 Data on disk

| Path (relative to project root, or to `/app` in Docker) | Format | Contents |
|---|---|---|
| `backend/data/uploads/<file>.pdf` | PDF | The original uploads |
| `backend/data/index.faiss` | FAISS binary | N vectors × 384 float32 numbers |
| `backend/data/metadata.json` | JSON list | N chunk objects (see §2.4) |
| `backend/data/metadata_bm25.json` | JSON `{"tokenized_corpus": [[...], ...]}` | N word lists |
| `data/temp_audio/podcast_<uuid>.mp3` | MP3 | Temporary podcast, deleted about 5 minutes after it's served |
| `~/.cache/huggingface/` | Model files | all-MiniLM-L6-v2 |

Row *i* refers to the same chunk in all three index files.

To inspect the index from the project root, with the virtual environment active:

```bash
python - <<'EOF'
import faiss, json
idx  = faiss.read_index("backend/data/index.faiss")
meta = json.load(open("backend/data/metadata.json"))
bm25 = json.load(open("backend/data/metadata_bm25.json"))["tokenized_corpus"]
print("vectors:", idx.ntotal, "dim:", idx.d, "| metadata:", len(meta), "| bm25 docs:", len(bm25))
print("documents:", sorted({m["doc_name"] for m in meta}))
print(meta[0])
EOF
```

## 4.2 API at a glance

| Method and path | Request | Response |
|---|---|---|
| `GET /api/health` | none | `{"status": "healthy", "service": "Project Synapse API", "version": "1.0.0"}` |
| `POST /api/ingest` | multipart, field `files` (one or more PDFs) | `{"message", "filenames", "note"}` |
| `POST /api/related-sections` | `{"query_text"}` | Up to 5 `RelatedSection` objects |
| `GET /api/pdf/{filename}` | none | The PDF bytes |
| `POST /api/insights` | `{"query_text", "related_snippets": [...]}` | `{"insights_text": "<markdown>"}` |
| `POST /api/podcast` | `{"query_text", "related_snippets": [...]}` | `audio/mpeg` |

For full examples with curl, see [RUNBOOK §9](RUNBOOK.md#9-api-reference).

## 4.3 Settings you can tune

| Name | Where it's set | Default | What it controls | Re-index needed? |
|---|---|---|---|---|
| `EMBEDDING_MODEL_NAME` | config.py or env | `all-MiniLM-L6-v2` | The embedding model | **Yes**; a different dimension makes the old index unusable |
| `CHUNK_SIZE` | config.py or env | 5 | Sentences per chunk | **Yes** |
| `CHUNK_OVERLAP` | config.py or env | 1 | Sentences shared by neighbouring chunks | **Yes** |
| `TOP_K_SEARCH` | config.py or env | 10 | Results kept after fusion; each retriever fetches twice this many | No, just restart |
| `MAX_RESULTS` | config.py or env | 5 | Number of cards returned | No |
| `FAISS_INDEX_PATH`, `METADATA_PATH`, `UPLOAD_DIR` | config.py or env | `backend/data/...` | Storage locations, relative to the working directory | n/a |
| `RRF_K` | constant in search.py | 60 | How strongly fusion smooths rank differences | No |
| temperature | chat_with_llm.py | 0.5 | LLM randomness | No |
| `GEMINI_MODEL` | env | Code default is `gemini-1.5-flash`, so **always set it** | Which LLM | No |
| `TTS_PROVIDER` | env | `local` in generate_audio.py; `azure` in the Docker entrypoint | Which TTS engine | No |
| Podcast voice | generation.py | `"nova"` | Azure voice | No |
| Script length limits | generation.py | 100 / 1800–2000 characters | Audio length | No |
| Audio cleanup delay | routes.py | 300 s | How long temporary files last | No |
| Minimum selection length | ReaderView.tsx | more than 10 characters | When analysis starts | No |

Re-indexing means stopping the backend, deleting the three index files, and uploading the PDFs again. See [RUNBOOK §5.8](RUNBOOK.md#58-reset-the-library).

## 4.4 Glossary (A–Z)

| Term | Meaning | In Synapse |
|---|---|---|
| AbortController | Browser API for cancelling a `fetch` in progress | Cancels old analysis requests |
| Adobe PDF Embed API | Adobe's JavaScript SDK for showing PDFs in a web page, with events and APIs | Viewer, text selection, `gotoLocation` |
| ANN | Approximate nearest neighbour: fast vector search that may miss a few true neighbours | Not used; the flat index is exact |
| API key | Secret string that identifies you to a paid API | `GOOGLE_API_KEY`, `AZURE_TTS_KEY` |
| ASGI | Standard interface between async Python apps and web servers | FastAPI running on Uvicorn |
| BackgroundTasks | FastAPI feature that runs work after the response is sent | Indexing uploaded PDFs |
| Bag of words | Text represented as word counts, ignoring order | The basis of BM25 |
| BERT | Encoder-only transformer pretrained by masking words | MiniLM belongs to this family |
| bbox | Bounding box (x0, y0, x1, y1) of a text block on a page | Orders blocks when building sections |
| Bi-encoder | Encodes query and documents separately into vectors | How sentence-transformers works |
| Blob / object URL | Binary data in the browser, and a temporary URL pointing to it | Podcast audio, fetched PDFs |
| BM25 / BM25Okapi | Keyword ranking formula with term saturation and length normalization | `rank_bm25.BM25Okapi`, k1 = 1.5, b = 0.75 |
| Build context | Files sent to Docker when building | Filtered by `.dockerignore` |
| Chunk / chunking | A small piece of a document, and the act of splitting into pieces | 5 sentences per chunk |
| Chunk overlap | Sentences shared by neighbouring chunks | 1 |
| Client ID (Adobe) | Public, domain-restricted credential for the Embed API | `VITE_ADOBE_CLIENT_ID` |
| Container / image / layer | Running instance / read-only template / one build step | Docker deployment |
| Context window | How many tokens an LLM can take in at once | Gemini's is very large |
| CORS | Browser rule controlling requests to other origins | `allow_origins=["*"]` |
| Cosine similarity | Similarity based on the angle between vectors | Same ranking as L2 for unit vectors |
| CPU-only PyTorch | PyTorch build without GPU libraries | Installed from download.pytorch.org/whl/cpu |
| Cross-encoder | Model that scores a (query, document) pair together; used for re-ranking | Not used (an improvement idea) |
| CSP | Content-Security-Policy: browser allow-list of content sources | Meta tag in `index.html` |
| Dense retrieval | Search using embeddings | FAISS + MiniLM |
| Deployment (Azure OpenAI) | Your named instance of a model inside an Azure resource | `AZURE_TTS_DEPLOYMENT=tts` |
| Distillation | Training a small model to imitate a larger one | How MiniLM was made |
| Embedding | Vector of numbers representing meaning | 384 dimensions |
| Entrypoint | Script a container runs at start | `entrypoint.sh` → `exec uvicorn` |
| espeak-ng | Free, offline, robotic-sounding TTS engine | `TTS_PROVIDER=local` |
| Event loop | Scheduler that runs async code in one thread | Uvicorn/FastAPI; must not be blocked |
| FAISS | Meta's library for vector similarity search | `IndexFlatL2(384)` |
| FastAPI | Python web framework with type-based validation | The backend |
| ffmpeg | Audio and video conversion tool | Used by pydub for WAV → MP3 |
| Flat index | Exact, brute-force vector index | `IndexFlatL2` |
| Gemini | Google's family of LLMs | 2.5 Flash for insights and scripts |
| Grounding | Basing LLM output on supplied source text | The RAG snippets |
| Hallucination | An LLM stating things its input doesn't support | Reduced (not eliminated) by RAG |
| HEALTHCHECK | Docker's periodic container health probe | `curl /api/health` every 30 s |
| HMR | Hot module replacement: live code updates in the dev server | Vite dev server |
| HNSW | Graph-based ANN index | Not used |
| Hugging Face Hub | Online repository of models | Where MiniLM is downloaded from |
| Hybrid search | Combining dense and sparse retrieval | FAISS + BM25 + RRF |
| IDF | Inverse document frequency: rare words weigh more | Part of BM25 |
| Ingestion | Turning uploaded files into searchable indexes | `process_and_index_pdf` |
| IVF | Cluster-based ANN index | Not used |
| joblib | Library for saving and loading Python objects | Old LightGBM model files |
| L2 distance | Straight-line (Euclidean) distance between vectors | FAISS `faiss_score` (squared) |
| LangChain | Framework offering one interface to many LLM providers | `ChatGoogleGenerativeAI` |
| LightGBM | Gradient-boosted decision tree library | Round 1A heading classifier (no longer used) |
| LLM | Large language model | Gemini |
| Mean pooling | Averaging token vectors into one sentence vector | Inside MiniLM |
| Metadata | Information stored alongside each vector | `metadata.json` |
| MiniLM | Small distilled transformer | `all-MiniLM-L6-v2` |
| Multipart/form-data | HTTP body format for uploading files | `/api/ingest` |
| Nearest-neighbour search | Finding the vectors closest to a query | `INDEX.search` |
| NLTK / Punkt | NLP toolkit, and its sentence-splitting model | Chunking |
| Normalization (L2) | Scaling a vector to length 1 | Last layer of MiniLM |
| OCR | Converting images of text into text | Installed, not used |
| Outline | Ordered list of a document's headings and sections | Parser output |
| PQ | Product quantization: compressing vectors | Not used |
| Prompt / prompt engineering | The instructions sent to an LLM, and the craft of designing them | Insights and podcast prompts |
| Prompt injection | Text that tries to override a model's instructions | Possible through PDF content; low impact |
| PyMuPDF (fitz) | Library for PDF parsing and rendering | Extracts text blocks, fonts and positions |
| Pydantic / pydantic-settings | Data validation / settings loaded from the environment | Request models / `Settings` |
| pydub | Simple audio-editing library | WAV → MP3 for local TTS |
| RAG | Retrieval-Augmented Generation | Search, then Gemini |
| React Router | Client-side routing for React | `/`, `/reader`, `/history` |
| Recall@k / MRR / nDCG | Metrics for evaluating search quality | Not measured (an improvement idea) |
| Re-ranking | A second, more accurate scoring pass over the top results | Not used |
| RRF | Reciprocal Rank Fusion: merging ranked lists by position | k = 60, section-level |
| Section | A heading plus the body text under it | The unit results point to |
| Self-attention | Transformer operation in which every token looks at every other token | Inside MiniLM |
| Semantic search | Search by meaning rather than exact words | The FAISS side |
| Sentence-BERT / sentence-transformers | Method, and library, for sentence embeddings | Loads MiniLM |
| SPA | Single-page application | The React frontend |
| Sparse retrieval | Search by word matching | BM25 |
| Temperature | LLM randomness setting | 0.5 |
| Thread pool / run_in_threadpool | Worker threads that keep blocking work off the event loop | `/podcast`, background tasks |
| Token / tokenization | Unit of text, and the act of splitting text into those units | Four different kinds (see §2.3) |
| Top-k | The k best results | 20 per retriever → 10 → 5 |
| Transformer | Neural network architecture based on attention | MiniLM, Gemini |
| TTS | Text-to-speech | Azure OpenAI `tts` |
| Uvicorn | ASGI web server | Runs FastAPI |
| Vector | Ordered list of numbers | An embedding |
| Vector database | Service for storing and searching vectors with metadata | Not used; FAISS + JSON instead |
| Vite | Frontend dev server and build tool | Port 8080; `VITE_*` variables |
| Volume (Docker) | Storage that persists beyond a container's life | `synapse-data` |
| WordPiece | Subword tokenizer used by BERT-family models | MiniLM's tokenizer |
| WSL2 | Windows Subsystem for Linux, version 2 | Your Linux environment |

---

# Part 5: Reality check

## 5.1 What the README says vs what the code does

| README says | What the code actually does |
|---|---|
| "2-speaker podcast conversations" | One narrator, one voice (`nova`) |
| "Azure Cognitive Services" TTS | Azure **OpenAI** `tts` model over REST |
| "Smart parsing (from Round 1A)" | A bold-font heuristic; the LightGBM model files are never loaded |
| "Hybrid search combines semantic similarity with keyword matching" | ✅ Accurate: FAISS + BM25 + RRF |
| "Contradiction detection" | An instruction inside the insights prompt; no dedicated model |
| "Query response < 500 ms", "~100 documents/minute" | Not measured anywhere in the repo |
| "82% faster builds / 75% smaller image" | Measured at hackathon time. Today, unpinned dependencies override the CPU-only torch pin ([RUNBOOK §7.9](RUNBOOK.md#79-known-issue-the-cpu-only-torch-pin-no-longer-holds)) |
| "Bulk upload with real-time progress" | The upload returns immediately; there's no progress or status for indexing |
| "Health checks", "graceful degradation" | ✅ Health endpoint and Docker HEALTHCHECK exist; TTS falls back to local in Docker; the podcast script falls back to canned text |
| `GOOGLE_APPLICATION_CREDENTIALS` for Gemini | The LLM code only accepts `GOOGLE_API_KEY` |
| Dev URL `http://localhost:5173` | Vite runs on port **8080** |
| History and library panels | Mock data |
| "Security best practices" | ✅ Non-root user and settings in environment variables. ❌ But keys are baked into the image, CORS allows `*`, there's no authentication, and there are path traversal risks |

## 5.2 Known limitations and bugs, with fixes

**Parsing and indexing**
1. Heading detection requires "Bold" in the font name, so PDFs without it produce **0 chunks**. *Fix:* also check the span's bold flag, font size relative to the median, and numbering patterns; fall back to page-level chunks when no headings are found.
2. There's no OCR path, so scanned PDFs can't be searched. *Fix:* bring back Round 1A's `is_scanned_page` check plus Tesseract.
3. Text before the first heading is dropped. *Fix:* add an implicit "Introduction" section.
4. Uploading the same file again duplicates its chunks. *Fix:* hash the file contents and skip or replace duplicates.
5. `page` is the heading's page and is 0-based. *Fix:* store each chunk's own page, and add 1 before showing or navigating.
6. BM25 is rebuilt and all three files are rewritten after every PDF, and the writes aren't atomic. *Fix:* batch the work, write to a temporary file and rename it, or use a proper search engine or vector database.
7. The NLTK punkt check catches the wrong exception, so a missing `punkt` crashes startup. *Fix:* use `except LookupError:` and download the data.
8. One non-PDF in a batch cancels indexing for the **whole** batch, although earlier files stay on disk. *Fix:* validate every file before saving any.

**Retrieval**

9. The BM25 tokenizer doesn't strip punctuation and doesn't stem words. *Fix:* use regex tokenization, stemming and stop-word removal.
10. BM25 returns chunks with a score of 0, which adds noise to fusion. *Fix:* keep only results with `score > 0`.
11. The section you're reading comes back as a match for itself. *Fix:* send the current document and page, and filter them out.
12. There's no re-ranking. *Fix:* run a cross-encoder (for example `cross-encoder/ms-marco-MiniLM-L-6-v2`) over the top 20.
13. Searches read without the lock, so a rare race can cause an `IndexError` during an upload. *Fix:* take a read lock, or search an immutable snapshot.
14. `sparse_rank` ends up holding the **worst** sparse rank for a section. *Fix:* keep the minimum.

**Generation**

15. Prompts don't include document names or pages, so the model can't cite sources. *Fix:* label each snippet with its source and ask for citations like `[1]`.
16. "Your own knowledge" invites claims the documents don't support. *Fix:* separate "from the documents" from "general knowledge", or forbid the latter.
17. There's one narrator, not two speakers. *Fix:* generate a dialogue script, synthesize two voices and merge them with pydub.
18. The `GEMINI_MODEL` default in the code is `gemini-1.5-flash`, which is outdated. *Fix:* update the default.
19. `cleanup_old_audio_files` calls `os.time()` (it should be `time.time()`) but is never called, and every podcast starts a thread that sleeps for 5 minutes. *Fix:* return the audio bytes directly, or run a single scheduled cleanup.

**Backend**

20. Blocking calls run inside `async def` endpoints: `/insights`, `/related-sections`, and the file saving in `/ingest`. *Fix:* use `def` endpoints, `run_in_threadpool`, or async clients.
21. When the browser aborts a request, the server keeps working. *Fix:* check `await request.is_disconnected()`, or move to jobs that can be cancelled.
22. Ingestion has no status. *Fix:* return a job ID and add a status endpoint, or push updates over Server-Sent Events or WebSocket.
23. State lives in one process, so workers can't be scaled out. *Fix:* use an external vector store or search service.
24. `@app.on_event` is deprecated. *Fix:* use a lifespan handler.
25. There's unused code and unused dependencies: the LightGBM model, pytesseract, the Azure Speech SDK, langchain-openai, torchvision/torchaudio, `requirements-core.txt`, `active_podcast_tasks`. *Fix:* remove them for a smaller image and a clearer codebase.

**Frontend**

26. The page jump is off by one, and first-page sections don't jump at all. *Fix:* use `page + 1`.
27. The podcast waits for insights to finish, and a podcast is generated for **every** selection, which costs money. *Fix:* run both in parallel once the related sections arrive, or generate the podcast only when the user asks.
28. Insights are shown as raw markdown. *Fix:* render them with `react-markdown`.
29. `VITE_API_URL` is baked in as `http://localhost:8080` in the Docker build, so the app breaks on any other host or port. *Fix:* use relative `/api` URLs.
30. The History and Library panels are mock data. A PDF opened in the reader lives only in the browser's navigation state, so a page refresh can lose it.

**Deployment and security**

31. `.env` is baked into the image, and `RUN cat /app/.env` prints the secrets into build logs. *Fix:* pass secrets at runtime, or use BuildKit secrets during the build.
32. A key in the baked `.env` overrides the same key passed with `docker run -e`. *Fix:* only fill in a value from the file when it isn't already set.
33. Real API keys are in the git history (commit `4dd5ea7`). *Fix:* rotate the keys, purge the history, and turn on secret scanning.
34. CORS allows `*`, and there's no authentication or rate limiting. *Fix:* restrict origins, and add authentication and rate limits.
35. The SPA catch-all joins the raw request path onto `dist`, which likely allows path traversal (such as reading `/app/.env`). *Fix:* resolve the real path and make sure it stays inside the static folder, or use `StaticFiles`.
36. Uploaded file names aren't sanitized. *Fix:* apply `os.path.basename` or generate the name, limit file size, and check the PDF's magic bytes.
37. Dependencies aren't pinned, so builds can't be reproduced; today the torch pin gets overridden. *Fix:* use a lock file or constraints file.
38. The embedding model is downloaded when the container starts, so the first start needs internet access and is slower. *Fix:* download it into the image at build time.

## 5.3 Improvement roadmap

| Horizon | Items |
|---|---|
| **Quick wins (≤ 1 day)** | Page +1; drop zero-score BM25 results; leave out the current document; use `def` endpoints; relative API URLs; restrict CORS; sanitize paths; remove `cat .env`; update the torch pin; render markdown; run insights and podcast in parallel |
| **Medium (a few days)** | Citations in prompts; cross-encoder re-ranking; ingestion job status; duplicate-upload detection; OCR and better heading detection; pytest tests plus a search evaluation set; bake the model into the image; lock dependencies |
| **Scale-up (weeks)** | Postgres + pgvector, or Qdrant; object storage for PDFs; a task queue with workers; authentication and multiple tenants; streaming LLM responses (SSE); caching; monitoring; a two-speaker podcast with streaming TTS |

## 5.4 Check your understanding

<details>
<summary>1. Why can Synapse use <code>IndexFlatL2</code> and still rank by cosine similarity?</summary>

all-MiniLM-L6-v2 ends with a Normalize layer, so every vector has length 1. For unit vectors, ‖a−b‖² = 2 − 2·cos(a, b), so the smallest distance always means the highest cosine similarity.
</details>

<details>
<summary>2. Which three files must stay aligned, and why?</summary>

`index.faiss`, `metadata.json` and `metadata_bm25.json`. FAISS IDs are just positions: vector i matches metadata entry i and word list i. If you delete or restore one file without the others, results point at the wrong text.
</details>

<details>
<summary>3. A section has chunks at FAISS ranks 2, 5 and 9, and nothing in the BM25 results. What is its RRF score?</summary>

1/62 + 1/65 + 1/69 = 0.01613 + 0.01538 + 0.01449 ≈ **0.0460**. Scores from chunks of the same section add up because the fusion key is (doc_name, section_title, page).
</details>

<details>
<summary>4. You change CHUNK_SIZE to 8. What else do you have to do?</summary>

Stop the backend, delete the three index files, restart, and upload the PDFs again. The existing chunks were built with the old window size.
</details>

<details>
<summary>5. Why does the Docker image need rebuilding when the Adobe client ID changes?</summary>

`VITE_ADOBE_CLIENT_ID` is written into the JavaScript bundle during `npm run build`, which happens inside `docker build`. Passing it with `docker run -e` doesn't change the bundle that's already built.
</details>

<details>
<summary>6. Why is the podcast endpoint wrapped in <code>run_in_threadpool</code>?</summary>

Generating a podcast means a blocking Gemini call plus a blocking TTS HTTP call, which can take many seconds. Running that on the event loop would freeze every other request.
</details>

<details>
<summary>7. A PDF uploaded successfully but never appears in results. Name two likely causes.</summary>

(a) Its headings aren't in a font whose name contains "Bold", or it's a scanned PDF, so 0 chunks were created (the log says "No meaningful text chunks were extracted"). (b) Processing failed, for example because NLTK's `punkt_tab` data was missing; check the backend logs.
</details>

<details>
<summary>8. What does k = 60 do in RRF?</summary>

It flattens the difference between ranks (1/61 vs 1/62 vs 1/63…). A result that several retrievers agree on then outweighs one retriever's single top pick, and no score normalization is needed.
</details>

<details>
<summary>9. Map each word of "RAG" to parts of Synapse.</summary>

**Retrieval**: hybrid search in `search.py`. **Augmented**: the snippets are inserted into the prompts in `generation.py`. **Generation**: Gemini, through `chat_with_llm.py`.
</details>

<details>
<summary>10. Why does clicking a related section land one page early?</summary>

PyMuPDF numbers pages from 0 and stores that number, while Adobe's `gotoLocation` numbers them from 1. Page 0 is also skipped by the `targetPage > 0` check.
</details>

<details>
<summary>11. What happens if you run <code>uvicorn main:app</code> from inside <code>backend/</code>?</summary>

`ModuleNotFoundError: No module named 'backend'`. main.py imports `backend.app...`, and the data paths are relative to the project root. Run `uvicorn backend.main:app` from the project root instead.
</details>
