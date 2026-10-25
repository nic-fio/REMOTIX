#!/usr/bin/env node
// ===========================================================================
// 22-page-decoder-sim.js — after a VideoDecoder error, does the picture come back?
//
//   node benches/22-page-decoder-sim.js src/page.html      (V=1 for the Viewer's lines)
//
// ⛔ The bug (fixed in b1dea604, RELEASE-CHECKLIST-1.5 B1.7): after a VideoDecoder error
//    the decoder is "closed", but deliver() called it ready (`!!this.dec`) and, the size
//    being unchanged, never rebuilt it.  The keyframe asked for after the error went to
//    decode() on the dead decoder, threw, opened another gap — the picture stayed FROZEN
//    for the rest of the session.
//
// What it does: OFFLINE, no browser.  It cuts the real `class Viewer` (and the helpers
// `difference`, `after`) out of the page, runs it in node with a FAKE VideoDecoder that
// behaves like the WebCodecs one (error ⇒ "closed"; decode()/configure() on a closed one
// throws; configure() can be made to throw once), and feeds it frames of the SAME size:
//
//   A  error, then the requested keyframe (same size)   ⇒ decoding resumes
//   B  error, the rebuild's configure() throws once,
//      then another keyframe                            ⇒ that keyframe rebuilds, resumes
//   C  error, then only deltas                          ⇒ no reconfigure, no new decoder
//                                                         (only a keyframe can rebuild)
//
// ⭐ And since 15 Oct 2026 (proposal DECISIONS §11.36 D, branch
//   `proposal/firefox-worker-default`) the WORKER route, the same way — its shell
//   (`WORKER_SHELL`) and the fall back (`worker_fall_back` and its helpers) cut out of
//   the page, the decoder now giving frames back two behind (picture age 32 ms):
//
//   D  the worker shell: the first keyframe is said once, the picture age
//      crosses to the main thread in the mirror (`fresh.age`), the
//      `#video_fault=blind` switch reads the key and delivers nothing
//   E  the fall back on the main thread: the canvas is replaced WITH its
//      listeners, the redirected methods are gone, a keyframe is asked at once,
//      the next frames paint on this side, the page's log says so ONCE, the route says
//      «main» — and a second fall back does nothing
//   F  a fall back in the middle of a canvas change (after CANVAS(FITTED), and
//      with a FIT_CANVAS unanswered): no PROTOCOL_ERROR — the main instance kept
//      the §6.2 tolerance through the shadow calls
//   G  the failure rule: stray exceptions keep the worker, WORKER_FAILS within
//      WORKER_FAILS_S fall back; an error before «ready» falls back at once; no
//      fall back on a stream count; nothing painted WORKER_PAINT_S after the key
//      ⇒ fall back; painted ⇒ none; close() disarms; an old session's key is
//      ignored
//   H  a worker that cannot be built: null, main route, a fresh canvas
//   I  (second review) the PACE cap reaches this side; sign-out on the worker route
//      (a transferred canvas refuses a resize) completes; a throwing canvas swap
//      leaves no redirection behind; a stale mirror is dropped; a throwing shadow
//      copy does not stop the worker's call.  G6–G8 and D3: the three clocks
//      (key from the END of the first video stream, silent from the first stream),
//      no arming after close(), video_seen once per session
//
// EXIT: 0 all pass · 1 a scenario failed (the bug) · 2 blind: node missing (the caller's
//       business), the page unreadable, `class Viewer` not found, or the healthy start
//       does not decode (the simulation no longer fits the page — fix THIS file).
// `[M]` 15 Oct 2026: pass on b1dea604, fail (A, B) on b1dea604^.
//   D–H: pass on the proposal branch; on `main` (no worker default) they are BLIND
//   (exit 2).  Mutants (15 Oct 2026): without the shadow E/F fail, a fall back on one
//   stray error fails G1, a 60-stream rule G3, no disarm in close G5, no session
//   tag G6, no catch at start H, no listener replay / age tap / immediate key E/D1.
// ===========================================================================
"use strict";
const fs = require("fs");

function blind(why) { console.log("BLIND: " + why); process.exit(2); }

const path = process.argv[2];
if (!path) blind("usage: node 22-page-decoder-sim.js <page.html>");
let src;
try { src = fs.readFileSync(path, "utf8"); } catch (e) { blind("cannot read " + path + ": " + e.message); }

function cut(start) {
  const a = src.indexOf(start);
  if (a < 0) return null;
  const b = src.indexOf("\n}\n", a);
  return b < 0 ? null : src.slice(a, b + 3);
}
const viewerSrc = cut("class Viewer {");
if (!viewerSrc) blind("`class Viewer {` not found in " + path);
const fnSrc = (name) => {
  const s = cut("function " + name + "(");
  if (!s) blind("`function " + name + "(` not found in " + path);
  return s.split("\n/*")[0];
};
const helpers = fnSrc("difference") + fnSrc("after");

