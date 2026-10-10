from build import arrow, box, c, code, fig, note, p, rif, seq, steps, table, text, tip, warn, zone

# ── 14.1 The security model ──────────────────────────────────────────────
ZONE = fig(
    zone(20, 12, 200, 300, "Network")
    + box(36, 60, 168, 54, "Browser", "page + WebTransport", "dark")
    + box(36, 210, 168, 54, "Anyone else", "may knock, may be banned", "grey")
    + zone(240, 12, 300, 300, "root")
    + box(258, 44, 264, 58, "Server parent", "TLS keys · ban table · RCP", "navy")
    + box(258, 128, 264, 50, "PAM dispatcher", "forks, never calls PAM", "dark")
    + box(258, 200, 264, 50, "PAM grandchild", "one transaction, then exits", "dark")
    + text(390, 290, "single poll loop; system bus only (logind)", 11)
    + zone(560, 12, 320, 300, "Each user, own uid")
    + box(578, 44, 284, 58, "Per-user child", "fork + exec, setuid, PAM session", "blue")
    + box(578, 140, 284, 58, "Desktop session", "compositor and programs", "light")
    + box(578, 236, 284, 50, "Card nodes", "/dev/dri via groups", "amber")
    + arrow(206, 86, 256, 76, "#003a90", label="TLS 1.3", lx=230, ly=66)
    + arrow(390, 104, 390, 126, "#475569") + arrow(390, 180, 390, 198, "#475569")
    + arrow(524, 70, 576, 70, "#0050C0", label="socketpair", lx=550, ly=60)
    + arrow(720, 104, 720, 138, "#3b82f6") + arrow(720, 200, 720, 234, "#d97706"),
    900, 320, "«FIG» — Trust boundaries: what runs as root, what runs as each user, and what faces the network")

S1 = p("REMOTIX has two security levels and deliberately no third (" + c("SPECIFICHE.md") + " §4.1, set by the user "
       "on 9 Aug 2026): the <b>transport</b>, so that nobody reads or rewrites what passes, and the <b>access</b>, "
       "i.e. who may enter the machine. Transport is TLS, always and without alternatives; access is address, port, "
       "user name and password, checked by the machine's own PAM.", lead=True) + ZONE + \
    table(["Principle", "What it means in the code"], [
        ["<b>The guard starts from «denied»</b> (invariant I3)", "Whoever does not pass the validator receives no "
         "pixel and commands nothing. Every failure of the authentication path — a dead helper, a timeout, a garbled "
         "byte — is a «no» (" + rif("Authentication with PAM") + ")."],
        ["<b>Root does only what needs root</b>", "Verifying anyone's password and descending to anyone's uid. "
         "Everything that touches the user's session (bus, capture, devices) runs as the user, in a separate "
         "image (" + rif("Isolation between users") + ")."],
        ["<b>Protections live in the program</b> (invariant I7)", "The ban survives restarts, the PAM service file "
         "is checked at startup, the uid descent is verified with the kernel. A protection that lives in a "
         "configuration line can be lost without anyone noticing."],
        ["<b>REMOTIX mirrors the system</b>", "The PAM stack is the distribution's own ssh stack plus one line "
         "(root excluded); account locking, " + c("pam_faillock") + " and SELinux contexts behave as for ssh "
         "(" + c("DECISIONI.md") + " §10.18)."],
        ["<b>REMOTIX does not modify the system</b>", "It says what it needs; the administrator provides it. One "
         "wanted exception: the card groups (" + rif("What REMOTIX does not change") + ")."],
        ["<b>Complexity is attack surface</b>", "No licence server, no update service, no relay of ours: the user "
         "removed the licence system on 10 Oct 2026 also because it was a networked service to keep alive and "
         "defend (" + c("DECISIONI.md") + " §10.33)."],
    ], "«TAB» — The principles behind the security model") + \
    p("Accepted risks, written down rather than hidden: the first connection from each device is open to a "
      "man-in-the-middle (there is no domain and no authority; with a web client the attacker does not intercept "
      "the page, they rewrite it), which is acceptable for the intended scenario — own server, own network or VPN. "
      "Multi-factor authentication is deferred by the user to after project completion (" + c("DECISIONI.md")
      + " §1.7). The desktops' own screen lockers stay off (" + c("SPECIFICHE.md") + " §5.4): the only road to a "
      "desktop is RCP, and RCP goes through PAM — a reasoning that holds only while the password is the only key.")

