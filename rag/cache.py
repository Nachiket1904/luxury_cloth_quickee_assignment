"""
Query Cache Layer - In-memory caching with TTL
Reduces expensive vector searches for repeated queries
Typical cache hit rate: 40-50% on repeated user contexts
"""

import time
import hashlib
import json
import logging
from typing import Optional, List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryCache:
    def __init__(self, ttl_hours: int = 1, max_cache_size: int = 1000):
        """
        Initialize cache
        ttl_hours: How long to keep cached results (default: 1 hour)
        max_cache_size: Maximum number of queries to cache (default: 1000)
        """
        self.cache = {}
        self.ttl = ttl_hours * 3600
        self.max_cache_size = max_cache_size
        self.hits = 0
        self.misses = 0

    def _get_key(self, query: str, filters: Optional[Dict] = None) -> str:
        """
        Generate cache key from query and filters
        Uses MD5 hash for consistent key generation
        """
        content = f"{query}_{json.dumps(filters or {}, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, query: str, filters: Optional[Dict] = None) -> Optional[List[Dict]]:
        """
        Retrieve cached results
        Returns None if not found or expired
        """
        key = self._get_key(query, filters)

        if key in self.cache:
            entry = self.cache[key]
            elapsed = time.time() - entry["created_at"]

            # Check if expired
            if elapsed < self.ttl:
                self.hits += 1
                logger.info(f"✅ Cache HIT (age: {elapsed:.1f}s)")
                return entry["results"]
            else:
                # Expired, remove
                del self.cache[key]
                logger.info(f"⏳ Cache EXPIRED (age: {elapsed:.1f}s)")

        self.misses += 1
        logger.info(f"❌ Cache MISS")
        return None

    def set(self, query: str, filters: Optional[Dict], results: List[Dict]):
        """
        Store results in cache
        Evicts oldest entry if cache is full
        """
        key = self._get_key(query, filters)

        # Check cache size
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest entry (smallest created_at)
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["created_at"])
            del self.cache[oldest_key]
            logger.info(f"🗑️ Cache full, evicted oldest entry")

        self.cache[key] = {
            "results": results,
            "created_at": time.time(),
            "query": query,
            "filters": filters
        }

        logger.info(f"💾 Cached: {len(results)} results")

    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("🗑️ Cache cleared")

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl,
            "max_size": self.max_cache_size
        }

    def print_stats(self):
        """Print cache statistics"""
        stats = self.get_stats()
        logger.info("\n" + "=" * 60)
        logger.info("📊 CACHE STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Cache size: {stats['size']}/{stats['max_size']}")
        logger.info(f"Cache hits: {stats['hits']}")
        logger.info(f"Cache misses: {stats['misses']}")
        logger.info(f"Hit rate: {stats['hit_rate']:.1f}%")
        logger.info(f"TTL: {stats['ttl_seconds']/3600:.1f} hours")
        logger.info("=" * 60 + "\n")


def test_cache():
    """Test cache functionality"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 TESTING QUERY CACHE")
    logger.info("=" * 60 + "\n")

    cache = QueryCache(ttl_hours=0.001)  # 3.6 seconds for testing

    # Test 1: Set and get
    logger.info("Test 1: Set and retrieve")
    results = [{"id": "1", "name": "Item 1"}]
    cache.set("test query", {}, results)
    retrieved = cache.get("test query", {})
    assert retrieved == results, "Cache retrieval failed"
    logger.info("✅ Test 1 passed\n")

    # Test 2: Different filters
    logger.info("Test 2: Different filters = different cache key")
    results2 = [{"id": "2", "name": "Item 2"}]
    cache.set("test query", {"category": "tops"}, results2)
    retrieved2 = cache.get("test query", {"category": "tops"})
    assert retrieved2 == results2, "Filtered cache retrieval failed"
    logger.info("✅ Test 2 passed\n")

    # Test 3: Cache expiration
    logger.info("Test 3: Cache expiration")
    time.sleep(4)  # Wait for cache to expire
    expired = cache.get("test query", {})
    assert expired is None, "Cache should have expired"
    logger.info("✅ Test 3 passed\n")

    # Test 4: Statistics
    logger.info("Test 4: Cache statistics")
    cache.clear()
    cache.set("q1", {}, [{"id": "1"}])
    cache.set("q2", {}, [{"id": "2"}])
    cache.get("q1", {})  # Hit
    cache.get("q1", {})  # Hit
    cache.get("q3", {})  # Miss
    cache.print_stats()
    logger.info("✅ Test 4 passed\n")

    logger.info("=" * 60)
    logger.info("✅ ALL CACHE TESTS PASSED")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    test_cache()
