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
    
    # Acceleration State
    current_yaw = 0.0
    current_pitch = 0.0
    ACCEL_STEP = 4.0 # Ramps up by 4 units per 20ms tick (reaches 100% in 0.5 seconds)
    
    last_zoom_state = 0
    last_btn_center = False
    last_btn_home = False
    
    POLL_RATE_HZ = 50
    poll_interval = 1.0 / POLL_RATE_HZ

    log.info(f"Controller loop running at {POLL_RATE_HZ}Hz. Press Ctrl+C to stop.")

    try:
        while True:
            loop_start = time.time()
            
            # Read hardware state
            state = joystick.read_state()
            
            # 1. Handle Center Button (One-shot on press)
            if state["btn_center"] and not last_btn_center:
                log.info("Center Button Pressed -> Sending Auto-Center Command")
                camera.send_center()
            last_btn_center = state["btn_center"]
            
            # 2. Handle Home Button (One-shot on press)
            if state["btn_home"] and not last_btn_home:
                log.info("Home Button Pressed -> Resetting Zoom to 1x")
                camera.send_absolute_zoom(1, 0)
            last_btn_home = state["btn_home"]

            # 3. Handle Zoom Buttons (Continuous while pressed)
            zoom_cmd = 0
            if state["btn_zoom_in"]:
                zoom_cmd = 1
            elif state["btn_zoom_out"]:
                zoom_cmd = -1
            
            if zoom_cmd != last_zoom_state:
                if zoom_cmd == 1:
                    log.info("Zoom In")
                elif zoom_cmd == -1:
                    log.info("Zoom Out")
                else:
                    log.info("Zoom Stop")
                camera.send_zoom(zoom_cmd)
                last_zoom_state = zoom_cmd
                
            # 4. Handle Rotation (Pan mapped to Yaw, Tilt mapped to Pitch)
            # Map normalized -1.0..1.0 to -100..100
            target_yaw = state["pan"] * 100.0
            target_pitch = state["tilt"] * 100.0
            
            # YAW ACCELERATION
            if target_yaw == 0:
                current_yaw = 0.0 # Instant stop when released
            elif current_yaw < target_yaw:
                current_yaw = min(current_yaw + ACCEL_STEP, target_yaw)
            elif current_yaw > target_yaw:
                current_yaw = max(current_yaw - ACCEL_STEP, target_yaw)
                
            # PITCH ACCELERATION
            if target_pitch == 0:
                current_pitch = 0.0 # Instant stop when released
            elif current_pitch < target_pitch:
                current_pitch = min(current_pitch + ACCEL_STEP, target_pitch)
            elif current_pitch > target_pitch:
                current_pitch = max(current_pitch - ACCEL_STEP, target_pitch)
            
            yaw_speed = int(current_yaw)
            pitch_speed = int(current_pitch)
            
            # Send rotation if it changed or if it's non-zero
            if (yaw_speed != last_yaw_speed) or (pitch_speed != last_pitch_speed) or (yaw_speed != 0 or pitch_speed != 0):
                camera.send_rotation_speed(yaw_speed, pitch_speed)
                last_yaw_speed = yaw_speed
                last_pitch_speed = pitch_speed
            
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