# ── 14.2 TLS and the two certificates ────────────────────────────────────
S2 = p("The server makes its own certificates — two of them, on purpose (" + c("RCP.md") + " §4.1-bis, "
       + c("certificati.h") + ", the certificates module). Confusing them passes every bench and makes the browser warning reappear every two "
       "weeks, «and nobody would connect the two things».", lead=True) + \
    table(["", "Page certificate (long-lived)", "Session certificate (short-lived)"], [
        ["Serves", "The page, over TCP (HTTP/1.1)", "The WebTransport session, over QUIC"],
        ["Files in " + c("--certificati"), c("pagina.pem") + ", " + c("pagina.key") + ", mark " + c("pagina.nostro") + " (nostro = ours)",
         c("sessione.pem") + ", " + c("sessione.key") + ", mark " + c("sessione.nostro")],
        ["Validity", c("CERT_GIORNI_PAGINA") + " = 365 days", c("CERT_GIORNI_SESSIONE") + " = 13 days, below the "
         "14-day ceiling browsers impose on " + c("serverCertificateHashes")],
        ["How the browser trusts it", "The user clicks through the warning once per device", "The page passes its "
         "SHA-256 fingerprint to " + c("WebTransport") + "; the exception is not consulted on that connection"],
        ["Renewal", "Only when expired, and only if it is ours", "Rotated when fewer than " + c("CERT_MARGINE_GIORNI")
         + " = 2 days remain — checked at startup and every 60 s; the QUIC TLS context is rebuilt on the fly"],
        ["Administrator's certificate", "Used as is and <b>never</b> regenerated, not even when expired", "Always ours"],
    ], "«TAB» — The two certificates") + \
    table(["Property", "Value", "Why"], [
        ["Key", "ECDSA P-256 (" + c("EVP_EC_gen(\"P-256\")") + "), never Ed25519, never RSA", "P-256 is the curve that "
         "keeps " + c("serverCertificateHashes") + " usable."],
        ["Subject and SAN", c("CN") + " = the name; SAN " + c("IP:") + " for an address, " + c("DNS:") + " otherwise",
         "A browser that finds a SAN that does not match shows a <i>different</i> warning, and some offer no click "
         "to proceed — hence the mandatory " + c("--nome") + " (the name to certify)."],
        ["Serial", "16 random bytes, top bit cleared", "Two certificates made in the same second must not share a "
         "serial."],
        ["Validity start", "One hour in the past", "Clock skew between server and browser."],
        ["Extensions", c("basicConstraints = critical,CA:FALSE"), "Self-signed leaf, not an authority."],
        ["Private key file", "Created with " + c("open(…, 0600)") + ", never " + c("chmod") + "ed afterwards", "Between "
         "creation and a later " + c("chmod") + " the key would be world-readable for as long as it takes."],
        ["Directory", "Created 0700; the packages create " + c("/var/lib/remotix") + " 0700 root (tmpfiles)", "It "
         "holds the private keys."],
        ["Whose certificate", "A " + c(".nostro") + " mark file next to every certificate REMOTIX generated",
         "«Did we write it?» is a fact; «is it self-signed?» is a deduction that would be wrong for a private CA."],
        ["Two must be two", "At startup the two fingerprints are compared; equal ⇒ refuse to start", "The defect "
         "B13.1 exists to catch, checked at birth instead of fourteen days later."],
        ["Fingerprint", "SHA-256 of the certificate's DER, base64 (and hex for the logs)", "Of the certificate, not "
         "of the public key (R1.14): the wrong one never matches and «WebTransport does not connect» names nothing."],
    ], "«TAB» — How " + c("certificati.c") + " generates and keeps them") + \
    p("A page left open for two weeks holds the fingerprint of a certificate that has since rotated. The page "
      "fetches the current one from " + c("GET /impronta") + " on the server that served it — a plain HTTPS "
      "request, since no RCP channel exists before the session opens.") + \
    table(["TLS setting", "QUIC context (" + c("tls_contesto_quic()") + ")", "Page context ("
           + c("tls_contesto_pagina()") + ")"], [
        ["Minimum version", "TLS 1.3", "TLS 1.3"],
        ["ALPN", c("h3") + " required; a client that does not offer it is refused with a fatal alert", c("http/1.1")
         + " chosen if offered; a client that offers nothing is not refused (HTTP/1.1 needs no ALPN), one that offers "
         "only other protocols is refused like the QUIC one"],
        ["0-RTT", "Off at context level (" + c("SSL_CTX_set_max_early_data(ctx, 0)") + ")", "—"],
        ["Options", c("SSL_OP_CIPHER_SERVER_PREFERENCE") + ", " + c("SSL_OP_NO_ANTI_REPLAY") + ", "
         + c("SSL_MODE_RELEASE_BUFFERS"), "Same"],
        ["Key check", c("SSL_CTX_check_private_key") + ": a mismatch refuses the context", "Same"],
    ], "«TAB» — The two TLS contexts") + \
    p("0-RTT is off because early data can be <b>replayed</b>, and the client's second RCP message is " + c("CREDENZIALI")
      + " (credentials); the gain would be one round trip on a session that lasts hours. The symptom of 0-RTT left on does not "
      "exist — the session opens the same — and libraries offer it by default (ngtcp2's example even sets it to "
      + c("UINT32_MAX") + "), so leaving it alone would be a distraction no functional bench sees. The page's "
      "responses carry " + c("Cross-Origin-Opener-Policy: same-origin") + ", "
      + c("Cross-Origin-Embedder-Policy: require-corp") + ", " + c("Cross-Origin-Resource-Policy: same-origin")
      + ", " + c("Cache-Control: no-store") + " and " + c("X-Content-Type-Options: nosniff") + ".") + \
    warn("QUIC address validation with Retry is not done (" + c("trasporto.c") + ", the QUIC transport): «the product is used on its own "
         "network or VPN; it must be put back before exposing it». Exposing REMOTIX directly to the Internet is "
         "outside the declared scenario.", "No Retry.")

# ── 14.3 Authentication with PAM ─────────────────────────────────────────
AUT = seq([("Browser", "page", "dark"), ("Parent", "rcp.c · webtransport.c", "navy"),
           ("Dispatcher", "aiutante.c", "dark"), ("Grandchild", "autenticazione.c", "blue"),
           ("PAM", "service remotix", "grey")], [
    (0, 1, "CREDENZIALI (user, password)"),
    (1, 2, "request: case id, user, password, rhost"),
    (2, 3, "fork"),
    (3, 4, "pam_authenticate, then pam_acct_mgmt"),
    (4, 3, "PAM_SUCCESS twice — or anything else", True),
    (3, 2, "one byte: exactly 1 = yes, then exit", True),
    (2, 1, "verdict for the case id", True),
    ("nota", 1, "≥ 1 s after CREDENZIALI, yes or no"),
    (1, 0, "AMMESSO (admitted), or RESPINTO (refused) 0x07 / 0x08", True),
], "«FIG» — The password check never runs in the server's loop", width=900)

