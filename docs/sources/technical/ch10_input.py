from build import (arrow, box, c, fig, key, note, p, path, rif, seq, steps, table, ul, warn, zone)

S1 = p("Input travels the opposite way to video: from the browser page to the desktop of the remote "
       "session. The page turns mouse, keyboard and fingers into five RCP messages on a single "
       "unidirectional stream; the parent process validates them and passes them to the per-user child; "
       "the child injects them into the compositor through " + c("libei") + " (GNOME and KDE) or through "
       "the Wayland virtual keyboard and pointer protocols (labwc, that is XFCE and LXQt).", lead=True) + \
    fig(
        zone(20, 12, 200, 236, "Browser page")
        + zone(240, 12, 190, 236, "Server parent")
        + zone(450, 12, 430, 236, "Per-user child")
        + box(36, 44, 168, 52, "Classic layout", "mouse + real keyboard", "navy")
        + box(36, 112, 168, 52, "Touch layout", "seven gestures", "navy")
        + box(36, 180, 168, 52, "REMOTIX_INPUT", "one id counter", "blue")
        + box(256, 112, 158, 52, "rcp.c", "decode + validate", "blue")
        + box(466, 44, 190, 52, "input.c", "count + release", "blue")
        + box(466, 112, 190, 52, "tastiera.c", "keyboard: letter to keys", "light")
        + box(674, 44, 190, 52, "libei", "Mutter / KWin", "dark")
        + box(674, 112, 190, 52, "wlr_input.c", "labwc virtual devices", "dark")
        + box(674, 180, 190, 52, "Compositor", "GNOME, KDE, XFCE, LXQt", "green")
        + path([(36, 70), (28, 70), (28, 206), (34, 206)])
        + arrow(120, 166, 120, 178)
        + arrow(206, 206, 254, 140, label="input stream", lx=232, ly=190)
        + arrow(416, 138, 464, 70, label="socket", lx=440, ly=96)
        + arrow(560, 98, 560, 110)
        + arrow(658, 70, 672, 70) + arrow(658, 70, 672, 132)
        + path([(864, 70), (874, 70), (874, 206), (866, 206)])
        + arrow(769, 166, 769, 178),
        900, 262, "«FIG» — The path of an input event, from a finger or a key to the remote desktop") + \
    table(["Rule", "What it means", "Why"], [
        ["The pointer is drawn by the client", "The remote cursor never travels inside the video; the page "
         "shows the pointer itself and sends <b>absolute</b> positions on the canvas",
         "Perceived latency: the arrow moves at the speed of the hand, not of the network"],
        ["Letters travel as letters", "Text is sent as Unicode code points (" + c("LETTERA") + ", letter)",
         "A client with a US keyboard attached to an Italian session would otherwise type the wrong letters"],
        ["Other keys travel as positions", "Enter, Tab, arrows, F1–F12 and every key pressed together with "
         "Ctrl, Alt or Super travel as evdev key codes (" + c("POSIZIONE_TASTO") + ", key position)",
         c("Ctrl+C") + " is a command, not a letter; shortcuts must match key positions"],
        ["What cannot be typed is declared", "A character that no key of the session layout produces is "
         "not sent, and the server writes it in the log", "Never a different letter, never silence"],
        ["Everything pressed is released", "Every key and button pressed is counted, and released when the "
         "client detaches, the page loses focus or the canvas changes size",
         "A Ctrl left down in a session that outlives the client makes the desktop unusable at reattach"],
    ], "«TAB» — The rules that shape input") + \
    table(["Desktop", "Compositor", "Transport", "Wheel", "Layout applied through"], [
        ["GNOME", "Mutter", c("libei") + " on the descriptor of " + c("ConnectToEIS"),
         c("ei_device_scroll_delta") + ", 120 units = 10.0", c("org.gnome.desktop.input-sources") + " in the session dconf"],
        ["KDE Plasma", "KWin", c("libei") + " on the descriptor of " + c("connectToEIS"),
         c("ei_device_scroll_discrete") + ", 120 units", c("kxkbrc") + " in the session configuration directory"],
        ["XFCE, LXQt", "labwc (wlroots)", c("zwp_virtual_keyboard_v1") + " + " + c("zwlr_virtual_pointer_v1"),
         "whole notches, " + c("axis_discrete"), "the keymap of our own virtual keyboard"],
    ], "«TAB» — The three injection paths")

S2 = p("Input uses five message types on the input channel, all big-endian, defined in RCP §7.3 and "
       "decoded by " + c("rcp_ricevi_input()") + " (receive input). The client opens exactly one unidirectional stream for "
       "them, after " + c("SESSIONE") + " (session), and keeps it open; a second input stream is a protocol error.",
       lead=True) + \
    table(["Type", "Name", "Fields after the common header", "Notes"], [
        [c("0x0101"), c("PUNTATORE") + " (pointer)", c("u32 x · u32 y"), "Absolute pixel index on the canvas (not on the view): "
         + c("0 ≤ x < canvas width") + ". The page rounds down and saturates."],
        [c("0x0102"), c("PULSANTE") + " (button)", c("u16 code · u8 pressed"), "evdev button code: " + c("BTN_LEFT")
         + " = " + c("0x110") + ", right " + c("0x111") + ", middle " + c("0x112")],
        [c("0x0103"), c("ROTELLA") + " (wheel)", c("i32 axis_x · i32 axis_y"), "120 units per notch; 60 is half a notch and "
         "must not be rounded to zero. The client sends +120 when the wheel turns <b>up</b>"],
        [c("0x0104"), c("LETTERA"), c("u32 character"), "Unicode scalar value, 0–0x10FFFF without surrogates"],
        [c("0x0105"), c("POSIZIONE_TASTO"), c("u16 code · u8 pressed"), "evdev key code, e.g. " + c("KEY_A")
         + " = 30"],
    ], "«TAB» — The input messages (RCP §7.3)") + \
    p("Every message starts with the same two fields: " + c("u32 id") + " and " + c("u64 istante") + " (instant, a timestamp). The "
      + c("id") + " grows by at least one on <b>every</b> message of the channel, whatever its type, and never "
      "takes the value 0, which means “no input”. It is the number that comes back in the "
      + c("input") + " field of every video frame header (RCP §6.2): the child sets that field to the last id "
      "<b>injected</b> before the capture, not the last received, so a message refused by the compositor or "
      "a letter the layout cannot produce never claims an effect that the frame does not show. The "
      + c("istante") + " is the client's monotonic clock in microseconds; no rule consumes it, it is kept "
      "for diagnosis.") + \
    p("Codes are those of evdev (" + "the kernel header <i>linux/input-event-codes.h</i>" + ") because " + c("libei") + " and "
      "the Wayland virtual devices both speak evdev: any other convention would add a translation table "
      "that fails silently. Coordinates outside the canvas close the session with " + c("ERRORE_PROTOCOLLO")
      + ", except during the one-second grace after a " + c("TELA(ADATTATA)") + " reply (canvas adapted), where they are saturated "
      "(RCP §7.1); the page saturates them anyway, three times over, because a closed session for a "
      "rounding error is the worst possible answer.") + \
    p("Two control-channel messages belong to input as well: the keyboard layout declared in "
      + c("ATTACCA") + " (attach, RCP §4.5) and " + c("DISPOSIZIONE") + " (layout, " + c("0x0009") + "), which changes "
      "it while the session is open (" + rif("Keyboard layout negotiation") + ").") + \
    note("the page writes " + c("istante") + " as " + c("Math.round(ms) * 1000") + " (" + c("cl_istante_us()")
         + ", " + c("tocco_istante_us()") + "), that is whole milliseconds. RCP §7.3 was corrected on "
         "14 Aug 2026 to say that the client should write the real microseconds it has (5 µs grain on an "
         "isolated page in Chrome 151); the page code still rounds.", "Clock grain.")

