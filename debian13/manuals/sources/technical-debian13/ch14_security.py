from build import arrow, box, c, fig, note, p, rif, steps, table, text, ul, warn, zone

# ── 14.1 Trust boundaries ────────────────────────────────────────────────
ZONES = fig(
    zone(20, 12, 210, 290, "Network")
    + box(36, 56, 178, 54, "Browser", "page + WebTransport", "dark")
    + box(36, 200, 178, 54, "Anyone else", "may knock, may be banned", "grey")
    + zone(250, 12, 250, 290, "Network side (uid remotix)")
    + box(266, 50, 218, 58, "TLS, QUIC, the page", "limiter, ban table", "blue")
    + box(266, 130, 218, 58, "Walls + AppArmor", "no capability, own namespaces", "amber")
    + zone(520, 12, 360, 290, "root")
    + box(536, 50, 328, 54, "Root side", "PAM bounds, denied list, birth of desktops", "navy")
    + box(536, 128, 328, 48, "PAM dispatcher and grandchildren", "root, one transaction each", "dark")
    + box(536, 200, 328, 54, "Per-user child, then uid of the user", "setgid, setuid, PAM session", "light")
    + arrow(216, 80, 264, 80, "#003a90", label="TLS 1.3", lx=240, ly=70)
    + arrow(484, 80, 534, 80, "#0050C0", label="closed list", lx=509, ly=70)
    + arrow(700, 106, 700, 126, "#475569")
    + arrow(700, 178, 700, 198, "#475569"),
    900, 310, "«FIG» — Trust boundaries of the packaged service: what faces the network, what is root, what is the user")

S1 = p("REMOTIX has two security levels and no third (" + c("SPECS.md") + " §4.1): the transport, so that nobody "
       "reads or rewrites what passes, and the access, that is address, port, user name and password checked by the "
       "machine's own PAM. The rest of this chapter is about what happens if something in the first process that "
       "touches the network is wrong. The packaged service is split in two for that reason (the shape is in "
       + rif("Overall architecture") + "); the login itself is in " + rif("Login and its defences") + ".",
       lead=True) + ZONES + \
    table(["Process", "Runs as", "Holds", "Is confined by"], [
        ["Network side", "System user " + c("remotix") + " (" + c("remotix.sysusers") + "), no groups",
         "The UDP and TCP sockets it was handed (descriptors 4 and 5), TLS keys, the ban table, the log secret, "
         "the page. Writes only in " + c("/var/lib/remotix/net") + " and " + c("/run/remotix/net") + ".",
         "The walls of " + c("walls.c") + " and the AppArmor profile " + c("remotix_network") + " (complain mode)."],
        ["Root side (the unit's main process)", "root", "The PAM helper, the render-grant record, the channel to "
         "the network side, the right to start a child as any user.", "Nothing: no profile, no unit hardening."],
        ["PAM dispatcher and grandchildren", "root", "One PAM transaction each; the typed password for its duration.",
         "A 20 s alarm; a fresh memory image (re-executed, not forked from the server)."],
        ["Per-user child", "Born as root for PAM and logind, then the user's uid and gid (" + c("setgid()") + " then "
         + c("setuid()") + ", read back with the kernel)", "The user's session bus, capture, input, the user's "
         "desktop.", "Ordinary Unix permissions of that user."],
        ["Desktop session", "The user", "The compositor and the user's programs.", "As for any local login of that "
         "user; the polkit rules below."],
    ], "«TAB» — The processes of the packaged service and their power") + \
    p("The principle is that root does only what needs root: verifying anyone's password, and descending to anyone's "
      "uid. Everything that faces the internet runs without it. The desktops are not behind the walls: their children "
      "are forked by the root side, never from the network side, so that for example " + c("sudo apt install")
      + " in a remote desktop keeps working (" + c("walls.h") + ").")

