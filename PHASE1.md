# PHASE 1: Implementation Roadmap

## 📅 Project Timeline
**Start**: May 22, 2024  
**Deadline**: May 23, 2024 (1 day)  
**Status**: 🚀 In Development

---

## 🎯 Objectives

Build a **production-grade AI-powered fashion recommendation engine** that demonstrates mastery of:
- Web scraping with resilience (async, rate-limiting, error handling)
- RAG pipelines (embeddings, vector search, metadata filtering)
- Agentic AI workflows (LangChain, tool-use, multi-step reasoning)
- Backend API design (FastAPI, Pydantic, structured responses)
- Token economics (caching, prompt optimization, cost awareness)

**Success Metric**: Complete, working system with 100+ real fashion items, smart recommendations, and documented decisions.

---

## 🏗️ Architecture Overview

```
Scrapers (Zara, Myntra)
    ↓ [catalog.json]
RAG Pipeline (embeddings, ChromaDB)
    ↓
AI Agent (LangChain, fashion rules)
    ↓
FastAPI Server (/api/v1/style-me)
```

See `ARCHITECTURE.md` for detailed design decisions.

---

## 📝 Phase 1 Breakdown

### MILESTONE 1: Data Collection (Scraping)
**Goal**: Extract 50+ tops + 50+ bottoms from 2 sources  
**Estimated Time**: 2-3 hours  

#### Task 1.1: Zara Scraper
- [ ] Setup Playwright (async)
- [ ] Extract men's t-shirts page (URL: zara.com/men/tshirts)
- [ ] Extract men's trousers page (URL: zara.com/men/trousers)
- [ ] Parse DOM: item_name, price, image_url, category, description, source_url
- [ ] Add delays (2-5s random) between requests
- [ ] Rotate user-agents (5 real browser signatures)
- [ ] Implement retry logic (3 attempts)
- [ ] Target: 50+ items from Zara
- [ ] Test: Verify no duplicate items, all fields populated

**Expected Output**:
```json
[
  {
    "id": "zara-001",
    "item_name": "Premium Cotton T-Shirt",
    "price": "₹1,299",
    "image_url": "...",
    "category": "tops",
    "brand": "Zara",
    "description": "...",
    "source_url": "..."
  }
]
```

#### Task 1.2: Myntra Scraper
- [ ] Setup Playwright (async, same as Zara)
- [ ] Extract men's t-shirts page (URL: myntra.com/men/tshirts)
- [ ] Extract men's trousers page (URL: myntra.com/men/trousers)
- [ ] Same field extraction + resilience measures
- [ ] Target: 50+ items from Myntra
- [ ] Test: Verify quality, no missing fields

#### Task 1.3: Orchestration
- [ ] Create `run_scrapers.py`
- [ ] Run both scrapers concurrently with `asyncio.gather()`
- [ ] Deduplication: Remove duplicates by (item_name, brand)
- [ ] Save merged result to `data/catalog.json`
- [ ] Verify: 100+ items total, clean JSON structure

**Success Criteria**:
- ✅ 50+ tops + 50+ bottoms in catalog.json
- ✅ All items have: name, price, image, category, brand, description, source_url
- ✅ No corrupted data, all URLs valid
- ✅ Execution time < 5 minutes

---

### MILESTONE 2: RAG Pipeline (Vector Intelligence)
**Goal**: Embed catalog, setup ChromaDB, implement search  
**Estimated Time**: 1.5-2 hours  

#### Task 2.1: Embedding Service
- [ ] Create `rag/embedder.py`
- [ ] Initialize OpenAI client (use OPENAI_API_KEY from .env)
- [ ] Load catalog from `data/catalog.json`
- [ ] Generate embeddings using `text-embedding-3-small` (1536 dims)
- [ ] **Batch embeddings**: Process 50 items per batch to reduce API calls
- [ ] Setup ChromaDB collection named "fashion_catalog"
- [ ] Store embeddings + metadata: {category, brand, price, color}

**Code Sketch**:
```python
from rag.embedder import EmbedderService

service = EmbedderService()
service.embed_catalog()  # Reads catalog.json, embeds, stores in ChromaDB
print("✅ 100 items embedded in ChromaDB")
```

#### Task 2.2: Vector Store (Search Logic)
- [ ] Create `rag/vector_store.py`
- [ ] Implement `search()` method:
  - Input: query (string), filters (dict), top_k (int)
  - Process: Embed query → Pre-filter by metadata → Semantic search
  - Output: Top-K items with similarity scores
