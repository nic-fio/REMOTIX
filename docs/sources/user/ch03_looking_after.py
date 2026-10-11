"""User Manual, chapter 3 — looking after an installation: checking it, updating, uninstalling, the logs.
Sources: installer/cmd/remotix-install/main.go, installer/engine/texts.go, uninstall.go,
packaging/debian/remotix.service and remotix.postrm, src/main.c (--journal), src/session.c (session.log),
src/remotix-no-poweroff.rules, packaging/*/remotix-no-suspend.conf and the belts in
packaging/debian/rules, rpm/remotix.spec, arch/PKGBUILD."""
from build import c, p, steps, table, term, ul, warn

RUN = "remotix-X.Y.Z-R.run"

STATUS = """$ sudo remotix-install status
…  CONFIRMED

Certification of installation …: GREEN
  PASS     …"""

S_STATUS = p("The installer stays on the machine as " + c("remotix-install") + ", so the installation can be "
             "checked again at any time, without the " + c(".run") + " file.", lead=True) + \
    term(STATUS, "Checking an installation (shortened)") + \
    p("It lists the installer's operations, then repeats the checks made at installation time and gives one of "
      "three results:") + \
    table(["Result", "Meaning"], [
        [c("GREEN"), "Everything passes."],
        [c("CONDITIONAL"), "It works, but something needs attention or could not be checked — usually the "
         "firewall."],
        [c("RED"), "Something REMOTIX installed is no longer in place, or a required check fails."],
    ], "«TAB» — The result of " + c("remotix-install status")) + \
    p("On a machine where REMOTIX was not installed by the installer it says “REMOTIX is not installed by the "
      "installer on this machine.”")

S_UPDATE = p("To update, run the newer " + c(".run") + " file exactly as for the installation. There is no "
             "automatic update.", lead=True) + \
    steps([
        "Copy the new file to the machine and run " + c(f"sudo sh {RUN}") + ".",
        "The installer sees the existing installation and makes an <b>upgrade</b> plan: only the packages change.",
        "Answer " + c("y") + " to " + c("Proceed? [y/N]") + ".",
    ]) + \
    p("The service restarts, and open desktops are <b>not</b> closed: people connected at that moment see the "
      "page disconnect, sign in again and find their windows. If the version is already installed the "
      "installer says “REMOTIX X is already installed: nothing to do.”") + \
    p("Updates of the distribution itself (" + c("apt upgrade") + ", " + c("dnf upgrade") + " and so on) are "
      "fine: the installation stays valid.")

UNINSTALL = """$ sudo remotix-install uninstall
The plan (uninstallation, …):
  …

Remove REMOTIX? [y/N]"""

S_UNINSTALL = p("REMOTIX is removed with the installer that stays on the machine:", lead=True) + \
    term(UNINSTALL, "Uninstalling (shortened)") + \
    p("Like the installation, it first shows the plan and asks " + c("Remove REMOTIX? [y/N]") + ". It undoes what "
      "the installation did, and only that:") + \
    ul([
        "it stops and disables the service;",
        "it closes every open REMOTIX desktop — <b>unsaved work in them is lost</b>, so warn people first; a "
        "session at the machine itself or by ssh is not touched;",
        "it takes people out of the graphics-card groups that REMOTIX put them in;",
        "it removes each user's " + c("~/.local/state/remotix/session.log") + ";",
        "it removes the packages it installed. A package that something else now needs is kept, and the plan "
        "says so.",
    ]) + \
    table(["Command", "What stays"], [
        [c("sudo remotix-install uninstall"), "The installer's history of operations, in "
         + c("/var/lib/remotix") + ", for support."],
        [c("sudo remotix-install uninstall --purge"), "Nothing: the configuration and REMOTIX's data go too "
         "(like " + c("apt purge") + ")."],
    ], "«TAB» — Uninstalling, with and without " + c("--purge")) + \
    warn("packages added later by an <i>upgrade</i> (a new dependency of a newer version) are not removed by "
         + c("uninstall") + ".", "Known limit.")

S_LOGS = p("When something does not work, the reason is written down. These are the places to look:",
           lead=True) + \
    table(["What", "Where", "How to read it"], [
        ["The server and each user's REMOTIX process", "the systemd journal", c("journalctl -t remotix")],
        ["The service as a whole (start, stop, crash)", "the systemd journal", c("journalctl -u remotix")],
        ["A user's desktop (what the desktop itself prints)", c("~/.local/state/remotix/session.log")
         + " in that user's home", "any text viewer"],
        ["Each installation, upgrade or uninstallation", c("/var/lib/remotix/operations/<id>/")
         + ": " + c("certificate.txt") + " is the summary, " + c("log.jsonl") + " every step",
         c("sudo remotix-install status") + " lists the operations"],
    ], "«TAB» — Where the logs are") + \
    p("Every message of the installer has a code (" + c("RX-…") + "); quote it when asking for help. "
      "Suggestions and bug reports are welcome as issues in the GitHub repository.")

B = "/usr/share/remotix/belts/"

S_SHARED = p("REMOTIX protects its own sessions: a user connected through REMOTIX cannot power off, restart or "
             "suspend the machine.", lead=True) + \
    p("For people sitting at the machine, the rules are the administrator's: REMOTIX does not change the "
      "system. On a machine that many people really share, though, no ordinary user should be able to take it "
      "down for everyone. For that case REMOTIX ships two ready-made rules, <b>switched off</b>, in the folder "
      + c(B) + ". Nothing reads them there; each one works only once the administrator copies it into place.") + \
    table(["File", "What it does", "Switch it on", "Switch it off"], [
        [c(B + "50-remotix-no-poweroff.rules"),
         "Ordinary users can no longer power off, restart, suspend or hibernate the machine (all twelve "
         "login1 actions, also with other people signed in). " + c("sudo systemctl poweroff") +
         " still works.",
         c("sudo cp " + B + "50-remotix-no-poweroff.rules /etc/polkit-1/rules.d/") +
         "<br>Nothing to reload: polkit reads it by itself.",
         c("sudo rm /etc/polkit-1/rules.d/50-remotix-no-poweroff.rules")],
        [c(B + "remotix-no-suspend.conf"),
         "The machine cannot suspend or hibernate at all, not even for root.",
         c("sudo mkdir -p /etc/systemd/sleep.conf.d") + "<br>" +
         c("sudo cp " + B + "remotix-no-suspend.conf /etc/systemd/sleep.conf.d/") +
         "<br>Nothing to reload.",
         c("sudo rm /etc/systemd/sleep.conf.d/remotix-no-suspend.conf")],
    ], "«TAB» — The two ready-made rules for a shared machine") + \
    p("Each file can be switched on alone. The administrator always keeps " + c("sudo systemctl poweroff") +
      " and " + c("sudo systemctl reboot") + ".") + \
    warn("switching these on is the administrator's choice, and uninstalling REMOTIX does not remove files the "
         "administrator copied: remove them with the commands in the last column.", "Whose choice.")

CHAPTER = ("Looking after an installation", [
    ("Checking an installation", S_STATUS),
    ("Updating", S_UPDATE),
    ("Uninstalling", S_UNINSTALL),
    ("On a shared machine", S_SHARED),
    ("Where the logs are", S_LOGS),
])
