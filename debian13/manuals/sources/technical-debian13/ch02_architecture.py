from build import arrow, box, c, fig, flow, note, p, path, rif, sysf, table, text, tip, warn, zone

# ── The roles of the server executable ──────────────────────────────────────────
S1 = p("The server is one executable, " + c("/usr/libexec/remotix/remotix") + ", that plays several roles. The role is "
       "chosen by the first argument, read at the top of " + c("main()") + " in " + c("main.c") + " before any option, "
       "certificate or socket is touched, so that each role starts from a fresh memory image: a child must not hold the "
       "server's TLS key, and the PAM dispatcher must not hold any password or secret. The package ships one more, very "
       "small program, " + c("/usr/libexec/remotix/remotix-local-login") + " (" + c("local_login.c") + ", libc only): it is "
       "not a role of the server but a hook that PAM runs at a local login (" + rif("The local-login hold") + "); the line that starts it is put into "
       + sysf("/etc/pam.d/common-session") + " by " + c("pam-auth-update") + " (the profile " + c("debian/remotix.pam-config") + "), and the shell script "
       + c("/usr/libexec/remotix/remotix-pam-hook") + " (" + c("src/remotix-pam-hook") + ") checks at every start of the service that it is still there.", lead=True) + \
    table(["First argument", "Role", "Runs as", "Entry point", "Started by"], [
        ["(none)", "<b>Root side</b>: the process systemd starts; the main PID of the unit. Parses the options, binds the "
         "UDP and TCP port, then hands everything to " + c("rootside_main()") + " and never comes back",
         "root", c("main()") + " then " + c("rootside_main()"), c("remotix.service")],
        [c("--network-side"), "<b>Network side</b>: QUIC, TLS, WebTransport, RCP and the page. The rest of " + c("main()"),
         "user " + c("remotix") + ", behind the walls", c("main()") + ", " + c("rootside_attach()"),
         "the root side, by " + c("execve()") + " of " + c("/proc/self/exe")],
        [c("--pam-helper"), "<b>PAM dispatcher</b>: reads a request and forks one process per password check",
         "root", c("helper_main()"), "the root side, through " + c("helper_turn_on_root()")],
        [c("--internal-child"), "<b>Child</b>: one per admitted user; holds the user's stage", "the user",
         c("child_alive()"), "the root side, in " + c("child_birth()")],
        [c("--kwin-nested"), "The host of a KDE user's KWin; opens nothing of the server", "the user",
         c("kwin_nested_alive()"), "the user's own " + sysf("plasma-kwin_wayland.service")],
        [c("--encoding-test"), "Encodes a synthetic 256×256 frame on the card and prints one JSON line (exit 0 encoded, 1 "
         "opened but no frame, 2 usage, 3 no card can encode); the same question the startup probe asks, as a command",
         "any user", c("child_test_encoding()"), "an administrator or a check, by hand"],
        [c("--drop-render-grants"), "Takes back the card ACLs the service granted; run by the package's removal scripts "
         "before the binary is deleted", "root", c("render_grant_drop_all()"), "the maintainer scripts"],
    ], "«TAB» — The roles of the server executable, by first argument") + \
    p("The unit's command line is in " + c("debian/remotix.service") + ": " + c("--address 0.0.0.0") + ", "
      + c("--name %H") + " (the certificate carries the machine's name), the port from " + c("REMOTIX_PORT") + " (default "
      "7447, " + c("debian/remotix.conf") + "), " + c("--certificates") + " and " + c("--ban-file") + " in "
      + c("/var/lib/remotix/net") + ", " + c("--page /usr/share/remotix/page.html") + ", " + c("--split") + ", "
      + c("--journal") + " and then " + c("REMOTIX_OPTIONS") + " from the administrator's drop-ins in "
      + c("/etc/remotix/remotix.conf.d/") + ". The unit sets no " + c("User=") + " and no hardening: whatever a unit "
      "restricts, every desktop born from it inherits (DECISIONS-11 §11.11), so the network side's restrictions are put on "
      "that one process by the program itself (" + rif("The network side and its walls") + ").") + \
    note("The binary can still run as a single process, with no walls and no privilege separation: " + c("--no-split")
         + ", or started as an ordinary user (" + c("main()") + " logs “not started as root: ONE process”). The unit never "
         "uses it, and the cleaning inventory " + c("docs/INVENTARIO-non-debian.md") + " lists it as code that stays for "
         "now. This manual describes the split server, which is the product. The single-process mode is not exercised by "
         "the checks in " + c("prove/") + ".", "Single-process mode.")

# ── The process tree ─────────────────────────────────────────────────────
PROCESSES = fig(
    zone(20, 12, 450, 312, "remotix.service")
    + box(40, 44, 410, 52, "Root side", "root · one thread, no GLib · probe, PAM, births, signals", "navy")
    + box(40, 140, 190, 52, "PAM dispatcher", "root · child of the root side", "dark")
    + box(40, 244, 190, 52, "PAM check", "root · one transaction, exits", "dark")
    + box(260, 140, 190, 52, "Network side", "user remotix · own namespaces", "navy")
    + box(260, 244, 190, 52, "GPU probe", "root · at startup and later", "grey")
    + arrow(135, 98, 135, 138) + arrow(135, 194, 135, 242) + arrow(355, 98, 355, 138)
    + text(355, 122, "fork, walls, execve", 10.5, "#334155")
    + arrow(355, 246, 355, 198, "#475569", True)
    + zone(500, 12, 380, 150, "logind session scope of user A")
    + box(520, 44, 150, 52, "Child of A", "runs as user A", "blue")
    + box(700, 44, 160, 52, "Desktop of A", "compositor + programs", "light")
    + zone(500, 172, 380, 150, "logind session scope of user B")
    + box(520, 204, 150, 52, "Child of B", "runs as user B", "blue")
    + box(700, 204, 160, 52, "Desktop of B", "compositor + programs", "light")
    + arrow(452, 70, 518, 70) + text(485, 62, "fork + exec", 10.5, "#334155")
    + path([(452, 80), (476, 80), (476, 226), (518, 226)], "#0050C0")
    + path([(452, 166), (486, 166), (486, 100), (518, 100)], "#475569", True)
    + arrow(672, 70, 698, 70, "#475569", True) + arrow(672, 230, 698, 230, "#475569", True)
    + text(686, 120, "setsid --fork", 10.5, "#334155") + text(686, 290, "setsid --fork", 10.5, "#334155"),
    900, 336, "«FIG» — The processes: the unit's tree, and one child per user in that user's logind session. The dashed line to the children is the socket the root side hands to the network side")

