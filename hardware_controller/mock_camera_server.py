import socket
import struct

def main():
    UDP_IP = "0.0.0.0"
    UDP_PORT = 37260

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"Mock Camera Server listening on UDP {UDP_IP}:{UDP_PORT}...")
    print("Run your controller scripts to see the incoming hex payloads here.\n")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            print(f"Received {len(data)} bytes from {addr}: {data.hex()}")
            
            # Basic parsing of the SIYI frame to make testing easier
            if len(data) >= 10 and data[0:2] == b'fU': # 0x5566 Little Endian is b'fU'
                cmd_id = data[7]
                
                if cmd_id == 0x07:
                    yaw, pitch = struct.unpack("<bb", data[8:10])
                    print(f" -> Decoded: ROTATION SPEED (Yaw: {yaw}, Pitch: {pitch})")
                elif cmd_id == 0x05:
                    zoom = data[8]
                    action = "Stop" if zoom == 0 else "In" if zoom == 1 else "Out"
                    print(f" -> Decoded: ZOOM ({action})")
                elif cmd_id == 0x08:
                    print(f" -> Decoded: AUTO-CENTER")
            print("-" * 40)
            
    except KeyboardInterrupt:
        print("\nMock server stopped.")

if __name__ == "__main__":
    main()
