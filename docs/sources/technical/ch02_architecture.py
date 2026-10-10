from build import arrow, box, c, fig, flow, note, p, path, rif, table, text, tip, warn, zone

S1 = p("REMOTIX grew out of a few rules, most of them written before the code and each paid for by a measurement or "
       "a defect. They explain choices that would otherwise look odd: a root server that never touches the user's "
       "desktop, a separate process for every password check, a desktop that outlives the server.", lead=True) + \
    table(["Principle", "What it means in the code", "Where it comes from"], [
        ["<b>Detect capabilities, not the distribution</b>", "At startup the server checks what is there — which "
         "desktop, which GPU encodes which codec, whether the PAM file exists — chooses the best path and writes "
         "in the log what is missing", "SPECIFICHE.md §2.1"],
        ["<b>Degrade, but say so</b>", "Every missing piece has a fallback, and every fallback is written in the "
         "log: a silent fallback gives two behaviours under the same label", "SPECIFICHE.md §2.2, " + c("CODER.md")
         + " §4.2"],
        ["<b>Depend, do not rewrite</b>", "logind, PAM, PipeWire, libei, xkbcommon, ngtcp2: one of each, the same "
         "everywhere, used as they are", "SPECIFICHE.md §2.3"],
        ["<b>Depend on the compositor, not on its surroundings</b>", "Only the compositor delivers frames and "
         "accepts input, so " + c("mutter.c") + ", " + c("kwin.c") + " and " + c("wlroots.c") + " exist. Screen "
         "lockers, idle daemons, power managers and display managers are not chased: REMOTIX keeps its own lock "
         "(the 30-minute detach) and turns theirs off", "DECISIONI.md §0.1"],
        ["<b>Talk to the compositor directly</b>", "Private D-Bus and Wayland interfaces, never "
         + c("xdg-desktop-portal") + ": a portal asks a person in front of the screen for permission, and an "
         "unattended server has nobody to click", "SPECIFICHE.md §2.5"],
        ["<b>No exceptions per compositor</b>", "A feature that works on one desktop and not on another leaves the "
         "product instead of hiding behind a switch (live resizing left on 17 August 2026 for this reason)",
         "DECISIONI.md §0.1, §5.1-bis"],
        ["<b>On the user's screen, their desktop and nothing else</b>", "No marks, no service boxes; test functions "
         "are not in the installed binary", "SPECIFICHE.md §2.6, DECISIONI.md §7.16"],
        ["<b>One job per process</b>", "The server checks passwords through a helper process and captures through "
         "a child process per user, because root cannot join a user's session bus and only root can verify "
         "another user's password", "DECISIONI.md §1.10, §1.10-bis"],
        ["<b>The server never ends a healthy session without a reason</b>", "Every close carries a reason code of "
         + c("RCP.md") + " §8.2 and a sentence the user reads; only the user ends their session", "DECISIONI.md §4.1-bis"],
        ["<b>Encode on the GPU only</b>", "VA-API or Vulkan Video; a machine without a GPU that encodes declares "
         "it at startup and offers no codec", "DECISIONI.md §10.27"],
        ["<b>REMOTIX does not modify the system</b>", "It says what it needs; the administrator provides it. The "
         "one deliberate exception: adding users to the GPU's groups, so that their session is not blind",
         "DECISIONI.md §10.36, §7.21"],
        ["<b>No GPL dependencies</b>", "All the server's libraries are MIT, BSD or Apache", "SPECIFICHE.md §11.4"],
    ], "«TAB» — The principles that shaped REMOTIX") + \
    p("Eight <b>invariants</b>, inherited from v1 and renumbered in " + c("CODER.md") + " §2, are quoted in the "
      "comments next to the lines that keep them. A change that breaks one of them is a defect even if every test "
      "passes.") + \
    table(["", "Invariant", "Where the code keeps it"], [
        ["I1", "The frame rate never drops out of prudence or because the scene is still: only when a measurement "
         "proves the line cannot carry it, and every drop is logged. Below the minimum, frames go — never "
         "resolution, and never the connection", rif("Quality, degradation and budget")],
        ["I2", "One graphical session per user; a local session wins over the remote one; a second remote "
         "connection is refused with an explicit reason", c("figli_assicura()") + " looks before forking; "
         + c("GIA_ATTIVA_REMOTA") + " (already active remotely) in " + c("rcp.c")],
        ["I3", "The authentication guard starts from “denied”: whoever has not passed the validator receives no "
         "pixel and controls nothing", "the single " + c("1") + " byte of the PAM helper; the kernel-stamped "
         "credentials on every child message"],
        ["I4", "The stage (capture, control, virtual monitor) belongs to the session, not to the connection, and "
         "survives detaching", "no line ties a child's life to a connection; the desktop starts with "
         + c("setsid --fork")],
        ["I5", "The volume belongs to the session: whoever connects finds it at maximum", c("suono.c")],
        ["I6", "Anything that changes what the user sees stays behind a switch that is off until the user has "
         "looked at it", "the switches of " + c("main.c") + " are logged at startup, on and off"],
        ["I7", "The protection against a known defect lives in the program, not in a configuration line that can "
         "be lost", "headless and power-off checks done by the child after startup"],
        ["I8", "The measure is what the user sees, not the number a bench prints", "the benches drive real "
         "browsers (" + rif("Testing") + ")"],
    ], "«TAB» — The eight invariants")

