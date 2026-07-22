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
    def __init__(self, adc_i2c_address=0x48):
        """
        Initializes the I2C ADC (ADS1115) for Pan and Tilt axes
        and GPIO pins for the 4 digital buttons.
        """
        self.mock_mode = not HARDWARE_AVAILABLE
        
        # Deadzone prevents drifting when joystick is centered.
        # Center voltage is usually around half of 3.3V (~1.65V)
        # Value ranges for 16-bit ADC: 0 to 65535, center ~32767
        self.deadzone_v = 0.2  # 0.2 Volts deadzone
        self.center_v = 2.5    # Assuming 5V joystick, center is 2.5V (Will be 1.65V if powered by 3.3V)
        self.max_v = 5.0       # Max voltage

        if not self.mock_mode:
            # Initialize I2C bus
            self.i2c = busio.I2C(board.SCL, board.SDA)
            
            # Initialize ADS1115 with 2/3 gain to safely read up to 6.144V
            self.ads = ADS.ADS1115(self.i2c, address=adc_i2c_address, gain=2/3)
            
            # Channels (Using integers instead of ADS.P2 to avoid Adafruit library AttributeError)
            self.chan_pan = AnalogIn(self.ads, 2)  # Pan (Yaw) on A2
            self.chan_tilt = AnalogIn(self.ads, 3) # Tilt (Pitch) on A3
            
            # Buttons
            self.btn_center = Button(20, pull_up=True, bounce_time=0.1)
            self.btn_zoom_in = Button(10, pull_up=True, bounce_time=0.1)
            self.btn_zoom_out = Button(11, pull_up=True, bounce_time=0.1)
            self.btn_home = Button(9, pull_up=True, bounce_time=0.1)
        else:
            log.warning("Mock mode enabled. Returning dummy values.")

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
        pan: -1.0 to 1.0
        tilt: -1.0 to 1.0
        btn_center: True/False
        btn_zoom_in: True/False
        btn_zoom_out: True/False
        btn_home: True/False
        """
        if self.mock_mode:
            import math
            t = time.time()
            return {
                "pan": math.sin(t) * 0.5,
                "tilt": math.cos(t * 1.5) * 0.5,
                "btn_center": (int(t) % 5 == 0),
                "btn_zoom_in": False,
                "btn_zoom_out": False,
                "btn_home": False
            }

        vol_pan = self.chan_pan.voltage
        vol_tilt = self.chan_tilt.voltage
        
        return {
            "pan": self._apply_deadzone(vol_pan),
            "tilt": self._apply_deadzone(vol_tilt),
            "btn_center": self.btn_center.is_pressed,
            "btn_zoom_in": self.btn_zoom_in.is_pressed,
            "btn_zoom_out": self.btn_zoom_out.is_pressed,
            "btn_home": self.btn_home.is_pressed
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