S2 = p("The process layout answers one question: what can each part of the server do if it is taken over? The line is "
       "drawn between the code that talks to strangers (QUIC, TLS and RCP parsers, the page server) and the code that "
       "can do things to the machine (check passwords, become a user, signal a desktop).", lead=True) + PROCESSES + \
    table(["Process", "Identity", "Talks to", "Can do", "Cannot do"], [
        ["Root side", "root, no walls", "the network side (one socket), the PAM dispatcher, its children, logind's "
         "files and " + c("/proc"), "fork the dispatcher, the network side and the children; reap them; signal only "
         "its own children; probe the card; read logind state", "open the network, parse a client byte, "
         "use GLib or D-Bus (it is single-threaded on purpose)"],
        ["Network side", "uid " + c("remotix") + ", no capability, tree read-only", "the clients (UDP 7447 and TCP 7447, "
         "inherited sockets), the root side, logind and the journal over their path sockets",
         "terminate TLS and QUIC, run RCP, serve the page, write " + c("/var/lib/remotix/net") + " and "
         + c("/run/remotix/net"), "fork, run a program, read " + c("/etc/shadow") + ", become another user, see another "
         "process, create a user namespace"],
        ["PAM dispatcher and checks", "root, fresh image after " + c("execve()"), "the root side (one socket)",
         "call PAM once per process", "talk to the network; keep any state"],
        ["Child", "the user, privilege drop verified with " + c("getresuid()"), "the root side's socket pair; the "
         "user's session bus; PipeWire; the compositor; the card", "capture, encode, inject input, clipboard, audio, "
         "end the session", "open the port; hold the TLS key; speak RCP"],
    ], "«TAB» — What each process may and may not do") + \
    p("Two numbers keep the layout honest. The network side is <i>never</i> the parent of anything that matters: the "
      "children are forked by the root side and the network side receives only the child's socket end and a "
      "<code>pidfd</code> over " + c("SCM_RIGHTS") + ". And the desktops are not behind the walls: they are started by the "
      "child, outside the unit, so that " + c("sudo apt install") + " inside a remote desktop keeps working "
      "(" + c("walls.h") + ").")

# ── The root side ────────────────────────────────────────────────────────
S3 = p("The root side is " + c("rootside_main()") + " in " + c("rootside.c") + ". It exists so that everything that needs "
       "root is done by a process that never parses a byte from the internet. It is <b>single-threaded and uses no "
       "GLib or D-Bus</b>: it forks children, and a fork of a multi-threaded process runs PAM and NSS in a copy whose "
       "locks may be held by a thread that is not there. For the same reason " + c("main()") + " must call "
       + c("rootside_main()") + " before anything that could start a GLib thread (" + c("rediscover.c") + " opens a "
       "D-Bus connection).", lead=True) + \
    p("<b>Startup order in " + c("rootside_main()") + ".</b>") + \
    table(["Step", "What", "Why"], [
        ["0", "Bind the UDP and TCP port in " + c("main()") + " (" + c("transport_bind()") + ", " + c("page_bind()")
         + ") before the split", "The network side then needs no capability, even for a port below 1024"],
        ["1", "Probe the card: " + c("child_video_capabilities()") + " in a forked process; if it finds no codec, remember "
         "to measure again", "A driver that crashes must not take the service down before it has a port"],
        ["2", c("render_grant_sweep()") + ": take back the card ACLs a previous run left", "A crash would leave grants "
         "in " + c("/var/lib/remotix/render-grants")],
        ["3", "Signals through a self-pipe (SIGTERM, SIGINT, SIGQUIT stop; SIGCHLD reaps; SIGUSR1/2 are forwarded to the "
         "children for the bench snapshot)", "One loop, no handler logic"],
        ["4", c("helper_turn_on_root()") + ": the PAM dispatcher, now the root side's own child", "PAM never runs in the "
         "network side"],
        ["5", c("rootside_bounds_init()") + ", then " + c("net_start()") + ": socket pair, fork with a new PID namespace "
         "(" + c("walls_fork_pidns()") + "), fds 3 (channel), 4 (UDP), 5 (TCP), " + c("walls_apply()") + ", "
         + c("execve()"), "No network side without its walls: if " + c("walls_apply()") + " fails the process exits with "
         "126 and is not started"],
    ], "«TAB» — How the root side starts") + \
    p("Then it loops on " + c("poll()") + " over the self-pipe, the channel to the network side, the PAM dispatcher and the inotify descriptor of the "
      "local-login requests, with a timeout of 1000 ms (100 ms while stopping or while a local login is being served). Each round it reads the channel (" + c("chan_read()")
      + "), flushes queued answers, reaps children (" + c("reap_kids()") + ") and the network side (" + c("reap_net()")
      + "), checks the desktops found again (" + c("found_check()") + ", " + c("found_pump()") + "), repeats the card "
      "probe if needed (" + c("codec_retry()") + "), sends overdue signals (" + c("kids_hurry()") + "), serves the "
      "requests of a local login that is held in PAM (" + c("pl_step()") + ", " + rif("The local-login hold") + "), keeps its tables "
      "(" + c("tables_minute()") + ") and sweeps the KDE compositor hosts (" + c("kdehost_sweep()") + ").") + \
    p("<b>If the network side dies</b> the root side reaps it, closes the channel, gives each of its children "
      + c("KIDS_EOF_GRACE_MS") + " (5000 ms) to leave on the end-of-file, then sends SIGTERM and, " + c("KIDS_TERM_GRACE_MS")
      + " (3000 ms) later, SIGKILL; only the children, never the desktops. It restarts the network side after a pause of "
      "1 s, 2 s, 4 s … up to " + c("NET_RESTART_CAP_MS") + " (30 s); a network side that lived at least "
      + c("NET_STABLE_MS") + " (60 s) resets the count (" + c("reap_net()") + "). Before each start it kills any process of "
      "the user " + c("remotix") + " that is in the root side's own cgroup (" + c("net_leftovers_kill()") + "), and it "
      "wipes the grants it had given to the previous network side (" + c("net_generation_reset()") + "). It starts the "
      "new one only after listing the desktops found again, so that the list is ready when the network side asks "
      "(" + c("found_look()") + ").") + \
    p("<b>If the root side dies</b> the network side sees end-of-file on its channel, leaves its loop and exits (" + c("rootside_lost()")
      + " in the loop of " + c("main()") + "); systemd restarts the unit (" + c("Restart=on-failure") + ", "
      + c("RestartSec=2") + "). The desktops are outside the unit, so a crash does not end them by itself; the restarted "
      "root side ends every REMOTIX desktop that has no child, unless its user comes back first (" + rif("Desktops found again after a restart")
      + ").") + \
    p("<b>Stopping.</b> On SIGTERM the root side sends SIGTERM to the network side and waits at most " + c("STOP_WAIT_MS")
      + " (25 000 ms) for it and for the children, then SIGKILLs the network side. An orderly stop closes the remote "
      "desktops: the network side asks each child for the close of its desktop (at most " + c("STOP_CLOSE_WAIT_MS")
      + ", 15 000 ms), and the root side ends what is still in a REMOTIX scope before it exits; " + c("KillMode=mixed")
      + " takes anything left (" + rif("Stopping the service") + ").")