S3 = p("The page has two input layouts and chooses between them by itself, from what the device "
       "<b>has</b> and what the user <b>is using</b>, never from the user-agent string: DeX is Android "
       "with a real mouse, a laptop is Linux with a touch screen.", lead=True) + \
    table(["Evidence (strongest first)", "Layout", "Notes"], [
        [c("?disposizione=tocco") + " or " + c("?disposizione=classico") + " (touch or classic layout) in the query or hash",
         "forced", "Service path for benches and diagnosis, declared in the page log; not a user setting"],
        ["Last " + c("pointerdown") + " had " + c("pointerType") + " " + c("mouse") + " or " + c("pen"),
         "classic", "The only proof that the user is using that device <b>now</b>"],
        ["Last " + c("pointerdown") + " had " + c("pointerType") + " " + c("touch"), "touch", ""],
        [c("(any-pointer: fine)"), "classic", "A fine pointer is attached"],
        [c("(pointer: coarse)") + " and no fine pointer", "touch", "Only a finger"],
        [c("matchMedia") + " does not answer", "by width", "800 CSS px or more: classic (" + c("TOCCO_LARGHEZZA_CLASSICO") + ")"],
    ], "«TAB» — How " + c("disposizione_dal_contesto()") + " (layout from context) picks the layout") + \
    p("A change of any media query discards the last observation and the context decides again: pick up "
      "the mouse and the page goes classic, touch the screen and it goes back to touch. The layout in force "
      "is written in " + c("body[data-disposizione]") + " so that benches read it from the document. "
      "Leaving the touch layout resets the pinch zoom (with the mouse there is no panning, and part of the "
      "desktop would be unreachable: measured on DeX on 14 Aug 2026) and releases the button held by a "
      "tap-and-a-half; leaving the classic layout releases every key and button it pressed.") + \
    p("Both layouts send through the same interface, " + c("window.REMOTIX_INPUT") + " (" + c("prossimo_id()")
      + ", next id; " + c("manda()") + ", send), created right after " + c("SESSIONE") + " together with the input stream, "
      "with a single writer so that messages leave in the order the user produced them. If the stream cannot be opened "
      "the session continues view-only, and the page says so. When the stream is congested ("
      + c("desiredSize") + " at or below zero) a " + c("PUNTATORE") + " is not queued: it is held aside and "
      "replaced by the next one, and the held position is always flushed before any key or button, so a "
      "click never travels with an old position. Measured from DeX on 14 Aug 2026: median input-to-frame "
      "loop 135 ms but worst case 2161 ms, which was a queue of stale pointer moves in front of a keystroke.")

