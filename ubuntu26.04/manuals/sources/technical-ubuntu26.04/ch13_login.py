from build import c, code, flow, note, p, rif, sysf, table, ul, warn

# ── 13.1 The path of one login attempt ───────────────────────────────────
PATH_FIG = flow([
    ("Browser", "CREDENTIALS", "dark"),
    ("Network side", "limiter, booking", "blue"),
    ("Root side", "bounds, denied list", "navy"),
    ("PAM dispatcher", "forks, never calls PAM", "light"),
    ("PAM grandchild", "one transaction", "light"),
], "«FIG» — The five hops of a login attempt; the verdict travels back the same way and the browser never receives it "
   "before the fixed answer time", "From the typed password to the verdict")

S1 = p("A login is the one place where an unknown person on the network makes REMOTIX do work as root. The defences "
       "are therefore spread over every hop of the path, and each hop assumes that the previous one may be wrong or "
       "hostile. This chapter follows one " + c("CREDENTIALS") + " message from the browser to PAM and back; "
       "the process shapes themselves are in " + rif("Overall architecture") + ", the wire format in "
       + rif("The RCP/1 protocol") + ", and the isolation of the network side in " + rif("Security model") + ".",
       lead=True) + PATH_FIG + \
    table(["Hop", "Process (uid)", "Code", "What it decides"], [
        ["1", "Network side (system user " + c("remotix") + ")", c("rcp.c") + " (" + c("handle_credentials()") + ")",
         "Range checks on the two strings; the three counters and the ban (" + c("login_reserve()") + "); the fixed "
         "answer time; the byte of the refusal."],
        ["2", "Root side (root)", c("rootside.c") + " (" + c("handle_auth()") + ")",
         "Its own bounds on AUTH messages; the denied-users list and uid 0, before PAM; its own pauses; the "
         "single-use grant for the later birth of the desktop."],
        ["3", "PAM dispatcher (root, child of the root side)", c("helper.c") + " (" + c("dispatcher()") + ")",
         "Reads one request, forks one grandchild, never calls PAM itself."],
        ["4", "PAM grandchild (root)", c("helper.c") + " (" + c("grandchild()") + "), " + c("authentication.c")
         + " (" + c("rcp_authenticate_judged()") + ")",
         "One PAM transaction (authenticate, then account management), one byte back, exit."],
        ["5", "PAM modules", c("src/remotix.pam"), "The administrator's policy: " + c("common-auth") + ", "
         + c("common-account") + ", " + c("pam_faillock") + " if configured (the module is in Ubuntu 26.04's PAM package, but no "
         "line enables it in the stock " + c("common-auth") + "; study 5 §3.1), and the denied-users list again."],
    ], "«TAB» — The hops of a login attempt and who decides what at each") + \
    p("The design rule behind it is invariant I3 (" + c("helper.h") + "): the guard starts from denied. The value "
      + c("true") + " for «admitted» is born at exactly one place, the byte " + c("1") + " that the grandchild "
      "writes after " + c("PAM_SUCCESS") + " on both PAM steps; a lost message, a timeout, a dead process, a short or "
      "mangled answer and any byte other than " + c("1") + " are all a «no».") + \
    p("<b>A login that PAM admits can still be refused.</b> On a machine with a screen the same person may already be at the keyboard "
      "of a local graphical session, and then the answer is " + c("0x05") + " and not a desktop: the rule «local excludes remote» and the "
      "behaviour of the real login screens of GDM, SDDM and LightDM are in " + rif("Local excludes remote and the session cap")
      + " and " + rif("The local-login hold") + ", with what was measured on Ubuntu 26.04 live images.") + \
    note("Everything below describes the packaged service, started with " + c("--split") + " by "
         + c("remotix.service") + ". In that shape the counters of hop 1 live in the network side and the "
         "pause tables of hop 2 live in the root side; the single-process build of the same program ("
         + c("--no-split") + ") exists in the code but is not what the package starts.", "Scope.")

