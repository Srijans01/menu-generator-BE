from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Dish(BaseModel):
    name: str
    price: float

class Category(BaseModel):
    name: str
    dishes: list[Dish] = []

class Menu(BaseModel):
    id: str = None  # Default to None, will be set on creation
    name: str
    categories: list[Category] = []

class Restaurant(BaseModel):
    name: str
    location: str
    menus: list[Menu] = []

class Ad(BaseModel):
    ad_name: str
    bid_price: float
    ad_image_url: str
    metadata: Optional[dict] = {}
    ttl: Optional[int] = 0  # TTL in seconds (configurable for each ad)
    created_at: Optional[datetime] = datetime.utcnow()  # When the ad was created
    impression_count: Optional[int] = 0
