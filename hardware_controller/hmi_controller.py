#!/usr/bin/env python3
import time
import logging
from joystick_reader import JoystickReader
from siyi_protocol import SiyiCameraProtocol

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
log = logging.getLogger("hmi-controller")

def main():
    log.info("Starting HMI Hardware Controller...")
    
    # Initialize Joystick Reader
    joystick = JoystickReader()
    
    # Initialize SIYI Camera Protocol
    camera = SiyiCameraProtocol(camera_ip="192.168.1.20", camera_port=37260)
    
    # State tracking to avoid spamming the same command
    last_yaw_speed = 0
    last_pitch_speed = 0
    last_zoom_state = 0
    
    POLL_RATE_HZ = 50
    poll_interval = 1.0 / POLL_RATE_HZ

    log.info(f"Controller loop running at {POLL_RATE_HZ}Hz. Press Ctrl+C to stop.")

    try:
        while True:
            loop_start = time.time()
            
            # Read hardware state
            state = joystick.read_state()
            
            # 1. Handle Button (Auto-Center)
            if state["button_clicked"]:
                log.info("Button Clicked -> Sending Auto-Center Command")
                camera.send_center()
            
            # 2. Handle Rotation (X, Y mapped to Yaw, Pitch)
            # Map normalized -1.0..1.0 to -100..100
            yaw_speed = int(state["x"] * 100)
            pitch_speed = int(state["y"] * 100)
            
            # Send rotation if it changed or if it's non-zero
            # (Continuous sending is sometimes needed by gimbal, but sending on change reduces network load)
            if (yaw_speed != last_yaw_speed) or (pitch_speed != last_pitch_speed) or (yaw_speed != 0 or pitch_speed != 0):
                camera.send_rotation_speed(yaw_speed, pitch_speed)
                last_yaw_speed = yaw_speed
                last_pitch_speed = pitch_speed

            # 3. Handle Zoom (Z mapped to Zoom In/Out)
            z_val = state["z"]
            zoom_cmd = 0
            if z_val > 0.5:
                zoom_cmd = 1   # Zoom In
            elif z_val < -0.5:
                zoom_cmd = -1  # Zoom Out
            
            if zoom_cmd != last_zoom_state:
                if zoom_cmd == 1:
                    log.info("Zoom In")
                elif zoom_cmd == -1:
                    log.info("Zoom Out")
                else:
                    log.info("Zoom Stop")
                camera.send_zoom(zoom_cmd)
                last_zoom_state = zoom_cmd
            
            # Sleep to maintain poll rate
            elapsed = time.time() - loop_start
            sleep_time = max(0, poll_interval - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        log.info("HMI Hardware Controller stopped by user.")
    except Exception as e:
        log.error(f"Controller encountered an error: {e}")

if __name__ == "__main__":
    main()
