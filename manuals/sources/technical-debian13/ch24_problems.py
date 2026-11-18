from build import c, note, p, table, ul, warn

def items(rows, cap):
    return table(["Item", "State"], rows, cap)

S_INTRO = p("This appendix lists what is known to be open, unverified or inconsistent in 1.0.0, area by area. It is "
            "meant to be complete rather than flattering. An item is here because a source file, a check or "
            "<code>PIANO.md</code> says so; where something was read only in a comment and not observed, it is said. "
            "The last two sections list the places where code, comments and documents disagree: in every case the code "
            "was taken as the truth and the chapters describe the code.", lead=True) + \
    note("The package has been run through <code>prove/all.sh</code> on four desktops on 17 Nov 2026 (see the chapter on "
         "testing). Nothing in this appendix is a failure of that run unless it is stated so.", "Scope.")

S_UNVERIFIED = items([
    ["AppArmor in a session", "The profile <code>remotix_network</code> is in complain mode. It was loaded on a Debian 13 VM "
     "(complain and enforce, no denial up to the connection) but the VM has no video card, so no session was observed. "
     "Do not switch it to enforce before a session has been observed on a machine with a card."],
    ["A real phone", "Touch behaviour is proven only by emulation in <code>prove/check-phone.py</code>. The owner tried a "
     "Samsung DeX on GNOME (clipboard, audio and video, window resize: regular). A real touch phone, Safari and iOS were never tested."],
    ["GNOME, first tap after login", "The first touch tap can land on the initial point if the pointer position arrives before "
     "Mutter is ready (<code>touch_announce_pointer</code>). 1 case in 13; not proven; low priority."],
    ["NVIDIA", "No NVIDIA card was used on Debian 13. Comments cite measurements on a rented RTX 4090 of an earlier build; "
     "the group of <code>/dev/nvidia*</code> is not handled by the grants."],
    ["4096×2304", "Not verified end to end. The test browser decodes at most 3840×2160, so <code>canvas-limits</code> fails on all four "
     "desktops; whether the limit is the right one is to be judged."],
    ["Capacity", "At most three users were attached together in the checks, and no run was made at the default cap of 10 sessions. "
     "No capacity figure exists for this tree."],
    ["Reproducible build", "No R23 run is recorded; the package is not claimed to be reproducible. QUIC library tags are not pinned by hash."],
    ["Local-session refusals", "No automatic check covers reasons 0x04 and 0x05; the test boxes run without a display manager."],
    ["Network hardening", "No check floods the server, rotates the page certificate, sends malformed RCP bytes, or uses IPv6. "
     "The packaged unit binds IPv4 only."],
    ["Versions of XFCE and LXQt on trixie", "Not recorded in the repository; the source comments name series 4.20 and 2.1, not re-checked."],
    ["Measured figures in comments", "Figures such as the pixel scan time, the 160 ms drift, the 1.86/0.97 Gpixel/s conversion rates and the "
     "39.54 fps drawn by GNOME at 60 Hz come from comments of earlier builds and were not re-measured on Debian 13."],
], "«TAB» — What was not verified.")

