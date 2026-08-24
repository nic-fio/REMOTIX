#!/usr/bin/env python3
"""09-b85-sincronia.py — LO SFALSO AUDIO-VIDEO, misurato invece che giudicato.

    python3 09-b85-sincronia.py --certifica          ⭐ senza macchina di prova
    python3 09-b85-sincronia.py giro --caso fermo
    python3 09-b85-sincronia.py giro --caso carico
    python3 09-b85-sincronia.py giro --caso perdita-1 --attesa 1800
    python3 09-b85-sincronia.py rimetti

---------------------------------------------------------------------------
⛔⛔ IL PUNTO APERTO, E PORTA CON SE' UN ERRORE DI METODO GIA' DICHIARATO

`fasi/09` §16.4: `[M]` **+331 ms a riposo**, **+690 ms sotto carico**, dal campo
`AV` del verbale della pagina.  ⛔ **Il numero non e' mai stato validato**: il
banco e' stato l'occhio dell'utente su un video di **pura grana**, e la
risposta e' stata *«non posso sapere se c'e' disallineamento se il video e'
incomprensibile»*.  ⇒ Due letture aperte, nessuna chiusa: o il disallineamento
**non morde**, o **lo strumento era inadeguato**.

⭐ Questo banco non sceglie fra le due: **taglia la domanda in due grandezze
   che si misurano separatamente**, e ne misura quella che il muro di Firefox
   lascia raggiungibile.

---------------------------------------------------------------------------
⭐⭐⭐ LE DUE META' DELLO SFALSO, E CONFONDERLE E' IL MODO FACILE DI SBAGLIARE

    quel che l'utente sente  =  SORGENTE  +  PERCORSO
                                    │           │
                                    │           └── `AV` della pagina: quanto
                                    │               ritarda l'audio RISPETTO al
                                    │               video **dopo** la marcatura
                                    │               (rete, coda, cuscino)
                                    │
                                    └── quanto sono gia' sfalsati i due flussi
                                        NEL MOMENTO IN CUI IL SERVER LI MARCA

⛔ `AV` **non puo' vedere la prima meta'.**  E' costruito apposta per elidere
   l'orologio: `aoff` e `voff` sottraggono tutt'e due l'`istante` del server, e
   se quell'istante e' **sbagliato di 300 ms sul video e giusto sull'audio**,
   `AV` esce **zero** e l'utente sente lo sfalso lo stesso.  ⇒ Un prodotto puo'
   avere `AV` verde ed essere desincronizzato, e questa e' la lettura che §16.4
   non poteva nemmeno formulare.

⭐ E LA PRIMA META' SI MISURA COSI', senza occhio e senza browser:
   §6.2 marca il fotogramma con «microsecondi dell'orologio **monotono del
   server** alla cattura»; §6.3 marca il blocco audio con lo stesso orologio.
   ⇒ Si mette sullo schermo un evento che si **vede** e si **sente** nello
   stesso istante (la claquette di `09-b85-claquette.py`), si guarda con che
   `istante` il server marca il lampo e con che `istante` marca il click, e la
   differenza e' la prima meta'.  ⛔ Zero e' il numero atteso.

⭐ E LA META' DI RETE si misura sulla stessa presa, **gratis e senza scena**:
   `arrivo - istante` per ciascun flusso, e la differenza fra le due latenze e'
   la parte di `AV` che vive prima del browser.  ⚠ Non e' `AV` — manca il
   cuscino dell'audio e la coda del decodificatore, che stanno nella pagina —
   e non si spaccia per `AV`.

---------------------------------------------------------------------------
⛔ IL MURO, DICHIARATO PRIMA DI COMINCIARE

`[M]` 24 agosto 2026: al server ci si attacca **uno per volta** — un secondo
client sullo stesso utente prende `CONGEDO(0x0f GIA_ATTIVA_REMOTA)`.  ⇒ Il
cliente che misura **e'** la sessione, e la scena si accende **dopo** che si e'
attaccato.  ⚠ E la meta' `AV` resta **aperta**: chiuderla vuole il browser, che
in questo momento non parte sulla macchina di prova.
"""
import argparse
import base64
import importlib.util
import json
import os
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ═══ 1 · L'ISOLAMENTO, PRIMA DI QUALUNQUE IMPORT CHE LO LEGGA ══════════════
#
# ⛔ `setdefault` e non `=`: i moduli dei banchi leggono l'ambiente **all'import**
#    (`LEZIONI.md` §1.26).  Un import fatto e poi corretto scriverebbe nel
#    lavoro di un altro agente e guasterebbe la porta di un altro banco —
#    e nessuno dei due darebbe rosso.
PORTA = int(os.environ.setdefault("PORTA", "7973"))
UTENTE = os.environ.setdefault("UTENTE", "provanr10")
UID_B = int(os.environ.setdefault("UID_B", "1073"))
MACCHINA = os.environ.setdefault("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.setdefault("PAROLA_SUDO", "nicfio")
IND = os.environ.setdefault("IND", "192.168.0.2")
LAV = os.environ.setdefault("LAV", "/media/REMOTIX/tmp/09nr10")
ALB = os.environ.setdefault("ALBERO", "/media/REMOTIX/src/09nr10-src")
DENTRO_ALB = os.environ.setdefault("DENTRO_ALB", "/srv/src/09nr10-src")
DENTRO_LAV = os.environ.setdefault("DENTRO_LAV", "/srv/remotix/tmp/09nr10")
os.environ.setdefault("PORTE_SONDA", "7979,7978,7977,7976,7975")
UNITA = os.environ.setdefault("UNITA", "remotix-%d" % PORTA)
FUORI = os.environ.setdefault("FUORI", "/tmp/09-b85")
DEV, VIETATA = "lo", "enp7s0"
CHI, AFFITTO = "09-b85", 900
FILM = LAV + "/film"

# ⛔ Le porte che NON sono mie, e la 7920 e' la sessione VIVA dell'utente.
VICINE = ("7900", "7910", "7920", "7700", "7730")


def _carica(nome, file_):
    sp = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file_))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