# ── 14.2 The closed list ─────────────────────────────────────────────────
S2 = p("The root side and the network side talk over one " + c("SOCK_SEQPACKET") + " socket pair with "
       + c("SO_PASSCRED") + ", created by the root side before it forks the network side (descriptor 3 there). "
       "The messages are a closed list in " + c("rootside_proto.h") + "; nothing else crosses.", lead=True) + \
    table(["Direction", "Kinds", "Notes"], [
        ["Network side to root side", c("AUTH") + ", " + c("SPAWN") + ", " + c("CLOSE_ORPHAN") + ", " + c("SIGNAL"),
         "Nothing else. The only descriptor that ever crosses back is the child's socket end, by " + c("SCM_RIGHTS")
         + "."],
        ["Root side to network side", c("READY") + " (once, first), " + c("VERDICT") + ", " + c("SPAWNED") + ", "
         + c("SPAWN_REFUSED") + ", " + c("CHILD_EXITED") + ", " + c("FOUND_AGAIN") + ", " + c("FOUND_END") + ", "
         + c("FOUND_GONE") + ", " + c("CODEC") + ", " + c("LOCAL_COMING"),
         "<b>" + c("LOCAL_COMING") + " (110, " + c("RXR_LOCAL_COMING") + ")</b> carries the uid and the user name of a user whose "
         "local login is held in PAM (" + rif("The local-login hold") + "); " + c("RXR_VERSION")
         + " is still 3. The order READY, N × FOUND_AGAIN, one FOUND_END with the count N, then any FOUND_GONE is part of the "
         "protocol; any other order is a broken channel."],
    ], "«TAB» — The messages between the two sides (" + c("enum rxr_kind") + ")") + \
    ul([
        "<b>Exact sizes.</b> Every message is one packet of exactly the size of its kind (" + c("size_of_request()")
        + "). A different length, an unknown kind, a wrong magic (" + c("RXR_MAGIC") + ") or version ("
        + c("RXR_VERSION") + " = 3) is not skipped: " + c("rootside_check_packet()") + " refuses it, the root side "
        "logs it, closes the channel, kills the network side and starts it again.",
        "<b>Kernel credentials on every packet.</b> The root side checks " + c("SCM_CREDENTIALS") + ": uid = "
        + c("remotix") + " and pid = the network side it forked. The network side checks uid 0 and its own parent.",
        "<b>Options come from the root side.</b> Every option of a child (canvas, card, encoding route, session cap) "
        "comes from the root side's own command line, never from a request of the network side.",
        "<b>A birth needs a grant.</b> A right password mints a single-use grant bound to (user, address), valid "
        + c("RXR_GRANT_LIFE_MS") + " = 30 s (" + c("rootside_grant_mint()") + ", " + c("rootside_grant_take()")
        + "). The SPAWN presents it, and the name is checked again against the denied list, uid 0 and NSS ("
        + c("birth()") + ").",
        "<b>CLOSE_ORPHAN is a birth without a password</b>, so it has its own limits: " + c("ROOTSIDE_ORPHAN_PER_S")
        + " = 2 per second with a burst of " + c("ROOTSIDE_ORPHAN_BURST") + " = 5, one per uid per "
        + c("ROOTSIDE_ORPHAN_UID_MS") + " = 30 s, only if logind shows a live session of that uid whose PAM service "
        "is " + c("remotix") + ", and only if the root side's own abandonment clock says the desktop was really "
        "abandoned.",
        "<b>Signals go only to the root side's own children,</b> and a child is reaped by the root side, which "
        "then tells the network side.",
    ]) + \
    p("The logic of the list is that a hijacked network side is the attacker the root side is built against. The "
      "list gives it no message that reads a file, runs a command, names a uid or chooses an option. What it can "
      "still do is ask for a login with a password it guesses (bounded, see " + rif("Login and its defences")
      + ") and ask for the birth of a desktop for a user whose password it knows.")

# ── 14.3 Walls ───────────────────────────────────────────────────────────
S3 = p("The walls are put up by the root side in the fork that is about to " + c("execve()") + " the network side, "
       "still as root, by " + c("walls_apply()") + " in " + c("walls.c") + ". The order is part of the design (each "
       "step needs the power the next one takes away), and any step that fails makes the root side refuse to start "
       "the network side: a network side without its walls is the unprotected server with extra steps, and that "
       "must never happen silently.", lead=True) + \
    table(["#", "Wall", "How", "Function or constant"], [
        ["1", "PID 1 of its own PID namespace, with a " + c("/proc") + " of its own",
         "The fork is a raw " + c("clone") + " with " + c("CLONE_NEWPID") + "; it lists itself only: no desktop, "
         "no root-side process. When it dies the kernel kills everything it started.",
         c("walls_fork_pidns()") + ", " + c("private_proc()")],
        ["2", "AppArmor profile, entered before the tree goes read-only",
         "Writes «exec remotix_network» into " + c("/proc/thread-self/attr/apparmor/exec") + "; off or not loaded is "
         "said and tolerated, a refused write is fatal (see the next section).", c("apparmor_exec_net()")],
        ["3", "A mount namespace where the whole tree is read-only, nosuid and nodev",
         c("mount_setattr()") + " by number (kernel 5.12 or later); mounts made slaves of the host's; the state "
         "folder and the run folder are bound onto themselves first so they can be made writable again, and "
         + c("noexec") + ". The result is read back with " + c("statvfs()") + ".", c("walls_apply()")],
        ["4", "Private " + c("/tmp") + " and " + c("/dev"), "A 16 MB " + c("tmpfs") + " for " + c("/tmp") + " ("
         + c("mode=1777") + ", nosuid, nodev, noexec); a read-only " + c("tmpfs") + " for " + c("/dev") + " with "
         "only " + c("null") + ", " + c("zero") + ", " + c("full") + ", " + c("random") + ", " + c("urandom") + ".",
         c("private_dev()") + ", " + c("walls_devices[]")],
        ["5", "A network namespace of its own", "Loopback only, brought up; the inherited sockets keep working.",
         c("own_network()")],
        ["6", "No capability, no group, the identity of " + c("remotix"), "The bounding set is dropped, then "
         + c("setgroups(0)") + ", " + c("setresgid()") + ", " + c("RLIMIT_NPROC") + " = " + c("WALLS_NPROC_MAX")
         + " (128), " + c("setresuid()") + ". The identities are read back with " + c("getresuid()")
         + " and " + c("getresgid()") + ", and the capability sets from " + c("/proc/self/status") + ".",
         c("drop_bounding_set()") + ", " + c("nothing_left()")],
        ["7", c("PR_SET_NO_NEW_PRIVS"), "Set after the identity change and checked.", c("walls_apply()")],
        ["8", "Landlock scope for abstract Unix sockets", "Needs Landlock ABI 6 (kernel 6.12). On an older kernel it "
         "is not applied, the notes say so, and the start goes on: this wall is never fatal.",
         c("scope_abstract_sockets()")],
        ["9", "A seccomp filter written by hand in BPF",
         "Allows only the socket families " + c("AF_UNIX") + ", " + c("AF_INET") + ", " + c("AF_INET6")
         + " (others get " + c("EAFNOSUPPORT") + "); " + c("io_uring") + " and " + c("clone3") + " get " + c("ENOSYS")
         + "; " + c("userfaultfd") + ", " + c("perf_event_open") + ", " + c("bpf") + ", the key syscalls, "
         + c("ptrace") + ", " + c("process_vm_readv") + ", " + c("process_vm_writev") + ", " + c("kcmp") + ", "
         + c("pidfd_getfd") + " and the " + c("ioctl") + " requests " + c("TIOCSTI") + " and " + c("TIOCLINUX")
         + " get " + c("EPERM") + "; " + c("unshare") + " and " + c("clone") + " with " + c("CLONE_NEWUSER")
         + " get " + c("EPERM") + "; another ABI (x32, a foreign architecture) is refused whole. Only x86_64 and "
         "aarch64 are supported: on another architecture the network side is not started.",
         c("no_user_namespaces()")],
    ], "«TAB» — The walls of the network side, in the order they are put up") + \
    p("The root side writes one log line with what is actually in force (" + c("walls_in_force()") + ": the "
      "AppArmor state, the folder, the limits). The package check " + c("check-package.py") + " (first-start) "
      "confirms the process layout of a running service, one root side as root and one network side as "
      + c("remotix") + ", records " + c("CapEff") + ", " + c("NoNewPrivs") + " and " + c("Seccomp") + " from "
      + c("/proc/<pid>/status") + " of the network side, and checks the owner and mode of every file under "
      + c("/var/lib/remotix/net") + " (directories 700, secrets and the ban file 600). It records those three "
      "status values as evidence; it does not compare them against fixed expected numbers.") + \
    note("The state folder " + c("/var/lib/remotix/net") + " and the run folder " + c("/run/remotix/net")
         + " are created by tmpfiles (" + c("remotix.tmpfiles") + ") owned by " + c("remotix") + " with mode 0700. "
         "The root side's own state, " + c("/var/lib/remotix") + ", is root's and mode 0755: a "
         + c("remotix") + "-writable folder holding root's files would let a hijacked network side swap them.",
         "Who owns what.")