PROCESSI = fig(
    zone(20, 12, 420, 290, "remotix.service (system.slice)")
    + box(40, 44, 380, 52, "remotix — the server", "root · one poll loop · ports, TLS, QUIC, RCP", "navy")
    + box(40, 128, 180, 52, "PAM dispatcher", "root · started once, forks", "dark")
    + box(240, 128, 180, 52, "Codec probe", "root · at startup, then exits", "grey")
    + box(40, 222, 180, 52, "PAM check", "root · one transaction, exits", "dark")
    + box(240, 222, 180, 52, "usermod, loginctl", "root · first login only", "grey")
    + arrow(130, 98, 130, 126) + arrow(330, 98, 330, 126, "#475569") + arrow(130, 182, 130, 220)
    + path([(422, 80), (432, 80), (432, 248), (422, 248)], "#475569")
    + zone(470, 12, 410, 135, "logind session of user A (session scope)")
    + box(490, 44, 175, 52, "Child of A", "--figlio-interno · uid of A", "blue")
    + box(690, 44, 170, 52, "Desktop of A", "compositor + programs", "light")
    + zone(470, 167, 410, 135, "logind session of user B (session scope)")
    + box(490, 199, 175, 52, "Child of B", "--figlio-interno · uid of B", "blue")
    + box(690, 199, 170, 52, "Desktop of B", "compositor + programs", "light")
    + arrow(422, 62, 488, 62) + arrow(422, 82, 488, 214)
    + arrow(667, 70, 688, 70, "#475569", True) + arrow(667, 225, 688, 225, "#475569", True)
    + text(675, 122, "setsid --fork", 10.5, "#334155") + text(675, 277, "setsid --fork", 10.5, "#334155"),
    900, 314, "«FIG» — The processes: the server's tree, and one child per user (fork, PAM session, execve) in that user's logind session")

S2 = p("REMOTIX is one binary, " + c("/usr/libexec/remotix/remotix") + ", that plays several roles. The server "
       "forks the others; the children re-execute the same binary with " + c("--figlio-interno") + " (internal child) so that they "
       "start from a clean process image, as a different user.", lead=True) + PROCESSI + \
    table(["Process", "Runs as", "Born", "Dies", "Job"], [
        [c("remotix") + " (the server)", "root", "started by systemd (" + c("ExecStart") + ")",
         "on " + c("SIGTERM") + "/" + c("SIGINT") + ", after saying farewell to every client",
         "ports, TLS, QUIC, RCP, the ban, the bridge between connections and children"],
        ["codec probe", "root", "forked by " + c("figlio_capacita_video()") + " at startup, before the ports are opened",
         "after writing its result on a pipe (the server waits at most 30 s)",
         "opens each GPU encoder on a 256×256 frame to decide which codecs the " + c("ECCOMI") + " (the server's "
         "answer to the client's hello) offers"],
        ["PAM dispatcher", "root", c("aiutante_accendi()") + ", before the ports are open",
         "with the server (" + c("PR_SET_PDEATHSIG") + ", or end of file on its socket)",
         "reads a request and forks; never calls PAM itself"],
        ["PAM check", "root", "one per password check", "after writing one result; an " + c("alarm(20)")
         + " kills it if a PAM module hangs", "one " + c("pam_authenticate") + " + " + c("pam_acct_mgmt")],
        [c("remotix-figlio --figlio-interno"), "the user", "when PAM says yes and the user has no child yet "
         "(" + c("figli_assicura_da()") + ")", "when their graphical session ends, when the server stops, or as soon "
         "as its identity does not match", "opens the user's logind session, starts the desktop, holds the stage"],
        [c("usermod") + ", " + c("loginctl"), "root", "at a user's first login, if they are not in the GPU's groups",
         "when the command ends", "adds the user to the groups of " + c("/dev/dri") + " (" + rif("Birth of a session")
         + ")"],
        ["the desktop", "the user", "started by the child with " + c("setsid --fork sh -c 'exec …'"),
         "at logout or when the session is abandoned", "the compositor and the user's programs"],
    ], "«TAB» — The processes and their lives") + \
    p("Two facts shape this tree. The desktop is started from inside the user's logind session, so it lives in that "
      "session's scope and not in the cgroup of " + c("remotix.service") + ": stopping the service (" + c("KillMode=mixed")
      + ") does not kill it. And the child is the leader of that logind session (it opened it with "
      + c("pam_open_session") + "): when the user logs out, logind ends the session and takes the child with it.") + \
    note("the sentinel (" + c("sentinella.c") + ") and the found-again search (" + c("ritrovo.c") + ") are not "
         "processes: they are modules that ask logind synchronously, with a short timeout, from inside the loop of "
         "whoever calls them (" + rif("The logind sentinel") + ").", "Not processes.")

