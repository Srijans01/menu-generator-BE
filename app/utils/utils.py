import json
from bson import ObjectId
import os
import qrcode
from fastapi import HTTPException
from app.db import db
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Paragraph, Frame, Spacer
from io import BytesIO
from datetime import datetime, timedelta
import random
import requests

# Directory where files (PDFs, QR codes) will be stored
FILE_DIR = './generated_files/'

# Ensure the directory exists
os.makedirs(FILE_DIR, exist_ok=True)

def obj_to_str(obj):
    """Convert non-serializable objects like ObjectId to strings."""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: obj_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [obj_to_str(i) for i in obj]
    else:
        return obj

def json_serialize(data):
    """JSON serialize, converting ObjectId and other non-serializable types to strings."""
    return json.loads(json.dumps(data, default=obj_to_str))


# Generate PDF for the menu using ReportLab
# Generate PDF for the menu using ReportLab
def download_image(url):
    """Download the image from the URL and return a BytesIO object."""
    response = requests.get(url)
    if response.status_code == 200:
        print("response.content is " ,response.content)
        return BytesIO(response.content)  # Returning the image data in BytesIO format
    else:
        raise FileNotFoundError(f"Could not download image from URL: {url}")

def generate_menu_pdf(menu_data, ad_data, file_path, welcome_text="Welcome to our restaurant. Enjoy the best dishes!"):
    # Ensure file_path is not None
    if not file_path:
        raise ValueError("File path is required to generate the PDF")

    # Create the PDF canvas
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter  # Dimensions of the PDF page

    # Define padding for all sides
    padding = 100  # Adjust padding as necessary for your design

    # Calculate the vertical position for the title (centered with padding)
    title_y_position = height - padding - (height - 2 * padding) / 2

    # Draw the Menu Title (Centered on the first page with padding)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width / 2, title_y_position, menu_data.get('name', 'Menu'))

    # Draw the custom welcome message centered below the title
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, title_y_position - 40, welcome_text)

    # Leave the first page with only the title
    c.showPage()  # New page after title
    
    # If ad_data exists, render the ad on the second page
    if ad_data:
        c.setFont("Helvetica-Bold", 24)
        if isinstance(ad_data, dict):
            # Render the ad details if it's a dictionary
            ad_name = ad_data.get('ad_name', 'Ad')
            c.drawCentredString(width / 2, height - padding, f"Sponsored Ad: {ad_name}")
            
            # Insert ad image (if provided)
            ad_image_url = ad_data.get('ad_image_url', '')
            print("trying outside ad_image_url" , ad_image_url)
            if ad_image_url:
                try:
                    print("trying in ad_image_url" , ad_image_url)
                    # Download the image and draw it in the PDF
                    image_data = download_image(ad_image_url)  # Get the image as a byte stream
                    image = ImageReader(image_data)
                    image_width, image_height = 200, 150  # Set image dimensions
                    x_position = (width - image_width) / 2  # Center image horizontally
                    y_position = height - padding - 200  # Position image below the title
                    c.drawImage(image, x_position, y_position, width=image_width, height=image_height)  # Pass the image byte stream
                except FileNotFoundError as e:
                    c.drawCentredString(width / 2, height - padding - 40, f"Image not available: {str(e)}")
            
            # Loop through metadata to display the ad details
            c.setFont("Helvetica", 12)
            y_position = height - padding - 40
            metadata = ad_data.get('metadata', {})
            for key, value in metadata.items():
                c.drawCentredString(width / 2, y_position, f"{key}: {value}")
                y_position -= 20

        elif isinstance(ad_data, str):
            # If ad_data is a simple string, render it as a message
            c.drawCentredString(width / 2, height - padding, ad_data)

        c.showPage()  # New page after ad

    # Render each category on a new page
    for category in menu_data.get("categories", []):
        # Category title (centered on each new page with padding)
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(width / 2, height - padding, category.get('name', 'Unnamed Category'))

        # Space between the category title and the first dish
        y_position = height - padding - 50
        c.setFont("Helvetica", 16)

        # Render dishes
        for dish in category.get("dishes", []):
            if y_position < padding:  # Start a new page if running out of space
                c.showPage()
                y_position = height - padding - 50

            dish_name = dish.get('name', 'Unnamed Dish')
            dish_price = dish.get('price', 'N/A')

            # Draw the dish name on the left and the price on the right
            c.drawString(padding, y_position, dish_name)
            c.drawRightString(width - padding, y_position, f"${dish_price:.2f}")

            # Optional: Draw separator line between dishes
            y_position -= 25
            c.setStrokeColor(colors.grey)
            c.line(padding, y_position, width - padding, y_position)
            y_position -= 20  # Add space after separator

        # Add a new page after each category
        c.showPage()

    # Save the PDF
    c.save()  
# Generate a QR code
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

ROTATION_PERIOD_SECONDS = 300

async def get_next_ad():
    # Fetch all ads sorted by bid_price (desc) and last_served (asc)
    ads = await db.ads.find().sort([("bid_price", -1), ("last_served", 1)]).to_list(100)
    
    # Check if any ad meets the rotation period criteria
    current_time = datetime.utcnow()
    eligible_ad = None

    for ad in ads:
        if ad['last_served'] is None or (current_time - ad['last_served']).total_seconds() >= ROTATION_PERIOD_SECONDS:
            eligible_ad = ad
            break
    
    # If no ad meets the primary criteria, use the highest bid_price ad regardless of last_served
    if not eligible_ad:
        eligible_ad = ads[0] if ads else None

    if not eligible_ad:
        raise HTTPException(status_code=404, detail="No ads available")

    # Update the selected ad's last_served and increment impression count
    await db.ads.update_one(
        {"_id": eligible_ad["_id"]},
        {"$set": {"last_served": current_time}, "$inc": {"impression_count": 1}}
    )

    return eligible_ad