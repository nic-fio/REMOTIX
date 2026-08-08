import gi
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf
try:
    p = GdkPixbuf.Pixbuf.new_from_file("/tmp/dal-client.png")
    px = p.get_pixels()
    print("SI %d %d %d %d %d" % (p.get_width(), p.get_height(), px[0], px[1], px[2]))
except Exception:
    print("NO")
