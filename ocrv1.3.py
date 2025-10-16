import cv2
import pytesseract
from PIL import Image
import os
import time
import requests
import json
import re
from threading import Thread
from adafruit_servokit import ServoKit


# --- CONFIGURATION ---
IMAGE_DIRECTORY = 'simulation/incoming_images'
FLASK_SERVER_URL = 'http://192.168.26.219:5000'
OCR_LANGUAGE = 'eng'  # Adjust if your receipts have other languages

# Servo control pins (adjust as needed for your hardware)
SERVO_CHANNELS = {
    0: 0, #Luzon
    1: 1, #Visayas
    2: 2, #Mindanao
}

PCA9685_CHANNELS = 16

# List of Philippine provinces for validation
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


class SortingController:
    """
    Controller for package sorting servos based on OCR-extracted addresses
    
    Mappings:
    - Box 1 (Luzon) = Servo Channel 0
    - Box 2 (Visayas) = Servo Channel 1
    - Box 3 (Mindanao) = Servo Channel 2
    - Box 4 (Unknown) = All servos move 90 degrees
    """
    
    def __init__(self, servo_channels):
        """Initialize the sorting controller with servo channels"""
        self.servo_channels = servo_channels
        
        # Initialize PCA9685 board (address defaults to 0x40)
        self.pca = ServoKit(channels=PCA9685_CHANNELS)
        
        # Configure servo parameters (adjust these based on your servo specs)
        for channel in self.servo_channels.values():
            # Set min and max pulse width for more precise control
            # These values might need adjustment for your specific servos
            self.pca.servo[channel].set_pulse_width_range(500, 2500)
            
        print("Sorting Controller initialized with PCA9685 servos on channels:", self.servo_channels)
        time.sleep(1)  # Allow servos to initialize
        self.reset_all_servos()
        
        
    def cleanup(self):
        """Clean up resources when done"""
        # Move all servos to neutral position before exiting
        self.reset_all_servos()
        print("Sorting Controller resources cleaned up")
    
    def move_servo(self, channel, angle):
        """
        Move a specific servo to the given angle
        
        Args:
            channel (int): Servo channel number
            angle (float): Desired angle in degrees (0-180)
        """
        if channel not in self.servo_channels:
            print(f"Error: Servo channel {channel} not mapped")
            return
            
        pca_channel = self.servo_channels[channel]
        self.pca.servo[pca_channel].angle = angle
        
        # Brief pause to allow servo to move
        time.sleep(0.5)
        
    def reset_all_servos(self):
        """Reset all servos to their default position (0 degrees)"""
        for channel in self.servo_channels.values():
            self.pca.servo[channel].angle = 0
            
    def sort_package(self, province):
        """
        Sort a package based on province to the appropriate box using servos
        
        Args:
            province (str): The province extracted from OCR
        
        Returns:
            dict: Information about the sorting operation
        """
        classification = self.classify_address(province)
        box_number = classification['box_number']
        region = classification['region']
        
        print(f"Sorting package to box {box_number} ({region})")
        
        # Execute the appropriate servo movement based on box number
        if box_number == 0:  # Unknown - move all servos to 90 degrees
            print("Unknown province - moving all servos to 90 degrees")
            for channel in self.servo_channels.values():
                self.pca.servo[channel].angle = 90
            time.sleep(2)  # Allow package to be sorted
            self.reset_all_servos()
                
        else:  # Known region - move specific servo
            # Box number to channel mapping according to requirements
            servo_channel = box_number - 1
            
            print(f"Activating servo on channel {servo_channel}")
            self.move_servo(servo_channel, 45)  # Move to 45 degrees to activate sorting mechanism
            time.sleep(2)  # Allow package to be sorted
            self.move_servo(servo_channel, 0)  # Reset servo position
            
        return classification
    
    def classify_address(self, province):
        """
        Classifies a Philippine province into one of 3 regional sorting boxes
        
        Args:
            province (str): Province name extracted from OCR
            
        Returns:
            dict: Contains box number, region name, and matching condition
        """
        # Check if province is valid
        if not province or province == "Unknown":
            return {
                'box_number': 0,  # Default box for unrecognized addresses
                'region': 'Unknown',
                'condition': 'province not found or unrecognized'
            }
        
        # Define provinces per region based on your requirements
        # Luzon provinces (Box 1) - includes Metro Manila
        luzon_provinces = [
            "Metro Manila", "Batangas", "Benguet", "Abra", "Albay", "Aurora", "Bataan", "Bulacan", 
            "Cagayan", "Camarines Norte", "Camarines Sur", "Catanduanes", "Cavite", 
            "Ifugao", "Ilocos Norte", "Ilocos Sur", "Isabela", "Kalinga", "La Union", 
            "Laguna", "Marinduque", "Masbate", "Mountain Province", "Nueva Ecija", 
            "Nueva Vizcaya", "Occidental Mindoro", "Oriental Mindoro", "Palawan", 
            "Pampanga", "Pangasinan", "Quezon", "Quirino", "Rizal", "Romblon", 
            "Sorsogon", "Tarlac", "Zambales"
        ]
        
        if province in luzon_provinces:
            return {
                'box_number': 1,
                'region': 'Luzon',
                'condition': f'province in Luzon provinces list'
            }
        
        # Visayas provinces (Box 2)
        visayas_provinces = [
            "Cebu", "Iloilo", "Aklan", "Antique", "Bohol", "Biliran", "Capiz", 
            "Eastern Samar", "Guimaras", "Leyte", "Negros Occidental", "Negros Oriental", 
            "Northern Samar", "Samar", "Siquijor", "Southern Leyte"
        ]
        
        if province in visayas_provinces:
            return {
                'box_number': 2,
                'region': 'Visayas',
                'condition': f'province in Visayas provinces list'
            }
        
        # Mindanao provinces (Box 3)
        mindanao_provinces = [
            "Davao del Sur", "Misamis Oriental", "Agusan del Norte", "Agusan del Sur", 
            "Basilan", "Bukidnon", "Camiguin", "Compostela Valley", "Cotabato", "Davao del Norte", 
            "Davao Occidental", "Davao Oriental", "Dinagat Islands", "Lanao del Norte", 
            "Lanao del Sur", "Maguindanao", "Misamis Occidental", "North Cotabato", 
            "Sarangani", "South Cotabato", "Sultan Kudarat", "Sulu", "Surigao del Norte", 
            "Surigao del Sur", "Tawi-Tawi", "Zamboanga del Norte", "Zamboanga del Sur", 
            "Zamboanga Sibugay"
        ]
        
        if province in mindanao_provinces:
            return {
                'box_number': 3,
                'region': 'Mindanao',
                'condition': f'province in Mindanao provinces list'
            }
        
        # If province doesn't match any known region
        return {
            'box_number': 0,  # Default box for unrecognized addresses
            'region': 'Unknown',
            'condition': f'province "{province}" not recognized'
        }


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