# ── The network side ─────────────────────────────────────────────────────
WALL_ORDER = flow([
    ("Checks", "user, dirs, PID 1", "dark"),
    ("AppArmor", "exec profile", "blue"),
    ("Mounts", "slave, /proc, RO", "navy"),
    ("Namespaces", "private net", "blue"),
    ("Identity", "caps, gid, uid", "navy"),
    ("Filters", "no new privs, BPF", "dark"),
], "«FIG» — The order in which " + "walls_apply()" + " puts the walls up (each step needs the power the next one removes)")

S4 = p("The network side is the same binary re-executed with " + c("--network-side") + " as its first argument; "
       "the rest of " + c("main()") + " is its code. It checks, before anything else, that it was born as intended ("
       + c("network_side_born_right()") + "): not uid 0, PID 1 with parent 0 (its own PID namespace), "
       + c("PR_SET_PDEATHSIG") + " set, and fd 3, 4 and 5 of the right socket types, with the peer of fd 3 being the root "
       "side (" + c("SO_PEERCRED") + "). It then waits up to " + c("READY_WAIT_MS") + " (30 s) for the root side's "
       + c("READY") + ", which carries the codec probe's result, and exits if it does not come.", lead=True) + \
    p("<b>What it holds:</b> the TLS key and certificates, the QUIC secret, the ban table, the log secret, the RCP "
      "sessions and the attach slots, every WebTransport connection, the page server, and the table of the children's "
      "socket ends. <b>What it asks the root side for</b> goes over the closed list described next: a password check, "
      "the birth of a child, a signal to one of its own children, and the list of desktops found again.") + \
    p("<b>The walls</b> are put up by the root side in the fork, as root, right before the " + c("execve()")
      + ", by " + c("walls_apply()") + " in " + c("walls.c") + ". Any step that fails stops the start: there is no silent "
      "fallback to a network side without its walls.") + WALL_ORDER + \
    table(["Wall", "What it does", "Function or constant"], [
        ["PID namespace", "The network side is PID 1 of a new PID namespace with a /proc of its own: it sees no other process; "
         "when it dies the kernel kills everything it started", c("walls_fork_pidns()") + ", " + c("private_proc()")],
        ["Mount namespace", "The whole tree is read-only, nosuid and nodev, mounts are slaves of the host's; only "
         + c("/var/lib/remotix/net") + " and " + c("/run/remotix/net") + " are writable again, and noexec; a private "
         + c("/tmp") + " (tmpfs, 16 MiB) and a read-only " + c("/dev") + " with null, zero, full, random, urandom only",
         c("walls_apply()") + ", " + c("private_dev()") + ", " + c("set_attr()")],
        ["Network namespace", "A namespace of its own with only a raised loopback; the inherited sockets keep working; abstract "
         "Unix sockets of the host disappear. A Landlock scope on abstract sockets is added where the kernel has it "
         "(never fatal)", c("own_network()") + ", " + c("scope_abstract_sockets()")],
        ["Identity", "Bounding set dropped, " + c("setgroups(0)") + ", gid, " + c("RLIMIT_NPROC") + " = " + c("WALLS_NPROC_MAX")
         + " (128), uid, then read back with " + c("getresuid()") + " and " + c("/proc/self/status") + ": no capability of any "
         "kind is left", c("drop_bounding_set()") + ", " + c("nothing_left()")],
        ["No new privileges", c("PR_SET_NO_NEW_PRIVS") + " after the identity change, before the filter", c("walls_apply()")],
        ["seccomp", "A raw BPF filter, no libseccomp: no user namespace (EPERM), " + c("clone3") + " ENOSYS, sockets only "
         + c("AF_UNIX") + "/" + c("AF_INET") + "/" + c("AF_INET6") + "; io_uring ENOSYS; userfaultfd, perf_event_open, bpf, keyctl "
         "family, ptrace and the " + c("TIOCSTI") + "/" + c("TIOCLINUX") + " ioctls EPERM", c("no_user_namespaces()")],
        ["AppArmor", "If AppArmor is on and the profile " + c("remotix_network") + " is loaded, the root side writes "
         + c("exec remotix_network") + " to the exec attribute so that the " + c("execve()") + " enters it; with no AppArmor "
         "or no profile it logs a note and goes on. The profile ships in complain mode", c("apparmor_exec_net()") + ", "
         + c("debian/remotix_network.apparmor")],
    ], "«TAB» — The network side's walls") + \
    warn("The AppArmor profile is shipped with " + c("flags=(complain)") + ": it logs what it would refuse and refuses nothing. "
         "On the real Debian 13 virtual machine it was loaded in complain and in enforce mode with no denial up to the "
         "connection; that machine has no graphics card, so a session was not run under it. Under a full session the profile "
         "has not been observed (PIANO.md, 17 Nov 2026). The walls other than AppArmor were exercised by every check in "
         + c("prove/") + ", because the network side always runs behind them.", "AppArmor is not yet enforcing.") + \
    p("The network side keeps four threads (the main one, a pool spawner, " + c("gmain") + " and " + c("gdbus") + ", "
      "measured and noted next to " + c("WALLS_NPROC_MAX") + " in " + c("walls.h") + "); they are GLib's, started by the "
      "logind sentinel. It runs one " + c("ppoll()") + " loop whose timeout is the smallest of the transport's next timer "
      "and the page's, at most one second (" + c("main()") + ").")

