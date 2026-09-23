#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""14-il-cliente-che-non-sta-fermo — ⭐⭐ UN CLIENTE CHE TOCCA LE COSE.

    python3 14-il-cliente-che-non-sta-fermo.py --certifica
    python3 14-il-cliente-che-non-sta-fermo.py --minuti 8 --desktop kde
    python3 14-il-cliente-che-non-sta-fermo.py --minuti 3 --desktop kde \
            --schermo-congelato            ⛔ il guasto innestato: DEVE dare 1

═══════════════════════════════════════════════════════════════════════════════
⭐⭐ PERCHE' QUESTO BANCO ESISTE — ed e' la lezione, non il codice
═══════════════════════════════════════════════════════════════════════════════
⛔⛔ **Tutti i nostri banchi avevano un cliente EDUCATO.**  Aprivano la pagina,
    entravano nella sessione, e poi stavano fermi a guardare: nessun
    movimento del mouse, nessun tasto, nessuna rotella.  Un utente vero non
    sta mai cosi'.

⇒ E per questo un difetto grosso e' stato invisibile **da sempre**: il 23
  settembre 2026 si e' scoperto che `batti_fra()` RIMANDAVA il battito del
  server a ogni chiamata, e `regola_battito()` gira a ogni messaggio di input
  del client.  ⚠ Un browser che manda ~40 messaggi di input al secondo teneva
  il battito da 1 s **in eterno**, e con lui `video_regola()`, cioe' l'unico
  posto da cui la CHIAVE si richiede al palco (§5.2).  ⇒ Lo schermo si fermava
  per minuti interi, e nessuna misura della notte lo vedeva, perche' nessuna
  misura della notte muoveva il mouse.

⭐ QUESTO BANCO FA LA COSA CHE ROMPE: muove il mouse di continuo (20
  `pointerMove` al secondo, in una sola `PerformActions`) per tutta la
  sessione, con Firefox VERO e VISIBILE sul tablet.  ⛔ Senza quel movimento la
  stessa misura e' verde e non dice niente.

═══════════════════════════════════════════════════════════════════════════════
`[M]` I DUE NUMERI CHE HA PRODOTTO — 23 settembre 2026, scatola `rete11-kde`
═══════════════════════════════════════════════════════════════════════════════
    PRIMA della cura       22 battiti in 3 minuti · il `da_ms` piu' lungo
                           **46 192 ms** — il battito si poteva rimandare
                           all'infinito, e il 58 % dei secondi aveva lo schermo
                           fermo, con blocchi fino a 6 minuti.
    DOPO la cura          508 battiti in 8 minuti · il `da_ms` piu' lungo
                           **1 102 ms** · 0 secondi fermi su 340.

⚠ E il numero che conta non e' la percentuale: e' **il blocco PIU' LUNGO**.
  Una media si puo' guardare e dire «va bene»; sei minuti di schermo fermo no.

