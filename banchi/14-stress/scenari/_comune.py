#!/usr/bin/env python3
"""_comune — quel che gli otto scenari della suite notturna condividono.

⭐ COSA C'E' QUI, e perche' non sta in ogni scenario:
   · il GIUDIZIO in una forma sola: 0 verde · 1 rosso · 3 «non ho potuto
     guardare».  ⛔ Un 3 non e' un verde, ed e' scritto in un posto solo;
   · il TETTO di tempo, che ogni scenario DEVE rispettare (una notte di misure
     non puo' dipendere dal fatto che una di esse finisca);
   · il BANCO — inquilino, browser, scena — che quasi tutti apparecchiano
     uguale, e che si sparecchia SEMPRE;
   · le tre cose che il nucleo non fa perche' non sono sue: riavviare il server
     (sta sull'ospite), strozzare la rete (sta sul tablet), uscire dalla
     sessione (e' un gesto del desktop, e cambia per desktop);
   · la misura delle STRISCE sulla tela;
   · ⭐⭐ l'OCCHIO (`Occhio`, `vede_l_occhio`, `conta_il_ritmo`): il giudice che
     GUARDA l'immagine invece di contarla.  ⛔ Senza di lui la suite ha dato
     verde due volte su un'immagine a mosaico — era il difetto piu' grave del
     23 settembre 2026, e non era nel prodotto;
   · ⭐⭐ il TOPO (`Topo`, `vede_il_topo`, `pausa`): il cliente che NON sta
     fermo — muove il mouse mentre si guarda, e giudica il blocco piu' lungo
     senza fotogrammi nuovi.  ⛔ Senza di lui lo schermo fermo per minuti del
     23 settembre 2026 passava verde in tutti gli scenari.

⛔⛔ E NON C'E' UN SECONDO NUCLEO.  Tutto quel che tocca la scatola, la pagina e
    il registro passa da `stress_nucleo.py`, con le SUE firme:

      dentro(desktop, copione, interprete="sh", argomenti=None, secondi=180)
                                                    → (codice, uscita, errore)
      crea_inquilino(desktop, chi, parola)           → (fatto, perche)
      sgombera(desktop, chi)
      scena(desktop, quale, chi, secondi=40)         → (accesa, perche)
      istante_nella_scatola(desktop)                 → "HH:MM:SS" (UTC)
      conta_dalla_pagina(browser) · conta_dal_server(desktop, da_istante, chi)
      avvia_browser(marca, porta, misura, tetto_s)   → Browser
      Browser: .apri() .entra(u,p,tetto_s) .chiudi() .misura(l,a) .fotografa()
               .vai() .ricarica() .muovi(x,y) .clic(x,y) .tasto(t) .js(...)

    ⚠ `[M]` 23 set 2026, e costa dirlo: la prima stesura di questo file
      INDOVINAVA le firme e scompattava DUE valori da `dentro`, che ne torna
      tre — «too many values to unpack».  ⛔ E il modulo finto con cui l'avevo
      provata aveva le firme sbagliate uguali: un finto che non ha le firme del
      vero non prova niente, e quello e' il difetto che l'ha nascosto.
      ⇒ Qui il nucleo si chiama com'e', e dove manca qualcosa lo si DICE invece
        di riscriverla.

⚠ QUESTO CODICE GIRA SUL TABLET: i browser veri stanno qui (decisione
  dell'utente, 22 set 2026 — «il tablet lo tengo acceso tutta la notte»).
"""
import json
import os
import re
import subprocess
import sys
import time

# ⛔ Il nucleo sta nella cartella SOPRA questa.  Senza questa riga, `esito()`
#    non puo' chiedergli di completare la riga quando gli scenari girano fuori
#    da `_lancia.py` (per esempio sotto `_prova_scenari.py`), e la riga esce
#    senza i numeri in vista — che e' il difetto del 23 set 2026.
_SOPRA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SOPRA not in sys.path:
    sys.path.append(_SOPRA)

# ⭐⭐ GLI OCCHI DEL GIUDICE.  ⛔ Senza di loro la suite conta i fotogrammi e
#    NON li guarda: un fotogramma sbagliato conta come uno giusto, ed e' il
#    verde falso della notte fra il 22 e il 23 settembre 2026 (due volte, mentre
#    l'utente guardava un'immagine a mosaico).  Il modulo sta un piano sopra e
#    si importa da solo; ⚠ se manca numpy o PIL il giro continua SENZA occhio —
#    un banco che non ha potuto guardare non accusa nessuno.
try:
    import stress_occhio as O                      # noqa: E402
    OCCHIO_PERCHE = ""
except Exception as _perche_no_occhio:             # noqa: BLE001
    O = None
    OCCHIO_PERCHE = "«stress_occhio» non si importa: %s" % str(_perche_no_occhio)[:160]

# ⭐⭐ LE MANI DEL CLIENTE, e il giudice che le guarda: vengono dal banco che le
#    ha inventate (`14-il-cliente-che-non-sta-fermo.py`), ⛔ non se ne fa una
#    copia.  Il 23 settembre 2026 un difetto che teneva lo schermo fermo per
#    minuti e' stato invisibile a TUTTI gli scenari, perche' nessuno muoveva il
#    mouse (memoria «il cliente educato»).  ⇒ Da qui il mouse si muove SEMPRE
#    mentre uno scenario guarda: e' il comportamento normale di un cliente.
#    ⚠ Se il banco non si importa, il giro va avanti senza topo e LO DICE (3).
try:
    import importlib.util as _iu
    _s14 = _iu.spec_from_file_location(
        "cliente_che_non_sta_fermo",
        os.path.join(_SOPRA, "14-il-cliente-che-non-sta-fermo.py"))
    B14 = _iu.module_from_spec(_s14)
    sys.modules["cliente_che_non_sta_fermo"] = B14
    _s14.loader.exec_module(B14)
    TOPO_PERCHE = ""
except Exception as _perche_no_topo:               # noqa: BLE001
    B14 = None
    TOPO_PERCHE = ("«14-il-cliente-che-non-sta-fermo» non si importa: %s"
                   % str(_perche_no_topo)[:160])

VERDE, ROSSO, CIECO = 0, 1, 3
PORTE ={"gnome": 8511, "kde": 8512, "xfce": 8513, "lxqt": 8514}
REGISTRO = "/var/lib/rete11/registro.log"
SERVER = os.environ.get("REMOTIX_SERVER", "192.168.0.2")
UTENTE_SERVER = os.environ.get("REMOTIX_UTENTE", "nicfio")
PAROLA_SUDO = os.environ.get("REMOTIX_PAROLA", "nicfio")
# ⚠ La scheda VERA del tablet, non `lo`: strozzare `lo` non strozza niente di
#   quel che attraversa il filo (memoria «wondershaper sul tablet»).
SCHEDA_DEL_TABLET = os.environ.get("REMOTIX_SCHEDA", "wlo1")


