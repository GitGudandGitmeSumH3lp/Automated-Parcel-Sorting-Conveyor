from flask import Flask, request, redirect, url_for, render_template, session, flash, jsonify, abort
import os
import psycopg2
import logging
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask import send_from_directory
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import pytesseract
from datetime import datetime,  timedelta
import cv2
from flask import Response, render_template_string
import sys
import time
import random
import qrcode
import barcode
from barcode.writer import ImageWriter
import numpy as np
import string
import json
from faker import Faker




# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('flask_ocr_server')

# Create necessary directories
os.makedirs('templates', exist_ok=True)
os.makedirs('logs', exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', '_,*H]wS;_ue|1SqXF~0B9~>HRYlDkr')

# Directory configuration - consolidate to avoid confusion
PROCESSED_IMAGE_FOLDER = 'simulation/processed_images'
UPLOAD_FOLDER = 'static/uploads'  # For serving uploaded images
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_IMAGE_FOLDER'] = PROCESSED_IMAGE_FOLDER

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
# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_IMAGE_FOLDER'], exist_ok=True)

# Other configuration
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://carlo:pogi@localhost/ocr_data'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database configuration
DB_CONFIG = {
    'dbname': 'ocr_data',
    'user': 'carlo',
    'password': 'pogi',
    'host': 'localhost',
    'port': 5432
}


# Initialize Faker with Philippines locale
fake = Faker(['en_PH'])

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



# --- Conditional Import of Servo Module ---
if sys.platform.startswith('linux'):
    # Assume 'linux' means Raspberry Pi OS or similar Linux where hardware is available
    try:
        import testservo as servo_module # Import the real module
        logger.info("Running on Linux, attempting to import real testservo module.")
        # servo_module_loaded = True # This will be determined below
    except ImportError as e:
        logger.error(f"Failed to import real testservo module on Linux: {e}")
        servo_module = None
        # servo_module_loaded = False # This will be determined below
    except Exception as e:
        # Catch potential errors during hardware initialization within testservo.py
        logger.error(f"Error initializing real testservo module on Linux: {e}")
        servo_module = None
        # servo_module_loaded = False # This will be determined below
else:
    # Assume other platforms (like Windows) are for simulation
    try:
        import mock_testservo as servo_module # Import the mock module
        logger.info("Running on non-Linux platform, importing mock_testservo module for simulation.")
        # servo_module_loaded = True # This will be determined below
    except ImportError as e:
        logger.error(f"Failed to import mock_testservo module: {e}")
        servo_module = None
        # servo_module_loaded = False # This will be determined below
    except Exception as e:
        # Catch potential errors during mock initialization (shouldn't happen often)
        logger.error(f"Error initializing mock_testservo module: {e}")
        servo_module = None
        # servo_module_loaded = False # This will be determined below

# Determine servo_module_loaded status AFTER the conditional import
servo_module_loaded = servo_module is not None
# Initialize SQLAlchemy
db = SQLAlchemy(app)

# --- Flexible Camera Setup ---
# Attempt to initialize the real camera on ANY platform.
# Fallback to mock camera only if real camera initialization fails.
ENABLE_BACKEND_CAMERA = False  # set to True only if using /video_feed
camera = None
logger.info(f"Attempting to initialize real camera on {sys.platform}...")
camera_indices_to_try = [0, 1, 2] # Or make this configurable

for index in camera_indices_to_try:
    try:
        temp_camera = cv2.VideoCapture(index, cv2.CAP_DSHOW) # Add API preference if needed, e.g., cv2.CAP_V4L2 for Linux
        if temp_camera.isOpened():
            camera = temp_camera
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            # Optional: Check if set worked
            actual_width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
            logger.info(f"Real camera initialized successfully on index {index} with resolution {actual_width}x{actual_height}.")
            break # Found a working camera
        else:
            logger.warning(f"cv2.VideoCapture({index}) failed to open.")
            temp_camera.release() # Release it if opened but not usable for some reason or to be safe
    except Exception as e:
        logger.error(f"Error during real camera initialization on index {index}: {e}")
        if temp_camera and temp_camera.isOpened(): # Ensure release if opened before error
            temp_camera.release()

if camera is None:
    logger.info("Real camera not available after trying specified indices. Will use mock camera for simulation.")
    

# --- Import the ocrv module ---
try:
    import ocrv_logic as ocr_module
    logger.info("ocrv module imported successfully.")
    ocr_module_loaded = True

except ImportError as e:
    # Catch ImportError specifically. Check if it's related to adafruit-blinka or board.
    # This is a common indicator of a hardware dependency issue on the wrong platform.
    if "adafruit_blinka" in str(e).lower() or "board" in str(e).lower() or "notimplementederror" in str(e).lower():
         logger.warning(f"OCR module import failed due to hardware dependency on non-Linux platform: {e}")
         logger.warning("Running in OCR simulation mode (module not fully loaded).")
         ocr_module = None
         ocr_module_loaded = False
    else:
        # If it's a different ImportError, log it as a critical error
        logger.critical(f"Failed to import OCR module (ocrv1.3 or ocrv4) due to unexpected ImportError: {e}", exc_info=True)
        ocr_module = None
        ocr_module_loaded = False