GIRO = flow([
    ("poll()", "≤ 1000 ms", "navy"),
    ("Transport", "UDP in, QUIC timers", "blue"),
    ("Clocks", "abandonment", "blue"),
    ("PAM", "verdicts, expiries", "dark"),
    ("Children", "messages, reaping", "blue"),
    ("Page, socket", "TCP and unblock", "light"),
], "«FIG» — One turn of the server's loop", width=900)

S3 = p("The server is a single thread around one " + c("poll()") + " in " + c("main()") + ". Everything that could "
       "block — PAM, a user's D-Bus, PipeWire, the GPU — lives in another process, so that one user logging in "
       "never freezes the frames of the others.", lead=True) + GIRO + \
    table(["Descriptor", "Who", "Handled by"], [
        ["the UDP socket (QUIC, every connection)", c("trasporto.c"), c("trasporto_leggi()") + ", then "
         + c("trasporto_scaduti()") + " for the timers"],
        ["the TCP listener and its connections (the page)", c("pagina.c"), c("pagina_muovi()")],
        ["the unblock socket, if " + c("--comando-socket") + " was given", c("comando.c"), c("comando_muovi()")],
        ["the PAM helper's socket", c("aiutante.c"), c("aiutante_muovi()") + " delivers each verdict to "
         + c("consegna_verdetto()")],
        ["one socket per child", c("figlio.c"), c("figli_muovi()") + ": checks, reassembles, dispatches"],
    ], "«TAB» — What the server's poll waits on (at most 64 descriptors, MAX_POLL)") + \
    p("The wait is the time to the next QUIC timer (" + c("trasporto_attesa_ms()") + "), capped at one second so that "
      "clocks that do not wait for an event still fire; with the test tone of " + c("--audio-prova") + " it is "
      "capped at 10 ms. After every wake-up the loop runs, in this order: " + c("trasporto_leggi()") + ", "
      + c("wt_giro_del_padre()") + ", the abandonment clock (" + c("abbandono_giro()")
      + "), " + c("ritrovati_ripassa()") + ", the PAM verdicts and expiries, " + c("figli_muovi()") + ", "
      + c("figli_ricontrolla()") + ", " + c("trasporto_scaduti()") + ", " + c("pagina_muovi()") + " and "
      + c("comando_muovi()") + ". Three slower duties hang off the same loop: every 2 s ("
      + c("RIPASSO_LOCALI_MS") + ") the sweep that looks for local sessions, every 60 s a log line with the "
      "sentinel's counters, and every 60 s the certificate rotation check.") + \
    p("<b>Why one thread.</b> Since 12 August 2026 the server process touches neither GLib nor PipeWire nor a user's "
      "D-Bus (those moved into the children). So the " + c("fork()") + " that creates a child starts from a "
      "process with one thread — the only condition in which forking a program that links threaded libraries is "
      "safe. The PAM verdict used to block this loop: measured on 11 August 2026 on the test machine (Intel "
      "i5-13500T), 1.0 to 2.2 s per attempt, most of it added by " + c("pam_faildelay") + " on failed attempts. "
      "With video that would have frozen every user's screen whenever someone else logged in (DECISIONI.md §1.10).") + \
    p("<b>The bridge.</b> " + c("main.c") + " is the only file that knows both the transport and the children. A "
      "small " + c("struct ponte") + " carries the two, and " + c("webtransport.c") + " and " + c("figlio.c")
      + " call each other only through hooks registered at startup:") + \
    table(["Direction", "Hook in main.c", "What crosses"], [
        ["child → clients", c("deposita_fotogramma()"), "an encoded frame: counted by the budget, then sent to "
         "every RCP session admitted for that user name (" + c("wt_video_diffondi()") + ")"],
        ["child → clients", c("cursore_dal_palco()") + ", " + c("audio_blocco()"), "cursor shape; audio blocks"],
        ["child → clients", c("tela_dal_palco()") + ", " + c("tela_attendi_dal_figlio()"),
         "the canvas the stage really has; “wait, the stage is not there yet”"],
        ["child → clients", c("appunti_dalla_sessione()") + ", " + c("appunti_richiesta_dalla_sessione()"),
         "clipboard text and paste requests"],
        ["child → clients", c("sessione_finita_dal_figlio()") + ", " + c("congeda_figlio()"),
         "the graphical session ended; the child is gone (both send farewell " + c("0x10") + ")"],
        ["clients → child", c("video_chiedi()") + ", " + c("audio_chiedi()"), "start or stop capturing, with the "
         "negotiated codec"],
        ["clients → child", c("input_al_figlio()") + ", " + c("ritela_al_figlio()") + ", "
         + c("disposizione_al_figlio()"), "input events (they also feed the abandonment clock), the canvas, the "
         "keyboard layout"],
        ["clients → child", c("termina_al_figlio()"), "the user asked to end the session"],
        ["clients → child", c("appunti_offri_al_figlio()") + ", " + c("appunti_risposta_al_figlio()"),
         "clipboard offers and answers"],
        ["RCP → logind", c("chiedi_sessione_locale()") + ", " + c("ripassa_sessioni_locali()"),
         "does this user, or do these users, have a local graphical session"],
    ], "«TAB» — The hooks that join the transport and the children")