# ── The closed list ──────────────────────────────────────────────────────
S5 = p("Everything the network side may ask of the root side crosses one " + c("SOCK_SEQPACKET") + " socket pair with "
       + c("SO_PASSCRED") + " on both ends, made by the root side before the fork (fd 3 in the network side). The list "
       "is closed and is in " + c("rootside_proto.h") + "; Appendix A has every message. The rules are in the header and "
       "in the validator " + c("rootside_check_packet()") + ":", lead=True) + \
    table(["Rule", "Detail"], [
        ["Exact length per kind", "Every message is one packet of exactly the size of its kind. A different length, an "
         "unknown kind, a wrong " + c("RXR_MAGIC") + " or " + c("RXR_VERSION") + " is not skipped: the root side logs it, "
         "closes the channel, kills the network side and starts it again (" + c("net_kill()") + ")"],
        ["The kernel's word, on every packet", "The root side checks " + c("SCM_CREDENTIALS") + " on every packet: uid "
         + c("remotix") + " and the pid of the network side it forked. The network side checks uid 0 and its parent pid"],
        ["Network side to root side", c("RXR_AUTH") + ", " + c("RXR_SPAWN") + ", " + c("RXR_CLOSE_ORPHAN") + ", "
         + c("RXR_SIGNAL") + ". Nothing else: a hijacked network side gains no new message"],
        ["Root side to network side", c("RXR_READY") + " (first, once), " + c("RXR_VERDICT") + ", " + c("RXR_SPAWNED") + " "
         "(with the child's socket end and a pidfd by " + c("SCM_RIGHTS") + "), " + c("RXR_SPAWN_REFUSED") + ", "
         + c("RXR_CHILD_EXITED") + ", " + c("RXR_FOUND_AGAIN") + ", " + c("RXR_FOUND_END") + ", " + c("RXR_FOUND_GONE")
         + ", " + c("RXR_CODEC") + ", " + c("RXR_LOCAL_COMING") + " (110: a local login of that user is held in PAM; "
         + rif("The local-login hold") + ")"],
        ["Names come from the root side", "The child's options (canvas, survey folder, quality switches, card route) come "
         "from the root side's own argument list, never from a request. A SPAWN names no user: it carries a one-time "
         "grant, and the user and address are those of the grant"],
        ["Grants", "A right password gets a 16-byte single-use grant bound to (user, address), valid " + c("RXR_GRANT_LIFE_MS")
         + " (30 s), kept in a table of " + c("ROOTSIDE_GRANTS_MAX") + " (32); a full table refuses to mint, it never "
         "overwrites"],
        ["Bounds before PAM", "At most " + c("RXR_AUTH_IN_FLIGHT_MAX") + " (16) AUTH in flight and " + c("RXR_AUTH_PER_S")
         + " (3) per second with a burst of " + c("RXR_AUTH_BURST") + " (8); above that the answer is “not checked”, not "
         "counted towards the ban. Names that are uid 0, in " + c("/etc/remotix/denied-users") + " or unknown are refused "
         "before PAM (" + c("rootside_user_refused()") + ")"],
        ["The root side's own pauses", "Three levels, from what PAM really refused: (uid, address) 5 in 5 minutes, "
         "address 20 in 5 minutes (both then 15 min, 1 h, 12 h), uid alone 15 in 5 minutes (a fixed 15 min); "
         "they live in the root side's memory and are lost at its restart (" + c("rootside_login_admit()") + ")"],
        ["CLOSE_ORPHAN", "A birth without a password, for a desktop found again, allowed only when logind shows a live "
         + c("remotix") + " session of that uid, no child exists for it, and it has been without a child for the abandonment "
         "time; one per uid per " + c("ROOTSIDE_ORPHAN_UID_MS") + " (30 s) and 2 per second with a burst of 5"],
    ], "«TAB» — The rules of the channel between the two sides") + \
    p("The structs are sent as they are, the two sides being the same binary; the sender zeroes the whole struct "
      "first so that no padding byte carries stack. The order of the desktops-found-again events is part of the "
      "protocol: " + c("RXR_READY") + ", then N times " + c("RXR_FOUND_AGAIN") + ", then one " + c("RXR_FOUND_END") + " whose "
      "count is N, and only after it any " + c("RXR_FOUND_GONE") + "; the network side treats any other order as a broken "
      "channel (" + c("rootside_found_step()") + "). The login rules that sit behind this table are in "
      + rif("Login and its defences") + ".")