// ── the fake decoder: the WebCodecs states that matter here
class FakeDecoder {
  constructor(cb) {
    this.cb = cb; this.state = "unconfigured"; this.decodeQueueSize = 0; this.decoded = 0;
    FakeDecoder.made.push(this);
  }
  configure() {
    if (this.state === "closed") throw new Error("InvalidStateError: configure on closed");
    if (FakeDecoder.configureFails > 0) { FakeDecoder.configureFails--; throw new TypeError("fake configure failure"); }
    this.state = "configured";
  }
  decode(chunk) {
    if (this.state !== "configured") throw new Error("InvalidStateError: decode on " + this.state);
    this.decoded++;
    if (FakeDecoder.emit && this.cb.output && chunk) {
      // frames come back `lag` behind: the picture age is lag × 16 ms
      (this.q = this.q || []).push(chunk.timestamp);
      while (this.q.length > FakeDecoder.lag) this.cb.output(fakeFrame(this.q.shift()));
    }
    if (FakeDecoder.failNext) {
      FakeDecoder.failNext = false; this.state = "closed";
      this.cb.error(new Error("EncodingError: fake"));
    }
  }
  close() { this.state = "closed"; }
  flush() { return Promise.resolve(); }
  reset() { if (this.state === "closed") throw new Error("InvalidStateError: reset on closed"); this.state = "unconfigured"; }
}

FakeDecoder.emit = false; FakeDecoder.lag = 2;
function fakeFrame(ts) {
  return { timestamp: ts, displayWidth: 1280, displayHeight: 720, codedWidth: 1280,
           codedHeight: 720, format: "I420", close() {} };
}
// a 2D context that accepts every call (the drawing itself is not under test here)
function fakeContext() {
  return new Proxy({}, { get: (t, k) => (k in t ? t[k] : () => ({})), set: (t, k, v) => { t[k] = v; return true; } });
}

const G = {
  VIA_MSE: false, CANVAS_GL: false, CANVAS_2D: true, DESYNCHRONIZED: false,
  ROUND_TRIP: { arrive() {} }, note: () => {}, CODEC_NAME: { 1: "H264", 2: "HEVC" },
  VideoDecoder: FakeDecoder, EncodedVideoChunk: class { constructor(o) { Object.assign(this, o); } },
};
let Viewer;
try {
  Viewer = new Function("g", Object.keys(G).map((k) => `const ${k} = g.${k};`).join("\n") + "\n"
    + helpers + viewerSrc + "\nreturn Viewer;")(G);
} catch (e) { blind("the cut Viewer does not compile: " + e); }

// one session: a Viewer at 1280x720 H.264, frames numbered in order
function session() {
  FakeDecoder.made = []; FakeDecoder.failNext = false; FakeDecoder.configureFails = 0;
  const v = new Viewer({ getContext() { return {}; } });
  const lines = [];
  v.on_line = (t) => lines.push(t);
  v.on_key = () => {};
  v.negotiate(1, 8, "avc1.640028", 1280, 720);
  v.pace_check = () => {};
  let n = 0;
  const frame = (key) => {
    n++;
    try {
      v.deliver({ type: key ? 0x0301 : 0x0302, codec: 1, number: n, width: 1280, height: 720,
                  instant: n * 16000, input: 0 }, new Uint8Array(10));
    } catch (e) { lines.push("THROW " + e); }
  };
  return { v, frame, lines };
}

const results = [];
function check(name, ok, facts) { results.push({ name, ok, facts }); }

function healthyStart(s) {
  s.frame(true); s.frame(false); s.frame(false);
  if (s.v.counts.delivered !== 3 || !s.v.dec || s.v.dec.state !== "configured")
    blind("the healthy start does not decode (delivered " + s.v.counts.delivered + ", decoder "
      + (s.v.dec && s.v.dec.state) + "): the simulation no longer fits the page\n" + s.lines.join("\n"));
}
function breakIt(s) {
  FakeDecoder.failNext = true; s.frame(false);           // the decoder errors -> "closed"
  for (let k = 0; k < 3; k++) s.frame(false);            // deltas while the gap is open
}
function resumed(s) {
  const before = s.v.counts.delivered;
  s.frame(true); for (let k = 0; k < 5; k++) s.frame(false);
  return { delivered_after_key: s.v.counts.delivered - before, dec_state: s.v.dec && s.v.dec.state,
           on_hold: s.v.on_hold, decoders: FakeDecoder.made.length,
           reconfigurations: s.v.counts.reconfigurations };
}