S4 = p("Checking a password is the only thing the server needs root for besides changing user, and PAM can take "
       "seconds. So it happens in another process, in a three-tier shape decided by the user on 11 August 2026: a "
       "process, not a thread, because PAM is not reliably reentrant.", lead=True) + \
    table(["Tier", "What it does", "Why"], [
        ["the server", "writes a request on a " + c("SOCK_SEQPACKET") + " socket pair and goes back to "
         + c("poll()"), "the loop never waits for PAM"],
        ["the dispatcher", "started once by " + c("aiutante_accendi()") + "; reads a request, forks, zeroes its "
         "copy of the password; " + c("SIGCHLD") + " ignored so the kernel reaps the grandchildren",
         "it never calls PAM, so it can never hang"],
        ["the grandchild", "arms " + c("alarm(20)") + ", calls " + c("rcp_autentica_da()") + " once, sends "
         "back the request number and one byte, exits", "no process ever touches libpam twice: reentrancy is not "
         "at stake, and ten users logging in together do not queue"],
    ], "«TAB» — The three tiers of the PAM helper") + \
    p("The request carries the case number (" + c("pratica") + ", 64 bits), the user name (up to 256 bytes), the "
      "password (up to 1024) and the client's bare address for " + c("PAM_RHOST") + " (taken from the "
      + c("[address]:port") + " form, with an IPv4-mapped prefix removed). The grandchild runs the service "
      + c("remotix") + " with " + c("PAM_TTY") + " set to " + c("remotix") + ", a conversation that answers only "
      "the hidden prompt with the password, then " + c("pam_authenticate") + " and " + c("pam_acct_mgmt")
      + ": only when both return " + c("PAM_SUCCESS") + " does it write the byte " + c("1") + ".") + \
    table(["What can go wrong", "Outcome"], [
        ["the helper did not start", c("aiutante_chiedi()") + " returns false: “no” at once"],
        ["the socket is full", "“no” at once"],
        ["more than 16 checks in flight (" + c("MAX_IN_VOLO") + ")", "“no” at once"],
        ["the dispatcher died", "every check in flight becomes “no”"],
        ["a grandchild died without answering", "the check expires after 8 s (" + c("SCADENZA_MS")
         + "): “no”; a second net in " + c("rcp.c") + " expires it after 12 s (" + c("TETTO_VERDETTO") + ")"],
        ["a short or garbled answer", "discarded; then it expires"],
        ["any byte other than exactly " + c("1"), "“no”"],
    ], "«TAB» — Invariant I3: every failure of the helper is a “no”") + \
    p("The password is in clear in the server's memory, in the request buffer and in the dispatcher: each copy is "
      "zeroed as soon as it has been used, and none reaches the log (" + c("RCP.md") + " §4.4). The socket pair has "
      "no name in the filesystem and dies with the two processes. The helper is started <b>before</b> "
      + c("trasporto_apri()") + " on purpose: a process forked later would inherit the UDP socket and the TCP "
      "listener and keep the port busy after the server died.") + \
    note("the in-flight cap of 16 is not the session cap and was deliberately left separate when every other copy "
         "of the session count was unified on 25 August 2026: it is how many password checks run at once, a "
         "different quantity.", "MAX_IN_VOLO.")

