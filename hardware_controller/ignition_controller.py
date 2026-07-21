import time
import os
import logging
from gpiozero import Button

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("ignition")

# TODO: Update this PIN to match the actual hardware wiring!
IGNITION_PIN = 27 

class IgnitionController:
    def __init__(self, pin=IGNITION_PIN):
        # We use pull_up=True, meaning the circuit is HIGH by default.
        # When the physical key switch is turned, it should short the pin to Ground (LOW).
        self.key_switch = Button(pin, pull_up=True, bounce_time=0.1)
        
        # Register event callbacks
        self.key_switch.when_pressed = self.ignition_on
        self.key_switch.when_released = self.ignition_off
        
        log.info(f"Ignition Controller started on GPIO {pin}")
        
        # Run an initial check to set the display state based on the physical key position at boot
        if self.key_switch.is_pressed:
            self.ignition_on()
        else:
            self.ignition_off()

    def ignition_on(self):
        log.info("Key turned ON -> Waking up display.")
        # Wake up the physical HDMI display
        os.system("vcgencmd display_power 1")

    def ignition_off(self):
        log.info("Key turned OFF -> Putting display to sleep.")
        # Turn off the physical HDMI display to save power
        os.system("vcgencmd display_power 0")
        
        # We can also kill chromium and restart it to ignition.html so it's ready for next time,
        # but leaving it on the dashboard is fine too, as waking the screen up is instantaneous.
        # For true reset, uncomment the below to force restart Chromium to the boot animation:
        # os.system("killall chromium-browser")
        # os.system("chromium-browser --kiosk http://localhost:8080/ignition.html &")

if __name__ == "__main__":
    try:
        controller = IgnitionController()
        # Keep the script running forever
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Ignition controller stopped.")
