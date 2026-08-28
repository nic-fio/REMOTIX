#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b98-mista — ⭐⭐ LA SCENA **MISTA**: la scena in cui il multi-tenant vive
               davvero, e che nessuno aveva ancora misurato.

    porta 8180 · utenti `provamt1`…`provamt11` (uid 1110-1120) ⛔ **CONDIVISI**
    albero `/media/REMOTIX/src/10b8-src` · lavoro `/media/REMOTIX/tmp/10b8`
    unita' `remotix-8180` · lucchetto `10-b8`

═══════════════════════════════════════════════════════════════════════════════
⭐⭐⭐ PERCHE' ESISTE — e la ragione e' un buco nel primo giro, non un'aggiunta
═══════════════════════════════════════════════════════════════════════════════

⛔ **Tutte** le misure del primo giro hanno **tutte le sessioni che fanno la
   stessa cosa**: o tutte sature (`10-b92-dieci.py`, §6.5) o tutte ferme.

⭐ Il multi-tenant vero non e' cosi' mai.  Dieci inquilini su una macchina sono
   due che lavorano, quattro che leggono, tre che hanno la finestra aperta e non
   la guardano, e uno che guarda un video.  ⇒ **E' la scena che il budget dovra'
   governare**, ed e' quella che non era stata misurata.

E il primo giro dice che la differenza fra i due estremi e' **enorme**, non
marginale — sono i due numeri da cui parte tutto questo banco:

  · `[M]` una sessione **FERMA** costa **GPU ZERO**, letteralmente: RC6 al
    100 %, GT a **0 MHz**, **un** fotogramma in 40,8 s, 266 byte l'uno
    (§6.4-bis);
  · `[M]` una sessione **SATURA** porta la macchina a cedere alla **sesta**, e
    all'ottava tutti stanno a 1,5 fotogrammi/s (§6.5).

⇒ `[?]` **Quante sessioni ferme «entrano» accanto a una che lavora?**  Nessuno
   lo sapeva, ed e' la domanda che decide **la forma del tetto del prodotto**:
   se il prodotto deve contare **sessioni** o contare **LAVORO**.

═══════════════════════════════════════════════════════════════════════════════
⭐ CHE COSA NON E' RISCRITTO — `10-b92-dieci.py` si IMPORTA, non si copia
═══════════════════════════════════════════════════════════════════════════════

`banchi/10-b92-dieci.py` esiste, e' certificato (42 casi, 0 rossi) e misura gia'
**ogni sessione a ogni gradino** con memoria PSS, tre motori di GPU, ritardo,
chiavi e byte per fotogramma.  ⛔ Riscriverlo sarebbe rifare — e sbagliare — la
parte del lavoro che qualcuno ha gia' pagato.

⇒ Da 10-b92 si importano **tali e quali**, e girano le sue righe, non copie:

    `apri_sessione` · `uscita_del` · `chi_c_e` · `sonda` · `fra` · `terreno` ·
    `spedisci` · `registro_righe` · `mappa_provenienze` · `conti_server` ·
    `chiudi_palchi` · `chiudi_palco` · `ritardi` · `stampa_riga` ·
    `tara_riduzione` · `_importa_b70` · `_lucchetto` · e **tutti** i predicati:
    `p_scena_viva` `p_ritmo` `p_quota_chiavi` `p_I1` `p_ancora` `p_metro_gpu`
    `p_gpu_vede_la_codifica` `p_clienti_non_sono_il_collo`.
    ⭐ E i quattro attrezzi che vivono sulla macchina (cliente, fetta, sonda,
      conti) sono i suoi, spediti dal suo `terreno()`.

⛔⛔ **E il file di 10-b92 NON SI TOCCA.**  Non una riga: cosi' il suo
    `--certifica` (42 casi) resta esattamente quello che era, e lo si rifa'
    girare **da qui** con `--certifica`, in coda ai casi miei.  ⇒ Un banco che
    modificasse il banco che importa dovrebbe ricertificare tutt'e due, e la
    prima volta che se ne dimenticasse nessuno se ne accorgerebbe.

⭐ Quel che 10-b98 aggiunge, e **soltanto** questo:

  1. **la RICETTA** — invece di N gradini uguali, un ruolo per sessione:
     `S` satura · `F` ferma · `T` a strappi (il «desktop vero» di §6.4-bis);
  2. **i tre metri dei ruoli** — la prova che una «ferma» era **davvero ferma**
     e una «satura» **davvero satura**.  ⛔ Una miscela in cui le ferme non
     erano ferme non e' una miscela: e' la scena uniforme di prima con un nome
     nuovo;
  3. **la GPU per SESSIONE** — 10-b92 legge i motori della macchina; qui serve
     sapere quanto costa **quella** sessione, perche' e' l'unico modo di
     provare che una ferma costa zero.  ⇒ La sonda di 10-b92 si spedisce con
     **due righe in piu'** (la mappa contesto→uid), ⛔ e la sostituzione si
     **verifica**: se il testo non e' cambiato, il banco **si rifiuta di
     partire** invece di misurare con la sonda vecchia;
  4. ⛔ **IL RISVEGLIO SIMULTANEO** — il caso che un budget prenotato
     all'ingresso **non vede**, e il suo metro a bucket, tarato prima.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ CHE COSA QUESTO BANCO **NON** SA VEDERE — si dichiara in testa
═══════════════════════════════════════════════════════════════════════════════

