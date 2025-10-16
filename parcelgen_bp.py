# parcelgen_bp.py

import os
import random
import datetime
import qrcode # Make sure this is installed: pip install qrcode
import barcode # Make sure this is installed: pip install python-barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont, ImageEnhance # Make sure Pillow is installed: pip install Pillow
import numpy as np # Make sure numpy is installed: pip install numpy
import string
import json
from faker import Faker # Make sure Faker is installed: pip install Faker

from flask import Blueprint, jsonify, send_from_directory, render_template, request, current_app

# --- Define the Blueprint ---
# The first argument is the Blueprint's name.
# The second argument (__name__) helps Flask locate the Blueprint's root path.
# template_folder: Specifies a subfolder within your main 'templates' folder for this blueprint's templates (optional but good practice)
# static_folder: Specifies a subfolder for this blueprint's static files (optional)
parcelgen_bp = Blueprint('parcelgen', __name__, template_folder='parcelgen_templates', static_folder='parcelgen_static')

# --- Configuration (Moved from parcelgen.py, adjusted for Blueprint context) ---
# Get the root path of the main application to correctly locate 'simulation' and 'fonts'
# We'll access the main app's config or define paths relative to the project root
# For simplicity, we'll assume these directories are at the project root or configured in the main app.

# INCOMING_IMAGES_DIR will be accessed via current_app.config later or defined directly
# FONT_DIR and FONT_PATH will also be handled similarly or defined directly

# --- Helper Functions (Copied from parcelgen.py) ---
# (Copy ALL your helper functions here: fake, PH_LOCATION_DATA, generate_address,
# generate_tracking_number, generate_order_id, generate_phone_number, generate_amount,
# generate_weight, generate_dates, generate_receipt_data, generate_barcode, generate_qr_code,
# load_fonts, generate_shopee_receipt, generate_lazada_receipt, generate_jnt_receipt,
# generate_ninjavan_receipt. Make sure they don't rely on a global 'app' instance
# directly, but use 'current_app' if needed for config values.)

# --- IMPORTANT: Adjust FONT_PATH and INCOMING_IMAGES_DIR ---
# These paths need to be correct relative to your main flask_server.py execution.
# It's best to configure these in your main app (flask_server.py) and access them via current_app.config.
# For now, let's define them here, assuming 'fonts' and 'simulation/incoming_images'
# are at the root of your project where flask_server.py is.

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '.')) # Assuming parcelgen_bp.py is in root

# --- CONFIGURATION FOR PARCELGEN BLUEPRINT ---
# Make sure these directories are created by your main flask_server.py startup
PARCELGEN_INCOMING_IMAGES_DIR = os.path.join(PROJECT_ROOT, 'simulation', 'incoming_images')
PARCELGEN_FONT_DIR = os.path.join(PROJECT_ROOT, 'fonts')

PARCELGEN_FONT_PATH = {
    'regular': os.path.join(PARCELGEN_FONT_DIR, 'Arial.ttf'),
    'bold': os.path.join(PARCELGEN_FONT_DIR, 'Arial_Bold.ttf')
}

# Initialize Faker (if not already done in a shared utility)
fake = Faker(['en_PH']) # Or your desired locale

