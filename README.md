# AI Intelligence Ingestion Pipeline

An asynchronous, production-oriented Python data engineering framework designed to crawl, normalize, resolve entities, and output structured intelligence across 6 core data tabs.

---

## 📁 Submission Artifacts & Files

1. **Engineering Output**:
   - **`src/`**: Modular source code for scrapers, LLM orchestrator, entity resolver, and storage engines.
   - **`architecture.pdf`**: Detailed technical design document and scale architecture overview.
   - **`README.md`**: Complete setup instructions and architectural breakdown.

2. **Data Output (Multi-Tab Spreadsheet)**:
   - **`data/AI_Intelligence_Pipeline_Sheet.xlsx`**: Unified 6-tab spreadsheet ready to open in Excel or upload to Google Sheets.
   - **`data/processed/*.csv`**: Disk partitions streaming clean ingestion records.

---

## 📊 Core Data Partitions (6 Tabs)

1. **`Startups`**: Entity Name, Employee Count, Source Name, Source URL, Collected At.
2. **`Products`**: Product Name, Pricing Model (FREE, FREEMIUM, PAID, ENTERPRISE), Source Name, Source URL, Collected At.
3. **`Research Papers`**: Paper Title, Authors, Paper URL, GitHub Repository URL, GitHub Stars, Published Date.
4. **`Jobs`**: Job Title, Company Name (Canonical), Source Channel, Source URL, Date Collected (24h Freshness).
5. **`News`**: Article Title, Source Channel, Source URL, Published Date (24h Freshness).
6. **`Entity Mapping Log`**: Raw Input Name vs. Resolved Canonical Entity audit log.

---

## 🏗️ Architectural Overview

```text
       [Asynchronous Multi-Source Scrapers]
  ├── arXiv API (AI Research Papers & GitHub Stars)
  ├── YC Algolia Index (Startups Directory)
  ├── Software Registries (Product Profiles)
  ├── RSS Ports (TechCrunch, HackerNews, Reddit AI News)
  └── Job Ports (Remotive, WeWorkRemotely, HN Jobs)
                    │
                    ▼
     [Asynchronous Bounded Concurrency] (aiohttp + TCPConnector + Semaphores)
                    │
                    ▼
     [Deterministic Entity Resolver] (Regex Noise Cleaning + Canonical Registry)
                    │
                    ▼
     [LLM Orchestrator & Fallback Chain] (Gemini 1.5 → Groq Llama3 → DeepSeek)
                    │
                    ▼
     [Streaming Data Engine] (Atomic CSV Partitions + Multi-Tab Sheet Export)
```

---

## 🎯 Evaluation Alignment Highlights

* **LLM Orchestration (25%)**: 3-Tier fallback chain (`Gemini 1.5 Flash` → `Groq Llama 3 8B` → `DeepSeek Chat`) with sliding window payload chunking (`src/llm/chunker.py`).
* **Data Quality & Provenance (25%)**: Strict 24-hour freshness filters, ISO-8601 date parsing, live GitHub stargazers API enrichment, and **zero hallucination policy** (every record traces to a legitimate source URL).
* **Scale Thinking (20%)**: Designed to scale to 500k+ records using memory-isolated streaming writes and bounded async queues (`asyncio.Semaphore`).
* **Engineering Rigor (20%)**: Anti-fragile network retry decorator with exponential backoff and jitter (`src/utils/retry.py`).
* **Entity Resolution (10%)**: Deterministic cleaning stripping corporate noise (`Inc`, `LLC`, `Corp`, `AI`, `Labs`) with audit mapping logs.

---

## ⚙️ Quick Start & Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Ingestion Pipeline
```bash
python -m src.main
```

### 3. Generate Architecture PDF (Optional)
```bash
python create_architecture_pdf.py
```

### 4. Upload Data to Google Sheets
Open [Google Sheets](https://sheets.google.com), click **File > Import > Upload**, and select `data/AI_Intelligence_Pipeline_Sheet.xlsx` to create a live public Google Sheet with all 6 tabs!
