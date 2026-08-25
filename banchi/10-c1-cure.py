#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
10-c1-cure — ⛔⛔ IL ROSSO PRIMA E IL VERDE DOPO, sulle due cure del terzo giro.

Non misura un difetto: misura **una cura**.  ⇒ Ogni prova gira DUE volte, sullo
stesso ferro, con la stessa scena e gli stessi predicati, e cambia **una cosa
sola**: il binario.

    `remotix-base-inn`   il prodotto di ieri (HEAD), col guardiano finto
    `remotix-cura-inn`   lo stesso, piu' le due cure di questo incarico

⭐ E il controllo negativo rimette il primo e pretende che il banco torni ROSSO.
   Un banco che non sa piu' dare rosso non sta misurando la cura, sta
   raccontandola.

---------------------------------------------------------------------------
⛔⛔ LE DUE PROVE, E OGNUNA ISOLA UNA CURA SOLA

  A · **LA GUARDIA SUL BUCO DEL CICLO** (la famiglia P2/P5 di §8.2, «il nostro
      silenzio contato come silenzio della rete»).  ⛔ `N = 1` apposta: con **un
      solo** inquilino la cura di P4 non cambia niente — una domanda o N domande
      sono la stessa domanda — quindi tutto quel che si vede lo fa l'altra cura.

      ⛔⛔⛔ E QUI IL BANCO DICE SUBITO UNA COSA CHE NON GLI FA COMODO: **lo
      sfratto di P2/P5 NON si e' riprodotto**, ne' su un ciclo sano ne' su un
      ciclo bloccato.  `[M]` 25 agosto 2026, questo incarico, una sessione sola:
      trenta secondi di buco fra due scene su un ciclo sano ⇒ **nessuno
      sfratto**, con i PING del trasporto puntuali ogni 5 s (`spediti_d=1`) e la
      risposta del client entro un secondo (`ricevuti_d=1`).
      ⇒ ⭐ Il margine «due volte» di §6.8 **regge**, e P5 nella forma in cui e'
        scritto — *«basta un buco di dieci secondi»* — **non basta**.
      ⇒ ⛔ Percio' questo banco NON pretende un rosso che non c'e', e non
        chiama «cura» quel che non ha visto guarire.  Misura **una guardia**, e
        una guardia si prova su tre cose, non su una:

        A1 · **si arma quando deve** — col ciclo fermo (guardiano finto a
             D = 12 000 ms) devono uscire le righe «il ciclo del padre e'
             rimasto indietro di … ms», e il buco dev'essere piu' lungo della
             soglia del silenzio;
        A2 · **NON si arma quando non deve** — su una macchina sana
             `giri_fermi` dev'essere **zero**.  ⛔ Senza questo, la guardia
             potrebbe star spegnendo la linea morta di nascosto, e nessuno se
             ne accorgerebbe;
        A3 · ⛔⛔ **e la linea morta funziona ancora** — `kill -9` sul client, e
             lo sfratto deve arrivare lo stesso, con `causa=silenzio`.  E' il
             controllo che conta di piu': una guardia che, per non sfrattare
             nessuno per sbaglio, non sfratta piu' nessuno **ha rotto la cura
             che voleva proteggere**.

  B · **IL GUARDIANO DI LOGIND** (P4).  `N = 7`, `D = 286 ms` — ⛔ la cella che
      §6.13 misura come la peggiore *dentro il bilancio che il codice stesso si
      concede* (`ATTESA_MS` = 300 ms): la' ogni desktop crollava a **1,3
      fotogrammi/s con un p95 di due secondi, e non si scriveva una riga**.

        ⇒ Il verde ha DUE colonne, non una: **nessuno staccato** *e* **il ritmo
          non cala**.  Un verde sulla sola prima colonna sarebbe il difetto
          stesso, che di sfratti non ne faceva.
        ⇒ E la colonna che lo dimostra alla radice: **le chiamate per ripasso**,
          che devono passare da `N` a `1`.

---------------------------------------------------------------------------
⛔ CHE COSA QUESTO BANCO **NON** SA DIRE — detto prima, non dopo

 1. ⚠ NON GARANTISCE di riprodurre l'anello di §6.15: la prova C ci prova —
    cinque sessioni sature, i due binari NUDI — ⛔ ma §6.15 stessa l'ha trovato
    «per strada», e un fenomeno che «a volte succede» non si comanda
    (`LEZIONI.md` §1.32).  ⇒ Se non si presenta, il banco lo DICE e **non
    giudica**: «non si e' presentato» non e' «e' curato».  ⭐ E in quel caso
    quel che resta e' comunque nuovo: la riga dello sfratto adesso porta
    `ritmo_giu=` e `fermo_ms=`, cioe' l'ATTRIBUZIONE che §6.15 ha dovuto
    dedurre appaiando due righe a occhio.
 2. ⛔ NON dice quanto e' lento logind su una macchina malata: il guardiano
    finto e' una leva, e quel che rappresenta e' **un giro su D-Bus che costa
    D**, non «una sessione».
 3. ⚠ NON parla dell'immagine: nessun banco dice «si vede peggio».
 4. ⛔⛔ E UNA GAMBA DEL TERRENO QUI NON REGGE, e va detta invece che nascosta:
    `10-b0-terreno.sh` T5.3 verifica che il binario sia PIU' NUOVO dei sorgenti
    che dichiara — ⚠ ma questo banco **scambia il binario** fra un braccio e
    l'altro (`10-c1-terreno.sh metti`), e il binario del rosso e' per forza piu'
    vecchio dei sorgenti curati.  ⇒ Il terreno si guarda **una volta sola**,
    all'inizio, sull'albero come e' stato costruito; da li' in poi l'identita'
    del binario la porta il suo **md5**, stampato a ogni scambio e conservato
    negli esiti.  ⭐ E' una gamba diversa, non una gamba in meno: l'md5 dice
    *quale* binario sta girando, che e' la domanda vera.

---------------------------------------------------------------------------
Uso (dal portatile):

    python3 banchi/10-c1-cure.py --certifica    # ⛔ i guasti innestati
    python3 banchi/10-c1-cure.py a              # la cura del buco del ciclo
    python3 banchi/10-c1-cure.py b              # la cura del guardiano
    python3 banchi/10-c1-cure.py c              # l'anello di §6.15, cinque sature
    python3 banchi/10-c1-cure.py tutto
    python3 banchi/10-c1-cure.py stato|sgombra

Codici d'uscita — ⛔ i primi due sono GIUDIZI, gli altri no:
    0  ⭐ tutti i predicati hanno fatto quel che era scritto prima
    1  ⛔ almeno un rosso
    3  ⚠ «NON HO NIENTE DA GIUDICARE» — ho misurato e qualcosa non ha parlato
    2  ⛔ uso sbagliato, o terreno che non regge
    4  ⛔ il turno non e' mai arrivato (lucchetto della GPU)
===========================================================================
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ISOLAMENTO, SCRITTO PRIMA DI QUALUNQUE IMPORT CHE LO LEGGA
# ═══════════════════════════════════════════════════════════════════════════
IO_SONO = os.environ.setdefault("IO_SONO", "10-c1")
PORTA = int(os.environ.setdefault("PORTA", "8210"))
LAV = os.environ.setdefault("LAV", "/media/REMOTIX/tmp/10c1")
ALB = os.environ.setdefault("ALBERO", "/media/REMOTIX/src/10c1-src")
os.environ.setdefault("DENTRO_ALB", "/srv/src/10c1-src")
os.environ.setdefault("DENTRO_LAV", "/srv/remotix/tmp/10c1")
UNITA = os.environ.setdefault("UNITA", "remotix-%d" % PORTA)
os.environ.setdefault("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")
# ⛔ `/dev/shm` e' UNO su tutta la macchina: il nome della scena dev'essere mio,
#    o `shm_open` risponde «Permission denied» sul segmento di un altro agente e
#    la scena non parte — cioe' il palco non produce, cioe' il meccanismo non
#    puo' scattare e il banco darebbe un verde PER COSTRUZIONE.
os.environ.setdefault("SHM_BASE", "10c1")
os.environ.setdefault("QUANTI", "7")
os.environ.setdefault("STAGING", "/tmp/10-c1-repo")
MACCHINA = os.environ.setdefault("MACCHINA", "nicfio@192.168.0.2")
FUORI = os.environ.get("FUORI", "/tmp/10-c1")

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LE SOGLIE, IN UN POSTO SOLO, CIASCUNA CON LA SUA RAGIONE
# ═══════════════════════════════════════════════════════════════════════════