def extract_address_from_image(image_path):
    """
    Extracts address information (specifically province) from an image using OCR,
    tailored for the Lazada receipt format.

    Args:
        image_path (str): Path to the image file.

    Returns:
        dict: A dictionary containing extracted address fields (or None if extraction fails).
    """
    try:
        # Preprocess the image
        pil_img = preprocess_image(image_path)
        
        # Apply OCR with custom configuration for better results
        custom_config = f'--oem 3 --psm 6 -l {OCR_LANGUAGE}'
        text = pytesseract.image_to_string(pil_img, config=custom_config)
        print(f"Raw OCR Output for {os.path.basename(image_path)}:\n{text}")
        
        # Extract province using a more robust approach
        province = extract_province_from_text(text)
        
        extracted_data = {'province': province}
        print(f"Extracted Data from {image_path}: {extracted_data}")
        return extracted_data

    except Exception as e:
        print(f"Error during OCR on {image_path}: {str(e)}")
        return None

def extract_province_from_text(text):
    """
    Extracts province information from OCR text using multiple strategies.
    
    Args:
        text (str): OCR extracted text.
        
    Returns:
        str or None: Extracted province name or None if not found.
    """
    # Strategy 1: Look for "Ship to:" section
    ship_to_pattern = re.compile(r'ship\s+to:.*?\n(.*?)(?=\n\n|\Z)', re.IGNORECASE | re.DOTALL)
    ship_to_match = ship_to_pattern.search(text)
    
    if ship_to_match:
        address_block = ship_to_match.group(1)
        # Process the address block to find province
        lines = [line.strip() for line in address_block.split('\n') if line.strip()]
        
        # Check each line for comma-separated parts that could contain the province
        for line in lines:
            if ',' in line:
                parts = [part.strip() for part in line.split(',')]
                # The province is typically either the second-to-last or last part
                for i in [-2, -1]:
                    if abs(i) <= len(parts):
                        potential_province = parts[i].strip()
                        # Check if it matches any known province
                        for province in PHILIPPINE_PROVINCES:
                            if province.lower() in potential_province.lower():
                                return province
    
    # Strategy 2: Look for any lines that contain known provinces
    lines = text.split('\n')
    for line in lines:
        for province in PHILIPPINE_PROVINCES:
            if province.lower() in line.lower():
                return province
    
    return None

