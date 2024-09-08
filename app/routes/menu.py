from app.db import db
from fastapi import APIRouter, HTTPException
from bson import ObjectId
import qrcode
import pdfkit
import os
from fastapi.responses import FileResponse
from app.models import Menu  # Assuming Menu is also needed for menu routes
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

router = APIRouter()

# Directory where PDF and QR codes are saved
FILE_DIR = './generated_files/'

# Ensure the directory exists
os.makedirs(FILE_DIR, exist_ok=True)

@router.post("/{restaurant_id}/menus")
async def create_menu(restaurant_id: str, menu: Menu):
    try:
        restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        result = await db.restaurants.update_one(
            {"_id": ObjectId(restaurant_id)},
            {"$push": {"menus": menu.dict()}}
        )
        return {"message": "Menu added successfully", "menu_id": menu.name}
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{restaurant_id}/menus")
async def get_menus(restaurant_id: str):
    restaurant = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant.get("menus", [])

# Generate PDF for the menu using ReportLab
def generate_menu_pdf(menu_data, file_path):
    c = canvas.Canvas(file_path, pagesize=letter)
    
    # Add menu name and handle missing 'location'
    c.drawString(100, 750, f"Menu Name: {menu_data.get('name', 'Unknown Menu')}")
    
    # Since 'location' is not part of 'menu_data', default to a fallback value
    c.drawString(100, 730, "Location: Location not specified")  # Hardcoded fallback value

    y = 700
    # Add categories and dishes
    for category in menu_data.get("categories", []):
        c.drawString(100, y, f"Category: {category.get('name', 'Unnamed Category')}")
        y -= 20
        for dish in category.get("dishes", []):
            c.drawString(120, y, f"Dish: {dish.get('name', 'Unnamed Dish')}, Price: {dish.get('price', 'N/A')}")
            y -= 20

    c.save()

# Generate QR code
def generate_qr_code(url, file_path):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save(file_path)

# Endpoint to download the generated PDF
@router.get("/menus/{menu_id}/download_pdf")
async def download_pdf(menu_id: str):
    pdf_file_path = f"{FILE_DIR}menu_{menu_id}.pdf"
    if not os.path.exists(pdf_file_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(pdf_file_path, media_type='application/pdf')

# Endpoint to download the generated QR code
@router.get("/{menu_id}/download_qr")
async def download_qr(menu_id: str):
    qr_file_path = f"{FILE_DIR}qr_{menu_id}.png"
    if not os.path.exists(qr_file_path):
        raise HTTPException(status_code=404, detail="QR Code not found")
    print(f"Serving QR code from {qr_file_path}")  # Debug: Add this line to check the path
    return FileResponse(qr_file_path, media_type='image/png')
