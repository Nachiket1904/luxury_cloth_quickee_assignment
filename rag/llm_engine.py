"""
Groq LLM Engine - Fast, cost-effective LLM for fashion recommendations
Uses Groq's fast inference to enhance outfit recommendations with reasoning
"""

import logging
import json
import os
from typing import Dict, List, Optional
from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroqLLMEngine:
    def __init__(self, model: str = "llama-3.1-8b-instant"):
        """
        Initialize Groq LLM Engine
        model: Groq model to use (default: llama-3.1-8b-instant - fastest & cost-effective)
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("⚠️  GROQ_API_KEY not set. Using mock responses.")
            self.client = None
            self.model = model
            return

        self.client = Groq(api_key=api_key)
        self.model = model
        logger.info(f"✅ Groq LLM Engine initialized with model: {model}")

    def generate_stylist_note(
        self,
        top: Dict,
        bottom: Dict,
        occasion: str,
        user_prompt: str
    ) -> str:
        """
        Generate a luxurious stylist note explaining why the pieces work together
        Uses Groq for fast, intelligent reasoning
        """
        if not self.client:
            return self._mock_stylist_note(top, bottom, occasion)

        prompt = f"""You are a luxury fashion stylist. Generate a short, elegant 1-2 sentence explanation
why this outfit works perfectly for the occasion.

Top: {top.get('item_name', 'Unknown')} ({top.get('color', 'neutral')}, {top.get('material', 'fabric')})
Bottom: {bottom.get('item_name', 'Unknown')} ({bottom.get('color', 'neutral')})
Occasion: {occasion}
User Request: {user_prompt}

Generate ONLY the stylist note, no extra text. Make it luxurious and persuasive."""

        try:
            message = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=100,
            )
            return message.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq error: {e}")
            return self._mock_stylist_note(top, bottom, occasion)

    def evaluate_outfit_quality(
        self,
        tops: List[Dict],
        bottoms: List[Dict],
        user_prompt: str
    ) -> Dict:
        """
        Use Groq to intelligently evaluate and rank outfit combinations
        Returns best pairing with reasoning
        """
        if not self.client:
            return self._mock_evaluation(tops, bottoms)

        tops_str = "\n".join([f"- {t.get('item_name')} ({t.get('color')}, {t.get('material')})" for t in tops[:3]])
        bottoms_str = "\n".join([f"- {b.get('item_name')} ({b.get('color')})" for b in bottoms[:3]])

        prompt = f"""You are a luxury fashion expert. Analyze these available items and recommend
the BEST outfit combination.

Available Tops:
{tops_str}

Available Bottoms:
{bottoms_str}

User Request: {user_prompt}

Respond in JSON format:
{{
    "best_top": "exact name from list",
    "best_bottom": "exact name from list",
    "confidence": 0.0-1.0,
    "reasoning": "why this pairing is perfect"
}}"""

        try:
            message = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.5,
                max_tokens=200,
            )

            try:
                response = json.loads(message.choices[0].message.content)
                return response
            except json.JSONDecodeError:
                logger.warning("Failed to parse Groq JSON response")
                return self._mock_evaluation(tops, bottoms)

        except Exception as e:
            logger.error(f"Groq evaluation error: {e}")
            return self._mock_evaluation(tops, bottoms)

    def _mock_stylist_note(self, top: Dict, bottom: Dict, occasion: str) -> str:
        """Fallback stylist note when Groq is unavailable"""
        color_combo = f"{top.get('color')} and {bottom.get('color')}"
        material = top.get('material', 'fabric')
        return f"This elegant {color_combo} combination in {material} is perfect for {occasion}. The pieces complement each other beautifully, creating a polished and sophisticated look."

    def _mock_evaluation(self, tops: List[Dict], bottoms: List[Dict]) -> Dict:
        """Fallback evaluation when Groq is unavailable"""
        return {
            "best_top": tops[0].get('item_name', 'Unknown') if tops else "None",
            "best_bottom": bottoms[0].get('item_name', 'Unknown') if bottoms else "None",
            "confidence": 0.85,
            "reasoning": "Best match based on color coordination and style compatibility"
        }

    def optimize_prompt(self, user_prompt: str) -> str:
        """
        Optimize user prompt using Groq for better search results
        Removes noise, extracts key fashion requirements
        """
        if not self.client:
            return user_prompt

        optimization_prompt = f"""Optimize this fashion search query to extract key style requirements.
Remove filler words, focus on: color, style, occasion, fit, material preferences.

Original query: {user_prompt}

Return ONLY the optimized query, no explanation."""

        try:
            message = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": optimization_prompt}
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=50,
            )
            optimized = message.choices[0].message.content.strip()
            logger.info(f"Optimized prompt: {optimized}")
            return optimized
        except Exception as e:
            logger.warning(f"Prompt optimization failed: {e}")
            return user_prompt