METRO = _carica("b85metro", "09-b85-metro.py")
LUC = _carica("lucchetto", "09-lucchetto.py")


def _log(t):
    print("   " + t, flush=True)


def _ok(t):
    print("   ✅ " + t, flush=True)


def _ko(t):
    print("   ⛔ " + t, flush=True)


def _inf(t):
    print("   -- " + t, flush=True)


# ═══ 2 · LE MANI SULLA MACCHINA ═══════════════════════════════════════════

def rem(comando, tetto=300):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                       capture_output=True, text=True, timeout=tetto)
    return p.returncode, p.stdout, p.stderr


def root(comando, tetto=300):
    """⛔ `sudo -S` copre UN comando solo e **consuma lo stdin**: una catena va
       dentro un `bash -c "…"`, o la seconda meta' gira come `nicfio` e fa
       *Permission denied* su un albero dove il file vecchio c'e' gia' — cioe'
       in silenzio (`09-b76`:1586)."""
    return rem("printf '%%s\\n' '%s' | sudo -S -p '' %s" % (PAROLA_SUDO, comando),
               tetto)


def dentro(comando, tetto=300):
    """Dentro il contenitore: fuori non c'e' `aioquic`."""
    return root("bash /media/REMOTIX/enter.sh --root '%s'" % comando, tetto)


def vicine():
    _, out, _ = rem("ss -lun 2>/dev/null | grep -oE ':(%s)' | sort -u | tr '\\n' ' '"
                    % "|".join(VICINE), 60)
    return out.strip() or "(nessuna)"


# ═══ 3 · LA SCENA ═════════════════════════════════════════════════════════

def scena_accendi(film):
    rc, out, err = root("env LAV=%s UID_B=%d UTENTE=%s FILM=%s sh /tmp/09-b85-scena.sh accendi"
                        % (LAV, UID_B, UTENTE, film), 180)
    if "SCENA ACCESA" not in out:
        return False, (out + err)[-500:]
    return True, out.strip().splitlines()[0]


def scena_spegni():
    root("env UID_B=%d sh /tmp/09-b85-scena.sh spegni; true" % UID_B, 120)