═══════════════════════════════════════════════════════════════════════════════
⛔ COME SI LEGGE IL RISULTATO
═══════════════════════════════════════════════════════════════════════════════
Il banco guarda `consegnati` della pagina UNA VOLTA AL SECONDO e conta i
secondi in cui non e' cresciuto.  ⭐ Da oggi (23 set 2026, sera) c'e' anche il
VERDETTO: `giudica_il_blocco()` guarda il blocco piu' lungo e da' 0 / 1 / 3,
e `--schermo-congelato` innesta il guasto senza ricompilare (SIGSTOP al
compositore dell'inquilino).  ⚠ La soglia e' provvisoria `[?]`: che cosa
manca per chiamarla una maglia sta in fondo a questo file, sotto «PERCHE' NON
E' (ANCORA) UNA MAGLIA DELLA RETE».

⭐⭐ E LO STESSO GESTO E LO STESSO GIUDICE GIRANO NEGLI SCENARI DELLA NOTTE:
   `scenari/_comune.py` importa da qui `muovi`, `giudica_il_blocco` e il
   `Congelatore` (il `Topo` del banco).  ⛔ Qui c'e' l'originale, e non se ne
   fa una copia.

⚠ E NON REIMPLEMENTA NIENTE: l'inquilino, la scena, il browser vero e i
  contatori vengono da `stress_nucleo`; la scena testimone da `stress_occhio`.
"""
import argparse
import importlib.util
import json
import os
import sys
import time

BANCHI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUI = os.path.dirname(os.path.abspath(__file__))


def carica(nome, percorso):
    s = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(s)
    sys.modules[nome] = m
    s.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
#  LA PARTE PURA — ⛔ si certifica senza toccare niente
# ═══════════════════════════════════════════════════════════════════════════
def blocchi(serie, chiave="consegnati"):
    """⭐ I TRATTI in cui il contatore non e' cresciuto — la sola cosa che conta.

    Torna `(buoni, tratti)`: `buoni` sono le letture con un numero, `tratti`
    le coppie `(i, j)` di indici in `buoni` che hanno lo STESSO valore di fila.
    ⚠ Una lettura che si porta dietro un `tratto` diverso dalla precedente
      apre un blocco nuovo anche a valore uguale: fra due misure dello stesso
      scenario (i gradini della rete strozzata) passano secondi in cui nessuno
      guardava, ⛔ e cucirle insieme fabbricherebbe un blocco che nessuno ha
      visto.
    ⛔ E' l'UNICO posto in cui si decide che cosa e' «fermo»: `fermi()` e il
       giudice qui sotto lo leggono da qui, cosi' non possono dissentire.
    """
    buoni = [r for r in (serie or []) if r.get(chiave) is not None]
    tratti, inizio = [], 0
    for i in range(1, len(buoni) + 1):
        if (i == len(buoni) or buoni[i][chiave] != buoni[i - 1][chiave]
                or buoni[i].get("tratto") != buoni[i - 1].get("tratto")):
            tratti.append((inizio, i - 1))
            inizio = i
    return buoni, tratti


def fermi(serie, chiave="consegnati"):
    """⭐⭐ La FORMA del blocco, non solo quanto.

    Da una serie di letture al secondo torna
    `(secondi_fermi, secondi_guardati, blocco_piu_lungo_s)`.

    ⛔ Il numero che decide e' **il blocco piu' lungo**: `[M]` 23 set 2026, il
       58 % di secondi fermi non ha convinto nessuno finche' non si e' detto
       che il piu' lungo durava **sei minuti**.  Una percentuale si negozia,
       sei minuti di schermo fermo no.

    ⚠ Le letture senza numero (`None`) non contano ne' come ferme ne' come
      vive: «non lo so» non e' «fermo», ed e' la regola di tutto il progetto.
    """
    buoni, tratti = blocchi(serie, chiave)
    lunghi = [j - i for i, j in tratti]
    return sum(lunghi), max(0, len(buoni) - 1), max(lunghi or [0])


# ═══════════════════════════════════════════════════════════════════════════
#  ⭐⭐ IL GIUDICE SUL BLOCCO PIU' LUNGO — ed e' cio' che fa di questo banco
#      una guardia, e non soltanto uno strumento
# ═══════════════════════════════════════════════════════════════════════════
# `[?]` LA SOGLIA E' PROVVISORIA, e si dice perche'.  `[M]` 23 set 2026, scatola
#   `rete11-kde`, mouse in moto: col difetto il blocco piu' lungo era **46 192
#   ms** (e blocchi fino a sei minuti), curato **1 102 ms**.  ⇒ Fra i due c'e'
#   un fattore quaranta, e dieci secondi stanno larghi nel mezzo.
# ⛔ MA NON E' TARATA: due numeri presi in un pomeriggio non sono la
#    distribuzione del sano.  La taratura si fa con TRE O QUATTRO GIRI SANI
#    SUL FERRO (la UHD 730 integrata del server, ogni desktop, tutti e due i
#    browser), si guarda il blocco piu' lungo di ognuno e la soglia si mette nel
#    vuoto fra il peggiore dei sani e il guasto innestato — come e' stato fatto
#    per l'occhio (`stress_occhio.SOGLIE`).  Fino a quel giorno questo numero e'
#    una scelta DICHIARATA, e ogni riga lo porta con se' (`topo_soglia_s`).
SOGLIA_BLOCCO_S = 10.0          # [?] oltre: ROSSO — da tarare sul ferro
# `[?]` Sotto mezzo minuto guardato il giudice non giudica: un blocco di dieci
#   secondi in una serie di quindici non si distingue dall'accensione.
MINIMO_GUARDATO_S = 30.0        # [?]
# `[?]` E il mouse deve essersi mosso in almeno meta' dei secondi: ⛔ senza
#   movimento questa misura e' quella dei banchi EDUCATI, che il difetto del 23
#   settembre non lo vedevano — un verde senza mouse non direbbe niente.
QUOTA_COL_MOUSE = 0.5           # [?]


def _secondi_fra(a, b, intervalli):
    """I secondi fra due letture: dall'orologio se c'e' (`t`), se no uno per
    intervallo.  ⚠ Il giro «di un secondo» dura di piu' quando la fotografia
    dell'occhio e' lenta: contare gli intervalli allungherebbe la soglia di
    nascosto."""
    if isinstance(a.get("t"), (int, float)) and isinstance(b.get("t"), (int, float)):
        return max(0.0, float(b["t"]) - float(a["t"]))
    return float(intervalli)


def blocco_piu_lungo_s(serie, chiave="consegnati"):
    """⭐ `(secondi, lettura_d_inizio)` del blocco piu' lungo senza fotogrammi
    nuovi.  ⛔ Il numero su cui si decide: non una media, non una quota."""
    buoni, tratti = blocchi(serie, chiave)
    peggio, da = 0.0, None
    for i, j in tratti:
        s = _secondi_fra(buoni[i], buoni[j], j - i)
        if s > peggio:
            peggio, da = s, buoni[i]
    return peggio, da


def giudica_il_blocco(serie, soglia_s=SOGLIA_BLOCCO_S, minimo_s=MINIMO_GUARDATO_S,
                      quota_col_mouse=QUOTA_COL_MOUSE, chiave="consegnati"):
    """⭐⭐ `(esito, perche, numeri)` — 0 verde · 1 rosso · 3 «non ho potuto
    guardare».  FUNZIONE PURA: la serie entra, il verdetto esce.

    La serie e' quella che il banco legge UNA VOLTA AL SECONDO: ogni lettura
    `{"t", "consegnati", "mosse", "tratto"}`, dove `mosse` sono i movimenti del
    mouse mandati nel secondo PRIMA di quella lettura.
    ⛔ Tre modi di dire 3, e nessuno e' un verde:
       · la serie e' troppo corta (meno di `minimo_s` guardati);
       · la serie non dice se il mouse si muoveva (nessuna `mosse`);
       · il mouse si e' mosso in meno di `quota_col_mouse` dei secondi.
    ⭐ Il bordo: un blocco LUNGO QUANTO la soglia e' verde, uno che la supera
       e' rosso.
    """
    buoni, _ = blocchi(serie, chiave)
    coppie = [(a, b) for a, b in zip(buoni, buoni[1:])
              if a.get("tratto") == b.get("tratto")]
    guardati = sum(_secondi_fra(a, b, 1) for a, b in coppie)
    numeri = {"topo_guardati_s": round(guardati, 1), "topo_soglia_s": soglia_s,
              "topo_letture": len(buoni)}
    if not coppie or guardati < minimo_s:
        return 3, ("serie troppo corta: %.0f s guardati, ne servono %.0f per "
                   "giudicare un blocco" % (guardati, minimo_s)), numeri
    if not any("mosse" in r for r in buoni):
        return 3, ("la serie non dice se il mouse si muoveva: senza movimento "
                   "questa misura e' quella dei banchi educati"), numeri
    col_mouse = sum(1 for a, b in coppie if (b.get("mosse") or 0) > 0)
    quota = col_mouse / float(len(coppie))
    numeri["topo_col_mouse_per_cento"] = round(100.0 * quota, 1)
    if quota < quota_col_mouse:
        return 3, ("il mouse si e' mosso solo nel %.0f %% dei secondi (ne serve "
                   "il %.0f %%): non ho guardato quel che questa guardia cerca"
                   % (100.0 * quota, 100.0 * quota_col_mouse)), numeri
    blocco, da = blocco_piu_lungo_s(serie, chiave)
    fermi_n, _, _ = fermi(serie, chiave)
    numeri.update({"topo_blocco_s": round(blocco, 1), "topo_fermi": fermi_n})
    if da is not None and da.get("ora"):
        numeri["topo_blocco_dalle"] = da["ora"]
    if blocco > soglia_s:
        return 1, ("⛔ LO SCHERMO SI E' FERMATO PER %.1f s MENTRE IL MOUSE SI "
                   "MUOVEVA (soglia %.0f s, su %.0f s guardati)"
                   % (blocco, soglia_s, guardati)), numeri
    return 0, ("il blocco piu' lungo senza fotogrammi nuovi e' %.1f s (soglia "
               "%.0f s), su %.0f s guardati col mouse in moto nel %.0f %% dei "
               "secondi" % (blocco, soglia_s, guardati, 100.0 * quota)), numeri


def esito_col_guasto(esito, chiesto, innestato):
    """⭐ `(esito, frase)` — il verdetto, riletto sapendo se c'era il guasto.

    ⛔⛔ Un giro col guasto chiesto e NON innestato non puo' dare verde: non
        prova niente della guardia (3).  Ma un suo ROSSO resta rosso — e' del
        prodotto, e nasconderlo sarebbe peggio.
    ⭐ Col guasto innestato il rosso e' quel che si vuole vedere, e LO SI DICE;
       ⛔ il verde e' la guardia cieca, e lo si dice piu' forte.
    """
    if not chiesto:
        return esito, ""
    if not innestato:
        if esito == 1:
            return 1, ("  ⚠ il guasto chiesto NON si e' potuto innestare: questo "
                       "rosso e' del prodotto, non del guasto")
        return 3, ("  ⛔ il guasto chiesto NON si e' innestato: questo giro non "
                   "prova niente della guardia")
    if esito == 1:
        return 1, "  ⭐ il guasto innestato e' stato visto"
    if esito == 0:
        return 0, ("  ⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO: con lo schermo "
                   "congelato la guardia ha detto verde, e' CIECA")
    return 3, "  ⚠ il guasto e' stato innestato ma la misura non ha potuto guardare"


# ═══════════════════════════════════════════════════════════════════════════
#  ⛔ IL GUASTO INNESTATO SENZA RICOMPILARE — lo schermo congelato
# ═══════════════════════════════════════════════════════════════════════════
# Il difetto del 23 settembre si rimetteva solo toccando `batti_fra()` in C.
# ⭐ Il suo EFFETTO pero' si puo' produrre da fuori: si FERMA il compositore
#   dell'inquilino (SIGSTOP) per venticinque secondi mentre il mouse si muove
#   ⇒ nessun fotogramma nuovo, come quando il battito non batteva.  E' quel che
#   la guardia deve vedere, ed e' lo stesso gesto di `11-c3` (SIGSTOP al
#   codificatore), un piano piu' in basso.
# ⛔⛔ E SI RILASCIA SEMPRE, due volte: dal tablet (`rilascia()`, chiamata dai
#     `finally`) E dentro la scatola, dove un cane da guardia staccato col suo
#     `setsid` manda il SIGCONT allo scadere anche se il tablet muore a meta'.
#     ⚠ Un compositore lasciato fermo e' una sessione morta che sembra viva.
CONGELA_S = 25.0

# ⭐ IL COMPOSITORE SI CERCA, NON SI NOMINA.  Si prende il socket Wayland in
#   ASCOLTO nella cartella dell'inquilino (`/proc/net/unix`, bandiera
#   `__SO_ACCEPTCON`) e si cerca chi tiene in mano quel socket: ⭐ e' il
#   compositore per definizione, qualunque sia il suo nome — gnome-shell,
#   kwin_wayland (col suo `kwin_wayland_wrapper`, che tiene lo stesso socket e
#   si ferma con lui), labwc.  ⛔ Una tavola di nomi per desktop sarebbe un
#   quinto desktop che tace.  E solo processi DI QUELL'UTENTE: mai un altro
#   inquilino, mai `nictest`.
COPIONE_CERCA = r"""# cerca-il-compositore
import os, pwd, sys
try:
    uid = pwd.getpwnam(sys.argv[1]).pw_uid
except (KeyError, IndexError):
    print("NESSUNO utente-sconosciuto"); sys.exit(0)
cartella = "/run/user/%d/" % uid
inodi = {}
for riga in open("/proc/net/unix").read().splitlines()[1:]:
    p = riga.split()
    if len(p) < 8:
        continue
    nome = os.path.basename(p[7])
    if (p[7].startswith(cartella) and nome.startswith("wayland-")
            and not nome.endswith(".lock") and int(p[3], 16) & 0x10000):
        inodi["socket:[%s]" % p[6]] = p[7]
if not inodi:
    print("NESSUNO nessun-socket-in-ascolto-in-%s" % cartella); sys.exit(0)
for pid in sorted((d for d in os.listdir("/proc") if d.isdigit()), key=int):
    try:
        if os.stat("/proc/" + pid).st_uid != uid:
            continue
        fd = os.listdir("/proc/%s/fd" % pid)
    except OSError:
        continue
    for f in fd:
        try:
            dove = os.readlink("/proc/%s/fd/%s" % (pid, f))
        except OSError:
            continue
        if dove in inodi:
            nome = open("/proc/%s/comm" % pid).read().strip()
            print("COMPOSITORE %s %s %s" % (pid, nome, inodi[dove]))
            break
"""


def copione_congela(pid, secondi):
    """⛔ Prima il cane da guardia, POI il SIGSTOP: se il secondo passo va
    storto il primo c'e' gia'.  E si guarda lo STATO di quei pid, non «qualcuno
    in T» (`LEZIONI.md` §1.52)."""
    p = " ".join(str(int(x)) for x in pid)
    return ("# congela-il-compositore\n"
            "setsid sh -c 'sleep %d; kill -CONT %s 2>/dev/null' "
            "</dev/null >/dev/null 2>&1 &\n"
            "kill -STOP %s 2>/dev/null\n"
            "sleep 1\n"
            "for p in %s; do echo \"STATO $p $(ps -o stat= -p $p 2>/dev/null)\"; done\n"
            % (int(secondi) + 5, p, p, p))


def copione_scongela(pid):
    p = " ".join(str(int(x)) for x in pid)
    return ("# scongela-il-compositore\n"
            "kill -CONT %s 2>/dev/null\n"
            "sleep 0.5\n"
            "for p in %s; do echo \"STATO $p $(ps -o stat= -p $p 2>/dev/null)\"; done\n"
            % (p, p))


def leggi_il_compositore(testo):
    """`[(pid, nome)]` dalle righe `COMPOSITORE pid nome socket` — pura."""
    fuori, visti = [], set()
    for riga in (testo or "").splitlines():
        p = riga.split()
        if len(p) >= 3 and p[0] == "COMPOSITORE" and p[1].isdigit():
            if int(p[1]) not in visti:
                visti.add(int(p[1]))
                fuori.append((int(p[1]), p[2]))
    return fuori


def leggi_gli_stati(testo):
    """`{pid: stato}` dalle righe `STATO pid stato` — pura.  ⚠ Un pid senza
    stato (processo sparito) resta con `""`: non e' fermo e non e' vivo."""
    fuori = {}
    for riga in (testo or "").splitlines():
        p = riga.split()
        if len(p) >= 2 and p[0] == "STATO" and p[1].isdigit():
            fuori[int(p[1])] = p[2] if len(p) >= 3 else ""
    return fuori


class Congelatore(object):
    """⛔ Il guasto innestato: congela il compositore dell'inquilino, e lo
    rilascia.  ⚠ Parla con la scatola per il nucleo (`nucleo.dentro`, le SUE
    firme): nessuna strada nuova verso il server."""

    def __init__(self, nucleo, desktop, chi, secondi=CONGELA_S):
        self.n, self.desktop, self.chi = nucleo, desktop, chi
        self.secondi = float(secondi)
        self.pid, self.nomi, self.fermati = [], [], []
        self.da = self.a = None
        self.rilasciato = None
        self.perche = ""

    def innesta(self):
        """Torna True se ALMENO un processo del compositore e' finito in T."""
        _, u, e = self.n.dentro(self.desktop, COPIONE_CERCA, "python3",
                                [self.chi], 90)
        trovati = leggi_il_compositore(u)
        if not trovati:
            self.perche = ("non ho trovato il compositore di %s: %s"
                           % (self.chi, ((u or "") + " " + (e or "")).strip()[-160:]))
            return False
        self.pid = [p for p, _ in trovati]
        self.nomi = [n for _, n in trovati]
        _, u, e = self.n.dentro(self.desktop, copione_congela(self.pid, self.secondi),
                                "sh", None, 90)
        self.da = time.time()
        stati = leggi_gli_stati(u)
        self.fermati = [p for p in self.pid if stati.get(p, "").startswith("T")]
        if not self.fermati:
            self.perche = ("SIGSTOP mandato a %s ma nessuno e' in stato T: %s"
                           % (" ".join(self.nomi), (u or e or "")[-160:]))
            return False
        self.perche = ("congelato %s (pid %s) per %.0f s"
                       % ("+".join(self.nomi), " ".join(map(str, self.fermati)),
                          self.secondi))
        return True

    def e_ora(self):
        return (self.da is not None and self.rilasciato is None
                and time.time() >= self.da + self.secondi)

    def rilascia(self):
        """⭐ Si puo' chiamare quante volte si vuole: il secondo SIGCONT non fa
        niente.  ⛔ E non solleva mai: sta nei `finally`."""
        if not self.pid or self.rilasciato:
            return self.rilasciato
        try:
            _, u, _ = self.n.dentro(self.desktop, copione_scongela(self.pid),
                                    "sh", None, 90)
            stati = leggi_gli_stati(u)
            self.rilasciato = not any(stati.get(p, "").startswith("T")
                                      for p in self.pid)
        except Exception as e:                           # noqa: BLE001
            self.perche += ("  ⚠ il SIGCONT dal tablet non e' partito (%s): lo "
                            "manda il cane da guardia nella scatola" % str(e)[:80])
            self.rilasciato = False
        self.a = time.time()
        return self.rilasciato

    def rapporto(self):
        return {"chiesto_s": self.secondi, "compositore": self.nomi,
                "pid": self.pid, "fermati": self.fermati,
                "innestato": bool(self.fermati),
                "durato_s": (round(self.a - self.da, 1)
                             if self.da is not None and self.a is not None else None),
                "rilasciato": self.rilasciato, "perche": self.perche}


def gesti_di_un_secondo(passo, x0=300, y0=300, quanti=20, durata_ms=50):
    """⭐ Un secondo di movimento VERO, in una sola andata e ritorno.

    ⛔ Venti `pointerMove` da 50 ms l'uno: e' il ritmo con cui un utente che
       muove il mouse riempie il canale di input, ed e' esattamente la cosa che
       teneva fermo il battito del server.
    ⚠ Una sola `PerformActions` per secondo, non venti chiamate: venti andate e
      ritorni di Marionette misurerebbero Marionette, non il prodotto.
    ⚠ E la figura resta nel MEZZO (300..500 × 300..450): lontana dagli angoli
      caldi di GNOME e KDE e dai pannelli, che altrimenti aprirebbero una
      panoramica sopra la scena e l'occhio la leggerebbe come un guasto.
    """
    return [{"type": "pointerMove",
             "x": int(x0 + 200 * ((i + passo) % 5) / 4.0),
             "y": int(y0 + 150 * ((i + passo) % 3) / 2.0),
             "origin": "viewport", "duration": durata_ms}
            for i in range(quanti)]


# ⭐ I due passaggi del decodificatore che la pagina non mette su `window`:
#   `fuori` (quanti ne ha consegnati il decodificatore) e `dentro` (quanti
#   gliene abbiamo dato e non sono usciti).  ⛔ Sono la meta' del conto che dice
#   DOVE si ferma l'immagine (`src/pagina.html`, `4a06829`).
JS_DOVE = r"""
const R = window.REMOTIX, s = R && R.schermo, c = s && s.conti;
if (!c) return {};
return {fuori: c.usciti, dentro: (c.consegnati - c.usciti)};
"""


# ═══════════════════════════════════════════════════════════════════════════
#  LA MISURA VIVA
# ═══════════════════════════════════════════════════════════════════════════
def muovi(browser, passo, quanti=20, durata_ms=50):
    """Il gesto, mandato al browser vero.  Torna quanti movimenti ha mandato.

    ⚠ Si passa dal guidatore Marionette di `12-client-veri.py`
      (`browser.g.m.chiama`): ⛔ `Browser.muovi()` sposta il puntatore UNA
      volta, e una volta al secondo non riempie niente.
    ⭐ Chrome parla CDP (`browser.g.cdp`): li' non c'e' una `PerformActions`
       con le durate, ⇒ un `Input.dispatchMouseEvent` per movimento, e il
       ritmo lo tiene l'orologio.  Sono eventi FIDATI nel renderer, come quelli
       di `GuidaCdp.muovi` — ⛔ non eventi costruiti in JavaScript.
    ⚠ E un browser senza guidatore (il nucleo finto degli scenari) passa da
      `browser.muovi(x, y)`, allo stesso ritmo: la certificazione deve provare
      la stessa cadenza del ferro, non una piu' comoda.
    ⭐ `quanti` lo sceglie chi chiama: gli scenari riempiono il RESTO del loro
       secondo (dopo contatori e fotografia), non un secondo in piu'.
    """
    gesti = gesti_di_un_secondo(passo, quanti=quanti, durata_ms=durata_ms)
    g = getattr(browser, "g", None)
    m = getattr(g, "m", None)
    if m is not None and getattr(browser, "marca", "firefox") == "firefox":
        m.chiama("WebDriver:PerformActions",
                 {"actions": [{"type": "pointer", "id": "topo",
                               "parameters": {"pointerType": "mouse"},
                               "actions": gesti}]})
        return len(gesti)
    cdp = getattr(g, "cdp", None)
    t0 = time.time()
    for i, a in enumerate(gesti):
        if cdp is not None:
            cdp.chiama("Input.dispatchMouseEvent", type="mouseMoved",
                       x=a["x"], y=a["y"])
        else:
            browser.muovi(a["x"], a["y"])
        resta = t0 + (i + 1) * durata_ms / 1000.0 - time.time()
        if resta > 0:
            time.sleep(resta)
    return len(gesti)


def gira(o):
    nucleo = carica("stress_nucleo", os.path.join(QUI, "stress_nucleo.py"))
    occhio = carica("stress_occhio", os.path.join(QUI, "stress_occhio.py"))
    porta = nucleo.PORTE[o.desktop]
    os.makedirs(o.uscita, exist_ok=True)
    chi = "%s%d" % (o.inquilino, 1 if o.browser == "firefox" else 2)

    print("== l'inquilino ==", flush=True)
    fatto, perche = nucleo.crea_inquilino(o.desktop, chi, o.parola)
    print("   %s — %s" % (fatto, perche), flush=True)
    if not fatto:
        return 3

    print("== la scena DICHIARATA ==", flush=True)
    fatto, perche = occhio.deposita_scena(nucleo, o.desktop)
    print("   %s — %s" % (fatto, perche), flush=True)
    if not fatto:
        return 3

    t_box = nucleo.istante_nella_scatola(o.desktop)
    print("   orologio della scatola: %s (UTC)" % t_box, flush=True)

    serie, b, codice, cong = [], None, 3, None
    try:
        print("== il browser VERO e VISIBILE ==", flush=True)
        b = nucleo.avvia_browser(o.browser, porta)
        ok, perche = b.apri()
        print("   apri: %s — %s" % (ok, perche), flush=True)
        if not ok:
            return 3
        esito, perche = b.entra(chi, o.parola)
        print("   entra: esito %s — %s" % (esito, perche), flush=True)
        if esito != 0:
            return 3

        # ⛔⛔ LA CORSA COL COMPOSITORE: la sessione grafica dell'inquilino
        #     NASCE ADESSO, e nell'istante in cui il client e' ammesso il
        #     socket wayland non c'e' ancora.  ⇒ Si aspetta (12 × 5 s), e se
        #     non si accende **si dice e si smette**: misurare un desktop fermo
        #     credendo di misurare una scena in movimento e' il modo peggiore
        #     in cui questo banco potrebbe sbagliare (`stress_nucleo.scena`).
        accesa, perche = nucleo.scena(o.desktop, o.scena, chi, giri=12, passo=5.0)
        print("   scena: %s — %s" % ("ACCESA" if accesa else "⛔ SPENTA", perche),
              flush=True)
        if not accesa:
            print("   ⛔ non misuro: senza scena questi numeri non direbbero "
                  "niente e sembrerebbero buoni.", flush=True)
            return 3
        time.sleep(o.attesa_scena)

        print("== %g minuti · MOUSE CHE SI MUOVE DI CONTINUO ==" % o.minuti,
              flush=True)
        t0 = time.time()
        fine, prossimo, passo, mosse = t0 + o.minuti * 60, t0, 0, 0
        mosse_ora = 0
        if o.schermo_congelato:
            cong = Congelatore(nucleo, o.desktop, chi, o.schermo_congelato)
            print("   ⛔ GUASTO INNESTATO: il compositore di %s si congela per "
                  "%.0f s dopo %.0f s di misura" % (chi, o.schermo_congelato,
                                                    o.congela_dopo), flush=True)
        while time.time() < fine:
            prossimo += 1.0
            # ⛔ Il guasto parte e finisce DENTRO la misura: congelare prima o
            #    dopo vorrebbe dire non guardarlo.
            if (cong is not None and cong.da is None and not cong.perche
                    and time.time() - t0 >= o.congela_dopo):
                ok = cong.innesta()
                print("   %s %s" % ("⛔" if ok else "⚠", cong.perche), flush=True)
            elif cong is not None and cong.e_ora():
                print("   rilascio: %s" % cong.rilascia(), flush=True)
            c = nucleo.conta_dalla_pagina(b)
            try:
                x = b.js(JS_DOVE)
            except Exception:                                # noqa: BLE001
                x = None
            if isinstance(x, dict):
                c.update(x)
            c["t"] = time.time()
            c["ora"] = time.strftime("%H:%M:%S")
            # ⭐ I movimenti del secondo PRIMA di questa lettura: e' cosi' che
            #   il giudice sa se il mouse si muoveva mentre lo schermo taceva.
            c["mosse"] = mosse_ora
            serie.append(c)
            if len(serie) % 30 == 0:
                print("   %s  consegnati=%s dipinti=%s mosse=%d"
                      % (c["ora"], c.get("consegnati"), c.get("dipinti"), mosse),
                      flush=True)
            # ⭐ E il movimento riempie il resto del secondo: e' la cosa che
            #   rompe, e va fatta SEMPRE, non ogni tanto.
            try:
                passo += 1
                mosse_ora = muovi(b, passo)
                mosse += mosse_ora
            except Exception as e:                           # noqa: BLE001
                mosse_ora = 0
                print("   ⚠ mouse: %s" % e, flush=True)
            resta = prossimo - time.time()
            if resta > 0:
                time.sleep(resta)
        codice = 0

        print("== chiudo la SCHEDA (congedo 0x01) ==", flush=True)
        b.vai("about:blank")
        time.sleep(4)
    finally:
        # ⛔⛔ IL COMPOSITORE SI RILASCIA PER PRIMO, comunque sia andata: uno
        #     sgombero che trova processi in T non li uccide con un TERM.
        if cong is not None:
            print("   rilascio del compositore: %s" % cong.rilascia(), flush=True)
        if b is not None:
            try:
                b.chiudi()
            except Exception:                            # noqa: BLE001
                pass
        # ⛔ E L'INQUILINO SI TOGLIE: `[M]` 22 set 2026, i residui di sessioni
        #    di prova hanno fatto smettere di rispondere `WebDriver:NewSession`.
        #    ⚠ `--lascia-l-inquilino` serve a chi vuole guardare la scatola dopo.
        if not o.lascia_l_inquilino:
            tolto, dice = nucleo.sgombera(o.desktop, chi)
            print("   sgombero: %s (%s)"
                  % ("pulito" if tolto else "⚠ resta roba", dice), flush=True)

    print("\n== I NUMERI DELLA PAGINA ==", flush=True)
    buoni = [r for r in serie if r.get("consegnati") is not None]
    riass = {}
    if buoni:
        u = buoni[-1]
        manc = (u["consegnati"] or 0) - (u["dipinti"] or 0)
        print("   consegnati %s · dipinti %s · MANCANO %d (%.1f %%)"
              % (u["consegnati"], u["dipinti"], manc,
                 100.0 * manc / max(1, u["consegnati"] or 1)), flush=True)
        print("   buchi %s · chiavi chieste %s"
              % (u.get("buchi"), u.get("chiavi_chieste")), flush=True)
        f, quanti, piu_lungo = fermi(serie)
        print("   ⚠ secondi in cui `consegnati` NON e' cresciuto: %d su %d "
              "(%.1f %%) — il blocco PIU' LUNGO: %d s"
              % (f, quanti, 100.0 * f / max(1, quanti), piu_lungo), flush=True)
        riass = {"consegnati": u["consegnati"], "dipinti": u["dipinti"],
                 "secondi_fermi": f, "secondi": quanti,
                 "blocco_piu_lungo_s": piu_lungo,
                 "chiavi_chieste": u.get("chiavi_chieste")}

    # ⭐⭐ IL VERDETTO — da oggi c'e', ed e' il giudice sul blocco piu' lungo.
    #   ⛔ Un 3 dello strumento (inquilino, scena, browser) resta 3: il giudice
    #      parla solo se la misura e' stata fatta.
    if codice == 0:
        esito, perche, numeri = giudica_il_blocco(serie)
        esito, frase = esito_col_guasto(esito, bool(o.schermo_congelato),
                                        bool(cong is not None and cong.fermati))
        codice = esito
        riass.update(numeri)
        riass["esito"], riass["perche"] = esito, perche + frase
        if cong is not None:
            riass["guasto_innestato"] = cong.rapporto()
        print("\n== IL VERDETTO: esito %d ==\n   %s%s" % (esito, perche, frase),
              flush=True)
    dove = os.path.join(o.uscita, "serie.json")
    with open(dove, "w", encoding="utf-8") as f:
        json.dump({"riassunto": riass, "serie": serie, "t_box": t_box,
                   "chi": chi, "desktop": o.desktop, "browser": o.browser,
                   "minuti": o.minuti}, f, ensure_ascii=False)
    print("   t_box=%s chi=%s · serie in %s" % (t_box, chi, dove), flush=True)
    return codice


# ═══════════════════════════════════════════════════════════════════════════
#  LA CERTIFICAZIONE — ⛔ prima si prova che sa dire di NO
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    guai = [0]

    def p(nome, ottenuto, atteso):
        bene = ottenuto == atteso
        if not bene:
            guai[0] += 1
        print("  %s  %-60s %s" % ("OK " if bene else "NO ", nome,
                                  "" if bene else "⇒ %r (volevo %r)" % (ottenuto, atteso)))

    print("\n══ il cliente che non sta fermo — la certificazione ═════════════")
    print("\n── il conto dei secondi fermi ──")
    vivo = [{"consegnati": i} for i in range(11)]
    p("⭐ undici letture che crescono: zero secondi fermi", fermi(vivo), (0, 10, 0))
    fermo = [{"consegnati": 5} for _ in range(11)]
    p("⛔ undici letture uguali: dieci secondi fermi, blocco lungo dieci",
      fermi(fermo), (10, 10, 10))
    misto = [{"consegnati": n} for n in (1, 1, 1, 2, 3, 3, 4)]
    p("⭐⭐ e la FORMA: sei fermi… no, tre fermi e il blocco piu' lungo e' due",
      fermi(misto), (3, 6, 2))
    p("⛔ due blocchi corti non fanno un blocco lungo",
      fermi([{"consegnati": n} for n in (1, 1, 2, 2, 3)]), (2, 4, 1))
    p("⚠ una serie vuota non fa cadere niente", fermi([]), (0, 0, 0))
    p("⚠ una lettura sola non ha intervalli", fermi([{"consegnati": 1}]), (0, 0, 0))
    p("⛔ le letture «non lo so» non contano come ferme",
      fermi([{"consegnati": 1}, {"consegnati": None}, {"consegnati": 2}]),
      (0, 1, 0))
    p("⛔ e non contano nemmeno come vive",
      fermi([{"consegnati": None}, {"consegnati": None}]), (0, 0, 0))

    print("\n── i gesti del mouse ──")
    g = gesti_di_un_secondo(0)
    p("⭐ venti movimenti in un secondo", len(g), 20)
    p("⭐ da 50 ms l'uno ⇒ un secondo pieno", sum(a["duration"] for a in g), 1000)
    p("⛔ e si MUOVONO davvero (non venti volte lo stesso punto)",
      len({(a["x"], a["y"]) for a in g}) > 1, True)
    p("⚠ e restano dentro la finestra (origine «viewport», mai negativi)",
      all(a["origin"] == "viewport" and a["x"] >= 0 and a["y"] >= 0 for a in g), True)
    p("⭐ il passo sposta la figura (due secondi non sono identici)",
      gesti_di_un_secondo(0) != gesti_di_un_secondo(1), True)

    print("\n── i tratti: una misura nuova non si cuce alla vecchia ──")
    cuciti = [{"consegnati": 5, "tratto": 1}, {"consegnati": 5, "tratto": 1},
              {"consegnati": 5, "tratto": 2}, {"consegnati": 5, "tratto": 2}]
    p("⛔ quattro letture uguali in DUE tratti: due blocchi da uno, non uno da tre",
      fermi(cuciti), (2, 3, 1))

    print("\n── ⭐⭐ il giudice sul blocco piu' lungo ──")

    def serie(valori, passo_s=1.0, mosse=20, tratto=1):
        return [{"t": 1000.0 + i * passo_s, "consegnati": v, "mosse": mosse,
                 "tratto": tratto} for i, v in enumerate(valori)]

    def crescente(n, da=0):
        return [da + 40 * i for i in range(n)]

    # ⭐ il sano: tre minuti, e ogni tanto un secondo senza fotogrammi nuovi
    sana = crescente(60) + [2360] + crescente(120, 2400)
    e, perche, num = giudica_il_blocco(serie(sana))
    p("⭐ serie SANA (tre minuti, blocco max 1 s) ⇒ 0", e, 0)
    p("   e il numero che la regge e' 1 s", num.get("topo_blocco_s"), 1.0)
    # ⛔ il difetto del 23 settembre: 46 s fermo mentre il mouse si muove
    # ⚠ l'ultima lettura che cresce (2360) apre il blocco: 1 + 46 letture uguali
    #   sono 46 intervalli fermi, cioe' 46 s.
    difetto = crescente(60) + [2360] * 46 + crescente(60, 2400)
    e, perche, num = giudica_il_blocco(serie(difetto))
    p("⛔ serie col DIFETTO (blocco 46 s) ⇒ 1", e, 1)
    p("   e il numero e' 46 s", num.get("topo_blocco_s"), 46.0)
    p("   e il perche' lo dice in parole", "SI E' FERMATO" in perche, True)
    # ⚠ il bordo della soglia: uguale e' verde, oltre e' rosso
    p("⚠ bordo: blocco di 10 s = soglia ⇒ 0",
      giudica_il_blocco(serie(crescente(40) + [9999] * 11 + crescente(40, 10000)))[0], 0)
    p("⚠ bordo: blocco di 11 s > soglia ⇒ 1",
      giudica_il_blocco(serie(crescente(40) + [9999] * 12 + crescente(40, 10000)))[0], 1)
    p("⚠ bordo: e la soglia si puo' passare da fuori (5 s ⇒ il 10 diventa rosso)",
      giudica_il_blocco(serie(crescente(40) + [9999] * 11 + crescente(40, 10000)),
                        soglia_s=5.0)[0], 1)
    # ⛔ i secondi si contano con l'OROLOGIO, non con gli intervalli
    lenta = serie(crescente(30) + [7777] * 9 + crescente(30, 8000), passo_s=1.5)
    p("⛔ giro da 1,5 s: 8 intervalli fermi sono 12 s ⇒ 1 (non 8 ⇒ 0)",
      giudica_il_blocco(lenta)[0], 1)
    # ⛔ i tre modi di dire 3
    p("⛔ serie troppo corta (20 s) ⇒ 3", giudica_il_blocco(serie(crescente(21)))[0], 3)
    p("⛔ anche se dentro c'e' un blocco (15 s fermi su 20) ⇒ 3, non 1",
      giudica_il_blocco(serie([1] * 16 + crescente(5, 100)))[0], 3)
    p("⛔ serie vuota ⇒ 3", giudica_il_blocco([])[0], 3)
    p("⛔ senza movimento del mouse ⇒ 3",
      giudica_il_blocco(serie(crescente(120), mosse=0))[0], 3)
    p("⛔ e una serie che non dice le mosse ⇒ 3",
      giudica_il_blocco([{"t": 1000.0 + i, "consegnati": 40 * i}
                         for i in range(120)])[0], 3)
    poco = serie(crescente(120))
    for r in poco[:80]:
        r["mosse"] = 0
    p("⛔ il mouse mosso in un terzo dei secondi ⇒ 3", giudica_il_blocco(poco)[0], 3)
    p("⚠ «non lo so» in mezzo non fa un blocco (None non e' fermo)",
      giudica_il_blocco(serie(crescente(30) + [None] * 20 + crescente(30, 5000)))[0], 0)
    secondo = [dict(r, t=r["t"] + 60)
               for r in serie([5] * 8 + crescente(30, 10), tratto=2)]
    p("⚠ due misure in due tratti non si cuciono in un blocco",
      giudica_il_blocco(serie([5] * 8, tratto=1) + secondo)[0], 0)

    print("\n── il verdetto riletto col guasto ──")
    p("⭐ niente guasto: il verdetto e' quello", esito_col_guasto(0, False, False), (0, ""))
    visto = esito_col_guasto(1, True, True)
    p("⭐ guasto innestato e visto ⇒ 1, e lo dice",
      (visto[0], "stato visto" in visto[1]), (1, True))
    p("⛔⛔ guasto innestato e verde ⇒ la guardia e' CIECA, e lo dice",
      "CIECA" in esito_col_guasto(0, True, True)[1], True)
    p("⛔ guasto chiesto e non innestato: un verde diventa 3",
      esito_col_guasto(0, True, False)[0], 3)
    p("⛔ ma un rosso resta rosso (e' del prodotto)", esito_col_guasto(1, True, False)[0], 1)

    print("\n── il compositore si CERCA ──")
    p("⭐ il copione di ricerca e' python valido",
      bool(compile(COPIONE_CERCA, "cerca", "exec")), True)
    p("⭐ kwin e il suo involucro: due pid, due nomi",
      leggi_il_compositore("COMPOSITORE 812 kwin_wayland_wr /run/user/4099/wayland-0\n"
                           "COMPOSITORE 830 kwin_wayland /run/user/4099/wayland-0\n"),
      [(812, "kwin_wayland_wr"), (830, "kwin_wayland")])
    p("⚠ lo stesso pid due volte (due socket) conta una volta",
      leggi_il_compositore("COMPOSITORE 7 labwc /a/wayland-0\nCOMPOSITORE 7 labwc /a/wayland-1"),
      [(7, "labwc")])
    p("⛔ nessun compositore ⇒ lista vuota",
      leggi_il_compositore("NESSUNO nessun-socket-in-ascolto"), [])
    p("⭐ gli stati: T fermo, S vivo, vuoto sparito",
      leggi_gli_stati("STATO 812 Tl\nSTATO 830 Sl\nSTATO 9 \n"),
      {812: "Tl", 830: "Sl", 9: ""})
    c = copione_congela([812, 830], 25)
    p("⛔ il cane da guardia parte PRIMA del SIGSTOP",
      0 <= c.find("setsid") < c.find("kill -STOP"), True)
    p("⛔ e rilascia QUEI pid, dopo piu' dei 25 s del guasto",
      "sleep 30; kill -CONT 812 830" in c, True)

    class _NucleoFinto(object):
        def __init__(self, cerca, stop, cont="STATO 812 S\n"):
            self.r = {"cerca-il-compositore": cerca, "# congela-il": stop,
                      "scongela-il": cont}
            self.chiamate = []

        def dentro(self, desktop, copione, interprete="sh", argomenti=None,
                   secondi=180):
            testa = copione.splitlines()[0]
            self.chiamate.append(testa)
            for k, v in self.r.items():
                if k in testa:
                    return 0, v, ""
            return 0, "", ""

    n = _NucleoFinto("COMPOSITORE 812 kwin_wayland /r/wayland-0\n", "STATO 812 T\n")
    k = Congelatore(n, "kde", "c43u1", 25)
    p("⭐ il congelatore innesta, e dice CHI ha fermato", (k.innesta(), k.fermati),
      (True, [812]))
    p("⭐ e rilascia", k.rilascia(), True)
    p("⚠ e rilasciare due volte non manda un secondo SIGCONT",
      (k.rilascia(), sum("scongela" in x for x in n.chiamate)), (True, 1))
    k = Congelatore(_NucleoFinto("NESSUNO utente-sconosciuto", ""), "kde", "x", 25)
    p("⛔ nessun compositore ⇒ non innestato, e il perche'",
      (k.innesta(), "non ho trovato" in k.perche), (False, True))
    k = Congelatore(_NucleoFinto("COMPOSITORE 5 labwc /r/wayland-0", "STATO 5 S\n"),
                    "xfce", "x", 25)
    p("⛔ SIGSTOP mandato ma nessuno in T ⇒ NON innestato",
      (k.innesta(), k.fermati), (False, []))
    p("⚠ rilasciare un congelatore mai innestato non esplode",
      Congelatore(_NucleoFinto("", ""), "kde", "x").rilascia(), None)

    print("\n── il gesto, a tutti i browser ──")

    class _Chiama(object):
        def __init__(self):
            self.fatte = []

        def chiama(self, *a, **k):
            self.fatte.append((a, k))

    class _G(object):
        pass

    class _B(object):
        def __init__(self, marca, m=None, cdp=None):
            self.marca, self.g, self.mosse = marca, _G(), 0
            if m is not None:
                self.g.m = m
            if cdp is not None:
                self.g.cdp = cdp

        def muovi(self, x, y):
            self.mosse += 1

    m = _Chiama()
    fatte = muovi(_B("firefox", m=m), 0)
    p("⭐ Firefox: UNA PerformActions con tutti i movimenti dentro",
      (fatte, len(m.fatte), len(m.fatte[0][0][1]["actions"][0]["actions"])),
      (20, 1, 20))
    c = _Chiama()
    t0 = time.time()
    fatte = muovi(_B("chrome", cdp=c), 0, quanti=4)
    p("⭐ Chrome: un dispatchMouseEvent per movimento",
      (fatte, len(c.fatte), c.fatte[0][1].get("type")), (4, 4, "mouseMoved"))
    p("⭐ e al ritmo del Firefox (4 × 50 ms ≈ 0,2 s, non tutti insieme)",
      time.time() - t0 >= 0.18, True)
    b = _B("firefox")
    p("⚠ senza guidatore (il finto): browser.muovi, uno per movimento",
      (muovi(b, 0, quanti=3), b.mosse), (3, 3))

    print("\n%s  %d guai" % ("⭐ LA PARTE PURA REGGE." if guai[0] == 0
                             else "⛔ QUALCOSA NON TORNA.", guai[0]))
    print("⚠ il resto lo prova il ferro: questo banco vale quando gira contro "
          "una scatola vera, con un Firefox vero e visibile.")
    return 1 if guai[0] else 0


def main():
    a = argparse.ArgumentParser(
        description="un cliente che muove il mouse di continuo, e misura se "
                    "lo schermo si ferma")
    a.add_argument("--certifica", action="store_true",
                   help="le funzioni pure, senza toccare niente")
    a.add_argument("--desktop", default="kde")
    a.add_argument("--browser", default="firefox")
    a.add_argument("--minuti", type=float, default=8.0)
    a.add_argument("--inquilino", default="c43u")
    a.add_argument("--parola", default="prova-lunga-2026")
    a.add_argument("--scena", default="testimone")
    a.add_argument("--attesa-scena", type=float, default=25.0)
    # ⛔ IL GUASTO INNESTATO: il compositore dell'inquilino si congela per
    #    questi secondi (25 se non si dice) — e il giudice DEVE dare 1.
    a.add_argument("--schermo-congelato", type=float, nargs="?", const=CONGELA_S,
                   default=None, metavar="SECONDI",
                   help="⛔ il guasto innestato: SIGSTOP al compositore "
                        "dell'inquilino per SECONDI (25), poi SIGCONT")
    a.add_argument("--congela-dopo", type=float, default=30.0,
                   help="dopo quanti secondi di misura si congela")
    a.add_argument("--lascia-l-inquilino", action="store_true",
                   help="⚠ non sgombera: per guardare la scatola dopo")
    # ⛔ Su questo tablet `/tmp` sta in RAM: le serie vanno su disco vero.
    a.add_argument("--uscita", default="/home/nicfio/REMOTIX-misure/battito")
    o = a.parse_args()
    if o.certifica:
        return certifica()
    return gira(o)


if __name__ == "__main__":
    sys.exit(main())


# ═══════════════════════════════════════════════════════════════════════════
# ⚠⚠ PERCHE' NON E' (ANCORA) UNA MAGLIA DELLA RETE
# ═══════════════════════════════════════════════════════════════════════════
# La rete delle maglie ha tre regole: un GUASTO INNESTATO che la fa diventare
# rossa, un verdetto 0/1/3, e il tetto di tempo della notte.  La strada scritta
# qui il 23 settembre 2026 aveva tre passi; ⭐ la sera stessa i primi e il
# terzo sono FATTI, e resta la taratura:
#
#   1. ⭐ FATTO — il mouse si muove negli scenari che gia' esistono, come
#      comportamento NORMALE del cliente e non come scenario a parte:
#      `scenari/_comune.py` ha il `Topo`, `guarda_per(..., topo=b.topo)` muove
#      il mouse nel resto di ogni secondo (lo stesso `muovi()` di qui, adesso
#      anche per Chrome via CDP), e `C.pausa()` fa aspettare col mouse in moto
#      i rientri di `stacca_riattacca` e `riavvio_del_server`.  ⚠ `esci_rientra`
#      NO, e si dice perche' la': il suo giudice dei fantasmi vuole il desktop
#      fermo.  `REMOTIX_TOPO=no` lo spegne (la controprova del cliente educato).
#   2. ⚠ MEZZO FATTO — il giudice c'e' (`giudica_il_blocco`, 0/1/3, entra nel
#      verdetto degli scenari con `C.vede_il_topo`, accanto all'occhio e senza
#      togliere niente), ⛔ ma la soglia di 10 s e' PROVVISORIA `[?]`: va
#      tarata con tre o quattro giri SANI SUL FERRO, per desktop e per browser,
#      guardando il blocco piu' lungo di ognuno (`topo_blocco_s` nella riga).
#      `[M]` col difetto 46 192 ms, curato 1 102 ms: il fattore quaranta dice
#      che la soglia non e' delicata, non che e' giusta.
#   3. ⭐ FATTO, senza ricompilare — `--schermo-congelato` (qui e in
#      `_lancia.py`) congela per 25 s il compositore DELL'INQUILINO (cercato dal
#      socket Wayland in ascolto, non dal nome: gnome-shell, kwin_wayland,
#      labwc) e lo rilascia sempre, dal tablet e da un cane da guardia nella
#      scatola.  Col guasto il giudice DEVE dare 1, e la riga dice «il guasto
#      innestato e' stato visto» — o, forte, che la guardia e' cieca.
#
# ⛔ QUEL CHE RESTA, prima di chiamarla maglia della rete:
#    · la TARATURA sul ferro (punto 2), e poi il primo giro col guasto
#      innestato su ognuna delle scatole — ⚠ nessuno dei due e' stato fatto:
#      questa parte e' certificata solo col nucleo finto;
#    · ⚠ un dubbio che solo il ferro scioglie: se il server, a compositore
#      fermo, rimanda comunque un fotogramma (una chiave dell'immagine ferma),
#      `consegnati` cresce e il guasto innestato NON si vede.  Il banco lo
#      direbbe da solo («guardia cieca»), e allora il guasto va cercato un piano
#      piu' in basso;
#    · il tetto della notte: gli scenari lunghi (`pesante`, `lunga`) bastano,
#      ⚠ quelli corti (sotto i 30 s guardati) danno 3 e lo dicono.
