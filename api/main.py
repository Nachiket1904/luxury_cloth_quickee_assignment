"""
FastAPI Server - Luxury Stylist Concierge API
Main endpoint: POST /api/v1/style-me
Accepts user prompt + budget, returns outfit recommendation
"""

import time
import logging
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.schemas import StyleRequest, StyleResponse, RecommendedItem, HealthResponse
from agent.stylist_agent import StylistAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Luxury Stylist Concierge",
    description="AI-powered fashion recommendation engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for Streamlit UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent = None


def init_agent():
    """Initialize stylist agent"""
    global agent
    try:
        if agent is None:
            logger.info("Initializing Stylist Agent...")
            agent = StylistAgent()
            logger.info("✅ Agent ready")
        return agent
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        return None


@app.on_event("startup")
async def startup_event():
    """Initialize on app startup"""
    logger.info("\n" + "=" * 60)
    logger.info("🚀 FASTAPI SERVER STARTUP")
    logger.info("=" * 60 + "\n")
    init_agent()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Luxury Stylist API is running"
    }


@app.post("/api/v1/style-me", response_model=StyleResponse)
async def style_me(request: StyleRequest) -> StyleResponse:
    """
    Main recommendation endpoint

    Args:
        request: StyleRequest with user_prompt, budget, preferred_brands

    Returns:
        StyleResponse with recommendations, total_price, stylist_note, confidence
    """
    start_time = time.time()

    logger.info("\n" + "=" * 60)
    logger.info("📨 INCOMING REQUEST")
    logger.info("=" * 60)
    logger.info(f"Prompt: {request.user_prompt}")
    logger.info(f"Budget: ₹{request.budget}")
    if request.preferred_brands:
        logger.info(f"Brands: {request.preferred_brands}")

    try:
        # Ensure agent is initialized
        stylist_agent = init_agent()
        if not stylist_agent:
            raise Exception("Failed to initialize stylist agent")

        # Get recommendation
        logger.info("\n🤖 Generating recommendation...")
        result = stylist_agent.recommend(
            user_prompt=request.user_prompt,
            budget=request.budget
        )

        # Handle error from agent
        if result.get("status") == "error":
            logger.warning(f"Agent returned error: {result.get('message')}")
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Failed to generate recommendation")
            )

        # Convert items to RecommendedItem schema
        recommendations = []
        for item in result.get("recommendations", []):
            recommendations.append(
                RecommendedItem(
                    id=item.get("id", "unknown"),
                    item_name=item.get("item_name", "Unknown Item"),
                    price=item.get("price", "Price N/A"),
                    image_url=item.get("image_url", ""),
                    brand=item.get("brand", "Unknown"),
                    category=item.get("category", "unknown"),
                    source_url=item.get("source_url", ""),
                    color=item.get("color"),
                    material=item.get("material")
                )
            )

        execution_time = (time.time() - start_time) * 1000

        response = StyleResponse(
            status="success",
            recommendations=recommendations,
            total_price=result.get("total_price", "Price N/A"),
            stylist_note=result.get("stylist_note", ""),
            confidence=result.get("confidence", 0.5),
            execution_time_ms=execution_time
        )

        logger.info(f"\n✅ REQUEST COMPLETE ({execution_time:.1f}ms)")
        logger.info(f"Recommendations: {len(recommendations)} items")
        logger.info(f"Confidence: {response.confidence:.2f}")
        logger.info("=" * 60 + "\n")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        execution_time = (time.time() - start_time) * 1000

        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
                "execution_time_ms": execution_time
            }
        )


@app.get("/api/v1/cache-stats")
async def cache_stats():
    """Get cache statistics"""
    stylist_agent = init_agent()
    if not stylist_agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    stats = stylist_agent.get_cache_stats()
    return {
        "status": "success",
        "cache_stats": stats
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail
        }
    )


@app.get("/")
async def root():
    """Root endpoint - redirects to API docs"""
    return {
        "message": "Welcome to Luxury Stylist Concierge API",
        "docs": "/docs",
        "endpoint": "/api/v1/style-me"
    }


def main():
    """Start FastAPI server"""
    logger.info("\n" + "=" * 80)
    logger.info("🎨 LUXURY STYLIST CONCIERGE - FastAPI Server")
    logger.info("=" * 80)
    logger.info(f"🌐 Server: http://0.0.0.0:8000")
    logger.info(f"📚 Docs: http://0.0.0.0:8000/docs")
    logger.info(f"🔌 Endpoint: POST /api/v1/style-me")
    logger.info("=" * 80 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    main()