# ⭐ PROVA A — il buco dev'essere PIU' LUNGO della soglia del silenzio (10 s), o
#    non si sta provando niente: a 9 s la linea morta non scatterebbe nemmeno
#    sul prodotto vecchio, e il verde sarebbe un verde per costruzione.
A_ENNE = 1
A_D_MS = 12000
A_DURATA_S = 70.0          # ⚠ almeno quattro ripassi: uno solo sarebbe un caso
A_SANA_S = 20.0            # ⭐ la finestra in cui si dimostra che consegnava
A_SANA_MINIMO = 5.0        # ⛔ sotto, «sana» non e' dimostrato e non si giudica
# ⛔ La soglia del silenzio del prodotto (`WT_LM_SILENZIO_S` × 1000).  ⚠ E' una
#    SECONDA copia di un numero che vive in `webtransport.h`: si scrive qui per
#    poterla confrontare, e se un giorno quel numero cambia questa riga mente.
#    ⇒ Il banco la stampa sempre accanto al buco, cosi' chi legge se ne accorge.
A_SOGLIA_SILENZIO_MS = 10000
A_SANA_MACCHINA_S = 90.0   # ⭐ A2: abbastanza da vedere ~45 ripassi
A_MORTO_ATTESA_S = 40.0    # ⭐ A3: la soglia e' 10 s, piu' il margine del giro

# ⭐ PROVA B — la cella di §6.13 che conta, e i due numeri sono i suoi.
B_ENNE = 7
B_D_MS = 286               # `[M]` esattamente il bilancio di `ATTESA_MS`
B_DURATA_S = 45.0
# ⛔ Il ritmo «non cala» rispetto a che cosa?  Rispetto alla stessa cella con
#    D=0 sullo STESSO binario: e' l'unico paragone che non porta dentro anche la
#    differenza fra i due binari.
#
# ⛔⛔ E IL 20 % NON E' UNA TOLLERANZA GENEROSA: E' IL PEDAGGIO CHE LA CURA NON
#     TOGLIE, ed e' meglio dirlo qui che scoprirlo leggendo il numero.
#     La cura toglie il fattore **N**, non il termine **D**: a N=7 con D=286 ms
#     il ciclo paga **286 ms ogni 2 000**, cioe' il **14,3 %** del tempo, e
#     quel pedaggio resta.  ⛔ Il difetto era che ne pagava **sette volte
#     tanto** — 2 002 ms su 2 000, cioe' il ciclo fermo **sempre**.
#     ⇒ Un calo entro il 20 % e' compatibile col solo pedaggio; sopra, la cura
#       non ha tolto quel che dice di togliere.  ⚠ E chi vuole togliere anche il
#       pedaggio deve spostare la domanda fuori dal ciclo (un aiutante, come
#       PAM), che e' un'altra decisione e non e' questa.
B_CALO_TOLLERATO = 0.20
# ⛔ E il rosso dev'essere GROSSO, o il banco non sta guardando il difetto che
#    §6.13 descrive: la' il ritmo passava da ~39 a 1,3 fot/s, cioe' −97 %.
B_CALO_ROSSO = 0.50
# ⭐ Quanto si aspetta un inquilino NUOVO prima di dire «non e' entrato».  ⛔ 60 s
#    e non 240: il palco c'e' gia', qui si misura la STRETTA DI MANO, e il tetto
#    di §4.6 per le credenziali e' 60 s.  ⚠ Un tetto lungo trasformerebbe un
#    rosso in quattro minuti di attesa per braccio.
B_PORTA_TETTO_S = 60.0
# ⛔ Quanto si aspetta che il posto si liberi prima di ribussare: lo sfratto del
#    fantasma e' a **15 000 ms** (`rcp.c`, `--sfratto-ms`), e sotto quello si
#    misurerebbe `0x0f GIA_ATTIVA_REMOTA` invece della stretta di mano.
B_SFRATTO_ATTESA_S = 22.0

# ⭐ Il binario che `costruisci.sh` ha prodotto DA QUESTI sorgenti: e' quello che
#    il terreno deve trovare in `$ALBERO/src/remotix` quando guarda T5.3.
BINARIO_ALBERO = os.environ.get("BINARIO_ALBERO", "remotix-cura")

# ⭐ PROVA C — L'ANELLO DI §6.15, ripreso alla lettera: cinque sessioni, scena
#    satura, e i binari NUDI (nessun guardiano finto: qui la leva e' la GPU).
#    ⛔ `[M]` §6.15: a cinque sessioni, **cinque client sfrattati in 1,3 s**, con
#       `arretrato` incollato ai posti del regolatore e `usciti_byte=0`.
#    ⚠ Che si riproduca NON e' garantito — dipende dal carico, e §6.15 stessa lo
#      ha trovato «per strada» mentre cercava altro.  ⇒ Se non si riproduce, il
#      banco lo DICE e non giudica: «non si e' presentato» non e' «e' curato».
C_ENNE = 5
C_DURATA_S = 150.0


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ GLI ATTREZZI SI IMPORTANO, NON SI RISCRIVONO
# ═══════════════════════════════════════════════════════════════════════════
b97 = None
b92 = None
luc = None


def _carica(nome, file_):
    perc = os.path.join(QUI, file_)
    if not os.path.exists(perc):
        raise SystemExit("⛔ NON MISURO: manca «%s»" % perc)
    s = importlib.util.spec_from_file_location(nome, perc)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def apri_attrezzi():
    """⭐ `10-b97-guardiano.py` porta il guardiano finto, la cella, il lettore
       del registro e la fetta per sessione; `10-b92-dieci.py` porta il cliente
       e le scene.  ⛔ Non se ne riscrive una riga: sono certificati (35/35 e
       75/75), e una copia che diverge e' un attrezzo che mente (`LEZIONI.md`
       §1.35)."""
    global b97, b92, luc
    b97 = _carica("b97", "10-b97-guardiano.py")
    b92, luc = b97.apri_attrezzi()
    # ⛔ Il file del ritardo e' il MIO: l'innesto di `10-c1-innesta.py` ci ha
    #    compilato dentro questo percorso, e due nomi diversi vorrebbero dire un
    #    banco che scrive dove nessuno legge — cioe' D=−1 per tutto il giro, e
    #    un verde per costruzione.
    # ⛔⛔ IL NOME DEL FILE E' QUELLO CHE L'INNESTO HA COMPILATO DENTRO, e non
    #     quello di `10-b97`.  `[M]` 25 agosto 2026, primo giro vero: il banco
    #     scriveva in `b97-ritardo` e il binario leggeva `c1-ritardo` ⇒ **zero
    #     righe `CAMBIO`, zero chiamate col mio giro, due celle buttate**.
    #     ⭐ Il banco NON ha detto «tutto bene»: ha detto «LA LEVA NON HA PRESO».
    #        E' la guardia di `ritardo_poni()` che ha fatto il suo mestiere.
    b97.FILE_RITARDO = "%s/c1-ritardo" % LAV
    b97.REGISTRO = "%s/registro.log" % LAV
    b92.SHM_BASE = os.environ["SHM_BASE"]
    # ⛔ E la scena prende il MIO nome di `/dev/shm`: `10-b97-guardiano.py` ci
    #    scrive dentro `/10b97-N`, che e' di un altro incarico.  `/dev/shm` e'
    #    UNO su tutta la macchina, e `shm_open` sul segmento di un altro
    #    risponde «Permission denied»: la scena non parte, il palco non produce,
    #    e il banco darebbe un verde PER COSTRUZIONE.
    b97.accendi_scena = accendi_scena
    # ⛔ IL METRO DEI FOTOGRAMMI SI TARA PRIMA (`LEZIONI.md` §1.33), e senza di
    #    lui `b92.fetta()` non sa leggere niente: `[M]` primo giro vero, sette
    #    sessioni su sette hanno risposto *«la fetta non si e' letta:
    #    'NoneType' object has no attribute 'misura'»* — cioe' il ritmo, che e'
    #    meta' del verdetto di P4, non c'era.
    b92.B70 = b92._importa_b70()
    sano, guai = b92.tara_riduzione(b92.B70, dillo=True)
    if not sano:
        for g in guai:
            _ko(g)
        raise SystemExit("⛔ NON MISURO: il metro dei fotogrammi non e' tarato")
    return b97


def accendi_scena(i, movimento="pieno"):
    """La scena di `b92`, col MIO nome di `/dev/shm` e il MIO giro.  ⛔ Tre
       tentativi, e il registro della scena si conserva: una scena che non parte
       deve poter dire perche' (e' la forma di `10-b97-guardiano.py`, cambiati
       solo i due nomi che devono essere miei)."""
    n = b92.uid(i)
    log = "%s/scena-%d.log" % (LAV, i)
    # ⛔⛔ Prima si spegne quella che c'e': questa funzione viene richiamata anche
    #     per una sessione RIAPERTA, e senza questa riga il secondo giro
    #     lascerebbe DUE scene addosso allo stesso utente — un carico doppio che
    #     non da' rosso, da' celle misurate su una macchina piu' carica di quella
    #     dichiarata.
    b92.root("pkill -u %d -f '04-b30-scena --uscita' ; true" % n)
    time.sleep(0.6)
    for tentativo in range(3):
        usc = b92.uscita_del(i)
        if not usc:
            time.sleep(3.0)
            continue
        b92.root(
            "setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
            "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
            "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
            "%s --uscita %s --movimento %s --shm /%s --giro c1-%d "
            ">> %s 2>&1 & echo acceso"
            % (n, n, b92.utente(i), b92.utente(i), n, b92.SCENA_BIN, usc,
               movimento, b92.shm_di(i), i, log))
        time.sleep(2.5)
        rc, out, _ = b92.root("pgrep -u %d -f '04-b30-scena --uscita' | head -1" % n)
        if out.strip():
            return usc
        rc, out, _ = b92.root("tail -3 %s 2>/dev/null || true" % log)
        _dub("⚠ la scena di s%d non e' partita al tentativo %d — dice: %s"
             % (i, tentativo + 1, out.strip()[-160:]))
        time.sleep(3.0)
    return None


