#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07-b64-rete — IL DATAGRAM QUANDO LA RETE NON E' IDEALE.

⛔ Che cosa era aperto (`fasi/07-audio-e-appunti.md` §8): *«1024/1214 byte sono
   presi **su cavo**; il giudizio dell'utente e' su **rete di casa**, e vale per
   quella»*.

⭐ Qui ci sono due misure, e sono diverse:

   1. **`casa`** — il cliente di prova gira SUL PORTATILE, che sta in **WiFi**
      (`wlo1`, 192.168.0.3), e il server e' sulla macchina di prova, in cavo.
      ⇒ Il datagram attraversa davvero l'aria: e' la «rete di casa», non una
      simulazione.  ⛔ Nessun `tc`, nessuna regola: si guarda e basta.

   2. **`netem`** — la rete si guasta APPOSTA, a gradini, per trovare il punto
      in cui l'esperienza si rompe.  ⛔ E qui c'e' un vincolo che vale piu' della
      misura: **la regola non deve toccare ne' la sessione ssh ne' la 7730
      dell'utente**.
      ⇒ Il guasto si mette su **`lo`** della macchina di prova (il cliente gira
        dentro il contenitore, quindi il suo traffico passa di li'), con un
        `prio` a quattro bande e **due filtri `u32` sulla sola porta 7801**:
        tutto il resto del traffico locale resta nelle bande predefinite.
        ⛔ `enp7s0` — che porta l'ssh e la 7730 — **non si tocca mai**.
      ⚠ E si dichiara il prezzo di questa scelta: su `lo` la MTU e' 65536, ⇒
        **questa meta' NON rimisura «quanti byte porta un datagram»**.  Quella
        domanda la puo' chiudere solo un cliente vero su una rete vera, ed e' la
        misura 1.

⛔ IL DISINNESCO E' AUTOMATICO: prima di applicare qualunque regola si lancia un
   guardiano staccato che, dopo N secondi, toglie la disciplina **anche se
   questo copione muore o l'ssh cade**.  Una macchina lasciata con `netem` su
   `lo` e' un guasto che il prossimo banco attribuirebbe al prodotto.
   ⚠ E per otto profili su nove **questo file non lo rispettava**: vedi il
     riquadro di `rimetti`, cura del 23 agosto 2026.

⛔⛔ QUATTRO DIFETTI CURATI IL 23 AGOSTO 2026, e sono tutti e quattro della
    stessa forma — **silenzio invece di rosso**, cioe' un numero plausibile e
    falso al posto di un «non ho letto» o di un rosso:
      1. `rimetti()` disarmava il guardiano dal gradino `0-liscio`, il PRIMO
         ⇒ gli otto dopo giravano scoperti.  ⇒ `rimetti(dillo, disarma)`.
      2. `a_non_si_apre` (`ricevuti == 0`) non poteva dare rosso: il cliente
         stampa `[audio] ricevuti 0` anche dal ramo `except`.  ⇒ sostituito da
         `a_resa_sul_filo`, che guarda i DUE capi.  E il `[M]` che ci stava
         appeso era falso (`banchi/09-b78-apertura.py`).
      3. `spediti_dal_server` a `None` («non ho letto il registro») filava al
         predicato come se fosse tutto a posto ⇒ adesso e' MUTO.
      4. La chiusura di una sessione e' LENTA (`[M]` fino a 29 s in piu' col
         pacer in coda) ⇒ il conto del server era **di un altro giro**, e il
         posto di §4.4-bis era ancora occupato.  ⇒ `registro_posato()`.
    ⚠ R13 era stato dichiarato chiuso su questo file, e ne sono usciti altri
      quattro casi: la forma non e' un difetto, e' un'abitudine del banco.

⭐ `[M]` 23 agosto 2026, giro intero dopo le cure — **9 gradini, 0 rossi, 0
   muti**, e il gradino della perdita adesso misura il filo:
   `7-perdita-10` ⇒ ricevuti **4 077** / spediti dal server **4 504** =
   **0,905**, contro `1-p` = 0,901 con `p` = **9,91 %** letta da `tc -s qdisc`.

Uso (dal portatile):
    python3 banchi/07-b64-rete.py casa   [--secondi 30]
    python3 banchi/07-b64-rete.py netem  [--secondi 25]
    python3 banchi/07-b64-rete.py rimetti          # ⛔ e si verifica
"""
import argparse, json, os, subprocess, sys, time

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
PORTA = int(os.environ.get("PORTA", "7801"))
UTENTE = os.environ.get("UTENTE", "provar7")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/07-r")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/07-r-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/07-r")
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/07-r-src")
UID_B = int(os.environ.get("UID_B", "1018"))
QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.environ.get("FUORI", "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2/"
                                "84687524-93d6-4003-8cd1-1ed07aa63454/scratchpad/r7")

# ⛔ L'interfaccia che NON si tocca, scritta qui perche' si veda:
VIETATA = "enp7s0"          # ci passano l'ssh e la 7730 dell'utente
DEV = "lo"                  # ci passa solo il traffico locale, cioe' il mio

# I gradini, dal piu' mite al piu' cattivo.  ⭐ L'atteso e' scritto PRIMA.
# ⛔⛔ R13 — GLI «ATTESO» ERANO PROSA: stampati, archiviati, MAI confrontati.
#      Nove frasi che descrivevano quel che sarebbe dovuto succedere, e nessuna
#      riga che verificasse se era successo.  ⚠ Un banco cosi' non puo' dare
#      rosso: qualunque numero esca, la frase accanto resta vera «a leggerla».
#
# ⭐ Adesso ogni gradino porta un PREDICATO — una funzione che riceve i numeri
#    e torna `(passa, perche)` — e il verdetto del banco e' la loro somma.
#    L'uscita del copione e' 0 solo se tutti passano.
#
# ⛔ E i predicati sono scritti PRIMA di girare, come gli attesi di `07-b43`:
#    sono la predizione, e quando sbagliano si vede (`LEZIONI.md` §1.11).


def _p(cond, perche):
    return (bool(cond), perche)


def a_pulito(n):
    """Il denominatore: quasi tutto arriva, niente si scarta, il tono e' puro."""
    return _p(n["resa"] is not None and n["resa"] >= 0.99
              and n["vecchi"] == 0 and (n["purezza"] or 0) >= 0.80,
              "resa >= 0,99 · vecchi 0 · purezza >= 0,80")