- [ ] Support filtering by: category, price_range, brand
- [ ] Enrich results with full item data from catalog.json

**Example**:
```python
from rag.vector_store import VectorStore

vs = VectorStore()
results = vs.search(
    query="white t-shirt for summer",
    filters={"category": "tops", "max_price": 2000},
    top_k=5
)
# Returns: [item1, item2, item3, item4, item5] (sorted by relevance)
```

#### Task 2.3: Caching Layer
- [ ] Create `rag/cache.py`
- [ ] Implement in-memory cache with TTL (1-hour default)
- [ ] Cache key: hash of (user_query + filters)
- [ ] Check cache before doing expensive searches
- [ ] Expected impact: 40% cache hit rate on repeated queries

**Success Criteria**:
- ✅ All 100 items successfully embedded
- ✅ Semantic search returns relevant results (manual testing)
- ✅ Metadata filtering works (category, price, brand)
- ✅ Cache reduces duplicate searches

---

### MILESTONE 3: AI Agent (Fashion Stylist)
**Goal**: Implement multi-step agentic workflow with fashion rules  
**Estimated Time**: 2-2.5 hours  

#### Task 3.1: Fashion Rules Engine
- [ ] Create `agent/fashion_rules.py`
- [ ] Define 15+ fashion matching rules:
  - **Color harmony**: navy pairs with white, cream, light blue
  - **Occasion fit**: yacht party → premium fabrics, bright colors
  - **Price ratio**: expensive top (~₹2000) should pair with comparable bottom
  - **Material compatibility**: cotton + linen work well, viscose + polyester balance
- [ ] Implement scoring function: validate_pairing(item1, item2) → score (0-1)
- [ ] Example usage:
  ```python
  rules = FashionRules()
  score = rules.validate_pairing(tshirt, trouser)  # 0.87
  ```

#### Task 3.2: Stylist Agent
- [ ] Create `agent/stylist_agent.py`
- [ ] Setup LangChain agent with tools:
  1. `search_catalog`: Query vector store for matching items
  2. `validate_pairing`: Check if two items work together
- [ ] Implement `recommend()` method:
  - Parse user prompt for context (occasion, mood, budget)
  - Search for matching tops + bottoms
  - Use fashion rules to validate pairings
  - Score confidence (0-1)
  - Generate "Stylist Note" explaining the recommendation

**Agent Workflow**:
```
User: "I have dark navy chinos, what t-shirt for yacht party?"
  ↓
Agent: "Parsing context: navy chinos + yacht party + budget ₹5000"
  ↓
Agent: "Searching for t-shirts..."
  → Vector search: "t-shirt white summer premium"
  → Filter: category=tops, price<=2000
  → Result: [Zara white tee ₹1299, Myntra cream tee ₹1499, ...]
  ↓
Agent: "Validating pairings with fashion rules..."
  → Zara white + navy chinos: Color harmony ✅, Price ratio ✅, Material ✅
  → Score: 0.92 (high confidence)
  ↓
Agent: "Generating stylist note..."
  → "This premium white cotton complements your navy chinos perfectly..."
  ↓
Return: {
  "recommendations": [Zara white tee, navy chinos],
  "total_price": "₹3,299",
  "stylist_note": "...",
  "confidence": 0.92
}
```

#### Task 3.3: Integration
- [ ] Connect agent to vector store (pass VectorStore instance)
- [ ] Connect agent to fashion rules (pass FashionRules instance)
- [ ] Test with manual prompts:
  - "Dark navy chinos, yacht party, ₹5000" → Should return white/cream t-shirt
  - "Black trousers, office meeting, ₹3000" → Should return formal t-shirt
  - "Blue jeans, casual outing, ₹1500" → Should return casual t-shirt

**Success Criteria**:
- ✅ Agent returns non-hallucinated items (only from catalog)
- ✅ Recommendations align with user context
- ✅ Confidence score >0.80 for good matches
- ✅ Stylist Note explains reasoning clearly

---

### MILESTONE 4: FastAPI Backend
**Goal**: Expose agent via REST API with structured responses  
**Estimated Time**: 1-1.5 hours  

#### Task 4.1: Pydantic Schemas
- [ ] Create `api/schemas.py`
- [ ] Define `StyleRequest`:
  ```python
  class StyleRequest(BaseModel):
      user_prompt: str  # min 10 chars, max 500
      budget: int = 10000  # default
      preferred_brands: List[str] = []  # optional
  ```