S5 = p("For every admitted user the server forks one child that becomes that user. Two facts measured on 12 August "
       "2026 force this shape (DECISIONI.md §1.10-bis): root cannot connect to a user's session bus — "
       + c("gdbus") + " to Mutter fails with “The connection is closed” — and only root can verify another user's "
       "password with PAM, because " + c("pam_unix") + " outside root goes through " + c("unix_chkpwd") + ". Without "
       "the bus there is no capture; without root there is no authentication.", lead=True) + \
    p("<b>Before forking</b>, " + c("figli_assicura_da()") + " looks for an existing child of that user and returns "
      "it (I2: two connections of the same user share one child, and one stage). It refuses, with a log line, a full "
      "table, a name that PAM admitted but NSS cannot resolve, and uid 0 (the child exists not to be root). It then "
      "adds the user to the GPU's groups if needed (" + rif("Birth of a session") + "), opens a "
      + c("SOCK_SEQPACKET") + " pair with " + c("SO_PASSCRED") + " on the server's end — refusing, again with a "
      "log line, if either fails — and forks. In the forked process " + c("diventa_ed_esegui()") + " does, in order:") + \
    table(["Step", "What", "Why"], [
        ["1", "moves its end of the socket to descriptor 3 and closes every descriptor from 4 up ("
         + c("close_range") + ")", "the child is forked after the ports are open and must not keep them"],
        ["2", c("pam_start(\"remotix\", user)") + " with a mute conversation; " + c("XDG_SESSION_TYPE=wayland")
         + ", " + c("XDG_SESSION_CLASS=user") + ", " + c("PAM_RHOST") + ", " + c("PAM_TTY") + "; no "
         + c("XDG_SEAT"), "without a logind session Mutter asks " + c("sd_pid_get_session()") + ", gets ENXIO and "
         "dies; no seat makes the session headless by construction"],
        ["3", c("pam_open_session") + ", then " + c("pam_getenvlist") + " and the SELinux level the way "
         + c("sshd") + " does it; " + c("pam_end") + " <b>without</b> " + c("pam_close_session"),
         "the logind session belongs to its leader process, this one after the exec, and logind takes it back when "
         "it dies"],
        ["4", c("setgroups") + ", " + c("setgid") + ", " + c("setuid") + ", then " + c("getresuid")
         + "/" + c("getresgid") + " must return the user's ids three times", "the drop is verified with the kernel, "
         "not assumed (exit 35 or 36 otherwise)"],
        ["5", "an environment built from scratch: " + c("HOME") + ", " + c("USER") + ", " + c("LOGNAME") + ", "
         + c("PATH=/usr/local/bin:/usr/bin:/bin") + ", an empty " + c("SHELL") + ", " + c("XDG_RUNTIME_DIR")
         + ", " + c("DBUS_SESSION_BUS_ADDRESS") + ", and " + c("XDG_SESSION_ID") + " as PAM returned it",
         "nothing of root's environment leaks; the session id is read, not invented"],
        ["6", c("execve") + " of the server's own binary, resolved from " + c("/proc/self/exe") + " at startup",
         "a clean image; the binary is the one KWin's permission names (" + rif("Screen capture per compositor")
         + ")"],
    ], "«TAB» — How a child becomes its user") + \
    p("The child's command line is " + c("remotix-figlio --figlio-interno <user> <uid> <gid> <width> <height> "
      "<serial> <dir|->") + ", followed by the switches the child must share with the server: " + c("--parlantina")
      + " (verbose log), " + c("--journal") + ", " + c("--qualita-risale") + " (let the quality climb back), "
      + c("--tetto-banda-mbit N") + " (the bandwidth floor in Mbit/s), " + c("--niente-audio-silenzio")
      + " (do not suppress silent audio blocks) and " + c("--codifica vulkan|vaapi") + " (the encoding path). They travel on the command "
      "line because the environment is rebuilt from nothing. The server refuses to fork children if its own "
      "binary was replaced on disk (" + c("/proc/self/exe") + " ends with " + c("(deleted)") + ").") + \
    p("<b>Identity is a fact of the kernel, not a promise of the code.</b> Once running, " + c("figlio_vive()")
      + " sets " + c("PR_SET_PDEATHSIG") + " (" + c("SIGTERM") + "), checks its ids again (exit 42 if wrong) and "
      "introduces itself with " + c("MSG_SONO") + " — real, effective and saved ids, parent pid, how many "
      "descriptors are still open, whether its runtime directory and bus socket exist. It must do so within 15 s ("
      + c("SCADENZA_SONO_MS") + ") or the server kills it. On every message the server reads the "
      + c("SCM_CREDENTIALS") + " the kernel attached and requires: the child's pid, the user's uid and gid, the "
      "child's serial number, the uid declared in the header, and that the user name still resolves to that uid "
      "(" + c("credenziali_combaciano()") + "). Any mismatch: " + c("SIGKILL") + ". Every 60 s ("
      + c("RICONTROLLO_MS") + ") the server asks “who are you” again.") + \
    table(["Exit", "Meaning"], [
        ["0", "it finished its job (the graphical session ended, or it was told to stop)"],
        ["30", "could not move its socket to descriptor 3"],
        ["31 · 32 · 33", "could not take the user's groups · gid · uid"],
        ["34", "could not ask the kernel who it is"],
        ["35 · 36", "the kernel reports a uid · gid other than the user's: stopped before running anything"],
        ["37", "could not execute the server's binary"],
        ["40", "started with a command line that is not its own"],
        ["41 · 42", "after the exec: could not ask the kernel · is not who it should be"],
        ["43", "could not introduce itself to the server"],
    ], "«TAB» — The child's exit codes, as the server explains them (perche_uscito())") + \
    warn("the child keeps no deadline after its introduction: a silent child is one nobody is asking anything "
         "(I4). Its life is tied to the graphical session, never to a connection.", "No idle timeout.")