def a_come_pulito(n):
    """Il ritardo fisso non riordina: dev'essere indistinguibile dal liscio."""
    return a_pulito(n)


def a_sorpassi(minimo):
    """Il jitter fa sorpassare i datagram, e §6.3 li butta: «vecchi» DEVE salire."""
    def f(n):
        return _p(n["vecchi"] >= minimo,
                  "vecchi >= %d (il jitter riordina e §6.3 scarta)" % minimo)
    return f


def a_perdita(frazione, tolleranza=0.5):
    """La perdita si vede nella resa, e in proporzione a quel che netem toglie."""
    def f(n):
        if n["resa"] is None:
            return _p(False, "nessuna resa da confrontare")
        atteso = 1.0 - frazione
        return _p(abs(n["resa"] - atteso) <= tolleranza * frazione + 0.02,
                  "resa ~ %.3f (perdita %.0f%%), vista %.3f"
                  % (atteso, frazione * 100, n["resa"]))
    return f


def a_resa_sul_filo(frazione, tolleranza=0.35):
    """LA RESA MISURATA SUI DUE CAPI: quanti ne ha spediti il SERVER, quanti ne
    ha ricevuti il CLIENTE — e il confronto e' con la perdita che `netem` ha
    **davvero** applicato, letta da `tc -s qdisc`, non con quella chiesta.

    ⛔⛔ QUESTO PREDICATO SOSTITUISCE `a_non_si_apre`, CHE NON POTEVA DARE
       ROSSO.  Era:

           def a_non_si_apre(n): return _p(n["ricevuti"] == 0, ...)

       e `banchi/01-b3-cliente.py:1466` (`scrivi_audio`) stampa
       `[audio] ricevuti 0` **anche dal ramo `except`**, prima di rilanciare.
       ⇒ **Ogni** modo di fallire — un `CONGEDO`, un tetto scaduto, un
       `NameError` del banco — dava «ricevuti 0» e faceva passare il gradino di
       **verde**.  Non misurava *«non si apre»*: misurava *«non ho ricevuto»*,
       e le due cose hanno la stessa faccia (`LEZIONI.md` §1.9).
    ⛔ E il `[M]` che ci stava appeso — *«la sessione non si apre affatto in
       25 s»* — era **falso**.  `[M]` 23 agosto 2026, `banchi/09-b78-apertura.py`:
       al 10 % di perdita la sessione si apre **10 volte su 10 in 1,1 s**
       (mediana), al 25 % 10/10 in 1,3 s; la rete costa **285 ms** fra lo 0 e
       il 25 %, e il secondo che si vedeva era il ritardo fisso di §4.4-bis.

    ⚠⚠ E IL CONTO DELLA PERDITA ATTESA NON E' QUELLO CHE SEMBRA — chi lo
       ritara senza questa nota lo ritara nel verso sbagliato.
       I due filtri `u32` di `guasta()` prendono i **due versi** (`sport` e
       `dport`), quindi:
         · un **giro** di rete (andata + ritorno) paga `1-(1-p)²`
           ⇒ il **19 %** quando `p` = 10 %;
         · un **datagram**, che fa **un verso solo**, paga `p`
           ⇒ il **10 %** quando `p` = 10 %.
       Qui si guarda un datagram, non un giro: la resa attesa e' **`1-p`**.
       `[M]` 23 agosto 2026 a `p` = 10 %: ricevuti **3 235**, spediti dal
       server **3 607** ⇒ resa **0,897**, che e' `1-p` (0,90), **non**
       `1-(1-p)²` (0,81).

    ⚠ E questa resa NON e' `resa_campioni` del giudice: quella ci mette dentro
      anche i blocchi che il server non ha **mai** spedito (finestra chiusa —
      `[M]` 391 su 3 607 al 10 %), e cosi' somma «perso sul filo» e «mai
      spedito», che sono due fatti.  Qui il denominatore e' `spediti`.
    """
    def f(n):
        ric, sped = n.get("ricevuti"), n.get("spediti_dal_server")
        # ⛔ `CODER.md` §3.10: «non ho letto» non e' «zero», ed e' rosso.
        if ric is None or not sped:
            return _p(False, "manca un capo del conto: ricevuti=%s · "
                             "spediti dal server=%s" % (ric, sped))
        resa = ric / float(sped)
        vera = n.get("perdita_vera")
        p = vera if vera is not None else frazione
        atteso = 1.0 - p
        larghezza = tolleranza * p + 0.02
        return _p(abs(resa - atteso) <= larghezza,
                  "resa sul filo %d/%d = %.3f · attesa 1-p = %.3f "
                  "(p %s = %.3f, ±%.3f)"
                  % (ric, sped, resa, atteso,
                     "letta da tc" if vera is not None else "CHIESTA (tc muto)",
                     p, larghezza))
    return f


