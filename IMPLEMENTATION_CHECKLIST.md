# Implementation Checklist

Use this checklist as you build the project. Check off each item as you complete it.

---

## 📋 Pre-Implementation Setup

- [ ] Create folder structure (`scrapers/`, `data/`, `rag/`, `agent/`, `api/`)
- [ ] Copy `.env.example` to `.env`
- [ ] Add your `OPENAI_API_KEY` to `.env`
- [ ] Run `pip install -r requirements.txt`
- [ ] Test imports:
  ```bash
  python -c "import playwright; import fastapi; import langchain; print('✅ All imports OK')"
  ```
- [ ] Initialize git repo (if not already):
  ```bash
  git init
  git add .
  git commit -m "Initial: project structure and documentation"
  ```

---

## 🕷️ Milestone 1: Web Scrapers

### Zara Scraper (`scrapers/zara_scraper.py`)

- [ ] Create empty file: `scrapers/zara_scraper.py`
- [ ] Import dependencies:
  ```python
  from playwright.async_api import async_playwright
  import asyncio
  import json
  from typing import List, Dict
  import random
  import time
  ```
- [ ] Define USER_AGENTS list (5 real browser signatures)
- [ ] Create `ZaraScraper` class with:
  - [ ] `__init__()` - Initialize Playwright
  - [ ] `async get_random_user_agent()` - Rotate user-agents
  - [ ] `async get_random_delay()` - Random 2-5s delay
  - [ ] `async fetch_with_retry(url, retries=3)` - Network retry logic
  - [ ] `async extract_items(page_url)` - Parse DOM and extract items
  - [ ] `async scrape()` - Main method

- [ ] Test Zara scraper:
  ```bash
  python -c "
  from scrapers.zara_scraper import ZaraScraper
  import asyncio
  result = asyncio.run(ZaraScraper().scrape())
  print(f'✅ Scraped {len(result)} items from Zara')
  "
  ```

- [ ] Verify output format:
  ```json
  [
    {
      "id": "zara-001",
      "item_name": "Premium Cotton T-Shirt",
      "price": "₹1,299",
      "image_url": "https://...",
      "category": "tops",
      "brand": "Zara",
      "description": "...",
      "source_url": "https://..."
    }
  ]
  ```

### Myntra Scraper (`scrapers/myntra_scraper.py`)

- [ ] Create empty file: `scrapers/myntra_scraper.py`
- [ ] Duplicate Zara scraper and adapt for Myntra:
  - [ ] Different base URLs (t-shirts, trousers pages)
  - [ ] Different DOM selectors (Myntra uses different HTML structure)
  - [ ] Same resilience features (delays, user-agents, retries)

- [ ] Test Myntra scraper:
  ```bash
  python -c "
  from scrapers.myntra_scraper import MyntraScraper
  import asyncio
  result = asyncio.run(MyntraScraper().scrape())
  print(f'✅ Scraped {len(result)} items from Myntra')
  "
  ```

### Orchestrator (`scrapers/run_scrapers.py`)

- [ ] Create file: `scrapers/run_scrapers.py`
- [ ] Implement:
  ```python
  async def main():
      # 1. Run both scrapers concurrently
      zara_items, myntra_items = await asyncio.gather(
          ZaraScraper().scrape(),
          MyntraScraper().scrape()
      )
      
      # 2. Merge items
      all_items = zara_items + myntra_items
      
      # 3. Deduplication by (item_name, brand)
      seen = set()
      deduplicated = []
      for item in all_items:
          key = (item['item_name'], item['brand'])
          if key not in seen:
              seen.add(key)
              deduplicated.append(item)
      
      # 4. Save to data/catalog.json
      with open('data/catalog.json', 'w') as f:
          json.dump(deduplicated, f, indent=2)
      
      print(f"✅ {len(deduplicated)} unique items saved to data/catalog.json")
  ```

- [ ] Test orchestrator:
  ```bash
  python scrapers/run_scrapers.py
  ```

- [ ] Verify output:
  - [ ] `data/catalog.json` exists
  - [ ] Contains 100+ items
  - [ ] At least 50 items have `category: "tops"`
  - [ ] At least 50 items have `category: "bottoms"`
  - [ ] All items have required fields

- [ ] Commit:
  ```bash
  git add scrapers/ data/catalog.json
  git commit -m "feat: Add async web scrapers for Zara and Myntra"
  ```

---

## 🔍 Milestone 2: RAG Pipeline

### Embedder Service (`rag/embedder.py`)