# ═══════════════════════════════════════════════════════════════════════════
# 1 · IL GIUDIZIO — in un posto solo
# ═══════════════════════════════════════════════════════════════════════════
def esito(scenario, desktop, marca, codice, perche, misure=None, secondi=None,
          regole=None, pagina=None, server=None, guasti=None, registro=None):
    """L'unica forma di risposta che uno scenario puo' dare.

    ⛔ Il `perche'` non e' facoltativo nemmeno sul verde: un verde senza ragione
       non si rilegge sei mesi dopo.

    ⭐ `marca` finisce nella riga anche come `browser`: sono la stessa cosa, e
       chi legge la riga domattina non deve sapere quale dei due nomi ha usato
       chi l'ha scritta.  ⛔⛔ 23 set 2026: e' esattamente cosi' che due righe
       piene di misure sono arrivate alla tabella con «browser: None».

    ⚠ `pagina` e `server` sono i numeri del PROTAGONISTA del giro, quando lo
      scenario ne ha uno solo: messi li', salgono alla radice della riga senza
      che nessuno debba indovinare in che ramo di `misure` stavano.
      `guasti` e' l'elenco per il paragrafo 3 del rapporto: ⛔ ognuno con la sua
      riga di registro, o e' un'opinione.
    """
    r = {"scenario": scenario, "desktop": desktop,
         "marca": marca, "browser": marca,
         "esito": int(codice), "perche": perche,
         "misure": misure or {}, "regole": regole or {},
         "secondi": round(secondi, 1) if secondi is not None else None,
         "quando": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if pagina:
        r["pagina"] = pagina
    if server:
        r["server"] = server
    if guasti:
        r["guasti"] = [g if isinstance(g, dict) else {"che_cosa": str(g)}
                       for g in guasti]
    if registro:
        r["registro"] = registro
    # ⛔ I numeri in vista li tira su IL NUCLEO, non una seconda copia qui: il
    #    vocabolario della riga sta in `stress_nucleo.NOMI_IN_VISTA`, e basta
    #    una sola tabella di nomi al mondo.  ⚠ Col nucleo finto l'import non
    #    c'e': la riga resta com'e', e la completa chi la scrive (`_lancia.py`).
    try:
        import stress_nucleo
        stress_nucleo.completa_la_riga(r)
    except Exception:                            # noqa: BLE001
        pass
    return r


def verde(sc, d, m, perche, **k):
    return esito(sc, d, m, VERDE, perche, **k)


def rosso(sc, d, m, perche, **k):
    return esito(sc, d, m, ROSSO, perche, **k)


def non_so(sc, d, m, perche, **k):
    """⛔ «Non ho potuto guardare»: lo strumento non ha funzionato.

    ⚠ NON si usa per «il prodotto non sa fare questa cosa su questo desktop»:
      quello e' un fatto del prodotto, e si dice con le parole del cancello
      delle capacita' (`11-capacita-del-prodotto.sh`).
    """
    return esito(sc, d, m, CIECO, perche, **k)


class Tetto(object):
    """Il tetto di tempo dello scenario.  ⛔ Nessuno scende dalla notte.

    ⚠ Non uccide niente: dice `scaduto()`, e chi lo chiede si ferma in modo
      pulito — lo sgombero deve girare comunque.
    """

    def __init__(self, secondi):
        self.secondi = float(secondi)
        self.da = time.time()

    def scaduto(self):
        return (time.time() - self.da) > self.secondi

    def resta(self):
        return max(0.0, self.secondi - (time.time() - self.da))

    def passati(self):
        return time.time() - self.da


# ═══════════════════════════════════════════════════════════════════════════
# 2 · IL NUCLEO, CHIAMATO COM'E'
# ═══════════════════════════════════════════════════════════════════════════
def dentro(nucleo, desktop, copione, secondi=180):
    """Un copione `sh` dentro la scatola.  Torna `(codice, testo)`.

    ⚠ Il nucleo torna TRE valori (codice, uscita, errore): qui si tiene
      l'uscita, e l'errore solo quando l'uscita e' vuota — altrimenti un
      `grep` che non trova niente somiglierebbe a un guasto.
    """
    c, u, e = nucleo.dentro(desktop, copione + "\n", "sh", None, secondi)
    return c, ((u or "").strip() or (e or "").strip())


def crea_inquilino(nucleo, desktop, chi, parola):
    return nucleo.crea_inquilino(desktop, chi, parola)


def sgombera(nucleo, desktop, chi):
    return nucleo.sgombera(desktop, chi)


def istante(nucleo, desktop):
    """Il segno da cui leggere il registro: l'orologio DELLA SCATOLA.

    ⛔ Non quello del tablet: sono due orologi diversi, e una finestra presa con
       quello sbagliato legge le righe di qualcun altro.
    """
    return nucleo.istante_nella_scatola(desktop)


def scena(nucleo, desktop, quale, chi):
    return nucleo.scena(desktop, quale, chi)


def modello_sicuro(nucleo, chi):
    """⛔ Un modello per `pkill -f` che NON pesca il guscio che lo esegue."""
    f = getattr(nucleo, "modello_senza_se_stesso", None)
    if callable(f):
        return f(chi)
    return "[%s]%s" % (chi[0], chi[1:])


CHIAVI = {
    "consegnati": ("consegnati",),
    "dipinti": ("dipinti",),
    "buchi": ("buchi",),
    "saltati": ("saltati_coda",),
    "chiavi_chieste": ("chiavi_chieste",),
    "coda": ("coda_decodificatore", "decodeQueueSize"),
    "errori": ("errori_pagina",),
    "sessione": ("sessione",),
    "sospeso": ("sospeso",),
}


def numeri(nucleo, browser):
    """I contatori della PAGINA, coi nomi normalizzati per gli scenari."""
    grezzi = nucleo.conta_dalla_pagina(browser) or {}
    fuori = {}
    if grezzi.get("errore_lettura"):
        fuori["errore_lettura"] = grezzi["errore_lettura"]
    for nostro, suoi in CHIAVI.items():
        for k in suoi:
            if grezzi.get(k) is not None:
                fuori[nostro] = grezzi[k]
                break
    return fuori


def dal_server(nucleo, desktop, da_istante=None, chi=None):
    """I fatti del SERVER in questa finestra (registro + bilancio).

    ⚠ I nomi sono quelli del nucleo: `spediti`, `chiavi`, `rc_accolte`,
      `rc_ignorate`, `linee_morte`, `tela_non_combacia`, `server_fd`…
    """
    return nucleo.conta_dal_server(desktop, da_istante, chi) or {}


def apri_browser(nucleo, marca, porta, misura=(1400, 1000), tetto_s=60):
    """Accende il browser VERO e lo porta fino al modulo d'accesso.

    Torna `(browser, codice, perche)`: ⛔ un browser che non si accende e' un
    **3**, non un rosso — lo strumento non ha guardato.
    """
    try:
        b = nucleo.avvia_browser(marca, porta, misura, tetto_s)
    except Exception as e:                       # noqa: BLE001
        return None, CIECO, "il browser non si e' acceso: %s" % str(e)[:200]
    try:
        aperta, perche = b.apri(tetto_s)
    except Exception as e:                       # noqa: BLE001
        return b, CIECO, "la pagina non si apre: %s" % str(e)[:200]
    if not aperta:
        return b, CIECO, "la pagina non si apre: %s" % perche
    return b, VERDE, perche


def entra(browser, utente, parola, tetto_s=60):
    """`(codice, perche)` — ⛔ e i tre casi restano tre: ammesso, RIFIUTATO
    (rosso: e' il prodotto che dice di no) e «non so» (il tetto)."""
    return browser.entra(utente, parola, tetto_s)


def foto(browser):
    """Una fotografia della TELA, in byte.

    ⚠ Non `getImageData`: la tela puo' essere `bitmaprenderer` o passata a un
      worker, e li' la lettura dal documento non vede niente.
    """
    d = browser.fotografa()
    # ⛔⛔ `fotografa_tela()` torna una COPPIA `(byte, perche')` in tutt e due i
    #     guidatori (`12-client-veri.py`, Marionette e CDP) ⇒ senza questa riga
    #     si cadeva nel `return None` finale e questa funzione non ha MAI
    #     restituito un pixel.  `[M]` 23 set 2026, provata con `(b'ciao', '')`.
    # ⚠ E il difetto era invisibile perche' `None` e' ANCHE il modo legittimo di
    #   dire «non ho potuto guardare»: chi la usava non vedeva niente e non
    #   aveva nessun motivo di sospettare.
    if isinstance(d, tuple):
        d = d[0]
    if isinstance(d, (bytes, bytearray)):
        return bytes(d)
    if isinstance(d, str):
        import base64
        if d.startswith("data:"):
            d = d.split(",", 1)[1]
        try:
            return base64.b64decode(d)
        except Exception:                        # noqa: BLE001
            return None
    return None


def chiudi(browser):
    try:
        browser.chiudi()
        return True
    except Exception:                            # noqa: BLE001
        return False


# ═══════════════════════════════════════════════════════════════════════════
# 3 · QUEL CHE IL NUCLEO NON FA, PERCHE' NON E' SUO
#
# ⛔ Tre cose sole, e ognuna ha la sua ragione:
#    · il RIAVVIO DEL SERVER sta sull'OSPITE, fuori dalle scatole;
#    · la STROZZATURA sta sul TABLET, che e' il capo che riceve;
#    · «ESCI» e' un gesto del DESKTOP, e cambia per desktop.
# ═══════════════════════════════════════════════════════════════════════════
def _ssh_ospite(comando, secondi=300):
    """Un comando sull'ospite (non dentro una scatola), da amministratore."""
    pieno = "printf '%s\\n' | sudo -S -v 2>/dev/null; %s" % (PAROLA_SUDO, comando)
    r = subprocess.run(["ssh", "-tt", "-o", "BatchMode=yes",
                        "-o", "ConnectTimeout=10",
                        "%s@%s" % (UTENTE_SERVER, SERVER), pieno],
                       # ⛔ `errors="replace"`: qui passa anche la coda del
                       #    registro, e un taglio a meta' di ⭐/⛔/→ faceva
                       #    MORIRE il banco (23 set 2026).
                       capture_output=True, text=True, errors="replace",
                       timeout=secondi)
    pulito = "\n".join(l for l in (r.stdout or "").splitlines()
                       if "tput:" not in l and "Connection to" not in l)
    return r.returncode, pulito.strip()


def riavvia_il_server(desktop):
    """Riavvia il server dentro la scatola, come fa il gancio.

    ⚠ Il registro si azzera: chi misura deve riprendere il suo segno DOPO.
    """
    c, t = _ssh_ospite("cd /media/REMOTIX/rete11 && sudo bash 11-accendi.sh "
                       "server %s 2>&1 | tail -3" % desktop, 300)
    return ("ascolta" in t), t[-300:]


def strozza(kbit):
    """Strozza la scheda vera del tablet.  Torna `(fatto, perche)`."""
    libera()
    r = subprocess.run(["sudo", "-n", "wondershaper", "-a", SCHEDA_DEL_TABLET,
                        "-d", str(int(kbit)), "-u", str(int(kbit))],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return False, (r.stderr or r.stdout or "").strip()[:200]
    return True, ""


def libera():
    subprocess.run(["sudo", "-n", "wondershaper", "-c", "-a", SCHEDA_DEL_TABLET],
                   capture_output=True, text=True)


def uid_di(nucleo, desktop, chi):
    c, t = dentro(nucleo, desktop, "id -u %s" % chi, 90)
    m = re.search(r"\b(\d{3,6})\b", t or "")
    return int(m.group(1)) if m else None


def compositore_vivo(nucleo, desktop, chi):
    """C'e' ancora un compositore per quell'inquilino? (il nome cambia per DE)"""
    # ⚠ lxqt: il compositore e' lo STESSO di xfce, `labwc` (`Contenitore.lxqt` §2).
    nomi = {"kde": "kwin_wayland", "gnome": "gnome-shell", "xfce": "labwc",
            "lxqt": "labwc"}
    c, t = dentro(nucleo, desktop,
                  "pgrep -u %s -x %s >/dev/null && echo SI || echo NO"
                  % (chi, nomi.get(desktop, "")), 90)
    return "SI" in (t or "")


def esci_dalla_sessione(nucleo, desktop, chi):
    """«Esci» col gesto del desktop — ⛔ non un `kill` del compositore, che
    proverebbe un'altra cosa (13-w4: il difetto si vede sull'uscita ORDINATA).

    ⚠ XFCE: `xfce4-session-logout` resta appeso (vuole la sua finestra), e il
      nome dell'interfaccia NON e' quello dell'oggetto — `[M]` 22 set 2026.
    """
    uid = uid_di(nucleo, desktop, chi)
    if uid is None:
        return False, "non so l'uid di %s" % chi
    amb = ("env DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%d/bus "
           "XDG_RUNTIME_DIR=/run/user/%d" % (uid, uid))
    gesti = {
        "kde": "busctl --user call org.kde.Shutdown /Shutdown "
               "org.kde.Shutdown logout",
        "gnome": "busctl --user call org.gnome.SessionManager "
                 "/org/gnome/SessionManager org.gnome.SessionManager Logout u 1",
        "xfce": "busctl --user call org.xfce.SessionManager "
                "/org/xfce/SessionManager org.xfce.Session.Manager Logout "
                "bb false false",
        # ⭐ lxqt: lo stesso gesto di C20 (`11-c20-…py`, `DESKTOP_E_GESTO`,
        #   dove stanno le fonti di lxqt-session 2.1.1).  ⛔ NON
        #   `lxqt-leave --logout`: apre una conferma modale.  ⚠ Il metodo e'
        #   `Q_NOREPLY` ⇒ `--expect-reply=no` `[?]`.
        "lxqt": "busctl --user --expect-reply=no call org.lxqt.session "
                "/LXQtSession org.lxqt.session logout",
    }
    if desktop not in gesti:
        return False, "non so come si esce da %s" % desktop
    c, t = dentro(nucleo, desktop,
                  "runuser -u %s -- %s %s >/dev/null 2>&1; echo fatto=$?"
                  % (chi, amb, gesti[desktop]), 120)
    return ("fatto=0" in (t or "")), (t or "")[-200:]


def scatola_pulita(nucleo, desktop, miei=()):
    """⭐ Dopo di me, che cosa resta?  Torna `(pulita, descrizione)`.

    ⛔ Si giudica SOLO quel che ho lasciato IO: nella stessa scatola puo' esserci
       un altro banco al lavoro, e accusarsi del suo inquilino e' il difetto che
       la fase 10 §7.3 nomina.  ⚠ `nictest` e `provanic` sono di chi usa la
       scatola a mano.
    """
    c, t = dentro(nucleo, desktop,
                  "awk -F: '$3>=1000 && $3<60000 {print $1}' /etc/passwd | "
                  "tr '\\n' ' '; echo; ps -eo stat= | grep -c '^[TZ]'", 90)
    righe = [r.strip() for r in (t or "").splitlines() if r.strip()]
    utenti = [u for u in (righe[0].split() if righe else [])
              if u not in ("nictest", "provanic")]
    try:
        fermi = int(righe[-1])
    except (ValueError, IndexError):
        fermi = -1
    miei = list(miei or [])
    restati = [u for u in utenti if u in miei] if miei else list(utenti)
    altri = [u for u in utenti if u not in miei]
    return (not restati) and fermi == 0, (
        "miei rimasti: %s · processi fermi o zombie: %s%s"
        % (" ".join(restati) if restati else "nessuno",
           fermi if fermi >= 0 else "non lo so",
           (" · di altri: %s" % " ".join(altri)) if (miei and altri) else ""))


# ═══════════════════════════════════════════════════════════════════════════
# 4 · LE STRISCE — e si misurano, non si guardano
# ═══════════════════════════════════════════════════════════════════════════
def strisce(png, riquadro=None, frazioni=None):
    """Quanto e' «sbavata a strisce» una fotografia della tela.

    ⭐ COME: sulla parte a rumore si prendono le medie dei blocchi 8×8 e se ne
       misura la dispersione.  Su rumore vero i blocchi si assomigliano tutti;
       quando i delta si decodificano su un riferimento sbagliato compaiono
       bande larghe e i blocchi divergono.
    `[M]` 22 set 2026, KDE, scena pesante: Firefox col difetto **37,8**, Firefox
       curato **23,3**, Chrome **16,7** ⇒ la soglia di 30 sta in mezzo.  ⚠ E' di
       QUESTA scena e di QUESTO ferro: il numero si riporta sempre, cosi' uno
       spostamento si vede anche quando il verdetto non cambia.
    ⛔ `None` se non si puo' misurare: un numero inventato sarebbe peggio.

    ⭐ `frazioni` = `(x0, y0, x1, y1)` in FRAZIONI della fotografia, per chi vuole
       misurare una zona precisa senza sapere quanto e' grande la fotografia (i
       due guidatori la consegnano a misure diverse: `[M]` 1368 px contro 609).
       ⛔ Serve con la scena TESTIMONE, dove il ritaglio centrale di qui sopra
          cade tutto dentro il campo a celle — rettangoli di un colore solo, che
          fanno dispersione altissima per costruzione e non vogliono dire
          niente sul prodotto.
    """
    if not png:
        return None
    try:
        import io

        import numpy as np
        from PIL import Image
    except Exception:                            # noqa: BLE001
        return None
    try:
        a = np.asarray(Image.open(io.BytesIO(png)).convert("L"), dtype=np.float32)
    except Exception:                            # noqa: BLE001
        return None
    if a.size == 0:
        return None
    if frazioni and not riquadro:
        h, w = a.shape
        riquadro = (int(w * frazioni[0]), int(h * frazioni[1]),
                    int(w * frazioni[2]), int(h * frazioni[3]))
    if riquadro:
        x0, y0, x1, y1 = riquadro
        a = a[y0:y1, x0:x1]
    else:
        # ⚠ I bordi portano barre e decorazioni del desktop, che non sono rumore.
        h, w = a.shape
        a = a[h // 4:3 * h // 4, w // 4:3 * w // 4]
    h, w = a.shape
    h, w = (h // 8) * 8, (w // 8) * 8
    if h < 32 or w < 32:
        return None
    a = a[:h, :w]
    return float(a.reshape(h // 8, 8, w // 8, 8).mean(axis=(1, 3)).std())


# ⭐ La fascia di RUMORE sotto il campo testimone: il campo arriva al 76 % della
#   tela (`stress_occhio.CAMPO`), sotto c'e' lo stesso generatore di rumore
#   della scena pesante.  ⛔ E' li' che si misurano le strisce quando la scena e'
#   quella dell'occhio: nel mezzo ci sono rettangoli di un colore solo.
FUORI_DAL_CAMPO = (0.10, 0.80, 0.90, 0.98)


def misura_le_strisce(banco, png):
    """⭐ Le strisce, e DOVE si misurano.  Torna `(numero, si_giudica, perche)`.

    ⛔⛔ CON LA SCENA DELL'OCCHIO LE STRISCE NON SI GIUDICANO PIU', e il motivo
        e' misurato, non prudenziale: il ritaglio centrale di `strisce()` cade
        tutto dentro il campo a celle, che e' fatto di rettangoli di un colore
        solo ⇒ la dispersione dei blocchi 8×8 e' altissima **per costruzione**,
        e la soglia di 30 — che viene da un'altra scena e da un altro ritaglio
        — accuserebbe il prodotto di un difetto del banco.
        `[M]` 23 set 2026, scena testimone col motore, la stessa immagine:
        ritaglio centrale **94,6** contro una soglia di 30,0, fascia di rumore
        sotto il campo **6,2**.  ⇒ Non e' un rischio, e' un rosso sicuro.
    ⭐ Il numero si misura lo stesso, sulla fascia di rumore sotto il campo, e si
       riporta: uno spostamento si vede anche quando nessuno lo giudica.  A
       giudicare l'immagine, li', c'e' l'occhio — che e' un testimone e non un
       indizio.
    """
    if not png:
        return None, False, "nessuna fotografia"
    if getattr(banco, "occhio", None) is not None:
        return (strisce(png, frazioni=FUORI_DAL_CAMPO), False,
                "misurata sulla fascia di rumore sotto il campo testimone; ⛔ non "
                "giudicata: la soglia di 30 e' di un'altra scena e di un altro "
                "ritaglio — qui l'immagine la giudica l'occhio")
    return strisce(png), True, ""


# ═══════════════════════════════════════════════════════════════════════════
# 5 · GUARDARE NEL TEMPO
# ═══════════════════════════════════════════════════════════════════════════
def guarda_per(nucleo, browser, secondi, passo=5.0, tetto=None, ogni_giro=None,
               occhio=None, topo=None):
    """Guarda i contatori della pagina per `secondi` e torna la STORIA.

    ⭐ La storia, non il totale: «e' salito per tutto il tempo» e «e' salito e
       poi si e' fermato» danno lo stesso totale, e la seconda e' precisamente
       il difetto del 22 settembre.

    ⭐⭐ E se c'e' un `occhio`, nello stesso giro si FOTOGRAFA LA TELA, **una
       volta al secondo**, mentre i contatori si leggono ogni `passo`.
    ⛔⛔ Dallo STESSO filo, e non da un secondo filo di esecuzione: il guidatore
       del browser (Marionette o CDP) e' una conversazione sola su un socket
       solo, e due comandi insieme la sfasano.  ⇒ Qui il giro diventa di un
       secondo, e i contatori si leggono ogni `passo` come prima.

    ⭐⭐ E se c'e' un `topo` (il cliente che non sta fermo), a ogni giro:
       · legge `consegnati` — UNA volta al secondo, per il giudice sul blocco
         piu' lungo (la `storia` resta ogni `passo`, com'era);
       · e riempie il RESTO del secondo muovendo il mouse (`B14.muovi`).
    ⛔ Sempre dallo stesso filo: il mouse passa dallo stesso guidatore delle
       fotografie, e un secondo filo lo sfaserebbe.
    """
    storia = []
    fine = time.time() + float(secondi)
    prossimo_conto = 0.0
    if topo is not None:
        topo.comincia(fine)
    try:
        while time.time() < fine:
            if tetto is not None and tetto.scaduto():
                break
            giro = time.time()
            n = None
            if giro >= prossimo_conto:
                n = numeri(nucleo, browser)
                n["t"] = round(time.time(), 1)
                storia.append(n)
                prossimo_conto = giro + float(passo)
                if ogni_giro:
                    try:
                        ogni_giro(n, storia)
                    except Exception:            # noqa: BLE001
                        pass
            if topo is not None:
                topo.conta(n)
            if occhio is None:
                dorme = topo.cadenza if topo is not None else float(passo)
            else:
                occhio.scatta()
                # ⛔ UNA FOTOGRAFIA AL SECONDO, non ogni cinque.  `[M]` 23 set
                #    2026: gli episodi di corruzione durano meno di mezzo secondo
                #    — lo stesso giro rotto letto uno ogni 60 dava «zero celle
                #    guaste», letto fitto ne mostrava sette fotogrammi devastati.
                dorme = occhio.cadenza
            # ⭐ Il mouse riempie quel che resta del giro: contatori e fotografia
            #   PRIMA, il movimento DOPO — cosi' la cadenza dell'occhio resta
            #   quella, e il mouse non si ferma mai piu' di un attimo.
            if topo is not None:
                topo.muovi_fino(min(giro + dorme, fine))
            dorme = max(0.0, dorme - (time.time() - giro))
            dorme = min(dorme, max(0.0, fine - time.time()))
            if dorme > 0:
                time.sleep(dorme)
    finally:
        # ⛔ Il guasto innestato non sopravvive alla misura che lo guarda.
        if topo is not None:
            topo.rilascia()
    if not storia or (time.time() - storia[-1]["t"]) > 1.0:
        n = numeri(nucleo, browser)
        n["t"] = round(time.time(), 1)
        storia.append(n)
    return storia


def pausa(banco, secondi):
    """⭐ Un'attesa da CLIENTE, non da banco: si aspetta muovendo il mouse.

    ⚠ Per le attese degli scenari che non guardano con `guarda_per` («e'
      ripartita l'immagine dopo il rientro?»): ⛔ il difetto del 23 settembre
      teneva ferma proprio la richiesta della chiave, e un rientro atteso col
      mouse fermo non l'avrebbe mai visto.  Senza topo e' un `sleep`.
    """
    fine = time.time() + float(secondi)
    topo = getattr(banco, "topo", None)
    if topo is not None:
        topo.muovi_fino(fine)
    resta = fine - time.time()
    if resta > 0:
        time.sleep(resta)


def sempre_in_salita(storia, chiave="consegnati", buco_massimo_s=25.0):
    """⭐ Il giudice del 22 settembre: il contatore e' salito per TUTTO il tempo?

    Torna `(sempre, fermo_piu_lungo_s)`.  ⚠ Una pausa breve non e' un difetto —
    a scena ferma non c'e' niente da mandare — ma un contatore fermo piu' a
    lungo del tetto, mentre la scena si muove, e' la pagina incastrata.
    """
    if not storia:
        return False, 0.0
    peggio = 0.0
    ultimo_cambio = storia[0]["t"]
    valore = storia[0].get(chiave)
    for n in storia[1:]:
        v = n.get(chiave)
        if v is not None and v != valore:
            peggio = max(peggio, n["t"] - ultimo_cambio)
            ultimo_cambio, valore = n["t"], v
    peggio = max(peggio, storia[-1]["t"] - ultimo_cambio)
    return peggio <= buco_massimo_s, round(peggio, 1)


def cresciuti(a, b):
    """Quanto sono cresciuti i contatori fra due letture (solo i numeri)."""
    fuori = {}
    for k, v in (b or {}).items():
        if isinstance(v, (int, float)) and isinstance((a or {}).get(k), (int, float)):
            fuori[k] = v - a[k]
    return fuori


def salva(dove, nome, roba):
    """Un pezzo di prova accanto all'esito (fotografie, storie, registri)."""
    if not dove:
        return None
    try:
        os.makedirs(dove, exist_ok=True)
        p = os.path.join(dove, nome)
        if isinstance(roba, (bytes, bytearray)):
            with open(p, "wb") as f:
                f.write(roba)
        elif isinstance(roba, str):
            with open(p, "w") as f:
                f.write(roba)
        else:
            with open(p, "w") as f:
                json.dump(roba, f, ensure_ascii=False, indent=1, default=str)
        return p
    except Exception:                            # noqa: BLE001
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 6 · L'OCCHIO — ⭐⭐ il giudice che guarda l'IMMAGINE, non i contatori
#
# ⛔⛔ PERCHE' ESISTE, e costa dirlo: la notte fra il 22 e il 23 settembre 2026
#     la suite ha dato VERDE due volte mentre l'utente guardava un'immagine a
#     mosaico.  I contatori dicevano «7000 consegnati, 7000 dipinti, zero
#     buchi» — ⭐ e un fotogramma SBAGLIATO conta come uno giusto.  Il difetto
#     non era nel prodotto: era nel giudice.
#
# ⭐ Come funziona, in tre righe: la scena di banco la scriviamo noi
#   (`stress_occhio.deposita_scena`), quindi disegna un contenuto PREVEDIBILE;
#   la fotografia della tela si confronta con quel che DOVEVA esserci; le celle
#   che non tornano si contano.  Il resto sta scritto in `stress_occhio.py`.
#
# ⛔ LE TRE REGOLE CHE NON SI NEGOZIANO, e vengono da errori gia' pagati:
#   1. UNA FOTOGRAFIA AL SECONDO — gli episodi durano meno di mezzo secondo;
#   2. SI ASPETTA CHE LA SCENA SALGA — ~20 s a freddo dentro la scatola, qui se
#      ne aspettano 25: le fotografie di prima sono «non lo so» e sprecano il
#      giro;
#   3. LE FOTOGRAFIE VANNO SU DISCO, in `/home` — ⛔ mai in `/tmp`, che sul
#      tablet e' in RAM (3,8 G): un giro lungo ne fa ~1100 e ci si fabbrica la
#      pressione di memoria che la misura deve escludere.  Si giudica DOPO, e
#      si tengono solo le fotografie con celle guaste.
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA TRADUZIONE DELLE SCENE: chi chiede «pesante» vuole il carico, chi chiede
#   «normale» vuole una scena leggera — e l'occhio ne ha una per ognuno dei due
#   casi.  ⛔ La stessa scena, con e senza motore: non due file da tenere
#   allineati.
SCENA_DELL_OCCHIO = {
    "pesante": "testimone",             # campo dichiarato + rumore (il carico)
    "normale": "testimone-scarico",     # lo stesso campo, motore spento
}


def occhio_acceso():
    """⚠ L'interruttore per spegnerlo da fuori senza toccare il codice
    (`REMOTIX_OCCHIO=no`).  ⭐ Non e' un comodo: e' il modo di far vedere che
    cosa vedeva la suite PRIMA di avere l'occhio — cioe' la controprova del
    verde falso della notte fra il 22 e il 23 settembre 2026.
    ⛔ Si legge OGNI VOLTA, non all'importazione: chi fa la controprova accende
       e spegne nello stesso processo."""
    return (os.environ.get("REMOTIX_OCCHIO", "si").strip().lower()
            not in ("no", "0", "off", "spento", "false"))


def cartella_dell_occhio(dove, sigla):
    """⭐ Dove finiscono le fotografie.  ⛔ MAI in RAM (vedi la regola 3)."""
    radice = dove or ""
    if (not radice or not os.path.isabs(radice)
            or radice.startswith(("/tmp", "/dev/shm", "/run", "/var/tmp"))):
        radice = os.path.expanduser("~/.local/state/remotix/stress")
    return os.path.join(radice, "occhio", str(sigla))


class Occhio(object):
    """⭐⭐ Fotografa la tela mentre il giro va avanti, e giudica alla fine.

    ⛔ Non e' un secondo filo di esecuzione: `scatta()` lo chiama chi sta gia'
       parlando col browser (vedi `guarda_per`), perche' il guidatore e' una
       conversazione sola.
    """

    CADENZA_S = 1.0
    ATTESA_S = 25.0
    # ⚠ I due tetti sono per il disco del tablet, non per la misura: `[M]` una
    #   fotografia di Firefox a schermo pieno sulla scena col motore pesa
    #   qualche MB, e un giro lungo ne fa piu' di mille.  Quando si sfora si
    #   smette di fotografare e LO SI DICE — ⛔ non si finge di aver guardato.
    TETTO_FOTO = 1500
    TETTO_MB = 1200

    def __init__(self, banco, cartella, cadenza_s=None, attesa_s=None,
                 tetto_foto=TETTO_FOTO, tetto_mb=TETTO_MB):
        self.banco = banco
        self.cartella = cartella
        # ⚠ I due numeri si possono cambiare da fuori, e servono alla
        #   certificazione col nucleo finto (dove non c'e' nessuna scatola che
        #   deve salire, e aspettarla venticinque secondi sarebbe solo attesa).
        #   ⛔ Non e' una scorciatoia nascosta: ogni giro li SCRIVE nelle proprie
        #      misure, quindi una ripresa fatta con la cadenza sbagliata lo dice
        #      da sola invece di somigliare a una buona.
        self.cadenza = float(cadenza_s if cadenza_s is not None else
                             os.environ.get("REMOTIX_OCCHIO_CADENZA", self.CADENZA_S))
        self.attesa = float(attesa_s if attesa_s is not None else
                            os.environ.get("REMOTIX_OCCHIO_ATTESA", self.ATTESA_S))
        self.tetto_foto = int(tetto_foto)
        self.tetto_byte = int(tetto_mb) * 1024 * 1024
        self.file = []
        self.byte = 0
        self.pronto_da = None          # None ⇒ la scena non e' ancora accesa
        self.ultima = 0.0
        self.senza_foto = 0
        self.spento = ""
        self.scena = None
        try:
            os.makedirs(self.cartella, exist_ok=True)
        except OSError as e:
            self.spento = "non posso scrivere in %s: %s" % (self.cartella, e)

    # ── quando si puo' cominciare a guardare ──────────────────────────────
    def acceso(self, quale=None):
        """⭐ La scena e' su: da qui si contano i 25 secondi di salita."""
        self.scena = quale or self.scena
        self.pronto_da = time.time() + self.attesa

    def riscalda(self, secondi=None):
        """⚠ Dopo un rientro la finestra si RIAPRE, e mezza scena sullo schermo
        non e' un difetto del prodotto: `[M]` 23 set 2026, la seconda
        fotografia di una ripresa sana dava 10,8 % di celle guaste, ed era
        l'animazione del compositore.  ⇒ si riparte dall'attesa."""
        self.pronto_da = time.time() + (self.attesa if secondi is None
                                        else float(secondi))

    # ── la fotografia ─────────────────────────────────────────────────────
    def scatta(self):
        """Una fotografia, se e' ora.  Torna True se l'ha presa davvero."""
        if self.spento or self.pronto_da is None:
            return False
        adesso = time.time()
        if adesso < self.pronto_da or (adesso - self.ultima) < self.cadenza:
            return False
        browser = getattr(self.banco, "browser", None)
        if browser is None:
            return False
        self.ultima = adesso
        try:
            png = foto(browser)
        except Exception:                        # noqa: BLE001
            png = None
        if not png:
            self.senza_foto += 1
            return False
        nome = os.path.join(self.cartella, "%05d.png" % len(self.file))
        try:
            with open(nome, "wb") as f:
                f.write(png)
        except OSError as e:
            self.spento = "il disco non prende piu' fotografie: %s" % e
            return False
        self.file.append(nome)
        self.byte += len(png)
        if len(self.file) >= self.tetto_foto:
            self.spento = ("tetto delle fotografie (%d): da qui in poi non ho "
                           "piu' guardato" % self.tetto_foto)
        elif self.byte >= self.tetto_byte:
            self.spento = ("tetto del disco (%d MB): da qui in poi non ho piu' "
                           "guardato" % (self.tetto_byte // (1024 * 1024)))
        return True

    # ── il verdetto, DOPO ─────────────────────────────────────────────────
    def giudizio(self, tetto_s=240.0):
        """⭐⭐ `(esito, perche, misure)` — e si giudica alla fine, non durante.

        ⛔ Si tengono solo le fotografie CON celle guaste: sono la prova, e le
           altre mille sono solo disco.
        ⚠ La cornice NON si impone da una fotografia all'altra: ogni fotografia
          si trova la sua.  `stress_occhio.guarda_per()` la riusa apposta (un
          guasto grosso mangia anche il magenta), ma qui le fotografie di prima
          che la scena salga e quelle di un rientro **non sono la nostra
          scena**, e imporre loro una geometria presa altrove vorrebbe dire
          leggere celle che non ci sono ⇒ un rosso falso.  Il prezzo si dice:
          la fotografia a cui il guasto ha mangiato la cornice diventa «non lo
          so», e si conta in `senza_scena`.
        """
        if O is None:
            return CIECO, OCCHIO_PERCHE or "l'occhio non c'e'", {}
        rapporti = []
        senza_scena = 0
        tenute = []
        t0 = time.time()
        guardate = 0
        for percorso in self.file:
            if (time.time() - t0) > float(tetto_s):
                break
            try:
                with open(percorso, "rb") as f:
                    png = f.read()
            except OSError:
                continue
            guardate += 1
            r = O.guarda(png)
            r.pop("cornice", None)
            rapporti.append(r)
            if r.get("guaste"):
                tenute.append(percorso)
                continue
            if not r.get("visto"):
                senza_scena += 1
            try:
                os.remove(percorso)
            except OSError:
                pass
        esito, perche, misure = O.giudizio(rapporti)
        misure = dict(misure or {})
        misure.update({
            "scena": self.scena,
            "cadenza_s": self.cadenza,
            "attesa_prima_di_guardare_s": self.attesa,
            "fotografie_prese": len(self.file),
            "fotografie_guardate": guardate,
            "senza_scena": senza_scena,
            "senza_fotografia": self.senza_foto,
            "megabyte": round(self.byte / (1024.0 * 1024.0), 1),
            "cartella": self.cartella,
            "tenute": [os.path.basename(x) for x in tenute[:20]],
            # ⭐ I NUMERI IN VISTA: i nomi stanno in `stress_nucleo.NOMI_IN_VISTA`,
            #   e da li' salgono da soli alla radice della riga.
            "occhio_foto": misure.get("foto_viste"),
            "occhio_guaste": misure.get("foto_sopra_soglia"),
            "occhio_devastate": misure.get("foto_devastate"),
            "occhio_peggiore_per_cento":
                (round(100.0 * misure["quota_guaste_peggiore"], 2)
                 if misure.get("quota_guaste_peggiore") is not None else None),
        })
        if self.spento:
            misure["ho_smesso_perche"] = self.spento
        if guardate < len(self.file):
            misure["non_giudicate"] = len(self.file) - guardate
            perche += ("  ⚠ %d fotografie non le ho nemmeno guardate: il tetto "
                       "di tempo del giudizio (%.0f s)"
                       % (len(self.file) - guardate, float(tetto_s)))
        return esito, perche, misure


def vede_l_occhio(banco, misure=None, guasti=None, giudica=True,
                  tetto_giudizio_s=240.0):
    """⭐⭐ IL VERDETTO DELL'OCCHIO ENTRA NEL GIRO.  Torna `(esito, perche)`.

    ⛔⛔ E un **3 non diventa mai un rosso**: se l'occhio non riconosce la
        propria scena non e' un guasto del prodotto — e' un banco che non ha
        guardato (§1.51).  Il numero si scrive lo stesso, cosi' domattina si
        vede che quel giro l'immagine non l'ha vista nessuno.

    ⚠ `giudica=False` per chi vuole il numero ma non il verdetto: serve dove le
      soglie dell'occhio non sono state tarate (la rete strozzata).
    """
    fuori = misure if isinstance(misure, dict) else {}
    occhio = getattr(banco, "occhio", None)
    if occhio is None:
        fuori["occhio"] = {"esito": CIECO,
                           "perche": getattr(banco, "occhio_perche", "")
                           or "l'occhio non era acceso in questo giro"}
        return CIECO, fuori["occhio"]["perche"]
    esito, perche, numeri_occhio = occhio.giudizio(tetto_giudizio_s)
    numeri_occhio["esito"] = esito
    numeri_occhio["perche"] = perche
    numeri_occhio["giudica"] = bool(giudica)
    fuori["occhio"] = numeri_occhio
    if esito == ROSSO and giudica and guasti is not None:
        guasti.append("⛔ L'IMMAGINE SULLO SCHERMO NON E' QUELLA CHE LA SCENA "
                      "DICHIARA — %s" % perche)
    return esito, perche


def conta_il_ritmo(banco, misure=None, guasti=None, giudica=True):
    """⭐ LA SECONDA RETE, sui soli NUMERI: il server ha buttato fotogrammi gia'
    codificati e nessuna chiave li ha ricuciti? ⇒ la catena dei riferimenti e'
    rotta (`stress_occhio.giudizio_dei_numeri`).

    ⛔⛔ VA CHIAMATA DOPO CHE L'INQUILINO E' USCITO, e per questo e' lei a farlo
        uscire: le righe di riepilogo (`ritmo`, `delta TENUTI`) il server le
        scrive alla CHIUSURA della sessione, e prima direbbe sempre «non lo
        so».  ⇒ Chi la chiama ha gia' finito di misurare: il browser si chiude
        e l'inquilino si sgombera QUI.
    ⚠ E il costo si dichiara: dopo questa chiamata `banco.browser` non c'e'
      piu' e `banco.numeri()` non si puo' piu' leggere.
    """
    fuori = misure if isinstance(misure, dict) else {}
    if O is None:
        fuori["ritmo"] = {"esito": CIECO, "perche": OCCHIO_PERCHE}
        return CIECO, OCCHIO_PERCHE
    try:
        banco.chiudi_tutto()
        time.sleep(3.0)
        conti = O.conti_del_ritmo(banco.n, banco.desktop, banco.segno, banco.chi)
    except Exception as e:                       # noqa: BLE001
        fuori["ritmo"] = {"esito": CIECO,
                          "perche": "non ho potuto leggere il registro: %s" % str(e)[:160]}
        return CIECO, fuori["ritmo"]["perche"]
    esito, perche, numeri_ritmo = O.giudizio_dei_numeri(conti)
    # ⚠ «chiavi» e' gia' un nome in vista (quelle del server): qui si rinomina,
    #   o due numeri diversi finirebbero nella stessa casella della riga.
    numeri_ritmo = {("chiavi_del_ritmo" if k == "chiavi" else k): v
                    for k, v in (numeri_ritmo or {}).items()}
    numeri_ritmo["esito"] = esito
    numeri_ritmo["perche"] = perche
    fuori["ritmo"] = numeri_ritmo
    if esito == ROSSO and giudica and guasti is not None:
        guasti.append("⛔ LA CATENA DEI RIFERIMENTI E' ROTTA — %s" % perche)
    return esito, perche


# ═══════════════════════════════════════════════════════════════════════════
# 6-bis · IL TOPO — ⭐⭐ il cliente che non sta fermo, e il giudice che lo guarda
#
# ⛔⛔ PERCHE' ESISTE, e costa dirlo: il 23 settembre 2026 `batti_fra()`
#     rimandava il battito del server a ogni messaggio di input, e con lui la
#     richiesta della chiave ⇒ schermo fermo per minuti, mouse alla mano.
#     Nessuno scenario lo vedeva: **tutti avevano un cliente educato**, che
#     entrava e stava a guardare (`14-il-cliente-che-non-sta-fermo.py`).
#
# ⭐ Che cosa fa, in tre righe:
#   · muove il mouse di continuo mentre lo scenario guarda (`guarda_per`, ~20
#     movimenti al secondo, il gesto del banco 14 — Firefox e Chrome);
#   · legge `consegnati` una volta al secondo, e segna quanti movimenti sono
#     partiti in quel secondo;
#   · alla fine GIUDICA il blocco piu' lungo senza fotogrammi nuovi
#     (`B14.giudica_il_blocco`: 0 · 1 · 3, soglia `[?]` da tarare sul ferro).
# ⛔ E il GUASTO INNESTATO, senza ricompilare: `REMOTIX_SCHERMO_CONGELATO=25`
#    (o `_lancia.py --schermo-congelato`) congela il compositore dell'inquilino
#    per 25 s a meta' misura, e lo rilascia SEMPRE.  Col guasto il giudice DEVE
#    dare 1, e la riga dice se il guasto e' stato visto.
# ═══════════════════════════════════════════════════════════════════════════
def topo_acceso():
    """⚠ `REMOTIX_TOPO=no` lo spegne da fuori — ⭐ ed e' la controprova: il
    cliente educato di prima del 23 settembre.  Si legge ogni volta."""
    return (os.environ.get("REMOTIX_TOPO", "si").strip().lower()
            not in ("no", "0", "off", "spento", "false"))


def schermo_congelato():
    """`(secondi, dopo_s)` del guasto innestato, o `(None, None)`.

    ⚠ Viaggia nell'AMBIENTE, come `REMOTIX_OCCHIO`: cosi' arriva al `Banco`
      di ognuno degli scenari senza toccarne le chiamate.  ⛔ E la riga lo dice
      comunque (`misure.topo.guasto_innestato`), quindi un giro col guasto non
      puo' somigliare a uno sano.
    """
    try:
        s = float(os.environ.get("REMOTIX_SCHERMO_CONGELATO", "") or 0)
    except ValueError:
        s = 0.0
    if s <= 0:
        return None, None
    try:
        dopo = float(os.environ.get("REMOTIX_SCHERMO_CONGELATO_DOPO", "") or 20.0)
    except ValueError:
        dopo = 20.0
    return s, dopo


class Topo(object):
    """⭐⭐ Muove il mouse, conta i secondi, e (se chiesto) congela lo schermo.

    ⛔ Non e' un secondo filo di esecuzione: `conta()` e `muovi_fino()` li chiama
       `guarda_per`, dallo stesso filo che parla col browser.
    ⚠ Il browser si legge dal `banco` OGNI volta: dopo un rientro e' un altro.
    """

    CADENZA_S = 1.0
    PASSO_MS = 50                 # ⭐ il ritmo del banco 14: 20 movimenti al secondo

    def __init__(self, banco, congela_s=None, congela_dopo_s=20.0):
        self.banco = banco
        self.cadenza = self.CADENZA_S
        self.serie = []
        self.passo = 0
        self.mosse = 0
        self.mosse_ora = 0
        self.errori = 0
        self.ultimo_errore = ""
        self.tratto = 0
        self.fine = None
        self.da = None
        self.congela_s = congela_s
        self.congela_dopo_s = float(congela_dopo_s or 0.0)
        self.congelatore = None
        self.perche_non_congelato = ""

    def comincia(self, fine):
        """Un tratto di misura nuovo: ⚠ i blocchi non si cuciono fra due tratti."""
        self.tratto += 1
        self.fine = fine
        if self.da is None:
            self.da = time.time()

    # ── la lettura, una al secondo ────────────────────────────────────────
    def conta(self, n=None):
        """⭐ Una lettura di `consegnati`, con i movimenti del secondo PRIMA.

        ⚠ Se chi chiama ha gia' letto i contatori in questo giro li passa, e non
          si rilegge: una chiamata in meno al guidatore."""
        try:
            if n is None:
                n = numeri(self.banco.n, self.banco.browser)
            valore = (n or {}).get("consegnati")
        except Exception:                        # noqa: BLE001
            valore = None                        # ⚠ «non lo so» non e' «fermo»
        self.serie.append({"t": round(time.time(), 2), "consegnati": valore,
                           "mosse": self.mosse_ora, "tratto": self.tratto,
                           "ora": time.strftime("%H:%M:%S")})
        self.mosse_ora = 0
        self._il_guasto()

    # ── il mouse ──────────────────────────────────────────────────────────
    def muovi_fino(self, istante):
        """Muove il mouse fino a `istante`.  ⛔ Un errore del guidatore non ferma
        la misura: si conta, e il giudice lo vedra' come secondi senza mouse."""
        browser = getattr(self.banco, "browser", None)
        quanti = int((istante - time.time()) * 1000.0 / self.PASSO_MS)
        if browser is None or quanti < 1 or B14 is None:
            return 0
        self.passo += 1
        try:
            fatte = B14.muovi(browser, self.passo, quanti, self.PASSO_MS)
        except Exception as e:                   # noqa: BLE001
            self.errori += 1
            self.ultimo_errore = str(e)[:160]
            return 0
        self.mosse += fatte
        self.mosse_ora += fatte
        return fatte

    # ── il guasto innestato ───────────────────────────────────────────────
    def _il_guasto(self):
        if not self.congela_s or B14 is None:
            return
        adesso = time.time()
        if self.congelatore is None:
            if self.da is None or adesso - self.da < self.congela_dopo_s:
                return
            # ⛔ Si congela solo se il tratto dura ABBASTANZA da vedere il
            #    congelamento intero e ancora qualche secondo dopo: un guasto
            #    tagliato dalla fine della misura non prova la guardia.
            if self.fine is None or (self.fine - adesso) < self.congela_s + 5.0:
                self.perche_non_congelato = (
                    "la misura era troppo corta per un congelamento di %.0f s "
                    "dopo %.0f s" % (self.congela_s, self.congela_dopo_s))
                return
            self.perche_non_congelato = ""
            self.congelatore = B14.Congelatore(self.banco.n, self.banco.desktop,
                                               self.banco.chi, self.congela_s)
            try:
                self.congelatore.innesta()
            except Exception as e:               # noqa: BLE001
                self.congelatore.perche = "il guasto non si e' innestato: %s" % str(e)[:160]
        elif self.congelatore.e_ora():
            self.rilascia()

    def rilascia(self):
        """⛔ Sta nei `finally`: non solleva mai, e si puo' chiamare sempre."""
        if self.congelatore is not None:
            try:
                self.congelatore.rilascia()
            except Exception:                    # noqa: BLE001
                pass

    # ── il verdetto, DOPO ─────────────────────────────────────────────────
    def giudizio(self):
        """`(esito, perche, numeri)` — ⛔ e un 3 non diventa mai un rosso."""
        esito, perche, numeri_topo = B14.giudica_il_blocco(self.serie)
        scena = getattr(self.banco, "scena_accesa", None)
        if esito != CIECO and (not scena or scena == "ferma"):
            # ⛔ A scena ferma lo schermo non ha niente da mandare: un blocco
            #    lungo li' e' giusto, e un verde non direbbe niente.
            esito, perche = CIECO, ("la scena era «%s»: senza una scena che si "
                                    "muove un blocco non vuol dire niente"
                                    % (scena or "nessuna"))
        chiesto = bool(self.congela_s)
        innestato = bool(self.congelatore is not None and self.congelatore.fermati)
        esito, frase = B14.esito_col_guasto(esito, chiesto, innestato)
        numeri_topo.update({"topo_mosse": self.mosse,
                            "topo_errori_mouse": self.errori})
        if self.ultimo_errore:
            numeri_topo["topo_ultimo_errore"] = self.ultimo_errore
        if chiesto:
            numeri_topo["guasto_innestato"] = (
                self.congelatore.rapporto() if self.congelatore is not None else
                {"chiesto_s": self.congela_s, "innestato": False,
                 "perche": self.perche_non_congelato or "non e' mai partito"})
            numeri_topo["guasto_visto"] = bool(innestato and esito == ROSSO)
        return esito, perche + frase, numeri_topo


def vede_il_topo(banco, misure=None, guasti=None, giudica=True):
    """⭐⭐ IL VERDETTO DEL TOPO ENTRA NEL GIRO.  Torna `(esito, perche)`.

    ⛔⛔ Come l'occhio: un **3 non diventa mai un rosso**, e il numero si scrive
        lo stesso.  ⚠ `giudica=False` dove la soglia non ha senso (la rete
        strozzata: li' un blocco lungo puo' essere la linea, non il difetto).
    ⭐ La serie al secondo si salva accanto all'esito (`topo-serie.json`): il
       blocco che ha fatto il rosso si deve poter RILEGGERE.
    """
    fuori = misure if isinstance(misure, dict) else {}
    topo = getattr(banco, "topo", None)
    if topo is None:
        fuori["topo"] = {"esito": CIECO,
                         "perche": getattr(banco, "topo_perche", "")
                         or "il mouse non si muoveva in questo giro"}
        return CIECO, fuori["topo"]["perche"]
    try:
        esito, perche, numeri_topo = topo.giudizio()
    except Exception as e:                       # noqa: BLE001
        esito, perche, numeri_topo = CIECO, ("il giudice del topo si e' rotto: %s"
                                             % str(e)[:160]), {}
    numeri_topo["esito"] = esito
    numeri_topo["perche"] = perche
    numeri_topo["giudica"] = bool(giudica)
    fuori["topo"] = numeri_topo
    salva(getattr(banco, "dove", None), "topo-serie-%s.json" % banco.chi, topo.serie)
    if esito == ROSSO and giudica and guasti is not None:
        guasti.append("⛔ IL CLIENTE CHE NON STA FERMO — %s" % perche)
    return esito, perche


# ═══════════════════════════════════════════════════════════════════════════
# 7 · IL BANCO — inquilino, browser e scena, e si sparecchia SEMPRE
# ═══════════════════════════════════════════════════════════════════════════
class Banco(object):
    """Apparecchia un giro e lo sparecchia comunque vada.

    ⛔ `chiudi_tutto()` si chiama da un `finally`: una notte di misure non puo'
       dipendere dal fatto che uno scenario finisca bene.
    """

    def __init__(self, nucleo, desktop, marca, chi, parola="stress2026",
                 misura=(1400, 1000), dove=None, occhio=True, topo=True):
        self.n, self.desktop, self.marca = nucleo, desktop, marca
        self.chi, self.parola, self.misura, self.dove = chi, parola, misura, dove
        self.browser = None
        self.creato = False
        self.segno = None
        # ⭐ L'occhio e' la NORMA: chi non lo vuole lo dice, e dice perche'.
        self.vuole_l_occhio = bool(occhio)
        self.occhio = None
        self.occhio_perche = ""
        self.scena_accesa = None
        # ⭐⭐ E anche il TOPO e' la norma: un cliente vero muove il mouse.
        self.vuole_il_topo = bool(topo)
        self.topo = None
        self.topo_perche = ""

    def prepara_il_topo(self):
        """⭐ Il cliente che non sta fermo.  ⛔ Se non c'e', il giro va avanti
        col mouse fermo e lo DICE — non ferma la misura e non accusa nessuno."""
        if not self.vuole_il_topo:
            self.topo_perche = "questo scenario non ha chiesto il topo"
            return False, self.topo_perche
        if B14 is None or not topo_acceso():
            self.topo_perche = (TOPO_PERCHE if B14 is None else
                                "spento da fuori (REMOTIX_TOPO=no): il cliente "
                                "educato di prima del 23 settembre")
            return False, self.topo_perche
        secondi, dopo = schermo_congelato()
        self.topo = Topo(self, congela_s=secondi, congela_dopo_s=dopo)
        return True, ("mouse in moto%s" % ("" if not secondi else
                      " ⛔ col GUASTO INNESTATO: schermo congelato %.0f s dopo "
                      "%.0f s" % (secondi, dopo)))

    def prepara_l_occhio(self):
        """⭐ Scrive la scena TESTIMONE dentro la scatola e accende l'occhio.

        ⛔ Se non ci riesce, il giro va avanti SENZA occhio e con la scena di
           prima: un banco che non puo' guardare non ferma la misura e non
           accusa nessuno — dice soltanto che non ha guardato.
        """
        if not self.vuole_l_occhio:
            self.occhio_perche = "questo scenario non ha chiesto l'occhio"
            return False, self.occhio_perche
        if O is None or not occhio_acceso():
            self.occhio_perche = (OCCHIO_PERCHE if O is None else
                                  "spento da fuori (REMOTIX_OCCHIO=no)")
            return False, self.occhio_perche
        try:
            fatto, perche = O.deposita_scena(self.n, self.desktop)
        except Exception as e:                   # noqa: BLE001
            fatto, perche = False, "la scena testimone non si e' depositata: %s" % str(e)[:160]
        if not fatto:
            self.occhio_perche = perche
            return False, perche
        self.occhio = Occhio(self, cartella_dell_occhio(
            self.dove, "%s-%s-%s" % (self.desktop, self.marca, self.chi)))
        if self.occhio.spento:
            self.occhio_perche, self.occhio = self.occhio.spento, None
            return False, self.occhio_perche
        return True, perche

    def scatta(self):
        """Una fotografia della tela, se l'occhio c'e' ed e' ora."""
        return bool(self.occhio and self.occhio.scatta())

    def apparecchia(self, scena_quale="pesante", tetto_accesso_s=60):
        """`(codice, perche)` — 0 apparecchiato · 1 il prodotto ha detto di no ·
        3 lo strumento non ce l'ha fatta."""
        fatto, perche = crea_inquilino(self.n, self.desktop, self.chi, self.parola)
        if not fatto:
            return CIECO, "non ho potuto creare l'inquilino: %s" % perche
        self.creato = True
        self.segno = istante(self.n, self.desktop)
        self.prepara_l_occhio()
        self.browser, codice, perche = apri_browser(
            self.n, self.marca, PORTE[self.desktop], self.misura, tetto_accesso_s)
        if codice != VERDE:
            return codice, perche
        codice, perche = entra(self.browser, self.chi, self.parola, tetto_accesso_s)
        if codice != VERDE:
            return codice, "non sono entrato: %s" % perche
        accesa, dice = self.accendi_la_scena(scena_quale)
        if not accesa:
            return CIECO, dice
        self.prepara_il_topo()
        return VERDE, perche

    def accendi_la_scena(self, quale, giri=30, passo=2.0):
        """⭐ E SI RIPROVA, perche' la sessione grafica NASCE ADESSO.

        ⛔ Il compositore non c'e' nell'istante in cui il client viene ammesso:
           lo fa nascere il prodotto, e la scena ha bisogno del suo socket
           Wayland.  ⚠ Un solo tentativo subito dopo l'accesso fallisce quasi
           sempre, e farebbe dire «la scena non si accende» a uno strumento che
           ha solo avuto fretta (e' il giro d'attesa di `prova_viva`).
        """
        if not quale or quale == "ferma":
            return True, "scena «ferma»: non accendo niente"
        # ⭐⭐ LA SCENA DICHIARATA: chi ha l'occhio non accende una scena
        #   qualunque, accende QUELLA CHE L'OCCHIO SA LEGGERE.  ⛔ Altrimenti
        #   l'occhio direbbe «non lo so» per tutto il giro, che e' il modo
        #   elegante di non guardare niente.
        voluta = quale
        if self.occhio is not None and quale in SCENA_DELL_OCCHIO:
            voluta = SCENA_DELL_OCCHIO[quale]
        dice = "non ci ho nemmeno provato"
        for _ in range(giri):
            accesa, dice = scena(self.n, self.desktop, voluta, self.chi)
            if accesa:
                self.scena_accesa = voluta
                if self.occhio is not None:
                    self.occhio.acceso(voluta)
                return True, dice
            time.sleep(passo)
        if voluta != quale:
            # ⛔ E SE LA SCENA TESTIMONE NON SALE, si torna a quella di prima e
            #    si spegne l'occhio: la prova di questo scenario vale piu' del
            #    giudice nuovo, e un banco che non parte non misura niente.
            self.occhio_perche = ("la scena «%s» non si e' accesa (%s): giro "
                                  "senza occhio, con la scena «%s»"
                                  % (voluta, str(dice)[:120], quale))
            self.occhio = None
            for _ in range(max(1, giri // 2)):
                accesa, dice = scena(self.n, self.desktop, quale, self.chi)
                if accesa:
                    self.scena_accesa = quale
                    return True, "%s ⚠ %s" % (dice, self.occhio_perche)
                time.sleep(passo)
        return False, ("la scena «%s» non si e' accesa in %d s: %s"
                       % (voluta, int(giri * passo), dice))

    def rientra(self, misura=None, scena_quale=None, tetto_accesso_s=60):
        """Chiude il browser e rientra — l'inquilino e la sua sessione RESTANO.

        ⭐ E' il gesto di §7.6: il distacco non e' l'uscita.  ⚠ La misura della
          finestra si cambia apposta: e' il difetto curato il 22 set 2026.
        """
        if self.browser is not None:
            chiudi(self.browser)
            self.browser = None
        time.sleep(2.0)
        self.misura = misura or self.misura
        self.browser, codice, perche = apri_browser(
            self.n, self.marca, PORTE[self.desktop], self.misura, tetto_accesso_s)
        if codice != VERDE:
            return codice, perche
        codice, perche = entra(self.browser, self.chi, self.parola, tetto_accesso_s)
        # ⚠ La finestra si riapre: l'occhio riparte dall'attesa, o la prima
        #   fotografia e' l'animazione del compositore e non il prodotto.
        if self.occhio is not None:
            self.occhio.riscalda()
        if codice == VERDE and scena_quale:
            self.accendi_la_scena(scena_quale)
        return codice, perche

    def numeri(self):
        return numeri(self.n, self.browser)

    def server(self):
        return dal_server(self.n, self.desktop, self.segno, self.chi)

    def foto(self, nome=None):
        try:
            png = foto(self.browser)
        except Exception:                        # noqa: BLE001
            return None
        if nome and png:
            salva(self.dove, nome, png)
        return png

    def chiudi_tutto(self):
        """⚠ Si puo' chiamare due volte: `conta_il_ritmo()` la chiama apposta
        PRIMA della fine (le righe di riepilogo escono all'uscita), e il
        `finally` dello scenario la richiama comunque.  ⛔ Il secondo giro non
        deve rifare lo sgombero — sarebbe un minuto buttato a ogni scenario.

        ⛔⛔ E IL COMPOSITORE SI RILASCIA PER PRIMO: uno sgombero che trova
            processi fermi (stato T) non li fa morire col TERM, e il guasto
            innestato di questo giro diventerebbe il guasto del giro dopo."""
        if self.topo is not None:
            self.topo.rilascia()
        if self.browser is not None:
            chiudi(self.browser)
            self.browser = None
        if self.creato:
            self.creato = False
            sgombera(self.n, self.desktop, self.chi)

    def pulita(self):
        return scatola_pulita(self.n, self.desktop, miei=[self.chi])


def nome_inquilino(sigla):
    """Un nome corto e che dica da dove viene: `useradd` rifiuta i nomi lunghi."""
    return ("s%s%d" % (sigla, os.getpid()))[:12]