S4 = p("In the classic layout (" + c("cl_*") + " functions, for “classic”, in " + c("pagina.html") + ") the mouse is the "
       "primary path, including on DeX, which is the main Android use.", lead=True) + \
    table(["Topic", "What the page does", "Why"], [
        ["Events", "Moves and clicks come from " + c("pointermove") + ", " + c("pointerdown") + " and "
         + c("pointerup") + " (with " + c("touch-action: none") + "); " + c("mouse*") + " events only where "
         + c("PointerEvent") + " does not exist",
         "On Android " + c("mouse*") + " are compatibility events: Chrome suspends the move flow on DeX and "
         "creates " + c("mousedown") + " only after a recognised tap (measured 14 Aug and 2 Oct 2026). "
         "Listening to both sent 184 of 219 moves twice."],
        ["A click carries its position", "Before " + c("PULSANTE") + " the page sends " + c("PUNTATORE")
         + " for the point of the click, unless it is less than one CSS pixel from the last move",
         c("PULSANTE") + " has no coordinates; on Samsung Chrome moves with buttons up are not delivered "
         "(noVNC #1727), so the server pointer stays where the last drag left it. The sub-pixel rule avoids "
         "Chrome's integer " + c("clientX") + " pushing the click into the neighbouring pixel (24 Sep 2026)."],
        ["A release carries its position", "Same rule on " + c("pointerup"), "Chrome can deliver "
         + c("pointerup") + " at a point no move reported: a drag selected one letter less (3 Oct 2026)"],
        ["Coordinates", "Kept in floating point on the canvas, saturated, rounded down only when sent, and "
         "not sent if the pixel did not change", "Moving the mouse very slowly must still move something"],
        ["Second button", "Chorded buttons arrive as " + c("pointermove") + " with " + c("button") + " ≠ −1 and are "
         "turned into press or release", "W3C Pointer Events"],
        ["Unknown button", c("MouseEvent.button") + " outside 0–4 is declared and not sent", "Inventing a code would "
         "press another button on the user's desktop"],
        [c("pointercancel"), "Every button still pressed is released", "The browser took the pointer back"],
        ["Context menu", c("contextmenu") + " is prevented while the layout is usable", "Otherwise the right "
         "button never reaches the remote desktop"],
        ["Login form", "Nothing is captured until the canvas is lit and while focus is in a form field "
         "(the hidden paste field " + c("#incolla-nascosto") + ", “hidden paste”, is the single named exception)",
         "Otherwise the user could not type the password"],
    ], "«TAB» — The mouse in the classic layout") + \
    p("<b>One visible pointer.</b> The page has three pointer modes (" + c("REMOTIX_PUNTATORE.modo()") + "): "
      + c("sistema") + " (system; the default since 14 Aug 2026), where the browser's own cursor takes the "
      "remote cursor shape through a CSS " + c("cursor: url(...) x y, default") + " rule, the way Xpra does; "
      + c("disegnata") + " (drawn), where the browser cursor is hidden and the page draws its arrow; and "
      + c("due") + " (two), both arrows overlaid, kept for comparison. In the touch layout the drawn arrow stays, because a finger has no cursor to restyle. "
      "A zero-by-zero shape (RCP §5.5) means “hidden” and is applied in both modes. The cursor "
      "shape itself comes from the capture (" + rif("Screen capture per compositor") + ").") + \
    p("<b>Pointer Lock only where hover is missing.</b> The lock is requested at the first click (the gesture "
      "it requires) only if, before that click, no move with buttons up arrived, or the last one is "
      + c("CL_SALTO_PX") + " (jump threshold) = 8 px or more from the click point. On a computer the last move falls on the "
      "click and the lock never fires; on DeX moves with buttons up arrive only around clicks, and with the "
      "lock the borders of windows can be grabbed (user test, S23, Android 16, Chrome 154, 3 Oct 2026). "
      "The lock asks for " + c("unadjustedMovement") + " (the client applies acceleration, "
      + c("CL_GUADAGNO") + ", the gain, = 1.0); the first movement after the lock is dropped if longer than 100 CSS px "
      "(Chrome reports the jump of the system cursor); pushing 160 CSS px beyond an edge releases the lock, "
      "so that the DeX bar and the browser tabs stay reachable, while a pointer resting on the edge still "
      "triggers GNOME's hot corner.") + \
    warn("on Samsung devices (DeX included) Chrome does not deliver mouse moves with buttons up "
         "(noVNC #1727, open since 2022; the same on moonlight-android #573, a native app). Pointing, "
         "clicking and dragging land correctly; what is missing is the preview: the resize arrow on window "
         "borders, buttons lighting up, tooltips. The automatic Pointer Lock above reduces it.",
         "A limit that is not ours.") + \
    note(c("SPECIFICHE.md") + " §7.4 and a comment in " + c("cl_su_mousedown()") + " still say that the lock is "
         "only manual through " + c("REMOTIX.input_classico.aggancia()") + ". The code requests it "
         "automatically (" + c("cl_hover_manca()") + ", “hover missing”) and " + c("REMOTIX.input_classico") + " exposes "
         "no such function.", "Documents behind the code.")

S5 = p("The wheel has one sign convention on the wire and three on the way out; the sign is inverted "
       "exactly twice, once in the page and once in the server, and nowhere else.", lead=True) + \
    table(["Step", "What happens", "Source of the number"], [
        ["Browser", c("deltaY > 0") + " means the content goes towards the end, i.e. the wheel turned down. "
         + c("deltaMode") + " 0: 100 px per notch; 1 (lines): 3 lines per notch; 2 (pages): 3 notches per "
         "page, declared as unmeasured", "100 px measured on Chrome 151 / Linux on 14 Aug 2026 against the "
         "legacy " + c("wheelDelta") + ", which rounds half notches up and was dropped"],
        ["Page", "Accumulates in units of 1/120 and sends whole units; sends " + c("−uy") + " so that a wheel "
         "turned up is +120", "RCP §7.3"],
        ["Touch", "Two-finger drag: 40 CSS px = one notch, sent in multiples of 60 with the rest kept",
         c("TOCCO_SOGLIE.PX_PER_SCATTO") + " (touch thresholds, pixels per notch), not measured"],
        ["Server, GNOME", c("ei_device_scroll_delta(x/12, −y/12)") + ": Mutter turns 10.0 into "
         + c("v120") + " 120 and emits a notch when its accumulator passes 60",
         c("UNITA_PER_DELTA") + " = 12. " + c("ei_device_scroll_discrete") + " was dropped: Mutter divides "
         "it by 120 with integer division and half notches vanish"],
        ["Server, KDE", c("ei_device_scroll_discrete(x, −y)") + " in 120 units", "On KWin "
         + c("scroll_delta") + " produces no notch"],
        ["Server, labwc", c("wlr_input_rotella()") + " (wheel): accumulator per axis, one notch at ±60, "
         + c("axis_discrete") + " with whole notches and value 15.0 per notch, source " + c("WHEEL"),
         "15.0 is the libinput step that wayvnc uses; a zero value would make wlroots send "
         + c("axis_stop")],
    ], "«TAB» — The wheel from the hand to the compositor") + \
    p("The sign was measured on 10 Aug 2026 on Mutter (libmutter 48.7, libei 1.3.901, Firefox 140): "
      + c("ei_device_scroll_discrete(0, +120)") + " scrolled the page 114 px towards its end. Hence the "
      "server inversion. The horizontal axis of the touch gesture mirrors the vertical one and has not been "
      "judged. The wheel event also carries a position, and the page sends it first, for the same reason as "
      "a click.")