except Exception as e:
     # Catch any other exceptions during the import process
     logger.critical(f"Error during OCR module import or initialization: {e}", exc_info=True)
     ocr_module = None
     ocr_module_loaded = False

# --- CONFIGURATION (from ocrv1.3, needed for Flask side logic) ---
IMAGE_DIRECTORY = 'simulation/incoming_images' # Directory monitored by ocrv1.3
PROCESSED_IMAGE_FOLDER = 'simulation/processed_images' # Directory for processed images (if used by Flask)
UPLOAD_FOLDER = 'static/uploads' # For serving uploaded images
SNAPSHOT_DIR = IMAGE_DIRECTORY

#----PARCEL GENERATOR


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
    today = datetime.now()
    
    # Shipping date (today or within last 3 days)
    ship_date = today - timedelta(days=random.randint(0, 3)) 
    
    # Expected delivery (2-7 days after shipping)
    delivery_date = ship_date + timedelta(days=random.randint(2, 7))
    
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
    unique_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
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
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f") # Added microseconds for more uniqueness
    filename = f"{courier.lower()}_{timestamp}.png"
    filepath = os.path.join(INCOMING_IMAGES_DIR, filename)
    image.save(filepath)
    print(f"Generated receipt: {filepath}")
    
    json_filename = f"{courier.lower()}_{timestamp}.json"
    json_filepath = os.path.join(INCOMING_IMAGES_DIR, json_filename)
    with open(json_filepath, 'w') as f:
        json.dump(data, f, indent=4)
    
    return filename # Return only filename for web path

# --- Route to serve the OCR Control Page ---
@app.route('/ocr_control')
def OCR():
    import sys
    # --- Add Authentication Check ---
    if 'user_id' not in session:
        flash('Please log in to access the OCR control page.', 'info')
        return redirect(url_for('index'))

    # Determine the platform (PC vs Pi)
    is_linux = sys.platform.startswith('linux')
    # Determine if camera is available (already done globally)
    camera_available = camera is not None
    # Determine if the ocr_module loaded
    ocr_module_available = ocr_module_loaded

    return render_template(
        'ocr_control.html',
        is_linux=is_linux,
        python_version=sys.version,
        camera_available=camera_available,
        ocr_module_available=ocr_module_available
        
    )
# --- API Route to Trigger OCR Scan of All Images ---
# This route is called by the JavaScript on ocr_control.html
@app.route('/api/trigger_ocr', methods=['POST'])
def api_trigger_ocr():
    # --- Add Authentication Check ---
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401

    # Check if the ocr_module was successfully loaded on server startup
    # Use the global ocr_module_loaded flag
    if not ocr_module_loaded:
         logger.error("API: OCR module not available. Request received but cannot process.")
         return jsonify({"success": False, "error": "OCR module not available on the server. Check server logs for import errors."}), 500

    scan_results = []
    supported_extensions = ('.png', '.jpg', '.jpeg')

    # Ensure the image directory exists
    if not os.path.exists(IMAGE_DIRECTORY):
        logger.warning(f"API: Image directory not found: {IMAGE_DIRECTORY}")
        # Return 404 Not Found if the directory doesn't exist
        return jsonify({"success": False, "error": f"Image directory not found at {IMAGE_DIRECTORY}."}), 404

    try:
        # Get list of supported image files in the directory
        files_to_process = [
            f for f in os.listdir(IMAGE_DIRECTORY)
            if f.lower().endswith(supported_extensions) and
            os.path.isfile(os.path.join(IMAGE_DIRECTORY, f))
        ]

        if not files_to_process:
            logger.info(f"API: No supported image files found in {IMAGE_DIRECTORY} to scan.")
            # Return success with an empty results list if no files
            return jsonify({"success": True, "message": "No image files found to scan.", "results": []}), 200

        logger.info(f"API: Found {len(files_to_process)} image(s) to scan in {IMAGE_DIRECTORY}.")

        # Process each file
        for filename in files_to_process:
            image_path = os.path.join(IMAGE_DIRECTORY, filename)
            logger.info(f"API: Attempting to scan file: {filename}")

            # Call the extraction function from the imported ocr_module
            # This function handles preprocessing and OCR
            try:
                # Call the main extraction function from your ocr_module
                # Assuming ocr_module.scannedParcelData  exists and works as expected
                extracted_data = ocr_module.extract_data_from_image(image_path)

                # Append the result for this file
                scan_results.append({
                    "filename": filename,
                    "extracted_data": extracted_data # This should be the dict from extract_data_from_image
                })
                logger.info(f"API: Scan successful for {filename}.")

            except FileNotFoundError:
                 logger.error(f"API: File not found during processing: {image_path}")
                 scan_results.append({
                    "filename": filename,
                    "error": "File not found during processing."
                 })
            except PermissionError:
                 logger.error(f"API: Permission denied for file: {image_path}")
                 scan_results.append({
                    "filename": filename,
                    "error": "Permission denied to access file."
                 })
            except Exception as e:
                # Catch any other exceptions during the processing of this specific file
                logger.error(f"API: Error processing file {filename}: {e}", exc_info=True)
                scan_results.append({
                    "filename": filename,
                    "error": f"Processing failed: {e}" # Include the specific error message
                })
                # Continue to the next file even if one fails

        # After processing all files in the loop
        message = f"Scan completed. Processed {len(files_to_process)} image(s)."
        logger.info(f"API: Scan of all images loop finished. {message}")

        # Return the list of results as JSON
        # If the loop completed, even with individual file errors, the overall request is successful
        return jsonify({"success": True, "message": message, "results": scan_results}), 200

    except Exception as e:
        # This catches errors outside the file processing loop (e.g., listing directory)
        logger.critical(f"API: A critical error occurred during the scan process: {e}", exc_info=True)
        # Return a 500 error for critical, unhandled exceptions
        return jsonify({"success": False, "error": f"A critical server error occurred during scan: {e}"}), 500