def sgombra(quanti=7, dillo=True):
    """⛔ Si lascia la macchina come la si e' trovata — e SOLO la propria roba.

    ⚠ `10-b97-guardiano.sgombra()` chiude con un modello che porta dentro la
      cartella di lavoro di QUELL'incarico, e con `pkill -f
      '10-b92-cliente[.]py --cliente'` — che e' GLOBALE.  `[M]` §7.3, quinta
      trappola: un modello globale ha combaciato con **24 clienti vivi di un
      altro banco che stava misurando**.  ⇒ Qui il modello porta la MIA cartella
      e nient'altro."""
    b92.root("printf 'sgombro -1\\n' > %s" % b97.FILE_RITARDO)
    for i in range(1, quanti + 1):
        b92.root("pkill -u %d -f '04-b30-scena' ; true" % b92.uid(i))
    b92.root("pkill -f -- '--giornale [/]srv/remotix/tmp/10c1/' ; true")
    time.sleep(2)
    b92.chiudi_palchi(quanti, dillo=dillo)


def terreno_sh(passo, **amb):
    e = dict(os.environ)
    e.update({k: str(v) for k, v in amb.items()})
    p = subprocess.run(["bash", os.path.join(QUI, "10-c1-terreno.sh"), passo],
                       env=e, capture_output=True)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def metti_binario(nome):
    """⛔ Il braccio si cambia sostituendo IL BINARIO, non ricompilando: due
       compilazioni possono differire per piu' di quel che si crede, e il banco
       deve poter dire «ho cambiato una cosa sola»."""
    rc, out = terreno_sh("metti", BINARIO=nome)
    if rc != 0:
        _ko("⛔ non ho potuto mettere «%s»: %s" % (nome, out[-300:]))
        return None
    md5 = ""
    for r in out.splitlines():
        if len(r.split()) == 2 and len(r.split()[0]) == 32:
            md5 = r.split()[0]
    rc, out = terreno_sh("accendi")
    if rc != 0:
        _ko("⛔ il server con «%s» non si e' acceso: %s" % (nome, out[-400:]))
        return None
    _ok("binario «%s» acceso (md5 %s)" % (nome, md5 or "?"))
    return md5 or "?"


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I GIUDIZI — funzioni PURE, cosi' il `--certifica` puo' innestare i guasti
#      senza toccare la macchina.  `(esito, perche)`:
#         True  l'atteso ha retto · False ⛔ rosso · None ⚠ NON GIUDICO
# ═══════════════════════════════════════════════════════════════════════════
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def leva_ha_preso(cella):
    """⛔ PRIMA DI OGNI GIUDIZIO: quanta sollecitazione e' ARRIVATA?
       (`LEZIONI.md` §1.30 — una prova che non morde da' un giudizio che sembra
       un risultato.)"""
    if not cella.get("leva"):
        return _muto("⛔ la leva NON ha preso: %s" % cella.get("leva_perche", "?"))
    n = cella.get("chiamate")
    if n is None:
        return _muto("⛔ non ho letto le chiamate al guardiano nella finestra")
    if n == 0:
        return _muto("⛔ ZERO chiamate al guardiano col mio giro: il ritardo non "
                     "e' mai stato pagato, quindi non ho misurato niente")
    return _si("la leva ha morso: %d chiamate col mio giro" % n)


def a1_si_arma(cella):
    """A1 · ⭐ LA GUARDIA SI ARMA QUANDO IL CICLO SI FERMA — e il buco che vede
       dev'essere piu' lungo della soglia del silenzio, o non e' il caso che ci
       interessa."""
    buchi = cella.get("buchi")
    if buchi is None:
        return _muto("⛔ non ho letto il registro: non giudico")
    if not buchi:
        return _no("⛔ il ciclo e' stato fermo (guardiano finto a %d ms) e la "
                   "guardia NON ha scritto una riga: o non si arma, o il ciclo "
                   "non si e' fermato davvero" % A_D_MS)
    peggiore = max(b["buco_ms"] for b in buchi)
    if peggiore < A_SOGLIA_SILENZIO_MS:
        return _muto("⚠ la guardia si e' armata %d volte, ⛔ ma il buco peggiore "
                     "e' %d ms, sotto la soglia del silenzio (%d): questo caso "
                     "non e' quello che mi interessa, non giudico"
                     % (len(buchi), peggiore, A_SOGLIA_SILENZIO_MS))
    return _si("⭐ la guardia si e' armata %d volte, buco peggiore %d ms — piu' "
               "lungo della soglia del silenzio (%d)"
               % (len(buchi), peggiore, A_SOGLIA_SILENZIO_MS))


def a1_sfratto_ingiusto(cella, quale):
    """⛔⛔⛔ IL ROSSO CHE CONTA, e questo si e' presentato: **col ciclo del padre
       bloccato, una sessione SANA viene sfrattata**.

    ⭐ E la riga porta la prova che la rete non c'entrava, in due campi:
       `persi=0` — non si e' perso un pacchetto — e `cwnd_left` ALTO, cioe' la
       finestra di congestione era **larga**: c'era posto per spedire, e non
       abbiamo spedito perche' non stavamo girando.
    ⇒ E' la famiglia P2/P5 di §8.2 vista dal capo che si puo' comandare."""
    sc = cella.get("scatti")
    if sc is None:
        return _muto("⛔ non ho letto gli scatti dal registro")
    if quale == "rosso":
        if not sc:
            return _no("⛔ il ciclo e' stato bloccato %d ms per volta e NESSUNO "
                       "e' stato sfrattato: il difetto non si e' presentato, e "
                       "allora il verde di dopo non dimostrerebbe niente"
                       % A_D_MS)
        innocenti = [s for s in sc if s.get("persi") == "0"]
        if not innocenti:
            return _no("⛔ %d sfratti, ma nessuno con `persi=0`: allora la linea "
                       "perdeva davvero, e non e' il difetto che cerco" % len(sc))
        s = innocenti[0]
        return _si("⛔ %d sfratti, %d con `persi=0` — causa=%s stallo_ms=%s "
                   "usciti_byte=%s coda_video=%s cwnd_left=%s: una sessione SANA "
                   "buttata fuori mentre la finestra di congestione era LARGA"
                   % (len(sc), len(innocenti), s.get("causa"),
                      s.get("stallo_ms"), s.get("usciti_byte"),
                      s.get("coda_video"), s.get("cwnd_left")))
    if sc:
        return _no("⛔ con la guardia ci sono ancora %d sfratti: causa=%s "
                   "persi=%s fermo_ms=%s saltati=%s"
                   % (len(sc), sc[0].get("causa"), sc[0].get("persi"),
                      sc[0].get("fermo_ms", "-"), sc[0].get("saltati", "-")))
    return _si("⭐ ZERO sfratti col ciclo bloccato %d ms per volta" % A_D_MS)


def a1_nessuna_guardia(cella):
    """⛔ IL «PRIMA»: sul prodotto di ieri il ciclo si ferma **e non lo dice
       nessuno**.  ⭐ E' il rosso onesto che questo banco puo' mostrare: non
       *«sfratta»* — quello non si e' riprodotto — ma *«resta cieco»*, che e' la
       forma di §6.13 («il degrado SILENZIOSO, che per `CODER.md` §1-bis pesa
       piu' dei fotogrammi»)."""
    buchi = cella.get("buchi")
    if buchi is None:
        return _muto("⛔ non ho letto il registro: non giudico")
    if buchi:
        return _no("⛔ il binario SENZA la cura ha scritto %d righe «il ciclo e' "
                   "rimasto indietro»: allora la cura c'e' gia', e i due bracci "
                   "non sono due bracci" % len(buchi))
    return _si("⛔ il ciclo del padre e' stato fermo (guardiano finto a %d ms) e "
               "nel registro non c'e' UNA riga che lo dica: il degrado e' "
               "silenzioso" % A_D_MS)


def a2_non_si_arma(cella):
    """A2 · ⛔⛔ E SU UNA MACCHINA SANA NON SI ARMA MAI.

    Senza questo predicato la guardia potrebbe star **spegnendo la linea morta
    di nascosto** — e uno sfratto che non arriva ha la stessa faccia di uno
    sfratto che non serviva."""
    buchi = cella.get("buchi")
    if buchi is None:
        return _muto("⛔ non ho letto il registro: non giudico")
    if buchi:
        return _no("⛔ su una macchina SANA la guardia si e' armata %d volte "
                   "(buco peggiore %d ms): sta spegnendo la linea morta di "
                   "nascosto, o il ciclo del padre e' davvero lento — e in "
                   "tutt'e due i casi va guardato"
                   % (len(buchi), max(b["buco_ms"] for b in buchi)))
    return _si("⭐ zero righe «il ciclo e' rimasto indietro» in %.0f s di "
               "macchina sana: la guardia non morde chi non deve"
               % (cella.get("durata_s") or 0))


