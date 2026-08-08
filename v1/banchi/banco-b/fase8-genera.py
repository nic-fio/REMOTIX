import struct, zlib
larg, alt = 8, 8
righe = b"".join(
    b"\x00" + bytes([(x * 30) % 256, (y * 30) % 256, 128, 255][k]
                    for x in range(larg) for k in range(4))
    for y in range(alt))
def pezzo(tipo, dati):
    return struct.pack(">I", len(dati)) + tipo + dati + struct.pack(">I", zlib.crc32(tipo + dati))
png = (b"\x89PNG\r\n\x1a\n"
       + pezzo(b"IHDR", struct.pack(">IIBBBBB", larg, alt, 8, 6, 0, 0, 0))
       + pezzo(b"IDAT", zlib.compress(righe))
       + pezzo(b"IEND", b""))
open("/tmp/prova.png", "wb").write(png)