S6 = p("The keyboard sends letters when the user writes text and positions when the user gives a command. "
       + c("cl_comando()") + " (is it a command?) decides: a key is a command when Ctrl, Meta or Alt (without AltGr) is down.",
       lead=True) + \
    table(["Key", "What leaves the page"], [
        ["A key that produces one character, no command modifier", c("LETTERA") + " with the code point of "
         + c("KeyboardEvent.key")],
        ["Shift, CapsLock, AltGr alone", "Nothing: they help make the letter, which already arrives made"],
        ["Enter, Tab, Escape, arrows, F-keys, Home/End, Page keys, Delete, Backspace",
         c("POSIZIONE_TASTO") + " press and release with the evdev code of " + c("KeyboardEvent.code")],
        [key("Ctrl", "C") + " and any combination with Ctrl, Alt, Super", "Positions: 29 down, 46 down, 46 up, "
         "29 up"],
        ["Key repeat", "Not forwarded: the remote desktop repeats, since the key is down there"],
        ["IME composition, dead keys (" + c("keyCode") + " 229, " + c("Dead") + ")", "Nothing, declared once "
         "in the page log. Not settled yet: composed characters need an editable focused element, which "
         "would break the canvas drawing path"],
        ["A " + c("code") + " missing from " + c("CL_POSIZIONE"), "Nothing, declared: a guessed code would "
         "press another key"],
    ], "«TAB» — From a browser key to an RCP message") + \
    p("The table " + c("CL_POSIZIONE") + " maps " + c("KeyboardEvent.code") + " to evdev by hand from the "
      "kernel table; positions are physical, so " + c("KeyZ") + " is the key where Z sits on a US board, "
      "which writes Y on a German one. That is exactly why shortcuts travel as positions.") + \
    p("<b>Modifier resynchronisation.</b> Because Shift alone is not sent, the page sends it at the moment "
      "a position key arrives while " + c("getModifierState(\"Shift\")") + " (or AltGr) is true but the page "
      "has not pressed it. Since 24 Sep 2026 this happens for every position key, not only for commands: "
      "before, " + key("Shift", "←") + " arrived as a bare arrow and did not select text on any of the four "
      "desktops. Conversely, before a " + c("LETTERA") + " the page releases the Shift or AltGr it holds, "
      "because the server presses and releases its own Shift to produce the letter and on labwc that release "
      "would leave the page and the server disagreeing.") + \
    p("<b>Ctrl+V is the one command the page does not cancel.</b> Calling " + c("preventDefault()") + " on it "
      "would stop the browser paste, and with it the " + c("paste") + " event that is the only free way to read "
      "the local clipboard on Firefox; the canvas is not editable, so the browser paste writes nowhere. When "
      "the clipboard is on, the V is also held back until the page has read the local clipboard and announced "
      "it, at most " + c("INCOLLA_TRATTIENI_MS") + " (paste hold time) = 400 ms, with every key typed meanwhile queued behind it "
      "(" + rif("Clipboard in the browser") + ").") + \
    p("<b>Release on focus loss.</b> On " + c("blur") + ", on " + c("visibilitychange") + " to hidden and on "
      + c("pagehide") + " the page releases every key and button it pressed (" + c("cl_rilascia_tutto()") + ", release all"
      + "). The Keyboard Lock switches itself off precisely when the page loses focus, which is when a "
      "modifier is likely to be held; the session does not detach in that case, so the server-side release at "
      "detach would not help.") + \
    note("by decision of 26 Sep 2026 (" + c("DECISIONI.md") + " §9.2) the log never contains what the user types: neither "
         "characters nor key codes. Lines say “a character” or “key pressed”; codes are "
         "written only for modifiers and mouse buttons (on the server, " + c("registro_tasto_dicibile()")
         + " in " + c("registro.c") + ": whether a key code may be named in the log). It applies to "
         "unproducible characters too: the log says that one occurred, not which.", "Privacy of keystrokes.")

S7 = p("Some combinations never reach the page, and some reach it while the browser also runs its own "
       "command. The page declares them per engine and per screen state instead of pretending they work.",
       lead=True) + \
    table(["State", "Meaning"], [
        ["delivered", "Reaches the remote session, and nothing else happens"],
        ["delivered and reserved", "Reaches the session <b>and</b> the browser runs its command; "
         + c("preventDefault()") + " turns it off (measured 14 Aug 2026: 18 of 42 combinations in a Chrome "
         "window, 18 → 0 with it; 15 → 0 on Firefox). The worst state, because a bench that looks only at the "
         "session marks it green"],
        ["not delivered", "The browser or the client's compositor keeps it"],
    ], "«TAB» — The three states of a shortcut") + \
    p("The catalogue " + c("SC_CATALOGO") + " holds, per engine family (" + c("blink") + ", " + c("blink-app")
      + " for an installed app, " + c("gecko") + ") and per screen state (" + c("finestra") + " window, "
      + c("intero") + " full screen, " + c("intero+lock") + " full screen with Keyboard Lock, " + c("F11") + "), what is lost; it was measured on 14 Aug "
      "2026 on GNOME/Wayland by injecting from a real keyboard path (" + c("org.gnome.Mutter.RemoteDesktop")
      + "), with Chrome 151 and Firefox 140 ESR. Safari, Chrome on Android/DeX and Firefox 151 or later are "
      "listed as not tested (" + c("SC_NON_PROVATI") + "), and an untested engine is never deduced from the "
      "others.") + \
    table(["Topic", "Behaviour"], [
        ["Keyboard Lock, two forms", "The page tries first the WHATWG form "
         + c("requestFullscreen({keyboardLock: \"browser\"})") + " (detecting whether the option was read at "
         "all), then " + c("navigator.keyboard.lock()") + " (Chrome, Edge)"],
        ["Full screen entered with F11", "Recognised from geometry; the lock does not exist there and the "
         "browser does not say so, so the page declares it"],
        ["Focus lost", "The lock dies silently; the page marks it dead and buys it back on " + c("focus")
         + " with the old form (the new form needs leaving and re-entering full screen, which is not done "
         "behind the user's back)"],
        ["Measured on Chrome 151", "Full screen with the lock: browser-reserved shortcuts go from 8 to 0, "
         "only " + key("F11") + " and " + key("Esc") + " remain. In an installed app window they are 0 "
         "already"],
        ["Measured on Firefox 140 ESR", "No form of the lock; full screen makes it worse (5 → 7)"],
        ["Android and DeX", "Every combination with Meta is kept by the system (AOSP rule)"],
    ], "«TAB» — Keyboard Lock and its traps") + \
    p("<b>On-screen buttons.</b> " + c("SC_BOTTONI") + " (buttons) lists five combinations that no browser lets "
      "through; only " + key("Ctrl", "Alt", "Del") + " is active (user decision, 14 Aug 2026), because "
      "without it a locked session cannot be entered at all. It is sent as positions 29, 56, 111 down and up "
      "in reverse. " + key("Ctrl", "W") + ", " + key("Ctrl", "T") + ", " + key("Alt", "F4") + " and "
      + key("Super") + " are present but off: switching one on is " + c("attivo: true") + " (active).")

