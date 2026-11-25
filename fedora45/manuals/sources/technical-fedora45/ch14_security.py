from build import arrow, box, c, fig, note, p, rif, steps, sysf, table, text, ul, warn, zone

# ── 14.1 Trust boundaries ────────────────────────────────────────────────
ZONES = fig(
    zone(20, 12, 210, 290, "Network")
    + box(36, 56, 178, 54, "Browser", "page + WebTransport", "dark")
    + box(36, 200, 178, 54, "Anyone else", "may knock, may be banned", "grey")
    + zone(250, 12, 250, 290, "Network side (uid remotix)")
    + box(266, 50, 218, 58, "TLS, QUIC, the page", "limiter, ban table", "blue")
    + box(266, 130, 218, 58, "Walls + SELinux", "remotix_net_t, no capability", "amber")
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
         "The walls of " + c("walls.c") + " and the SELinux domain " + c("remotix_net_t") + " (enforcing: " + rif("The SELinux module and its mode") + ")."],
        ["Root side (the unit's main process)", "root", "The PAM helper, the render-grant record, the channel to "
         "the network side, the right to start a child as any user.", "The SELinux domain " + c("remotix_t") + ", a login program like sshd, "
         "<b>not</b> unconfined; no unit hardening. Every right is written in " + c("selinux/remotix.te") + " with its reason, and the domain "
         "stays wide (" + rif("The SELinux module and its mode") + ")."],
        ["PAM dispatcher and grandchildren", "root", "One PAM transaction each; the typed password for its duration.",
         "A 20 s alarm; a fresh memory image (re-executed, not forked from the server)."],
        ["Per-user child", "Born as root for PAM and logind, then the user's uid and gid (" + c("setgid()") + " then "
         + c("setuid()") + ", read back with the kernel)", "The user's session bus, capture, input, the user's "
         "desktop.", "Ordinary Unix permissions of that user, and the SELinux context of a local login of that user (" + c("unconfined_t") + " for an ordinary user, "
         + c("staff_t") + " or " + c("user_t") + " for a confined one)."],
        ["Desktop session", "The user", "The compositor and the user's programs.", "As for any local login of that "
         "user; the polkit rules below."],
    ], "«TAB» — The processes of the packaged service and their power") + \
    p("The principle is that root does only what needs root: verifying anyone's password, and descending to anyone's "
      "uid. Everything that faces the internet runs without it. The desktops are not behind the walls: their children "
      "are forked by the root side, never from the network side, so that for example " + c("sudo dnf install")
      + " in a remote desktop keeps working (" + c("walls.h") + " still says " + c("sudo apt") + ", a leftover of the Ubuntu text).") + \
    p("<b>The third domain.</b> The hook of the local login, " + c("remotix-local-login") + ", runs in its own domain " + c("remotix_hook_t")
      + " (" + c("selinux/remotix.te") + ", " + rif("The local-login hold") + "): PAM runs it inside a login screen's stack, and it may touch "
      "only the requests folder " + sysf("/run/remotix/prelocal") + ".")

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
        ["2", "SELinux domain, entered before the tree goes read-only",
         "The root side's fork writes " + c("system_u:system_r:remotix_net_t:s0") + " into " + c("/proc/thread-self/attr/exec")
         + " before the " + c("execve()") + " (" + c("WALLS_SELINUX_EXEC") + ", " + c("WALLS_SELINUX_NET_TYPE") + "). The new context keeps the user and the role of the root "
         "side and the low level. Protection off (no " + c("/sys/fs/selinux/enforce") + "): a note «SELinux: off» and the start goes on. Protection on "
         "but the root side not in " + c("remotix_t") + ", or the domain not in the policy (" + c("EINVAL") + "): a ⚠ line and the start goes on. "
         "Loaded and the write <b>refused</b>: " + c("-1") + ", the network side is not started (see the next section).", c("selinux_exec_in()") + ", " + c("selinux_exec_net()")],
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
         "is not applied, the notes say so, and the start goes on: this wall is never fatal. The kernel and the Landlock ABI of Fedora 45 were "
         "<b>not read</b> for this manual (the Ubuntu virtual machines, kernel 7.0.0-44, reported «landlock ABI 8: abstract unix sockets scoped»; "
         "the logs of the Fedora machines are on the dev server and were not opened).",
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
      "SELinux state, the folder, the limits). The package check " + c("check-package.py") + " (first-start) "
      "confirms the process layout of a running service, one root side as root and one network side as "
      + c("remotix") + ", records " + c("CapEff") + ", " + c("NoNewPrivs") + " and " + c("Seccomp") + " from "
      + c("/proc/<pid>/status") + " of the network side, and checks the owner and mode of every file under "
      + c("/var/lib/remotix/net") + " (directories 700, secrets and the ban file 600). It records those three "
      "status values as evidence; it does not compare them against fixed expected numbers. <b>That file is still the Debian and Ubuntu one</b> "
      "(identical to Ubuntu's: 35 of its lines mention AppArmor or dpkg, counted with " + c("grep -c 'apparmor\\|dpkg'") + "): it does not prove the "
      "SELinux wall of Fedora. The negative proof of the wall is " + c("prove/wall-selinux.sh") + " with " + c("prove/wall-neg-domain.py") + ": the probe runs inside "
      + c("remotix_net_t") + " <i>as root with every capability</i>, against targets that Unix permissions alone would let it reach, so only SELinux can "
      "say no; it makes 25 attempts, 23 that must be refused (root's files, a user's home, the root side's state, a write in "
      + sysf("/run/remotix/prelocal") + ", a shell, another program, writes in " + sysf("/etc") + ", " + sysf("/usr") + " and " + sysf("/var/lib/remotix") + ", TCP, UDP, "
      "IPv6, raw and packet sockets, an X socket and a user's socket in " + sysf("/run/user") + ", " + sysf("/run/systemd/private") + ", "
      + sysf("/proc/1/environ") + ", a signal to a root-side process, " + sysf("/proc/<root side>/mem") + ", and D-Bus calls to services other than logind) and 2 that must "
      "work (logind's " + c("ListSessions") + " and a write in its own state folder). An attempt passes only if it is refused <b>and</b> an AVC of that "
      "process appears in the journal inside the window of that attempt. " + c("prove/wall-sesearch.sh") + " saves what the policy allows to "
      + c("remotix_t") + " for signals (registers F24, F33; the count of 23 and 2 was taken from the script in this tree, and the register's "
      "earlier figure of 21 predates two additions).") + \
    p("<b>User namespaces.</b> Fedora has no AppArmor sysctl that restricts them. The code creates its namespaces as root, in the fork of the "
      "root side (" + c("walls.c") + "), and its seccomp filter denies " + c("CLONE_NEWUSER") + ", which is what counts here; that is read in the code, "
      "and the behaviour of Fedora's kernel on this point was not measured. The SELinux domain is the second wall ("
      + rif("The SELinux module and its mode") + ").") + \
    note("The state folder " + c("/var/lib/remotix/net") + " and the run folder " + c("/run/remotix/net")
         + " are created by tmpfiles (" + c("remotix.tmpfiles") + ") owned by " + c("remotix") + " with mode 0700. "
         "The root side's own state, " + c("/var/lib/remotix") + ", is root's and mode 0755: a "
         + c("remotix") + "-writable folder holding root's files would let a hijacked network side swap them. The SELinux types of these folders "
         "come from " + c("selinux/remotix.fc") + ": " + c("remotix_var_lib_t") + " for " + sysf("/var/lib/remotix") + ", " + c("remotix_net_state_t")
         + " for its " + sysf("net") + " folder, " + c("remotix_var_run_t") + " for " + sysf("/run/remotix") + " and " + c("remotix_net_run_t") + " for "
         + sysf("/run/remotix/net") + " (the tmpfiles file is " + c("rpm/remotix.tmpfiles") + ").",
         "Who owns what.")

