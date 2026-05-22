"""
Vector Store with Hybrid Search
Combines BM25 (keyword-based) + Semantic (neural) search
BM25: Fast, keyword-aware matching
Semantic: Understanding meaning and context
Hybrid: Best of both worlds!
"""

import json
import logging
import numpy as np
from typing import List, Dict, Optional
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import chromadb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize vector store with hybrid search"""
        logger.info("Initializing Vector Store with Hybrid Search...")

        # Load embedding model
        self.model = SentenceTransformer(model_name)

        # Initialize ChromaDB
        self.chromadb_client = chromadb.Client()

        # Load catalog for BM25 and enrichment
        logger.info("Loading catalog...")
        with open("scrapers\\data\\catalog.json", "r", encoding="utf-8") as f:
            self.catalog = json.load(f)
            self.catalog_dict = {item["id"]: item for item in self.catalog}

        # Initialize BM25
        logger.info("Building BM25 index...")
        self.bm25_corpus = []
        self.bm25_ids = []

        for item in self.catalog:
            # Create BM25 document
            text = f"{item['item_name']} {item['description']} {item.get('color', '')} {item['brand']}".lower()
            tokens = text.split()
            self.bm25_corpus.append(tokens)
            self.bm25_ids.append(item["id"])

        self.bm25 = BM25Okapi(self.bm25_corpus)

        # Get ChromaDB collection
        try:
            self.collection = self.chromadb_client.get_collection(name="fashion_catalog")
            logger.info("✅ ChromaDB collection loaded")
        except Exception as e:
            logger.error(f"ChromaDB collection not found: {e}")
            logger.error("Run embedder.embed_catalog() first")
            self.collection = None

        logger.info("✅ Vector Store ready for hybrid search\n")

    def search_bm25(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        BM25 keyword-based search
        Fast, good for exact term matching
        """
        # Tokenize query
        tokens = query.lower().split()

        # BM25 score
        scores = self.bm25.get_scores(tokens)

        # Get top-k
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include if score > 0
                item_id = self.bm25_ids[idx]
                item = self.catalog_dict.get(item_id)
                if item:
                    results.append({**item, "_score": float(scores[idx]), "_method": "bm25"})

        return results

    def search_semantic(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Semantic (neural) search using embeddings
        Good for understanding meaning and context
        """
        if not self.collection:
            logger.error("ChromaDB collection not available")
            return []

        try:
            # Embed query
            query_embedding = self.model.encode(query, convert_to_numpy=True)

            # Search ChromaDB
            results_data = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                include=["distances", "metadatas", "documents"]
            )

            # Convert distances to similarity scores (1 - distance for cosine)
            results = []
            if results_data["ids"] and len(results_data["ids"]) > 0:
                for i, item_id in enumerate(results_data["ids"][0]):
                    distance = results_data["distances"][0][i]
                    similarity = 1 - distance  # Convert distance to similarity

                    if similarity > 0.3:  # Threshold
                        item = self.catalog_dict.get(item_id)
                        if item:
                            results.append({
                                **item,
                                "_score": float(similarity),
                                "_method": "semantic"
                            })

            return results

        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []

    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        bm25_weight: float = 0.4,
        semantic_weight: float = 0.6,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Hybrid search combining BM25 and Semantic
        Weights: BM25 (0.4) + Semantic (0.6) for balanced results

        Args:
            query: Search query
            top_k: Number of results to return
            bm25_weight: Weight for BM25 score (0-1)
            semantic_weight: Weight for semantic score (0-1)
            filters: Optional filters (category, price_range, brand)

        Returns:
            List of ranked items
        """
        # Get results from both methods
        bm25_results = self.search_bm25(query, top_k=top_k * 2)  # Get more for hybrid merging
        semantic_results = self.search_semantic(query, top_k=top_k * 2)

        # Normalize scores
        bm25_max = max([r["_score"] for r in bm25_results], default=1.0)
        semantic_max = max([r["_score"] for r in semantic_results], default=1.0)

        if bm25_max > 0:
            for r in bm25_results:
                r["_score"] = r["_score"] / bm25_max

        if semantic_max > 0:
            for r in semantic_results:
                r["_score"] = r["_score"] / semantic_max

        # Merge results by ID
        merged = {}
        for result in bm25_results:
            merged[result["id"]] = {
                **result,
                "_bm25_score": result["_score"],
                "_semantic_score": 0,
                "_hybrid_score": 0
            }

        for result in semantic_results:
            if result["id"] in merged:
                merged[result["id"]]["_semantic_score"] = result["_score"]
            else:
                merged[result["id"]] = {
                    **result,
                    "_bm25_score": 0,
                    "_semantic_score": result["_score"],
                    "_hybrid_score": 0
                }

        # Calculate hybrid score
        for item_id in merged:
            bm25_score = merged[item_id].get("_bm25_score", 0)
            semantic_score = merged[item_id].get("_semantic_score", 0)
            hybrid = (bm25_weight * bm25_score) + (semantic_weight * semantic_score)
            merged[item_id]["_hybrid_score"] = hybrid

        # Apply filters
        if filters:
            merged = self._apply_filters(merged, filters)

        # Sort by hybrid score
        sorted_results = sorted(
            merged.values(),
            key=lambda x: x["_hybrid_score"],
            reverse=True
        )[:top_k]

        return sorted_results

    def _apply_filters(self, items_dict: Dict, filters: Dict) -> Dict:
        """Apply category, price, brand filters"""
        filtered = {}

        for item_id, item in items_dict.items():
            keep = True

            # Category filter
            if "category" in filters:
                if item.get("category") != filters["category"]:
                    keep = False

            # Price filter
            if "max_price" in filters and keep:
                try:
                    price_str = item.get("price", "₹0").replace("₹", "").replace(",", "")
                    price = float(price_str)
                    if price > filters["max_price"]:
                        keep = False
                except:
                    pass

            # Brand filter
            if "brand" in filters and keep:
                if item.get("brand") != filters["brand"]:
                    keep = False

            if keep:
                filtered[item_id] = item

        return filtered

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None,
        method: str = "hybrid"
    ) -> List[Dict]:
        """
        Main search method
        Supports: 'bm25', 'semantic', 'hybrid'
        """
        logger.info(f"🔍 Searching ({method}): '{query}'")

        if method == "bm25":
            results = self.search_bm25(query, top_k)
        elif method == "semantic":
            results = self.search_semantic(query, top_k)
        else:  # hybrid (default)
            results = self.hybrid_search(query, top_k, filters=filters)

        # Apply filters if using non-hybrid methods
        if method != "hybrid" and filters:
            results = self._apply_filters({r["id"]: r for r in results}, filters)
            results = list(results.values())

        logger.info(f"✅ Found {len(results)} results")

        return results[:top_k]