# ── 14.4 AppArmor ────────────────────────────────────────────────────────
S4 = p("The profile is " + c("debian/remotix_network.apparmor") + ", installed as " + c("/etc/apparmor.d/remotix_network")
       + " (a conffile) and loaded by the " + c("dh_apparmor") + " lines that debhelper adds to the postinst. "
       "<b>It ships in complain mode:</b> its flags are " + c("complain,attach_disconnected") + ", so it logs what it "
       "would refuse and refuses nothing. It has not been moved to enforce.", lead=True) + \
    p("<b>How a process enters it.</b> The profile has no attachment path. Executing " + c("/usr/libexec/remotix/remotix")
      + " never puts anything in it, so the root side, which runs the same program, and every desktop stay "
      "unconfined. Only the root side's fork, by writing " + c("exec remotix_network") + " to the process's AppArmor "
      "exec attribute right before its " + c("execve()") + " (what " + c("aa_change_onexec()") + " does, without the "
      "library), puts the network side in it (" + c("apparmor_exec_net()") + ").") + \
    table(["Allowed", "Detail"], [
        ["No capability", "No " + c("capability") + " line at all."],
        ["Files", "The binary and " + c("/usr/share/remotix") + " read; the XKB data read; " + c("/etc/machine-id")
         + " read; " + c("/var/lib/remotix/net") + " and " + c("/run/remotix/net") + " read, write and lock; the "
         "system bus, the journal sockets and logind's session files; selected " + c("/proc") + ", " + c("/sys")
         + " and " + c("/dev") + " entries (" + c("null") + ", " + c("urandom") + ", " + c("random") + ")."],
        ["Network", c("inet") + " and " + c("inet6") + " " + c("dgram") + " and " + c("stream") + ", " + c("unix")
         + " " + c("stream") + " and " + c("dgram") + ", and " + c("netlink raw") + " (marked in the profile as to be "
         "removed when proven unused; the seccomp filter of the walls already refuses " + c("AF_NETLINK") + ")."],
        ["Signals", "Receive from unconfined processes (the root side); send and receive among profile members."],
        ["Denied", c("deny ptrace") + ", " + c("deny mount") + ", " + c("deny unix addr=@*") + " (abstract sockets)."],
    ], "«TAB» — What the profile allows, in summary") + \
    p("<b>What was verified, and what was not.</b> " + c("PIANO.md") + " records, for 17 Nov 2026, a run on a "
      "real Debian 13 virtual machine: installation, the profile loaded in complain and then in enforce mode, "
      "0 denials up to the connection, restart, removal and purge without residue. The same record says the "
      "session could not be tried, because that virtual machine has no video card. <b>The profile has therefore never "
      "been observed during a session</b> (login, desktop birth, video, audio), neither in complain nor in "
      "enforce mode, and it must not be moved to enforce until it has, on a machine with a card, with zero "
      "unexpected audit lines through the functional checks. " + c("check-package.py") + " has an " + c("apparmor")
      + " check that tests that the profile text compiles and, when the interface exists, that it is loaded; "
      "in containers, which have no AppArmor interface, it answers BLOCKED.") + \
    note("The header of the profile now states the same facts (corrected on 17 Nov 2026): loaded in complain mode, 0 denials up to the "
         "connection on a Debian 13 virtual machine, no session tried there for lack of a video card. The rules for " + c("/proc")
         + " are still marked «not tried». Neither the header nor the machine run covers a session.", "State of the profile.") + \
    p("On removal, " + c("debian/remotix.postrm") + " writes the profile name to the kernel's " + c(".remove")
      + " file of AppArmor, so the profile leaves the kernel even if its file is already gone.")