def a3_linea_morta_regge(cella):
    """A3 · ⛔⛔ IL CONTROLLO CHE CONTA DI PIU': dopo la cura, un client MORTO
       viene ancora sfrattato.

    Una guardia che, per non sfrattare nessuno per sbaglio, non sfratta piu'
    nessuno ha rotto la cura che voleva proteggere."""
    sc = cella.get("scatti")
    if sc is None:
        return _muto("⛔ non ho letto gli scatti dal registro")
    if not sc:
        return _no("⛔ il client e' stato ucciso con `kill -9` e la linea morta "
                   "NON e' scattata: la cura ha spento la cura")
    # ⚠⚠ E LA CAUSA E' UN DATO, NON UN REQUISITO — corretto il 25 agosto 2026,
    #    dopo che questo predicato ha dato ROSSO SU CODICE GIUSTO.
    #    `[M]` Sul prodotto di ieri il client morto se ne va per `silenzio`
    #    (10 965 ms); con la guardia se ne va per `stallo` (5 000 ms), perche' i
    #    conti sono ripartiti insieme e la soglia dello stallo e' la meta' di
    #    quella del silenzio.  ⛔ Tutt'e due sono strade legittime della stessa
    #    cura, tutt'e due scrivono la loro riga, e tutt'e due se ne accorgono —
    #    anzi, la seconda **prima**.  ⇒ Quel che si pretende e' che lo sfratto
    #    ARRIVI: pretendere la strada sarebbe scambiare il come per il cosa.
    s = sc[0]
    return _si("⭐ il client morto e' stato sfrattato lo stesso: causa=%s "
               "stallo_ms=%s silenzio_ms=%s prove=%s fermo_ms=%s saltati=%s"
               % (s.get("causa"), s.get("stallo_ms"), s.get("silenzio_ms"),
                  s.get("prove"), s.get("fermo_ms", "(campo assente)"),
                  s.get("saltati", "(campo assente)")))


def b_chiamate(cella, enne, atteso_per_ripasso):
    """⭐⭐ LA COLONNA CHE DIMOSTRA LA CURA ALLA RADICE: quante domande a logind
       costa UN ripasso.  ⛔ Era `N`, dev'essere `1`."""
    n = cella.get("chiamate")
    durata = cella.get("durata_s")
    if n is None or not durata:
        return _muto("⛔ non ho letto le chiamate o la durata")
    ripassi = durata / 2.0            # `RIPASSO_LOCALI_MS` = 2000
    per_ripasso = n / ripassi if ripassi else None
    if per_ripasso is None:
        return _muto("⛔ non ho potuto contare i ripassi")
    # ⚠ Il conto e' approssimato per costruzione: mentre il ciclo e' bloccato i
    #   ripassi non cadono a due secondi esatti.  ⇒ Si giudica sul VERSO e su un
    #   fattore, non sulla seconda cifra.
    if atteso_per_ripasso == 1:
        ok = per_ripasso < (1 + enne) / 2.0
        detto = ("%0.2f chiamate per ripasso (attese ~1, con %d inquilini): %s"
                 % (per_ripasso, enne, "⭐ UNA sola" if ok else "⛔ ancora N"))
    else:
        ok = per_ripasso > (1 + enne) / 2.0
        detto = ("%0.2f chiamate per ripasso (attese ~%d, uno per inquilino): %s"
                 % (per_ripasso, enne, "⛔ N, come il difetto dice" if ok
                    else "⚠ non sono N"))
    return (_si(detto) if ok else _no(detto))


def b_ritmo(fermo, corrente, quale):
    """⛔ LA SECONDA COLONNA DEL VERDE: il ritmo non cala.

    `fermo` = la stessa cella con D=0 sullo stesso binario (il paragone giusto).
    ⚠ `None` dove non ho misurato: un ritmo che non si e' letto non e' un ritmo
      che non e' calato."""
    if fermo is None or corrente is None:
        return _muto("⛔ %s: manca uno dei due ritmi, non giudico" % quale)
    if fermo <= 0:
        return _muto("⛔ %s: il ritmo di riferimento e' %s, non giudico"
                     % (quale, fermo))
    calo = (fermo - corrente) / fermo
    if quale == "rosso":
        if calo >= B_CALO_ROSSO:
            return _si("⛔ il ritmo cala del %.0f %% (%.1f → %.1f fot/s): e' il "
                       "difetto di §6.13" % (calo * 100, fermo, corrente))
        return _no("⛔ il ritmo cala solo del %.0f %% (%.1f → %.1f): il difetto "
                   "NON si e' presentato, e il verde di dopo non direbbe niente"
                   % (calo * 100, fermo, corrente))
    if calo <= B_CALO_TOLLERATO:
        return _si("⭐ il ritmo NON cala: %.1f → %.1f fot/s (%.0f %%, sotto la "
                   "tolleranza del %.0f %%)"
                   % (fermo, corrente, calo * 100, B_CALO_TOLLERATO * 100))
    return _no("⛔ il ritmo cala ancora del %.0f %% (%.1f → %.1f fot/s)"
               % (calo * 100, fermo, corrente))


def nessuno_staccato(cella, quanti):
    vivi = cella.get("vivi_dopo")
    if vivi is None:
        return _muto("⛔ non ho potuto chiedere chi c'e'")
    if len(vivi) < quanti:
        return _no("⛔ ne sono rimasti %d su %d" % (len(vivi), quanti))
    return _si("tutte e %d le sessioni sono ancora attaccate" % quanti)


# ═══════════════════════════════════════════════════════════════════════════
# LA MISURA
# ═══════════════════════════════════════════════════════════════════════════
def buchi_nella_fetta(r0, r1):
    """Le righe «il ciclo del padre e' rimasto indietro» nella finestra.

    ⛔ `None` se non ho letto: zero righe e «non ho letto» non devono avere la
       stessa faccia (`LEZIONI.md` §1.9)."""
    if r0 is None or r1 is None or r1 < r0:
        return None
    rc, out, err = b92.root(
        "python3 - %s %d %d <<'FINE'\n"
        "import re, sys, json\n"
        "p, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])\n"
        "f = open(p, 'rb'); f.seek(a); t = f.read(max(0, b - a)).decode('utf-8', 'replace')\n"
        "R = re.compile(r\"(\\S+): il ciclo del padre e' rimasto indietro di (\\d+) ms\")\n"
        "print(json.dumps([{'chi': m.group(1), 'buco_ms': int(m.group(2))}\n"
        "                  for m in R.finditer(t)]))\n"
        "FINE" % (b97.REGISTRO, r0, r1), 300)
    try:
        return json.loads(out.strip().splitlines()[-1])
    except Exception:
        return None


def cella_piena(giro, quanti, ritardo_ms, durata_s):
    """La cella di `10-b97`, piu' i buchi del ciclo e il ritmo per sessione."""
    r0 = b97.registro_byte()
    c = b97.cella(giro, quanti, ritardo_ms, durata_s)
    r1 = b97.registro_byte()
    c["buchi"] = buchi_nella_fetta(r0, r1)
    c["per"] = b97.per_sessione(c, quanti, durata_s)
    b97.stampa_sessioni(c["per"])
    # ⛔ Solo le sessioni che hanno DAVVERO misurato: una fetta che non ha letto
    #    torna `esito` diverso da «misurato», e mediarla come uno zero direbbe
    #    «il ritmo e' crollato» su una sessione che non e' stata guardata.
    fot = []
    if isinstance(c["per"], dict):
        for i in sorted(k for k in c["per"] if isinstance(k, int)):
            v = c["per"][i]
            if (isinstance(v, dict) and v.get("esito") == "misurato"
                    and isinstance(v.get("fps"), (int, float))):
                fot.append(v["fps"])
    c["fot_s"] = (sum(fot) / len(fot)) if fot else None
    c["fot_s_letti"] = len(fot)
    _inf("ritmo medio nella cella: %s fot/s (letto su %d sessioni) · buchi del "
         "ciclo: %s" % (round(c["fot_s"], 2) if c["fot_s"] is not None else "?",
                        c["fot_s_letti"],
                        "?" if c["buchi"] is None else len(c["buchi"])))
    return c


