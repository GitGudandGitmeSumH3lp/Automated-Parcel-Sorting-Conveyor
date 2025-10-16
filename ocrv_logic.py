import cv2
import pytesseract
from PIL import Image
import os
import time
import requests
import json
import re
from threading import Thread # Imported but not used
import logging
import sys # Import sys for platform check if needed for hardware
import platform
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


IS_LINUX = platform.system() == 'Linux'

if IS_LINUX:
    from adafruit_servokit import ServoKit
else:
    # Create a dummy class to simulate ServoKit
    class ServoKit:
        def __init__(self, channels):
            print("Mock ServoKit initialized (non-Linux)")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
IMAGE_DIRECTORY = 'simulation/incoming_images'
FLASK_SERVER_URL = 'http://192.168.26.219:5000' # Your Flask server URL
OCR_LANGUAGE = 'eng'  # Adjust if your receipts have other languages

# --- Sorting Mode Configuration ---
# Choose the active sorting mode: 'region' or 'courier'
SORTING_MODE = 'region' # <--- SET YOUR DESIRED SORTING MODE HERE

# Servo control channels mapping
# Maps sorting categories (regions or couriers) to physical PCA9685 channels
# Assuming different physical channels for each sorting mode for clarity
SERVO_CHANNELS = {
    'region': {
        'Luzon': 0,
        'Visayas': 1,
        'Mindanao': 2,
        # Unknown region will move all region servos
    },
    'courier': {
        'Shopee': 3,
        'Lazada': 4,
        'Jnt': 5,
        'Ninjavan': 6,
        # Unknown courier will move all courier servos
    }
}

# Default angle for sorting action (adjust based on your mechanism)
SORTING_ANGLE = 45 # Angle to move servo for sorting

PCA9685_CHANNELS = 16 # Total channels on PCA9685



# List of Philippine provinces for region validation
PHILIPPINE_PROVINCES = [
    "Metro Manila", "Batangas", "Benguet", "Abra", "Albay", "Aurora", "Bataan", "Bulacan",
    "Cagayan", "Camarines Norte", "Camarines Sur", "Catanduanes", "Cavite", "Ifugao",
    "Ilocos Norte", "Ilocos Sur", "Isabela", "Kalinga", "La Union", "Laguna", "Marinduque",
    "Masbate", "Mountain Province", "Nueva Ecija", "Nueva Vizcaya", "Occidental Mindoro",
    "Oriental Mindoro", "Palawan", "Pampanga", "Pangasinan", "Quezon", "Quirino", "Rizal",
    "Romblon", "Sorsogon", "Tarlac", "Zambales", "Cebu", "Iloilo", "Aklan", "Antique",
    "Bohol", "Biliran", "Capiz", "Eastern Samar", "Guimaras", "Leyte", "Negros Occidental",
    "Negros Oriental", "Northern Samar", "Samar", "Siquijor", "Southern Leyte",
    "Davao del Sur", "Misamis Oriental", "Agusan del Norte", "Agusan del Sur", "Basilan",
    "Bukidnon", "Camiguin", "Compostela Valley", "Cotabato", "Davao del Norte",
    "Davao Occidental", "Davao Oriental", "Dinagat Islands", "Lanao del Norte",
    "Lanao del Sur", "Maguindanao", "Misamis Occidental", "North Cotabato", "Sarangani",
    "South Cotabato", "Sultan Kudarat", "Sulu", "Surigao del Norte", "Surigao del Sur",
    "Tawi-Tawi", "Zamboanga del Norte", "Zamboanga del Sur", "Zamboanga Sibugay"
]

TRACKING_ID_PATTERNS = {
    "LAZADA": r'\bLZD-?PH-?\d{12,15}\b',      # Requires LZD-PH- prefix, followed by 12-15 digits
    "SHOPEE": r'\bSPX(?:PH|MY|SG|TH|ID|VN|BR)?[A-Za-z0-9vgxVGX]{10,20}\b', # Added 'xX' and A-Za-z
    "J&T": r'\b(?:JNT|JT)\d{10,15}\b',        # Requires JNT or JT prefix, followed by 10-15 digits
    "NINJAVAN": r'\bNV\d{10,20}\b',          # Requires NV prefix, followed by 10-20 digits
    "LBC": r'\bLBC\d{10,15}PH\b',            # Requires LBC prefix and PH suffix with digits in between
    "DHL": r'\b(?:[A-Z]{2}\d{9}[A-Z]{2})|(?:[0-9]{10}(?![0-9]))\b', # Standard international format OR 10 digits not followed by another digit
    "FEDEX": r'\b(?:\d{12})|(?:96\d{20})|(?:[0-9]{15})\b', # Common FedEx formats

}