S3 = p("The server runs one " + c("poll") + " loop for every connected user, and a PAM transaction blocks: measured "
       "on 11 Aug 2026 (bench B8) at 1.0–2.2 s per attempt, of which PAM itself added +1034 ms on refusals against "
       "+84 ms on admissions — the signature of " + c("pam_faildelay") + ". With video, that would freeze every "
       "connected screen whenever somebody logs in. Since 12 Aug 2026 (" + c("DECISIONI.md") + " §1.10) PAM is "
       "asked by a helper process.", lead=True) + AUT + \
    table(["Level", "Does", "Never does"], [
        ["Server parent", "Writes a request on a " + c("SOCK_SEQPACKET") + " socketpair and returns to " + c("poll"),
         "Call PAM"],
        ["Dispatcher (" + c("aiutante.c") + ", the PAM helper)", "Started once at startup, before any listening socket exists; reads "
         "a request and forks", "Call PAM"],
        ["Grandchild", "Calls " + c("rcp_autentica_da()") + " (authenticate, with the client address) <b>once</b>, writes one byte, exits", "Live on: "
         + c("alarm") + " after " + c("NIPOTE_ALLARME_S") + " = 20 s"],
    ], "«TAB» — Three levels, so that PAM's re-entrancy is not managed but out of play") + \
    p("One process per transaction was chosen over a thread by the user: PAM is not reliably re-entrant, and its "
      "modules — foreign code loaded at runtime, with " + c("getpwnam") + ", sockets to " + c("nscd") + ", "
      + c("dlopen") + " — share nothing with anybody this way. Ten users logging in together do not queue: they are "
      "ten grandchildren. " + c("SOCK_SEQPACKET") + " keeps messages delimited by the kernel, so a request cannot "
      "arrive in half and two answers cannot merge into «somebody else's answer»; the socketpair has no name in "
      "the filesystem.") + \
    table(["Road to failure", "Outcome"], [
        ["Helper not started", "At startup: the parent declares it and falls back to the synchronous check, which stops "
         "the loop for 1–2 s per attempt; on a helper that is not running " + c("aiutante_chiedi()")
         + " (ask the helper) returns false ⇒ no"],
        ["Socket full, " + c("EAGAIN"), "No"],
        ["More than " + c("MAX_IN_VOLO") + " (in flight) = 16 cases in flight", "No. Sized on the peak of <i>arrivals</i>, not "
         "on the session cap: 17 people pressing «enter» together with zero sessions is possible (R10-A7)."],
        ["Dispatcher dead (EOF)", "Every case in flight ⇒ no"],
        ["Grandchild dead without answering", "The case expires after " + c("SCADENZA_MS") + " (deadline) = 8 s ⇒ no"],
        ["Short or garbled answer", "Discarded, then expiry"],
        ["Answer byte not exactly 1", "No"],
        ["The helper itself is the broken piece", "Second net in the RCP state machine: " + c("TETTO_VERDETTO")
         + " (verdict ceiling) = 12 s ⇒ no. Longer than the helper's, so that normally the no comes from there with its log line."],
    ], "«TAB» — The seven roads to «no» (" + c("aiutante.h") + "), plus the second net") + \
    p("Inside the grandchild, " + c("rcp_autentica_da()") + " follows sshd: " + c("pam_start(\"remotix\", user, …)")
      + ", " + c("PAM_RHOST") + " = the client's bare address (no brackets, no port, " + c("::ffff:1.2.3.4")
      + " reduced to " + c("1.2.3.4") + ", like sshd with " + c("UseDNS no") + "), " + c("PAM_TTY") + " = "
      + c("remotix") + ", then " + c("pam_authenticate") + " <b>and</b> " + c("pam_acct_mgmt") + ": the first says "
      "the password is right, only the second says the account is usable (expired or locked accounts pass the "
      "first). The conversation answers only " + c("PAM_PROMPT_ECHO_OFF") + " with the password and at most 16 "
      "prompts. With " + c("PAM_RHOST") + " set, " + c("pam_faillock") + " records the address, " + c("pam_unix")
      + " logs " + c("rhost=…") + ", " + c("pam_access") + " has the host and logind marks the session "
      + c("RemoteHost") + ".") + \
    table(["Rule", "Value", "Why"], [
        ["Fixed delay", c("RITARDO_FISSO") + " = 1000 ms after " + c("CREDENZIALI") + ", on every answer, admissions "
         "included", "Not to slow guessing, but to remove timing as a channel: without it «no such user» answers "
         "in a millisecond and «wrong password» in fifty."],
        ["One reason for every refusal", "The client gets " + c("0x07 CREDENZIALI_ERRATE") + " (wrong credentials) whether the user does "
         "not exist, the password is wrong, the account is expired, or PAM could not judge", "Telling the outside "
         "«your account is locked» is an oracle."],
        ["Two facts in the log", c("PAM ha RIFIUTATO") + " (PAM REFUSED) for " + c("PAM_AUTH_ERR") + ", " + c("PAM_USER_UNKNOWN") + ", "
         + c("PAM_PERM_DENIED") + ", " + c("PAM_CRED_INSUFFICIENT") + ", " + c("PAM_ACCT_EXPIRED") + ", "
         + c("PAM_NEW_AUTHTOK_REQD") + ", " + c("PAM_MAXTRIES") + "; " + c("⛔ PAM NON HA POTUTO GIUDICARE")
         + " (PAM COULD NOT JUDGE) for anything else, naming the service file and " + c("/etc/remotix/utenti-negati")
         + " (the denied-users list)", "Otherwise a missing PAM file looks "
         "exactly like a thousand wrong passwords, and the diagnosis hunts the password for hours."],
        ["One attempt per connection", c("RCP.md") + " §4.4", "The ban counter must count attempts, not connections."],
    ], "«TAB» — What the outside sees and what the log says") + \
    note("the server checks at startup that " + c("/etc/pam.d/remotix") + " or " + c("/usr/lib/pam.d/remotix")
         + " exists (" + c("guarda_il_servizio_pam()") + ", check the PAM service). Without it Linux-PAM falls back to the " + c("other")
         + " service: " + c("pam_deny") + " on Fedora and Arch (every right password refused), the common stacks "
         "without the root exclusion on Debian. The server does not refuse to start — the page, the ban and the "
         "certificates still work — but it writes the fault with the remedy.", "The service file is checked.")