# ── 13.2 The PAM service file ────────────────────────────────────────────
S2 = p("REMOTIX authenticates against its own PAM service, named " + c("remotix") + ", whose file is "
       + c("src/remotix.pam") + ", installed by the package as " + c("/etc/pam.d/remotix") + " (a dpkg conffile, "
       "see " + rif("Files the package installs") + "). The service name is the constant " + c("SERVICE_PAM")
       + " in " + c("authentication.c") + "; the child that later opens the logind session uses the same name "
       "(" + c("pam_start()") + " in " + c("child.c") + ").", lead=True) + \
    p("The file mirrors the system's own " + c("/etc/pam.d/sshd") + " line by line, with one extra line on top (Debian's and Ubuntu's "
      "files are the same). The rule "
      "behind it (" + c("DECISIONS.md") + " §10.18) is that REMOTIX must not drift from the machine's default network "
      "authentication: whatever the administrator puts in " + c("common-auth") + " (lockout with "
      + c("pam_faillock") + ", a second factor module, an LDAP or sssd line) holds for REMOTIX as it does for ssh. "
      "The header of the file says that the comparison with sshd's file was made on 30 Sep 2026, on a Debian 13 image and an Ubuntu "
      "26.04 image (identical to each other), and found 15 lines equal out of 15. Study 5 (§3.1) repeated it for Ubuntu 26.04 on the "
      + c("openssh-server") + " package 1:10.2p1-2ubuntu3.8 extracted in a container: " + c("remotix.pam") + ", without the "
      + c("pam_listfile") + " line, equals the " + c("sshd") + " file line by line, 15 of 15. The comparison on the installed images of "
      "the four flavours was postponed (study 11, item S5.P6) and was not made; for the sessions of the four flavours see the "
      "ordering of the " + c("pam_exec") + " line below. The header of " + c("src/remotix.pam") + " still carries Debian-only wording "
      "(«DEBIAN 13 ONLY», the other distribution families): these are leftovers of the earlier tree and not statements about this "
      "tree.") + \
    table(["Stack", "Lines in " + c("remotix.pam"), "Why"], [
        [c("auth"), c("requisite pam_listfile.so item=user sense=deny file=/etc/remotix/denied-users onerr=fail")
         + ", then " + c("@include common-auth"),
         "Root is refused before any password is tried. It is in " + c("auth") + " and " + c("requisite")
         + ", not in " + c("account") + ": with the line in " + c("account") + " the root password would still be "
         "tried, and «right password, account denied» would answer differently from «wrong password», an oracle for "
         "whoever guesses it. " + c("onerr=fail") + ": if the file is missing or unreadable nobody gets in."],
        [c("account"), c("required pam_nologin.so") + ", then " + c("@include common-account"),
         "Expired or locked accounts. " + c("pam_authenticate()") + " says «this password is right», not «this "
         "account is usable»; " + c("authentication.c") + " calls " + c("pam_acct_mgmt()") + " on purpose."],
        [c("session"), c("pam_selinux") + " (with actions that silence it where the module is absent), "
         + c("pam_loginuid") + ", " + c("pam_keyinit") + ", " + c("@include common-session") + ", " + c("pam_motd")
         + " twice, " + c("pam_mail") + ", " + c("pam_limits") + ", " + c("pam_env") + " twice, " + c("pam_selinux")
         + " open",
         "Never run by the authentication step. It is run by the per-user child (" + c("pam_open_session()")
         + "), and the logind session is born from " + c("pam_systemd") + ", which is inside "
         + c("common-session") + ". On Ubuntu 26.04 with " + c("libpam-sss") + " installed that file holds " + c("pam_umask")
         + ", " + c("pam_unix") + ", " + c("optional pam_sss.so") + " and " + c("optional pam_systemd.so") + " (study 5 §3.1). That include "
         "also carries REMOTIX's own " + c("pam_exec") + " line, after " + c("pam_systemd") + " (next paragraph); for "
         "the service " + c("remotix") + " the program exits at once (" + c("local_login.c") + " leaves service " + c("remotix") + " alone). "
         "The " + c("pam_motd") + " line with " + c("motd=/run/motd.dynamic") + " runs, on Ubuntu, the scripts of " + sysf("/etc/update-motd.d")
         + " at every opening of a session; the latency this adds was not measured (study 5 §3.1)."],
        [c("password"), c("@include common-password"), "Present as in sshd; REMOTIX never changes a password."],
    ], "«TAB» — The four PAM stacks of the " + c("remotix") + " service") + \
    p("<b>The other PAM line the package adds.</b> " + c("/etc/pam.d/common-session") + " is not a REMOTIX file (it belongs to "
      + c("libpam-runtime") + ", which the package depends on, and it is not a conffile of REMOTIX), but the package edits it "
      "through " + c("pam-auth-update") + ": the profile " + c("/usr/share/pam-configs/remotix") + " (" + c("debian/remotix.pam-config")
      + ": " + c("Default: yes") + ", " + c("Priority: -1") + ", " + c("Session-Interactive-Only: yes") + ", " + c("Session-Type: Additional")
      + ") adds " + c("session optional pam_exec.so quiet /usr/libexec/remotix/remotix-local-login") + ". Every service that includes "
      + c("common-session") + " (sshd, su, the display managers, and " + c("/etc/pam.d/remotix") + " itself) runs it at each opening and closing of a session (the non-interactive stack, used for example by cron, "
      "does not carry the line: " + c("Session-Interactive-Only") + "); the program acts only for a graphical session on a seat and returns 0 at once everywhere else, and the line is "
      + c("optional") + ", so it can never make a login fail. What it does, and why, is in " + rif("The local-login hold")
      + "; the package side (postinst, prerm, the dependency) is in " + rif("Files the package installs") + ".") + \
    p("The reason the service is not " + c("login") + ": on Debian and Ubuntu " + c("/etc/pam.d/login") + " is the local console "
      "stack (" + c("pam_securetty") + " and others), policies meant for whoever sits at the machine, and the "
      "network login would inherit them in a way that depends on how that machine is configured. sshd's stack is "
      "the network-access one.") + \
    warn("If " + c("/etc/pam.d/remotix") + " is missing, Linux-PAM falls back to the service " + c("other") + ", "
         "which on Debian and on Ubuntu 26.04 includes the common stacks (study 5 §3.1) and does not exclude root. Two protections live in the "
         "program for that: " + c("look_pam_service()") + " in " + c("main.c") + " says at start-up whether the file "
         "is there, and " + c("why_no()") + " in " + c("authentication.c") + " tells in the log «PAM refused» from "
         "«PAM could not judge» and names this file and the denied-users file in the second case.") + \
    p("Two PAM items are set before authenticating, as sshd does: " + c("PAM_RHOST") + " is the client's bare "
      "address (no brackets, no port, an IPv4-mapped IPv6 address turned back into IPv4; "
      + c("rcp_rhost_from_provenance()") + "), so " + c("pam_faillock") + ", " + c("pam_unix") + " and logind see "
      "where the attempt comes from; " + c("PAM_TTY") + " is the service name.") + \
    note("Some text of the product still mentions other distributions' variants of the file. The one an administrator can "
         "read is a <b>run-time log message</b>, not a comment: when " + c("/etc/pam.d/remotix") + " is missing, " + c("look_pam_service()")
         + " in " + c("main.c") + " writes at start-up a line that begins “the PAM service «remotix» DOES NOT EXIST” and ends "
         "“Install the file of the family: src/remotix.pam (Debian/Ubuntu), .fedora, .suse, .arch.”, and it also says that "
         "on Fedora and Arch the fallback is " + c("pam_deny") + ". On this package the administrator should do one thing: "
         + c("apt install --reinstall remotix") + ". A comment in " + c("authentication.c") + " also quotes a variant of the file "
         "for another distribution. None of those files exists in this tree; the texts are leftovers of the earlier multi-distribution "
         "product and are to be corrected at the next build "
         "(" + rif("Appendix C — Known issues and open points") + ").", "Stale text.")

