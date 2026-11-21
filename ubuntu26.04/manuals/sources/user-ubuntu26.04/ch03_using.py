"""User Manual, chapter 3 — connecting and using REMOTIX.
Sources: src/page.html (sign-in form and texts, keyboard, clipboard, touch layout, the shortcut catalogue
SC_CATALOG), docs/SPECS.md §5.1-§5.3, §6, §7, §9, §10, src/rcp.c, src/main.c (clocks)."""
from build import key, note, p, rif, sysf, table, term, ui, ul, warn

S_SIGNIN = p("Open the machine's address in the browser: <code class=\"sys\">https://machine-name:7447</code> (use "
             "the port the administrator tells you if it is not 7447). The first time on a device the browser warns "
             "about the certificate: see " + rif("Ubuntu 26.04: the first visit and the certificate") + ".", lead=True) + \
    p("The page shows a sign-in form with two fields, <b>Username</b> and <b>Password</b>, and a <b>Connect</b> "
      "button. Type the user name and password you have on that machine — the ones you would use at its own "
      "screen — and press Connect. Between the two fields and the button there is a <b>Keyboard</b> menu, "
      "which tells the machine what kind of keyboard you are typing on (Italian, French, German, English (US) and so on: "
      "33 layouts). It already shows the layout that goes with the language of your browser, so most people leave it "
      "alone; if your keyboard is different, choose the right one before pressing Connect. When you choose, the page "
      "remembers it on that browser and that device, and proposes it again next time; the browser language is used "
      "only until you have chosen. To change keyboard later, sign out and sign in again. At the bottom the page says "
      "“Encrypted connection” and the name of the machine.") + \
    ul([
        "The answer takes about a second even when everything is right, and a refusal for a wrong user name or "
        "password takes about two and a half seconds. That is deliberate: it makes it impossible to tell, by "
        "timing, whether a user name exists.",
        "A green line then says “Admitted, new session…” (or “resumed session…” if you are coming back), with the size "
        "of the desktop, and the desktop appears in place of the form.",
        "The first sign-in after the machine has restarted, after the service was restarted, or after you logged out, is slower: the page says "
        + ui("Connected. The desktop is on its way…") + " and the desktop appears by itself, in a few seconds on "
        "most desktops and up to about thirty seconds on the first start. You do not have to do anything.",
        "<b>Who can sign in:</b> any user of the machine except <code class=\"sys\">root</code> and the users the "
        "administrator has excluded, with the machine's password. <b>Who cannot:</b> a user who is already signed "
        "in at the machine's own screen, and, while the first is connected, a second browser of the same user (see "
        + rif("When something does not work") + ").",
    ])