try {
  // A — error, then the requested keyframe at the same size
  {
    const s = session(); healthyStart(s); breakIt(s);
    const f = resumed(s);
    check("A error then same-size keyframe: decoding resumes",
      f.delivered_after_key === 6 && f.dec_state === "configured" && !f.on_hold, f);
    if (process.env.V) console.log(s.lines.join("\n"));
  }
  // B — the rebuild's configure() throws once; the next keyframe rebuilds
  {
    const s = session(); healthyStart(s); breakIt(s);
    FakeDecoder.configureFails = 1;
    s.frame(true); s.frame(false);
    const f = resumed(s);
    check("B configure() throws once: the next keyframe rebuilds",
      f.delivered_after_key === 6 && f.dec_state === "configured" && !f.on_hold, f);
    if (process.env.V) console.log(s.lines.join("\n"));
  }
  // C — after the error only deltas: no reconfigure, no new decoder
  {
    const s = session(); healthyStart(s);
    const rec0 = s.v.counts.reconfigurations, made0 = FakeDecoder.made.length;
    breakIt(s);
    for (let k = 0; k < 5; k++) s.frame(false);
    const f = { reconfigurations_delta: s.v.counts.reconfigurations - rec0,
                new_decoders: FakeDecoder.made.length - made0, dec_state: s.v.dec && s.v.dec.state };
    check("C delta after the error does not reconfigure",
      f.reconfigurations_delta === 0 && f.new_decoders === 0, f);
    if (process.env.V) console.log(s.lines.join("\n"));
  }
} catch (e) { blind("the simulation fell over: " + (e && e.stack || e)); }

// ── D and E: the worker route, cut out of the page the same way ──────────────
function cutShell() {
  const a = src.indexOf("const WORKER_SHELL = `");
  if (a < 0) return null;
  const b = src.indexOf("\n`;\n", a);
  if (b < 0) return null;
  try { return eval(src.slice(a + "const WORKER_SHELL = ".length, b + 2)); } catch (e) { return null; }
}
const shellSrc = cutShell();
function cutFn(name) {
  const s = cut("function " + name + "(");
  return s ? s.split("\n/*")[0] : null;
}
const fbNames = ["worker_fall_back", "track_canvas_listeners", "swap_viewer_canvas", "viewer_take_canvas",
                 "redirect_viewer_to_worker", "start_worker_wire", "start_video_worker",
                 "back_to_form"];
const fbSrc = fbNames.map(cutFn);
// `read_one_stream` goes into the worker as `worker_source()` puts it there (async)
const readOneSrc = (cut("async function read_one_stream(") || "").split("\n/*")[0];
const workerReady = shellSrc && shellSrc.indexOf("first_key") >= 0 && fbSrc.every(Boolean) && readOneSrc
  && /const WORKER_SHADOWED = \[/.test(src) && /\bWORKER_FAILS_S = \d+/.test(src);

// D — the worker shell, composed like `worker_source()` composes it
function workerScope(fault) {
  const posted = [], intervals = [];
  const self = { postMessage: (m) => posted.push(m) };
  const W = Object.assign({}, G, { VIDEO_FAULT: fault, CHANNEL: {}, REASON: {}, self,
    setInterval: (f) => { intervals.push(f); return intervals.length; } });
  delete W.ROUND_TRIP; delete W.note;           // the shell defines its own
  const body = Object.keys(W).map((k) => `const ${k} = g.${k};`).join("\n") + "\n"
    + helpers + shellSrc + "\n" + viewerSrc + "\n" + readOneSrc + "\nreturn { onmessage: self.onmessage, REMOTIX: () => self.REMOTIX };";
  const w = new Function("g", body)(W);
  const oc = { width: 16, height: 16, getContext: () => fakeContext() };
  w.onmessage({ data: { t: "turn_on", canvas: oc, dpr: 1, view: [1280, 720] } });
  const v = w.REMOTIX().viewer;
  w.onmessage({ data: { t: "call", method: "negotiate", args: [1, 8, "avc1.640028", 1280, 720] } });
  v.pace_check = () => {};
  let n = 0;
  const frame = (key) => { n++;
    try { v.deliver({ type: key ? 0x0301 : 0x0302, codec: 1, number: n, width: 1280, height: 720,
                      instant: n * 16000, input: 0 }, new Uint8Array(10)); }
    catch (e) { posted.push({ t: "THROW", e: "" + (e && e.stack || e) }); } };
  return { v, frame, posted, mirror: () => intervals.forEach((f) => f()) };
}

// E…H — the main thread's side, with a fake DOM, a fake clock and the real `Viewer`
class FakeCanvas extends EventTarget {
  // ⛔ like the browser: a canvas given to a worker refuses a new size (InvalidStateError)
  get width() { return this._w; }
  set width(x) { if (this.transferred) throw new Error("InvalidStateError: transferred canvas"); this._w = x; }
  get height() { return this._h; }
  set height(x) { if (this.transferred) throw new Error("InvalidStateError: transferred canvas"); this._h = x; }
  constructor() { super(); this.attrs = new Map(); this.style = {}; this._w = 16; this._h = 16;
                  this.ctx = null; this.transferred = false; }
  get attributes() { return Array.from(this.attrs, ([name, value]) => ({ name, value })); }
  setAttribute(k, v) { this.attrs.set(k, "" + v); }
  getContext() { if (this.transferred) throw new Error("InvalidStateError: transferred"); return (this.ctx = fakeContext()); }
  transferControlToOffscreen() { this.transferred = true; return {}; }
  getBoundingClientRect() { return { left: 0, top: 0, width: 1280, height: 720 }; }
  replaceWith(c) { FakeDOM.viewer = c; }
  focus() { FakeDOM.active = this; }
}
const FakeDOM = { viewer: null, active: null };
// the page's own numbers, read from it (a sim with its own copy would test the copy)
function pageConst(name) {
  const m = src.match(new RegExp("\\b" + name + " = (\\d+)"));
  return m ? +m[1] : null;
}
const PAGE_K = {};
for (const k of ["WORKER_PAINT_S", "WORKER_KEY_S", "WORKER_SILENT_S", "WORKER_FAILS", "WORKER_FAILS_S"])
  PAGE_K[k] = pageConst(k);
const shadowLine = (src.match(/const WORKER_SHADOWED = \[[^\]]*\];/) || [null])[0];