# --- Mock Frame Generation Function ---
def generate_mock_frame():
    """Generates a simple mock image frame with text overlay."""
    width, height = 640, 480
    # Create a blank white image
    img = Image.new('RGB', (width, height), color = (70, 80, 90)) # Dark background

    d = ImageDraw.Draw(img)
    try:
        # Try to use a common font
        font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        # Fallback font if arial.ttf is not found
        font = ImageFont.load_default()
        logger.warning("Arial font not found, using default PIL font for mock stream.")

    text = f"SIMULATION FEED\n{time.strftime('%Y-%m-%d %H:%M:%S')}\n(No Camera Detected)"
    text_color = (150, 160, 170) # Light gray text
    # Calculate text size and position
    text_bbox = d.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2

    d.text((text_x, text_y), text, fill=text_color, font=font, align="center")

    # Convert PIL image to OpenCV format (NumPy array)
    # This is needed because cv2.imencode expects a NumPy array
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    return frame

# Using psycopg2 directly
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None
    
# User model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = generate_password_hash(password)

def connect_to_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

# Receipts model
class Receipt(db.Model):
    # __tablename__ = 'receipts' # Optional: specify table name if it's different from class name (lowercase)

    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String) # Original filename
    raw_text = db.Column(db.Text)         # Raw extracted text
    # Fields extracted by ocrv_logic.py and sent in the payload:
    extracted_province = db.Column(db.String)
    extracted_courier = db.Column(db.String)
    sorting_mode_used = db.Column(db.String)
    sorted_category = db.Column(db.String) # Final category used for sorting (e.g., 'SHOPEE', 'LUZON', 'UNKNOWN')
    sorting_box_number = db.Column(db.Integer)
    # Timestamp (you were sending time.time() in ocrv_logic, consider saving as DateTime)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    original_image = db.Column(db.LargeBinary) # Binary data for the image

    # Optional: Add a __repr__ method for easier debugging
    def __repr__(self):
        return f"<Receipt {self.id}: {self.image_filename} ({self.extracted_courier})>"

# --- Database Data Fetching Functions ---
# Ensure 'parcels' table exists with appropriate columns (status, timestamp, zip_code, courier)
def get_total_processed_count():
    conn = get_db_connection()
    if conn is None:
        return 0
    cur = None
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM receipts;") # Assuming table is named 'receipts' as in previous steps
        count = cur.fetchone()[0]
        return count
    except Exception as e:
        print(f"Error fetching total processed count: {e}")
        return 0
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# --- Frame Generation Function (Uses real or mock camera) ---
def generate_frames():
    """Generates video frames from the camera (real or mock)."""
    if camera is None:
        # Use mock frames if real camera is not available
        while True:
            frame = generate_mock_frame()
            # Encode the frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

       
            # Stream frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.1) # Simulate frame rate
            
            

    else:
        # Use real camera frames
        while True:
            success, frame = camera.read()
            if not success:
                logger.warning("Failed to read frame from real camera.")
                # Optionally yield a static error image here before breaking
                break
            else:
                
                frame = cv2.flip(frame, 1)
                # Encode the frame to JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()

    

                # Stream frame in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