S_DESKTOP = p("Once signed in you have your own desktop — GNOME (Ubuntu), KDE Plasma (Kubuntu), XFCE (Xubuntu) or "
              "LXQt (Lubuntu), whichever the machine uses — in the browser tab.", lead=True) + \
    table(["", "What you should know"], [
        ["The size",
         "The desktop is created <b>as large as the browser window at the moment you sign in</b> (from 320×240 "
         "pixels, counted in screen pixels). REMOTIX is supported up to <b>3K</b>; the size you really get depends "
         "on the device and the browser you connect from. The program may accept a larger window, but that is not "
         "supported; a window larger than the maximum gets the desktop at the maximum, with bands around it."],
        ["Resizing the window",
         "Changing the size of the window during the session <b>does not change the desktop</b>: the page scales the "
         "picture to fit the new window. To get a desktop of exactly the new size, close the tab and sign in again "
         "(your programs stay open: see " + rif("Leaving and coming back") + ")."],
        ["Full screen",
         "The page has no full-screen button. Use your browser's own full screen (usually F11): the desktop has the "
         "same size, and the picture gets more room."],
        ["The mouse",
         "Move, click, double-click, right-click, middle-click, drag and wheel work as at the machine."],
        ["Sound",
         "What the desktop plays comes out of your device's speakers, through the browser tab (which must not be "
         "muted). Nothing goes back: there is no microphone."],
        ["No screen lock",
         "The desktops' screen lock is switched off in a remote session: the only way into the desktop is the "
         "sign-in page."],
        ["No power buttons",
         "There is no shut down, restart, suspend or hibernate in the desktop's menus, on any of the four desktops, "
         "because other people may be working on the same machine."],
        ["XFCE: the wallpaper",
         "XFCE keeps one wallpaper for each screen, and the remote desktop is a screen of its own: the wallpaper you "
         "chose at the machine does not pass to it by itself. Choose one in the remote desktop if you want it."],
        ["GNOME: the Overview",
         "The remote GNOME desktop starts in the Activities Overview, which covers the desktop. Press Escape or choose a "
         "program."],
        ["A background tab",
         "A browser may freeze a tab left in the background for a few minutes. REMOTIX then sees silence, detaches "
         "you, and keeps the desktop waiting: come back and sign in again."],
    ], "«TAB» — The desktop in the browser") + \
    note("an administrator action inside the desktop (installing a program, for example) asks for a "
         "password, as at the machine. On GNOME the password window of graphical programs was <b>not verified</b>: "
         "in the automatic test, a program started with <code class=\"sys\">pkexec</code> refused to start in a "
         "remote GNOME session, so no password window could appear. If it does not appear, do the same action with "
         "<code class=\"sys\">sudo</code> in a terminal. Three requests that a desktop makes on its own at "
         "sign-in, and that would only confuse, are settled quietly (see "
         + rif("Users, groups and what REMOTIX changes") + ").", "Passwords inside the desktop.")

