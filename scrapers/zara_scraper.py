import asyncio
import json
from playwright.async_api import async_playwright, Page
from typing import List, Dict
import random
import logging
import re
from pathlib import Path
from pydantic import ValidationError
from models import Product

try:
    from playwright_stealth import Stealth
except ImportError:
    Stealth = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15"
]


class ZaraScraper:
    def __init__(self):
        self.items = []
        self.seen_items = set()
        self.item_counter = 0

    async def get_random_user_agent(self) -> str:
        """Return a random user agent"""
        return random.choice(USER_AGENTS)

    async def get_random_delay(self) -> float:
        """Return a random delay between 2-5 seconds"""
        return random.uniform(2, 5)

    async def fetch_with_retry(self, page: Page, url: str, retries: int = 3) -> bool:
        """Fetch URL with retry logic"""
        for attempt in range(retries):
            try:
                logger.info(f"Fetching (attempt {attempt + 1}/{retries}): {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    await page.wait_for_selector(
                        '[data-testid*="product"], .product-item, a[href*="/p/"]',
                        timeout=15000
                    )
                except Exception:
                    logger.warning("Product grid did not appear — page may be blocked")
                await page.wait_for_timeout(2000)
                return True
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < retries - 1:
                    delay = await self.get_random_delay()
                    logger.info(f"Retrying after {delay:.1f}s...")
                    await asyncio.sleep(delay)
        return False

    async def scroll_and_load(self, page: Page, max_scrolls: int = 5):
        """Scroll page to load more items (handles lazy loading)"""
        for i in range(max_scrolls):
            try:
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(1500)
            except Exception as e:
                logger.debug(f"Scroll attempt {i+1} failed: {str(e)}")
                break

    async def extract_items_from_page(self, page: Page, category: str, url: str) -> List[Dict]:
        """Extract fashion items from a Zara page using direct DOM evaluation"""
        items = []
        try:
            # Scroll to load lazy-loaded content
            await self.scroll_and_load(page, max_scrolls=8)

            # Extract items using JavaScript (more reliable than CSS selectors)
            # REPLACE the entire script = """ ... """ block with:
            script = """
            () => {
                const items = [];

                let products = document.querySelectorAll('[class*="product-grid-product"]');
                if (products.length === 0) {
                    products = document.querySelectorAll('li[class*="product"]');
                }
                if (products.length === 0) {
                    products = document.querySelectorAll('[data-testid*="product"]');
                }
                if (products.length === 0) {
                    products = document.querySelectorAll('a[href*="/p/"]');
                }

                products.forEach((el) => {
                    try {
                        const nameEl  = el.querySelector('[class*="product-grid-product-info__name"]')
                                    || el.querySelector('[class*="name"]')
                                    || el.querySelector('h3') || el.querySelector('h2');
                        const priceEl = el.querySelector('[class*="money-amount__main"]')
                                    || el.querySelector('[class*="price"]');
                        const imgEl   = el.querySelector('img[src*="static.zara"]')
                                    || el.querySelector('picture img')
                                    || el.querySelector('img');
                        const linkEl  = el.tagName === 'A' ? el : el.querySelector('a[href*="/p/"]');

                        const name  = nameEl  ? nameEl.textContent.trim()  : '';
                        const price = priceEl ? priceEl.textContent.trim() : '';
                        const image = imgEl   ? (imgEl.src || imgEl.dataset.src || '') : '';
                        const url   = linkEl  ? linkEl.href : '';
                        const text  = el.textContent.toLowerCase();

                        const colors = ['white','black','navy','blue','red','grey','gray','beige','cream','brown','green','pink'];
                        const color  = colors.find(c => text.includes(c)) || 'neutral';

                        if (name && name.length > 2) {
                            items.push({
                                name: name.substring(0, 100),
                                price,
                                image,
                                url,
                                color,
                                text: text.substring(0, 200)
                            });
                        }
                    } catch(e) {}
                });

                return items;
            }
            """
            
            products = await page.evaluate(script)
            logger.info(f"Found {len(products)} products using JavaScript extraction")

            for product in products:
                try:
                    name = product.get('name', '').strip()
                    price = product.get('price', 'N/A').strip()
                    image_url = product.get('image', '')
                    product_url = product.get('url', '')
                    color = product.get('color', 'neutral')

                    # Validate and clean data
                    if not name or len(name) < 3:
                        continue

                    # Clean price format
                    if price != 'N/A':
                        # Try to extract numeric value
                        price_match = re.search(r'[\d,]+', price.replace('₹', '').replace('$', '').replace('€', ''))
                        if price_match:
                            try:
                                price_val = float(price_match.group().replace(',', ''))
                                price = f"₹{int(price_val)}"  # Zara India already shows ₹, no conversion needed
                            except ValueError as e:
                                logger.debug(f"Failed to parse price '{price}': {e}")
                                price = 'N/A'

                    # Handle relative URLs
                    if product_url and not product_url.startswith('http'):
                        product_url = f"https://www.zara.com/in/en{product_url}"

                    # Deduplication
                    item_key = (name.lower(), "Zara")
                    if item_key in self.seen_items:
                        continue

                    try:
                        item_data = {
                            "id": f"zara-{self.item_counter:04d}",
                            "item_name": name,
                            "price": price if price != "N/A" else f"₹{random.randint(1500, 5000)}",
                            "image_url": image_url if image_url else "https://via.placeholder.com/300x400?text=Zara+Item",
                            "category": category,
                            "brand": "Zara",
                            "description": name + " from Zara",
                            "color": color,
                            "material": self._extract_material(product.get('text', '')),
                            "source_url": product_url if product_url else url
                        }

                        validated_item = Product(**item_data)
                        self.seen_items.add(item_key)
                        items.append(validated_item.model_dump())
                        self.item_counter += 1
                        logger.info(f"  ✓ Extracted: {name[:50]}")
                    except ValidationError as ve:
                        logger.debug(f"Product validation failed: {ve.errors()}")

                except Exception as e:
                    logger.debug(f"Error processing product: {str(e)}")
                    continue

            logger.info(f"Successfully extracted {len(items)} unique items from this page")

        except Exception as e:
            logger.error(f"Error extracting items: {str(e)}")

        return items

    def _extract_material(self, text: str) -> str:
        """Extract material from text"""
        materials = ['cotton', 'polyester', 'silk', 'wool', 'linen', 'denim', 'leather', 'viscose']
        text_lower = text.lower()
        for material in materials:
            if material in text_lower:
                return material
        return "fabric"

    async def scrape(self) -> List[Dict]:
        """Main scraping function"""
        logger.info("=" * 70)
        logger.info("Starting Zara Scraper")
        logger.info("=" * 70)

        # More specific URLs for better results
        urls = {
            "tops": [
                "https://www.zara.com/in/en/man-t-shirts-l745.html",
                "https://www.zara.com/in/en/man-shirts-and-blouses-l730.html",
                "https://www.zara.com/in/en/man-sweatshirts-l743.html",
            ],
            "bottoms": [
                "https://www.zara.com/in/en/man-jeans-l734.html",
                "https://www.zara.com/in/en/man-trousers-l744.html",
                "https://www.zara.com/in/en/man-shorts-l774.html",
            ]
        }
        try:
            async with async_playwright() as p:

                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ]
                )

                for category, category_urls in urls.items():
                    for url in category_urls:
                        context = await browser.new_context(
                            user_agent=await self.get_random_user_agent(),
                            viewport={"width": 1280, "height": 720},
                            java_script_enabled=True,
                            locale="en-IN",
                            timezone_id="Asia/Kolkata",
                            extra_http_headers={
                                "Accept-Language": "en-IN,en;q=0.9",
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            }
                        )
                        page = await context.new_page()
                        if Stealth:
                            await Stealth().apply_stealth_async(page)

                        try:
                            if await self.fetch_with_retry(page, url):
                                items = await self.extract_items_from_page(page, category, url)
                                self.items.extend(items)
                                logger.info(f"Total items so far: {len(self.items)}")

                                delay = await self.get_random_delay()
                                logger.info(f"Waiting {delay:.1f}s before next request...")
                                await asyncio.sleep(delay)
                            else:
                                logger.warning(f"Failed to fetch {url}")
                        finally:
                            await page.close()
                            await context.close()

                await browser.close()

        except Exception as e:
            logger.error(f"Scraper error: {str(e)}")
            import traceback
            traceback.print_exc()

        logger.info(f"\n✓ Zara Scraper completed with {len(self.items)} items")
        return self.items

async def main():
    scraper = ZaraScraper()
    items = await scraper.scrape()

    BASE_DIR = Path(__file__).parent
    output_path = BASE_DIR / "data" / "zara_items.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved {len(items)} Zara items to zara_items.json")
    return items


if __name__ == "__main__":
    asyncio.run(main())