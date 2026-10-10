from build import c, note, p, table

S1 = p("Defects found while this manual was written (10 October 2026), by reading the code against the documents. "
       "Each one was checked in the source. They are recorded here so that a maintainer meets them before a user does; "
       "a defect leaves this table in the commit that cures it.", lead=True) + \
    table(["Defect", "Where", "Consequence"], [
        ["<b>No way to lift an address ban on an installed machine.</b> The unlock socket " + c("--comando-socket")
         + " is treated as a bench option, and none of the three packaged units passes it.",
         c("packaging/debian/remotix.service") + ", " + c("packaging/rpm/remotix.service") + ", "
         + c("packaging/arch/remotix.service"),
         "A banned address waits the full 12 hours. The unlock command promised by SPECIFICHE.md §4.2 and RCP.md §4.4-bis "
         "does not exist there; the directory " + c("/run/remotix") + " is created for a socket nobody opens."],
        ["<b>The Arch unit reads no configuration.</b> It has no " + c("EnvironmentFile") + " and no "
         + c("--journal") + ", unlike the Debian and RPM units.",
         c("packaging/arch/remotix.service"),
         "A non-default port chosen at installation is never applied, so the installation's own verification fails "
         "and it rolls back; " + c("REMOTIX_OPZIONI") + " is ignored; nothing reaches the journal."],
        ["<b>The first enrolment in the graphics card groups ends every session of that user.</b> After adding the "
         "user to the groups of the " + c("/dev/dri") + " nodes, the parent (before the fork) runs " + c("loginctl terminate-user")
         + " so that the new groups reach the compositor. It spares a live REMOTIX desktop (" + c("ritrovo_vivo()")
         + ", the found-again check), but nothing else.",
         c("iscrivi_ai_gruppi_della_scheda()") + " (enrol in the card groups) in " + c("src/figlio.c"),
         "The first REMOTIX login of a user who is not yet in the group closes that user's SSH and local sessions "
         "without warning. It happens once per user."],
        ["<b>The groups are all those of the card nodes</b>, usually " + c("video") + " and " + c("render")
         + ", while DECISIONI.md §10.36 asks for " + c("render") + " alone, if it holds on the four desktops (still to "
         "be tried there).",
         c("iscrivi_ai_gruppi_della_scheda()"),
         c("video") + " also grants " + c("/dev/fb*") + " and webcams."],
        ["<b>The installer knows no derivative distribution by name.</b> " + c("Bersaglio()")
         + " (target) builds the package folder from " + c("ID") + " and " + c("VERSION_ID") + " (for example "
         + c("linuxmint22") + "); only Arch-like, openSUSE and Alma/Rocky/RHEL IDs are mapped. The .run carries "
         "only the seven release targets of " + c("packaging/rilascio.sh") + ".",
         c("installatore/motore/archivio.go"),
         "Linux Mint, and any Debian, Ubuntu or Fedora version other than the targets, stop with " + c("RX-MANCA-004") + " even "
         "where the catalogue calls them compatible."],
        ["<b>Uninstallation forgets what upgrades added.</b> The removal plan is built from the operation named in "
         + c("installation.json") + ", which only an installation writes, never an upgrade.",
         c("installatore/motore/disinstalla.go") + ", " + c("installatore/motore/operazione.go"),
         "Packages that a later upgrade brought in as new stay on the machine."],
        ["<b>The server would reject its own farewell reason from the client.</b> " + c("motivo_di_82()")
         + " (the reasons of RCP.md §8.2) accepts 0x01–0x0F, while RCP/1 defines 0x10 ("
         + c("SESSIONE_TERMINATA") + ", session ended).",
         c("src/rcp.c"),
         "Harmless today, because only the server sends 0x10; a client " + c("CONGEDO") + " (farewell) with 0x10 would be answered with "
         + c("ERRORE_PROTOCOLLO") + " (protocol error)."],
        ["<b>Bench messages are compiled into the product.</b> " + c("BANCO_MARCA") + " (bench marker) is present, "
         "switched off with " + c("BANCO_ACCESO") + " (bench switch) set to 0, whereas RCP.md §7.5 says it must be "
         "absent from the installed binary, not merely off.",
         c("src/rcp.c"),
         "The server answers it with " + c("BANCO_ESITO") + " " + c("FUNZIONE_SPENTA") + " (function off) instead of "
         "not knowing it. (RCP.md's own test table asks for that answer, so the specification contradicts itself.)"],
        ["<b>Retired installer codes are still raised.</b> " + c("RX-H264-003") + " and " + c("RX-H264-004")
         + " are marked retired in " + c("codici.go") + " but " + c("codiceH264()") + " still returns them for "
         "Fedora and openSUSE; " + c("RX-FW-004") + " is still returned by the firewall stub for nftables or no "
         "firewall.",
         c("installatore/motore/preflight.go") + ", " + c("installatore/motore/ambiente.go"),
         "An administrator may meet a code the catalogue says no longer exists."],
        ["<b>The package metadata still speaks of the old licence and in Italian.</b> The Debian copyright file says "
         "proprietary, licence not yet decided; the spec says " + c("LicenseRef-Proprietary") + " and its summaries "
         "and descriptions are Italian.",
         c("packaging/debian/copyright") + ", " + c("packaging/rpm/remotix.spec"),
         "Contradicts DECISIONI.md §10.33 (free of charge) and §10.32 (the product speaks English)."],
        ["<b>Parts of the interface are still in Italian</b>: the farewell sentences of the page, the logout "
         "notice, the ban notice served by the page server.",
         c("src/pagina.html") + ", " + c("src/pagina.c"),
         "Listed as pending in DECISIONI.md §10.32."],
    ], "«TAB» — Open defects in the product")