# ── 14.5 Local excludes remote ───────────────────────────────────────────
S5 = p("The rule is that a user with an active local graphical session gets a refusal from REMOTIX and nothing alive. "
       "REMOTIX never mounts anything on a local desktop. The reason is practical and was measured: on GNOME the "
       "user's session bus is one and shared, and a child spawned for the same user finds the local Mutter and "
       "mounts a virtual monitor, input and the clipboard on it (" + c("DECISIONS.md") + " and the box above "
       + c("local_guard()") + " in " + c("child.c") + "). What counts as a local session is a session with a seat "
       "(" + c("sentinel_local()") + "), not logind's " + c("Remote") + " flag, which would make REMOTIX's own "
       "seatless sessions look local.", lead=True) + \
    table(["Defence", "Where", "When", "What happens"], [
        ["1, before birth", c("delivery_verdict()") + " in " + c("main.c") + " (" + c("local_three()") + ")",
         "After PAM said yes, before a child is spawned",
         "A local session: no child is born, the login gets " + c("0x05") + " " + c("ALREADY_ACTIVE_LOCALLY")
         + ", and any existing child of that user is closed lightly. Cannot verify (logind silent, no guard): "
         "refused with " + c("0x0E") + " (fail-closed)."],
        ["2, sweep and attach", c("local_children_round()"), "At attach, at the keep-alive check, and in a periodic "
         "round over the children that have no browser",
         "A live child whose user now has a local session is closed lightly; its logged-in clients receive "
         + c("0x04") + " " + c("LOCAL_SESSION_PREVAILED") + " (the local one wins)."],
        ["3, in the child", c("local_guard()") + " in " + c("child.c") + ", " + c("sentinel_local3()"),
         "Before every attempt to mount the stage (the first, retries, after a compositor channel closes)",
         "Answers 1 (local), 0 (surely none) or -1 (could not look); 1 and -1 both refuse: the child mounts "
         "nothing, starts no desktop and exits after a light close. -1 is asked once more after about one "
         "second before being decided."],
        ["4, at the local login", c("remotix-local-login") + " in PAM (" + c("local_login.c") + "), served by " + c("pl_step()") + " in " + c("rootside.c"),
         "While the local login is being opened, before the local desktop starts",
         "The user's REMOTIX desktop is closed completely first and the login goes on only afterwards (" + rif("The local-login hold") + ")."],
    ], "«TAB» — The four defences of " + c("0x05") + " and " + c("0x04")) + \
    p("Each of the first three defences is enough alone. The " + c("0x05") + " is sent only after PAM's yes, so whoever has no password "
      "learns nothing about the account, and only to the login that asked, because the other connections carrying "
      "the same name may be strangers. The decision to fail closed, so that a lookup that fails is a refusal and "
      "never a yes, is the owner's of 15 Nov 2026 according to the comments in " + c("main.c") + " and "
      + c("child.c") + ". A light close ends the REMOTIX desktop of that user without touching the local session; "
      "the details are in " + rif("Startup and life cycle") + ". A desktop found again, with no child, whose user now has a "
      "local session is not revived. The network side does not close it (it is user " + c("remotix") + ": " + c("found_again_close_for_local()")
      + " in " + c("main.c") + " logs “the root side ends its scope by itself”), and in the packaged (split) service the root "
      "side ends its scope within about ten seconds (" + c("localx_sweep()") + "); in the single-process mode (" + c("--no-split")
      + ", not packaged) the process itself is root and closes that session with logind's " + c("TerminateSession") + "; only if that fails "
      "is the stage left alone.") + \
    p("<b>The session cap answers " + c("0x0E") + ".</b> The default cap is " + c("RCP_SESSION_CAP") + " = 10 users "
      "served at once (" + c("rcp.h") + "; changed by " + c("--session-cap") + " at start-up, " + c("rcp_cap_set()")
      + "). Whoever does not fit gets " + c("0x0E") + " " + c("SESSION_UNSERVABLE") + " with the detail in the body. "
      "The cap is checked at two points: in " + c("delivery_verdict()") + " in " + c("main.c") + ", on the count of "
      "desktops, before a child is spawned, so a user who does not fit costs no process, no logind session and no "
      "compositor; and in " + c("slot_take()") + " in " + c("rcp.c") + ", on the registry of attached sessions, at "
      "the attach. It is deliberately not "
      + c("0x06") + " (no composition capacity left, which is the budget, see " + rif("Quality, degradation and budget")
      + ") and not " + c("0x0F") + " (this user already has a session): the person must be told that the table is full "
      "and not, falsely, that they are connected elsewhere. The cap is administrative, not a physical limit, and 10 is a technical default: the <b>declared</b> limit of the "
      "product (owner's decision, " + c("DECISIONS-11") + " §11.51, confirmed 18 Nov 2026) is <b>8 users</b> at the same time. "
      "Related: a second device of a user whose first client is alive gets " + c("0x0F") + " "
      + c("ALREADY_ACTIVE_REMOTELY") + "; a client silent for long enough is detached and does not hold the slot.")

