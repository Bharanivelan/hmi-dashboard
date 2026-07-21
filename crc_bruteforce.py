def crc16(data: bytes, poly: int, init: int, ref_in: bool, ref_out: bool, xor_out: int) -> int:
    crc = init
    for byte in data:
        if ref_in:
            byte = int('{:08b}'.format(byte)[::-1], 2)
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFFFF
    
    if ref_out:
        crc = int('{:016b}'.format(crc)[::-1], 2)
    return crc ^ xor_out

# The target CRC is 3D CF (so 0xCF3D or 0x3DCF)
payload_without_stx = bytes([0x01, 0x02, 0x00, 0x00, 0x00, 0x07, 0x64, 0x64])
payload_with_stx = bytes([0x55, 0x66, 0x01, 0x02, 0x00, 0x00, 0x00, 0x07, 0x64, 0x64])

targets = [0xCF3D, 0x3DCF]

polys = [0x1021, 0x8005, 0x1021, 0x8408, 0xA001]
inits = [0x0000, 0xFFFF, 0x1D0F]

found = False
for p in polys:
    for i in inits:
        for ref_in in [True, False]:
            for ref_out in [True, False]:
                for xor_out in [0x0000, 0xFFFF]:
                    for data, name in [(payload_without_stx, "without STX"), (payload_with_stx, "with STX")]:
                        res = crc16(data, p, i, ref_in, ref_out, xor_out)
                        if res in targets:
                            print(f"FOUND! Data: {name}, Poly: {hex(p)}, Init: {hex(i)}, RefIn: {ref_in}, RefOut: {ref_out}, XorOut: {hex(xor_out)}")
                            print(f"Result CRC: {hex(res)}")
                            found = True

if not found:
    print("Not found with standard configs.")

# SIYI custom SDK CRC function from C++ translated to Python?
def crc16_cal(ptr: bytes, len_bytes: int, crc_init: int) -> int:
    crc = crc_init
    for byte in ptr:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

print(f"Custom Modbus/A001 without STX: {hex(crc16_cal(payload_without_stx, len(payload_without_stx), 0x0000))}")
print(f"Custom Modbus/A001 with STX: {hex(crc16_cal(payload_with_stx, len(payload_with_stx), 0x0000))}")
print(f"Custom Modbus/A001 without STX (FFFF): {hex(crc16_cal(payload_without_stx, len(payload_without_stx), 0xFFFF))}")
print(f"Custom Modbus/A001 with STX (FFFF): {hex(crc16_cal(payload_with_stx, len(payload_with_stx), 0xFFFF))}")