S_KEYS = p("<b>Typing.</b> Letters, numbers and symbols travel as <i>letters</i>: what you type is what appears, "
           "whatever your keyboard layout, and accents and symbols that are keys of your layout (Shift and AltGr "
           "included) come out right. Keys that are not letters — Enter, Tab, Esc, the arrows, F1 to F12, Ctrl, "
           "Alt, Super — travel as <i>positions</i> on the keyboard, and so do letters when you hold Ctrl, Alt or "
           "Super (a shortcut such as Ctrl+C is a command, not text). The desktop's keyboard layout is set again "
           "at every sign-in, from the Keyboard menu of the sign-in form. On GNOME the layout the page sends is written for the session in a small file in "
           "your home folder (" + sysf("~/.config/dconf/remotix") + "), which only REMOTIX uses.", lead=True) + \
    ul([
        "If characters come out wrong (for example a <i>y</i> where you typed a <i>z</i>, or a symbol that is not the one printed on "
        "your key), or a shortcut seems to be on the wrong key, check the <b>Keyboard</b> menu of the sign-in form: it must be the "
        "layout of the keyboard you are really typing on. Sign out, sign in again with the right one.",
        "If you use a <b>virtual machine</b> (for example QEMU) inside the remote desktop, choose in the Keyboard menu the layout "
        "of the system that runs <i>in the virtual machine</i>: such programs pass on the keys by position, and the guest system "
        "turns the positions into characters with its own layout.",
        "A character that is on no key of the session's layout (an emoji, another alphabet) produces <b>nothing</b>; "
        "it never produces a different letter. The server notes it in its log.",
        "Characters you compose with <b>dead keys</b> (an accent typed first, then the letter) or with an <b>input "
        "method</b> (the kind used for Chinese, Japanese or Korean) may not arrive: the page ignores a dead key by "
        "itself and a keystroke that is still being composed. <b>Not yet verified</b> case by case. Characters that "
        "have a key of their own on your layout (for example é on an Italian or French keyboard) arrive "
        "normally.",
    ]) + \
    p("<b>Combinations that do not reach the desktop.</b> The page itself keeps <b>no</b> key combination: every "
      "command it receives is sent to the desktop, and the page asks the browser not to act on it as well (so "
      "Ctrl+S or F5 should go to the desktop only; this was <b>not measured</b> key by key). The one exception is "
      "Ctrl+V, which the browser must see in order to paste. What cannot be recovered is what the <i>browser or "
      "your own computer</i> keeps before the page sees it: in a normal Chrome window, for example, Ctrl+W still "
      "closes the tab. The table comes from measurements made on <b>Debian 13</b>, on GNOME with Chrome 151 and "
      "Firefox 140 ESR; they were <b>not repeated on Ubuntu</b> (the tests there used newer browsers), but what a "
      "browser keeps depends on the browser and on your own computer, not on the machine you connect to, so the "
      "table is the best guide there is:") + \
    table(["Browser", "Kept by the browser or by your computer (does not reach the desktop)"], [
        ["Chrome, Edge (normal window)",
         key("Ctrl", "T") + ", " + key("Ctrl", "W") + ", " + key("Ctrl", "N") + ", " + key("Ctrl", "Shift", "N")
         + ", " + key("Ctrl", "Tab") + ", " + key("Ctrl", "Shift", "Tab") + ", " + key("Ctrl", "PageUp") + ", "
         + key("Ctrl", "PageDown") + ", " + key("Alt", "Tab") + ", " + key("Alt", "F4") + ", " + key("Alt", "F2")
         + ", " + key("Super", "D")],
        ["Chrome, Edge (full screen with F11)",
         key("Alt", "Tab") + ", " + key("Alt", "F4") + ", " + key("Alt", "F2") + ", " + key("Super", "D") + ", "
         + key("F11") + " (leaves full screen)"],
        ["Firefox (normal window)",
         key("Ctrl", "T") + ", " + key("Ctrl", "Tab") + ", " + key("Ctrl", "Shift", "Tab") + ", " + key("Ctrl", "PageUp")
         + ", " + key("Ctrl", "PageDown") + ", " + key("Super", "D")],
    ], "«TAB» — What the browser or the system keeps (Chrome 151 and Firefox 140 ESR, measured on Debian 13, not repeated on Ubuntu)") + \
    ul([
        "Your own computer may keep others that depend on it and were not measured: the Super (Windows) key, "
        "Alt+Tab, and combinations of Ctrl+Alt with the arrows or the function keys are the usual ones. On "
        "Android and Samsung DeX every combination with the Super key is kept by Android.",
        "The table is not complete for other browsers, other systems or Firefox in full screen: <b>not yet "
        "verified</b> there. Safari, macOS and iPhone were not tried at all.",
        "<b>The page offers no way to send the keys the browser keeps</b>, and no on-screen Ctrl+Alt+Del button: "
        "it is not available in the page as it is shipped. Use the desktop's own menus (for example “Log Out…”) "
        "instead of key combinations; for windows, the mouse works wherever a shortcut does not.",
    ])

S_CLIP = p("<b>Text only, in both directions.</b> You can copy text on your device and paste it in the remote "
           "desktop, and copy in the remote desktop and paste on your device. Images, files and formatting do not "
           "travel; the limit is one million bytes per copy. The tab of REMOTIX has to be the one in front "
           "(the browser lets a page write to your clipboard only then).", lead=True) + \
    table(["", "Chrome, Edge", "Firefox"], [
        ["Copy in the remote desktop, paste on your device",
         "Works by itself: when you copy in the desktop, the text arrives on your device's clipboard.",
         "Works by itself, in the same way."],
        ["Copy on your device, paste in the remote desktop",
         "Works by itself: Chrome tells the page when your clipboard changes, so the text is ready when you paste. "
         "If the browser asks for permission to read the clipboard, allow it.",
         "Firefox does not tell the page when your clipboard changes, so the text crosses when you press "
         + key("Ctrl", "V") + " <b>on the page</b>. If you paste in another way (the right-click menu of a "
         "program in the desktop) the new text may not have arrived yet. The page shows, for a few seconds, the "
         "hint “To paste here what you copied on your computer, press Ctrl+V on this page”."],
    ], "«TAB» — The clipboard, browser by browser") + \
    p("Safari was not tried.") + \
    note("this is what the page is built to do. On Ubuntu 26.04 the automatic tests checked the clipboard with Chrome "
         "(both directions) and with Firefox (the lines specific to Firefox), on the four desktops in the first "
         "rounds and on GNOME in the last one. Other browsers and Safari were not checked.", "What was tried.")