PROFILI = [
    ("0-liscio", [], "nessun guasto: e' il denominatore, e deve essere pulito",
     a_pulito),
    ("1-ritardo-30", ["delay", "30ms"],
     "30 ms fissi, senza jitter: arrivano tardi ma in ordine -- non deve cambiare niente",
     a_come_pulito),
    ("2-jitter-2", ["delay", "20ms", "2ms", "distribution", "normal"],
     "jitter 2 ms, meno di un blocco PCM (5 ms): i sorpassi devono gia' esserci",
     a_sorpassi(100)),
    ("3-jitter-5", ["delay", "20ms", "5ms", "distribution", "normal"],
     "jitter 5 ms = un blocco: i sorpassi crescono",
     a_sorpassi(500)),
    ("4-jitter-10", ["delay", "20ms", "10ms", "distribution", "normal"],
     "jitter 10 ms = due blocchi", a_sorpassi(1000)),
    ("5-jitter-15", ["delay", "30ms", "15ms", "distribution", "normal"],
     "jitter 15 ms = tre blocchi: qui l ascolto e' gia' rotto",
     a_sorpassi(1500)),
    ("6-perdita-1", ["loss", "1%"], "1 datagram su 100 perso",
     a_perdita(0.01)),
    # ⛔ LA PROSA DI QUESTO GRADINO ERA FALSA e va letta come un avvertimento:
    #    diceva «10 %: `[M]` la sessione non si apre affatto in 25 s».
    #    `[M]` 23 agosto 2026 (`banchi/09-b78-apertura.py`): la sessione si apre
    #    **10 volte su 10, mediana 1,1 s**; al 25 % 10/10 in 1,3 s.  Il `[M]`
    #    vecchio era il riflesso di un predicato che non poteva dare rosso.
    ("7-perdita-10", ["loss", "10%"],
     "10 %: `[M]` 23 ago 2026 la sessione SI APRE (10/10, mediana 1,1 s) e il "
     "filo rende 1-p ~ 0,90 — ricevuti/spediti sui due capi, non 1-(1-p)²",
     a_resa_sul_filo(0.10)),
    ("8-casa-cattiva", ["delay", "40ms", "20ms", "distribution", "normal",
                        "loss", "2%"],
     "il misto che somiglia a una casa col WiFi lontano", a_sorpassi(500)),
]


def rem(comando, tetto=120):
    """⛔ Niente redirezione ATTORNO a ssh: la richiesta di sudo va sullo stderr
       e un redirect la mangerebbe — il comando resterebbe appeso in silenzio."""
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                       capture_output=True, timeout=tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def root(comando, tetto=120):
    return rem("printf '%%s\\n' '%s' | sudo -S -p '' %s" % (PAROLA_SUDO, comando), tetto)


def qdisc():
    return root("/usr/sbin/tc qdisc show dev %s" % DEV)[1].strip()


def perdita_vera():
    """⛔ LA PERDITA CHE `netem` HA DAVVERO APPLICATO, **letta** e non dedotta.

    ⚠ «Ho chiesto il 10 %» e «ne ha buttati il 10 %» sono due fatti diversi:
      `netem` butta a caso, e su qualche migliaio di pacchetti la frazione vera
      si scosta.  Il predicato si tara su QUESTA, o darebbe rosso alla rete
      invece che al prodotto.
    ⛔ Si legge PRIMA di passare al gradino dopo: il `tc qdisc del` con cui si
       apre il profilo successivo azzera i contatori.
    Torna `None` quando non c'e' nessun `netem` (gradino liscio) o quando la
    riga non si legge — ⛔ e `None` NON e' zero.
    """
    rc, out, _ = root("/usr/sbin/tc -s qdisc show dev %s" % DEV)
    import re as _re
    dentro = False
    for riga in out.split("\n"):
        s = riga.strip()
        if s.startswith("qdisc netem"):
            dentro = True
            continue
        if dentro and s.startswith("qdisc"):
            break
        if dentro and "Sent" in s:
            m = _re.search(r"Sent \d+ bytes (\d+) pkt \(dropped (\d+)", s)
            if not m:
                return None
            passati, buttati = int(m.group(1)), int(m.group(2))
            tot = passati + buttati
            return round(buttati / float(tot), 4) if tot else None
    return None



# ── ⛔ IL GUARDIANO SI ARMA E SI DISARMA PER PID, NON PER MOTIVO ───────────
GUARDIANO = LAV + "/.guardiano.pid"


def guardiano_arma(secondi):
    """Nasce con `setsid`: e' capo del suo gruppo, e il gruppo si uccide intero."""
    guardiano_disarma()
    # ⛔ Il `&` e l'`echo $!` devono girare DENTRO la shell di root, o il
    #    redirect verso `$LAV` (che e' di root) fallisce e il pid non si scrive:
    #    `[M]` il primo giro stampava «pid ?», cioe' un guardiano che non si
    #    sarebbe potuto disarmare per pid — la cura senza la sua meta'.
    root('bash -c "setsid sh -c \'sleep %d; /usr/sbin/tc qdisc del dev %s root\' '
         '>/dev/null 2>&1 & echo \\$! > %s"' % (secondi, DEV, GUARDIANO))
    rc, out, _ = root("cat %s 2>/dev/null" % GUARDIANO)
    print("   OK  guardiano armato per %d s (pid %s): la rete torna com'era "
          "ANCHE se muoio" % (secondi, out.strip() or "?"))