def braccio_a(nome_binario, quale, esiti):
    """⭐ LA SCENA DELLA PROVA A, e la sua forma e' quella di P5: **una sessione
       SANA che un attimo prima consegnava**, e poi un buco fra due scene.

    ⛔ E il buco da solo NON BASTA — `[M]` 25 agosto 2026, questo incarico: una
       sessione sola, 30 s senza scena, ciclo sano ⇒ **nessuno sfratto**, con i
       PING del trasporto puntuali ogni 5 s (`spediti_d=1`) e la risposta del
       client entro un secondo (`ricevuti_d=1`).  ⇒ Il margine «due volte» di
       §6.8 REGGE finche' il ciclo gira.
    ⭐⭐ Quel che lo rompe e' che **i PING non possono uscire da un ciclo fermo**:
       li' il silenzio che la linea morta misura e' il NOSTRO.  ⇒ Il guardiano
       finto a D=12 s e' la leva che ferma il ciclo, e il buco fra le scene e'
       quel che toglie al client qualunque altra cosa da riscontrare."""
    _log("PROVA A · %s — binario «%s», N=%d" % (quale.upper(), nome_binario,
                                                A_ENNE))
    md5 = metti_binario(nome_binario)
    if md5 is None:
        return None
    guai = b97.apri_fino_a(A_ENNE, 3600, gia=0)
    if guai:
        for g in guai:
            _ko(g)
        return None
    time.sleep(5)
    fuori = {"binario": nome_binario, "md5": md5}

    # ── A2 · LA MACCHINA SANA, e si guarda PRIMA ──────────────────────
    # ⛔ Prima del ciclo bloccato, non dopo: dopo, un contatore cumulativo di
    #    buchi renderebbe questo predicato impossibile da soddisfare per
    #    costruzione — e un predicato che non puo' dare verde non e' un
    #    predicato, e' un rosso travestito.
    _log("A2 · la macchina SANA — la guardia non deve armarsi mai")
    fuori["sana_macchina"] = cella_piena(
        "a-%s-sana-%d" % (quale, int(time.time())), A_ENNE, 0,
        A_SANA_MACCHINA_S)

    # ── A1 · IL CICLO CHE SI FERMA ────────────────────────────────────
    _log("A1 · il ciclo che si ferma — guardiano finto a %d ms" % A_D_MS)
    fuori["ciclo_fermo"] = cella_piena(
        "a-%s-fermo-%d" % (quale, int(time.time())), A_ENNE, A_D_MS,
        A_DURATA_S)

    # ── A3 · E LA LINEA MORTA DEVE FUNZIONARE ANCORA ──────────────────
    _log("A3 · ⛔ il controllo che conta di piu': `kill -9` sul client, e lo "
         "sfratto deve arrivare LO STESSO")
    b97.guardiano_a_riposo("sto per riaprire la sessione per A3")
    b97.riapri_i_caduti(A_ENNE, 3600)
    time.sleep(5)
    r0 = b97.registro_byte()
    giro = "a-%s-morto-%d" % (quale, int(time.time()))
    ok, perche = b97.ritardo_poni(giro, 0)
    _inf(perche)
    vivo_prima = b92.vivo(1)
    b92.root("pkill -9 -f -- '%s' ; true" % b92.cerca_giornale(1))
    time.sleep(2)
    vivo_dopo = b92.vivo(1)
    _inf("il client s1: vivo prima=%s, dopo il `kill -9`=%s"
         % (vivo_prima, vivo_dopo))
    time.sleep(A_MORTO_ATTESA_S)
    r1 = b97.registro_byte()
    fetta = b97.registro_fetta(r0, r1)
    morto = {"giro": giro, "leva": ok, "leva_perche": perche,
             "vivo_prima": vivo_prima, "vivo_dopo": vivo_dopo,
             "scatti": fetta.get("scatti") if fetta.get("esito") == "letto" else None,
             "buchi": buchi_nella_fetta(r0, r1),
             "durata_s": A_MORTO_ATTESA_S}
    if morto["scatti"]:
        for s in morto["scatti"][:4]:
            _inf("   %s causa=%s silenzio_ms=%s prove=%s persi=%s fermo_ms=%s "
                 "saltati=%s ritmo_giu=%s"
                 % (s.get("provenienza"), s.get("causa"), s.get("silenzio_ms"),
                    s.get("prove"), s.get("persi"), s.get("fermo_ms", "-"),
                    s.get("saltati", "-"), s.get("ritmo_giu", "-")))
    fuori["client_morto"] = morto

    esiti["a_" + quale] = fuori
    return fuori


def braccio_b(nome_binario, quale, esiti):
    _log("PROVA B · %s — binario «%s», N=%d, D=%d ms"
         % (quale.upper(), nome_binario, B_ENNE, B_D_MS))
    md5 = metti_binario(nome_binario)
    if md5 is None:
        return None
    guai = b97.apri_fino_a(B_ENNE, 3600, gia=0)
    if guai:
        for g in guai:
            _ko(g)
        return None
    time.sleep(5)
    # ⛔ PRIMA il riferimento sullo STESSO binario: «il ritmo non cala» va detto
    #    rispetto a se stesso a guardiano fermo, non rispetto all'altro braccio.
    fermo = cella_piena("b-%s-fermo-%d" % (quale, int(time.time())), B_ENNE, 0,
                        B_DURATA_S)
    b97.riapri_i_caduti(B_ENNE, 3600)
    carico = cella_piena("b-%s-carico-%d" % (quale, int(time.time())), B_ENNE,
                         B_D_MS, B_DURATA_S)
    # ⛔⛔ E LA PORTA: col guardiano ancora lento, un inquilino nuovo entra?
    #     §6.13 l'ha trovato per sbaglio, e vale la pena chiuderlo: si uccide il
    #     client dell'ultima sessione e si prova a rientrare, **senza toccare il
    #     ritardo** — se lo si rimettesse a zero prima, si misurerebbe la porta
    #     di una macchina sana, cioe' un verde per costruzione.
    _log("B · ⛔ la porta a chi arriva — guardiano ancora a %d ms" % B_D_MS)
    # ⛔⛔ E IL POSTO VA LIBERATO DAVVERO PRIMA DI RIBUSSARE.  `[M]` 25 agosto
    #     2026, primo giro vero: il banco uccideva il client e ribussava subito,
    #     e il server rispondeva `CONGEDO 0x0f GIA_ATTIVA_REMOTA` — cioe' il
    #     banco misurava **il posto ancora occupato**, non la stretta di mano.
    #     ⚠ Un rosso giusto per la ragione sbagliata e' peggio di nessun rosso.
    #     ⇒ `kill -9`, e poi si aspetta lo sfratto del fantasma (`--sfratto-ms`,
    #       15 000 ms) con il suo margine.
    b92.root("pkill -9 -f -- '%s' ; true" % b92.cerca_giornale(B_ENNE))
    time.sleep(B_SFRATTO_ATTESA_S)
    porta = riesce_a_collegarsi(B_ENNE)
    (_ok if porta[0] else _ko)(porta[1])
    for c, n in ((fermo, "fermo"), (carico, "carico")):
        c["binario"], c["md5"] = nome_binario, md5
        esiti["b_%s_%s" % (quale, n)] = c
    carico["porta"] = {"esito": porta[0], "perche": porta[1]}
    return fermo, carico


def riesce_a_collegarsi(i, tetto_s=B_PORTA_TETTO_S):
    """⛔⛔ «UN INQUILINO NUOVO RIESCE ANCORA A ENTRARE?» — il rilievo di prodotto
       che §6.13 ha trovato per sbaglio: *«col guardiano lento un inquilino nuovo
       non riesce a collegarsi affatto: la stretta di mano scade»*.  ⇒ Non
       rallenta chi e' dentro: **chiude la porta a chi arriva**.

    ⛔ E' scritto qui e non si usa `b92.apri_sessione()` per UNA ragione sola: la'
       il tetto e' 240 s, giusto per una sessione grafica che deve NASCERE.  Qui
       il palco c'e' gia' (l'ha appena aperto il braccio), e quel che si misura
       e' la **stretta di mano**: un tetto da quattro minuti trasformerebbe un
       rosso in quattro minuti di attesa per braccio.
    ⚠ Torna `(True/False/None, perche)`: `None` quando non ho potuto guardare."""
    u = b92.utente(i)
    log, gio = b92.registro_di(i), b92.giornale_di(i)
    seg = "%s/segnale-%d" % (LAV, i)
    b92.root("rm -f %s %s %s" % (log, gio, seg))
    dentro = ("python3 -u %s/10-b92-cliente.py "
              "--cliente %s/banchi/01-b3-cliente.py --giornale %s "
              "--indirizzo %s --porta %d --utente %s --parola-file %s/parola "
              "--tela %s --video-codec %s --audio-codec pcm --resta %d "
              "--segnale %s"
              % (os.environ["DENTRO_LAV"], os.environ["DENTRO_ALB"],
                 os.environ["DENTRO_LAV"] + "/giornale-%d.jsonl" % i,
                 b92.IND, PORTA, u, os.environ["DENTRO_LAV"], b92.TELA,
                 b92.CODEC_CHIESTO, int(tetto_s) + 60,
                 os.environ["DENTRO_LAV"] + "/segnale-%d" % i))
    import shlex
    b92.root("setsid nohup bash /media/REMOTIX/enter.sh --root %s >> %s 2>&1 & "
             "echo avviato" % (shlex.quote(dentro), log))
    fine = time.time() + tetto_s
    while time.time() < fine:
        time.sleep(2.0)
        rc, out, _ = b92.root("test -f %s && echo si || echo no" % seg)
        if "si" in out:
            return _si("⭐ l'inquilino nuovo e' ENTRATO in %.0f s: la porta e' "
                       "aperta anche col guardiano lento"
                       % (tetto_s - (fine - time.time())))
    rc, out, _ = b92.root("tail -6 %s || true" % log)
    return _no("⛔ l'inquilino nuovo NON e' entrato in %.0f s — la stretta di "
               "mano scade: il guardiano lento chiude la porta a chi arriva.  "
               "Il suo registro dice: %s" % (tetto_s, out.strip()[-260:]))


