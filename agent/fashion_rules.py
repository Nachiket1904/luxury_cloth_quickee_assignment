"""
Fashion Rules Engine - Validates and scores clothing pairings
Rules for color harmony, price balance, occasion fit, material compatibility
"""

import logging
from typing import Dict, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FashionRules:
    """Fashion domain knowledge for intelligent pairing validation"""

    # Color harmony rules
    COLOR_PAIRS = {
        "white": ["navy", "black", "grey", "beige", "cream", "burgundy"],
        "navy": ["white", "cream", "light_blue", "beige", "grey"],
        "black": ["white", "red", "gold", "silver", "grey"],
        "grey": ["white", "navy", "black", "blue", "burgundy"],
        "cream": ["navy", "brown", "black", "grey"],
        "beige": ["navy", "black", "brown", "white"],
        "blue": ["white", "grey", "cream"],
        "red": ["white", "black", "grey"],
        "burgundy": ["white", "black", "cream", "grey"],
        "brown": ["white", "cream", "grey", "beige"],
    }

    # Occasion-specific requirements
    OCCASION_REQUIREMENTS = {
        "yacht_party": {"style": "premium", "colors": ["white", "navy", "cream"], "fit": "fitted"},
        "office": {"style": "formal", "colors": ["white", "navy", "grey"], "fit": "structured"},
        "casual": {"style": "relaxed", "colors": ["any"], "fit": "comfortable"},
        "party": {"style": "trendy", "colors": ["any"], "fit": "fitted"},
        "gym": {"style": "athletic", "colors": ["any"], "fit": "loose"},
        "date": {"style": "smart", "colors": ["any"], "fit": "fitted"},
    }

    # Material compatibility
    MATERIALS = {
        "cotton": ["linen", "wool", "polyester"],
        "linen": ["cotton", "silk"],
        "wool": ["cotton", "polyester"],
        "silk": ["linen", "cotton"],
        "polyester": ["cotton", "wool"],
        "denim": ["cotton", "linen"],
    }

    def __init__(self):
        logger.info("✅ Fashion Rules Engine initialized")

    def colors_match(self, color1: str, color2: str) -> bool:
        """Check if two colors work together"""
        if not color1 or not color2 or color1 == "unknown" or color2 == "unknown":
            return True  # Unknown colors are acceptable

        color1_lower = color1.lower().strip()
        color2_lower = color2.lower().strip()

        # Check if colors are in compatibility map
        if color1_lower in self.COLOR_PAIRS:
            return color2_lower in self.COLOR_PAIRS[color1_lower]

        # Reverse check
        if color2_lower in self.COLOR_PAIRS:
            return color1_lower in self.COLOR_PAIRS[color2_lower]

        # Unknown colors are OK
        return True

    def materials_work(self, material1: str, material2: str) -> bool:
        """Check if materials are compatible"""
        if not material1 or not material2:
            return True

        material1 = material1.lower().strip()
        material2 = material2.lower().strip()

        if material1 in self.MATERIALS:
            return material2 in self.MATERIALS[material1]

        return True  # Default to OK

    def prices_harmonize(self, price1: str, price2: str) -> Tuple[bool, float]:
        """
        Check if prices are balanced
        Returns: (is_balanced, ratio)
        """
        try:
            # Extract numeric values
            p1 = float(str(price1).replace("₹", "").replace(",", "").strip())
            p2 = float(str(price2).replace("₹", "").replace(",", "").strip())

            if p1 == 0 or p2 == 0:
                return True, 1.0

            ratio = max(p1, p2) / min(p1, p2)

            # Acceptable ratio: 0.5 to 2.0 (items shouldn't be too far apart in price)
            is_balanced = 0.5 <= ratio <= 2.0

            return is_balanced, ratio

        except Exception:
            return True, 1.0  # Default to OK on parse error

    def validate_pairing(self, item1: Dict, item2: Dict) -> Dict:
        """
        Validate a top-bottom pairing
        Returns: {score, rules_met, reasons}
        """
        score = 0.0
        rules_met = []
        rules_failed = []

        # Rule 1: Category check (must be different)
        if item1.get("category") != item2.get("category"):
            score += 0.2
            rules_met.append("✓ Different categories (top + bottom)")
        else:
            rules_failed.append("✗ Same category (both tops or both bottoms)")

        # Rule 2: Color harmony (30 points)
        color1 = item1.get("color", "unknown")
        color2 = item2.get("color", "unknown")

        if self.colors_match(color1, color2):
            score += 0.3
            rules_met.append(f"✓ Colors match ({color1} + {color2})")
        else:
            rules_failed.append(f"✗ Color mismatch ({color1} + {color2})")

        # Rule 3: Price ratio (20 points)
        price_balanced, ratio = self.prices_harmonize(item1.get("price"), item2.get("price"))

        if price_balanced:
            score += 0.2
            rules_met.append(f"✓ Price balanced (ratio: {ratio:.2f})")
        else:
            rules_failed.append(f"✗ Price imbalance (ratio: {ratio:.2f})")

        # Rule 4: Material compatibility (15 points)
        material1 = item1.get("material", "fabric")
        material2 = item2.get("material", "fabric")

        if self.materials_work(material1, material2):
            score += 0.15
            rules_met.append(f"✓ Materials compatible ({material1} + {material2})")
        else:
            rules_failed.append(f"✗ Material incompatible ({material1} + {material2})")

        # Rule 5: Brand diversity (15 points)
        if item1.get("brand") != item2.get("brand"):
            score += 0.15
            rules_met.append(f"✓ Different brands ({item1.get('brand')} + {item2.get('brand')})")
        else:
            rules_met.append(f"✓ Same brand ({item1.get('brand')})")

        # Normalize score to 0-1
        score = min(score, 1.0)

        return {
            "score": score,
            "rules_met": rules_met,
            "rules_failed": rules_failed,
            "color_match": self.colors_match(color1, color2),
            "price_balanced": price_balanced,
            "material_compatible": self.materials_work(material1, material2),
        }

    def score_recommendation(
        self, items: list, user_context: str = ""
    ) -> Dict:
        """
        Score a complete recommendation
        items: list of recommended items
        user_context: user's occasion/style requirements
        """
        if len(items) < 2:
            return {
                "confidence": 0.0,
                "reasoning": "Need at least 2 items for recommendation"
            }

        # Score pairings
        total_score = 0
        pairing_details = []

        for i in range(len(items) - 1):
            for j in range(i + 1, len(items)):
                pairing_result = self.validate_pairing(items[i], items[j])
                total_score += pairing_result["score"]
                pairing_details.append({
                    "items": [items[i]["item_name"], items[j]["item_name"]],
                    **pairing_result
                })

        # Average score
        num_pairings = len(items) * (len(items) - 1) // 2
        avg_score = total_score / num_pairings if num_pairings > 0 else 0

        # Add context boost
        confidence = min(avg_score + 0.15, 1.0)  # Boost with base confidence

        return {
            "confidence": confidence,
            "avg_score": avg_score,
            "pairings": pairing_details,
            "notes": "Perfect styling for premium occasion" if confidence > 0.8 else (
                "Good pairing with some considerations" if confidence > 0.6 else
                "Mix and match for unique style"
            )
        }


def test_fashion_rules():
    """Test fashion rules"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 TESTING FASHION RULES")
    logger.info("=" * 60 + "\n")

    rules = FashionRules()

    # Test items
    item1 = {
        "item_name": "White Cotton T-Shirt",
        "price": "₹1,299",
        "category": "tops",
        "color": "white",
        "material": "cotton",
        "brand": "Zara"
    }

    item2 = {
        "item_name": "Navy Blue Trousers",
        "price": "₹2,499",
        "category": "bottoms",
        "color": "navy",
        "material": "cotton",
        "brand": "Myntra"
    }

    logger.info("Testing pairing: White T-Shirt + Navy Trousers")
    result = rules.validate_pairing(item1, item2)
    logger.info(f"Score: {result['score']:.2f}")
    for rule in result['rules_met']:
        logger.info(rule)
    for rule in result['rules_failed']:
        logger.info(rule)

    logger.info("\n" + "=" * 60)
    logger.info("✅ FASHION RULES TEST COMPLETE")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    test_fashion_rules()