# ── 14.4 The PAM service files ───────────────────────────────────────────
S4 = p("One file per distribution family, like Cockpit: " + c("@include") + " is a Debian modification of Linux-PAM "
       "and is an «illegal module type» elsewhere. Since " + c("DECISIONI.md") + " §10.18 (D3, 30 Sep 2026) each "
       "file is the distribution's own " + c("sshd") + " PAM file, line for line, plus one line at the top.",
       lead=True) + \
    table(["File in " + c("src/"), "Installed as", "Families", "Mirrors (measured 30 Sep 2026)"], [
        [c("remotix.pam"), c("/etc/pam.d/remotix"), "Debian, Ubuntu, Mint", c("/etc/pam.d/sshd") + " of Debian 13 "
         "and Ubuntu 26.04: 15 lines of 15 equal (" + c("common-auth") + ", " + c("common-account") + ", "
         + c("common-session") + ", " + c("common-password") + ", motd, mail, limits, env, loginuid, keyinit, "
         "selinux silenced where absent)"],
        [c("remotix.pam.fedora"), c("/etc/pam.d/remotix"), "Fedora, RHEL, Rocky, Alma", c("password-auth")
         + " + " + c("postlogin") + ", " + c("pam_sepermit") + ", " + c("pam_namespace") + ", " + c("pam_selinux")
         + " close/open: 14 of 14"],
        [c("remotix.pam.suse"), c("/usr/lib/pam.d/remotix") + " (the admin's " + c("/etc/pam.d/remotix")
         + " wins)", "openSUSE Leap, Tumbleweed", c("common-*") + " + " + c("postlogin-*") + ": 13 of 13"],
        [c("remotix.pam.arch"), c("/etc/pam.d/remotix"), "Arch, Manjaro", c("system-remote-login") + ": 4 of 4"],
    ], "«TAB» — The four PAM files") + \
    code("auth  requisite  pam_listfile.so item=user sense=deny file=/etc/remotix/utenti-negati onerr=fail",
         "text", "The one line that is not sshd's: root excluded, as ssh does by default") + \
    table(["Choice", "Why"], [
        ["In " + c("auth") + ", " + c("requisite") + ", before the password", "In " + c("account") + " root's password "
         "would still be <b>tried</b>, and «right password, account denied» answers differently from «wrong "
         "password»: an oracle for whoever guesses root's password from the network."],
        [c("onerr=fail") + " (Cockpit uses " + c("succeed") + ")", "A missing or malformed list lets <b>nobody</b> in, "
         "and PAM's log says why. With " + c("succeed") + " a lost file would silently remove the root exclusion — a "
         "protection in a line that can be lost (I7)."],
        ["The list file", c("/etc/remotix/utenti-negati") + ", one name per line, shipped containing " + c("root")
         + ", owned by root and not writable by others (otherwise " + c("pam_listfile") + " rejects it)"],
        ["The rest is the system's", "Whatever the administrator configures for ssh — " + c("pam_faillock")
         + " via " + c("authselect") + " on Fedora, " + c("pam-config") + " on openSUSE, " + c("pambase")
         + "'s faillock on Arch (3 failures in 15 minutes, 10-minute lock, " + c("faillock --user <name> --reset")
         + ") — applies to REMOTIX too, with the same risk of remote account locking as ssh."],
        ["Session stack included", c("figlio.c") + " calls " + c("pam_open_session") + "; the stack must reach "
         + c("pam_systemd") + " or no logind session is born and the compositor does not start. On 15 Aug 2026 the "
         "Debian file included " + c("common-session-noninteractive") + ", which lacks it; the defect was invisible "
         "because the file was not even installed and " + c("other") + " was used. " + c("provisiona.sh")
         + " checks that the installed file reaches " + c("pam_systemd") + "."],
        [c("pam_loginuid required"), "As sshd: the service starts from systemd without a loginuid and can write it. "
         "A server started by hand from an open session (immutable loginuid) cannot open sessions — the same as "
         "sshd started that way."],
        [c("login") + " is not used", "It is the <i>console</i> stack (" + c("pam_securetty") + ", " + c("pam_lastlog")
         + ", …); sshd's is the network-access stack, and REMOTIX is network access (B-11, 10 Aug 2026)."],
    ], "«TAB» — Why the files look the way they do")

# ── 14.5 The address ban ─────────────────────────────────────────────────
S5 = p("Three failed authentications from the same address within five minutes, and that address is out for twelve "
       "hours (" + c("DECISIONI.md") + " §1.9, " + c("SPECIFICHE.md") + " §4.2, decided 10 Aug 2026). The user name "
       "does not count: three different names count three. A successful login resets the count. The ban survives "
       "restarts.", lead=True) + \
    table(["Constant (" + c("rcp.c") + ")", "Value", "Meaning"], [
        [c("SOGLIA"), "3", "Failures that ban"],
        [c("FINESTRA"), "300,000 ms", "The three must fit in five minutes. The window <b>slides</b>: the times of the "
         "last three are kept. Anchored to the first failure, failures at 0:00, 4:59 and 5:01 would restart the "
         "count from one, and whoever guesses slightly slower than the window would never be stopped."],
        [c("BAN_DURATA"), "43,200,000 ms", "Twelve hours"],
        [c("MAX_TENTATIVI"), "256", "Entries in the table. When full, the victim is the least recently touched "
         "<b>non-banned</b> entry (a banned one only when every entry is banned), and the eviction is logged; otherwise filling the table with invented addresses "
         "would be a way to erase a ban."],
    ], "«TAB» — The ban parameters") + \
    table(["Counts", "Does not count"], [
        ["A failed authentication — wrong password and unknown user are the same thing",
         "Protocol errors, timeouts, and the refusal of a second device of the same user ("
         + c("0x0F GIA_ATTIVA_REMOTA") + ", already active remotely)"],
    ], "«TAB» — What feeds the counter") + \
    p("The key is the address <b>without the port</b>, in brackets even for IPv4: " + c("[192.168.0.2]") + ", "
      + c("[fe80::1]") + ". The first version keyed on " + c("192.168.0.2:44661") + "; with one attempt per "
      "connection the port changes every time and the counter was always 1 — code that looked right and did "
      "nothing, found only by a bench case that tries seven <i>different</i> names from one address. The key is "
      "built in exactly one place, " + c("rcp_chiave_indirizzo()") + " (the address key), used by the session, the page server and "
      "the unlock command alike: before 10 Aug 2026 a second function made keys without brackets and "
      + c("rcp_bannato(\"192.168.0.2\")") + " (is it banned?) answered «not banned» (B-8).") + \
    table(["Aspect", "Behaviour"], [
        ["File", "Default " + c("/var/lib/remotix/ban") + ": one line " + c("<key> <epoch-seconds-of-expiry>")
         + " per banned address, only those still banned"],
        ["Writing", "At every change (new ban, unlock), to " + c("<file>.nuovo") + " (nuovo = new) then " + c("rename()")
         + ": a file truncated by a crash would claim «these addresses were not banned»"],
        ["Clock", "Epoch seconds on disk, monotonic in memory: a monotonic time written to disk is meaningless after "
         "a restart"],
        ["Loading", c("rcp_ban_carica()") + " (load the bans) at startup. A file that exists and cannot be read stops the server "
         "(exit 1): «zero bans» and «could not look» are different facts"],
        ["What a banned client sees", "The page still loads (" + c("pagina.c") + " asks " + c("rcp_bannato()")
         + ") and says the attempts are exhausted; RCP answers " + c("0x08 TROPPI_TENTATIVI") + " (too many attempts). Never silence: "
         "whoever is banned by mistake is almost always the owner"],
        ["Ways out", "Twelve hours, or the unlock command (" + rif("The unlock command socket") + ")"],
    ], "«TAB» — Persistence and the visible side") + \
    warn("behind a NAT addresses are shared, so three mistakes by one person close the door to everybody for twelve "
         "hours, and the first to trip is whoever types a long password on a phone keyboard. A per-name counter that "
         "softened this was removed knowingly. Whether 256 entries are enough against an attacker with more "
         "addresses is not measured: the eviction line in the log is where it would show.", "The declared price.")