S_OPEN = items([
    ["No unblock for the administrator", "By the owner's decision (17 Nov 2026) a ban ends only by itself. The command socket "
     "(<code>command.c</code>, <code>--command-socket</code>) is compiled in and used by <code>check-ban.py</code>; the packaged unit never passes it."],
    ["No firewall rule opened", "The package ships a ufw application profile; an administrator must run <code>ufw allow REMOTIX</code>."],
    ["Page certificate name", "<code>certificates_prepare()</code> does not compare an existing certificate's name with <code>--name</code>: "
     "a renamed host keeps a certificate with the wrong name until it expires."],
    ["Root-side login pauses", "Lost when the root side restarts; the global AUTH rate (3 per second, burst 8) means a ninth simultaneous login is not checked: it gets «could not check» (0x0E, not counted towards the ban) and must be tried again (<code>rootside.c</code>; the comment in <code>rootside.h</code> says it «waits»)."],
    ["Timing tail on a refusal", "If PAM's own delay exceeds the 2.5 s floor the answer time is no longer fixed."],
    ["Faillock detection", "The detection of <code>pam_faillock</code> works on English text only."],
    ["Quotas unmeasured", "The ban table (160 bans / 256 slots) and the unknown-user limit of 5 were not measured."],
    ["Kernel requirements", "Landlock needs kernel 6.12 (skipped on older ones), <code>mount_setattr</code> needs 5.12, "
     "the seccomp filter exists for x86_64 and aarch64 only (the aarch64 one was never run)."],
    ["Trust boundaries", "The root side is root and unconfined, and PAM modules run as root; users are separated by uid only; "
     "the product adds users to the card groups and puts ACLs on <code>renderD*</code>."],
    ["Power belts shipped off", "The logind power-key and no-suspend drop-ins are installed off, so the power button still works."],
    ["Found-again desktop with a local session", "<code>main.c</code> (~910-935) says «not done, protocol change»: the desktop leaves the list, "
     "so it has no cap count and no abandonment clock."],
    ["TERMINATE_SESSION", "Message 0x0011 is served, but nothing in the page sends it."],
    ["PACE", "The decoder pace message is dormant: the unit does not pass <code>--decoder-pace</code>, a PACE message is a violation, and "
     "RCP.md has no section for it."],
    ["Single-process mode", "<code>--no-split</code> is still in the code, with no walls and no coverage in <code>prove/</code>."],
    ["Clocks", "The 30 and 60 minute clocks were verified by mechanism at short values only. The dead line (10 s of silence) can detach before the 30 s silence clock."],
    ["Mounts after start", "Mounts made on the host after the network side starts arrive without the read-only bit."],
    ["Certificate and library pins", "The key-exchange fallback, the SETTINGS rewrite and the ngtcp2/nghttp3 pins must be re-tested at every upgrade. "
     "The congestion controller was never chosen (default CUBIC). The residual Stateless Reset limit is about 100 collected ids (<code>cid.h</code>)."],
    ["Session id in stream preambles", "Read and logged, never compared with the CONNECT stream id."],
], "«TAB» — Open points in the server.")

S_VIDEO = items([
    ["Dead AV1 code", "<code>encoder.c</code> still holds <code>read_av1_sequence</code>, OBU constants and <code>CODIFICATORE_AV1</code>; AV1 is not produced."],
    ["Shader header", "<code>vulkanvideo_rgb_nv12_spv.h</code> cannot be regenerated from the tree (the generator script is not in it)."],
    ["Budget, cap, quality rise, decoder pace", "All off and uncalibrated. <code>BUDGET_MAX_FPS</code> and <code>BUDGET_STRAIN_DELAY_MS</code> come from one GNOME/Intel UHD 770 machine; <code>WT_RATE_SLOTS</code> = 2 is uncalibrated."],
    ["No card or card that does not encode", "The error repeats every 2 s in the log. A new installation without a card is refused; with a card that does not encode it only says so."],
    ["KDE and labwc", "KDE depends on the system <code>labwc</code>, which is only a Recommends; the fallback that starts KWin with <code>--virtual</code> when labwc is missing was not re-tested. Only Plasma 6.3 behaviour is described."],
    ["Startup codec probe", "Uses the default <code>renderD128</code>; on two cards the encoding node is re-tested per session only when the nodes differ."],
    ["Encoded cursor theme", "Depends on a real cursor theme being installed; its effect on screen is unjudged."],
    ["HEVC", "Never reached the pixel on the test browsers: in the final round the page's probe refused every HEVC string on Chrome and Firefox and every run negotiated H.264 (server logs <code>prove/log/v160-&lt;de&gt;/media.out</code>)."],
], "«TAB» — Open points in capture and encoding.")

