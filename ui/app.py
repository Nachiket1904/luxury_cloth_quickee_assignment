"""
Streamlit UI - Luxury Stylist Concierge Frontend
Beautiful, interactive interface for fashion recommendations
Connected to FastAPI backend
"""

import streamlit as st
import requests
import json
import logging
from typing import Optional
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{API_BASE_URL}/api/v1/style-me"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

# Page configuration
st.set_page_config(
    page_title="Luxury Stylist Concierge",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    .recommendation-card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    .item-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .confidence-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        color: white;
    }
    .confidence-high {
        background-color: #28a745;
    }
    .confidence-medium {
        background-color: #ffc107;
        color: #333;
    }
    .confidence-low {
        background-color: #dc3545;
    }
    .header-title {
        color: white;
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .tagline {
        color: rgba(255,255,255,0.9);
        text-align: center;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)


def check_api_health() -> bool:
    """Check if FastAPI server is running"""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        return response.status_code == 200
    except:
        return False


def get_recommendations(prompt: str, budget: int, brands: list) -> Optional[dict]:
    """Call FastAPI endpoint to get recommendations"""
    try:
        payload = {
            "user_prompt": prompt,
            "budget": budget,
            "preferred_brands": brands
        }

        with st.spinner("🤖 AI Stylist is thinking..."):
            response = requests.post(
                API_ENDPOINT,
                json=payload,
                timeout=30
            )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ API Error: {response.status_code}")
            return None

    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to API at {API_BASE_URL}")
        st.info("Make sure FastAPI server is running: `python api/main.py`")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def get_confidence_badge(confidence: float) -> str:
    """Get confidence badge HTML"""
    percentage = int(confidence * 100)

    if confidence >= 0.8:
        css_class = "confidence-high"
        emoji = "⭐⭐⭐"
    elif confidence >= 0.6:
        css_class = "confidence-medium"
        emoji = "⭐⭐"
    else:
        css_class = "confidence-low"
        emoji = "⭐"

    return f"""
    <span class="confidence-badge {css_class}">
        {emoji} Confidence: {percentage}%
    </span>
    """


def display_item_card(item: dict, position: int):
    """Display a recommendation item card"""
    with st.container():
        col1, col2 = st.columns([1, 3])

        with col1:
            if item.get("image_url"):
                try:
                    st.image(item["image_url"], width=150, use_column_width=True)
                except:
                    st.write("📸 Image unavailable")

        with col2:
            st.markdown(f"### {position}. {item['item_name']}")
            st.markdown(f"**Brand:** {item['brand']}")
            st.markdown(f"**Category:** {item['category'].upper()}")
            st.markdown(f"**Price:** `{item['price']}`")

            if item.get("color"):
                st.markdown(f"**Color:** {item['color']}")
            if item.get("material"):
                st.markdown(f"**Material:** {item['material']}")

            st.markdown(f"[View on {item['brand']}]({item['source_url']})", unsafe_allow_html=True)


def main():
    """Main Streamlit app"""

    # Header
    st.markdown('<div class="header-title">🎨 Luxury Stylist Concierge</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tagline">AI-Powered Fashion Recommendations | Smart Styling for Every Occasion</div>',
        unsafe_allow_html=True
    )

    # Check API health
    api_healthy = check_api_health()
    if not api_healthy:
        st.error(
            "🔌 **API Server Not Connected**\n\n"
            "Please start the FastAPI server:\n"
            "`python api/main.py`\n\n"
            "Then refresh this page."
        )
        return

    st.success("✅ API Connected")

    # Sidebar for filters
    with st.sidebar:
        st.header("⚙️ Settings")

        # Budget slider
        budget = st.slider(
            "💰 Budget (INR)",
            min_value=500,
            max_value=20000,
            value=10000,
            step=500,
            help="Maximum price for recommendations"
        )

        # Brand selection
        st.subheader("🏷️ Preferred Brands")
        show_all_brands = st.checkbox("Show all brands", value=True)

        brands = []
        if not show_all_brands:
            brands = st.multiselect(
                "Select brands:",
                options=["Zara", "Myntra", "H&M", "Forever 21"],
                default=["Zara", "Myntra"],
                help="Leave empty to include all brands"
            )

        # Advanced options
        with st.expander("📊 Advanced Options"):
            search_method = st.radio(
                "Search Method:",
                options=["Hybrid (BM25 + Semantic)", "Semantic Only", "BM25 Only"],
                index=0,
                help="Hybrid combines keyword and neural search for best results"
            )

        # Statistics
        st.divider()
        st.subheader("📈 Statistics")
        st.info(
            "💡 **Hybrid Search**: Combines:\n"
            "• **BM25**: Fast keyword matching\n"
            "• **Semantic**: Neural understanding\n"
            "= Best of both worlds!"
        )

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("👕 Tell us about your style")

        # User input
        user_prompt = st.text_area(
            "What are you looking for?",
            placeholder="E.g., 'Dark navy chinos for a yacht party' or 'White shirt for office meeting'",
            height=120,
            help="Describe the occasion, color, and style you want"
        )

        # Validate input
        if len(user_prompt) < 10:
            st.warning("⚠️ Please describe what you're looking for (at least 10 characters)")
            user_prompt = None

    with col2:
        st.subheader("🎯 Quick Filters")

        # Quick occasion buttons
        occasions = ["Casual", "Office", "Party", "Date", "Gym"]
        for occasion in occasions:
            if st.button(f"👉 {occasion}", key=f"occasion_{occasion}"):
                user_prompt = f"{occasion} wear for work"

    # Get recommendations
    if user_prompt:
        st.divider()

        # Show loading state
        recommendation = get_recommendations(user_prompt, budget, brands)

        if recommendation and recommendation.get("status") == "success":
            # Success state
            st.success("✅ Recommendation Generated!")

            # Display execution time
            exec_time = recommendation.get("execution_time_ms", 0)
            st.caption(f"⚡ Generated in {exec_time:.1f}ms")

            # Confidence and total price
            st.divider()

            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                confidence = recommendation.get("confidence", 0)
                st.markdown(get_confidence_badge(confidence), unsafe_allow_html=True)

            with col2:
                st.metric("💳 Total Price", recommendation.get("total_price", "N/A"))

            with col3:
                st.metric("📦 Items", len(recommendation.get("recommendations", [])))

            # Stylist note
            st.divider()
            st.subheader("💬 Stylist's Note")
            st.info(recommendation.get("stylist_note", "No note available"))

            # Recommendations
            st.divider()
            st.subheader("👗 Your Recommendations")

            recommendations = recommendation.get("recommendations", [])

            for idx, item in enumerate(recommendations, 1):
                with st.container():
                    display_item_card(item, idx)
                    st.divider()

            # Additional info
            with st.expander("📋 Detailed Analysis"):
                st.json(recommendation.get("reasoning", {}))

        elif recommendation:
            st.error(f"❌ {recommendation.get('message', 'Failed to generate recommendation')}")

    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🏢 About")
        st.caption("Luxury Stylist Concierge - AI-powered fashion recommendations")

    with col2:
        st.markdown("### 🔧 Technology")
        st.caption(
            "• FastAPI Backend\n"
            "• Hybrid Search (BM25 + Semantic)\n"
            "• ONNX Embeddings\n"
            "• ChromaDB Vector DB"
        )

    with col3:
        st.markdown("### ⚡ Features")
        st.caption(
            "• Real-time Recommendations\n"
            "• Query Caching\n"
            "• Fashion Rules Engine\n"
            "• Confidence Scoring"
        )


if __name__ == "__main__":
    main()