- [ ] Create file: `rag/embedder.py`
- [ ] Implement:
  ```python
  from openai import OpenAI
  import chromadb
  import json
  import os
  
  class EmbedderService:
      def __init__(self):
          self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
          self.chromadb_client = chromadb.Client()
          self.collection = None
      
      def embed_catalog(self):
          # 1. Load catalog
          with open('data/catalog.json', 'r') as f:
              items = json.load(f)
          
          # 2. Prepare texts for embedding
          texts = [item['description'] for item in items]
          
          # 3. Batch embed
          embeddings = self.batch_embed(texts, batch_size=50)
          
          # 4. Create ChromaDB collection
          self.collection = self.chromadb_client.get_or_create_collection(
              name="fashion_catalog"
          )
          
          # 5. Add to ChromaDB
          self.collection.add(
              ids=[item['id'] for item in items],
              documents=texts,
              embeddings=embeddings,
              metadatas=[
                  {
                      'category': item['category'],
                      'brand': item['brand'],
                      'price': float(item['price'].replace('₹', '').replace(',', '')),
                      'item_name': item['item_name']
                  }
                  for item in items
              ]
          )
          print(f"✅ Embedded {len(items)} items in ChromaDB")
      
      def batch_embed(self, texts, batch_size=50):
          embeddings = []
          for i in range(0, len(texts), batch_size):
              batch = texts[i:i+batch_size]
              response = self.client.embeddings.create(
                  input=batch,
                  model="text-embedding-3-small"
              )
              embeddings.extend([r.embedding for r in response.data])
          return embeddings
  ```

- [ ] Test embedder:
  ```bash
  python -c "
  from rag.embedder import EmbedderService
  service = EmbedderService()
  service.embed_catalog()
  "
  ```

- [ ] Verify: ChromaDB collection created with 100+ items

### Vector Store (`rag/vector_store.py`)

- [ ] Create file: `rag/vector_store.py`
- [ ] Implement:
  ```python
  import chromadb
  import json
  from openai import OpenAI
  import os
  
  class VectorStore:
      def __init__(self):
          self.chromadb_client = chromadb.Client()
          self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
          self.collection = self.chromadb_client.get_collection("fashion_catalog")
          
          # Load catalog for enrichment
          with open('data/catalog.json', 'r') as f:
              self.catalog = {item['id']: item for item in json.load(f)}
      
      def search(self, query, filters=None, top_k=5):
          # 1. Embed query
          response = self.openai_client.embeddings.create(
              input=query,
              model="text-embedding-3-small"
          )
          query_embedding = response.data[0].embedding
          
          # 2. Search ChromaDB
          results = self.collection.query(
              query_embeddings=[query_embedding],
              n_results=top_k,
              where=self.build_where(filters) if filters else None
          )
          
          # 3. Hydrate with full item data
          items = []
          for item_id in results['ids'][0]:
              items.append(self.catalog[item_id])
          
          return items
      
      def build_where(self, filters):
          where = {}
          if filters.get('category'):
              where['category'] = {'$eq': filters['category']}
          if filters.get('max_price'):
              where['price'] = {'$lte': filters['max_price']}
          if filters.get('brand'):
              where['brand'] = {'$eq': filters['brand']}
          return where
  ```

- [ ] Test vector store:
  ```bash
  python -c "
  from rag.vector_store import VectorStore
  vs = VectorStore()
  results = vs.search('white t-shirt for summer', {'category': 'tops'}, top_k=5)
  print(f'✅ Found {len(results)} matching items')
  for item in results:
      print(f\"  - {item['item_name']} ({item['brand']})\")
  "
  ```

### Cache Layer (`rag/cache.py`)

- [ ] Create file: `rag/cache.py`
- [ ] Implement:
  ```python
  import time
  import hashlib
  
  class QueryCache:
      def __init__(self, ttl_hours=1):
          self.cache = {}
          self.ttl = ttl_hours * 3600
      
      def get_key(self, query, filters):
          content = f"{query}_{str(filters)}"
          return hashlib.md5(content.encode()).hexdigest()
      
      def get(self, query, filters):
          key = self.get_key(query, filters)
          if key in self.cache:
              entry = self.cache[key]
              if time.time() - entry['created_at'] < self.ttl:
                  return entry['results']
          return None
      
      def set(self, query, filters, results):
          key = self.get_key(query, filters)
          self.cache[key] = {
              'results': results,
              'created_at': time.time()
          }
  ```