# ── 14.4 SELinux ─────────────────────────────────────────────────────────
S4 = p("The wall of Fedora is a SELinux module, " + c("selinux/remotix.te") + " (" + c("policy_module(remotix, 1.1.1)") + "), with the file contexts "
       + c("remotix.fc") + " and the interfaces " + c("remotix.if") + "; it is decision D3 of " + c("PIANO.md") + " and registers F24 to F28. The "
       "package installs it in its " + c("%post") + " scriptlet with " + c("%selinux_modules_install -s targeted /usr/share/selinux/packages/remotix.pp.bz2") + ", "
       "then " + c("%selinux_relabel_post") + ", and removes it in " + c("%postun") + " (" + c("%selinux_modules_uninstall") + "). If the module "
       "does not get in, " + c("%post") + " says so clearly (the server will not run in its own domain and the network side will have no SELinux wall) "
       "and the installation does not fail. SELinux stays <b>enforcing</b>: the module is never permissive, has no " + c("dontaudit") + " of its own and "
       "was not made with " + c("audit2allow") + " (header of the " + c(".te") + " file); every rule has a line saying what it is for.", lead=True) + \
    table(["Domain", "What it is", "What it may do"], [
        [c("remotix_t"), "The <b>root side</b> of the server. A login program like sshd or gdm's session worker (" + c("auth_login_pgm_domain") + "): "
         + c("pam_selinux open") + " asks for the user's context and " + c("child.c") + " lets PAM set it for the next " + c("exec") + ".",
         "Wide, and written down (below). Since 25 Nov 2026 it may also " + c("stop") + " and " + c("status") + " units of type " + c("xdm_unit_file_t")
         + " (every " + c("plasma-*") + " unit of Fedora 45), which the forced close of KDE needs (register F36)."],
        [c("remotix_net_t"), "The <b>network side</b>, the process that speaks QUIC, WebTransport and HTTP/3. The root side puts it there before its " + c("execve")
         + ".", "Uses the three descriptors it was handed (channel, UDP, TCP) and no more: no " + c("create") + ", " + c("bind") + ", " + c("name_bind")
         + " or " + c("name_connect") + " on IP sockets. Runs nothing (no " + c("execute_no_trans") + ", no transition out). Reads its few files and "
         "writes only " + sysf("/var/lib/remotix/net") + " and " + sysf("/run/remotix/net") + ". Asks logind on the system bus and nobody else."],
        [c("remotix_hook_t"), "The hook of the local login.", "Touches only " + sysf("/run/remotix/prelocal") + " (type " + c("remotix_prelocal_t") + ")."],
    ], "«TAB» — The three SELinux domains of REMOTIX") + \
    table(["Path", "Type"], [
        [sysf("/usr/libexec/remotix/remotix"), c("remotix_exec_t") + " (root side, network side and the user's child are the same binary)"],
        [sysf("/usr/libexec/remotix/remotix-local-login"), c("remotix_hook_exec_t")],
        [sysf("/run/remotix"), c("remotix_var_run_t")],
        [sysf("/run/remotix/prelocal"), c("remotix_prelocal_t") + " (the only thing the hook may touch)"],
        [sysf("/run/remotix/net"), c("remotix_net_run_t")],
        [sysf("/var/lib/remotix"), c("remotix_var_lib_t") + " (the root side's state: card grants, enrolments)"],
        [sysf("/var/lib/remotix/net"), c("remotix_net_state_t") + " (certificates, QUIC secret, the ban table)"],
        [sysf("/etc/dconf/db/remotix") + " and " + sysf("remotix.new"), c("remotix_dconf_db_t") + " (the system dconf database of the GNOME session; by name: " + rif("GNOME: headless Shell and session dconf") + ")"],
    ], "«TAB» — The file contexts of " + c("selinux/remotix.fc")) + \
    p("<b>How a process enters the network domain.</b> Not by path: the same binary is the root side, the network side and the user's child, so no file "
      "context could tell them apart. The root side's fork writes the wanted context into " + sysf("/proc/thread-self/attr/exec") + " right before "
      "the " + c("execve()") + " (" + rif("The walls of the network side") + "). The behaviour is the one AppArmor had on the other distributions: protection "
      "off is a note, a protection that cannot be entered is a ⚠ and the start goes on, a refused write stops the network side. <b>No port type:</b> it was "
      "evaluated and left out. A module cannot carry a " + c("portcon") + ", it would need " + c("semanage port") + " (a dependency, a scriptlet that must run before the module is removed, a command "
      "for every administrator who picks another port), and it would buy nothing for the wall, because the network side never binds: the root side "
      "binds the unreserved ports and the http ones.") + \
    p("<b>The users' sessions.</b> They are not in these domains. A local login of an ordinary user gives " + c("unconfined_t") + " and the remote session does the same; "
      "for a confined SELinux user the child takes the context that a local graphical login would give (" + c("selinux_exec_like_local_login()") + ": " + c("staff_t")
      + " for " + c("staff_u") + ", " + c("user_t") + " for " + c("user_u") + "), checked again before the " + c("execve") + " (" + rif("How a session is born")
      + "; register F25). " + c("sysadm_u") + " does not get in, as with ssh and gdm of a stock machine. Two refusals that stay and are not REMOTIX's: with "
      "confined users, " + c("systemd --user") + " asks " + c("relabelto") + " on " + c("tmp_t") + ", " + c("bwrap") + " is refused in " + c("staff_t") + " and " + c("user_t")
      + " (F30), and on XFCE " + c("ssh-agent") + " cannot append to the session log (register F28); and on gdm every <i>local</i> login leaves an AVC of "
      + c("xdm_t") + " towards " + c("stratisd_t") + " (F15), the same with REMOTIX's line taken out.") + \
    p("<b>What the module still leaves wide (register F27).</b> " + c("remotix_t") + " is no longer unconfined, but it stays wide in six places: the rights of a login "
      "program (PAM, change of identity, reading the state of every process, " + c("corecmd_exec_bin") + "); the transition towards every unprivileged user domain and "
      + c("unconfined_t") + " (it must be able to start anyone's session); " + c("sys_admin") + ", " + c("net_admin") + ", " + c("setpcap") + " and " + c("mount") + " on "
      + sysf("/") + ", " + sysf("/proc") + ", " + sysf("/dev") + ", " + sysf("/tmp") + " and the two folders of the network side, only to build the private rooms of the "
      "network side in the fork; the «chores» in the user manager (the light close for the local login, the sweep of orphans, the KWin unit), which are forks of the root side that "
      "drop to the user's uid but stay in " + c("remotix_t") + " (the user's session bus, " + c("systemctl --user") + ", REMOTIX's XDG files in the home, " + c("kill") + " also in "
      "user namespaces); writing in " + sysf("/etc/dconf/db") + " for two fixed names only; and binding the unreserved and the http ports. The alternative on the table, to run "
      "those chores again as processes in the user's domain as the child does, changes the structure of the product and is the owner's decision; "
      "whether it has been taken since was not checked.") + \
    p("<b>What was verified, and how.</b> The figures below are the ones written in " + c("PIANO.md") + " and in the register, with their date; the logs were not "
      "read again. Final round of 23 Nov 2026, package " + c("h1") + " (module 1.1.1), in enforcing: all four desktops passed, GNOME with 52 PASS (and the known " + c("pkexec")
      + " failure) and 39 PASS of " + c("prove/all.sh") + ", KDE 76, XFCE 60, LXQt 60; the negative proof of the wall, 0 failures; REMOTIX's own AVC, 0. Install, update, removal and "
      "reboot with the module loaded were tried (F24): after a reboot the service restarts in " + c("remotix_t") + " and the network side in " + c("remotix_net_t") + ". "
      "KDE with package " + c("i2") + " (module changed only for the rule of F36) was tried on the virtual machine and by the owner; GNOME, XFCE and LXQt were <b>not</b> run again with "
      + c("i2") + ", by the owner's decision.") + \
    p("<b>The window of an update.</b> Updating from a package without the wall, with the service running, there is a moment between the loading of the module and "
      "the restart of the service in which the old root side and its old network side run in " + c("remotix_t") + " and some of their accesses are refused (register F24 notes the two lines "
      "about the session certificate and key); it is the cost of an update that crosses the wall. On removal, " + c("%postun") + " runs " + c("restorecon -R /var/lib/remotix")
      + " if the folder stays, so that nothing keeps a type that no longer exists.") + \
    note("the <b>lesson</b> of the AppArmor wall of the other distributions, valid here too, is that a security profile must be tried on a real or virtual machine with the protection "
         "<i>in force</i>, because a test in a container does not exercise it. On Fedora the module was tried only on virtual machines and on the owner's live images, always in enforcing; "
         "see " + c("PIANO.md") + " D3.", "Lesson.")



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
    p("<b>Who is told, and when, when the session ends.</b> In defence 3 the child's guard now tells the parent first, "
      + c("local_found_by_child()") + ": the logged-in clients receive " + c("0x04") + " at once, and only then does the child do the "
      "light close, because the closing can wait for PipeWire for up to 25 s where RealtimeKit cannot start (comment in " + c("child.c")
      + "). When a child ends because the graphical session ended, " + c("session_ended_by_child()") + " and the dismissal of a gone child "
      "call " + c("wt_dismiss_user_session_over()") + " and not " + c("wt_dismiss_user()") + ". Of the connections that carry the name, a "
      "logged-in one gets the farewell at once; one that was admitted but is still inside the fixed second (" + c("rcp_admitted_waiting()")
      + ") gets " + c("0x10") + " at the end of that second, in the place of ADMITTED; one still waiting for PAM, or whose «no» is being "
      "kept, is skipped, because it was never attached to that session and a stranger trying passwords under that name must learn "
      "nothing about the account. Before, a login refused with " + c("0x0E") + " «still closing» could receive a false " + c("0x10")
      + " (seen on 18 Nov 2026 in a rejoin 8 to 10.5 s after the logout of a young session; comment in " + c("webtransport.c") + ").") + \
    p("<b>What else answers " + c("0x0E") + ".</b> The text the page shows for " + c("0x0E") + " is generic on purpose, because the byte "
      "covers several different causes (a comment in " + c("page.html") + " lists them as six routes). Two of them are newer than the Debian release: "
      "the desktop's compositor is not installed (XFCE or LXQt without " + c("labwc") + ": the parent says it before spawning the child, in "
      + c("delivery_verdict()") + " through " + c("session_missing_component()") + "; no process, no logind session; the log names the "
      "package the administrator must install; " + rif("The four desktops side by side") + "), and the child's refusal of the stage "
      "because of the scale (" + c("MSG_STAGE") + " with " + c("fatal") + ", " + c("stage_refused_by_child()") + " answers with "
      + c("RCP_SESSION_UNSERVABLE") + " to every connection of that user, admitted or logged in; " + rif("GNOME: headless Shell and session dconf")
      + "). Two more are specific to Fedora: a KWin older than 6.8, which does not offer " + c("kde_output_management_v2") + " version 22 (the session is "
      "refused with a clear message, once, and the graphical session is closed by the same road; " + rif("KDE Plasma: KWin alone") + "), and the child's SELinux "
      "refusals, written in the log as «⛔ SELinux …: the login is REFUSED» (codes 44 to 47 of " + c("child.c") + "; " + rif("How a session is born") + ").") + \
    p("<b>The session cap answers " + c("0x0E") + ".</b> The default cap is " + c("RCP_SESSION_CAP") + " = 10 users "
      "served at once (" + c("rcp.h") + "; changed by " + c("--session-cap") + " at start-up, " + c("rcp_cap_set()")
      + "). Whoever does not fit gets " + c("0x0E") + " " + c("SESSION_UNSERVABLE") + " with the detail in the body. "
      "The cap is checked at two points: in " + c("delivery_verdict()") + " in " + c("main.c") + ", on the count of "
      "desktops, before a child is spawned, so a user who does not fit costs no process, no logind session and no "
      "compositor; and in " + c("slot_take()") + " in " + c("rcp.c") + ", on the registry of attached sessions, at "
      "the attach. It is deliberately not "
      + c("0x06") + " (no composition capacity left, which is the budget, see " + rif("Quality, degradation and budget")
      + ") and not " + c("0x0F") + " (this user already has a session): the person must be told that the table is full "
      "and not, falsely, that they are connected elsewhere. The cap is administrative, not a physical limit, and 10 is an administrative default: how many users a machine really serves at once depends on the machine (video card, processor, memory). "
      "Related: a second device of a user whose first client is alive gets " + c("0x0F") + " "
      + c("ALREADY_ACTIVE_REMOTELY") + "; a client silent for long enough is detached and does not hold the slot.")