async def test_hybrid_search():
    """Test hybrid search"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 TESTING HYBRID SEARCH")
    logger.info("=" * 60 + "\n")

    vs = VectorStore()

    # Test 1: Simple semantic search
    logger.info("Test 1: Semantic search for 'white t-shirt'")
    results = vs.search("white t-shirt", top_k=3, method="semantic")
    for i, r in enumerate(results, 1):
        logger.info(f"  {i}. {r['item_name']} - {r['price']} ({r['brand']})")

    # Test 2: BM25 search
    logger.info("\nTest 2: BM25 search for 'premium cotton'")
    results = vs.search("premium cotton", top_k=3, method="bm25")
    for i, r in enumerate(results, 1):
        logger.info(f"  {i}. {r['item_name']} - {r['price']} ({r['brand']})")

    # Test 3: Hybrid search
    logger.info("\nTest 3: Hybrid search for 'casual wear'")
    results = vs.search("casual wear", top_k=5, method="hybrid")
    for i, r in enumerate(results, 1):
        logger.info(
            f"  {i}. {r['item_name']} - {r['price']} "
            f"(score: {r.get('_hybrid_score', 0):.3f})"
        )

    # Test 4: Filtered search
    logger.info("\nTest 4: Filtered hybrid search (tops, <₹2000)")
    results = vs.search(
        "t-shirt for office",
        top_k=5,
        filters={"category": "tops", "max_price": 2000},
        method="hybrid"
    )
    for i, r in enumerate(results, 1):
        logger.info(
            f"  {i}. {r['item_name']} - {r['price']} "
            f"(score: {r.get('_hybrid_score', 0):.3f})"
        )

    logger.info("\n" + "=" * 60)
    logger.info("✅ TESTS COMPLETE")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_hybrid_search())