- [ ] Test cache:
  ```bash
  python -c "
  from rag.cache import QueryCache
  cache = QueryCache()
  
  # Set
  cache.set('test query', {}, ['item1', 'item2'])
  
  # Get (should hit)
  result = cache.get('test query', {})
  print(f'✅ Cache hit: {result}')
  
  # Get different query (should miss)
  result = cache.get('different query', {})
  print(f'✅ Cache miss: {result}')
  "
  ```

- [ ] Commit:
  ```bash
  git add rag/
  git commit -m "feat: Add RAG pipeline (embeddings, vector search, caching)"
  ```

---

## 🤖 Milestone 3: AI Agent

### Fashion Rules (`agent/fashion_rules.py`)

- [ ] Create file: `agent/fashion_rules.py`
- [ ] Implement:
  ```python
  class FashionRules:
      COLOR_PAIRS = {
          'white': ['navy', 'black', 'grey', 'beige'],
          'navy': ['white', 'cream', 'light_blue'],
          'black': ['white', 'red', 'gold'],
          'grey': ['white', 'navy', 'black'],
          # ... add more
      }
      
      OCCASION_REQUIREMENTS = {
          'yacht_party': {
              'style': 'premium',
              'colors': ['white', 'navy', 'cream'],
              'fit': 'fitted'
          },
          'office': {
              'style': 'formal',
              'colors': ['white', 'navy', 'grey'],
              'fit': 'structured'
          },
          'casual': {
              'style': 'relaxed',
              'colors': ['any'],
              'fit': 'comfortable'
          }
      }
      
      def validate_pairing(self, item1, item2):
          score = 0.0
          
          # Color harmony (30 points)
          if self.colors_match(item1.get('color'), item2.get('color')):
              score += 0.3
          
          # Price ratio (30 points)
          if self.prices_harmonize(item1.get('price'), item2.get('price')):
              score += 0.3
          
          # Material compatibility (20 points)
          if self.materials_work(item1.get('material'), item2.get('material')):
              score += 0.2
          
          # Category check (20 points) - must be different
          if item1.get('category') != item2.get('category'):
              score += 0.2
          
          return min(score, 1.0)
      
      def colors_match(self, color1, color2):
          # Check if colors complement each other
          if not color1 or not color2:
              return True  # Unknown colors are OK
          
          color1_lower = color1.lower()
          if color1_lower in self.COLOR_PAIRS:
              return color2.lower() in self.COLOR_PAIRS[color1_lower]
          
          return True  # Unknown colors are OK
      
      def prices_harmonize(self, price1, price2):
          # Extract numeric values
          try:
              p1 = float(str(price1).replace('₹', '').replace(',', ''))
              p2 = float(str(price2).replace('₹', '').replace(',', ''))
              
              ratio = max(p1, p2) / min(p1, p2) if min(p1, p2) > 0 else 1
              
              # Acceptable ratio: 0.5 to 2.0
              return 0.5 <= ratio <= 2.0
          except:
              return True
      
      def materials_work(self, mat1, mat2):
          # Simple check: common materials work together
          if not mat1 or not mat2:
              return True
          return True  # Most materials work together
  ```

- [ ] Test fashion rules:
  ```bash
  python -c "
  from agent.fashion_rules import FashionRules
  rules = FashionRules()
  
  item1 = {'color': 'white', 'price': '₹1,299', 'material': 'cotton', 'category': 'tops'}
  item2 = {'color': 'navy', 'price': '₹3,999', 'material': 'cotton', 'category': 'bottoms'}
  
  score = rules.validate_pairing(item1, item2)
  print(f'✅ Pairing score: {score:.2f}')
  "
  ```

### Stylist Agent (`agent/stylist_agent.py`)