def guardiano_disarma():
    """⛔ Si uccide il GRUPPO, cosi' `sh` non arriva mai alla riga del `tc`."""
    rc, out, _ = root("cat %s 2>/dev/null || true" % GUARDIANO)
    p = out.strip()
    if p.isdigit():
        root("kill -TERM -%s 2>/dev/null; kill -TERM %s 2>/dev/null; true" % (p, p))
    root("rm -f %s; true" % GUARDIANO)


def rimetti(dillo=True, disarma=True):
    """⛔ E si VERIFICA: «ho tolto» e «non c'e' piu'» sono due fatti diversi.

    ⛔⭐ `disarma` NON E' UNA COMODITA', ED ECCO PERCHE' ESISTE — chi lo legge
       senza la ragione lo toglie, e il difetto torna.
       `[M]` 23 agosto 2026, rileggendo: il profilo `0-liscio` e' il **primo**
       della griglia, e per «guastare con nessuna regola» chiamava
       `rimetti(False)` — che disarmava il guardiano armato **due righe prima**
       in `principale()`.  ⇒ Gli **otto profili successivi** giravano senza
       rete di sicurezza: una morte del copione (o un ssh caduto) da li' in poi
       lasciava la macchina col `netem` addosso, e il prossimo banco avrebbe
       attribuito **al prodotto** un guasto mio.  E' scritto nell'intestazione
       di questo stesso file (§«IL DISINNESCO E' AUTOMATICO»), e il file non lo
       rispettava: silenzio invece di rosso, come i predicati di R13.
       ⇒ Chi toglie la disciplina **dentro** un giro passa `disarma=False`;
         solo chi chiude il giro (il `finally`, e il passo `rimetti` da riga di
         comando) disarma davvero.
    ⚠ La firma resta compatibile: `rimetti()` e `rimetti(dillo=False)` — le due
      forme che usano `09-b70`, `09-b76` e `09-b79` — si comportano come prima.
    """
    # ⛔ Prima si disarma il guardiano, POI si toglie la disciplina: al
    #    contrario resterebbe una finestra in cui il guardiano puo' scattare su
    #    un `netem` che nel frattempo ha messo qualcun altro.
    if disarma:
        guardiano_disarma()
    root("/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV)
    q = qdisc()
    ok = "netem" not in q
    if dillo:
        print("   %s la disciplina di «%s» adesso e': %s"
              % ("OK " if ok else "NO ", DEV, q or "(nessuna)"))
        # ⛔ E si dichiara che l'interfaccia vietata non e' MAI stata toccata.
        print("   --  %s (ssh + 7730): %s"
              % (VIETATA, root("/usr/sbin/tc qdisc show dev %s" % VIETATA)[1].split("\n")[0]))
    return ok


def guasta(regole):
    """Il guasto, e SOLO sul mio traffico."""
    if not regole:
        # ⛔ `disarma=False`: siamo DENTRO il giro, e il guardiano e' di tutto
        #    il giro (vedi il riquadro di `rimetti`).  Con `rimetti(False)` il
        #    gradino `0-liscio` scopriva gli otto gradini dopo di se'.
        rimetti(False, disarma=False)
        return True, "(nessun guasto)"
    passi = [
        "/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV,
        "/usr/sbin/tc qdisc add dev %s root handle 1: prio bands 4" % DEV,
        "/usr/sbin/tc qdisc add dev %s parent 1:4 handle 40: netem %s"
        % (DEV, " ".join(regole)),
        # ⛔ DUE filtri, e la porta e' la MIA: uno per i datagram che scendono
        #    (sport 7801) e uno per quel che risale (dport 7801).
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip sport %d 0xffff flowid 1:4" % (DEV, PORTA),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip dport %d 0xffff flowid 1:4" % (DEV, PORTA),
    ]
    # (il guardiano si arma UNA volta sola, in `principale`: vedi la nota li')
    for c in passi:
        rc, out, err = root(c)
        if rc != 0 and "del dev" not in c:
            rimetti()
            return False, "⛔ tc ha rifiutato «%s»: %s" % (c[-60:], err[:200])
    return True, qdisc()


def innesca_sessione(secondi=8):
    """⛔ Il sink «remotix» lo crea il FIGLIO, e il figlio nasce quando un
       cliente entra: su un server appena acceso `pw-play --target remotix` non
       si lega a niente.  ⇒ Si apre una sessione corta apposta; il palco e il
       sink le sopravvivono (I4)."""
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec pcm --resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 180)
    return "SESSIONE" in (out + err)


def tono_fabbrica(hz=440, secondi=70, ampiezza=0.5):
    """⛔ Il tono si fabbrica QUI se manca, e l'ampiezza e' NOTA: l'RMS atteso
       e' un conto (A/sqrt2), non una stima.  ⚠ E il file dev'essere leggibile
       dall'utente della sessione, che non e' root."""
    f = "%s/tono-%d.wav" % (LAV, hz)
    rc, out, _ = root("test -s %s && stat -c %%s %s || echo 0" % (f, f))
    if out.strip().isdigit() and int(out.strip()) > 48000 * secondi * 2:
        return f
    root("mkdir -p %s && chmod 755 %s" % (LAV, LAV))
    copione = (
        "import math,struct,wave;"
        "w=wave.open('%s','wb');w.setnchannels(2);w.setsampwidth(2);"
        "w.setframerate(48000);d=bytearray();"
        "[d.extend(struct.pack('<hh',v,v)) for v in "
        "[int(%f*math.sin(2*math.pi*%d*n/48000)*32767) for n in range(48000*%d)]];"
        "w.writeframes(bytes(d));w.close()" % (f, ampiezza, hz, secondi))
    root("python3 -c \"%s\" && chmod 644 %s" % (copione, f), 300)
    return f