def cliente_fermo(tetto=40):
    """⛔⛔ SI CONGEDA, NON SI AMMAZZA — e la differenza e' un giro perso.

    `[M]` 24 agosto 2026, primo tentativo: il cliente di prima ucciso con
    `-9`, un secondo e mezzo d'attesa, e il giro nuovo si e' preso
    `CONGEDO(0x0f GIA_ATTIVA_REMOTA)` con **zero fotogrammi e zero blocchi**.
    ⚠ Non e' un difetto del prodotto: un cliente ucciso di forza **non manda
    il CONGEDO**, e il server tiene la sessione attiva finche' non se ne
    accorge da se' — e' la stessa trappola gia' pagata da
    `09-b71-sessione.sh`:21-36 il 23 agosto.

    ⇒ TERM, si **aspetta che il processo sparisca davvero**, e solo alla fine
      `-9`.  ⚠ E poi si aspetta ancora: «il cliente e' morto» e «il server ha
      liberato la sessione» sono due fatti diversi, e il secondo arriva dopo.
    """
    pat = "(09-b85-cliente|b3-cliente)[.]py .*--porta %d" % PORTA
    root("bash -c \"pkill -f '%s' ; true\"" % pat, 120)
    for _ in range(tetto):
        rc, out, _ = root("bash -c \"pgrep -f '%s' | head -1\"" % pat, 60)
        if not out.strip():
            break
        time.sleep(1)
    else:
        _inf("il cliente non se n'e' andato con TERM: -9")
        root("bash -c \"pkill -9 -f '%s' ; true\"" % pat, 120)
        time.sleep(3)
    time.sleep(3)


# ═══ 3-bis · IL GUASTO DI RETE ════════════════════════════════════════════
#
# ⛔⛔ IL `netem` SU `lo` E' UNA RISORSA SOLA PER TUTTA LA MACCHINA.
#     La disciplina si mette sulla RADICE dell'interfaccia: due banchi che
#     guastano insieme non si dividono il lavoro — **il secondo cancella il
#     guasto del primo, e il primo continua a misurare credendo di averlo**.
#     ⚠ E non darebbe rosso: darebbe un numero plausibile.  ⇒ Il possesso si
#     prende col lucchetto di `09-lucchetto.py` (`mkdir`, atomico anche su ssh).
#
# ⛔ E `enp7s0` NON SI TOCCA MAI: ci passano l'ssh e la sessione viva
#    dell'utente sulla 7920.

def guasta(percento):
    """`tc` sulla banda 1:4, e solo per LA MIA porta.  ⛔ Il filtro sulla porta
       e' quel che tiene il guasto dentro il mio banco: un `netem` sulla radice
       senza filtro guasterebbe anche l'audio della sessione dell'utente."""
    passi = [
        "/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV,
        "/usr/sbin/tc qdisc add dev %s root handle 1: prio bands 4" % DEV,
        "/usr/sbin/tc qdisc add dev %s parent 1:4 handle 40: netem limit 20000 "
        "delay 15ms loss %s%%" % (DEV, percento),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip sport %d 0xffff flowid 1:4"
        % (DEV, PORTA),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip dport %d 0xffff flowid 1:4"
        % (DEV, PORTA),
    ]
    root("bash -c \"%s\"" % " ; ".join(passi), 180)
    # ⛔ E SI RILEGGE: «ho messo» e «c'e'» sono due fatti diversi, e `tc` e'
    #    appiccicoso.  Un banco che desse per messo un guasto che non c'e'
    #    misurerebbe la linea liscia e la chiamerebbe perdita.
    rc, out, _ = root("/usr/sbin/tc qdisc show dev %s" % DEV, 60)
    messa = ("loss %s%%" % percento) in out or ("loss %s.%%" % percento) in out
    return messa, out.strip().replace("\n", " · ")


def guasto_visto():
    """La seconda gamba: il `dropped` del qdisc.  ⛔ Un solo testimone su un
       guasto e' un testimone che non si puo' controllare."""
    rc, out, _ = root("/usr/sbin/tc -s qdisc show dev %s" % DEV, 60)
    import re as _re
    m = _re.findall(r"dropped (\d+)", out)
    return sum(int(x) for x in m) if m else None