#OCR COUNT
def get_successful_ocr_count():
    conn = get_db_connection()
    if conn is None:
        return 0
    cur = None
    try:
        cur = conn.cursor()
        # Assuming 'status' column exists and 'successful' is a possible value
        # You might need to adjust the WHERE clause based on how you store success/failure
        cur.execute("SELECT COUNT(*) FROM receipts WHERE raw_text IS NOT NULL AND raw_text != '';") # Example: count if raw_text was extracted
        count = cur.fetchone()[0]
        return count
    except Exception as e:
        print(f"Error fetching successful OCR count: {e}")
        return 0
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_failed_ocr_count():
    conn = get_db_connection()
    if conn is None:
        return 0
    cur = None
    try:
        cur = conn.cursor()
        # Example: count if raw_text is NULL or empty, indicating potential failure
        cur.execute("SELECT COUNT(*) FROM receipts WHERE raw_text IS NULL OR raw_text = '';")
        count = cur.fetchone()[0]
        return count
    except Exception as e:
        print(f"Error fetching failed OCR count: {e}")
        return 0
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_latest_parcel_info():
    conn = get_db_connection()
    if conn is None:
        return {}
    cur = None
    try:
        # Use RealDictCursor to fetch results as dictionaries (easier to access columns by name)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Ensure these column names (zip_codes, courier_service, timestamp) match your table
        cur.execute("SELECT zip_codes, courier_service, timestamp FROM receipts ORDER BY timestamp DESC LIMIT 1;")
        result = cur.fetchone()
        # zip_codes is stored as JSONB, fetchone() will return it as a Python dict/list
        # courier_service is VARCHAR
        return result if result else {}
    except Exception as e:
        print(f"Error fetching latest parcel info: {e}")
        return {}
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


 #SAVE RECEIPT DATA
def save_receipt_data(raw_text, zip_codes, courier_service, image_bytes):
    conn = get_db_connection()
    if conn is None:
        return False # Cannot save if no DB connection

    cur = None
    try:
        cur = conn.cursor()

        # Convert Python list of zip codes to a format suitable for PostgreSQL (JSONB)
        zip_codes_json = json.dumps(zip_codes)

        cur.execute(
            """INSERT INTO receipts (raw_text, zip_codes, courier_service, original_image, timestamp)
               VALUES (%s, %s, %s, %s, %s)""",
            (raw_text, zip_codes_json, courier_service, image_bytes, datetime.now())
        )

        conn.commit()
        return True
    except Exception as e:
        print("Database error during save:", e)
        if conn:
            conn.rollback() # Roll back in case of error
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()            

