#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f021 — F-021 «ESCI» DAL MENU: la sessione finisce, i programmi si chiudono,
          la pagina torna al modulo, niente rinascita; e chi rientra ne apre
          una NUOVA, pulita

    python3 15-f021-esci.py --scatola lxqt --browser chrome [--guasto]

⭐ CHE COSA FA, in una sessione sola (inquilino c15021u<n>), come l'utente:
   1  entra dal browser vero; dentro la sessione apre un PROGRAMMA vero
      (firefox-esr con la scena di C20, il suo processo e' il testimone)
   2  il gesto «Esci» (vedi GESTO, sotto) e la guardia:
        F  il prodotto dichiara la sessione finita (`C20.RIGHE_FINITA`)
        M  la PAGINA torna al modulo (campo `#modulo` visibile) e la riga
           `#esito` dice «la sessione e' terminata» (`pagina.html` 0x10)
        P  i processi dell'inquilino: nessuno, salvo quelli di ESENTI
           (`ps -u`), e il programma aperto al punto 1 non c'e' piu'
        N  ⛔ per GUARDIA_S secondi dopo la fine, nel registro del server
           nessuna nascita per questo inquilino («LA FACCIO NASCERE»,
           «formato negoziato»): niente rinascita
   3  un nuovo accesso DALLA STESSA PAGINA (se il modulo non c'e': ricarica,
      e lo si dice) ⇒ primo fotogramma, e
        R  NUOVA: il registro dice «LA FACCIO NASCERE» dopo il rientro (una
           sessione ripresa non la dice: il figlio la trova viva)
        C  PULITA: il programma del punto 1 non c'e'
   Esito: PASS solo se F M P N R C.  Un gesto che non risponde, una pagina
   che non si apre ⇒ BLOCKED.

⚠ GESTO — dichiarato.  Non il clic sul menu col mouse del browser: e' il
  METODO che la voce «Esci» del menu raggiunge, la tavola di C20
  (`DESKTOP_E_GESTO`, la stessa di `12-c20-veri.py`, importata):
     GNOME  org.gnome.SessionManager.Logout(1)
     KDE    org.kde.Shutdown.logout
     XFCE   xfce4-session-logout --logout --fast
     LXQt   org.lxqt.session.logout
  Perche': il menu e' diverso nei quattro desktop (GNOME: tre clic e un
  dialogo col conto alla rovescia; KDE: lanciatore, «Esci», conferma; XFCE e
  LXQt: menu classico), e a 3840x2160 le voci andrebbero TROVATE sulla
  fotografia — una prova di riconoscimento d'immagine, non dell'uscita.
  Quel che il prodotto vede (il compositore che se ne va, il gestore di
  sessione che chiude) e' lo stesso: il difetto 6 della fase 14 (la
  rinascita su LXQt) si riproduceva con questo gesto (C24, 16 su 20).

⛔ IL GUASTO INNESTATO (nella stessa sessione, dopo la passata sana) — due, e
   devono essere visti TUTT'E DUE:
   G1 «Esci a vuoto»: al posto del gesto una chiamata D-Bus innocua (GetId del
      bus di sessione, risponde 0 e non fa niente) ⇒ la sessione NON finisce
      ⇒ il giudice DEVE dire FAIL (F, M, P rossi).
   G2 «rientro dentro la guardia»: «Esci» vero, e appena la pagina e' tornata
      al modulo il banco rientra SUBITO ⇒ una sessione nasce dentro la
      finestra di GUARDIA_S ⇒ il giudice DEVE dire FAIL per rinascita (N).
      ⚠ Prova che il giudice LEGGE una nascita dopo la fine e la chiama
      rosso; nella passata sana il banco non rientra mai dentro la finestra
      ⇒ ogni nascita che vi compare e' del prodotto.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNZIONI = ("F-021",)


