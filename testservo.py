#!/usr/bin/env python3
"""
MG995 Servo Test Script for Raspberry Pi 5 with PCA9685 PWM Controller
Adapted for use as a module callable from a Flask web server.
"""

import time
# Ensure adafruit_servokit is installed: pip install adafruit-circuitpython-servokit
from adafruit_servokit import ServoKit
# Ensure board and busio are installed: pip install adafruit-blinka
import board # type: ignore # Ignores Pylance missing stubs for board
import busio # type: ignore # Ignores Pylance missing stubs for busio
import logging

# Configure logging for this module
# This logger can be accessed by the Flask app if needed, or use Flask's own logger.
logger = logging.getLogger(__name__) # Use __name__ for module-specific logger
logger.setLevel(logging.INFO) # Set logging level as needed
# Add a handler if running this script directly or if Flask doesn't configure one for this logger
if not logger.hasHandlers():
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


# --- Global ServoKit Instance ---
kit = None # Initialize kit to None
servo_module_initialized_successfully = False

try:
    logger.info("Attempting to initialize I2C bus and PCA9685...")
    # It's good practice to ensure I2C is available.
    # On some systems, `board.SCL` might raise an error if not properly configured.
    if hasattr(board, 'SCL') and hasattr(board, 'SDA'):
        i2c = busio.I2C(board.SCL, board.SDA)
        # Create ServoKit instance with 16 channels (PCA9685 has 16 channels)
        kit = ServoKit(channels=16, i2c=i2c, frequency=50) # Standard frequency for servos
        logger.info("PCA9685 ServoKit initialized successfully.")

        # MG995 servo parameters - you may need to adjust these
        MIN_PULSE = 500   # Min pulse length in microseconds
        MAX_PULSE = 2500  # Max pulse length in microseconds

        def setup_channels_pulse_range():
            """Set up all channels with proper pulse range for MG995-like servos"""
            if kit is None:
                logger.error("Cannot set pulse range: ServoKit not initialized.")
                return
            logger.info(f"Setting pulse width range ({MIN_PULSE}-{MAX_PULSE}us) for all 16 channels...")
            for channel_num in range(16):
                try:
                    kit.servo[channel_num].set_pulse_width_range(MIN_PULSE, MAX_PULSE)
                except Exception as e:
                     logger.warning(f"Could not set pulse range for channel {channel_num}: {e}")
            logger.info("Pulse width range setup complete for all channels.")

        setup_channels_pulse_range()
        servo_module_initialized_successfully = True

    else:
        logger.error("board.SCL or board.SDA not available. I2C pins may not be configured on this system.")
        # kit remains None

except ImportError as ie:
    logger.error(f"Failed to import necessary libraries (adafruit_servokit, board, busio): {ie}. Please ensure they are installed.")
except RuntimeError as re: # Catches errors like "No I2C device at address: 0x40"
    logger.error(f"RuntimeError during PCA9685 initialization: {re}. Check I2C connection and address.")
except Exception as e:
    logger.error(f"An unexpected critical error occurred during PCA9685 or I2C initialization: {e}")
    # kit remains None

# --- Functions Callable from Flask ---

def _check_kit_and_channel(channel):
    """Internal helper to validate kit and channel."""
    if kit is None or not servo_module_initialized_successfully:
        logger.error("ServoKit not initialized or initialization failed. Hardware error or setup issue?")
        raise RuntimeError("ServoKit not initialized. Check hardware connection and server logs.")
    if not (0 <= channel <= 15):
        logger.error(f"Invalid channel: {channel}. Must be between 0 and 15.")
        raise ValueError("Channel must be between 0 and 15")
    return True

def set_servo_angle(channel, angle):
    """
    Sets a specific servo channel to a specific angle.
    Args:
        channel (int): The servo channel number (0-15).
        angle (int): The desired angle (0-180).
    """
    _check_kit_and_channel(channel)
    if not (0 <= angle <= 180):
        logger.error(f"Invalid angle: {angle} for channel {channel}. Must be between 0 and 180.")
        raise ValueError("Angle must be between 0 and 180")

    logger.info(f"Setting servo channel {channel} to {angle}°")
    try:
        kit.servo[channel].angle = angle
        # time.sleep(0.01) # Very small delay to allow command to be sent, usually not needed for single set
    except Exception as e:
        logger.error(f"Error setting angle for channel {channel} to {angle}°: {e}")
        raise # Re-raise the exception after logging

