#!/usr/bin/python3
"""fan.py PREFIX OUTFILE: log (time, pid, comm, event, path) of every write under PREFIX, by fanotify on the mount."""
import ctypes, os, struct, sys, time, select
libc = ctypes.CDLL(None, use_errno=True)
FAN_CLASS_NOTIF, FAN_CLOEXEC = 0, 1
FAN_MODIFY, FAN_CLOSE_WRITE, FAN_OPEN = 0x2, 0x8, 0x20
FAN_MARK_ADD, FAN_MARK_MOUNT = 1, 0x10
fd = libc.fanotify_init(FAN_CLASS_NOTIF | FAN_CLOEXEC, os.O_RDONLY | os.O_LARGEFILE)
if fd < 0:
    print("fanotify_init failed errno", ctypes.get_errno(), flush=True); sys.exit(3)
r = libc.fanotify_mark(fd, FAN_MARK_ADD | FAN_MARK_MOUNT, ctypes.c_uint64(FAN_MODIFY | FAN_CLOSE_WRITE), -100, sys.argv[1].encode())
if r < 0:
    print("fanotify_mark failed errno", ctypes.get_errno(), flush=True); sys.exit(4)
prefix, out = sys.argv[1], open(sys.argv[2], "a")
print("ready", flush=True)
FMT = "IBBHQiI"; SZ = struct.calcsize(FMT)
seen = {}
while True:
    buf = os.read(fd, 65536); off = 0
    while off < len(buf):
        evlen, ver, res, mlen, mask, efd, pid = struct.unpack_from(FMT, buf, off)
        off += evlen
        if efd < 0: continue
        try: path = os.readlink("/proc/self/fd/%d" % efd)
        except OSError: path = "?"
        os.close(efd)
        if not path.startswith(prefix): continue
        try: comm = open("/proc/%d/comm" % pid).read().strip()
        except OSError: comm = seen.get(pid, "gone")
        seen[pid] = comm
        out.write("%.3f %d %s %s %s\n" % (time.time(), pid, comm, "W" if mask & FAN_CLOSE_WRITE else "m", path)); out.flush()
