# The Android tests on your phone (phase 19 §5)

**What it does.** It runs the 10 tests of `fasi/19-nvidia.md` §5.1 by itself, on your phone, with **Chrome**,
against the server's boxes. They are the same tests as the suite, with the same judges: the phone's Chrome
takes the place of the server's, and that is all. Full round on GNOME (rows 1-10), short round on KDE, XFCE and
LXQt (rows 1, 2, 6, 9).

**What it needs.** Phonestra open on the laptop (the phone seen by adb), phone **unlocked**,
on the same network, preferably charging. The boxes running and no other round on the server.

**How to launch it** (from the laptop, in the REMOTIX folder):

    bash banchi/19-android/19-android.sh controlla       # phone, calls, Chrome, server: all in order?
    bash banchi/19-android/19-android.sh prova tutte     # all 10 (about an hour and a half)
    bash banchi/19-android/19-android.sh prova 7         # a single row, on GNOME
    bash banchi/19-android/19-android.sh prova 2 --desktop kde

**The phone stays yours.**
- It opens **only Chrome**, in tabs of its own, only towards `192.168.0.2`. It records your tabs at the start and does not
  touch them; at the end it closes its own and checks that yours are all there.
- **Never during a call**: before every gesture it looks; if the phone rings, it stops and waits (up to 20
  minutes), then redoes the interrupted test.
- For the duration of the round the screen does not turn off by itself, and in test 7 the phone **rotates by itself**
  (portrait → landscape → portrait). At the end it puts everything back as it was: automatic rotation, screen
  timeout, and Chrome closed if it was.
- Test 8 **closes Chrome abruptly**: normal tabs come back by themselves, **incognito ones do not** —
  close them first, if you have any.
- If you interrupt it (Ctrl-C) it puts the phone back in order by itself; if it is interrupted badly:
  `bash banchi/19-android/19-android.sh ripristina`.

**Where the results end up.** In the suite's log, on the server, in
`/media/REMOTIX/misure/fase19-android/registro.jsonl` (browser "telefono"), with the photos of the canvas
and of the phone's page next to it. At the end the script prints the summary and the report command.

**Two things said plainly.** Test 9 (network drops) does not turn off the phone's Wi-Fi — the
connection with adb would be lost — but cuts the line on the server side, as the suite does. Tests 3-10 type and
click like mouse and keyboard (the DeX case); the **real finger** (touch, dragging with the finger) is test 2,
which also checks the **on-screen keyboard**: closed by itself, opened and closed again by the small ⌨ button (it reads the state
from Android).
