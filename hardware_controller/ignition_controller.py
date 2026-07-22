import time
import os
import logging
from gpiozero import Button

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("ignition")

# TODO: Update this PIN to match the actual hardware wiring!
IGNITION_PIN = 4 

class IgnitionController:
    def __init__(self, pin=IGNITION_PIN):
        # We use pull_up=False, meaning the circuit is LOW (0) by default.
        # When the physical key switch is turned, it connects to 3.3V and goes HIGH (1).
        self.key_switch = Button(pin, pull_up=False, bounce_time=0.1)
        
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
        # Universal Display WAKEUP (Shotgun approach for all display types)
        # 1. Try standard X11 DPMS (Works for most GUI displays)
        os.system("xset -display :0 dpms force on > /dev/null 2>&1")
        # 2. Try Broadcom HDMI power
        os.system("vcgencmd display_power 1 > /dev/null 2>&1")
        # 3. Try Official Raspberry Pi DSI Touchscreen Backlight
        os.system("echo 0 | sudo tee /sys/class/backlight/rpi_backlight/bl_power > /dev/null 2>&1")
        
        # Launch Chromium with full desktop environment variables (Handles both X11 and Wayland)
        home = os.environ.get("HOME", "/home/suresh")
        cmd = (
            f"export DISPLAY=:0; "
            f"export WAYLAND_DISPLAY=wayland-1; "
            f"export XDG_RUNTIME_DIR=/run/user/1000; "
            f"export XAUTHORITY={home}/.Xauthority; "
            f"chromium --kiosk --password-store=basic file://{home}/hmi-dashboard/ignition.html > /dev/null 2>&1 &"
        )
        os.system(cmd)

    def ignition_off(self):
        log.info("Key turned OFF -> Putting display to sleep.")
        # Kill current Chromium
        os.system("pkill -o chromium")
        os.system("pkill -o chromium-browser")
        
        # Since AMC is 3.3V, backlight won't turn off. 
        # We launch a pitch-black webpage to simulate a powered-off screen!
        home = os.environ.get("HOME", "/home/suresh")
        cmd = (
            f"export DISPLAY=:0; "
            f"export WAYLAND_DISPLAY=wayland-1; "
            f"export XDG_RUNTIME_DIR=/run/user/1000; "
            f"export XAUTHORITY={home}/.Xauthority; "
            f"chromium --kiosk --password-store=basic file://{home}/hmi-dashboard/black.html > /dev/null 2>&1 &"
        )
        os.system(cmd)
        
        # Attempt hardware sleep anyway
        os.system("DISPLAY=:0 xset dpms force off > /dev/null 2>&1")
        os.system("echo 1 | sudo tee /sys/class/backlight/rpi_backlight/bl_power > /dev/null 2>&1")

if __name__ == "__main__":
    try:
        controller = IgnitionController()
        # Keep the script running forever
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Ignition controller stopped.")