#INITIALIZE OCR_RESULTS TABLE
def ensure_ocr_table():
    conn = connect_to_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ocr_results (
                    id SERIAL PRIMARY KEY,
                    text_content TEXT,
                    image_path TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    predicted_destination TEXT,
                    match_score FLOAT
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            logger.info("ocr_results table ensured.")
        except Exception as e:
            logger.error(f"Error creating ocr_results table: {e}")




@app.route('/', methods=['GET','POST'])
def index():
    """Renders the terminal login page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')  # Serve the HTML file


    
#LOGIN
@app.route('/login', methods=['POST'])
def login():
    """Handles user login."""

    username = request.form.get('username')
    password = request.form.get('password')
    from_terminal = request.form.get('from_terminal')  # Check if login is from terminal

    try:
        user = User.query.filter_by(username=username).one()
        if check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username

            if from_terminal == 'true':
                return redirect(url_for('dashboard'))  # Redirect to dashboard
            else:
                return jsonify({'success': True, 'username': user.username, 'name': user.username})

        else:
            if from_terminal == 'true':
                flash('Invalid username or password', 'danger')  # Use 'danger' for error styling
                return redirect(url_for('index'))
            else:
                return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except NoResultFound:
        if from_terminal == 'true':
            flash('Invalid username or password', 'danger')
            return redirect(url_for('index'))
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        if from_terminal == 'true':
            flash(f'An error occurred during login: {e}', 'danger')
            return redirect(url_for('index'))
        else:
            return jsonify({'success': False, 'message': f'Login error: {e}'}), 500
        
 

# --- Completed Route for Dashboard ---
@app.route('/dashboard')
def dashboard():
    # --- Add Authentication Check ---
    # Check if 'user_id' is in the session
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'info')
        return redirect(url_for('index'))

    # --- Fetch Data for Dashboard ---
    total_processed = get_total_processed_count()
    successful_ocr = get_successful_ocr_count()
    failed_ocr = get_failed_ocr_count()
    latest_parcel = get_latest_parcel_info() # This returns a dictionary or {}

    # Extract latest parcel info, handling cases where no parcels exist
    latest_zip = latest_parcel.get('zip_codes', 'N/A') # Use .get() with a default value
    # zip_codes is JSONB, might be a list. Display it appropriately.
    if isinstance(latest_zip, list):
        latest_zip_display = ', '.join(map(str, latest_zip)) if latest_zip else 'N/A'
    else:
         latest_zip_display = latest_zip if latest_zip else 'N/A'


    latest_courier = latest_parcel.get('courier_service', 'N/A')
    # You might not have a 'status' column in 'receipts',
    # or you might derive status from raw_text presence.
    # Adjust this based on your table schema.
    # For now, let's just indicate if latest_parcel info was found.
    latest_status_display = "Info Available" if latest_parcel else "No Recent Data"


    # Pass data to the template
    return render_template('dashboard.html',
        total_processed=total_processed,
        successful_ocr=successful_ocr,
        failed_ocr=failed_ocr,
        current_status=latest_status_display, # Pass the derived status
        last_zip=latest_zip_display, # Pass the formatted zip code(s)
        last_courier=latest_courier
    )


#RECEIPTS PAGE
@app.route('/receipts', methods=['POST','GET'])
def receipts():
    # --- Optional: Add Authentication Check if upload requires login ---
    # if 'user_id' not in session:
    #     return jsonify({"error": "Authentication required"}), 401
    # ---------------------------------------------------------------

    if request.method == 'POST':
        # --- Handle Incoming Data (POST Request) ---
        # This is the logic from your original code snippet
        if 'data' not in request.form or 'image' not in request.files:
            return jsonify({"error": "Missing required form data ('data' or 'image')"}), 400

        try:
            data = json.loads(request.form['data'])
            raw_text = data.get('raw_text')
            # Assuming zip_codes and courier_service are also in the 'data' JSON
            zip_codes = data.get('zip_codes', []) # Assuming zip_codes is a list
            courier_service = data.get('courier_service')
            extracted_province = data.get('extracted_province') # Include extracted fields
            extracted_courier = data.get('extracted_courier')
            sorting_mode_used = data.get('sorting_mode_used')
            sorted_category = data.get('sorted_category')
            sorting_box_number = data.get('sorting_box_number')
            # Timestamp is generated by the database or can be sent in data

            image_file = request.files['image']
            image_bytes = image_file.read()
            image_filename = secure_filename(image_file.filename) # Get and secure filename

            # Call your save_receipt_data function
            # Make sure save_receipt_data in your backend accepts these arguments
            # Based on your previous code, save_receipt_data expects raw_text, zip_codes, courier_service, image_bytes.
            # You might need to update save_receipt_data to accept/store the new extracted fields like province, sorting details.
            db_save_success = save_receipt_data(
                image_filename=image_filename, # Pass filename
                raw_text=raw_text,
                zip_codes=zip_codes, # Assuming zip_codes is passed and saved
                courier_service=courier_service, # Assuming this is the original courier input, maybe also store extracted_courier
                extracted_province=extracted_province, # Pass new extracted fields
                extracted_courier=extracted_courier,
                sorting_mode_used=sorting_mode_used,
                sorted_category=sorted_category,
                sorting_box_number=sorting_box_number,
                image_bytes=image_bytes
            )


            if db_save_success:
                 logger.info(f"Data and image saved for {image_filename}.")
                 return jsonify({"success": True, "message": "Data and image received and processed"}), 200
            else:
                 logger.error(f"Failed to save data and image for {image_filename} to database.")
                 return jsonify({"success": False, "error": "Failed to save to database"}), 500

        except json.JSONDecodeError:
            logger.error("Invalid JSON data in 'data' field during POST to /receipts.")
            return jsonify({"success": False, "error": "Invalid JSON data in 'data' field"}), 400
        except Exception as e:
            logger.error(f"Server error during POST to /receipts: {e}", exc_info=True)
            return jsonify({"success": False, "error": str(e)}), 500

    elif request.method == 'GET':
        # --- Handle Displaying Page (GET Request) ---
        # This will render the HTML template for the receipts page
        # Your HTML file should be in the 'templates' folder
        return render_template('receipts.html')



# --- New API Endpoint for Searching Receipts ---
@app.route('/api/search_receipts', methods=['GET'])
def api_search_receipts():
    # --- Add Authentication Check ---
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401

    query = request.args.get('query', '').strip()
    logger.info(f"API: Received search query for receipts: '{query}'")

    try:
        # Base query: Fetch all receipts
        receipts_query = Receipt.query

        # Apply search filter if a query is provided
        if query:
            # This performs a case-insensitive search across raw_text, courier, and province
            # You might need to adjust the fields based on your Receipt model
            search_filter = or_(
                Receipt.raw_text.ilike(f'%{query}%'),
                Receipt.extracted_courier.ilike(f'%{query}%'), # Search in the extracted courier field
                Receipt.extracted_province.ilike(f'%{query}%') # Search in the extracted province field
                # Add other searchable fields like zip_codes if you have them structured
                # Example for zip_codes if they are stored as a comma-separated string:
                # Receipt.zip_codes.ilike(f'%{query}%')
            )
            receipts_query = receipts_query.filter(search_filter)

        # Order by timestamp, newest first
        receipts_query = receipts_query.order_by(Receipt.timestamp.desc())

        # Execute the query
        receipts = receipts_query.all()

        # Prepare data for JSON response
        receipts_list = []
        for receipt in receipts:
            # Convert image bytes to base64 string for embedding in HTML
            image_base64 = None
            if receipt.original_image:
                try:
                    # If stored as LargeBinary/bytes, encode directly
                    image_base64 = base64.b64encode(receipt.original_image).decode('utf-8')
                    # If image is stored differently (e.g., path), you'd load and encode it here
                except Exception as e:
                    logger.error(f"Error encoding image for receipt {receipt.id}: {e}")
                    image_base64 = None # Ensure it's None if encoding fails

            receipts_list.append({
                'id': receipt.id,
                'image_filename': receipt.image_filename,
                'raw_text': receipt.raw_text,
                'extracted_province': receipt.extracted_province, # Include extracted fields
                'extracted_courier': receipt.extracted_courier,
                'sorting_mode_used': receipt.sorting_mode_used,
                'sorted_category': receipt.sorted_category,
                'sorting_box_number': receipt.sorting_box_number,
                'timestamp': receipt.timestamp.isoformat(), # Send timestamp in ISO format
                'original_image': image_base64 # Base64 encoded image data
                # Add other fields you want to display
            })

        logger.info(f"API: Found {len(receipts_list)} receipts matching the query.")
        return jsonify(receipts_list), 200

    except Exception as e:
        logger.error(f"API: An error occurred during receipt search: {e}", exc_info=True)
        return jsonify({"error": "Server error fetching receipts."}), 500


# Upload OCR result
@app.route('/upload_ocr_result', methods=['POST'])
def upload_ocr_result():
    if 'image' not in request.files:
        return "No image part", 400

    image = request.files['image']
    image_name = request.form.get('image_name')
    text_content = request.form.get('text')

    # Save OCR result to database
    conn = connect_to_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO ocr_results (text_content, image_path, timestamp, predicted_destination, match_score)
                VALUES (%s, %s, NOW(), %s, %s)
            """, (text_content, image_name, 'Unknown', 0))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving OCR result: {e}")
            return "Database error", 500

    return "Success", 200