# ── 13.3 One PAM transaction ─────────────────────────────────────────────
S3 = p("Only one function in the product touches " + c("libpam") + ": " + c("rcp_authenticate_judged()") + " in "
       + c("authentication.c") + ". It is called only by the grandchild of the PAM helper, never by the serving "
       "process. It returns one of three values, which are the byte the grandchild writes back.", lead=True) + \
    table(["Value", "Constant", "Meaning"], [
        [c("1"), c("RCP_PAM_ADMITTED"), "Both " + c("pam_authenticate()") + " and " + c("pam_acct_mgmt()")
         + " returned " + c("PAM_SUCCESS") + ". The only «yes»."],
        [c("0"), c("RCP_PAM_REFUSED"), "Any other outcome, including «PAM could not judge» (a failed "
         + c("pam_start()") + ", a module error)."],
        [c("2"), c("RCP_PAM_REFUSED_LOCKED"), "A refusal while " + c("pam_faillock") + " had the account locked. "
         "Still a «no»; the network side may leave it out of the counters (see below)."],
    ], "«TAB» — The three answers of " + c("rcp_authenticate_judged()")) + \
    p("Details that a maintainer needs:") + \
    ul([
        "Both PAM calls pass " + c("PAM_DISALLOW_NULL_AUTHTOK") + ". sshd refuses empty passwords itself, before "
        "PAM; REMOTIX copied sshd's stack but not that check, and without the flag " + c("pam_unix nullok")
        + " in " + c("common-auth") + " admitted an account with no password whatever was typed (measured 16 Nov "
        "2026 according to the comment in the code). The stock Ubuntu 26.04 " + c("common-auth") + " with " + c("libpam-sss") + " has "
        + c("pam_unix.so nullok") + " followed by " + c("pam_sss.so use_first_pass") + " (study 5 §3.1), so the flag is needed there "
        "too.",
        "The conversation function (" + c("conversation()") + ") answers one kind of question only, the "
        "echo-off prompt, with the password; echo-on prompts and informational messages get no reply. "
        "A conversation of more than 16 messages is refused.",
        "The password copy handed to PAM is freed by libpam, not by REMOTIX. The code does not overwrite it; the "
        "comment documents that Linux-PAM does it in its reply-dropping routine and that anyone porting the file to "
        "another PAM library must re-read that line.",
        "The «locked» judgement is PAM's own, never a guess: the line «The account is locked due to » (constant "
        + c("FAILLOCK_LOCKED") + ") must have been sent through the conversation " + "<i>before</i>" + " the "
        "password prompt, and " + c("pam_authenticate()") + " must have returned " + c("PAM_AUTH_ERR") + ". The text "
        "is matched in English because the program never calls " + c("setlocale()") + "; a translated or silenced "
        "module simply produces value " + c("0") + ", the old behaviour.",
        "Both outcomes of a refusal are one wire answer for the client (" + c("REJECTED") + " with reason "
        + c("0x07") + "), on purpose: telling the outside «your account is locked» would be an oracle. The "
        "distinction exists only in the server log.",
        "The log lines of this file go to " + c("stderr") + ", not through " + c("log.h") + ", because the same "
        "file is compiled into a test host that has no log module. The name in them never appears as typed "
        "(" + rif("What the login logs and what it never logs") + ").",
    ])