# ── PAM helper ───────────────────────────────────────────────────────────
S6 = p("Checking a password is the one thing the server needs root for besides changing user, and PAM can take "
       "one to two seconds (the delay is added by PAM's failure delay, measured on 11 August 2026). The PAM helper "
       "exists so that this wait is never in a loop that delivers frames, and so that PAM, which is not reliably "
       "reentrant, is never used twice in one process.", lead=True) + \
    table(["Storey", "Process", "What it does"], [
        ["1", "The root side", "Never calls PAM. " + c("helper_ask_bare()") + " writes the request on a socket and returns "
         "at once; the answer arrives in the loop (" + c("helper_move()") + ")"],
        ["2", "The dispatcher (" + c("--pam-helper") + ")", "Started once; re-executed (" + c("execve()") + " of "
         + c("/proc/self/exe") + ") so that its image holds no key or secret; closes every descriptor above 3; reads a "
         "request and forks. Named " + c("remotix-pam") + " in " + c("ps")],
        ["3", "The check", "A forked process that calls PAM once (" + c("pam_start()") + " with the service " + c("remotix")
         + ", then authenticate and account), writes one byte and exits"],
    ], "«TAB» — The three storeys of the PAM helper") + \
    p("<b>A failure is a refusal.</b> The only way to a yes is the byte " + c("1") + " written by the check after both PAM "
      "steps succeeded; any other byte, a short answer, a silence, a dead dispatcher or a full queue is a no. The socket "
      "is " + c("SOCK_SEQPACKET") + " so an answer can neither arrive halfway nor merge with another. The numbers are in "
      + c("helper.c") + ": " + c("MAX_IN_FLIGHT") + " = 16 requests in flight (an address not known to " + c("rcp.c")
      + " gets " + c("MAX_IN_FLIGHT") + " minus " + c("RESERVED_FOR_KNOWN") + " = 14), " + c("EXPIRY_MS") + " = 8000 ms "
      "before a request is called a no, " + c("GRANDCHILD_ALARM_S") + " = 20 s after which a check kills itself. "
      "A dead dispatcher is started again after 1 s, 2 s, 4 s … up to " + c("RESTART_CAP_MS") + " (60 s); a dispatcher "
      "that lived " + c("STABLE_MS") + " (60 s) resets the count. While it is down, logins are refused and not counted "
      "towards the ban.") + \
    p("<b>The password's journey.</b> It exists in the network side (the RCP buffer, zeroed after use), in one packet "
      "of the closed list (" + c("RXR_PASSWORD_MAX") + " = 1025 bytes in " + c("struct rxr_auth") + "), in the root "
      "side's request to the dispatcher and in the check. Each copy is zeroed as soon as it has served; the in-flight "
      "tables keep the name and address, never the password. A second net sits in " + c("rcp.c") + ": a session still "
      "waiting for a verdict after " + c("VERDICT_CAP") + " (12 000 ms) is refused, so that it cannot hang on a silence "
      "(" + rif("Login and its defences") + ").")

