#!/usr/bin/env python3
"""
gimbal_server.py  —  Aerostat HMI Gimbal Control Bridge
=========================================================
Runs on the Raspberry Pi (ground station).

What it does
------------
1.  Starts a WebSocket server on ws://localhost:8765
2.  The HMI dashboard (browser) connects and sends JSON commands:
        { "cmd": "gimbal", "pitch": -10.5, "yaw": 45.0 }
        { "cmd": "home" }
        { "cmd": "zoom", "level": 2 }
3.  This server translates those commands into the protocol your
    team uses to talk to the CEZR10 camera.

⚠️  IMPORTANT — SET YOUR PROTOCOL BELOW:
    Search for "PROTOCOL ADAPTER" and fill in your camera's
    actual command format (SIYI SDK / MAVLink / HTTP REST / custom).

Dependencies
------------
    pip3 install websockets

Usage
-----
    python3 gimbal_server.py
    # Runs on port 8765. Keep it running alongside go2rtc.
"""

import asyncio
import json
import logging
import socket
import struct
import websockets

# ── Configuration ──────────────────────────────────────────────────────────────
WS_PORT      = 8765          # WebSocket port the browser connects to
CAMERA_IP    = "192.168.1.20"   # ← Replace with actual camera IP (e.g. 192.168.144.25)
CAMERA_PORT  = 37260         # ← SIYI SDK default UDP port (change if different)
LOG_LEVEL    = logging.INFO

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=LOG_LEVEL,
    format="[%(asctime)s] %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("gimbal-bridge")


# ══════════════════════════════════════════════════════════════════════════════
#  PROTOCOL ADAPTER
#  This is the only section you need to edit when you know your camera's
#  exact control protocol.
# ══════════════════════════════════════════════════════════════════════════════

class CameraProtocol:
    """
    Translates abstract gimbal commands into camera-specific bytes/HTTP calls.

    Currently implemented: SIYI SDK (UDP) — most common for ZR10-type cameras.
    Uncomment/add the MAVLink or HTTP sections if your team uses a different protocol.
    """

    def __init__(self, camera_ip: str, camera_port: int):
        self.camera_ip   = camera_ip
        self.camera_port = camera_port

        # UDP socket for SIYI SDK
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setblocking(False)
        log.info(f"Protocol adapter ready → UDP {camera_ip}:{camera_port}")

    # ── SIYI SDK helpers ────────────────────────────────────────────────────
    # Reference: https://github.com/mzahana/siyi_sdk (open-source implementation)

    SIYI_STX   = 0x5566          # Start-of-frame marker
    SEQ        = 0               # Command sequence counter

    @classmethod
    def _checksum(cls, data: bytes) -> int:
        """Simple CRC-16 used by SIYI protocol."""
        crc = 0
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0x8408
                else:
                    crc >>= 1
        return crc & 0xFFFF

    def _build_siyi_packet(self, cmd_id: int, payload: bytes) -> bytes:
        CameraProtocol.SEQ = (CameraProtocol.SEQ + 1) & 0xFFFF
        data_len = len(payload)
        # Header: STX(2) + CTRL(1) + DATA_LEN(2) + SEQ(2) + CMD_ID(1)
        header = struct.pack("<HBHHB",
            self.SIYI_STX,
            0x01,           # CTRL = request
            data_len,
            CameraProtocol.SEQ,
            cmd_id,
        )
        body    = header + payload
        crc     = self._checksum(body)
        return body + struct.pack("<H", crc)

    def _send_udp(self, packet: bytes):
        try:
            self._sock.sendto(packet, (self.camera_ip, self.camera_port))
            log.debug(f"UDP → {self.camera_ip}:{self.camera_port}  {packet.hex()}")
        except Exception as e:
            log.warning(f"UDP send failed: {e}")

    # ── Public command methods ───────────────────────────────────────────────

    def set_gimbal_angles(self, pitch_deg: float, yaw_deg: float):
        """
        Send absolute gimbal angle command.
        SIYI CMD_ID 0x0E = Set Gimbal Attitude (absolute)
        Pitch range: -90 to +25 degrees
        Yaw range:   -135 to +135 degrees
        """
        # Convert degrees × 10 → int16
        pitch_i = int(pitch_deg * 10)
        yaw_i   = int(yaw_deg   * 10)
        payload = struct.pack("<hh", yaw_i, pitch_i)   # SIYI order: yaw first
        packet  = self._build_siyi_packet(0x0E, payload)
        self._send_udp(packet)
        log.info(f"Gimbal → pitch={pitch_deg:.1f}°  yaw={yaw_deg:.1f}°")

    def center_gimbal(self):
        """Return gimbal to home/center position (pitch=0, yaw=0)."""
        self.set_gimbal_angles(0.0, 0.0)
        log.info("Gimbal → CENTER")

    def set_zoom(self, level: int):
        """
        Absolute zoom.  level: 1–10 for ZR10 (1 = 1× wide, 10 = 10× tele)
        SIYI CMD_ID 0x0F = Absolute Zoom
        """
        payload = struct.pack("<B", max(1, min(10, level)))
        packet  = self._build_siyi_packet(0x0F, payload)
        self._send_udp(packet)
        log.info(f"Zoom → {level}×")

    def take_photo(self):
        """Trigger a still photo capture on the camera."""
        packet = self._build_siyi_packet(0x0C, b"\x01")
        self._send_udp(packet)
        log.info("Camera → SNAPSHOT")

    def toggle_record(self):
        """Start/stop video recording on the camera's SD card."""
        packet = self._build_siyi_packet(0x0D, b"\x02")
        self._send_udp(packet)
        log.info("Camera → RECORD TOGGLE")