# ── 14.6 The unlock command socket ───────────────────────────────────────
S6 = p("The way out for whoever bans themselves from their own phone must ask «the only key that case admits — access "
       "to the machine». " + c("comando.c") + " (the command module) implements it as a Unix socket, opened with "
       + c("--comando-socket PATH") + ".", lead=True) + \
    table(["Request", "Answer", "Effect"], [
        [c("SBLOCCA <address>") + " (unlock)", c("TOLTO <key>") + " (removed)", "The ban existed and was removed from the serving process's "
         "memory; the file was asked to be rewritten"],
        [c("SBLOCCA <address>"), c("NON-BANNATO <key>") + " (not banned)", "Nothing to remove; the failure count of that address "
         "restarts from zero anyway"],
        [c("PING"), c("PONG"), "Touches nothing; tells a bench the command exists"],
        ["anything else", c("NON-CAPITO <line>") + " (not understood)", "Nothing"],
    ], "«TAB» — The protocol: one line, readable without tools") + \
    code("printf 'SBLOCCA 192.168.0.2\\n' | nc -U /run/remotix/comando\n"
         "python3 banchi/01-b8-sblocca.py --socket /run/remotix/comando 192.168.0.2", "bash",
         "Unlocking an address (the socket path is whatever " + c("--comando-socket") + " was given)") + \
    table(["Rejected form", "Why it fails"], [
        ["A second process (" + c("remotix --sblocca IND") + ", the removed unlock option)", "The ban lives in the memory of the serving process. "
         "A second process can only rewrite the file; the server keeps answering " + c("TROPPI_TENTATIVI")
         + ", and the next ban of anyone rewrites the file from stale memory, putting the address back. And it "
         "exited 0."],
        ["A signal", "Carries no address and has no answer: «was not banned» and «removed» could not be told apart."],
    ], "«TAB» — Why a socket") + \
    p("The socket is created with " + c("umask(0177)") + " around " + c("bind") + " so that it is born 0600, then "
      + c("chmod") + " 0600 again: a later " + c("chmod") + " alone left a window with whatever the inherited umask "
      "allowed. It has no IP address, so it adds no surface reachable from the network. " + c("PING") + " answers "
      "«somebody answers», not «the right server answers»: with two servers on a machine, the wrong socket replies "
      + c("PONG") + " and " + c("NON-BANNATO") + ". No identity verb was added to the protocol; the client asks the "
      "kernel instead (" + c("SO_PEERCRED") + ").") + \
    warn("the packaged units do not pass " + c("--comando-socket") + " (it is listed among the bench options kept "
         "off the shipped command line), although the deb and rpm tmpfiles entries create " + c("/run/remotix") + " «for the "
         "command socket». On an installed system a ban therefore ends only after twelve hours, unless the "
         "administrator adds the option through " + c("REMOTIX_OPZIONI") + " (deb, rpm). " + c("SPECIFICHE.md")
         + " §4.2 promises the command as a way out. Not settled yet.", "Not in the packaged units.") + \
    note(c("rcp_sblocca()") + " (unlock) writes the file through " + c("salva_ban()") + " (save the bans) without a "
         "session, which stays silent on a write failure: the line " + c("⛔ SBLOCCATO") + " (unlocked) therefore says the rewrite was <i>requested</i>, not done.",
         "Requested, not confirmed.")