# ── 13.4 The PAM helper ──────────────────────────────────────────────────
S4 = p("PAM blocks, and it is not reentrant. A PAM check was measured at 1.0 to 2.2 s (the " + c("helper.h")
       + " header cites 2123, 2198 and 1086 ms medians under the old " + c("login") + " service, measured on Debian; the difference "
       "between a refused and an admitted attempt is the signature of " + c("pam_faildelay") + "; these times were not measured on Ubuntu "
       "26.04, where " + c("pam_sss") + " and " + c("pam_motd") + " may add their own). In a "
       "single-threaded " + c("poll") + " loop that would freeze every connected screen at each login. So PAM runs "
       "in separate processes, by a decision of the owner: a process, not a thread, and one transaction per process.",
       lead=True) + \
    table(["Storey", "Function", "Calls PAM?", "Lifetime"], [
        ["Requester (network side, or the whole server in single-process mode)", c("helper_ask()") + ", "
         + c("helper_move()") + ", " + c("helper_expired()"), "Never",
         "Sends a request on a " + c("SOCK_SEQPACKET") + " socket pair and returns at once."],
        ["Dispatcher", c("dispatcher()") + " (entered by " + c("helper_main()") + ")", "Never",
         "Started once, then restarted by " + c("helper_expired()") + " if it dies. Reads one request, forks."],
        ["Grandchild", c("grandchild()"), "Once", "One transaction, one answer, " + c("_exit(0)") + "; " + c("alarm()")
         + " armed before PAM is called."],
    ], "«TAB» — The three storeys of the PAM helper") + \
    p("Why " + c("SOCK_SEQPACKET") + ": the kernel delimits the messages, so a request cannot arrive halfway and an "
      "answer cannot merge with another grandchild's. With a stream a framing of our own would be needed, and a "
      "parsing defect there would produce «somebody else's answer», invariant I3 broken by a bug.") + \
    table(["Constant", "Value", "File", "Meaning"], [
        [c("MAX_IN_FLIGHT"), "16", c("helper.c"), "Authentications in flight at the same instant. Deliberately "
         "not tied to the session cap: it counts requests lasting seconds, not sessions lasting hours. Beyond it "
         + c("helper_ask()") + " returns false, an immediate refusal that is not counted."],
        [c("RESERVED_FOR_KNOWN"), "2", c("helper.c"), "Of the 16 places, two are kept for a key that "
         + c("rcp_asking_for_known_key()") + " says logged in during the last 30 days, so a flood of fresh addresses "
         "cannot lock the owner out."],
        [c("EXPIRY_MS"), "8000", c("helper.c"), "How long an answer is awaited before it counts as «no». "
         "About four times the slowest known PAM check."],
        [c("GRANDCHILD_ALARM_S"), "20", c("helper.c"), "Kills a grandchild stuck in a module. Longer than the "
         "expiry, so the «no» always comes from the expiry, which is logged."],
        ["Dispatcher cap", "2 × " + c("MAX_IN_FLIGHT"), c("helper.c"), "Counts grandchildren the requester has "
         "already forgotten (expired but alive, or answered but not yet reaped). Over it the answer is outcome "
         + c("3") + " «not checked», never a «no»: a «no» would count towards the ban."],
        [c("RESTART_FIRST_MS") + ", " + c("RESTART_CAP_MS"), "1000, 60000", c("helper.c"),
         "A dead dispatcher is restarted after 1 s, 2 s, 4 s, up to 60 s for deaths in a row; "
         + c("STABLE_MS") + " (60000) of life resets the count; after " + c("LOUD_AFTER") + " (5) deaths the log "
         "says so loudly and the attempts go on."],
    ], "«TAB» — The bounds of the PAM helper") + \
    p("The dispatcher is not only forked but re-executed: " + c("spawn()") + " forks and at once runs "
      + c("/proc/self/exe --pam-helper") + " with its socket on descriptor 3, and " + c("main()") + " sends that "
      "argument to " + c("helper_main()") + " before reading any option, certificate or key. A plain fork would copy "
      "the server's heap, with TLS keys, other users' password buffers and clipboard text, into every grandchild, "
      "and a crashing PAM module would dump all of it into a root core file. " + c("helper_main()") + " refuses to "
      "run unless descriptor 3 is a " + c("SOCK_SEQPACKET") + " socket.") + \
    p("The password lives, on its way, in the requester's buffer and in the receiver's buffer; both are zeroed with "
      + c("explicit_bzero()") + " as soon as they have served. A request of the wrong length is discarded, not "
      "repaired, and expires as a «no». In the split server the same questions travel as " + c("AUTH") + " and "
      + c("VERDICT") + " messages over the root channel and the dispatcher is the root side's child; the network "
      "side never sees it (" + rif("Overall architecture") + ").")

