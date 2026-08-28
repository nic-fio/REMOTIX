import struct
d = open("/tmp/dal-server.bmp", "rb").read()
if len(d) < 54 or d[:2] != b"BM":
    print("NO")
else:
    off = struct.unpack("<I", d[10:14])[0]
    larg = struct.unpack("<i", d[18:22])[0]
    alt = struct.unpack("<i", d[22:26])[0]
    p = d[off:off + 3]
    print("SI %d %d %d %d %d" % (larg, alt, p[0], p[1], p[2]))