# ── The child ────────────────────────────────────────────────────────────
S7 = p("For every admitted user the root side forks one child that becomes that user. Two facts, measured on 12 August "
       "2026, force the split: root does not connect to the user's session bus (no bus, no capture), and only root can "
       "check another user's password. The child is born by " + c("child_birth()") + " in " + c("child.c") + ", in this order:",
       lead=True) + \
    table(["Step", "What happens in the fork (as root)"], [
        ["1", "The name is resolved by the root side, once, with " + c("getpwnam_r()") + "; uid 0 is refused; the uid that "
         "results is the one the kernel must stamp on every message from the child"],
        ["2", "First connection only: the user is enrolled in the groups that own the card's render nodes with "
         + c("usermod -aG") + " (bounded by " + c("RUN_AS_ROOT_MAX_MS") + " = 5000 ms) and the enrolment is appended to "
         + c("/var/lib/remotix/group-enrollments.jsonl") + ". On GNOME and KDE, where a user manager already runs with old groups, a card "
         "ACL for the user's private group is added (" + c("render_grant_add()") + ")"],
        ["3", "A socket pair; fork; in the fork " + c("close_range()") + " leaves only 0, 1, 2 and the child's socket end"],
        ["4", "The PAM session, opened by the child itself before it drops privileges: " + c("pam_start()") + ", "
         + c("XDG_SESSION_TYPE=wayland") + ", " + c("XDG_SESSION_CLASS=user") + ", the client's address as " + c("PAM_RHOST")
         + ", no seat, then " + c("pam_open_session()") + " and " + c("pam_end()") + " <i>without</i> " + c("pam_close_session()")
         + ". The logind session belongs to the process that holds the session's fifo, so the fifo's descriptor is carried "
         "across the " + c("execve()") + " with " + c("--session-fd") + " (17 Nov 2026)"],
        ["5", c("setgroups()") + ", " + c("setgid()") + ", " + c("setuid()") + ", then " + c("getresuid()") + " and "
         + c("getresgid()") + " read back; any difference exits with 34-36"],
        ["6", "The environment is composed from scratch (" + c("HOME") + ", " + c("USER") + ", " + c("LOGNAME") + ", "
         + c("PATH") + ", an empty " + c("SHELL") + ", " + c("XDG_RUNTIME_DIR") + ", " + c("DBUS_SESSION_BUS_ADDRESS")
         + "). <b>" + c("PATH") + "</b> is the one that PAM composed, if there is one: the session's PAM stack runs " + c("pam_env") + ", which reads "
         + sysf("/etc/environment") + ", and what it composed is taken as it is. A " + c("PATH") + " from PAM is "
         "accepted only if it is a list of absolute folders with no " + c("..") + " component, made of plain characters and at most "
         "400 long (" + c("child_path_ok()") + "). On Debian " + sysf("/etc/environment") + " is empty by default, so the usual case is the fallback, " + sysf("~/.local/bin") + ":" + sysf("~/bin") + ":" + sysf("/usr/local/bin") + ":" + sysf("/usr/bin")
         + ", which is what a local graphical login has in front of the system folders; the shorter list " + c("/usr/local/bin:/usr/bin:/bin") + " is used only if the user's home has a colon in it. "
         "The " + c("remotix.pam") + " stack has no " + c("user_readenv") + " on purpose: the user would choose the " + c("PATH") + " of their own session from " + sysf("~/.pam_environment") + ". "
         "<b>Language.</b> " + c("LANG") + " is the user's own choice (" + c("Languages=") + " or the older " + c("Language=") + " in AccountsService, the first item counting), else the system's ("
         + sysf("/etc/default/locale") + ", which the second " + c("pam_env") + " line of " + c("remotix.pam") + " puts in the PAM environment), plus the system's " + c("LC_*") + " and "
         + c("LANGUAGE") + " (up to " + c("CHILD_LOCALE_MAX") + " = 12 words). The AccountsService file belongs to root and is read <i>before</i> the "
         "change of identity (" + c("child_locale_read()") + "); every value is checked for plain characters, and " + c("session.c") + " still checks that the "
         "locale exists and is UTF-8, otherwise it falls back to " + c("C.UTF-8") + ". Before 1.2.0 the language was always " + c("C.UTF-8") + ". "
         "Every signal goes back to default, and " + c("execve()") + " of " + c("remotix-child --internal-child") + " with "
         "the user, uid, gid, canvas, serial and switches on the command line"],
    ], "«TAB» — The birth of a child") + \
    p("The new image runs " + c("child_alive()") + ": it logs its identity, re-checks " + c("getresuid()") + " (a mismatch "
      "exits 42, “I am not who I should be”), arms " + c("PR_SET_PDEATHSIG") + " and the end-of-file on the socket as two "
      "independent ways to die with the server, introduces itself with " + c("MSG_INTRO") + " and mounts the stage "
      "(" + c("take_stage()") + "). The parent gives it " + c("SHOW_UP_DEADLINE_MS") + " (15 s) to introduce itself; after that "
      "there is no deadline, because a stage that is silent because nobody asks it anything is doing its job (invariant I4). "
      "Every minute the parent asks “who are you” again (" + c("RECHECK_MS") + ", " + c("MSG_CHI_SEI") + "), and a child that "
      "has sent nothing for " + c("WHOAMI_DEADLINE_MS") + " (600 s) after the question is killed. A child may also tell the parent "
      "that the graphical session is over <i>before</i> it dismantles its stage (" + c("session_over_early()") + "); the parent "
      "then keeps it as “closing” for " + c("CLOSING_GRACE_MS") + " (30 s) so that a login in the meantime is refused with the "
      "truth (" + rif("When the session ends before the stage is gone") + ").") + \
    p("<b>A stage the child refuses.</b> " + c("MSG_STAGE") + " ends with a " + c("fatal") + " field (" + c("struct body_stage")
      + "; a parent also accepts the older, shorter body, " + c("STAGE_MIN") + ", and reads it as “not fatal”). Only the refusal "
      "for the screen scale (guard 2: on Mutter, the scale of the stage's monitor is not 1 and one temporary attempt to bring it "
      "back with " + c("mutter_scale_to_one()") + " failed) sets it. The hook " + c("children_hook_stage_refused()") + " then reaches "
      + c("stage_refused_by_child()") + " in " + c("main.c") + ", which sends " + c("0x0E") + " to the clients "
      "(" + c("wt_dismiss_user_session_over()") + "), and the child closes the session (" + rif("When the session ends before the stage is gone")
      + ").") + \
    p("<b>The close-only child.</b> A desktop found again may have no client and no password to start a child with. "
      "The root side then starts a child with " + c("--close-only") + " (a " + c("RXR_CLOSE_ORPHAN") + " birth): no stage, no "
      "frame, no input; it obeys only “end the session” and leaves after " + c("CLOSE_ONLY_LIFE_MS") + " (30 s) if none "
      "comes (" + rif("Ending a graphical session") + ").") + \
    tip("The child is an <code>execve()</code> and not a bare <code>fork()</code> for three reasons: the parent's memory "
        "holds the TLS key (in the split server, the network side's; in the root side, the ban and grants), and "
        "<code>/proc/self/mem</code> belongs to the owner of the process; the environment is then composed variable by "
        "variable; and the child uses PipeWire and GLib threads, which a fresh image makes irrelevant to the fork.",
        "Why exec.")