S8 = p("The touch layout turns the phone screen into a trackpad: the finger pushes a pointer drawn by the "
       "page, and clicks happen where the pointer is, not where the finger lands.", lead=True) + \
    table(["Gesture", "Effect on the wire"], [
        ["One finger drags", c("PUNTATORE") + " (relative movement, gain 1.0)"],
        ["One finger tap", "Left press + release"],
        ["Two fingers tap", "Right press + release"],
        ["Three fingers tap", "Middle press + release"],
        ["Two fingers drag", c("ROTELLA")],
        ["Tap-and-a-half (tap, then press and drag)", "Left pressed at the second contact, released when it lifts"],
        ["Pinch", "Nothing: it zooms the page <b>view</b> with a CSS transform, up to 4×"],
        ["Four fingers", "Nothing, declared"],
    ], "«TAB» — The gestures (" + c("SPECIFICHE.md") + " §7.2)") + \
    table(["Threshold", "Value", "Provenance"], [
        [c("T_TAP"), "180 ms per contact", "Android " + c("TAP_TIMEOUT") + " and the libinput default"],
        [c("D_TAP"), "9 CSS px", "Android touch slop, 8 dp"],
        [c("T_SEQUENZA") + " (sequence)", "300 ms", "Android " + c("DOUBLE_TAP_TIMEOUT")],
        [c("D_STESSO_DITO") + " (same finger)", "40 CSS px ≈ 10 mm", "The width of a finger, the same figure that motivates the drawn pointer"],
        [c("D_PIZZICO") + " (pinch)", "24 CSS px", "Assumed, not measured"],
        [c("PX_PER_SCATTO") + " (pixels per notch)", "40 CSS px", "Assumed, not measured"],
        [c("ZOOM_MAX"), "4.0", ""],
    ], "«TAB» — " + c("TOCCO_SOGLIE") + ", in CSS pixels because a finger is ten millimetres wide on any screen") + \
    p("The thresholds are a declared starting point, judged by using them. Four design points are not "
      "thresholds, and each came from a failing bench run (" + c("04-b28-gesti.py") + ", gestures, 14 Aug 2026):") + \
    ul([
        "<b>Tap-and-a-half and double click are the same gesture.</b> At the second contact the two have "
        "produced the same events, so the button is pressed at contact and released at lift: a quick lift is "
        "the second click of a double click, a drag is a drag. Waiting to decide would delay every double "
        "click.",
        "<b>Two fingers make a two-finger gesture if they are down together for at least one sample.</b> "
        "Two non-overlapping taps are two one-finger taps, so a badly timed right click comes out as a left "
        "double click; the only cure would delay every click by 300 ms, above the 50 ms budget.",
        "<b>A tap is short if every contact is short</b>, not the whole gesture: three fingers never land and "
        "lift together.",
        "<b>When the set of fingers changes, the two-finger reference is rebuilt</b> and nothing is decided "
        "in that sample: three fingers lifting one by one move the centre by tens of pixels without any "
        "movement, which used to be read as a wheel.",
    ]) + \
    p("Wheel and pinch are both “two moving fingers”: the page compares the change of distance "
      "with the movement of the centre, takes the larger once, and keeps that decision for the whole gesture. "
      "The pointer is moved on every touch sample, without coalescing and without "
      + c("requestAnimationFrame") + " (which never ran on the Xvfb bench). Times come from "
      + c("event.timeStamp") + " when plausible (within 5 s of " + c("performance.now()") + "), otherwise "
      "from the handler time, declared.")

S9 = p("With the phone in hand the system keyboard opens only on request (" + c("DECISIONI.md") + " §10.28, 2 Oct 2026), "
       "through a small " + c("⌨") + " button at the top right that exists only in the touch layout.",
       lead=True) + \
    steps([
        "<b>Why.</b> The hidden paste field is always focused, and on Android a focused text field opens "
        "the keyboard, which covered half the desktop for 60 % of a test and typed nothing (measured on an "
        "S23+ with Chrome 154).",
        "<b>The field.</b> In the touch layout it carries " + c("inputmode=\"none\"") + " and "
        + c("virtualkeyboardpolicy=\"manual\"") + " (and no autocapitalisation or autocorrection); in the "
        "classic layout none of these attributes is present, so paste and keys are unchanged.",
        "<b>The button.</b> " + c("tastiera_commuta()") + " (toggle keyboard) switches " + c("inputmode") + " to "
        + c("text") + ", re-focuses the field inside the user's touch, and calls "
        + c("navigator.virtualKeyboard.show()") + " where it exists. The button never takes focus. It sits at "
        "the top because the open keyboard covers the bottom.",
        "<b>What is typed.</b> " + c("tastiera_su_input()") + " compares the field with what was already sent: "
        "the common prefix stays, every vanished character becomes Backspace (position 14), every new one a "
        + c("LETTERA") + "; newline and tab become Enter and Tab positions. Autocorrection works by rewriting "
        "the word. Outside composition the field is emptied.",
        "<b>Real keys</b> (Enter and Backspace on an empty field, a Bluetooth keyboard without a mouse) are "
        "handled in " + c("tastiera_su_keydown()") + "; if " + c("code") + " is empty, as can happen on "
        "Android, the key name is used.",
        "<b>Closing.</b> The button again, or Android's back gesture, recognised when the visual viewport grows "
        "back above 85 % of the window height.",
    ])

S10 = p(c("tastiera.c") + " (keyboard) solves the reverse problem of a keyboard: given a character, which keys must be "
        "pressed on the session's layout to make the compositor produce it. It works on the keymap the "
        "session itself handed over, compiled with xkbcommon.", lead=True) + \
    table(["Rule", "How", "Why"], [
        ["Scan every key and level", "For each keycode and each shift level, compare "
         + c("xkb_keysym_to_utf32(sym)") + " with the character",
         "The same character has a legacy and a Unicode keysym; comparing characters covers both"],
        ["Modifiers come from the layout", c("xkb_keymap_key_get_mods_for_level()") + " gives the masks; "
         "which key turns on which modifier is learned by pressing every key on an " + c("xkb_state"),
         "v1 assumed level 1 = Shift, level 2 = AltGr; on " + c("de(neo)") + " the level-3 key is 43, not 100"],
        ["Locks are never used", "Masks that need CapsLock or NumLock are discarded",
         "A lock changes the session for the next letters"],
        ["Shortest path wins", "Fewest modifiers, then the lowest keycode", "Keeps the keypad away from digits"],
        ["At most four positions", c("TASTIERA_MAX_POSIZIONI") + " = 4", "Worst case measured: three ("
         + c("√") + " on " + c("de(neo)") + " is 100 + 43 + 17, 14 Aug 2026)"],
        ["Only the first group", "A keymap with several layouts uses the first, declared", ""],
    ], "«TAB» — How a letter becomes key positions") + \
    p(c("input_lettera()") + " (input a letter) presses the modifiers first and the key last, releases in reverse order, and "
      "if a press fails halfway it releases what it already pressed. It returns 0 when sent, 1 when the "
      "character is not producible (the log line is written by " + c("tastiera_posizioni_per()") + ", positions for a character, which "
      "knows the layout name), −1 on a fault; values outside the Unicode scalar range are protocol errors, "
      "not “unproducible”. xkbcommon's own log is redirected so that a layout that does not compile "
      "says why, and the layout name always includes what the compiled keymap calls itself (“it [Italian]”), "
      "so a silent fallback would read “it [English (US)]”.")