- [ ] Create file: `agent/stylist_agent.py`
- [ ] Implement:
  ```python
  from langchain.agents import initialize_agent, Tool
  from langchain_openai import ChatOpenAI
  from langchain.schema import HumanMessage
  from rag.vector_store import VectorStore
  from agent.fashion_rules import FashionRules
  import os
  
  class StylistAgent:
      def __init__(self):
          self.llm = ChatOpenAI(
              model="gpt-3.5-turbo",
              temperature=0.7,
              api_key=os.getenv("OPENAI_API_KEY")
          )
          self.vector_store = VectorStore()
          self.fashion_rules = FashionRules()
      
      def recommend(self, user_prompt, budget=10000):
          # 1. Search for matching tops
          tops = self.vector_store.search(
              f"tops for {user_prompt}",
              {'category': 'tops', 'max_price': budget}
          )
          
          # 2. Search for matching bottoms
          bottoms = self.vector_store.search(
              f"bottoms for {user_prompt}",
              {'category': 'bottoms', 'max_price': budget}
          )
          
          # 3. Find best pairing
          best_pairing = None
          best_score = 0
          
          for top in tops[:3]:  # Check top-3 results
              for bottom in bottoms[:3]:
                  score = self.fashion_rules.validate_pairing(top, bottom)
                  if score > best_score:
                      best_score = score
                      best_pairing = (top, bottom)
          
          if not best_pairing:
              best_pairing = (tops[0], bottoms[0]) if tops and bottoms else None
          
          if not best_pairing:
              return {
                  'status': 'error',
                  'message': 'No matching items found'
              }
          
          top, bottom = best_pairing
          
          # 4. Generate stylist note
          note = self._generate_note(top, bottom, user_prompt)
          
          # 5. Calculate confidence
          confidence = min(best_score + 0.1, 1.0)  # Boost with base confidence
          
          # 6. Calculate total price
          total_price = self._calculate_total_price(top, bottom)
          
          return {
              'recommendations': [top, bottom],
              'total_price': total_price,
              'stylist_note': note,
              'confidence': confidence
          }
      
      def _generate_note(self, top, bottom, context):
          # Simple rule-based note generation
          notes = [
              f"The {top['item_name']} in {top.get('color', 'this color')} ",
              f"perfectly complements your {bottom['item_name']}. ",
              f"Premium {top.get('material', 'fabric')} creates a luxurious pairing. ",
              f"This combination exudes elegance and sophistication."
          ]
          return "".join(notes)
      
      def _calculate_total_price(self, top, bottom):
          try:
              p1 = float(str(top['price']).replace('₹', '').replace(',', ''))
              p2 = float(str(bottom['price']).replace('₹', '').replace(',', ''))
              total = p1 + p2
              return f"₹{total:,.0f}"
          except:
              return "Price unavailable"
  ```

- [ ] Test agent:
  ```bash
  python -c "
  from agent.stylist_agent import StylistAgent
  agent = StylistAgent()
  
  result = agent.recommend('Dark navy chinos, yacht party', budget=5000)
  print(f'✅ Recommendations: {len(result[\"recommendations\"])} items')
  print(f\"   - {result['recommendations'][0]['item_name']}\")
  print(f\"   - {result['recommendations'][1]['item_name']}\")
  print(f'   Confidence: {result[\"confidence\"]:.2f}')
  "
  ```

- [ ] Commit:
  ```bash
  git add agent/
  git commit -m "feat: Add AI agent with fashion rules and recommendations"
  ```

---

## ⚡ Milestone 4: FastAPI Server

### Pydantic Schemas (`api/schemas.py`)

- [ ] Create file: `api/schemas.py`
- [ ] Implement:
  ```python
  from pydantic import BaseModel, Field
  from typing import List, Optional
  
  class StyleRequest(BaseModel):
      user_prompt: str = Field(..., min_length=10, max_length=500)
      budget: int = Field(default=10000, ge=100, le=100000)
      preferred_brands: List[str] = Field(default=[])
  
  class RecommendedItem(BaseModel):
      id: str
      item_name: str
      price: str
      image_url: str
      brand: str
      category: str
      source_url: str
  
  class StyleResponse(BaseModel):
      status: str
      recommendations: List[RecommendedItem]
      total_price: str
      stylist_note: str
      confidence: float = Field(ge=0, le=1)
      execution_time_ms: float
  ```

- [ ] Test schemas:
  ```bash
  python -c "
  from api.schemas import StyleRequest, StyleResponse
  
  req = StyleRequest(user_prompt='I need a white shirt for office')
  print(f'✅ Request validated')
  "
  ```

### FastAPI Server (`api/main.py`)

