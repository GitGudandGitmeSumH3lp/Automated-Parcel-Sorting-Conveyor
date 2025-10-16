# mock_testservo.py

import time
import logging
import sys # Import sys to check the platform

# Configure logging for the mock module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Mock Servo Functions ---

# Simulate ServoKit initialization
# In a real scenario, this would initialize the PCA9685
logger.info("Mock Servo: Initializing simulated PCA9685...")
# No actual hardware initialization needed here
logger.info("Mock Servo: Simulated PCA9685 initialized.")

# Simulate setting pulse width range
def setup_channels_pulse_range():
    """Simulate setting up channels with pulse range"""
    logger.info("Mock Servo: Simulating setting pulse width range for all channels.")
    # No actual hardware setup needed
    time.sleep(0.1) # Simulate a small delay
    logger.info("Mock Servo: Simulated pulse width range set.")

# Simulate centering all servos
def center_all_servos():
     """Simulate centering all servos to 90 degrees"""
     logger.info("Mock Servo: Simulating centering all servos...")
     # No actual hardware movement
     time.sleep(0.5) # Simulate a small delay
     logger.info("Mock Servo: Simulated all servos centered.")

# Simulate setting a specific servo angle
def set_servo_angle(channel, angle):
    """
    Simulates setting a specific servo channel to a specific angle.
    Args:
        channel (int): The servo channel number (0-15).
        angle (int): The desired angle (0-180).
    """
    if not (0 <= channel <= 15):
        logger.warning(f"Mock Servo: Received invalid channel {channel}")
        raise ValueError("Channel must be between 0 and 15")
    if not (0 <= angle <= 180):
        logger.warning(f"Mock Servo: Received invalid angle {angle}")
        raise ValueError("Angle must be between 0 and 180")

    logger.info(f"Mock Servo: Simulating setting servo channel {channel} to {angle}°")
    # No actual hardware interaction
    time.sleep(0.05) # Simulate a small delay for movement


# Simulate a basic sweep
def sweep_channel_basic(channel):
    """Simulate a basic 0-90-180-90 sweep on a single channel."""
    if not (0 <= channel <= 15):
        logger.warning(f"Mock Servo: Received invalid channel {channel} for basic sweep")
        raise ValueError("Channel must be between 0 and 15")

    logger.info(f"Mock Servo: Simulating basic sweep on channel {channel}")
    # Simulate the steps
    time.sleep(0.2)
    logger.info(f"Mock Servo: Channel {channel} -> 0 degrees")
    time.sleep(0.2)
    logger.info(f"Mock Servo: Channel {channel} -> 90 degrees")
    time.sleep(0.2)
    logger.info(f"Mock Servo: Channel {channel} -> 180 degrees")
    time.sleep(0.2)
    logger.info(f"Mock Servo: Channel {channel} -> 90 degrees")
    time.sleep(0.2)
    logger.info(f"Mock Servo: Basic sweep complete for channel {channel}")


# Simulate a smooth sweep
def sweep_channel_smooth(channel):
    """Simulate a smooth sweep on a single channel."""
    if not (0 <= channel <= 15):
        logger.warning(f"Mock Servo: Received invalid channel {channel} for smooth sweep")
        raise ValueError("Channel must be between 0 and 15")

    logger.info(f"Mock Servo: Simulating smooth sweep on channel {channel}")
    # Simulate the steps
    for angle in range(0, 181, 10): # Simulate larger steps for quicker simulation
        # logger.info(f"Mock Servo: Channel {channel} -> {angle} degrees") # Too verbose
        time.sleep(0.01)
    for angle in range(180, -1, -10):
        # logger.info(f"Mock Servo: Channel {channel} -> {angle} degrees") # Too verbose
        time.sleep(0.01)
    logger.info(f"Mock Servo: Channel {channel} -> 90 degrees")
    time.sleep(0.1)
    logger.info(f"Mock Servo: Smooth sweep complete for channel {channel}")


# Simulate testing all channels
def test_all_channels():
    """Simulate a basic sweep on all 16 channels."""
    logger.info("Mock Servo: Simulating testing all channels...")
    # Simulate testing each channel
    for channel in range(16):
        logger.info(f"Mock Servo: Simulating test on channel {channel}...")
        time.sleep(0.1) # Simulate time per channel
    logger.info("Mock Servo: All channels test complete.")


# Call setup functions on import if needed, similar to real module
setup_channels_pulse_range()
# center_all_servos() # You might call this on mock startup too if desired