# ── 13.5 The fixed answer time ───────────────────────────────────────────
S5 = p("Without a delay, «no such user» would answer in a millisecond and «wrong password» in fifty, and the "
       "distinction the protocol forbids writing in the reason could be read with a stopwatch. The server therefore "
       "never answers a login sooner than a fixed time, and the time is chosen by the kind of answer, not by "
       "how long PAM took.", lead=True) + \
    table(["Answer", "Wire byte", "Earliest delivery", "Constant"], [
        ["Admitted", "—", "1000 ms after " + c("CREDENTIALS"), c("FIXED_DELAY") + " (" + c("rcp.c") + ")"],
        ["PAM said no (wrong password, unknown user, denied name, locked account, an attempt that got no verdict)",
         c("0x07") + " " + c("WRONG_CREDENTIALS"), "2500 ms", c("REJECT_FLOOR") + " (" + c("rcp.c") + ")"],
        ["The limiter refused (banned, busy, quota, attempt table full)", c("0x08") + " " + c("TOO_MANY_ATTEMPTS"), "1000 ms",
         c("FIXED_DELAY")],
        ["REMOTIX could not check (helper down, over the bounds, cannot verify a local session)",
         c("0x0E") + " " + c("SESSION_UNSERVABLE"), "1000 ms", c("FIXED_DELAY")],
        ["No verdict at all from the helper", "counted as " + c("0x07"), "12000 ms ceiling",
         c("VERDICT_CAP") + " (" + c("rcp.c") + "); the helper's own net is " + c("EXPIRY_MS") + " 8000"],
    ], "«TAB» — When a login answer may leave the server") + \
    p("The floor of 2500 ms for refusals exists because PAM's own failure delay (about 2.0 to 2.2 s for a real user "
      "with a wrong password and for an unknown name, according to the comment citing the " + c("pam-tempi")
      + " measurement) runs inside the helper, while a name rejected by the denied-users list is refused before the "
      "password stage and came back after only the fixed second: the time told whether a name was on the list. "
      "Making every PAM refusal leave not before 2500 ms hides that. It is a floor like " + c("FIXED_DELAY")
      + ": a slower verdict still sets the pace, so a PAM delay above 2.5 s (the comment says it can reach 2.5 s "
      "with the default 2 s base) leaves a residual tail. The comment itself calls the number a margin to be "
      "re-measured, not a proof.") + \
    p("The other bytes are not held to the floor because their own byte already says which road they took, and a "
      "connection in " + c("S_WAIT_VERDICT") + " cannot be evicted by the transport: holding 0x08 and 0x0E answers "
      "for 2.5 s would let about 51 " + c("CREDENTIALS") + " per second fill the 128 pre-login places instead of 128 "
      "per second. A name that the system could not look up (an NSS error) is answered as a plain " + c("0x07")
      + " at the floor, not as " + c("0x0E") + ", for the same reason. This matters on Ubuntu: on Ubuntu Desktop " + sysf("/etc/nsswitch.conf")
      + " has " + c("passwd: files systemd sss") + " (the line " + c("libnss-sss") + " adds, study 5 §3.2), and a lookup of a "
      "non-existent name there may end in an error and not in «not found»; " + c("root_user_lookup()") + " and " + c("user_refused_as()")
      + " in " + c("rootside.c") + " turn that error into a refusal and " + c("handle_auth()") + " answers it like any other (" + c("RXR_NO")
      + "). Study 11 (item S5 N.7) records the check row for this case as verified, with the risk rated low; the times of the Ubuntu rounds "
      "themselves are not in this tree and were not read (not verified).") + \
    p("The check " + c("check-ban.py") + " (wrong-password and same-answer) lists the measured times, requires the "
      "floor, and compares a wrong password with a non-existent user (medians within 500 ms). Its individual times on Ubuntu 26.04 "
      "were not read for this manual: the logs of the rounds are on the dev server and not in this tree (not verified). On the "
      "virtual machines of the Ubuntu bench every client appears to the server as " + c("10.0.2.2") + " (QEMU's user network; " + c("ADDR")
      + " in " + c("check-ban.py") + "), which has no effect on the product.")

