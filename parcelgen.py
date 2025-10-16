import os
import random
import datetime
import qrcode
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont, ImageEnhance # Added ImageEnhance here
import numpy as np
import string
import json
from faker import Faker

# Flask imports
from flask import Flask, jsonify, send_from_directory, render_template, request

# Initialize Flask App
app = Flask(__name__, template_folder='.', static_folder='simulation') # Assuming parcelgen.html is in the same directory as parcelgen.py

# Ensure the output directory exists
INCOMING_IMAGES_DIR = os.path.join('simulation', 'incoming_images')
os.makedirs(INCOMING_IMAGES_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
# Define font paths and provide fallbacks
FONT_DIR = os.path.join(BASE_DIR, 'fonts')
os.makedirs(INCOMING_IMAGES_DIR, exist_ok=True)
os.makedirs(FONT_DIR, exist_ok=True)
FONT_PATH = {
    'regular': os.path.join(FONT_DIR, 'Arial.ttf'), # Assuming Arial.ttf is in a 'fonts' subdirectory
    'bold': os.path.join(FONT_DIR, 'Arial_Bold.ttf')   # Assuming Arial_Bold.ttf is in a 'fonts' subdirectory
}

# ---- (Your existing functions: fake, PH_LOCATION_DATA, generate_address, etc.) ----
# (Make sure to place all your existing helper functions here)

# Initialize Faker with Philippines locale
fake = Faker(['en_PH'])

# Load Philippines cities and barangays
# This is a simplified list - in a production environment, you'd use a more comprehensive dataset
# More accurate Philippines location data
PH_LOCATION_DATA = [
    # Metro Manila
    {"city": "Manila", "zip_codes": ["1000", "1001", "1002", "1004", "1005", "1006", "1007", "1008", "1009"],
     "barangays": ["Binondo", "Ermita", "Intramuros", "Malate", "Paco", "Pandacan", "Port Area", "Quiapo", "Sampaloc", "San Andres", "San Miguel", "San Nicolas", "Santa Ana", "Santa Cruz", "Santa Mesa", "Tondo"]},
    
    {"city": "Quezon City", "zip_codes": ["1100", "1101", "1102", "1103", "1104", "1105", "1106", "1107", "1108", "1109", "1110", "1111", "1112", "1113", "1114", "1115", "1116", "1117", "1118", "1119", "1120", "1121"],
     "barangays": ["Alicia", "Bagong Lipunan ng Crame", "Bagumbayan", "Bahay Toro", "Balingasa", "Balong Bato", "Batasan Hills", "Bayanihan", "Blue Ridge", "Botocan", "Bungad", "Camp Aguinaldo", "Central", "Commonwealth", "Culiat", "Damar", "Damayan", "Diliman", "Doña Imelda", "Doña Josefa", "Don Manuel", "East Kamias"]},
    
    {"city": "Makati", "zip_codes": ["1200", "1201", "1202", "1203", "1204", "1205", "1206", "1207", "1208", "1209", "1210", "1211", "1212", "1213", "1214", "1215", "1216", "1217", "1218", "1219", "1220", "1221", "1222", "1223", "1224", "1225", "1226", "1227", "1228", "1229", "1230", "1231", "1232"],
     "barangays": ["Bangkal", "Bel-Air", "Carmona", "Cembo", "Comembo", "Dasmariñas", "East Rembo", "Forbes Park", "Guadalupe Nuevo", "Guadalupe Viejo", "Kasilawan", "La Paz", "Magallanes", "Olympia", "Palanan", "Pembo", "Pinagkaisahan", "Pio del Pilar", "Poblacion", "Post Proper Northside", "Post Proper Southside", "Rizal", "San Antonio", "San Isidro", "San Lorenzo", "Santa Cruz", "Singkamas", "South Cembo", "Tejeros", "Urdaneta", "Valenzuela", "West Rembo"]},
    
    {"city": "Pasig", "zip_codes": ["1600", "1601", "1602", "1603", "1604", "1605", "1606", "1607", "1608", "1609", "1610", "1611", "1612", "1613", "1614", "1615", "1616"],
     "barangays": ["Bagong Ilog", "Bagong Katipunan", "Bambang", "Buting", "Caniogan", "Dela Paz", "Kalawaan", "Kapasigan", "Kapitolyo", "Malinao", "Manggahan", "Maybunga", "Oranbo", "Palatiw", "Pinagbuhatan", "Pineda", "Rosario", "Sagad", "San Antonio", "San Joaquin", "San Jose", "San Miguel", "San Nicolas", "Santa Cruz", "Santa Lucia", "Santa Rosa", "Santo Tomas", "Santolan", "Sumilang", "Ugong"]},
    
    {"city": "Taguig", "zip_codes": ["1630", "1631", "1632", "1633", "1634", "1635", "1636", "1637", "1638", "1639"],
     "barangays": ["Bagumbayan", "Bambang", "Calzada", "Central Bicutan", "Central Signal Village", "Fort Bonifacio", "Hagonoy", "Ibayo-Tipas", "Katuparan", "Ligid-Tipas", "Lower Bicutan", "Maharlika Village", "Napindan", "New Lower Bicutan", "North Daang Hari", "North Signal Village", "Palingon", "San Miguel", "Santa Ana", "South Daang Hari", "South Signal Village", "Tanyag", "Tuktukan", "Upper Bicutan", "Ususan", "Wawa", "Western Bicutan"]},
    
    {"city": "Parañaque", "zip_codes": ["1700", "1701", "1702", "1703", "1704", "1705", "1706", "1707", "1708", "1709", "1710", "1711", "1712", "1713", "1714", "1715", "1716"],
     "barangays": ["Baclaran", "BF Homes", "Don Bosco", "Don Galo", "La Huerta", "Marcelo Green Village", "Merville", "Moonwalk", "San Antonio", "San Dionisio", "San Isidro", "San Martin de Porres", "Santo Niño", "Sun Valley", "Tambo", "Vitalez"]},
    
    {"city": "Cebu City", "zip_codes": ["6000", "6001", "6002", "6003", "6004", "6005"],
     "barangays": ["Adlaon", "Agsungot", "Apas", "Babag", "Bacayan", "Banilad", "Basak Pardo", "Basak San Nicolas", "Binaliw", "Bonbon", "Budlaan", "Buhisan", "Bulacao", "Buot", "Busay", "Calamba", "Cambinocot", "Capitol Site", "Carreta", "Cogon Pardo", "Cogon Ramos", "Day-as", "Duljo Fatima", "Ermita", "Guadalupe", "Guba", "Hipodromo", "Inayawan", "Kalubihan", "Kamagayan"]},
    
    {"city": "Davao City", "zip_codes": ["8000", "8001", "8002", "8003", "8004", "8005", "8006", "8007", "8008", "8009", "8010", "8011", "8012"],
     "barangays": ["1-A", "2-A", "3-A", "4-A", "5-A", "6-A", "7-A", "8-A", "9-A", "10-A", "11-B", "12-B", "13-B", "14-B", "15-B", "16-B", "17-B", "18-B", "19-B", "20-B", "21-C", "22-C", "23-C", "24-C", "25-C", "26-C", "27-C", "28-C", "29-C", "30-C", "Angalan", "Bago Aplaya", "Bago Gallera", "Bago Oshiro", "Balengaeng", "Baliok", "Bangkas Heights"]},
    
    # Luzon provinces
    {"city": "Baguio City", "zip_codes": ["2600", "2601", "2602", "2603"],
     "barangays": ["Abanao-Zandueta-Kayeng-Chugum", "Ambiong", "Andres Bonifacio", "Apugan-Loakan", "Asin Road", "Atok Trail", "Aurora Hill North", "Aurora Hill Proper", "Aurora Hill South", "Bagong Lipunan", "Bakakeng Central", "Bakakeng North", "Bakakeng South", "Balsigan", "Brookside", "Cabinet Hill-Teachers Camp", "Camdas Subdivision", "Camp 7", "Camp 8", "Camp Allen"]},
    
    {"city": "Batangas City", "zip_codes": ["4200", "4201", "4202", "4203", "4204", "4205"],
     "barangays": ["Alangilan", "Balagtas", "Balete", "Banaba Center", "Banaba East", "Banaba West", "Barangay 1", "Barangay 2", "Barangay 3", "Barangay 4", "Barangay 5", "Barangay 6", "Barangay 7", "Barangay 8", "Barangay 9", "Barangay 10", "Barangay 11", "Barangay 12", "Barangay 13", "Barangay 14", "Barangay 15", "Barangay 16"]},
    
    # Visayas
    {"city": "Iloilo City", "zip_codes": ["5000", "5001", "5002", "5003", "5004"],
     "barangays": ["Aguinaldo", "Airport", "Alalasan", "Arsenal Aduana", "Baldoza", "Bantud", "Baybay Tanza", "Bolong Oeste", "Bolong Este", "Bolilao", "Buhang", "Buntatala", "Buntala", "Bito-on", "Calumpang", "Calaparan", "Cochero", "Compania", "Concepcion", "Cuartero", "Danao", "Del Rosario"]},
    
    # Mindanao
    {"city": "Cagayan de Oro", "zip_codes": ["9000", "9001", "9002", "9003", "9004", "9005", "9006", "9007", "9008", "9009", "9010", "9011", "9012", "9013", "9014"],
     "barangays": ["Agusan", "Baikingon", "Balubal", "Balulang", "Barangay 1", "Barangay 2", "Barangay 3", "Barangay 4", "Barangay 5", "Barangay 6", "Barangay 7", "Barangay 8", "Barangay 9", "Barangay 10", "Barangay 11", "Barangay 12", "Barangay 13", "Barangay 14", "Barangay 15", "Barangay 16", "Barangay 17", "Barangay 18", "Barangay 19", "Barangay 20"]}
]

def generate_address():
    """Generate a realistic Philippine address with matching city, barangay and ZIP code"""
    # Select a random location
    location = random.choice(PH_LOCATION_DATA)
    
    # Get city and a matching ZIP code
    city = location["city"]
    zip_code = random.choice(location["zip_codes"])
    
    # Get a barangay for this city
    barangay = random.choice(location["barangays"])
    
    # Generate house number and street
    house_number = random.randint(1, 9999)
    
    # Create more realistic street names
    street_types = ["Street", "Avenue", "Road", "Boulevard", "Drive", "Lane", "Highway"]
    street_names = [
        "Rizal", "Bonifacio", "Mabini", "Aguinaldo", "Quezon", "Sampaguita", "Orchid", 
        "Ilang-Ilang", "Magsaysay", "Roxas", "Laurel", "Jacinto", "Luna", "Malvar",
        "Ramos", "Quirino", "Osmena", "Escoda", "Katipunan", "Legarda", "Lacson",
        "Taft", "Burgos", "Del Pilar", "Zamora", "Gomez", "Aquino", "Malakas",
        "Maginhawa", "Matimtiman", "Maharlika", "Magallanes", "Lapu-Lapu", "Tandang Sora"
    ]
    
    street = f"{random.choice(street_names)} {random.choice(street_types)}"
    
    # Determine province based on city
    # (This is simplified; in reality, you'd have a proper mapping)
    province_mapping = {
        "Manila": "Metro Manila",
        "Quezon City": "Metro Manila",
        "Makati": "Metro Manila",
        "Pasig": "Metro Manila",
        "Taguig": "Metro Manila",
        "Parañaque": "Metro Manila",
        "Cebu City": "Cebu",
        "Davao City": "Davao del Sur",
        "Baguio City": "Benguet",
        "Batangas City": "Batangas",
        "Iloilo City": "Iloilo",
        "Cagayan de Oro": "Misamis Oriental"
    }
    
    province = province_mapping.get(city, fake.administrative_unit())
    
    # Some Filipino address conventions
    lot_block = ""
    if random.random() < 0.3:  # 30% chance of having a lot/block format
        lot_block = f"Lot {random.randint(1, 50)} Block {random.randint(1, 50)}, "
    
    subdivision = ""
    if random.random() < 0.4:  # 40% chance of being in a subdivision
        subdivisions = [
            "Green Heights Subdivision", "Villa Esperanza", "San Lorenzo Village",
            "Valle Verde", "Camella Homes", "SM Residences", "Ayala Heights",
            "Filinvest Homes", "Ciudad Verde", "Crown Asia", "South Crest Village",
            "North View Homes", "East Bay Residences", "West Gate Subdivision",
            "Royal Palm Residences", "Golden Haven", "Emerald Estate", "Diamond Village"
        ]
        subdivision = f"{random.choice(subdivisions)}, "
    
    # Format the address with Filipino style
    if lot_block:
        formatted = f"{lot_block}{street}, {subdivision}Brgy. {barangay}, {city}, {province}, {zip_code}"
    else:
        formatted = f"{house_number} {street}, {subdivision}Brgy. {barangay}, {city}, {province}, {zip_code}"
    
    address = {
        'house_number': house_number,
        'street': street,
        'barangay': barangay,
        'city': city,
        'province': province,
        'zip_code': zip_code,
        'formatted': formatted
    }
    
    return address

# Text generation functions for more realistic data
def generate_tracking_number(courier):
    """Generate a realistic tracking number based on courier format"""
    if courier == "shopee":
        return f"SPX{fake.bothify('PH?##?#')}{''.join(random.choices(string.digits, k=10))}"
    elif courier == "lazada":
        return f"LZD-PH-{''.join(random.choices(string.digits, k=12))}"
    elif courier == "lalamove":
        return f"LLM{''.join(random.choices(string.digits + string.ascii_uppercase, k=12))}"
    elif courier == "jnt":
        return f"JX{''.join(random.choices(string.digits, k=12))}"
    elif courier == "ninjavan":
        return f"NINJAVAN{''.join(random.choices(string.digits, k=10))}"
    else:
        return f"TRK{''.join(random.choices(string.digits, k=14))}"

def generate_order_id(courier):
    """Generate order ID based on courier"""
    if courier == "shopee":
        return f"S{''.join(random.choices(string.digits, k=16))}"
    elif courier == "lazada":
        return f"L{''.join(random.choices(string.digits, k=12))}"
    else:
        return f"ORD{''.join(random.choices(string.digits, k=10))}"

def generate_phone_number():
    """Generate realistic Philippine phone number"""
    prefix = random.choice(['0917', '0918', '0919', '0920', '0921', '0922', '0923', '0927', '0928', '0929'])
    return f"{prefix}{''.join(random.choices(string.digits, k=7))}"

def generate_amount():
    """Generate a realistic amount for COD or package value"""
    # Most common price points in e-commerce
    if random.random() < 0.7:  # 70% chance for common price range
        return round(random.uniform(100, 5000), 2)
    else:  # 30% chance for higher value items
        return round(random.uniform(5001, 50000), 2)

def generate_weight():
    """Generate package weight"""
    # Most parcels are lightweight
    if random.random() < 0.8:  # 80% chance for lightweight
        return round(random.uniform(0.1, 5), 2)
    else:  # 20% chance for heavier packages
        return round(random.uniform(5.1, 20), 2)

def generate_dates():
    """Generate shipping and expected delivery dates"""
    today = datetime.datetime.now()
    
    # Shipping date (today or within last 3 days)
    ship_date = today - datetime.timedelta(days=random.randint(0, 3))
    
    # Expected delivery (2-7 days after shipping)
    delivery_date = ship_date + datetime.timedelta(days=random.randint(2, 7))
    
    return ship_date, delivery_date

def generate_receipt_data(courier):
    """Generate a complete data object for a receipt"""
    ship_date, delivery_date = generate_dates()
    
    data = {
        'tracking_number': generate_tracking_number(courier),
        'order_id': generate_order_id(courier),
        'recipient_name': fake.name(),
        'recipient_address': generate_address(),
        'contact_number': generate_phone_number(),
        'shipping_provider': courier.upper(),
        'payment_type': random.choice(['COD', 'Prepaid']),
        'amount': generate_amount(),
        'weight': generate_weight(),
        'date_shipped': ship_date.strftime('%Y-%m-%d'),
        'expected_delivery': delivery_date.strftime('%Y-%m-%d'),
        'package_type': random.choice(['Parcel', 'Document', 'Box', 'Pouch']),
        'seller_name': fake.company(),
        'rider_name': fake.name()
    }
    
    return data

# Barcode and QR code generation functions
def generate_barcode(data, barcode_type='code128'):
    """Generate a barcode image for tracking number"""
    # Create a unique temporary filename to avoid conflicts
    temp_dir = os.path.join(os.getcwd(), 'temp_barcodes')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Use a timestamp to create a unique filename
    unique_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    temp_filename = os.path.join(temp_dir, f'barcode_{unique_id}')
    
    try:
        # Generate the barcode
        barcode_class = barcode.get_barcode_class(barcode_type)
        code = barcode_class(data, writer=ImageWriter())
        
        # Get the full filename after save (with extension)
        full_filename = code.save(temp_filename)
        
        # Open the image
        barcode_img = Image.open(full_filename)
        
        # Make a copy of the image before deleting the file
        barcode_copy = barcode_img.copy()
        
        # Clean up
        barcode_img.close()
        os.remove(full_filename)
        
        return barcode_copy
    except Exception as e:
        print(f"Error generating barcode: {e}")
        # Create a fallback barcode image as text
        fallback_img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(fallback_img)
        # Ensure a font is loaded for fallback text
        try:
            font = ImageFont.truetype(FONT_PATH['regular'], 20)
        except:
            font = ImageFont.load_default()
        draw.text((20, 40), f"BARCODE: {data}", fill='black', font=font)
        return fallback_img

def generate_qr_code(data):
    """Generate a QR code image for the data"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    return qr.make_image(fill_color="black", back_color="white")

# Improved font loading function with better fallbacks
def load_fonts():
    """Load fonts with fallbacks for better OCR readability"""
    # Try to load Arial from the specified FONT_PATH first
    try:
        header_font = ImageFont.truetype(FONT_PATH['bold'], 48)
        title_font = ImageFont.truetype(FONT_PATH['bold'], 36)
        normal_font = ImageFont.truetype(FONT_PATH['regular'], 30)
        small_font = ImageFont.truetype(FONT_PATH['regular'], 24)
        return header_font, title_font, normal_font, small_font
    except IOError:
        print(f"Could not load custom fonts from {FONT_PATH}. Trying system fonts or default.")


    # Fallback font loading logic (same as your original, but ensure it's robust)
    system_font_paths = {
        'regular': ['Arial.ttf', 'DejaVuSans.ttf', 'LiberationSans-Regular.ttf'],
        'bold': ['Arialbd.ttf', 'arialbd.ttf', 'DejaVuSans-Bold.ttf', 'LiberationSans-Bold.ttf']
    }
    
    found_regular = None
    found_bold = None

    # Search for system fonts in common locations
    font_dirs = []
    if os.name == 'nt': # Windows
        font_dirs.append(os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'))
    elif os.name == 'posix': # Linux, macOS
        font_dirs.extend(['/usr/share/fonts/truetype/', '/usr/local/share/fonts/', '~/Library/Fonts/', '/Library/Fonts/'])

    for style, names in system_font_paths.items():
        for name in names:
            for dir_path in font_dirs:
                font_file = os.path.join(os.path.expanduser(dir_path), name)
                if os.path.exists(font_file):
                    if style == 'regular' and not found_regular:
                        found_regular = font_file
                    elif style == 'bold' and not found_bold:
                        found_bold = font_file
            if found_regular and found_bold:
                break
        if found_regular and found_bold:
                break
    
    try:
        if found_bold and found_regular:
            print(f"Using system fonts: Bold='{found_bold}', Regular='{found_regular}'")
            header_font = ImageFont.truetype(found_bold, 48)
            title_font = ImageFont.truetype(found_bold, 36)
            normal_font = ImageFont.truetype(found_regular, 30)
            small_font = ImageFont.truetype(found_regular, 24)
            return header_font, title_font, normal_font, small_font
        else:
            raise IOError("System fonts not found.")
    except Exception as e:
        print(f"Error loading system fonts: {e}. Falling back to default PIL font.")
        default_font = ImageFont.load_default()
        return default_font, default_font, default_font, default_font


# Receipt template generators
def generate_shopee_receipt(data):
    """Generate a Shopee-style receipt image"""
    # Create a white canvas (portrait receipt)
    width, height = 800, 1200
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Load fonts with better sizes for OCR readability
    header_font, title_font, normal_font, small_font = load_fonts()
    
    # Header with Shopee logo placeholder
    draw.rectangle([0, 0, width, 120], fill=(238, 77, 45))  # Shopee orange
    draw.text((width//2, 60), "SHOPEE", font=header_font, fill='white', anchor="mm")
    
    # Tracking number (large and prominent)
    draw.text((width//2, 170), "TRACKING NUMBER", font=title_font, fill='black', anchor="mm")
    draw.text((width//2, 220), data['tracking_number'], font=header_font, fill=(0, 0, 0), anchor="mm")
    
    # Add high contrast box around tracking number for better OCR
    tracking_text_width = draw.textlength(data['tracking_number'], font=header_font)
    text_height = header_font.getbbox("A")[3] - header_font.getbbox("A")[1] # More accurate height
    
    draw.rectangle([
        (width//2 - tracking_text_width//2 - 10, 220 - text_height//2 - 5),
        (width//2 + tracking_text_width//2 + 10, 220 + text_height//2 + 5)
    ], outline='black', width=2)
    
    # Order information
    draw.text((50, 280), f"Order ID: {data['order_id']}", font=title_font, fill='black')
    draw.text((50, 330), f"Date: {data['date_shipped']}", font=normal_font, fill='black')
    
    # Create a line to separate sections
    draw.line([(50, 370), (width-50, 370)], fill='black', width=2)
    
    # Recipient information
    draw.text((50, 400), "SHIP TO:", font=title_font, fill='black')
    draw.text((50, 440), data['recipient_name'], font=normal_font, fill='black')
    
    # Format address with line breaks for better readability
    address_text = data['recipient_address']['formatted']
    
    # Split long addresses into multiple lines for better OCR
    words = address_text.split()
    address_lines = []
    current_line = "" # Initialize as empty string
    line_height_approx = normal_font.getbbox("A")[3] - normal_font.getbbox("A")[1]


    for word in words:
        # Test if adding the new word exceeds the line width limit
        if draw.textlength(current_line + " " + word, font=normal_font) <= (width - 100): # 50px margin on each side
            if current_line: # Add space if not the first word on the line
                current_line += " " + word
            else:
                current_line = word
        else: # Word doesn't fit, so start a new line
            if current_line: # Add the completed line
                address_lines.append(current_line)
            current_line = word # Start new line with current word
    
    if current_line: # Add any remaining text as the last line
        address_lines.append(current_line)

    
    # Draw each line of the address
    y_offset = 480
    for line in address_lines:
        draw.text((50, y_offset), line, font=normal_font, fill='black')
        y_offset += line_height_approx + 5 # Add some spacing between lines
    
    # Phone number
    draw.text((50, y_offset + 20), f"Contact: {data['contact_number']}", font=normal_font, fill='black')
    
    # Package information
    y_position = y_offset + line_height_approx + 60 # Adjust based on address lines
    draw.line([(50, y_position-20), (width-50, y_position-20)], fill='black', width=2)
    draw.text((50, y_position), "PACKAGE DETAILS:", font=title_font, fill='black')
    draw.text((50, y_position+50), f"Weight: {data['weight']} kg", font=normal_font, fill='black')
    draw.text((50, y_position+100), f"Package Type: {data['package_type']}", font=normal_font, fill='black')
    draw.text((50, y_position+150), f"Expected Delivery: {data['expected_delivery']}", font=normal_font, fill='black')
    
    # Payment information
    y_position = y_position + 200 # Adjust based on package details
    draw.line([(50, y_position-20), (width-50, y_position-20)], fill='black', width=2)
    draw.text((50, y_position), "PAYMENT DETAILS:", font=title_font, fill='black')
    draw.text((50, y_position+50), f"Payment Type: {data['payment_type']}", font=normal_font, fill='black')
    
    if data['payment_type'] == 'COD':
        # Highlight COD amount with a box for better visibility
        cod_text = f"Amount Due: PHP {data['amount']:.2f}"
        cod_text_width = draw.textlength(cod_text, font=normal_font)
        cod_text_height = normal_font.getbbox("A")[3] - normal_font.getbbox("A")[1]
        
        # Draw a light background box for the COD amount
        draw.rectangle([
            (50 - 5, y_position+100 - 5),
            (50 + cod_text_width + 5, y_position+100 + cod_text_height + 5)
        ], fill=(255, 250, 230), outline='black', width=1)
        
        draw.text((50, y_position+100), cod_text, font=normal_font, fill='black')
    
    # Generate and place barcode at the bottom
    barcode_img = generate_barcode(data['tracking_number'])
    barcode_img = barcode_img.resize((int(width*0.8), 120))  # Larger barcode
    
    # Center the barcode
    barcode_pos_y = height - 170 # Position from bottom
    barcode_pos_x = (width - barcode_img.width)//2
    image.paste(barcode_img, (barcode_pos_x, barcode_pos_y))
    
    # Add barcode number under the barcode
    draw.text((width//2, barcode_pos_y + 120 + 10), data['tracking_number'], font=normal_font, fill='black', anchor="mm")
    
    return image

def generate_lazada_receipt(data):
    """Generate a Lazada-style receipt image"""
    # Create a white canvas (portrait receipt)
    width, height = 800, 1200
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Load fonts with better sizes for OCR readability
    header_font, title_font, normal_font, small_font = load_fonts()
    
    # Header with Lazada logo placeholder
    draw.rectangle([0, 0, width, 120], fill=(0, 83, 204))  # Lazada blue
    draw.text((width//2, 60), "LAZADA", font=header_font, fill='white', anchor="mm")
    
    # Tracking number (large and prominent)
    draw.text((width//2, 170), "TRACKING NUMBER", font=title_font, fill='black', anchor="mm")
    draw.text((width//2, 220), data['tracking_number'], font=header_font, fill=(0, 0, 0), anchor="mm")
    
    # Add high contrast box around tracking number for better OCR
    tracking_text_width = draw.textlength(data['tracking_number'], font=header_font)
    text_height = header_font.getbbox("A")[3] - header_font.getbbox("A")[1]
    draw.rectangle([
        (width//2 - tracking_text_width//2 - 10, 220 - text_height//2 - 5),
        (width//2 + tracking_text_width//2 + 10, 220 + text_height//2 + 5)
    ], outline='black', width=2)
    
    # Order information
    draw.text((50, 280), f"Order ID: {data['order_id']}", font=title_font, fill='black')
    draw.text((50, 330), f"Date: {data['date_shipped']}", font=normal_font, fill='black')
    
    # Create a line to separate sections
    draw.line([(50, 370), (width-50, 370)], fill='black', width=2)
    
    # Recipient information
    draw.text((50, 400), "SHIP TO:", font=title_font, fill='black')
    draw.text((50, 440), data['recipient_name'], font=normal_font, fill='black')
    
    # Format address with line breaks for better readability
    address_text = data['recipient_address']['formatted']
    words = address_text.split()
    address_lines = []
    current_line = ""
    line_height_approx = normal_font.getbbox("A")[3] - normal_font.getbbox("A")[1]

    for word in words:
        if draw.textlength(current_line + " " + word, font=normal_font) <= (width - 100):
            if current_line: current_line += " " + word
            else: current_line = word
        else:
            if current_line: address_lines.append(current_line)
            current_line = word
    if current_line: address_lines.append(current_line)
    
    y_offset = 480
    for line in address_lines:
        draw.text((50, y_offset), line, font=normal_font, fill='black')
        y_offset += line_height_approx + 5
    
    # Phone number
    draw.text((50, y_offset + 20), f"Contact: {data['contact_number']}", font=normal_font, fill='black')
    
    # Package information
    y_position = y_offset + line_height_approx + 60
    draw.line([(50, y_position-20), (width-50, y_position-20)], fill='black', width=2)
    draw.text((50, y_position), "PACKAGE DETAILS:", font=title_font, fill='black')
    draw.text((50, y_position+50), f"Weight: {data['weight']} kg", font=normal_font, fill='black')
    draw.text((50, y_position+100), f"Package Type: {data['package_type']}", font=normal_font, fill='black')
    draw.text((50, y_position+150), f"Expected Delivery: {data['expected_delivery']}", font=normal_font, fill='black')
    
    # Payment information with better visual distinction
    y_position = y_position + 200
    draw.line([(50, y_position-20), (width-50, y_position-20)], fill='black', width=2)
    draw.text((50, y_position), "PAYMENT DETAILS:", font=title_font, fill='black')
    draw.text((50, y_position+50), f"Payment Type: {data['payment_type']}", font=normal_font, fill='black')
    
    if data['payment_type'] == 'COD':
        cod_text = f"Amount Due: PHP {data['amount']:.2f}"
        cod_text_width = draw.textlength(cod_text, font=normal_font)
        cod_text_height = normal_font.getbbox("A")[3] - normal_font.getbbox("A")[1]
        draw.rectangle([
            (50 - 5, y_position+100 - 5),
            (50 + cod_text_width + 5, y_position+100 + cod_text_height + 5)
        ], fill=(255, 250, 230), outline='black', width=2)
        draw.text((50, y_position+100), cod_text, font=normal_font, fill='black')
    
    # Generate and place QR code for Lazada (instead of barcode)
    qr_img = generate_qr_code(data['tracking_number'])
    qr_img = qr_img.resize((200, 200))  # Large QR code for better scanning
    
    qr_pos_y = height - 220 # Position from bottom
    qr_pos_x = (width - qr_img.width)//2
    image.paste(qr_img, (qr_pos_x, qr_pos_y))
    
    # Add tracking number under the QR code
    draw.text((width//2, qr_pos_y + 200 + 10), data['tracking_number'], font=normal_font, fill='black', anchor="mm")
    
    return image

def generate_jnt_receipt(data):
    """Generate a J&T Express-style receipt image"""
    width, height = 800, 1200
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    header_font, title_font, normal_font, small_font = load_fonts()

    draw.rectangle([0, 0, width, 120], fill=(224, 36, 36))  # J&T red
    draw.text((width//2, 60), "J&T EXPRESS", font=header_font, fill='white', anchor="mm")
    
    draw.text((width//2, 170), "WAYBILL NUMBER", font=title_font, fill='black', anchor="mm")
    draw.text((width//2, 230), data['tracking_number'], font=header_font, fill=(0, 0, 0), anchor="mm")
    
    tracking_text_width = draw.textlength(data['tracking_number'], font=header_font)
    text_height = header_font.getbbox("A")[3] - header_font.getbbox("A")[1]
    draw.rectangle([
        (width//2 - tracking_text_width//2 - 10, 230 - text_height//2 - 5),
        (width//2 + tracking_text_width//2 + 10, 230 + text_height//2 + 5)
    ], outline='black', width=3)
    
    draw.text((50, 290), f"Order ID: {data['order_id']}", font=title_font, fill='black')
    draw.text((50, 340), f"Date: {data['date_shipped']}", font=normal_font, fill='black')
    draw.line([(50, 380), (width-50, 380)], fill='black', width=3)
    
    draw.text((50, 410), "RECIPIENT:", font=title_font, fill='black')
    draw.text((50, 450), data['recipient_name'], font=normal_font, fill='black')
    
    address_text = data['recipient_address']['formatted']
    words = address_text.split()
    address_lines = []
    current_line = ""
    line_height_approx = normal_font.getbbox("A")[3] - normal_font.getbbox("A")[1]

    for word in words: # Shorter lines for J&T
        if draw.textlength(current_line + " " + word, font=normal_font) <= (width - 100): # Max width of 700px for address lines
            if current_line: current_line += " " + word
            else: current_line = word
        else:
            if current_line: address_lines.append(current_line)
            current_line = word
    if current_line: address_lines.append(current_line)

    y_offset = 490
    for line in address_lines:
        draw.text((50, y_offset), line, font=normal_font, fill='black')
        y_offset += line_height_approx + 5
        
    contact_y = y_offset + 20
    contact_text = f"Contact: {data['contact_number']}"
    contact_width = draw.textlength(contact_text, font=normal_font)
    contact_height = normal_font.getbbox("A")[3] - normal_font.getbbox("A")[1]
    draw.rectangle([
        (50 - 5, contact_y - 5),
        (50 + contact_width + 5, contact_y + contact_height + 5)
    ], outline='black', width=2, fill=(255, 255, 230))
    draw.text((50, contact_y), contact_text, font=normal_font, fill='black')
    
    y_position = contact_y + contact_height + 60
    draw.line([(50, y_position-20), (width-50, y_position-20)], fill='black', width=3)
    draw.text((50, y_position), "PACKAGE DETAILS:", font=title_font, fill='black')
    draw.text((50, y_position+50), f"Weight: {data['weight']} kg", font=normal_font, fill='black')
    draw.text((50, y_position+100), f"Package Type: {data['package_type']}", font=normal_font, fill='black')
    draw.text((50, y_position+150), f"Expected Delivery: {data['expected_delivery']}", font=normal_font, fill='black')
    
    y_position = y_position + 200
    draw.line([(50, y_position-20), (width-50, y_position-20)], fill='black', width=3)
    draw.text((50, y_position), "PAYMENT DETAILS:", font=title_font, fill='black')
    draw.text((50, y_position+50), f"Payment Type: {data['payment_type']}", font=normal_font, fill='black')
    
    if data['payment_type'] == 'COD':
        cod_text = f"COLLECT: PHP {data['amount']:.2f}"
        cod_text_width = draw.textlength(cod_text, font=title_font) # Use title_font for COD amount
        cod_text_height = title_font.getbbox("A")[3] - title_font.getbbox("A")[1]
        draw.rectangle([
            (50 - 10, y_position+100 - 10),
            (50 + cod_text_width + 10, y_position+100 + cod_text_height + 5) # Adjusted height
        ], fill=(255, 240, 200), outline='black', width=3)
        draw.text((50, y_position+100), cod_text, font=title_font, fill='black')
    
    barcode_img = generate_barcode(data['tracking_number'])
    barcode_img = barcode_img.resize((int(width*0.9), 140))
    barcode_pos_y = height - 180
    barcode_pos_x = (width - barcode_img.width)//2
    image.paste(barcode_img, (barcode_pos_x, barcode_pos_y))
    draw.text((width//2, barcode_pos_y + 140 + 10), data['tracking_number'], font=normal_font, fill='black', anchor="mm")
    
    return image

def generate_ninjavan_receipt(data):
    """Generate a Ninja Van-style receipt image"""
    width, height = 800, 1200
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    header_font, title_font, normal_font, small_font = load_fonts()

    draw.rectangle([0, 0, width, 120], fill=(253, 90, 30))  # Ninja Van orange
    draw.text((width//2, 60), "NINJA VAN", font=header_font, fill='white', anchor="mm")
    
    draw.text((width//2, 170), "TRACKING NUMBER", font=title_font, fill='black', anchor="mm")
    
    tracking_text_width = draw.textlength(data['tracking_number'], font=header_font)
    text_height = header_font.getbbox("A")[3] - header_font.getbbox("A")[1]
    draw.rectangle([
        (width//2 - tracking_text_width//2 - 15, 220 - text_height//2 - 10),
        (width//2 + tracking_text_width//2 + 15, 220 + text_height//2 + 10)
    ], fill=(255, 240, 230), outline='black', width=3)
    draw.text((width//2, 220), data['tracking_number'], font=header_font, fill=(0, 0, 0), anchor="mm")
    
    draw.text((50, 290), f"Order ID: {data['order_id']}", font=title_font, fill='black')
    draw.text((50, 340), f"Date: {data['date_shipped']}", font=normal_font, fill='black')
    draw.line([(50, 380), (width-50, 380)], fill='black', width=3)
    
    # Dynamic box height for recipient info
    address_text = data['recipient_address']['formatted']
    words = address_text.split()
    address_lines_count = 0
    current_line_test = ""
    for word in words:
        if draw.textlength(current_line_test + " " + word, font=normal_font) <= (width - 120): # 60px padding for box
             if current_line_test: current_line_test += " " + word
             else: current_line_test = word
        else:
            if current_line_test: address_lines_count +=1
            current_line_test = word
    if current_line_test: address_lines_count +=1
    
    line_height_approx = normal_font.getbbox("A")[3] - normal_font.getbbox("A")[1]
    contact_height = normal_font.getbbox("A")[3] - normal_font.getbbox("A")[1]
    recipient_box_height = 40 + line_height_approx + (address_lines_count * (line_height_approx + 5)) + contact_height + 40 # padding + name + address + contact + padding

    draw.rectangle([(40, 400), (width-40, 400 + recipient_box_height)], outline='black', width=3)
    
    draw.text((50, 410), "SHIP TO:", font=title_font, fill='black')
    draw.text((50, 450), data['recipient_name'], font=normal_font, fill='black')
    
    y_offset = 490
    address_lines = [] # Re-split for drawing
    current_line = ""
    for word in words:
        if draw.textlength(current_line + " " + word, font=normal_font) <= (width - 120):
            if current_line: current_line += " " + word
            else: current_line = word
        else:
            if current_line: address_lines.append(current_line)
            current_line = word
    if current_line: address_lines.append(current_line)

    for line in address_lines:
        draw.text((50, y_offset), line, font=normal_font, fill='black')
        y_offset += line_height_approx + 5
    
    contact_y = y_offset + 20
    contact_text = f"Contact: {data['contact_number']}"
    draw.text((50, contact_y), contact_text, font=normal_font, fill='black')
    
    y_position = 400 + recipient_box_height + 40 # Position after recipient box
    draw.line([(50, y_position-20), (width-50, y_position-20)], fill='black', width=3)
    draw.text((50, y_position), "PACKAGE DETAILS:", font=title_font, fill='black')
    draw.text((50, y_position+50), "Weight:", font=normal_font, fill='black')
    draw.text((250, y_position+50), f"{data['weight']} kg", font=normal_font, fill='black')
    draw.text((50, y_position+100), "Package Type:", font=normal_font, fill='black')
    draw.text((250, y_position+100), f"{data['package_type']}", font=normal_font, fill='black')
    draw.text((50, y_position+150), "Expected Delivery:", font=normal_font, fill='black')
    draw.text((250, y_position+150), f"{data['expected_delivery']}", font=normal_font, fill='black')
    
    # QR code for 2D scanning - position it relative to package details
    qr_img = generate_qr_code(data['tracking_number'])
    qr_img = qr_img.resize((150, 150))
    qr_pos_x = (width - qr_img.width) // 2
    qr_pos_y = y_position + 200 # Below package details
    image.paste(qr_img, (qr_pos_x, qr_pos_y))


    y_position = qr_pos_y + 150 + 30 # After QR code
    draw.line([(50, y_position-20), (width-50, y_position-20)], fill='black', width=3)
    draw.text((50, y_position), "PAYMENT DETAILS:", font=title_font, fill='black')
    draw.text((50, y_position+50), "Payment Type:", font=normal_font, fill='black')
    draw.text((250, y_position+50), f"{data['payment_type']}", font=normal_font, fill='black')
    
    if data['payment_type'] == 'COD':
        cod_text_height = title_font.getbbox("A")[3] - title_font.getbbox("A")[1]
        draw.rectangle([
            (width//2 - 150, y_position+100),
            (width//2 + 150, y_position+100 + cod_text_height + 20) # Adjusted height
        ], fill=(255, 230, 210), outline='black', width=3)
        cod_text = f"PHP {data['amount']:.2f}"
        draw.text((width//2, y_position+100 + (cod_text_height+20)//2 ), cod_text, font=title_font, fill='black', anchor="mm") # Centered vertically
    
    barcode_img = generate_barcode(data['tracking_number'])
    barcode_img = barcode_img.resize((int(width*0.8), 120))
    barcode_pos_y = height - 150 # From bottom
    barcode_pos_x = (width - barcode_img.width)//2
    image.paste(barcode_img, (barcode_pos_x, barcode_pos_y))
    draw.text((width//2, barcode_pos_y + 120 + 10), data['tracking_number'], font=normal_font, fill='black', anchor="mm")
    
    return image

def generate_shipping_label(courier):
    """Generate shipping label based on courier type"""
    data = generate_receipt_data(courier)
    
    if courier.lower() == "shopee": image = generate_shopee_receipt(data)
    elif courier.lower() == "lazada": image = generate_lazada_receipt(data)
    elif courier.lower() == "jnt": image = generate_jnt_receipt(data)
    elif courier.lower() == "ninjavan": image = generate_ninjavan_receipt(data)
    else: image = generate_jnt_receipt(data) # Default
    
    enhancer = ImageEnhance.Contrast(image); image = enhancer.enhance(1.2)
    enhancer = ImageEnhance.Sharpness(image); image = enhancer.enhance(1.5)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f") # Added microseconds for more uniqueness
    filename = f"{courier.lower()}_{timestamp}.png"
    filepath = os.path.join(INCOMING_IMAGES_DIR, filename)
    image.save(filepath)
    print(f"Generated receipt: {filepath}")
    
    json_filename = f"{courier.lower()}_{timestamp}.json"
    json_filepath = os.path.join(INCOMING_IMAGES_DIR, json_filename)
    with open(json_filepath, 'w') as f:
        json.dump(data, f, indent=4)
    
    return filename # Return only filename for web path

# --- Flask Routes ---
@app.route('/parcelgenerator')
def index():
    """Serves the main HTML page."""
    return render_template('parcelgen.html') # Ensure parcelgen.html is in a 'templates' folder or adjust template_folder

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serves images from the simulation/incoming_images directory."""
    return send_from_directory(INCOMING_IMAGES_DIR, filename)

@app.route('/simulate-scan', methods=['POST'])
def simulate_scan_route():
    """Simulates initiating a scan. For now, let's generate a couple of labels."""
    print("Simulating scan...")
    # For demonstration, let's generate one of each label type
    # In a real scenario, this would trigger actual scanning and image capture.
    generated_files = []
    couriers = ["shopee", "lazada"] # Generate two sample images
    for courier in couriers:
        try:
            # Temporarily remove a file if it exists to simulate new scan
            # This is a simple simulation. A real app would handle new scans differently.
            for f in os.listdir(INCOMING_IMAGES_DIR):
                if f.startswith(courier):
                    try:
                        os.remove(os.path.join(INCOMING_IMAGES_DIR, f))
                    except OSError as e:
                        print(f"Error removing old file {f}: {e}")
            
            filename = generate_shipping_label(courier)
            generated_files.append(filename)
        except Exception as e:
            print(f"Error in simulate_scan_route generating {courier} label: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
            
    return jsonify({'status': 'success', 'message': 'Scan initiated, images generated.', 'files': generated_files})

@app.route('/process-parcel', methods=['POST'])
def process_parcel_route():
    """Placeholder for processing a parcel."""
    # This would involve OCR, data extraction, etc.
    # For now, let's just simulate it by perhaps generating another label.
    print("Processing parcel...")
    try:
        filename = generate_shipping_label("jnt") # Generate a J&T label as an example
        return jsonify({'status': 'success', 'message': 'Parcel processing simulated.', 'file': filename})
    except Exception as e:
        print(f"Error in process_parcel_route: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/generate-label', methods=['POST']) # Changed from GET to POST as it's an action
def generate_label_route():
    """Generates a new shipping label for a random courier."""
    print("Generating label...")
    try:
        # You could add logic here to get courier type from request if needed
        # e.g., courier = request.json.get('courier', 'shopee')
        random_courier = random.choice(["shopee", "lazada", "jnt", "ninjavan"])
        filename = generate_shipping_label(random_courier)
        return jsonify({'status': 'success', 'message': f'{random_courier.upper()} label generated.', 'file': filename})
    except Exception as e:
        print(f"Error in generate_label_route: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get-images', methods=['GET'])
def get_images_route():
    """Returns a list of image URLs in the incoming_images directory."""
    try:
        images = [f for f in os.listdir(INCOMING_IMAGES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        # Return paths that the HTML can use (prefixed with the image serving route)
        image_urls = [f'/images/{image_name}' for image_name in images]
        return jsonify(image_urls)
    except Exception as e:
        print(f"Error in get_images_route: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
@app.route('/clear-all-images', methods=['POST']) # New route for clearing backend images
def clear_all_images_route():
    """Clears all images from the simulation/incoming_images directory."""
    print("Clearing all images from backend...")
    cleared_count = 0
    errors = []
    try:
        for filename in os.listdir(INCOMING_IMAGES_DIR):
            file_path = os.path.join(INCOMING_IMAGES_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    cleared_count += 1
                elif os.path.isdir(file_path): # Should not happen if only images are saved
                    # shutil.rmtree(file_path) # Be careful with rmtree
                    pass 
            except Exception as e:
                errors.append(f"Could not delete {filename}: {e}")
        if errors:
            return jsonify({'status': 'partial_success', 'message': f'Cleared {cleared_count} images. Some errors occurred.', 'errors': errors}), 207
        return jsonify({'status': 'success', 'message': f'All {cleared_count} images cleared from backend.'})
    except Exception as e:
        print(f"Error in clear_all_images_route: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Main execution for Flask
if __name__ == "__main__":
    # Ensure the 'fonts' directory exists and create dummy font files if not found,
    # as ImageFont.truetype will error otherwise.
    # This is a simplified solution for local development.
    # In production, ensure fonts are properly deployed.
    os.makedirs(FONT_DIR, exist_ok=True)
    for style, path in FONT_PATH.items():
        if not os.path.exists(path):
            try:
                # Create a very basic dummy font file if the actual one is missing.
                # This is just to prevent ImageFont.truetype from erroring out immediately.
                # It will likely not render text correctly.
                # You SHOULD place actual .ttf files (e.g., Arial.ttf, Arial_Bold.ttf) in the 'fonts' folder.
                print(f"Warning: Font file {path} not found. Creating a dummy file. Text rendering might be affected.")
                with open(path, 'wb') as f_dummy: # create an empty file, Pillow might handle it or use default
                    f_dummy.write(b'') # Minimal content for a file
            except Exception as e_font:
                print(f"Could not create dummy font file {path}: {e_font}")


    # Your original main() function logic for generating initial samples can be called here if needed
    # For example, if you want to populate some images on startup:
    # print("Generating initial sample labels...")
    # couriers_to_generate = ["shopee", "lazada"]
    # for courier in couriers_to_generate:
    #    try:
    #        generate_shipping_label(courier)
    #    except Exception as e:
    #        print(f"Error generating initial {courier} label: {e}")
            
    app.run(debug=True) # Runs the Flask development server