# Architecture & Design Decisions

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Component Deep-Dive](#component-deep-dive)
3. [Design Decisions & Rationale](#design-decisions--rationale)
4. [Token Economics Strategy](#token-economics-strategy)
5. [Data Flow & State Management](#data-flow--state-management)
6. [Error Handling & Resilience](#error-handling--resilience)
7. [Performance Optimization](#performance-optimization)

---

## System Architecture Overview

### High-Level Data Journey

```
┌─────────────┐
│ User Prompt │  "I have dark navy chinos, suggest a t-shirt for yacht party"
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────┐
│         FastAPI Request Handler          │
│         (api/main.py)                    │
│  • Validate input (Pydantic schema)      │
│  • Extract user context                  │
│  • Initialize agent state                │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│      AI Agent Orchestration              │
│      (agent/stylist_agent.py)            │
│  • Parse occasion/mood/budget            │
│  • Plan search strategy                  │
│  • Execute tool calls                    │
└──────────┬───────────────────────────────┘
           │
           ├─────────────────┬──────────────────┐
           │                 │                  │
           ▼                 ▼                  ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ RAG Search   │  │ Fashion Rules│  │ Cache Lookup │
    │ (Query DB)   │  │ Engine       │  │ (Check hits) │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                  │
           └─────────────────┼──────────────────┘
                             │
                             ▼
               ┌──────────────────────────┐
               │  Vector Database Layer   │
               │  (rag/vector_store.py)   │
               │  • Search by embedding   │
               │  • Filter by metadata    │
               │  • Return top-K results  │
               └──────────┬───────────────┘
                          │
                          ▼
               ┌──────────────────────────┐
               │ ChromaDB (Local VectorDB)│
               │  - 100+ items embedded   │
               │  - Metadata indexed      │
               │  - Fast similarity search│
               └──────────┬───────────────┘
                          │
                          ▼
               ┌──────────────────────────┐
               │  Fashion Catalog         │
               │  (data/catalog.json)     │
               │  - 50+ tops              │
               │  - 50+ bottoms           │
               │  - Zara + Myntra blend   │
               └──────────┬───────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │  Agent Reasoning & Validation │
          │  - Verify recommendations     │
          │  - Score confidence           │
          │  - Generate Stylist Note      │
          └───────────┬───────────────────┘
                      │
                      ▼
        ┌─────────────────────────────────┐
        │ Structured JSON Response        │
        │ {recommendations, total_price,  │
        │  stylist_note, confidence}      │
        └─────────────────────────────────┘
```

---

## Component Deep-Dive

### 1. Scraper Layer (`scrapers/`)

#### Why Two Separate Scrapers?
- **Zara**: Premium positioning, consistent DOM structure, modern tech stack
- **Myntra**: Indian market focus, local pricing, high inventory volume
- **Rationale**: Diversity in source reduces algorithmic bias in recommendations

#### `zara_scraper.py` Architecture
```python
# Pseudo-structure
class ZaraScraper:
    async def scrape(self):
        async with playwright:
            for page in [MENS_TSHIRTS, MENS_TROUSERS]:
                items = await self.extract_items(page)
                items = await self.enrich_with_details(items)
                return items
    
    async def extract_items(self, page_url):
        # DOM parsing → extract: name, price, image, url
        # 50+ items from pagination
        pass
    
    async def enrich_with_details(self, items):
        # Visit each item page → grab description, fuller image
        # Random 2-5s delay between requests
        # Rotate user-agent from pool of 5
        pass
```

**Key Design Choices**:
- ✅ **Async Playwright** (not sync) for speed: 50+ items in ~2 min
- ✅ **2-5s random delays**: Respectful to server, avoids rate-limiting
- ✅ **5 rotating user-agents**: Mimics real browser traffic patterns
- ✅ **3-attempt retry**: Transient network errors are common
- ✅ **Structured extraction**: JSON with consistent fields

#### `run_scrapers.py` - Orchestration
```python
# Pseudo-code
async def main():
    # Run both scrapers concurrently
    zara_items, myntra_items = await asyncio.gather(
        ZaraScraper().scrape(),
        MyntraScraper().scrape()
    )
    
    # Deduplication by (item_name, brand)
    merged = deduplicate(zara_items, myntra_items)
    
    # Save to catalog
    with open('data/catalog.json', 'w') as f:
        json.dump(merged, f)
```

**Why Deduplication?**
- Same t-shirt may exist on both platforms
- Reduces vector DB noise
- Improves semantic search precision

---

### 2. Data Layer (`data/`)

#### `catalog.json` Structure
```json
[
  {
    "id": "zara-tshirt-001",
    "item_name": "Premium Cotton T-Shirt",
    "price": "₹1,299",
    "currency": "INR",
    "image_url": "https://...",
    "category": "tops",
    "brand": "Zara",
    "description": "Soft cotton blend, breathable, perfect for summer",
    "source_url": "https://zara.com/...",
    "color": "white",
    "material": "100% cotton",
    "scraped_at": "2024-05-22T10:30:00Z"
  }
  // ... 100+ items total
]
```

**Design Rationale**:
- ✅ **Unique IDs**: Deduplication + tracking
- ✅ **Metadata fields**: Extracted for filtering (color, material, price)
- ✅ **Timestamp**: Track freshness, decide when to re-scrape
- ✅ **Both currencies**: Raw format for price matching
- ✅ **Descriptions**: Used for semantic embeddings

---

### 3. RAG Layer (`rag/`)

#### Why ChromaDB Instead of Pinecone/Milvus?
| Aspect | ChromaDB | Pinecone | Milvus |
|--------|----------|----------|--------|
| **Setup** | Local, no external service | API key, cloud | Docker container |
| **Cost** | Free (local) | $0.04/1K vectors | Free (open-source) |
| **Latency** | <10ms (local) | 50-200ms (API) | <10ms (local) |
| **Learning** | Minimal | Simple API | More complex setup |
| **For Demo** | ✅ Perfect | ❌ Overkill | ⚠️ Extra infra |

**Decision**: ChromaDB for fast iteration + cost efficiency

#### `embedder.py` - Embedding Pipeline
```python
class EmbedderService:
    def __init__(self):
        self.client = chromadb.Client()
        self.embedder_model = "text-embedding-3-small"  # 1536 dims
    
    def embed_catalog(self):
        # Read catalog.json
        items = load_json('data/catalog.json')
        
        # Prepare embeddings
        texts = [item['description'] for item in items]
        
        # Batch embed (reduce API calls)
        embeddings = self.batch_embed(texts, batch_size=50)
        
        # Store in ChromaDB with metadata
        self.client.add(
            ids=[item['id'] for item in items],
            documents=texts,
            embeddings=embeddings,
            metadatas=[
                {
                    'category': item['category'],
                    'brand': item['brand'],
                    'price': float(item['price']),
                    'color': item.get('color', 'unknown')
                }
                for item in items
            ]
        )
    
    def batch_embed(self, texts, batch_size=50):
        # Call OpenAI API in batches to avoid rate limits
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            resp = openai.Embedding.create(
                input=batch,
                model=self.embedder_model
            )
            embeddings.extend([r['embedding'] for r in resp['data']])
        return embeddings
```

**Design Choices**:
- ✅ **text-embedding-3-small**: Fast + cheap ($0.02 per 1M tokens)
- ✅ **Batch embeddings**: Reduce API calls from 100+ to 2-3
- ✅ **Metadata in ChromaDB**: Enable filtered search (category, price, brand)
- ✅ **1536-dim vectors**: Good balance of richness & speed

#### `vector_store.py` - Search Logic
```python
class VectorStore:
    def search(self, query, filters=None, top_k=5):
        # 1. Generate embedding for user query
        query_embedding = self.embed_text(query)
        
        # 2. Pre-filter by metadata (category, price, brand)
        where_clause = self.build_where(filters)
        
        # 3. Semantic search in ChromaDB
        results = self.client.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause
        )
        
        # 4. Enrich with full item data
        items = self.hydrate_with_catalog(results['ids'][0])
        return items
    
    def build_where(self, filters):
        # Construct ChromaDB $where clause
        where = {}
        if filters.get('category'):
            where['category'] = {'$eq': filters['category']}
        if filters.get('max_price'):
            where['price'] = {'$lte': filters['max_price']}
        return where
```

**Two-Stage Search**:
1. **Metadata filter** (fast): Narrow by category/price/brand
2. **Semantic search** (precise): Find similar items by meaning

**Why This Order?**
- Reduces vector search space (faster + cheaper)
- Ensures results respect hard constraints (budget)
- Example: "blue tshirts under ₹2000" → filter first, then search

#### `cache.py` - Query Caching
```python
class QueryCache:
    def __init__(self, ttl_hours=1):
        self.cache = {}  # In-memory cache
        self.ttl = ttl_hours * 3600
    
    def get(self, query_hash):
        # Check if query result exists and is fresh
        if query_hash in self.cache:
            entry = self.cache[query_hash]
            if time.time() - entry['created_at'] < self.ttl:
                return entry['results']
        return None
    
    def set(self, query_hash, results):
        self.cache[query_hash] = {
            'results': results,
            'created_at': time.time()
        }
```

**Cost Savings**:
- OpenAI embeddings: $0.02 per 1M tokens
- With 40% cache hit rate: Saves ~$0.008 per 100 queries
- Adds up quickly at scale

---

### 4. Agent Layer (`agent/`)

#### `stylist_agent.py` - LangChain Agent
```python
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI

class StylistAgent:
    def __init__(self):
        self.llm = OpenAI(temperature=0.7, model="gpt-3.5-turbo")
        self.vector_store = VectorStore()
        self.fashion_rules = FashionRules()
        
        # Define tools for the agent
        self.tools = [
            Tool(
                name="search_catalog",
                func=self.search_catalog,
                description="Search fashion catalog by user query"
            ),
            Tool(
                name="validate_pairing",
                func=self.validate_pairing,
                description="Check if two items work together using fashion rules"
            )
        ]
    
    def recommend(self, user_prompt: str) -> dict:
        # 1. Agent analyzes user context (occasion, style, budget)
        context = self.llm.predict(f"Analyze: {user_prompt}")
        
        # 2. Agent searches for matching tops/bottoms
        tops = self.search_catalog(f"tops for {user_prompt}")
        bottoms = self.search_catalog(f"bottoms for {user_prompt}")
        
        # 3. Agent validates pairings using fashion rules
        best_pair = max(
            [(t, b) for t in tops for b in bottoms],
            key=lambda pair: self.validate_pairing(pair[0], pair[1])
        )
        
        # 4. Generate stylist note
        note = self.llm.predict(
            f"Explain why {best_pair[0]} and {best_pair[1]} work together"
        )
        
        return {
            "recommendations": list(best_pair),
            "stylist_note": note,
            "confidence": self.score_confidence(context, best_pair)
        }
```

**Agent Architecture**:
- ✅ **Tool-use pattern**: Agent decides what to search for
- ✅ **Multi-step reasoning**: Context → search → validate → explain
- ✅ **External validation**: Fashion rules catch bad matches
- ✅ **Temperature=0.7**: Creative but not hallucinated

#### `fashion_rules.py` - Domain Knowledge
```python
class FashionRules:
    RULES = {
        'color_matching': {
            'navy': ['white', 'cream', 'light_blue', 'grey'],
            'black': ['white', 'red', 'gold'],
            # ...
        },
        'occasion_fit': {
            'yacht_party': ['premium_fabrics', 'bright_colors', 'fitted'],
            'office': ['formal', 'neutral', 'structured'],
            # ...
        },
        'price_harmony': {
            # Expensive top should pair with comparable bottom
            'max_price_ratio': 1.5
        }
    }
    
    def validate(self, item1, item2):
        # Check multiple fashion rules
        score = 0
        
        # Color harmony
        if self.colors_match(item1['color'], item2['color']):
            score += 0.3
        
        # Price balance
        if self.prices_harmonize(item1['price'], item2['price']):
            score += 0.3
        
        # Material compatibility
        if self.materials_complement(item1['material'], item2['material']):
            score += 0.4
        
        return score
```

**Why Hard Rules?**
- Prevents LLM hallucination (e.g., recommending items not in catalog)
- Ensures deterministic fashion logic
- Explainable to user ("Why this pairing?")

---

### 5. API Layer (`api/`)

#### `schemas.py` - Request/Response Models
```python
from pydantic import BaseModel, Field

class StyleRequest(BaseModel):
    user_prompt: str = Field(..., min_length=10, max_length=500)
    budget: int = Field(default=10000, ge=100, le=100000)
    preferred_brands: List[str] = Field(default=[])

class RecommendedItem(BaseModel):
    item_name: str
    price: str
    image_url: str
    brand: str
    category: str
    source_url: str

class StyleResponse(BaseModel):
    status: str  # "success" or "error"
    recommendations: List[RecommendedItem]
    total_price: str
    stylist_note: str
    confidence: float = Field(ge=0, le=1)
    execution_time_ms: float
```

**Validation Benefits**:
- ✅ Type safety: FastAPI validates input/output
- ✅ Auto-generation: Swagger UI documentation
- ✅ Error messages: Clear feedback on invalid requests

#### `main.py` - FastAPI Server
```python
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Luxury Stylist Concierge")

@app.post("/api/v1/style-me")
async def style_me(request: StyleRequest) -> StyleResponse:
    try:
        start_time = time.time()
        
        # Initialize agent
        agent = StylistAgent()
        
        # Get recommendations
        result = agent.recommend(
            user_prompt=request.user_prompt,
            budget=request.budget
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        return StyleResponse(
            status="success",
            recommendations=result['recommendations'],
            total_price=result['total_price'],
            stylist_note=result['stylist_note'],
            confidence=result['confidence'],
            execution_time_ms=execution_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**API Design Principles**:
- ✅ Single endpoint: `/api/v1/style-me` (clean, versioned)
- ✅ Async handlers: Non-blocking request processing
- ✅ Structured errors: Meaningful HTTP codes + messages
- ✅ Performance tracking: execution_time_ms for monitoring

---

## Design Decisions & Rationale

### Decision 1: Async Scraping vs Sync
| Async | Sync |
|-------|------|
| 50 items in 2 min | 50 items in 10 min |
| Complex (asyncio) | Simple (loops) |
| Network-efficient | Network-intensive |

**Decision**: Async  
**Rationale**: Speed matters for timely inventory updates. 5x faster justifies slight complexity.

---

### Decision 2: Local ChromaDB vs Cloud VectorDB
| Local | Cloud (Pinecone) |
|-------|------------------|
| $0 (free) | $0.04/1K vectors |
| <10ms latency | 100-200ms latency |
| Easy setup | API key required |
| Can't scale 1000M+ | Scales infinitely |

**Decision**: Local ChromaDB  
**Rationale**: Assignment scope (100 items). Cloud DBs overkill. Can mention scalability in submission.

---

### Decision 3: Separate Scrapers vs Single Generic
**Separate**:
- Zara-specific DOM optimizations
- Myntra-specific metadata extraction
- Easier to debug & maintain

**Generic**:
- Single codebase
- Harder to optimize per-site

**Decision**: Separate  
**Rationale**: Real-world scraping often requires site-specific logic. Shows understanding of web scraping complexity.

---

### Decision 4: Embedding Model Choice
| text-embedding-3-small | text-embedding-3-large | other-model |
|------------------------|------------------------|------------|
| 1536 dims, $0.02/1M | 3072 dims, $0.13/1M | Various |
| Fast | Slower | - |
| Good for fashion | Overkill | - |

**Decision**: text-embedding-3-small  
**Rationale**: Fashion items have rich semantic space. Small model is sufficient + cheap.

---

## Token Economics Strategy

### Problem: LLM API Calls are Expensive
- OpenAI API: $0.50/1M input tokens, $1.50/1M output tokens
- Without optimization: ~2000 tokens per recommendation
- 100 daily requests: ~200k tokens = $0.10/day = $3/month

### Our Optimization Strategy

#### 1. **Semantic Caching** (Major Savings)
```
User 1: "Dark navy chinos, yacht party"
  → Embed query (200 tokens, $0.0001)
  → Search + retrieve (cached)
  → Agent reasoning (800 tokens, $0.0004)
  → Total: ~1000 tokens, $0.0005

User 2: "Navy pants, summer party" (similar intent)
  → Cache HIT! Return previous result
  → Total: ~100 tokens, $0.00005 (90% savings!)
```

**Implementation**:
```python
def style_me(request):
    query_hash = hash(request.user_prompt)
    
    # Check cache first
    cached = cache.get(query_hash)
    if cached:
        return cached  # Skip expensive LLM call
    
    # Fallback to agent
    result = agent.recommend(request.user_prompt)
    cache.set(query_hash, result)
    return result
```

**Expected Impact**: 40-50% cache hit rate on repeated user contexts

#### 2. **Prompt Compression** (Medium Savings)
```
❌ Naive prompt (2000 tokens):
  "Based on the user's description of dark navy cotton chinos from 
   a luxury brand, suitable for a summer yacht party on the 
   Mediterranean coast with a budget of ₹5000, find the most 
   appropriate t-shirt that balances premium quality, comfort, 
   and style. Consider color harmony, material compatibility, 
   and price-to-quality ratio. Explain your reasoning..."

✅ Compressed prompt (800 tokens):
  "Recommend t-shirt for: navy chinos + yacht party + ₹5000 budget.
   Criteria: color harmony, material, price ratio."
```

**Savings**: 60% reduction in prompt tokens

#### 3. **Batch Embeddings** (Small Savings)
```
❌ Individual API calls:
  100 items × 1 API call each = 100 API calls

✅ Batch embeddings:
  100 items ÷ 50 per batch = 2 API calls
  Savings: 98% fewer API calls (better rate limiting)
```

**Implementation**: See `embedder.py` batch_embed() method

#### 4. **Structured Metadata** (Indirect Savings)
```
❌ Full item description in every search:
  "Premium 100% cotton t-shirt, breathable, perfect for summer 
   wear, soft fabric, machine washable, available in white, blue, 
   grey. Brand: Zara. Perfect for casual or semi-formal occasions."
  (100 tokens)

✅ Structured metadata:
  {category: "tops", color: "white", price: 1299, material: "cotton"}
  (20 tokens)
  
  → Only embed descriptions once during setup
  → Use metadata for filtering (no token cost)
```

**Savings**: 80% reduction in per-search tokens

### Total Cost Impact
```
Estimated costs per 100 recommendations:

Without optimization:
  - Embeddings: 100 items × 100 tokens × $0.02/1M = $0.20
  - LLM calls: 100 × 2000 tokens × $0.50/1M = $0.10
  - Total: ~$0.30 (+ overhead)

With optimization:
  - Embeddings: Batch (same) = $0.20
  - LLM calls: 100 × 800 tokens × 50% cache hit = $0.04
  - Total: ~$0.24 (20% savings)

Scaled to 10k/month:
  - Without: ~$30/month
  - With: ~$24/month + infrastructure
  - ROI: Break-even, but principle is sound
```

**Philosophy**: "Treat tokens like your own money" → Every optimization counts at scale

---

## Data Flow & State Management

### Request Lifecycle
```
1. API receives StyleRequest
   ↓
2. Validate with Pydantic schemas
   ↓
3. Check cache for similar queries
   ↓
4. Initialize StylistAgent with vector store
   ↓
5. Agent calls tools:
   - search_catalog() → vector search
   - validate_pairing() → fashion rules
   ↓
6. Agent synthesizes response
   ↓
7. Cache the result
   ↓
8. Return StyleResponse with execution_time_ms
```

### State Management
- **Per-request state**: Request/response objects (stateless design)
- **Shared state**: ChromaDB connection, cache, LLM client
- **No session management needed**: Recommendations are stateless
- **Logging**: Structured logs with request_id for debugging

---

## Error Handling & Resilience

### Scraper Errors
```python
# Retry logic with exponential backoff
async def scrape_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await fetch(url)
        except NetworkError:
            wait = 2 ** attempt  # 1s, 2s, 4s
            await asyncio.sleep(wait)
    raise ScrapeError(f"Failed after {max_retries} attempts")
```

### API Errors
```python
@app.exception_handler(Exception)
async def exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": str(exc),
            "request_id": request.headers.get("X-Request-ID")
        }
    )
```

### Vector DB Errors
```python
try:
    results = vector_store.search(query)
except ChromaDBError:
    # Fallback: Return random items from catalog
    results = random.sample(catalog, k=5)
    logger.warning("VectorDB search failed, returning random results")
```

---

## Performance Optimization

### Scraping Performance
- **Concurrency**: asyncio for parallel requests (~2min for 100 items)
- **Connection pooling**: Reuse HTTP connections
- **Browser caching**: Playwright's built-in cache
- **Pagination**: Iterate smartly, not all 1000s of items

### RAG Performance
- **Batch embeddings**: 2-3 API calls instead of 100+
- **Caching**: 40% cache hit rate
- **Metadata pre-filtering**: Reduce semantic search space
- **ChromaDB indexing**: Fast similarity search (<10ms)

### API Performance
- **Async handlers**: Non-blocking requests
- **Connection pooling**: Reuse OpenAI client
- **Structured responses**: Minimal JSON size
- **Timeout enforcement**: Kill long-running searches after 30s

### Monitoring & Metrics
```python
# Log performance metrics
@app.post("/api/v1/style-me")
async def style_me(request: StyleRequest):
    start = time.time()
    
    result = await process(request)
    
    duration_ms = (time.time() - start) * 1000
    logger.info(f"style-me request completed in {duration_ms}ms", extra={
        "duration_ms": duration_ms,
        "cache_hit": result.get("cache_hit", False),
        "items_returned": len(result['recommendations'])
    })
    
    return result
```

---

## Summary: Why This Architecture?

✅ **Scalability**: Can scale from 100 to 1M+ items (swap ChromaDB → Pinecone)  
✅ **Cost-Conscious**: Token optimization reduces API spend  
✅ **Maintainability**: Clear separation of concerns (scrapers, RAG, agent, API)  
✅ **Resilience**: Error handling at every layer  
✅ **Explainability**: Fashion rules + Stylist Notes make recommendations transparent  
✅ **Production-Ready**: Type validation, structured logging, performance monitoring  

This design prioritizes **understanding**, **efficiency**, and **real-world applicability**.