C20 = S.C20V.C20
RIGHE_FINITA = [p for p, _d in C20.RIGHE_FINITA]
NASCITE = ("LA FACCIO NASCERE", "formato negoziato")
FRASE_PAGINA = "terminata"                       # pagina.html, MESSAGGI[0x10]
GUARDIA_S = 25.0
TETTO_FINITA = 60.0
TETTO_PROCESSI = 30.0
# ⭐ I processi dell'inquilino che possono restare dopo «Esci», e perche' —
#   si giudica dal GRUPPO DI CONTROLLO (/proc/<pid>/cgroup), non dal nome:
#   remotix        il FIGLIO del prodotto (gira col suo uid, nel gruppo del
#                  server): per disegno resta, e il rientro nasce in lui (I2;
#                  C24: «il secondo accesso nasce nel figlio sopravvissuto»).
#   user@<uid>.service/…/*.service e init.scope   il GESTORE D'UTENTE di
#                  systemd e i suoi servizi (dbus, pipewire, wireplumber…):
#                  vivono quanto il gestore d'utente, che resta finche' logind
#                  ha una sessione dell'utente — quella del figlio.  Non li ha
#                  aperti l'utente e non sono la sessione grafica.
#   ⛔ CONTANO: tutto quel che sta in una `session-N.scope` (il desktop e i
#      programmi aperti da lui, LXQt/XFCE) e in una `app-*.scope` (i programmi
#      aperti da GNOME e KDE), e ogni altro posto.  L'elenco intero sta
#      nell'«osservato».
ESENTI = ("remotix",)


def esente(voce):
    """`voce` = «nome|cgroup».  Vedi ESENTI qui sopra — pura."""
    nome, _, cg = voce.partition("|")
    if nome in ESENTI:
        return True
    if "/user@" not in cg:
        return False
    foglia = cg.rstrip("/").rsplit("/", 1)[-1]
    return foglia == "init.scope" or (foglia.endswith(".service")
                                       and not foglia.startswith("app-"))


PROGRAMMA = "firefox-esr"
# ⚠ Le righe del server che dicono «il filo della pagina e' caduto» (rcp.c,
#   webtransport.c): con dieci banchi sullo stesso server il ciclo del padre
#   si e' fermato fino a 17 s (24 set, «rimasto indietro di … ms»), e Chrome
#   ha chiuso il trasporto PRIMA che «Esci» arrivasse.
FILO_CADUTO = ("la pagina ha CHIUSO la sessione", "STACCATO per silenzio")
GESTO_A_VUOTO = ("busctl --user call org.freedesktop.DBus /org/freedesktop/DBus "
                 "org.freedesktop.DBus GetId")


# ═══════════════════════════════════════════════════════════════════════════
#  I GIUDICI — puri
# ═══════════════════════════════════════════════════════════════════════════
def e_di(riga, chi):
    return ("[%s]" % chi) in riga or ("«%s»" % chi) in riga


def nascite_in(righe, chi):
    if righe is None:
        return None
    return [r for r in righe if e_di(r, chi) and any(n in r for n in NASCITE)]


def residui(voci):
    if voci is None:
        return None
    return sorted(v for v in voci if not esente(v))