# ── 14.5b The local-login hold ───────────────────────────────────────────
S5C = p("<b>The problem.</b> A user who has a REMOTIX desktop and then logs in at the machine starts a second graphical "
        "session of the same user. GNOME's login screen holds that login while the user has another graphical session that is "
        "active or online; SDDM and LightDM hold nothing, and the local desktop starts on the user manager and the bus that the "
        "remote one is still using (read in the sources on 18 Nov 2026: Plasma adopts the remote units and dies with them, the "
        "local " + c("xfce4-session") + " finds its bus name taken and leaves, so KDE and XFCE return to the login screen). The "
        "owner's order (" + c("DECISIONS-11") + " §11.57, 18 Nov 2026) is one rule for every desktop and display manager: "
        "<b>a local graphical login closes the user's remote desktop first</b>, completely, and goes on only after that.",
        lead=True) + \
    table(["Piece", "What it is"], [
        ["The hook", c("/usr/libexec/remotix/remotix-local-login") + " (mode 0755), built from " + c("src/local_login.c") + " with libc "
         "only. PAM runs it as root, inside the login's own stack, and the login waits for it."],
        ["The PAM line", c("session optional pam_exec.so quiet /usr/libexec/remotix/remotix-local-login") + " in " + c("/etc/pam.d/common-session")
         + ", put there by " + c("pam-auth-update") + " from the profile " + c("/usr/share/pam-configs/remotix") + " ("
         + rif("The PAM service file remotix.pam") + ", " + rif("Files the package installs") + ")."],
        ["The requests", c("/run/remotix/prelocal/") + ": a folder of root, mode 0700, made by the root side (not by tmpfiles). "
         "A request is an empty file named by the uid. The file " + c(".lock") + " in it is held with an exclusive lock for as long "
         "as the root side lives."],
        ["The message", c("RXR_LOCAL_COMING") + " (110), root side to network side: the uid and the user name of the user whose login is "
         "held (" + rif("The closed list between the network side and the root side") + ")."],
        ["The root side", c("pl_step()") + " and the " + c("PL_*") + " constants in " + c("rootside.c") + ": it serves the requests."],
    ], "«TAB» — The pieces of the local-login hold") + \
    p("<b>What happens, in order.</b>") + steps([
        "<b>The hook decides if the login is its business.</b> Only for " + c("PAM_TYPE=open_session") + " with " + c("XDG_SEAT")
        + " set, session class " + c("user") + " (or none), type " + c("wayland") + ", " + c("x11") + " or " + c("mir") + " (or none), "
        "a user that is not root, and a PAM service that is not " + c("remotix") + ". Everywhere else (ssh, a text console, "
        "REMOTIX's own sessions, and the closing of any session) it returns 0 at once. Cron never runs it: with "
        + c("Session-Interactive-Only: yes") + " the line is not in " + c("common-session-noninteractive") + ".",
        "<b>It looks for the root side.</b> The folder must belong to root and not be writable by others; the hook opens " + c(".lock")
        + " and, if a shared lock can be taken (nobody holds the exclusive one: the service is not running), it returns at once. "
        "No login waits for a service that is not there.",
        "<b>It leaves a request and waits.</b> It creates the empty file named by the uid and checks every 50 ms (the first look after 5 ms) "
        "whether the root side has removed it; every half second it also checks that the service is still there.",
        "<b>The root side sees the request</b> (inotify, and the folder is read every second). If a child of ours serves that uid, it "
        "sends " + c("RXR_LOCAL_COMING") + ": the network side sends the logged clients 0x04 and asks the child for the <i>full</i> "
        "close, the logout's road, because the local desktop has not started and must find a user manager with nothing of REMOTIX in it. "
        "The log line starts “local login of … HELD in PAM”.",
        "<b>If there is no child</b> (a desktop that nobody holds), or the order could not leave, or the child has not finished after "
        + c("PL_GRACE_MS") + " (13 s), the root side ends the scope itself with the machinery of the rule “no orphan desktops” "
        "(SIGTERM, SIGKILL after 3 s, the clean-up of what REMOTIX put in the user manager).",
        "<b>The login goes on.</b> When no child of that uid, no seatless REMOTIX session of that uid with processes and no ending in "
        "progress are left, the root side removes the file and the hook returns. At most " + c("PL_CEIL_MS") + " (20 s): then the file "
        "is removed anyway and the log warns that the desktop is still there.",
        "<b>New births are refused for a while.</b> While the login is held and for " + c("PL_HOLD_MS") + " (10 s) after the answer, a "
        "birth for that uid gets no child; the root side answers it as it does for a child that is still closing ("
        + c("RXR_REF_CLOSING") + ") and logs “SPAWN for … refused: a local login of uid N is being held”. Once the local session is "
        "in logind, the usual refusal (0x05) takes over.",
    ]) + \
    ul([
        "<b>It never makes a login fail.</b> The hook always exits 0, the PAM line is " + c("optional") + ", and the hook's own ceiling is "
        + c("LOCAL_CEIL_MS") + " = 25 s, above the root side's 20 s. Up to " + c("PL_MAX") + " (8) logins can be held at the same time.",
        "<b>The request is only a uid.</b> The folder is writable only by root; the root side reads logind's own files to decide "
        "what to end, and does so again just before the signal. Nothing in a request is believed beyond “look at this uid now”.",
        "<b>While the service stops</b> no request is served: every desktop is being closed anyway, and the hook returns when "
        "the root side exits.",
        "<b>The older defences stay as a second belt:</b> the sweep of the root side every 5 s (" + c("localx_sweep()")
        + ") and the network side's 2 s sweep (" + c("LOCAL_SWEEP_MS") + ").",
    ]) + \
    p("<b>The second rule, “no orphan desktops”</b> (" + c("DECISIONS-11") + " §11.56), uses the same machinery. A seatless REMOTIX session "
      "whose scope still has processes and whose user has no child of ours must not stay: while the service runs, the root side "
      "ends it when it is seen so in two scans in a row (" + c("LX_EVERY_MS") + " = 5 s), and at an orderly stop it ends whatever "
      "is left (" + rif("Stopping the service") + "). A user who comes back before the second scan gets a child, and a desktop "
      "with a child is not an orphan.") + \
    note("Where the rest is: the log lines in " + rif("Logging and diagnostics") + ", the files and maintainer scripts in "
         + rif("Files the package installs") + ", the checks in " + rif("Testing") + ", and what was and was not proven in "
         + rif("Appendix C — Known issues and open points") + ".", "Elsewhere in this manual.")

