"""
Stylist Agent - AI-powered fashion recommendation engine
Uses hybrid search (BM25 + semantic) + fashion rules + Groq LLM for enhanced recommendations
"""

import logging
import json
from typing import Dict, List, Optional
from rag.vector_store import VectorStore
from rag.cache import QueryCache
from agent.fashion_rules import FashionRules
from rag.llm_engine import GroqLLMEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StylistAgent:
    def __init__(self):
        """Initialize stylist agent with vector store, cache, fashion rules, and Groq LLM"""
        logger.info("Initializing Stylist Agent...")

        self.vector_store = VectorStore()
        self.cache = QueryCache(ttl_hours=1)
        self.fashion_rules = FashionRules()
        self.llm_engine = GroqLLMEngine()

        logger.info("✅ Stylist Agent ready (with Groq LLM integration)\n")

    def _parse_user_context(self, prompt: str) -> Dict:
        """
        Parse user prompt to extract context
        Looks for: occasion, color preferences, budget, style
        """
        prompt_lower = prompt.lower()

        occasion = "casual"
        if any(word in prompt_lower for word in ["office", "meeting", "work", "formal"]):
            occasion = "office"
        elif any(word in prompt_lower for word in ["party", "yacht", "event", "celebration"]):
            occasion = "party"
        elif any(word in prompt_lower for word in ["gym", "fitness", "exercise", "sports"]):
            occasion = "gym"
        elif any(word in prompt_lower for word in ["date", "romantic", "casual meet"]):
            occasion = "date"

        # Extract budget if mentioned
        budget = 10000
        if "₹" in prompt:
            import re
            match = re.search(r"₹(\d+)", prompt)
            if match:
                budget = int(match.group(1))

        return {
            "occasion": occasion,
            "budget": budget,
            "full_prompt": prompt
        }

    def recommend(self, user_prompt: str, budget: int = 10000) -> Dict:
        """
        Main recommendation method
        Takes user prompt and budget, returns outfit recommendation
        """
        logger.info("\n" + "=" * 60)
        logger.info("🧥 STYLIST AGENT - RECOMMENDATION")
        logger.info("=" * 60)
        logger.info(f"User: {user_prompt}")
        logger.info(f"Budget: ₹{budget}")

        # Check cache first
        cached = self.cache.get(user_prompt, {"budget": budget})
        if cached:
            logger.info("\n📌 Using cached recommendation")
            return cached

        # Parse context
        context = self._parse_user_context(user_prompt)
        context["budget"] = budget

        logger.info(f"📊 Parsed context:")
        logger.info(f"   Occasion: {context['occasion']}")
        logger.info(f"   Budget: ₹{context['budget']}")

        try:
            # Step 1: Search for matching tops
            logger.info("\n🔍 Step 1: Searching for tops...")
            tops = self.vector_store.search(
                query=f"tops for {user_prompt}",
                top_k=10,
                filters={"category": "tops", "max_price": budget},
                method="hybrid"
            )

            if not tops:
                logger.warning("No tops found!")
                tops = []
            else:
                logger.info(f"✅ Found {len(tops)} potential tops")
                for top in tops[:3]:
                    logger.info(f"   - {top['item_name']} ({top['price']})")

            # Step 2: Search for matching bottoms
            logger.info("\n🔍 Step 2: Searching for bottoms...")
            bottoms = self.vector_store.search(
                query=f"bottoms for {user_prompt}",
                top_k=10,
                filters={"category": "bottoms", "max_price": budget},
                method="hybrid"
            )

            if not bottoms:
                logger.warning("No bottoms found!")
                bottoms = []
            else:
                logger.info(f"✅ Found {len(bottoms)} potential bottoms")
                for bottom in bottoms[:3]:
                    logger.info(f"   - {bottom['item_name']} ({bottom['price']})")

            if not tops or not bottoms:
                logger.warning("⚠️ Not enough items to recommend")
                return {
                    "status": "error",
                    "message": "Not enough items found in catalog for this query",
                    "tops": tops,
                    "bottoms": bottoms
                }

            # Step 3: Find best pairing using fashion rules
            logger.info("\n⚖️ Step 3: Validating pairings with fashion rules...")

            best_pairing = None
            best_score = 0
            pairing_results = []

            # Score all combinations
            for top in tops[:5]:  # Check top-5 results
                for bottom in bottoms[:5]:
                    validation = self.fashion_rules.validate_pairing(top, bottom)
                    score = validation["score"]

                    pairing_results.append({
                        "top": top["item_name"],
                        "bottom": bottom["item_name"],
                        "score": score,
                        "validation": validation
                    })

                    if score > best_score:
                        best_score = score
                        best_pairing = (top, bottom, validation)

            # Fallback if no good pairing found
            if not best_pairing:
                logger.warning("⚠️ No ideal pairing found, using top candidates")
                best_pairing = (tops[0], bottoms[0], self.fashion_rules.validate_pairing(tops[0], bottoms[0]))

            top_item, bottom_item, validation = best_pairing

            logger.info(f"\n✅ Best pairing found (score: {best_score:.2f})")
            logger.info(f"   Top: {top_item['item_name']} ({top_item['price']})")
            logger.info(f"   Bottom: {bottom_item['item_name']} ({bottom_item['price']})")

            # Step 4: Generate stylist note using Groq LLM
            logger.info("\n📝 Step 4: Generating stylist explanation with Groq LLM...")

            stylist_note = self.llm_engine.generate_stylist_note(
                top_item,
                bottom_item,
                context["occasion"],
                user_prompt
            )

            logger.info(f"✅ Stylist note generated: {stylist_note[:100]}...")

            # Step 5: Calculate total price
            total_price = self._calculate_total_price(top_item, bottom_item)

            # Step 6: Calculate confidence
            confidence = min(best_score + 0.15, 1.0)

            logger.info(f"\n📊 Final Recommendation:")
            logger.info(f"   Confidence: {confidence:.2f}")
            logger.info(f"   Total Price: {total_price}")

            result = {
                "status": "success",
                "recommendations": [top_item, bottom_item],
                "total_price": total_price,
                "stylist_note": stylist_note,
                "confidence": confidence,
                "reasoning": {
                    "validation": validation,
                    "pairing_score": best_score,
                    "occasion": context["occasion"]
                }
            }

            # Cache the result
            self.cache.set(user_prompt, {"budget": budget}, result)

            logger.info("\n" + "=" * 60)
            logger.info("✅ RECOMMENDATION COMPLETE")
            logger.info("=" * 60 + "\n")

            return result

        except Exception as e:
            logger.error(f"❌ Error generating recommendation: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def _generate_stylist_note(self, top: Dict, bottom: Dict, validation: Dict, context: Dict) -> str:
        """Generate explanatory stylist note"""
        notes = []

        # Start with the pairing
        notes.append(f"The {top['item_name']} in {top.get('color', 'this elegant shade')}")
        notes.append(f"pairs beautifully with your {bottom['item_name']}. ")

        # Add color comment
        if validation.get("color_match"):
            notes.append(
                f"The {top.get('color', 'color')} and {bottom.get('color', 'shade')} "
                f"create a harmonious, balanced look. "
            )

        # Add material comment
        if validation.get("material_compatible"):
            notes.append(
                f"The premium {top.get('material', 'fabric')} blend ensures comfort and elegance. "
            )

        # Add occasion-specific comment
        occasion = context.get("occasion", "casual")
        if occasion == "office":
            notes.append(
                "This professional combination is perfect for business settings, "
                "conveying confidence and sophistication. "
            )
        elif occasion == "party":
            notes.append(
                "This chic pairing will make you stand out at any social event "
                "with its refined elegance. "
            )
        elif occasion == "casual":
            notes.append(
                "This relaxed combination is versatile and comfortable for everyday wear. "
            )

        # Confidence note
        if validation.get("score", 0) > 0.8:
            notes.append("A perfect match! 🌟")
        elif validation.get("score", 0) > 0.6:
            notes.append("An excellent choice!")
        else:
            notes.append("A nice combination worth trying!")

        return "".join(notes)

    def _calculate_total_price(self, top: Dict, bottom: Dict) -> str:
        """Calculate total price of pairing"""
        try:
            p1_str = str(top.get("price", "₹0")).replace("₹", "").replace(",", "")
            p2_str = str(bottom.get("price", "₹0")).replace("₹", "").replace(",", "")

            p1 = float(p1_str)
            p2 = float(p2_str)
            total = p1 + p2

            return f"₹{total:,.0f}"
        except Exception as e:
            logger.warning(f"Error calculating price: {e}")
            return "Price unavailable"

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return self.cache.get_stats()


async def test_agent():
    """Test stylist agent"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 TESTING STYLIST AGENT")
    logger.info("=" * 60 + "\n")

    agent = StylistAgent()

    # Test recommendation
    result = agent.recommend(
        "I have dark navy chinos, what t-shirt should I wear for a yacht party?",
        budget=5000
    )

    if result["status"] == "success":
        logger.info("\n✅ Recommendation successful!")
        logger.info(f"Items: {[r['item_name'] for r in result['recommendations']]}")
        logger.info(f"Total: {result['total_price']}")
        logger.info(f"Confidence: {result['confidence']:.2f}")
    else:
        logger.error(f"❌ Recommendation failed: {result['message']}")

    # Print cache stats
    agent.cache.print_stats()


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_agent())