S_LEAVE = p("Your desktop belongs to <i>you</i>, not to the browser tab. Closing the tab, a dropped line or moving to "
            "another device does <b>not</b> close it. Stopping, restarting or upgrading the service, switching the "
            "machine off, or signing in at the machine's own screen with the same user <b>does</b> close it, with "
            "its programs: unsaved work is lost.",
            lead=True) + \
    table(["What you do or what happens", "What happens to the desktop"], [
        ["You close the tab or the browser, switch off your PC, or lose the network",
         "The desktop and all its programs <b>keep running</b> on the machine. Sign in again — from the same device "
         "or from another one — and you find everything as you left it."],
        ["You come back, but not within an hour",
         "If <b>60 minutes</b> go by in which you give no input at all (keys, mouse, touch), REMOTIX closes the "
         "desktop and its programs: unsaved work is lost. Looking at the screen or playing a video counts as no "
         "input. The next sign-in opens a new, empty desktop."],
        ["You stay connected but touch nothing for <b>30 minutes</b>",
         "The page is disconnected and says " + ui("you went half an hour without touching anything: getting back "
                                                   "in needs you, with your password — the programs stayed open")
         + ". Sign in again; the desktop is as you left it. If you still do not return, the 60-minute rule above "
         "applies."],
        ["You choose <b>Log Out</b> in the desktop's own menu",
         "This is the way to say “I am done”. The desktop and all its programs are closed, and the page goes back to "
         "the sign-in form with the line " + ui("the session has ended: the programs were closed") + ". On XFCE, "
         "a Log Out chosen in the first seconds, while the desktop is still starting, may be ignored: choose it "
         "again."],
        ["You sign in from a second device while the first is still connected",
         "The second one is refused with “this session's slot shows as taken by another client”. Close the tab on "
         "the first device, or, if the first simply dropped, wait up to about half a minute and try again (see "
         + rif("When something does not work") + ")."],
        ["The administrator stops, restarts or upgrades the service",
         "The page says " + ui("the server is shutting down") + ". Every desktop is closed with its programs, as at "
         "a shutdown of the machine: unsaved work is lost. When the service is running again, sign in: you get a "
         "new, empty desktop."],
        ["The machine is restarted or switched off",
         "The page says " + ui("the server is shutting down") + " (when it is shut down in the normal way; after a power cut "
         "the page only says " + ui("the connection to the server was interrupted: to get back in, type your password "
         "again") + "). All the desktops and their programs end: unsaved work is lost. Nothing survives a restart "
         "of the machine itself."],
        ["Somebody signs in at the machine's screen with your user name",
         "Your remote desktop is closed at once, with all its programs: unsaved work is lost. The page says "
         + ui("the local session on that machine took precedence") + ". While that person is signed in at the "
         "machine you cannot sign in from the browser (the page says " + ui("that user is already signed in locally")
         + "); after they sign out you can, and you get a new desktop. This was tried at the real login screens of "
         "<b>Ubuntu</b> (GDM) and <b>Kubuntu</b> (SDDM), from live systems: the local login waited, your desktop was "
         "closed and the local login went on (about a second on GNOME; on KDE the person at the machine waited "
         "about eleven seconds). At the login screens of Xubuntu (LightDM) and Lubuntu (SDDM) it was <b>not tried</b>."],
    ], "«TAB» — Leaving and coming back") + \
    warn("only your own input — keys, mouse, touch — counts as touching the desktop. A desktop left for an hour "
         "without any input is closed even if a video is playing in it.", "The one-hour clock.")

