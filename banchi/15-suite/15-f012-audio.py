#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f012 — F-012 AUDIO: un'applicazione vera suona, il BROWSER sente suono e non silenzio

    python3 15-f012-audio.py --scatola kde --browser chrome [--guasto]

LA SCENA.  Dentro la sessione dell'inquilino gira un'applicazione vera che
suona: `pw-play` (client PipeWire come un lettore qualunque) di un tono puro a
440 Hz, ampiezza 0,5, sul sink PREDEFINITO — ⛔ senza `--target`: un programma
vero non sa che il sink si chiama «remotix», e se il predefinito non fosse
quello del prodotto l'utente non sentirebbe niente.

IL GIUDIZIO — un campo misurato NEL BROWSER, non un contatore di pacchetti.
  L'orecchio di `15-g4-comune.py`: un `AnalyserNode` messo come passante fra i
  blocchi che la pagina programma e l'`AudioDestinationNode` (cioe' quel che va
  all'altoparlante).  Livello RMS e frequenza di picco ogni 100 ms.
  ⭐ Il gesto: il contesto della pagina nasce `suspended` senza un gesto
  dell'utente; il banco fa un CLIC VERO sulla tela (evento fidato), come
  l'utente.  Si scrive se il contesto era sospeso e se il clic l'ha svegliato.

F-012  atteso: su 6 s, udibile >= 80 % dei campioni (RMS > −40 dBFS a contesto
       running), picco a 440 ± 12 Hz per >= 80 % degli udibili;
       e I5 (SPECIFICHE §10, `src/suono.c` `alza()` chiamato a OGNI
       collegamento, `figlio.c`): al collegamento il sink predefinito e' «remotix»
       al volume 1.00 e non muto; se l'utente nella sessione lo porta a 0.10 e
       muto, il browser sente SILENZIO (il cursore governa: `monitor.channel-
       volumes`), e al RIATTACCO il volume e' di nuovo 1.00, non muto, e il tono
       si risente.

GUASTO (stessa sessione, dopo la passata sana):
  g1  l'applicazione si ZITTISCE (pw-play ucciso) ⇒ la stessa lettura deve dire
      silenzio (FAIL);
  g2  i campioni veri della passata sana giudicati contro un'ATTESA SBAGLIATA
      (660 Hz) ⇒ deve dire FAIL.
  Visto = tutt'e due rossi.