# OCR Images page
@app.route('/ocr-images', methods=['GET'])
def ocr_images():
    # Get OCR results
    results = get_ocr_results()
    
    # Return JSON if requested via AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(results)
    
    # Otherwise render the template with results
    return render_template('ocr_images.html', results=results)

# Process new uploaded image
@app.route('/process_image', methods=['POST'])
def process_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['PROCESSED_IMAGE_FOLDER'], filename)
        file.save(filepath)
        
        # Call your image_watcher.py or its function
        try:
            result = subprocess.run(['python', 'image_watcher.py', filepath], 
                                   capture_output=True, text=True)
            
            # For image_watcher.py, you'll need to make sure it accepts a file path parameter
            # and performs OCR on that specific file rather than watching a directory
            
            # You could also directly call OCR here if preferred:
            text = pytesseract.image_to_string(Image.open(filepath))
            
            # Save OCR result to database
            conn = connect_to_db()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO ocr_results (text_content, image_path, timestamp, predicted_destination, match_score)
                        VALUES (%s, %s, NOW(), %s, %s)
                    """, (text, filename, 'Unknown', 0))
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception as e:
                    logger.error(f"Error saving OCR result: {e}")
            
            return jsonify({
                'success': True, 
                'filename': filename,
                'text': text
            }), 200
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return jsonify({'error': 'Processing failed'}), 500
    
    return jsonify({'error': 'Invalid request'}), 400

# Get OCR results
def get_ocr_results():
    results = []
    folder = app.config['PROCESSED_IMAGE_FOLDER']
    
    # Get files from the processed images folder
    for fname in os.listdir(folder):
        if fname.lower().endswith(('.jpg', '.png', '.jpeg')):
            full_path = os.path.join(folder, fname)
            
            # Try to get text from database first
            conn = connect_to_db()
            text = None
            
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT text_content FROM ocr_results WHERE image_path = %s", (fname,))
                    result = cur.fetchone()
                    if result:
                        text = result[0]
                    cur.close()
                    conn.close()
                except Exception as e:
                    logger.error(f"Database error: {e}")
            
            # If not found in database, do OCR
            if not text:
                try:
                    text = pytesseract.image_to_string(Image.open(full_path))
                except Exception as e:
                    logger.error(f"OCR error for {fname}: {e}")
                    text = "Error processing image"
            
            results.append({'filename': fname, 'text': text})
    
    return results

# Logout
@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('user_id', None)  # Remove user ID from session
    session.pop('username', None)
    return redirect('/')  # Redirect to the login page
  
#CAMERA
@app.route('/snapshot')
def snapshot():
    # Create snapshot directory if it doesn't exist
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    
    success, frame = camera.read()
    if not success:
        return jsonify({"error": "Failed to capture image"}), 500

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"snapshot_{timestamp}.jpg"
    filepath = os.path.join(SNAPSHOT_DIR, filename)
    cv2.imwrite(filepath, frame)
    
    # Return the relative path that will work in your browser
    return jsonify({"image": f"/simulation/incoming_images/{filename}"})

@app.route('/livestream')
def livestream_page(): 
    # --- Add Authentication Check ---
    if 'user_id' not in session:
        flash('Please log in to access the livestream.', 'info')
        return redirect(url_for('index'))

    return render_template('stream.html')

@app.route('/video_feed')
def video_feed():
    # --- Add Authentication Check ---
    # You might want to protect the raw video feed as well
    if 'user_id' not in session:
         # Return a simple error response instead of the feed
         return Response("Authentication required", status=401)

    # Check if camera is available before starting the response
    if camera is None:
        # Return a static image or error message if camera not available
         return Response("Camera not available", status=503) # Service Unavailable

    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/simulation/incoming_images/<path:filename>')
def serve_snapshot_images(filename):
    try:
        return send_from_directory(SNAPSHOT_DIR, filename)
    except FileNotFoundError:
        abort(404)

#SERVO CONTROLS

@app.route('/api/servo/status', methods=['GET'])
def api_servo_status():
    """Returns the status of the servo module."""
    loaded, error_response = check_servo_module()
    if not loaded:
        return jsonify(error_response), 503 # Service Unavailable
    return jsonify({"status": "success", "message": "Servo module loaded and PCA9685 initialized.", "servo_kit_available": True})


@app.route('/api/servo/activate', methods=['POST'])
def api_activate_servo():
    data = request.get_json()
    servo_id = data.get('channel') # 'channel' is used in the JS for servo ID

    if servo_id is None:
        return jsonify({"status": "error", "message": "Servo ID (channel) not provided."}), 400

    # --- Interaction with your servo controller ---
    success, message = servo_controller.activate(servo_id)
    # ---

    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"status": "error", "message": message}), 500
    
 
@app.route('/api/servo/calibrate', methods=['POST'])
def api_calibrate_servo():
    data = request.get_json()
    servo_id = data.get('channel')

    if servo_id is None:
        return jsonify({"status": "error", "message": "Servo ID (channel) not provided."}), 400

    # --- Interaction with your servo controller ---
    # Calibration logic can be complex and specific to your hardware.
    # This might involve moving to limit switches, sensor feedback, etc.
    success, message = servo_controller.calibrate(servo_id)
    # ---

    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"status": "error", "message": message}), 500
    
@app.route('/api/servo/reset', methods=['POST'])
def api_reset_servo():
    """Resets a servo to its home position (90 degrees)."""
    loaded, error_response = check_servo_module()
    if not loaded:
        return jsonify(error_response), 503

    data = request.get_json()
    channel = data.get('channel')

    if channel is None:
        return jsonify({"status": "error", "message": "Missing 'channel' for reset."}), 400

    try:
        channel = int(channel)
        home_angle = 90
        testservo.set_servo_angle(channel, home_angle)
        logger.info(f"API: Reset servo {channel} to {home_angle}°")
        return jsonify({"status": "success", "message": f"Servo {channel} reset to {home_angle}°."})
    except ValueError as e:
        logger.error(f"API Error (reset): Invalid channel - {e}")
        return jsonify({"status": "error", "message": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"API Error (reset): Runtime error - {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logger.error(f"API Error (reset): Unexpected error - {e}")
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500

@app.route('/api/servo/random_test', methods=['POST'])
def api_run_random_test():
    """Moves a servo to a series of random positions."""
    loaded, error_response = check_servo_module()
    if not loaded:
        return jsonify(error_response), 503

    data = request.get_json()
    channel = data.get('channel')
    num_positions = data.get('positions', 5) # Default to 5 random positions

    if channel is None:
        return jsonify({"status": "error", "message": "Missing 'channel' for random test."}), 400

    try:
        channel = int(channel)
        num_positions = int(num_positions)
        logger.info(f"API: Starting random test for servo {channel} ({num_positions} positions)...")

        for i in range(num_positions):
            random_angle = random.randint(0, 180)
            testservo.set_servo_angle(channel, random_angle)
            logger.info(f"API Random Test (Servo {channel}): Moved to {random_angle}°")
            time.sleep(0.8) # Pause between movements, adjust as needed

        testservo.set_servo_angle(channel, 90) # Return to center
        logger.info(f"API: Random test complete for servo {channel}. Returned to 90°.")
        return jsonify({"status": "success", "message": f"Random position test complete for servo {channel}."})
    except ValueError as e:
        logger.error(f"API Error (random_test): Invalid input - {e}")
        return jsonify({"status": "error", "message": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"API Error (random_test): Runtime error - {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logger.error(f"API Error (random_test): Unexpected error - {e}")
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500

           
@app.route('/testservo')
def test_servo_page():
    # --- Add Authentication Check ---
    if 'user_id' not in session:
        flash('Please log in to access the servo control page.', 'info')
        return redirect(url_for('index'))

    # Pass the servo_module_loaded status to the template
    # The variable servo_module_loaded is now correctly defined globally
    return render_template('test_servo.html', servo_module_loaded=servo_module_loaded)

 # API endpoint to set an individual servo angle
@app.route('/api/servo/set_angle', methods=['POST'])
def api_set_servo_angle():
    """Sets the angle of a specific servo."""
    loaded, error_response = check_servo_module()
    if not loaded:
        return jsonify(error_response), 503

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload."}), 400

    channel = data.get('channel')
    angle = data.get('angle')

    if channel is None or angle is None:
        return jsonify({"status": "error", "message": "Missing 'channel' or 'angle' in request."}), 400

    try:
        channel = int(channel)
        angle = int(angle)
        testservo.set_servo_angle(channel, angle)
        logger.info(f"API: Set servo {channel} to {angle}°")
        return jsonify({"status": "success", "message": f"Servo {channel} set to {angle}°"})
    except ValueError as e:
        logger.error(f"API Error (set_angle): Invalid input - {e}")
        return jsonify({"status": "error", "message": str(e)}), 400
    except RuntimeError as e: # Catch errors from testservo.py (e.g., kit not initialized)
        logger.error(f"API Error (set_angle): Runtime error - {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logger.error(f"API Error (set_angle): Unexpected error - {e}")
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500

## API endpoint to run a basic sweep on a specific channel
@app.route('/api/servo/sweep_basic', methods=['POST'])
def api_sweep_basic():
    """Runs a basic sweep test on a servo."""
    loaded, error_response = check_servo_module()
    if not loaded:
        return jsonify(error_response), 503

    data = request.get_json()
    channel = data.get('channel')
    if channel is None:
        return jsonify({"status": "error", "message": "Missing 'channel' for sweep test."}), 400
    try:
        channel = int(channel)
        logger.info(f"API: Starting basic sweep for servo {channel}...")
        testservo.sweep_channel_basic(channel)
        logger.info(f"API: Basic sweep complete for servo {channel}.")
        return jsonify({"status": "success", "message": f"Basic sweep test complete for servo {channel}."})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500


# API endpoint to run a smooth sweep on a specific channel
@app.route('/api/servo/sweep_smooth', methods=['POST'])
def api_sweep_smooth():
    """Runs a smooth sweep test on a servo."""
    loaded, error_response = check_servo_module()
    if not loaded:
        return jsonify(error_response), 503

    data = request.get_json()
    channel = data.get('channel')
    if channel is None:
        return jsonify({"status": "error", "message": "Missing 'channel' for smooth sweep test."}), 400
    try:
        channel = int(channel)
        logger.info(f"API: Starting smooth sweep for servo {channel}...")
        testservo.sweep_channel_smooth(channel) # Assuming this function exists in testservo.py
        logger.info(f"API: Smooth sweep complete for servo {channel}.")
        return jsonify({"status": "success", "message": f"Smooth sweep test complete for servo {channel}."})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    except AttributeError: # If sweep_channel_smooth doesn't exist
         logger.error(f"API Error: sweep_channel_smooth not found in testservo module.")
         return jsonify({"status": "error", "message": "Smooth sweep function not available in servo module."}), 501 # Not Implemented
    except Exception as e:
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500


# API endpoint to run the test all channels sequence
@app.route('/api/servo/test_all', methods=['POST'])
def api_test_all_servos():
    # --- Add Authentication Check ---
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401

    logger.info("API: Received request to test all servos.")

    if servo_module is None:
         logger.error("API: Servo control module not available.")
         return jsonify({"success": False, "error": "Servo control module not available. Check server logs."}), 500

    try:
        servo_module.test_all_channels()

        logger.info("API: All servos test sequence command sent.")
        return jsonify({"success": True, "message": f"All servos test sequence complete (Simulated)" if sys.platform != 'linux' else "All servos test sequence complete."})

    except Exception as e:
        logger.error(f"API: Error during all servos test: {e}")
        return jsonify({"success": False, "error": f"Server error during all servos test: {e}"}), 500






# Serve static files from the build folder
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(os.path.join(app.static_folder, 'static'), path)

@app.route('/nemo')
def nemo_page():
    return render_template('nemo.html')


#--- PARCEL GEN
@app.route('/parcelgenerator')
def parcelgen():
    return render_template('parcelgen.html')

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


# ------ OCR CONTROL







if __name__ == '__main__':
    logger.info("Starting Flask server")
    app.run(debug=True, host='0.0.0.0', port=5000)
    

