from build import c, note, p, rif, table

S1 = p("Defects found while this manual was written (10 October 2026), by reading the code against the documents, and "
       "checked again in the source of 1.0.0 (11 October 2026). They are recorded here so that a maintainer meets them before a user does; "
       "a defect leaves this table in the commit that cures it.", lead=True) + \
    table(["Defect", "Where", "Consequence"], [
        ["<b>No way to lift an address ban on an installed machine.</b> The unlock socket " + c("--command-socket")
         + " is treated as a bench option, and none of the three packaged units passes it.",
         c("packaging/debian/remotix.service") + ", " + c("packaging/rpm/remotix.service") + ", "
         + c("packaging/arch/remotix.service"),
         "A banned address waits the full step of the ladder (15 minutes, 1 hour or 12 hours). The unlock command promised by SPECS.md §4.2 and RCP.md §4.4-bis "
         "does not exist there; the directory " + c("/run/remotix") + " is created for a socket nobody opens."],
        ["<b>(Fixed in 1.5) The first enrolment in the graphics card groups used to end every session of that user.</b> Until 1.0 the "
         "parent ran " + c("loginctl terminate-user") + " so the new groups reached the compositor; 1.5 removed it and gives the user's "
         "primary group an ACL on the render nodes instead (DECISIONS-11 §11.4).",
         c("render_grant_add()") + " in " + c("src/render_grant.c"),
         "Nothing is closed. Declared limits: a device recreated while the desktop lives loses the grant; a network account gets none "
         "and its desktop is born in software."],
        ["<b>(Fixed in 1.5) The groups are those of the render nodes only</b> — " + c("render") + " on the usual distributions; " + c("video")
         + " (which also grants " + c("/dev/fb*") + " and webcams) is no longer added (DECISIONS-11 §11.38). Open: AMD and NVIDIA "
         "were not measured; with the NVIDIA proprietary driver the card is opened through " + c("/dev/nvidia*") + ".",
         c("collect_card_groups()"),
         "A desktop born in software on such a machine means " + c("video") + " must be added by hand."],
        ["<b>The installer knows no derivative distribution by name.</b> " + c("Target()")
         + " builds the package folder from " + c("ID") + " and " + c("VERSION_ID") + " (for example "
         + c("linuxmint22") + "); only Arch-like, openSUSE and Alma/Rocky/RHEL IDs are mapped. The .run carries "
         "only the seven release targets of " + c("packaging/release.sh") + ".",
         c("installer/engine/archive.go"),
         "Linux Mint, and any Debian, Ubuntu or Fedora version other than the targets, stop with " + c("RX-MANCA-004") + " even "
         "where the catalogue calls them compatible."],
        ["<b>Uninstallation forgets what upgrades added.</b> The removal plan is built from the operation named in "
         + c("installation.json") + ", which only an installation writes, never an upgrade.",
         c("installer/engine/uninstall.go") + ", " + c("installer/engine/operation.go"),
         "Packages that a later upgrade brought in as new stay on the machine."],
        ["<b>The server would reject its own farewell reason from the client.</b> " + c("reason_for_82()")
         + " (the reasons of RCP.md §8.2) accepts 0x01–0x0F, while RCP/1 defines 0x10 ("
         + c("SESSION_TERMINATED") + ", session ended).",
         c("src/rcp.c"),
         "Harmless today, because only the server sends 0x10; a client " + c("FAREWELL") + " with 0x10 would be answered with "
         + c("PROTOCOL_ERROR") + "."],
        ["<b>Bench messages are compiled into the product.</b> " + c("BENCH_MARK") + " is present, "
         "switched off with " + c("BENCH_ON") + " set to 0, whereas RCP.md §7.5 says it must be "
         "absent from the installed binary, not merely off.",
         c("src/rcp.c"),
         "The server answers it with " + c("BENCH_OUTCOME") + " " + c("FEATURE_OFF") + " instead of "
         "not knowing it. (RCP.md's own test table asks for that answer, so the specification contradicts itself.)"],
    ], "«TAB» — Open defects in the product")

