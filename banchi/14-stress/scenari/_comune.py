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
   · la misura delle STRISCE sulla tela.

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

VERDE, ROSSO, CIECO = 0, 1, 3
PORTE = {"gnome": 8511, "kde": 8512, "xfce": 8513, "lxqt": 8514}
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
                       capture_output=True, text=True, timeout=secondi)
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
    nomi = {"kde": "kwin_wayland", "gnome": "gnome-shell", "xfce": "labwc"}
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
def strisce(png, riquadro=None):
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


# ═══════════════════════════════════════════════════════════════════════════
# 5 · GUARDARE NEL TEMPO
# ═══════════════════════════════════════════════════════════════════════════
def guarda_per(nucleo, browser, secondi, passo=5.0, tetto=None, ogni_giro=None):
    """Guarda i contatori della pagina per `secondi` e torna la STORIA.

    ⭐ La storia, non il totale: «e' salito per tutto il tempo» e «e' salito e
       poi si e' fermato» danno lo stesso totale, e la seconda e' precisamente
       il difetto del 22 settembre.
    """
    storia = []
    fine = time.time() + float(secondi)
    while time.time() < fine:
        if tetto is not None and tetto.scaduto():
            break
        n = numeri(nucleo, browser)
        n["t"] = round(time.time(), 1)
        storia.append(n)
        if ogni_giro:
            try:
                ogni_giro(n, storia)
            except Exception:                    # noqa: BLE001
                pass
        time.sleep(passo)
    if not storia or (time.time() - storia[-1]["t"]) > 1.0:
        n = numeri(nucleo, browser)
        n["t"] = round(time.time(), 1)
        storia.append(n)
    return storia


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
# 6 · IL BANCO — inquilino, browser e scena, e si sparecchia SEMPRE
# ═══════════════════════════════════════════════════════════════════════════
class Banco(object):
    """Apparecchia un giro e lo sparecchia comunque vada.

    ⛔ `chiudi_tutto()` si chiama da un `finally`: una notte di misure non puo'
       dipendere dal fatto che uno scenario finisca bene.
    """

    def __init__(self, nucleo, desktop, marca, chi, parola="stress2026",
                 misura=(1400, 1000), dove=None):
        self.n, self.desktop, self.marca = nucleo, desktop, marca
        self.chi, self.parola, self.misura, self.dove = chi, parola, misura, dove
        self.browser = None
        self.creato = False
        self.segno = None

    def apparecchia(self, scena_quale="pesante", tetto_accesso_s=60):
        """`(codice, perche)` — 0 apparecchiato · 1 il prodotto ha detto di no ·
        3 lo strumento non ce l'ha fatta."""
        fatto, perche = crea_inquilino(self.n, self.desktop, self.chi, self.parola)
        if not fatto:
            return CIECO, "non ho potuto creare l'inquilino: %s" % perche
        self.creato = True
        self.segno = istante(self.n, self.desktop)
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
        for _ in range(giri):
            accesa, dice = scena(self.n, self.desktop, quale, self.chi)
            if accesa:
                return True, dice
            time.sleep(passo)
        return False, ("la scena «%s» non si e' accesa in %d s: %s"
                       % (quale, int(giri * passo), dice))

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
        if self.browser is not None:
            chiudi(self.browser)
            self.browser = None
        if self.creato:
            sgombera(self.n, self.desktop, self.chi)

    def pulita(self):
        return scatola_pulita(self.n, self.desktop, miei=[self.chi])


def nome_inquilino(sigla):
    """Un nome corto e che dica da dove viene: `useradd` rifiuta i nomi lunghi."""
    return ("s%s%d" % (sigla, os.getpid()))[:12]