# ── 14.7 Isolation between users ─────────────────────────────────────────
S7 = p("The parent stays root because only root can verify another user's password with PAM and descend to any uid; "
       "for every admitted user it creates a child that runs <b>as that user</b> and holds the session bus, the "
       "capture and the devices (" + c("DECISIONI.md") + " §1.10-bis, 12 Aug 2026). Root does not connect to a "
       "user's session bus, which was measured.", lead=True) + \
    p("The child is a " + c("fork") + " <b>and</b> an " + c("exec") + " of the same binary. A " + c("fork")
      + " alone would run as the user while holding the parent's memory: the TLS private key, the ban table and the "
      "state of every other session — and " + c("/proc/self/mem") + " is readable by the process owner, who would be "
      "the user. That would be the worst defect this work could produce. The descent happens before " + c("exec")
      + ", so there is no instant in which the new image runs as root.") + \
    steps([
        "The socketpair end goes to descriptor 3, without " + c("CLOEXEC") + ": the only thing that must cross "
        + c("exec") + ".",
        "Every other descriptor from 4 up is closed (" + c("close_range") + ", or a loop up to 4096 as declared "
        "fallback). A child that kept the UDP socket and the TCP listener would hold the port after the server "
        "died. 0, 1 and 2 stay: the child logs to the parent's stream.",
        "A PAM session is opened for the user (service " + c("remotix") + ", silent conversation) with "
        + c("XDG_SESSION_TYPE=wayland") + ", " + c("XDG_SESSION_CLASS=user") + ", no " + c("XDG_SEAT")
        + " (a session without a seat is headless by construction), " + c("PAM_RHOST") + " = the client address "
        "(" + c("remotix") + " if unknown) and " + c("PAM_TTY") + " = " + c("remotix") + "; then " + c("pam_end")
        + " <b>without</b> " + c("pam_close_session") + ": the logind session belongs to this process and logind "
        "reclaims it when it dies. A failure is logged and the child goes on.",
        "On SELinux systems the exec context gets the level of the user's login mapping, as sshd does ("
        + c("livello_selinux_come_sshd()") + ", " + c("libselinux") + " opened with " + c("dlopen") + ").",
        c("setgroups") + ", then " + c("setgid") + ", then " + c("setuid") + " — never in another order: groups "
        "first or the right to change them is lost, gid before uid or the privilege to set it is lost. Exits 31, "
        "32, 33.",
        c("getresuid") + " and " + c("getresgid") + " are read back: all three uids and all three gids must be the "
        "user's, or the child does not start (exits 34–36). A " + c("setuid") + " that returns 0 does not prove "
        "that the saved uid changed; one left at 0 would be one line away from root.",
        "The environment is composed from scratch, one variable at a time, and only " + c("XDG_SESSION_ID")
        + " is taken from PAM's list. Then " + c("execve") + " (exit 37 if it fails). No secret is on the command "
        "line: the password died with the PAM grandchild.",
    ]) + \
    p("Before any of this, " + c("figli_assicura_da()") + " (ensure the user has a child) refuses to create a child for a user whose uid is 0: the "
      "child exists in order <b>not</b> to be root, and a root child would have nobody's session bus anyway. (Root "
      "is also excluded earlier, by PAM.)") + \
    table(["Check", "How", "Why"], [
        ["Who is at the other end of the socketpair", c("SO_PASSCRED") + " + " + c("SCM_CREDENTIALS") + ": the kernel "
         "stamps <b>every message</b> with the sender's pid/uid/gid at write time; " + c("credenziali_combaciano()")
         + " (credentials match) compares", c("SO_PEERCRED") + " on a socketpair returns the credentials of whoever called "
         + c("socketpair()") + " — root — on both ends, forever: a check that reads a number and checks nothing."],
        ["Re-check of silent children", c("figli_ricontrolla()") + " (re-check the children) asks every child «who are "
         "you» at most once every " + c("RICONTROLLO_MS") + " (re-check interval) = 60 s", "A child that delivered its frame and then fell silent would "
         "otherwise be verified once, at the start. A mismatch kills it."],
        ["First words of a child", c("SCADENZA_SONO_MS") + " (deadline for «I am») = 15 s to say who it is", "A process running as a user "
         "that does not answer is not a stage, it is a forgotten process. After the first answer there is no "
         "deadline: the stage survives detachment (I4)."],
        ["The child re-checks itself", "At start " + c("figlio_vive()") + " (the child's main function) compares its "
         "uid/gid with " + c("argv[3]") + "/" + c("argv[4]"), c("⛔⛔ NON SONO CHI DOVREI ESSERE") + " (I am not who I "
         "should be) is logged with the user's name."],
    ], "«TAB» — How the parent and the child keep each other honest") + \
    p("One child per user, one graphical session per user (" + c("SPECIFICHE.md") + " §5.1): a second device of the "
      "same user is refused with " + c("0x0F GIA_ATTIVA_REMOTA") + " (or takes the seat by ghost eviction, never "
      "across users), and a user who sits at the machine and opens a local session wins over the remote one ("
      + c("0x05 GIA_ATTIVA_LOCALE") + " (already active locally) at attach, " + c("0x04 SESSIONE_LOCALE_PREVALSA")
      + " (the local session prevailed) for a session already running; logind is polled once every 2 s for all tenants). The session cap and the composition budget keep "
      "one user from starving the others (" + c("0x0E") + ", " + c("0x06") + ").") + \
    p("Per-session files live with the user: runtime configuration (systemd user drop-ins, labwc and Qt settings, "
      "menu rules) under " + c("$XDG_RUNTIME_DIR") + ", which disappears at reboot, and the session log under "
      + c("~/.local/state/remotix") + ", created 0700/0600 with " + c("O_NOFOLLOW") + " checks. Nothing is written "
      "in shared " + c("/tmp") + ".")

# ── 14.8 The graphics card groups ────────────────────────────────────────
S8 = p("On a normal desktop logind grants access to " + c("/dev/dri") + " with an ACL (" + c("uaccess") + ") to "
       "whoever owns a <b>seat</b>. A remote session has no seat on purpose, so the ACL never comes and only the "
       "groups of the card nodes remain. Without them the session is born blind: measured 27 Aug 2026, 0 sessions "
       "of 4 without the groups, 17 of 17 with them — and no error says so.", lead=True) + \
    table(["When", "Who", "What"], [
        ["Installation", "The installer engine (" + c("PianoInstallazione()") + ", the installation plan; "
         + c("GruppiScheda()") + ", the card groups)",
         "Adds the people of the machine to the groups <b>read from the nodes</b> " + c("card*") + " and "
         + c("renderD*") + " (never a hard-coded name or gid). It is a step of the plan the administrator confirms."],
        ["First connection", "The parent, as root, just before forking the user's child ("
         + c("iscrivi_ai_gruppi_della_scheda()") + ", enrol in the card groups, called from "
         + c("figli_assicura_da()") + ")", "After PAM said yes, runs " + c("usermod -aG <groups> <user>") + " for the groups the user lacks, "
         "logs it, appends one JSON line per group to " + c("/var/lib/remotix/gruppi-iscritti.jsonl")
         + " (enrolled groups; format " + c("remotix-gruppi/1") + ", origin " + c("DIRETTA") + ", direct), and "
         "restarts the user manager (" + c("loginctl terminate-user") + ") so the compositor sees the new groups — "
         "unless a desktop of that user is alive, or logind cannot say."],
        ["Every birth", "The parent, same place (" + c("gruppi_della_scheda()") + ", the card-group check)", "Checks membership and says it loudly, with the cure, when the "
         "user is still not in the groups."],
        ["Uninstallation", "The installer engine", "Removes the memberships its own plan added and those listed in "
         + c("gruppi-iscritti.jsonl") + "; a membership that existed before, or is already gone, is never touched."],
    ], "«TAB» — Who puts users in the card groups") + \
    p("This is the one wanted exception to «REMOTIX does not modify the system» (" + c("DECISIONI.md") + " §7.21 and "
      "§10.36: «no packages without authorisation, but users must be able to access»). The annotation file is "
      "opened before " + c("usermod") + " with " + c("O_NOFOLLOW") + " in a root-owned directory that others cannot write, born 0600, "
      "one " + c("write") + " plus " + c("fsync") + " per line, and written only after " + c("usermod")
      + " succeeded: annotating an enrolment that never happened would make the uninstaller remove a group someone "
      "else gave.") + \
    note(c("DECISIONI.md") + " §10.36 asks to restrict the groups to " + c("render") + " if that does not hurt the four "
         "desktops, because " + c("video") + " also grants " + c("/dev/fb*") + " and webcams; and later a dedicated "
         + c("remotix") + " group. The code still enrols in every group that owns a card node (typically both). "
         "Not settled yet.", "Only render?")