Valgono per intero i sei buchi di 10-b92 (l'immagine, il browser, la rete vera
su `lo`, il costo dei clienti, la riga `ciclo:` non attribuibile, chi altro sta
sulla macchina).  ⇒ Non si ripetono qui: si leggono la'.  Questi sono **i tre
che nascono dalle miscele**, e sono nuovi:

 1. ⛔ **«A STRAPPI» QUI NON E' UN'INTERMITTENZA, E' UNA FINESTRA.**
    Il «desktop vero» di §6.4-bis e' `04-b30-scena --finestra 1280x720
    --movimento pieno` con accanto delle finestre vere, e vale `[M]` **5 130
    byte per fotogramma** a **18,92 fot/s**.  ⇒ Qui si riproduce **quello**, e
    la sollecitazione e' **continua su un'area piu' piccola**, non un ciclo
    acceso/spento.  ⚠ Un vero ciclo acceso/spento non si e' fatto per una
    ragione precisa: mentre la scena e' spenta, `chi_disegna` la vedrebbe
    «ferma» — cioe' il banco chiamerebbe ferma una sessione che sta lavorando,
    che e' esattamente la forma d'errore che questo banco esiste per chiudere.
    ⇒ Il buco si dichiara invece di essere aggirato con un ripiego.

 2. ⛔ **LE FINESTRE VERE POSSONO NON APRIRSI**, e allora il ruolo `T` e' la
    sola scena in finestra.  ⇒ Si CONTA quante ne sono vive per sessione e si
    stampa: un `T` con zero finestre vere e' piu' leggero di quello di
    §6.4-bis, e chi legge deve saperlo.

 3. ⛔ **LA GPU PER SESSIONE E' UN TEMPO OCCUPATO, NON UN LAVORO FATTO**, e
    dipende dalla frequenza della GT: `[M]` §6.1 §CLOCK, la stessa codifica da'
    26,41 % a 300 MHz e 7,01 % a 1550 — un fattore **3,8**.  ⇒ Accanto a ogni
    riga di GPU sta la GT, e i confronti si fanno **fra sessioni della stessa
    fotografia**, dove la frequenza e' la stessa per tutte.  ⚠ Un confronto fra
    due gradini con GT diverse non e' un confronto.

═══════════════════════════════════════════════════════════════════════════════
I CODICI D'USCITA — gli stessi di 10-b92, e per la stessa ragione
═══════════════════════════════════════════════════════════════════════════════

    0   CONFORME       1   ⛔ almeno un rosso       2   uso/terreno/lucchetto
    3   ⛔ NON HO NIENTE DA GIUDICARE — ⚠ e **non e' un verde**

L'ORDINE:

    1. PORTA=8180 ALBERO=… bash banchi/10-b91-terreno-dieci.sh porta
    2. PORTA=8180 …                                            utenti
    3. PORTA=8180 …                                            accendi
    4. python3 banchi/10-b98-mista.py --certifica     ⭐ i miei guasti + i 42 di b92
    5. python3 banchi/10-b98-mista.py taratura        ⛔ i metri, PRIMA
    6. python3 banchi/10-b98-mista.py miscela --ricetta SFFFFFFFFFF --durata 30
    7. python3 banchi/10-b98-mista.py risveglio --sature 1 --ferme 8
    8. PORTA=8180 … bash banchi/10-b91-terreno-dieci.sh sgombra ; … spegni
"""
import argparse
import base64
import gzip
import importlib.util
import json
import os
import statistics
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ L'ISOLAMENTO — PRIMA DELL'IMPORT DI 10-b92, CHE LO LEGGE DALL'AMBIENTE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ 10-b92 fissa porta, albero, lavoro e unita' **al momento dell'import**
#    (sono costanti di modulo).  ⇒ Se questo blocco stesse sotto l'import,
#    girerebbe sulla porta 8100 e sull'albero di un altro agente — e non
#    darebbe rosso: darebbe numeri, sull'albero sbagliato.
for _chiave, _valore in (("PORTA", "8180"),
                         ("ALBERO", "/media/REMOTIX/src/10b8-src"),
                         ("LAV", "/media/REMOTIX/tmp/10b8"),
                         ("DENTRO_ALB", "/srv/src/10b8-src"),
                         ("DENTRO_LAV", "/srv/remotix/tmp/10b8"),
                         ("UNITA", "remotix-8180"),
                         ("IO_SONO", "10-b8"),
                         ("FUORI", "/tmp/10-b98")):
    os.environ.setdefault(_chiave, _valore)

_spec = importlib.util.spec_from_file_location(
    "b92", os.path.join(QUI, "10-b92-dieci.py"))
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

# ⛔ E l'import si CONTROLLA, invece di darlo per riuscito: un modulo che si
#    carica a meta' non alza, perde solo dei nomi (`LEZIONI.md` §1.33, e la
#    stessa cura che 10-b92 ha addosso verso 09-b70).
for _nome in ("apri_sessione", "uscita_del", "chi_c_e", "sonda", "fra",
              "terreno", "spedisci", "registro_righe", "mappa_provenienze",
              "conti_server", "chiudi_palchi", "chiudi_palco", "ritardi",
              "tara_riduzione", "_importa_b70", "_lucchetto", "root", "uid",
              "utente", "p_scena_viva", "p_ritmo", "p_quota_chiavi", "p_I1",
              "p_ancora", "p_metro_gpu", "p_gpu_vede_la_codifica",
              "p_clienti_non_sono_il_collo", "SONDA", "ha_misurato",
              "certifica", "_fab", "BYTE_VIVI", "ASSESTAMENTO_S", "SCENA_BIN"):
    if not hasattr(B, _nome):
        raise SystemExit("⛔ NON MISURO: «%s» non c'e' in 10-b92-dieci.py — "
                         "l'import e' riuscito a meta'" % _nome)

if B.PORTA != int(os.environ["PORTA"]) or B.LAV != os.environ["LAV"]:
    raise SystemExit("⛔ NON MISURO: 10-b92 si e' importato con porta %d e "
                     "lavoro «%s», che NON sono i miei (%s / %s)"
                     % (B.PORTA, B.LAV, os.environ["PORTA"], os.environ["LAV"]))

_ok, _ko, _dub, _inf, _log = B._ok, B._ko, B._dub, B._inf, B._log
FUORI = os.environ["FUORI"]

# ⭐ Lo `shm` della scena e' MIO: `/dev/shm` e' UNO su tutta la macchina, e due
#    agenti con lo stesso nome si leggerebbero i disegni a vicenda **senza che
#    nessuno dei due dia rosso** (la stessa ragione di `10-b89-scena.sh`).
SHM = os.environ.get("SHM", "/10b98")
FINESTRA_T = os.environ.get("FINESTRA_T", "1280x720")


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LA SONDA DI 10-b92, PIU' DUE RIGHE — e la sostituzione SI VERIFICA
# ═══════════════════════════════════════════════════════════════════════════
#
# La sonda di 10-b92 deduplica gli `fdinfo` per `(pdev, drm-client-id)` e tiene
# `per_contesto[cid][motore] = nanosecondi`, che e' **la sola forma in cui quei
# nanosecondi si possono sottrarre** (i `drm-engine-*` sono cumulativi per
# contesto, e il contesto muore col processo).  ⚠ Ma non dice **di chi** e' il
# contesto ⇒ i motori si possono sommare per macchina, non per sessione.
#
# ⭐ Qui serve la GPU per SESSIONE, perche' e' l'unico modo di provare il fatto
#    su cui questo banco e' costruito: **una sessione ferma costa zero**.
#    ⇒ Due righe: la mappa `contesto → uid`.  Il delta si fa poi come lo fa
#      `fra()` — solo sui contesti presenti in TUTT'E DUE le fotografie.
#
# ⛔⛔ E LA SOSTITUZIONE SI CONTROLLA.  Un `replace` che non combacia non alza:
#     torna la stringa immutata, la sonda vecchia parte, e il banco stampa
#     «GPU per sessione: {}» — cioe' **tace invece di dare rosso**, che e'
#     `REVIEWER.md` E14 e la forma che nel primo giro ha prodotto ventidue
#     difetti di banco.  ⇒ Si conta, e se non e' cambiato **non si misura**.
def _sonda_piu():
    testo = B.SONDA
    a1 = '"per_contesto": {}, "contesti_miei": {},'
    n1 = '"per_contesto": {}, "contesti_miei": {}, "contesti_uid": {},'
    a2 = '        gpu["contesti_miei"][cid] = bool(mio)'
    n2 = ('        gpu["contesti_miei"][cid] = bool(mio)\n'
          '        gpu["contesti_uid"][cid] = u')
    guai = []
    if testo.count(a1) != 1:
        guai.append("l'ancora «%s» compare %d volte, non 1" % (a1, testo.count(a1)))
    if testo.count(a2) != 1:
        guai.append("l'ancora «%s» compare %d volte, non 1" % (a2, testo.count(a2)))
    if guai:
        return None, guai
    fuori = testo.replace(a1, n1).replace(a2, n2)
    if fuori == testo or "contesti_uid" not in fuori:
        return None, ["la sostituzione non ha cambiato niente"]
    return fuori, []


SONDA_PIU, _GUAI_SONDA = _sonda_piu()


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ I RUOLI, E LE SOGLIE CHE LI SEPARANO — tarate sugli ESTREMI NOTI
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `LEZIONI.md` §1.33: una soglia si tara sui due estremi **noti** prima di
#    crederci.  ⭐ Qui gli estremi non si sono scelti: li ha misurati il primo
#    giro, e stanno in `fasi/10-multi-tenant-e-il-budget.md` §6.4-bis e §6.5.
#
#   | scena                       | fot/s   | byte/fot | byte/s  | GPU render |
#   |-----------------------------|---------|----------|---------|------------|
#   | FERMA (§6.4-bis)            |  0,0245 |    266   |     6,5 |   0,00 %   |
#   | ⚠ CONGELATA (E15, §6.4-bis) |  0,55   |  1 982   | 1 090   |     -      |
#   | desktop vero  (§6.4-bis)    | 18,92   |  5 130   | 97 060  |   3,24 %   |
#   | continuo      (§6.4-bis)    | 41,77   |  1 805   | 75 400  |  10,01 %   |
#   | satura 1080p  (§6.5)        | 38-39   |  5 600   | ~215 000|     -      |
#
# ⛔⛔ E LA COLONNA CHE SEPARA NON E' QUELLA CHE SEMBRAVA — `REVIEWER.md` E15,
#     riprodotto dal vivo il 24 agosto 2026: sui **byte per fotogramma** la
#     scena **sana** fa 1 651-1 805 e la stessa scena **congelata** ne fa
#     **1 982** ⇒ quella grandezza **ordina i due estremi al contrario**, e
#     nessuna soglia poteva separarli.  ⭐ La grandezza che li separa e' il
#     **RITMO** (44,6/s contro 0,55/s).
#   ⇒ La soglia principale delle ferme e' il RITMO, non i byte per fotogramma.
SOGLIA_FERMA_FPS = 2.0
#   ⭐ 3,6 volte sopra l'estremo fermo piu' alto che si conosca (0,55/s, la
#     scena congelata) e 9,5 volte sotto il lavoro piu' leggero che si conosca
#     (18,92/s, il desktop vero).  ⇒ Margine dichiarato da tutt'e due i lati.

# ⭐ E LA SECONDA COLONNA, INDIPENDENTE DALLA PRIMA (`LEZIONI.md` §1.34: *«non
#   dare per scontato quale sia la colonna che avvisa: portane piu' di una»*).
#   I byte al secondo: `[M]` 6,5 B/s da ferma contro 97 000 da desktop vero.
#   ⛔ La soglia sta a 5 000 — **770 volte** sopra l'estremo fermo e **19 volte**
#   sotto il lavoro piu' leggero.
SOGLIA_FERMA_BYTE_S = 5000.0
# ⛔ E le due colonne devono ANDARE D'ACCORDO.  Se una dice «ferma» e l'altra
#    «lavora», il banco **non giudica**: due metri che si contraddicono non
#    fanno una misura, ne fanno mezza — e la meta' che si sceglie e' quella che
#    fa comodo.

# ⭐ La «satura» si giudica sulla SOLLECITAZIONE ARRIVATA, non sul ritmo
#    consegnato.  ⛔ E la ragione e' il risultato stesso di §6.5: all'ottava
#    sessione una satura consegna **1,5 fot/s** — e' il crollo che si sta
#    misurando, non una scena che non morde.  ⇒ Il metro e' quello di 10-b92,
#    `p_scena_viva`: **byte per fotogramma >= 4 000** (`B.BYTE_VIVI`), piu' il
#    fatto, indipendente, che il processo della scena sia **vivo**.

RUOLI = {
    "S": ("satura", "scena a schermo intero, `--movimento pieno`: ventiquattro "
                    "bande che scorrono, schermo intero danneggiato a ogni "
                    "fotogramma"),
    "F": ("ferma", "⛔ NESSUNA scena: il desktop GNOME e basta.  `[M]` §6.4-bis: "
                   "un fotogramma in 40,8 s, GPU ZERO, RC6 100 %, GT 0 MHz"),
    "T": ("strappi", "il «desktop vero» di §6.4-bis: scena in FINESTRA "
                     "1280x720 `--movimento pieno`, con accanto finestre vere"),
}

# ⛔ Il numero di fotogrammi sotto il quale non si riduce niente: e' quello di
#    09-b70 (30), e per le FERME non si applica — una ferma **e'** una sessione
#    con pochi fotogrammi, e pretenderne trenta vorrebbe dire non poterla
#    misurare mai.  ⇒ Per le ferme la riduzione e' quella di `riduci_finestra`
#    qui sotto, che divide per la DURATA CHIESTA e non per l'intervallo fra il
#    primo e l'ultimo fotogramma.
MIN_FOT_RITARDO = 3     # sotto tre fotogrammi un ritardo mediano non e' una
                        # mediana: e' un aneddoto.  ⇒ `None`.


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA RIDUZIONE DELLA FINESTRA — e ⛔ NON e' quella di 09-b70, apposta
# ═══════════════════════════════════════════════════════════════════════════
def riduci_finestra(giornale, t0, t1):
    """I numeri di una finestra, ⛔ divisi per la **durata chiesta**.

    ⛔⛔ PERCHE' NON BASTA `misura()` DI 09-b70, che pure si usa accanto.

    `misura()` divide i fotogrammi per l'intervallo **fra il primo e l'ultimo**,
    e si rifiuta sotto i 30 fotogrammi.  Sono due scelte giuste per una sessione
    che lavora e ⛔ **sbagliate tutt'e due per una sessione ferma**:

      · una ferma fa `[M]` **un** fotogramma in 40,8 s ⇒ `misura()` direbbe
        *«non ho niente da giudicare»*, e il banco perderebbe **proprio il dato
        che cerca** — che quella sessione era ferma;
      · e con due soli fotogrammi l'intervallo fra il primo e l'ultimo puo'
        essere di mezzo secondo ⇒ *«4 fotogrammi/s»* per una sessione che in
        quaranta secondi ne ha fatti due.  ⚠ Un numero plausibile e falso, che
        e' peggio di un rifiuto.

    ⇒ Qui il denominatore e' **`t1 - t0`**, cioe' la finestra che il banco ha
      chiesto: `[M]` 1 fotogramma in 40,8 s = **0,0245/s**, che e' la verita'.
    ⭐ E la distorsione al rialzo di `misura()` — **+1/(N−1)**, +0,5 % a 200
      fotogrammi — qui non c'e' per costruzione.

    ⚠ I due numeri si stampano **tutt'e due** (`fps` di 09-b70 accanto a
      `fps_finestra` mio): chi confronta con §6.5 usa il primo, chi giudica un
      ruolo usa il secondo.
    """
    secondi = (t1 - t0) / 1000.0
    if secondi <= 0:
        return {"esito_finestra": "⛔ NON GIUDICO — la finestra e' lunga "
                                  "%.3f s" % secondi}
    # ⛔⛔ LA CHIAVE SI CHIAMA `esito_finestra`, E NON E' UN DETTAGLIO DI NOME.
    #
    #     Questa riduzione si FONDE con quella di 09-b70 (`n.update(...)` in
    #     `fetta_mista`), e 09-b70 mette in `esito` la parola **«misurato»**:
    #     e' quella che `ha_misurato()` guarda, ed e' il cancello di
    #     `p_scena_viva`, `p_ritmo`, `p_quota_chiavi` e `p_I1` di 10-b92.
    #   ⛔ La prima stesura scriveva `esito` anche qui ⇒ dopo la fusione
    #     `ha_misurato()` era **sempre falso**, e quei quattro predicati
    #     tacevano tutti insieme: nessun rosso, nessun giallo, nessuna riga.
    #     ⚠ E' `REVIEWER.md` E14 in casa mia — *«il banco tace invece di dare
    #       rosso»* — trovata rileggendo il codice PRIMA di misurare, non dopo.
    n = {"esito_finestra": "finestra letta", "finestra_s": round(secondi, 3),
         "fotogrammi_finestra": len(giornale)}
    if not giornale:
        # ⛔ ZERO FOTOGRAMMI E' UN DATO, NON UN'ASSENZA — ed e' precisamente il
        #    dato che una sessione ferma produce.  ⚠ Ma i byte per fotogramma
        #    di zero fotogrammi **non esistono**: `None`, non zero
        #    (`CODER.md` §3.10).
        n.update({"fps_finestra": 0.0, "byte_finestra": 0,
                  "byte_al_secondo": 0.0, "byte_per_fotogramma_f": None,
                  "chiavi_finestra": 0, "ritardo_f": None, "numeri_f": None})
        return n
    byte = sum(f["byte"] for f in giornale)
    n["fps_finestra"] = round(len(giornale) / secondi, 4)
    n["byte_finestra"] = byte
    n["byte_al_secondo"] = round(byte / secondi, 1)
    n["byte_per_fotogramma_f"] = int(byte / len(giornale))
    n["chiavi_finestra"] = sum(1 for f in giornale if f["chiave"])
    # ⛔ Sotto tre fotogrammi il ritardo mediano non si dichiara: `None`.
    n["ritardo_f"] = (B.ritardi(giornale)
                      if len(giornale) >= MIN_FOT_RITARDO else None)
    num = sorted(f["numero"] for f in giornale)
    n["numeri_f"] = [num[0], num[-1]]
    return n


def tara_finestra(dillo=True):
    """⛔ IL METRO SI TARA PRIMA — `LEZIONI.md` §1.33, e qui il valore iniettato
       e' **il numero misurato di una sessione ferma vera**.

    Si inietta il caso di §6.4-bis: **1 fotogramma in 40,8 s da 266 byte**, e si
    pretende `0,0245/s`.  ⭐ Poi il caso opposto — 900 fotogrammi in 30 s da
    5 600 byte — e si pretende `30,00/s` e `168 000 B/s`.
    ⚠ E il terzo caso e' quello che 09-b70 **non** sa fare: due fotogrammi a
      mezzo secondo l'uno dentro una finestra di 40 s.  `misura()` direbbe
      «4/s»; qui dev'essere **0,05/s**.
    """
    guai = []
    # ── caso A: la sessione ferma vera di §6.4-bis ──
    g = [{"numero": 7, "chiave": True, "tipo": 0x0301, "codec": 3,
          "l": 1920, "a": 1080, "byte": 266,
          "istante_us": int((1000.0 - 10.0) * 1000), "arrivo_ms": 1000.0}]
    a = riduci_finestra(g, 500.0, 500.0 + 40800.0)
    if abs(a["fps_finestra"] - 0.0245) > 0.0005:
        guai.append("ferma: atteso 0,0245/s (1 fotogramma in 40,8 s), visto %s"
                    % a["fps_finestra"])
    if a["byte_per_fotogramma_f"] != 266:
        guai.append("ferma: attesi 266 B/fot, visti %s"
                    % a["byte_per_fotogramma_f"])
    if a["ritardo_f"] is not None:
        guai.append("ferma: con UN fotogramma il ritardo mediano deve essere "
                    "`None`, non un numero — visto %s" % (a["ritardo_f"],))
    # ── caso B: la sessione satura ──
    g = B._fab(900, fps=30.0, byte=5600, chiave_ogni=0, primo_numero=100,
               ritardo_ms=10.0, t0=1000.0)
    b = riduci_finestra(g, 1000.0, 1000.0 + 30000.0)
    if abs(b["fps_finestra"] - 30.0) > 0.01:
        guai.append("satura: attesi 30,00/s (900 in 30 s), visti %s"
                    % b["fps_finestra"])
    if abs(b["byte_al_secondo"] - 168000.0) > 1.0:
        guai.append("satura: attesi 168 000 B/s, visti %s" % b["byte_al_secondo"])
    # ── caso C: ⛔ quello su cui 09-b70 sbaglierebbe ──
    g = B._fab(2, fps=2.0, byte=300, chiave_ogni=0, primo_numero=1,
               ritardo_ms=10.0, t0=1000.0)
    c = riduci_finestra(g, 1000.0, 1000.0 + 40000.0)
    if abs(c["fps_finestra"] - 0.05) > 0.001:
        guai.append("due fotogrammi a mezzo secondo l'uno in una finestra di "
                    "40 s: atteso 0,05/s, visto %s  ⚠ e 09-b70 direbbe 4,00/s"
                    % c["fps_finestra"])
    if dillo and not guai:
        _ok("il metro della finestra e' tarato: 1 fot/40,8 s → %.4f/s · 900 "
            "fot/30 s → %.2f/s e %.0f B/s · 2 fot a 0,5 s in 40 s → %.3f/s "
            "(⚠ 09-b70 direbbe 4,00/s)"
            % (a["fps_finestra"], b["fps_finestra"], b["byte_al_secondo"],
               c["fps_finestra"]))
    return (not guai), guai


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA FETTA DI UNA MISCELA — una lettura sola, e ne escono TUTTI i numeri
# ═══════════════════════════════════════════════════════════════════════════
def fetta_mista(i, t0, t1, durata, con_giornale=False):
    """Il giornale di s`i` fra `t0` e `t1`, ridotto in DUE modi.

    ⛔ Perche' non si chiama `B.fetta()` e basta: quella butta il giornale
       grezzo appena ridotto, e qui serve **due volte** — una per la riduzione
       di 09-b70 (che rende i numeri confrontabili con §6.5) e una per la
       riduzione a finestra (che e' l'unica che sappia misurare una ferma).
       ⭐ Ma l'attrezzo che gira sulla macchina e' **il suo**, `10-b92-fetta.py`,
       spedito dal suo `terreno()`: qui non si riscrive nessun ritaglio.
    """
    rc, out, err = B.root("python3 %s/10-b92-fetta.py %s %.3f %.3f | gzip | "
                          "base64 -w0" % (B.LAV, B.giornale_di(i), t0, t1), 300)
    try:
        crudo = json.loads(gzip.decompress(base64.b64decode(out.strip())))
    except Exception as e:
        return {"esito": "⛔ la fetta non si e' letta: %s — %s"
                         % (e, (out + err)[-160:])}
    if crudo.get("esito") != "letto":
        return {"esito": crudo.get("esito", "?")}
    g = crudo["giornale"]
    # 1 · la riduzione di 09-b70, tale e quale — cosi' i numeri di una `S` si
    #     confrontano con quelli di §6.5 senza conversioni.
    n = B.B70.misura(g, durata, scaldata_s=0.0)
    n["ritardo"] = B.ritardi(g)
    n["righe_nel_file"] = crudo.get("righe_nel_file")
    if g:
        num = sorted(f["numero"] for f in g)
        n["numeri"] = [num[0], num[-1]]
    # 2 · la riduzione a finestra, che c'e' SEMPRE — anche a zero fotogrammi.
    n.update(riduci_finestra(g, t0, t1))
    if con_giornale:
        n["giornale"] = g
    return n


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LE SCENE DEI RUOLI — e `F` non ne ha nessuna, che e' il punto
# ═══════════════════════════════════════════════════════════════════════════
def _ambiente(n, u):
    """⛔⭐ L'AMBIENTE DI UNA SESSIONE STA IN UN POSTO SOLO — 25 agosto 2026.

    Era scritto a mano qui, un'altra volta piu' sotto (le scene del risveglio),
    in `10-b92-dieci.py` e in `10-b89-scena.sh`: **quattro copie**, ⛔ e a
    tutt'e quattro mancavano le tre variabili senza cui **Nautilus non parte
    affatto** — cioe' il braccio «desktop vero» misurava uno schermo vuoto.
    Il riquadro coi numeri sta in `banchi/10-ambiente-sessione.sh`.

    ⚠ Il frammento si compone QUI SUL PORTATILE, leggendo l'unico file: non
      serve spedirlo, e non c'e' un giro di `ssh` in piu' per riga lanciata.
    ⛔ E se il file non c'e', si ALZA: un ambiente composto a meta' non da'
      rosso, da' un desktop vuoto che sembra un desktop.
    """
    p = subprocess.run(
        ["bash", os.path.join(QUI, "10-ambiente-sessione.sh"), str(n), u],
        capture_output=True, text=True)
    frammento = p.stdout.strip()
    if p.returncode != 0 or "XDG_SESSION_TYPE=wayland" not in frammento:
        raise SystemExit("⛔ non ho potuto comporre l'ambiente della sessione "
                         "da «10-ambiente-sessione.sh»: %s"
                         % (p.stderr.strip() or frammento)[:200])
    return frammento


def _giu(n, u, comando, log):
    """Accende `comando` DENTRO la sessione di `u`.

    ⛔ Il redirect vive nella shell di ROOT (in una cartella di root la shell
       di `nicfio` non potrebbe scrivere, e il processo morirebbe col registro
       VUOTO — la ragione per cui `10-b89-scena.sh` esiste)."""
    return B.root(
        "setsid nohup %s %s >> %s 2>&1 & echo avviato"
        % (_ambiente(n, u), comando, log), 90)


def finestre_vere(i):
    """⭐ Le finestre vere del «desktop vero» di §6.4-bis: `nautilus` e
       `gnome-terminal`.  ⛔ Non si dichiarano aperte perche' il comando e'
       partito: si CONTA chi e' vivo (`LEZIONI.md` §1.9)."""
    n, u = B.uid(i), B.utente(i)
    log = "%s/finestre-%d.log" % (B.LAV, i)
    for a in ("nautilus", "gnome-terminal"):
        _giu(n, u, a, log)
    time.sleep(5.0)
    rc, out, _ = B.root("pgrep -u %d -c -f 'nautilu[s]|gnome-termina[l]' "
                        "2>/dev/null || echo 0" % n)
    t = out.strip().splitlines()[-1] if out.strip() else "0"
    return int(t) if t.isdigit() else 0


def accendi_ruolo(i, ruolo):
    """Accende la scena del ruolo di s`i`.  ⛔ Torna `None` se NON e' partita.

    ⭐ Non riscrive `accendi_scena` di 10-b92 per capriccio: gliene servono due
      cose che quella non ha, e tutt'e due sono di isolamento o di ruolo —
        · lo `shm` e' `/10b98-*`, non `/10b92-*` (⛔ `/dev/shm` e' UNO su tutta
          la macchina, e gli utenti di questo giro sono **condivisi**: due
          agenti sullo stesso nome si leggerebbero i disegni a vicenda senza che
          nessuno dei due dia rosso);
        · il ruolo `T` vuole `--finestra`, che `accendi_scena` non passa.
      ⚠ Il resto — `uscita_del`, i tre tentativi, il registro conservato — e'
        preso da la', e la ragione dei tre tentativi e' misurata: `[M]` 24
        agosto 2026 la scena di s1 non parti' perche' il palco era nato due
        secondi prima e il compositore non era ancora pronto a dare l'uscita.
    """
    if ruolo == "F":
        # ⛔ E QUI NON SI ACCENDE NIENTE, ED E' IL PUNTO DEL BANCO.  Una `F` e'
        #    una sessione RCP aperta su un desktop GNOME **fermo**: se le si
        #    desse una scena «leggera» non sarebbe piu' una ferma, sarebbe una
        #    terza cosa senza estremo noto a cui tararla.
        return "SENZA-SCENA"
    n, u = B.uid(i), B.utente(i)
    log = "%s/scena-%d.log" % (B.LAV, i)
    for tentativo in range(3):
        if ruolo == "S":
            usc = B.uscita_del(i)
            if not usc:
                time.sleep(3.0)
                continue
            comando = ("%s --uscita %s --movimento pieno --shm %s-%d "
                       "--giro b98-%d" % (B.SCENA_BIN, usc, SHM, i, i))
            eti = usc
        else:                                   # T — in finestra
            # ⚠ Anche in finestra si chiede prima l'uscita: non serve al
            #   comando, serve a sapere che il compositore RISPONDE.  Un
            #   `--finestra` lanciato su un compositore non pronto muore in
            #   silenzio, e la sessione resterebbe «viva e ferma» dentro il
            #   conto di una miscela che la dichiara «a strappi».
            if not B.uscita_del(i):
                time.sleep(3.0)
                continue
            comando = ("%s --finestra %s --movimento pieno --shm %s-%d "
                       "--giro b98t-%d" % (B.SCENA_BIN, FINESTRA_T, SHM, i, i))
            eti = "finestra %s" % FINESTRA_T
        _giu(n, u, comando, log)
        time.sleep(2.5)
        rc, out, _ = B.root("pgrep -u %d -f '04-b30-scen[a]' | head -1" % n)
        if out.strip():
            return eti
        rc, out, _ = B.root("tail -3 %s 2>/dev/null || true" % log)
        _dub("⚠ la scena «%s» di s%d non e' partita al tentativo %d — dice: %s"
             % (ruolo, i, tentativo + 1, out.strip()[-160:]))
        time.sleep(3.0)
    return None


def chi_disegna(quanti):
    """⭐ CHI E' VIVO E CHI DISEGNA, in UNA domanda sola — ⛔ e la differenza
       con `chi_c_e` di 10-b92 e' UNA e vale il file.

    `chi_c_e` cerca `04-b30-scena --uscita`: e' giusto per lui, che ha solo
    scene a schermo intero.  ⛔ Qui il ruolo `T` gira **in finestra**, senza
    `--uscita` ⇒ `chi_c_e` lo direbbe **fermo**.  E non darebbe rosso: darebbe
    una miscela in cui le sessioni «a strappi» risultano ferme, cioe' un numero
    plausibile per una scena che non e' quella.
    ⇒ Qui si cerca `04-b30-scen[a]` e basta, e la classe di caratteri non e' un
      vezzo: senza, `pgrep -f` combacia con la propria riga di comando.
    """
    righe = []
    for i in range(1, quanti + 1):
        righe.append(
            "printf '%%d ' %d; "
            "pgrep -f -- '%s' >/dev/null 2>&1 && printf vivo || printf morto; "
            "printf ' '; "
            "pgrep -u %d -f '04-b30-scen[a]' >/dev/null 2>&1 && "
            "printf disegna || printf ferma; printf ' '; "
            "pgrep -u %d -c -f 'nautilu[s]|gnome-termina[l]' 2>/dev/null "
            "|| printf 0; printf '\\n'"
            % (i, B.cerca_giornale(i), B.uid(i), B.uid(i)))
    rc, out, _ = B.root(" ; ".join(righe), 240)
    vive, scene, finestre = {}, {}, {}
    for r in out.splitlines():
        p = r.split()
        if len(p) >= 3 and p[0].isdigit():
            k = int(p[0])
            vive[k] = (p[1] == "vivo")
            scene[k] = (p[2] == "disegna")
            finestre[k] = int(p[3]) if len(p) > 3 and p[3].isdigit() else 0
    # ⛔ Chi non ha risposto NON e' «morto»: e' «non lo so», e si dichiara.
    manca = [i for i in range(1, quanti + 1) if i not in vive]
    return vive, scene, finestre, manca


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA GPU PER SESSIONE — e il delta si fa SOLO sui contesti comuni
# ═══════════════════════════════════════════════════════════════════════════
def gpu_per_uid(a, b):
    """I motori della GPU **per uid**, fra due fotografie.

    ⛔ Si sommano SOLO i contesti presenti in tutt'e due, per la ragione scritta
       nel riquadro di `fra()` di 10-b92: i `drm-engine-*` sono cumulativi **per
       contesto**, e sottrarre due somme prese su platee diverse non da' il
       lavoro fatto — da' il lavoro fatto meno tutto il cumulativo che se n'e'
       andato in mezzo.  `[M]` 24 agosto: `render −76,4 %` per questo.
    ⚠ Un contesto che NASCE fra le due fotografie porta dentro il cumulativo
      dall'inizio dei tempi: si conta e si dichiara, non si somma.
    """
    ga, gb = (a or {}).get("gpu") or {}, (b or {}).get("gpu") or {}
    ca, cb = ga.get("per_contesto") or {}, gb.get("per_contesto") or {}
    ua = ga.get("contesti_uid") or {}
    ub = gb.get("contesti_uid") or {}
    if not ub:
        # ⛔ «Non ho la mappa» non e' «zero per tutti»: e' `None`, e chi legge
        #    deve poterlo distinguere.
        return None, {"esito": "⛔ la sonda non porta `contesti_uid`: NON so di "
                               "chi siano i contesti"}
    secondi = (b["t_ms"] - a["t_ms"]) / 1000.0
    if secondi <= 0:
        return None, {"esito": "⛔ le due fotografie non sono in ordine"}
    comuni = set(ca) & set(cb)
    per_uid, negativi = {}, {}
    for cid in comuni:
        u = ub.get(cid, ua.get(cid))
        if u is None:
            continue
        d = per_uid.setdefault(str(u), {})
        for m in set(list(ca[cid]) + list(cb[cid])):
            d[m] = d.get(m, 0) + cb[cid].get(m, 0) - ca[cid].get(m, 0)
    fuori = {}
    for u, mot in per_uid.items():
        fuori[u] = {m: round(100.0 * ns / 1e9 / secondi, 2)
                    for m, ns in mot.items()}
        for m, v in fuori[u].items():
            if v < -0.05:
                negativi.setdefault(u, {})[m] = v
    nota = {"esito": "misurato", "secondi": round(secondi, 2),
            "contesti_comuni": len(comuni),
            "nati": len(set(cb) - set(ca)), "morti": len(set(ca) - set(cb)),
            "negativi": negativi}
    if negativi:
        # ⛔ Un motore non puo' lavorare per un tempo negativo.  ⇒ Il metro non
        #    e' quello che credo, e la riga NON si giudica.
        nota["esito"] = ("⛔ NON GIUDICO — occupazione NEGATIVA per uid: %s"
                         % json.dumps(negativi))
    return fuori, nota


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I PREDICATI DEI RUOLI — e ne torna (passa, perche), come in 10-b92
# ═══════════════════════════════════════════════════════════════════════════
_si, _no, _muto = B._si, B._no, B._muto


def p_ferma_e_ferma(n, disegna):
    """⛔⛔ IL PREDICATO CHE RENDE VALIDA UNA MISCELA.

    *«Una miscela in cui le ferme non erano ferme non e' una miscela: e' la
    scena uniforme di prima, con un nome nuovo.»*

    ⇒ Tre prove, e vengono da **tre parti diverse**:
      1. il RITMO, dal giornale del cliente — sotto `SOGLIA_FERMA_FPS`;
      2. i BYTE AL SECONDO, dallo stesso giornale ma da un'altra colonna;
      3. ⭐ la SCENA, dalla macchina: `pgrep` non deve trovare nessun
         `04-b30-scena` per quell'utente.

    ⛔⛔ E BASTA CHE **UNA** DELLE TRE DICA «SI MUOVE»: una sessione ferma
        dev'essere ferma su **tutt'e tre**, o non e' una ferma.
    ⚠ La prima stesura, davanti a due colonne che si contraddicevano, si
      rifiutava di giudicare.  ⛔ Era sbagliato, e il caso che l'ha mostrato e'
      l'orologio di GNOME che batte: **3 fot/s da 900 byte** — il ritmo dice
      «lavora», i byte (2 700 B/s) dicono «ferma».  ⇒ Un «non giudico» avrebbe
      lasciato passare per FERMA una sessione che disegna tre volte al secondo,
      ed e' esattamente la miscela finta che questo predicato esiste per
      smascherare.  ⭐ Il «non giudico» resta per **«non ho letto»**, che e'
      un'altra cosa (`CODER.md` §3.10).
    """
    if not n or n.get("fps_finestra") is None:
        return _muto("non misurato: nessuna finestra letta per questa sessione")
    if disegna:
        return _no("⛔ LA MISCELA NON E' VALIDA — questa sessione e' dichiarata "
                   "FERMA e sulla macchina c'e' un `04-b30-scena` a suo nome: "
                   "sta disegnando.  ⇒ Non e' una miscela, e' la scena uniforme "
                   "con un nome nuovo")
    fps = n["fps_finestra"]
    bs = n["byte_al_secondo"]
    dett = ("%.4f fot/s · %.0f byte/s · %s fotogrammi in %.1f s · %s B/fot"
            % (fps, bs, n["fotogrammi_finestra"], n["finestra_s"],
               n["byte_per_fotogramma_f"]))
    q_fps = fps <= SOGLIA_FERMA_FPS
    q_byte = bs <= SOGLIA_FERMA_BYTE_S
    if not (q_fps and q_byte):
        chi = []
        if not q_fps:
            chi.append("il RITMO (%.4f/s, sopra %.1f)" % (fps, SOGLIA_FERMA_FPS))
        if not q_byte:
            chi.append("i BYTE (%.0f B/s, sopra %.0f)"
                       % (bs, SOGLIA_FERMA_BYTE_S))
        return _no("⛔ LA MISCELA NON E' VALIDA — una «ferma» che SI MUOVE, e a "
                   "smascherarla e' %s%s.  %s  ⇒ Le soglie sono tarate su `[M]` "
                   "0,0245/s e 0,55/s da un lato e 18,92/s dall'altro; ⭐ basta "
                   "che UNA colonna dica «si muove»"
                   % (" e ".join(chi),
                      "" if len(chi) > 1 else " (⚠ l'altra colonna diceva "
                                              "«ferma»: e non basta)", dett))
    return _si("ferma davvero: %s — e nessun `04-b30-scena` a suo nome sulla "
               "macchina" % dett)


def p_satura_satura(n, disegna):
    """⛔ Una «satura» che NON satura ⇒ la miscela non e' valida.

    ⭐ E il metro e' la SOLLECITAZIONE ARRIVATA, non il ritmo consegnato: a
      otto sessioni una satura consegna `[M]` **1,5 fot/s** — ed e' il crollo
      che si sta misurando, non una scena che non morde.  ⇒ Si guarda che il
      processo della scena sia vivo, e che i fotogrammi PESINO (`p_scena_viva`
      di 10-b92, soglia 4 000 byte, tarata su 242-283 e 2 448 e 3 801).
    """
    if not disegna:
        return _no("⛔ LA MISCELA NON E' VALIDA — questa sessione e' dichiarata "
                   "SATURA e sulla macchina NON c'e' nessun `04-b30-scena` a "
                   "suo nome: la scena e' morta, e i suoi numeri sarebbero "
                   "quelli di una ferma")
    if not B.ha_misurato(n):
        # ⛔ Sotto i 30 fotogrammi 09-b70 si rifiuta.  Ma la finestra c'e'
        #    sempre: se la scena e' viva e i pochi fotogrammi arrivati PESANO,
        #    la sollecitazione e' arrivata lo stesso e lo si dice.
        if n and n.get("byte_per_fotogramma_f") is not None:
            b = n["byte_per_fotogramma_f"]
            if b >= B.BYTE_VIVI:
                return _si("⚠ pochi fotogrammi (%s in %.1f s: %.2f/s) ma "
                           "PESANTI — %d B/fot: la scena morde, e il ritmo "
                           "basso e' il RISULTATO, non una scena spenta"
                           % (n["fotogrammi_finestra"], n["finestra_s"],
                              n["fps_finestra"], b))
            return _no("⛔ LA MISCELA NON E' VALIDA — %d byte per fotogramma, "
                       "sotto i %d: questa «satura» non satura"
                       % (b, B.BYTE_VIVI))
        return _muto("non misurato, e nemmeno un fotogramma nella finestra: "
                     "NON so dire se saturava")
    return B.p_scena_viva(n)


def p_strappi(n, disegna, finestre):
    """Il ruolo `T`, il «desktop vero» di §6.4-bis — `[M]` 5 130 B/fot, 18,92/s.

    ⚠ E qui il banco dichiara un limite invece di nasconderlo: `T` e `S` NON si
      distinguono per una soglia.  Il desktop vero fa **piu'** byte per
      fotogramma della scena satura (`[M]` 5 130 contro 1 805 in §6.4-bis) ⇒
      nessuna soglia sui byte li separa, ed e' `REVIEWER.md` E15 un'altra volta.
    ⇒ Quel che si giudica di un `T` e' che **abbia sollecitato**; quel che lo
      distingue da un `S` si dichiara — la scena e' in **finestra 1280x720**,
      cioe' il 44 % dell'area, con accanto `finestre` finestre vere.
    """
    if not disegna:
        return _no("⛔ LA MISCELA NON E' VALIDA — «a strappi» senza nessun "
                   "`04-b30-scena` a suo nome: la scena in finestra e' morta")
    if not B.ha_misurato(n):
        if n and n.get("byte_per_fotogramma_f") is not None:
            return _muto("⚠ %s fotogrammi in %.1f s (%.2f/s, %s B/fot): sotto "
                         "il minimo di 09-b70, giudico solo la finestra"
                         % (n["fotogrammi_finestra"], n["finestra_s"],
                            n["fps_finestra"], n["byte_per_fotogramma_f"]))
        return _muto("non misurato")
    esito = B.p_scena_viva(n)
    if esito[0] is not True:
        return esito
    return _si("%s · scena in FINESTRA %s (⚠ il 44 %% dell'area di una `S`) · "
               "%d finestre vere accanto  ⇒ §6.4-bis: `[M]` 5 130 B/fot, "
               "18,92 fot/s" % (esito[1], FINESTRA_T, finestre))


def p_ferma_costa_zero(gpu_u, uid_suo, gt):
    """⭐ IL MECCANISMO ACCANTO AL SINTOMO, dal lato della macchina.

    `[M]` §6.4-bis: una sessione ferma costa **GPU ZERO** — RC6 100 %, GT
    0 MHz.  ⇒ Se una sessione dichiarata ferma consuma GPU, o non era ferma o il
    prodotto le sta facendo pagare qualcosa che non ha chiesto.  ⛔ In tutt'e
    due i casi non e' un dettaglio: e' **la premessa del budget**.
    ⚠ Soglia a **1,0 %** di tempo di parete per motore: `[M]` il desktop vero
      piu' leggero che si conosca costa 3,24 % di render, e la ferma 0,00 %.
    """
    if gpu_u is None:
        return _muto("la GPU per sessione non si e' letta")
    mot = gpu_u.get(str(uid_suo))
    if mot is None:
        # ⭐ Nessun contesto DRM comune per quell'uid: e' **compatibile** con
        #   una sessione ferma, ma non e' una misura di zero.  ⇒ Non giudico, e
        #   lo dico.
        return _muto("⚠ nessun contesto DRM comune alle due fotografie per uid "
                     "%d: NON e' «zero», e' «non ho misurato»" % uid_suo)
    peggio = max(mot.values()) if mot else 0.0
    if peggio > 1.0:
        return _no("⛔ una sessione dichiarata FERMA costa GPU: %s (GT %s MHz) "
                   "— `[M]` §6.4-bis dice 0,00 %%"
                   % (json.dumps(mot), (gt or {}).get("act_mhz")))
    return _si("costa GPU ~zero, come §6.4-bis: %s (GT %s MHz, RC6 %s %%)"
               % (json.dumps(mot), (gt or {}).get("act_mhz"),
                  (gt or {}).get("rc6_pc")))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA RICETTA
# ═══════════════════════════════════════════════════════════════════════════
def leggi_ricetta(testo):
    """`SFFFF` oppure `S,F,F,F,F` → ['S','F','F','F','F'].  ⛔ O `SystemExit`."""
    grezzo = [x.strip().upper() for x in testo.replace(",", " ").split()]
    if len(grezzo) == 1 and len(grezzo[0]) > 1:
        grezzo = list(grezzo[0])
    if not grezzo:
        raise SystemExit("⛔ ricetta vuota")
    for r in grezzo:
        if r not in RUOLI:
            raise SystemExit("⛔ ruolo «%s» sconosciuto: %s"
                             % (r, "/".join(sorted(RUOLI))))
    return grezzo


def nome_miscela(ricetta):
    return "".join(ricetta) + "  (%s)" % " + ".join(
        "%d %s" % (ricetta.count(r), RUOLI[r][0])
        for r in ("S", "T", "F") if ricetta.count(r))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LA MISCELA — la salita di 10-b92, con un RUOLO al posto di un gradino
# ═══════════════════════════════════════════════════════════════════════════
def miscela(ricetta, durata, doppia, resta):
    """⭐ La forma e' quella di `salita()` di 10-b92, e non e' un caso: la
       domanda *«chi paga quando arriva l'ennesimo»* si risponde **solo**
       appaiando la stessa sessione con se stessa, gradino per gradino.
       ⇒ Qui il gradino `g` aggiunge una sessione **col ruolo `ricetta[g-1]`**,
       e tutto il resto — l'ancora, le fotografie, i predicati, i conti del
       server — sono le righe di 10-b92, chiamate.
    """
    quanti = len(ricetta)
    esiti = {"ricetta": ricetta, "quanti": quanti, "durata_s": durata,
             "tela": B.TELA, "codec": B.CODEC_CHIESTO, "gradini": []}
    fette, prima_volta = {}, {}
    rossi, muti = [], []
    ruolo_di = {i: ricetta[i - 1] for i in range(1, quanti + 1)}
    finestre_di = {}

    _log("LA MISCELA — %s · %s a testa · gradini da %d s a regime"
         % (nome_miscela(ricetta), B.TELA, durata))
    for r in ("S", "T", "F"):
        if r in ricetta:
            _inf("  %s = %-8s %s" % (r, RUOLI[r][0], RUOLI[r][1]))
    _inf("⛔ le cure della fase 9 sono ACCESE per predefinito (`CODER.md` "
         "§2-bis).  Questo banco NON le spegne e non confronta col passato")
    _inf("⛔ i clienti girano SULLA MACCHINA DI PROVA: il filo e' `lo`, non una "
         "rete vera.  Il loro costo si misura a parte")

    for g in range(1, quanti + 1):
        ruolo = ruolo_di[g]
        _log("GRADINO %d/%d — arriva s%d (%s) col ruolo «%s» %s"
             % (g, quanti, g, B.utente(g), ruolo, RUOLI[ruolo][0].upper()))
        t_apre = time.time()
        aperta, detto = B.apri_sessione(g, resta)
        ms_apre = int(1000 * (time.time() - t_apre))
        if not aperta:
            # ⛔ ROSSO, E LA MISCELA SI FERMA.  Continuare contandone una di
            #    meno vorrebbe dire scrivere «1 satura + 8 ferme» sotto un
            #    numero che ne aveva sette.
            _ko(detto)
            esiti["gradini"].append({"gradino": g, "aperta": False,
                                     "perche": detto, "ruolo": ruolo})
            rossi.append("gradino %d · la sessione non si apre" % g)
            esiti["fermata_al_gradino"] = g
            break
        _ok("s%d aperta in %d ms (⚠ tetto, non cronometro) — %s"
            % (g, ms_apre, detto))
        esiti.setdefault("apertura_ms", {})[g] = ms_apre
        eti = accendi_ruolo(g, ruolo)
        if eti is None:
            _ko("⛔ la scena «%s» di s%d non parte: quella sessione NON si "
                "giudica finche' non riparte" % (ruolo, g))
            muti.append("gradino %d · la scena di s%d non parte" % (g, g))
        else:
            _inf("scena di s%d: %s" % (g, eti))
        if ruolo == "T":
            finestre_di[g] = finestre_vere(g)
            _inf("finestre vere di s%d: %d (⚠ se 0, il «desktop vero» e' la "
                 "sola scena in finestra, e vale meno di §6.4-bis)"
                 % (g, finestre_di[g]))
        provenienze, posti = B.mappa_provenienze()

        for etichetta, quanto in ([("normale", durata)] +
                                  ([("doppia", 2 * durata)]
                                   if (doppia and g == quanti) else [])):
            if etichetta == "doppia":
                _log("⭐ GRADINO %d, SECONDA DURATA (%d s) — `LEZIONI.md` "
                     "§1.32: i giri corti sottostimano" % (g, quanto))
            # ⛔ Le scene che sono morte si riaccendono, o il carico cala a
            #    meta' e al gradino dopo la macchina sembra piu' larga.
            riaccese = []
            _v, _s, _f, _m = chi_disegna(g)
            for i in range(1, g + 1):
                if ruolo_di[i] != "F" and not _s.get(i):
                    if accendi_ruolo(i, ruolo_di[i]):
                        riaccese.append(i)
            if riaccese:
                _dub("⚠ RIACCESE le scene di %s"
                     % ", ".join("s%d" % i for i in riaccese))
            _inf("assestamento %.0f s (apertura, prima chiave, prima tela: si "
                 "tolgono e si dice)" % B.ASSESTAMENTO_S)
            time.sleep(B.ASSESTAMENTO_S)

            # ⛔⛔ L'ANCORA — la porta la SONDA STESSA, ed e' lo stesso confine
            #     per i fotogrammi, la CPU, la GPU, la memoria e il filo.
            f0 = B.sonda(quanti)
            r0 = B.registro_righe()
            if f0 is None or f0.get("t_ms") is None:
                _ko("⛔ non ho l'ancora del gradino %d: NON misuro" % g)
                muti.append("gradino %d · niente ancora" % g)
                continue
            t0 = f0["t_ms"]
            if esiti.get("ultimo_t1") is not None and t0 <= esiti["ultimo_t1"]:
                _ko("⛔ L'ANCORA NON AVANZA: il gradino %d comincia a %.0f e il "
                    "precedente finiva a %.0f — NON misuro"
                    % (g, t0, esiti["ultimo_t1"]))
                rossi.append("gradino %d · l'ancora non avanza" % g)
                break
            time.sleep(quanto)
            f1 = B.sonda(quanti)
            r1 = B.registro_righe()
            if f1 is None or f1.get("t_ms") is None:
                _ko("⛔ l'ancora finale del gradino %d non si legge" % g)
                muti.append("gradino %d · niente ancora finale" % g)
                continue
            t1 = f1["t_ms"]
            esiti["ultimo_t1"] = t1

            d = B.fra(f0, f1, quanti)
            gpu_u, nota_gpu = gpu_per_uid(f0, f1)
            vive, scene, finestre, non_so = chi_disegna(g)
            if non_so:
                _dub("⚠ di %s non ho saputo dire se sono vive: NON le giudico"
                     % ", ".join("s%d" % i for i in non_so))
                for i in non_so:
                    vive[i], scene[i] = True, False
            voce = {"gradino": g, "quale": etichetta, "durata_s": quanto,
                    "t0": t0, "t1": t1, "macchina": d, "vive": vive,
                    "scene": scene, "finestre": finestre, "riaccese": riaccese,
                    "ruoli": {i: ruolo_di[i] for i in range(1, g + 1)},
                    "gpu_per_uid": gpu_u, "gpu_per_uid_nota": nota_gpu,
                    "sessioni": {}, "predicati": []}

            _inf("MACCHINA  CPU %s %% (%s nuclei) · server %s nuclei · clienti "
                 "%s nuclei" % (d.get("cpu_occupata_pc"), d.get("cpu_nuclei"),
                                d.get("cpu_server_nuclei"),
                                d.get("cpu_clienti_nuclei")))
            _inf("MEMORIA   PSS sessioni %s MiB · PSS server %s MiB · PSS "
                 "totale %s MiB (⚠ RSS sommati: %s MiB)"
                 % (d.get("pss_sessioni_mib"), d.get("pss_server_mib"),
                    d.get("pss_totale_mib"),
                    round((d.get("rss_sessioni_mib") or 0)
                          + (d.get("rss_server_mib") or 0), 1)))
            _inf("GPU       %s ⇒ uso della capacita' %s (capacita' %s)"
                 % (json.dumps(d.get("gpu_pc")), json.dumps(d.get("gpu_uso_pc")),
                    json.dumps(d.get("gpu_capacita"))))
            _inf("          GT %s MHz (min %s, max %s) · RC6 %s %% ⛔ "
                 "l'occupazione dipende dalla FREQUENZA (§6.1 §CLOCK, fattore "
                 "3,8)" % ((d.get("gt") or {}).get("act_mhz"),
                           (d.get("gt") or {}).get("min_mhz"),
                           (d.get("gt") or {}).get("max_mhz"),
                           (d.get("gt") or {}).get("rc6_pc")))
            _inf("          %s contesti su %s, di cui %s NON miei · GPU per "
                 "sessione: %s" % (d.get("gpu_clienti"), B.PDEV_BUONO,
                                   d.get("gpu_estranei"),
                                   nota_gpu.get("esito")))

            cpu_satura = (d.get("cpu_occupata_pc") or 0) >= 90.0
            for i in range(1, g + 1):
                if not vive.get(i):
                    voce["sessioni"][i] = {
                        "esito": "⛔ NON HO NIENTE DA GIUDICARE — il cliente %d "
                                 "e' MORTO durante il gradino: i suoi numeri "
                                 "sono None, non zero" % i}
                    _dub("s%-2d  ⛔ il cliente e' morto durante il gradino: "
                         "None, non zero" % i)
                    muti.append("gradino %d · s%d · cliente morto" % (g, i))
                    continue
                n = fetta_mista(i, t0, t1, quanto)
                n["gradino"] = g
                n["ruolo"] = ruolo_di[i]
                voce["sessioni"][i] = n
                if etichetta == "normale":
                    fette[(g, i)] = n
                    if i not in prima_volta and n.get("fps_finestra") is not None:
                        prima_volta[i] = n
                stampa_riga_mista(i, ruolo_di[i], n)

            # ── I predicati ──
            def registra(nome, esito, dove=""):
                passa, perche = esito
                voce["predicati"].append({"predicato": nome, "passa": passa,
                                          "perche": perche})
                (_ok if passa else (_dub if passa is None else _ko))(
                    "%s%s: %s" % (nome, dove, perche))
                marca = "gradino %d%s · %s%s" % (
                    g, "" if etichetta == "normale" else " (doppia)", nome, dove)
                if passa is False:
                    rossi.append(marca)
                elif passa is None:
                    muti.append("%s — %s" % (marca, perche))

            registra("il metro della GPU e' sano", B.p_metro_gpu(d))
            consegnati = sum(x["fotogrammi_finestra"]
                             for x in voce["sessioni"].values()
                             if x.get("fotogrammi_finestra"))
            # ⚠ La codifica si pretende visibile solo se qualcuno la sta
            #   chiedendo: una miscela di sole ferme fa `[M]` zero fotogrammi, e
            #   allora zero sul motore video e' la risposta giusta, non un metro
            #   cieco.
            if any(ruolo_di[i] != "F" for i in range(1, g + 1)):
                registra("il metro della GPU vede la codifica",
                         B.p_gpu_vede_la_codifica(d, consegnati))
            registra("i clienti non sono il collo",
                     B.p_clienti_non_sono_il_collo(d))
            for i in range(1, g + 1):
                n = voce["sessioni"].get(i)
                r = ruolo_di[i]
                dove = " · s%d[%s]" % (i, r)
                if r == "F":
                    registra("⛔ la «ferma» era DAVVERO ferma",
                             p_ferma_e_ferma(n, scene.get(i)), dove)
                    registra("una ferma costa GPU zero",
                             p_ferma_costa_zero(gpu_u, B.uid(i), d.get("gt")),
                             dove)
                elif r == "S":
                    registra("⛔ la «satura» SATURAVA",
                             p_satura_satura(n, scene.get(i)), dove)
                    registra("il ritmo tiene il pavimento", B.p_ritmo(n), dove)
                    registra("niente spirale di chiavi",
                             B.p_quota_chiavi(n), dove)
                else:
                    registra("⛔ «a strappi» sollecitava",
                             p_strappi(n, scene.get(i), finestre.get(i, 0)),
                             dove)
                    registra("niente spirale di chiavi",
                             B.p_quota_chiavi(n), dove)
                if etichetta == "normale":
                    registra("l'ancora del gradino", B.p_ancora(fette, i, g),
                             dove)
                # ⛔⛔ I1: chi era gia' dentro non peggiora.
                if i < g and i in prima_volta:
                    if r == "F":
                        # ⭐ E PER UNA FERMA I1 SI GUARDA DA UN'ALTRA COLONNA.
                        #   Il ritmo di una ferma e' gia' ~0: non puo'
                        #   peggiorare, e un I1 sugli fps direbbe sempre verde.
                        #   ⇒ `LEZIONI.md` §1.34: quale sia la colonna che
                        #     avvisa cambia col fenomeno.  Per una ferma e' il
                        #     RITARDO dei pochi fotogrammi che manda.
                        registra("⛔ I1 — chi era FERMO se ne accorge? "
                                 "(colonna: il RITARDO)",
                                 p_I1_ritardo(prima_volta[i], n, i, g), dove)
                    else:
                        registra("⛔ I1 — chi era gia' dentro NON peggiora",
                                 B.p_I1(prima_volta[i], n, i, g, cpu_satura),
                                 dove)

            voce["server"] = B.conti_server(r0, r1, provenienze)
            if voce["server"].get("posti_occupati") is None:
                voce["server"]["posti_occupati"] = posti
            _inf("SERVER    posti occupati %s · negati %s"
                 % (voce["server"].get("posti_occupati"),
                    len(voce["server"].get("posti_negati") or [])))
            mio_filo, quante = 0.0, 0
            for u, v in sorted((voce["server"].get("per_utente") or {}).items()):
                if "provenienza" in v:
                    mio_filo += v["mbit_s"]
                    quante += 1
            voce["mio_filo_mbit_s"] = round(mio_filo, 2)
            _inf("          ⭐ IL MIO FILO: %.2f Mbit/s su %d sessioni (dai "
                 "contatori QUIC del server; `lo` NON e' mio)"
                 % (mio_filo, quante))
            esiti["gradini"].append(voce)

    return esiti, rossi, muti, fette, prima_volta


def stampa_riga_mista(i, ruolo, n):
    """⛔ Si stampano TUTTE le grandezze: una tabella con una colonna sola non
       e' una misura corta, e' una misura ORIENTATA (`LEZIONI.md` §6.2)."""
    if n.get("fps_finestra") is None:
        _dub("s%-2d[%s] %s" % (i, ruolo, n.get("esito", "?")))
        return
    r = n.get("ritardo_f") or {}
    b70 = ("%6.2f/s" % n["fps"]) if B.ha_misurato(n) else "   —   "
    _inf("s%-2d[%s] %8.3f fot/s finestra (09-b70: %s) · %5s fot · %7s B/fot · "
         "%9.0f B/s · chiavi %3d · ritardo med %s ms p95 %s"
         % (i, ruolo, n["fps_finestra"], b70, n["fotogrammi_finestra"],
            n["byte_per_fotogramma_f"], n["byte_al_secondo"],
            n["chiavi_finestra"], r.get("mediano_ms"), r.get("p95_ms")))


def p_I1_ritardo(primo, adesso, quale, gradino):
    """⭐ I1 PER UNA SESSIONE FERMA — e la colonna NON e' il ritmo.

    `LEZIONI.md` §1.34, scritta il 23 agosto 2026: *«la colonna che avvisa
    cambia col fenomeno»*.  In fase 9 erano le chiavi; nella salita a dieci le
    chiavi sono rimaste a **zero** e a muoversi e' stato il **ritardo**.
    ⛔ Per una sessione ferma il ritmo e' gia' ~0 e non puo' peggiorare: un I1
       sugli fps darebbe **sempre verde**, che e' la forma peggiore — il banco
       che tace.  ⇒ Si guarda il ritardo dei pochi fotogrammi che manda.
    ⚠ E si rifiuta dove non ce ne sono abbastanza: `None`, non zero.
    """
    ra = (primo or {}).get("ritardo_f")
    rb = (adesso or {}).get("ritardo_f")
    if not ra or ra.get("mediano_ms") is None:
        return _muto("s%d: quando e' entrata non ha mandato abbastanza "
                     "fotogrammi per una mediana del ritardo (ne servono %d) — "
                     "⭐ ed e' proprio quel che vuol dire «ferma»"
                     % (quale, MIN_FOT_RITARDO))
    if not rb or rb.get("mediano_ms") is None:
        return _muto("s%d: al gradino %d non ha mandato abbastanza fotogrammi "
                     "per una mediana del ritardo" % (quale, gradino))
    a, b = ra["mediano_ms"], rb["mediano_ms"]
    dett = ("s%d: ritardo mediano %s ms al gradino %s → %s ms al gradino %d "
            "(%+.0f %%) · fotogrammi %s → %s"
            % (quale, a, primo.get("gradino"), b, gradino,
               100.0 * (b - a) / a if a else 0.0,
               primo.get("fotogrammi_finestra"),
               adesso.get("fotogrammi_finestra")))
    if a <= 0:
        return _muto("⚠ ritardo di partenza nullo: non lo so confrontare — %s"
                     % dett)
    if b <= a * (1.0 + B.I1_SICURO):
        return _si(dett)
    return _no("⛔ I1 — CHI ERA FERMO SE NE E' ACCORTO: %s" % dett)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL RISVEGLIO SIMULTANEO — il caso che un budget all'ingresso NON VEDE
# ═══════════════════════════════════════════════════════════════════════════
#
# Dieci sessioni ammesse quando erano ferme, e alle nove del mattino cominciano
# tutte a lavorare.  ⭐ Un budget **prenotato all'ingresso** non lo vede: al
# momento dell'ammissione quelle sessioni costavano `[M]` GPU **zero**.
#
# ⛔ E il metro di questo caso ha una trappola sua, che e' la forma «silenzio
#   invece di rosso» (`REVIEWER.md` E14): se le ferme NON si svegliano davvero,
#   il banco misurerebbe «nessun effetto» — cioe' darebbe al prodotto un buon
#   voto per un risveglio che non e' avvenuto.  ⇒ Prima si PROVA che si sono
#   svegliate, e solo dopo si guarda l'effetto.
BUCKET_MS = 2000.0        # ⚠ due secondi, non uno: a 38 fot/s un bucket da un
                          #   secondo balla di ±3 fotogrammi, e un solo bucket
                          #   basso sarebbe rumore letto come inizio del danno.
CADUTA = 0.85             # sotto l'85 % del suo regime, la sessione e' calata
BUCKET_CONSECUTIVI = 2    # ⛔ e due bucket di fila, o si datano i singhiozzi


def bucket(giornale, t_zero, larghezza_ms, quanti):
    """Il giornale spezzato in bucket a partire da `t_zero`.  ⛔ Un bucket senza
       fotogrammi e' **0 fotogrammi**, che qui e' un dato (la sessione taceva) —
       ma i suoi byte per fotogramma restano `None`."""
    fuori = []
    for k in range(quanti):
        a = t_zero + k * larghezza_ms
        b = a + larghezza_ms
        dentro = [f for f in giornale if a <= f["arrivo_ms"] < b]
        v = {"k": k, "da_ms": round(k * larghezza_ms), "quanti": len(dentro),
             "fps": round(len(dentro) / (larghezza_ms / 1000.0), 2)}
        if dentro:
            v["byte_per_fotogramma"] = int(
                sum(f["byte"] for f in dentro) / len(dentro))
            rit = sorted(f["arrivo_ms"] - f["istante_us"] / 1000.0
                         for f in dentro)
            v["ritardo_ms"] = round(statistics.median(rit), 1)
        else:
            v["byte_per_fotogramma"] = None
            v["ritardo_ms"] = None
        fuori.append(v)
    return fuori


def quando_cade(bucket_i, base_fps, quota=CADUTA, consecutivi=BUCKET_CONSECUTIVI):
    """⭐ QUANDO comincia il danno, in ms dal risveglio.  ⛔ `None` se non cade.

    ⚠ `None` qui vuol dire **«non e' caduta»**, ed e' un risultato; il caso «non
      ho misurato» e' un altro e sta piu' su, dove si controlla che il risveglio
      sia avvenuto.  Le due cose non si confondono perche' non passano dalla
      stessa funzione.
    """
    if not base_fps or base_fps <= 0:
        return None
    soglia = base_fps * quota
    fila = 0
    for v in bucket_i:
        if v["fps"] < soglia:
            fila += 1
            if fila >= consecutivi:
                return v["da_ms"] - (consecutivi - 1) * BUCKET_MS
        else:
            fila = 0
    return None


def quando_sale(bucket_i, quanti_ms_fattore=2.0, base=None):
    """⭐ E LA SECONDA COLONNA: quando il RITARDO raddoppia.  `None` se mai.

    `LEZIONI.md` §1.34: *«non dare per scontato quale sia la colonna che
    avvisa: portane piu' di una»*.  Nella salita a dieci le chiavi tacevano e a
    muoversi era il ritardo ⇒ qui si datano tutt'e due, il ritmo e il ritardo, e
    si guarda **quale arriva prima**.
    """
    if base is None or base <= 0:
        return None
    for v in bucket_i:
        if v["ritardo_ms"] is not None and v["ritardo_ms"] > base * quanti_ms_fattore:
            return v["da_ms"]
    return None


def comando_risveglio(pezzi):
    """La riga che accende TUTTE le scene insieme, fra due letture dell'orologio.

    ⛔ Ogni pezzo finisce gia' con «&», che in bash **e' un separatore**: fra un
       pezzo e il successivo NON ci va un « ; », o esce «& ;» e bash si ferma.
    ⭐ E i due `python3` che leggono `CLOCK_MONOTONIC` stanno nella STESSA shell
       delle scene: e' l'unico modo perche' l'istante zero e quello delle scene
       siano lo stesso orologio, senza il giro di `ssh` in mezzo.
    ⚠ Niente `%` di formattazione qui dentro: la riga porta gia' i `%` del
      `print` remoto, e un `%.3f` mangiato dal formattatore di fuori non da' un
      errore leggibile — da' un `TypeError` in fondo a seicento caratteri.
    """
    ora = ('python3 -c \'import time;print("@ %.3f" % '
           '(time.clock_gettime(time.CLOCK_MONOTONIC)*1000))\'')
    return (ora.replace("@", "ZERO", 1) + " ; "
            + " ".join(pezzi) + " "
            + ora.replace("@", "DOPO", 1))


def sintassi_bash(comando):
    """`None` se bash lo accetta, il motivo se no.  ⛔ E se `bash -n` non si e'
       potuto eseguire torna `None`: «non ho potuto controllare» non e' «e'
       rotto», e un banco che si fermasse per un controllo mancante sarebbe
       peggio del difetto che cerca."""
    try:
        p = subprocess.run(["bash", "-n"], input=comando.encode(),
                           capture_output=True, timeout=20)
    except Exception:
        return None
    if p.returncode == 0:
        return None
    return p.stderr.decode("utf-8", "replace").strip()[:200]


def risveglio(quante_sature, quante_ferme, durata, resta, dopo_s):
    """⛔ N ferme che si svegliano TUTTE INSIEME, e quanto ci mette a succedere."""
    quanti = quante_sature + quante_ferme
    ricetta = ["S"] * quante_sature + ["F"] * quante_ferme
    esiti = {"ricetta": ricetta, "quanti": quanti, "durata_s": durata,
             "dopo_s": dopo_s}
    rossi, muti = [], []
    _log("⛔⛔ IL RISVEGLIO SIMULTANEO — %d sature + %d ferme che si svegliano "
         "TUTTE INSIEME" % (quante_sature, quante_ferme))
    _inf("⭐ e' il caso che un budget PRENOTATO ALL'INGRESSO non vede: quelle "
         "%d sessioni, quando sono state ammesse, costavano `[M]` GPU ZERO"
         % quante_ferme)

    # ── 1 · si aprono tutte, e le ferme restano ferme ──
    for i in range(1, quanti + 1):
        aperta, detto = B.apri_sessione(i, resta)
        if not aperta:
            _ko(detto)
            return {"esito": "⛔ NON HO MISURATO — la sessione %d non si apre"
                             % i}, ["la sessione %d non si apre" % i], [], None
        _ok("s%d aperta (%s) — %s" % (i, ricetta[i - 1], detto[:80]))
        if ricetta[i - 1] == "S" and not accendi_ruolo(i, "S"):
            _ko("⛔ la scena satura di s%d non parte" % i)
            rossi.append("la scena satura di s%d non parte" % i)

    # ── 2 · IL REGIME PRIMA — e si PROVA che le ferme erano ferme ──
    _log("1/3 · IL REGIME PRIMA — %d s, con le %d ferme ancora ferme"
         % (durata, quante_ferme))
    time.sleep(B.ASSESTAMENTO_S)
    f0 = B.sonda(quanti)
    if f0 is None or f0.get("t_ms") is None:
        return {"esito": "⛔ NON HO MISURATO — niente ancora"}, [], ["ancora"], None
    t0 = f0["t_ms"]
    time.sleep(durata)
    f1 = B.sonda(quanti)
    if f1 is None or f1.get("t_ms") is None:
        return {"esito": "⛔ NON HO MISURATO — niente ancora finale"}, [], ["ancora"], None
    t1 = f1["t_ms"]
    d_prima = B.fra(f0, f1, quanti)
    gpu_prima, nota_prima = gpu_per_uid(f0, f1)
    vive, scene, finestre, _m = chi_disegna(quanti)
    prima = {}
    for i in range(1, quanti + 1):
        n = fetta_mista(i, t0, t1, durata)
        n["ruolo"] = ricetta[i - 1]
        prima[i] = n
        stampa_riga_mista(i, ricetta[i - 1], n)
    esiti["prima"] = {"t0": t0, "t1": t1, "macchina": d_prima,
                      "sessioni": prima, "gpu_per_uid": gpu_prima,
                      "gpu_per_uid_nota": nota_prima, "scene": scene}
    _inf("MACCHINA PRIMA  CPU %s %% · GPU %s · GT %s MHz · RC6 %s %% · PSS %s MiB"
         % (d_prima.get("cpu_occupata_pc"), json.dumps(d_prima.get("gpu_uso_pc")),
            (d_prima.get("gt") or {}).get("act_mhz"),
            (d_prima.get("gt") or {}).get("rc6_pc"),
            d_prima.get("pss_totale_mib")))
    # ⛔ Le ferme DEVONO essere ferme, o quel che segue non e' un risveglio.
    # ⛔⛔ E PRIMA DI TUTTO: IL CLIENTE DEV'ESSERE VIVO.
    #
    #     ⚠ Un cliente MORTO e una sessione FERMA hanno lo stesso identico
    #       aspetto sul filo: zero fotogrammi.  ⇒ Senza questa riga il banco
    #       avrebbe dichiarato «ferma davvero» una sessione che il server aveva
    #       gia' sfrattato, e poi avrebbe misurato un risveglio di cadaveri.
    #     ⭐ E il caso non e' teorico: `fasi/10-…md` §6.3, `[M]` 24 agosto 2026 —
    #       *«linea-morta causa=silenzio silenzio_ms=10004 … persi=0»*, cioe' un
    #       desktop **fermo**, con perdita **zero**, chiuso dopo **dieci
    #       secondi**, perche' la cura dell'audio ha tolto il traffico che la
    #       linea morta si aspettava.  ⇒ Su questo prodotto una sessione ferma
    #       e' esattamente il caso che rischia di non esserci piu'.
    #   ⇒ `None` (non ho misurato), non zero, e non «ferma».
    morte = [i for i in range(1, quanti + 1) if not vive.get(i)]
    if morte:
        _ko("⛔⛔ NON HO MISURATO IL RISVEGLIO — i clienti di %s sono MORTI "
            "prima ancora del risveglio.  ⚠ Un cliente morto e una sessione "
            "ferma danno lo stesso zero sul filo: sono due cose, e solo una e' "
            "quella che volevo misurare"
            % ", ".join("s%d" % i for i in morte))
        esiti["esito"] = ("⛔ NON HO MISURATO — clienti morti prima del "
                          "risveglio: %s" % morte)
        return esiti, [], ["clienti morti prima del risveglio: %s" % morte], None
    non_ferme = []
    for i in range(quante_sature + 1, quanti + 1):
        passa, perche = p_ferma_e_ferma(prima[i], scene.get(i))
        (_ok if passa else (_dub if passa is None else _ko))(
            "⛔ la «ferma» era DAVVERO ferma · s%d: %s" % (i, perche))
        if passa is not True:
            non_ferme.append(i)
    if non_ferme:
        _ko("⛔⛔ NON HO MISURATO IL RISVEGLIO — %s non erano ferme PRIMA: "
            "quel che segue non e' un risveglio, e' un cambio di scena"
            % ", ".join("s%d" % i for i in non_ferme))
        esiti["esito"] = "⛔ NON HO MISURATO — le ferme non erano ferme prima"
        return esiti, [], ["le ferme non erano ferme prima: %s" % non_ferme], None

    base_fps = {i: prima[i].get("fps_finestra") for i in range(1, quanti + 1)}
    base_rit = {}
    for i in range(1, quanti + 1):
        r = prima[i].get("ritardo_f") or {}
        base_rit[i] = r.get("mediano_ms")

    # ── 3 · ⛔ IL RISVEGLIO: tutte insieme, in UN comando solo ──
    _log("2/3 · ⛔ IL RISVEGLIO — %d scene accese in UN COMANDO SOLO"
         % quante_ferme)
    _inf("⚠ un `ssh` per sessione sarebbero %d istanti diversi, cioe' un "
         "risveglio scaglionato su decine di secondi: non sarebbe la scena che "
         "questo banco esiste per misurare" % quante_ferme)
    # ⛔ L'uscita di ciascuna si chiede PRIMA, o il tempo di quelle domande
    #    entrerebbe dentro il risveglio.
    uscite = {}
    for i in range(quante_sature + 1, quanti + 1):
        uscite[i] = B.uscita_del(i)
    manca = [i for i, u in uscite.items() if not u]
    if manca:
        _ko("⛔ NON HO MISURATO — il compositore di %s non da' l'uscita: non "
            "posso svegliarle" % ", ".join("s%d" % i for i in manca))
        esiti["esito"] = "⛔ NON HO MISURATO — manca l'uscita di %s" % manca
        return esiti, [], ["manca l'uscita di %s" % manca], None
    pezzi = []
    for i in range(quante_sature + 1, quanti + 1):
        n, u = B.uid(i), B.utente(i)
        # ⛔ La SECONDA copia a mano dell'ambiente stava qui, e adesso passa
        #    dall'unico posto (`_ambiente`, e sotto di lui
        #    `10-ambiente-sessione.sh`).  ⚠ Il frammento si compone prima di
        #    entrare nella riga del risveglio: quella riga NON tollera un `%`
        #    di formattazione in piu' (il riquadro qui sotto dice perche').
        pezzi.append(
            "setsid nohup %s "
            "%s --uscita %s --movimento pieno --shm %s-%d --giro b98r-%d "
            ">> %s/scena-%d.log 2>&1 &"
            % (_ambiente(n, u), B.SCENA_BIN, uscite[i], SHM, i, i, B.LAV, i))
    # ⭐ L'istante zero: l'orologio monotono della macchina letto **dalla stessa
    #   shell** che accende le scene, nella stessa riga.  ⚠ Un `time.time()` del
    #   portatile sarebbe un altro orologio, piu' il giro di `ssh`.
    # ⚠ Niente `%` di formattazione in questa riga, e non e' pignoleria: dentro
    #   ci sono gia' i `%` del `print` di Python remoto, e un `%.3f` che il
    #   formattatore di fuori si mangia non da' un errore leggibile — da' un
    #   `TypeError` in fondo a una stringa di seicento caratteri.  ⇒ Si
    #   concatena.
    comando = comando_risveglio(pezzi)
    # ⛔⛔ E IL COMANDO SI CONTROLLA PRIMA DI SPEDIRLO — `bash -n`.
    #     `[M]` 24 agosto 2026, e questo giro l'ha pagato per intero: la prima
    #     stesura univa i pezzi con « ; », ma ogni pezzo finisce gia' con «&» ⇒
    #     usciva «... 2>&1 & ; python3 ...», che per bash e' un ERRORE DI
    #     SINTASSI.  Il comando moriva tutto insieme, nessuna scena si
    #     accendeva, e l'istante del risveglio non tornava.
    #   ⭐ Il banco ha detto «NON HO MISURATO» invece di «nessun effetto», ed e'
    #     esattamente quel che deve fare — ma ha comunque **bruciato un turno di
    #     lucchetto** per scoprire una virgola.  ⇒ Adesso la sintassi si prova
    #     in locale, dove non costa niente, e un comando che non compila si
    #     rifiuta di partire.
    ko_sintassi = sintassi_bash(comando)
    if ko_sintassi:
        _ko("⛔ NON MISURO — il comando del risveglio non e' bash valido: %s"
            % ko_sintassi)
        esiti["esito"] = "⛔ NON HO MISURATO — comando del risveglio malformato"
        return esiti, ["comando del risveglio malformato"], [], None
    rc, out, err = B.root(comando, 180)
    t_zero = t_fine = None
    for r in out.splitlines():
        if r.startswith("ZERO "):
            t_zero = float(r.split()[1])
        elif r.startswith("DOPO "):
            t_fine = float(r.split()[1])
    if t_zero is None or t_fine is None:
        _ko("⛔ NON HO MISURATO — non ho l'istante del risveglio: %s"
            % (out + err)[-200:])
        esiti["esito"] = "⛔ NON HO MISURATO — niente istante del risveglio"
        return esiti, [], ["niente istante del risveglio"], None
    _ok("⭐ le %d scene sono state lanciate in %.0f ms (⚠ e' la larghezza del "
        "«tutte insieme»: il risveglio non e' un istante, e' questa finestra)"
        % (quante_ferme, t_fine - t_zero))
    esiti["risveglio"] = {"t_zero": t_zero, "larghezza_ms": t_fine - t_zero}

    # ── 4 · IL DOPO, a bucket ──
    _log("3/3 · IL DOPO — %d s a bucket da %.0f ms" % (dopo_s, BUCKET_MS))
    time.sleep(dopo_s + 2)
    f2 = B.sonda(quanti)
    d_dopo = B.fra(f1, f2, quanti) if f2 else {"esito": "⛔ niente"}
    gpu_dopo, nota_dopo = (gpu_per_uid(f1, f2) if f2 else (None, {}))
    vive2, scene2, finestre2, _m2 = chi_disegna(quanti)
    # ⛔⛔ IL CONTROLLO CHE VIENE PRIMA DELL'EFFETTO: si sono svegliate DAVVERO?
    svegliate, non_svegliate = [], []
    dopo, bucket_di = {}, {}
    for i in range(1, quanti + 1):
        n = fetta_mista(i, t_zero, t_zero + dopo_s * 1000.0, dopo_s,
                        con_giornale=True)
        dopo[i] = n
        g = n.pop("giornale", []) if isinstance(n, dict) else []
        bucket_di[i] = bucket(g, t_zero, BUCKET_MS,
                              int(dopo_s * 1000.0 / BUCKET_MS))
        n["ruolo"] = ricetta[i - 1]
        stampa_riga_mista(i, ricetta[i - 1], n)
    for i in range(quante_sature + 1, quanti + 1):
        # ⭐ «Svegliata» vuol dire DUE cose insieme, da due parti diverse: la
        #   macchina vede la sua scena, e il filo porta i suoi fotogrammi.
        vede_scena = bool(scene2.get(i))
        fps = dopo[i].get("fps_finestra") or 0.0
        byte = dopo[i].get("byte_per_fotogramma_f")
        # ⛔⛔ «SVEGLIATA» SI GIUDICA DALLA SOLLECITAZIONE, NON DAL RITMO.
        #
        #     `[M]` 25 agosto 2026, e questo giro l'ha pagato: le otto ferme si
        #     erano svegliate benissimo — scena viva, fotogrammi da **4 825-5 421
        #     byte**, diciotto volte i 266 di una ferma — ma consegnavano
        #     **1,47-1,55 fot/s**, cioe' SOTTO la soglia delle ferme (2,0).
        #     ⇒ Il banco le ha dichiarate «non svegliate» e si e' rifiutato di
        #       misurare **proprio la scena che esisteva per misurare**.
        #   ⚠ E il ritmo basso non era il contrario del risveglio: ERA IL SUO
        #     RISULTATO.  Nove sessioni che chiedono 14,4 % di `render` a testa
        #     fanno 130 % di un motore che ne ha 100 ⇒ crollano tutte insieme,
        #     e 1,5 fot/s e' esattamente il dirupo gia' misurato in §6.5.
        #   ⭐ La grandezza che separa «dorme» da «lavora ma e' affamata» e' la
        #     stessa che separa una scena che morde da uno schermo nero: i BYTE
        #     PER FOTOGRAMMA (`p_scena_viva`, soglia 4 000).  E' `LEZIONI.md`
        #     §1.34 un'altra volta: la colonna che avvisa cambia col fenomeno.
        desta = (fps > SOGLIA_FERMA_FPS
                 or (byte is not None and byte >= B.BYTE_VIVI))
        if vede_scena and desta:
            svegliate.append(i)
        else:
            non_svegliate.append((i, vede_scena, fps))
    if non_svegliate:
        # ⛔⛔ LA FORMA «SILENZIO INVECE DI ROSSO», CHIUSA QUI.
        #     Se le ferme non si sono svegliate, l'effetto sull'incumbent non e'
        #     «nessuno»: e' **non misurato**.  Un banco che scrivesse «nessun
        #     effetto» darebbe al prodotto un buon voto per una prova che non e'
        #     stata fatta — ed e' la forma che nel primo giro ha prodotto
        #     ventidue difetti di banco.
        _ko("⛔⛔ NON HO MISURATO IL RISVEGLIO SIMULTANEO — %d sessioni su %d "
            "NON si sono svegliate: %s"
            % (len(non_svegliate), quante_ferme,
               " · ".join("s%d (scena vista: %s, %.2f fot/s, %s B/fot)"
                          % (x[0], x[1], x[2],
                             dopo[x[0]].get("byte_per_fotogramma_f"))
                          for x in non_svegliate)))
        _ko("   ⇒ Quel che si vede sull'incumbent NON e' «nessun effetto»: e' "
            "«non misurato».  Il banco NON giudica.")
        esiti["esito"] = ("⛔ NON HO MISURATO — %d su %d non si sono svegliate"
                          % (len(non_svegliate), quante_ferme))
        esiti["dopo"] = {"sessioni": dopo, "macchina": d_dopo}
        return esiti, [], ["il risveglio non e' avvenuto: %s"
                           % [x[0] for x in non_svegliate]], None
    _ok("⭐ tutte e %d si sono svegliate: la scena c'e' sulla macchina E i "
        "fotogrammi arrivano sul filo" % quante_ferme)

    esiti["dopo"] = {"sessioni": dopo, "macchina": d_dopo,
                     "gpu_per_uid": gpu_dopo, "gpu_per_uid_nota": nota_dopo,
                     "bucket": bucket_di}
    _inf("MACCHINA DOPO   CPU %s %% · GPU %s · GT %s MHz · RC6 %s %% · PSS %s MiB"
         % (d_dopo.get("cpu_occupata_pc"), json.dumps(d_dopo.get("gpu_uso_pc")),
            (d_dopo.get("gt") or {}).get("act_mhz"),
            (d_dopo.get("gt") or {}).get("rc6_pc"),
            d_dopo.get("pss_totale_mib")))

    # ── 5 · ⭐ QUANTO CI METTE A SUCCEDERE ──
    _log("⭐⭐ QUANTO CI METTE A SUCCEDERE — dal risveglio, in ms")
    print("\n   IL PRIMO FOTOGRAMMA DI CHI SI SVEGLIA")
    for i in svegliate:
        primo = next((v for v in bucket_di[i] if v["quanti"] > 0), None)
        print("      s%-2d  primo bucket con fotogrammi: %s ms · poi %s"
              % (i, primo["da_ms"] if primo else "MAI",
                 " ".join("%.0f" % v["fps"] for v in bucket_di[i][:10])))
    print("\n   ⛔ CHI LAVORAVA GIA' — il ritmo (sintomo) e il ritardo (meccanismo)")
    tempi = {}
    for i in range(1, quante_sature + 1):
        cade = quando_cade(bucket_di[i], base_fps.get(i))
        sale = quando_sale(bucket_di[i], base=base_rit.get(i))
        tempi[i] = {"ritmo_ms": cade, "ritardo_ms": sale,
                    "base_fps": base_fps.get(i), "base_ritardo": base_rit.get(i)}
        # ⛔ UNO ZERO NON E' UNA PRECISIONE.  Se il danno c'e' gia' nel PRIMO
        #    bucket, il metro non sa dire «a zero millisecondi»: sa dire «prima
        #    che il primo bucket finisse», cioe' **entro** la sua risoluzione.
        #    ⚠ Stampare «0 ms» sarebbe un numero piu' preciso della misura che
        #      lo produce — la forma che `REVIEWER.md` chiama numero plausibile.
        def quando(v):
            if v is None:
                return "MAI (non e' caduto)"
            if v <= 0:
                return ("gia' nel PRIMO bucket ⇒ **entro %.0f ms**, "
                        "⛔ sotto la risoluzione di questo metro" % BUCKET_MS)
            return "%s ms" % v
        print("      s%-2d  regime %s fot/s, ritardo %s ms  ⇒  il ritmo cade a "
              "%s · il ritardo raddoppia a %s"
              % (i, base_fps.get(i), base_rit.get(i), quando(cade),
                 quando(sale)))
        print("           fot/s per bucket da %.0f ms: %s"
              % (BUCKET_MS, " ".join("%.0f" % v["fps"]
                                     for v in bucket_di[i][:16])))
        print("           ritardo ms per bucket:       %s"
              % " ".join(("%.0f" % v["ritardo_ms"]) if v["ritardo_ms"] is not None
                         else "—" for v in bucket_di[i][:16]))
    esiti["tempi"] = tempi
    # ⭐ E la riga che risponde alla domanda dell'incarico.
    for i in range(1, quante_sature + 1):
        t = tempi[i]
        if t["ritmo_ms"] is None and t["ritardo_ms"] is None:
            _dub("⚠ s%d NON si e' accorta del risveglio in %d s: ne' il ritmo "
                 "ne' il ritardo si sono mossi" % (i, dopo_s))
        else:
            quale = ("il RITARDO" if (t["ritardo_ms"] is not None
                                      and (t["ritmo_ms"] is None
                                           or t["ritardo_ms"] < t["ritmo_ms"]))
                     else "il RITMO")
            _ok("⭐ s%d se n'e' accorta: %s per primo, a %s ms dal risveglio "
                "(l'altro a %s) — ⭐ `LEZIONI.md` §1.34: la colonna che avvisa "
                "cambia col fenomeno, e va cercata ogni volta"
                % (i, quale, min(x for x in (t["ritmo_ms"], t["ritardo_ms"])
                                 if x is not None),
                   t["ritardo_ms"] if quale == "il RITMO" else t["ritmo_ms"]))
    esiti["esito"] = "misurato"
    return esiti, rossi, muti, bucket_di


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL RIASSUNTO DI UNA MISCELA
# ═══════════════════════════════════════════════════════════════════════════
def riassunto(esiti, quanti, ricetta):
    _log("⭐ LA MISCELA, gradino per gradino")
    gradini = [v for v in esiti["gradini"]
               if v.get("quale") == "normale" and v.get("sessioni")]
    if not gradini:
        _dub("nessun gradino ha prodotto numeri")
        return

    def griglia(titolo, prendi, forma):
        print("\n   %s" % titolo)
        print("           %s" % "  ".join("g%-5d" % v["gradino"] for v in gradini))
        for i in range(1, quanti + 1):
            celle, visto = [], False
            for v in gradini:
                n = v["sessioni"].get(i)
                try:
                    celle.append(forma % prendi(n))
                    visto = True
                    continue
                except Exception:
                    pass
                celle.append("     -")
            if visto:
                print("   s%-2d[%s] %s" % (i, ricetta[i - 1], " ".join(celle)))

    griglia("FOTOGRAMMI/S sulla FINESTRA — il sintomo (⛔ e vale anche a zero)",
            lambda n: n["fps_finestra"], "%7.2f")
    griglia("BYTE AL SECONDO — ⛔ quanta sollecitazione e' ARRIVATA (§1.30)",
            lambda n: n["byte_al_secondo"] / 1000.0, "%7.1f")
    griglia("BYTE PER FOTOGRAMMA (÷1000) — e la prova che una scena morde",
            lambda n: n["byte_per_fotogramma_f"] / 1000.0, "%7.2f")
    griglia("RITARDO MEDIANO ms — ⭐ il MECCANISMO (§1.34)",
            lambda n: n["ritardo_f"]["mediano_ms"], "%7.1f")
    griglia("CHIAVI nella finestra — ⚠ nella salita a dieci sono rimaste a ZERO",
            lambda n: n["chiavi_finestra"], "%7d")
    _inf("⚠ «-» vuol dire «non c'era» oppure «non ho misurato»: ⛔ NON zero")

    print("\n   LA MACCHINA — e quale risorsa finisce per prima")
    print("        %-3s %-12s %6s %7s %7s %7s %8s %8s"
          % ("g", "miscela", "CPU%", "GPUren%", "GPUvid%", "GPUveh%", "PSS MiB",
             "GT MHz"))
    for v in gradini:
        m = v["macchina"]
        gp = m.get("gpu_uso_pc") or {}
        r = v["ruoli"]
        eti = "%dS+%dT+%dF" % (sum(1 for x in r.values() if x == "S"),
                               sum(1 for x in r.values() if x == "T"),
                               sum(1 for x in r.values() if x == "F"))
        print("        %-3d %-12s %6s %7s %7s %7s %8s %8s"
              % (v["gradino"], eti, m.get("cpu_occupata_pc"), gp.get("render"),
                 gp.get("video"), gp.get("video-enhance"),
                 m.get("pss_totale_mib"), (m.get("gt") or {}).get("act_mhz")))
    _inf("⚠ le colonne GPU sono l'USO DELLA CAPACITA' (0..100 %), non i "
         "motori-equivalenti: i VDBOX di questa scheda sono DUE")
    _inf("⛔ e l'occupazione dipende dalla FREQUENZA della GT (§6.1 §CLOCK, "
         "fattore 3,8): due gradini con GT diverse non si confrontano")

    # ⭐ LA GPU PER SESSIONE — la prova che una ferma costa zero.
    print("\n   ⭐ GPU PER SESSIONE (%% del tempo di parete, motore `render`)")
    print("           %s" % "  ".join("g%-5d" % v["gradino"] for v in gradini))
    for i in range(1, quanti + 1):
        celle, visto = [], False
        for v in gradini:
            gu = v.get("gpu_per_uid") or {}
            mot = gu.get(str(B.uid(i)))
            if mot is not None:
                celle.append("%7.2f" % mot.get("render", 0.0))
                visto = True
            else:
                celle.append("     -")
        if visto:
            print("   s%-2d[%s] %s" % (i, ricetta[i - 1], " ".join(celle)))
    _inf("⛔ «-» = nessun contesto DRM comune alle due fotografie: NON e' zero")

    # ⭐ IL NUMERO DELLA MISCELA.
    lavora = [i for i in range(1, quanti + 1) if ricetta[i - 1] != "F"]
    if lavora and gradini:
        i = lavora[0]
        primo = next((v for v in gradini
                      if v["sessioni"].get(i, {}).get("fps_finestra") is not None),
                     None)
        ultimo = gradini[-1]
        a = (primo or {}).get("sessioni", {}).get(i)
        b = ultimo["sessioni"].get(i)
        if a and b and a.get("fps_finestra") and b.get("fps_finestra") is not None:
            r = ultimo["ruoli"]
            _ok("⭐ IL NUMERO DELLA MISCELA — s%d[%s] da sola: %.2f fot/s, %s "
                "B/fot, ritardo %s ms · con %d ferme e %d a strappi accanto: "
                "%.2f fot/s, %s B/fot, ritardo %s ms  (%+.1f %% di ritmo)"
                % (i, ricetta[i - 1], a["fps_finestra"],
                   a["byte_per_fotogramma_f"],
                   (a.get("ritardo_f") or {}).get("mediano_ms"),
                   sum(1 for x in r.values() if x == "F"),
                   sum(1 for x in r.values() if x == "T"),
                   b["fps_finestra"], b["byte_per_fotogramma_f"],
                   (b.get("ritardo_f") or {}).get("mediano_ms"),
                   100.0 * (b["fps_finestra"] - a["fps_finestra"])
                   / a["fps_finestra"]))
    ap = esiti.get("apertura_ms") or {}
    if ap:
        _inf("⭐ APERTURA della sessione ennesima (ms, tetto): %s"
             % " ".join("s%s:%s" % (k, v) for k, v in sorted(ap.items())))
    _inf("⛔ IL FERRO: i5-13500T · **Intel UHD 730 INTEGRATA** (`renderD128`, "
         "`i915`) · la Radeon RX 6800 e' chiusa da udev (§4.6-quinquies)")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL CONTROLLO POSITIVO — ⛔ e ogni caso e' stato FATTO GIRARE
# ═══════════════════════════════════════════════════════════════════════════
def certifica(anche_b92=True):
    print("== ⭐ `10-b98-mista.py --certifica` — i guasti si INNESTANO e si "
          "FANNO GIRARE\n")
    B.B70 = B._importa_b70()
    rossi = []

    def caso(nome, atteso, visto, ok):
        print("  %s %s" % ("⭐" if ok else "⛔", nome))
        print("      atteso: %s" % (atteso,))
        print("      visto:  %s" % (visto,))
        if not ok:
            rossi.append(nome)

    # ── 0 · I METRI SI TARANO PRIMA (`LEZIONI.md` §1.33) ──────────────────
    print("  ── 0 · i metri si tarano PRIMA, su valori NOTI ──")
    sano, guai = B.tara_riduzione(B.B70, dillo=False)
    caso("0a · la riduzione di 09-b70, importata da 10-b92, ritrova i valori "
         "iniettati", "200/7,960 = 25,13/s · 10 000 B/fot · ritardo 37,5 ms",
         "tutto ritrovato" if sano else guai, sano)
    sano2, guai2 = tara_finestra(dillo=False)
    caso("0b · ⛔ il metro della FINESTRA (il solo che sappia misurare una "
         "ferma)", "1 fot in 40,8 s → 0,0245/s · 900 in 30 s → 30,00/s e "
         "168 000 B/s · 2 fot a 0,5 s in 40 s → 0,05/s (⚠ 09-b70 direbbe 4,00/s)",
         "tutto ritrovato" if sano2 else guai2, sano2)

    # ── 0c · LA SONDA ESTESA — ⛔ e la sostituzione si VERIFICA ────────────
    print("\n  ── 0c · ⛔ la sonda estesa: una sostituzione che non combacia "
          "NON alza, TACE ──")
    caso("0c · la sonda di 10-b92 e' stata estesa con `contesti_uid`",
         "la sostituzione combacia una volta sola e il testo cambia",
         "ok" if SONDA_PIU else _GUAI_SONDA, bool(SONDA_PIU))
    # ⛔ IL GUASTO INNESTATO: si sposta l'ancora, e ci si aspetta il RIFIUTO.
    _vero = B.SONDA
    try:
        B.SONDA = _vero.replace('"contesti_miei": {},', '"contesti_miei": {} ,')
        finta, guai_f = _sonda_piu()
        ok = finta is None and guai_f
        caso("0c-guasto · ⛔ GUASTO: l'ancora della sostituzione non combacia "
             "piu' → il banco SI RIFIUTA (non misura con la sonda vecchia)",
             "None + un motivo", "None + %s" % (guai_f or "NIENTE"), ok)
    finally:
        B.SONDA = _vero
    rifatta, _g = _sonda_piu()
    caso("0c-risanato · tolto il guasto, la sostituzione torna a combaciare",
         "una sonda con `contesti_uid`",
         "ok" if rifatta and "contesti_uid" in rifatta else "NO",
         bool(rifatta and "contesti_uid" in rifatta))

    # ── 1 · ⛔ UNA «FERMA» CHE SI MUOVE ⇒ la miscela non e' valida ─────────
    print("\n  ── 1 · ⛔ una «ferma» che SI MUOVE (notifica, orologio, "
          "salvaschermo) ──")
    #  sano: la ferma vera di §6.4-bis
    g_sano = [{"numero": 7, "chiave": True, "tipo": 0x0301, "codec": 3,
               "l": 1920, "a": 1080, "byte": 266,
               "istante_us": 990000, "arrivo_ms": 1000.0}]
    n_sano = riduci_finestra(g_sano, 500.0, 500.0 + 40800.0)
    passa, perche = p_ferma_e_ferma(n_sano, False)
    caso("1a · sano: la ferma vera di §6.4-bis (1 fot in 40,8 s, 266 B)",
         "VERDE", "%s — %s" % (passa, perche[:90]), passa is True)
    #  guasto A: un orologio che batte — 3 fot/s da 900 byte
    g_orol = B._fab(120, fps=3.0, byte=900, chiave_ogni=0, primo_numero=100,
                    ritardo_ms=10.0, t0=1000.0)
    n_orol = riduci_finestra(g_orol, 1000.0, 1000.0 + 40000.0)
    passa, perche = p_ferma_e_ferma(n_orol, False)
    caso("1b · ⛔ GUASTO: l'orologio di GNOME che batte a 3 fot/s da 900 byte → "
         "ROSSO, e la miscela e' dichiarata NON VALIDA  ⭐ e a smascherarlo e' "
         "il RITMO da solo: i suoi 2 700 B/s dicevano «ferma»", "ROSSO",
         "%s — %s" % (passa, perche[:150]), passa is False)
    #  guasto B: la scena c'e' sulla macchina, ma il filo tace (schermo nero)
    passa, perche = p_ferma_e_ferma(n_sano, True)
    caso("1c · ⛔ GUASTO: `pgrep` trova un `04-b30-scena` a nome di una FERMA → "
         "ROSSO anche se il filo tace ⭐ (due sorgenti, e basta UNA)",
         "ROSSO", "%s — %s" % (passa, perche[:120]), passa is False)
    #  guasto C: le due colonne si contraddicono ⇒ NON GIUDICO
    g_contr = B._fab(60, fps=1.5, byte=90000, chiave_ogni=0, primo_numero=1,
                     ritardo_ms=10.0, t0=1000.0)
    n_contr = riduci_finestra(g_contr, 1000.0, 1000.0 + 40000.0)
    passa, perche = p_ferma_e_ferma(n_contr, False)
    caso("1d · ⛔ GUASTO: il caso OPPOSTO — ritmo da ferma (1,5/s) e byte da "
         "lavoro (135 kB/s, un salvaschermo a pieno schermo che si ridisegna "
         "piano) → ROSSO ⭐ smascherato dalla SECONDA colonna, quella che nella "
         "salita a dieci non era quella che avvisava (§1.34)", "ROSSO",
         "%s — %s" % (passa, perche[:150]), passa is False)
    passa, perche = p_ferma_e_ferma({"esito": "⛔ la fetta non si e' letta"},
                                    False)
    caso("1d-bis · ⚠ e «non ho letto» resta un esito SUO: la fetta illeggibile "
         "→ NON GIUDICO, ⛔ non «ferma»", "None (non giudico)",
         "%s — %s" % (passa, perche[:90]), passa is None)
    passa, perche = p_ferma_e_ferma(n_sano, False)
    caso("1e · risanato: tolti i guasti, la ferma vera torna VERDE", "VERDE",
         "%s" % passa, passa is True)

    # ── 2 · ⛔ UNA «SATURA» CHE NON SATURA ────────────────────────────────
    print("\n  ── 2 · ⛔ una «satura» che NON satura ──")
    g_sat = B._fab(900, fps=30.0, byte=5600, chiave_ogni=0, primo_numero=1,
                   ritardo_ms=10.0, t0=1000.0)
    n_sat = B.B70.misura(g_sat, 30.0, scaldata_s=0.0)
    n_sat.update(riduci_finestra(g_sat, 1000.0, 1000.0 + 30000.0))
    passa, perche = p_satura_satura(n_sat, True)
    caso("2a · sano: 30 fot/s da 5 600 byte, scena viva", "VERDE",
         "%s — %s" % (passa, perche[:90]), passa is True)
    g_mag = B._fab(900, fps=30.0, byte=2448, chiave_ogni=0, primo_numero=1,
                   ritardo_ms=10.0, t0=1000.0)
    n_mag = B.B70.misura(g_mag, 30.0, scaldata_s=0.0)
    n_mag.update(riduci_finestra(g_mag, 1000.0, 1000.0 + 30000.0))
    passa, perche = p_satura_satura(n_mag, True)
    caso("2b · ⛔ GUASTO: la scena `barra` (`[M]` 2 448 B/fot) messa dove ci "
         "vuole una satura → ROSSO", "ROSSO",
         "%s — %s" % (passa, perche[:110]), passa is False)
    passa, perche = p_satura_satura(n_sat, False)
    caso("2c · ⛔ GUASTO: byte giusti ma NESSUN `04-b30-scena` sulla macchina → "
         "ROSSO ⭐ (la seconda sorgente, indipendente dal filo)", "ROSSO",
         "%s — %s" % (passa, perche[:110]), passa is False)
    # ⭐ E IL CONTROLLO NEGATIVO CHE VALE PIU' DEGLI ALTRI: una satura AFFAMATA
    #   (1,5 fot/s, che e' il crollo di §6.5) NON dev'essere scambiata per una
    #   scena che non morde.
    g_aff = B._fab(45, fps=1.5, byte=5600, chiave_ogni=0, primo_numero=1,
                   ritardo_ms=500.0, t0=1000.0)
    n_aff = B.B70.misura(g_aff, 30.0, scaldata_s=0.0)
    n_aff.update(riduci_finestra(g_aff, 1000.0, 1000.0 + 30000.0))
    passa, perche = p_satura_satura(n_aff, True)
    caso("2d · ⭐ CONTROLLO NEGATIVO: una satura AFFAMATA (1,5 fot/s da 5 600 "
         "byte, il crollo di §6.5) NON e' «non satura» — il ritmo basso e' il "
         "RISULTATO", "VERDE", "%s — %s" % (passa, perche[:110]), passa is True)
    # ⛔⛔ E IL GUASTO CHE HO TROVATO IN CASA MIA, INNESTATO E FATTO GIRARE.
    #
    #     Le due riduzioni si FONDONO in un dizionario solo.  Se quella a
    #     finestra scrivesse `esito` — come faceva la prima stesura — coprirebbe
    #     il «misurato» di 09-b70, e `ha_misurato()` diventerebbe sempre falso:
    #     ⛔ `p_scena_viva`, `p_ritmo`, `p_quota_chiavi` e `p_I1` tacerebbero
    #     **tutti e quattro insieme**, senza un rosso e senza un giallo.
    #   ⭐ Il caso serve a impedire che qualcuno lo rimetta domani.
    passa_sano, _p = B.p_ritmo(n_sat)
    n_rotto = dict(n_sat)
    n_rotto["esito"] = "finestra letta"
    passa_rotto, perche_rotto = B.p_ritmo(n_rotto)
    caso("2e · ⛔⛔ GUASTO IN CASA MIA: la riduzione a finestra che scrive "
         "`esito` copre il «misurato» di 09-b70 → `ha_misurato()` sempre falso "
         "⇒ p_ritmo, p_scena_viva, p_quota_chiavi e p_I1 TACCIONO tutti "
         "insieme (E14).  ⭐ Con la chiave giusta (`esito_finestra`) p_ritmo "
         "giudica", "sano: VERDE · col guasto: ⚠ «non misurato» (il silenzio)",
         "sano: %s · guasto: %s (%s)" % (passa_sano, passa_rotto,
                                         perche_rotto[:40]),
         passa_sano is True and passa_rotto is None)
    caso("2e-bis · ⭐ e nella fusione VERA `ha_misurato()` regge",
         "True", B.ha_misurato(n_sat), B.ha_misurato(n_sat) is True)

    # ── 3 · ⛔ IL CONTO DI UNA MISCELA LETTO DA QUELLA PRECEDENTE ──────────
    print("\n  ── 3 · ⛔ il conto di un gradino letto da quello precedente ──")
    fette = {(1, 1): {"numeri": [1000, 2000]}, (2, 1): {"numeri": [2001, 3000]}}
    passa, perche = B.p_ancora(fette, 1, 2)
    caso("3a · sano: i `numero` del gradino 2 vengono DOPO quelli del gradino 1",
         "VERDE", "%s — %s" % (passa, perche[:90]), passa is True)
    fette_g = {(1, 1): {"numeri": [1000, 2000]}, (2, 1): {"numeri": [1500, 2500]}}
    passa, perche = B.p_ancora(fette_g, 1, 2)
    caso("3b · ⛔ GUASTO: i due gradini si sovrappongono sui `numero` → ROSSO "
         "⭐ e non e' una statistica: e' un fatto, senza tolleranza", "ROSSO",
         "%s — %s" % (passa, perche[:110]), passa is False)
    passa, perche = B.p_ancora(fette, 1, 2)
    caso("3c · risanato", "VERDE", "%s" % passa, passa is True)

    # ── 4 · ⛔⛔ IL RISVEGLIO CHE NON AVVIENE ⇒ «non ho misurato» ──────────
    print("\n  ── 4 · ⛔⛔ il risveglio simultaneo che NON avviene ──")
    fatti = risveglio_finto(sature=1, ferme=3, si_svegliano=3)
    ok = (fatti["esito"] == "misurato" and fatti.get("tempi"))
    caso("4a · sano: tre ferme che si svegliano davvero → il banco MISURA",
         "esito «misurato» e i tempi ci sono",
         "%s · tempi %s" % (fatti.get("esito"), bool(fatti.get("tempi"))), ok)
    fatti = risveglio_finto(sature=1, ferme=3, si_svegliano=0)
    ok = ("NON HO MISURATO" in (fatti.get("esito") or "")
          and not fatti.get("tempi"))
    caso("4b · ⛔⛔ GUASTO: NESSUNA si sveglia → il banco dice «NON HO "
         "MISURATO», ⛔ **non** «nessun effetto»",
         "esito che nomina «NON HO MISURATO», e NESSUN tempo",
         "%s · tempi %s" % ((fatti.get("esito") or "?")[:70],
                            bool(fatti.get("tempi"))), ok)
    fatti = risveglio_finto(sature=1, ferme=3, si_svegliano=2)
    ok = ("NON HO MISURATO" in (fatti.get("esito") or "")
          and not fatti.get("tempi"))
    caso("4c · ⛔ GUASTO: solo DUE su tre si svegliano → idem ⭐ (un risveglio "
         "parziale non e' un risveglio simultaneo)",
         "esito che nomina «NON HO MISURATO»",
         (fatti.get("esito") or "?")[:70], ok)
    fatti = risveglio_finto(sature=1, ferme=3, si_svegliano=3, morto=3)
    ok = ("NON HO MISURATO" in (fatti.get("esito") or "")
          and "morti" in (fatti.get("esito") or ""))
    caso("4d-bis · ⛔⛔ GUASTO: il cliente di una «ferma» e' MORTO prima del "
         "risveglio (⭐ e' `[M]` §6.3: `linea-morta causa=silenzio`, un "
         "desktop fermo chiuso a 10 s con perdita ZERO) → «non ho misurato» "
         "⛔ e NON «ferma davvero»: un morto e un fermo danno lo stesso zero",
         "esito che nomina «NON HO MISURATO» e «morti»",
         (fatti.get("esito") or "?")[:80], ok)
    fatti = risveglio_finto(sature=1, ferme=3, si_svegliano=3,
                            ferme_gia_sveglie=True)
    ok = ("NON HO MISURATO" in (fatti.get("esito") or ""))
    caso("4d · ⛔ GUASTO: le «ferme» NON erano ferme PRIMA → «non ho misurato», "
         "⭐ perche' quel che segue non e' un risveglio, e' un cambio di scena",
         "esito che nomina «NON HO MISURATO»",
         (fatti.get("esito") or "?")[:70], ok)
    fatti = risveglio_finto(sature=1, ferme=3, si_svegliano=3)
    caso("4e · risanato: il risveglio torna a essere misurato", "misurato",
         fatti.get("esito"), fatti.get("esito") == "misurato")
    # ⭐⭐ IL CONTROLLO CHE MANCAVA, E CHE UN GIRO VERO HA PAGATO.
    fatti = risveglio_finto(sature=1, ferme=3, si_svegliano=3, affamate=True)
    ok = (fatti.get("esito") == "misurato" and fatti.get("tempi"))
    caso("4e-bis · ⭐⭐ CONTROLLO NEGATIVO: le ferme si svegliano ma la macchina "
         "le AFFAMA (1,5 fot/s con fotogrammi PIENI da 5 600 B) → e' un "
         "risveglio MISURATO, ⛔ non «non si sono svegliate».  `[M]` 25 ago: il "
         "banco sbagliava proprio qui, e si rifiutava di misurare la scena che "
         "esiste per misurare", "esito «misurato» e i tempi ci sono",
         "%s · tempi %s" % (fatti.get("esito"), bool(fatti.get("tempi"))), ok)
    fatti = risveglio_finto(sature=1, ferme=3, si_svegliano=0)
    ok = "NON HO MISURATO" in (fatti.get("esito") or "")
    caso("4e-ter · ⭐ e la distinzione REGGE dall'altro lato: chi resta a 266 "
         "B/fot NON e' «affamato», dorme ⇒ «non ho misurato»",
         "esito che nomina «NON HO MISURATO»",
         (fatti.get("esito") or "?")[:70], ok)

    # ── 4f · ⛔⛔ LA SINTASSI DEL COMANDO DEL RISVEGLIO ────────────────────
    #     `[M]` 24 agosto 2026: questo difetto e' costato UN TURNO INTERO di
    #     lucchetto.  I pezzi finiscono con «&», che in bash e' gia' un
    #     separatore; unirli con « ; » produce «& ;», che e' un errore di
    #     sintassi.  ⭐ Il banco disse «NON HO MISURATO» — giusto — ma dopo aver
    #     acceso otto sessioni e aspettato quaranta secondi.
    print("\n  ── 4f · ⛔ il comando del risveglio dev'essere bash VALIDO, e si "
          "controlla PRIMA di spedirlo ──")
    finti = ["setsid nohup sh -c vero%d >> /dev/null 2>&1 &" % i
             for i in range(1, 9)]
    buono = comando_risveglio(finti)
    caso("4f · sano: otto scene accese in una riga sola → bash la accetta",
         "None (nessun errore di sintassi)", sintassi_bash(buono),
         sintassi_bash(buono) is None)
    rotto = (buono.split(" ; ", 1)[0] + " ; " + " ; ".join(finti) + " ; echo DOPO")
    ko = sintassi_bash(rotto)
    caso("4f-guasto · ⛔ GUASTO: i pezzi uniti con « ; » invece che con lo "
         "spazio → «& ;» ⇒ bash RIFIUTA, e il banco non spedisce niente",
         "un errore di sintassi da bash", (ko or "NESSUN ERRORE")[:90],
         ko is not None)
    caso("4f-risanato · tolto il « ; », la riga torna valida", "None",
         sintassi_bash(buono), sintassi_bash(buono) is None)
    caso("4f-bis · ⚠ e se `bash -n` non si puo' eseguire, «non ho potuto "
         "controllare» NON diventa «e' rotto»", "None",
         sintassi_bash("echo ok"), sintassi_bash("echo ok") is None)

    # ── 5 · ⭐ IL METRO DEL «QUANTO CI METTE», TARATO SU UN ISTANTE NOTO ───
    print("\n  ── 5 · ⭐ il metro del «quanto ci mette»: si inietta un istante "
          "NOTO e si guarda se lo ritrova ──")
    #  Un giornale che va a 38 fot/s e crolla a 10 esattamente al secondo 6.
    g = []
    t, num = 0.0, 1
    while t < 30000.0:
        g.append({"numero": num, "chiave": False, "tipo": 0x0301, "codec": 3,
                  "l": 1920, "a": 1080, "byte": 5600,
                  "istante_us": int((t - (10.0 if t < 6000.0 else 300.0)) * 1000),
                  "arrivo_ms": t})
        num += 1
        t += (1000.0 / 38.0) if t < 6000.0 else (1000.0 / 10.0)
    bk = bucket(g, 0.0, BUCKET_MS, 15)
    trovato = quando_cade(bk, 38.0)
    caso("5a · il crollo iniettato al secondo 6,0 (38 → 10 fot/s)",
         "il metro lo data a 6 000 ms (⚠ con bucket da 2 000 ms la risoluzione "
         "E' 2 000 ms, e si dichiara)", "%s ms" % trovato, trovato == 6000)
    salito = quando_sale(bk, base=10.0)
    caso("5b · e il RITARDO, iniettato a raddoppiare allo stesso istante "
         "(10 → 300 ms)", "6 000 ms", "%s ms" % salito, salito == 6000)
    #  ⭐ IL CONTROLLO NEGATIVO: senza crollo, il metro NON deve trovarne uno.
    g2 = B._fab(1140, fps=38.0, byte=5600, chiave_ogni=0, primo_numero=1,
                ritardo_ms=10.0, t0=0.0)
    bk2 = bucket(g2, 0.0, BUCKET_MS, 15)
    trovato2 = quando_cade(bk2, 38.0)
    caso("5c · ⭐ CONTROLLO NEGATIVO: 30 s a 38 fot/s senza crollo → il metro "
         "NON deve datare niente", "None", "%s" % trovato2, trovato2 is None)
    #  ⭐ E un singolo bucket basso NON e' un inizio: ci vogliono due di fila.
    g3 = [f for f in g2 if not (10000.0 <= f["arrivo_ms"] < 12000.0)]
    bk3 = bucket(g3, 0.0, BUCKET_MS, 15)
    trovato3 = quando_cade(bk3, 38.0)
    caso("5d · ⭐ CONTROLLO NEGATIVO: UN solo bucket vuoto (un singhiozzo) → "
         "non e' l'inizio del danno, servono due bucket di fila", "None",
         "%s" % trovato3, trovato3 is None)

    # ── 6 · `None` NON E' ZERO ────────────────────────────────────────────
    print("\n  ── 6 · ⛔ `None` non e' zero ──")
    v = riduci_finestra([], 1000.0, 41000.0)
    ok = (v["fotogrammi_finestra"] == 0 and v["fps_finestra"] == 0.0
          and v["byte_per_fotogramma_f"] is None and v["ritardo_f"] is None)
    caso("6a · zero fotogrammi: il CONTO e' zero (e' un dato), ma i byte per "
         "fotogramma e il ritardo sono `None`", "0 · 0,0 · None · None",
         "%s · %s · %s · %s" % (v["fotogrammi_finestra"], v["fps_finestra"],
                                v["byte_per_fotogramma_f"], v["ritardo_f"]), ok)
    passa, perche = p_ferma_costa_zero({}, 1110, {"act_mhz": 0})
    caso("6b · ⛔ nessun contesto DRM comune per quell'uid → ⚠ NON GIUDICO, "
         "⛔ e non «costa zero»", "None (non giudico)",
         "%s — %s" % (passa, perche[:90]), passa is None)
    passa, perche = p_ferma_costa_zero(None, 1110, {})
    caso("6c · la GPU per sessione non letta → NON GIUDICO", "None",
         "%s" % passa, passa is None)
    passa, perche = p_ferma_costa_zero({"1110": {"render": 0.0, "video": 0.0}},
                                       1110, {"act_mhz": 0, "rc6_pc": 100.0})
    caso("6d · sano: una ferma a 0,00 % su ogni motore, GT 0 MHz, RC6 100 % "
         "(`[M]` §6.4-bis)", "VERDE", "%s" % passa, passa is True)
    passa, perche = p_ferma_costa_zero({"1110": {"render": 3.24}}, 1110, {})
    caso("6e · ⛔ GUASTO: una dichiarata FERMA che costa 3,24 % di render (il "
         "desktop vero di §6.4-bis) → ROSSO", "ROSSO",
         "%s — %s" % (passa, perche[:90]), passa is False)

    # ── 7 · IL DELTA DELLA GPU PER SESSIONE, SUI SOLI CONTESTI COMUNI ─────
    print("\n  ── 7 · ⛔ il delta della GPU su una platea che CAMBIA ──")
    a = {"t_ms": 0.0, "gpu": {"per_contesto": {"1": {"render": 0},
                                               "2": {"render": 500000000}},
                              "contesti_uid": {"1": 1110, "2": 1111}}}
    b = {"t_ms": 10000.0, "gpu": {"per_contesto": {"1": {"render": 1000000000},
                                                   "3": {"render": 900000000}},
                                  "contesti_uid": {"1": 1110, "3": 1112}}}
    u, nota = gpu_per_uid(a, b)
    ok = (u == {"1110": {"render": 10.0}} and nota["morti"] == 1
          and nota["nati"] == 1)
    caso("7a · il contesto NATO fra le due fotografie non entra nel delta (e "
         "quello MORTO nemmeno) ⭐ altrimenti `[M]` render −76,4 %",
         "solo uid 1110 a 10,00 % · 1 nato · 1 morto",
         "%s · nati %s · morti %s" % (json.dumps(u), nota["nati"],
                                      nota["morti"]), ok)
    b2 = {"t_ms": 10000.0,
          # ⚠ −1 secondo su una finestra di 10: −10,0 %.  Un guasto da −0,01 %
          #   non avrebbe provato niente — starebbe **dentro** la soglia di
          #   −0,05 che il predicato usa apposta per non chiamare «negativo» un
          #   arrotondamento.  ⛔ Un guasto va innestato dove morde.
          "gpu": {"per_contesto": {"1": {"render": -1000000000}},
                  "contesti_uid": {"1": 1110}}}
    u2, nota2 = gpu_per_uid(a, b2)
    caso("7b · ⛔ GUASTO: occupazione NEGATIVA → «non giudico» ⭐ (un motore "
         "non puo' lavorare per un tempo negativo)",
         "esito che nomina «NON GIUDICO»", (nota2.get("esito") or "?")[:70],
         "NON GIUDICO" in (nota2.get("esito") or ""))
    u3, nota3 = gpu_per_uid({"t_ms": 0.0, "gpu": {}}, {"t_ms": 1.0, "gpu": {}})
    caso("7c · ⛔ la sonda senza `contesti_uid` → `None`, ⛔ non «zero per "
         "tutti»", "None", "%s" % (u3,), u3 is None)

    # ── 8 · LA RICETTA ────────────────────────────────────────────────────
    print("\n  ── 8 · la ricetta ──")
    ok = leggi_ricetta("SFFF") == ["S", "F", "F", "F"] == leggi_ricetta("S,F,F,F")
    caso("8a · `SFFF` e `S,F,F,F` sono la stessa ricetta", "['S','F','F','F']",
         leggi_ricetta("SFFF"), ok)
    try:
        leggi_ricetta("SXF")
        ok = False
        visto = "nessun rifiuto"
    except SystemExit as e:
        ok, visto = True, str(e)[:60]
    caso("8b · ⛔ GUASTO: un ruolo che non esiste → il banco si RIFIUTA",
         "SystemExit", visto, ok)

    # ── 9 · ⛔ LA MISCELA INTERA, contro una macchina finta ────────────────
    print("\n  ── 9 · ⛔ la MISCELA intera: e' `miscela()` stessa, con le sole "
          "funzioni che toccano la macchina sostituite ──")
    fatti = miscela_finta("SFFF")
    gradini = [v for v in fatti["gradini"] if v.get("sessioni")]
    ok = (len(gradini) == 4 and not fatti["rossi"]
          and len(gradini[-1]["sessioni"]) == 4)
    caso("9a · sano: 1 satura + 3 ferme, quattro gradini, nessun rosso",
         "4 gradini · 0 rossi · 4 sessioni all'ultimo gradino",
         "%d gradini · %d rossi %s · %d sessioni"
         % (len(gradini), len(fatti["rossi"]), fatti["rossi"][:2],
            len(gradini[-1]["sessioni"])), ok)
    fatti = miscela_finta("SFFF", fallisce_al=3)
    ok = (fatti.get("fermata_al_gradino") == 3
          and any("non si apre" in x for x in fatti["rossi"]))
    caso("9b · ⛔ GUASTO: la terza sessione non si apre → la miscela SI FERMA "
         "⭐ (continuare contandone una di meno vorrebbe dire scrivere «1 "
         "satura + 3 ferme» sotto un numero che ne aveva due)",
         "fermata_al_gradino = 3 e un rosso «non si apre»",
         "fermata a %s · rossi %s" % (fatti.get("fermata_al_gradino"),
                                      fatti["rossi"][:2]), ok)
    fatti = miscela_finta("SFFF", ferma_che_si_muove=3)
    ok = any("DAVVERO ferma" in x and "s3" in x for x in fatti["rossi"])
    caso("9c · ⛔ GUASTO: s3, dichiarata FERMA, fa 6 fot/s da 9 kB (un "
         "salvaschermo) → ROSSO a OGNI gradino in cui c'e', e la miscela e' "
         "dichiarata non valida", "rossi che nominano «DAVVERO ferma · s3»",
         "%d rossi: %s" % (len(fatti["rossi"]), fatti["rossi"][:3]), ok)
    fatti = miscela_finta("SFFF")
    caso("9d · risanato: senza guasti la miscela torna a zero rossi", "0 rossi",
         "%d" % len(fatti["rossi"]), not fatti["rossi"])

    print("\n== %d casi rossi su 10-b98" % len(rossi))
    for r in rossi:
        print("   ⛔ %s" % r)
    if anche_b92:
        print("\n" + "=" * 75)
        print("== ⭐⭐ E ADESSO I 42 CASI DI `10-b92-dieci.py`, RIFATTI GIRARE")
        print("   ⛔ 10-b98 importa 10-b92 e non ne modifica una riga: il suo")
        print("      controllo positivo dev'essere ancora esattamente quello.")
        print("=" * 75 + "\n")
        rc92 = B.certifica()
        if rc92 != 0:
            rossi.append("⛔ il --certifica di 10-b92 e' uscito %d" % rc92)
    if rossi:
        return 1
    print("\n== ⭐ OGNI PREDICATO DI 10-b98 E' STATO VISTO FALLIRE, E POI "
          "RISANARE — e i 42 di 10-b92 reggono ancora")
    return 0


def miscela_finta(ricetta, fallisce_al=None, ferma_che_si_muove=None):
    """⛔ LA MISCELA VERA, contro una macchina finta.

    ⚠ Non e' una simulazione della miscela: e' `miscela()` **stessa**, con le
      sole funzioni che toccano la macchina sostituite — la stessa forma di
      `giro_finto` in 10-b92, e per la stessa ragione: il `break` che ferma la
      salita, il `None` del cliente morto e l'ordine dei predicati sono quelli
      che gireranno per davvero.  ⭐ Provarli su una copia sarebbe certificare
      un altro programma.
    """
    ric = leggi_ricetta(ricetta)
    quanti = len(ric)
    orig = {n: globals().get(n) for n in
            ("accendi_ruolo", "chi_disegna", "fetta_mista", "finestre_vere")}
    orig_b = {n: getattr(B, n) for n in
              ("apri_sessione", "sonda", "uscita_del", "root",
               "mappa_provenienze", "registro_righe", "conti_server")}
    stato = {"t": 100000.0}

    def f_apri(i, resta):
        if fallisce_al is not None and i == fallisce_al:
            return False, ("⛔ la sessione %d NON si e' aperta in 240 s "
                           "(guasto innestato)" % i)
        return True, "SESSIONE stato=1 tela=1920x1080"

    def f_sonda(q):
        stato["t"] += 30000.0
        return {"t_ms": stato["t"], "gpu": {"per_contesto": {}, "motori": {},
                                            "capacita": {}, "clienti": 0,
                                            "contesti_uid": {}, "estranei": 0,
                                            "altri_pdev": {}},
                "cpu": {"totale": 100000, "inattivo": 90000, "nuclei": 20},
                "rete": {}, "gt": {},
                "processi": {"per_uid": {}, "negati": 0,
                             "server": {"pss_kib": 0, "rss_kib": 0,
                                        "cpu_jiffies": 0, "quanti": 0},
                             "clienti": {"pss_kib": 0, "rss_kib": 0,
                                         "cpu_jiffies": 0, "quanti": 0}},
                "costo_ms": 1.0}

    def f_fetta(i, t0, t1, durata, con_giornale=False):
        r = ric[i - 1]
        if r == "F" and i != ferma_che_si_muove:
            # ⚠ Il `numero` avanza di t0 in MILLISECONDI, non in secondi: con
            #   i secondi due gradini distanti 30 s si sovrapporrebbero sui
            #   1 140 fotogrammi del gradino, e `p_ancora` darebbe rosso — ⭐ e
            #   avrebbe ragione lui.  E' successo davvero scrivendo questo
            #   controllo positivo: il guasto era nei dati finti, non nel banco.
            g = [{"numero": 1000000 * i + int(t0), "chiave": True,
                  "tipo": 0x0301, "codec": 3, "l": 1920, "a": 1080,
                  "byte": 266, "istante_us": int((t0 + 50.0 - 10.0) * 1000),
                  "arrivo_ms": t0 + 50.0}]
        elif r == "F":
            # ⛔ IL GUASTO: una «ferma» che si muove — un salvaschermo.
            g = B._fab(int(6 * durata), fps=6.0, byte=9000, chiave_ogni=0,
                       primo_numero=1000000 * i + int(t0),
                       ritardo_ms=12.0, t0=t0)
        else:
            g = B._fab(int(38 * durata), fps=38.0, byte=5600, chiave_ogni=0,
                       primo_numero=1000000 * i + int(t0),
                       ritardo_ms=10.0, t0=t0)
        n = B.B70.misura(g, durata, scaldata_s=0.0)
        n["ritardo"] = B.ritardi(g)
        if g:
            num = sorted(f["numero"] for f in g)
            n["numeri"] = [num[0], num[-1]]
        n.update(riduci_finestra(g, t0, t1))
        if con_giornale:
            n["giornale"] = g
        return n

    def f_chi(q):
        return ({i: True for i in range(1, q + 1)},
                {i: (ric[i - 1] != "F") for i in range(1, q + 1)},
                {i: 0 for i in range(1, q + 1)}, [])

    try:
        globals()["accendi_ruolo"] = lambda i, r: "FINTO"
        globals()["chi_disegna"] = f_chi
        globals()["fetta_mista"] = f_fetta
        globals()["finestre_vere"] = lambda i: 2
        B.apri_sessione = f_apri
        B.sonda = f_sonda
        B.uscita_del = lambda i: "FINTO-0"
        B.root = lambda c, t=120: (0, "", "")
        B.mappa_provenienze = lambda: ({}, None)
        B.registro_righe = lambda: 1000
        B.conti_server = lambda a, b, c: {"esito": "finto",
                                          "posti_occupati": None,
                                          "posti_negati": [], "per_utente": {}}
        vecchio = time.sleep
        time.sleep = lambda s: None
        try:
            esiti, rossi, muti, fette, prima = miscela(ric, 30, False, 600)
            riassunto(esiti, quanti, ric)
        finally:
            time.sleep = vecchio
    finally:
        for n, v in orig.items():
            if v is not None:
                globals()[n] = v
        for n, v in orig_b.items():
            setattr(B, n, v)
    esiti["rossi"], esiti["muti"] = rossi, muti
    return esiti


def risveglio_finto(sature, ferme, si_svegliano, ferme_gia_sveglie=False,
                    morto=None, affamate=False):
    """⛔ IL RISVEGLIO VERO, contro una macchina finta.

    ⚠ Non e' una simulazione: e' `risveglio()` stessa, con le sole funzioni che
      toccano la macchina sostituite.  ⇒ Il rifiuto quando il risveglio non
      avviene e' quello che girera' per davvero (`10-b92`, `giro_finto`).
    """
    quanti = sature + ferme
    orig = {n: globals().get(n) for n in
            ("accendi_ruolo", "chi_disegna", "fetta_mista", "finestre_vere")}
    orig_b = {n: getattr(B, n) for n in
              ("apri_sessione", "sonda", "fra", "uscita_del", "root",
               "mappa_provenienze", "registro_righe", "conti_server")}
    stato = {"t": 100000.0, "svegliate": False}

    def f_sonda(q):
        # ⚠ La finestra finta dura quanto quella vera (30 s), o gli fps della
        #   fetta finta sarebbero divisi per un secondo e le righe di prova
        #   direbbero «1 140 fot/s» — un numero che non somiglia a niente e che
        #   renderebbe illeggibile il rapporto del controllo positivo.
        stato["t"] += 30000.0
        return {"t_ms": stato["t"], "gpu": {"per_contesto": {}, "motori": {},
                                            "contesti_uid": {}},
                "cpu": {"totale": 0, "inattivo": 0, "nuclei": 20}, "rete": {},
                "processi": {"per_uid": {}, "negati": 0,
                             "server": {"pss_kib": 0, "rss_kib": 0,
                                        "cpu_jiffies": 0, "quanti": 0},
                             "clienti": {"pss_kib": 0, "rss_kib": 0,
                                         "cpu_jiffies": 0, "quanti": 0}},
                "costo_ms": 1.0}

    def f_root(comando, tetto=120):
        if "ZERO" in comando:
            stato["svegliate"] = True
            return (0, "ZERO 200000.000\nDOPO 200120.000\n", "")
        return (0, "", "")

    def f_chi(q):
        # ⛔ `morto` innesta il caso peggiore: un cliente sfrattato PRIMA del
        #    risveglio, che sul filo e' indistinguibile da una sessione ferma.
        vive = {i: (i != morto) for i in range(1, q + 1)}
        scene = {}
        for i in range(1, q + 1):
            if i <= sature:
                scene[i] = True
            elif ferme_gia_sveglie:
                scene[i] = True
            else:
                scene[i] = stato["svegliate"] and (i - sature) <= si_svegliano
        return vive, scene, {i: 0 for i in range(1, q + 1)}, []

    def f_fetta(i, t0, t1, durata, con_giornale=False):
        sveglia = stato["svegliate"] and (i > sature)
        attiva = (i <= sature) or ferme_gia_sveglie or \
                 (sveglia and (i - sature) <= si_svegliano)
        if attiva and affamate and stato["svegliate"]:
            # ⛔ IL CASO VERO DEL 25 AGOSTO: svegliata E AFFAMATA — 1,5 fot/s,
            #    ma fotogrammi PIENI da 5 600 byte.  Il ritmo dice «dorme», la
            #    sollecitazione dice «lavora», ⭐ e ha ragione la seconda.
            g = B._fab(max(4, int(1.5 * durata)), fps=1.5, byte=5600,
                       chiave_ogni=0, primo_numero=1000 * i + int(t0 / 1000),
                       ritardo_ms=780.0, t0=t0)
        elif attiva:
            g = B._fab(int(38 * durata), fps=38.0, byte=5600, chiave_ogni=0,
                       primo_numero=1000 * i + int(t0 / 1000), ritardo_ms=10.0,
                       t0=t0)
        else:
            g = [{"numero": 1000 * i, "chiave": True, "tipo": 0x0301,
                  "codec": 3, "l": 1920, "a": 1080, "byte": 266,
                  "istante_us": int((t0 + 100.0 - 10.0) * 1000),
                  "arrivo_ms": t0 + 100.0}]
        n = B.B70.misura(g, durata, scaldata_s=0.0)
        n["ritardo"] = B.ritardi(g)
        n.update(riduci_finestra(g, t0, t1))
        if con_giornale:
            n["giornale"] = g
        return n

    try:
        globals()["accendi_ruolo"] = lambda i, r: "FINTO"
        globals()["chi_disegna"] = f_chi
        globals()["fetta_mista"] = f_fetta
        globals()["finestre_vere"] = lambda i: 0
        B.apri_sessione = lambda i, r: (True, "SESSIONE stato=1")
        B.sonda = f_sonda
        B.uscita_del = lambda i: "FINTO-0"
        B.root = f_root
        B.mappa_provenienze = lambda: ({}, None)
        B.registro_righe = lambda: 1000
        B.conti_server = lambda a, b, c: {"esito": "finto"}
        vecchio = time.sleep
        time.sleep = lambda s: None
        try:
            esiti, rossi, muti, bk = risveglio(sature, ferme, 30, 600, 30)
        finally:
            time.sleep = vecchio
    finally:
        for n, v in orig.items():
            if v is not None:
                globals()[n] = v
        for n, v in orig_b.items():
            setattr(B, n, v)
    return esiti


# ═══════════════════════════════════════════════════════════════════════════
def durata_del_giro(quanti, durata, doppia, extra=0):
    """⛔ UN SOLO numero per il `--resta` dei clienti e per il lucchetto: due
       formule vicine sarebbero due numeri che divergono, e il primo che scade
       rovina il giro dell'altro (10-b92, `durata_del_giro`)."""
    return int((durata + 140) * quanti + (2 * durata + 120 if doppia else 0)
               + extra + 600)


def _muori_pulito(segnale, _telaio):
    """⛔ IL PILOTA STACCATO DEVE PULIRE DA SE' ANCHE SE MUORE.

    Un `SIGTERM` — quello che manda `timeout`, o `systemctl stop` — uccide
    Python **senza** eseguire i `finally`: il lucchetto resterebbe preso fino
    alla sua scadenza, le scene accese e i palchi in piedi, e chi arriva dopo
    troverebbe il campo sporco senza sapere di chi.  ⚠ E non darebbe rosso a
    nessuno: darebbe a quello dopo un terreno che non e' quello che crede.
    ⇒ Il segnale si trasforma in un'eccezione, che i `finally` sanno gestire.
    """
    raise KeyboardInterrupt("⛔ segnale %d: smonto e mollo il lucchetto"
                            % segnale)


def principale():
    import signal
    for _s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        try:
            signal.signal(_s, _muori_pulito)
        except (ValueError, OSError):
            pass    # ⚠ «non ho potuto armarlo» si tace qui e si vede la',
                    #   non si finge di averlo armato
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?",
                   choices=["taratura", "miscela", "risveglio", "stato",
                            "sgombra"])
    p.add_argument("--certifica", action="store_true",
                   help="⭐ i guasti di 10-b98 + i 42 di 10-b92.  Non tocca la "
                        "macchina di prova")
    p.add_argument("--solo-miei", action="store_true",
                   help="con --certifica: NON rifa' girare i 42 di 10-b92")
    p.add_argument("--ricetta", default="SFFFFFFFFFF",
                   help="i ruoli, uno per sessione: S satura · F ferma · "
                        "T a strappi.  Es. «SSFFFFFF» o «S,S,F,F»")
    p.add_argument("--durata", type=int, default=30,
                   help="secondi a regime per gradino (⚠ §1.32: i giri corti "
                        "sottostimano)")
    p.add_argument("--doppia", action="store_true")
    p.add_argument("--sature", type=int, default=1, help="risveglio: quante S")
    p.add_argument("--ferme", type=int, default=8, help="risveglio: quante F")
    p.add_argument("--dopo", type=int, default=40,
                   help="risveglio: quanti secondi si guarda DOPO")
    p.add_argument("--senza-lucchetto", action="store_true",
                   help="⛔ solo per la messa a punto: quei numeri NON valgono")
    a = p.parse_args()

    if a.certifica:
        return certifica(anche_b92=not a.solo_miei)
    if not a.passo:
        p.error("serve un passo, oppure --certifica")

    if SONDA_PIU is None:
        _ko("⛔ NON MISURO — la sonda di 10-b92 non si e' potuta estendere: %s"
            % _GUAI_SONDA)
        return 2
    os.makedirs(FUORI, exist_ok=True)
    B.B70 = B._importa_b70()
    # ⭐ La sonda estesa prende il posto della sua PRIMA che `terreno()` la
    #   spedisca: il nome del file sulla macchina resta il suo, e vive nella
    #   MIA cartella di lavoro.  ⇒ Il file di 10-b92 non cambia di una riga.
    B.SONDA = SONDA_PIU

    if a.passo == "stato":
        return 0 if B.terreno(11) else 2
    if a.passo == "sgombra":
        import subprocess
        amb = dict(os.environ)
        subprocess.run(["bash", os.path.join(QUI, "10-b91-terreno-dieci.sh"),
                        "sgombra"], env=amb)
        return 0
    if a.passo == "taratura":
        _log("⛔ I METRI SI TARANO PRIMA — `LEZIONI.md` §1.33")
        sano, guai = B.tara_riduzione(B.B70)
        if not sano:
            for g in guai:
                _ko(g)
            return 1
        _ok("la riduzione di 09-b70 (importata via 10-b92) ritrova i valori "
            "iniettati")
        sano, guai = tara_finestra()
        if not sano:
            for g in guai:
                _ko(g)
            return 1
        quanti = max(len(leggi_ricetta(a.ricetta)), a.sature + a.ferme)
        if not B.terreno(quanti):
            return 2
        _log("⭐ LA SONDA ESTESA, sulla macchina vera")
        f0 = B.sonda(quanti)
        if not f0:
            return 2
        time.sleep(5)
        f1 = B.sonda(quanti)
        d = B.fra(f0, f1, quanti)
        u, nota = gpu_per_uid(f0, f1)
        _inf("costo della sonda: %s ms" % d.get("costo_sonda_ms"))
        passa, perche = B.p_metro_gpu(d)
        (_ok if passa else (_dub if passa is None else _ko))(
            "il metro della GPU: %s" % perche)
        if u is None:
            _ko("⛔ la sonda estesa NON porta `contesti_uid`: %s" % nota)
            return 1
        _ok("⭐ la GPU per sessione si legge: %s contesti comuni · %s"
            % (nota.get("contesti_comuni"), json.dumps(u)[:300]))
        return 0 if passa is not False else 1

    # ── LE MISURE ─────────────────────────────────────────────────────────
    if a.passo == "miscela":
        ricetta = leggi_ricetta(a.ricetta)
        quanti = len(ricetta)
        extra = 0
    else:
        ricetta = ["S"] * a.sature + ["F"] * a.ferme
        quanti = a.sature + a.ferme
        extra = a.dopo + 120
    if quanti > 11:
        _ko("⛔ ho undici utenti (`provamt1…provamt11`), non %d" % quanti)
        return 2

    _log("10-b98 · %s — porta %d · tela %s · codec «%s»"
         % (nome_miscela(ricetta), B.PORTA, B.TELA, B.CODEC_CHIESTO))
    sano, guai = B.tara_riduzione(B.B70, dillo=False)
    sano2, guai2 = tara_finestra(dillo=False)
    if not (sano and sano2):
        for g in (guai + guai2):
            _ko("⛔ un metro non e' tarato: %s" % g)
        return 2
    _ok("i due metri sono tarati (giornali a valore noto ritrovati)")

    # ⛔⛔ IL LUCCHETTO PRIMA, GLI UTENTI DOPO — il protocollo del giro 2.
    luc = None
    if not a.senza_lucchetto:
        luc = B._lucchetto()
        quanto = durata_del_giro(quanti, a.durata, a.doppia, extra)
        _inf("⛔ chiedo il lucchetto della GPU per %d s (%d min)"
             % (quanto, quanto // 60))
        try:
            # ⛔ DUE ORE DI ATTESA, E SI ASPETTA DENTRO IL PROCESSO.
            #    `prendi()` dorme e ritenta da se' ogni 5 s, stampando di chi
            #    e' il turno.  ⚠ Uscire per «tornare a guardare» non fa
            #    arrivare prima: fa perdere il posto e ricominciare l'attesa.
            #    ⭐ `[M]` 24 agosto 2026: sulla stessa GPU lavorano cinque
            #    incarichi, e un turno e' stato tenuto per 98 minuti di fila —
            #    un'attesa corta non evita la coda, la fa solo scadere a vuoto.
            # ⛔⛔ E L'ATTESA E' LUNGHISSIMA APPOSTA, perche' `prendi()` NON
            #     E' UNA CODA: e' una GARA.  Ogni 5 s tenta un `mkdir`, e chi
            #     capita per primo dopo un `molla` vince — non c'e' nessun
            #     turno prenotato, e chi ha aspettato di piu' non ha nessuna
            #     precedenza.  `[M]` 24 agosto 2026: aspettando dalle 19:53 ho
            #     perso DUE passaggi di mano di fila (10-b4 → 10-b9) senza mai
            #     toccare la GPU.
            #   ⇒ Un'attesa «generosa» di due ore non basta: con cinque
            #     incarichi che tengono ~90 minuti a testa, due ore scadono
            #     dentro il turno di un altro e il giro si perde **senza aver
            #     misurato niente**.  ⚠ E il danno non e' l'attesa: e' che il
            #     giro viene SALTATO, cioe' la domanda centrale resta senza
            #     risposta mentre il banco esce 2 come se fosse un problema di
            #     terreno.
            luc.prendi(B.IO_SONO, secondi=quanto, attesa=21600)
        except Exception as e:
            _ko("⛔ NON MISURO: %s" % e)
            return 2
    else:
        _dub("⛔ SENZA LUCCHETTO: i numeri di questo giro NON valgono")

    esiti, rossi, muti = {}, [], []
    try:
        # ⛔ Appena preso il lucchetto: i palchi orfani, che NON danno rosso —
        #    danno un numero plausibile (fase 9, tre cure innocenti accusate).
        # ⛔⛔ IL PROTOCOLLO DEGLI UTENTI CONDIVISI: prima il lucchetto (fatto
        #     qui sopra), POI si guarda che il posto sia libero, e solo dopo si
        #     sgombra.  ⚠ Guardare DOPO aver sgomberato non e' guardare: un
        #     palco orfano non da' rosso, da' un numero plausibile, e in fase 9
        #     stava per far accusare tre cure innocenti.  ⇒ Lo `stato` si
        #     stampa PRIMA, e finisce nel rapporto.
        _log("⛔ COL LUCCHETTO IN MANO — che cosa c'era prima che io toccassi "
             "gli utenti CONDIVISI `provamt1…provamt11`")
        import subprocess
        subprocess.run(["bash", os.path.join(QUI, "10-b91-terreno-dieci.sh"),
                        "stato"], env=dict(os.environ))
        _log("⛔ e adesso i palchi si CHIUDONO (I4 li fa sopravvivere al "
             "distacco, ed e' giusto — ma non sono miei da misurare)")
        B.chiudi_palchi(11)
        if not B.terreno(quanti):
            return 2
        resta = durata_del_giro(quanti, a.durata, a.doppia, extra)
        if a.passo == "miscela":
            esiti, rossi, muti, fette, prima = miscela(ricetta, a.durata,
                                                       a.doppia, resta)
            riassunto(esiti, quanti, ricetta)
        else:
            esiti, rossi, muti, bk = risveglio(a.sature, a.ferme, a.durata,
                                               resta, a.dopo)
    finally:
        _log("⛔ LA MACCHINA SI RIMETTE COM'ERA")
        for i in range(1, 12):
            B.root("pkill -u %d -f 04-b30-scena; pkill -u %d -f "
                   "'nautilu[s]|gnome-termina[l]'; true" % (B.uid(i), B.uid(i)))
        # ⛔⛔ SOLO I MIEI CLIENTI, E NON E' UNA RIFINITURA — `[M]` 25 agosto
        #     2026.  La riga di prima era `pkill -f '10-b92-cliente[.]py
        #     --cliente'`, ereditata da 10-b92: un modello **GLOBALE**.  ⚠ Ma
        #     `10-b92-cliente.py` e' il nome che usano TUTTI gli agenti della
        #     fase, e in questo giro gli utenti sono per giunta CONDIVISI ⇒
        #     quella riga ammazza i clienti dei vicini.  `[M]` A fine giro, sulla
        #     macchina, quel modello trovava **24 clienti, tutti di «10b6»** —
        #     l'agente che aveva appena preso il lucchetto e stava misurando.
        #     Non li ho uccisi solo perche' avevo sgomberato PRIMA che nascessero.
        #   ⭐ E' la cura gia' scritta in `fasi/10-…md` §6.3: *«chiude SOLO le
        #     proprie sessioni — `09-b71` chiudeva con `pkill -f
        #     01-b3-cliente.py`, che in fase 10 ammazzerebbe i clienti dei
        #     vicini»*.  ⇒ Si riconoscono dal GIORNALE, che porta la mia
        #     cartella di lavoro nel nome, e la classe di caratteri impedisce al
        #     modello di combaciare con la propria riga di comando.
        B.root("pkill -f -- '--giornale [%s]%s/' ; true"
               % (B.DENTRO_LAV[0], B.DENTRO_LAV[1:]))
        time.sleep(3)
        B.chiudi_palchi(11)
        if luc:
            luc.molla(B.IO_SONO)

    nome = ("10-b98-%s.json" % ("".join(ricetta) if a.passo == "miscela"
                                else "risveglio-%dS-%dF" % (a.sature, a.ferme)))
    with open(os.path.join(FUORI, nome), "w") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1, default=str)
    _inf("esiti in %s/%s" % (FUORI, nome))

    _log("IL VERDETTO — %d rossi · %d non giudicati" % (len(rossi), len(muti)))
    for r in rossi[:40]:
        _ko(r)
    for m in muti[:40]:
        _dub(m)
    if rossi:
        return 1
    if muti:
        return 3
    _ok("⭐ tutti i predicati hanno fatto quel che era scritto prima")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
