import json
from bson import ObjectId
import os
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Paragraph, Frame, Spacer

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
def generate_menu_pdf(menu_data, file_path):
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter  # Dimensions of the PDF page

    # Set up styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.alignment = TA_CENTER
    
    subtitle_style = styles['Heading2']
    subtitle_style.alignment = TA_CENTER
    
    dish_style = styles['Normal']

    # Draw the Menu Title (First Page)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width / 2, height - 100, menu_data.get('name', 'Menu'))
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 120, "Welcome to our restaurant. Enjoy the best dishes!")

    c.showPage()  # New page after title

    # Render each category on a new page
    for category in menu_data.get("categories", []):
        # Category title
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(width / 2, height - 100, category.get('name', 'Unnamed Category'))

        # Add space between category and dishes
        y_position = height - 150
        c.setFont("Helvetica", 16)
        
        # Render dishes
        for dish in category.get("dishes", []):
            if y_position < 100:  # Start a new page if running out of space
                c.showPage()
                y_position = height - 150

            dish_name = dish.get('name', 'Unnamed Dish')
            dish_price = dish.get('price', 'N/A')

            # Draw the dish name on the left and the price on the right
            c.drawString(100, y_position, dish_name)
            c.drawRightString(width - 100, y_position, f"${dish_price:.2f}")

            # Optional: Draw separator line between dishes
            y_position -= 25
            c.setStrokeColor(colors.grey)
            c.line(100, y_position, width - 100, y_position)
            y_position -= 20  # Add space after separator

        # Add a new page after each category
        c.showPage()

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