def giudica_uscita(d):
    """⭐ (esito, ragione) dell'uscita dai campi misurati:
         finita   la forma di RIGHE_FINITA vista, o None
         modulo   il modulo e' visibile nella pagina
         frase    il testo di #esito
         rimasti  i processi dell'inquilino non esenti (lista, o None)
         programma  il programma del punto 1 c'e' ancora
         nascite  le righe di nascita dopo la fine (lista, o None)
    ⛔ La rinascita si guarda PRIMA di tutto: nel difetto 6 il prodotto dice
       «e' finita» e poi la fa nascere, e un verde letto sulla fine sarebbe il
       difetto che passa."""
    if not d.get("finita") and d.get("filo_caduto") and not d.get("nascite"):
        # ⚠ il filo della pagina e' caduto PRIMA che la fine arrivasse: il
        #   prodotto non aveva nessuno a cui dirla, e la pagina non l'ha potuta
        #   sentire ⇒ non ho potuto guardare (mai un FAIL, mai un PASS)
        return S.BLOCKED, ("il filo della pagina e' caduto prima della fine («%s»): "
                           "non ho potuto guardare l'uscita" % d["filo_caduto"][:140])
    muta = d.get("pagina_letta") is False and not d.get("nascite")
    guai = []
    if d.get("nascite"):
        guai.append("dopo «Esci» la sessione RINASCE (%d righe; la prima: %s)"
                    % (len(d["nascite"]), d["nascite"][0].strip()[:120]))
    if not d.get("finita"):
        guai.append("il prodotto non dichiara la sessione finita")
    if muta and d.get("finita") and not d.get("rimasti") and not d.get("programma"):
        return S.BLOCKED, ("la fine e' dichiarata e i programmi sono chiusi, ma la pagina "
                           "non ha mai risposto al banco: non ho potuto guardarla")
    if not d.get("modulo"):
        guai.append("la pagina NON torna al modulo")
    if FRASE_PAGINA not in (d.get("frase") or ""):
        guai.append("la pagina non dice «la sessione e' terminata» (dice «%s»)"
                    % (d.get("frase") or "")[:80])
    if d.get("programma"):
        guai.append("il programma aperto nella sessione (%s) e' ancora vivo" % PROGRAMMA)
    if d.get("rimasti"):
        guai.append("restano processi dell'inquilino: %s" % " ".join(d["rimasti"])[:160])
    if guai:
        return S.FAIL, " · ".join(guai)
    if d.get("rimasti") is None or d.get("nascite") is None:
        return S.BLOCKED, "non ho potuto leggere i processi o il registro"
    return S.PASS, ("finita («%s»), la pagina al modulo con «%s», nessun processo "
                    "dell'inquilino (esenti: %s), nessuna nascita in %.0f s"
                    % (d["finita"], (d.get("frase") or "")[:60], "/".join(ESENTI),
                       d.get("guardia", GUARDIA_S)))


def giudica_rientro(d):
    """(esito, ragione) del rientro: entrato, nuova (nascita vista), pulita."""
    if not d.get("entrato"):
        return S.FAIL, "dopo «Esci» NON si rientra: %s" % d.get("perche", "")
    guai = []
    if not d.get("nuova"):
        guai.append("il rientro non fa nascere una sessione nuova (nessun «LA FACCIO "
                    "NASCERE»: ripresa?)")
    if d.get("programma"):
        guai.append("la sessione del rientro NON e' pulita: %s c'e' ancora%s" % (
            PROGRAMMA, (" — " + d["chi_lo_riapre"].splitlines()[0][:160])
            if d.get("chi_lo_riapre") else ""))
    if guai:
        return S.FAIL, " · ".join(guai)
    return S.PASS, "rientro: sessione NUOVA («LA FACCIO NASCERE») e pulita"