function mainScope(opts) {
  opts = opts || {};
  const notes = [];
  const clock = { t: 1000, timers: [] };
  const old = new FakeCanvas(); old.setAttribute("id", "viewer"); old.setAttribute("tabindex", "-1");
  old.transferred = !!opts.transferred;
  FakeDOM.viewer = old; FakeDOM.active = old;
  let M;
  M = Object.assign({}, G, PAGE_K, {
    $: (id) => (id === "viewer" ? FakeDOM.viewer : null),
    document: { createElement: () => new FakeCanvas(), get activeElement() { return FakeDOM.active; },
                body: { dataset: {} }, pointerLockElement: null, fullscreenElement: null },
    audio_stop: () => {}, logout_show: (yes) => { M.logout_shown = !!yes; }, logout_shown: true,
    window: { REMOTIX: { video: "the worker object" } },
    // the page's `note()`: a line in the page's log (since 8a46c9c9 nothing goes to the server)
    note: (l) => { notes.push(l); },
    view_size: () => [1280, 720], devicePixelRatio: 1,
    VIDEO_ROUTE: { chosen: "worker", fell_back: null },
    VIDEO_WORKER: true, start_worker: opts.start_worker || (() => { throw new Error("not in this scene"); }),
    SCENE: { on_painted() {} },
    performance: { now: () => clock.t },
    setTimeout: (f, ms) => { const h = { at: clock.t + ms, f }; clock.timers.push(h); return h; },
    clearTimeout: (h) => { clock.timers = clock.timers.filter((x) => x !== h); },
  });
  const body = Object.keys(M).map((k) => `const ${k} = g.${k};`).join("\n")
    + "\nlet VW = null;\nconst CANVAS_LISTENERS = [];\nlet logout_in_progress = true;\n" + shadowLine + "\n"
    + helpers + viewerSrc + "\n" + fbSrc.join("\n") + "\n"
    + "return { Viewer, worker_fall_back, track_canvas_listeners, redirect_viewer_to_worker,"
    + " start_worker_wire, start_video_worker, back_to_form, logoutFlag: () => logout_in_progress,"
    + " setVW: (x) => { VW = x; }, getVW: () => VW, setViewer: (x) => { viewer = x; } };";
  // `viewer` is a page global: declared here so the cut functions see the instance
  const sc = new Function("g", "let viewer = null;\n" + body)(M);
  const advance = (ms) => {
    const end = clock.t + ms;
    for (;;) {
      clock.timers.sort((x, y) => x.at - y.at);
      const h = clock.timers[0];
      if (!h || h.at > end) break;
      clock.timers.shift(); clock.t = h.at; h.f();
    }
    clock.t = end;
  };
  return { sc, M, notes, old, clock, advance };
}

// a page with the worker route on: the mirror, its wire to a fake worker, the redirections
function workerPage(opts) {
  const m = mainScope(Object.assign({ transferred: false }, opts));
  const v = new m.sc.Viewer(new FakeCanvas());          // the mirror, on a detached canvas
  m.sc.setViewer(v);
  v.pace_check = () => {};
  m.keysAsked = []; v.on_key = (u) => m.keysAsked.push(u);
  m.vlines = []; v.on_line = (t) => m.vlines.push(t);
  m.protocolErrors = []; v.on_protocol_error = (why) => m.protocolErrors.push(why);
  m.sc.track_canvas_listeners(m.old);
  m.toWorker = []; m.terminated = 0;
  const V = { ready: false, streams: 0,
              w: { postMessage: (x) => m.toWorker.push(x), terminate: () => m.terminated++ } };
  m.sc.start_worker_wire(V);
  m.sc.setVW(V);
  m.sc.redirect_viewer_to_worker();
  m.V = V; m.v = v;
  // a stopped worker hears nothing: after a fall back these are no-ops, not throws
  m.fromWorker = (x) => { if (V.w.onmessage) V.w.onmessage({ data: x }); };
  m.workerError = (x) => { if (V.w.onerror) V.w.onerror(x); };
  m.n = 0;
  m.frame = (key, w, h) => { m.n++;
    try { v.deliver({ type: key ? 0x0301 : 0x0302, codec: 1, number: m.n, width: w || 1280,
                      height: h || 720, instant: m.n * 16000, input: 0 }, new Uint8Array(10)); }
    catch (e) { m.protocolErrors.push("THROW " + e); } };
  // a session as `connect()` opens it: restart, negotiate, pace
  m.session = () => { v.restart(); v.negotiate(1, 8, "avc1.640028", 1280, 720); v.pace_enable(true); };
  // the mirror catches up with what the worker delivered (as the 100 ms mirror does)
  m.mirrored = (last) => { v.last_delivered = last; v.expected = last + 1; m.n = last; };
  return m;
}