S6 = p("Server and children talk over the " + c("SOCK_SEQPACKET") + " pair created at the fork: the kernel keeps "
       "message boundaries, so a message can neither arrive in halves nor merge with the next one. Every message "
       "starts with the same header.", lead=True) + \
    table(["Field", "Type", "Value"], [
        [c("magia") + " (magic)", "4 bytes", c("FIG1")],
        [c("tipo") + " (type)", "u16", "the message type, below"],
        [c("versione"), "u16", c("FIGLIO_VERSIONE") + " = 1"],
        [c("matricola") + " (serial)", "u64", "the child's serial number, given by the server at the fork"],
        [c("uid_dichiarato") + " (declared uid)", "u32", "the uid the sender claims; checked against the kernel's credentials"],
        [c("byte"), "u32", "bytes of body after the header"],
    ], "«TAB» — The header of a server–child message (struct testa)") + \
    table(["Type", "Name", "Direction", "Body"], [
        ["1", c("MSG_CHI_SEI"), "server → child", "none: “who are you”, every 60 s"],
        ["2", c("MSG_SPEGNITI"), "server → child", "none: stop"],
        ["3", c("MSG_RIMANDA_PALCO"), "server → child", "none: send again the frames you keep (a client reattached)"],
        ["4", c("MSG_VIDEO"), "server → child", "codec (0 = stop capturing), keyframe due, bit depth, level ×10"],
        ["5", c("MSG_INPUT"), "server → child", "id, action, pressed, evdev code, two 32-bit values; the actions "
         "include the canvas (" + c("FIGLI_INPUT_RITELA") + ") and the end of the session ("
         + c("FIGLI_INPUT_TERMINA") + ")"],
        ["6", c("MSG_DISPOSIZIONE"), "server → child", "the keyboard layout name (64 characters)"],
        ["7", c("MSG_AUDIO"), "server → child", "audio codec, 0 = stop"],
        ["8 · 9", c("MSG_APPUNTI_OFFERTA") + " · " + c("MSG_APPUNTI_DAL_CLIENT"), "server → child",
         "the client offers text · the text, in pieces"],
        ["10", c("MSG_SONO"), "child → server", "who the child is (" + c("struct corpo_sono") + ")"],
        ["11", c("MSG_PALCO"), "child → server", "outcome of mounting the stage: bus, session state, capture, "
         "monitor, size, how many streams encoded, the failure in words"],
        ["12", c("MSG_FOTOGRAMMA"), "child → server", "an encoded frame, in pieces"],
        ["13", c("MSG_CURSORE"), "child → server", "the cursor image, in pieces"],
        ["14", c("MSG_TELA"), "child → server", "canvas wanted, canvas obtained (0×0 = failed), or “wait”"],
        ["15", c("MSG_SESSIONE_FINITA"), "child → server", "none: the graphical session ended"],
        ["16", c("MSG_BLOCCO"), "child → server", "an audio block with its timestamp"],
        ["17 · 18", c("MSG_APPUNTI_DALLA_SESSIONE") + " · " + c("MSG_APPUNTI_VUOLE"), "child → server",
         "the session copied text · something in the session is pasting"],
    ], "«TAB» — The messages between server and child") + \
    p("Large payloads — frames, cursor images, clipboard text — are cut into pieces of at most 32 KiB ("
      + c("PEZZO_MAX") + ") with total, offset and piece length, and reassembled on the other side. A frame may be "
      "up to 16 MiB (" + c("FOTOGRAMMA_MAX") + "), the same limit as " + c("RCP.md") + " §6.2, so that no limit "
      "of ours is lower than the protocol's. The frame's " + c("input") + " field is stamped by the child at "
      "capture time with the last input it injected: only the child knows what the compositor had actually "
      "received, and stamping it in the server would make the measured delay shorter than the real one.")