# ══════════════════════════════════════════════════════════════════════════════
#  If your team uses HTTP REST commands instead of SIYI UDP, replace the
#  CameraProtocol methods above with HTTP calls, e.g.:
#
#  import httpx  (pip3 install httpx)
#  async def set_gimbal_angles(self, pitch, yaw):
#      await httpx.get(f"http://{self.camera_ip}/api/gimbal?pitch={pitch}&yaw={yaw}")
#
#  Or for MAVLink (pip3 install pymavlink):
#  from pymavlink import mavutil
#  self.mav = mavutil.mavlink_connection('udpout:CAMERA_IP:14550')
#  def set_gimbal_angles(self, pitch, yaw):
#      self.mav.mav.command_long_send(...)
# ══════════════════════════════════════════════════════════════════════════════


# ── WebSocket Server ───────────────────────────────────────────────────────────

camera = CameraProtocol(CAMERA_IP, CAMERA_PORT)
connected_clients: set = set()


async def handle_client(websocket):
    """Handles one browser connection."""
    connected_clients.add(websocket)
    remote = websocket.remote_address
    log.info(f"Client connected: {remote}")

    try:
        async for raw in websocket:
            try:
                msg = json.loads(raw)
                cmd = msg.get("cmd", "")

                # ── Route commands ────────────────────────────────────────
                if cmd == "gimbal":
                    pitch = float(msg.get("pitch", 0.0))
                    yaw   = float(msg.get("yaw",   0.0))
                    camera.set_gimbal_angles(pitch, yaw)

                elif cmd == "home":
                    camera.center_gimbal()

                elif cmd == "zoom":
                    camera.set_zoom(int(msg.get("level", 1)))

                elif cmd == "snapshot":
                    camera.take_photo()

                elif cmd == "record":
                    camera.toggle_record()

                else:
                    log.warning(f"Unknown command: {cmd}")

                # Acknowledge back to browser
                await websocket.send(json.dumps({"ok": True, "cmd": cmd}))

            except (json.JSONDecodeError, ValueError) as e:
                log.warning(f"Bad message from {remote}: {e}")
                await websocket.send(json.dumps({"ok": False, "error": str(e)}))

    except websockets.exceptions.ConnectionClosedOK:
        log.info(f"Client disconnected: {remote}")
    except Exception as e:
        log.error(f"Client error ({remote}): {e}")
    finally:
        connected_clients.discard(websocket)


async def main():
    log.info(f"Gimbal bridge starting on ws://0.0.0.0:{WS_PORT}")
    async with websockets.serve(handle_client, "0.0.0.0", WS_PORT):
        log.info("Gimbal bridge running. Press Ctrl+C to stop.")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutdown requested.")