if (!workerReady) {
  results.push({ name: "D-H worker route", ok: null,
    facts: "WORKER_SHELL with `first_key`, or " + fbNames.join("/") + ", not found in the page" });
} else try {
  // D1 — first key said once; the picture age crosses in the mirror
  {
    FakeDecoder.made = []; FakeDecoder.failNext = false; FakeDecoder.configureFails = 0;
    FakeDecoder.emit = true; FakeDecoder.lag = 2;
    const s = workerScope(null);
    s.frame(true); for (let k = 0; k < 9; k++) s.frame(false);
    s.mirror();
    const keys = s.posted.filter((m) => m.t === "first_key").length;
    const c = s.posted.filter((m) => m.t === "counts").pop() || {};
    const age = (c.fresh && c.fresh.age) || [];
    s.mirror();
    const c2 = s.posted.filter((m) => m.t === "counts").pop() || {};
    const f = { first_key_msgs: keys, painted: s.v.counts.painted, age_samples: age.length,
                age_values: Array.from(new Set(age)), second_mirror_age: ((c2.fresh || {}).age || []).length,
                queue_out: c.queue_out, throws: s.posted.filter((m) => m.t === "THROW").map((m) => m.e) };
    check("D1 worker: first keyframe said once, picture age crosses in the mirror (32 ms, no repeats)",
      keys === 1 && age.length === 8 && f.age_values.length === 1 && f.age_values[0] === 32
        && f.second_mirror_age === 0 && f.throws.length === 0, f);
  }
  // D2 — `#video_fault=blind`: the key is said, nothing is delivered
  {
    FakeDecoder.made = []; FakeDecoder.emit = true;
    const s = workerScope("blind");
    s.frame(true); for (let k = 0; k < 5; k++) s.frame(false);
    const f = { first_key_msgs: s.posted.filter((m) => m.t === "first_key").length,
                delivered: s.v.counts.delivered, painted: s.v.counts.painted };
    check("D2 worker video_fault=blind: keyframe said, nothing delivered or painted",
      f.first_key_msgs === 1 && f.delivered === 0 && f.painted === 0, f);
  }
  // D3 — the first VIDEO stream read to its end is said once per session, with the session
  {
    FakeDecoder.made = []; FakeDecoder.emit = false;
    const s = workerScope(null);
    s.v.stream_video(new Uint8Array(4), false); s.v.stream_video(new Uint8Array(4), false);
    const first = s.posted.filter((m) => m.t === "video_seen");
    s.v.restart(); s.v.negotiate(1, 8, "avc1.640028", 1280, 720);
    s.v.stream_video(new Uint8Array(4), false);
    s.mirror();
    const all = s.posted.filter((m) => m.t === "video_seen");
    const c = s.posted.filter((m) => m.t === "counts").pop() || {};
    const f = { first: first.map((m) => m.sess), all: all.map((m) => m.sess), mirror_sess: c.sess };
    check("D3 worker: video_seen once per session, tagged; the mirror carries the session",
      first.length === 1 && first[0].sess === 0 && all.length === 2 && all[1].sess === 1 && c.sess === 1, f);
  }
  // E — the fall back
  {
    FakeDecoder.made = []; FakeDecoder.failNext = false; FakeDecoder.configureFails = 0;
    FakeDecoder.emit = true;
    const m = workerPage();
    const v = m.v;
    let wheel = 0, removedCalled = 0;
    const onWheel = () => wheel++, gone = () => removedCalled++;
    m.old.addEventListener("wheel", onWheel, { passive: false });
    m.old.addEventListener("mousedown", gone);
    m.old.removeEventListener("mousedown", gone);
    m.fromWorker({ t: "ready" });
    m.session();
    m.mirrored(40);
    const first = m.sc.worker_fall_back("sim: painted nothing");
    const keysAtFallBack = m.keysAsked.length;   // asked AT the fall back, not at the next delta
    const second = m.sc.worker_fall_back("sim: again");
    const c = FakeDOM.viewer;
    c.dispatchEvent(new Event("wheel")); c.dispatchEvent(new Event("mousedown"));
    m.frame(true); for (let k = 0; k < 5; k++) m.frame(false);
    const f = { first, second, VW_after: m.sc.getVW(), new_canvas: c !== m.old,
                id: c.attrs.get("id"), tabindex: c.attrs.get("tabindex"), has_context: !!c.ctx,
                viewer_canvas_is_new: v.canvas === c, wheel_heard: wheel, removed_listener_heard: removedCalled,
                redirect_left: Object.keys(v).filter((k) => typeof v[k] === "function" && k in m.sc.Viewer.prototype),
                keys_asked: m.keysAsked, keys_at_fall_back: keysAtFallBack, painted: v.counts.painted,
                terminated: m.terminated, chosen: m.M.VIDEO_ROUTE.chosen, remotix_video: m.M.window.REMOTIX.video,
                fell_back: m.M.VIDEO_ROUTE.fell_back && m.M.VIDEO_ROUTE.fell_back.why,
                failed: m.M.VIDEO_ROUTE.fell_back && m.M.VIDEO_ROUTE.fell_back.failed,
                logged: m.notes.filter((l) => l.indexOf("FELL BACK") >= 0).length,
                route_line: m.vlines.some((l) => l.indexOf("after the fall back") >= 0),
                protocol_errors: m.protocolErrors };
    check("E fall back: new canvas with its listeners, prototype methods, keyframe asked at once, paints, once, said once",
      first === true && second === false && f.VW_after === null && f.new_canvas && f.id === "viewer"
        && f.tabindex === "-1" && f.has_context && f.viewer_canvas_is_new && wheel === 1
        && removedCalled === 0 && f.redirect_left.length === 0 && m.keysAsked.length === 1
        && keysAtFallBack === 1 && f.painted > 0 && f.terminated === 1 && f.logged === 1 && !f.failed
        && f.chosen === "main" && f.remotix_video === null && f.route_line && f.protocol_errors.length === 0, f);
    if (process.env.V) console.log(m.notes.concat(m.vlines).join("\n"));
  }
  // F — a fall back in the MIDDLE of a canvas change must not close the session (review 1)
  for (const when of ["after CANVAS(FITTED)", "FIT_CANVAS unanswered"]) {
    FakeDecoder.made = []; FakeDecoder.emit = true;
    const m = workerPage();
    const v = m.v;
    m.fromWorker({ t: "ready" });
    m.session();
    m.mirrored(40);
    v.fit_canvas_requested();
    if (when === "after CANVAS(FITTED)") v.canvas_adapted(1600, 900);
    m.sc.worker_fall_back("sim: mid canvas change");
    // the frames already on the wire: old-size deltas, then the new size
    m.frame(false, 1280, 720); m.frame(false, 1280, 720);
    m.frame(false, 1600, 900);
    if (when === "FIT_CANVAS unanswered") v.canvas_adapted(1600, 900);   // the CANVAS arrives now
    m.frame(true, 1600, 900); for (let k = 0; k < 4; k++) m.frame(false, 1600, 900);
    const f = { protocol_errors: m.protocolErrors, canvas: [v.canvas_w, v.canvas_h],
                painted: v.counts.painted, closed: v.is_closed };
    check("F fall back " + when + ": no PROTOCOL_ERROR, the new size paints",
      f.protocol_errors.length === 0 && f.canvas[0] === 1600 && f.painted > 0, f);
  }
  // G — the failure rule (review 3) and the watchdog (review 2, 5)
  {
    const P = PAGE_K;
    // G1 — one stray exception after "ready" does not move the route; WORKER_FAILS in the window does
    {
      const m = workerPage(); m.fromWorker({ t: "ready" }); m.session();
      m.workerError({ message: "stray" });
      m.fromWorker({ t: "broke", why: "one stream" });
      const after_two = m.sc.getVW() === m.V;
      m.advance((P.WORKER_FAILS_S + 1) * 1000);           // the window passes: they are forgotten
      m.workerError({ message: "stray again" });
      const after_window = m.sc.getVW() === m.V;
      for (let k = 1; k < P.WORKER_FAILS; k++) m.fromWorker({ t: "broke", why: "repeat " + k });
      const f = { after_two_still_worker: after_two, after_window_still_worker: after_window,
                  fell: m.M.VIDEO_ROUTE.fell_back && m.M.VIDEO_ROUTE.fell_back.why };
      check("G1 failures: " + (P.WORKER_FAILS - 1) + " stray ones keep the worker, " + P.WORKER_FAILS
            + " within " + P.WORKER_FAILS_S + " s fall back",
        f.after_two_still_worker && f.after_window_still_worker && /worker failures/.test(f.fell || ""), f);
    }
    // G2 — an error before "ready": the worker is dead, fall back at once
    {
      const m = workerPage();
      m.workerError({ message: "SyntaxError in the composed source" });
      const f = { fell: m.M.VIDEO_ROUTE.fell_back && m.M.VIDEO_ROUTE.fell_back.why };
      check("G2 error before ready: fall back at once", /could not start/.test(f.fell || ""), f);
    }
    // G3 — the 60-stream check is gone: 120 streams in 2 s, nothing painted yet, no fall back
    {
      const m = workerPage(); m.fromWorker({ t: "ready" }); m.session();
      for (let k = 0; k < 120; k++) { m.V.send_stream({}); m.advance(16); }
      const early = m.sc.getVW() === m.V;
      m.fromWorker({ t: "first_key", number: 1, sess: m.V.sess });
      m.advance(P.WORKER_PAINT_S * 1000 - 100);
      const before_clock = m.sc.getVW() === m.V;
      m.advance(200);
      const f = { still_worker_after_120_streams: early, still_worker_before_clock: before_clock,
                  fell: m.M.VIDEO_ROUTE.fell_back && m.M.VIDEO_ROUTE.fell_back.why };
      check("G3 no fall back on stream count; nothing painted " + P.WORKER_PAINT_S + " s after the key ⇒ fall back",
        early && before_clock && /painted nothing/.test(f.fell || ""), f);
    }
    // G4 — painted in time: no fall back
    {
      const m = workerPage(); m.fromWorker({ t: "ready" }); m.session();
      m.V.send_stream({}); m.fromWorker({ t: "first_key", number: 1, sess: m.V.sess });
      m.v.counts.painted = 3;                               // what the mirror brings
      m.advance(30000);
      check("G4 the worker paints: no fall back", m.sc.getVW() === m.V && !m.M.VIDEO_ROUTE.fell_back,
        { fell: m.M.VIDEO_ROUTE.fell_back });
    }
    // G5 — `close()` disarms the watchdog
    {
      const m = workerPage(); m.fromWorker({ t: "ready" }); m.session();
      m.V.send_stream({}); m.fromWorker({ t: "first_key", number: 1, sess: m.V.sess });
      m.v.close();
      m.advance(30000);
      check("G5 close() disarms the watchdog", m.sc.getVW() === m.V && !m.M.VIDEO_ROUTE.fell_back,
        { fell: m.M.VIDEO_ROUTE.fell_back, timers: m.clock.timers.length });
    }
    // G6 — an OLD session's keyframe does not start the new session's clock
    {
      const m = workerPage(); m.fromWorker({ t: "ready" }); m.session();
      const oldSess = m.V.sess;
      m.session();                                          // a new session
      m.V.send_stream({});
      m.fromWorker({ t: "first_key", number: 1, sess: oldSess });   // crossed the restart
      m.fromWorker({ t: "video_seen", sess: oldSess });
      const f = { key_t: m.V.key_t, video_t: m.V.video_t };
      m.advance(P.WORKER_SILENT_S * 1000 + 100);
      f.fell = m.M.VIDEO_ROUTE.fell_back && m.M.VIDEO_ROUTE.fell_back.why;
      check("G6 a stale first_key/video_seen is ignored: the silent clock fires",
        f.key_t === null && f.video_t === null && /no video stream/.test(f.fell || ""), f);
    }
    // G7 — a slow 4K keyframe: streams for 20 s before the first video stream ends ⇒ no
    //      fall back at WORKER_KEY_S from the first stream; then no key ⇒ fall back
    {
      const m = workerPage(); m.fromWorker({ t: "ready" }); m.session();
      m.V.send_stream({});                                  // a clipboard stream, or the key opening
      m.advance(20000);
      const slow_ok = m.sc.getVW() === m.V;
      m.fromWorker({ t: "video_seen", sess: m.V.sess });
      m.advance(P.WORKER_KEY_S * 1000 + 100);
      const f = { still_worker_at_20s: slow_ok,
                  fell: m.M.VIDEO_ROUTE.fell_back && m.M.VIDEO_ROUTE.fell_back.why };
      check("G7 the no-keyframe clock runs from the END of the first video stream",
        slow_ok && /no keyframe/.test(f.fell || ""), f);
    }
    // G8 — a closed session is never armed (second review 4)
    {
      const m = workerPage(); m.fromWorker({ t: "ready" }); m.session();
      m.v.close();
      m.V.send_stream({});                                  // a stream after the FAREWELL
      const armed = m.V.armed;
      m.advance(60000);
      check("G8 a stream after close() does not arm the watchdog",
        armed === false && !m.M.VIDEO_ROUTE.fell_back, { armed, fell: m.M.VIDEO_ROUTE.fell_back });
    }
  }
  // I — the second review (15 Oct 2026)
  {
    // I1 — the PACE cap the worker set is this side's too: after a fall back calm can lift it
    {
      const m = workerPage(); m.fromWorker({ t: "ready" }); m.session();
      let told = null; m.v.on_pace = (x) => { told = x; };
      m.fromWorker({ t: "pace", fps: 20 });
      const f = { told, pace_fps: m.v.pace && m.v.pace.fps, calm: m.v.pace && m.v.pace.calm };
      check("I1 the worker's PACE cap reaches this side's pace", told === 20 && f.pace_fps === 20 && f.calm === 0, f);
    }
    // I2 — signing out on the worker route: the canvas is the worker's, the return completes
    {
      const m = workerPage({ transferred: false });
      m.fromWorker({ t: "ready" }); m.session();
      let threw = null;
      try { m.sc.back_to_form(); } catch (e) { threw = "" + e; }
      const f = { threw, logout_in_progress: m.sc.logoutFlag(), dialog_shown: m.M.logout_shown,
                  blank_sent: m.toWorker.some((x) => x.t === "blank"), closed: m.v.is_closed };
      check("I2 back_to_form() on the worker route: no throw, flag/dialog reset, worker blanks",
        !threw && f.logout_in_progress === false && f.dialog_shown === false && f.blank_sent && f.closed, f);
    }
    // I3 — the canvas swap throws: the redirections are already gone, the session's calls work
    {
      const m = workerPage(); m.fromWorker({ t: "ready" }); m.session();
      m.old.replaceWith = () => { throw new Error("sim: replaceWith refused"); };
      m.sc.worker_fall_back("sim: swap will throw");
      let threw = null;
      try { m.v.restart(); m.v.negotiate(1, 8, "avc1.640028", 1280, 720); m.v.fit_canvas_requested(); }
      catch (e) { threw = "" + e; }
      const f = { threw, failed: m.M.VIDEO_ROUTE.fell_back && m.M.VIDEO_ROUTE.fell_back.failed };
      check("I3 the swap throws: the session's calls still work (prototype)", !threw && !!f.failed, f);
    }
    // I4 — a mirror of an older session does not put its counts on the new one
    {
      const m = workerPage(); m.fromWorker({ t: "ready" }); m.session();
      const oldSess = m.V.sess;
      m.session();
      m.fromWorker({ t: "counts", sess: oldSess, counts: { painted: 5 }, state: {} });
      const stale = m.v.counts.painted;
      m.fromWorker({ t: "counts", sess: m.V.sess, counts: { painted: 2 }, state: {} });
      const f = { after_stale: stale, after_current: m.v.counts.painted };
      check("I4 a stale mirror is dropped, the current one applied", stale === 0 && f.after_current === 2, f);
    }
    // I5 — this side's copy throws: the worker's call still goes out, the caller does not see it
    {
      const m = workerPage(); m.fromWorker({ t: "ready" }); m.session();
      const proto = m.sc.Viewer.prototype, keep = proto.canvas_refused;
      proto.canvas_refused = function () { throw new Error("sim: the copy throws"); };
      let threw = null;
      try { m.v.canvas_refused(); } catch (e) { threw = "" + e; }
      proto.canvas_refused = keep;
      const f = { threw, sent: m.toWorker.some((x) => x.t === "call" && x.method === "canvas_refused") };
      check("I5 the shadow copy throws: the worker still gets the call", !threw && f.sent, f);
    }
  }
  // H — a worker that cannot be built does not take the page down (review 4)
  {
    FakeDecoder.made = []; FakeDecoder.emit = true;
    const m = mainScope({ transferred: false, start_worker: () => { FakeDOM.viewer.transferred = true;
                                                                     throw new Error("sim: Blob refused"); } });
    const v = new m.sc.Viewer(new FakeCanvas());
    m.sc.setViewer(v);
    let r, threw = null;
    try { r = m.sc.start_video_worker(); } catch (e) { threw = "" + e; }
    const c = FakeDOM.viewer;
    const f = { returned: r, threw, chosen: m.M.VIDEO_ROUTE.chosen,
                fell: m.M.VIDEO_ROUTE.fell_back && m.M.VIDEO_ROUTE.fell_back.why,
                new_canvas: c !== m.old, viewer_on_it: v.canvas === c, has_context: !!c.ctx };
    check("H start_worker throws: null, main route, a fresh canvas with a context",
      r === null && !threw && f.chosen === "main" && /could not be built/.test(f.fell || "")
        && f.new_canvas && f.viewer_on_it && f.has_context, f);
  }
} catch (e) { blind("the worker simulation fell over: " + (e && e.stack || e)); }
FakeDecoder.emit = false;

let bad = 0;
let blindOnes = 0;
for (const r of results) {
  if (r.ok === null) { blindOnes++; console.log("BLIND " + r.name + "  " + JSON.stringify(r.facts)); continue; }
  if (!r.ok) bad++;
  console.log((r.ok ? "PASS " : "FAIL ") + r.name + "  " + JSON.stringify(r.facts));
}
console.log(bad ? "RESULT: FAIL (" + bad + " of " + results.length + ")"
  : blindOnes ? "RESULT: BLIND (" + blindOnes + " of " + results.length + " could not run)"
  : "RESULT: PASS (" + results.length + ")");
process.exit(bad ? 1 : blindOnes ? 2 : 0);