def certifica():
    guai = 0

    def p(nome, ottenuto, atteso):
        nonlocal guai
        ok = ottenuto == atteso
        guai += not ok
        print("  %s %-62s %s (atteso %s)" % ("OK " if ok else "NO ", nome, ottenuto, atteso))

    buona = {"finita": "E' FINITA", "modulo": True,
             "frase": "la sessione e' terminata: i programmi sono stati chiusi",
             "rimasti": [], "programma": False, "nascite": []}
    g = lambda **k: giudica_uscita(dict(buona, **k))[0]           # noqa: E731
    p("⭐ tutto in ordine ⇒ PASS", g(), S.PASS)
    p("⛔ finita E poi rinata ⇒ FAIL", g(nascite=["figlio [c15021u1] LA FACCIO NASCERE"]),
      S.FAIL)
    p("⛔ non finita (Esci a vuoto) ⇒ FAIL", g(finita=None, modulo=False, frase="Ammesso",
                                             programma=True), S.FAIL)
    p("⛔ la pagina resta sul desktop ⇒ FAIL", g(modulo=False), S.FAIL)
    p("⛔ al modulo ma senza la frase ⇒ FAIL", g(frase="errore di rete"), S.FAIL)
    p("⛔ un processo rimasto ⇒ FAIL", g(rimasti=["pcmanfm-qt"]), S.FAIL)
    p("⚠ filo caduto prima della fine ⇒ BLOCKED",
      g(finita=None, modulo=False, frase="", filo_caduto="la pagina ha CHIUSO la sessione"),
      S.BLOCKED)
    p("⛔ filo caduto MA rinata ⇒ FAIL",
      g(finita=None, filo_caduto="x", nascite=["[c15021u1] LA FACCIO NASCERE"]), S.FAIL)
    p("⚠ la pagina non risponde al banco ⇒ BLOCKED",
      g(modulo=False, frase="", pagina_letta=False), S.BLOCKED)
    p("⛔ la pagina risponde e non e' al modulo ⇒ FAIL",
      g(modulo=False, frase="", pagina_letta=True), S.FAIL)
    p("⚠ processi non letti ⇒ BLOCKED, mai PASS", g(rimasti=None), S.BLOCKED)
    p("⚠ registro non letto ⇒ BLOCKED, mai PASS", g(nascite=None), S.BLOCKED)
    U = "0::/user.slice/user-4013.slice/user@4013.service"
    p("⭐ il figlio e il gestore d'utente non contano",
      residui(["remotix|0::/system.slice/rete11-server.service", "systemd|%s/init.scope" % U,
               "pipewire|%s/session.slice/pipewire.service" % U]), [])
    p("⛔ il desktop nella session scope conta",
      residui(["lxqt-panel|0::/user.slice/user-4013.slice/session-5.scope"]),
      ["lxqt-panel|0::/user.slice/user-4013.slice/session-5.scope"])
    p("⛔ un programma aperto da GNOME (app-*.scope) conta",
      len(residui(["firefox|%s/app.slice/app-gnome-firefox-12.scope" % U])), 1)
    p("⛔ un processo senza gruppo leggibile conta", residui(["x|"]), ["x|"])
    fin = ["figlio  [c15021u1] ⭐ ... LA FACCIO NASCERE io (tela 3840x2160)",
           "figlio  [c15021u10] LA FACCIO NASCERE", "cattura [c15021u1] formato negoziato"]
    p("⚠ le nascite di c15021u10 non sono di c15021u1", len(nascite_in(fin, "c15021u1")), 2)
    p("⭐ rientro nuovo e pulito ⇒ PASS",
      giudica_rientro({"entrato": True, "nuova": True, "programma": False})[0], S.PASS)
    p("⛔ rientro ripreso ⇒ FAIL",
      giudica_rientro({"entrato": True, "nuova": False, "programma": False})[0], S.FAIL)
    p("⛔ rientro col programma di prima ⇒ FAIL",
      giudica_rientro({"entrato": True, "nuova": True, "programma": True})[0], S.FAIL)
    p("⛔ non rientra ⇒ FAIL", giudica_rientro({"entrato": False})[0], S.FAIL)
    p("⭐ le forme della fine vengono da C20", len(RIGHE_FINITA), 2)
    print("⛔ %d casi sbagliati" % guai if guai else "⭐ i giudici dicono quel che devono")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def _ritenta(f, volte=3):
    """⚠ Il server e' di dieci banchi: una lettura che non risponde si rifa'."""
    for _ in range(volte):
        v = f()
        if v is not None:
            return v
        time.sleep(2)
    return None


def processi(s):
    """«nome|cgroup» per ogni processo dell'inquilino, o None."""
    def una():
        c, t = s.sc.dentro(
            "for p in $(pgrep -u %s); do printf '@@p %%s|%%s\\n' \"$(cat /proc/$p/comm "
            "2>/dev/null)\" \"$(head -1 /proc/$p/cgroup 2>/dev/null)\"; done; echo @@fine"
            % s.chi, 40)
        if "@@fine" not in (t or ""):
            return None
        return [x[4:].strip() for x in t.splitlines() if x.startswith("@@p ")
                and x[4:].strip() != "|"]
    return _ritenta(una)


