import time
from hardware_controller.siyi_protocol import SiyiCameraProtocol

print("=========================================")
print("   SIYI CAMERA HARDWARE API TEST SUITE   ")
print("=========================================")

# Connect to the real camera
cam = SiyiCameraProtocol(camera_ip="192.168.1.20", camera_port=37260)

print("\n[1/5] Centering camera...")
cam.center()
time.sleep(3)

print("[2/5] Rotating LEFT at 30% speed...")
cam.rotate_left(30)
time.sleep(2)
cam.stop()
time.sleep(1)

print("[3/5] Rotating RIGHT at 50% speed...")
cam.rotate_right(50)
time.sleep(2)
cam.stop()
time.sleep(1)

print("[4/5] Moving to ABSOLUTE ANGLE (Yaw: 0, Pitch: -45.0)...")
# Sending Pitch -45.0 degrees
cam.absolute_angle(0.0, -45.0)
time.sleep(3)

print("[5/5] Re-centering...")
cam.center()
time.sleep(2)

print("\n✅ Hardware Test Sequence Complete!")
