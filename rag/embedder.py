"""
Embedder Service - Uses ONNX-optimized sentence-transformers for local embeddings
Free, fast, and no API costs. Perfect for fashion item embeddings.
Model: all-MiniLM-L6-v2 (384 dimensions, very efficient)
"""

import json
import logging
import os
from typing import List, Dict
from tqdm import tqdm
import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbedderService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedder with ONNX-optimized sentence transformer
        Model: all-MiniLM-L6-v2 (384 dims, 22M params, super fast)
        """
        logger.info(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

        # Initialize ChromaDB
        logger.info("Initializing ChromaDB...")
        self.chromadb_client = chromadb.Client()

        logger.info(f"✅ Embedder ready. Model: {model_name}")

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Embed multiple texts efficiently in batches
        batch_size: number of texts to process at once
        """
        embeddings = []

        logger.info(f"Embedding {len(texts)} texts in batches of {batch_size}...")

        for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
            batch = texts[i : i + batch_size]
            batch_embeddings = self.model.encode(batch, convert_to_numpy=True)
            embeddings.extend(batch_embeddings)

        return embeddings

    def embed_catalog(self, catalog_path: str = "scrapers\\data\\catalog.json"):
        """
        Load catalog and embed all items
        Store embeddings and metadata in ChromaDB
        """
        logger.info("\n" + "=" * 60)
        logger.info("🚀 EMBEDDING CATALOG")
        logger.info("=" * 60)

        # Load catalog
        logger.info(f"Loading catalog from {catalog_path}...")
        with open(catalog_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        logger.info(f"✅ Loaded {len(items)} items")

        # Prepare texts for embedding
        logger.info("\nPreparing texts...")
        texts = []
        ids = []
        metadatas = []

        for item in items:
            # Create rich description for embedding
            text = f"{item['item_name']} {item['description']} {item.get('color', '')} {item.get('material', '')}"
            texts.append(text)

            # Store ID
            ids.append(item["id"])

            # Store metadata for filtering
            metadata = {
                "item_name": item["item_name"],
                "category": item["category"],
                "brand": item["brand"],
                "price": str(item["price"]),
                "source_url": item["source_url"],
                "image_url": item["image_url"],
            }
            metadatas.append(metadata)

        # Embed texts
        logger.info(f"\nEmbedding {len(texts)} items...")
        embeddings = self.embed_batch(texts, batch_size=32)

        # Create or get collection
        logger.info("\nCreating ChromaDB collection...")
        try:
            collection = self.chromadb_client.delete_collection(name="fashion_catalog")
            logger.info("Deleted existing collection")
        except:
            pass

        collection = self.chromadb_client.create_collection(
            name="fashion_catalog",
            metadata={"hnsw:space": "cosine"},
        )

        # Add to ChromaDB
        logger.info("\nAdding embeddings to ChromaDB...")
        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings,
            metadatas=metadatas,
        )

        logger.info("\n" + "=" * 60)
        logger.info(f"✅ EMBEDDING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"✓ {len(items)} items embedded")
        logger.info(f"✓ Model: {self.model_name}")
        logger.info(f"✓ Dimensions: {embeddings[0].shape if embeddings else 0}")
        logger.info(f"✓ Storage: ChromaDB (local)")
        logger.info("=" * 60 + "\n")

        return collection

    def get_collection(self):
        """Get the fashion catalog collection"""
        try:
            return self.chromadb_client.get_collection(name="fashion_catalog")
        except Exception as e:
            logger.error(f"Collection not found: {e}")
            logger.error("Run embed_catalog() first to create embeddings")
            return None


async def main():
    """Test embedder"""
    service = EmbedderService()

    # Embed catalog
    collection = service.embed_catalog()

    if collection:
        logger.info("\n✅ Embedder test successful!")
    else:
        logger.error("❌ Embedder test failed!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