def monitor_image_directory(sorting_controller):
    """
    Monitors the specified directory for new image files, processes them with OCR,
    activates the appropriate servo, and optionally sends data to the Flask server.
    
    Args:
        sorting_controller: Initialized SortingController object
    """
    processed_files = set()
    
    # First, check if directory exists
    if not os.path.exists(IMAGE_DIRECTORY):
        os.makedirs(IMAGE_DIRECTORY)
        print(f"Created directory: {IMAGE_DIRECTORY}")
    
    print(f"Monitoring directory: {IMAGE_DIRECTORY}")
    
    while True:
        try:
            # Get list of image files in the directory
            if not os.path.exists(IMAGE_DIRECTORY):
                print(f"Warning: Directory {IMAGE_DIRECTORY} no longer exists. Recreating...")
                os.makedirs(IMAGE_DIRECTORY)
                time.sleep(5)
                continue
                
            files = [f for f in os.listdir(IMAGE_DIRECTORY) 
                    if f.lower().endswith(('.png', '.jpg', '.jpeg')) and 
                    os.path.isfile(os.path.join(IMAGE_DIRECTORY, f))]
            
            # Process new files
            for filename in files:
                if filename not in processed_files:
                    image_path = os.path.join(IMAGE_DIRECTORY, filename)
                    print(f"\nProcessing new image: {image_path}")
                    
                    # Check if file is accessible
                    if not os.access(image_path, os.R_OK):
                        print(f"Warning: No read permission for {image_path}")
                        continue
                        
                    # Wait for the file to be completely written
                    file_size = -1
                    current_size = os.path.getsize(image_path)
                    while file_size != current_size:
                        file_size = current_size
                        time.sleep(1)  # Wait a second before checking again
                        # Check if file still exists
                        if not os.path.exists(image_path):
                            break
                        current_size = os.path.getsize(image_path)
                    
                    if not os.path.exists(image_path):
                        print(f"File {image_path} was deleted during processing")
                        continue
                        
                    address_data = extract_address_from_image(image_path)

                    if address_data and address_data.get('province'):
                        province = address_data.get('province')
                        
                        # Activate servo based on province
                        sort_result = sorting_controller.sort_package(province)
                        
                        # Prepare data to send to Flask server (if used)
                        payload = {
                            'image_filename': filename,
                            'extracted_province': province,
                            'sorting_box': sort_result['box_number'],
                            'region': sort_result['region'],
                            'timestamp': time.time()
                        }

                        try:
                            # Send data to Flask server (if enabled)
                            if FLASK_SERVER_URL:
                                response = requests.post(FLASK_SERVER_URL, json=payload, timeout=10)
                                response.raise_for_status()  # Raise an exception for bad status codes
                                print(f"Data sent to Flask server for {filename}. Response: {response.text}")
                        except requests.exceptions.RequestException as e:
                            print(f"Error sending data to Flask server: {e}")
                    else:
                        print(f"Could not extract province from {filename}. Moving to unknown box.")
                        # Handle unknown case - move all servos to 90 degrees
                        sorting_controller.sort_package(None)

                    processed_files.add(filename)
                    
            # Clean up processed_files set for files that no longer exist
            processed_files = {f for f in processed_files if os.path.exists(os.path.join(IMAGE_DIRECTORY, f))}
            
        except Exception as e:
            print(f"Error in monitoring loop: {str(e)}")
            
        time.sleep(5)  # Check for new files every 5 seconds

def run_test_sequence(sorting_controller):
    """
    Run a test sequence to verify all servos are working properly
    
    Args:
        sorting_controller: Initialized SortingController object
    """
    print("Running test sequence for all servo channels...")
    
    # Test each region
    test_provinces = ["Metro Manila", "Cebu", "Davao del Sur", "Unknown"]
    
    for province in test_provinces:
        print(f"\nTesting servo for province: {province}")
        result = sorting_controller.sort_package(province)
        print(f"Package sorted to Box {result['box_number']} ({result['region']})")
        time.sleep(1)  # Pause between tests
    
    print("\nTest sequence completed.")

if __name__ == "__main__":
    # Check if Tesseract is installed and configured
    try:
        pytesseract.get_tesseract_version()
        print(f"Tesseract version: {pytesseract.get_tesseract_version()}")
    except pytesseract.TesseractNotFoundError:
        print("Error: Tesseract OCR is not installed or not in PATH")
        print("Please install Tesseract OCR and make sure it's in your system PATH")
        exit(1)
        
    # Initialize sorting controller with PCA9685
    try:
        print("Initializing sorting controller with PCA9685 servo channels:", SERVO_CHANNELS)
        controller = SortingController(SERVO_CHANNELS)
        
        # Run initial test sequence to verify servos
        run_test_sequence(controller)
        
        # Start monitoring for images
        print("\nStarting image monitoring system...")
        monitor_image_directory(controller)
        
    except KeyboardInterrupt:
        print("\nSystem shutdown requested. Cleaning up...")
    finally:
        if 'controller' in locals():
            controller.cleanup()
        print("System shutdown complete.")
