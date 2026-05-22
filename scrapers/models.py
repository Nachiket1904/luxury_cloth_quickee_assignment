from pydantic import BaseModel, Field, field_validator
from typing import Optional


class Product(BaseModel):
    """Validated product schema for fashion items"""
    id: str
    item_name: str = Field(..., min_length=3, max_length=200)
    price: str
    image_url: str
    category: str = Field(..., pattern="^(tops|bottoms)$")
    brand: str
    description: str
    color: str
    material: str
    source_url: str

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        """Ensure price is not empty"""
        if not v or v.strip() == '':
            raise ValueError('Price cannot be empty')
        return v

    @field_validator('image_url')
    @classmethod
    def validate_image_url(cls, v):
        """Ensure image URL is valid"""
        if not v or not v.startswith('http'):
            raise ValueError('Image URL must be a valid HTTP URL')
        return v

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        """Ensure category is valid"""
        if v not in ['tops', 'bottoms']:
            raise ValueError('Category must be either "tops" or "bottoms"')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "zara-0001",
                "item_name": "Blue Cotton T-Shirt",
                "price": "₹1999",
                "image_url": "https://example.com/image.jpg",
                "category": "tops",
                "brand": "Zara",
                "description": "Blue Cotton T-Shirt from Zara",
                "color": "blue",
                "material": "cotton",
                "source_url": "https://www.zara.com/product"
            }
        }
