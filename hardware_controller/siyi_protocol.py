import socket
import struct
import logging
import time

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("siyi-protocol")

class SiyiCameraProtocol:
    """
    Handles UDP communication with the SIYI ZR10 Gimbal Camera
    using the official SIYI SDK protocol.
    """
    SIYI_STX = 0x6655
    
    def __init__(self, camera_ip="127.0.0.1 ", camera_port=37260):
        self.camera_ip = camera_ip
        self.camera_port = camera_port
        self.seq = 0
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        log.info(f"Initialized SIYI Protocol -> {self.camera_ip}:{self.camera_port}")

    @staticmethod
    def _crc16(data: bytes) -> int:
        """SIYI uses CRC16-CCITT with poly 0x1021, init 0x0000, non-reflected."""
        crc = 0x0000
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF
        return crc

    def _build_packet(self, cmd_id: int, payload: bytes = b"") -> bytes:
        """
        Constructs the full binary frame:
        STX (2) + CTRL (1) + DATALEN (2) + SEQ (2) + CMD_ID (1) + DATA (N) + CRC16 (2)
        """
        data_len = len(payload)
        
        # Header: < (Little Endian)
        # H: STX (uint16)
        # B: CTRL (uint8)
        # H: DATA_LEN (uint16)
        # H: SEQ (uint16)
        # B: CMD_ID (uint8)
        header = struct.pack("<HBHHB",
            self.SIYI_STX,
            0x01,           # CTRL = 1 (Request)
            data_len,
            self.seq,
            cmd_id
        )
        
        body = header + payload
        crc = self._crc16(body)
        
        # Append CRC16 as uint16
        packet = body + struct.pack("<H", crc)
        return packet

    def _send(self, packet: bytes):
        # """Sends the constructed packet over UDP."""
        # try:
        #     self.sock.sendto(packet, (self.camera_ip, self.camera_port))
        #     # log.debug(f"Sent: {packet.hex()}")
        # except Exception as e:
        #     log.error(f"UDP send failed: {e}")
        print(f"Sending {len(packet)}bytes")
        print(packet.hex())
        self.sock.sendto(packet,(self.camera_ip,self.camera_port))

    # --- Camera Commands ---

    def send_rotation_speed(self, yaw_speed: int, pitch_speed: int):
        """
        Set gimbal rotation speed.
        CMD_ID: 0x07
        Yaw and Pitch speed ranges: -100 to 100
        """
        # Clamp values to -100 to 100
        yaw_speed = max(-100, min(100, int(yaw_speed)))
        pitch_speed = max(-100, min(100, int(pitch_speed)))
        
        # Payload: yaw_speed (int8), pitch_speed (int8)
        payload = struct.pack("<bb", yaw_speed, pitch_speed)
        packet = self._build_packet(0x07, payload)
        self._send(packet)

    # --- Requested Convenience API ---
    def rotate_left(self, speed: int):
        self.send_rotation_speed(-speed, 0)

    def rotate_right(self, speed: int):
        self.send_rotation_speed(speed, 0)

    def rotate_up(self, speed: int):
        self.send_rotation_speed(0, speed)

    def rotate_down(self, speed: int):
        self.send_rotation_speed(0, -speed)

    def stop(self):
        self.send_rotation_speed(0, 0)

    def send_zoom(self, direction: int):
        """
        Control Manual Zoom.
        CMD_ID: 0x05
        direction: 1 (Zoom In), -1 (Zoom Out), 0 (Stop)
        """
        if direction > 0:
            val = 0x01  # Zoom In
        elif direction < 0:
            val = 0xFF  # Zoom Out
        else:
            val = 0x00  # Stop
            
        payload = struct.pack("<B", val)
        packet = self._build_packet(0x05, payload)
        self._send(packet)

    def zoom_in(self):
        self.send_zoom(1)

    def zoom_out(self):
        self.send_zoom(-1)

    def center(self):
        """
        Auto-Center the Gimbal.
        CMD_ID: 0x08
        """
        payload = struct.pack("<B", 0x01)
        packet = self._build_packet(0x08, payload)
        self._send(packet)
        log.info("Sent Auto-Center command")

    def send_center(self):
        """Compatibility wrapper used by the HMI controller."""
        self.center()

    def send_absolute_zoom(self, integer_part: int, fractional_part: int):
        """
        Set absolute zoom level (e.g. 1x).
        CMD_ID: 0x0F
        Data length: 3 bytes (uint16_t int, uint8_t frac)
        """
        payload = struct.pack("<HB", int(integer_part), int(fractional_part))
        packet = self._build_packet(0x0F, payload)
        self._send(packet)
        log.info(f"Sent Absolute Zoom: {integer_part}.{fractional_part}x")

    def absolute_angle(self, yaw: float, pitch: float):
        """
        Set gimbal absolute angle.
        CMD_ID: 0x0E
        Expects integer values in tenths of a degree? 
        The official manual example sends 55 66 01 04 00 00 00 0E 00 00 FF A6 3B 11
        Data: 00 00 (Yaw=0) FF A6 (Wait: A6FF is -23040? Actually it's just raw bytes.
        We will pass exactly the signed 16-bit integers provided.)
        """
        # SIYI uses int16 for Yaw and Pitch. 
        # Typically 1 unit = 0.1 degrees. So -90 degrees = -900 = 0xFC7C.
        # If the manual payload is 00 00 FF A6, and FF A6 = -90 in some formats? 
        # Actually struct.pack("<h", val) takes a standard signed 16-bit int.
        yaw_int = int(yaw * 10)
        pitch_int = int(pitch * 10)
        payload = struct.pack("<hh", yaw_int, pitch_int)
        packet = self._build_packet(0x0E, payload)
        self._send(packet)

if __name__ == "__main__":
    # Quick offline test to print hex strings
    cam = SiyiCameraProtocol()
    
    print("Testing packet generation...")
    # Generate a center packet and print hex
    center_pkt = cam._build_packet(0x08, struct.pack("<B", 0x01))
    print(f"Center Packet: {center_pkt.hex()}")
    
    # Generate a rotation packet
    rot_pkt = cam._build_packet(0x07, struct.pack("<bb", 50, -50))
    print(f"Rotation Packet (50, -50): {rot_pkt.hex()}")