def programma_vivo(s):
    c, _t = s.sc.dentro("pgrep -u %s -x %s >/dev/null" % (s.chi, PROGRAMMA), 30)
    return c == 0


def apri_programma(s):
    """firefox-esr con la scena di C20, DENTRO la sessione (come C20)."""
    ok, t = s.sc.accendi_scena(s.chi)
    if not ok:
        return False, "il programma non si apre nella sessione: %s" % t[-160:]
    fine = time.time() + 20
    while time.time() < fine:
        if programma_vivo(s):
            time.sleep(3)                  # la finestra si disegna
            return True, "%s aperto" % PROGRAMMA
        time.sleep(1)
    return False, "%s non e' fra i processi dell'inquilino dopo 20 s" % PROGRAMMA


def leggi_pagina(s, tetto):
    """(modulo visibile, frase di #esito, letta) aspettando fino a `tetto`.
    `letta` e' False se la pagina non ha MAI risposto al banco (browser in
    stallo: `[M]` 25 set, Chrome sotto carico 50, CDP «timed out»)."""
    fine = time.time() + tetto
    modulo, frase, letta = False, "", False
    while time.time() < fine:
        try:
            m = s.g.js(S.VERI.JS_MODULO)
            modulo = bool(m and m.get("modulo") and m.get("visibile"))
            st = s.stato()
            if "⛔" not in st:
                letta = True
                frase = st.get("esito") or ""
        except Exception:                        # noqa: BLE001
            modulo = False
        if modulo and FRASE_PAGINA in frase:
            break
        time.sleep(0.5)
    return modulo, frase, letta


def aspetta_finita(s, segno, tetto):
    fine = time.time() + tetto
    while time.time() < fine:
        for r in s.registro_da(segno):
            for f in RIGHE_FINITA:
                if f in r and e_di(r, s.chi):
                    return f, r
        time.sleep(1)
    return None, None


def esci_e_guarda(s, gesto, tetto_finita=TETTO_FINITA, rientra_subito=False, nome="esci"):
    """Il gesto e le quattro guardie F M P N.  Torna (dati, evidenze) o
    solleva Bloccata."""
    segno = _ritenta(s.segno_registro)
    if segno is None:
        raise S.Bloccata("non leggo il registro del server")
    c, t = s.sc.come_utente(s.chi, gesto)
    if c != 0:
        raise S.Bloccata("il gesto «Esci» non ha risposto (codice %s): %s" % (c, t[-200:]))
    t0 = time.time()
    finita, _r = aspetta_finita(s, segno, tetto_finita)
    d = {"finita": finita}
    if finita:
        d["finita_s"] = round(time.time() - t0, 1)
    segno_fine = (_ritenta(s.segno_registro) if finita else None) or segno
    d["modulo"], d["frase"], d["pagina_letta"] = leggi_pagina(s, 30 if finita else 5)
    if rientra_subito and d["modulo"]:
        # ⛔ G2: il banco rientra DENTRO la guardia
        e, m, _st = s.pr.entra(s.parola)
        d["rientro_guasto"] = "%s: %s" % ({S.VERDE: "ammesso"}.get(e, "non ammesso"), m[:80])
    # P — i processi: si aspetta che se ne vadano, fino a TETTO_PROCESSI
    fine = time.time() + (TETTO_PROCESSI if finita else 3)
    while True:
        nomi = processi(s)
        d["rimasti"] = residui(nomi)
        d["tutti"] = nomi
        d["programma"] = programma_vivo(s)
        if (d["rimasti"] == [] and not d["programma"]) or time.time() >= fine:
            break
        time.sleep(2)
    # N — la guardia: TUTTA (il verde e' un'assenza)
    resto = GUARDIA_S - (time.time() - t0)
    if resto > 0:
        time.sleep(resto)
    d["guardia"] = time.time() - t0
    if not finita:
        tutta = _ritenta(lambda: s.registro_da(segno) or None) or []
        d["filo_caduto"] = next((r.strip() for r in tutta if e_di(r, s.chi) and any(
            k in r for k in FILO_CADUTO)), None)
    fetta = _ritenta(lambda: s.registro_da(segno_fine) or None)
    # ⚠ una fetta vuota e' possibile solo se il registro non risponde: dopo la
    #   fine il figlio scrive a ogni tentativo («CHIUSA dall'utente»)
    d["nascite"] = nascite_in(fetta, s.chi)
    print("      [%s] segno %s→%s · fetta %s righe · processi %s · nascite %s" % (
        nome, segno, segno_fine, None if fetta is None else len(fetta),
        None if d["rimasti"] is None else len(d["rimasti"]),
        None if d["nascite"] is None else len(d["nascite"])), flush=True)
    ev = [s.salva_testo("server-%s.txt" % nome, s.registro_da(segno))]
    return d, ev