def c_anello(cella, quale):
    """PROVA C · l'anello di §6.15, e ⛔ **l'attribuzione**, che e' la parte
       nuova: la riga dello sfratto adesso porta `ritmo_giu=` e `fermo_ms=`, e
       dice da sola se a non far uscire niente eravamo NOI."""
    sc = cella.get("scatti")
    if sc is None:
        return _muto("⛔ non ho letto gli scatti dal registro")
    if quale == "rosso":
        if not sc:
            return _muto("⚠ l'anello di §6.15 NON si e' presentato su %d "
                         "sessioni sature in %.0f s: ⛔ e «non si e' presentato» "
                         "non e' «e' curato» — non giudico"
                         % (C_ENNE, cella.get("durata_s") or 0))
        return _si("⛔ %d sfratti (persi=%s, causa=%s): l'anello si e' presentato"
                   % (len(sc), sc[0].get("persi"), sc[0].get("causa")))
    if sc:
        return _no("⛔ con la cura ci sono ancora %d sfratti: causa=%s persi=%s "
                   "ritmo_giu=%s ritmo_arretrato=%s fermo_ms=%s saltati=%s"
                   % (len(sc), sc[0].get("causa"), sc[0].get("persi"),
                      sc[0].get("ritmo_giu", "-"),
                      sc[0].get("ritmo_arretrato", "-"),
                      sc[0].get("fermo_ms", "-"), sc[0].get("saltati", "-")))
    return _si("⭐ zero sfratti su %d sessioni sature in %.0f s"
               % (C_ENNE, cella.get("durata_s") or 0))


def braccio_c(nome_binario, quale, esiti):
    """⛔ Qui i binari sono NUDI (senza guardiano finto): la leva e' la GPU, e un
       adattatore che dorme falserebbe proprio la grandezza in prova."""
    _log("PROVA C · %s — binario «%s», %d sessioni SATURE, %.0f s"
         % (quale.upper(), nome_binario, C_ENNE, C_DURATA_S))
    md5 = metti_binario(nome_binario)
    if md5 is None:
        return None
    guai = b97.apri_fino_a(C_ENNE, 3600, gia=0)
    if guai:
        for g in guai:
            _ko(g)
        # ⚠ Non si esce: cinque sessioni sature sono proprio la scena in cui
        #   qualcuna puo' non aprirsi.  ⛔ Ma quante ce ne sono davvero si
        #   DICHIARA, e il giudizio lo dice.
    time.sleep(5)
    r0 = b97.registro_byte()
    t0 = b97.orologio_ms()
    vivi_prima, scene_prima, _ = b92.chi_c_e(C_ENNE)
    partito = time.time()
    time.sleep(C_DURATA_S)
    durata = time.time() - partito
    t1 = b97.orologio_ms()
    r1 = b97.registro_byte()
    fetta = b97.registro_fetta(r0, r1)
    vivi_dopo, scene_dopo, manca = b92.chi_c_e(C_ENNE)
    c = {"binario": nome_binario, "md5": md5, "durata_s": durata,
         "scatti": fetta.get("scatti") if fetta.get("esito") == "letto" else None,
         "buchi": buchi_nella_fetta(r0, r1),
         "vivi_prima": [i for i in vivi_prima if vivi_prima[i]],
         "vivi_dopo": [i for i in vivi_dopo if vivi_dopo[i]],
         "scene_prima": sum(1 for i in scene_prima if scene_prima[i]),
         "scene_dopo": (None if manca
                        else sum(1 for i in scene_dopo if scene_dopo[i])),
         "t0_ms": t0, "t1_ms": t1}
    c["per"] = b97.per_sessione(c, C_ENNE, durata)
    b97.stampa_sessioni(c["per"])
    _inf("sessioni vive: %d prima, %d dopo · scene che disegnano: %s prima, %s "
         "dopo · buchi del ciclo: %s"
         % (len(c["vivi_prima"]), len(c["vivi_dopo"]), c["scene_prima"],
            c["scene_dopo"], "?" if c["buchi"] is None else len(c["buchi"])))
    if c["scatti"]:
        _ko("⛔ %d SCATTI di linea morta" % len(c["scatti"]))
        for s in c["scatti"][:8]:
            _inf("   %s causa=%s persi=%s usciti_byte=%s coda_video=%s "
                 "silenzio_ms=%s stallo_ms=%s ritmo_giu=%s ritmo_arretrato=%s "
                 "ritmo_scesi=%s fermo_ms=%s saltati=%s cwnd_left=%s"
                 % (s.get("provenienza"), s.get("causa"), s.get("persi"),
                    s.get("usciti_byte"), s.get("coda_video"),
                    s.get("silenzio_ms"), s.get("stallo_ms"),
                    s.get("ritmo_giu", "-"), s.get("ritmo_arretrato", "-"),
                    s.get("ritmo_scesi", "-"), s.get("fermo_ms", "-"),
                    s.get("saltati", "-"), s.get("cwnd_left")))
    else:
        _ok("nessuno sfratto")
    esiti["c_" + quale] = c
    return c


def dillo(nome, esito_perche, rossi, muti):
    esito, perche = esito_perche
    if esito is True:
        _ok("%s: %s" % (nome, perche))
    elif esito is False:
        _ko("%s: %s" % (nome, perche))
        rossi.append("%s: %s" % (nome, perche))
    else:
        _dub("%s: %s" % (nome, perche))
        muti.append("%s: %s" % (nome, perche))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LA CERTIFICAZIONE — «un banco non e' finito finche' non lo si e' visto
#      dare ROSSO» (`LEZIONI.md` §1.29).  Ogni predicato ha il suo guasto, e il
#      guasto GIRA: qui sotto non si immagina niente.
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL SENTINELLA, E NON E' PEDANTERIA: la prima stesura scriveva
#     `scatti if scatti is not None else []`, cioe' trasformava «non ho letto»
#     in «zero scatti» — proprio la confusione che TUTTI i predicati di questo
#     banco esistono per non fare.  ⭐ E l'ha trovata il `--certifica`: il caso
#     «registro non letto ⇒ non giudico» e' uscito ROSSO.  Un difetto del banco,
#     preso dal banco.
MANCA = object()


def _cella(scatti=MANCA, chiamate=8, buchi=None, vivi=None, durata=70.0,
           leva=True):
    return {"leva": leva, "leva_perche": "posto", "chiamate": chiamate,
            "scatti": [] if scatti is MANCA else scatti,
            "buchi": buchi, "vivi_dopo": vivi, "durata_s": durata}


def _scatto(causa="silenzio", persi="0"):
    return {"causa": causa, "persi": persi, "usciti_byte": "0",
            "silenzio_ms": "10997", "coda_video": "10443"}


