import asyncio
import json
import logging
import sys
from pathlib import Path

try:
    from .zara_scraper import ZaraScraper
    from .myntra_scraper import MyntraScraper
except ImportError:
    # Support running as script
    from zara_scraper import ZaraScraper
    from myntra_scraper import MyntraScraper

try:
    from playwright_stealth import Stealth  # noqa: F401
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("⚠️  playwright-stealth not installed, continuing without stealth")


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def run_all_scrapers():
    """Run both Zara and Myntra scrapers concurrently - REAL DATA ONLY"""
    logger.info("=" * 70)
    logger.info("LUXURY STYLIST CONCIERGE - DATA PIPELINE (REAL DATA)")
    logger.info("=" * 70)

    try:
        # Run both scrapers concurrently
        logger.info("\n📊 Starting concurrent scraping from Zara and Myntra...")
        zara_items, myntra_items = await asyncio.gather(
            ZaraScraper().scrape(),
            MyntraScraper().scrape(),
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(zara_items, Exception):
            logger.error(f"Zara scraper error: {zara_items}")
            zara_items = []
        else:
            logger.info(f"✓ Zara items scraped: {len(zara_items)}")

        if isinstance(myntra_items, Exception):
            logger.error(f"Myntra scraper error: {myntra_items}")
            myntra_items = []
        else:
            logger.info(f"✓ Myntra items scraped: {len(myntra_items)}")

        # Merge items
        all_items = zara_items + myntra_items
        logger.info(f"\n📦 Total items before deduplication: {len(all_items)}")

        # Deduplication by (item_name, brand)
        seen = {}
        deduplicated = []

        for item in all_items:
            key = (item['item_name'].lower(), item['brand'].lower())

            if key not in seen:
                seen[key] = True
                deduplicated.append(item)
            else:
                logger.debug(f"Skipping duplicate: {item['item_name']} by {item['brand']}")

        logger.info(f"✓ Deduplicated items: {len(deduplicated)}")

        # Count by category
        tops_count = sum(1 for item in deduplicated if item['category'] == 'tops')
        bottoms_count = sum(1 for item in deduplicated if item['category'] == 'bottoms')

        logger.info(f"\n📊 Category breakdown:")
        logger.info(f"  - Tops: {tops_count}")
        logger.info(f"  - Bottoms: {bottoms_count}")

        # Validate minimum requirements
        if len(deduplicated) < 100:
            logger.warning(f"⚠️  WARNING: Only {len(deduplicated)} items (target: 100+)")
        if tops_count < 50:
            logger.warning(f"⚠️  WARNING: Only {tops_count} tops (target: 50+)")
        if bottoms_count < 50:
            logger.warning(f"⚠️  WARNING: Only {bottoms_count} bottoms (target: 50+)")

        # Ensure data/catalog.json directory exists
        # WITH:
        BASE_DIR = Path(__file__).parent  # always points to the scrapers/ folder
        catalog_path = BASE_DIR / "data" / "catalog.json"
        catalog_path.parent.mkdir(parents=True, exist_ok=True)


        # Save to catalog.json - REAL DATA ONLY
        with open(catalog_path, 'w', encoding='utf-8') as f:
            json.dump(deduplicated, f, indent=2, ensure_ascii=False)

        logger.info(f"\n✅ Successfully saved {len(deduplicated)} REAL items to {catalog_path}")

        # Show sample items
        if deduplicated:
            logger.info("\n📋 Sample items from catalog:")
            for item in deduplicated[:5]:
                logger.info(f"  • {item['item_name']} by {item['brand']} - {item['price']} ({item['category']})")

        return deduplicated

    except Exception as e:
        logger.error(f"❌ Pipeline error: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


async def main():
    """Main entry point - ONLY REAL DATA"""
    scraped_items = await run_all_scrapers()

    logger.info("\n" + "=" * 70)
    if scraped_items:
        logger.info(f"✅ DATA PIPELINE COMPLETE - {len(scraped_items)} REAL ITEMS SCRAPED")
    else:
        logger.warning("⚠️  No items were scraped. Check logs for errors and try again.")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
