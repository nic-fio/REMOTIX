import math, struct, wave
w = wave.open("/tmp/tono.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(44100)
w.writeframes(b"".join(struct.pack("<hh", v, v) for v in
    (int(3000 * math.sin(2 * math.pi * 440 * i / 44100)) for i in range(88200))))
w.close()
