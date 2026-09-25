#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-attore — UN UTENTE SIMULATO della fase 16 (fasi/16-stress-e-capacita.md §4, §5, §7)

    python3 16-attore.py --scatola gnome|kde|xfce|lxqt --utente N (1..16) \\
        --wayland wayland-K --dir DIR --seme S \\
        [--largo 3840 --alto 2160] [--porte-base P] [--video URL] [--host 192.168.0.2]
    python3 16-attore.py --certifica

Gira SUL SERVER come nicfio (e' lui a mettere l'ambiente dei banchi 15: labwc
`--wayland`, `sudo podman exec` locale).  Un processo = una persona:

  browser   N dispari Firefox (Marionette, porta P), N pari Chrome (CDP, porta P+1)
  profilo   N%4: 1 A navigazione · 2 B file manager · 3 C terminale · 0 D video 4K
  inquilino c16<NNN>u<N> (es. c16001u1), parola casuale, creato qui e SGOMBERATO
            sempre all'uscita (fine normale, SIGTERM, SIGINT, eccezione).
            ⛔ Una sola prova d'accesso, con la parola giusta: mai un ban.

  1. crea l'inquilino, accende il browser nel suo labwc, prepara la casa;
  2. ENTRA: misura accesso (invio → «Ammesso») e primo fotogramma (invio →
     `dipinti > 0`), poi guarda che il desktop non sia degenere ⇒ nascita.json;
  3. lancia l'applicazione del profilo DENTRO la sessione (16-lavori.py);
  4. lavora in ciclo fino a SIGTERM, con input VERO dal browser e il ritmo
     estratto da random.Random(«seme:utente») — ripetibile fra le campagne.

  DIR/utente-NN/stato.jsonl   SOLO righe di stato, ogni 5 s, nello schema di
                              16-classifica.py: t, profilo, inquilino, conti
                              (cumulativi: consegnati dipinti salt buchi tard
                              ricevuti suonati BUCHI mancati), diario (la riga
                              «audio: …» della pagina COM'E'), giro
                              (REMOTIX.giro: visti, campioni), input
                              [{ok, latenza_ms, azione}], blocco_max_ms, lavoro,
                              caduta, errori; e in piu' diario_letto, delta,
                              azioni, verifiche, dettagli_lavoro, eventi
  DIR/utente-NN/eventi.jsonl  inizio, nascita, applicazione, foto, errore, fine
  DIR/utente-NN/nascita.json  {accesso_ms, primo_fotogramma_ms (ore in ms
                              dall'epoca), nascita_ms (la durata), esito "ok"|…}
  SIGUSR1                     foto piena della tela in DIR/utente-NN/foto-<t>.png
  all'uscita                  console-<browser>.txt e registro-pagina.txt

Codice d'uscita: 0 fermato da SIGTERM/SIGINT dopo aver lavorato · 1 l'accesso o
l'avvio non sono riusciti · 2 errore del banco.
"""
import argparse
import importlib.util as _iu
import io
import json
import math
import os
import random
import re
import secrets
import signal
import sys
import time
import traceback

QUI = os.path.dirname(os.path.abspath(__file__))
BANCHI = os.path.dirname(QUI)
SUITE = os.path.join(BANCHI, "15-suite")
DESKTOP = ("gnome", "kde", "xfce", "lxqt")


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


L = _carica("lavori16", os.path.join(QUI, "16-lavori.py"))


# ═══════════════════════════════════════════════════════════════════════════
#  IL RITMO — una persona, ripetibile (funzione pura)
# ═══════════════════════════════════════════════════════════════════════════
class Ritmo:
    """Pause, scelte e velocita' di battitura di UNA persona.  ⭐ Tutto da
    `random.Random("remotix16:<seme>:<utente>")`: la stessa salita rifatta
    (Intel/Radeon) ha le stesse scelte nello stesso ordine; utenti diversi
    hanno ritmi diversi anche con lo stesso seme."""

    def __init__(self, seme, utente, sorgente=None):
        self.r = sorgente or random.Random("remotix16:%s:%d" % (seme, utente))
        self.base_ms = self.r.uniform(110, 240)        # battuta media della persona
        self.lentezza = self.r.uniform(0.7, 1.5)       # scala delle sue pause

    def battuta_ms(self):
        v = self.r.lognormvariate(math.log(self.base_ms), 0.35)
        if self.r.random() < 0.04:
            v += self.r.uniform(300, 900)              # un'esitazione
        return max(40.0, min(1500.0, v))

    def tenuta_ms(self):
        return self.r.uniform(35, 95)

    def pausa_s(self, tipo="breve"):
        if tipo == "gesto":
            v = self.r.uniform(0.15, 0.6)
        elif tipo == "leggere":
            v = self.r.uniform(5.0, 18.0) * self.lentezza
        else:
            v = self.r.lognormvariate(math.log(2.0), 0.5) * self.lentezza
        return max(0.1, min(30.0, v))

    def scegli(self, voci, pesi=None):
        return self.r.choices(list(voci), pesi)[0]

    def intero(self, a, b):
        return self.r.randint(a, b)

    def uniforme(self, a, b):
        return self.r.uniform(a, b)

    def probabile(self, p):
        return self.r.random() < p

    def cifre(self, n):
        return "".join(str(self.r.randint(0, 9)) for _ in range(n))


def impronta(ritmo, n=300):
    """La sequenza di `n` estrazioni di tutti i tipi (per la certificazione)."""
    out = []
    for i in range(n):
        out += [round(ritmo.battuta_ms(), 6), round(ritmo.pausa_s(("gesto", "breve", "leggere")[i % 3]), 6),
                ritmo.scegli("abcd", (1, 2, 3, 4)), ritmo.intero(1, 99), ritmo.cifre(2)]
    return out


def ripetibile(fabbrica, n=300):
    """⭐ Due ritmi dalla stessa fabbrica danno la stessa sequenza?"""
    return impronta(fabbrica(), n) == impronta(fabbrica(), n)


# ═══════════════════════════════════════════════════════════════════════════
#  IL DIARIO DELLA PAGINA — la riga «audio: …» che la pagina manda ogni 5 s
#  (src/pagina.html ~6970), letta com'e' (funzione pura)
# ═══════════════════════════════════════════════════════════════════════════
# nomi della meta' audio (prima di « | ») e della meta' pagina (dopo)
_AUDIO = {"ricevuti": "ricevuti", "suonati": "suonati", "BUCHI": "BUCHI", "vecchi": "vecchi",
          "tardivi": "tardivi", "fuori": "audio_fuori_ordine", "rec": "recuperati",
          "dop": "doppioni", "pieni": "pieni", "errori": "audio_errori", "mancati": "mancati",
          "volte": "mancati_volte", "usciti": "audio_usciti", "tagliati": "tagliati",
          "sospesi": "sospesi", "salti": "salti_suono", "risv": "risvegli", "coda": "coda_ms"}
_PAGINA = {"tasti": "tasti", "dipinti": "dipinti", "fuori": "video_fuori", "dentro": "video_dentro",
           "coda_dec": "coda_dec", "bmp": "bmp", "salt": "salt", "buchi": "buchi", "ord": "ord",
           "mis": "mis", "tard": "tard", "err": "err", "voff": "voff", "AV": "AV_ms"}


def _intero(t):
    m = re.match(r"^([+-]?\d+)", t or "")
    return int(m.group(1)) if m else None


def leggi_riga_diario(riga):
    """⭐ La riga del diario ⇒ dict.  Un campo che non c'e' resta None («non
    letto»), MAI zero: un zero inventato e' un verde falso."""
    if not riga or not riga.startswith("audio: "):
        return None
    audio, _, pagina = riga[len("audio: "):].partition(" | ")
    d = {v: None for v in list(_AUDIO.values()) + list(_PAGINA.values())}
    d.update({"video_consegnati": None, "video_dipinti": None, "schermo": None, "fuoco": None,
              "classico": None, "ctx": None})
    for parte, tabella in ((audio, _AUDIO), (pagina, _PAGINA)):
        p = parte.split()
        for i in range(len(p) - 1):
            if p[i] in tabella and d[tabella[p[i]]] is None:
                d[tabella[p[i]]] = _intero(p[i + 1])
    p = pagina.split()
    for i in range(len(p) - 1):
        if p[i] == "video" and "→" in p[i + 1]:
            a, _, b = p[i + 1].partition("→")
            d["video_consegnati"], d["video_dipinti"] = _intero(a), _intero(b)
        elif p[i] in ("schermo", "fuoco", "classico"):
            d[p[i]] = p[i + 1]
    pa = audio.split()
    for i in range(len(pa) - 1):
        if pa[i] == "ctx":
            d["ctx"] = pa[i + 1]
    return d


def differenze(prima, dopo, nomi):
    """Le crescite dei contatori fra due letture.  ⚠ Un contatore che CALA (la
    pagina ricaricata, la sessione rinata) non e' una crescita negativa: e'
    «azzerato», e il suo delta e' None."""
    out, azzerati = {}, []
    for n in nomi:
        a, b = (prima or {}).get(n), (dopo or {}).get(n)
        if a is None or b is None:
            out[n] = None
        elif b < a:
            out[n] = None
            azzerati.append(n)
        else:
            out[n] = b - a
    return out, azzerati


JS_DIARIO = r"""
const da = arguments[0] || 0;
const R = window.REMOTIX, s = R && R.schermo, reg = document.getElementById('registro');
const t = reg ? reg.textContent : '';
const i = t.lastIndexOf('audio: ricevuti');
let riga = null;
if (i >= 0) { const j = t.indexOf('\n', i); riga = j < 0 ? t.slice(i) : t.slice(i, j); }
const nuove = (da <= t.length ? t.slice(da) : t).split('\n')
  .filter(r => r.indexOf('⛔') >= 0 || r.indexOf('MISURA') === 0).slice(-20).map(r => r.slice(0, 300));
const c = s && s.conti;
const e = document.getElementById('esito');
const G = R && R.giro;
const giro = G && G.campioni ? { visti: G.visti, campioni: G.campioni.map(x => Math.round(x * 10) / 10) } : null;
const dt = window.__C16 ? window.__C16.t.splice(0) : null;
return { riga: riga, lung: t.length, giro: giro, dipinti_t: dt, nuove: nuove, sessione: !!(s && s.sessione),
  schermo: document.body ? (document.body.dataset.schermo || null) : null,
  fuoco: document.hasFocus(), visibile: document.visibilityState,
  esito: e ? e.textContent.slice(0, 200) : null, esito_classe: e ? e.className : null,
  conti: c ? { dipinti: c.dipinti, consegnati: c.consegnati, saltati_coda: c.saltati_coda,
               buchi: c.buchi, chiavi_chieste: c.chiavi_chieste, tardive: c.tardive,
               scartati_ordine: c.scartati_ordine, scartati_misura: c.scartati_misura,
               usciti: c.usciti } : null };
"""
CONTI_DELTA = ("consegnati", "dipinti", "salt", "buchi", "tard", "chiavi_chieste",
               "ricevuti", "suonati", "BUCHI", "mancati")

# ⭐ La sonda dei dipinti: nella pagina VERA, ogni 10 ms guarda `conti.dipinti`
#   e annota l'ora (Date.now: lo stesso orologio dell'attore, stessa macchina)
#   di ogni cambio.  JS_DIARIO li prende e svuota ogni 5 s.
SONDA_DIPINTI = r"""
(function () {
  if (window.__C16) return;
  const C = window.__C16 = { t: [], ultimo: null };
  setInterval(function () {
    const s = window.REMOTIX && window.REMOTIX.schermo;
    const d = s && s.conti ? s.conti.dipinti : null;
    if (d === null || d === C.ultimo) return;
    if (C.ultimo !== null) { C.t.push(Date.now()); if (C.t.length > 20000) C.t.splice(0, 5000); }
    C.ultimo = d;
  }, 10);
})();
"""


def conti_classifica(c, diario):
    """⭐ I contatori CUMULATIVI coi nomi che legge 16-classifica.py: dalla
    pagina (`REMOTIX.schermo.conti`) e, per l'audio, dalla riga del diario.
    Solo quelli che ci sono: un None qui farebbe credere al classificatore
    di averlo letto."""
    out = {}
    c = c or {}
    for mio, suo in (("consegnati", "consegnati"), ("dipinti", "dipinti"), ("salt", "saltati_coda"),
                     ("buchi", "buchi"), ("tard", "tardive"), ("chiavi_chieste", "chiavi_chieste")):
        if c.get(suo) is not None:
            out[mio] = c[suo]
    d = diario or {}
    for k in ("ricevuti", "suonati", "BUCHI", "mancati"):
        if d.get(k) is not None:
            out[k] = d[k]
    for mio, suo in (("consegnati", "video_consegnati"), ("dipinti", "video_dipinti"),
                     ("salt", "salt"), ("buchi", "buchi"), ("tard", "tard")):
        if mio not in out and d.get(suo) is not None:
            out[mio] = d[suo]
    return out


JS_GIRO = r"""
const G = window.REMOTIX && window.REMOTIX.giro;
return G && G.campioni ? { visti: G.visti, campioni: G.campioni.map(x => Math.round(x * 10) / 10) } : null;
"""


def campioni_nuovi(prima, dopo):
    """⭐ I campioni del GIRO arrivati fra due letture di `REMOTIX.giro`
    ({visti, campioni: gli ultimi 200}): gli ultimi `dopo.visti − prima.visti`.
    Prese SOLO attorno a una battitura a eco immediato, sono il ritardo del
    PRODOTTO (il carattere compare subito), senza il tempo di reazione
    dell'applicazione (una pagina che carica, una finestra che si apre).
    ⚠ Se ne sono arrivati piu' di quanti la lista ne tiene, si prendono quelli
    che ci sono; una lettura mancata ⇒ nessun campione (mai inventati)."""
    if not prima or not dopo or dopo.get("campioni") is None:
        return []
    n = (dopo.get("visti") or 0) - (prima.get("visti") or 0)
    if n <= 0:
        return []
    return list(dopo["campioni"])[-n:]


def attese_impulsi(impulsi, dipinti_t, ora, tetto_s=5.0):
    """⭐ Per ogni impulso (un input che DEVE cambiare l'immagine), l'attesa
    fino al primo dipinto DOPO di lui.  ⇒ (attese in s, impulsi ancora aperti).
    Un impulso senza dipinto da piu' di `tetto_s` si chiude con l'attesa fin
    qui (e' un blocco, non si butta)."""
    attese, aperti = [], []
    pt = sorted(dipinti_t)
    for e in sorted(impulsi):
        dopo = next((x for x in pt if x > e), None)
        if dopo is not None:
            attese.append(dopo - e)
        elif ora - e > tetto_s:
            attese.append(ora - e)
        else:
            aperti.append(e)
    return attese, aperti


def pausa_piu_lunga(dipinti_t, da, a):
    """⭐ Il fermo piu' lungo dell'immagine in [da, a] (video: deve sempre
    cambiare), bordi compresi: dall'ultimo dipinto prima di `da`, fino ad `a`."""
    pt = sorted(dipinti_t)
    prima = [x for x in pt if x <= da]
    punti = ([prima[-1]] if prima else [da]) + [x for x in pt if da < x <= a] + [a]
    return max((y - x for x, y in zip(punti, punti[1:])), default=a - da)


class Fine(Exception):
    """SIGTERM / SIGINT: si smette di lavorare e si sgombera."""


# ═══════════════════════════════════════════════════════════════════════════
#  LA CERTIFICAZIONE — le funzioni pure, con i GUASTI INNESTATI
# ═══════════════════════════════════════════════════════════════════════════
RIGA_ESEMPIO = ("audio: ricevuti 1200 suonati 1188 BUCHI 2 vecchi 3 tardivi 0 fuori 5 rec 1 "
                "dop 0 pieni 0 errori 0 mancati 7 volte 3 usciti 1180 tagliati 0 sospesi 0 "
                "salti 0 risv 1 coda 270ms dec wasm 55/210us usc 12ms aoff 40 ctx running"
                " | tasti 88 ultimo KeyA classico si schermo acceso dipinti 5000 video "
                "5210→5000 fuori 5100 dentro 110 coda_dec 2 bmp 0 salt 90 buchi 1 ord 0 mis 0 "
                "tard 0 err 0 voff 33 AV +7ms fuoco si")


def certifica():
    guai = []

    def prova(cosa, vero, det=""):
        print("   %s %s%s" % ("⭐ ok " if vero else "⛔ NO ", cosa, (" — " + det) if det else ""))
        if not vero:
            guai.append(cosa)

    print("── il ritmo")
    prova("stesso seme e utente ⇒ stessa sequenza", ripetibile(lambda: Ritmo("s1", 3)))
    prova("utenti diversi ⇒ sequenze diverse",
          impronta(Ritmo("s1", 3)) != impronta(Ritmo("s1", 4)))
    prova("semi diversi ⇒ sequenze diverse",
          impronta(Ritmo("s1", 3)) != impronta(Ritmo("s2", 3)))
    # ⛔ GUASTO: un ritmo senza seme (dall'orologio) deve risultare NON ripetibile
    prova("GUASTO visto: ritmo senza seme ⇒ non ripetibile",
          not ripetibile(lambda: Ritmo("s1", 3, sorgente=random.Random())))
    r = Ritmo("s1", 5)
    b = [r.battuta_ms() for _ in range(3000)]
    media = sum(b) / len(b)
    prova("battute fra 40 e 1500 ms, media umana (80-400 ms)",
          min(b) >= 40 and max(b) <= 1500 and 80 <= media <= 400, "media %.0f ms" % media)
    pp = {k: [r.pausa_s(k) for _ in range(500)] for k in ("gesto", "breve", "leggere")}
    prova("pause: gesto < breve < leggere (in media)",
          sum(pp["gesto"]) < sum(pp["breve"]) < sum(pp["leggere"]),
          " ".join("%s %.1f s" % (k, sum(v) / len(v)) for k, v in pp.items()))
    basi = {round(Ritmo("s1", n).base_ms) for n in range(1, 17)}
    prova("16 persone, 16 velocita' diverse", len(basi) == 16, str(sorted(basi)))

    print("── il diario della pagina")
    d = leggi_riga_diario(RIGA_ESEMPIO)
    prova("riga d'esempio letta", d is not None)
    atteso = {"ricevuti": 1200, "suonati": 1188, "BUCHI": 2, "mancati": 7, "mancati_volte": 3,
              "audio_fuori_ordine": 5, "video_fuori": 5100, "video_consegnati": 5210,
              "video_dipinti": 5000, "salt": 90, "buchi": 1, "dipinti": 5000, "coda_ms": 270,
              "tasti": 88, "AV_ms": 7, "fuoco": "si", "schermo": "acceso", "ctx": "running"}
    storti = {k: (d or {}).get(k) for k, v in atteso.items() if (d or {}).get(k) != v}
    prova("ogni campo al suo valore (i due «fuori» NON confusi)", not storti, str(storti))
    # ⛔ GUASTO: la riga senza BUCHI ⇒ BUCHI None (non letto), mai 0
    g = leggi_riga_diario(RIGA_ESEMPIO.replace(" BUCHI 2", ""))
    prova("GUASTO visto: BUCHI tolto dalla riga ⇒ None, non zero", g and g["BUCHI"] is None,
          "BUCHI=%r" % (g or {}).get("BUCHI"))
    # ⛔ GUASTO: BUCHI cambiato ⇒ il valore letto cambia
    g = leggi_riga_diario(RIGA_ESEMPIO.replace(" BUCHI 2", " BUCHI 41"))
    prova("GUASTO visto: BUCHI 41 ⇒ letto 41", g and g["BUCHI"] == 41)
    g = leggi_riga_diario(RIGA_ESEMPIO.split(" | ")[0])
    prova("GUASTO visto: senza la meta' pagina ⇒ video None", g and g["video_dipinti"] is None
          and g["salt"] is None)
    prova("una riga d'altro ⇒ None", leggi_riga_diario("MISURA qualcosa") is None)
    dd, az = differenze({"dipinti": 100, "buchi": 1}, {"dipinti": 160, "buchi": 1},
                        ("dipinti", "buchi", "salt"))
    prova("differenze: crescita e campo mancante", dd == {"dipinti": 60, "buchi": 0, "salt": None}
          and not az, str(dd))
    # ⛔ GUASTO: la pagina ricaricata azzera i contatori ⇒ «azzerato», non un delta negativo
    dd, az = differenze({"dipinti": 900}, {"dipinti": 12}, ("dipinti",))
    prova("GUASTO visto: contatore che cala ⇒ azzerato, delta None",
          dd["dipinti"] is None and az == ["dipinti"])

    print("── i contatori per il classificatore")
    cc = conti_classifica({"consegnati": 10, "dipinti": 9, "saltati_coda": 1, "buchi": 0,
                           "tardive": 0, "chiavi_chieste": 2}, d)
    prova("nomi del classificatore, audio dal diario", cc == {
        "consegnati": 10, "dipinti": 9, "salt": 1, "buchi": 0, "tard": 0, "chiavi_chieste": 2,
        "ricevuti": 1200, "suonati": 1188, "BUCHI": 2, "mancati": 7}, str(cc))
    cc = conti_classifica(None, None)
    prova("GUASTO visto: niente pagina ⇒ nessun contatore (non zeri)", cc == {}, str(cc))
    cc = conti_classifica(None, d)
    prova("senza conti diretti ⇒ dal diario (video X→Y)", cc.get("consegnati") == 5210
          and cc.get("dipinti") == 5000, str(cc))

    print("── il giro a eco (solo le battiture)")
    g0 = {"visti": 10, "campioni": [30.0] * 10}
    g1 = {"visti": 11, "campioni": [30.0] * 10 + [1136.0]}            # un clic che carica una pagina
    g2 = {"visti": 16, "campioni": [30.0] * 10 + [1136.0] + [41.0, 38.5, 44.0, 40.2, 39.9]}
    eco = campioni_nuovi(g1, g2)                                      # attorno alla sola battitura
    prova("i 5 campioni della battitura, e solo quelli", eco == [41.0, 38.5, 44.0, 40.2, 39.9],
          str(eco))
    # ⛔ GUASTO: la differenza presa dall'inizio (prima del clic) si porta dentro il 1136
    tutto = campioni_nuovi(g0, g2)
    prova("GUASTO visto: senza la lettura prima della battitura il clic di caricamento entra",
          1136.0 in tutto and 1136.0 not in eco, str(tutto))
    prova("lettura mancata ⇒ nessun campione", campioni_nuovi(None, g2) == []
          and campioni_nuovi(g2, g2) == [])
    g3 = {"visti": 500, "campioni": [float(i) for i in range(200)]}
    prova("piu' campioni della lista ⇒ quelli che ci sono", len(campioni_nuovi(g0, g3)) == 200)

    print("── il blocco dell'immagine")
    at, ap = attese_impulsi([10.0, 12.0, 19.5], [10.2, 10.25, 13.5], 20.0)
    prova("attese: 0,2 s e 1,5 s, l'ultimo ancora aperto",
          [round(x, 2) for x in at] == [0.2, 1.5] and ap == [19.5], "%s %s" % (at, ap))
    # ⛔ GUASTO: l'immagine non cambia piu' dopo l'input ⇒ l'attesa diventa un blocco
    at, ap = attese_impulsi([10.0], [9.0], 16.0)
    prova("GUASTO visto: nessun dipinto dopo l'input ⇒ blocco di 6 s", at == [6.0] and not ap,
          str(at))
    pl = pausa_piu_lunga([x / 30.0 for x in range(0, 300)], 2.0, 9.9)
    prova("video a 30 al secondo ⇒ fermo di ~33 ms", 0.03 <= pl <= 0.04, "%.3f s" % pl)
    buco = [x / 30.0 for x in range(0, 300) if not 150 <= x < 210]
    pl = pausa_piu_lunga(buco, 2.0, 9.9)
    # ⛔ GUASTO: 2 s senza fotogrammi in mezzo al video ⇒ visto
    prova("GUASTO visto: 2 s senza fotogrammi ⇒ fermo di 2 s", 1.9 <= pl <= 2.1, "%.3f s" % pl)
    pl = pausa_piu_lunga([1.0, 1.1], 2.0, 7.0)
    prova("GUASTO visto: video fermo da prima della finestra ⇒ fermo intero", pl >= 5.9,
          "%.1f s" % pl)

    print("── le verifiche dell'input")
    st = "ls -la ~/prova16 #k3\nfind /usr/share -name '*.png' | head -n 60 #k4\n"
    prova("storia: la riga esatta c'e'", L.storia_contiene(st, "ls -la ~/prova16 #k3"))
    # ⛔ GUASTO: un carattere perso nel tragitto ⇒ KO
    prova("GUASTO visto: un carattere perso ⇒ KO",
          not L.storia_contiene(st, "ls -la ~/prova16 #k4")
          and not L.storia_contiene("ls -la ~/prova1 #k3\n", "ls -la ~/prova16 #k3"))
    q = L.leggi_quaderno("1727.500 carica testo 0 9000\n1727.900 scroll testo 1200 9000\n"
                         "rotta\n1728.1 video yt t=12.40 stato=1 q=hd2160 livelli=hd2160,hd1440\n")
    prova("quaderno: tre righe buone, la rotta scartata", len(q) == 3 and q[1][1] == "scroll"
          and q[1][2] == ["testo", "1200", "9000"], str(q))
    v = L.leggi_video(q[2][2])
    prova("video: t, stato, qualita'", v.get("t") == 12.4 and v.get("stato") == 1
          and v.get("q") == "hd2160", str(v))
    prova("fonte video: YouTube e file", L.fonte_video("https://www.youtube.com/watch?v=LXb3EKWsInQ")
          == ("yt", "LXb3EKWsInQ") and L.fonte_video("file:///rete11/v.mp4") == ("file", "/rete11/v.mp4")
          and L.fonte_video("ftp://x")[0] is None)

    print("── la finestra nella foto")
    try:
        from PIL import Image, ImageDraw
        a = Image.new("RGB", (960, 540), (0, 0, 0))
        ImageDraw.Draw(a).rectangle([880, 0, 930, 12], fill=(200, 200, 200))    # orologio
        b = a.copy()
        dr = ImageDraw.Draw(b)
        dr.rectangle([880, 0, 930, 12], fill=(90, 90, 90))                       # l'orologio cambia
        dr.rectangle([200, 100, 700, 420], outline=(220, 220, 220), width=3)     # finestra scura
        dr.rectangle([200, 100, 700, 130], fill=(60, 60, 200))                   # sua testata
        dr.text((220, 200), "user@host:~$ ls", fill=(200, 200, 200))
        r = L.rett_finestra(a, b)
        prova("finestra scura su fondo nero trovata (%s)" % (r,), r is not None and
              abs(r[0] - 200) <= 16 and abs(r[1] - 100) <= 16 and abs(r[2] - 700) <= 16
              and abs(r[3] - 420) <= 16)
        c = a.copy()
        ImageDraw.Draw(c).rectangle([880, 0, 930, 12], fill=(90, 90, 90))
        # ⛔ GUASTO: cambia solo l'orologio ⇒ nessuna finestra
        prova("GUASTO visto: cambia solo l'orologio ⇒ nessuna finestra",
              L.rett_finestra(a, c) is None)
    except ImportError:
        prova("PIL c'e'", False)

    print("── utenti, profili, browser")
    prof = "".join(L.profilo_di(n) for n in range(1, 17))
    prova("profili 1..16 = ABCD×4", prof == "ABCD" * 4, prof)
    br = [L.browser_di(n) for n in range(1, 17)]
    prova("dispari Firefox, pari Chrome", all(b == ("firefox" if n % 2 else "chrome")
                                             for n, b in zip(range(1, 17), br)))
    sg = re.compile(r"^c[0-9]+b?u[0-9]+$")
    nomi = [L.inquilino_di(n) for n in range(1, 17)]
    prova("inquilini riconosciuti dallo sgombero e tutti diversi",
          all(sg.match(x) for x in nomi) and len(set(nomi)) == 16, "%s … %s" % (nomi[0], nomi[-1]))
    porte = {L.porta_interna(d, n) for d in DESKTOP for n in range(1, 17)}
    prova("porte interne tutte diverse (4 desktop × 16)", len(porte) == 64)
    print("⛔ CERTIFICAZIONE FALLITA (%d)" % len(guai) if guai else "⭐ CERTIFICATO")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  L'AMBIENTE — prima di importare la suite (legge REMOTIX_SUL_SERVER all'import)
# ═══════════════════════════════════════════════════════════════════════════
def ambiente(o):
    u = os.getuid()
    os.environ.update({
        "XDG_RUNTIME_DIR": "/run/user/%d" % u,
        "WAYLAND_DISPLAY": o.wayland,
        "REMOTIX_SCHERMO_ANNIDATO": "1",
        "REMOTIX_SUL_SERVER": "1",
        "MOZ_ENABLE_WAYLAND": "1",
        "REMOTIX_CHROME_OPZIONI": "--ozone-platform=wayland --disable-backgrounding-occluded-windows "
                                  "--disable-renderer-backgrounding --disable-background-timer-throttling "
                                  # ⭐ le opzioni in piu' della salita (es. --render-node-override)
                                  + os.environ.get("REMOTIX_16_CHROME_IN_PIU", ""),
    })
    os.environ["REMOTIX_CHROME_OPZIONI"] = os.environ["REMOTIX_CHROME_OPZIONI"].strip()
    os.environ.pop("DISPLAY", None)


def argomenti():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--scatola", choices=DESKTOP)
    a.add_argument("--utente", type=int)
    a.add_argument("--wayland", help="il socket del labwc di questo utente (wayland-K)")
    a.add_argument("--dir", help="la cartella delle evidenze della salita")
    a.add_argument("--seme", default="0")
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    a.add_argument("--porte-base", type=int, default=0,
                   help="Firefox P, Chrome P+1 (di serie 9700 + 4·N)")
    a.add_argument("--video", default="",
                   help="utenti D: URL YouTube, o un file (percorso DENTRO la scatola, /rete11/…)")
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--tetto-s", type=int, default=60, help="tetto dell'accesso e del primo fotogramma")
    o = a.parse_args()
    if o.certifica:
        return o
    for k in ("scatola", "utente", "wayland", "dir"):
        if getattr(o, k) in (None, ""):
            a.error("serve --%s" % k)
    if not 1 <= o.utente <= 99:
        a.error("--utente fra 1 e 16 (fino a 99 per il sovraccarico)")
    if not o.porte_base:
        o.porte_base = 9700 + 4 * o.utente
    return o


# ═══════════════════════════════════════════════════════════════════════════
#  L'ATTORE
# ═══════════════════════════════════════════════════════════════════════════
class Attore:
    def __init__(self, o, S, G2):
        self.o, self.S, self.G2 = o, S, G2
        self.C21 = S.C21
        self.n = o.utente
        self.profilo = L.profilo_di(self.n)
        self.browser = L.browser_di(self.n)
        self.chi = L.inquilino_di(self.n)
        self.parola = "c16-" + secrets.token_hex(8)
        self.porta_interna = L.porta_interna(o.scatola, self.n)
        self.ritmo = Ritmo(o.seme, self.n)
        self.cartella = os.path.join(o.dir, "utente-%02d" % self.n)
        os.makedirs(self.cartella, exist_ok=True)
        self.f_stato = open(os.path.join(self.cartella, "stato.jsonl"), "a", buffering=1)
        self.f_eventi = open(os.path.join(self.cartella, "eventi.jsonl"), "a", buffering=1)
        self.eventi_finestra = []
        self.errori_finestra = []
        self.giro_eco_finestra = []
        self.impulsi = []
        self.dipinti_t = []
        self.entrato = False
        self.muti = 0
        self.s = self.sc = self.g = None
        self.geo = None
        self.desktop = (o.largo, o.alto)
        self.mani = None
        self.lavoro = None
        self.voglio_foto = False
        self.fermati = False
        self.prossimo_stato = 0.0
        self.azioni = {}
        self.fatte_finestra = 0
        self.verifiche = {"ok": 0, "ko": 0}
        self.ver_finestra = []
        self.reg_da = 0
        self.prec = None                   # (ora, conti, diario) della riga precedente
        self.foto_size = None

    # -- le righe -------------------------------------------------------------
    #  stato.jsonl: SOLO le righe di stato (ogni 5 s), nello schema che legge
    #  16-classifica.py; gli eventi vanno in eventi.jsonl E nella riga di stato
    #  dopo (campo `eventi`), cosi' non si perdono e non sporcano le finestre.
    def _testa(self, evento):
        return {"t": round(time.time(), 3), "utente": self.n, "profilo": self.profilo,
                "browser": self.browser, "versione": getattr(self, "esiti", None)
                and self.esiti.versione, "inquilino": self.chi, "evento": evento}

    def riga(self, evento, **campi):
        r = self._testa(evento)
        r.pop("evento")
        r.update(campi)
        self.f_stato.write(json.dumps(r, ensure_ascii=False) + "\n")

    def evento(self, tipo, **campi):
        r = self._testa(tipo)
        r.update(campi)
        self.f_eventi.write(json.dumps(r, ensure_ascii=False) + "\n")
        self.eventi_finestra.append(r)
        print("   [%02d %s] %s %s" % (self.n, self.profilo, tipo,
                                    json.dumps(campi, ensure_ascii=False)[:240]), flush=True)

    def conta(self, azione):
        self.azioni[azione] = self.azioni.get(azione, 0) + 1
        self.fatte_finestra += 1

    def verifica(self, azione, ok, lat_ms, det=""):
        self.conta(azione)
        self.verifiche["ok" if ok else "ko"] += 1
        v = {"azione": azione, "ok": bool(ok),
             "latenza_ms": None if lat_ms is None else round(lat_ms), "det": det}
        self.ver_finestra.append(v)
        if not ok:
            print("   [%02d %s] ⚠ input NON verificato: %s" % (self.n, self.profilo, v), flush=True)

    def impulso(self, t):
        """Un input che DEVE cambiare l'immagine (un carattere battuto, un Invio
        nel terminale, un clic su un collegamento, una tacca che scorre)."""
        self.impulsi.append(t)

    # -- il cuore: segnali, foto, stato ---------------------------------------
    def cuore(self):
        """⭐ Il punto SICURO: qui (e solo qui) il SIGTERM diventa `Fine`.
        ⛔ `[M]` 25 set 2026: interrotta a meta' di una chiamata, Marionette
        restava con la risposta pendente e la chiamata dopo leggeva quella —
        il registro della pagina all'uscita non si salvava piu'."""
        if self.fermati:
            raise Fine("segnale")
        if self.voglio_foto:
            self.voglio_foto = False
            self.scatta()
        if time.time() >= self.prossimo_stato:
            self.in_ritardo = time.time() - self.prossimo_stato if self.prossimo_stato else 0.0
            self.scrivi_stato()
            # ⚠ la prossima fra 5 s DA ORA, non sulla griglia: dopo una riga in
            #   ritardo, una seconda a 0,7 s di distanza sarebbe per il
            #   classificatore «5 s senza fotogrammi» (`[M]` 25 set, utente D)
            self.prossimo_stato = time.time() + 5.0

    def dorme(self, secondi):
        fine = time.time() + max(0.0, secondi)
        while True:
            self.cuore()
            resto = fine - time.time()
            if resto <= 0:
                return
            time.sleep(min(0.25, resto))

    def arma_sonda(self):
        """La sonda dei dipinti nella pagina (ogni 10 ms: l'ora di ogni cambio)."""
        try:
            with self.G2.tetto(20, "la sonda"):
                self.g.js(self.S.VERI._inietta(SONDA_DIPINTI))
            return True
        except Exception as e:                   # noqa: BLE001
            self.evento("errore", testo="sonda dei dipinti non armata: %s" % str(e)[:200])
            return False

    def scrivi_stato(self):
        if self.g is None:
            return
        try:
            with self.G2.tetto(20, "il diario"):
                p = self.g.js(JS_DIARIO, self.reg_da) or {}
        except Exception as e:                   # noqa: BLE001
            p = {"errore": str(e)[:200]}
        ora = time.time()
        riga_d = p.get("riga")
        diario = leggi_riga_diario(riga_d)
        conti = conti_classifica(p.get("conti"), diario)
        errori = []
        if p.get("errore"):
            errori.append("la pagina non risponde al banco: " + p["errore"])
            self.muti += 1
        else:
            self.muti = 0
        # ⭐ la caduta: dopo l'ingresso la pagina non e' piu' in sessione
        caduta = bool(self.entrato and not p.get("errore") and not p.get("sessione"))
        if caduta:
            errori.append("la pagina non e' piu' in sessione (schermo %s, esito «%s»)"
                          % (p.get("schermo"), p.get("esito")))
        # ⭐ il blocco piu' lungo: dai tempi dei dipinti e dagli impulsi
        pt = [x / 1000.0 for x in (p.get("dipinti_t") or [])]
        self.dipinti_t = [x for x in self.dipinti_t if x > ora - 30] + pt
        blocco, lavoro = None, False
        if self.profilo == "D":
            if self.video_in_corso():
                blocco = pausa_piu_lunga(self.dipinti_t, self.prec[0] if self.prec else ora - 5, ora)
                lavoro = True
        else:
            attese, self.impulsi = attese_impulsi(self.impulsi, self.dipinti_t, ora)
            if attese:
                blocco, lavoro = max(attese), True
        campi = {"conti": conti, "diario": riga_d, "diario_letto": diario,
                 "giro": p.get("giro"), "giro_eco": self.giro_eco_finestra,
                 "input": self.ver_finestra,
                 "blocco_max_ms": None if blocco is None else round(blocco * 1000),
                 "lavoro": lavoro, "caduta": caduta, "errori": errori + self.errori_finestra,
                 "sessione": p.get("sessione"), "schermo": p.get("schermo"),
                 "fuoco": p.get("fuoco"), "visibile": p.get("visibile")}
        if self.prec:
            dt = ora - self.prec[0]
            dc, az = differenze(self.prec[1], conti, CONTI_DELTA)
            campi["delta"] = dict(dc, s=round(dt, 2))
            if dc.get("dipinti") is not None and dt > 0:
                campi["dipinti_s"] = round(dc["dipinti"] / dt, 2)
            if az:
                campi["azzerati"] = az
        self.prec = (ora, conti)
        if p.get("nuove"):
            campi["pagina"] = p["nuove"]
        if isinstance(p.get("lung"), int):
            self.reg_da = p["lung"]
        # ⚠ quanto e' arrivata tardi questa riga (un gesto lungo la trattiene)
        campi["in_ritardo_s"] = round(getattr(self, "in_ritardo", 0.0), 2)
        campi.update({"azioni": dict(self.azioni), "azioni_finestra": self.fatte_finestra,
                      "verifiche": dict(self.verifiche)})
        if self.lavoro is not None:
            try:
                campi["dettagli_lavoro"] = self.lavoro.extra()
            except Exception as e:               # noqa: BLE001
                campi["dettagli_lavoro"] = {"errore": str(e)[:200]}
        if self.eventi_finestra:
            campi["eventi"] = self.eventi_finestra
        self.fatte_finestra = 0
        self.ver_finestra = []
        self.errori_finestra = []
        self.eventi_finestra = []
        self.giro_eco_finestra = []
        self.riga("stato", **campi)

    def video_in_corso(self):
        v = getattr(self.lavoro, "ultimo_video", None) or {}
        return self.entrato and v.get("stato") == 1

    # -- le foto ----------------------------------------------------------------
    def png(self):
        self.G2.davanti(self.g)
        with self.G2.tetto(30, "la fotografia"):
            return self.C21.foto_piena(self.g)

    def scatta(self):
        t = time.time()
        try:
            png = self.png()
        except Exception as e:                   # noqa: BLE001
            self.evento("foto", ok=False, perche=str(e)[:200])
            return
        if not png:
            self.evento("foto", ok=False, perche="la tela non si fotografa")
            return
        f = os.path.join(self.cartella, "foto-%d.png" % int(t * 1000))
        with open(f, "wb") as h:
            h.write(png)
        self.evento("foto", ok=True, file=f, ms=round((time.time() - t) * 1000))

    def foto_pil(self):
        from PIL import Image
        try:
            png = self.png()
        except Exception:                        # noqa: BLE001
            return None
        if not png:
            return None
        im = Image.open(io.BytesIO(png)).convert("RGB")
        self.foto_size = im.size
        return im

    def foto_al_desktop(self, r):
        if not r or not self.foto_size or not self.geo:
            return None
        pw, ph = self.foto_size
        x0, y0 = self.C21.dalla_foto_al_desktop(self.geo, pw, ph, r[0], r[1])
        x1, y1 = self.C21.dalla_foto_al_desktop(self.geo, pw, ph, r[2], r[3])
        tl, ta = self.desktop
        return (max(0, x0), max(0, y0), min(tl, x1), min(ta, y1))

    def preferenze_interne(self):
        return self.C21.PREFERENZE

    # -- l'accesso ------------------------------------------------------------
    def entra(self):
        s, VERI = self.s, self.S.VERI
        n = {"inquilino": self.chi, "browser": self.browser, "versione": self.esiti.versione,
             "scatola": self.o.scatola, "misura": [self.o.largo, self.o.alto]}
        ok, m = s.pr.apri()
        if not ok:
            n.update(esito="pagina_non_aperta", motivo="la pagina non si apre: " + m)
            return n
        t0 = time.time()
        r = s.g.js(VERI.JS_ENTRA, self.chi, self.parola)
        if r != "mandato":
            n.update(esito="modulo_non_compilato", motivo="il modulo non si compila: %s" % r)
            return n
        ammesso = primo = None
        st = {}
        while time.time() < t0 + self.o.tetto_s:
            st = s.pr.stato()
            ora = time.time()
            if ammesso is None and st.get("sessione") and st.get("esito_classe") == "bene" \
                    and (st.get("esito") or "").startswith("Ammesso"):
                ammesso = ora
            if st.get("esito_classe") == "male" and st.get("esito"):
                n.update(esito="rifiuto", motivo="rifiuto: «%s»" % st["esito"],
                         accesso_ms=round(t0 * 1000))
                return n
            if (st.get("dipinti") or 0) > 0:
                primo = ora
                ammesso = ammesso or ora
                break
            if self.fermati:
                raise Fine("segnale")
            time.sleep(0.1)
        # ⭐ nello schema di 16-classifica: ore in ms dall'epoca, e la durata a parte
        n["accesso_ms"] = round(t0 * 1000)
        n["ammesso_ms"] = round(ammesso * 1000) if ammesso else None
        n["primo_fotogramma_ms"] = round(primo * 1000) if primo else None
        n["nascita_ms"] = round((primo - t0) * 1000) if primo else None
        n["ammissione_ms"] = round((ammesso - t0) * 1000) if ammesso else None
        if not primo:
            n.update(esito="nessun_fotogramma", motivo="nessun fotogramma in %d s (esito «%s»)"
                     % (self.o.tetto_s, st.get("esito")))
            return n
        # ⚠ il giudizio «non degenere» fotografa fino al tetto: `[M]` 25 set,
        #   xfce ha lo sfondo NERO e lo aspettava 60 s ⇒ tetto corto, e il
        #   desktop scuro ma vivo lo riconosce `desktop_scuro_ma_vivo`
        tetto, self.o.tetto_s = self.o.tetto_s, 8
        try:
            e, m, st2 = s.pr.primo_fotogramma()
        finally:
            self.o.tetto_s = tetto
        e, m = self.S.C20V.desktop_scuro_ma_vivo(e, m, st2)
        n["desktop_vivo_ms"] = round((time.time() - t0) * 1000)
        n["esito"] = {self.S.VERDE: "ok", self.S.ROSSO: "degenere"}.get(e, "non_guardato")
        n["motivo"] = m
        return n

    # -- tutto ------------------------------------------------------------------
    def corri(self):
        o, S = self.o, self.S
        self.esiti = S.Esiti(o)
        S.MODELLO_INQUILINO = re.compile(r"^c16[0-9]{3}u[0-9]+$")
        self.s = S.Sessione(o, "%03d" % self.n, self.esiti, chi=self.chi, parola=self.parola)
        self.sc = self.s.sc
        self.evento("inizio", inquilino=self.chi, scatola=o.scatola, wayland=o.wayland,
                    porte_base=o.porte_base, seme=o.seme, porta_interna=self.porta_interna,
                    misura=[o.largo, o.alto], video=o.video or None, pid=os.getpid())
        codice = 2
        try:
            self.s.__enter__()                   # crea l'inquilino, accende il browser
            self.g = self.s.g
            self.lavoro = L.LAVORI[self.profilo](self)
            self.lavoro.prepara()
            nascita = self.entra()
            with open(os.path.join(self.cartella, "nascita.json"), "w") as f:
                json.dump(nascita, f, ensure_ascii=False, indent=1)
            self.evento("nascita", **nascita)
            if nascita.get("esito") != "ok":
                codice = 1
                self.aspetta_la_fine("accesso non riuscito")
                return codice
            self.entrato = True
            self.arma_sonda()
            self.geo = self.s.geometria()
            self.desktop = (self.geo["tl"], self.geo["ta"])
            self.mani = Mani(self)
            print("   [%02d] sveglia: %s" % (self.n, self.C21.sveglia(self.g, self.geo)), flush=True)
            # ⭐ IL CLIC DI BENVENUTO, su un punto vuoto del desktop, prima di ogni
            #   applicazione: e' il gesto dell'utente che sveglia l'audio della
            #   pagina.  ⛔ `[M]` 25 set, utente D senza: 6090 blocchi ricevuti,
            #   0 suonati, `ctx suspended` (l'accesso e' un modulo riempito dal
            #   banco, non un gesto; l'ESC della sveglia non attiva).
            self.dorme(1.0)
            self.mani.clic(self.desktop[0] * 0.55, self.desktop[1] * 0.55)
            self.dorme(1.0)
            codice = 0
            for prova in range(3):
                ok, m = self.lavoro.avvia()
                self.evento("applicazione", ok=ok, testo=m, tentativo=prova + 1)
                if ok:
                    break
                self.dorme(10)
            else:
                codice = 1
                self.aspetta_la_fine("l'applicazione non parte")
                return codice
            errori = 0
            while True:
                try:
                    t_passo = time.time()
                    self.lavoro.passo()
                    if time.time() - t_passo > 45 and self.profilo != "D":
                        print("   [%02d] ⚠ un passo di %.0f s" % (self.n, time.time() - t_passo),
                              flush=True)
                    errori = 0
                except Fine:
                    raise
                except Exception as e:           # noqa: BLE001
                    errori += 1
                    self.errori_finestra.append("%r" % e)
                    self.evento("errore", testo="%r" % e, dove=traceback.format_exc()[-600:],
                                di_fila=errori)
                    self.dorme(min(30, 2 * errori))
        except Fine:
            pass
        except Exception as e:                   # noqa: BLE001
            self.evento("errore", testo="%r" % e, dove=traceback.format_exc()[-800:], fatale=True)
            codice = 2
        finally:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            self.chiudi()
        return codice

    def aspetta_la_fine(self, perche):
        """⚠ Un utente che non e' riuscito a entrare resta a disposizione
        (stato, foto) finche' l'orchestratore non lo ferma: non sparisce."""
        self.evento("in_attesa", perche=perche)
        while True:
            self.dorme(5)

    def chiudi(self):
        try:
            if self.g is not None:
                try:
                    self.scrivi_stato()
                except Exception:                # noqa: BLE001
                    pass
                try:
                    with self.G2.tetto(20, "il registro della pagina"):
                        reg = self.g.js("const r=document.getElementById('registro');"
                                        "return r ? r.textContent : '';") or ""
                    with open(os.path.join(self.cartella, "registro-pagina.txt"), "w") as f:
                        f.write(reg)
                except Exception:                # noqa: BLE001
                    pass
                try:
                    self.s.salva_console()
                except Exception:                # noqa: BLE001
                    pass
        finally:
            try:
                self.s.__exit__(None, None, None)     # chiude il browser e SGOMBERA
            except Exception as e:               # noqa: BLE001
                print("   ⚠ uscita: %s" % e, flush=True)
            _c, t = self.sc.dentro("id %s >/dev/null 2>&1 && echo RESTA || echo via" % self.chi, 30)
            self.evento("fine", sgomberato=(t or "").strip().endswith("via"), azioni=self.azioni,
                        verifiche=self.verifiche)
            self.f_stato.close()
            self.f_eventi.close()


# ═══════════════════════════════════════════════════════════════════════════
#  LE MANI — input VERO dal browser, coordinate del DESKTOP remoto
# ═══════════════════════════════════════════════════════════════════════════
class Mani:
    def __init__(self, att):
        self.a = att
        self.G2 = att.G2
        self.pos = None

    @property
    def g(self):
        return self.a.g

    def vetro(self, X, Y):
        tl, ta = self.a.desktop
        X, Y = max(1, min(tl - 2, X)), max(1, min(ta - 2, Y))
        return self.a.C21.dal_desktop_al_vetro(self.a.geo, X, Y)

    def _cammino(self, X, Y):
        """Il puntatore ci va a passi, non di colpo."""
        vx, vy = self.vetro(X, Y)
        R = self.a.ritmo
        passi = []
        if self.pos:
            n = R.intero(3, 8)
            for i in range(1, n):
                f = i / float(n)
                passi += [("muovi", self.pos[0] + (vx - self.pos[0]) * f,
                           self.pos[1] + (vy - self.pos[1]) * f), ("pausa", R.intero(12, 30))]
        passi += [("muovi", vx, vy), ("pausa", R.intero(60, 180))]
        self.pos = (vx, vy)
        return passi

    def muovi(self, X, Y):
        self.G2.mouse(self.g, self._cammino(X, Y))
        return time.time()

    # ⭐ Ogni gesto torna l'ora di PRIMA dell'evento decisivo (la pressione,
    #   la prima tacca, il tasto): `[M]` 25 set, con l'ora di DOPO la chiamata
    #   la storia di bash risultava scritta 200 ms «prima» dell'Invio.
    def clic(self, X, Y, bottone=0, atteso=False):
        R = self.a.ritmo
        self.G2.mouse(self.g, self._cammino(X, Y))
        t = time.time()
        if atteso:
            self.a.impulso(t)
        self.G2.mouse(self.g, [("muovi",) + tuple(self.pos), ("giu", bottone, 1),
                               ("pausa", R.intero(50, 120)), ("su", bottone, 1)])
        self.a.conta("clic_mouse")
        return t

    def rotella(self, X, Y, tacche, atteso=False):
        """`tacche` > 0 in giu', < 0 in su; una tacca = 120 (una rotella vera)."""
        self.muovi(X, Y)
        vx, vy = self.pos
        R = self.a.ritmo
        dy = 120 if tacche > 0 else -120
        t = time.time()
        if atteso:
            self.a.impulso(t)
        if hasattr(self.g, "cdp"):
            self.G2.davanti(self.g)
            with self.G2.tetto(60, "la rotella"):
                for _ in range(abs(tacche)):
                    self.g.cdp.chiama("Input.dispatchMouseEvent", type="mouseWheel", x=vx, y=vy,
                                      deltaX=0, deltaY=dy)
                    time.sleep(R.intero(40, 160) / 1000.0)
        else:
            az = []
            for _ in range(abs(tacche)):
                az += [{"type": "scroll", "x": int(vx), "y": int(vy), "deltaX": 0, "deltaY": dy,
                        "origin": "viewport", "duration": 0},
                       {"type": "pause", "duration": R.intero(40, 160)}]
            self.g.m.chiama("WebDriver:PerformActions",
                            {"actions": [{"type": "wheel", "id": "rotella", "actions": az}]})
            self.g.m.chiama("WebDriver:ReleaseActions")
        self.a.conta("tacche")
        return t

    def premi(self, nome, atteso=False):
        t = time.time()
        if atteso:
            self.a.impulso(t)
        self.G2.tasti(self.g, self.G2.premi(nome))
        return t

    def combo(self, mod, tasto):
        passi = self.G2.premi(tasto)
        for m in reversed(mod):
            passi = self.G2.col(m, passi)
        t = time.time()
        self.G2.tasti(self.g, passi)
        return t

    def giro(self):
        try:
            with self.G2.tetto(15, "il giro"):
                return self.g.js(JS_GIRO)
        except Exception:                        # noqa: BLE001
            return None

    def batti(self, testo, atteso=True, eco=False):
        """Ogni carattere un tasto vero, col ritmo della persona.  `atteso`: ogni
        carattere deve comparire (eco) ⇒ e' un impulso per il blocco.  `eco`:
        il carattere compare SUBITO (terminale, campo di testo) ⇒ i campioni del
        giro arrivati durante la battitura vanno in `giro_eco`."""
        g_prima = self.giro() if eco else None
        self._batti(testo, atteso)
        fine = time.time()
        if eco:
            time.sleep(0.4)                      # l'eco degli ultimi caratteri
            self.a.giro_eco_finestra += campioni_nuovi(g_prima, self.giro())
        return fine

    def _batti(self, testo, atteso):
        R = self.a.ritmo
        tempi = [(R.tenuta_ms(), R.battuta_ms()) for _ in testo]
        # ⚠ a pezzi di ~1,5 s, col cuore in mezzo: una riga lunga battuta in una
        #   catena sola tratteneva la riga di stato fino a 10 s (`[M]` 25 set)
        pezzi, pezzo, dur = [], [], 0.0
        for c, tb in zip(testo, tempi):
            pezzo.append((c, tb))
            dur += max(tb) / 1000.0
            if dur >= 1.5:
                pezzi.append(pezzo)
                pezzo, dur = [], 0.0
        if pezzo:
            pezzi.append(pezzo)
        for i, pz in enumerate(pezzi):
            if i:
                self.a.cuore()
            if atteso:
                # ⚠ l'ora di ogni tasto e' quella PROGRAMMATA dalla partenza del
                #   pezzo (con Marionette il pezzo parte in una chiamata sola)
                k = time.time()
                for _c, (ten, bat) in pz:
                    self.a.impulso(k)
                    k += max(ten, bat) / 1000.0
            if hasattr(self.g, "cdp"):
                self.G2.davanti(self.g)
                with self.G2.tetto(30, "la battitura"):
                    for c, (ten, bat) in pz:
                        cd, vk = self.G2.codice_di(c)
                        self.g.cdp.chiama("Input.dispatchKeyEvent", type="keyDown", key=c, code=cd,
                                          windowsVirtualKeyCode=vk, text=c, unmodifiedText=c)
                        time.sleep(ten / 1000.0)
                        self.g.cdp.chiama("Input.dispatchKeyEvent", type="keyUp", key=c, code=cd,
                                          windowsVirtualKeyCode=vk)
                        time.sleep(max(0.0, bat - ten) / 1000.0)
            else:
                az = []
                for c, (ten, bat) in pz:
                    az += [{"type": "keyDown", "value": c}, {"type": "pause", "duration": int(ten)},
                           {"type": "keyUp", "value": c},
                           {"type": "pause", "duration": int(max(0, bat - ten))}]
                self.g.m.chiama("WebDriver:PerformActions",
                                {"actions": [{"type": "key", "id": "tastiera", "actions": az}]})
                self.g.m.chiama("WebDriver:ReleaseActions")
        self.a.conta("tasti")
        return time.time()


# ═══════════════════════════════════════════════════════════════════════════
def main():
    o = argomenti()
    if o.certifica:
        return certifica()
    ambiente(o)
    sys.path.insert(0, SUITE)
    import suite as S                                                 # noqa: E402
    G2 = S._carica("g2scena", os.path.join(SUITE, "15-g2-scena.py"))
    # ⭐ i tasti che servono ai lavori e che la tabella di G2 non ha
    G2.SPECIALI.setdefault("Delete", ("Delete", "Delete", 46, "", 0))
    G2.SPECIALI.setdefault("Home", ("Home", "Home", 36, "", 0))
    G2.SPECIALI.setdefault("PageDown", ("PageDown", "PageDown", 34, "", 0))
    G2.SPECIALI.setdefault("PageUp", ("PageUp", "PageUp", 33, "", 0))
    # i campi che `Sessione` e le guide di 12-client-veri si aspettano
    o.browser = L.browser_di(o.utente)
    o.guasto = False
    o.visibile = True
    o.porta = 0
    o.evidenze = os.path.join(o.dir, "utente-%02d" % o.utente)
    o.url = "https://%s:%d/" % (o.host, S.PORTE[o.scatola])
    o.scena, o.continuita_s, o.registro_cmd, o.lascia_acceso, o.salva = "viva", 8, "", False, ""
    att = Attore(o, S, G2)

    def _fine(_n, _f):
        att.fermati = True

    def _foto(_n, _f):
        att.voglio_foto = True
    signal.signal(signal.SIGTERM, _fine)
    signal.signal(signal.SIGINT, _fine)
    signal.signal(signal.SIGUSR1, _foto)
    print("⭐ attore %02d · %s · profilo %s · %s · %s · %s" % (
        o.utente, o.scatola, att.profilo, o.browser, o.wayland, att.chi), flush=True)
    return att.corri()


if __name__ == "__main__":
    sys.exit(main())
