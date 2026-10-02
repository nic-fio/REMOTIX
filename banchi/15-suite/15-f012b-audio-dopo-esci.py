#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f012b — F-012B AUDIO DOPO «ESCI»: si esce, si rientra subito, e un programma
           PulseAudio si sente ancora nel browser

    python3 15-f012b-audio-dopo-esci.py --scatola gnome --browser firefox [--guasto]

IL DIFETTO CHE GUARDA (segnalazione dell'utente, 2 ott 2026, GNOME sulla Radeon,
Firefox).  Dopo «Esci» e un nuovo accesso — il GESTORE D'UTENTE di systemd e'
ancora vivo (resta finche' c'e' la sessione logind del figlio `remotix`) — la
sessione di prima ferma pipewire, wireplumber e filter-chain ma NON
`pipewire-pulse`; la sessione nuova accende un pipewire nuovo, e il
`pipewire-pulse` vecchio resta attaccato al niente ⇒ i programmi che parlano
PulseAudio (firefox-esr dentro la sessione) sono muti, e il nostro sink cattura
solo silenzio digitale.  La cura sta in `src/sessione.c` («IL `pipewire-pulse`
RIMASTO DALLA SESSIONE DI PRIMA»).

⛔ PERCHE' NON `pw-play` (quello di F-012): e' un client PipeWire NATIVO, parla
   al pipewire nuovo e si sente anche col difetto.  Qui suona un client
   PulseAudio VERO: `libpulse-simple` (la stessa libreria che usano i
   programmi PulseAudio) chiamata da python3 con ctypes — nelle quattro
   scatole non c'e' `paplay` (pulseaudio-utils non e' installato) e ffmpeg e'
   compilato senza l'uscita pulse.  Il tono e' quello di F-012 (440 Hz,
   ampiezza 0,5, sink PREDEFINITO, nessun bersaglio).

LA SCENA (un inquilino, c15912u<n>):
  1  accesso con l'orecchio di F-012 (`15-g4-comune.py`), il client pulse
     suona ⇒ il tono DEVE arrivare (se no la prova non ha una base: BLOCKED);
  2  «Esci» col gesto di F-021 (il metodo che la voce del menu raggiunge):
     il prodotto dichiara la fine, la pagina torna al modulo;
  3  SUBITO un nuovo accesso (pagina ricaricata, orecchio rimesso): il
     registro dice «LA FACCIO NASCERE» (sessione nuova) e il gestore d'utente
     e' lo STESSO di prima (stesso pid di `systemd --user`) — altrimenti la
     scena del difetto non c'e' e non ho guardato niente (BLOCKED);
  4  il client pulse suona di nuovo ⇒ il tono DEVE arrivare al browser.

F-012B  atteso: al punto 4, il giudice di F-012 (>= 80 % dei campioni
        udibili, picco a 440 ± 12 Hz su 6 s) dice PASS, E `pipewire-pulse`
        non e' piu' vecchio di `pipewire` (inizio letto da /proc/<pid>/stat,
        tolleranza 2 s; pid e ora d'inizio di pipewire, pipewire-pulse,
        wireplumber e del gestore d'utente si scrivono nelle evidenze ai
        quattro momenti: suona, dopo «Esci», dopo il rientro, risuona).

GUASTO (stessa sessione, dopo la passata sana): al punto 4 non suona NIENTE
  g1  il client pulse ucciso ⇒ la stessa lettura dell'orecchio DEVE dire FAIL;
  g2  i campioni veri del punto 4 contro un'ATTESA SBAGLIATA (660 Hz) ⇒ FAIL;
  g3  la regola dei pid su una fotografia FINTA del difetto (pulse nato prima
      di pipewire) ⇒ FAIL.
  Visto = tutt'e tre rossi.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

F12 = S._carica("f012", os.path.join(S.QUI, "15-f012-audio.py"))
F21 = S._carica("f021", os.path.join(S.QUI, "15-f021-esci.py"))
G4 = F12.G4

FUNZIONI = ("F-012B",)
CLIENT = "c15pulse.py"
SEGNO_CLIENT = "c15pulse"
TOLL_INIZIO_S = 2.0
# le unita' del gestore d'utente che si fotografano; `systemd` nella init.scope
# e' il gestore stesso
UNITA = ("pipewire.service", "pipewire-pulse.service", "wireplumber.service",
         "filter-chain.service")

# ⭐ Il client PulseAudio: libpulse-simple, il tono in giro finche' non lo si
#   uccide.  Se il server pulse non risponde (o la scrittura cade) lo dice e
#   riprova, come un lettore vero.
CLIENT_PY = r'''
import ctypes, sys, time, wave
pa = ctypes.CDLL("libpulse-simple.so.0")
class Spec(ctypes.Structure):
    _fields_ = [("format", ctypes.c_int), ("rate", ctypes.c_uint32), ("channels", ctypes.c_uint8)]
pa.pa_simple_new.restype = ctypes.c_void_p
pa.pa_simple_new.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                             ctypes.c_char_p, ctypes.POINTER(Spec), ctypes.c_void_p,
                             ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
pa.pa_simple_write.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t,
                               ctypes.POINTER(ctypes.c_int)]
pa.pa_simple_free.argtypes = [ctypes.c_void_p]
w = wave.open(sys.argv[1])
assert w.getsampwidth() == 2
spec = Spec(3, w.getframerate(), w.getnchannels())          # PA_SAMPLE_S16LE
dati = w.readframes(w.getnframes())
pezzo = w.getframerate() * w.getnchannels() * 2 // 10       # 100 ms
while True:
    err = ctypes.c_int(0)
    h = pa.pa_simple_new(None, b"c15pulse", 1, None, b"tono 440", ctypes.byref(spec),
                         None, None, ctypes.byref(err))      # 1 = PA_STREAM_PLAYBACK
    if not h:
        print("pa_simple_new: errore %d" % err.value, flush=True)
        time.sleep(1)
        continue
    print("collegato al server pulse", flush=True)
    vivo = True
    while vivo:
        for i in range(0, len(dati), pezzo):
            b = dati[i:i + pezzo]
            if pa.pa_simple_write(h, b, len(b), ctypes.byref(err)) < 0:
                print("pa_simple_write: errore %d" % err.value, flush=True)
                vivo = False
                break
    pa.pa_simple_free(h)
    time.sleep(1)
'''


# ═══════════════════════════════════════════════════════════════════════════
#  I GIUDICI — puri
# ═══════════════════════════════════════════════════════════════════════════
def leggi_foto(testo):
    """Le righe `@@p <comm> <pid> <inizio_tick> <unita'>` e `@@hz <n>` ⇒
    {"hz": n, "proc": [{"comm", "pid", "inizio_s", "unita"}]} — pura."""
    hz, proc = None, []
    for r in (testo or "").splitlines():
        p = r.split()
        if len(p) == 2 and p[0] == "@@hz" and p[1].isdigit():
            hz = int(p[1])
        elif len(p) >= 4 and p[0] == "@@p" and p[2].isdigit() and p[3].isdigit():
            proc.append({"comm": p[1], "pid": int(p[2]), "tick": int(p[3]),
                         "unita": p[4] if len(p) > 4 else ""})
    for x in proc:
        x["inizio_s"] = round(x.pop("tick") / float(hz or 100), 2)
    return {"hz": hz, "proc": proc}


def di(foto, unita):
    """Il processo dell'unita' (o il gestore, `unita="init.scope"`), o None.
    Se ce n'e' piu' d'uno: il PIU' VECCHIO (e' quello rimasto)."""
    v = [x for x in (foto or {}).get("proc", []) if x["unita"] == unita
         and (unita != "init.scope" or x["comm"] == "systemd")]
    return min(v, key=lambda x: x["inizio_s"]) if v else None


def riassunto(foto):
    pezzi = []
    for u in ("init.scope",) + UNITA:
        x = di(foto, u)
        if x:
            pezzi.append("%s pid %d da %.1f s" % (u.replace(".service", "").replace(
                "init.scope", "gestore"), x["pid"], x["inizio_s"]))
    return ", ".join(pezzi) or "(nessuno)"


def giudica_pid(prima, dopo):
    """(esito, ragione) della regola: pipewire-pulse non piu' vecchio di
    pipewire nella sessione nuova, col gestore d'utente sopravvissuto.
    `prima` = foto della sessione 1, `dopo` = foto della sessione 2 che suona."""
    g1, g2 = di(prima, "init.scope"), di(dopo, "init.scope")
    if not g1 or not g2:
        return S.BLOCKED, "non vedo il gestore d'utente (prima %s, dopo %s)" % (g1, g2)
    if g1["pid"] != g2["pid"]:
        return S.BLOCKED, ("il gestore d'utente NON e' sopravvissuto all'uscita (pid %d ⇒ %d): "
                           "la scena del difetto non c'e'" % (g1["pid"], g2["pid"]))
    pw, pp = di(dopo, "pipewire.service"), di(dopo, "pipewire-pulse.service")
    if not pw:
        return S.FAIL, "nella sessione nuova non c'e' pipewire"
    if not pp:
        return S.FAIL, "nella sessione nuova, col client pulse che suona, non c'e' pipewire-pulse"
    if pp["inizio_s"] < pw["inizio_s"] - TOLL_INIZIO_S:
        vecchio = di(prima, "pipewire-pulse.service")
        return S.FAIL, ("pipewire-pulse (pid %d, da %.1f s) e' PIU' VECCHIO di pipewire "
                        "(pid %d, da %.1f s)%s" % (
                            pp["pid"], pp["inizio_s"], pw["pid"],
                            pw["inizio_s"], " — e' quello della sessione di prima"
                            if vecchio and vecchio["pid"] == pp["pid"] else ""))
    return S.PASS, ("gestore vivo (pid %d); pipewire-pulse pid %d da %.1f s, pipewire pid %d "
                    "da %.1f s" % (g2["pid"], pp["pid"], pp["inizio_s"], pw["pid"],
                                   pw["inizio_s"]))


def giudica(e_tono, d_tono, e_pid, d_pid):
    """L'esito di F-012B: il tono al punto 4 e la regola dei pid."""
    if e_pid == S.BLOCKED:
        return S.BLOCKED, d_pid
    guai = []
    if e_tono != "PASS":
        guai.append("dopo «Esci» e il rientro il programma PulseAudio NON si sente nel "
                    "browser: %s" % d_tono)
    if e_pid != S.PASS:
        guai.append(d_pid)
    if guai:
        if e_tono == "BLOCKED" and e_pid == S.PASS:
            return S.BLOCKED, " · ".join(guai)
        return S.FAIL, " · ".join(guai)
    return S.PASS, "dopo «Esci» e il rientro il tono si sente: %s · %s" % (d_tono, d_pid)


def certifica():
    guai = 0

    def p(nome, ottenuto, atteso):
        nonlocal guai
        ok = ottenuto == atteso
        guai += not ok
        print("  %s %-62s %s (atteso %s)" % ("OK " if ok else "NO ", nome, ottenuto, atteso))

    U = "user@4013.service"
    t1 = ("@@hz 100\n@@p systemd 700 1000 init.scope\n@@p pipewire 710 1100 pipewire.service\n"
          "@@p pipewire 711 1100 filter-chain.service\n"
          "@@p pipewire-pulse 712 1110 pipewire-pulse.service\n")
    prima = leggi_foto(t1)
    p("⭐ la foto si legge (4 processi, hz 100)", (prima["hz"], len(prima["proc"])), (100, 4))
    p("⭐ il pipewire e' quello di pipewire.service, non filter-chain",
      di(prima, "pipewire.service")["pid"], 710)
    sana = leggi_foto("@@hz 100\n@@p systemd 700 1000 init.scope\n"
                      "@@p pipewire 810 9000 pipewire.service\n"
                      "@@p pipewire-pulse 812 9050 pipewire-pulse.service\n")
    p("⭐ sessione nuova, pulse nato dopo pipewire ⇒ PASS", giudica_pid(prima, sana)[0], S.PASS)
    difetto = leggi_foto("@@hz 100\n@@p systemd 700 1000 init.scope\n"
                         "@@p pipewire 810 9000 pipewire.service\n"
                         "@@p pipewire-pulse 712 1110 pipewire-pulse.service\n")
    p("⛔ il pulse della sessione di prima resta ⇒ FAIL", giudica_pid(prima, difetto)[0], S.FAIL)
    p("⛔ ⇒ e lo dice", "sessione di prima" in giudica_pid(prima, difetto)[1], True)
    p("⭐ pulse nato 1 s prima (attivazione a socket) ⇒ PASS, tolleranza",
      giudica_pid(prima, leggi_foto("@@hz 100\n@@p systemd 700 1000 init.scope\n"
                                    "@@p pipewire 810 9000 pipewire.service\n"
                                    "@@p pipewire-pulse 812 8900 pipewire-pulse.service\n"))[0],
      S.PASS)
    p("⚠ gestore rinato ⇒ BLOCKED (la scena non c'e')",
      giudica_pid(prima, leggi_foto("@@hz 100\n@@p systemd 900 8000 init.scope\n"
                                    "@@p pipewire 810 9000 pipewire.service\n"
                                    "@@p pipewire-pulse 812 9050 pipewire-pulse.service\n"))[0],
      S.BLOCKED)
    p("⚠ foto non letta ⇒ BLOCKED, mai PASS", giudica_pid(prima, leggi_foto(""))[0], S.BLOCKED)
    p("⛔ pulse assente col client che suona ⇒ FAIL",
      giudica_pid(prima, leggi_foto("@@hz 100\n@@p systemd 700 1000 init.scope\n"
                                    "@@p pipewire 810 9000 pipewire.service\n"))[0], S.FAIL)
    p("⛔ un systemd non nella init.scope non e' il gestore",
      di(leggi_foto("@@p systemd 5 1 %s\n" % U), "init.scope"), None)
    p("⭐ tono PASS e pid PASS ⇒ PASS", giudica("PASS", "x", S.PASS, "y")[0], S.PASS)
    p("⛔ tono FAIL (silenzio) ⇒ FAIL", giudica("FAIL", "x", S.PASS, "y")[0], S.FAIL)
    p("⛔ tono PASS ma pulse vecchio ⇒ FAIL", giudica("PASS", "x", S.FAIL, "y")[0], S.FAIL)
    p("⚠ gestore rinato ⇒ BLOCKED anche col tono", giudica("PASS", "x", S.BLOCKED, "y")[0],
      S.BLOCKED)
    p("⚠ pochi campioni e pid in ordine ⇒ BLOCKED", giudica("BLOCKED", "x", S.PASS, "y")[0],
      S.BLOCKED)
    print("⛔ %d casi sbagliati" % guai if guai else "⭐ i giudici dicono quel che devono")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def fotografa(s):
    """Pid, inizio e unita' dei processi dell'inquilino che contano (pipewire,
    pipewire-pulse, wireplumber, il gestore) ⇒ (foto, testo grezzo)."""
    def una():
        c, t = s.sc.dentro(
            "echo \"@@hz $(getconf CLK_TCK)\"; for p in $(pgrep -u %s); do "
            "n=$(cat /proc/$p/comm 2>/dev/null); case \"$n\" in systemd|pipewire*|wireplumber) "
            "st=$(awk '{print $22}' /proc/$p/stat 2>/dev/null); "
            "u=$(head -1 /proc/$p/cgroup 2>/dev/null | awk -F/ '{print $NF}'); "
            "echo \"@@p $n $p $st $u\";; esac; done; echo @@fine; "
            "echo \"@@ora_s $(cut -d' ' -f1 /proc/uptime)\"; "
            "ps -o pid,lstart,etimes,args -u %s | grep -E 'systemd --user|pipewire|wireplumber' "
            "| grep -v grep" % (s.chi, s.chi), 40)
        return t if "@@fine" in (t or "") else None
    t = F21._ritenta(una) or ""
    return leggi_foto(t), t


def prepara_client(s):
    h = "/home/%s/%s" % (s.chi, CLIENT)
    c, t = s.sc.dentro("cat > %s <<'@@FINE@@'\n%s\n@@FINE@@\nchown %s: %s && ls -l %s"
                       % (h, CLIENT_PY, s.chi, h, h), 30)
    return c == 0, (t or "").strip()[-200:]


def suona_pulse(s):
    return s.nella_sessione("exec python3 /home/%s/%s /home/%s/%s # %s"
                            % (s.chi, CLIENT, s.chi, F12.WAV, SEGNO_CLIENT))


def zittisci_pulse(s):
    s.sc.dentro("pkill -u %s -f '[c]15pulse'; sleep 0.3; pgrep -u %s -f '[c]15pulse' || "
                "echo zitto" % (s.chi, s.chi), 30)


def diario_client(s):
    _c, t = s.sc.dentro("tail -n 20 /home/%s/.c15-exec.log 2>/dev/null" % s.chi, 30)
    return (t or "").strip()


def client_visto(s):
    """Il client pulse e' visto dal pipewire della sessione? (diagnosi)"""
    _c, t = s.come_utente("pw-cli ls Client 2>&1 | grep -c c15pulse", 30)
    return (t or "").strip()


def entra_e_ascolta(s, nome, ev, note):
    """Il client suona e l'orecchio ascolta FINESTRA_S ⇒ (esito, descr, numeri, r)."""
    c, t = suona_pulse(s)
    if c != 0:
        raise S.Bloccata("il client pulse non parte nella sessione: " + (t or "")[-200:])
    if not F12.sveglia(s, note):
        return "FAIL", "nessun AudioContext nella pagina in 30 s", {}, {}
    time.sleep(1.0)
    e, d, num, r = F12.ascolta(s, F12.FINESTRA_S)
    ev.append(G4.salva_json(s.o, "f012b-orecchio-%s.json" % nome, r))
    note.append("%s: client «%s», visto da pipewire: %s" % (
        nome, diario_client(s).replace("\n", " | ")[-160:], client_visto(s)))
    return e, d, num, r


def corpo(o, E):
    sess = S.Sessione(o, "912", E)
    G4.robusta(sess.sc)
    with sess as s:
        desktop, gesto = s.sc.gesto_esci()
        if not gesto:
            raise S.Bloccata("non so come si dice «Esci» in %s" % s.sc.contenitore)
        print("   «Esci» (%s): %s" % (desktop, gesto), flush=True)
        ok, m = F12.entra_con_orecchio(s)
        if not ok:
            raise S.Bloccata(m)
        ok, m = F12.prepara_tono_ffmpeg(s)
        if not ok:
            print("   ⚠ il tono con ffmpeg: %s — lo scrive il banco" % m, flush=True)
            ok, m = F12.prepara_tono(s)
        if not ok:
            raise S.Bloccata("il tono non si prepara nella scatola: " + m)
        ok, m = prepara_client(s)
        if not ok:
            raise S.Bloccata("il client pulse non si scrive nella scatola: " + m)
        segno = s.segno_registro()
        ev, note, foto = [], [], {}

        def scatta(nome):
            f, t = fotografa(s)
            foto[nome] = f
            ev.append(s.salva_testo("f012b-processi-%s.txt" % nome, t))
            print("      [%s] %s" % (nome, riassunto(f)), flush=True)
            return f

        # 1 ── la prima sessione suona ───────────────────────────────────────
        e1, d1, _n1, _r1 = entra_e_ascolta(s, "1-prima", ev, note)
        scatta("1-suona")
        print("   1 prima di «Esci»: %s — %s" % (e1, d1), flush=True)
        if e1 != "PASS":
            ev.append(s.salva_testo("server-f012b.txt", s.registro_da(segno) if segno else []))
            raise S.Bloccata("gia' PRIMA di «Esci» il client pulse non si sente (%s): non e' "
                             "la scena di questa prova (vedi F-012)" % d1)
        zittisci_pulse(s)

        # 2 ── «Esci» come l'utente ───────────────────────────────────────────
        segno_esci = F21._ritenta(s.segno_registro)
        c, t = F21.fai_il_gesto(s, gesto)
        if c != 0:
            raise S.Bloccata("il gesto «Esci» non ha risposto (codice %s): %s" % (c, t[-200:]))
        t0 = time.time()
        finita, _r = F21.aspetta_finita(s, segno_esci, F21.TETTO_FINITA)
        if not finita:
            raise S.Bloccata("dopo «Esci» il prodotto non dichiara la sessione finita in %.0f s"
                             % F21.TETTO_FINITA)
        modulo, frase, _letta = F21.leggi_pagina(s, 30)
        esci = "finita («%s») dopo %.1f s, pagina al modulo=%s «%s»" % (
            finita, time.time() - t0, modulo, frase[:60])
        print("   2 %s" % esci, flush=True)
        scatta("2-dopo-esci")

        # 3 ── SUBITO dentro di nuovo ───────────────────────────────────────
        segno_rientro = F21._ritenta(s.segno_registro)
        t1 = time.time()
        ok, m = F12.entra_con_orecchio(s)
        if not ok:
            raise S.Bloccata("il rientro dopo «Esci» non riesce: %s" % m)
        fetta = F21.registro(s, segno_rientro) or []
        nuova = any("LA FACCIO NASCERE" in r and F21.e_di(r, s.chi) for r in fetta)
        rientro = "rientro %.1f s dopo il modulo, sessione %s" % (
            t1 - t0, "NUOVA («LA FACCIO NASCERE»)" if nuova else "NON nuova (ripresa?)")
        print("   3 %s" % rientro, flush=True)
        scatta("3-dopo-rientro")
        if not nuova:
            ev.append(s.salva_testo("server-f012b.txt", s.registro_da(segno) if segno else []))
            raise S.Bloccata("il rientro non ha fatto nascere una sessione nuova: la scena "
                             "del difetto non c'e' (%s)" % rientro)

        # 4 ── il client pulse risuona ──────────────────────────────────────
        e4, d4, num4, r4 = entra_e_ascolta(s, "4-dopo-esci", ev, note)
        campioni4 = r4.get("campioni") or []
        dopo = scatta("4-risuona")
        e_pid, d_pid = giudica_pid(foto["1-suona"], dopo)
        nome, _v, _m, tv = F12.volume(s)
        esito, perche = giudica(e4, d4, e_pid, d_pid)
        ev.append(s.salva_testo("server-f012b.txt", s.registro_da(segno) if segno else []))
        ev.append(s.salva_console())
        _png, dove = s.foto("f012b-fine")
        if dove:
            ev.append(dove)
        oss = " · ".join([
            "1: %s" % d1, "2: %s" % esci, "3: %s" % rientro, "4: %s" % d4,
            "sink predefinito «%s», %s" % (nome, tv),
            "pid 1: %s" % riassunto(foto["1-suona"]),
            "pid 2: %s" % riassunto(foto["2-dopo-esci"]),
            "pid 3: %s" % riassunto(foto["3-dopo-rientro"]),
            "pid 4: %s" % riassunto(dopo), "; ".join(note)])
        print("   4 %s — %s" % (esito, perche), flush=True)
        E.metti("F-012B", esito, perche,
                atteso="dopo «Esci» e un rientro subito (gestore d'utente vivo) un client "
                       "PulseAudio suona e il browser sente il tono 440 Hz (>=80%% udibile, "
                       "picco 440±12 Hz); pipewire-pulse non piu' vecchio di pipewire "
                       "(tolleranza %.0f s)" % TOLL_INIZIO_S,
                osservato=oss, evidenze=ev, numeri=num4, gesto=gesto)

        if not o.guasto:
            return
        # ── il guasto: al punto 4 non suona niente ─────────────────────────
        zittisci_pulse(s)
        time.sleep(1.5)
        eg1, dg1, _x, rg1 = F12.ascolta(s, 4.0)
        evg = [G4.salva_json(o, "f012b-orecchio-guasto.json", rg1)]
        if not campioni4:
            E.guasto("F-012B", None, "nessun campione sano al punto 4 per l'attesa sbagliata")
            return
        eg2, dg2, _y = G4.giudica_suono(campioni4, 660)
        finto = leggi_foto("@@hz 100\n@@p systemd 1 10 init.scope\n"
                           "@@p pipewire 3 900 pipewire.service\n"
                           "@@p pipewire-pulse 2 20 pipewire-pulse.service\n")
        eg3, dg3 = giudica_pid(leggi_foto("@@hz 100\n@@p systemd 1 10 init.scope\n"
                                          "@@p pipewire-pulse 2 20 pipewire-pulse.service\n"),
                               finto)
        visto = eg1 == "FAIL" and eg2 == "FAIL" and eg3 == S.FAIL
        E.guasto("F-012B", visto,
                 "al punto 4 nessun suono ⇒ %s «%s» · attesa 660 Hz sui campioni veri ⇒ %s "
                 "«%s» · pulse piu' vecchio di pipewire (foto finta) ⇒ %s «%s»"
                 % (eg1, dg1, eg2, dg2, eg3, dg3), evidenze=evg)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
