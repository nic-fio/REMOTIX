from build import c, note, p, rif, table, ul, warn

def items(rows, cap):
    return table(["Item", "State"], rows, cap)

S_INTRO = p("This appendix lists what is known to be open, unverified or inconsistent in 1.0.1, area by area. It is "
            "meant to be complete rather than flattering. An item is here because a source file, a check or "
            "<code>PIANO.md</code> says so; where something was read only in a comment and not observed, it is said. "
            "The last two sections list the places where code, comments and documents disagree: in every case the code "
            "was taken as the truth and the chapters describe the code.", lead=True) + \
    note("The package has been run through <code>prove/all.sh</code> on four desktops on 17 Nov 2026 (see the chapter on "
         "testing), on the code of 1.0.0. Release 1.0.1 changed only the choice of key positions in <code>keyboard.c</code> and the Keyboard menu of the page; "
         "the key-position change was compared with the old rule on 98 layouts, and no full round of <code>prove/all.sh</code> on 1.0.1 is recorded in the sources read for this manual. "
         "Nothing in this appendix is a failure of that run unless it is stated so.", "Scope.")

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
    ["4096×2304", "Not verified end to end. The page's size ladder stops at 3840×2160, so <code>canvas-limits</code> fails on all four "
     "desktops; whether the limit is the right one is to be judged. The <b>declared</b> limit of the product is 3K (the size actually "
     "used depends on the client), so 4096×2304 is a technical bound, not a promise."],
    ["Capacity", "At most three users were attached together in the checks, and no run was made at the default cap of 10 sessions, nor at "
     "the declared limit of 8 users. No capacity figure exists for this tree."],
    ["Reproducible build", "No R23 run is recorded; the package is not claimed to be reproducible. QUIC library tags are not pinned by hash."],
    ["Local-session refusals", "<code>prove/check-prelocal.py</code> covers the 0x04 on the local-login hook's road, with the login simulated. "
     "No automatic check covers reason 0x05, nor the sweeps against a real local session; the test boxes run without a display manager."],
    ["Network hardening", "No check floods the server, rotates the page certificate, sends malformed RCP bytes, or uses IPv6. "
     "The packaged unit binds IPv4 only."],
    ["Versions of XFCE and LXQt on trixie", "Not recorded in the repository; the source comments name series 4.20 and 2.1, not re-checked."],
    ["Measured figures in comments", "Figures such as the pixel scan time, the 160 ms drift, the 1.86/0.97 Gpixel/s conversion rates and the "
     "39.54 fps drawn by GNOME at 60 Hz come from comments of earlier builds and were not re-measured on Debian 13."],
], "«TAB» — What was not verified.")

S_LIMITS = items([
    ["Declared limits of the product", "Resolution up to <b>3K</b> (the size actually used depends on the client) and <b>8 users</b> at the same "
     "time. Owner's decision, <code>DECISIONS-11</code> §11.51, confirmed 18 Nov 2026. The program technically accepts more (a protocol "
     "canvas of 4096×2304, a probe ladder in the page up to 3840×2160, <code>--session-cap</code> default 10), but those are not the declared values."],
    ["XFCE: black background in the remote desktop", "The wallpaper of the remote desktop is black instead of the user's (seen by the owner on a live XFCE; "
     "in the server's checks the picture was 93% of one colour). REMOTIX does not touch the wallpaper settings. <b>Unverified hypothesis:</b> "
     "XFCE stores the wallpaper per monitor name and the remote virtual screen has another name. Postponed by the owner; to be checked on a machine "
     "with XFCE, and on the other three desktops too. XFCE only, so far."],
    ["Service killed and not yet restarted", "If the service is killed outright (SIGKILL, a crash) there is a window of about 2 s, until systemd restarts "
     "it, in which nobody can close the desktop left behind. The restarted root side then ends it unless its user returns first (“no orphan desktops”; "
     + rif("Desktops found again after a restart") + ")."],
    ["How the local-login hold was proven", "On the four real login screens, by the owner: GNOME on the tablet (18 Nov 2026, with the journal read: the "
     "login was held in PAM, the remote desktop closed by its child in 803 ms, the page told with 0x04, the local session entered and stayed), and KDE "
     "(SDDM), XFCE and LXQt on Debian 13 live systems started on the server, as <b>reported by the owner</b> (the remote desktop was disconnected and the "
     "local login entered at the first try; the logs were not read). In the automatic checks the local login is <b>simulated</b> by calling the hook "
     "by hand (<code>check-prelocal.py</code>): the boxes have no real login screen and no local session is registered. The interplay "
     "with the periodic sweeps, and the hook's skipping of the guard in the child, are exercised only by a real local login."],
    ["GNOME, graphical password window (<code>pkexec</code>)", "The automated check (<code>users-shell-and-environment</code>) does not pass in the test containers. <code>SHELL</code> is empty in every GNOME remote session, "
     "by design of the composed environment (<code>session.c</code>). Whether the password window appears on a real machine was not verified; if it does not, use <code>sudo</code> in the terminal."],
    ["RealtimeKit in the containers", "In the test containers RealtimeKit does not start and holds the exit of a young child for 25 s (the check waits 31 s). "
     "It is an artefact of the test boxes; it does not happen on the tablet."],
], "«TAB» — Known limits of this release.")

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
    ["Found-again desktop with a local session", "The network side does not close it (<code>found_again_close_for_local()</code>, "
     "<code>main.c</code>): the desktop leaves the list, so it has no cap count and no abandonment clock, and in the split server the root side "
     "ends its scope within about ten seconds. In the single-process mode (<code>--no-split</code>, not packaged) the process itself is root and closes that session with logind's <code>TerminateSession</code>; only if that fails is the stage left alone."],
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
    ["Keyboard layout and zoom", "The sign-in form has a Keyboard menu (since 1.0.1) but it offers only the 33 plain layouts of the <code>KEYBOARDS</code> table: no variants such as «US international»; the layout can be changed only at sign-in (the <code>LAYOUT</code> message exists, the page does not send it); a layout the server cannot compile gets the generic «the server could not open your session» refusal, with the reason only in the log; a change of <code>devicePixelRatio</code> (page zoom) is not handled."],
    ["Test switches", "<code>?canvas=2d</code>, <code>?canvas=bmp</code>, <code>?draw=mse</code> and <code>#video_fault</code> remain; deleting the MSE path is undecided."],
    ["KDE", "A held Delete key is kept by the desktop (visible in diagnostics only). Klipper stops following above 10 changes a second."],
    ["Audio and clipboard", "No Safari or Windows Firefox; text only; no microphone. <code>SCHED_FIFO</code> may be refused with <code>CONFIG_RT_GROUP_SCHED</code>, so audio can crackle under load."],
    ["Opus decoder", "Nothing verifies that <code>page.html</code> embeds the current <code>opus.wasm</code>; <code>build.sh --verify</code> is run by hand only."],
], "«TAB» — Open points in the page, input, audio and clipboard.")