S2 = p("Comments and log lines in the code that no longer describe what the code does. None changes behaviour, but each "
       "one misleads the next reader.", lead=True) + \
    table(["Where", "What it says", "What is true"], [
        [c("src/rcp.c"), "the QUIC " + c("max_idle_timeout") + " is 120 s", "the transport announces 30 s ("
         + c("IDLE_MS") + " in " + c("src/transport.c") + ")"],
        [c("src/encoder.h"), "the bandwidth ceiling applies only to " + c("h264_vaapi") + ", the software "
         "fallback keeps its CRF", "no software path since phase 19; the ceiling also applies to Vulkan Video, as VBR"],
        [c("src/capture.h"), "canvas limits 200..8192", "320×240 to 4096×2304 (" + c("rcp.h") + "), larger "
         "requests reduced to the maximum"],
        [c("src/cursor.c"), "encoded cursor colours 0x40..0x83", "0x40..0x8D: " + c("SHAPE_COUNT") + " is 78 "
         "shapes (" + c("src/shape.h") + ")"],
        [c("src/session.h"), "the GNOME session is born with a monitor",
         "it starts headless without " + c("--virtual-monitor") + " (removed on 14 Aug 2026, " + c("session.c")
         + "); the only monitor is the capture's"],
        [c("src/sentinel.c"), c("PAM_RHOST") + " is not set yet, so the remote-session check cuts nothing",
         "set by both the PAM check (" + c("authentication.c") + ") and the child's PAM session (" + c("child.c") + ")"],
        [c("src/input.c"), "line references " + c("child.c:3964") + " and " + c("child.c:6365"),
         "the lines have moved"],
        [c("src/child.c") + ", " + c("struct body_video"), "codec 1 = HEVC, 2 = AV1, 0 = off",
         "AV1 is retired; H.264 is 3 (" + c("RCP_CODEC_VIDEO_MAX") + " in " + c("rcp.h") + ")"],
        [c("src/page.html"), "a message naming the two video codecs as HEVC and AV1",
         "AV1 left the product; the codecs are HEVC and H.264"],
        [c("src/main.c"), "the program is at phase 1, with no video (header, usage line, first log line); 0x06 "
         "means no encoding capacity left", "0x06 is composition capacity since DECISIONS.md §4.6-nonies"],
        [c("src/main.c"), "the help of " + c("--journal") + ": " + c("--verbose") + " lines go to "
         "the journal with PRIORITY 7", "detail lines never reach the journal (" + c("src/log.c") + ")"],
        [c("WT_FLOOR_BYTE_MS") + " in " + c("src/webtransport.c") + ", the help of " + c("--bandwidth-cap-mbit")
         + " in " + c("src/main.c") + " (help and comments)", "a 20 Mbit/s floor",
         "the decided floor is 30 Mbit/s since 23 Aug 2026 (DECISIONS.md §3.1-sexies)"],
        [c("packaging/debian/remotix.service"),
         c("RestartPreventExitStatus=78"), "the server exits only with 0, 1 or 2"],
        ["comments in " + c("remotix.postinst") + ", " + c("remotix.spec") + ", " + c("remotix-firewalld.xml")
         + " and the three " + c("remotix-no-suspend.conf") + " files (whose own header already gives them an English name)", "the engine enables the power safety settings and opens the firewall with consent",
         "since DECISIONS.md §10.36 it does neither"],
    ], "«TAB» — Stale texts in the code") + \
    note("the project documents (SPECS.md, RCP.md, DECISIONS.md, the phase documents) carry their own list of "
         "stale passages, found in the same pass; they are corrected there, not here.", "Documents.")

S3 = p("Not defects but declared limits of 1.0.0: each is written in the log or in DECISIONS.md, and each has a "
       "known cause outside the code that would have to change to remove it.", lead=True) + \
    table(["Limit", "Where", "What it means"], [
        ["<b>KDE without labwc keeps its birth size at reattach.</b> The nested KWin needs a labwc to host it; where "
         "none is installed " + c("remotix --kwin-nested") + " starts KWin " + c("--virtual") + " and says so.",
         c("src/kwin.c"),
         "The desktop keeps the canvas it was born with; the page centres it with black bands. The packages ask for "
         "labwc on KDE, so this happens only on a damaged installation (DECISIONS.md §10.40)."],
        ["<b>The nested KWin costs frames at 3K and 4K on an integrated card.</b>",
         c("src/kwin.c") + ", " + c("src/session.c"),
         "On the Intel UHD 770 (integrated) a 60 fps scene loses 3–4 fps at 3K and 9–14 fps at 4K; nothing at "
         "1080p and 2K (" + rif("The cost of the nested KWin") + ")."],
        ["<b>Our own labwc must be followed by hand.</b> From KWin 6.5 on the Ubuntu 26.04, Fedora 44, Alma 10, Tumbleweed and "
         "Arch packages build labwc 0.9.3 with a patched wlroots 0.19.2 (static) and install it at "
         + c("/usr/lib/remotix/labwc") + ".",
         c("packaging/labwc-ospite/") + ", " + c("packaging/rpm/remotix.spec"),
         "At every REMOTIX release the releases of labwc and wlroots must be checked, and the patch dropped if upstream fixes "
         "it (DECISIONS.md §10.43, replaced in 1.5)."],
        ["<b>KWin 6.6 (Ubuntu 26.04) is untested.</b>", "—",
         "The nested road was tried on KWin 6.3.6 (Debian 13) and 6.4.2 (openSUSE Leap 16) only; no box of Ubuntu "
         "26.04 exists on the test machine."],
    ], "«TAB» — Declared limits")

CHAPTER = ("Appendix C — Known issues", [
    ("Open defects in the product", S1),
    ("Stale texts in the code", S2),
    ("Declared limits", S3),
])
