
# servo_test_pca9685.py

import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

# Initialize I2C bus
i2c = busio.I2C(SCL, SDA)

# Initialize PCA9685
pca = PCA9685(i2c)
pca.frequency = 50  # Typical servo frequency

# Create 16 servo objects (one for each channel)
servos = [servo.Servo(pca.channels[i]) for i in range(16)]

# Define movement function
def move_all_servos():
    for i, s in enumerate(servos):
        print(f"Moving servo on channel {i}")
        s.angle = 0    # Move to 0 degrees
        time.sleep(1.5)  # Wait for full rotation
        s.angle = 180  # Move to 180 degrees
        time.sleep(1.5)  # Wait for full rotation
        s.angle = 90   # Return to center
        time.sleep(0.5)

try:
    while True:
        move_all_servos()
        print("Cycle complete. Waiting 5 seconds before next test...")
        time.sleep(5)

except KeyboardInterrupt:
    print("Stopping test...")
    # Deactivate servos (optional: set all angles to None)
    for s in servos:
        s.angle = None
    pca.deinit()
# servo_test_pca9685.py

import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

# Initialize I2C bus
i2c = busio.I2C(SCL, SDA)

# Initialize PCA9685
pca = PCA9685(i2c)
pca.frequency = 50  # Typical servo frequency

# Create 16 servo objects (one for each channel)
servos = [servo.Servo(pca.channels[i]) for i in range(16)]

# Define movement function
def move_all_servos():
    for i, s in enumerate(servos):
        print(f"Moving servo on channel {i}")
        s.angle = 0    # Move to 0 degrees
        time.sleep(1.5)  # Wait for full rotation
        s.angle = 180  # Move to 180 degrees
        time.sleep(1.5)  # Wait for full rotation
        s.angle = 90   # Return to center
        time.sleep(0.5)

try:
    while True:
        move_all_servos()
        print("Cycle complete. Waiting 5 seconds before next test...")
        time.sleep(5)

except KeyboardInterrupt:
    print("Stopping test...")
    # Deactivate servos (optional: set all angles to None)
    for s in servos:
        s.angle = None
    pca.deinit()