# ── The channel with a child ─────────────────────────────────────────────
S8 = p("The network side and a child talk over a " + c("SOCK_SEQPACKET") + " pair created at the fork. The kernel keeps message "
       "boundaries and, with " + c("SO_PASSCRED") + ", stamps every message with the sender's real pid, uid and gid "
       "(" + c("SCM_CREDENTIALS") + "). " + c("SO_PEERCRED") + " would be the wrong tool: on a " + c("socketpair()")
       + " it holds the credentials of the process that created the pair, on both ends. Both ends check: the child "
       "discards a message not stamped with the network side's uid (" + c("--parent-uid") + "), and the network side "
       "checks the stamp against the child's uid (" + c("child_credentials_ok()") + ") and, where the kernel gives it, the "
       + c("pidfd") + " the root side handed over (" + c("child_credentials_pidfd_ok()") + ").", lead=True) + \
    table(["Field", "Type", "Value"], [
        [c("magic"), "4 bytes", c("FIG1")],
        [c("kind"), "u16", "the message type, " + c("MSG_*") + " in " + c("child.c")],
        [c("version"), "u16", c("CHILD_VERSION") + " = 1"],
        [c("serial"), "u64", "the child's serial number, given by the root side"],
        [c("declared_uid"), "u32", "the uid the sender believes the child has; compared with the kernel's stamp"],
        [c("byte"), "u32", "bytes of body after the header (24 bytes of header in all)"],
    ], "«TAB» — The header of every message between the network side and a child (struct head)") + \
    p("The twenty message kinds are listed in Appendix A (" + rif("Appendix A — Data structures and messages") + "). Large "
      "payloads (frames, cursor images, clipboard text) travel in pieces of at most " + c("MAX_PIECE") + " = 32 768 bytes "
      "with total, offset and piece length, and are reassembled on the other side; a table per kind, because the three "
      "arrive interleaved. A frame's " + c("input") + " field is written by the child at capture time: only the child "
      "knows which input the compositor had received. If the socket is full an audio block is dropped, not waited for: "
      "late audio must not stop the capture.")

# ── The sentinel ─────────────────────────────────────────────────────────
S9 = p("The sentinel answers questions for which logind is the authority, through the <b>system</b> bus, in " + c("sentinel.c")
       + ". It is synchronous with a short wait because a thread and a mutex would cost more in a server that keeps one "
       "loop by choice.", lead=True) + \
    table(["Question", "Function", "Asked by", "Used for"], [
        ["Does this user have a local graphical session now?", c("sentinel_local3()") + " (the two-valued "
         + c("sentinel_local()") + " is still in the file but no longer called)",
         "the network side at " + c("ATTACH") + " and before a birth; the child before a logout",
         "refusing with " + c("0x05 ALREADY_ACTIVE_LOCALLY") + "; the answer has three values and “could not look” "
         "refuses too (fail-closed)"],
        ["Which of these users have one?", c("sentinel_locals()"), "the network side, every " + c("LOCAL_SWEEP_MS") + " (2000 ms)",
         "dismissing a remote client with " + c("0x04 LOCAL_SESSION_PREVAILED")],
        ["Is my session without a seat?", c("sentinel_without_seat()"), "the child, after startup",
         "proving the session is headless; also the proof that the child's scope is not the local desktop's"],
        ["Is power-off really forbidden?", c("sentinel_shutdown_forbidden()"), "the child",
         c("CanPowerOff") + ", " + c("CanReboot") + ", " + c("CanSuspend") + ", " + c("CanHibernate") + " must all say " + c("no")
         + " or " + c("na") + " (“not available on this machine”, as on a virtual machine or a server). Any error is “not "
         "safe”, and the detail names the call and the error"],
        ["Close one remote session", c("sentinel_terminate_remote_session()"), "only the single-process mode, for a "
         "desktop found again whose user has a local session (" + c("found_again_close_for_local()") + " in " + c("main.c") + ")",
         "logind " + c("TerminateSession") + ", only for a session that is certainly REMOTIX's. In the split server the "
         "network side does not attempt it (it is not root): the desktop leaves the list, and the root side ends its "
         "scope by itself (" + c("localx_sweep()") + ", " + rif("Local excludes remote and the session cap") + ")"],
    ], "«TAB» — What the sentinel is asked") + \
    p("<b>A local session is one with a seat.</b> The obvious criterion (graphical type, not remote) would refuse REMOTIX "
      "itself: REMOTIX's own sessions are created without a seat, and a seat is what separates a real screen from a "
      "headless one. The numbers: the question at " + c("ATTACH") + ", before a birth and before a logout ("
      + c("sentinel_local3()") + ") waits at most " + c("FAIL_CLOSED_WAIT_MS") + " (1000 ms) and is asked a second time "
      "before it answers “could not look”; the periodic one waits " + c("WAIT_MS") + " (300 ms), and an answer older than "
      + c("ANSWER_MAX_AGE_MS") + " (7000 ms) is not used. " + c("ATTACH_WAIT_MS") + " (100 ms) and " + c("SILENT_BACKOFF_MS")
      + " (30 s) belong to the two-valued " + c("sentinel_local()") + ", which no caller uses any more. The periodic check asks logind once for all users, not once "
      "per user (the cost measured on 25 August 2026 grew with the number of tenants), and does not wait for the answer: "
      "it uses the previous round's.") + \
    note("The power-off check runs in the child, never in the root side: root is always answered yes because logind "
         "looks at " + c("CAP_SYS_BOOT") + " before polkit.", "Asked from the right place.") + \
    p("If logind does not answer, the periodic check dismisses nobody: “I do not know” must not close the session of a "
      "user who did nothing wrong (I1). If the system bus cannot be opened at startup, the periodic half is not "
      "connected and the log says so. The question asked at " + c("ATTACH") + ", before a birth and before a logout is "
      "fail-closed and refuses when in doubt (" + c("ask_local_session()") + " and " + c("local_three()") + " in " + c("main.c")
      + "): it protects the user's local desktop from a remote session and from a remote logout (" + rif("Security model") + ").")

