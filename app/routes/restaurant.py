from fastapi import APIRouter, HTTPException
from app.models import Restaurant, Menu, Category, Dish
from app.db import db
from bson import ObjectId
from app.utils.utils import obj_to_str,generate_menu_pdf, generate_qr_code,FILE_DIR

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
async def generate_menu_qr(restaurant_id: str, menu_id: str):
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    menu = next((menu for menu in restaurant["menus"] if menu["id"] == menu_id), None)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Generate the PDF of the menu
    pdf_file_path = f"{FILE_DIR}menu_{menu_id}.pdf"
    generate_menu_pdf(menu, pdf_file_path)

    # URL where the PDF will be served
    pdf_url = f"http://127.0.0.1:8000/menus/{menu_id}/download_pdf"

    # Generate the QR code linking to the PDF
    qr_file_path = f"{FILE_DIR}qr_{menu_id}.png"
    generate_qr_code(pdf_url, qr_file_path)

    return {
        "message": "QR Code and PDF generated",
        "pdf_url": pdf_url,
        "qr_code_url": f"http://127.0.0.1:8000/menus/{menu_id}/download_qr"
    }