- [ ] Create file: `api/main.py`
- [ ] Implement:
  ```python
  from fastapi import FastAPI, HTTPException
  from api.schemas import StyleRequest, StyleResponse, RecommendedItem
  from agent.stylist_agent import StylistAgent
  import time
  import uvicorn
  
  app = FastAPI(
      title="Luxury Stylist Concierge",
      description="AI-powered fashion recommendation engine"
  )
  
  @app.post("/api/v1/style-me", response_model=StyleResponse)
  async def style_me(request: StyleRequest) -> StyleResponse:
      start_time = time.time()
      
      try:
          agent = StylistAgent()
          result = agent.recommend(request.user_prompt, request.budget)
          
          if result.get('status') == 'error':
              raise HTTPException(status_code=400, detail=result['message'])
          
          recommendations = [
              RecommendedItem(
                  id=item['id'],
                  item_name=item['item_name'],
                  price=item['price'],
                  image_url=item['image_url'],
                  brand=item['brand'],
                  category=item['category'],
                  source_url=item['source_url']
              )
              for item in result['recommendations']
          ]
          
          execution_time = (time.time() - start_time) * 1000
          
          return StyleResponse(
              status="success",
              recommendations=recommendations,
              total_price=result['total_price'],
              stylist_note=result['stylist_note'],
              confidence=result['confidence'],
              execution_time_ms=execution_time
          )
      except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
  
  @app.get("/health")
  async def health_check():
      return {"status": "healthy"}
  
  if __name__ == "__main__":
      uvicorn.run(app, host="0.0.0.0", port=8000)
  ```

- [ ] Test server:
  ```bash
  python api/main.py
  # Should output: "Uvicorn running on http://0.0.0.0:8000"
  ```

- [ ] Test endpoint (in another terminal):
  ```bash
  curl -X POST "http://localhost:8000/api/v1/style-me" \
    -H "Content-Type: application/json" \
    -d '{
      "user_prompt": "Dark navy chinos, yacht party",
      "budget": 5000
    }'
  ```

- [ ] Visit Swagger UI: http://localhost:8000/docs

- [ ] Commit:
  ```bash
  git add api/
  git commit -m "feat: Add FastAPI server with /api/v1/style-me endpoint"
  ```

---

## 📸 Final Steps

### Testing & Validation

- [ ] All files exist and have no syntax errors
- [ ] Catalog has 100+ items (check `data/catalog.json`)
- [ ] API server starts without errors
- [ ] POST /api/v1/style-me returns valid response
- [ ] Response execution_time_ms is logged
- [ ] Error handling works (test with invalid input)

### Git Commit

- [ ] Final commit:
  ```bash
  git add .
  git commit -m "feat: Complete Luxury Stylist Concierge implementation"
  git log --oneline  # Verify clean history
  ```

### Demo & Screen Recording

- [ ] Record screen showing:
  1. Terminal: `python scrapers/run_scrapers.py` (shows scraped items)
  2. Terminal: `python api/main.py` (server starts)
  3. Browser: `http://localhost:8000/docs` (Swagger UI)
  4. Swagger: POST request with example prompt
  5. Browser: Response JSON with recommendations
  6. Terminal: Logs showing agent reasoning

- [ ] Save recording (Google Drive, YouTube unlisted, etc.)
- [ ] Get shareable link

### GitHub Push

- [ ] Create GitHub repository (public)
- [ ] Add `.gitignore`:
  ```
  .env
  __pycache__/
  *.pyc
  .venv/
  chromadb_data/
  *.log
  ```
- [ ] Push code:
  ```bash
  git remote add origin https://github.com/your-username/luxury-stylist.git
  git branch -M main
  git push -u origin main
  ```

### Final Submission

- [ ] Email to: mehtesham@quickeee.com
- [ ] Subject: "Gen AI & Data Engineer Assignment - Luxury Stylist Concierge"
- [ ] Body:
  ```
  Hi Ehtesham,
  
  I've completed the Luxury Stylist Concierge assignment.
  
  GitHub Repository: https://github.com/your-username/luxury-stylist
  Demo Recording: [link to recorded video]
  
  The implementation includes:
  - Async web scrapers for Zara & Myntra (100+ items)
  - RAG pipeline with ChromaDB and semantic search
  - LangChain AI agent with fashion rules
  - FastAPI server with /api/v1/style-me endpoint
  - Token-optimized prompt design
  - Complete documentation (README, ARCHITECTURE, PHASE1)
  
  Looking forward to your feedback!
  
  Best regards,
  [Your Name]
  ```

---

## ✅ Success Checklist

- [ ] 100+ items in `data/catalog.json`
- [ ] All files implemented (no placeholders)
- [ ] All imports work without errors
- [ ] API server runs and responds to requests
- [ ] Swagger UI loads
- [ ] Recommendations are non-hallucinated
- [ ] Confidence scores are reasonable (0.7+)
- [ ] Total price is calculated correctly
- [ ] Stylist Note explains the pairing
- [ ] Execution time logged
- [ ] Documentation complete (README, ARCHITECTURE, PHASE1)
- [ ] GitHub repo created and code pushed
- [ ] Screen recording created
- [ ] Email submitted

---

**You're almost there! Keep pushing! 💪✨**