def tono_accendi():
    tono_fabbrica()
    """⛔ Il tono deve suonare DENTRO la sessione, o il giudice misura silenzio
       e il banco riferisce «rms 0» come se fosse un guasto della rete.
       ⚠ E' successo al primo giro di «casa»: 5993 datagram perfetti e rms 0,0.
       ⭐ E «acceso» non e' «suona»: si controlla che il grafo abbia i legami."""
    # ⛔ IL TONO SI RIPETE IN UN CICLO, e la prima stesura no.
    #   Il file dura ~55 s; il giro dei profili ne dura trecento.  Dal secondo
    #   profilo in poi il giudice leggeva rms 0,0 e purezza nulla -- cioe'
    #   "silenzio" -- accanto a contatori di trasporto perfetti.  Il numero
    #   della RETE restava buono, ma la meta' che ASCOLTA era sparita senza
    #   dirlo, che e' precisamente la trappola 1 di questa fase.
    root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%d/bus "
         "sh -c 'while :; do pw-play --target remotix %s/tono-440.wav; done' "
         ">/dev/null 2>&1 & echo acceso"
         % (UID_B, UID_B, UTENTE, UTENTE, UID_B, UID_B, LAV))
    for _ in range(25):
        time.sleep(0.4)
        rc, out, _ = root("env UTENTE=%s UID_B=%d LAV=%s python3 %s/banchi/07-b64-scena.py grafo"
                          % (UTENTE, UID_B, LAV, ALB))
        try:
            if json.loads(out).get("legami_in_ingresso", 0) > 0:
                return True
        except Exception:
            pass
    return False


def tono_spegni():
    # ⛔ si uccide anche il CICLO, non solo il lettore: uccidere pw-play
    #   dentro un `while :` lo fa ripartire subito, ed e' la stessa forma del
    #   difetto di 07-b43 (`kill` sull'involucro invece che sul lettore).
    root("pkill -u %d -f 'while :; do pw-play'; pkill -u %d -x pw-play; true"
         % (UID_B, UID_B))


def cliente(nome, dove, secondi):
    """dove = 'portatile' (WiFi vero) oppure 'contenitore' (loopback + netem)."""
    j = os.path.join(FUORI, nome + ".jsonl")
    t = os.path.join(FUORI, nome + ".txt")
    for f in (j, t, os.path.join(FUORI, nome + ".segnale")):
        try: os.remove(f)
        except Exception: pass
    if dove == "portatile":
        pf = os.path.join(FUORI, ".parola")
        if not os.path.exists(pf):
            print("⛔ manca %s (0600, con la parola di %s): NON la metto in argv (D12)"
                  % (pf, UTENTE))
            return None
        cmd = [os.environ.get("PY", "python3"), "-u",
               os.path.join(QUI, "01-b3-cliente.py"),
               "--indirizzo", IND, "--porta", str(PORTA), "--utente", UTENTE,
               "--parola-file", pf, "--audio-codec", "pcm",
               "--audio-scrivi", j, "--segnale", os.path.join(FUORI, nome + ".segnale"),
               "--resta", str(secondi)]
        p = subprocess.run(cmd, capture_output=True, timeout=secondi + 120)
        uscita = p.stdout.decode("utf-8", "replace")
        open(t, "w").write(uscita + p.stderr.decode("utf-8", "replace"))
    else:
        dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
                  "--utente %s --parola-file %s/parola --audio-codec pcm "
                  "--audio-scrivi %s/rete-%s.jsonl --resta %d"
                  % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, DENTRO_LAV,
                     nome, secondi))
        rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                            secondi + 180)
        uscita = out + err
        open(t, "w").write(uscita)
        # si riporta il JSONL
        subprocess.run("ssh -o BatchMode=yes %s \"printf '%%s\\n' '%s' | sudo -S -p '' "
                       "cat %s/rete-%s.jsonl\" > %s"
                       % (MACCHINA, PAROLA_SUDO, LAV, nome, j), shell=True)
    conti = {}
    for r in uscita.splitlines():
        if "[audio] ricevuti" in r or "[audio] scartati" in r:
            conti[r.strip()[:9]] = r.strip()
    return {"uscita_coda": uscita[-1200:], "conti": conti,
            "jsonl": j, "byte_jsonl": os.path.getsize(j) if os.path.exists(j) else 0}


def conta_conti_finali():
    """Quante righe «audio di …, conto finale» ci sono ADESSO nel registro."""
    rc, out, _ = root("grep -ac 'audio di .*conto finale' %s/registro.log || true"
                      % LAV)
    try:
        return int(out.strip())
    except Exception:
        return -1