S7 = p("The sentinel answers three questions for which logind is the authority, through the <b>system</b> bus, "
       "synchronously and with a 300 ms timeout (" + c("ATTESA_MS") + "): a short wait is cheaper than a thread "
       "and a mutex in a server that has one thread on purpose.", lead=True) + \
    table(["Question", "Function", "Asked by", "Used for"], [
        ["Does this user have a local graphical session now?", c("sentinella_locale()"), "the server, at "
         + c("ATTACCA"), "refusing the attach with " + c("0x05 GIA_ATTIVA_LOCALE") + " (already active locally)"],
        ["Which of these users have one?", c("sentinella_locali()"), "the server, every 2 s",
         "dismissing a remote client with " + c("0x04 SESSIONE_LOCALE_PREVALSA") + " (the local session prevailed)"],
        ["Is my session without a seat?", c("sentinella_senza_seat()"), "the child, once, after the first stage",
         "proving the session is headless (DECISIONI.md §4.3-bis)"],
        ["Is power-off really forbidden?", c("sentinella_spegnimento_vietato()"), "the child, once",
         "proving the belts are in force: " + c("CanPowerOff") + ", " + c("CanReboot") + ", "
         + c("CanSuspend") + " and " + c("CanHibernate") + " must all say " + c("no")],
    ], "«TAB» — What the sentinel is asked") + \
    p("<b>A local session is one with a seat.</b> The obvious criterion — graphical type and " + c("Remote=no")
      + " — would make REMOTIX refuse itself: logind marked REMOTIX's own sessions " + c("Remote=no") + " as long as "
      "no " + c("PAM_RHOST") + " was set. The discriminating fact is the seat: a local session sits on "
      + c("seat0") + ", with a real screen and keyboard; REMOTIX's sessions have none, which is also what makes "
      "Mutter headless. A session counts as local when it has a seat, a graphical " + c("Type") + ", "
      + c("Class") + " " + c("user") + " (greeters and lock screens are not the user at work), is not "
      + c("Remote") + ", and is not " + c("closing") + ".") + \
    p("<b>One question for all tenants.</b> The sweep used to call logind once per attached user. Measured on 25 "
      "August 2026 on the test machine: with 7 tenants and logind answering in 286 ms, every desktop fell to 1.3 "
      "frames per second, silently. " + c("ListSessions") + " already returns every session of the machine and "
      "cost 2.4–2.6 ms whatever the number of sessions, so " + c("sentinella_locali()") + " asks once and answers "
      "for everyone; only sessions with a seat are opened one by one, and on a headless machine there are none.") + \
    note("the power-off check must run in the child. Root always gets " + c("yes") + ", because logind checks "
         + c("CAP_SYS_BOOT") + " before asking polkit (measured on 15 August 2026): asked from the server, the "
         "check would always pass.", "Asked from the right place.") + \
    p("If logind does not answer, the sentinel answers “no local session” and writes one line (not repeated until "
      "logind is back): “I don't know” is treated as “there is none”, the only choice that does not punish a user "
      "who did nothing wrong (I1). If the system bus cannot be opened at startup, the local-session rule is not "
      "applied and the log says so.")

S8 = p("Each process has its own loop. Only the child has threads, and they are the libraries' or narrow helpers "
       "that never touch the encoder.", lead=True) + \
    table(["Process", "Loop", "Threads", "Notes"], [
        ["server", c("poll()") + " on transport, page, unblock socket, PAM helper, children; wakes at least once a "
         "second", "one", "no blocking call except the 300 ms logind questions and the startup work"],
        ["PAM dispatcher", "blocking " + c("recv()"), "one", "forks per request"],
        ["child", c("poll()") + " on the server's socket and the libei descriptor; 1000 ms when idle, 0 while "
         "capturing, at most 5 ms while audio is on", "see below", "captures, encodes and sends in the same thread"],
    ], "«TAB» — The loops") + \
    table(["Thread", "Where", "What it does"], [
        [c("remotix-cattura"), c("cattura.c"), "PipeWire thread loop of the video stream (GNOME, KDE); the frame is "
         "taken by the child's loop with a wait of at most 8 ms (" + c("MOVIMENTO_ATTESA_S") + ")"],
        [c("remotix-suono"), c("suono.c"), "PipeWire thread loop of the audio sink; samples go into a ring of "
         "48,000 frames that the child's loop drains"],
        [c("remotix-appunti"), c("appunti.c") + " (GNOME), " + c("appunti_kde.c") + " (KDE, XFCE, LXQt)",
         "the clipboard: a GLib main loop on GNOME, a Wayland data-control pump elsewhere"],
        [c("remotix-kwin"), c("kwin.c"), "pumps KWin's Wayland connection"],
        [c("powerdevil"), c("sessione.c"), "on KDE, waits up to 120 s for PowerDevil to appear and asks it to "
         "inhibit"],
        [c("pannello-xfce"), c("sessione.c"), "on XFCE, watches the panel to remove lock, suspend, reboot and "
         "power-off actions"],
    ], "«TAB» — The threads of a child") + \
    p("On labwc (XFCE, LXQt) the capture and the virtual devices run on the child's own loop with Wayland calls; "
      "on GNOME the D-Bus calls to Mutter iterate a private GLib context. The encoder runs synchronously in the "
      "child's loop: capture, encode, send, then the next frame. Encoding frame N while capturing N+1 would raise "
      "the frame rate and add delay, and SPECIFICHE.md §3.2 forbids that trade.")

