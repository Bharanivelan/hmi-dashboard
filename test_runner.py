import subprocess
import time

print("Starting Mock Camera Server...")
server = subprocess.Popen(["python", "-u", "hardware_controller/mock_camera_server.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

time.sleep(1)

print("Starting HMI Controller in Mock Mode...")
controller = subprocess.Popen(["python", "-u", "hardware_controller/hmi_controller.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

print("Letting them run for 3 seconds...")
time.sleep(3)

print("Terminating processes...")
controller.terminate()
server.terminate()

server_out, _ = server.communicate(timeout=2)
controller_out, _ = controller.communicate(timeout=2)

print("\n--- CONTROLLER LOG ---")
print(controller_out)

print("\n--- MOCK SERVER RECEIVED ---")
print(server_out)
