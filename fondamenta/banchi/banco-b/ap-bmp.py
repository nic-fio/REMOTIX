import struct, sys
d = open(sys.argv[1], "rb").read()
if len(d) < 54 or d[:2] != b"BM":
    print("NO %d" % len(d))
else:
    print("SI %d %d %d"
          % (struct.unpack("<i", d[18:22])[0], struct.unpack("<i", d[22:26])[0],
             struct.unpack("<H", d[28:30])[0]))