S2 = p("Comments and log lines in the code that no longer describe what the code does. None changes behaviour, but each "
       "one misleads the next reader.", lead=True) + \
    table(["Where", "What it says", "What is true"], [
        [c("src/rcp.c"), "the QUIC " + c("max_idle_timeout") + " is 120 s", "the transport announces 30 s ("
         + c("IDLE_MS") + " in " + c("src/trasporto.c") + ")"],
        [c("src/codificatore.h"), "the bandwidth ceiling applies only to " + c("h264_vaapi") + ", the software "
         "fallback keeps its CRF", "no software path since phase 19; the ceiling also applies to Vulkan Video, as VBR"],
        [c("src/cattura.h"), "canvas limits 200..8192", "320×240 to 4096×2304 (" + c("rcp.h") + "), larger "
         "requests reduced to the maximum"],
        [c("src/cursore.c"), "encoded cursor colours 0x40..0x83", "0x40..0x8D: " + c("FORMA_QUANTE") + " is 78 "
         "shapes (" + c("src/forma.h") + ")"],
        [c("src/sessione.h"), "the GNOME session is born with a monitor",
         "it starts headless without " + c("--virtual-monitor") + " (removed on 14 Aug 2026, " + c("sessione.c")
         + "); the only monitor is the capture's"],
        [c("src/sentinella.c"), c("PAM_RHOST") + " is not set yet, so the remote-session check cuts nothing",
         "set by both the PAM check (" + c("autenticazione.c") + ") and the child's PAM session (" + c("figlio.c") + ")"],
        [c("src/input.c"), "line references " + c("figlio.c:3964") + " and " + c("figlio.c:6365"),
         "the lines have moved"],
        [c("src/figlio.c") + ", " + c("struct corpo_video"), "codec 1 = HEVC, 2 = AV1, 0 = off",
         "AV1 is retired; H.264 is 3 (" + c("RCP_CODEC_VIDEO_MAX") + " in " + c("rcp.h") + ")"],
        [c("src/pagina.html"), "WebGL2 is a candidate path, not the default; a message naming the codecs (HEVC, AV1)",
         "WebGL2 has been the default since 26 Sep 2026; the codecs are HEVC and H.264"],
        [c("src/main.c"), "the program is at phase 1, with no video (header, usage line, first log line); 0x06 "
         "means no encoding capacity left", "0x06 is composition capacity since DECISIONI.md §4.6-nonies"],
        [c("src/main.c"), "the help of " + c("--journal") + ": " + c("--parlantina") + " (chatter) lines go to "
         "the journal with PRIORITY 7", "detail lines never reach the journal (" + c("src/registro.c") + ")"],
        [c("WT_PAVIMENTO_BYTE_MS") + " in " + c("src/webtransport.c") + ", the help of " + c("--tetto-banda-mbit")
         + " in " + c("src/main.c"), "a 20 Mbit/s floor",
         "the decided floor is 30 Mbit/s since 23 Aug 2026 (DECISIONI.md §3.1-sexies)"],
        [c("packaging/debian/remotix.service") + ", " + c("packaging/rpm/remotix.service"),
         c("RestartPreventExitStatus=78"), "the server exits only with 0, 1 or 2"],
        ["comments in " + c("remotix.postinst") + ", " + c("remotix.spec") + ", " + c("remotix-firewalld.xml")
         + " and the three " + c("remotix-niente-sospensione.conf") + " (no-suspend) files", "the engine enables the power safety settings and opens the firewall with consent",
         "since DECISIONI.md §10.36 it does neither"],
    ], "«TAB» — Stale texts in the code") + \
    note("the project documents (SPECIFICHE.md, RCP.md, DECISIONI.md, the phase documents) carry their own list of "
         "stale passages, found in the same pass; they are corrected there, not here.", "Documents.")

CHAPTER = ("Appendix C — Known issues", [
    ("Open defects in the product", S1),
    ("Stale texts in the code", S2),
])
