# Project Summary & Quick Reference

## 📌 One-Page Overview

You're building a **Luxury Stylist Concierge** - an AI-powered fashion recommendation API for Quickeee. Users ask "What t-shirt goes with my navy chinos for a yacht party?" and your system returns structured outfit recommendations with styling explanations.

---

## 🎯 What You're Delivering

### 1. **Scrapers** (2-3 hours)
Extract real fashion inventory from Zara & Myntra. Must handle:
- Async requests (fast)
- Rate-limiting (delays 2-5s between requests)
- User-agent rotation (5 real browser signatures)
- Retry logic (3 attempts on failure)
- Target: 100+ items (50+ tops, 50+ bottoms)

**Output**: `data/catalog.json`

### 2. **RAG Pipeline** (1.5-2 hours)
Store inventory smartly with embeddings. Must have:
- OpenAI embeddings (text-embedding-3-small)
- ChromaDB for local vector storage
- Semantic search + metadata filtering
- Query caching (1-hour TTL)

**Purpose**: Find relevant items based on user intent + budget

### 3. **AI Agent** (2-2.5 hours)
Use LangChain to reason about fashion. Must:
- Parse user context (occasion, style, budget)
- Search catalog for matching items
- Apply fashion rules (color harmony, price ratio, occasion fit)
- Generate confidence score + explanation

**Why**: LLMs alone hallucinate. Rules ground it in catalog reality.

### 4. **FastAPI Server** (1-1.5 hours)
Single endpoint: `POST /api/v1/style-me`
- Accepts: user prompt, budget, preferred brands
- Returns: recommendations, total price, stylist note, confidence
- Validates input with Pydantic
- Logs execution time

**Why**: Production-grade API, not just scripts

### 5. **Documentation** (1-1.5 hours)
- `README.md` - Project overview, quick start
- `ARCHITECTURE.md` - Design decisions, token economics
- `PHASE1.md` - Implementation roadmap (milestone-by-milestone)
- Screen recording of live demo

---

## 📁 Folder Structure (Ready to Build)

```
luxury-stylist/
├── README.md                    ← Project overview (DONE)
├── ARCHITECTURE.md              ← Design decisions (DONE)
├── PHASE1.md                    ← Implementation roadmap (DONE)
├── PROJECT_SUMMARY.md           ← This file (DONE)
├── requirements.txt             ← Dependencies (TODO)
├── .env.example                 ← Environment vars (TODO)
│
├── scrapers/
│   ├── zara_scraper.py          ← Extract from zara.com (TODO)
│   ├── myntra_scraper.py        ← Extract from myntra.com (TODO)
│   └── run_scrapers.py          ← Orchestrate both (TODO)
│
├── data/
│   └── catalog.json             ← 100+ items (TODO - auto-generated)
│
├── rag/
│   ├── embedder.py              ← Embed catalog to ChromaDB (TODO)
│   ├── vector_store.py          ← Search with filtering (TODO)
│   └── cache.py                 ← Query caching (TODO)
│
├── agent/
│   ├── stylist_agent.py         ← LangChain orchestration (TODO)
│   └── fashion_rules.py         ← Fashion matching logic (TODO)
│
└── api/
    ├── main.py                  ← FastAPI server (TODO)
    └── schemas.py               ← Pydantic models (TODO)
```

---

## 🔄 Data Flow (Visual)

```
User: "Navy chinos, yacht party, ₹5000"
         ↓
    Validate Input (Pydantic)
         ↓
    Parse Context (Agent)
         ↓
    Search Catalog (Vector DB)
         → Filter: category=tops, price≤2000
         → Embed query: "white premium t-shirt summer"
         → Find similar items (top-5)
         ↓
    Validate Pairing (Fashion Rules)
         → Color match? (navy + white = ✅)
         → Price ratio? (₹1299 vs ₹3999 = ✅)
         → Material? (cotton + cotton = ✅)
         → Occasion? (yacht party = ✅)
         ↓
    Score & Explain (Agent)
         → Confidence: 0.92
         → Note: "White cotton balances your navy chinos perfectly..."
         ↓
    Return JSON Response
    {
      "recommendations": [Zara white tee],
      "total_price": "₹5,298",
      "stylist_note": "...",
      "confidence": 0.92
    }
```

---

## 💡 Key Design Decisions (Why This Approach?)

### Why Async Scraping?
- 50 items in 2 minutes (vs. 10+ minutes sync)
- Uses `asyncio` + `aiohttp` for concurrent requests
- Real-world scraping is I/O bound, async is natural

### Why ChromaDB (Not Pinecone)?
- Local: No API key, no network latency
- Free: No recurring costs
- Fast: <10ms queries
- For 100 items, overkill to use cloud VectorDB

### Why Separate Scrapers (Not Generic)?
- Zara has unique DOM structure
- Myntra uses different HTML classes
- Site-specific optimization = better data quality
- Shows understanding of real-world complexity

### Why Fashion Rules (Not Just LLM)?
- Prevents hallucination (LLM might invent items not in catalog)
- Explainable: "Why this pairing?" has clear answers
- Deterministic: Same input always gives same rule evaluation
- Domain expertise: Developers know fashion rules better than LLM