def certifica():
    print(__doc__.split("Uso (dal portatile)")[0])
    _log("⛔ I GUASTI INNESTATI — sano → guasto → risanato, ciascuno GIRATO")
    casi, buoni = [], 0

    def caso(nome, atteso, visto):
        nonlocal buoni
        ok = (visto[0] is atteso)
        casi.append((nome, ok))
        if ok:
            buoni += 1
            _ok("%s → %s" % (nome, {True: "verde", False: "ROSSO",
                                    None: "non giudico"}[visto[0]]))
        else:
            _ko("%s → atteso %s, visto %s (%s)"
                % (nome, atteso, visto[0], visto[1]))

    # ── la leva ────────────────────────────────────────────────────────
    caso("leva sana", True, leva_ha_preso(_cella()))
    caso("leva NON presa", None, leva_ha_preso(_cella(leva=False)))
    caso("leva con ZERO chiamate", None, leva_ha_preso(_cella(chiamate=0)))
    caso("leva con chiamate None", None,
         leva_ha_preso({"leva": True, "chiamate": None}))

    # ── A1 · la guardia si arma quando deve ────────────────────────────
    caso("A1 sano (si arma, e il buco supera la soglia)", True,
         a1_si_arma(_cella(buchi=[{"buco_ms": 11400}, {"buco_ms": 11000}])))
    caso("A1 con ZERO righe ⇒ non si arma", False,
         a1_si_arma(_cella(buchi=[])))
    caso("A1 con un buco sotto la soglia del silenzio ⇒ non giudico", None,
         a1_si_arma(_cella(buchi=[{"buco_ms": 2400}])))
    caso("A1 col registro non letto ⇒ non giudico", None,
         a1_si_arma(_cella(buchi=None)))

    # ── A1 · lo sfratto ingiusto ───────────────────────────────────────
    caso("A1/rosso sano (una sessione sana sfrattata, persi=0)", True,
         a1_sfratto_ingiusto(_cella(scatti=[_scatto(causa="stallo")]), "rosso"))
    caso("A1/rosso senza sfratti ⇒ il difetto non c'e'", False,
         a1_sfratto_ingiusto(_cella(scatti=[]), "rosso"))
    caso("A1/rosso con la linea che perdeva davvero", False,
         a1_sfratto_ingiusto(_cella(scatti=[_scatto(persi="37")]), "rosso"))
    caso("A1/verde sano (zero sfratti)", True,
         a1_sfratto_ingiusto(_cella(scatti=[]), "verde"))
    caso("A1/verde che sfratta ancora", False,
         a1_sfratto_ingiusto(_cella(scatti=[_scatto()]), "verde"))
    caso("A1 col registro non letto ⇒ non giudico", None,
         a1_sfratto_ingiusto(_cella(scatti=None), "verde"))

    # ── A1 · il PRIMA: il ciclo si ferma e nessuno lo dice ─────────────
    caso("A/prima sano (nessuna riga: il degrado e' silenzioso)", True,
         a1_nessuna_guardia(_cella(buchi=[])))
    caso("A/prima con le righe della guardia ⇒ non sono due bracci", False,
         a1_nessuna_guardia(_cella(buchi=[{"buco_ms": 11400}])))
    caso("A/prima col registro non letto ⇒ non giudico", None,
         a1_nessuna_guardia(_cella(buchi=None)))

    # ── A2 · e NON si arma su una macchina sana ────────────────────────
    caso("A2 sano (zero righe su macchina sana)", True,
         a2_non_si_arma(_cella(buchi=[], durata=90.0)))
    caso("A2 con la guardia che morde una macchina sana", False,
         a2_non_si_arma(_cella(buchi=[{"buco_ms": 1600}], durata=90.0)))
    caso("A2 col registro non letto ⇒ non giudico", None,
         a2_non_si_arma(_cella(buchi=None, durata=90.0)))

    # ── A3 · ⛔ e la linea morta funziona ancora ────────────────────────
    caso("A3 sano (il client morto viene sfrattato per silenzio)", True,
         a3_linea_morta_regge(_cella(scatti=[_scatto()])))
    caso("A3 ⛔ nessuno sfratto: la cura ha spento la cura", False,
         a3_linea_morta_regge(_cella(scatti=[])))
    caso("A3 con uno sfratto per STALLO invece che per silenzio ⇒ va bene "
         "lo stesso: lo sfratto e' arrivato", True,
         a3_linea_morta_regge(_cella(scatti=[_scatto(causa="stallo")])))
    caso("A3 col registro non letto ⇒ non giudico", None,
         a3_linea_morta_regge(_cella(scatti=None)))

    # ── prova B, le chiamate per ripasso ───────────────────────────────
    caso("B chiamate: 7 per ripasso sul binario vecchio", True,
         b_chiamate(_cella(chiamate=157, durata=45.0), 7, 7))
    caso("B chiamate: UNA per ripasso sul binario curato", True,
         b_chiamate(_cella(chiamate=22, durata=45.0), 7, 1))
    caso("B chiamate: ancora sette dove ne attendevo una", False,
         b_chiamate(_cella(chiamate=157, durata=45.0), 7, 1))
    caso("B chiamate: una dove ne attendevo sette", False,
         b_chiamate(_cella(chiamate=22, durata=45.0), 7, 7))
    caso("B chiamate non lette ⇒ non giudico", None,
         b_chiamate(_cella(chiamate=None, durata=45.0), 7, 1))
    caso("B durata a zero ⇒ non giudico", None,
         b_chiamate(_cella(chiamate=22, durata=0), 7, 1))

    # ── prova B, il ritmo ──────────────────────────────────────────────
    caso("B ritmo rosso sano (39 → 1,3)", True, b_ritmo(39.0, 1.3, "rosso"))
    caso("B ritmo rosso che non cala ⇒ il difetto non c'e'", False,
         b_ritmo(39.0, 38.0, "rosso"))
    caso("B ritmo verde sano (39 → 38)", True, b_ritmo(39.0, 38.0, "verde"))
    caso("B ritmo verde che cala ancora", False, b_ritmo(39.0, 20.0, "verde"))
    caso("B ritmo con un termine non letto ⇒ non giudico", None,
         b_ritmo(None, 38.0, "verde"))
    caso("B ritmo di riferimento a zero ⇒ non giudico", None,
         b_ritmo(0.0, 38.0, "verde"))

    # ── prova C · l'anello di §6.15 ────────────────────────────────────
    caso("C/prima: l'anello si e' presentato", True,
         c_anello(_cella(scatti=[_scatto()], durata=150.0), "rosso"))
    caso("C/prima: non si e' presentato ⇒ ⛔ NON e' «curato», non giudico", None,
         c_anello(_cella(scatti=[], durata=150.0), "rosso"))
    caso("C/dopo: zero sfratti", True,
         c_anello(_cella(scatti=[], durata=150.0), "verde"))
    caso("C/dopo: sfratta ancora", False,
         c_anello(_cella(scatti=[_scatto()], durata=150.0), "verde"))
    caso("C col registro non letto ⇒ non giudico", None,
         c_anello(_cella(scatti=None, durata=150.0), "verde"))

    # ── chi e' rimasto ─────────────────────────────────────────────────
    caso("nessuno staccato, sano", True,
         nessuno_staccato(_cella(vivi=[1, 2, 3]), 3))
    caso("uno staccato", False, nessuno_staccato(_cella(vivi=[1, 2]), 3))
    caso("non ho potuto chiedere ⇒ non giudico", None,
         nessuno_staccato(_cella(vivi=None), 3))

    _log("ESITO DELLA CERTIFICAZIONE")
    print("    %d casi su %d hanno fatto quel che era scritto prima"
          % (buoni, len(casi)))
    return 0 if buoni == len(casi) else 1


