
import time
from adafruit_servokit import ServoKit
import board
import busio

# Initialize I2C bus (use default Pi pins - GPIO 2 (SDA) and GPIO 3 (SCL))
i2c = busio.I2C(board.SCL, board.SDA)

# Create ServoKit instance with 16 channels (PCA9685 has 16 channels)
print("Initializing PCA9685...")
kit = ServoKit(channels=16)

# MG995 servo parameters - you may need to adjust these based on your specific servos
MIN_PULSE = 500   # Min pulse length in microseconds (1ms)
MAX_PULSE = 2500  # Max pulse length in microseconds (2ms)

def setup_channels():
    """Set up all channels with proper pulse range for MG995"""
    for channel in range(16):
        kit.servo[channel].set_pulse_width_range(MIN_PULSE, MAX_PULSE)
        # Center all servos initially
        kit.servo[channel].angle = 0
    
    print("All channels initialized and centered at 90 degrees")
    time.sleep(2)

#FOR TESTSERVO.HTML
def set_servo_angle(channel,angle):
    if not( 0 <= channel <= 15):
        raise ValueError("Channel must be between 0 and 15")
    if not ( 0 <=angle <= 180): # Assume 0-1800 degree range
        raise ValueError("Angle must be between 0 and 180")
    print(f"Setting channel {channel} to {angle} degrees")

    actual_channel = int(channel)
    actual_angle = int(angle)

    print(f"Setting Channel {actual_channel} to {actual_angle} degrees")
    kit.servo[actual_channel].angle = actual_angle
    time.sleep(0.05)
    print(f"Channel {actual_channel} set to {actual_angle} degrees")


def sweep_channel(channel):
    """Sweep a single channel through its range of motion"""
    print(f"Testing channel {channel}...")
    
    # Move to 0 degrees
    kit.servo[channel].angle = 0
    print(f"Channel {channel}: 0 degrees")
    time.sleep(1)
    
    # Move to 90 degrees
    kit.servo[channel].angle = 70
    print(f"Channel {channel}: 90 degrees")
    time.sleep(5)
    
    # Move to 180 degrees
    #kit.servo[channel].angle = 180
    #print(f"Channel {channel}: 180 degrees")
    #time.sleep(1)
    
    # Return to 90 degrees (neutral position)
    kit.servo[channel].angle = 0
   
    print(f"Channel {channel}: Back to 90 degrees")
    time.sleep(1)
    
    print(f"Channel {channel} test complete")

def smooth_sweep_channel(channel):
    """Perform a smooth sweep across the servo's range"""
    print(f"Performing smooth sweep on channel {channel}...")
    
    # Sweep from 0 to 180 degrees
    for angle in range(0, 181, 5):  # Step by 5 degrees
        kit.servo[channel].angle = angle
        print(f"Channel {channel}: {angle} degrees")
        time.sleep(0.1)  # Small delay for smooth movement
    
    # Sweep from 180 back to 0 degrees
    #for angle in range(180, -1, -5):  # Step by 5 degrees
        #kit.servo[channel].angle = angle
        #print(f"Channel {channel}: {angle} degrees")
        #time.sleep(0.1)  # Small delay for smooth movement
    
    # Return to neutral position
    kit.servo[channel].angle = 0
    print(f"Channel {channel}: Back to neutral position (90 degrees)")
    time.sleep(0.5)
    
    print(f"Smooth sweep test for channel {channel} complete")

def test_specific_channel():
    """Test a specific channel based on user input"""
    try:
        channel = int(input("Enter channel number to test (0-15): "))
        if 0 <= channel <= 15:
            test_type = input("Enter test type ('sweep' for smooth sweep, any key for basic test): ").lower()
            if test_type == 'sweep':
                smooth_sweep_channel(channel)
            else:
                sweep_channel(channel)
        else:
            print("Channel must be between 0 and 15")
    except ValueError:
        print("Please enter a valid number")

def test_all_channels():
    """Test all 16 channels one by one"""
    print("Testing all channels...")
    for channel in range(16):
        sweep_channel(channel)
        time.sleep(1)  # Pause between channels
    print("All channels tested!")

def main():
    """Main program"""
    print("MG995 Servo Test with PCA9685 on Raspberry Pi 5")
    setup_channels()
    
    while True:
        print("\nMenu:")
        print("1. Test a specific channel")
        print("2. Test all channels")
        print("3. Perform smooth sweep on a specific channel")
        print("4. Exit")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == '1':
            test_specific_channel()
        elif choice == '2':
            test_all_channels()
        elif choice == '3':
            try:
                channel = int(input("Enter channel number for smooth sweep (0-15): "))
                if 0 <= channel <= 15:
                    smooth_sweep_channel(channel)
                else:
                    print("Channel must be between 0 and 15")
            except ValueError:
                print("Please enter a valid number")
        elif choice == '4':
            print("Centering all servos before exit...")
            for channel in range(16):
                kit.servo[channel].angle = 70
            time.sleep(1)
            print("Exiting program")
            break
        else:
            print("Invalid choice. Please select 1-4")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
        # Center all servos before exiting
        for channel in range(16):
            kit.servo[channel].angle = 0
        print("All servos centered")