# ═══ 4 · IL GIRO ══════════════════════════════════════════════════════════

def giro(nome, film, secondi, ritardo_scena=14.0):
    """Una presa: il cliente apre la sessione, poi si accende la claquette.

    ⛔ L'ORDINE E' OBBLIGATO e non e' una comodita': il pozzo audio `remotix` e
       il monitor li crea il figlio del server **quando un client si attacca**
       (I4).  Accendere mpv prima vorrebbe dire mandarlo sul pozzo predefinito,
       che non e' catturato — e si misurerebbe **silenzio**, che ha la stessa
       faccia di «l'audio non arriva».
    """
    cliente_fermo()
    scena_spegni()
    base = "%s/%s" % (DENTRO_LAV, nome)
    seg = base + ".segnale"
    root("bash -c \"rm -f %s/%s.* ; true\"" % (LAV, nome), 60)
    cmd = ("python3 -u %s/banchi/09-b85-cliente.py --indirizzo %s --porta %d "
           "--utente %s --parola-file %s/parola --audio-codec pcm "
           "--video-codec h264 --adatta 1920x1080 --segnale %s "
           "--video-scrivi %s.h264 --audio-scrivi %s-audio.jsonl "
           "--tempi %s-tempi.jsonl --resta %.1f"
           % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, seg,
              base, base, base, secondi))
    dentro("setsid nohup %s > %s.log 2>&1 & sleep 1; echo lanciato"
           % (cmd, base), 120)

    # ⛔ Si aspetta il SEGNALE, non un tempo: «la sessione si e' aperta» e «sono
    #    passati N secondi» sono due fatti diversi, e su una macchina carica il
    #    secondo mente.
    # ⭐ E si guarda ANCHE il registro del cliente, perche' `GIA_ATTIVA_REMOTA`
    #    e' un fallimento che arriva in un secondo: aspettarlo sessanta
    #    vorrebbe dire buttare un minuto per sapere una cosa gia' scritta.
    aperta = False
    for _ in range(75):
        rc, out, _ = root("bash -c \"test -f %s/%s.segnale && echo SI ; "
                          "grep -c GIA_ATTIVA_REMOTA %s/%s.log 2>/dev/null || true\""
                          % (LAV, nome, LAV, nome), 60)
        if "SI" in out:
            aperta = True
            break
        if out.strip().splitlines() and out.strip().splitlines()[-1] not in ("0", ""):
            return {"guasto": "⛔ CONGEDO(0x0f GIA_ATTIVA_REMOTA): un'altra "
                              "sessione e' ancora aperta su questo utente. "
                              "⇒ NON e' un difetto del prodotto, e' il cliente "
                              "di prima che non si e' congedato"}
        time.sleep(1)
    if not aperta:
        return {"guasto": "⛔ la sessione non si e' aperta: NON misuro"}
    _ok("sessione aperta")
    time.sleep(max(0.0, ritardo_scena - 2))
    acceso, dettaglio = scena_accendi(film)
    if not acceso:
        cliente_fermo()
        return {"guasto": "⛔ la claquette NON si accende: %s" % dettaglio}
    _ok("claquette accesa — %s" % dettaglio)

    # si aspetta che il cliente finisca da se'
    for _ in range(int(secondi) + 120):
        rc, out, _ = root("bash -c \"pgrep -f '09-b85-cliente[.]py .*--porta %d' | "
                          "head -1\"" % PORTA, 60)
        if not out.strip():
            break
        time.sleep(2)
    scena_spegni()
    rc, out, _ = root("bash -c \"tail -25 %s/%s.log\"" % (LAV, nome), 60)
    return {"log": out}


