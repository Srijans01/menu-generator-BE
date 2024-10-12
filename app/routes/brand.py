from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from typing import Optional
from app.db import db
from app.models import Ad
from datetime import datetime, timedelta

router = APIRouter()

# Brand Model
class Brand(BaseModel):
    brand_name: str
    metadata: Optional[dict] = {}

# Onboard a new brand
@router.post("/onBoardBrand")
async def create_brand(brand: Brand):
    result = await db.brands.insert_one({
        "brand_name": brand.brand_name,
        "metadata": brand.metadata
    })
    return {"message": "Brand onboarded successfully", "brand_id": str(result.inserted_id)}

# Search brands by name
@router.get("/searchBrand/{name}")
async def search_brand(name: str):
    brands = await db.brands.find({"brand_name": {"$regex": name, "$options": "i"}}).to_list(10)
    if not brands:
        raise HTTPException(status_code=404, detail="No brands found")
    return brands

# Add a new ad for a specific brand
@router.post("/{brand_id}/ads")
async def add_ad_to_brand(brand_id: str, ad: Ad):
    # Verify if brand exists
    brand = await db.brands.find_one({"_id": ObjectId(brand_id)})
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Calculate TTL expiration date if TTL is provided
    expiration_time = None
    if ad.ttl and ad.ttl > 0:
        expiration_time = datetime.utcnow() + timedelta(seconds=ad.ttl)
    
    # Create ad with brand_id reference
    new_ad = ad.dict()
    new_ad['brand_id'] = brand_id
    new_ad['expires_at'] = expiration_time  # Store the expiration time in the ad

    result = await db.ads.insert_one(new_ad)

    return {"message": "Ad added successfully", "ad_id": str(result.inserted_id)}

@router.post("/{brand_id}/ads")
async def add_ad_to_brand(brand_id: str, ad: Ad):
    brand = await db.brands.find_one({"_id": ObjectId(brand_id)})
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    ad_dict = ad.dict()
    ad_dict["last_served"] = None
    ad_dict["impression_count"] = 0

    result = await db.brands.update_one(
        {"_id": ObjectId(brand_id)},
        {"$push": {"ads": ad_dict}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to add ad to brand")

    return {"message": "Ad added successfully", "brand_id": brand_id}

# Fetch ads for a brand (excluding expired ones)
@router.get("/{brand_id}/ads")
async def get_ads_for_brand(brand_id: str):
    # Fetch ads excluding those with expired TTL
    current_time = datetime.utcnow()
    ads = await db.ads.find({
        "brand_id": brand_id,
        "$or": [{"expires_at": None}, {"expires_at": {"$gte": current_time}}]
    }).to_list(100)

    if not ads:
        raise HTTPException(status_code=404, detail="No ads found or all ads expired")

    return ads

# TTL Cleanup - Can be used as a background task (optional)
async def ttl_cleanup():
    current_time = datetime.utcnow()
    result = await db.ads.delete_many({"expires_at": {"$lte": current_time}})
    return result.deleted_count


# Utility function to convert ObjectId to string
def convert_objectid_to_str(data):
    if isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    if isinstance(data, dict):
        return {key: (str(value) if isinstance(value, ObjectId) else value) for key, value in data.items()}
    return data

# Get all brands
@router.get("/getAllBrands")
async def get_brands():
    brands = await db.brands.find().to_list(100)
    return convert_objectid_to_str(brands)

@router.get("/{brand_id}/ads")
async def get_ads_for_brand(brand_id: str):
    brand = await db.brands.find_one({"_id": ObjectId(brand_id)})
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand["ads"]