# ── 14.5b The local-login hold ───────────────────────────────────────────
S5C = p("<b>The problem.</b> A user who has a REMOTIX desktop and then logs in at the machine starts a second graphical "
        "session of the same user. GNOME's login screen holds that login while the user has another graphical session that is "
        "active or online (the dialog «Session Already Running»); " + c("plasmalogin") + ", LightDM and SDDM hold nothing (register A2), and the local desktop starts on the user manager and the bus that the "
        "remote one is still using (read in the sources on 18 Nov 2026, for the Ubuntu flavours: Plasma adopts the remote units and dies with them, the "
        "local " + c("xfce4-session") + " finds its bus name taken and leaves, so KDE and XFCE return to the login screen). The "
        "owner's order (" + c("DECISIONS-11") + " §11.57, 18 Nov 2026) is one rule for every desktop and display manager: "
        "<b>a local graphical login closes the user's remote desktop first</b>, completely, and goes on only after that.",
        lead=True) + \
    table(["Piece", "What it is"], [
        ["The hook", c("/usr/libexec/remotix/remotix-local-login") + " (mode 0755), built from " + c("src/local_login.c") + " with libc "
         "only. PAM runs it as root, inside the login's own stack, and the login waits for it."],
        ["The PAM line", c("session optional pam_exec.so quiet /usr/libexec/remotix/remotix-local-login") + " in the PAM files of the login screens "
         "(gdm, plasmalogin, lightdm, sddm), put there and kept by the script " + c("/usr/libexec/remotix/remotix-pam-hook") + " (below; "
         + rif("The PAM service file remotix.pam") + ", " + rif("Files the package installs") + ")."],
        ["The script", c("remotix-pam-hook") + " (" + c("src/remotix-pam-hook") + ", 335 lines of shell, counted with " + c("wc -l") + "), with four verbs: "
         + c("apply") + ", " + c("check") + ", " + c("remove") + " and " + c("prepare") + ". The hook it installs, " + c("local_login.c") + ", has 132 lines."],
        ["The requests", c("/run/remotix/prelocal/") + ": a folder of root, mode 0700, made by the root side (not by tmpfiles). "
         "A request is an empty file named by the uid. The file " + c(".lock") + " in it is held with an exclusive lock for as long "
         "as the root side lives."],
        ["The message", c("RXR_LOCAL_COMING") + " (110), root side to network side: the uid and the user name of the user whose login is "
         "held (" + rif("The closed list between the network side and the root side") + ")."],
        ["The root side", c("pl_step()") + " and the " + c("PL_*") + " constants in " + c("rootside.c") + ": it serves the requests."],
    ], "«TAB» — The pieces of the local-login hold") + \
    p("<b>How the line gets into the login screens, and stays there</b> (" + c("remotix-pam-hook") + ", registers F6, F9, F18, F19, F21; decision D4). The line "
      "is the same as on Debian and Ubuntu, but it cannot go through " + c("pam-auth-update") + ": Fedora has none, and " + c("authselect") + " rewrites "
      + sysf("system-auth") + ", " + sysf("password-auth") + " and " + sysf("postlogin") + " from the administrator's profile, so a package that edited them would "
      "replace that choice (tried on the virtual machine, study 1 §9.1: " + c("authselect apply-changes") + " deletes lines added by hand; a profile in " + sysf("custom/") + " would replace the "
      "administrator's own). The script therefore never touches anything authselect generates, and works on the files of the login screens themselves:") + \
    ul([
        "<b>Where in the file.</b> In the " + c("session") + " phase, right <b>after the first " + c("pam_selinux.so close") + " line</b>, that is <b>before</b> "
        + c("pam_selinux open") + ", and not after " + c("pam_systemd") + " as on Debian. Three reasons, all measured on 21 and 22 Nov 2026 with gdm 51 and "
        "plasmalogin: the worker of the login screen already puts " + c("XDG_SEAT") + ", " + c("XDG_SESSION_TYPE") + " and " + c("XDG_VTNR")
        + " in the PAM environment, which is all the hook looks at; " + c("pam_selinux open") + " sets the exec context of the <i>next</i> exec, and a "
        + c("pam_exec") + " after it would spend that exec on the hook (an AVC of type " + c("entrypoint") + "); and not before " + c("close") + ", because the stack also "
        "runs when the session is closed, and at that point the helper of plasmalogin still holds the user's exec context and would be refused (the same AVC).",
        "<b>Which file.</b> A file of the login screen's package in " + sysf("/usr/lib/pam.d") + " with no file of the same name in " + sysf("/etc/pam.d")
        + ": the script makes " + sysf("/etc/pam.d/<name>") + " as a copy of the current vendor file plus its block, with a first line that says it is REMOTIX's; it is "
        "<b>regenerated at every apply</b>, so it is never older than the vendor file. A file of the same name in " + sysf("/etc/pam.d") + " that is not ours: only "
        "the marked block is added and removed. A file of ours whose vendor file has gone is deleted. Symbolic links (authselect's) are never touched.",
        "<b>sddm is the odd one.</b> Its files " + sysf("sddm") + " and " + sysf("sddm-autologin") + " are in " + sysf("/etc/pam.d") + " and are " + c("%config")
        + " of the sddm package; there is nothing in " + sysf("/usr/lib/pam.d") + ". The block is added <b>in place</b> and taken out byte for byte, and " + c("rpm -V sddm")
        + " reports the file as modified while REMOTIX is installed (register F19).",
        "<b>Safety.</b> A broken PAM file shuts everybody out, so every file is composed in a temporary file in the same folder, command by command (the status of "
        "each is looked at), checked (every line has the shape of a PAM line, there is a " + c("session") + " line, and the composed file minus our block and marker is "
        "<i>byte for byte</i> the source it was made from), given owner, mode and SELinux label, and only then renamed over the target. If anything looks wrong the file "
        "is not touched and the reason is said; a block with a BEGIN and no END is not touched either. If our own generated copy cannot be refreshed it is <b>deleted</b>, "
        "so that the vendor's new file is in force without the hook: no hook is better than an out-of-date login file. The exit status is 0 or 1 and callers ignore it: "
        "packaging never fails because of the hook.",
        "<b>The login screens that are active,</b> each proved with its real login screen on the test virtual machines on 21 and 22 Nov 2026 (registers F6, F9, F18, F19), and on the real server from the live images on 25 Nov 2026 (table below): " + c("gdm") + "; " + c("plasmalogin") + " (KDE, package "
        + c("plasma-login-manager") + "); " + c("lightdm") + " (XFCE; the session class is not yet in the PAM environment there, and " + c("local_login.c") + " accepts "
        "an empty class); " + c("sddm") + " (LXQt).",
        "<b>What keeps it there.</b> " + c("%post") + " runs " + c("apply") + "; the triggers " + c("%triggerin") + " and " + c("%triggerpostun") + " run it again whenever "
        "gdm, lightdm, sddm or plasma-login-manager is installed or updated (with " + c("%triggerprein") + " and " + c("%triggerun") + " running " + c("prepare") + " for sddm, "
        "so that rpm's decision about a changed " + c("%config") + " file is not confused by our block); the service runs " + c("ExecStartPre=-remotix-pam-hook check") + " at every "
        "start (the " + c("-") + " means it never prevents the start); " + c("%preun") + " runs " + c("remove") + " on removal, after the service has stopped, otherwise its "
        + c("ExecStartPre") + " would put the line back. The few seconds of an update of sddm without the block are accepted: a local login in that window does not close the "
        "remote desktop first (register F21).",
    ]) + \
    p("<b>What happens, in order.</b>") + steps([
        "<b>The hook decides if the login is its business.</b> Only for " + c("PAM_TYPE=open_session") + " with " + c("XDG_SEAT")
        + " set, session class " + c("user") + " (or none), type " + c("wayland") + ", " + c("x11") + " or " + c("mir") + " (or none), "
        "a user that is not root, and a PAM service that is not " + c("remotix") + ". Everywhere else (ssh, a text console, "
        "REMOTIX's own sessions, and the closing of any session) it returns 0 at once. Cron and the other services never run it: the line is only in the "
        "PAM files of the login screens.",
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
    p("<b>The real login screens on Fedora 45.</b> The checks " + c("prove/prelocal.sh") + " and " + c("check-prelocal.py") + " run the three proofs on the virtual machines, "
      "with each desktop's real login screen: (1) with the remote desktop open, a local login closes it; (2) the orphan case, " + c("kill -9") + " of the remote "
      "desktop's leader and a restart of the service, where the root side says «local login … HELD in PAM: its REMOTIX desktop is closed first»; (3) with the local "
      "session active, a remote login is refused with " + c("0x05") + " and the local session stays intact. All three passed on GNOME, KDE (plasmalogin), XFCE (lightdm) and LXQt (sddm) "
      "(registers F9, F18, F22); with the remote open the remote desktop closed in 1 to 2 s. The first tests through the owner's own hands were made on 25 Nov 2026, with "
      "the Fedora 45 live USB sticks on the real server (two video cards, Intel and Radeon, SELinux enforcing, package " + c("h1") + " installed with " + c("server/live-installa.sh") + "):") + \
    table(["Live image (screen)", "What was seen", "Status"], [
        ["Fedora 45 GNOME (gdm)", "The local session disconnected the remote session (the owner's words). The logs of that live machine were not saved.",
         "Passed, by hand, 25 Nov 2026 (" + c("PIANO.md") + ")."],
        ["Fedora 45 KDE (plasmalogin)", "<b>First attempt not passed</b>: with a remote desktop that had Konsole and " + c("top") + " open, the browser was disconnected but the remote desktop was "
         "not closed and the local one did not start (register F36): the orderly close did not finish in 10 s, the forced close was refused by the SELinux wall, and the local login was let "
         "through with the remote KWin still alive. After the correction (package " + c("i1") + ", then " + c("i2") + " with the 5 s wait): the forced close came at 5.04 s, everything was "
         "stopped 0.56 s later, the hook was released at 5.9 s, the local desktop came at once, 0 SELinux refusals, 0 core dumps, nothing of the remote left.",
         "Passed after the correction, by hand, 25 Nov 2026."],
        ["Fedora 45 XFCE (lightdm)", "Orderly close of the remote desktop in 1.7 s, the local session opened at the first attempt, nothing of the remote left.", "Passed, by hand, 25 Nov 2026."],
        ["Fedora 45 LXQt (sddm)", "Orderly close of the remote desktop in 0.7 s, the local session opened, nothing of the remote left.", "Passed, by hand, 25 Nov 2026."],
    ], "«TAB» — The local-login hold tried through real login screens") + \
    p("The figures in the table are the ones written in " + c("PIANO.md") + " and in the register with their date; the logs of the live machines were not available "
      "for this manual (those of KDE are kept outside the tree), and the times were not checked on them. The hold on gdm has one more behaviour that was <b>observed on a virtual machine without "
      "REMOTIX's line</b> (study 1 §5.1 and §5.2): with the remote session active, GDM 51 shows «Session Already Running» with «Cancel» and «Force Stop», and «Force Stop» "
      "asks logind to terminate every graphical session of the user other than the one just opened, the remote one included; but GDM then also closed the local login just opened, "
      "and the owner had to sign in a second time. With REMOTIX's hook the remote desktop is closed <i>before</i> the screen looks, so the dialog should not appear; this was "
      "<b>not tried</b> on Fedora with the hook, only the result of the owner's live test is known. GDM's worker waits without a limit, so the hook's 25 s are not cut by it.") + \
    p("<b>The second rule, “no orphan desktops”</b> (" + c("DECISIONS-11") + " §11.56), uses the same machinery. A seatless REMOTIX session "
      "whose scope still has processes and whose user has no child of ours must not stay: while the service runs, the root side "
      "ends it when it is seen so in two scans in a row (" + c("LX_EVERY_MS") + " = 5 s), and at an orderly stop it ends whatever "
      "is left (" + rif("Stopping the service") + "). A user who comes back before the second scan gets a child, and a desktop "
      "with a child is not an orphan.") + \
    note("Where the rest is: the log lines in " + rif("Logging and diagnostics") + ", the files and maintainer scripts in "
         + rif("Files the package installs") + ", the checks in " + rif("Testing") + ", and what was and was not proven in "
         + rif("Appendix C — Known issues and open points") + ".", "Elsewhere in this manual.")

S5B = p("<b>The denied-users list.</b> " + c("/etc/remotix/denied-users") + " (with one line, " + c("root") + ") is consulted twice by two different "
        "programs, so that neither is a single point of failure: by the root side before PAM and at the birth of a "
        "desktop (" + c("user_refused_as()") + "), and by " + c("pam_listfile") + " as the first " + c("auth")
        + " line (" + c("onerr=fail") + "). Uid 0 is refused by the root side whatever the list says. The root side's "
        "check also compares the spelling NSS returns, so that «BRUNO» resolving to «bruno» is refused when «bruno» "
        "is listed. An unreadable list refuses everybody. The file is " + c("rpm/denied-users") + ", installed as " + sysf("/etc/remotix/denied-users") + " with "
        + c("%config(noreplace)") + ": the administrator may add names, and an update keeps them (rpm writes a " + c(".rpmnew") + " beside it if the package's own copy changes); "
        "the removal of the package deletes only " + c("denied-users.rpmsave") + ", by name.", lead=True) + \
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
         "Returns " + c("polkit.Result.NO") + " for <b>19</b> " + c("org.freedesktop.login1") + " actions: " + c("power-off")
         + ", " + c("reboot") + ", " + c("halt") + ", " + c("suspend") + " and " + c("hibernate") + ", each with its "
         + c("-multiple-sessions") + " and " + c("-ignore-inhibit") + " variant (15), and since 20 Nov 2026 the four "
         + c("set-reboot-parameter") + ", " + c("set-reboot-to-firmware-setup") + ", " + c("set-reboot-to-boot-loader-menu") + " and "
         + c("set-reboot-to-boot-loader-entry") + " (next paragraph). " + c("NO") + " and not "
         + c("AUTH_ADMIN") + ": «challenge» would leave the entry in the menu asking a password, which promises "
         "something that is not there."],
        [c("remotix-remote-sessions.rules"), c("40-remotix-remote-sessions.rules"),
         "Removes the unrequested password windows of a remote session, for <b>six</b> actions only. Catalogue refresh "
         "(" + c("Flatpak.metadata-update") + ", " + c("Flatpak.appstream-update") + ", "
         + c("packagekit.system-sources-refresh") + " and, new on Fedora (21 Nov 2026, register F3), " + c("fwupd.refresh-remote") + ", which GNOME Software asks at login and which covered "
         "the desktop with a password window): " + c("YES") + " for every REMOTIX user, if the machine "
         "gives the seated user " + c("yes") + ". Network control and system repositories ("
         + c("NetworkManager.network-control") + ", " + c("Flatpak.modify-repo") + "): " + c("YES") + " for an "
         "administrator (member of " + c("wheel") + ", Fedora's administrator group, or " + c("sudo") + " or " + c("admin") + ") under the same "
         "condition, " + c("NO") + " for an ordinary user. Everything else: " + c("NOT_HANDLED") + ". A comment in the file still says «five actions»: "
         "a leftover, the code lists six (4 catalogue refreshes and 2 machine actions)."],
    ], "«TAB» — The two polkit rules of the package") + \
    ul([
        "<b>Administrative actions still ask a password,</b> exactly as with " + c("sudo") + ", seated or remote. That "
        "is not touched.",
        "<b>Root needs no exception for power.</b> logind checks the caller's capabilities before polkit, and root "
        "has " + c("CAP_SYS_BOOT") + ", so " + c("sudo systemctl poweroff") + " keeps working. Fedora uses the classic " + c("sudo") + " (Ubuntu 26.04 has sudo-rs); "
        "the behaviour of " + c("CAP_SYS_BOOT") + " with it was not verified on Fedora. The consequence for "
        "testing is that the rule cannot be checked from the root side: it must be checked as the user, from inside "
        "the session. " + c("check-desktop.py") + " does that: logind's " + c("CanPowerOff") + " and its siblings "
        "answer no, " + c("pkcheck") + " refuses the 15 actions it is asked about, and a real " + c("systemctl poweroff") + " as the "
        "user fails (check " + c("power-entries-absent") + "; on Ubuntu the check was adapted to the messages of sudo-rs). The child repeats the question about " + c("CanPowerOff") + ", " + c("CanReboot")
        + ", " + c("CanSuspend") + " and " + c("CanHibernate") + " every time it mounts the stage (" + c("sentinel_shutdown_forbidden()")
        + "): an answer " + c("no") + " or " + c("na") + " («not available here», a virtual machine or a server) counts as safe, any other "
        "answer or an error is an alarm in the log, and the error line names the call and the reason.",
        "<b>Why nineteen and not fifteen (REGISTRO C6, 20 Nov 2026).</b> On a real Debian machine, in front of the machine, the "
        "local user could reboot: logind's " + c("CanReboot") + " said yes and " + c("pkcheck") + " authorised " + c("reboot")
        + ", although the rule says NO to it and the round said «no power off, no reboot». The cause: in logind's policy four actions "
        "that the rule did not forbid (" + c("set-reboot-parameter") + ", " + c("set-reboot-to-firmware-setup") + ", "
        + c("set-reboot-to-boot-loader-menu") + ", " + c("set-reboot-to-boot-loader-entry") + ") carry the annotation "
        + c("org.freedesktop.policykit.imply") + " = " + c("reboot") + " and the default «yes» for the active user seated at the machine; "
        "whoever is authorised for one of them is authorised for " + c("reboot") + " by implication, <b>despite</b> the explicit NO on "
        + c("reboot") + " (an explicit NO is not enough against an implication from an authorised action). The four are now forbidden, "
        "and the version of the package stayed 1.0.0 at the time. With other users logged in, logind asks " + c("reboot-multiple-sessions") + ", which "
        "was and is denied, so the hole let only a local user reboot, only when he was alone on the machine, and it never allowed a "
        "power-off. The round had not seen it because it looked only at the <i>remote</i> session, which is not «seated at the machine» "
        "so the «yes» for the active user does not apply to it, and only at the fifteen actions known by name. The same four annotations were found "
        "on Ubuntu 26.04 (systemd 259.9, 51 policy files read) by the check below, on 20 Nov 2026. <b>On Fedora</b> the rule is the same file as on Ubuntu, and all "
        "its 19 actions exist in the policy of systemd 262 (" + c("org.freedesktop.login1.policy") + " has 37 actions; the 18 not named are the " + c("inhibit-*") + " ones, "
        + c("attach-device") + ", " + c("chvt") + ", " + c("flush-devices") + ", " + c("lock-sessions") + ", " + c("manage") + ", " + c("set-self-linger") + ", " + c("set-user-linger")
        + " and " + c("set-wall-message") + "; study 1 §9.4). The 19 were counted in the rule with its list of action names, " + c("grep -c") + " of the quoted names, not of the word "
        + c("login1") + ", which also appears in comments.",
        "<b>The checks that look from the right places.</b> Two checks of " + c("prove/check-desktop.py") + " were added on 20 Nov 2026, next "
        "to " + c("power-entries-absent") + " (which now says in its header what it does not see). " + c("power-implied") + " needs no session: "
        "it reads the installed rule " + sysf("/usr/share/polkit-1/rules.d/50-remotix-no-poweroff.rules") + " and <b>all</b> the "
        + c(".policy") + " files of the machine, builds the graph of the " + c("imply") + " annotations (chains included) and fails if an action that "
        "is not forbidden implies a forbidden one. " + c("power-local-seat") + " runs from root, with no REMOTIX session, and asks " + c("pkcheck")
        + " about <b>every</b> forbidden action as a process of the active session on " + c("seat0") + " (the greeter's user, the one at the "
        "machine): all must be refused, calibrated against " + c("login1.chvt") + ", which must be granted. In the latest version of the "
        "script the process is one of the session's own non-root user, because the leader of GDM's greeter session can be a root process and "
        "polkit authorises root unconditionally, which would make everything look granted; with no greeter the check answers "
        "BLOCKED. The greeter case, in which someone in front of a machine with nobody logged in might reboot from the login screen's menu, was "
        "<b>deduced</b> when REGISTRO C6 was written and was then <b>measured on Ubuntu</b>; on Fedora the greeter case was <b>not measured</b> (study 1 §9.4: the "
        "power menu is there in the login screen, but the reboot question was not asked). In the final round the checks " + c("power-entries-absent") + ", "
        + c("power-implied") + ", " + c("power-local-seat") + " and " + c("no-password-windows") + " are reported as passed on XFCE (register F22); the " + c("check-desktop.py")
        + " of this tree is not the Ubuntu one (the two files differ). The Ubuntu runs: both checks were run on an Ubuntu 26.04 virtual "
        "machine on 20 Nov 2026 (logs on the Ubuntu tree's dev server, not read for this manual). With the rule at 15 actions (an Ubuntu test package): "
        + c("power-implied") + " FAILED (the four " + c("set-reboot-*") + " imply " + c("reboot") + " on Ubuntu too) and " + c("power-local-seat")
        + " FAILED («polkit GRANTS: reboot» from the greeter's session). With 19 actions (the next Ubuntu test package): both PASS, 19 of 19 "
        "refused, the calibration " + c("chvt") + " granted; that run was a partial round of the desktop check only, 8 PASS plus the known "
        "failure " + c("users-shell-and-environment") + ". The same test from the local user's seat with the corrected package on Debian was not "
        "yet made.",
        "<b>Polkit on Fedora.</b> polkit 127-5 with its vendor rules in " + sysf("/usr/share/polkit-1/rules.d") + " (" + c("20-gdm.rules") + ", " + c("50-default.rules") + ", …); "
        "the administrator group is " + c("wheel") + ", and " + c("/etc/polkit-1/rules.d") + " is readable only by root (study 1 §9.4). There are no snap policies. "
        "Rule 40 was written for polkit 126 and was not re-read against 127 beyond the fact that the helper works.",
        "<b>How the second rule recognises a REMOTIX session.</b> Not from the subject's fields (" + c("local")
        + " and " + c("seat") + " are the same for ssh, and the programs that ask run under the user manager's service, where polkit hands the rule no session) but by " + c("remotix-polkit-seated") + ", a shell script that "
        "reads logind's state files in " + sysf("/run/systemd/sessions") + " for a session of that user with "
        + c("SERVICE=remotix") + ", and prints what the machine gives the seated user for the action (the "
        + c("allow_active") + " of the policy file). It does not use D-Bus, " + c("loginctl") + ", " + c("pkaction")
        + " or " + c("pkcheck") + ": logind's checks call polkitd synchronously, and polkitd would be waiting for "
        "the helper, a deadlock measured at 10 s. The user name is passed as an argument, never inside a script text, "
        "and the script exits 0 always (with systemd 259, read on Ubuntu, the state files keep " + c("SERVICE=") + ", " + c("USER=") + " and " + c("SEAT=")
        + "; the " + c(".ref") + " file that the script skips no longer exists, which is harmless; the files of systemd 262 were not read); anything unexpected becomes "
        + c("none") + ", which the rule turns into "
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
      + ", where nothing reads them (" + c("rpm/remotix-no-suspend.conf") + " and the other file of the package). REMOTIX does not modify the system beyond what it needs (the list of what it changes is in " + rif("What the security model does not defend") + "); an administrator "
      "who wants them copies them into " + c("/etc/systemd/logind.conf.d/") + " and " + c("/etc/systemd/sleep.conf.d/")
      + ". Consequence: without them, a person at the machine can still switch it off with the power button, "
      "and the polkit rule does not see that road, because logind acts on its own account there.")

# ── 14.7 The unit ────────────────────────────────────────────────────────
S7 = p("<b>" + c("remotix.service") + " has no sandboxing directive on purpose.</b> There is no " + c("User=") + ", no "
       + c("ProtectSystem=") + ", no " + c("NoNewPrivileges=") + ", no " + c("PrivateTmp=") + ". The unit's comment "
       "gives the reason: the process systemd starts is the root side, and whatever the unit restricts, every "
       "desktop born from it inherits (" + c("walls.h") + " names " + c("sudo apt install") + " in a remote "
       "desktop as the thing that must keep working; the header still says " + c("sudo apt") + "). The network side's confinement is done in the program (" + c("walls.c") + ") "
       "and in the SELinux domain " + c("remotix_net_t") + ", where only that process receives it.", lead=True) + \
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
        [c("WorkingDirectory"), c("/"), "The service's folder is the root, not a folder of the package."],
        [c("Environment=MESA_SHADER_CACHE_DISABLE"), c("true"), "The codec probe of the root side made Mesa open its shader cache in " + sysf("/root/.cache") + ", which "
         + c("remotix_t") + " may not do, and the cache is useless to a probe that runs once. Only the service's own environment: the users' desktops get theirs from PAM "
         "and keep the cache (register F24)."],
        [c("ExecStartPre"), c("-/usr/libexec/remotix/remotix-pam-hook check"), "Puts the local-login line back into the login screens' PAM files if it is missing, and writes one "
         "summary line. The " + c("-") + " means that a failure never prevents the start (" + rif("The local-login hold") + ")."],
        [c("LimitRTPRIO") + ", " + c("LimitNICE"), "20, -11", "Priority for audio and video."],
        [c("Restart"), c("on-failure") + ", " + c("RestartSec=2") + ", " + c("RestartPreventExitStatus=78"),
         "Exit status 78 (" + c("EX_CONFIG") + ") is for a real configuration error, for example the user "
         + c("remotix") + " missing; it stops the restart loop."],
        [c("WantedBy"), c("multi-user.target"), "Present, but the package does not enable the unit: Fedora's preset is " + c("disable *") + " and " + c("%systemd_post")
         + " honours it, so the administrator runs " + c("sudo systemctl enable --now remotix") + "."],
    ], "«TAB» — The service unit") + \
    warn("The unit does not make REMOTIX safe against a compromised root side. That process runs as root, "
         "in the wide domain " + c("remotix_t") + " (not unconfined, but wide), and runs PAM in grandchildren as root: PAM modules are other people's code loaded into "
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
        ["A compromised root side", "Root, in the wide domain " + c("remotix_t") + " (not unconfined, but wide in six points, " + rif("The SELinux module and its mode") + "), runs PAM. See the warning above."],
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
         "and aarch64 have a seccomp filter. The kernel of Fedora 45 and the Landlock ABI that its network side reports were not read for this manual "
         "(the Ubuntu virtual machines, kernel 7.0, reported ABI 8)."],
        ["SELinux in a session", "The module is <b>enforcing</b>, never permissive. In the final round of 23 Nov 2026 (package " + c("h1") + ") REMOTIX's own AVCs were zero on all four "
         "desktops and the negative proof of the wall had no failure, but " + c("remotix_t") + " is wide in six points (register F27), " + c("prove/giro-selinux.sh") + " hides a "
         "dead check halfway (KDE, " + c("check-kde-exit") + ", the «service restart» case, intermittent), and the open points of the owner's list at 25 Nov 2026 include: "
         + c("force_guard_on") + " staying on after a failed close for a local login (" + c("session.c") + "), " + c("catatonit") + ", a refusal of " + c("search") + " on "
         + sysf("/proc/sys/dev") + " seen on the live KDE, NVIDIA on Fedora 45 (measured on Ubuntu, not run again here), Safari and Firefox on Windows, and IPv6 (" + c("PIANO.md") + "). They are listed and not solved."],
        ["Variables of the user manager", "The snapshot of the user manager's variables can be old after a close made from the root side, "
         "and the question «is the desktop alive» treats an unanswered question as «closed» in two places; not corrected because the "
         "cases are forced (" + c("docs/REGISTRO-problemi.md") + " E3, non-blocking)."],
        ["What the package changes on the machine",
         "<b>The PAM files of the login screens are edited.</b> " + c("remotix-pam-hook") + " creates or changes files in " + sysf("/etc/pam.d") + ": a marked copy of the vendor file "
         "for gdm, plasmalogin and lightdm, and a marked block in the sddm files, which are the sddm package's " + c("%config") + " files (" + rif("The local-login hold")
         + "). It removes them when the package is removed, and never touches the files of authselect. The package also adds " + c("/etc/pam.d/remotix") + " and "
         + c("/etc/remotix/denied-users") + " (both " + c("%config(noreplace)") + "). At a user's first connection the product adds the user to the groups that own the card's render nodes "
         "(" + c("usermod -aG") + ", run as root after PAM said yes and before the child is forked), records it in " + c("/var/lib/remotix/group-enrollments.jsonl")
         + ", and the removal undoes it with " + c("gpasswd -d") + ". For a user manager already running, it "
         "puts a POSIX ACL for the user's private group on " + c("/dev/dri/renderD*") + " and records it in "
         + c("/var/lib/remotix/render-grants") + "; " + c("remotix --drop-render-grants") + " takes it back. Both are "
         "necessary for the card, and both are changes to the system that an administrator should know about. The other things the "
         "package puts on the machine: <b>the SELinux module</b> " + c("remotix") + " (installed by " + c("%post") + ", removed by " + c("%postun") + "); <b>the system dconf database</b> "
         + sysf("/etc/dconf/db/remotix") + " (compiled by " + c("%post") + ", and again by the service at its start if it is missing or different; removed by " + c("%postun")
         + "); <b>the small user file</b> " + sysf("~/.config/dconf/remotix") + " (the keyboard layout of the remote session, three keys, "
         "emptied at every birth; removed on removal as the user, only that regular file, " + rif("GNOME: headless Shell and session dconf")
         + "); <b>the empty file</b> " + sysf("~/.local/share/gnome-shell/lock-warning-shown") + " (made at birth, removed at the end of the "
         "session if REMOTIX made it); <b>the firewalld service definition</b> " + sysf("/usr/lib/firewalld/services/remotix.xml") + " (7447 over TCP and UDP): it only <i>defines</i> the service "
         "and opens nothing, and the administrator opens the port with " + c("sudo firewall-cmd --permanent --add-service=remotix && sudo firewall-cmd --reload")
         + "; the triggers on the packages of the login screens (gdm, lightdm, sddm, plasma-login-manager); and <b>a needrestart rule</b> "
         + sysf("/etc/needrestart/conf.d/remotix.conf") + " (" + c("rpm/needrestart.conf") + ", " + c("$nrconf{override_rc}") + " = 0 for " + c("remotix.service") + "): "
         "restarting REMOTIX closes every remote desktop, and needrestart would otherwise restart it by itself after the update of a library. needrestart is not "
         "installed on a stock Fedora, so the line is harmless there, and " + c("%postun") + " removes the folders " + sysf("/etc/needrestart") + " if needrestart is not present; "
         "whether dnf-automatic respects the rule was not checked. There is <b>no labwc of REMOTIX's own</b> in this package. The removal that leaves the system clean is in "
         + rif("Removal: prerm, postrm and purge") + " (" + c("sudo dnf remove remotix") + ")."],
        ["Hardware and clients not tried", "NVIDIA on Fedora 45 (measured on Ubuntu 26.04 on 5–6 Oct 2026, not run again here), Samsung DeX (tried by the owner only on Debian: not tried on Fedora), a canvas above 3840x2160 (the page's own size ladder stops there; "
         "the protocol canvas is 4096×2304), and the first tap on GNOME touch (the Ubuntu register's E2; on Fedora the cure of F34 is in "
         "place) are open or untried. The hardware of the Fedora tests is the Radeon handed to the test virtual machines (" + c("server/vm-radeon.sh") + "), and, for the owner's hand tests of "
         "25 Nov 2026, a real server with an Intel and a Radeon card. H.264 encoding on the video card is <b>required</b> and on Fedora the drivers come from RPM Fusion "
         "(" + c("mesa-va-drivers-freeworld") + ", decision D1); without them the " + c("%post") + " scriptlet warns that no card encoded a test frame, and VA-API and Vulkan "
         "have no H.264 in the base repositories (study 4, point 1). The security model has not been tested with NVIDIA."],
    ], "«TAB» — What the security model does not cover") + \
    p("The transport limits that bound a flood of connections before login (a cap on connections, on pending "
      "connections and per address) are in " + rif("Transport") + "; the encodings of the identity in the log "
      "are in " + rif("Logging and diagnostics") + ".")

CHAPTER = ("Security model", [
    ("Trust boundaries and the processes of the service", S1),
    ("The closed list between the network side and the root side", S2),
    ("The walls of the network side", S3),
    ("The SELinux module and its mode", S4),
    ("Local excludes remote and the session cap", S5),
    ("The local-login hold", S5C),
    ("The denied-users list", S5B),
    ("Polkit rules, password windows and the power belts", S6),
    ("The service unit and why it is not sandboxed", S7),
    ("What the security model does not defend", S8),
])
