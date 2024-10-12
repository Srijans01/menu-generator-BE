from fastapi import APIRouter, HTTPException , Body
from app.models import Ad
from app.db import db
from bson import ObjectId
from datetime import datetime , timedelta

router = APIRouter()

# Onboard a new ad
@router.post("/onboardAd")
async def create_ad(ad: Ad):
    ad.last_served = None  # Initialize with no last served
    ad.impression_count = 0  # Initialize the impression count
    result = await db.ads.insert_one(ad.dict())
    return {"message": "Ad added successfully", "ad_id": str(result.inserted_id)}

# Fetch all ads (for management UI)
@router.get("/ads")
async def get_ads():
    ads = await db.ads.find().to_list(100)
    return [ad for ad in ads]

@router.post("/brands/{brand_id}/ads")
async def add_ad_to_brand(brand_id: str, ad: Ad = Body(...)):
    # Check if brand exists
    brand = await db.brands.find_one({"_id": ObjectId(brand_id)})
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Set up the ad with TTL
    expiration_date = datetime.utcnow() + timedelta(seconds=ad.ttl)
    ad_data = {
        "ad_name": ad.ad_name,
        "bid_price": ad.bid_price,
        "ad_image_url": ad.ad_image_url,
        "metadata": ad.metadata,
        "ttl": ad.ttl,
        "created_at": ad.created_at,
        "expires_at": expiration_date,
        "impression_count": ad.impression_count,
        "brand_id": ObjectId(brand_id)  # Store the reference to the brand
    }

    # Insert the ad into the ads collection
    result = await db.ads.insert_one(ad_data)
    
    return {"message": "Ad added successfully", "ad_id": str(result.inserted_id)}