S_PAGE = items([
    ["Ctrl+Alt+Del button", "Hidden unless <code>?logbook</code> is in the address; Ctrl+Alt+End was removed. SPECS §7.3-bis and §5.2-bis still require them, so <code>page-cad-button</code> and <code>page-ctrl-alt-end</code> fail. "
     "<code>run_logout()</code> exists but nothing calls <code>logout_show(true)</code>."],
    ["Firefox", "The video worker is the default on desktop Firefox without an isolated live proof. The Firefox clipboard checks pass in the final run although PIANO's first status lists the item as open."],
    ["Keyboard layout and zoom", "No user-selectable keyboard layout (<code>navigator.language</code> is only a hint); a change of <code>devicePixelRatio</code> (page zoom) is not handled."],
    ["Test switches", "<code>?canvas=2d</code>, <code>?canvas=bmp</code>, <code>?draw=mse</code> and <code>#video_fault</code> remain; deleting the MSE path is undecided."],
    ["KDE", "A held Delete key is kept by the desktop (visible in diagnostics only). Klipper stops following above 10 changes a second."],
    ["Audio and clipboard", "No Safari or Windows Firefox; text only; no microphone. <code>SCHED_FIFO</code> may be refused with <code>CONFIG_RT_GROUP_SCHED</code>, so audio can crackle under load."],
    ["Opus decoder", "Nothing verifies that <code>page.html</code> embeds the current <code>opus.wasm</code>; <code>build.sh --verify</code> is run by hand only."],
], "«TAB» — Open points in the page, input, audio and clipboard.")

S_DESK = items([
    ["XFCE", "Ignores a Log Out requested while the desktop is still starting (no retry in the code); a corner covered by the panel; the state file <code>xfce-chiavi</code> is not removed after the restore; an action button added by hand during a session is not locked until the next birth."],
    ["GNOME", "Starts in the Overview and REMOTIX does not leave it; the Overview holds touches. <code>pkexec</code> fails because <code>SHELL</code> is empty (wanted)."],
    ["KDE", "Only KDE has the watch that finishes a Log Out systemd refused; whether other desktops can hit the same refusal was not investigated."],
    ["LXQt", "Whether <code>lxqt-session</code> logout without force works within 10 s is marked «[?]» in a comment."],
    ["Settings left behind", "Two exceptions to «nothing permanent in the user's settings»: the XFCE copy and restore of locked keys and the LXQt one-time restore. One-time cleanup marks (<code>gnome-ripristinato</code>, <code>lxqt-restored</code>, <code>xfce-vecchi-ripristinati</code>) remain for values of earlier versions."],
    ["Environment variables", "<code>REMOTIX_VPP_PADDING</code> and <code>REMOTIX_VULKAN_CONVERSION</code> never reach a real session (the child environment is composed from scratch); they reach only the startup probe and <code>--encoding-test</code>."],
    ["Log priorities", "About 700 call sites starting with ⛔ were not observed in the priority run; their level is unverified."],
], "«TAB» — Open points in the desktops and logging.")

S_TEST = items([
    ["Final round", "Passes on the four desktops except the items explained in PIANO.md: XFCE 111/118, LXQt 112/118, KDE 111/118, GNOME 104/118. The run was made with the same code under a provisional version label; on the 1.0.0 package itself only a short run is recorded (server logs <code>prove/log/v100c-&lt;de&gt;.out</code>: the base check with Chrome and the ban check, 13 PASS and nothing else on each of the four desktops)."],
    ["Package check", "PIANO says 8/8; the XFCE log shows 8 PASS plus <code>apparmor</code> BLOCKED and the script exits 1. The file holds nine check names."],
    ["LXQt Firefox audio", "<code>audio-lxqt-firefox</code> was BLOCKED in the round (Marionette timeout); the re-run passes."],
    ["Check scripts", "<code>prove/fresh.sh</code>, <code>matrix.sh</code> and <code>all.sh --fresh</code> call <code>prove/boxes</code>, which exists on the server but not in the tree (the folder is top-level <code>boxes/</code>). "
     "<code>lib.sweep()</code> omits the prefixes <code>in</code> and <code>ph</code>. <code>headless-multi.sh</code> and <code>lifecycle-window.py</code> have no caller. <code>base-check.py</code> and <code>check-base.py</code> are near duplicates."],
    ["Unit tests", "No in-tree tests exist for <code>hsrate.h</code>, <code>msgrate.h</code>, <code>linebudget.h</code>, <code>dimcheck.h</code>, <code>unchanged.h</code>, <code>damage_classify</code>."],
    ["Build", "A plain <code>make</code> in <code>src/</code> needs <code>TWIN=none</code>. <code>SOURCE_DATE_EPOCH</code> defaults to file mtimes, so two checkouts differ."],
    ["Clean-up", "Tranche 2 of the non-Debian clean-up is open. Many identifiers are Italian (<code>registro_dice()</code> with 1171 uses, <code>SORGENTI</code>, <code>wt_chi</code>, ...). A port needs the removed SELinux and Ubuntu code again."],
], "«TAB» — Open points in testing and build.")