S11 = p("The layout is negotiated at every attach, like the canvas, for two reasons: to make characters "
        "reachable and to make shortcut positions match. The client proposes, the server asks the session, "
        "and the session's real keymap is always the one in force.", lead=True) + \
    steps([
        "<b>The page proposes</b> a layout in " + c("ATTACCA") + " from " + c("navigator.language")
        + " (" + c("disposizione()") + ", layout): " + c("en") + " becomes " + c("us") + " (or " + c("gb") + "/"
        + c("ie") + " by region), " + c("sv") + " → " + c("se") + ", " + c("da") + " → " + c("dk") + ", "
        + c("cs") + " → " + c("cz") + ", " + c("el") + " → " + c("gr") + ", " + c("he") + " → " + c("il")
        + ", " + c("ja") + " → " + c("jp") + ", " + c("ko") + " → " + c("kr") + ", " + c("uk") + " → "
        + c("ua") + ", thirty languages whose XKB name equals the ISO code pass unchanged, everything else "
        "becomes " + c("us") + ". Until 10 Aug 2026 the page sent " + c("en") + ", which is not an XKB name, "
        "and the server rightly refused the session of every English-language browser.",
        "<b>The server checks the form</b> (" + c("disposizione_ben_formata()") + ", well-formed layout): at most 64 "
        "characters in all, a name of " + c("[A-Za-z0-9_-]") + " optionally followed by a non-empty variant of the "
        "same characters in parentheses. Dots, slashes and commas are "
        "refused because the string ends up in XKB's include machinery, which opens files by name. A bad form "
        "is " + c("ERRORE_PROTOCOLLO") + ".",
        "<b>The server checks existence</b> by compiling it with xkbcommon (" + c("gancio_disposizione_esiste()")
        + ", the layout-exists hook, → " + c("tastiera_apri_per()") + "). At attach an unknown layout is " + c("SESSIONE_NON_SERVIBILE")
        + " (session cannot be served); the fixed list of twenty layouts of phase 1 is only a declared fallback when the hook is "
        "missing. Until 16 Aug 2026 that list refused " + c("hu") + ", " + c("tr") + ", " + c("gr") + " and "
        + c("ua") + ", which were installed.",
        "<b>The child asks the session</b> (" + c("input_disposizione()") + "), after releasing everything "
        "pressed, unless the current keymap already does the same thing as the requested layout (compared "
        "key by key, " + c("tastiera_e_questa()") + ", “is the keyboard this one”): a needless change costs Mutter the destruction of the "
        "keyboard device.",
        "<b>The keymap confirms.</b> The compositor recreates the keyboard device with the new keymap; "
        + c("leggi_keymap()") + " reads it, fingerprints it (size plus hash, since Mutter names every keymap "
        + c("(unnamed)") + ") and writes " + c("KEYMAP CAMBIATA") + " (keymap changed). If the session layout differs from the "
        "requested one, " + c("tastiera.c") + " writes " + c("RIPIEGO DICHIARATO") + " (declared fallback) and uses the session's.",
    ]) + \
    table(["Desktop", "How the layout is applied", "Notes"], [
        ["GNOME", c("org.gnome.desktop.input-sources") + " " + c("sources") + " = "
         + c("[('xkb','de+neo')]") + ", " + c("current") + " = 0", "Written only in the <b>session</b> dconf "
         "(D-015, " + rif("GNOME sessions") + "); if that is not in force, or the schema is missing, the "
         "layout is not applied and the fallback is declared"],
        ["KDE", c("kwin_disposizione()") + " writes " + c("LayoutList[$i]") + " and " + c("VariantList[$i]")
         + " in " + c("kxkbrc") + " of the session directory, then emits " + c("org.kde.keyboard /Layouts reloadConfig")
         + " and " + c("org.kde.kconfig.notify ConfigChanged"), "KWin 6.6.6 (Ubuntu 26.04) only listens to the "
         "second; the first is kept for KWin up to 6.3. If the keymap that arrives is not the requested one, it is "
         "asked again, at most three times (measured 6 Oct 2026)"],
        ["XFCE, LXQt", c("wlr_input_keymap_da_nome()") + " (keymap from name) compiles " + c("evdev/pc105/layout/variant")
         + " and sends it as the keymap of our virtual keyboard", "No session setting is touched; labwc hands "
         "the keymap to applications with our keys. Whether labwc forwards it is not measured"],
    ], "«TAB» — Applying the negotiated layout per compositor") + \
    p("While the session is open, " + c("DISPOSIZIONE") + " (" + c("0x0009") + ") changes the layout: a "
      "well-formed unknown layout does <b>not</b> close the session (the previous keyboard still works, and "
      "“never detach” applies); the same layout as the current one asks nothing; there is no "
      "reply on the wire. The page does not send this message today.") + \
    note("a page cannot know the physical layout of the keyboard in front of it; " + c("navigator.language")
         + " is a hint. Letting the user choose is the real cure and has not been decided.", "Not settled yet:")

LIBEI_SEQ = seq(
    [("Child", "input.c", "blue"), ("libei", "client context", "dark"), ("Compositor", "Mutter or KWin", "green")],
    [
        (0, 2, "ConnectToEIS / connectToEIS → socket"),
        (0, 1, "ei_new_sender, name “remotix”, dup(fd)"),
        (2, 1, "EI_EVENT_CONNECT (handshake done)", True),
        (2, 1, "SEAT_ADDED", True),
        (1, 2, "bind POINTER, POINTER_ABSOLUTE, BUTTON, SCROLL, KEYBOARD"),
        (2, 1, "DEVICE_ADDED: absolute pointer (regions), keyboard (keymap)", True),
        (2, 1, "DEVICE_RESUMED", True),
        (0, 2, "start_emulating, then events, each followed by a frame"),
        ("sep", "geometry, keymap or capture wake-up"),
        (2, 1, "DEVICE_REMOVED + DEVICE_ADDED: a new device", True),
        ("nota", 0, "keys still down become orphans"),
    ],
    "«FIG» — Life of a libei channel, and the silent device swap")