# (Paste your PH_LOCATION_DATA here or import it)
PH_LOCATION_DATA = [
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

# --- EXAMPLE: Adjusting a helper function ---
def load_fonts():
    """Load fonts with fallbacks for better OCR readability"""
    try:
        # Use PARCELGEN_FONT_PATH defined within this blueprint's scope
        header_font = ImageFont.truetype(PARCELGEN_FONT_PATH['bold'], 48)
        title_font = ImageFont.truetype(PARCELGEN_FONT_PATH['bold'], 36)
        normal_font = ImageFont.truetype(PARCELGEN_FONT_PATH['regular'], 30)
        small_font = ImageFont.truetype(PARCELGEN_FONT_PATH['regular'], 24)
        return header_font, title_font, normal_font, small_font
    except IOError:
        # Access logger from current_app if you want to log this
        # current_app.logger.warning(f"Could not load custom fonts from {PARCELGEN_FONT_PATH}. Trying system fonts or default.")
        print(f"Warning: Could not load custom fonts from {PARCELGEN_FONT_PATH}. Trying system fonts or default.")
        # ... (rest of your fallback font logic, ensure it doesn't rely on global FONT_PATH from parcelgen.py) ...
        # For simplicity, if custom fonts fail, try to load default directly
        # Fallback font loading logic (same as your original, but ensure it's robust)
        system_font_paths = {
            'regular': ['Arial.ttf', 'DejaVuSans.ttf', 'LiberationSans-Regular.ttf'],
            'bold': ['Arialbd.ttf', 'arialbd.ttf', 'DejaVuSans-Bold.ttf', 'LiberationSans-Bold.ttf']
        }

        found_regular = None
        found_bold = None

        font_dirs = []
        if os.name == 'nt': # Windows
            font_dirs.append(os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'))
        elif os.name == 'posix': # Linux, macOS
            font_dirs.extend(['/usr/share/fonts/truetype/', '/usr/local/share/fonts/', os.path.expanduser('~/Library/Fonts/'), '/Library/Fonts/'])

        for style, names in system_font_paths.items():
            for name in names:
                for dir_path in font_dirs:
                    font_file = os.path.join(dir_path, name)
                    if os.path.exists(font_file):
                        if style == 'regular' and not found_regular:
                            found_regular = font_file
                        elif style == 'bold' and not found_bold:
                            found_bold = font_file
                if found_regular and found_bold: # Check if both found after iterating names for a style
                    break
            if found_regular and found_bold: # Check if both found after iterating styles
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
            default_font = ImageFont.load_default() # Load default PIL font
            return default_font, default_font, default_font, default_font

# --- (Paste ALL your other helper functions from parcelgen.py here) ---
# generate_address, generate_tracking_number, etc.
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
# Make sure any file paths (like for barcode saving) are handled correctly.
# The generate_barcode function saves a temporary file. Ensure the temp directory
# it uses ('temp_barcodes') is either created or uses a robust temp file mechanism.

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
    
    

# --- Main Label Generation Function (from parcelgen.py) ---
def generate_shipping_label_bp(courier): # Renamed slightly to avoid potential name clashes if imported elsewhere
    """Generate shipping label based on courier type"""
    # Ensure PARCELGEN_INCOMING_IMAGES_DIR and PARCELGEN_FONT_PATH are accessible
    # and correctly defined for the blueprint's context.
    # Also ensure the directories exist.
    # This should ideally be handled at app startup.
    os.makedirs(PARCELGEN_INCOMING_IMAGES_DIR, exist_ok=True)
    os.makedirs(PARCELGEN_FONT_DIR, exist_ok=True)
    # (Add font file check here if desired, similar to parcelgen.py's main block)

    data = generate_receipt_data(courier) # Assumes this function is copied above

    # Select appropriate receipt generation function
    if courier.lower() == "shopee": image = generate_shopee_receipt(data) # Assumes this is copied
    elif courier.lower() == "lazada": image = generate_lazada_receipt(data) # Assumes this is copied
    elif courier.lower() == "jnt": image = generate_jnt_receipt(data) # Assumes this is copied
    elif courier.lower() == "ninjavan": image = generate_ninjavan_receipt(data) # Assumes this is copied
    else: image = generate_jnt_receipt(data) # Default

    enhancer = ImageEnhance.Contrast(image); image = enhancer.enhance(1.2)
    enhancer = ImageEnhance.Sharpness(image); image = enhancer.enhance(1.5)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f")
    filename = f"{courier.lower()}_{timestamp}.png"
    filepath = os.path.join(PARCELGEN_INCOMING_IMAGES_DIR, filename)
    image.save(filepath)
    # current_app.logger.info(f"Generated receipt: {filepath}") # If using app logger

    json_filename = f"{courier.lower()}_{timestamp}.json"
    json_filepath = os.path.join(PARCELGEN_INCOMING_IMAGES_DIR, json_filename)
    with open(json_filepath, 'w') as f:
        json.dump(data, f, indent=4)

    return filename # Return only filename for web path


# --- Blueprint Routes (Adapted from parcelgen.py) ---
# Note: We use '@parcelgen_bp.route' instead of '@app.route'

@parcelgen_bp.route('/') # This will be the root of the blueprint, e.g., /parcelgen/
def index():
    """Serves the main HTML page for parcel generation."""
    # This will look for 'parcelgen.html' inside 'your_project_root/templates/'
    # because we didn't specify a template_folder for the blueprint earlier,
    # or if we did ('parcelgen_templates'), it would look in 'templates/parcelgen_templates/'.
    # For simplicity, let's assume parcelgen.html is in the main 'templates' folder.
    return render_template('parcelgen.html')

@parcelgen_bp.route('/images/<path:filename>')
def serve_image(filename):
    """Serves images from the PARCELGEN_INCOMING_IMAGES_DIR."""
    # Ensure PARCELGEN_INCOMING_IMAGES_DIR is correctly defined and accessible
    return send_from_directory(PARCELGEN_INCOMING_IMAGES_DIR, filename)

@parcelgen_bp.route('/simulate-scan', methods=['POST'])
def simulate_scan_route():
    # current_app.logger.info("Simulating scan...") # Example of using app logger
    generated_files = []
    couriers = ["shopee", "lazada"]
    for courier in couriers:
        try:
            filename = generate_shipping_label_bp(courier)
            generated_files.append(filename)
        except Exception as e:
            # current_app.logger.error(f"Error in simulate_scan_route: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    return jsonify({'status': 'success', 'message': 'Scan initiated, images generated.', 'files': generated_files})

@parcelgen_bp.route('/process-parcel', methods=['POST'])
def process_parcel_route():
    # current_app.logger.info("Processing parcel...")
    try:
        filename = generate_shipping_label_bp("jnt")
        return jsonify({'status': 'success', 'message': 'Parcel processing simulated.', 'file': filename})
    except Exception as e:
        # current_app.logger.error(f"Error in process_parcel_route: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@parcelgen_bp.route('/generate-label', methods=['POST'])
def generate_label_route():
    # current_app.logger.info("Generating label...")
    try:
        random_courier = random.choice(["shopee", "lazada", "jnt", "ninjavan"])
        filename = generate_shipping_label_bp(random_courier)
        return jsonify({'status': 'success', 'message': f'{random_courier.upper()} label generated.', 'file': filename})
    except Exception as e:
        # current_app.logger.error(f"Error in generate_label_route: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@parcelgen_bp.route('/get-images', methods=['GET'])
def get_images_route():
    try:
        images = [f for f in os.listdir(PARCELGEN_INCOMING_IMAGES_DIR)
                  if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        # IMPORTANT: Adjust the image URLs based on how the blueprint is registered
        # If registered with url_prefix='/parcelgen', then URLs should be '/parcelgen/images/...'
        # The 'serve_image' route in this blueprint is at '/images/<filename>' *relative to the blueprint's prefix*.
        image_urls = [f'{parcelgen_bp.url_prefix}/images/{image_name}' for image_name in images]
        return jsonify(image_urls)
    except Exception as e:
        # current_app.logger.error(f"Error in get_images_route: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@parcelgen_bp.route('/clear-all-images', methods=['POST'])
def clear_all_images_route():
    # current_app.logger.info("Clearing all images from backend...")
    cleared_count = 0
    errors = []
    try:
        for filename in os.listdir(PARCELGEN_INCOMING_IMAGES_DIR):
            file_path = os.path.join(PARCELGEN_INCOMING_IMAGES_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    cleared_count += 1
            except Exception as e_file:
                errors.append(f"Could not delete {filename}: {e_file}")
        if errors:
            return jsonify({'status': 'partial_success', 'message': f'Cleared {cleared_count} images. Some errors occurred.', 'errors': errors}), 207
        return jsonify({'status': 'success', 'message': f'All {cleared_count} images cleared from backend.'})
    except Exception as e:
        # current_app.logger.error(f"Error in clear_all_images_route: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- (Ensure all helper functions from parcelgen.py are copied above this line) ---
# For example: fake, PH_LOCATION_DATA, generate_address, generate_tracking_number,
# generate_order_id, generate_phone_number, generate_amount, generate_weight, generate_dates,
# generate_receipt_data, generate_shopee_receipt, generate_lazada_receipt,
# generate_jnt_receipt, generate_ninjavan_receipt.