CONTRA = [
    ["Unblock command", "SPECS.md:295,309; DECISIONS-11.md:1987,2002; main.c:245,3621; prove/check-ban.py header", "Describe an unblock command. The package ships none. page.c and page.html were changed to say the block ends by itself."],
    ["Fixed answer time", "SPECS.md §4.4; RCP.md §4.4-bis", "One fixed second. Code: 1000 ms for success, 0x08, 0x0E; REJECT_FLOOR 2500 ms for a PAM refusal (rcp.c:227-248)."],
    ["Key limit", "check-ban.py:3,22,266; rootside.h:273", "Say 12. Code and SPECS: 20 (rcp.c LIMIT[] = 5/20/30)."],
    ["Paused AUTH", "rootside.h:285", "Says not counted. Code answers RXR_PAUSED, a counted refusal 0x07."],
    ["AUTH rate", "rootside_proto.h:56", "Says 10 per second, burst 20. Constants and the comment at :62: 3 and 8."],
    ["fds crossing", "rootside_proto.h:21; :19-27", "Say one fd crosses and omit RXR_CODEC (109). Code sends two (rootside.c:1421: socket and pidfd)."],
    ["PAM_RHOST", "sentinel.h:27", "Says never set. authentication.c and child.c:1675 set it."],
    ["Process limit", "walls.c:791", "Says 64 is wide. WALLS_NPROC_MAX is 128 (walls.h:71)."],
    ["/proc", "walls.h:45", "Says /proc is not hidden. The network side has its own /proc (main.c, rediscover_refuse_here)."],
    ["AppArmor", "remotix_network.apparmor:3-4, :33", "«Never loaded» and «10 audit lines on 26 Oct»; PIANO records a VM run. The profile allows <code>network netlink raw</code> while seccomp refuses AF_NETLINK."],
    ["tmpfiles", "remotix.tmpfiles:1", "«Not active yet»; it is installed and used."],
    ["Stale installer text", "remotix.pam:3-9; main.c:472; authentication.c:64,244; debian/control; debian/rules:61; remotix.service:6,25; kwin.c RX-KDE-001; LICENSE.md", "Mention other distributions' PAM files, build.sh, «the engine», «the installer», the old run files or REMOTIX_SPLIT."],
    ["Paths", "debian/control; src/Makefile; build/quic-static.sh", "Name src/build-targets/quic-static.sh (now build/quic-static.sh), a <code>dipendenze</code> target (it is <code>deps</code>), benches scripts and provision.sh."],
    ["Licences", "CLAUDE.md", "Says licenses/ ships in the package; debian/rules installs only THIRD-PARTY-LICENSES."],
    ["Hooks", "rcp.h:164", "«Three, and no more»; about 27 exist."],
    ["Pending caps", "transport.h:129; hsrate.h:3", "Say 8 and 32. Code: PENDING_PER_ADDRESS 16, PENDING_PER_48 64."],
    ["Page caps", "page.h PAGE_MAX_CLIENTS comment; page.c", "Say 4 per address and a page of about 907 KB. Code: PAGE_PER_ADDRESS 32, PAGE_PER_48 64; the page is 937 155 bytes."],
    ["Keepalive", "rcp.c:8746 comment; webtransport.c keepalive_rule()", "Comment: PINGs only during credentials. Code: every state except finished."],
    ["Client close codes", "webtransport.c closed_by_client() ~7597; RCP.md §8.2", "Code accepts 0x01..0x0F; RCP.md and reason_for_82() up to 0x10."],
    ["Shutdown wait", "main.c ~4140", "Comment: two seconds. Loop: 4000 ms."],
    ["PACE", "DECISIONS-11 §11.32 title; comments citing RCP.md §13", "Title says on by default; body, rcp.h and main.c say off. RCP.md has no §13."],
    ["Encoder header", "encoder.c:2; child.c:7055-56", "Header names software and AV1; code has neither. Comment says hevc_strada, code prints hevc_route."],
    ["NVIDIA", "SPECS.md:1273", "Says nobody has seen NVIDIA work; comments cite measurements on an RTX 4090."],
    ["KWin --virtual", "session.c:3008; kwin.h", "Say it is gone; kwin.c:1318-1330 still uses it when labwc is not in PATH."],
    ["Bandwidth floor", "encoder.c, main.c, budget comments", "20 Mbit/s; WT_FLOOR_BYTE_MS is 3750 bytes/ms (webtransport.c:4018)."],
    ["Names", "wlroots.c; rcp.c comments", "RCP_TELA_L/A_MASSIMA for RCP_CANVAS_MAX_W/H; <code>tratta_*()</code> does not exist. SPECS names MAX_ATTACCATE, MAX_FIGLI, QUANTI_PRESENTI, WT_PALCHI, which are not in src/."],
    ["Logging", "log.h; log.c line()", "log.h: detail lines at priority 7; code never sends them to the journal. «Async-signal-safe» no longer true."],
    ["Settings comments", "session.c session_inhibit(), local_session()", "LXQt panel entries «not touched» (six are hidden); local_session() returns an empty structure on Debian 13."],
    ["Firefox worker", "page.html ~1318-1346, 9800-9803; DECISIONS-11 §11.36", "«Proposal, not decided»; code makes it the default; the decision is marked DECIDED."],
    ["Pointer mode, WebGL2", "page.html CSS 395-460; Viewer constructor ~3295", "<code>both</code> as default (code: <code>cl_mode = \"system\"</code>); WebGL2 «not the default» wording; <code>classic_input.hook()</code> (page.html:11411) does not exist."],
    ["Ctrl+Alt+Del", "SPECS §7.3-bis, §5.2-bis", "Require the button and Ctrl+Alt+End; the page hides one and removed the other."],
    ["Session survival", "SPECS §5.2 box", "Says desktops do not survive the server; its own T2 measurement shows they do."],
    ["Test windows", "check-media.py docstring; DECISIONS §4.6-septies", "250 ms (code 400 ms); UHD 730 (corrected to 770 in DECISIONS-11 §11.21)."],
    ["Missing files", "Comments in many headers", "Cite benches/, phases/, STUDIES.md, CODER.md, REVIEWER.md: not in this tree. main.c:3153 and :514 carry old wording."],
    ["PIANO.md", "PIANO.md", "Says specs aligned on the unblock (they are not); «8 utenti» vs RCP_SESSION_CAP = 10; a provisional version label (this manual uses 1.0.0); check-package 8/8."],
]

S_CONTRA = table(["Subject", "Where", "What disagrees"], CONTRA,
                 "«TAB» — Contradictions between code, comments and documents (the code wins).")

CHAPTER = ("Appendix C — Known issues and open points", [
    ("How to read this appendix", S_INTRO),
    ("What is unverified", S_UNVERIFIED),
    ("Open points in the server", S_OPEN),
    ("Open points in capture and encoding", S_VIDEO),
    ("Open points in the page, input, audio and clipboard", S_PAGE),
    ("Open points in the desktops and logging", S_DESK),
    ("Open points in testing and build", S_TEST),
    ("Contradictions between code, comments and documents", S_CONTRA),
])