# ── Loops and threads ────────────────────────────────────────────────────
S10 = p("Each process has its own loop. Only the network side and the child have threads, and they are the libraries' or "
        "narrow helpers.", lead=True) + \
    table(["Process", "Loop", "Threads", "Notes"], [
        ["Root side", c("poll()") + " over the self-pipe, the channel and the PAM dispatcher; 1000 ms", "one, by design",
         "no GLib, no blocking call except the card probe's wait in its own fork"],
        ["Network side", c("ppoll()") + " over the UDP socket, the page's sockets, the command socket if " + c("--command-socket") + " is given (the unit does not give it), and the root "
         "channel; at most 1000 ms; SIGCHLD wakes it", "four (GLib and GDBus)", "no blocking call except the sentinel's "
         "short waits and the SPAWN wait of " + c("SPAWN_WAIT_MS") + " (15 s)"],
        ["PAM dispatcher", "blocking " + c("recv()"), "one", "forks per request"],
        ["Child", c("poll()") + " on the socket, the libei descriptor and a self-pipe; 1000 ms idle, 0 while capturing, at "
         "most 5 ms while audio is on", "see below", "captures, encodes and sends in the same thread"],
    ], "«TAB» — The loops") + \
    table(["Thread", "Where", "What it does"], [
        [c("remotix-cattura"), c("capture.c"), "PipeWire thread loop of the video stream; the child's loop takes the frame "
         "with a wait of at most " + c("MOTION_WAIT_S") + " (8 ms)"],
        [c("remotix-suono"), c("sound.c"), "PipeWire thread loop of the audio sink"],
        [c("remotix-appunti"), c("clipboard.c") + " (GNOME), " + c("clipboard_kde.c") + " (the other desktops)",
         "the clipboard: a GLib main loop on GNOME, a Wayland data-control pump elsewhere"],
        [c("remotix-kwin"), c("kwin.c"), "pumps KWin's Wayland connection"],
        [c("powerdevil"), c("session.c"), "on KDE, a short-lived guard that waits for PowerDevil and asks it to inhibit"],
    ], "«TAB» — The threads of a child") + \
    p("The encoder runs synchronously in the child's loop: capture, encode, send, then the next frame. Encoding frame N while "
      "capturing N+1 would raise the frame rate and add delay, and SPECS §3.2 forbids that trade.")

# ── State ────────────────────────────────────────────────────────────────
S11 = p("Each piece of state has one owner and one lifetime. Two of them are deliberately held on both sides of the "
        "channel, and the table says so.", lead=True) + \
    table(["State", "Owner", "Lives", "Notes"], [
        ["Certificates and fingerprint", c("certificates.c") + " (network side)", "files in " + c("/var/lib/remotix/net/certificates")
         + ", rotated while running (checked every 60 s in " + c("main()") + ")", rif("Transport")],
        ["QUIC secret, log secret", c("rcp.c") + ", " + c("transport.c") + " (network side)", "files " + c("quic-secret") + ", "
         + c("log-secret") + " in the certificates folder, mode 0600", "the log secret keys the tags of unknown user names"],
        ["The address ban", c("rcp.c") + " (network side)", "memory and the file " + c("/var/lib/remotix/net/ban")
         + ": survives restarts", rif("Login and its defences")],
        ["The root side's pauses", c("rootside.c"), "root side memory only", "lost at its restart (Appendix A)"],
        ["RCP sessions and attach slots", c("rcp.c"), "one session per connection; a slot per user while attached",
         rif("The RCP/1 protocol")],
        ["Children: two tables", c("child.c") + " (network side) and " + c("struct own_child") + " (root side)",
         "a slot per user while the child lives", "the root side's is the truth about who exists and reaps it; the network "
         "side's holds the socket and the identity checks"],
        ["Grants: two tables", c("struct rootside_grant") + " and the network side's table", "from VERDICT to SPAWN, at most 30 s",
         "wiped at every network side start"],
        ["Presence table (abandonment clock)", c("main.c"), "a slot per user from their first input to the end of their stage",
         "sized on the cap; survives clients"],
        ["Desktops found again", c("main.c") + " and " + c("struct found_slot") + " in " + c("rootside.c"),
         "from startup until the user returns, the desktop dies or the root side ends it (a few seconds)", "at most " + c("MAX_FOUND_AGAIN") + " (256)"],
        ["The budget's accounts", c("budget.c"), "per user", rif("Quality, degradation and budget")],
        ["Card ACL record, enrolments", c("render_grant.c") + ", " + c("child.c") + " (root)", c("/var/lib/remotix/render-grants")
         + ", " + c("/var/lib/remotix/group-enrollments.jsonl"), "root-owned, never writable by " + c("remotix")],
        ["The stage: capture, encoders, input, clipboard", "the child", "as long as the child", "statics of " + c("child.c")
         + ": one stage per process"],
        ["The desktop and the user's programs", "the compositor", "until logout, abandonment, a local login of that user "
         "or a stop of the service", "survives clients and a network side that dies for a few seconds; an orderly stop of "
         "the service closes it"],
    ], "«TAB» — Where state lives") + \
    p("<b>One number for the cap.</b> " + c("RCP_SESSION_CAP") + " (10) in " + c("rcp.h") + " is the default, " + c("--session-cap N")
      + " moves it at startup, and " + c("rcp_cap()") + " is read once by every table that counts users: the attach slots of "
      + c("rcp.c") + ", the children of " + c("child.c") + ", the presence table of " + c("main.c") + ", the root side's "
      "children and the budget's cells. The root side's children table is sized on the cap handed to it in " + c("struct rootside_options") + ". "
      "The default of 10 is a technical value; the <b>declared</b> limit of the product (owner's decision, "
      + c("DECISIONS-11") + " §11.51, confirmed 18 Nov 2026) is <b>8 users</b> at the same time.") + \
    tip("the cap counts <b>stages</b>, not connections: a user who closed the browser still holds a stage until logout or "
        "abandonment. " + c("stage_count()") + " adds the children and the desktops found again; a new user who finds them "
        "all taken is refused with " + c("0x0E SESSION_UNSERVABLE") + " before any process is forked.", "Stages, not connections.")

CHAPTER = ("Overall architecture", [
    ("The roles of the server executable", S1),
    ("Process tree and privileges at a glance", S2),
    ("The root side", S3),
    ("The network side and its walls", S4),
    ("The closed list between the two sides", S5),
    ("The PAM helper", S6),
    ("The per-user child", S7),
    ("The channel between the network side and a child", S8),
    ("The logind sentinel", S9),
    ("Event loops and threads", S10),
    ("Where state lives, owner by owner", S11),
])
