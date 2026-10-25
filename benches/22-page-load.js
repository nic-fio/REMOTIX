#!/usr/bin/env node
// 22-page-load.js — does the page's main script LOAD (its top level runs to the end)?
//
//   node benches/22-page-load.js src/page.html [SEARCH [HASH]]      e.g. "?logbook" "#video_fault=die"
//
// Runs the biggest <script> of the page in a `vm` whose globals are permissive stubs (document, window, navigator …
// answer anything).  Only the top level runs; timers are inert.  It exists because 22-page-decoder-sim.js fakes the
// page's functions and cannot see a ReferenceError at load: `DIARY` (removed by 8a46c9c9) in VIDEO_FAULT broke the
// login on every browser.  EXIT: 0 the top level ran (or died of a stub limit: said), 1 a ReferenceError.
// `[M]` 25 Oct 2026: the page of ff-worker 0, the same with the old `if (!DIARY)` line 1 (ReferenceError: DIARY).
const fs=require("fs"),vm=require("vm");
const html=fs.readFileSync(process.argv[2],"utf8");
const m=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(x=>x[1]).sort((a,b)=>b.length-a.length)[0]+"\n;globalThis.__vf = VIDEO_FAULT;";
const seen=new Set();
function stub(name){const f=function(){return stub(name+"()")};
  return new Proxy(f,{get(t,k){if(k===Symbol.toPrimitive)return()=>"";if(k==="then"||k==="catch"||k==="finally")return()=>stub(name+".then");if(k==="length")return 0;
    if(k==="indexOf")return()=>-1;if(k==="replace"||k==="split"||k==="slice"||k==="toString")return()=>"";return stub(name+"."+String(k))},
    apply(){return stub(name+"()")},construct(){return stub("new "+name)},set(){return true},has(){return true}})}
const sb={};
for(const n of ["document","window","navigator","performance","localStorage","sessionStorage","screen","history","crypto","console","URL","URLSearchParams","Intl","WebAssembly","AudioContext","MediaSource","Worker","Blob","Notification","matchMedia","requestAnimationFrame","cancelAnimationFrame","fetch","addEventListener","removeEventListener","devicePixelRatio","innerWidth","innerHeight","VideoDecoder","EncodedVideoChunk","AudioDecoder","WebTransport","TextDecoder","TextEncoder","ImageData","OffscreenCanvas","Image","MessageChannel","getComputedStyle","ResizeObserver","MutationObserver","IntersectionObserver","Event","CustomEvent","KeyboardEvent","MouseEvent","Uint8Array"]) if(!["Uint8Array","console","URL","URLSearchParams","Intl","WebAssembly","TextDecoder","TextEncoder"].includes(n)) sb[n]=stub(n);
sb.location={search:process.argv[3]||"",hash:process.argv[4]||"",href:"https://h/",hostname:"h",host:"h",port:"",protocol:"https:",pathname:"/",origin:"https://h",reload(){}};
sb.navigator=stub("navigator"); sb.navigator.userAgent; 
sb.console=console; sb.URL=URL; sb.URLSearchParams=URLSearchParams; sb.TextDecoder=TextDecoder; sb.TextEncoder=TextEncoder; sb.WebAssembly=WebAssembly;
sb.setTimeout=()=>0; sb.setInterval=()=>0; sb.clearTimeout=()=>{}; sb.clearInterval=()=>{}; sb.queueMicrotask=()=>{};
sb.window=sb; sb.self=sb; sb.globalThis=sb;
const ctx=vm.createContext(sb);
try{ vm.runInContext(m,ctx,{filename:"page-main.js"}); console.log("TOP LEVEL RAN TO THE END, no throw; VIDEO_FAULT = " + JSON.stringify(ctx.__vf)); }
catch(e){ console.log((e.name==="ReferenceError"?"REFERENCEERROR: ":"other error (stub limit?): ")+e.name+": "+e.message+"\n"+String(e.stack).split("\n").slice(1,3).join("\n")); process.exitCode = e.name==="ReferenceError"?1:0; }
