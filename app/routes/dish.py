from fastapi import APIRouter,HTTPException
from app.models import Restaurant, Menu, Category, Dish
from app.db import db
from bson import ObjectId
from app.utils.utils import obj_to_str

router = APIRouter()

@router.get("/")
async def get_dishes():
    return {"message": "This is a dish route"}

@router.post("/")
async def create_dish(name: str, price: float):
    return {"message": f"Dish {name} with price {price} created"}

@router.post("/restaurants/{restaurant_id}/menus/{menu_id}/categories/{category_name}/dishes")
async def add_dish(restaurant_id: str, menu_id: str, category_name: str, dish: Dish):
    print(f"Received request to add dish to category: {category_name} in menu: {menu_id} for restaurant: {restaurant_id}")
    # Fetch the restaurant by ID
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Find the menu by menu_id
    menu = next((menu for menu in restaurant["menus"] if menu["id"] == menu_id), None)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Find the category by name
    category = next((cat for cat in menu["categories"] if cat["name"] == category_name), None)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Add the new dish to the category
    new_dish = dish.dict()
    category["dishes"].append(new_dish)

    # Update the restaurant document in the database
    await db.restaurants.update_one(
        {"_id": ObjectId(restaurant_id)},
        {"$set": {"menus": restaurant["menus"]}}
    )

    return new_dish

@router.delete("/restaurants/{restaurant_id}/menus/{menu_id}/categories/{category_name}/dishes/{dish_index}")
async def delete_dish(restaurant_id: str, menu_id: str, category_name: str, dish_index: int):
    # Fetch the restaurant by ID
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Find the menu by menu_id
    menu = next((menu for menu in restaurant["menus"] if menu["id"] == menu_id), None)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Find the category by name
    category = next((cat for cat in menu["categories"] if cat["name"] == category_name), None)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Ensure the dish index is valid
    if dish_index < 0 or dish_index >= len(category["dishes"]):
        raise HTTPException(status_code=404, detail="Dish not found")

    # Remove the dish
    category["dishes"].pop(dish_index)

    # Update the restaurant document in the database
    await db.restaurants.update_one(
        {"_id": ObjectId(restaurant_id)},
        {"$set": {"menus": restaurant["menus"]}}
    )

    return {"message": "Dish deleted successfully"}


@router.put("/restaurants/{restaurant_id}/menus/{menu_id}/categories/{category_name}/dishes/{dish_index}")
async def update_dish(restaurant_id: str, menu_id: str, category_name: str, dish_index: int, updated_dish: Dish):
    # Fetch the restaurant by ID
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Find the menu by menu_id
    menu = next((menu for menu in restaurant["menus"] if menu["id"] == menu_id), None)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Find the category by name
    category = next((cat for cat in menu["categories"] if cat["name"] == category_name), None)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Ensure the dish index is valid
    if dish_index < 0 or dish_index >= len(category["dishes"]):
        raise HTTPException(status_code=404, detail="Dish not found")

    # Update the dish information
    category["dishes"][dish_index] = updated_dish.dict()

    # Update the restaurant document in the database
    await db.restaurants.update_one(
        {"_id": ObjectId(restaurant_id)},
        {"$set": {"menus": restaurant["menus"]}}
    )

    return {"message": "Dish updated successfully"}