S12 = p("On GNOME and KDE the child is a " + c("libei") + " sender on a socket that the compositor hands "
        "over: " + c("ConnectToEIS") + " on the Mutter " + c("RemoteDesktop") + " session (asked before "
        + c("Start") + ", see " + c("mutter_apri()") + ") or " + c("connectToEIS") + " on "
        + c("org.kde.KWin.EIS.RemoteDesktop") + " with the capability mask 7 (keyboard, pointer, touch) and a "
        "token.", lead=True) + LIBEI_SEQ + \
    table(["Rule", "Why"], [
        ["One thread: all of " + c("input.h") + " is called from the thread that calls " + c("input_gira()")
         + "; no lock, no queue", c("libei") + " is not reentrant, and two threads on one context fail without "
         "an error. The descriptor goes into the child's " + c("poll()") + " and is never read by hand"],
        ["Always take the <b>last</b> device added", "After a geometry change the old pointer stops working "
         "without an error"],
        ["Re-read region and keymap at every " + c("DEVICE_ADDED") + " (and the region again at "
         + c("DEVICE_RESUMED") + ")", "Mutter recreates devices on every geometry or keymap change"],
        ["Choose the region by mapping id, then by geometry (same size as the canvas), then “the only "
         "one”; with several unknown regions, do not move", "A wrong region sends the pointer to another "
         "screen without an error. Mutter generates its own mapping id and publishes it; v1 looked for the "
         "one it had declared and never found it. KWin publishes none"],
        [c("ei_device_frame()") + " after every single event", "Ignored by Mutter, mandatory on KWin and wlroots"],
        ["Codes at or above " + c("0x300") + " are refused and logged", "Mutter would drop them silently"],
        ["If the region is not as large as the canvas, coordinates are scaled and a warning is written once",
         "The canvas granted by RCP should match the region"],
    ], "«TAB» — How " + c("input.c") + " drives libei") + \
    warn("until 25 Aug 2026 " + c("input_chiudi()") + " called " + c("ei_disconnect()") + " and "
         + c("ei_unref()") + " unconditionally, and a channel opened 33 ms earlier killed the child with "
         "SIGSEGV before the first frame. In libei 1.3.901, a context whose handshake was requested but not "
         "answered has a NULL connection that " + c("ei_disconnect()") + " dereferences, and "
         + c("ei_unref()") + " calls it first. The cure (D4): " + c("EI_EVENT_CONNECT") + " marks the handshake; "
         "without it the context is <b>abandoned</b> (its descriptors closed, the memory lost, the count kept "
         "in " + c("input_abbandoni()") + ", the abandonment count), and " + c("input_gira()") + " (the input loop step) checks with a zero-timeout "
         + c("poll()") + " whether the compositor hung up before dispatching a context whose handshake is incomplete.",
         "The handshake that must not be interrupted.")

S13 = p("Input keeps a ledger of everything pressed (RCP §11), because a modifier or a button left down in a "
        "session that outlives its client makes the desktop unusable, and nobody connects the two.", lead=True) + \
    table(["Mechanism", "Where", "What it does"], [
        ["The ledger", c("tasti[]") + ", " + c("bottoni[]") + " (keys, buttons) bitmaps in " + c("struct input"),
         "A bit is set <b>after</b> the event was sent, never before; a release clears it"],
        ["Release at detach", c("input_rilascia_tutto()"), "Releases every bit, returns how many left, and always "
         "writes a line, even with zero, so that “nothing was pressed” and “I did not look” "
         "differ. The child calls it on detach and on " + c("FIGLI_INPUT_RILASCIA_TUTTO") + ". "
         + c("input_chiudi()") + " does it as a safety net and says the caller forgot"],
        ["Release before resizing", c("figlio.c") + " (the per-user child), before " + c("cattura_ridimensiona()") + " (capture resize)",
         "Everything is released while the old devices are still alive. The price, declared: a drag in "
         "progress is cut when the canvas changes"],
        ["No wake-up while something is held (cure A)", c("figlio.c") + ", " + c("input_premuti()") + " (pressed count)", "On a still "
         "desktop the capture wake-up also recreates devices; with a key or button down the wake-up waits"],
        ["Orphans", c("segna_orfani()") + " (mark orphans)", "What was down on a device that the compositor removed. Its release "
         "cannot reach anyone: it is not sent, " + c("−1") + " is returned (counted as refused), and the log "
         "says so at the moment of damage"],
        ["Healing (cure C)", c("guarisci()") + " (heal) in " + c("input_gira()"), "Drops and reopens the EIS channel "
         "(" + c("mutter_eis_riattacca()") + ", " + c("kwin_eis_riattacca()") + ": reattach), which is the only thing "
         "that resets the compositor's per-seat count. At most once per second; the session, the monitor and "
         "the stream are not touched"],
    ], "«TAB» — Counting, releasing, healing") + \
    p("<b>Why orphans exist.</b> Measured on 16 and 21 Aug 2026 with a Wayland test client inside the session: "
      "hold " + c("BTN_LEFT") + ", let Mutter recreate the absolute pointer (canvas change, or simply a capture "
      "wake-up on a still desktop), then release. The release never arrives, and from then on <b>no click "
      "arrives at all</b>, while the keyboard keeps working. The chain is in Mutter: "
      + c("remove_viewport_devices") + " removes the device without " + c("drop_device()") + "; the new device "
      "silently swallows a release it never saw pressed; and the seat counts presses across devices, so it "
      "stays at one forever. A press-release on the new device makes the count go 1 → 2 → 1. Only the drop of "
      "the EIS client resets it, and it is the " + c("ei_disconnect()") + " message, not the closing of the "
      "descriptor, that triggers it (both verified with injected faults). Releasing before a resize and cure A close "
      "the doors that REMOTIX controls; cure C repairs the doors it does not control (" + c("monitors-changed") + ", keymap changes, "
      "and whatever GNOME adds: " + c("meta_eis_viewport_notify_changed()") + " is new in GNOME 48.5).") + \
    p("Keyboard devices are not recreated by geometry changes (measured: zero keyboard swaps out of fifteen "
      "pointer swaps) but they are by keymap changes, which is why every layout change starts with "
      + c("input_rilascia_tutto()") + ".")