S9 = p("Each piece of state has one owner and one lifetime. The rule in the code is that a global is a second place "
       "where something can be alive or dead, so shared things travel in structures (" + c("struct ponte")
       + ") and each table is sized once, at startup.", lead=True) + \
    table(["State", "Owner", "Lives", "Notes"], [
        ["certificates and their fingerprint", c("certificati.c"), "files in " + c("/var/lib/remotix/certificati")
         + ", rotated while running", rif("Transport: QUIC, HTTP/3, WebTransport")],
        ["the address ban", c("rcp.c"), "in memory and in " + c("/var/lib/remotix/ban") + ": survives restarts",
         "lifted early only through the unblock socket of the running server"],
        ["RCP sessions and attach slots", c("rcp.c"), "one per connection; the slot is freed on detach or after "
         "30 s of silence", rif("The RCP/1 protocol")],
        ["WebTransport connections, per-user stage size", c("webtransport.c"), "per connection; the stage size "
         "is forgotten when the child dies", c("wt_palco_dimentica()")],
        ["the children table", c("figlio.c"), "a slot per user while their child lives", "sized on the cap"],
        ["the presence table (abandonment clock)", c("main.c"), "a slot per user from the birth of their stage to its "
         "end", "sized on the cap; survives clients"],
        ["found-again desktops", c("main.c"), "from startup until their user returns or the desktop dies",
         "at most 256"],
        ["the budget's accounts", c("budget.c"), "per user", rif("Quality, degradation and budget")],
        ["PAM checks in flight", c("aiutante.c"), "up to 8 s each", "user name and address only, never the "
         "password"],
        ["the stage: capture, encoders, input, clipboard, the last keyframe per codec", "the child", "as long as the "
         "child", "statics of " + c("figlio.c") + ": one stage per process"],
        ["the desktop and the user's programs", "the compositor", "until logout or abandonment", "survives clients, "
         "children and the server"],
        ["the user manager's environment before REMOTIX", "the child", c("$XDG_RUNTIME_DIR/remotix/gestore-prima")
         + ", consumed at the next cleanup", rif("Files on the machine")],
    ], "«TAB» — Where state lives") + \
    p("<b>One number for the cap.</b> " + c("RCP_TETTO_SESSIONI") + " (10) in " + c("rcp.h") + " is the default, "
      + c("--tetto-sessioni N") + " moves it at startup, and " + c("rcp_tetto()") + " is read once by every table "
      "that counts users: the attach slots of " + c("rcp.c") + ", the children of " + c("figlio.c") + ", the "
      "presence table of " + c("main.c") + " and the stages of " + c("webtransport.c") + ". Until 25 August 2026 "
      "these were five hand copies of 16 (one of them 8) while SPECIFICHE.md promised 10.") + \
    tip("the cap counts <b>stages</b>, not connections: a user who closed their browser still holds a stage until "
        "logout or abandonment. " + c("palchi_quanti()") + " adds the children and the found-again desktops; a new "
        "user who finds them all taken is refused with " + c("0x0E SESSIONE_NON_SERVIBILE") + " (the session cannot be "
        "served) before any process "
        "is forked.", "Stages, not connections.")

CHAPTER = ("Overall architecture", [
    ("Architectural principles", S1),
    ("The processes of REMOTIX", S2),
    ("The parent process", S3),
    ("The PAM helper process", S4),
    ("The per-user child process", S5),
    ("The server–child channel", S6),
    ("The logind sentinel", S7),
    ("Event loops and threads", S8),
    ("Where state lives", S9),
])
