from build import c, note, p, table

S1 = p("Defects found while this manual was written (10 October 2026), by reading the code against the documents. "
       "Each one was checked in the source. They are recorded here so that a maintainer meets them before a user does; "
       "a defect leaves this table in the commit that cures it.", lead=True) + \
    table(["Defect", "Where", "Consequence"], [
        ["<b>No way to lift an address ban on an installed machine.</b> The unlock socket " + c("--comando-socket")
         + " is treated as a bench option, and none of the three packaged units passes it.",
         c("packaging/debian/remotix.service") + ", " + c("packaging/rpm/remotix.service") + ", "
         + c("packaging/arch/remotix.service"),
         "A banned address waits the full 12 hours. The promise of an unlock command (SPECIFICHE §4.2, RCP §4.4-bis) "
         "is not kept; the directory " + c("/run/remotix") + " is created for a socket nobody opens."],
        ["<b>The Arch unit reads no configuration.</b> It has no " + c("EnvironmentFile") + " and no "
         + c("--journal") + ", unlike the Debian and RPM units.",
         c("packaging/arch/remotix.service"),
         "A non-default port chosen at installation is never applied, so the installation's own verification fails "
         "and it rolls back; " + c("REMOTIX_OPZIONI") + " is ignored; nothing reaches the journal."],
        ["<b>The first enrolment in the graphics card groups ends every session of that user.</b> After adding the "
         "user to the groups of the " + c("/dev/dri") + " nodes, the parent runs " + c("loginctl terminate-user")
         + " so that the new groups reach the compositor. It spares a live REMOTIX desktop (" + c("ritrovo_vivo()")
         + "), but nothing else.",
         c("iscrivi_ai_gruppi_della_scheda()") + " in " + c("src/figlio.c"),
         "The first REMOTIX login of a user who is not yet in the group closes that user's SSH and local sessions "
         "without warning. It happens once per user."],
        ["<b>The groups are all those of the card nodes</b>, usually " + c("video") + " and " + c("render")
         + ", while DECISIONI §10.36 asks for " + c("render") + " alone (not yet measured on the four desktops).",
         c("iscrivi_ai_gruppi_della_scheda()"),
         c("video") + " also grants " + c("/dev/fb*") + " and webcams."],
        ["<b>The installer knows no derivative distribution by name.</b> " + c("Bersaglio()")
         + " builds the package folder from " + c("ID") + " and " + c("VERSION_ID") + " (for example "
         + c("linuxmint22") + "), and the .run carries only the seven release targets.",
         c("installatore/motore/archivio.go"),
         "Linux Mint, and any Debian, Ubuntu or Fedora version other than the targets, stop with RX-MANCA-004 even "
         "where the catalogue calls them compatible."],
        ["<b>Uninstallation forgets what upgrades added.</b> The removal plan is built from the original "
         "installation only.",
         c("installatore/motore/disinstalla.go"),
         "Packages that a later upgrade brought in as new stay on the machine."],
        ["<b>The server would reject its own farewell reason from the client.</b> " + c("motivo_di_82()")
         + " accepts reasons 0x01–0x0F, while RCP/1 defines 0x10.",
         c("src/rcp.c"),
         "Harmless today, because only the server sends 0x10; it becomes a protocol error the day the client does."],
        ["<b>Bench messages are compiled into the product.</b> " + c("BANCO_MARCA") + " is present, switched off "
         "with " + c("BANCO_ACCESO") + " set to 0, whereas the protocol says it must be absent from the delivered "
         "binary.",
         c("src/rcp.c"),
         "The server answers it with FUNZIONE_SPENTA instead of not knowing it."],
        ["<b>Retired installer codes are still raised.</b> RX-H264-003 and RX-H264-004 are marked retired but "
         + c("codiceH264()") + " still returns them; RX-FW-004 likewise.",
         c("installatore/motore/preflight.go") + ", " + c("installatore/motore/ambiente.go"),
         "An administrator may meet a code the catalogue says no longer exists."],
        ["<b>The package metadata still speaks of the old licence and in Italian.</b>",
         c("packaging/debian/copyright") + ", " + c("packaging/rpm/remotix.spec"),
         "Contradicts DECISIONI §10.33 (free of charge) and §10.32 (the product speaks English)."],
        ["<b>Parts of the interface are still in Italian</b>: the farewell sentences of the page, the logout "
         "dialog, the ban notice.",
         c("src/pagina.html") + ", " + c("src/pagina.c"),
         "Listed as pending in DECISIONI §10.32."],
    ], "«TAB» — Open defects in the product")

S2 = p("Comments and log lines in the code that no longer describe what the code does. None changes behaviour, but each "
       "one misleads the next reader.", lead=True) + \
    table(["Where", "What it says", "What is true"], [
        [c("src/rcp.c"), "the QUIC idle timeout is 120 s", "the transport announces 30 s"],
        [c("src/autenticazione.c"), "the refusal is RESPINTO (0x07)", "the code value is CREDENZIALI_ERRATE"],
        [c("src/codificatore.h"), "AV1, a software fallback, the ceiling only on " + c("h264_vaapi"),
         "no software path since phase 19; the ceiling also applies to Vulkan, as VBR"],
        [c("src/cattura.h"), "canvas limits 200..8192", "320×240 to 4096×2304, larger requests reduced"],
        [c("src/cursore.c"), "encoded cursor colours 0x40..0x83", "0x40..0x8D with 78 shapes"],
        [c("src/sessione.h"), "the GNOME session is born with a monitor",
         "it starts headless without one; the only monitor is the capture's"],
        [c("src/sentinella.c"), "PAM_RHOST is never set", "set by both the PAM check and the child's PAM session"],
        [c("src/input.c"), "line references into " + c("src/figlio.c"), "the lines have moved"],
        [c("src/pagina.html"), "WebGL2 is a candidate, not the default; codecs (HEVC, AV1)",
         "WebGL2 has been the default since 26 Sep 2026; the codecs are HEVC and H.264"],
        [c("src/main.c"), "phase 1 (header and first log line); 0x06 is encoding capacity",
         "0x06 is composition capacity since DECISIONI §4.6-nonies"],
        [c("WT_PAVIMENTO_BYTE_MS") + ", the help of " + c("--tetto-banda-mbit"), "a 20 Mbit/s floor",
         "the product floor is 30 Mbit/s since 23 Aug 2026"],
        [c("packaging/debian/remotix.service"), c("RestartPreventExitStatus=78"),
         "the server exits only with 0, 1 or 2"],
        ["packaging comments, ufw and firewalld files", "the engine enables the power belts and opens the firewall "
         "with consent", "since DECISIONI §10.36 it does neither"],
    ], "«TAB» — Stale texts in the code") + \
    note("the project documents (SPECIFICHE.md, RCP.md, DECISIONI.md, the phase documents) carry their own list of "
         "stale passages, found in the same pass; they are corrected there, not here.", "Documents.")

CHAPTER = ("Appendix C — Known issues", [
    ("Open defects in the product", S1),
    ("Stale texts in the code", S2),
])