def registro_posato(tetto=90.0, quiete=3.0):
    """⛔⛔ SI ASPETTA CHE LA SESSIONE DI PRIMA ABBIA FINITO DI CHIUDERSI, e
       sono due guasti in uno quelli che questo evita — `[M]` 23 agosto 2026,
       trovati facendo girare il banco dopo le cure di stasera:

       1. **IL CONTO DEL SERVER ERA DI UN ALTRO GIRO.**  La chiusura di una
          sessione e' LENTA quando il pacer ha una coda (`[M]` il profilo
          `7-perdita-10` ci ha messo **29 s** in piu' degli altri a scrivere il
          suo «conto finale»).  ⇒ `riga0` del giro dopo veniva presa PRIMA che
          la riga del giro prima fosse scritta, e `conti_del_server` — che
          prende l'ULTIMA riga dopo `riga0` — leggeva quella **del giro
          precedente**.  `[M]` i profili 6, 7 e 8 hanno riferito tutt'e tre
          «spediti 4999 · rifiutati 3 · rimandati 7410», che era il conto del
          **6**; il conto vero del 7 era 4632.  ⚠ E il predicato ci ha dato
          rosso su un denominatore altrui: 4152/4999 = 0,831 (rosso) contro
          4152/4632 = **0,896** (verde, ed e' `1-p`).  ⛔ E' la stessa forma
          dei difetti curati stasera — un numero plausibile e falso al posto di
          un «non ho letto».
       2. **IL POSTO ERA ANCORA OCCUPATO.**  Finche' la sessione di prima non
          si e' chiusa, §4.4-bis rifiuta la nuova con
          `CONGEDO 0x0F GIA_ATTIVA_REMOTA` (`banchi/09-b78-apertura.py` §4:
          la serratura dura fino a `SILENZIO` = 30 s).  `[M]` il profilo
          `8-casa-cattiva` e' morto cosi', e l'`[audio] ricevuti 0` che ne
          usciva e' esattamente il numero che il vecchio `a_non_si_apre`
          avrebbe chiamato **verde**.

    ⇒ Si aspetta che il conto delle righe «conto finale» stia FERMO per
      `quiete` secondi, e si torna quel conto: e' il `n0` da cui il giro nuovo
      pretende una riga **sua**.
    """
    n = conta_conti_finali()
    fermo, scade = 0.0, time.time() + tetto
    while time.time() < scade and fermo < quiete:
        time.sleep(1.0)
        m = conta_conti_finali()
        fermo = (fermo + 1.0) if m == n else 0.0
        n = m
    return n


def conti_del_server(riga0, n0=None, tetto=90.0):
    """⛔⛔ R13 — SENZA QUESTO IL BANCO ERA CIECO PER COSTRUZIONE.

       Il cliente sa dire quanti datagram ha ricevuto; **non** sa dire quanti
       ne sono partiti.  ⇒ «la rete l ha perso» e «il server non l ha mai
       spedito» davano lo stesso numero, e in un banco che guasta la RETE
       apposta e' la distinzione che serve piu' di ogni altra:
       senza, un difetto del server verrebbe attribuito al `netem`.

       ⭐ Il conto ce l ha gia' il prodotto, alla chiusura della sessione:
       «N blocchi spediti, N buttati, N rifiutati da ngtcp2, N rimandati».
       Qui si legge, e si legge SOLO da `riga0` in poi, cosi' e' di questo
       giro e non di quello prima.

       ⛔⛔ E «DOPO `riga0`» NON BASTA: vedi il riquadro di `registro_posato`.
          Se la sessione del giro PRIMA scrive il suo «conto finale» dopo che
          `riga0` e' stata presa, quella riga cade dentro la finestra e viene
          letta come se fosse mia.  ⇒ `n0` = quante righe di «conto finale»
          c'erano quando questo giro e' cominciato, e qui si **aspetta** che ne
          compaia una in piu'.  Se non compare, «NIENTE DA LEGGERE» — che ora
          e' MUTO, non verde."""
    if n0 is not None:
        scade = time.time() + tetto
        while conta_conti_finali() <= n0:
            if time.time() >= scade:
                return {"esito": "NIENTE DA LEGGERE — in %d s questo giro non ha "
                                 "scritto nessun «conto finale» suo (sessione "
                                 "rifiutata? ancora in chiusura?)" % int(tetto)}
            time.sleep(1.0)
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'audio di .*conto finale' "
                      "| tail -1" % (riga0 + 1, LAV))
    r = out.strip()
    if not r:
        # ⛔ `CODER.md` §3.10: «non ho letto» non e' «zero».
        return {"esito": "NIENTE DA LEGGERE — nessun «conto finale» in questo giro"}
    import re as _re
    m = _re.search(r"(\d+) blocchi spediti, (\d+) buttati.*?(\d+) rifiutati.*?"
                   r"(\d+) RIMANDATI", r)
    if not m:
        return {"esito": "riga trovata ma illeggibile", "riga": r[:160]}
    fuori = {"spediti": int(m.group(1)), "buttati": int(m.group(2)),
             "rifiutati": int(m.group(3)), "rimandati": int(m.group(4))}
    # ⭐ E gia' che il registro e' aperto, si legge anche il conto del VIDEO:
    #    e' la riga che il prodotto ha imparato a scrivere il 22 agosto, e
    #    porta i due numeri che prima si confondevano.
    rc, out2, _ = root("tail -n +%d %s/registro.log | grep -a 'video di .*conto finale' "
                       "| tail -1" % (riga0 + 1, LAV))
    m2 = _re.search(r"(\d+) fotogrammi consegnati.*?(\d+) NON SPEDITI.*?"
                    r"(\d+) spediti sul filo.*?(\d+) abbandonati.*?e (\d+) ANNUNCI",
                    out2.strip())
    if m2:
        fuori["video"] = {"consegnati": int(m2.group(1)),
                          "non_spediti": int(m2.group(2)),
                          "spediti": int(m2.group(3)),
                          "abbandonati": int(m2.group(4)),
                          "annunci_tela": int(m2.group(5))}
    return fuori


def righe_registro():
    rc, out, _ = root("wc -l < %s/registro.log" % LAV)
    try:
        return int(out.strip())
    except Exception:
        return 0