S5B = p("<b>The denied-users list.</b> " + c("/etc/remotix/denied-users") + " (installed from "
        + c("debian/denied-users") + ", with one line, " + c("root") + ") is consulted twice by two different "
        "programs, so that neither is a single point of failure: by the root side before PAM and at the birth of a "
        "desktop (" + c("user_refused_as()") + "), and by " + c("pam_listfile") + " as the first " + c("auth")
        + " line (" + c("onerr=fail") + "). Uid 0 is refused by the root side whatever the list says. The root side's "
        "check also compares the spelling NSS returns, so that «BRUNO» resolving to «bruno» is refused when «bruno» "
        "is listed. An unreadable list refuses everybody. The file is a dpkg conffile: the administrator may add "
        "names, and an upgrade keeps them.", lead=True) + \
    p("The list is the only way the product offers to keep a given account off REMOTIX. It is not a group or a role "
      "mechanism and it does not restrict which users may log in in the other direction (there is no allow list).")

# ── 14.6 Polkit ──────────────────────────────────────────────────────────
S6 = p("A REMOTIX session has no seat, so polkit gives it the answer meant for a remote subject (" + c("allow_any")
       + ", usually a password) even for actions that a distribution grants to the user sitting at the machine "
       "without one. Two polkit rules and one helper script handle the two consequences. Both rules are installed "
       "active in polkit's vendor folder, not in " + c("/etc") + ", so the package owns them and removing the package "
       "removes them; an administrator overrides them with a rule of a lower number in " + c("/etc/polkit-1/rules.d/")
       + ", since polkit stops at the first rule that decides.", lead=True) + \
    table(["Rule", "Installed as", "What it does"], [
        [c("remotix-no-poweroff.rules"), c("50-remotix-no-poweroff.rules"),
         "Returns " + c("polkit.Result.NO") + " for 15 " + c("org.freedesktop.login1") + " actions: " + c("power-off")
         + ", " + c("reboot") + ", " + c("halt") + ", " + c("suspend") + " and " + c("hibernate") + ", each with its "
         + c("-multiple-sessions") + " and " + c("-ignore-inhibit") + " variant. " + c("NO") + " and not "
         + c("AUTH_ADMIN") + ": «challenge» would leave the entry in the menu asking a password, which promises "
         "something that is not there."],
        [c("remotix-remote-sessions.rules"), c("40-remotix-remote-sessions.rules"),
         "Removes the unrequested password windows of a remote session, for five actions only. Catalogue refresh "
         "(" + c("Flatpak.metadata-update") + ", " + c("Flatpak.appstream-update") + ", "
         + c("packagekit.system-sources-refresh") + "): " + c("YES") + " for every REMOTIX user, if the machine "
         "gives the seated user " + c("yes") + ". Network control and system repositories ("
         + c("NetworkManager.network-control") + ", " + c("Flatpak.modify-repo") + "): " + c("YES") + " for an "
         "administrator (member of " + c("wheel") + ", " + c("sudo") + " or " + c("admin") + ") under the same "
         "condition, " + c("NO") + " for an ordinary user. Everything else: " + c("NOT_HANDLED") + "."],
    ], "«TAB» — The two polkit rules of the package") + \
    ul([
        "<b>Administrative actions still ask a password,</b> exactly as with " + c("sudo") + ", seated or remote. That "
        "is not touched.",
        "<b>Root needs no exception for power.</b> logind checks the caller's capabilities before polkit, and root "
        "has " + c("CAP_SYS_BOOT") + ", so " + c("sudo systemctl poweroff") + " keeps working. The consequence for "
        "testing is that the rule cannot be checked from the root side: it must be checked as the user, from inside "
        "the session. " + c("check-desktop.py") + " does that: logind's " + c("CanPowerOff") + " and its siblings "
        "answer no, " + c("pkcheck") + " refuses the 15 actions it is asked about, and a real " + c("systemctl poweroff") + " as the "
        "user fails (check " + c("power-entries-absent") + "). <b>The rule forbids 19 actions, not 15:</b> four more, "
        + c("set-reboot-parameter") + ", " + c("set-reboot-to-firmware-setup") + ", " + c("set-reboot-to-boot-loader-menu") + " and "
        + c("set-reboot-to-boot-loader-entry") + ", carry the annotation " + c("org.freedesktop.policykit.imply") + " = "
        + c("reboot") + " and are allowed for the user seated at the machine, so polkit granted " + c("reboot") + " by implication "
        "despite the rule's explicit NO (an explicit NO is not enough against an implication) (found 20 November 2026; in 1.0.0 a local user could restart the machine when alone on it). "
        "The check " + c("power-implied") + " reads the installed rule and every policy file of the machine and fails if an action "
        "left alone implies, even through a chain, a forbidden one.",
        "<b>How the second rule recognises a REMOTIX session.</b> Not from the subject's fields (" + c("local")
        + " and " + c("seat") + " are the same for ssh, and the programs that ask run under the user manager's service, where polkit hands the rule no session) but by " + c("remotix-polkit-seated") + ", a shell script that "
        "reads logind's state files in " + c("/run/systemd/sessions") + " for a session of that user with "
        + c("SERVICE=remotix") + ", and prints what the machine gives the seated user for the action (the "
        + c("allow_active") + " of the policy file). It does not use D-Bus, " + c("loginctl") + ", " + c("pkaction")
        + " or " + c("pkcheck") + ": logind's checks call polkitd synchronously, and polkitd would be waiting for "
        "the helper, a deadlock measured at 10 s. The user name is passed as an argument, never inside a script text, "
        "and the script exits 0 always; anything unexpected becomes " + c("none") + ", which the rule turns into "
        + c("NOT_HANDLED") + ", or " + c("?") + ", which the rule reads as «the seated user does not get yes» "
        "(" + c("NOT_HANDLED") + ", except the silent " + c("NO") + " of an ordinary user for the two machine "
        "actions).",
        "<b>Declared:</b> a REMOTIX user who is also logged in over ssh gets the same answers there; a REMOTIX "
        "session that is still closing counts too. " + c("check-desktop.py") + " also has a check "
        + c("no-password-windows"),
    ]) + \
    p("<b>The other two belts</b> of the owner's rule «nobody switches off the server» (" + c("DECISIONS.md")
      + " §4.7) are not active. " + c("remotix-power-keys.conf") + " (logind ignores the power, reboot, suspend and "
      "hibernate keys and the lid switch, including long presses) and " + c("remotix-no-suspend.conf")
      + " (systemd's " + c("Allow*=no") + " for sleep) are installed under " + c("/usr/share/remotix/belts/")
      + ", where nothing reads them. REMOTIX does not modify the system beyond what it needs (the list of what it changes is in " + rif("What the security model does not defend") + "); an administrator "
      "who wants them copies them into " + c("/etc/systemd/logind.conf.d/") + " and " + c("/etc/systemd/sleep.conf.d/")
      + ". Consequence: without them, a person at the machine can still switch it off with the power button, "
      "and the polkit rule does not see that road, because logind acts on its own account there.")

