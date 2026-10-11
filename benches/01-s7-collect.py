#!/usr/bin/env python3
"""01-s7-collect.py — serves the S7 page and RECORDS what it sees.

    python3 -u 01-s7-collect.py [port]        default: 8877

---------------------------------------------------------------------------
WHY IT EXISTS, GIVEN THAT B2 ALREADY HAS ONE

The same job as `01-b2-collect.py` — B0.4: *the expected is compared by the
bench, not by whoever reads* — but on another log and another port.  ⛔ B2's one
is not reused on purpose: `b2-outcomes.jsonl` is already shared between B2 and B11,
and finding R8.10 tells in full what a shared log costs — «the last line» stops
meaning «the line of this test».  S7 has its own file, and no other bench writes
in it.

⛔ AND HERE THE LOG IS THE ONLY EYE WE HAVE.  The GNOME session of this
   measurement has no screen: nobody can *look* at which way the page goes.
   What the page does not send did not happen for anybody.

---------------------------------------------------------------------------
⛔ THE DENOMINATOR, and in this bench it bites more than elsewhere

Every request is written on standard error (`LESSONS.md` §1.9, fourth rule).
«No outcome» has two opposite causes — the browser did not open the page, or it
opened it and the click did not arrive — and without the log of the requests
they look the same.  It is the same line that on 10 Aug 2026 said `pass` in
`01-b2-collect.py` and made two defects indistinguishable.
"""
import json
import sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE / "01-s7-outcomes.jsonl"


class Collector(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE), **kw)

    def do_POST(self):
        if self.path != "/outcome":
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n).decode("utf-8", "replace")
        try:
            data = json.loads(body)
        except Exception:
            data = {"grezzo": body}
        data["time"] = datetime.now().isoformat(timespec="milliseconds")
        with LOG.open("a") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"=== {data['time']}  {data.get('type')}  "
              f"deltaY={data.get('deltaY')}  scroll={data.get('scroll')}", flush=True)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def log_message(self, fmt, *a):
        sys.stderr.write("request: " + (fmt % a) + "\n")
        sys.stderr.flush()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8877
    print(f"== S7: page on http://127.0.0.1:{port}/01-s7-page.html")
    print(f"   the log accumulates in {LOG}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Collector).serve_forever()