def giudica(nome):
    j = os.path.join(FUORI, nome + ".jsonl")
    if not os.path.exists(j) or os.path.getsize(j) == 0:
        return {"esito": "NIENTE DA GIUDICARE — nessun blocco"}
    p = subprocess.run(["python3", os.path.join(QUI, "07-b64-orecchio.py"), j,
                        "--hz", "440"], capture_output=True)
    try:
        d = json.loads(p.stdout.decode())["nostro"]
    except Exception as e:
        return {"esito": "il giudice non ha risposto: %s" % e}
    s = d["scoppiettii"]
    return {"blocchi": d["blocchi"], "resa_campioni": d.get("resa_campioni"),
            "buchi_istante": d["buchi_istante"], "scoppiettii": s["scoppiettii"],
            "scoppiettii_al_s": s["al_secondo"], "tono": d["tono"]}


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", choices=["casa", "netem", "rimetti", "stato"])
    p.add_argument("--secondi", type=int, default=25)
    p.add_argument("--solo", default="", help="un profilo solo, per nome")
    p.add_argument("--controllo-rosso", action="store_true",
                   help="⭐ il controllo positivo DEL VERDETTO: al gradino "
                        "«0-liscio» (rete perfetta) si appiccica l'atteso del "
                        "jitter, che su una linea pulita NON puo' passare.  "
                        "⛔ Se il banco resta verde, il banco e' cieco e non si "
                        "crede a nessun altro suo verde")
    a = p.parse_args()
    os.makedirs(FUORI, exist_ok=True)

    if a.passo in ("rimetti", "stato"):
        print("== la rete della macchina di prova")
        return 0 if rimetti() else 2

    if a.passo == "casa":
        print("== 1 · LA RETE DI CASA VERA — il cliente gira sul portatile, in WiFi")
        print("   --  portatile 192.168.0.3 (wlo1) → server %s:%d (cavo)" % (IND, PORTA))
        print("   ⛔ nessuna regola di tc: non si simula niente")
        if not tono_accendi():
            print("   NO  il tono NON sta suonando dentro la sessione: mi fermo,"
                  " invece di misurare silenzio e chiamarlo rete")
            tono_spegni(); return 2
        print("   OK  il tono suona: il grafo ha i legami in ingresso al sink")
        try:
            c = cliente("casa", "portatile", a.secondi)
        finally:
            tono_spegni()
        if c is None:
            return 2
        for r in c["conti"].values():
            print("   ", r)
        print("   ", json.dumps(giudica("casa"), ensure_ascii=False))
        return 0

    print("== 2 · LA RETE GUASTATA APPOSTA — netem su «%s», solo porta %d" % (DEV, PORTA))
    print("   ⛔ «%s» (ssh + 7730 dell utente) NON si tocca" % VIETATA)
    prima = qdisc()
    print("   --  «%s» prima: %s" % (DEV, prima or "(nessuna)"))
    # ⛔⛔ IL GUARDIANO SI ARMA UNA VOLTA SOLA, E PER TUTTO IL GIRO.
    #
    #     La prima stesura ne armava uno **per profilo**, ciascuno con la sua
    #     attesa: il guardiano del primo profilo sarebbe scattato **in mezzo al
    #     terzo**, togliendo il netem senza dirlo.  ⇒ Avrei misurato una rete
    #     sana credendola guasta, e scritto «il 10 % di perdita non si sente».
    #     ⚠ E' la forma peggiore di difetto di banco: fa apparire buono il
    #     prodotto.  Trovato rileggendo, prima di girare.
    totale = (a.secondi + 120) * len(PROFILI) + 300
    guardiano_arma(totale)
    esiti = []
    if a.controllo_rosso:
        # ⛔ Si sostituisce l'atteso del primo gradino con uno che su rete
        #    pulita e' impossibile: «almeno 100 datagram scartati perche'
        #    sorpassati» dove non c'e' nessun guasto.
        for i, (nome, regole, testo, _pred) in enumerate(PROFILI):
            if nome.startswith("0-"):
                PROFILI[i] = (nome, regole,
                              "⛔ CONTROLLO ROSSO: atteso impossibile apposta "
                              "(100 sorpassi su una rete senza guasti)",
                              a_sorpassi(100))
        print("   ⛔ CONTROLLO ROSSO acceso: il gradino «0-liscio» DEVE fallire")
    print("   --  apro una sessione corta per far nascere il palco e il sink")
    if not innesca_sessione():
        print("   NO  la sessione non si apre: non misuro")
        rimetti(); return 2
    if not tono_accendi():
        print("   NO  il tono non suona: non misuro")
        tono_spegni(); rimetti(); return 2
    print("   OK  il tono suona dentro la sessione")
    try:
        for nome, regole, atteso, predicato in PROFILI:
            if a.solo and a.solo not in nome:
                continue
            print("\n-- %s · %s" % (nome, atteso))
            # ⛔ PRIMA DI TUTTO: la sessione del giro prima dev'essere chiusa
            #    davvero, o si legge il suo conto e si prende il suo posto in
            #    faccia (`CONGEDO 0x0F`).  Vedi il riquadro di `registro_posato`.
            n0 = registro_posato()
            riga0 = righe_registro()
            ok, q = guasta(regole)
            if not ok:
                # ⛔ R13: il `break` usciva e il copione tornava 0 lo stesso.
                print("   ", q)
                esiti.append({"profilo": nome, "passa": False,
                              "perche": "tc ha rifiutato la regola"})
                break
            # ⛔ M3 si riverifica a OGNI profilo.  "Il tono suonava
            #   all'inizio" non e' "il tono sta suonando adesso".
            rc, out, _ = root("env UTENTE=%s UID_B=%d LAV=%s python3 %s/banchi/"
                              "07-b64-scena.py grafo" % (UTENTE, UID_B, LAV, ALB))
            try:
                leg = json.loads(out).get("legami_in_ingresso", 0)
            except Exception:
                leg = -1
            print("    M3: legami in ingresso al sink = %s" % leg)
            if leg <= 0:
                print("   NO  il tono non suona piu': NON giudico questo profilo")
                esiti.append({"profilo": nome, "passa": None,
                              "esito": "NIENTE DA GIUDICARE, il tono taceva"})
                continue
            print("    tc:", " ".join(q.split("\n")[:2])[:160])
            c = cliente(nome, "contenitore", a.secondi)
            # ⛔ La perdita VERA si legge ADESSO: il gradino dopo azzera i
            #    contatori del `netem` con il suo `tc qdisc del`.
            pv = perdita_vera()
            g = giudica(nome)
            sv = conti_del_server(riga0, n0)
            for r in (c or {}).get("conti", {}).values():
                print("   ", r)
            print("    SERVER:", json.dumps(sv, ensure_ascii=False))
            print("    giudizio:", json.dumps(g, ensure_ascii=False))

            # ⭐ E QUI L'ATTESO SMETTE DI ESSERE PROSA: si confronta.
            #    ⚠ I numeri che il predicato guarda vengono da DUE lati — il
            #    cliente e il server — cosi' «perso sul filo» e «mai spedito»
            #    non si confondono.
            conti = (c or {}).get("conti", {})
            import re as _re

            def daconti(chiave, testo):
                for x in conti.values():
                    if chiave in x:
                        m = _re.search(testo, x)
                        return int(m.group(1)) if m else None
                return None

            numeri = {
                "ricevuti": daconti("ricevuti", r"ricevuti (\d+)"),
                "vecchi": daconti("scartati", r"vecchi (\d+)"),
                "resa": g.get("resa_campioni"),
                "purezza": (g.get("tono") or {}).get("purezza"),
                "spediti_dal_server": sv.get("spediti"),
                # ⚠ La perdita LETTA da `tc -s qdisc`, non quella chiesta:
                #   `a_resa_sul_filo` si tara su questa (vedi il suo riquadro).
                "perdita_vera": pv,
            }
            print("    netem: perdita davvero applicata = %s"
                  % ("%.2f %%" % (pv * 100) if pv is not None
                     else "(nessuna disciplina, o non letta)"))
            # ⛔⛔ E SE IL CONTO DEL SERVER NON SI E' LETTO, IL GRADINO E' MUTO.
            #     `[M]` 23 agosto 2026 — terzo caso della stessa forma dei due
            #     curati stasera: `sv.get("spediti")` torna `None` quando il
            #     «conto finale» non e' nel registro, `None == 0` e' **falso**,
            #     e il gradino filava dritto al predicato.  ⇒ I predicati che
            #     non guardano il server (`a_pulito`, `a_sorpassi`) davano
            #     **verde** su un giro in cui il capo del server non era stato
            #     letto affatto.  `CODER.md` §3.10: «non ho letto» non e'
            #     «zero», e qui non e' nemmeno «verde».
            if numeri["spediti_dal_server"] is None:
                passa, perche = None, ("NIENTE DA GIUDICARE: il conto del SERVER "
                                       "non si e' letto (%s)"
                                       % sv.get("esito", "?"))
            elif numeri["spediti_dal_server"] == 0:
                # ⛔ E se il server non ha spedito, il rosso NON e' della rete.
                passa, perche = False, ("il SERVER non ha spedito niente: il rosso "
                                        "non e' della rete guastata, e' nostro")
            else:
                passa, perche = predicato(numeri)
            print("    %s ATTESO: %s"
                  % ("OK " if passa else ("⚠ MUTO" if passa is None else "⛔ NO"),
                     perche))
            esiti.append({"profilo": nome, "regole": regole, "atteso": atteso,
                          "conti": conti, "server": sv, "giudizio": g,
                          "numeri": numeri, "passa": passa, "perche": perche,
                          "esito": perche if passa is None else None})
    finally:
        tono_spegni()
        print("\n== ⛔ LA RETE SI RIMETTE COM'ERA")
        guardiano_disarma()
        rimetti()
    json.dump(esiti, open(os.path.join(FUORI, "rete-esiti.json"), "w"),
              ensure_ascii=False, indent=1)

    # ⛔⛔ R13 — E L'ESITO SI PROPAGA.  Prima `principale()` tornava 0 in ogni
    #      caso, `break` compreso: un banco che non puo' dare rosso non e' un
    #      banco, e' un rapporto.
    rossi = [e for e in esiti if e.get("passa") is False]
    muti = [e for e in esiti if e.get("passa") is None]
    print("\n== IL VERDETTO — %d gradini, %d rossi, %d non giudicati"
          % (len(esiti), len(rossi), len(muti)))
    for e in rossi:
        print("   ⛔ %s: %s" % (e["profilo"], e.get("perche")))
    for e in muti:
        print("   ⚠  %s: %s" % (e["profilo"], e.get("esito")))
    if rossi:
        return 1
    if muti:
        return 2      # ⚠ «non ho misurato» e' un esito SUO, non un verde
    print("   ⭐ tutti i gradini hanno fatto quel che era scritto prima")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