S14 = p("labwc has no " + c("libei") + ". " + c("wlr_input.c") + " creates our own virtual keyboard ("
        + c("zwp_virtual_keyboard_manager_v1") + ") and pointer (" + c("zwlr_virtual_pointer_manager_v1")
        + ") on the user's Wayland socket; " + c("input.c") + " keeps the same contract on top of it, branching "
        "at the top of every public function, so the GNOME and KDE paths are untouched.", lead=True) + \
    table(["Silent trap", "What wlroots does", "What " + c("wlr_input.c") + " does"], [
        ["1. Wheel units", c("discrete") + " is in notches; wlroots multiplies by 120", "Sends whole notches "
         "from an accumulator"],
        ["2. Zero value", "A " + c("value") + " of 0 becomes " + c("axis_stop") + " and the notch vanishes",
         "Sends only when there is at least one notch, with 15.0 per notch"],
        ["3. Frames", "Axes stay pending until " + c("frame") + "; applications group events by frame",
         c("cornice()") + " (frame) after every pointer event"],
        ["4. Modifiers", "Keys are forwarded with " + c("update_state = false") + ": Shift+A gives "
         + c("a") + ", Ctrl+C does not copy, no error anywhere", "Keeps its own " + c("xkb_state")
         + " on the same keymap and sends " + c("modifiers") + " after every key that changes them"],
        ["5. Destruction", c("wlr_pointer_finish()") + " does not release buttons", "Releases held buttons, "
         "with a frame, and flushes before destroying"],
    ], "«TAB» — The five traps of wlroots (" + c("STUDI.md") + " §xfce §7.2) and their cures") + \
    p("Measured on 21 Sep 2026 on the laptop, with a private headless labwc 0.8.3 (the Trixie version) and "
      "the test client " + c("06-b33-testimone.c") + " (the “witness”), not on the test server nor in a full XFCE session: Shift "
      "arrives as a modifier before the letter; CapsLock pressed three times locks once; +120 from the client "
      "is one notch up and two halves of 60 are one notch; absolute positions are exact and saturated; a "
      "double press with one release gives one pair; switching to " + c("de") + " puts Z on key 21; closing "
      "with Ctrl and left button down releases both.") + \
    table(["Topic", "Behaviour"], [
        ["Keymap at start", "A temporary " + c("wl_keyboard") + " “spy” receives the session keymap and "
         "is released; on headless labwc there is no real keyboard, the seat has no keyboard capability, and "
         "the keymap is composed from the child's environment instead (declared). The negotiated layout "
         "replaces it right after"],
        ["Keymap before any key", "Without a keymap a key is a protocol error that closes the whole "
         "connection (" + c("no_keymap") + "), so keys are refused until one was sent"],
        ["Duplicates", "A press of a key already down, or a release of one already up, is dropped: the seat "
         "would count two presses"],
        ["Pointer bound to the output", "With manager version 2 the pointer is created on our output, so "
         "absolute coordinates are relative to it; whether labwc honours it is read, not measured"],
        ["Normalised coordinates", c("motion_absolute(x, y, width, height)") + ": if the output changes size "
         "between two messages the point keeps its proportion"],
        ["Connection lost", c("riattacca_wlr()") + " (reattach) reconnects within one second (same back-off as cure C), "
         "re-sends the negotiated keymap, releases held buttons on the new device, and writes one line "
         "however many times it fails"],
        ["Blocking waits", "Only at open and reattach, each bounded by 2 s; the loop path never waits"],
    ], "«TAB» — The labwc input path in practice") + \
    warn("labwc applies its own keybindings to virtual keys too. Measured on 21 Sep 2026 (laptop, headless "
         "labwc): " + key("Alt", "F4") + " from our channel closes the test client's window, which sees Alt and never "
         "F4. It is the desktop's behaviour, and on XFCE what the user expects.", "Shortcuts belong to labwc.") + \
    p("<b>Bringing windows back inside.</b> On labwc a shrinking output leaves large windows partly outside "
      "the right and bottom edges. After every resize the child calls " + c("input_riporta_dentro()") + " (bring back inside), "
      "which releases everything and types the unused shortcut " + c("SESSIONE_LABWC_TASTO") + " (the labwc session key, "
      + c("W-C-A-S-F12") + ", i.e. Super+Ctrl+Alt+Shift+F12) that REMOTIX writes into labwc's configuration, "
      "then puts the pointer back where the user had it. On GNOME and KDE the function does nothing, because "
      "the compositor already does it. The shortcut itself is described in " + rif("Output size on labwc") + ".")

S15 = p("The main decisions of the input subsystem, with the reason that made each one.", lead=True) + \
    table(["Decision", "Rejected alternative", "Reason"], [
        ["Absolute pointer, drawn by the client", "Relative pointer with Pointer Lock always on; pointer "
         "inside the video", "Latency perceived at hand speed; no trails; one cursor"],
        ["Letters as letters, commands as positions", "Positions only (like RDP)", "Wrong letters with "
         "different layouts; Android keyboards have no positions"],
        ["Session layout wins, mismatch declared", "Force the client's layout silently", "The compositor "
         "interprets keys with its own keymap"],
        ["Layout written in the session dconf / session config", "Write the user's settings and restore later",
         "A crash would leave the change forever (D-015)"],
        [c("scroll_delta") + " on Mutter", c("scroll_discrete"), "Integer division by 120 loses half notches"],
        ["Release before resize, heal by reconnecting EIS", "Release on the new device", "Measured: it never "
         "arrives, and clicks die for the whole session"],
        ["Abandon a libei context whose handshake is incomplete", "Free it", "Freeing it crashes in libei 1.3.901"],
        ["Ctrl+V not cancelled, V held up to 400 ms", "Delay every keystroke by 100 ms (Xpra)", "Twice the "
         "latency budget, paid on every key"],
        ["Only Ctrl+Alt+Del as an on-screen button", "A bar of buttons", "The bar costs pixels; only that one "
         "locks the user out when missing"],
        ["Gesture thresholds in CSS pixels", "Physical pixels", "A finger is ten millimetres on every screen"],
    ], "«TAB» — Input decisions")

CHAPTER = ("Input", [
    ("Input at a glance", S1),
    ("The input messages", S2),
    ("Classic and touch layouts in the page", S3),
    ("Mouse and pointer in the classic layout", S4),
    ("Wheel and scrolling", S5),
    ("Keyboard: letters and positions", S6),
    ("Shortcuts the browser keeps", S7),
    ("Touch gestures", S8),
    ("The on-screen keyboard on a phone", S9),
    ("From a letter to key positions", S10),
    ("Keyboard layout negotiation", S11),
    ("Injection through libei", S12),
    ("Pressed keys: counting, releasing, healing", S13),
    ("Virtual keyboard and pointer on labwc", S14),
    ("Input decisions", S15),
])