# ── 13.6 The counters and the ban ────────────────────────────────────────
S6 = p("The limiter is in " + c("rcp.c") + ", in the network side. It is the rule of " + c("SPECS.md") + " §4.2 "
       "and " + c("DECISIONS-11.md") + " §11.53: three levels of sliding-window counters and, for each level, a "
       "ban whose length grows with repetition.", lead=True) + \
    table(["Level", "Constant index", "Limit", "Window", "A ban closes"], [
        ["(key, user)", c("LK_USER"), "5 failures", "5 min", "that user on that key"],
        ["key", c("LK_KEY"), "20 failures, any user", "5 min", "the key, for every user"],
        ["IPv6 /48", c("LK_NET48"), "30 failures", "10 min", "the whole /48"],
    ], "«TAB» — The three counters (" + c("LIMIT[]") + " and " + c("WINDOW_MS[]") + " in " + c("rcp.c") + ")") + \
    ul([
        "<b>The key</b> is built by " + c("rcp_key_address()") + ": an IPv4 address whole, an IPv6 address reduced "
        "to its /64 (a link-local address too, with its zone cut), an IPv4-mapped or NAT64 address turned back into "
        "the IPv4 inside it, " + c("::1") + " whole. The user level uses the HMAC of the name, never the name.",
        "<b>The ladder</b> (" + c("LADDER_MS[]") + "): the first ban of a level lasts 15 min, the second 1 h, the "
        "third and every later one 12 h. The memory of past bans is forgotten after 24 h without a ban "
        "(" + c("FORGET_MS") + "). The three levels have separate ladders.",
        "<b>The window slides.</b> The time of the last N failures is kept, not their number, so failures at 0:00, "
        "4:59 and 5:01 still count as three. A window anchored to the first failure would never stop someone trying "
        "at a pace just slower than the window.",
        "<b>The attempt in flight counts.</b> " + c("login_reserve()") + " checks and books in one step before PAM "
        "is asked: counters are «failed in the window plus in flight», so sixteen attempts sent together cannot all "
        "pass before the first verdict. At most " + c("MAX_PER_USER_IN_FLIGHT") + " (2) verifications run for the "
        "same (key, user). The key level counts only failures, not attempts in flight, so eight people behind one "
        "NAT logging in together are not refused by their own number.",
        "<b>What counts as a failure:</b> a PAM «no» (value 0), and an attempt that got no verdict (helper timeout, "
        "the 12 s ceiling), because a PAM that does not answer is exactly what an attacker would try to produce. "
        "A late verdict for a connection that has gone is still counted, by name and address ("
        + c("rcp_orphan_verdict()") + ").",
        "<b>What does not count:</b> a refusal in which the question never left (helper off, socket full, 16 already "
        "in flight; " + c("login_release()") + " gives the booking back), a refusal by the limiter itself, a "
        "protocol error, the second connection of the same user (" + c("0x0F") + "). Also a «no» given while "
        + c("pam_faillock") + " had the account locked, but only for a key that logged in within 30 days "
        "(" + c("GOOD_AGE") + ", " + c("GOOD_KEYS") + " = 64 keys): the owner locked out by a stranger must not ban "
        "his own address. For any other key a locked-account «no» is an ordinary failure.",
        "<b>A success</b> clears only the failures of its (key, user). Neither the ladder nor the other two levels "
        "are touched: an attacker with one valid account must not be able to wash the key's count.",
    ]) + \
    p("<b>The table has a bottom.</b> " + c("attempts[]") + " holds " + c("MAX_ATTEMPTS") + " = 256 entries. "
      + c("BAN_QUOTA") + " = 160 of them may be bans; a compile-time assertion keeps room for the counters and the "
      "bookings. A new ban never evicts another ban. When the quota is full, keys that never logged in share one "
      "common counter (" + c("UNKNOWN_LIMIT") + " = 5 in " + c("UNKNOWN_WINDOW_MS") + " = 5 min) and are refused "
      "with " + c("0x08") + " before PAM when it is full: the declared price is that a legitimate new user from an "
      "address that never logged in is refused too, while the quota and that counter are both full. The comment in "
      "the code marks «256 slots are enough» and «5 in 5 min» as not measured.") + \
    p("<b>What the banned person sees.</b> The page still loads and says that the attempts are used up, with the "
      "time left (" + c("rcp_banned()") + " answers for the key and /48 levels only: the page does not know the "
      "user). An attempt at the login gets " + c("0x08") + ". A ban is never silence.") + \
    p("<b>The ban survives a restart</b> (invariant I7). " + c("save_ban()") + " writes " + c("--ban-file")
      + ", which the unit sets to " + c("/var/lib/remotix/net/ban") + " (mode 0600, owner " + c("remotix") + "), "
      "to a temporary file created with " + c("O_EXCL") + " and " + c("O_NOFOLLOW") + ", synced and renamed over the "
      "final name, at every change. " + c("rcp_ban_load()") + " reads it at start-up, after the log secret is "
      "loaded. The format has two kinds of line:") + \
    code("B2 <U|K|N> <level> <epoch> <key>[ <user HMAC>]    # a ban or a remembered level: user, key, /48\n"
         "G2 <epoch of the login> <key or HMAC of the key>   # a key that logged in lately",
         "text", "The ban file (comments added)") + \
    p("The epoch is an absolute time because the in-memory clock is monotonic and restarts with each process. The "
      "file never holds a typed name: the user is a full HMAC-SHA256, and the known keys are HMACs when the log "
      "secret persists. " + c("check-ban.py") + " verifies the file holds no typed name and that the key is still "
      "banned after " + c("systemctl restart remotix") + ".")

S6B = p("The root side applies a second, independent set of bounds, because a network side that has been taken over "
        "must not be able to make PAM an unlimited password oracle (" + c("DECISIONS-11.md") + " §11.50, review "
        "R2). They are in " + c("rootside.h") + " and " + c("rootside.c") + ", all in the root side's memory only "
        "(they do not survive a restart of the root side).", lead=True) + \
    table(["Bound", "Value", "Constant", "Effect"], [
        ["AUTH messages in flight", "16", c("RXR_AUTH_IN_FLIGHT_MAX"), "The same 16 as the PAM helper's table."],
        ["AUTH rate", "3 per second, burst 8", c("RXR_AUTH_PER_S") + ", " + c("RXR_AUTH_BURST"),
         "Above it an AUTH is refused without asking PAM and without looking at the name; the answer is «not "
         "checked» and is not counted. Eight users can log in together; a ninth at the same instant gets that «not checked» answer and tries again."],
        ["(uid, address) pair", "5 refused in 5 min", c("ROOTSIDE_LOGIN_PAIR_LIMIT"),
         "No AUTH for that pair for 15 min, then 1 h, then 12 h; forgotten after 24 h."],
        ["Address", "20 refused in 5 min", c("ROOTSIDE_LOGIN_HOST_LIMIT"), "The same ladder, for any user."],
        ["User alone", "15 refused in 5 min from any addresses", c("ROOTSIDE_LOGIN_USER_LIMIT"),
         "Fixed 15 min pause (" + c("ROOTSIDE_LOGIN_USER_PAUSE_MS") + "), never growing: a stranger who knows a name "
         "must not keep its owner out for good."],
        ["Grant for the birth of the desktop", "30 s, single use", c("RXR_GRANT_LIFE_MS"),
         "Minted after a «yes», bound to (user, address), consumed by the SPAWN."],
    ], "«TAB» — The root side's own bounds on logins") + \
    p("A paused AUTH is answered " + c("RXR_PAUSED") + ": for the browser a plain refusal, " + c("0x07") + " at the "
      "2.5 s floor, counted by the network side like any refusal (except for a key that logged in within 30 days, "
      "by the same rule as the locked account; " + c("refusal_uncounted()") + " in " + c("rcp.c") + "). It is deliberately not " + c("RXR_NOT_CHECKED")
      + " (" + c("0x0E") + " at 1 s): a different byte and a different time would tell anyone who can provoke the "
      "pause that the name exists. The tables never fail open: when the per-user table has no room the AUTH is "
      "refused.") + \
    p("Before any of this, the root side refuses, with the plain «no» and without PAM, an empty name, a name in "
      + c("/etc/remotix/denied-users") + " (comments and blanks allowed, one name per line), uid 0, a name NSS does "
      "not know, a lookup error, and a name whose canonical spelling NSS returns is in the list. A denied-users "
      "file that exists but cannot be read refuses everybody (" + c("user_refused_as()") + "). The same check is "
      "repeated at the SPAWN, and the list is the one the PAM stack reads with " + c("pam_listfile") + ": the package "
      "ships it containing one line, " + c("root") + ".")