### Why Token Optimization?
- OpenAI API costs money (even at scale)
- Semantic caching: 40% of queries are similar → reuse results
- Batch embeddings: 100 items → 1-2 API calls (not 100)
- Prompt compression: 2000 tokens → 800 tokens per recommendation
- Principle: "Treat tokens like your own money"

---

## ⏱️ Time Breakdown

| Phase | Time | Status |
|-------|------|--------|
| Scraping | 2-3 hrs | TODO |
| RAG | 1.5-2 hrs | TODO |
| Agent | 2-2.5 hrs | TODO |
| API | 1-1.5 hrs | TODO |
| Config + Docs | 1-1.5 hrs | TODO |
| **Total** | **8-11 hrs** | TODO |

**Deadline**: May 23, 2024 (1 day)  
**Recommendation**: Start immediately, focus on core features first

---

## 🚀 Implementation Sequence

1. **Setup** (15 min)
   - Create folder structure
   - Create requirements.txt
   - Create .env.example
   - Install dependencies: `pip install -r requirements.txt`

2. **Scraping** (2-3 hours)
   - Implement `zara_scraper.py`
   - Implement `myntra_scraper.py`
   - Implement `run_scrapers.py`
   - Verify: 100+ items in `data/catalog.json`

3. **RAG** (1.5-2 hours)
   - Implement `embedder.py`
   - Implement `vector_store.py`
   - Implement `cache.py`
   - Verify: ChromaDB working, search returning results

4. **Agent** (2-2.5 hours)
   - Implement `fashion_rules.py`
   - Implement `stylist_agent.py`
   - Test with manual prompts

5. **API** (1-1.5 hours)
   - Implement `schemas.py`
   - Implement `main.py`
   - Test POST requests

6. **Demo & Submit** (30 min)
   - Record 5-10 min screen recording
   - Push to GitHub
   - Email GitHub link to mehtesham@quickeee.com

---

## ✅ Quality Checklist

### Scraper Quality
- [ ] Handles network errors gracefully (3 retries)
- [ ] Respects server (2-5s delays, rotating user-agents)
- [ ] Extracts all required fields (name, price, image, category, etc.)
- [ ] Deduplicates by (item_name, brand)
- [ ] 100+ items total (50+ tops, 50+ bottoms)

### RAG Quality
- [ ] Embeddings generated batch-wise (efficient)
- [ ] ChromaDB indexed and searchable
- [ ] Semantic search returns relevant items
- [ ] Metadata filtering works (category, price, brand)
- [ ] Cache reduces duplicate queries

### Agent Quality
- [ ] Recommends only items from catalog (no hallucination)
- [ ] Validates pairings with fashion rules
- [ ] Confidence score reflects quality (0.7-1.0)
- [ ] Stylist Note explains reasoning

### API Quality
- [ ] FastAPI server starts without errors
- [ ] Swagger UI loads at /docs
- [ ] Request validation works (rejects invalid input)
- [ ] Response matches schema
- [ ] Execution time logged

### Documentation Quality
- [ ] README explains project in business terms
- [ ] ARCHITECTURE explains design decisions
- [ ] PHASE1 provides implementation roadmap
- [ ] Code has minimal comments (good naming instead)
- [ ] All files follow consistent style

---

## 🎓 What This Demonstrates

**For Quickeee** (They care about):
- ✅ You can build RAG systems (prompt, search, retrieve)
- ✅ You understand token economics (not wasting money)
- ✅ You can use modern AI tools (LangChain, OpenAI, ChromaDB)
- ✅ You write production-grade code (validation, error handling, logging)
- ✅ You think like an engineer (design decisions with tradeoffs)

**Technical Skills Shown**:
- 🐍 Python (async, OOP, error handling)
- 🌐 Web scraping (Playwright, rate limiting, resilience)
- 🔍 RAG & Vector DBs (embeddings, semantic search, caching)
- 🤖 AI Agents (LangChain, tool-use, multi-step reasoning)
- ⚡ Backend APIs (FastAPI, Pydantic, async handlers)
- 💰 Cost optimization (token economics, prompt compression)

---

## 🔗 Quick References

**FastAPI Docs**: https://fastapi.tiangolo.com/  
**LangChain Docs**: https://python.langchain.com/  
**ChromaDB Docs**: https://www.trychroma.com/  
**Playwright Docs**: https://playwright.dev/python/  
**OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings

---

## 📧 Submission Info

**To**: mehtesham@quickeee.com  
**Subject**: Gen AI & Data Engineer Assignment - Luxury Stylist Concierge  
**What to Include**:
1. GitHub repository link (public)
2. Brief note: "Assignment completed as per PHASE1.md"
3. Link to screen recording (Google Drive, YouTube, etc.)

**Expected**: Complete, working code with zero placeholders

---

## 💪 You've Got This!

- You have clear requirements ✅
- You have architecture design ✅
- You have implementation roadmap ✅
- You have time: ~8-11 hours for ~1 day ✅

**Focus**:
1. Get scrapers working first (easiest to validate)
2. Get RAG pipeline working (embedding catalog)
3. Build agent (complex but exciting)
4. Wrap with API (easy once others work)
5. Record demo
6. Submit

**Start NOW!** The sooner you start, the more time you have for debugging.

---

**Last Updated**: May 22, 2024  
**For Questions**: Refer to ARCHITECTURE.md (design), PHASE1.md (implementation), or README.md (overview)