def rientra(s):
    """Il nuovo accesso dalla stessa pagina: (dati, evidenze)."""
    segno = _ritenta(s.segno_registro)
    if segno is None:
        return {"entrato": False, "perche": "non leggo il registro del server"}, []
    d = {"ricaricata": False}
    m = s.g.js(S.VERI.JS_MODULO)
    if not (m and m.get("modulo") and m.get("visibile")):
        d["ricaricata"] = True
        s.g.ricarica()
        ok, perche = s.pr.apri_dopo_ricarica()
        if not ok:
            return dict(d, entrato=False, perche="dopo la ricarica: " + perche), []
    ok, m = s.entra(apri=False)
    d["entrato"], d["perche"] = ok, m
    if not ok:
        return d, [s.salva_testo("server-rientro.txt", s.registro_da(segno or 0))]
    fetta = _ritenta(lambda: s.registro_da(segno) or None) or []
    d["nuova"] = any("LA FACCIO NASCERE" in r and e_di(r, s.chi) for r in fetta)
    time.sleep(3)
    d["programma"] = programma_vivo(s)
    png, dove = s.foto("rientro")
    ev = [s.salva_testo("server-rientro.txt", fetta)] + ([dove] if dove else [])
    if d["programma"]:
        # ⭐ chi l'ha riaperto?  il padre del processo e il salvataggio della
        #   sessione del desktop (KDE: ksmserverrc)
        _c, t = s.sc.dentro(
            "for p in $(pgrep -u %(c)s -x %(p)s); do pp=$(awk '{print $4}' /proc/$p/stat); "
            "echo \"$p padre $pp $(cat /proc/$pp/comm) · $(tr '\\0' ' ' < /proc/$p/cmdline "
            "| cut -c1-160)\"; done; echo ---; "
            "grep -A12 -i 'Session: saved' /home/%(c)s/.config/ksmserverrc 2>/dev/null "
            "| head -40" % {"c": s.chi, "p": PROGRAMMA}, 40)
        d["chi_lo_riapre"] = (t or "").strip()
        ev.append(s.salva_testo("rientro-programma-riaperto.txt", t or ""))
        print("   ⚠ %s riaperto al rientro:\n%s" % (PROGRAMMA, (t or "")[:900]), flush=True)
    return d, ev


def rimetti_in_piedi(s):
    """Una sessione viva col programma aperto, per rifare un'uscita."""
    r, _ev = rientra(s)
    if not r.get("entrato"):
        return False, "non rientro: %s" % r.get("perche")
    return apri_programma(s)


def uscita(s, gesto, nome, **k):
    """Un'uscita guardata e giudicata; se il filo e' caduto prima della fine
    (BLOCKED), la si rifa' UNA volta da una sessione nuova."""
    for tentativo in (1, 2):
        d, ev = esci_e_guarda(s, gesto, nome="%s-%d" % (nome, tentativo), **k)
        e, p = giudica_uscita(d)
        if not (e == S.BLOCKED and d.get("filo_caduto")) or tentativo == 2:
            break
        print("   ⚠ %s: %s — rifaccio" % (nome, p), flush=True)
        ok, m = rimetti_in_piedi(s)
        if not ok:
            return d, ev, S.BLOCKED, p + " · e non ho potuto rifarla: " + m
    return d, ev, e, p


