"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class StyleRequest(BaseModel):
    """User request for style recommendation"""
    user_prompt: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="What you want to wear (e.g., 'Dark navy chinos for a yacht party')"
    )
    budget: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Maximum budget in INR"
    )
    preferred_brands: List[str] = Field(
        default=[],
        description="Preferred brands (e.g., ['Zara', 'Myntra'])"
    )


class RecommendedItem(BaseModel):
    """Recommended fashion item"""
    id: str
    item_name: str
    price: str
    image_url: str
    brand: str
    category: str
    source_url: str
    color: Optional[str] = None
    material: Optional[str] = None


class StyleResponse(BaseModel):
    """Response with recommendation"""
    status: str = Field(..., description="'success' or 'error'")
    recommendations: List[RecommendedItem] = Field(
        ...,
        description="List of recommended items"
    )
    total_price: str
    stylist_note: str = Field(
        ...,
        description="Explanation of why these items work together"
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence score (0-1)"
    )
    execution_time_ms: float = Field(
        ...,
        description="Time taken to generate recommendation (ms)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "recommendations": [
                    {
                        "id": "zara-001",
                        "item_name": "Premium White T-Shirt",
                        "price": "₹1,299",
                        "image_url": "https://...",
                        "brand": "Zara",
                        "category": "tops",
                        "source_url": "https://zara.com/...",
                        "color": "white",
                        "material": "cotton"
                    }
                ],
                "total_price": "₹5,298",
                "stylist_note": "The white cotton perfectly complements navy chinos...",
                "confidence": 0.92,
                "execution_time_ms": 342.5
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
