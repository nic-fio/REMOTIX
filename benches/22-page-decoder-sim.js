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
// EXIT: 0 all pass · 1 a scenario failed (the bug) · 2 blind: node missing (the caller's
//       business), the page unreadable, `class Viewer` not found, or the healthy start
//       does not decode (the simulation no longer fits the page — fix THIS file).
// `[M]` 15 Oct 2026: pass on b1dea604, fail (A, B) on b1dea604^.
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
  decode() {
    if (this.state !== "configured") throw new Error("InvalidStateError: decode on " + this.state);
    this.decoded++;
    if (FakeDecoder.failNext) {
      FakeDecoder.failNext = false; this.state = "closed";
      this.cb.error(new Error("EncodingError: fake"));
    }
  }
  close() { this.state = "closed"; }
  flush() { return Promise.resolve(); }
  reset() { if (this.state === "closed") throw new Error("InvalidStateError: reset on closed"); this.state = "unconfigured"; }
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

let bad = 0;
for (const r of results) {
  if (!r.ok) bad++;
  console.log((r.ok ? "PASS " : "FAIL ") + r.name + "  " + JSON.stringify(r.facts));
}
console.log(bad ? "RESULT: FAIL (" + bad + " of " + results.length + ")" : "RESULT: PASS (" + results.length + ")");
process.exit(bad ? 1 : 0);