# ── 14.9 What REMOTIX does not change ────────────────────────────────────
S9 = p("«The key of everything is that REMOTIX does not modify the systems it is installed on: it says what it needs, "
       "and then it is up to the administrator» (the user, 10 Oct 2026, " + c("DECISIONI.md") + " §10.36). The "
       "installer's " + c("check") + " says what is missing without suggesting packages or commands; the plan "
       "stops before touching anything if something blocking is missing.", lead=True) + \
    table(["REMOTIX never", "Instead"], [
        ["Adds third-party repositories (RPM Fusion, EPEL, Packman)", "Says what is missing"],
        ["Installs a graphics driver or a Vulkan driver", "Declares the requirement; " + c("--prova-codifica")
         + " stops the installation with a message if the card cannot encode (§10.34)"],
        ["Installs a desktop", "Refuses to install without a supported desktop"],
        ["Opens the firewall", "Warns «the firewall (…) is on: port N TCP and UDP must be reachable … opening it is "
         "up to the administrator»; ships a ufw profile (" + c("/etc/ufw/applications.d/remotix") + ") or a "
         "firewalld service (" + c("/usr/lib/firewalld/services/remotix.xml") + ") <b>defined, not enabled</b>"],
        ["Changes power, suspend and key handling (the «belts»)", "Ships them inert; says «REMOTIX does not change how "
         "this machine suspends or powers off: a machine that suspends when idle disconnects everyone» ("
         + rif("The power belts, shipped inert") + ")"],
        ["Changes the desktops' language or the users' settings", "Only REMOTIX's own text is in English (§10.35)"],
    ], "«TAB» — What is left to the administrator") + \
    table(["What the packages and the product do place", "Where", "Removed by"], [
        ["Binary, page, defaults, KWin capture permission", c("/usr/libexec/remotix/") + " (Arch: "
         + c("/usr/lib/remotix/") + "), " + c("/usr/share/remotix/") + ", "
         + c("/usr/share/applications/org.kde.remotix.desktop"), "Package manager"],
        ["PAM service and root exclusion list (configuration files)", c("/etc/pam.d/remotix") + " or "
         + c("/usr/lib/pam.d/remotix") + "; " + c("/etc/remotix/utenti-negati"), "Package manager (purge)"],
        ["Unit, tmpfiles, empty " + c("/etc/remotix/remotix.conf.d/"), "System unit directory, " + c("tmpfiles.d"),
         "Package manager"],
        ["State: certificates, ban file, group annotations", c("/var/lib/remotix") + " (0700 root)", "Purge (deb), "
         + c("%ghost") + " files (rpm)"],
        ["SELinux module and port type (rpm, policy " + c("targeted") + ")", c("remotix-selinux") + " sub-package",
         "Package manager"],
        ["Card group memberships", c("/etc/group") + ", annotated", "Installer engine"],
        ["A non-default port", c("/etc/remotix/remotix.conf.d/porta.conf") + " (porta = port)", "Installer engine"],
        ["Enabling the service", "systemd", "Installer engine; packages never enable or start it"],
        ["Per-user session log", c("~/.local/state/remotix/sessione.log"), "Installer engine, on uninstall"],
    ], "«TAB» — Everything REMOTIX puts on a machine")

# ── 14.10 The power belts ────────────────────────────────────────────────
S10 = p("On 15 Aug 2026 the user decided that nobody powers off, reboots, suspends or hibernates the server — not even "
        "who sits in front of it — because powering off takes away every session at once and whoever does it does "
        "not see who is connected (" + c("DECISIONI.md") + " §4.7). Three «belts» implement it. Since §10.12 and "
        "§10.36 they are shipped inert in " + c("/usr/share/remotix/cinture/") + " (cinture = belts), where nothing reads them, and "
        "the installer no longer applies them.", lead=True) + \
    table(["Belt", "Shipped as", "Would go in", "What it does"], [
        ["polkit rule", c("50-remotix-niente-spegnimento.rules") + " (no power-off)", c("/etc/polkit-1/rules.d/"), "Returns "
         + c("polkit.Result.NO") + " for twelve logind actions: power-off, reboot, suspend, hibernate, each also as "
         + c("-multiple-sessions") + " and " + c("-ignore-inhibit")],
        ["logind keys", c("remotix-tasti.conf") + " (keys)", c("/etc/systemd/logind.conf.d/"), c("HandlePowerKey") + ", "
         + c("HandleRebootKey") + ", " + c("HandleSuspendKey") + ", " + c("HandleHibernateKey") + " (and their "
         + c("LongPress") + " variants) and the three " + c("HandleLidSwitch*") + " set to " + c("ignore")],
        ["sleep", c("remotix-niente-sospensione.conf") + " (no suspend)", c("/etc/systemd/sleep.conf.d/"), c("AllowSuspend")
         + ", " + c("AllowHibernation") + ", " + c("AllowSuspendThenHibernate") + ", " + c("AllowHybridSleep")
         + " = " + c("no") + "; refuses at the systemd level, root included"],
    ], "«TAB» — The three belts") + \
    table(["Finding (measured 15 Aug 2026 on the test machine)", "Consequence for the design"], [
        ["With several users' sessions logind asks " + c("power-off-multiple-sessions") + ", not " + c("power-off"),
         "v1's rule, three actions of twelve, failed exactly in the case it was written for"],
        [c("org.freedesktop.login1.halt") + " does not exist on that systemd", "v1 had a dead line"],
        ["From a user " + c("CanPowerOff") + " = " + c("no") + "; from root " + c("yes"), "logind checks "
         + c("CAP_SYS_BOOT") + " before polkit: " + c("sudo systemctl poweroff") + " keeps working without an "
         "exception, and the rule can only be verified from the child, not from the root server"],
        ["The physical key does not go through polkit", "Hence the logind belt; the default of "
         + c("HandlePowerKey") + " is " + c("poweroff")],
        [c("AUTH_ADMIN") + " / challenge shows the menu entry and asks a password", "Hence " + c("NO")
         + ": an entry that appears and asks for a password promises something"],
    ], "«TAB» — Why the belts look the way they do") + \
    p("What remains in force regardless is session behaviour, not system configuration: inside a REMOTIX session the "
      "desktops' menus lose suspend, lock, restart, power-off and switch user, so that the only gesture that ends "
      "something is the logout (" + c("DECISIONI.md") + " §4.7, §8.2; described with the four desktops). When root "
      "does stop the machine, attached clients receive " + c("0x0C SERVER_IN_CHIUSURA") + " (server shutting down).") + \
    warn(c("SPECIFICHE.md") + " §11.3 still says power-off and suspend are «taken away from everyone». Since "
         + c("DECISIONI.md") + " §10.36 that holds only inside REMOTIX sessions; the machine itself suspends and "
         "powers off as its administrator configured it.", "The specification is older than the decision.")

