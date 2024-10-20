from fastapi import APIRouter, HTTPException, Request
from app.models import Restaurant, Menu, Category, Dish
from app.db import db
from app.utils.utils import get_next_ad
from bson import ObjectId
from app.utils.utils import obj_to_str,generate_menu_pdf, generate_qr_code,FILE_DIR
from pydantic import BaseModel

class MenuNameUpdate(BaseModel):
    new_name: str
    welcome_text: str

router = APIRouter()

# Restaurant CRUD Operations
@router.post("/")
async def create_restaurant(restaurant: Restaurant):
    result = await db.restaurants.insert_one(restaurant.dict())
    return {"id": str(result.inserted_id)}

@router.get("/")
async def get_restaurants():
    restaurants = await db.restaurants.find().to_list(100)
    return [obj_to_str(rest) for rest in restaurants]

@router.get("/{restaurant_id}")
async def get_restaurant(restaurant_id: str):
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if restaurant:
        return obj_to_str(restaurant)
    raise HTTPException(status_code=404, detail="Restaurant not found")

# Menu Operations within a Restaurant
@router.post("/{restaurant_id}/menus")
async def create_menu(restaurant_id: str, menu: Menu):
    # Create a unique ID for the menu
    menu_with_id = {**menu.dict(), "id": str(ObjectId())}
    
    result = await db.restaurants.update_one(
        {"_id": ObjectId(restaurant_id)},
        {"$push": {"menus": menu_with_id}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    return {"message": "Menu added successfully", "menu_id": menu_with_id["id"]}

@router.get("/{restaurant_id}/menus")
async def get_menus(restaurant_id: str):
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant.get("menus", [])

@router.post("/{restaurant_id}/menus/{menu_id}/categories")
async def add_category(restaurant_id: str, menu_id: str, category: Category):
    # Find the restaurant by restaurant_id
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Find the menu by menu_id
    menu = next((menu for menu in restaurant["menus"] if menu["id"] == menu_id), None)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Add the category to the menu
    new_category = category.dict()
    menu["categories"].append(new_category)

    # Update the restaurant document with the new category
    await db.restaurants.update_one({"_id": ObjectId(restaurant_id)}, {"$set": {"menus": restaurant["menus"]}})

    return {"message": "Category added successfully"}

@router.put("/{restaurant_id}/menus/{menu_id}/categories/{category_index}")
async def update_category(restaurant_id: str, menu_id: str, category_index: int, updated_category: Category):
    # Fetch the restaurant by ID
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Find the menu by menu_id
    menu = next((menu for menu in restaurant["menus"] if menu["id"] == menu_id), None)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Ensure the category index is valid
    if category_index < 0 or category_index >= len(menu["categories"]):
        raise HTTPException(status_code=404, detail="Category not found")

    # Update the category
    menu["categories"][category_index]["name"] = updated_category.name

    # Save the updated menu
    await db.restaurants.update_one({"_id": ObjectId(restaurant_id)}, {"$set": {"menus": restaurant["menus"]}})

    return {"message": "Category updated successfully"}

@router.delete("/{restaurant_id}/menus/{menu_id}/categories/{category_index}")
async def delete_category(restaurant_id: str, menu_id: str, category_index: int):
    # Fetch the restaurant by ID
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Find the menu by menu_id
    menu = next((menu for menu in restaurant["menus"] if menu["id"] == menu_id), None)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Ensure the category index is valid
    if category_index < 0 or category_index >= len(menu["categories"]):
        raise HTTPException(status_code=404, detail="Category not found")

    # Remove the category by index
    del menu["categories"][category_index]

    # Update the restaurant document in the database
    await db.restaurants.update_one(
        {"_id": ObjectId(restaurant_id)}, 
        {"$set": {"menus": restaurant["menus"]}}
    )

    return {"message": "Category deleted successfully"}

@router.get("/{restaurant_id}/menus/{menu_id}/generate_qr")
async def generate_menu_qr(restaurant_id: str, menu_id: str, request: Request):
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    menu = next((menu for menu in restaurant["menus"] if menu["id"] == menu_id), None)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    # Fetch the next ad to insert
    ad = await get_next_ad()

    # Ensure that only the necessary ad information is passed as strings
    ad_name = ad.get("ad_name", "")
    ad_image_url = ad.get("ad_image_url", "")

    # Generate the PDF of the menu with the ad
    pdf_file_path = f"{FILE_DIR}menu_{menu_id}.pdf"
    generate_menu_pdf(menu, ad, pdf_file_path)  # Include the ad name and image URL in the PDF
    
    # URL where the PDF will be served
    base_url = str(request.base_url).rstrip("/")
    pdf_url = f"{base_url}/menus/{menu_id}/download_pdf"
    
    # Generate the QR code linking to the PDF
    qr_file_path = f"{FILE_DIR}qr_{menu_id}.png"
    generate_qr_code(pdf_url, qr_file_path)

    return {
        "message": "QR Code and PDF generated",
        "pdf_url": pdf_url,
        "qr_code_url": f"{base_url}/menus/{menu_id}/download_qr"
    }

@router.put("/{restaurant_id}/menus/{menu_id}")
async def update_menu_name(restaurant_id: str, menu_id: str, data: MenuNameUpdate):
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    menu = next((menu for menu in restaurant["menus"] if menu["id"] == menu_id), None)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    menu["name"] = data.new_name  # Update the menu name
    menu["welcome_text"] = data.welcome_text  # Update the welcome text

    # Save the updated restaurant document
    await db.restaurants.update_one({"_id": ObjectId(restaurant_id)}, {"$set": {"menus": restaurant["menus"]}})

    return {"message": "Menu name and welcome text updated successfully"}

@router.put("/{restaurant_id}")
async def update_restaurant_name(restaurant_id: str, updated_data: dict):
    new_name = updated_data.get("new_name")
    if not new_name:
        raise HTTPException(status_code=400, detail="New name is required")

    # Ensure that restaurant_id is converted to ObjectId
    try:
        object_id = ObjectId(restaurant_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid restaurant ID")

    result = await db.restaurants.update_one(
        {"_id": object_id},
        {"$set": {"name": new_name}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return {"message": "Restaurant name updated successfully"}