- [ ] Define `RecommendedItem`:
  ```python
  class RecommendedItem(BaseModel):
      item_name: str
      price: str
      image_url: str
      brand: str
      category: str
      source_url: str
  ```
- [ ] Define `StyleResponse`:
  ```python
  class StyleResponse(BaseModel):
      status: str  # "success" or "error"
      recommendations: List[RecommendedItem]
      total_price: str
      stylist_note: str
      confidence: float  # 0-1
      execution_time_ms: float
  ```

#### Task 4.2: FastAPI Server
- [ ] Create `api/main.py`
- [ ] Initialize FastAPI app:
  ```python
  from fastapi import FastAPI
  from api.schemas import StyleRequest, StyleResponse
  
  app = FastAPI(
      title="Luxury Stylist Concierge",
      description="AI-powered fashion recommendation engine"
  )
  ```
- [ ] Implement POST `/api/v1/style-me`:
  - Accept StyleRequest
  - Validate input with Pydantic
  - Call StylistAgent.recommend()
  - Return StyleResponse with execution_time_ms
  - Handle errors gracefully

**Example Endpoint**:
```python
@app.post("/api/v1/style-me", response_model=StyleResponse)
async def style_me(request: StyleRequest) -> StyleResponse:
    start_time = time.time()
    
    try:
        agent = StylistAgent()
        result = agent.recommend(request.user_prompt, request.budget)
        
        return StyleResponse(
            status="success",
            recommendations=result['items'],
            total_price=result['total_price'],
            stylist_note=result['stylist_note'],
            confidence=result['confidence'],
            execution_time_ms=(time.time() - start_time) * 1000
        )
    except Exception as e:
        return StyleResponse(
            status="error",
            recommendations=[],
            total_price="0",
            stylist_note=str(e),
            confidence=0,
            execution_time_ms=(time.time() - start_time) * 1000
        )
```

#### Task 4.3: Server Launch
- [ ] Add main block to start server:
  ```python
  if __name__ == "__main__":
      import uvicorn
      uvicorn.run(app, host="0.0.0.0", port=8000)
  ```
- [ ] Test server startup:
  ```bash
  python api/main.py
  # Output: "Uvicorn running on http://0.0.0.0:8000"
  ```
- [ ] Visit `http://localhost:8000/docs` → Swagger UI should load
- [ ] Manually test POST request with sample data

**Success Criteria**:
- ✅ Server starts without errors
- ✅ Swagger UI loads at /docs
- ✅ POST /api/v1/style-me accepts requests
- ✅ Response matches StyleResponse schema
- ✅ Execution time logged (typical: <2 seconds)

---

### MILESTONE 5: Configuration & Deployment
**Goal**: Setup environment, requirements, and documentation  
**Estimated Time**: 30-45 minutes  

#### Task 5.1: requirements.txt
- [ ] List all dependencies:
  ```
  playwright>=1.40.0
  asyncio  (built-in)
  aiohttp>=3.9.0
  aiofiles>=23.0.0
  python-dotenv>=1.0.0
  fastapi>=0.104.0
  uvicorn>=0.24.0
  langchain>=0.1.0
  langchain-openai>=0.0.5
  chromadb>=0.4.0
  openai>=1.3.0
  pydantic>=2.0.0
  ```
- [ ] Test installation:
  ```bash
  pip install -r requirements.txt
  ```

#### Task 5.2: .env Configuration
- [ ] Create `.env.example`:
  ```
  OPENAI_API_KEY=sk-...
  ZARA_BASE_URL=https://www.zara.com
  MYNTRA_BASE_URL=https://www.myntra.com
  CHROMADB_PATH=./chromadb_data
  CACHE_TTL_HOURS=1
  ```