S_DESK = items([
    ["XFCE", "Ignores a Log Out requested while the desktop is still starting (no retry in the code); a corner covered by the panel; the state file <code>xfce-chiavi</code> is not removed after the restore; an action button added by hand during a session is not locked until the next birth."],
    ["GNOME", "Starts in the Overview and REMOTIX does not leave it; the Overview holds touches. The <code>SHELL</code> variable is deliberately empty in the composed environment (a trap of gnome-session's login shell, <code>session.c</code>); see the known limit on <code>pkexec</code>."],
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
    ["Paused AUTH", "rootside.h:290", "Says a paused request gets «not checked» and is not counted. Code answers RXR_PAUSED, a counted refusal 0x07."],
    ["fds crossing", "rootside_proto.h:19-27", "Says the child's socket end is the only fd that ever crosses. Code sends two with RXR_SPAWNED (the socket and a pidfd, rootside.c). The header now names RXR_CODEC."],
    ["PAM_RHOST", "sentinel.h:27", "Says never set. authentication.c and child.c:1675 set it."],
    ["Process limit", "walls.c:791", "Says 64 is wide. WALLS_NPROC_MAX is 128 (walls.h:71)."],
    ["/proc", "walls.h:45", "Says /proc is not hidden. The network side has its own /proc (main.c, rediscover_refuse_here)."],
    ["AppArmor", "remotix_network.apparmor:57", "The profile allows <code>network netlink raw</code> (marked «remove when proven unused») while seccomp refuses AF_NETLINK. The header now reports the VM run (corrected on 17 Nov 2026)."],
    ["Stale installer text", "main.c:445-473; authentication.c:94; remotix.service:6; LICENSE.md:13", "Mention other distributions' PAM files (<code>.fedora</code>, <code>.suse</code>, <code>.arch</code>), «phases/17-the-installer.md», <code>--without split</code> / REMOTIX_SPLIT, and «the installer» (<code>remotix-*.run</code>). "
     "The text at main.c:466-473 is a <b>run-time log message</b> (" + "the PAM service «remotix» DOES NOT EXIST" + "): it should tell the administrator <code>apt install --reinstall remotix</code>; to be corrected at the next build."],
    ["Desktops survive the stop", "debian/rules:103; debian/remotix.postinst:11; debian/remotix.service:40; debian/remotix.prerm:11; main.c:3918-3923", "Comments (and, in main.c, the log message «the network side stops — systemd restarts the unit, the desktops stay alive») say that the desktops stay alive "
     "when the service stops. Since 17 Nov 2026 (DECISIONS-11 §11.56) an orderly stop closes them, and after a fall of the root side the restarted root side ends them unless their user returns within about 10 s. To be corrected at the next build."],
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
    ["Session survival", "SPECS §5.2 box", "Reports the T2 measurement of 29 Sep 2026: stopping the unit leaves the desktops alive. Since §11.56 (17 Nov 2026) an orderly stop closes them; SPECS was not updated."],
    ["Test windows", "check-media.py docstring; DECISIONS §4.6-septies", "250 ms (code 400 ms); UHD 730 (corrected to 770 in DECISIONS-11 §11.21)."],
    ["Missing files", "Comments in many headers", "Cite benches/, phases/, STUDIES.md, CODER.md, REVIEWER.md: not in this tree. main.c:3153 and :514 carry old wording."],
    ["PIANO.md", "PIANO.md", "Says specs aligned on the unblock (they are not); «8 utenti» vs RCP_SESSION_CAP = 10; a provisional version label (this manual uses 1.0.0); check-package 8/8."],
]

S_CONTRA = table(["Subject", "Where", "What disagrees"], CONTRA,
                 "«TAB» — Contradictions between code, comments and documents (the code wins).")

CHAPTER = ("Appendix C — Known issues and open points", [
    ("How to read this appendix", S_INTRO),
    ("What is unverified", S_UNVERIFIED),
    ("Known limits and what was proven", S_LIMITS),
    ("Open points in the server", S_OPEN),
    ("Open points in capture and encoding", S_VIDEO),
    ("Open points in the page, input, audio and clipboard", S_PAGE),
    ("Open points in the desktops and logging", S_DESK),
    ("Open points in testing and build", S_TEST),
    ("Contradictions between code, comments and documents", S_CONTRA),
])