# ═══════════════════════════════════════════════════════════════════════════
def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?", default="tutto",
                   choices=["a", "b", "c", "tutto", "stato", "sgombra"])
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--senza-lucchetto", action="store_true",
                   help="⚠ per la messa a punto: i numeri NON si riferiscono")
    p.add_argument("--senza-controllo", action="store_true",
                   help="⚠ salta il controllo negativo (solo per la messa a punto)")
    p.add_argument("--lucchetto-esterno", action="store_true",
                   help="⭐ il lucchetto lo tiene chi mi ha lanciato")
    a = p.parse_args()

    if a.certifica:
        return certifica()

    apri_attrezzi()
    os.makedirs(FUORI, exist_ok=True)

    if a.passo == "stato":
        rc, out, _ = b92.root("systemctl is-active %s; ss -uln | grep -c ':%d ' "
                              "|| true" % (UNITA, PORTA))
        _inf("unita' %s: %s" % (UNITA, out.strip().replace("\n", " · ")))
        _inf("innesto nel registro: %s" % b97.innesto_c_e())
        for i in range(1, 8):
            _inf("s%d (%s): %s" % (i, b92.utente(i),
                                   "viva" if b92.vivo(i) else "spenta"))
        return 0
    if a.passo == "sgombra":
        sgombra()
        return 0

    esiti = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "porta": PORTA,
             "passo": a.passo}
    rossi, muti = [], []

    # ⛔⛔ LA STIMA DEL POSSESSO SI SBAGLIA PER ECCESSO — §7.3, terza trappola:
    #     un giro che dura piu' di quanto ha dichiarato si vede SCASSINARE il
    #     lucchetto a meta' misura, e chi lo prende misura su sette palchi vivi
    #     credendo la macchina sgombra.  Nessuno dei due vede rosso.
    bracci_a = 2 if a.passo in ("a", "tutto") else 0
    bracci_b = 2 if a.passo in ("b", "tutto") else 0
    if not a.senza_controllo:
        bracci_a += 1 if bracci_a else 0
        bracci_b += 1 if bracci_b else 0
    bracci_c = 2 if a.passo in ("c", "tutto") else 0
    stima = (120                                       # spedizioni e terreno
             + bracci_a * (A_SANA_MACCHINA_S + A_DURATA_S + A_MORTO_ATTESA_S
                           + 120 + 240)                # apertura + le tre scene
             + bracci_b * (2 * B_DURATA_S + 120 + 7 * 240)
             + bracci_c * (C_DURATA_S + 120 + C_ENNE * 240)
             + 180)                                    # lo sgombero finale
    quanto = int(stima * 1.6)
    _inf("⭐ il giro si stima in %d s; dichiaro di tenere il lucchetto %d s "
         "(margine ×1,6, e si sbaglia per ECCESSO)" % (stima, quanto))

    preso = False
    try:
        if a.lucchetto_esterno:
            _inf("⭐ il lucchetto lo tiene chi mi ha lanciato")
        elif a.senza_lucchetto:
            _dub("⚠ SENZA LUCCHETTO: questi numeri NON si riferiscono")
        else:
            try:
                luc.prendi(IO_SONO, secondi=quanto, attesa=21600)
                preso = True
            except Exception as e:
                _ko("⛔ IL TURNO NON E' MAI ARRIVATO: %s" % e)
                return 4

        _log("SGOMBERO DI PARTENZA — chi arriva dopo deve trovare pulito, e io pure")
        sgombra()

        guai = b97.spedisci_attrezzi()
        if guai:
            for g in guai:
                _ko(g)
            return 2

        # ⛔⛔ PRIMA DEL TERRENO SI RIMETTE IL BINARIO DELL'ALBERO, e non e' una
        #     furbizia: `10-b0-terreno.sh` T5.3 pretende che il binario sia piu'
        #     NUOVO dei sorgenti che dichiara — la guardia che in fase 1 ha
        #     salvato il progetto («sorgente sano, binario bugiardo»).
        #     ⚠ Questo banco scambia i binari, e alla fine del giro precedente in
        #       `$ALBERO/src/remotix` resta quello del ROSSO, costruito prima.
        #       `[M]` 25 agosto 2026: T5.3 ha dato rosso, giustamente.
        #     ⇒ Si rimette quello costruito DA QUESTI sorgenti, si guarda il
        #       terreno, e solo dopo si comincia a scambiare.  ⛔ Non si tocca
        #       T5.3 e non si tocca la data di nessun file: si rimette la
        #       verita' invece di aggirare il controllo.
        _log("IL BINARIO DELL'ALBERO, prima del terreno")
        if metti_binario(BINARIO_ALBERO) is None:
            _ko("⛔ NON MISURO: non ho potuto rimettere il binario dell'albero")
            return 2

        _log("⛔ IL TERRENO DELLA FASE 10 — si guarda PRIMA di misurare")
        rc = b97.terreno(lucchetto_mio=preso or a.lucchetto_esterno)
        if rc != 0:
            _ko("⛔ il terreno non ha dato verde (uscita %d): NON misuro" % rc)
            return 2

        # ── PROVA A ────────────────────────────────────────────────────
        if a.passo in ("a", "tutto"):
            # ── il PRIMA: il prodotto di ieri, sulle stesse tre scene ──
            prima = braccio_a("remotix-base-inn", "prima", esiti)
            if prima is None:
                muti.append("A: il braccio SENZA la cura non e' stato misurato")
            else:
                dillo("A/prima · la leva",
                      leva_ha_preso(prima["ciclo_fermo"]), rossi, muti)
                dillo("A/prima · ⛔⛔ IL DIFETTO: una sessione sana sfrattata",
                      a1_sfratto_ingiusto(prima["ciclo_fermo"], "rosso"),
                      rossi, muti)
                dillo("A/prima · e nessuna riga lo dice",
                      a1_nessuna_guardia(prima["ciclo_fermo"]), rossi, muti)
                dillo("A/prima · la linea morta sfratta il client morto",
                      a3_linea_morta_regge(prima["client_morto"]), rossi, muti)
            sgombra()
            # ── il DOPO: lo stesso, con la guardia ────────────────────
            dopo = braccio_a("remotix-cura-inn", "dopo", esiti)
            if dopo is None:
                muti.append("A: il braccio CON la cura non e' stato misurato")
            else:
                dillo("A/dopo · la leva",
                      leva_ha_preso(dopo["ciclo_fermo"]), rossi, muti)
                dillo("A1/dopo · ⛔⛔ NESSUNO viene piu' sfrattato",
                      a1_sfratto_ingiusto(dopo["ciclo_fermo"], "verde"),
                      rossi, muti)
                dillo("A1/dopo · la guardia si arma quando deve",
                      a1_si_arma(dopo["ciclo_fermo"]), rossi, muti)
                dillo("A2/dopo · e NON si arma su una macchina sana",
                      a2_non_si_arma(dopo["sana_macchina"]), rossi, muti)
                dillo("A3/dopo · ⛔ e la linea morta funziona ANCORA",
                      a3_linea_morta_regge(dopo["client_morto"]), rossi, muti)
            if not a.senza_controllo:
                sgombra()
                _log("⛔ IL CONTROLLO NEGATIVO — rimetto il binario SENZA la "
                     "guardia e pretendo che il banco torni a non vedere niente")
                indietro = braccio_a("remotix-base-inn", "controllo", esiti)
                if indietro is None:
                    muti.append("A: il controllo negativo non e' stato misurato")
                else:
                    dillo("A/controllo · torna a sfrattare",
                          a1_sfratto_ingiusto(indietro["ciclo_fermo"], "rosso"),
                          rossi, muti)
                    dillo("A/controllo · e torna cieco",
                          a1_nessuna_guardia(indietro["ciclo_fermo"]),
                          rossi, muti)
            sgombra()

        # ── PROVA B ────────────────────────────────────────────────────
        if a.passo in ("b", "tutto"):
            due = braccio_b("remotix-base-inn", "rosso", esiti)
            if due is None:
                muti.append("B: il braccio del rosso non e' stato misurato")
            else:
                fermo, carico = due
                dillo("B/rosso · la leva", leva_ha_preso(carico), rossi, muti)
                dillo("B/rosso · le chiamate",
                      b_chiamate(carico, B_ENNE, B_ENNE), rossi, muti)
                dillo("B/rosso · il ritmo crolla",
                      b_ritmo(fermo.get("fot_s"), carico.get("fot_s"), "rosso"),
                      rossi, muti)
                # ⚠⚠ E QUI IL BANCO HA IMPARATO QUALCOSA, IL 25 AGOSTO 2026: la
                #     porta sul braccio del ROSSO era scritta come PREDICATO
                #     («deve NON entrare»), e ha dato rosso su codice giusto.
                #     `[M]` A D=286 ms l'inquilino nuovo **entra lo stesso**, in
                #     9 s; §6.13 aveva visto la porta chiudersi col guardiano a
                #     **5 000 ms**, che e' un'altra cella.
                #  ⇒ Qui la porta e' una MISURA, non un giudizio: si riferisce il
                #    tempo nei due bracci, e il rosso lo si da' solo se **con la
                #    cura** non entra.  ⭐ Pretendere un difetto a una cella in
                #    cui non e' mai stato misurato e' la forma E1 al contrario.
                _inf("la porta a chi arriva, SENZA la cura: %s"
                     % (carico.get("porta") or {}).get("perche", "?"))
            sgombra()
            due = braccio_b("remotix-cura-inn", "verde", esiti)
            if due is None:
                muti.append("B: il braccio del verde non e' stato misurato")
            else:
                fermo, carico = due
                dillo("B/verde · la leva", leva_ha_preso(carico), rossi, muti)
                dillo("B/verde · una domanda sola",
                      b_chiamate(carico, B_ENNE, 1), rossi, muti)
                dillo("B/verde · il ritmo NON cala",
                      b_ritmo(fermo.get("fot_s"), carico.get("fot_s"), "verde"),
                      rossi, muti)
                dillo("B/verde · chi e' rimasto",
                      nessuno_staccato(carico, B_ENNE), rossi, muti)
                p = (carico.get("porta") or {}).get("esito")
                dillo("B/verde · la porta a chi arriva",
                      (_si("⭐ l'inquilino nuovo entra") if p is True
                       else _no("⛔ l'inquilino nuovo NON entra nemmeno con la "
                                "cura: %s"
                                % (carico.get("porta") or {}).get("perche", "?"))),
                      rossi, muti)
            sgombra()
            if not a.senza_controllo:
                _log("⛔ IL CONTROLLO NEGATIVO — rimetto il binario SENZA la cura "
                     "e pretendo che il banco torni ROSSO")
                due = braccio_b("remotix-base-inn", "controllo", esiti)
                if due is None:
                    muti.append("B: il controllo negativo non e' stato misurato")
                else:
                    fermo, carico = due
                    dillo("B/controllo · tornano N chiamate per ripasso",
                          b_chiamate(carico, B_ENNE, B_ENNE), rossi, muti)
                    dillo("B/controllo · il ritmo torna a crollare",
                          b_ritmo(fermo.get("fot_s"), carico.get("fot_s"),
                                  "rosso"), rossi, muti)
                sgombra()

        # ── PROVA C ────────────────────────────────────────────────────
        if a.passo in ("c", "tutto"):
            prima = braccio_c("remotix-base", "prima", esiti)
            if prima is None:
                muti.append("C: il braccio SENZA la cura non e' stato misurato")
            else:
                dillo("C/prima · l'anello si presenta?",
                      c_anello(prima, "rosso"), rossi, muti)
            sgombra()
            dopo = braccio_c("remotix-cura", "dopo", esiti)
            if dopo is None:
                muti.append("C: il braccio CON la cura non e' stato misurato")
            else:
                dillo("C/dopo · l'anello e' chiuso?", c_anello(dopo, "verde"),
                      rossi, muti)
            sgombra()

    finally:
        try:
            sgombra()
            terreno_sh("spegni")
        except Exception as e:
            _dub("⚠ lo sgombero finale non e' riuscito: %s" % e)
        if preso:
            luc.molla(IO_SONO)
        with open(os.path.join(FUORI, "esiti.json"), "w") as f:
            json.dump(esiti, f, indent=1, default=str)
        _inf("gli esiti crudi in %s/esiti.json" % FUORI)

    _log("IL VERDETTO")
    for r in rossi:
        _ko(r)
    for m in muti:
        _dub(m)
    if rossi:
        return 1
    if muti:
        return 3
    _ok("⭐ tutti i predicati hanno fatto quel che era scritto prima")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