# ── 14.7 The unit ────────────────────────────────────────────────────────
S7 = p("<b>" + c("remotix.service") + " has no sandboxing directive on purpose.</b> There is no " + c("User=") + ", no "
       + c("ProtectSystem=") + ", no " + c("NoNewPrivileges=") + ", no " + c("PrivateTmp=") + ". The unit's comment "
       "gives the reason: the process systemd starts is the root side, and whatever the unit restricts, every "
       "desktop born from it inherits (" + c("walls.h") + " names " + c("sudo apt install") + " in a remote "
       "desktop as the thing that must keep working). The network side's confinement is done in the program (" + c("walls.c") + "), where only that "
       "process receives it.", lead=True) + \
    table(["Setting", "Value", "Why"], [
        [c("Type"), c("simple") + ", " + c("ExecStart") + " through " + c("/bin/sh -c 'exec …'"),
         "The shell only expands the variables of the environment files, then " + c("exec") + "s, so the server stays "
         "the main process."],
        [c("EnvironmentFile"), c("/usr/share/remotix/remotix.conf") + " then " + c("-/etc/remotix/remotix.conf.d/*.conf"),
         "Defaults of the package, then the administrator's choices, which win. Variables: " + c("REMOTIX_PORT")
         + " (7447) and " + c("REMOTIX_OPTIONS") + "."],
        ["Options on the command line", c("--address 0.0.0.0 --name %H --port … --certificates /var/lib/remotix/net/certificates "
         "--page /usr/share/remotix/page.html --ban-file /var/lib/remotix/net/ban --split --journal"),
         "No bench options (" + c("--command-socket") + ", " + c("--survey") + ", " + c("--verbose") + ")."],
        [c("KillMode"), c("mixed"), "SIGTERM to the main process, SIGKILL to what is left of the unit. The desktops "
         "live outside the unit (they are started with " + c("setsid --fork") + "), so the unit's kill does not reach them; "
         "the root side closes them itself at an orderly stop (" + rif("Stopping the service") + ")."],
        [c("LimitRTPRIO") + ", " + c("LimitNICE"), "20, -11", "Priority for audio and video."],
        [c("Restart"), c("on-failure") + ", " + c("RestartSec=2") + ", " + c("RestartPreventExitStatus=78"),
         "Exit status 78 (" + c("EX_CONFIG") + ") is for a real configuration error, for example the user "
         + c("remotix") + " missing; it stops the restart loop."],
        [c("WantedBy"), c("multi-user.target"), "Present, but the package does not enable the unit."],
    ], "«TAB» — The service unit") + \
    warn("The unit does not make REMOTIX safe against a compromised root side. That process runs as root, "
         "unconfined, and runs PAM in grandchildren as root: PAM modules are other people's code loaded into "
         "root processes. What bounds the damage is that the root side never reads from the network, that "
         "its only input from the network side is the closed list above, and that the PAM transaction runs in a "
         "fresh image with a 20 s alarm.")