- [ ] Create actual `.env` with real keys
- [ ] Add `.env` to `.gitignore` (don't commit secrets)

#### Task 5.3: Project Setup
- [ ] Create folder structure:
  ```
  luxury-stylist/
  ├── README.md
  ├── ARCHITECTURE.md
  ├── PHASE1.md
  ├── requirements.txt
  ├── .env.example
  ├── scrapers/
  ├── data/
  ├── rag/
  ├── agent/
  └── api/
  ```
- [ ] Initialize git repository (if not already)
- [ ] Create meaningful commit messages

**Success Criteria**:
- ✅ All files in correct locations
- ✅ requirements.txt installs without errors
- ✅ .env file created with OPENAI_API_KEY
- ✅ Git repo initialized with clean history

---

## 🧪 Testing Checklist

### Unit Tests (Manual for now)
- [ ] Zara scraper returns 50+ items
- [ ] Myntra scraper returns 50+ items
- [ ] Deduplication works (no duplicates in catalog.json)
- [ ] Vector search returns relevant items
- [ ] Fashion rules score valid pairings
- [ ] Agent generates non-hallucinated recommendations

### Integration Tests
- [ ] Scraper → catalog.json → embedder workflow
- [ ] Catalog → ChromaDB → vector search workflow
- [ ] User prompt → agent reasoning → recommendations workflow
- [ ] Request → API → response workflow

### API Testing
- [ ] POST /api/v1/style-me with valid request
- [ ] POST /api/v1/style-me with invalid budget (should fail)
- [ ] POST /api/v1/style-me with short prompt (should fail)
- [ ] Response schema matches Pydantic model

---

## 📊 Submission Deliverables

### Code
- [x] `scrapers/zara_scraper.py` - Production-grade Zara scraper
- [x] `scrapers/myntra_scraper.py` - Production-grade Myntra scraper
- [x] `scrapers/run_scrapers.py` - Orchestrator with dedup
- [x] `data/catalog.json` - 100+ items (50+ tops, 50+ bottoms)
- [x] `rag/embedder.py` - Embedding service with batch processing
- [x] `rag/vector_store.py` - Vector search with filtering
- [x] `rag/cache.py` - Query caching layer
- [x] `agent/stylist_agent.py` - LangChain agent orchestration
- [x] `agent/fashion_rules.py` - 15+ fashion matching rules
- [x] `api/main.py` - FastAPI server with /api/v1/style-me
- [x] `api/schemas.py` - Pydantic request/response models
- [x] `requirements.txt` - All dependencies
- [x] `.env.example` - Environment template

### Documentation
- [x] `README.md` - Project overview, features, quick start
- [x] `ARCHITECTURE.md` - Design decisions, token economics, data flow
- [x] `PHASE1.md` - This file, implementation roadmap

### Demo
- [ ] **Screen Recording** (5-10 min):
  - Terminal: Run `python scrapers/run_scrapers.py`
  - Terminal: Start server `python api/main.py`
  - Browser: Open Swagger UI at http://localhost:8000/docs
  - Swagger: Send test request to /api/v1/style-me
  - Browser: Show response JSON
  - Terminal: Show agent reasoning logs

---

## 🎯 Success Criteria (Final)

| Criterion | Status |
|-----------|--------|
| 100+ real fashion items (50+/50+) | ⬜ |
| Robust scrapers (async, delays, retries) | ⬜ |
| RAG pipeline (embeddings, vector search, caching) | ⬜ |
| AI agent (LangChain, tool-use, fashion rules) | ⬜ |
| FastAPI endpoint (/api/v1/style-me) | ⬜ |
| Structured responses (Pydantic schemas) | ⬜ |
| Token optimization (semantic cache, batching) | ⬜ |
| Complete documentation (README, ARCHITECTURE, PHASE1) | ⬜ |
| Screen recording (demo) | ⬜ |
| GitHub repo with clean history | ⬜ |

---

## 📈 Time Estimate Breakdown

| Milestone | Est. Time | Status |
|-----------|-----------|--------|
| 1. Scraping | 2-3 hours | ⬜ |
| 2. RAG Pipeline | 1.5-2 hours | ⬜ |
| 3. AI Agent | 2-2.5 hours | ⬜ |
| 4. FastAPI | 1-1.5 hours | ⬜ |
| 5. Config & Docs | 1-1.5 hours | ⬜ |
| **Total** | **8-11 hours** | **⬜** |

---

## 🚀 Next Steps

1. **Review** this PHASE1.md and ARCHITECTURE.md
2. **Start coding** Task 1.1 (Zara Scraper)
3. **Iterate** through milestones in order
4. **Test** each milestone before moving to next
5. **Record demo** once all code is complete
6. **Submit** to mehtesham@quickeee.com with GitHub link

---

## 💡 Key Principles

✅ **Complete, Not Perfect**: Focus on working code first  
✅ **Real Data**: Use actual Zara/Myntra inventory, no mocks  
✅ **Explain Choices**: Every design decision has a reason (see ARCHITECTURE.md)  
✅ **Show Reasoning**: Agent logs must reveal its thinking  
✅ **Cost-Conscious**: Demonstrate token optimization mindset  
✅ **Production-Grade**: Error handling, validation, logging throughout  

---

**Let's build something amazing! 🎨✨**