def porta_giu(nome):
    """I tre file della presa vengono sul portatile, dove c'e' il metro."""
    os.makedirs(FUORI, exist_ok=True)
    root("bash -c \"chmod 644 %s/%s.* 2>/dev/null; ls -la %s/%s.* \""
         % (LAV, nome, LAV, nome), 60)
    fuori = []
    for est in (".h264", "-audio.jsonl", "-tempi.jsonl"):
        loc = "%s/%s%s" % (FUORI, nome, est)
        p = subprocess.run(["scp", "-q", "-o", "BatchMode=yes",
                            "%s:%s/%s%s" % (MACCHINA, LAV, nome, est), loc],
                           capture_output=True, text=True, timeout=900)
        if p.returncode or not os.path.exists(loc):
            return None, "⛔ non arriva «%s%s»: %s" % (nome, est, p.stderr[-200:])
        fuori.append(loc)
    return fuori, None


# ═══ 5 · LA META' DI RETE — gratis, sulla stessa presa ════════════════════

def sfalso_di_rete(tempi_jsonl):
    """⭐ `arrivo - istante` per ogni flusso, e la differenza fra le due.

    ⛔ E si guarda la MEDIANA e non la media: sotto perdita la coda del video
       ha delle punte lunghissime, e una media le lascerebbe dominare il numero
       — cioe' direbbe «il video e' indietro di due secondi» perche' **un**
       fotogramma lo era.  ⚠ E si stampano tutt'e due, e anche il 90esimo:
       la coda **e'** quel che l'utente vede, e nasconderla sarebbe la stessa
       forma d'errore di §16.4 al contrario.
    """
    v, a = [], []
    with open(tempi_jsonl) as f:
        for r in f:
            r = r.strip()
            if not r:
                continue
            d = json.loads(r)
            lat = d["arrivo"] - d["istante"] / 1e6
            (v if d["che"] == "video" else a).append(lat)
    if len(v) < 20 or len(a) < 20:
        return {"guasto": "⛔ %d fotogrammi e %d blocchi: non misuro" % (len(v), len(a))}

    def q(x, p):
        y = sorted(x)
        return y[min(len(y) - 1, int(p * len(y)))]

    # ⛔ Le due latenze contengono TUTT'E DUE lo scarto (ignoto) fra l'orologio
    #    monotono del server e il mio: si elide nella differenza, esattamente
    #    come si elide dentro `AV`.  ⇒ I due valori assoluti NON significano
    #    niente da soli, e non si stampano come se lo fossero.
    dv, da = q(v, 0.5), q(a, 0.5)
    return {"fotogrammi": len(v), "blocchi": len(a),
            "video_mediana_ms": round(dv * 1000, 1),
            "audio_mediana_ms": round(da * 1000, 1),
            "video_p90_ms": round(q(v, 0.9) * 1000, 1),
            "audio_p90_ms": round(q(a, 0.9) * 1000, 1),
            # positivo = l'audio arriva DOPO il video (stessa convenzione)
            "sfalso_rete_ms": round((da - dv) * 1000, 1),
            "sfalso_rete_p90_ms": round((q(a, 0.9) - q(v, 0.9)) * 1000, 1)}


# ═══ 6 · L'AUTOPROVA ══════════════════════════════════════════════════════

def certifica():
    print("\n   ⭐ 09-b85-sincronia — l'autoprova, senza macchina di prova\n")
    male = 0
    # ⛔ L'isolamento si verifica QUI, non nel rapporto: un banco che girasse
    #    sulla 7920 spegnerebbe la sessione viva dell'utente.
    if PORTA in (7900, 7910, 7920) or UTENTE in ("prova", "prova2"):
        _ko("girerei sulla sessione di qualcun altro: NON misuro")
        male += 1
    else:
        _ok("isolamento: porta %d, utente %s, unita' %s" % (PORTA, UTENTE, UNITA))
    if DEV != "lo" or VIETATA != "enp7s0":
        _ko("la rete che guasterei non e' `lo`")
        male += 1
    else:
        _ok("il guasto va su `lo`; `enp7s0` non si tocca")
    # ⛔ Il conto della latenza si prova su numeri INVENTATI di cui so la
    #    risposta: un banco che non sa sommare non se ne accorge misurando.
    import tempfile
    d = tempfile.mkdtemp(prefix="b85cert")
    p = os.path.join(d, "t.jsonl")
    with open(p, "w") as f:
        for i in range(100):
            # video marcato a i*25ms, arrivato 100 ms dopo
            f.write(json.dumps({"che": "video", "numero": i,
                                "istante": i * 25000,
                                "arrivo": i * 0.025 + 0.100}) + "\n")
            # audio marcato a i*25ms, arrivato 40 ms dopo ⇒ sfalso -60 ms
            f.write(json.dumps({"che": "audio", "istante": i * 25000,
                                "arrivo": i * 0.025 + 0.040}) + "\n")
    s = sfalso_di_rete(p)
    if s.get("sfalso_rete_ms") != -60.0:
        _ko("il conto della latenza da' %s invece di -60,0" % s.get("sfalso_rete_ms"))
        male += 1
    else:
        _ok("il conto della latenza: -60,0 ms su un caso di cui so la risposta")
    print()
    if male:
        _ko("NON MISURARE finche' non e' verde.")
        return 3
    _ok("verde.")
    return 0