# ── 14.11 The service unit ───────────────────────────────────────────────
S11 = p("The server runs as a systemd system service, as <b>root</b> and outside any user session: PAM must verify "
        "anyone's password, and the parent descends to each user's uid for the child. No " + c("User=") + " and no "
        + c("ProtectSystem") + ": it opens logind sessions, writes in users' homes and touches " + c("/dev/dri") + ".",
        lead=True) + \
    table(["Directive", "deb (" + c("packaging/debian/remotix.service") + ")", "rpm", "Arch", "Why"], [
        [c("ExecStart"), c("/bin/sh -c 'exec …/remotix …'"), "The binary directly", "The binary directly",
         "rpm: systemd moves to " + c("remotix_t") + " only if it executes " + c("remotix_exec_t") + " itself; a shell "
         "in between would stay " + c("unconfined_service_t") + "."],
        ["Options", c("--indirizzo 0.0.0.0 --nome %H --porta … --certificati /var/lib/remotix/certificati --pagina "
                      "/usr/share/remotix/pagina.html --ban-file /var/lib/remotix/ban --journal") + " + "
         + c("REMOTIX_OPZIONI"), "Same", "Same <b>without</b> " + c("--journal") + "; " + c("--nome")
         + " from " + c("REMOTIX_NOME"), "No bench option (" + c("--rilievo") + " (frame dump), " + c("--comando-socket") + ", "
         + c("--audio-prova") + " (test tone), " + c("--parlantina") + " (verbose)): R13."],
        [c("EnvironmentFile"), c("/usr/share/remotix/remotix.conf") + " then " + c("/etc/remotix/remotix.conf.d/*.conf"),
         "Same", "None: " + c("Environment=") + " lines, drop-in via " + c("systemctl edit"), "Defaults in "
         + c("/usr") + ", choices in " + c("/etc") + "."],
        [c("KillMode"), c("mixed"), c("mixed"), c("mixed"), "SIGTERM to the parent only, then SIGKILL to what is left "
         "of the unit. Desktops are started with " + c("setsid --fork") + " outside the unit and survive a stop "
         "(measured T2, 10 of 10)."],
        [c("LimitRTPRIO") + " / " + c("LimitNICE"), "20 / −11", "20 / −11", "20 / −11", "Real-time priority for audio "
         "and video, as every bench since phase 9."],
        [c("Restart"), c("on-failure") + ", 2 s", "Same", "Same", ""],
        [c("RestartPreventExitStatus"), "78", "—", "—", "Left from an earlier version that refused to start without "
         "an installer mark; no code path exits 78 today."],
        ["Enabled by the package", "No (" + c("--no-enable --no-start") + ")", "No", "No (" + c("disable *")
         + " preset)", "Enabling is a step of the installer the administrator confirms (§10.12)."],
    ], "«TAB» — The unit in the three package families") + \
    warn("the Arch unit reads no " + c("EnvironmentFile") + ": the " + c("REMOTIX_PORTA") + " that the installer writes "
         "to " + c("/etc/remotix/remotix.conf.d/porta.conf") + " for a non-default port is not seen there, and the "
         "unit lacks " + c("--journal") + ". The deb and rpm units are the reference. Not settled yet.",
         "The Arch unit differs.") + \
    p("On SELinux distributions the " + c("remotix-selinux") + " sub-package (" + c("packaging/rpm/selinux/")
      + ") confines the server in " + c("remotix_t") + " with its own types for the executable, the port (7447 TCP "
      "and UDP, declared in CIL because " + c("portcon") + " cannot be written in a " + c(".te") + " module), "
      + c("/var/lib/remotix") + " and " + c("/run/remotix") + ". The domain may authenticate like a login program ("
      + c("auth_login_pgm_domain") + ", the rule of sshd and Cockpit's session), talk to logind, and transition to "
      "the users' domains, so desktops are born " + c("unconfined_t") + " like an ssh login. Without the module, "
      "measured 29 Sep 2026, the child exited with 37 (" + c("{ transition } unconfined_service_t → unconfined_t")
      + "); with it, enforcing, 0 denials on Fedora 44, Alma 10, Tumbleweed and Leap 16. A different port needs "
      + c("semanage port -a -t remotix_port_t -p tcp N") + " (and " + c("udp") + ") by the administrator.")

# ── 14.12 Known limits ───────────────────────────────────────────────────
S12 = p("The weaknesses that are known and written in the code, collected in one place for whoever evaluates "
        "exposing a REMOTIX server.", lead=True) + \
    table(["Limit", "Where", "Status"], [
        ["First connection per device open to a man-in-the-middle", c("SPECIFICHE.md") + " §4.1", "Accepted risk "
         "for own network or VPN; a real certificate removes the warning"],
        ["No QUIC Retry address validation", c("trasporto.c"), "To be put back before exposing the server"],
        ["Password-only authentication, no MFA", c("DECISIONI.md") + " §1.7", "Deferred by the user to after "
         "completion; when it comes, the screen-locker choice must be reread"],
        ["Local password copy zeroed with " + c("memset"), c("rcp.c"), "[?] R9.20: inspect the binary, then "
         + c("explicit_bzero()")],
        [c("/diario") + " is unauthenticated and writes a log line per request", c("pagina.c"), "Sanitised and cut; "
         "no rate limit in the code"],
        ["Ban shared behind NAT; 256-entry table", c("rcp.c"), "Declared price; eviction logged"],
        ["Unlock socket absent from the packaged units", "packaging", "Not settled yet"],
        ["Every journal line twice under systemd with " + c("--journal"), c("registro.c"), "Not settled yet"],
        ["Card groups include " + c("video"), c("figlio.c"), "Restriction to " + c("render") + " not settled yet"],
        ["Safari and iOS", "—", "Never tested"],
    ], "«TAB» — Known limits of the security model")

CHAPTER = ("Security model", [
    ("Two security levels", S1),
    ("Certificates and TLS settings of the server", S2),
    ("Authentication with PAM", S3),
    ("The PAM service files", S4),
    ("The address ban", S5),
    ("The unlock command socket", S6),
    ("Isolation between users", S7),
    ("The graphics card groups", S8),
    ("What REMOTIX does not change", S9),
    ("The power belts, shipped inert", S10),
    ("The service unit and SELinux", S11),
    ("Known limits of the security model", S12),
])