# ── 13.7 No administrator unblock ────────────────────────────────────────
S7 = p("There is no administrator command to lift a ban, and that is a decision, not an omission. On 17 Nov 2026 the "
       "owner decided that an unblock command is not a planned function (" + c("docs/DECISIONS-11.md") + " §11.54); the "
       "ban of the address stays at 20 failed attempts in 5 minutes. A ban ends only when its time passes: 15 min, "
       "1 h or 12 h.", lead=True) + \
    p("What the code actually contains, so that nobody is surprised:") + \
    ul([
        c("command.c") + " implements an " + c("UNBLOCK <address>") + " line on a Unix socket (" + c("PING")
        + " answers " + c("PONG") + "; the answers are " + c("REMOVED") + ", " + c("NOT-BANNED") + " and "
        + c("NOT-UNDERSTOOD") + "), calling " + c("rcp_unblock()") + ", which removes every level of the address "
        "and writes a log line. It is opened only when the server is started with " + c("--command-socket")
        + " (" + c("command_open()") + ").",
        "The packaged unit does not pass that option; its comment lists " + c("--command-socket") + " among the "
        "bench options that must not be there. The package ships no CLI either. " + c("check-ban.py")
        + " has a check, " + c("unblock-shipped") + ", that asserts this and passes with the message «by design the "
        "package ships NO administrator unblock».",
        "The option is nevertheless reachable: " + c("REMOTIX_OPTIONS") + " in " + c("/etc/remotix/remotix.conf.d/*.conf")
        + " is appended to the command line of the unit, and " + c("check-ban.py") + " uses exactly that, with a "
        "drop-in that it removes at the end, to unblock its test address. It is a test hook, not a supported "
        "administrator function; it would be reachable by whoever can write that folder, that is by root.",
        "Restarting the service does not lift a ban: the ban file is loaded again (" + c("rcp_ban_load()") + ").",
    ]) + \
    warn("The text the banned person reads is " + c("page.c") + " (the notice with the countdown) and the reason "
         "text for " + c("0x08") + " in " + c("page.html") + ". Both now say that the block ends by itself when the time "
         "is up and that there is no other way back in, which matches the package. " + c("SPECS.md") + " and "
         + c("DECISIONS-11.md") + " still describe an unblock command. See "
         + rif("Appendix C — Known issues and open points") + ".")