S_TOUCH = p("On a phone or a tablet, REMOTIX works like on a PC if you have a mouse: connect, sign in, use the "
            "desktop. If you only have your finger, the page switches by itself to a <b>touch layout</b>. You do not "
            "choose it: the page looks at what you use. A touch screen used with the finger gets the touch layout; "
            "as soon as you use a mouse or a pen it goes back to the normal one, and a finger touch brings the touch "
            "layout back.", lead=True) + \
    p("In the touch layout your finger does not point at the desktop directly: it works like the trackpad of a "
      "laptop. The pointer is drawn by the page and moves when you drag; a tap clicks <i>where the pointer is</i>, "
      "not where your finger lands.") + \
    table(["With your fingers", "What happens"], [
        ["Drag with one finger", "Moves the pointer."],
        ["Tap with one finger", "Left click, where the pointer is."],
        ["Tap with two fingers", "Right click."],
        ["Tap with three fingers", "Middle click."],
        ["Drag with two fingers", "Scrolls (the content follows your fingers)."],
        ["Tap, then touch again within a third of a second, close to where you tapped, and drag",
         "Holds the left button down while you drag: moves a window or selects text. The button is released when "
         "you lift the finger."],
        ["Pinch (two fingers apart or together)",
         "Enlarges your <i>view</i> of the picture, up to four times; it does not change the desktop and the "
         "enlarged picture looks soft. Pinch back to return."],
        ["Four or more fingers", "Nothing: no gesture is defined."],
        ["The small ⌨ button, top right", "Opens the on-screen keyboard; touch it again, or press “back”, to close it. "
                                          "The keyboard never opens by itself."],
    ], "«TAB» — The gestures of the touch layout") + \
    ul([
        "<b>What you type</b> with the on-screen keyboard reaches the desktop as letters (corrections included); "
        "Enter and Delete as keys.",
        "<b>Rotating the device</b> does not rotate the desktop: it shows bands and the picture is scaled to fit. "
        "To get a desktop of the new shape, close the tab and sign in again.",
        "A phone held upright gives a tall, narrow desktop, which is odd for a desktop: a tablet, or a phone with a "
        "mouse and keyboard, is more comfortable.",
    ]) + \
    note("the touch layout has been exercised on a simulated phone, and the gestures were <b>not tried one by one on "
         "a real phone</b> on Ubuntu. What was tried by hand on Ubuntu 26.04, on all four desktops, from an Android "
         "phone and a tablet: signing in, working, and leaving and coming back. On GNOME the desktop starts in the "
         "Overview, which holds touches, and the first tap after signing in may land in the wrong place: touch "
         "again. (It was seen once in thirteen tries on Debian 13 and not measured again on Ubuntu.)",
         "Not yet verified gesture by gesture on a real phone.")

S_DEX = p("<b>Samsung DeX</b> (a phone or tablet connected to a screen, with a mouse and keyboard) is used as a PC: "
          "the page sees a mouse and uses the normal layout. Chrome on Android is the browser. On "
          "Ubuntu 26.04 it was tried by hand once, on GNOME, in a first test environment (a container, not a virtual "
          "machine), and it worked; it was <b>not repeated</b> on the virtual machines nor on the other three "
          "desktops.", lead=True) + \
    ul([
        "<b>No hover on the desktop.</b> On Samsung devices Chrome does not report mouse movement while no button "
        "is pressed. Pointing, clicking and dragging land exactly where they should, but you do not see what "
        "needs hovering: buttons that light up, tooltips, the pointer changing shape at the edge of a window.",
        "<b>Combinations with the Super key never reach the desktop</b>: Android keeps them.",
        "Whether the browser can keep other combinations for the page on DeX is <b>not yet verified</b>.",
    ])

CHAPTER = ("Connecting and using it", [
    ("Signing in", S_SIGNIN),
    ("The desktop in the browser", S_DESKTOP),
    ("The keyboard", S_KEYS),
    ("Copy and paste", S_CLIP),
    ("Leaving and coming back", S_LEAVE),
    ("On a phone or a tablet", S_TOUCH),
    ("Samsung DeX", S_DEX),
])