# ── 14.8 What is not defended ────────────────────────────────────────────
S8 = p("The honest list, from the code and the decisions:", lead=True) + \
    table(["Not defended or not proven", "Detail"], [
        ["A man in the middle on the first connection of a device",
         "There is no domain and no certificate authority. The first connection from each device asks the person to "
         "accept the server's certificate, and an attacker in the middle does not read the page, he rewrites it. "
         "Accepted in " + c("SPECS.md") + " §4.1 for the intended scenario (own server, own network or VPN). A real "
         "certificate removes the warning."],
        ["Anything beyond a password", "No second factor. Deferred by the owner until the project is complete "
         "(" + c("SPECS.md") + " §4.1)."],
        ["The desktop's own screen lock", "Switched off in every desktop (" + c("SPECS.md") + " §5.4). The reasoning, "
         "that the only road to a desktop is RCP and RCP goes through PAM, holds only while the password is the only key."],
        ["Users against each other", "The product adds no containment between users beyond their uids: one child per "
         "user, one logind session each, ordinary Unix permissions. A user is as able to read what other users leave "
         "world-readable, or to exhaust the machine's memory or CPU, as in any local login. The session cap and the "
         "pixel budget bound the number of desktops, not what a user does inside one."],
        ["An administrator", "Anyone in the sudo, wheel or admin group is an administrator inside the remote "
         "desktop as at the machine. The power rule does not stop root, and is not meant to."],
        ["A compromised root side", "Unconfined, root, runs PAM. See the warning above."],
        ["The root side's login pauses after a restart", "They live in its memory; the network side's ban is in a "
         "file. A restart of the root side forgets its pauses, while the network side's ban survives."],
        ["Bans behind shared addresses", "One NAT address, or one IPv6 /64, is one key: five mistakes by one user ban "
         "that user on that key, twenty failures ban every user behind it. Declared in " + c("SPECS.md") + " §4.2."],
        ["The residual timing channel", "A PAM failure delay above the 2.5 s floor can still be told apart "
         "(" + rif("Login and its defences") + ")."],
        ["The English match of the faillock line", "A translated or silenced " + c("pam_faillock") + " is not "
         "recognised: the owner's own typos while locked then count towards a ban."],
        ["Kernel facilities that the walls need", "The read-only tree needs kernel 5.12; without it the network side "
         "does not start. Landlock's abstract-socket scope needs 6.12 and is skipped on an older kernel. Only x86_64 "
         "and aarch64 have a seccomp filter."],
        ["AppArmor in a session", "The profile is in complain mode and was never observed during a session (previous "
         "section)."],
        ["What the package changes on the machine",
         "<b>One system file is edited:</b> through " + c("pam-auth-update") + " the package adds one line, " + c("session optional pam_exec.so quiet "
         "/usr/libexec/remotix/remotix-local-login") + ", to " + c("/etc/pam.d/common-session") + " (a file of "
         + c("libpam-runtime") + ", not a conffile of REMOTIX) and removes it when the package is removed (" + rif("The local-login hold")
         + "). At a user's first connection the product adds the user to the groups that own the card's render nodes "
         "(" + c("usermod -aG") + ", run as root after PAM said yes and before the child is forked), records it in " + c("/var/lib/remotix/group-enrollments.jsonl")
         + ", and the removal script undoes it with " + c("gpasswd -d") + ". For a user manager already running, it "
         "puts a POSIX ACL for the user's private group on " + c("/dev/dri/renderD*") + " and records it in "
         + c("/var/lib/remotix/render-grants") + "; " + c("remotix --drop-render-grants") + " takes it back. Both are "
         "necessary for the card, and both are changes to the system that an administrator should know about."],
        ["Hardware and clients not tried", "NVIDIA (deferred), a phone in touch mode (the owner tried Samsung DeX only), a canvas above "
         "3840x2160 (the page's own size ladder stops there; the protocol canvas is 4096×2304, and the <b>declared</b> limit of the "
         "product is 3K) and the first tap on GNOME touch are open or "
         "untried items in " + c("PIANO.md") + ". The security model has not been tested with those."],
    ], "«TAB» — What the security model does not cover") + \
    p("The transport limits that bound a flood of connections before login (a cap on connections, on pending "
      "connections and per address) are in " + rif("Transport") + "; the encodings of the identity in the log "
      "are in " + rif("Logging and diagnostics") + ".")

CHAPTER = ("Security model", [
    ("Trust boundaries and the processes of the service", S1),
    ("The closed list between the network side and the root side", S2),
    ("The walls of the network side", S3),
    ("The AppArmor profile and its mode", S4),
    ("Local excludes remote and the session cap", S5),
    ("The local-login hold", S5C),
    ("The denied-users list", S5B),
    ("Polkit rules, password windows and the power belts", S6),
    ("The service unit and why it is not sandboxed", S7),
    ("What the security model does not defend", S8),
])