FUZZY_MATCH_THRESHOLD = 75 

# List of common courier names for courier validation/extraction
COURIER_NAMES = [
    "Shopee", "Lazada", "J&T", "J&T Express", "Ninja Van", "Ninjavan", "LBC", "DHL", "FedEx", "Grab Express"
    # Add more courier names as needed
]

# --- Image Processing and OCR Functions ---

def preprocess_image(image_path):
    """
    Preprocesses the image to improve OCR accuracy.

    Args:
        image_path (str): Path to the image file.

    Returns:
        PIL.Image: Preprocessed image.
    """
    # Read the image using OpenCV
    img = cv2.imread(image_path)
    if img is None:
        logger.error(f"Could not read image from {image_path}")
        raise ValueError(f"Could not read image from {image_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply adaptive thresholding to improve text visibility
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Convert back to PIL Image for Tesseract
    pil_img = Image.fromarray(thresh)
    return pil_img

def extract_data_from_image(image_path):
    """
    Extracts address information (province) and courier name from an image using OCR.

    Args:
        image_path (str): Path to the image file.

    Returns:
        dict: A dictionary containing extracted fields (e.g., 'province', 'courier').
              Returns {'province': None, 'courier': None} if extraction fails.
    """
    raw_text = ""
    try:
        # Preprocess the image
        pil_img = preprocess_image(image_path)

        # Apply OCR with custom configuration
        custom_config = f'--oem 3 --psm 6 -l {OCR_LANGUAGE}'
        raw_text = pytesseract.image_to_string(pil_img, config=custom_config)
        logger.info(f"Raw OCR Output for {os.path.basename(image_path)}:\n{raw_text}")

        # Extract province and courier using updated functions
        province = extract_province_from_text(raw_text)
        courier = extract_courier_from_text(raw_text)

        extracted_data = {'province': province, 'courier': courier, 'raw_text': raw_text}
        logger.info(f"Extracted Data from {image_path}: {extracted_data}")
        return extracted_data

    except Exception as e:
        logger.error(f"Error during OCR on {image_path}: {str(e)}")
        return {'province': None, 'courier': None, 'raw_text': raw_text} # Return None for fields on error


def extract_province_from_text(text):
    """
    Extracts province information from OCR text using multiple strategies.

    Args:
        text (str): OCR extracted text.

    Returns:
        str or None: Extracted province name or None if not found.
    """
    if not text:
        return None

    # Strategy 1: Look for "Ship to:" or "Delivery Address:" section
    # Added "Delivery Address:" as an alternative pattern
    address_pattern = re.compile(r'(ship\s+to:|delivery\s+address:).*?\n(.*?)(?=\n\n|\Z)', re.IGNORECASE | re.DOTALL)
    address_match = address_pattern.search(text)

    if address_match:
        address_block = address_match.group(2) # Capture the content after the label
        lines = [line.strip() for line in address_block.split('\n') if line.strip()]

        # Check each line for comma-separated parts that could contain the province
        for line in lines:
            if ',' in line:
                parts = [part.strip() for part in line.split(',')]
                # The province is typically either the second-to-last or last part
                for i in [-2, -1]:
                    if abs(i) <= len(parts):
                        potential_province = parts[i].strip()
                        # Check if it matches any known province (case-insensitive)
                        for province in PHILIPPINE_PROVINCES:
                            if province.lower() == potential_province.lower(): # Exact match check first
                                return province
                                                # If direct match fails for this part, try fuzzy match on this part
                        best_match = process.extractOne(
                            potential_province,
                            PHILIPPINE_PROVINCES,
                            scorer=fuzz.ratio,
                            score_cutoff=FUZZY_MATCH_THRESHOLD
                        )
                        if best_match:
                            matched_province, score = best_match
                            logger.info(f"Fuzzy province match in address block: '{matched_province}' with score {score} for text '{potential_province}'")
                            return matched_province
                        
    # Strategy 2: Look for any lines that contain known provinces (case-insensitive)
    lines = text.split('\n')
    for line in lines:
        for province in PHILIPPINE_PROVINCES:
            if province.lower() in line.lower():
                return province # Return the first match found
        # If direct line match fails, try fuzzy matching the entire line against province names
        best_match = process.extractOne(
            line, # Match the whole line
            PHILIPPINE_PROVINCES,
            scorer=fuzz.partial_ratio, # Use partial_ratio as the line might contain more than just the province
            score_cutoff=FUZZY_MATCH_THRESHOLD
        )
        if best_match:
            matched_province, score = best_match
            logger.info(f"Fuzzy partial match found for province: '{matched_province}' with score {score} in line '{line}'")
            return matched_province
        
    # --- Strategy 3: Fuzzy Matching on the entire text (least precise but can catch some) ---
    logger.info("No pattern or direct substring match for province, attempting fuzzy match on entire text...")
    best_match = process.extractOne(
            text, # Match against the entire raw text
            PHILIPPINE_PROVINCES,
            scorer=fuzz.partial_ratio, # Use partial_ratio as province name is only a part of the text
            score_cutoff=FUZZY_MATCH_THRESHOLD
        )

    if best_match:
            matched_province, score = best_match
            logger.info(f"Fuzzy partial match found for province in entire text: '{matched_province}' with score {score}")
            return matched_province


    logger.warning(f"Could not extract province from text using any strategy:\n{text[:200]}...")
    return None # Return None if no province is found after all strategies
    

def extract_courier_from_text(text):
    """
    Extracts courier name from OCR text using keywords.

    Args:
        text (str): OCR extracted text.

    Returns:
        str or None: Extracted courier name or None if not found.
    """
    if not text:
        return None

    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()
    logger.info(f"Attempting to extract courier from text (lower):\n{text_lower[:300]}...")
    
    # --- Strategy 1: Check for Tracking ID Patterns (Prioritize) ---
    for courier_name, pattern in TRACKING_ID_PATTERNS.items():
        if re.search(pattern, text): # Use original text here as patterns might be case-sensitive or mix case
            logger.info(f"Matched tracking ID pattern '{pattern}' for courier '{courier_name}'")
            # Return the standardized courier name directly from the TRACKING_ID_PATTERNS key

    # ----Fallback to Searching for Courier names
    for courier_name in COURIER_NAMES:
        courier_lower = courier_name.lower()  
        # Use word boundaries (\b) to avoid matching parts of other words
        # e.g., avoid matching "an" in "banana" if "an" is in COURIER_NAMES
        # Also handle variations like "J&T" vs "J&T Express" vs "JNT"
        patterns = [
            r'\b' + re.escape(courier_lower) + r'(\W|\d|$)',
            r'\b' + re.escape(courier_lower).replace('&', '.*?') + r'(\W|\d|$)',
            r'\b' + re.escape(courier_name.lower()) + r'\b', # Exact word match
            r'\b' + re.escape(courier_name.lower()).replace('&', '.*?') + r'\b', # Handle '&' variations
            r'\b' + re.escape(courier_name.lower()).replace(' ', '.*?') + r'\b', # Handle space variations
            re.escape(courier_lower),
        ]

        for i, pattern in enumerate(patterns):
            compiled_pattern = re.compile(pattern)
            if compiled_pattern.search(text_lower):
                logger.info(f"Matched courier name pattern {i+1} ('{pattern}') for courier '{courier_name}'")
                # --- Standardization Step (Recommended) ---
                # Standardize the found courier name before returning
                standardized_courier = courier_name.upper().replace(' ', '').replace('&', '')
                logger.info(f"Standardized courier name from text match: {standardized_courier}")
                return standardized_courier 
    
    # --- Strategy 3: Fuzzy Matching (Fallback if direct/regex match fails) ---
    logger.info("No direct or regex match for courier name, attempting fuzzy match...")
    
    # Get the best fuzzy match from the COURIER_NAMES list against the raw text
    # process.extractOne returns a tuple: (best_match, score)
    best_match = process.extractOne(
        text, # Search within the entire raw text
        COURIER_NAMES, # List of choices to match against
        scorer=fuzz.ratio, # Use ratio similarity score
        score_cutoff=FUZZY_MATCH_THRESHOLD # Only consider matches above this score
    )

    if best_match:
        matched_name, score = best_match
        logger.info(f"Fuzzy match found: '{matched_name}' with score {score}")
        # --- Standardization Step ---
        standardized_courier = matched_name.upper().replace(' ', '').replace('&', '')
        logger.info(f"Standardized courier name from fuzzy match: {standardized_courier}")
        return standardized_courier
    else:
        logger.warning(f"No fuzzy match found for courier name above threshold {FUZZY_MATCH_THRESHOLD} in text:\n{text[:300]}...")
        return None # Return None if no fuzzy match is found


# --- Sorting Controller Class ---
class SortingController:
    """
    Controller for package sorting servos based on OCR-extracted data (Region or Courier).
    """

    def __init__(self, servo_channels_mapping):
        """Initialize the sorting controller with servo channel mappings for different modes."""
        self.servo_channels_mapping = servo_channels_mapping
        self.pca = None # Initialize PCA9685 later if running on Pi

        # Attempt to initialize PCA9685 only if on a Linux-like platform
        # This prevents crashes on Windows simulation
        if sys.platform.startswith('linux'):
             logger.info("Running on Linux, attempting to initialize PCA9685...")
             try:
                 # Initialize PCA9685 board (address defaults to 0x40)
                 # Ensure I2C is enabled and adafruit-blinka is installed
                 import board
                 import busio
                 i2c = busio.I2C(board.SCL, board.SDA)
                 self.pca = ServoKit(channels=PCA9685_CHANNELS, i2c=i2c)
                 logger.info("PCA9685 initialized.")

                 # Configure servo parameters for ALL relevant channels
                 all_used_channels = set()
                 for mode_channels in self.servo_channels_mapping.values():
                     all_used_channels.update(mode_channels.values())

                 logger.info(f"Configuring pulse width range for channels: {all_used_channels}")
                 for channel in all_used_channels:
                     try:
                         # Set min and max pulse width for more precise control
                         # These values might need adjustment for your specific servos
                         self.pca.servo[channel].set_pulse_width_range(500, 2500)
                     except Exception as e:
                          logger.warning(f"Could not set pulse range for PCA channel {channel}: {e}")

                 logger.info("Servo pulse width range configured.")
                 self.reset_all_servos() # Reset all controlled servos to default
                 logger.info("All controlled servos reset to 0 degrees.")

             except ImportError:
                 logger.error("Adafruit Blinka or ServoKit not found. Cannot initialize PCA9685.")
                 self.pca = None
             except Exception as e:
                 logger.error(f"Failed to initialize PCA9685 or I2C: {e}")
                 self.pca = None
        else:
            logger.info("Running on non-Linux platform. PCA9685 initialization skipped (simulation mode).")
            self.pca = None # Ensure pca is None

    def cleanup(self):
        """Clean up resources when done - reset servos if PCA is initialized."""
        if self.pca:
            logger.info("Sorting Controller cleanup: Resetting servos...")
            self.reset_all_servos()
            logger.info("Sorting Controller resources cleaned up.")
        else:
            logger.info("Sorting Controller cleanup: PCA9685 not initialized, no servos to reset.")


    def move_servo(self, pca_channel, angle):
        """
        Move a specific physical PCA9685 servo channel to the given angle.

        Args:
            pca_channel (int): Physical PCA9685 channel number (0-15).
            angle (float): Desired angle in degrees (0-180).
        """
        if self.pca is None:
            logger.info(f"Mock Servo Move: Channel {pca_channel} to {angle}°")
            # Simulate movement time in simulation mode
            time.sleep(0.1)
            return

        # Ensure channel is valid for PCA9685
        if not (0 <= pca_channel < PCA9685_CHANNELS):
            logger.warning(f"Invalid PCA9685 channel: {pca_channel}")
            return

        # Ensure angle is within valid range
        if not (0 <= angle <= 180):
             logger.warning(f"Invalid angle for servo channel {pca_channel}: {angle}")
             # Optionally clamp the angle or raise an error
             angle = max(0, min(180, angle)) # Clamp angle

        logger.info(f"Moving PCA9685 channel {pca_channel} to {angle}°")
        try:
            self.pca.servo[pca_channel].angle = angle
            # Brief pause to allow servo to move
            time.sleep(0.5) # Adjust delay as needed
        except Exception as e:
            logger.error(f"Error moving servo on PCA channel {pca_channel}: {e}")


    def reset_all_servos(self):
        """Reset all servos defined in the mappings to their default position (0 degrees)."""
        if self.pca is None:
            logger.info("Mock Servo Reset: Resetting all controlled servos to 0 degrees.")
            time.sleep(0.5) # Simulate reset time
            return

        all_used_channels = set()
        for mode_channels in self.servo_channels_mapping.values():
            all_used_channels.update(mode_channels.values())

        logger.info(f"Resetting PCA9685 channels {all_used_channels} to 0 degrees.")
        for pca_channel in all_used_channels:
            try:
                self.pca.servo[pca_channel].angle = 0
            except Exception as e:
                 logger.warning(f"Could not reset PCA channel {pca_channel}: {e}")
        time.sleep(0.5) # Allow servos to return


    def sort_package(self, sorting_data, mode='region'):
        """
        Sort a package based on extracted data and the specified mode (region or courier).

        Args:
            sorting_data (dict): Dictionary containing extracted data (e.g., {'province': 'Cebu', 'courier': 'Lazada'}).
            mode (str): The sorting mode to use ('region' or 'courier').

        Returns:
            dict: Information about the sorting operation result.
        """
        classification = {'mode': mode, 'category': 'Unknown', 'box_number': 0, 'region_or_courier': 'Unknown', 'condition': 'No data'}

        if mode == 'region':
            province = sorting_data.get('province')
            classification = self.classify_address(province)
            category = classification['region'] # Luzon, Visayas, Mindanao, Unknown
            channels_for_mode = self.servo_channels_mapping.get('region', {})
            unknown_category = 'Unknown' # Use 'Unknown' as the key for unknown region

        elif mode == 'courier':
            courier = sorting_data.get('courier')
            classification = self.classify_courier(courier)
            category = classification['courier'] # Shopee, Lazada, Jnt, Ninjavan, Unknown
            channels_for_mode = self.servo_channels_mapping.get('courier', {})
            unknown_category = 'Unknown' # Use 'Unknown' as the key for unknown courier

        else:
            logger.warning(f"Invalid sorting mode specified: {mode}. Defaulting to Unknown.")
            # No specific servo action for invalid mode, falls through to Unknown handling

        box_number = classification.get('box_number', 0) # Get box_number, default to 0 if not set

        logger.info(f"Sorting package by {mode}: Category '{category}' -> Box {box_number}")

        pca_channel_to_move = None

        # Find the physical PCA channel for the classified category in the current mode
        if category != unknown_category:
            # Find the key in channels_for_mode that matches the category
            # This handles cases where category string might not be the exact key (e.g., 'J&T' vs 'Jnt')
            for key, channel in channels_for_mode.items():
                if key.lower() == category.lower():
                    pca_channel_to_move = channel
                    break

        if pca_channel_to_move is not None: # Found a specific channel for the category
             logger.info(f"Activating servo on PCA channel {pca_channel_to_move} for {mode} category '{category}'")
             self.move_servo(pca_channel_to_move, SORTING_ANGLE) # Move to sorting angle
             time.sleep(2) # Allow package to be sorted (adjust time)
             self.move_servo(pca_channel_to_move, 0) # Reset servo position

        else: # Unknown category for the current mode
            logger.info(f"Unknown {mode} category '{category}' - Moving all servos for mode to 90 degrees.")
            # Move all servos associated with the active mode to a neutral/unknown position (e.g., 90 degrees)
            if channels_for_mode: # Only move if there are channels defined for this mode
                for pca_channel in channels_for_mode.values():
                    self.move_servo(pca_channel, 90) # Move to 90 degrees
                time.sleep(2) # Allow package to be sorted (adjust time)
                # Reset all servos for this mode back to 0
                for pca_channel in channels_for_mode.values():
                    self.move_servo(pca_channel, 0)


        return classification


    def classify_address(self, province):
        """
        Classifies a Philippine province into one of 3 regional sorting boxes.

        Args:
            province (str): Province name extracted from OCR

        Returns:
            dict: Contains box number, region name, and matching condition
        """
        # Check if province is valid
        if not province:
            return {
                'box_number': 0,  # Default box for unrecognized addresses
                'region': 'Unknown',
                'condition': 'province not found or empty'
            }

        # Define provinces per region based on your requirements
        # Luzon provinces (Box 1) - includes Metro Manila
        luzon_provinces = [p.lower() for p in [
            "Metro Manila", "Batangas", "Benguet", "Abra", "Albay", "Aurora", "Bataan", "Bulacan",
            "Cagayan", "Camarines Norte", "Camarines Sur", "Catanduanes", "Cavite",
            "Ifugao", "Ilocos Norte", "Ilocos Sur", "Isabela", "Kalinga", "La Union",
            "Laguna", "Marinduque", "Masbate", "Mountain Province", "Nueva Ecija",
            "Nueva Vizcaya", "Occidental Mindoro", "Oriental Mindoro", "Palawan",
            "Pampanga", "Pangasinan", "Quezon", "Quirino", "Rizal", "Romblon",
            "Sorsogon", "Tarlac", "Zambales"
        ]]

        if province.lower() in luzon_provinces:
            return {
                'box_number': 1,
                'region': 'Luzon',
                'condition': f'province "{province}" in Luzon provinces list'
            }

        # Visayas provinces (Box 2)
        visayas_provinces = [p.lower() for p in [
            "Cebu", "Iloilo", "Aklan", "Antique", "Bohol", "Biliran", "Capiz",
            "Eastern Samar", "Guimaras", "Leyte", "Negros Occidental", "Negros Oriental",
            "Northern Samar", "Samar", "Siquijor", "Southern Leyte"
        ]]

        if province.lower() in visayas_provinces:
            return {
                'box_number': 2,
                'region': 'Visayas',
                'condition': f'province "{province}" in Visayas provinces list'
            }

        # Mindanao provinces (Box 3)
        mindanao_provinces = [p.lower() for p in [
            "Davao del Sur", "Misamis Oriental", "Agusan del Norte", "Agusan del Sur",
            "Basilan", "Bukidnon", "Camiguin", "Compostela Valley", "Cotabato", "Davao del Norte",
            "Davao Occidental", "Davao Oriental", "Dinagat Islands", "Lanao del Norte",
            "Lanao del Sur", "Maguindanao", "Misamis Occidental", "North Cotabato",
            "Sarangani", "South Cotabato", "Sultan Kudarat", "Sulu", "Surigao del Norte",
            "Surigao del Sur", "Tawi-Tawi", "Zamboanga del Norte", "Zamboanga del Sur",
            "Zamboanga Sibugay"
        ]]

        if province.lower() in mindanao_provinces:
            return {
                'box_number': 3,
                'region': 'Mindanao',
                'condition': f'province "{province}" in Mindanao provinces list'
            }

        # If province doesn't match any known region
        return {
            'box_number': 0,  # Default box for unrecognized addresses
            'region': 'Unknown',
            'condition': f'province "{province}" not recognized'
        }

    def classify_courier(self, courier_name):
        """
        Classifies a courier name into one of the courier sorting boxes.

        Args:
            courier_name (str): Courier name extracted from OCR.

        Returns:
            dict: Contains box number, courier name, and matching condition.
        """
        if not courier_name:
             return {
                'box_number': 0, # Default box for unrecognized couriers
                'courier': 'Unknown',
                'condition': 'courier name not found or empty'
             }

        # Define couriers per box based on your requirements
        # Using lowercase for case-insensitive matching
        courier_mapping = {
            'SHOPEE': 1,
            'Lazada': 2,
            'Jnt': 3,
            'Ninjavan': 4,
            # Add other couriers and their box numbers
        }

        # Clean and standardize courier name for matching
        cleaned_courier = courier_name.lower().replace('express', '').strip() # Remove 'express' and trim whitespace

        for name, box_num in courier_mapping.items():
            if cleaned_courier in name.lower() or name.lower() in cleaned_courier:
                 return {
                    'box_number': box_num,
                    'courier': name, # Return the standardized name
                    'condition': f'matched "{courier_name}" to "{name}"'
                 }

        # If courier doesn't match any known courier
        return {
            'box_number': 0, # Default box for unrecognized couriers
            'courier': 'Unknown',
            'condition': f'courier "{courier_name}" not recognized'
        }


def monitor_image_directory(sorting_controller, sorting_mode):
    """
    Monitors the specified directory for new image files, processes them with OCR,
    activates the appropriate servo based on the sorting mode, and optionally sends data to the Flask server.

    Args:
        sorting_controller: Initialized SortingController object
        sorting_mode (str): The active sorting mode ('region' or 'courier').
    """
    processed_files = set()

    # First, check if directory exists
    if not os.path.exists(IMAGE_DIRECTORY):
        os.makedirs(IMAGE_DIRECTORY)
        logger.info(f"Created directory: {IMAGE_DIRECTORY}")

    logger.info(f"Monitoring directory: {IMAGE_DIRECTORY} with sorting mode: {sorting_mode}")

    while True:
        try:
            # Ensure directory still exists
            if not os.path.exists(IMAGE_DIRECTORY):
                logger.warning(f"Warning: Directory {IMAGE_DIRECTORY} no longer exists. Recreating...")
                os.makedirs(IMAGE_DIRECTORY)
                time.sleep(5)
                continue

            # Get list of image files in the directory
            files = [f for f in os.listdir(IMAGE_DIRECTORY)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg')) and
                    os.path.isfile(os.path.join(IMAGE_DIRECTORY, f))]

            # Process new files
            for filename in files:
                if filename not in processed_files:
                    image_path = os.path.join(IMAGE_DIRECTORY, filename)
                    logger.info(f"\nProcessing new image: {image_path}")

                    # Check if file is accessible
                    if not os.access(image_path, os.R_OK):
                        logger.warning(f"Warning: No read permission for {image_path}")
                        continue

                    # Wait for the file to be completely written (heuristic)
                    file_size = -1
                    try:
                        current_size = os.path.getsize(image_path)
                        while file_size != current_size:
                            file_size = current_size
                            time.sleep(0.5)  # Wait a bit before checking again
                            # Check if file still exists
                            if not os.path.exists(image_path):
                                break
                            current_size = os.path.getsize(image_path)
                    except FileNotFoundError:
                         logger.warning(f"File {image_path} was deleted during size check.")
                         continue # Skip this file

                    if not os.path.exists(image_path):
                        logger.warning(f"File {image_path} was deleted during processing")
                        continue

                    # Extract all relevant data
                    extracted_data = extract_data_from_image(image_path)

                    # Determine data to use for sorting based on mode
                    data_for_sorting = None
                    if sorting_mode == 'region':
                         data_for_sorting = extracted_data.get('province')
                    elif sorting_mode == 'courier':
                         data_for_sorting = extracted_data.get('courier')

                    sort_result = {'mode': sorting_mode, 'category': 'Unknown', 'box_number': 0, 'region_or_courier': 'Unknown', 'condition': 'No data'}

                    if data_for_sorting:
                        # Activate servo based on the extracted data and selected mode
                        # Pass the entire extracted_data dictionary to sort_package
                        sort_result = sorting_controller.sort_package(extracted_data, mode=sorting_mode)
                    else:
                        logger.warning(f"Could not extract required data for sorting mode '{sorting_mode}' from {filename}. Moving to unknown box.")
                        # Handle unknown case for the selected mode
                        sort_result = sorting_controller.sort_package(extracted_data, mode=sorting_mode) # Pass extracted_data even if empty


                    # Prepare data to send to Flask server
                    payload = {
                        'image_filename': filename,
                        'raw_text': extracted_data.get('raw_text', ''), # Include raw text
                        'extracted_province': extracted_data.get('province'),
                        'extracted_courier': extracted_data.get('courier'),
                        'sorting_mode_used': sorting_mode,
                        'sorted_category': sort_result.get('category'),
                        'sorting_box_number': sort_result.get('box_number'),
                        'timestamp': time.time() # Use Unix timestamp
                    }

                    try:
                        # Send data to Flask server (if enabled)
                        if FLASK_SERVER_URL:
                            # And it expects JSON data
                            # If your Flask route expects multipart/form-data with the image,
                            # you'll need to modify this request.
                            flask_endpoint = f'{FLASK_SERVER_URL}/receipts' # Example endpoint
                            logger.info(f"Sending data to Flask server at {flask_endpoint}")
                            response = requests.post(flask_endpoint, json=payload, timeout=10)
                            response.raise_for_status()  # Raise an exception for bad status codes
                            logger.info(f"Data sent to Flask server for {filename}. Response: {response.text}")
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Error sending data to Flask server: {e}")
                    except Exception as e:
                         logger.error(f"Unexpected error during Flask request: {e}")


                    processed_files.add(filename)

            # Clean up processed_files set for files that no longer exist
            processed_files = {f for f in processed_files if os.path.exists(os.path.join(IMAGE_DIRECTORY, f))}

        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")

        time.sleep(5)  # Check for new files every 5 seconds


def run_test_sequence(sorting_controller, mode):
    """
    Run a test sequence to verify sorting logic and servo movements for a given mode.

    Args:
        sorting_controller: Initialized SortingController object
        mode (str): The sorting mode to test ('region' or 'courier').
    """
    logger.info(f"Running test sequence for sorting mode: {mode}...")

    if mode == 'region':
        test_data_list = [
            {'province': 'Metro Manila'},
            {'province': 'Cebu'},
            {'province': 'Davao del Sur'},
            {'province': 'Batanes'}, # Unknown province
            {'province': None} # No province extracted
        ]
        print("Testing Region Sorting:")
        for data in test_data_list:
            province = data.get('province')
            print(f"\nTesting with province: {province}")
            result = sorting_controller.sort_package(data, mode='region')
            print(f"Sorting Result: {result}")
            time.sleep(1) # Pause between tests

    elif mode == 'courier':
        test_data_list = [
            {'courier': 'Shopee'},
            {'courier': 'Lazada Express'}, # Test variation
            {'courier': 'J&T'},
            {'courier': 'Ninja Van'},
            {'courier': 'Grab'}, # Known but maybe not in primary list
            {'courier': 'Some Random Courier'}, # Unknown courier
            {'courier': None} # No courier extracted
        ]
        print("Testing Courier Sorting:")
        for data in test_data_list:
            courier = data.get('courier')
            print(f"\nTesting with courier: {courier}")
            result = sorting_controller.sort_package(data, mode='courier')
            print(f"Sorting Result: {result}")
            time.sleep(1) # Pause between tests

    else:
        logger.warning(f"Cannot run test sequence for unknown mode: {mode}")

    logger.info(f"\nTest sequence for mode '{mode}' completed.")


if __name__ == "__main__":
    # Check if Tesseract is installed and configured
    try:
        pytesseract.get_tesseract_version()
        logger.info(f"Tesseract version: {pytesseract.get_tesseract_version()}")
    except pytesseract.TesseractNotFoundError:
        logger.error("Error: Tesseract OCR is not installed or not in PATH")
        logger.error("Please install Tesseract OCR and make sure it's in your system PATH")
        sys.exit(1) # Use sys.exit for cleaner exit

    # Initialize sorting controller with PCA9685
    try:
        logger.info("Initializing sorting controller...")
        # Pass the entire SERVO_CHANNELS mapping
        controller = SortingController(SERVO_CHANNELS)

        # Run test sequence for the selected mode
        run_test_sequence(controller, SORTING_MODE)

        # Start monitoring for images
        logger.info(f"\nStarting image monitoring system with mode: {SORTING_MODE}...")
        monitor_image_directory(controller, SORTING_MODE)

    except KeyboardInterrupt:
        logger.info("\nSystem shutdown requested. Cleaning up...")
    except Exception as e:
         logger.critical(f"An unhandled error occurred during startup or main loop: {e}", exc_info=True)
    finally:
        # Ensure cleanup is called even if errors occur before the main loop starts
        if 'controller' in locals():
            controller.cleanup()
        logger.info("System shutdown complete.")