"""
import base64
import importlib.util as _iu
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

_s = _iu.spec_from_file_location("g4", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    "15-g4-comune.py"))
G4 = _iu.module_from_spec(_s)
_s.loader.exec_module(G4)

FUNZIONI = ("F-012",)
TONO_HZ = 440
FINESTRA_S = 6.0
WAV = "c15-tono-440.wav"


def certifica():
    return G4.certifica_comune()


def prepara_tono(s):
    b = base64.b64encode(G4.onda_wav(TONO_HZ, 20.0)).decode()
    # ⚠ il file e' ~3,8 MB: in base64 ~5 MB, troppo per una riga di comando.
    #   ⇒ lo si scrive dentro la scatola a pezzi.
    h = "/home/%s/%s" % (s.chi, WAV)
    s.sc.dentro("rm -f %s.b64" % h, 30)
    pezzo = 60000
    for i in range(0, len(b), pezzo):
        c, t = s.sc.dentro("printf '%%s' '%s' >> %s.b64" % (b[i:i + pezzo], h), 30)
        if c != 0:
            return False, "il tono non si scrive: %s" % t[-200:]
    c, t = s.sc.dentro("base64 -d %s.b64 > %s && rm -f %s.b64 && chown %s: %s && ls -l %s"
                       % (h, h, h, s.chi, h, h), 30)
    return c == 0, t.strip()[-200:]


def prepara_tono_ffmpeg(s):
    """⭐ Piu' rapido: il tono lo scrive ffmpeg DENTRO la scatola, con un'ampiezza
    esatta (`aevalsrc`, non `sine` che attenua da se' — la lezione di C5)."""
    h = "/home/%s/%s" % (s.chi, WAV)
    c, t = s.sc.dentro(
        "ffmpeg -loglevel error -y -f lavfi -i "
        "\"aevalsrc=0.5*sin(2*PI*%d*t)|0.5*sin(2*PI*%d*t):s=48000:d=20\" "
        "-c:a pcm_s16le %s && chown %s: %s && ls -l %s" % (TONO_HZ, TONO_HZ, h, s.chi, h, h), 60)
    return c == 0, t.strip()[-200:]


def suona(s):
    return s.nella_sessione("while true; do pw-play /home/%s/%s || sleep 1; done # c15tono"
                            % (s.chi, WAV))


def zittisci(s):
    s.sc.dentro("pkill -u %s -f '[c]15tono'; pkill -u %s -x pw-play; sleep 0.3; "
                "pgrep -u %s -x pw-play || echo zitto" % (s.chi, s.chi, s.chi), 30)


def wpctl(s, cosa):
    c, t = s.come_utente("wpctl %s" % cosa, 30)
    return t.strip()


def volume(s):
    """(nome del sink predefinito, volume float | None, muto bool, testo)."""
    t = wpctl(s, "get-volume @DEFAULT_AUDIO_SINK@")
    ins = wpctl(s, "inspect @DEFAULT_AUDIO_SINK@")
    m = re.search(r'node\.name = "([^"]+)"', ins)
    v = re.search(r"Volume:\s*([0-9.]+)", t)
    riga = next((r.strip() for r in t.splitlines() if "Volume:" in r), "(nessuna riga Volume: %s)"
                % t.replace("\n", " ")[-120:])
    return (m.group(1) if m else None, float(v.group(1)) if v else None, "MUTED" in t, riga)


def ascolta(s, secondi, attesa_hz=TONO_HZ, **k):
    t0 = G4.ora_pagina(s.g)
    time.sleep(secondi)
    r = G4.leggi_orecchio(s.g, t0) or {}
    camp = r.get("campioni") or []
    e, d, num = G4.giudica_suono(camp, attesa_hz, **k)
    return e, d, num, r


def sveglia(s, note):
    """Aspetta il contesto audio della pagina e fa il clic vero."""
    stato, conti = G4.aspetta_contesto(s.g, 30)
    if stato is None:
        note.append("la pagina non ha creato un AudioContext in 30 s (conti %s)" % (conti,))
        return False
    note.append("contesto nato «%s»" % stato)
    note.append(G4.clic_vero(s, 0.62, 0.55))
    time.sleep(1.5)
    stato2, _ = G4.aspetta_contesto(s.g, 5)
    note.append("dopo il clic «%s»" % stato2)
    return True


def entra_con_orecchio(s):
    """La pagina, l'orecchio PRIMA dell'accesso (il contesto audio puo' nascere
    subito dopo l'ammissione, se la sessione sta gia' suonando), poi l'accesso."""
    ok, m = s.pr.apri()
    if not ok:
        return False, "la pagina non si apre: " + m
    ok, m = G4.metti_orecchio(s.g)
    if not ok:
        return False, m
    ok, m = s.entra(apri=False)
    if not ok:
        return False, "senza sessione non c'e' audio da guardare: " + m
    return True, m


def corpo(o, E):
    sess = S.Sessione(o, "012", E)
    G4.robusta(sess.sc)
    with sess as s:
        ok, m = entra_con_orecchio(s)
        if not ok:
            raise S.Bloccata(m)
        ok, m = prepara_tono_ffmpeg(s)
        if not ok:
            print("   ⚠ il tono con ffmpeg: %s — lo scrive il banco" % m, flush=True)
            ok, m = prepara_tono(s)
        if not ok:
            raise S.Bloccata("il tono non si prepara nella scatola: " + m)
        segno = s.segno_registro()
        c, t = suona(s)
        if c != 0:
            raise S.Bloccata("pw-play non parte nella sessione: " + t[-200:])
        note = []
        if not sveglia(s, note):
            r = G4.leggi_orecchio(s.g) or {}
            conti = r.get("conti")
            nome, vol, muto, tv = volume(s)
            ev = [s.salva_testo("server-f012.txt", s.registro_da(segno) if segno else []),
                  s.salva_console()]
            if conti and (conti.get("ricevuti") or 0) > 0:
                raise S.Bloccata("la pagina riceve audio (%s) ma l'orecchio non vede il contesto"
                                 % conti)
            E.metti("F-012", S.FAIL, "l'applicazione suona e alla pagina non arriva audio: "
                    "nessun AudioContext in 30 s (sink predefinito %s, %s)" % (nome, tv),
                    atteso="tono a 440 Hz nel browser", osservato="; ".join(note), evidenze=ev)
            return
        time.sleep(1.0)
        e1, d1, num1, r1 = ascolta(s, FINESTRA_S)
        campioni_sani = r1.get("campioni") or []
        ev = [G4.salva_json(o, "f012-orecchio-sano.json", r1)]
        nome, vol, muto, tv = volume(s)
        i5 = ["al collegamento: sink predefinito «%s», %s" % (nome, tv)]
        male = []
        if e1 != "PASS":
            male.append("il tono: " + d1)
        if nome != "remotix":
            male.append("I5: il sink predefinito e' «%s», non «remotix»" % nome)
        if vol is None or abs(vol - 1.0) > 0.005 or muto:
            male.append("I5: al collegamento il volume non e' al massimo: %s" % tv)

        # I5, seconda meta': l'utente abbassa e zittisce ⇒ silenzio; riattacco ⇒ massimo
        wpctl(s, "set-volume @DEFAULT_AUDIO_SINK@ 0.10")
        wpctl(s, "set-mute @DEFAULT_AUDIO_SINK@ 1")
        time.sleep(1.5)
        _n, vb, mb, tvb = volume(s)
        e2, d2, num2, r2 = ascolta(s, 3.0)
        ev.append(G4.salva_json(o, "f012-orecchio-muto.json", r2))
        i5.append("abbassato e zittito nella sessione (%s) ⇒ %s" % (tvb, d2))
        if e2 == "PASS" or (num2.get("udibili") or 0) > 0.2:
            male.append("I5: con il sink muto a 0.10 il browser SENTE ancora (il cursore "
                        "della sessione non governa): %s" % d2)
        # il riattacco: la pagina di nuovo, utente e parola, stessa sessione
        ok, m = entra_con_orecchio(s)
        if not ok:
            male.append("I5: il riattacco non riesce: %s" % m)
        else:
            note2 = []
            if ok and sveglia(s, note2):
                time.sleep(1.0)
                _n, vr, mr, tvr = volume(s)
                e3, d3, num3, r3 = ascolta(s, 4.0)
                ev.append(G4.salva_json(o, "f012-orecchio-riattacco.json", r3))
                i5.append("al riattacco: %s ⇒ %s" % (tvr, d3))
                if vr is None or abs(vr - 1.0) > 0.005 or mr:
                    male.append("I5: al riattacco il volume NON torna al massimo: %s" % tvr)
                if e3 != "PASS":
                    male.append("I5: al riattacco il tono non si risente: %s" % d3)
            else:
                male.append("I5: dopo il riattacco la pagina non suona (%s %s)" % (m, note2))
        # evidenze del server
        ev.append(s.salva_testo("server-f012.txt", s.registro_da(segno) if segno else []))
        ev.append(s.salva_console())
        foto, dove = s.foto("f012-fine")
        if dove:
            ev.append(dove)
        oss = "%s · %s · %s" % ("; ".join(note), d1, " | ".join(i5))
        atteso = ("tono 440 Hz udibile nel browser (>=80%% dei campioni, picco 440±12 Hz); "
                  "I5: sink «remotix» a 1.00 non muto al collegamento, muto ⇒ silenzio, "
                  "riattacco ⇒ di nuovo 1.00 e tono")
        if male:
            E.metti("F-012", S.FAIL, " · ".join(male), atteso=atteso, osservato=oss, evidenze=ev,
                    numeri=num1)
        else:
            E.metti("F-012", S.PASS, "tono sentito nel browser: %s; I5 regge" % d1,
                    atteso=atteso, osservato=oss, evidenze=ev, numeri=num1)

        if o.guasto:
            # g2 prima (non tocca la scena): l'attesa sbagliata sui campioni veri
            eg2, dg2, _ = G4.giudica_suono(campioni_sani, 660)
            # g1: l'applicazione si zittisce
            zittisci(s)
            time.sleep(1.5)
            eg1, dg1, _n1, rg1 = ascolta(s, 4.0)
            evg = [G4.salva_json(o, "f012-orecchio-guasto.json", rg1)]
            if not campioni_sani:
                E.guasto("F-012", None, "nessun campione sano su cui giudicare l'attesa sbagliata")
            else:
                visto = eg1 == "FAIL" and eg2 == "FAIL"
                E.guasto("F-012", visto,
                         "applicazione zittita ⇒ %s «%s» · attesa 660 Hz sui campioni veri ⇒ %s «%s»"
                         % (eg1, dg1, eg2, dg2), evidenze=evg)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
