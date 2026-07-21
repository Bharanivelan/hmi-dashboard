from hardware_controller.siyi_protocol import SiyiCameraProtocol

# Official manual packet without STX and without CRC? Wait, CRC is calculated over the WHOLE packet except STX?
# Let's check how siyi_protocol does it.
cam = SiyiCameraProtocol()

# Manual packet: 55 66 01 02 00 00 00 07 64 64 3D CF
# Let's see what cam generates for yaw=100, pitch=100
packet = cam._build_packet(0x07, bytes([0x64, 0x64]))

print("Generated packet:", packet.hex(' '))
print("Expected packet : 55 66 01 02 00 00 00 07 64 64 3d cf")