def sweep_channel_basic(channel):
    """Perform a basic 0-90-180-90 sweep on a single channel."""
    _check_kit_and_channel(channel)
    logger.info(f"Performing basic sweep on channel {channel} (0-90-180-90)")
    angles = [0, 40, 60, 90]
    delays = [0.7, 0.7, 0.7, 0.5] # Delays after reaching the angle
    try:
        for i, angle in enumerate(angles):
            logger.debug(f"Sweep channel {channel}: setting angle to {angle}°")
            kit.servo[channel].angle = angle
            time.sleep(delays[i])
        logger.info(f"Basic sweep complete for channel {channel}")
    except Exception as e:
        logger.error(f"Error during basic sweep for channel {channel}: {e}")
        raise

def sweep_channel_smooth(channel, step=2, delay=0.02):
    """Perform a smooth sweep on a single channel."""
    _check_kit_and_channel(channel)
    logger.info(f"Performing smooth sweep on channel {channel} (0 to 180 to 0)")
    try:
        # Sweep from 0 to 180
        for angle_val in range(0, 90, step):
            kit.servo[channel].angle = angle_val
            time.sleep(delay)
        time.sleep(0.3) # Pause at 180

        # Sweep from 180 to 0
        for angle_val in range(90, -1, -step):
            kit.servo[channel].angle = angle_val
            time.sleep(delay)
        time.sleep(0.3) # Pause at 0

        kit.servo[channel].angle = 90 # Return to center
        time.sleep(0.5)
        logger.info(f"Smooth sweep complete for channel {channel}, returned to 90°.")
    except Exception as e:
        logger.error(f"Error during smooth sweep for channel {channel}: {e}")
        raise

def center_all_servos(delay_between_servos=0.1):
    """Centers all servos to 90 degrees."""
    if kit is None or not servo_module_initialized_successfully:
        logger.warning("Cannot center servos: ServoKit not initialized.")
        return False # Indicate failure
    
    logger.info("Centering all servos to 90°...")
    success_count = 0
    for channel_num in range(16):
        try:
            kit.servo[channel_num].angle = 90
            logger.debug(f"Centered servo channel {channel_num}")
            success_count +=1
            if delay_between_servos > 0:
                time.sleep(delay_between_servos)
        except Exception as e:
            logger.warning(f"Could not center channel {channel_num}: {e}")
    logger.info(f"Centering attempt complete. {success_count}/16 servos centered.")
    return success_count == 16


# --- Main section for direct script execution (testing) ---
if __name__ == '__main__':
    logger.info("------------------------------------")
    logger.info("Running testservo.py directly for testing...")
    if kit is None or not servo_module_initialized_successfully:
        logger.critical("ServoKit not initialized. Cannot run tests. Exiting.")
    else:
        logger.info("ServoKit appears to be initialized.")
        
        # Example Usage:
        test_channel = 0 # Choose a channel to test
        logger.info(f"Testing servo on channel {test_channel}")

        try:
            logger.info("1. Setting to 0 degrees...")
            set_servo_angle(test_channel, 0)
            time.sleep(1)

            logger.info("2. Setting to 90 degrees...")
            set_servo_angle(test_channel, 90)
            time.sleep(1)

            logger.info("4. Performing basic sweep...")
            sweep_channel_basic(test_channel)
            time.sleep(1)

            logger.info("5. Performing smooth sweep...")
            sweep_channel_smooth(test_channel)
            time.sleep(1)
            
            logger.info(f"Test sequence for channel {test_channel} complete. Servo left at 90°.")

            # Optional: Test centering all servos
            # logger.info("6. Centering all servos...")
            # center_all_servos()

        except ValueError as ve:
            logger.error(f"Value Error during test: {ve}")
        except RuntimeError as rte:
            logger.error(f"Runtime Error during test: {rte}")
        except Exception as ex:
            logger.error(f"An unexpected error occurred during test: {ex}")
        finally:
            logger.info("Test script finished.")
    logger.info("------------------------------------")