# ── 13.8 Logging ─────────────────────────────────────────────────────────
S8 = p("The log is a file that is kept, so the rule is that what is typed by an unauthenticated person never "
       "reaches it. The rules, all in code:", lead=True) + \
    table(["Item", "What is written", "Where in the code"], [
        ["The password", "Never, at any level. Neither is its exact length. It is zeroed in every copy REMOTIX "
         "owns.", c("handle_credentials()") + " (" + c("rcp.c") + "), " + c("helper.c")],
        ["The user name before PAM's «yes»", c("user [a1b2c3]") + " for a name that is an account of this machine, "
         + c("unknown user [a1b2c3]") + " for any other; the six hex digits are the first three bytes of an "
         "HMAC-SHA256 of the name under the server's " + c("log-secret") + ". The same name gives the same tag, so "
         "repeated tries stay recognisable; the secret never leaves the network side. An attempt that the limiter "
         "refuses is written as " + c("user [a1b2c3]") + " whether the name exists or not, because no lookup is "
         "made for it.",
         c("log_user()") + ", " + c("rcp_log_tag()") + " (" + c("rcp.c") + ")"],
        ["The same, from the PAM grandchild", "The network side computes the tag and hands it down; the helper puts "
         "it in the environment variable " + c("REMOTIX_PAM_LOG_TAG") + " of the grandchild, because the "
         "grandchild is a fresh image without the secret. Without a tag the line says " + c("[??????]") + "; the name "
         "still never appears.", c("name_for_log()") + " (" + c("authentication.c") + ")"],
        ["The user name after PAM's «yes»", "By name (admitted lines, the successful login).", c("rcp.c")],
        ["Why PAM said no", "«PAM REFUSED … in pam_authenticate: <text>» or «PAM COULD NOT JUDGE … it is NOT wrong "
         "password», with the locked-account remark when applicable, on " + c("stderr") + ".", c("why_no()")],
        ["Failures and bans", "«failed attempt from [address] as <tag>: n of m for the user, n of m for the address, "
         "n of m for the /48»; «BANNED <level> of <key> for N minutes (ban number k)»; «the ban file is up to date: "
         "N bans in force».", c("rcp.c")],
        ["The address", "In clear: it is the key of the counters.", c("rcp.c")],
        ["The ban file", "Keys and HMACs; no typed name.", c("save_ban()")],
        ["Floods", "The root side writes at most one line per second for refused-before-PAM and over-the-bounds "
         "AUTHs, with a count.", c("handle_auth()")],
    ], "«TAB» — What the login writes to the log and what it never writes") + \
    warn("Two limits of the claim. First, " + c("check-ban.py") + " (typed-names-not-logged) fails only on two "
         "things: a name that does not exist appearing anywhere in the journal of the boot, whoever wrote it, and "
         "the real user's name in REMOTIX's own lines before the verdict. The lines that PAM modules and other "
         "system programs write with the name of an existing user (" + c("pam_unix") + " logs the user and the "
         "address of a failed authentication through syslog; on Ubuntu with " + c("libpam-sss") + " " + c("pam_sss") + " is a second such module, "
         "and whether it writes the name was not checked) are only reported as notes: REMOTIX does not control "
         "them. Second, the log lines of "
         + c("authentication.c") + " go to " + c("stderr") + " and do not pass the cleaning of " + c("log.c")
         + ", which is why the name there is never printed as typed. The log itself is described in "
         + rif("Logging and diagnostics") + ".")

# ── 13.9 Code against SPECS ──────────────────────────────────────────────
S9 = p("Every number in this chapter was read in the code. Against " + c("SPECS.md") + " §4.2 and "
       + c("DECISIONS-11.md") + " §11.53 the result is:", lead=True) + \
    table(["Subject", "SPECS says", "The code does", "Verdict"], [
        ["Counter limits and windows", "5 in 5 min, 20 in 5 min, 30 in 10 min", c("LIMIT[]") + " = 5, 20, 30; "
         + c("WINDOW_MS[]") + " = 5, 5, 10 min", "Equal."],
        ["Ladder and forgetting", "15 min, 1 h, 12 h; 24 h", c("LADDER_MS[]") + ", " + c("FORGET_MS"), "Equal."],
        ["Key", "Whole IPv4, /64 of IPv6", c("rcp_key_address()"), "Equal."],
        ["Success", "Resets only (key, user)", "Same", "Equal."],
        ["Fixed delay", "One fixed second on every answer, «admitted» too",
         "1000 ms for success, " + c("0x08") + " and " + c("0x0E") + "; 2500 ms for a PAM refusal (" + c("REJECT_FLOOR")
         + ")", "Differs: SPECS does not mention the floor."],
        ["Way out of a ban", "The wait passing, or an unblock command on the server (§4.2, table and the sentence "
         "«UNBLOCK &lt;address&gt; removes every level»)", "Only the wait in the packaged product; the socket "
         "exists but is not started", "Differs from the text; the owner's decision of 17 Nov 2026 is the newer."],
        ["Root side's bounds (15 per user, 3 AUTH/s)", "Not in §4.2", c("rootside.h"), "Extra, in the code only."],
        ["Banned person sees", "The page loads and says the attempts are used up", c("rcp_banned()") + ", " + c("page.c"),
         "Equal, except the unblock sentence above."],
    ], "«TAB» — The login defences, SPECS against code") + \
    p("The 1.0 form of the rule (three failed attempts from one address, twelve hours) is kept in " + c("SPECS.md")
      + " §4.2 as history; it is not in the code.") + \
    p("One comment in the code still contradicts the code next to it, and the code wins: " + c("rootside.h")
      + " says a paused request gets «not checked» and is not counted (it gets " + c("RXR_PAUSED") + ", a plain refusal that is counted unless the key logged in within 30 days, as "
      + c("rootside_proto.h") + " and " + c("rootside.c") + " say). The other two that this manual used to list, the key limit "
      "written as 12 in " + c("rootside.h") + " and in " + c("check-ban.py") + ", were corrected on 17 Nov 2026 (both say 20 now).")

CHAPTER = ("Login and its defences", [
    ("The path of one login attempt", S1),
    ("The PAM service file remotix.pam", S2),
    ("One PAM transaction in authentication.c", S3),
    ("The PAM helper: dispatcher and grandchild", S4),
    ("The fixed answer time and the floor of a refusal", S5),
    ("The three counters and the progressive ban", S6),
    ("The root side's own bounds on logins", S6B),
    ("No administrator unblock, by design", S7),
    ("What the login logs and what it never logs", S8),
    ("Login defences against SPECS", S9),
])