def corpo(o, E):
    with S.Sessione(o, "021", E) as s:
        desktop, gesto = s.sc.gesto_esci()
        if o.gesto:
            desktop, gesto = "%s (gesto dato a mano)" % o.scatola, o.gesto
        if not gesto:
            raise S.Bloccata("non so come si dice «Esci» in %s" % s.sc.contenitore)
        print("   «Esci» (%s): %s" % (desktop, gesto), flush=True)
        ok, m = s.entra()
        if not ok:
            raise S.Bloccata(m)
        ok, m = apri_programma(s)
        if not ok:
            raise S.Bloccata(m)
        png, dove = s.foto("prima-di-esci")
        ev0 = [dove] if dove else []

        # ── la passata sana ───────────────────────────────────────────────
        d, ev, esito, perche = uscita(s, gesto, "esci")
        oss = ("finita=%s dopo %s s · modulo=%s · «%s» · processi dopo: %s · nascite=%d"
               % (d.get("finita"), d.get("finita_s"), d.get("modulo"),
                  (d.get("frase") or "")[:70],
                  " ".join(v.split("|")[0] for v in d.get("tutti") or []) or "nessuno",
                  len(d.get("nascite") or [])))
        print("   uscita: %s — %s" % (esito, oss), flush=True)
        ev.append(s.salva_testo("processi-dopo-esci.txt", d.get("tutti") or ["(nessuno)"]))
        if esito == S.PASS:
            r, ev2 = rientra(s)
            esito, p2 = giudica_rientro(r)
            perche = perche + " · " + p2 + (" (⚠ il modulo non c'era: ricaricata)"
                                             if r.get("ricaricata") else "")
            ev += ev2
            oss += " · rientro: %s" % p2
        E.metti("F-021", esito, perche,
                atteso="«Esci» ⇒ finita, programmi chiusi, pagina al modulo con «la sessione "
                       "e' terminata», nessuna nascita in %.0f s; il rientro apre una "
                       "sessione NUOVA e pulita" % GUARDIA_S,
                osservato=oss, evidenze=ev0 + ev + [s.salva_console()],
                gesto=gesto)

        if not o.guasto:
            return
        # serve una sessione viva da cui partire
        if not (s.stato().get("sessione")):
            r, _ev = rientra(s)
            if not r.get("entrato"):
                E.guasto("F-021", None, "nessuna sessione viva per il guasto: %s"
                         % r.get("perche"))
                return
        # ── G1 «Esci a vuoto» ─────────────────────────────────────────────
        d1, _ev = esci_e_guarda(s, GESTO_A_VUOTO, tetto_finita=15, nome="guasto-a-vuoto")
        e1, p1 = giudica_uscita(d1)
        print("   G1 a vuoto: %s — %s" % (e1, p1[:200]), flush=True)
        # ── G2 «rientro dentro la guardia» ────────────────────────────────
        d2, _ev, e2, p2 = uscita(s, gesto, "guasto-rientro", rientra_subito=True)
        rinata = e2 == S.FAIL and bool(d2.get("nascite"))
        print("   G2 rientro subito (%s): %s — %s" % (d2.get("rientro_guasto"), e2, p2[:200]),
              flush=True)
        if not d2.get("finita") or "rientro_guasto" not in d2:
            E.guasto("F-021", None, "G2 non innestato: l'uscita vera non e' finita o "
                     "la pagina non e' tornata al modulo (%s)" % p2[:200])
            return
        E.guasto("F-021", e1 == S.FAIL and rinata,
                 "G1 Esci a vuoto ⇒ %s (%s) · G2 rientro dentro la guardia ⇒ %s (%s)"
                 % (e1, p1[:120], e2, p2[:120]))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, extra=lambda a: a.add_argument(
        "--gesto", default="", help="un altro gesto «Esci» (diagnosi: es. XFCE senza "
        "--fast, che salva la sessione come il dialogo del menu)")))