# ═══ 7 · IL RIPRISTINO ════════════════════════════════════════════════════

def rimetti():
    root("/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV, 120)
    rc, out, _ = root("/usr/sbin/tc qdisc show dev %s" % DEV, 120)
    pulita = "netem" not in out and "tbf" not in out
    rc2, out2, _ = root("/usr/sbin/tc qdisc show dev %s" % VIETATA, 120)
    (_ok if pulita else _ko)("`lo`: %s" % out.strip().replace("\n", " · "))
    _inf("`%s` (mai toccata): %s" % (VIETATA, out2.strip().replace("\n", " · ")))
    _inf("porte NON mie: %s" % vicine())
    return 0 if pulita else 2


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="lo sfalso audio-video, misurato")
    p.add_argument("passo", nargs="?", default="")
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--caso", default="fermo")
    p.add_argument("--film", default="")
    p.add_argument("--secondi", type=float, default=60.0)
    p.add_argument("--nome", default="")
    p.add_argument("--perdita", default="",
                   help="percentuale di perdita `netem` su `lo`, solo sulla MIA "
                        "porta e col lucchetto (es. `1` o `5`)")
    p.add_argument("--attesa", type=float, default=1800,
                   help="quanto si aspetta il lucchetto del netem")
    a = p.parse_args()
    if a.certifica or a.passo == "certifica":
        sys.exit(certifica())
    if a.passo == "rimetti":
        sys.exit(rimetti())
    if a.passo == "giro":
        nome = a.nome or ("b85-" + a.caso)
        film = a.film or (FILM + "/09-b85-claquette-calma-p000.mp4")
        preso = False
        try:
            if a.perdita:
                # ⛔ Il lucchetto PRIMA di toccare `tc`, e si molla in un
                #    `finally`: un banco che morisse col guasto messo lo
                #    lascerebbe addosso a chi viene dopo, che misurerebbe una
                #    rete cattiva credendola liscia.
                LUC.prendi(CHI, secondi=AFFITTO, attesa=a.attesa)
                preso = True
                messa, q = guasta(a.perdita)
                (_ok if messa else _ko)("il guasto: %s" % q)
                if not messa:
                    _ko("la regola chiesta NON e' quella installata: NON misuro")
                    sys.exit(2)
                d0 = guasto_visto()
            e = giro(nome, film, a.secondi)
            if a.perdita:
                d1 = guasto_visto()
                _inf("il qdisc ha buttato %s pacchetti durante il giro"
                     % (None if d1 is None or d0 is None else d1 - d0))
        finally:
            if preso:
                rimetti()
                LUC.molla(CHI)
        if e.get("guasto"):
            _ko(e["guasto"])
            sys.exit(2)
        print(e.get("log", ""))
        f, guasto = porta_giu(nome)
        if guasto:
            _ko(guasto)
            sys.exit(2)
        print("\n   ⭐ LA META' DI RETE (arrivo - istante):")
        print(json.dumps(sfalso_di_rete(f[2]), indent=1, ensure_ascii=False))
        print("\n   ⭐ LA META' DELLA SORGENTE (la claquette):")
        print(json.dumps(METRO.misura_presa(f[0], f[2], f[1]), indent=1,
                         ensure_ascii=False))
        sys.exit(0)
    p.print_help()
    sys.exit(2)
