import time
import threading
from siyi_protocol import SiyiCameraProtocol

def main():
    print("==================================================")
    print("      MANUAL CAMERA MOCK CONTROLLER (LOCAL)       ")
    print("==================================================")
    
    # Point this directly to the REAL camera to test physical movement
    camera = SiyiCameraProtocol(camera_ip="192.168.1.20", camera_port=37260)
    
    print("\nConnected to REAL SIYI Camera (192.168.1.20:37260)")
    print("Commands Available:")
    print("  r <yaw> <pitch>  : Send Rotation Speed (-100 to 100)")
    print("                     Example: r 50 -20")
    print("  z <dir>          : Send Zoom (1=In, -1=Out, 0=Stop)")
    print("                     Example: z 1")
    print("  c                : Auto-Center Gimbal")
    print("  q                : Quit")
    print("==================================================\n")

    while True:
        try:
            user_input = input("Enter command: ").strip().lower()
            if not user_input:
                continue
                
            parts = user_input.split()
            cmd = parts[0]
            
            if cmd == 'q':
                print("Exiting manual mock.")
                break
                
            elif cmd == 'c':
                print("-> Sending AUTO-CENTER command")
                camera.send_center()
                
            elif cmd == 'r':
                if len(parts) != 3:
                    print("Error: Format is 'r <yaw> <pitch>' (e.g. 'r 50 -50')")
                    continue
                yaw = int(parts[1])
                pitch = int(parts[2])
                print(f"-> Sending ROTATION: Yaw={yaw}, Pitch={pitch}")
                camera.send_rotation_speed(yaw, pitch)
                
            elif cmd == 'z':
                if len(parts) != 2:
                    print("Error: Format is 'z <direction>' (1, -1, or 0)")
                    continue
                z_val = int(parts[1])
                print(f"-> Sending ZOOM: {z_val}")
                camera.send_zoom(z_val)
                
            else:
                print("Unknown command.")
                
        except ValueError:
            print("Error: Invalid numbers provided.")
        except KeyboardInterrupt:
            print("\nExiting.")
            break

if __name__ == "__main__":
    main()
