import time
import logging

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    from gpiozero import Button
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    logging.warning("Hardware libraries (adafruit-circuitpython-ads1x15 or gpiozero) not found. Running in mock mode.")

log = logging.getLogger("joystick-reader")

class JoystickReader:
    def __init__(self, button_pin=17, adc_i2c_address=0x48):
        """
        Initializes the I2C ADC (ADS1115) for X, Y, Z axes
        and a GPIO pin for the digital button.
        """
        self.mock_mode = not HARDWARE_AVAILABLE
        
        # Deadzone prevents drifting when joystick is centered.
        # Center voltage is usually around half of 3.3V (~1.65V)
        # Value ranges for 16-bit ADC: 0 to 65535, center ~32767
        self.deadzone_v = 0.2  # 0.2 Volts deadzone
        self.center_v = 2.5    # Assuming 5V joystick, center is 2.5V (Will be 1.65V if powered by 3.3V)
        self.max_v = 5.0       # Max voltage
        
        self.button_pressed_flag = False

        if not self.mock_mode:
            # Initialize I2C bus
            self.i2c = busio.I2C(board.SCL, board.SDA)
            
            # Initialize ADS1115 with 2/3 gain to safely read up to 6.144V
            # (Default gain=1 clips at 4.096V, which would break 5V joystick reading)
            self.ads = ADS.ADS1115(self.i2c, address=adc_i2c_address, gain=2/3)
            
            # Channels
            self.chan_x = AnalogIn(self.ads, ADS.P0) # Yaw
            self.chan_y = AnalogIn(self.ads, ADS.P1) # Pitch
            self.chan_z = AnalogIn(self.ads, ADS.P2) # Zoom (rotary)
            
            # Button with pull-up and debounce
            self.btn = Button(button_pin, pull_up=True, bounce_time=0.1)
            self.btn.when_pressed = self._button_callback
        else:
            log.warning("Mock mode enabled. Returning dummy values.")

    def _button_callback(self):
        self.button_pressed_flag = True

    def _apply_deadzone(self, voltage):
        """Applies deadzone and returns normalized value -1.0 to 1.0 based on Voltage"""
        diff = voltage - self.center_v
        if abs(diff) < self.deadzone_v:
            return 0.0
        
        # Normalize
        if diff > 0:
            return min(1.0, diff / (self.max_v - self.center_v))
        else:
            return max(-1.0, diff / self.center_v)

    def read_state(self):
        """
        Reads the hardware and returns a dictionary of normalized states:
        x: -1.0 to 1.0 (Yaw)
        y: -1.0 to 1.0 (Pitch)
        z: -1.0 to 1.0 (Zoom)
        button_clicked: True if clicked since last read, False otherwise.
        """
        if self.mock_mode:
            import math
            # Simulate joystick being moved around in a circle over time
            t = time.time()
            state = {
                "x": math.sin(t) * 0.5,
                "y": math.cos(t * 1.5) * 0.5,
                "z": 0.0,
                "button_clicked": (int(t) % 5 == 0) # Click every 5 seconds
            }
            return state

        vol_x = self.chan_x.voltage
        vol_y = self.chan_y.voltage
        vol_z = self.chan_z.voltage
        
        x_norm = self._apply_deadzone(vol_x)
        y_norm = self._apply_deadzone(vol_y)
        z_norm = self._apply_deadzone(vol_z)
        
        btn_clicked = self.button_pressed_flag
        if btn_clicked:
            self.button_pressed_flag = False # Reset flag after reading

        return {
            "x": x_norm,
            "y": y_norm,
            "z": z_norm,
            "button_clicked": btn_clicked
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    reader = JoystickReader()
    print("Reading joystick values. Press Ctrl+C to stop.")
    try:
        while True:
            state = reader.read_state()
            print(f"X: {state['x']:.2f} | Y: {state['y']:.2f} | Z: {state['z']:.2f} | Btn: {state['button_clicked']}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopped.")
