#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f009 — F-009 DISPOSIZIONE, ACCENTI, AltGr (disposizione italiana)

    python3 15-f009-accenti-e-altgr.py --scatola gnome --browser chrome [--guasto]

⭐ CHE COSA PROMETTE IL PRODOTTO (verificato nel codice, 24 set 2026):
   · la pagina dichiara la disposizione in `ATTACCA` dalla LINGUA del browser
     (`pagina.html` `disposizione()`: `navigator.language` «it-IT» ⇒ «it»);
   · le lettere viaggiano come LETTERE (`LETTERA`, il carattere di `ev.key`);
     Maiusc, BlocMaiusc e AltGr non partono: «servono a fare la lettera»
     (`cl_su_keydown`, SPECIFICHE §7.3);
   · il server cerca il carattere nella disposizione della sessione
     (`tastiera.c` `tastiera_posizioni_per`, tutti i livelli) e ne preme i
     tasti; la disposizione negoziata la mette nella sessione (`input.c`
     `input_disposizione`: GSettings su GNOME, keymap della tastiera virtuale
     su wlroots);
   · ⛔ un carattere che la disposizione NON ha non esce e il server lo SCRIVE
     nel registro («U+XXXX non e' producibile con la disposizione …»): mai una
     lettera diversa, mai un silenzio (SPECIFICHE §7.3, RCP §7.3).
   ⇒ Con «it» (xkb `it` basic): è à ò ù (livello 1), é ç ° § (Maiusc),
     @ # [ ] € (AltGr) SI scrivono; «È» NON c'e' su nessun tasto ⇒ l'atteso e'
     che non esca E che il registro lo dichiari (non e' un FAIL).

⭐ COME: il browser in italiano (Firefox `intl.accept_languages`, Chrome
   `Emulation.setUserAgentOverride acceptLanguage`), si entra, e nella scena
   nota (`15-g2-scena.py`, campo «a» in firefox-esr dentro la sessione) si
   battono con TASTI VERI i caratteri come li manda una tastiera italiana:
   `key` = il carattere, `code` = la posizione (BracketLeft, Semicolon, Quote,
   Backslash, KeyE…), preceduti da Maiusc / AltGr / BlocMaiusc dove servono.
   ⚠ LIMITE DICHIARATO: WebDriver (Marionette) non ha AltGraph ne' BlocMaiusc:
     con Firefox quelle due pressioni non si mandano, e arriva solo il
     carattere che la tastiera vera avrebbe dato (la pagina lo manda comunque
     come LETTERA: e' lo stesso percorso).  Con Chrome (CDP) si mandano.
   Il giudizio: il valore del campo LETTO NELLA SESSIONE, e per «È» la riga del
   registro del server; la foto si salva.

⭐ E LE IMPOSTAZIONI DELL'UTENTE NON SI TOCCANO (D-015, decisione dell'utente
   del 25 set 2026, su tutti i desktop): la disposizione negoziata vale per la
   SESSIONE, non si scrive dove l'utente la ritroverebbe entrando al monitor.
   Si leggono DAL DISCO, come l'utente, prima dell'accesso e dopo la passata:
   `org.gnome.desktop.input-sources` (sources, mru-sources, current,
   xkb-options) del dconf dell'utente — letto con un profilo che ha SOLO
   `user-db:user`, cioe' `~/.config/dconf/user` e nient'altro — e l'impronta
   di `~/.config/kxkbrc`.  Devono essere quelli di PRIMA, o F-009 e' rosso
   anche con tutte le lettere giuste.

GUASTO (--guasto, stessa sessione), due innesti e un verdetto solo:
   1. una SCRITTURA PERSISTENTE simulata — `sources` = de nel dconf
      dell'utente (col suo profilo) e una riga di commento in fondo a
      `~/.config/kxkbrc` — ⇒ il giudice delle impostazioni deve dare rosso;
   2. il browser torna in INGLESE (en-US) e si RIATTACCA: la pagina dichiara
      «us», la sessione prende la disposizione americana, e gli accenti non ci
      sono ⇒ il giudice delle lettere deve dare rosso.
   Visto = tutt'e due rossi.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G2 = S._carica("g2scena", os.path.join(S.QUI, "15-g2-scena.py"))

FUNZIONI = ("F-009",)
#   carattere, code della posizione (tastiera italiana), keyCode, modificatore
TASTIERA_IT = (
    ("è", "BracketLeft", 219, None), ("à", "Quote", 222, None),
    ("ò", "Semicolon", 186, None), ("ù", "Backslash", 220, None),
    ("é", "BracketLeft", 219, "Shift"), ("ç", "Semicolon", 186, "Shift"),
    ("°", "Quote", 222, "Shift"), ("§", "Backslash", 220, "Shift"),
    ("@", "Semicolon", 186, "AltGraph"), ("#", "Quote", 222, "AltGraph"),
    ("[", "BracketLeft", 219, "AltGraph"), ("]", "BracketRight", 221, "AltGraph"),
    ("€", "KeyE", 69, "AltGraph"),
    ("È", "BracketLeft", 219, "CapsLock"),
)
DICHIARATI_NON_SCRIVIBILI = {"È"}     # xkb `it` basic non ha Egrave su nessun livello
SCRIVIBILI = "".join(c for c, _k, _v, _m in TASTIERA_IT if c not in DICHIARATI_NON_SCRIVIBILI)
TUTTI = "".join(c for c, _k, _v, _m in TASTIERA_IT)
ATTESA_S = 8.0
PRODUCIBILE = re.compile(r"U\+([0-9A-Fa-f]{4,6}) non e' producibile con la disposizione ([^:]*)")
IN_VIGORE = re.compile(r"disposizione in vigore[^:]*: (.*)$")

# ── D-015: le impostazioni dell'utente, lette DAL DISCO come le leggerebbe lui
CHIAVI_IS = ("sources", "mru-sources", "current", "xkb-options")
LEGGI_IMPOSTAZIONI = (
    "export HOME=/home/%(c)s; p=$(mktemp); echo user-db:user > \"$p\"; "
    "for k in " + " ".join(CHIAVI_IS) + "; do "
    "v=$(DCONF_PROFILE=\"$p\" gsettings get org.gnome.desktop.input-sources \"$k\" "
    "2>/dev/null) || v='(non letta)'; echo \"is.$k=$v\"; done; rm -f \"$p\"; "
    "if [ -f \"$HOME/.config/kxkbrc\" ]; then "
    "echo \"kxkbrc=$(sha256sum < \"$HOME/.config/kxkbrc\" | cut -c1-16)\"; "
    "else echo kxkbrc=assente; fi")
SCRIVI_GUASTO = (
    "export HOME=/home/%(c)s; p=$(mktemp); echo user-db:user > \"$p\"; "
    "DCONF_PROFILE=\"$p\" gsettings set org.gnome.desktop.input-sources sources "
    "\"[('xkb','de')]\" 2>&1 | head -2; rm -f \"$p\"; mkdir -p \"$HOME/.config\"; "
    "echo '# 15-f009 guasto: scrittura persistente simulata' >> \"$HOME/.config/kxkbrc\"; "
    "echo scritto")


def leggi_impostazioni(testo):
    """{chiave: valore} dalle righe «nome=valore»; None se non c'e' niente."""
    d = {}
    for r in (testo or "").splitlines():
        if "=" in r and (r.startswith("is.") or r.startswith("kxkbrc=")):
            k, v = r.split("=", 1)
            d[k] = v.strip()
    return d or None


def giudica_impostazioni(prima, dopo):
    """(esito, frase): le impostazioni dell'utente devono essere quelle di PRIMA."""
    if prima is None or dopo is None:
        return S.BLOCKED, "le impostazioni dell'utente non si sono potute leggere (%s)" % (
            "prima" if prima is None else "dopo")
    cambiate = ["%s: %s → %s" % (k, prima.get(k, "?"), dopo.get(k, "?"))
                for k in sorted(set(prima) | set(dopo)) if prima.get(k) != dopo.get(k)]
    if cambiate:
        return S.FAIL, ("⛔ IMPOSTAZIONI DELL'UTENTE TOCCATE (D-015): %s" % "; ".join(cambiate))
    return S.PASS, "impostazioni dell'utente intatte (%s)" % ", ".join(
        "%s=%s" % (k, v) for k, v in sorted(prima.items()))


def impostazioni(s):
    c, t = s.come_utente("sh -c %s" % S._q(LEGGI_IMPOSTAZIONI % {"c": s.chi}), 60)
    return leggi_impostazioni(t) if c == 0 else None


def sequenza():
    p = []
    for c, code, vk, mod in TASTIERA_IT:
        tasto = G2.premi(c, code, vk)
        if mod == "CapsLock":
            p += G2.premi("CapsLock") + tasto + G2.premi("CapsLock")
        elif mod:
            p += G2.col(mod, tasto)
        else:
            p += tasto
    return p


def dichiarati(righe):
    """{carattere: disposizione} dalle righe «non e' producibile» del registro."""
    d = {}
    for r in righe:
        m = PRODUCIBILE.search(r)
        if m:
            d[chr(int(m.group(1), 16))] = m.group(2).strip()
    return d


def giudica(st, righe):
    """(esito, frase) dal valore del campo e dalle righe del registro."""
    if not st or st.get("a") is None:
        return S.BLOCKED, "la scena non ha detto il valore del campo"
    a = st["a"]
    dic = dichiarati(righe)
    if a == TUTTI:
        return S.PASS, "a=%r (anche «È» e' uscita)" % a
    if a == SCRIVIBILI:
        mancanti_dichiarati = [c for c in DICHIARATI_NON_SCRIVIBILI if c in dic]
        if len(mancanti_dichiarati) == len(DICHIARATI_NON_SCRIVIBILI):
            return S.PASS, ("a=%r; «%s» non scrivibile con «%s» ed e' DICHIARATO nel registro"
                            % (a, "".join(mancanti_dichiarati), dic[mancanti_dichiarati[0]]))
        return S.FAIL, ("a=%r: «%s» e' sparito IN SILENZIO (nessuna riga «non e' producibile»)"
                        % (a, "".join(DICHIARATI_NON_SCRIVIBILI)))
    mancano = [c for c in SCRIVIBILI if c not in a]
    return S.FAIL, ("a=%r invece di %r · mancano %s · dichiarati non producibili dal server: %s"
                    % (a, SCRIVIBILI, "".join(mancano) or "-",
                       ", ".join("%s (%s)" % kv for kv in dic.items()) or "nessuno"))


def certifica():
    guai = []

    def prova(cosa, vero, det=""):
        print("   %s %s%s" % ("⭐ ok " if vero else "⛔ NO ", cosa, (" — " + det) if det else ""))
        if not vero:
            guai.append(cosa)
    riga_e = ("21:00:00.000 tastiera [c15009u1] U+00C8 non e' producibile con la disposizione "
              "it [Italian]: NON mandato niente (RCP.md §7.3)")
    riga_u = riga_e.replace("U+00C8", "U+00E8").replace("it [Italian]", "us [English (US)]")
    prova("lettura del registro", dichiarati([riga_e]) == {"È": "it [Italian]"},
          repr(dichiarati([riga_e])))
    prova("tutti scritti, È dichiarata ⇒ PASS", giudica({"a": SCRIVIBILI}, [riga_e])[0] == S.PASS)
    prova("anche È scritta ⇒ PASS", giudica({"a": TUTTI}, [])[0] == S.PASS)
    prova("È sparita in silenzio ⇒ FAIL", giudica({"a": SCRIVIBILI}, [])[0] == S.FAIL)
    prova("con «us» (è non producibile) ⇒ FAIL",
          giudica({"a": SCRIVIBILI.replace("è", "")}, [riga_e, riga_u])[0] == S.FAIL)
    prova("una lettera diversa ⇒ FAIL", giudica({"a": SCRIVIBILI.replace("@", "\"")}, [riga_e])[0]
          == S.FAIL)
    prova("niente campo ⇒ BLOCKED", giudica(None, [])[0] == S.BLOCKED)
    seq = sequenza()
    prova("la sequenza porta ogni carattere", all(any(p[1] == c for p in seq)
                                                  for c in TUTTI))
    prova("AltGr giu' prima di «@»", seq[seq.index(("giu", "@", "Semicolon", 186)) - 1][1]
          == "AltGraph")
    # D-015
    uscita = ("is.sources=@a(ss) []\nis.mru-sources=@a(ss) []\nis.current=uint32 0\n"
              "is.xkb-options=@as []\nkxkbrc=assente\n")
    pr = leggi_impostazioni(uscita)
    prova("lettura delle impostazioni", pr and pr["is.sources"] == "@a(ss) []"
          and pr["kxkbrc"] == "assente", repr(pr))
    prova("impostazioni uguali ⇒ PASS", giudica_impostazioni(pr, dict(pr))[0] == S.PASS)
    scritta = dict(pr, **{"is.sources": "[('xkb', 'it')]"})
    prova("input-sources scritta nell'utente ⇒ FAIL",
          giudica_impostazioni(pr, scritta)[0] == S.FAIL)
    prova("kxkbrc dell'utente nato ⇒ FAIL",
          giudica_impostazioni(pr, dict(pr, kxkbrc="0123456789abcdef"))[0] == S.FAIL)
    prova("non lette ⇒ BLOCKED", giudica_impostazioni(None, pr)[0] == S.BLOCKED)
    prova("niente da leggere ⇒ None", leggi_impostazioni("sh: errore") is None)
    print("⛔ CERTIFICAZIONE FALLITA" if guai else "⭐ CERTIFICATO")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
def prova_una(s, sc, mp, nome):
    """Batte la sequenza; torna (esito, frase, evidenze, disposizioni in vigore)."""
    segno = s.segno_registro()
    st, foto, saltati, perche = G2.batti(
        s, sc, mp, sequenza(), nome, lambda q: q.get("a") in (TUTTI, SCRIVIBILI), ATTESA_S,
        saltabili=("AltGraph", "CapsLock"))
    righe = s.registro_da(segno) if segno is not None else []
    ev = [x for x in (foto, s.salva_testo("server-%s.txt" % nome, righe)) if x]
    if perche:
        return S.BLOCKED, perche, ev, []
    e, m = giudica(st, righe)
    if saltati:
        m += " · ⚠ non mandati da questo browser: %s" % ", ".join(
            sorted({x[1] for x in saltati}))
    return e, m, ev, righe


def disposizione_in_vigore(s, segno):
    righe = s.registro_da(segno) if segno is not None else []
    v = [IN_VIGORE.search(r).group(1).strip() for r in righe if IN_VIGORE.search(r)]
    rip = [r for r in righe if "RIPIEGO" in r and "disposizione" in r]
    return v[-1] if v else "?", rip


def corpo(o, E):
    with S.Sessione(o, "009", E) as s:
        segno0 = s.segno_registro()
        # D-015: le impostazioni dell'utente PRIMA che la sessione lo veda
        prima = impostazioni(s)
        print("   impostazioni dell'utente, prima: %s" % prima, flush=True)
        sc, mp, geo, dove = G2.prepara(s, o.porte_base + 7, lingua="it-IT")
        disp, rip = disposizione_in_vigore(s, segno0)
        print("   disposizione in vigore: %s%s" % (disp, " · ⚠ " + rip[-1][:200] if rip else ""),
              flush=True)
        e, m, ev, _r = prova_una(s, sc, mp, "accenti-sana")
        if e == S.FAIL:
            print("   ⚠ rosso (%s): lo rifaccio per confermarlo" % m, flush=True)
            e2, m2, ev2, _r = prova_una(s, sc, mp, "accenti-sana-bis")
            ev += ev2
            if e2 == S.PASS:
                e, m = S.PASS, "⚠ ROSSO al primo tentativo (%s), verde al secondo: %s" % (m, m2)
            else:
                m = "rosso due volte: %s · %s" % (m, m2)
        m = "[disposizione in vigore: %s%s] %s" % (
            disp, "; RIPIEGO: " + rip[-1].split("] ", 1)[-1][:160] if rip else "", m)
        # D-015: e DOPO la passata, dal disco, le stesse di prima
        dopo = impostazioni(s)
        ei, mi = giudica_impostazioni(prima, dopo)
        p = s.salva_testo("impostazioni-utente.txt",
                          "prima: %r\ndopo:  %r\n%s" % (prima, dopo, mi))
        if p:
            ev.append(p)
        m += " · " + mi
        if ei == S.FAIL or (ei == S.BLOCKED and e == S.PASS):
            e = ei
        E.metti("F-009", e, m, atteso="«%s» nel campo; «È» non scrivibile e dichiarata; "
                "impostazioni dell'utente (input-sources, kxkbrc) quelle di prima"
                % SCRIVIBILI, osservato=m, evidenze=([dove] if dove else []) + ev
                + ([s.salva_console()] if e != S.PASS else []))
        if o.guasto:
            # innesto 1 (D-015): una scrittura persistente simulata nell'utente
            _c, t = s.come_utente("sh -c %s" % S._q(SCRIVI_GUASTO % {"c": s.chi}), 60)
            dopo_g = impostazioni(s)
            eig, mig = giudica_impostazioni(prima, dopo_g)
            print("   GUASTO 1, scrittura persistente simulata (%s): %s"
                  % ((t or "").strip().replace("\n", " | ")[-120:], mig), flush=True)
            if eig == S.BLOCKED:
                E.guasto("F-009", None, "innesto 1 (scrittura persistente simulata) non "
                         "guardabile: %s" % mig)
                return
            visto_1 = eig == S.FAIL
            # innesto 2: il browser in inglese
            segno1 = s.segno_registro()
            print("   GUASTO: %s, e si riattacca" % G2.metti_lingua(s.g, "en-US"), flush=True)
            ok, mm = s.entra()
            nl = s.g.js("return navigator.language") if ok else "?"
            if not ok or nl != "en-US":
                E.guasto("F-009", None, "il riattacco in inglese non e' riuscito: %s (lingua %s)"
                         % (mm, nl))
                return
            disp_g, _rip = disposizione_in_vigore(s, segno1)
            eg, mg, evg, _r = prova_una(s, sc, mp, "accenti-guasto")
            visto_2 = None if eg == S.BLOCKED else eg == S.FAIL
            E.guasto("F-009", None if visto_2 is None else (visto_1 and visto_2),
                     "innesto 1, scrittura persistente simulata: %s — %s · innesto 2, "
                     "browser in en-US, disposizione in vigore «%s»: %s"
                     % ("ROSSO (visto)" if visto_1 else "⛔ NON visto", mig, disp_g, mg),
                     atteso="rosso tutt'e due: le impostazioni dell'utente cambiate; con "
                     "«us» gli accenti non ci sono", osservato=mig + " · " + mg,
                     evidenze=evg)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
