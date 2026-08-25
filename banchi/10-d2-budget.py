#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-d2-budget — ⭐⭐⭐ IL BANCO DEL BUDGET, **SCRITTO PRIMA CHE IL BUDGET ESISTA**.

    porta 8260 · utenti `provadec4` (1103) `provadec5` (1104) `provadec6` (1105)
    e `provamt1`…`provamt11` ⛔ **CONDIVISI** solo quando servono i dieci
    albero `/media/REMOTIX/src/10d2-src` · lavoro `/media/REMOTIX/tmp/10d2`
    unita' `remotix-8260` · lucchetto GPU `10-d2`

    bash    banchi/10-d2-lancia.sh certifica  ⭐ a secco: NIENTE macchina, NIENTE GPU
    bash    banchi/10-d2-lancia.sh prepara    utenti + sorgenti + compila
    bash    banchi/10-d2-lancia.sh dichiara   ⭐ che cosa il BINARIO sa fare
    bash    banchi/10-d2-lancia.sh fisico     ⭐ D2 e D6-fisico: ZERO GPU
    bash    banchi/10-d2-lancia.sh vero       ⛔ tutte e sei: VUOLE il lucchetto
    python3 banchi/10-d2-budget.py oracolo --dentro 1920x1080,1920x1080 \
            --nuovo 1920x1080 --budget 970 --riserva 0.5 --ritardo 10

═══════════════════════════════════════════════════════════════════════════════
⭐⭐⭐ PERCHE' ESISTE, E PERCHE' ADESSO — `PIANO.md` §0.1
═══════════════════════════════════════════════════════════════════════════════

*«Il banco si scrive PRIMA di sviluppare.»*  Mentre questo file veniva scritto,
un altro incarico stava scrivendo il budget nel prodotto.  ⛔ Questo banco e'
scritto **contro la specifica**, non contro il suo codice — cosi' quando i due
si incontrano **il banco puo' dire di no**.

⛔⛔ E se il banco non sa dire di no, il budget entra nel prodotto senza che
    nessuno l'abbia messo alla prova.  ⇒ `--certifica` non e' un accessorio:
    e' il prodotto di questo incarico.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LA SPECIFICA CONTRO CUI QUESTO BANCO GIUDICA — verbatim, e in COSTANTI
═══════════════════════════════════════════════════════════════════════════════

    regge(dentro, nuovo)  ⟺  domanda(dentro) + costo(nuovo)  ≤  C × (1 − riserva)
                              E  il ritardo di chi e' dentro sta sotto la soglia

  · la grandezza      ⛔ **pixel di COMPOSIZIONE** (`tela × cadenza`), **non**
                      di codifica.  §6.11: il soffitto e' 0,97 Gpixel/s e a
                      saturarlo e' `gnome-shell`, non noi;
  · `--budget-mpixel-s N`  il limite fisico dichiarato · ⛔ predefinito **`0` =
                      SPENTO** (`CODER.md` **I6**);
  · `--tetto-sessioni N`   il tetto **amministrativo** · predefinito **10**;
  · `--riserva F`     la manopola, 0-1 · predefinito **0,5**;
  · il rifiuto        **`CONGEDO` con `BUDGET_PIENO 0x06`**, col dettaglio nel
                      corpo · ⛔ `0x06` **si AGGIUNGE** a `0x0E`, non lo
                      sostituisce (§8.1 D5);
  · la soglia del ritardo  **22,9 ms** — `[M]` sano ≤ 13,1, rotto ≥ 39,9,
                      **nessuna sovrapposizione** (§6.9).

⚠ **SE LA SPECIFICA CAMBIA NOME O FRASE, SI CAMBIA UNA COSTANTE IN TESTA**, non
  si riscrive il banco: tutto quel che il prodotto espone vive nel blocco
  `SPEC` qui sotto — nomi delle opzioni, codici, predefiniti, soglie, e le
  parole che la riga d'avvio deve contenere.  ⛔ Non c'e' una sola stringa del
  prodotto scritta a mano piu' in giu' nel file.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LE SEI DOMANDE, e per ciascuna IL ROSSO CHE DEVE SAPER DARE
═══════════════════════════════════════════════════════════════════════════════

 **D1 · col budget SPENTO, il difetto c'e' ancora?**
     `[M]` §6.5: l'ottavo entra con **`negati 0`** e tutti vanno a **1,5 fot/s**.
     ⛔ Se il banco NON ritrova questo, **non sta misurando niente** — e lo dice
     con un rosso, non con un silenzio.

 **D2 · chi arriva di troppo riceve `BUDGET_PIENO`?**
     ⛔ Letto **sul filo, nel client** — non nel registro del server: §6.4 ha
     imparato che leggere dove la cosa *parte* invece che dove *arriva* fa
     ritirare un rilievo intero (la capsula «0 spedite» era vera per `aioquic`,
     falsa per Firefox).

 **D3 · ⛔⛔ chi era dentro NON peggiora?**
     `DECISIONI.md` §4.6-bis e l'invariante **I1**.  Appaiato: **prima, durante,
     dopo**.  ⚠ E `LEZIONI.md` §1.34: **le chiavi restano a ZERO** (`[M]` 0 su
     8 741, anche dentro il crollo) ⇒ ⭐ **la colonna che avvisa e' il RITARDO**,
     e un predicato che guardasse le sole chiavi sarebbe verde per costruzione.

 **D4 · ⭐ dieci sessioni FERME devono ENTRARE**
     `[M]` §6.16: costano **0,01 %** l'una e **+0,2 %** a chi lavora.
     ⛔ Un budget che le rifiuta sbaglia quanto uno che ammette l'ottavo che fa
     crollare tutto: e' il **falso no**, il lato che costa un utente.

 **D5 · ⛔⛔ il RISVEGLIO**
     `[M]` §6.16: otto ferme ammesse a 0,01 % l'una si accendono **in 19 ms** e
     chiedono il **130 %**; chi lavorava perde il **96 %**.  ⭐ Con `riserva 0,5`
     lo sforamento deve restare **~2×**.
     ⚠ **Questa e' la cella che il budget NON puo' prevedere**: si misura
     **quanto la riserva lo contiene**, non che lo eviti.

 **D6 · il tetto amministrativo e quello fisico sono DUE cose**
     `--tetto-sessioni 3` con budget larghissimo ⇒ il quarto riceve **`0x0E`**;
     budget stretto con tetto largo ⇒ **`0x06`**.
     ⛔ **Due motivi diversi per due fatti diversi**, ed e' §8.1 **D5**.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ CHE COSA QUESTO BANCO **NON** SA DIRE — dichiarato in testa, non in fondo
═══════════════════════════════════════════════════════════════════════════════

 1. ⛔ **NON dice se il budget e' TARATO BENE.**  Dice se il prodotto obbedisce
    alla regola con la capacita' che **gli e' stata dichiarata**.  Il numero
    vero della macchina e' un'altra misura (§6.11: 0,97 Gpixel/s), e §8.1 **D8**
    dice che `--budget-mpixel-s` **non si auto-tara**: prima che la macchina
    abbia ceduto una volta, la capacita' e' **un limite inferiore, non un
    soffitto**.  ⇒ Qui la capacita' e' un **ingresso**, non un risultato.

 2. ⛔ **NON osserva la COMPOSIZIONE.**  §6.9 punto 6: i compositori disegnano
    ~958 Mpixel/s mentre noi ne consegniamo 21,6, e **il prodotto non li vede**.
    ⇒ `costo(nuovo)` qui e' `tela × cadenza` **chieste**, cioe' la stessa cosa
    che il prodotto ha in mano all'ammissione — non il lavoro vero della GPU.
    Un budget che governasse i pixel veri della macchina misurerebbe un'altra
    grandezza, e questo banco **non lo saprebbe distinguere**.

 3. ⛔ **NON sa in che ORDINE i due limiti debbano mordere** quando mordono
    tutt'e due insieme.  La specifica non lo dice.  ⇒ Quando SOLO
    l'amministrativo morde si pretende `0x0E`; quando SOLO il fisico morde si
    pretende `0x06`; quando mordono **insieme** si accetta **l'uno o l'altro**,
    purche' sia **sempre lo stesso** — e questa tolleranza e' **dichiarata**,
    non nascosta.

 4. ⛔ **NON dice «si vede peggio».**  Nessun banco lo dice: quello lo dice il
    regista (§10).

 5. ⚠ **La soglia dei 22,9 ms e' della SCENA SATURA a 1080p** (§6.9), e il
    ritardo del padre e' un **maggiorante** del tempo di ritenuta: prudente nel
    verso giusto, ma non e' la grandezza del meccanismo.  Su un'altra tela o su
    un'altra scena **va rimisurata**, e il banco lo stampa ogni volta.

 6. ⚠ **Il RISVEGLIO e' misurato a OTTO ferme** (§6.16): fra una e otto **non
    si sa dov'e' il ginocchio**.  ⇒ D5 dice quanto la riserva contiene *quel*
    risveglio, non tutti.

 7. ⛔ **NON misura la rete vera**: i clienti girano sulla stessa macchina, su
    `lo` (MTU 65536).  Il filo e' **contato, non provato**.

 8. ⚠ **Le occupazioni della GPU sono TEMPO OCCUPATO, non lavoro fatto**, e il
    tempo dipende dalla frequenza della GT (§6.1 §CLOCK, fattore **3,8**).  ⇒
    Non si confrontano due fotografie con GT diverse.

 9. ⛔⛔ **E il buco piu' onesto di tutti, al 25 agosto 2026**: la parte che
    RACCOGLIE i fatti di **D1, D3, D4 e D5 non e' mai stata fatta girare** —
    il lucchetto della GPU era di un altro agente per tutto il turno, e il
    terreno si e' rifiutato di partire (⭐ come deve).  ⇒ Di quelle quattro e'
    provato **il giudizio** (85 guasti su 85), non il **raccoglitore**.
    ⚠ Chi le fa girare per primo si aspetti di pagare qualche difetto di banco:
    e' quel che questo giro ha visto succedere a tutti gli altri.
    `[M]` Girate davvero, e verdi nel senso giusto: **D2** e il braccio
    **fisico** di **D6** — tutt'e due **«non ho misurato»**, perche' oggi il
    server non conosce `--budget-mpixel-s`.

═══════════════════════════════════════════════════════════════════════════════
⭐ CHE COSA NON E' RISCRITTO — tre banchi si IMPORTANO, non si copiano
═══════════════════════════════════════════════════════════════════════════════

  · `10-b93-pieno.py` (45/45) — ⭐ **come si legge un `CONGEDO` NEL CLIENT**,
    il lettore della traccia §11.1, il ponte fra i due orologi, `p_ha_morso`
    (⛔ *«il respinto che non arriva a provarci»*), `p_dettaglio_nel_corpo`;
  · `10-b98-mista.py` (50/50) — le **miscele di ruoli** `S`/`T`/`F`, la GPU per
    sessione, ⭐ **il risveglio col metro a bucket**;
  · `10-b92-dieci.py` (75/75, importato da 10-b98) — la salita a gradini, ogni
    sessione a ogni gradino, l'**ancora**, `p_scena_morde`, `p_I1`, la resa.

⛔⛔ **E nessuno dei tre si tocca.**  Non una riga: cosi' i loro `--certifica`
    restano quelli che erano, e si rifanno girare **da qui**, in coda ai miei.

═══════════════════════════════════════════════════════════════════════════════
⛔ L'ISOLAMENTO, E LE DUE TRAPPOLE DI COORDINAMENTO CHE HANNO MORSO DAVVERO
═══════════════════════════════════════════════════════════════════════════════

 · ⛔ **Lo sgombero non ha modelli globali** (§7.3): a fine giro un modello
   globale ereditato combaciava con **24 clienti vivi di un altro banco**.
   ⇒ Qui ogni `pkill` porta `-u <uid mio>` **oppure** un modello che nomina la
   **mia** cartella di lavoro.  E i modelli si scrivono `campagn[a]`, perche'
   `pgrep -f`/`pkill -f` **acchiappano la riga di comando che li esegue**.
 · ⛔ **La parola d'ordine non si rifa' a un utente che esiste gia'** (§5.4):
   l'ultimo che chiama vince, gli altri leggono «credenziali errate» su una
   macchina sana, ⛔⛔ **e ogni respinto consuma uno dei tre tentativi del ban
   per INDIRIZZO, che dura dodici ore.**  Il terreno lo sa (`RIFAI_PAROLA=1`
   per forzare) e questo banco **non forza mai**.

I CODICI D'USCITA — gli stessi degli altri banchi della fase:

    0   CONFORME       1   ⛔ almeno un rosso       2   uso/terreno/lucchetto
    3   ⛔ NON HO NIENTE DA GIUDICARE — ⚠ e **non e' un verde**
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
# ⛔⛔ L'ISOLAMENTO — PRIMA DEGLI IMPORT, CHE LEGGONO L'AMBIENTE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ 10-b92, 10-b93 e 10-b98 fissano porta, albero, lavoro e unita' **al momento
#    dell'import** (sono costanti di modulo).  ⇒ Se questo blocco stesse sotto
#    gli import, il banco girerebbe sulla porta 8100 e sull'albero di un altro
#    agente — e non darebbe rosso: darebbe **numeri, sull'albero sbagliato**.
for _chiave, _valore in (("PORTA", "8260"),
                         ("ALBERO", "/media/REMOTIX/src/10d2-src"),
                         ("LAV", "/media/REMOTIX/tmp/10d2"),
                         ("DENTRO_ALB", "/srv/src/10d2-src"),
                         ("DENTRO_LAV", "/srv/remotix/tmp/10d2"),
                         ("UNITA", "remotix-8260"),
                         ("IO_SONO", "10-d2"),
                         ("SHM_BASE", "10d2"),
                         ("FUORI", "/tmp/10-d2")):
    os.environ.setdefault(_chiave, _valore)

PORTA = int(os.environ["PORTA"])
LAV = os.environ["LAV"]
ALB = os.environ["ALBERO"]
UNITA = os.environ["UNITA"]
IO_SONO = os.environ["IO_SONO"]
FUORI = os.environ["FUORI"]
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
LUCCHETTO = os.environ.get("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")

VERDE, ROSSO_C, GIALLO, GRIGIO = ("\033[1;32m", "\033[1;31m",
                                  "\033[1;33m", "\033[0m")


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO_C, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ `SPEC` — LA SPECIFICA IN COSTANTI, E IL SOLO POSTO DA CAMBIARE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ L'altro incarico, se dovra' cambiare un nome o una frase, **lo dichiarera'**.
#    ⇒ Questo banco si ri-punta cambiando QUI, non riscrivendolo.  Ogni voce
#    porta accanto la fonte, cosi' chi cambia sa che cosa sta contraddicendo.
class SPEC:
    # ── le tre opzioni, coi nomi esatti ───────────────────────────────────
    OPZ_BUDGET = "--budget-mpixel-s"     # §8.1 D3 · il limite FISICO
    OPZ_TETTO = "--tetto-sessioni"       # §8.1 D7 · il tetto AMMINISTRATIVO
    OPZ_RISERVA = "--riserva"            # §8.1 D4 · la manopola del regista

    # ── i predefiniti ─────────────────────────────────────────────────────
    # ⛔ `CODER.md` I6: quel che cambia cio' che l'utente VEDE nasce SPENTO.
    BUDGET_PREDEFINITO = 0               # 0 = SPENTO, nessun tetto di capacita'
    TETTO_PREDEFINITO = 10
    RISERVA_PREDEFINITA = 0.5

    # ── i due motivi, e ⛔ si AGGIUNGONO, non si sostituiscono (§8.1 D5) ───
    COD_BUDGET_PIENO = 0x06              # `rcp.h` RCP_BUDGET_PIENO — il FISICO
    COD_NON_SERVIBILE = 0x0E             # RCP_SESSIONE_NON_SERVIBILE — l'AMMIN.

    # ── la soglia del ritardo · `[M]` §6.9, MISURATA e non scelta ─────────
    #    sano ≤ 13,1 ms · rotto ≥ 39,9 ms · ⭐ nessuna sovrapposizione
    SOGLIA_RITARDO_MS = 22.9
    RITARDO_SANO_MAX_MS = 13.1
    RITARDO_ROTTO_MIN_MS = 39.9

    # ── le parole che la riga d'avvio DEVE contenere, acceso E spento ─────
    # ⛔ `CODER.md` §2-bis: «con la riga d'avvio che dichiara il valore in
    #    vigore, acceso E spento».  Senza questa riga il banco NON SA con che
    #    capacita' il prodotto stia giudicando ⇒ non giudica.
    PAROLA_AVVIO_BUDGET = "budget"
    PAROLA_AVVIO_TETTO = "tetto"
    PAROLA_AVVIO_RISERVA = "riserva"

    # ── la grandezza ⛔ pixel di COMPOSIZIONE, non di codifica (§S.1) ──────
    GRANDEZZA = "Mpixel/s di COMPOSIZIONE (tela × cadenza)"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LE SOGLIE DEL BANCO — ⛔ MIE, non del prodotto, e si dichiarano
# ═══════════════════════════════════════════════════════════════════════════
#
# ⚠ I numeri grezzi si stampano SEMPRE accanto al giudizio, cosi' chi legge
#   puo' non essere d'accordo con la soglia senza perdere la misura.
class MIO:
    # D1 — il dirupo di §6.5: all'ottavo gradino tutti a 1,45-1,72 fot/s
    GRADINO_DIRUPO = 8
    FPS_DIRUPO = 2.5          # sotto questo, «il dirupo c'e'»
    FPS_SANO_MIN = 20.0       # sopra questo, ai primi gradini, «sta bene»

    # D3 — I1.  ⭐ La colonna che avvisa e' il RITARDO (§1.34), non le chiavi.
    I1_CALO_FPS = 0.15        # oltre il 15 % di calo: violato (come 10-b92)
    I1_RITARDO_FATTORE = 2.0  # il ritardo non piu' del doppio di «prima»
    I1_QUOTA_CHIAVI = 0.02    # ⚠ testimone: se sale e' rosso; se resta a zero
                              #   NON basta a dare verde — lo dice il riquadro

    # D4 — una ferma e' ferma: `[M]` §6.12 203-389 B/fot, 0,02 fot/s
    FERMA_BYTE_MAX = 600.0
    FERMA_FPS_MAX = 3.0
    # `[M]` §6.16: dieci ferme costano +0,2 % a chi lavora ⇒ tolleranza larga
    # cinque volte quel che si e' misurato, e si dichiara.
    D4_CALO_AMMESSO = 0.05

    # D5 — il risveglio.  ⛔ «Svegliata» si giudica sulla SOLLECITAZIONE.
    #    `[M]` §6.16: i fotogrammi passano da 266 B a ~5 kB — 18 volte.
    RISVEGLIO_FATTORE_BYTE = 5.0   # tre volte piu' prudente del misurato
    RISVEGLIO_ACCENSIONE_MS = 500.0  # `[M]` 19 ms; qui si tollera 500
    # ⭐ `[M]` §6.9/§6.16: con riserva 0,5 lo sforamento resta ~2×.
    SFORAMENTO_ATTESO = 2.0
    SFORAMENTO_MAX = 2.5           # il tetto del predicato, dichiarato

    # la scena deve MORDERE prima di ogni giudizio (`LEZIONI.md` §1.30)
    BYTE_VIVI_SATURA = 4000.0
    DISEGNI_VIVI = 2.0


# ⛔ Il ferro, accanto a ogni numero, sempre (`CODER.md` §1-bis).
FERRO = ("i5-13500T · Intel UHD 730 INTEGRATA (`renderD128`, la Radeon e' "
         "chiusa da udev, §4.6-quinquies) · 31 GB")


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ GLI IMPORT — e si CONTROLLANO, invece di darli per riusciti
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Un modulo che si carica a meta' non alza: perde solo dei nomi, e il banco
#    stampa un dizionario vuoto invece di dare rosso (`REVIEWER.md` E14).
def _carica(nome, file_):
    spec = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file_))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


W = _carica("b93", "10-b93-pieno.py")      # il filo: come si legge un CONGEDO
M = _carica("b98", "10-b98-mista.py")      # le miscele e il risveglio
B = M.B                                    # 10-b92: la salita a gradini

for _mod, _nome, _quali in (
        (W, "10-b93-pieno.py",
         ("p_ha_morso", "p_motivo_sul_filo", "p_dettaglio_nel_corpo",
          "corpo_congedo", "fabbrica_traccia", "leggi_canale_qui",
          "_si", "_no", "_muto", "certifica", "MOTIVO_GIUSTO", "MOTIVO_BUDGET",
          "dentro", "cliente_riga", "riempi", "riempi_e_aspetta",
          "aspetta_posti", "aspetta_tabella_vuota", "modello_cliente",
          "righe_registro", "registro_da", "righe_ancora", "root",
          "leggi_traccia_canale", "leggi_traccia_video", "spedisci_lettori",
          "offset_del_cliente", "spezza_in_finestre", "ancora_finestre",
          "sod_adesso_sul_server", "scena_accendi", "scena_spegni",
          "DENTRO", "RESPINTO", "TELA", "DENTRO_LAV")),
        (M, "10-b98-mista.py",
         ("risveglio", "risveglio_finto", "miscela", "miscela_finta",
          "p_ferma_e_ferma", "p_satura_satura", "p_I1_ritardo", "certifica",
          "bucket", "SOGLIA_FERMA_BYTE_S", "SOGLIA_FERMA_FPS")),
        (B, "10-b92-dieci.py",
         ("ha_misurato", "p_ancora", "p_scena_morde", "p_I1", "_fab",
          "ritardi", "certifica", "salita", "terreno", "_importa_b70",
          "BYTE_VIVI", "TELA", "root", "utente", "uid"))):
    for _n in _quali:
        if not hasattr(_mod, _n):
            raise SystemExit("⛔ NON MISURO: «%s» non c'e' in %s — l'import e' "
                             "riuscito a meta'" % (_n, _nome))

if B.PORTA != PORTA or B.LAV != LAV or W.PORTA != PORTA or W.LAV != LAV:
    raise SystemExit(
        "⛔ NON MISURO: i banchi importati si sono presi porta/lavoro che NON "
        "sono i miei — b92 %d/%s · b93 %d/%s · io %d/%s"
        % (B.PORTA, B.LAV, W.PORTA, W.LAV, PORTA, LAV))

# ⭐ I tre esiti, e sono gli stessi di tutti i banchi della fase:
#     (True,  perche)  l'atteso ha retto
#     (False, perche)  ⛔ rosso
#     (None,  perche)  ⚠ NON GIUDICO — ⛔ e non e' un verde educato
_si, _no, _muto = W._si, W._no, W._muto


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ L'ORACOLO — la specifica scritta come funzione, e giudica il PRODOTTO
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ QUESTA E' LA PARTE CHE RENDE IL BANCO INDIPENDENTE DAL CODICE DELL'ALTRO
#     INCARICO.  Il prodotto decide chi entra; l'oracolo dice chi **doveva**
#     entrare, secondo la formula, con gli stessi ingressi che il prodotto ha
#     in mano all'ammissione.  ⇒ Dal confronto nascono le due colonne che
#     contano:
#       · **falso SI'**  l'oracolo dice no, il prodotto ha ammesso  → il lato
#         che affama tutti (`[M]` §6.5: l'ottavo, e vanno tutti a 1,5 fot/s);
#       · **falso NO**   l'oracolo dice si', il prodotto ha rifiutato → il lato
#         che costa un utente (`[M]` §6.16: dieci ferme costano +0,2 %).
#
# ⚠ E l'oracolo NON e' un secondo prodotto: non si auto-tara, non misura, non
#   indovina.  Prende quel che gli si da' e, dove non gli e' stato dato,
#   ⛔ **torna `None`** invece di scegliere un predefinito comodo.
def costo_mpixel_s(larghezza, altezza, cadenza):
    """⛔ `costo(nuovo)` = **tela × cadenza**, in Mpixel/s di COMPOSIZIONE.

    ⚠ Non e' il lavoro vero della GPU (§6.9 punto 6: la composizione non e'
      osservabile dal prodotto): e' esattamente cio' che il prodotto ha in mano
      al `CIAO`, cioe' la stessa grandezza su cui deve saper decidere.
    """
    if not larghezza or not altezza or not cadenza:
        return None
    return larghezza * altezza * cadenza / 1e6


def regge(dentro, nuovo, capacita, riserva, ritardo_ms, tetto=None):
    """⭐ LA FORMULA, e torna QUATTRO cose, non due.

        regge  ⟺  domanda(dentro) + costo(nuovo)  ≤  C × (1 − riserva)
                  E  il ritardo di chi e' dentro sta sotto la soglia

    Ingressi:
      `dentro`     lista di costi in Mpixel/s (uno per sessione gia' ammessa);
      `nuovo`      il costo del richiedente, in Mpixel/s, oppure `None`;
      `capacita`   C in Mpixel/s.  ⛔ **`0` vuol dire SPENTO**, e spento non e'
                   «capacita' zero»: e' «nessun tetto di capacita'» (I6);
      `riserva`    F in [0,1];
      `ritardo_ms` il ritardo mediano di chi e' dentro, oppure `None`;
      `tetto`      il tetto amministrativo, oppure `None` per «non dichiarato».

    Torna `(verdetto, motivo_atteso, perche, numeri)`:
      verdetto  True = deve entrare · False = deve essere rifiutato ·
                ⛔ **None = non lo so**, e chi riceve non giudica.
      motivo    il codice di §8.2 che il rifiuto deve portare, o `None`.

    ⛔⛔ L'ORDINE NON E' UN DETTAGLIO, ed e' quello di §6.9: **prima il
        RITARDO, poi i pixel**.  `[M]` a otto sessioni il conto sui pixel dice
        *«c'e' posto per altre cinque»* mentre tutti stanno a 1,5 fot/s: la
        porta del ritardo e' l'unica cosa che salva quel caso.
    """
    num = {"dentro": len(dentro) if dentro is not None else None,
           "domanda_mpixel_s": None, "costo_nuovo_mpixel_s": nuovo,
           "capacita_mpixel_s": capacita, "riserva": riserva,
           "tetto_ammesso_mpixel_s": None, "ritardo_mediano_ms": ritardo_ms,
           "soglia_ritardo_ms": SPEC.SOGLIA_RITARDO_MS, "tetto_sessioni": tetto}

    if dentro is None:
        return (None, None, "⛔ NON SO: non mi e' stato detto chi e' dentro", num)
    if any(x is None for x in dentro):
        return (None, None, "⛔ NON SO: %d sessioni dentro su %d non hanno un "
                "costo misurato — ⚠ `None` non e' zero, e sommarle come zero "
                "direbbe «c'e' posto»"
                % (sum(1 for x in dentro if x is None), len(dentro)), num)
    domanda = sum(dentro)
    num["domanda_mpixel_s"] = domanda

    # ── 1 · il tetto AMMINISTRATIVO, che e' un'altra cosa dal fisico ──────
    # ⛔ §8.1 D5: due limiti diversi, DUE GESTI DIVERSI per l'utente.
    ammin = None
    if tetto is not None and len(dentro) >= tetto:
        ammin = ("il tetto amministrativo e' %d e dentro ce ne sono gia' %d"
                 % (tetto, len(dentro)))

    # ── 2 · il budget SPENTO ⇒ nessun tetto di CAPACITA' (I6) ─────────────
    if capacita is not None and capacita == 0:
        if ammin:
            return (False, SPEC.COD_NON_SERVIBILE,
                    "il budget e' SPENTO (%s 0) ma %s ⇒ rifiuto AMMINISTRATIVO"
                    % (SPEC.OPZ_BUDGET, ammin), num)
        return (True, None,
                "⭐ il budget e' SPENTO (%s 0): nessun tetto di capacita', e "
                "I6 vuole che spento voglia dire spento" % SPEC.OPZ_BUDGET, num)

    if capacita is None:
        return (None, None,
                "⛔ NON SO: la capacita' non e' stata dichiarata.  ⚠ §8.1 D8: "
                "prima che la macchina abbia ceduto una volta e' un LIMITE "
                "INFERIORE, non un soffitto — e un limite inferiore non si "
                "usa per dire di no", num)
    if riserva is None:
        return (None, None, "⛔ NON SO: la riserva non e' stata dichiarata "
                "(%s)" % SPEC.OPZ_RISERVA, num)
    if not (0.0 <= riserva <= 1.0):
        return (None, None, "⛔ NON SO: riserva %r fuori da [0,1]" % riserva, num)

    limite = capacita * (1.0 - riserva)
    num["tetto_ammesso_mpixel_s"] = limite

    # ── 3 · ⛔⛔ LA PORTA DEL RITARDO, e viene PRIMA dei pixel ─────────────
    if ritardo_ms is None:
        if dentro:
            return (None, None,
                    "⛔ NON SO: il ritardo di chi e' dentro non e' stato "
                    "misurato, e §6.9 dice che senza quello il conto sui pixel "
                    "mente proprio quando serve (`[M]` a otto sessioni diceva "
                    "«c'e' posto per altre cinque» con tutti a 1,5 fot/s)", num)
        # ⭐ Nessuno dentro: non c'e' nessun ritardo da misurare, e non e' un buco.
        ritardo_ms = 0.0
        num["ritardo_mediano_ms"] = 0.0
    if ritardo_ms >= SPEC.SOGLIA_RITARDO_MS:
        return (False, SPEC.COD_BUDGET_PIENO,
                "⛔ IL RITARDO di chi e' dentro e' %.1f ms, sopra la soglia di "
                "%.1f (`[M]` §6.9: sano ≤ %.1f, rotto ≥ %.1f, nessuna "
                "sovrapposizione) ⇒ la macchina e' gia' oltre, e il conto sui "
                "pixel non conta"
                % (ritardo_ms, SPEC.SOGLIA_RITARDO_MS,
                   SPEC.RITARDO_SANO_MAX_MS, SPEC.RITARDO_ROTTO_MIN_MS), num)

    # ── 4 · e infine i PIXEL ──────────────────────────────────────────────
    if nuovo is None:
        return (None, None, "⛔ NON SO: il costo del richiedente non e' stato "
                "calcolato (tela o cadenza mancanti)", num)
    if domanda + nuovo > limite:
        motivo = SPEC.COD_BUDGET_PIENO
        perche = ("⛔ %.1f + %.1f = %.1f Mpixel/s, sopra %.1f × (1 − %.2f) = "
                  "%.1f ⇒ rifiuto FISICO"
                  % (domanda, nuovo, domanda + nuovo, capacita, riserva, limite))
        if ammin:
            # ⛔ Mordono TUTT'E DUE.  La specifica non dice chi vince ⇒ il banco
            #    lo dichiara e accetta l'uno o l'altro (buco n. 3 in testa).
            return (False, None,
                    perche + " · ⚠ E MORDE ANCHE L'AMMINISTRATIVO (%s): la "
                    "specifica non dice quale dei due vinca, e questo banco "
                    "accetta l'uno o l'altro purche' sia sempre lo stesso"
                    % ammin, num)
        return (False, motivo, perche, num)
    if ammin:
        return (False, SPEC.COD_NON_SERVIBILE,
                "⭐ di capacita' ce n'e' (%.1f + %.1f ≤ %.1f) ma %s ⇒ rifiuto "
                "AMMINISTRATIVO, che e' un altro fatto"
                % (domanda, nuovo, limite, ammin), num)
    return (True, None,
            "⭐ %.1f + %.1f = %.1f ≤ %.1f × (1 − %.2f) = %.1f Mpixel/s, e il "
            "ritardo di chi e' dentro e' %.1f ms (soglia %.1f)"
            % (domanda, nuovo, domanda + nuovo, capacita, riserva, limite,
               ritardo_ms, SPEC.SOGLIA_RITARDO_MS), num)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LE PORTE CHE VENGONO PRIMA DI OGNI GIUDIZIO
# ═══════════════════════════════════════════════════════════════════════════
def p_riga_d_avvio(avvio):
    """⛔ LA RIGA D'AVVIO DICHIARA IL VALORE IN VIGORE, **acceso E spento**.

    `CODER.md` §2-bis lo impone per ogni opzione nuova, e qui non e' una
    formalita': ⛔ **senza quella riga il banco non sa con che capacita' il
    prodotto stia giudicando**, e un oracolo tarato su un numero diverso da
    quello in vigore darebbe falsi sì e falsi no che sono suoi, non del
    prodotto.  ⇒ Senza, **non si giudica**.

    `avvio` = `{"budget": …, "tetto": …, "riserva": …, "riga": "…"}`, letto dal
    registro del server (non dagli argomenti che gli abbiamo passato: ⛔ quello
    sarebbe leggere dove la cosa parte invece che dove arriva, §6.4).
    """
    if not avvio:
        return _muto("il registro del server non e' stato letto: non giudico")
    riga = (avvio.get("riga") or "")
    if not riga:
        return _muto("⛔ NON HO MISURATO: il server non ha scritto nessuna riga "
                     "d'avvio che dichiari il budget in vigore.  ⚠ `CODER.md` "
                     "§2-bis la vuole **acceso E spento**, e senza di lei "
                     "l'oracolo girerebbe su un numero che ho scelto io")
    manca = [p for p in (SPEC.PAROLA_AVVIO_BUDGET, SPEC.PAROLA_AVVIO_TETTO,
                         SPEC.PAROLA_AVVIO_RISERVA) if p not in riga.lower()]
    if manca:
        return _no("⛔ la riga d'avvio non nomina %s: «%s»"
                   % (" ne' ".join("«%s»" % m for m in manca), riga.strip()))
    valori = {k: avvio.get(k) for k in ("budget", "tetto", "riserva")}
    if any(v is None for v in valori.values()):
        return _muto("⛔ la riga d'avvio c'e' ma non se ne sono letti i valori "
                     "(%s): non giudico su meta' lettura" % valori)
    return _si("la riga d'avvio dichiara %s=%s · %s=%s · %s=%s — «%s»"
               % (SPEC.OPZ_BUDGET, valori["budget"], SPEC.OPZ_TETTO,
                  valori["tetto"], SPEC.OPZ_RISERVA, valori["riserva"],
                  riga.strip()))


def p_la_scena_ha_morso(sessioni, scena="satura"):
    """⛔⛔ QUANTA SOLLECITAZIONE E' ARRIVATA — `LEZIONI.md` §1.30.

    ⚠ E si guarda **il byte per fotogramma E i disegni della scena**, non il
      ritmo: `[M]` §6.12 il pavimento dei 25 fot/s ha dato **rosso con UNA
      sessione e la GPU al 2,2 %** — e ⛔ **tutti e 66 i rossi erano del metro,
      zero del prodotto**.  ⭐ E §6.12 n.4: una scena CONGELATA faceva 1 368
      byte/fotogramma, cioe' **sopra** il pavimento dei byte ⇒ i soli byte le
      avrebbero dato verde.  **Chi la prende sono i disegni.**
    """
    if not sessioni:
        return _muto("nessuna sessione da guardare")
    vivi = {i: n for i, n in sessioni.items() if B.ha_misurato(n)}
    if not vivi:
        return _muto("nessuna sessione ha un numero: non giudico")
    if scena == "ferma":
        # ⭐ Qui «mordere» vuol dire il contrario: la scena deve stare FERMA.
        return p_le_ferme_sono_ferme(sessioni)
    fiacchi, disegni_muti, ok = [], [], []
    for i, n in sorted(vivi.items()):
        b = n.get("byte_per_fotogramma")
        d = ((n.get("disegni") or {}).get("disegni_s"))
        if b is None:
            fiacchi.append("s%d: byte/fotogramma NON letto" % i)
            continue
        if d is None:
            disegni_muti.append("s%d" % i)
        elif d < MIO.DISEGNI_VIVI:
            fiacchi.append("s%d: la scena disegna %.2f/s (minimo %.1f) — "
                           "⛔ CONGELATA, e i byte da soli non l'avrebbero "
                           "presa (%.0f B/fot)" % (i, d, MIO.DISEGNI_VIVI, b))
            continue
        if b < MIO.BYTE_VIVI_SATURA:
            fiacchi.append("s%d: %.0f B/fotogramma, sotto %.0f — la scena non "
                           "morde" % (i, b, MIO.BYTE_VIVI_SATURA))
        else:
            ok.append("s%d %.0f B/fot%s"
                      % (i, b, "" if d is None else " · %.1f disegni/s" % d))
    if fiacchi:
        return _muto("⛔ NON HO MISURATO: la scena non ha morso — %s.  ⚠ Un "
                     "giudizio su una prova che non morde sembra un risultato"
                     % " · ".join(fiacchi))
    if disegni_muti:
        return _muto("⛔ NON HO MISURATO: i disegni della scena non si sono "
                     "letti per %s, e i soli byte non bastano (§6.12 n.4: una "
                     "scena congelata sta SOPRA il pavimento dei byte)"
                     % ", ".join(disegni_muti))
    return _si("la scena ha morso su tutte e %d: %s" % (len(ok), " · ".join(ok)))


def p_le_ferme_sono_ferme(sessioni):
    """⛔ E il verso opposto: una «ferma» che si muove non e' una ferma.

    `[M]` §6.12: una ferma vale **203-389 B/fotogramma** e **0,02 fot/s**.
    ⚠ Le due colonne servono tutt'e due: un **orologio** sul desktop la
      smaschera dal ritmo, un **salvaschermo** dai byte (§6.16, i guasti).
    """
    if not sessioni:
        return _muto("nessuna sessione da guardare")
    guai, ok = [], []
    for i, n in sorted(sessioni.items()):
        if not B.ha_misurato(n):
            guai.append("s%d non ha un numero (%s)"
                        % (i, (n or {}).get("esito", "manca")))
            continue
        b, f = n.get("byte_per_fotogramma"), n.get("fps")
        if b is None or f is None:
            guai.append("s%d: byte/fotogramma %r · fot/s %r NON letti" % (i, b, f))
            continue
        if b > MIO.FERMA_BYTE_MAX or f > MIO.FERMA_FPS_MAX:
            return _no("⛔ s%d non era FERMA: %.0f B/fotogramma (tetto %.0f) e "
                       "%.2f fot/s (tetto %.1f) ⇒ questa non e' la scena che "
                       "D4/D5 misurano"
                       % (i, b, MIO.FERMA_BYTE_MAX, f, MIO.FERMA_FPS_MAX))
        ok.append("s%d %.0f B/fot · %.2f fot/s" % (i, b, f))
    if guai:
        return _muto("⛔ NON HO MISURATO: %s" % " · ".join(guai))
    return _si("tutte e %d erano ferme davvero: %s" % (len(ok), " · ".join(ok)))


def p_motivo_atteso(tentativi, atteso, e_non=()):
    """⛔⛔ IL MOTIVO, LETTO **SUL FILO NEL CLIENT** — e il rosso e' SUL BYTE.

    ⚠ `10-b93-pieno.py` ha gia' `p_motivo_sul_filo`, ma quello ha `0x0E`
      **incastonato**: qui il motivo atteso e' un parametro, perche' D2 pretende
      `0x06` e D6 pretende `0x0E` **nella stessa giornata**.  ⇒ Un solo
      predicato, due attese, e il rosso nomina i due byte.

    ⛔ E si legge dove la cosa **ARRIVA**, non dove parte: §6.4 ha fatto
       ritirare un rilievo intero perche' i conti erano stati presi dal lato che
       manda (*«0 capsule spedite»* era vero per `aioquic`, falso per Firefox).
    """
    if not tentativi:
        return _muto("nessun tentativo: non giudico")
    senza = [t for t in tentativi if t.get("motivo") is None]
    if senza:
        return _muto("⛔ NON HO MISURATO: %d tentativi su %d non portano nessun "
                     "motivo LETTO SUL FILO — la traccia §11.1 non si e' letta, "
                     "e ⚠ il registro del server NON e' il filo"
                     % (len(senza), len(tentativi)))
    visti = sorted({t["motivo"] for t in tentativi})
    if visti == [atteso]:
        return _si("tutti e %d i tentativi hanno ricevuto CONGEDO %#04x sul "
                   "filo, nel client" % (len(tentativi), atteso))
    for cattivo in e_non:
        if cattivo in visti:
            return _no("⛔⛔ IL MOTIVO SBAGLIATO SUL BYTE: e' arrivato %#04x "
                       "dove va %#04x.  ⚠ §8.1 D5: i due motivi **si aggiungono, "
                       "non si sostituiscono** — sono due limiti diversi e due "
                       "gesti diversi per l'utente.  Motivi visti: %s"
                       % (cattivo, atteso, [hex(m) for m in visti]))
    return _no("⛔ motivo inatteso sul filo: %s (atteso solo %#04x)"
               % ([hex(m) for m in visti], atteso))


def p_corpo_non_vuoto(tentativi):
    """⛔ Il corpo del `CONGEDO` porta il dettaglio — e vale per `0x06` come
       gia' vale per `0x0E` (`RCP.md` riga 2301).

    ⚠ «vuoto» e «non letto» sono **due fatti diversi** (`LEZIONI.md` §1.9): il
      primo e' un rosso del prodotto, il secondo e' un buco del banco — e il
      predicato di 10-b93 li separa gia', per questo si riusa invece di
      riscriverlo.
    """
    return W.p_dettaglio_nel_corpo(tentativi)


def p_corpo_porta_i_numeri(tentativi):
    """⭐ E il dettaglio DICE QUALCOSA: la specifica vuole «col dettaglio nel
       corpo», e un dettaglio che non porta ne' la domanda ne' la capacita' e'
       un numero in meno nel registro di domani.

    ⚠ Questo predicato e' **piu' esigente della specifica**, e lo dichiara: da'
      **giallo** (non giudico) invece che rosso quando il corpo c'e' ma non
      porta cifre, cosi' non si accusa il prodotto di una cosa che nessuno gli
      ha chiesto per iscritto.
    """
    if not tentativi:
        return _muto("nessun tentativo")
    senza_cifre = [t for t in tentativi
                   if not any(c.isdigit() for c in (t.get("dettaglio") or ""))]
    if senza_cifre:
        return _muto("⚠ il corpo c'e' ma non porta nessuna cifra in %d "
                     "tentativi su %d: «%s».  ⭐ Non e' un rosso — la specifica "
                     "dice «col dettaglio nel corpo» e non dice quali numeri — "
                     "ma senza domanda e capacita' la riga di domani non si "
                     "sapra' rileggere"
                     % (len(senza_cifre), len(tentativi),
                        (senza_cifre[0].get("dettaglio") or "")[:80]))
    return _si("il corpo porta le cifre in tutti e %d: «%s»"
               % (len(tentativi), (tentativi[0].get("dettaglio") or "")[:120]))


def p_oracolo_contro_prodotto(decisioni):
    """⭐⭐⭐ IL CONFRONTO CHE DA' LE DUE COLONNE — falsi SI' e falsi NO.

    `decisioni` = lista di
        `{"chi": …, "atteso": True|False|None, "ammesso": True|False|None,
          "perche_oracolo": …}`

    ⛔ E i due errori NON si sommano in un numero solo: costano cose diverse.
       · **falso SI'**  → chi c'era gia' viene affamato (`[M]` §6.5: l'ottavo
         porta tutti a 1,5 fot/s);
       · **falso NO**   → un utente che ci stava resta fuori (`[M]` §6.16:
         dieci ferme costano +0,2 %), e ⚠ **nessuno se ne accorge**, perche'
         l'utente respinto non e' nella stanza.
    """
    if not decisioni:
        return _muto("nessuna decisione da confrontare")
    ignoti = [d for d in decisioni
              if d.get("atteso") is None or d.get("ammesso") is None]
    if ignoti:
        return _muto("⛔ NON GIUDICO: %d decisioni su %d non hanno un atteso o "
                     "un esito (%s)"
                     % (len(ignoti), len(decisioni),
                        "; ".join(str(d.get("perche_oracolo"))[:70]
                                  for d in ignoti[:2])))
    falsi_si = [d for d in decisioni if d["ammesso"] and not d["atteso"]]
    falsi_no = [d for d in decisioni if d["atteso"] and not d["ammesso"]]
    if falsi_si:
        return _no("⛔⛔ %d FALSI SI': il prodotto ha ammesso chi la formula "
                   "rifiutava — e' il lato che affama chi c'era gia'.  %s"
                   % (len(falsi_si),
                      " · ".join("«%s»: %s" % (d["chi"], d["perche_oracolo"])
                                 for d in falsi_si[:3])))
    if falsi_no:
        return _no("⛔⛔ %d FALSI NO: il prodotto ha rifiutato chi la formula "
                   "ammetteva — e' il lato che costa un utente, e sbaglia "
                   "quanto l'altro.  %s"
                   % (len(falsi_no),
                      " · ".join("«%s»: %s" % (d["chi"], d["perche_oracolo"])
                                 for d in falsi_no[:3])))
    return _si("⭐ 0 falsi si', 0 falsi no su %d decisioni" % len(decisioni))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LE SEI DOMANDE — ciascuna e' una lista di predicati, e il verdetto e'
#     il PEGGIORE dei suoi.  ⛔ Rosso batte «non giudico», che batte verde.
# ═══════════════════════════════════════════════════════════════════════════
def _peggiore(predicati):
    """`predicati` = [(nome, (passa, perche)), …] → True | False | None."""
    passi = [p for _n, (p, _perche) in predicati]
    if any(p is False for p in passi):
        return False
    if any(p is None for p in passi) or not passi:
        return None
    return True


def domanda(numero, titolo, predicati):
    return {"numero": numero, "titolo": titolo,
            "verdetto": _peggiore(predicati),
            "predicati": [{"predicato": n, "passa": p, "perche": q}
                          for n, (p, q) in predicati]}


def p_ancora_dei_gradini(gradini):
    """⛔ IL CONTO DI UN GRADINO NON SI LEGGE DAL PRECEDENTE.

    ⭐ `10-b92-dieci.py` `p_ancora` fa gia' questo confronto sui `numero` dei
       fotogrammi, con tolleranza **zero**: qui si riusa la sua logica invece di
       riscriverla — un secondo confronto scritto a mano sarebbe una seconda
       occasione di sbagliarlo.
    """
    if len(gradini) < 2:
        return _muto("meno di due gradini: non c'e' niente da disgiungere")
    fette, quali = {}, set()
    for g in gradini:
        for i, n in (g.get("sessioni") or {}).items():
            if n and n.get("numeri"):
                fette[(g["gradino"], i)] = {"numeri": n["numeri"]}
                quali.add(i)
    if not fette:
        return _muto("⛔ NON GIUDICO: nessuna sessione porta i `numero` dei "
                     "fotogrammi ⇒ non posso provare che due gradini non "
                     "raccontino lo stesso conto")
    guai, ok = [], 0
    ordinati = sorted({g["gradino"] for g in gradini})
    for i in sorted(quali):
        for a, b in zip(ordinati, ordinati[1:]):
            if (a, i) in fette and (b, i) in fette:
                passa, perche = B.p_ancora(fette, i, b)
                if passa is False:
                    guai.append("s%d fra %d e %d: %s" % (i, a, b, perche))
                elif passa is True:
                    ok += 1
    if guai:
        return _no("⛔⛔ IL CONTO DI UN GRADINO E' LETTO DAL PRECEDENTE — %s"
                   % " · ".join(guai[:3]))
    if not ok:
        return _muto("⛔ NON GIUDICO: nessuna coppia di gradini confrontabile")
    return _si("%d passaggi di gradino disgiunti, tolleranza ZERO" % ok)


# ── D1 ─────────────────────────────────────────────────────────────────────
def d1_col_budget_spento(fatti):
    """⛔⛔ COL BUDGET SPENTO, IL DIFETTO C'E' ANCORA?

    `[M]` §6.5: l'ottavo entra con **`negati 0`** e tutti vanno a **1,5 fot/s**.
    ⇒ ⛔ **Se il banco non ritrova questo, non sta misurando niente** — e lo dice
      con un ROSSO, non con un silenzio.  ⚠ E' l'unica domanda in cui il verde
      significa *«il difetto c'e'»*: e' **l'ancora del banco**, non un giudizio
      sul prodotto.
    """
    p = []
    avvio = fatti.get("avvio")
    p.append(("D1.0 la riga d'avvio dichiara il budget in vigore",
              p_riga_d_avvio(avvio)))
    budget = (avvio or {}).get("budget")
    if budget is None:
        p.append(("D1.1 il budget e' SPENTO",
                  _muto("⛔ NON HO MISURATO: non so con che budget il server "
                        "stia girando ⇒ non so nemmeno se questa e' la scena "
                        "di D1")))
        return domanda(1, "col budget SPENTO, il difetto c'e' ancora?", p)
    if budget != SPEC.BUDGET_PREDEFINITO:
        p.append(("D1.1 il budget e' SPENTO",
                  _muto("⛔ NON E' LA SCENA DI D1: il server gira con %s %s, non "
                        "%s.  ⚠ Il difetto di §6.5 e' quello del prodotto SENZA "
                        "budget" % (SPEC.OPZ_BUDGET, budget,
                                    SPEC.BUDGET_PREDEFINITO))))
        return domanda(1, "col budget SPENTO, il difetto c'e' ancora?", p)
    p.append(("D1.1 il budget e' SPENTO",
              _si("%s = %s ⇒ e' la scena di §6.5" % (SPEC.OPZ_BUDGET, budget))))

    gradini = {g.get("gradino"): g for g in (fatti.get("gradini") or [])}
    basso = gradini.get(1)
    if basso:
        p.append(("D1.2 la scena ha morso ai primi gradini",
                  p_la_scena_ha_morso(basso.get("sessioni") or {})))
    else:
        p.append(("D1.2 la scena ha morso ai primi gradini",
                  _muto("⛔ NON HO MISURATO: nessun gradino basso")))

    p.append(("D1.3 l'ancora: ogni gradino ha i suoi fotogrammi",
              p_ancora_dei_gradini(fatti.get("gradini") or [])))

    g = gradini.get(MIO.GRADINO_DIRUPO)
    if not g:
        p.append(("D1.4 il gradino del dirupo e' stato raggiunto",
                  _muto("⛔ NON HO MISURATO: la salita non e' arrivata al "
                        "gradino %d (si e' fermata a %s).  ⚠ Senza quel gradino "
                        "il difetto di §6.5 non e' stato nemmeno sfiorato"
                        % (MIO.GRADINO_DIRUPO,
                           max(gradini) if gradini else "?"))))
        return domanda(1, "col budget SPENTO, il difetto c'e' ancora?", p)
    p.append(("D1.4 il gradino del dirupo e' stato raggiunto",
              _si("gradino %d misurato" % MIO.GRADINO_DIRUPO)))

    # ⛔ `negati 0` — e col budget SPENTO un rifiuto e' una violazione di I6.
    neg = g.get("negati")
    if neg is None:
        p.append(("D1.5 nessuno e' stato negato",
                  _muto("⛔ NON HO MISURATO: i conti del server non dicono "
                        "quanti sono stati negati.  ⚠ `None` non e' zero")))
    elif neg > 0:
        p.append(("D1.5 nessuno e' stato negato",
                  _no("⛔⛔ I6 VIOLATO: col budget SPENTO (%s %s) il prodotto ha "
                      "negato %d.  ⚠ Spento deve voler dire spento: `CODER.md` "
                      "I6 vuole che quel che cambia cio' che l'utente vede "
                      "nasca spento finche' l'utente non l'ha guardato"
                      % (SPEC.OPZ_BUDGET, budget, neg))))
    else:
        p.append(("D1.5 nessuno e' stato negato",
                  _si("⛔ `negati 0` al gradino %d: **il prodotto non sa dire "
                      "di no** — ed e' esattamente il difetto di §6.5"
                      % MIO.GRADINO_DIRUPO)))

    sess = {i: n for i, n in (g.get("sessioni") or {}).items()
            if B.ha_misurato(n)}
    if not sess:
        p.append(("D1.6 il dirupo: tutti a ~1,5 fot/s",
                  _muto("⛔ NON HO MISURATO: nessuna sessione col numero al "
                        "gradino %d" % MIO.GRADINO_DIRUPO)))
        return domanda(1, "col budget SPENTO, il difetto c'e' ancora?", p)
    senza = [i for i, n in sess.items() if n.get("fps") is None]
    if senza:
        p.append(("D1.6 il dirupo: tutti a ~1,5 fot/s",
                  _muto("⛔ NON GIUDICO: %s non hanno un ritmo — ⚠ `None` non e' "
                        "zero, e uno zero finto farebbe *trovare* il dirupo"
                        % ", ".join("s%d" % i for i in sorted(senza)))))
        return domanda(1, "col budget SPENTO, il difetto c'e' ancora?", p)
    ritmi = {i: n["fps"] for i, n in sess.items()}
    peggio, meglio = min(ritmi.values()), max(ritmi.values())
    rit = [n["ritardo_mediano_ms"] for n in sess.values()
           if n.get("ritardo_mediano_ms") is not None]
    testimone = ("ritardo mediano %.0f-%.0f ms" % (min(rit), max(rit))
                 if rit else "⚠ ritardo NON letto")
    chiavi = sum((n.get("chiavi") or 0) for n in sess.values())
    if meglio <= MIO.FPS_DIRUPO:
        p.append(("D1.6 il dirupo: tutti a ~1,5 fot/s",
                  _si("⛔ IL DIFETTO C'E': al gradino %d tutte e %d le sessioni "
                      "stanno fra %.2f e %.2f fot/s (tetto %.1f) · %s · "
                      "⭐ e le CHIAVI sono %d — `LEZIONI.md` §1.34: la colonna "
                      "che avvisa qui e' il RITARDO, non le chiavi.  Ferro: %s"
                      % (MIO.GRADINO_DIRUPO, len(ritmi), peggio, meglio,
                         MIO.FPS_DIRUPO, testimone, chiavi, FERRO))))
    elif peggio >= MIO.FPS_SANO_MIN:
        p.append(("D1.6 il dirupo: tutti a ~1,5 fot/s",
                  _no("⛔⛔ IL BANCO NON RITROVA IL DIFETTO DI §6.5: al gradino "
                      "%d le sessioni stanno fra %.2f e %.2f fot/s, cioe' STANNO "
                      "BENE.  ⇒ O la macchina non e' quella (%s), o la scena non "
                      "e' satura, o **questo banco non sta misurando niente**.  "
                      "%s" % (MIO.GRADINO_DIRUPO, peggio, meglio, FERRO,
                              testimone))))
    else:
        p.append(("D1.6 il dirupo: tutti a ~1,5 fot/s",
                  _muto("⚠ NON LO DISTINGUO: al gradino %d le sessioni stanno "
                        "fra %.2f e %.2f fot/s — sopra il tetto del dirupo "
                        "(%.1f) e sotto il pavimento del sano (%.1f).  ⛔ Un "
                        "«forse» non e' un verde: la zona di mezzo si dichiara"
                        % (MIO.GRADINO_DIRUPO, peggio, meglio,
                           MIO.FPS_DIRUPO, MIO.FPS_SANO_MIN))))
    return domanda(1, "col budget SPENTO, il difetto c'e' ancora?", p)


# ── D2 ─────────────────────────────────────────────────────────────────────
def d2_budget_pieno_sul_filo(fatti):
    """⛔ CHI ARRIVA DI TROPPO RICEVE `BUDGET_PIENO`, letto SUL FILO NEL CLIENT."""
    p = []
    avvio = fatti.get("avvio")
    p.append(("D2.0 la riga d'avvio dichiara il budget in vigore",
              p_riga_d_avvio(avvio)))
    budget = (avvio or {}).get("budget")
    if budget is None:
        p.append(("D2.1 il budget e' ACCESO",
                  _muto("⛔ NON HO MISURATO: non so con che budget il server "
                        "stia girando")))
    elif budget == SPEC.BUDGET_PREDEFINITO:
        p.append(("D2.1 il budget e' ACCESO",
                  _muto("⛔ NON E' LA SCENA DI D2: il budget e' SPENTO (%s %s) "
                        "⇒ nessuno puo' ricevere %#04x, ed e' giusto cosi'"
                        % (SPEC.OPZ_BUDGET, budget, SPEC.COD_BUDGET_PIENO))))
        return domanda(2, "chi arriva di troppo riceve BUDGET_PIENO?", p)
    else:
        p.append(("D2.1 il budget e' ACCESO",
                  _si("%s = %s Mpixel/s · %s = %s"
                      % (SPEC.OPZ_BUDGET, budget, SPEC.OPZ_RISERVA,
                         (avvio or {}).get("riserva")))))

    tent = fatti.get("tentativi") or []

    # ⛔⛔ L'ORACOLO VIENE PRIMA DELLA PORTA DELLA SOLLECITAZIONE, ED E' VOLUTO.
    #
    #     Il caso «il budget acceso NON rifiuta nessuno» non lascia **niente sul
    #     filo**: nessun `CONGEDO`, nessun respinto, nessun `arrivato_a`.  ⚠ Se
    #     la porta della sollecitazione stesse prima, quel caso uscirebbe **«non
    #     ho misurato»** invece che rosso — cioe' il difetto piu' grave della
    #     fase (l'ottavo che entra e affama tutti) sarebbe un silenzio.
    #  ⇒ Il confronto con la formula si fa SEMPRE; la porta governa solo i
    #    predicati che leggono il filo, che senza filo non hanno che dire.
    p.append(("D2.2 l'oracolo dice chi doveva entrare e chi no",
              p_oracolo_contro_prodotto(fatti.get("decisioni") or [])))

    # ⛔⛔ E POI: la sollecitazione e' ARRIVATA?  Un respinto che non ha mai
    #    raggiunto l'`ATTACCA` — parola sbagliata, ban, server spento — NON e'
    #    «rifiutato correttamente»: e' «non ho misurato».  E' la forma che in
    #    fase 9 ha prodotto nove difetti su nove.
    morso = W.p_ha_morso(tent)
    p.append(("D2.3 il respinto e' ARRIVATO a provarci", morso))
    if morso[0] is not True:
        return domanda(2, "chi arriva di troppo riceve BUDGET_PIENO?", p)

    p.append(("D2.4 ⛔ il motivo sul filo e' %#04x" % SPEC.COD_BUDGET_PIENO,
              p_motivo_atteso(tent, SPEC.COD_BUDGET_PIENO,
                              e_non=(SPEC.COD_NON_SERVIBILE,))))
    p.append(("D2.5 il corpo porta il dettaglio", p_corpo_non_vuoto(tent)))
    p.append(("D2.6 e il dettaglio porta i numeri", p_corpo_porta_i_numeri(tent)))
    return domanda(2, "chi arriva di troppo riceve BUDGET_PIENO?", p)


# ── D3 ─────────────────────────────────────────────────────────────────────
def p_tre_finestre(fatti):
    """⛔ L'ANCORA DI D3 — «prima», «durante» e «dopo» non si sovrappongono.

    ⚠ Il conto di «prima» letto **dopo** il tentativo e' un verde per
      costruzione, ed e' la forma d'errore piu' comoda che ci sia (§6.4, punto b
      delle «tre cose che rendono onesto quel banco»).
    """
    fin = fatti.get("finestre")
    if not fin:
        return _muto("⛔ NON GIUDICO: il banco non dice quando comincia e "
                     "finisce ciascuna delle tre finestre")
    ordine = ("prima", "durante", "dopo")
    for nome in ordine:
        if not fin.get(nome) or None in fin[nome]:
            return _muto("⛔ NON GIUDICO: la finestra «%s» non ha estremi (%s)"
                         % (nome, fin.get(nome)))
    for a, b in zip(ordine, ordine[1:]):
        if fin[a][1] > fin[b][0]:
            return _no("⛔ LE FINESTRE SI SOVRAPPONGONO: «%s» finisce a %.3f e "
                       "«%s» comincia a %.3f ⇒ il conto di una e' anche il "
                       "conto dell'altra, e il confronto e' con se stesso"
                       % (a, fin[a][1], b, fin[b][0]))
    return _si("le tre finestre sono disgiunte: prima %.1f-%.1f · durante "
               "%.1f-%.1f · dopo %.1f-%.1f"
               % (fin["prima"][0], fin["prima"][1], fin["durante"][0],
                  fin["durante"][1], fin["dopo"][0], fin["dopo"][1]))


def p_il_dopo_torna(dentro):
    """⭐ Il danno non deve sopravvivere alla sua causa.

    ⚠ E se «dopo» non c'e', si dice — non si finge che il giro sia finito bene.
      (`fasi/10-…md` §9 porta un `[?]` proprio di questa forma: due sessioni
      restate a 7-9 fot/s **col guardiano a zero**, meccanismo ignoto.)
    """
    guai, ok, muti = [], 0, []
    for i, tre in sorted(dentro.items()):
        a, c = tre.get("prima"), tre.get("dopo")
        if not B.ha_misurato(c):
            muti.append("s%d" % i)
            continue
        fa, fc = (a or {}).get("fps"), c.get("fps")
        if fa in (None, 0) or fc is None:
            muti.append("s%d" % i)
            continue
        if (fa - fc) / fa >= MIO.I1_CALO_FPS:
            guai.append("s%d: %.2f → %.2f fot/s e NON e' tornata" % (i, fa, fc))
        else:
            ok += 1
    if guai:
        return _no("⛔ IL DANNO SOPRAVVIVE ALLA SUA CAUSA: %s" % " · ".join(guai))
    if muti and not ok:
        return _muto("⛔ NON GIUDICO: la finestra «dopo» non ha numeri per %s"
                     % ", ".join(muti))
    return _si("%d sessioni su %d sono tornate come «prima»%s"
               % (ok, ok + len(muti),
                  "" if not muti else " (⚠ %s senza «dopo»)" % ", ".join(muti)))


def d3_chi_era_dentro_non_peggiora(fatti):
    """⛔⛔ CHI ERA DENTRO NON PEGGIORA — `DECISIONI.md` §4.6-bis, invariante I1.

    ⭐ **Appaiato: prima, durante, dopo.**  E ⚠ `LEZIONI.md` §1.34: nella salita
      a dieci **le chiavi sono rimaste a ZERO** (`[M]` 0 su 8 741, anche dentro
      il crollo) ⇒ ⛔ **la colonna che avvisa e' il RITARDO**.  Un predicato che
      guardasse le sole chiavi sarebbe **verde per costruzione**, ed e' per
      questo che il guasto G4b della certificazione innesta un peggioramento
      **che tocca solo il ritardo**.
    """
    p = []
    p.append(("D3.0 l'ancora: le tre finestre non si sovrappongono",
              p_tre_finestre(fatti)))
    if p[0][1][0] is False:
        return domanda(3, "chi era dentro NON peggiora?", p)

    dentro = fatti.get("dentro") or {}
    if not dentro:
        p.append(("D3.1 c'e' qualcuno da guardare",
                  _muto("⛔ NON HO MISURATO: nessuna sessione era dentro")))
        return domanda(3, "chi era dentro NON peggiora?", p)

    guai_ritmo, guai_ritardo, guai_chiavi, righe, muti = [], [], [], [], []
    for i, tre in sorted(dentro.items()):
        a, b = tre.get("prima"), tre.get("durante")
        if not (B.ha_misurato(a) and B.ha_misurato(b)):
            muti.append("s%d: «prima» o «durante» non hanno un numero (%s / %s)"
                        % (i, (a or {}).get("esito"), (b or {}).get("esito")))
            continue
        fa, fb = a.get("fps"), b.get("fps")
        ra, rb = a.get("ritardo_mediano_ms"), b.get("ritardo_mediano_ms")
        ka, kb = a.get("chiavi"), b.get("chiavi")
        na, nb = a.get("fotogrammi"), b.get("fotogrammi")
        if fa in (None, 0) or fb is None:
            muti.append("s%d: il ritmo non e' stato letto (%r → %r)" % (i, fa, fb))
            continue
        calo = (fa - fb) / fa
        riga = "s%d: %.2f → %.2f fot/s (%+.1f %%)" % (i, fa, fb, -100 * calo)
        if calo >= MIO.I1_CALO_FPS:
            guai_ritmo.append(riga)
        # ⭐⭐ LA COLONNA CHE AVVISA — e si guarda **anche quando il ritmo regge**.
        if ra is None or rb is None:
            muti.append("s%d: ⛔ il RITARDO non e' stato letto (%r → %r) — ed e' "
                        "la colonna che avvisa (§1.34)" % (i, ra, rb))
        else:
            riga += " · ritardo %.1f → %.1f ms" % (ra, rb)
            if rb > SPEC.SOGLIA_RITARDO_MS and rb > MIO.I1_RITARDO_FATTORE * ra:
                guai_ritardo.append(
                    "s%d: il ritardo va da %.1f a %.1f ms — sopra la soglia di "
                    "%.1f (`[M]` §6.9) e piu' del %.0f× di prima"
                    % (i, ra, rb, SPEC.SOGLIA_RITARDO_MS,
                       MIO.I1_RITARDO_FATTORE))
        # ⚠ IL TESTIMONE, non la porta: `[M]` zero chiavi su 8 741.
        if None not in (ka, kb, na, nb) and na and nb:
            qa, qb = ka / float(na), kb / float(nb)
            riga += " · chiavi %.4f → %.4f" % (qa, qb)
            if qb > qa + MIO.I1_QUOTA_CHIAVI:
                guai_chiavi.append("s%d: la quota di chiavi sale da %.4f a %.4f"
                                   % (i, qa, qb))
        righe.append(riga)

    if guai_ritardo:
        p.append(("D3.1 ⭐ il RITARDO di chi era dentro",
                  _no("⛔⛔ I1 VIOLATO SUL RITARDO — %s.  ⭐ E' la colonna che "
                      "avvisa (`LEZIONI.md` §1.34): qui le chiavi tacciono"
                      % " · ".join(guai_ritardo))))
    elif muti:
        p.append(("D3.1 ⭐ il RITARDO di chi era dentro",
                  _muto("⛔ NON GIUDICO: %s" % " · ".join(muti[:3]))))
    else:
        p.append(("D3.1 ⭐ il RITARDO di chi era dentro",
                  _si("il ritardo regge su tutte e %d — %s"
                      % (len(righe), " · ".join(righe[:4])))))

    if guai_ritmo:
        p.append(("D3.2 il ritmo di chi era dentro",
                  _no("⛔⛔ I1 VIOLATO SUL RITMO: %s (tolleranza %.0f %%) — "
                      "`DECISIONI.md` §4.6-bis: *«non si fa degradare chi sta "
                      "gia' lavorando per far entrare chi arriva»*"
                      % (" · ".join(guai_ritmo), 100 * MIO.I1_CALO_FPS))))
    elif not righe:
        p.append(("D3.2 il ritmo di chi era dentro",
                  _muto("⛔ NON GIUDICO: nessuna coppia prima/durante completa")))
    else:
        p.append(("D3.2 il ritmo di chi era dentro",
                  _si("nessun calo oltre il %.0f %% su %d sessioni"
                      % (100 * MIO.I1_CALO_FPS, len(righe)))))

    if guai_chiavi:
        p.append(("D3.3 ⚠ il testimone: la quota di CHIAVI",
                  _no("⛔ la spirale di chiavi si e' accesa: %s"
                      % " · ".join(guai_chiavi))))
    else:
        p.append(("D3.3 ⚠ il testimone: la quota di CHIAVI",
                  _si("le chiavi non salgono.  ⛔⛔ E QUESTO DA SOLO NON E' UN "
                      "VERDE: `[M]` §6.5 zero chiavi su 8 741 **anche dentro il "
                      "crollo** ⇒ chi si fermasse qui direbbe «tutto bene» "
                      "mentre tutti stanno a 1,5 fot/s")))

    # ⭐ E il DOPO: il danno non deve sopravvivere alla sua causa.
    p.append(("D3.4 e «dopo» si torna com'era", p_il_dopo_torna(dentro)))
    return domanda(3, "chi era dentro NON peggiora?", p)


# ── D4 ─────────────────────────────────────────────────────────────────────
def d4_dieci_ferme_entrano(fatti):
    """⭐ DIECI SESSIONI FERME DEVONO ENTRARE.

    `[M]` §6.16: costano **0,01 %** l'una di `rcs0` e **+0,2 %** a chi lavora.
    ⛔ **Un budget che le rifiuta sbaglia quanto uno che ammette l'ottavo che fa
       crollare tutto**: e' il **falso NO**, il lato che costa un utente — e
       nessuno se ne accorge, perche' l'utente respinto non e' nella stanza.
    """
    p = []
    p.append(("D4.0 la riga d'avvio dichiara il budget in vigore",
              p_riga_d_avvio(fatti.get("avvio"))))
    # ⛔ PRIMA DI TUTTO: erano ferme davvero?  Una «ferma» che si muove non e'
    #    la scena che questa domanda misura — e §6.16 lo ha pagato.
    p.append(("D4.1 ⛔ le ferme erano FERME davvero",
              p_le_ferme_sono_ferme(fatti.get("ferme") or {})))

    ammesse = fatti.get("ammissioni") or {}
    if not ammesse:
        p.append(("D4.2 tutte e dieci sono ENTRATE",
                  _muto("⛔ NON HO MISURATO: non so chi sia stato ammesso")))
        return domanda(4, "dieci sessioni FERME devono ENTRARE", p)
    ignote = [i for i, v in ammesse.items() if v is None]
    respinte = [i for i, v in ammesse.items() if v is False]
    if ignote:
        p.append(("D4.2 tutte e dieci sono ENTRATE",
                  _muto("⛔ NON GIUDICO: di %s non so se siano entrate — "
                        "⚠ `None` non e' «respinta»"
                        % ", ".join("s%d" % i for i in sorted(ignote)))))
    elif respinte:
        motivi = sorted(str(fatti.get("motivi", {}).get(i)) for i in respinte)
        p.append(("D4.2 tutte e dieci sono ENTRATE",
                  _no("⛔⛔ FALSO NO: %d ferme su %d sono state RIFIUTATE (%s), "
                      "coi motivi %s.  ⚠ `[M]` §6.16: una ferma costa **0,01 %%** "
                      "di `rcs0` e dieci costano **+0,2 %%** a chi lavora ⇒ "
                      "rifiutarle e' sbagliato quanto ammettere l'ottavo che "
                      "porta tutti a 1,5 fot/s.  Ferro: %s"
                      % (len(respinte), len(ammesse),
                         ", ".join("s%d" % i for i in sorted(respinte)),
                         sorted(set(motivi)), FERRO))))
    else:
        p.append(("D4.2 tutte e dieci sono ENTRATE",
                  _si("⭐ tutte e %d le ferme sono entrate" % len(ammesse))))

    p.append(("D4.3 l'oracolo le ammetteva tutte",
              p_oracolo_contro_prodotto(fatti.get("decisioni") or [])))

    lav = fatti.get("chi_lavora") or {}
    a, b = lav.get("prima"), lav.get("dopo")
    if not (B.ha_misurato(a) and B.ha_misurato(b)):
        p.append(("D4.4 chi lavorava non se ne accorge",
                  _muto("⛔ NON GIUDICO: chi lavorava non ha un numero prima "
                        "(%s) o dopo (%s)" % ((a or {}).get("esito"),
                                              (b or {}).get("esito")))))
    elif a.get("fps") in (None, 0) or b.get("fps") is None:
        p.append(("D4.4 chi lavorava non se ne accorge",
                  _muto("⛔ NON GIUDICO: il ritmo di chi lavorava non e' stato "
                        "letto (%r → %r)" % (a.get("fps"), b.get("fps")))))
    else:
        calo = (a["fps"] - b["fps"]) / a["fps"]
        testo = ("%.2f → %.2f fot/s (%+.1f %%)"
                 % (a["fps"], b["fps"], -100 * calo))
        if calo > MIO.D4_CALO_AMMESSO:
            p.append(("D4.4 chi lavorava non se ne accorge",
                      _no("⛔ chi lavorava HA PERSO: %s, oltre il %.0f %% che "
                          "questo banco tollera.  `[M]` §6.16 misurava **+0,2 %%**"
                          % (testo, 100 * MIO.D4_CALO_AMMESSO))))
        else:
            p.append(("D4.4 chi lavorava non se ne accorge",
                      _si("⭐ %s — `[M]` §6.16 misurava +0,2 %%" % testo)))
    return domanda(4, "dieci sessioni FERME devono ENTRARE", p)


# ── D5 ─────────────────────────────────────────────────────────────────────
def p_risveglio_avvenuto(fatti):
    """⛔⛔ «SVEGLIATA» SI GIUDICA SULLA **SOLLECITAZIONE**, NON SUL RITMO.

    `[M]` §6.16, il terzo difetto di quel banco, e questo predicato esiste per
    non ripeterlo: le otto si erano svegliate benissimo — fotogrammi da 4 825-
    5 421 byte, **diciotto volte** i 266 di una ferma — ma consegnavano 1,47-
    1,55 fot/s, cioe' **sotto la soglia delle ferme**.  ⇒ Il banco le dichiaro'
    «non svegliate» e si rifiuto' di misurare **proprio la scena che esisteva
    per misurare**.

    ⭐⭐ **Il ritmo basso non e' il contrario del risveglio: e' il suo
        RISULTATO.**  ⇒ Qui si guarda **quanto sono cresciuti i fotogrammi**, e
        il ritmo non entra nel giudizio nemmeno di striscio.
    """
    prima = fatti.get("prima") or {}
    dopo = fatti.get("dopo") or {}
    comuni = sorted(set(prima) & set(dopo))
    if not comuni:
        return _muto("⛔ NON HO MISURATO: manca il prima (%d) o il dopo (%d), o "
                     "non parlano delle stesse sessioni"
                     % (len(prima), len(dopo)))
    sveglie, dormienti, muti = [], [], []
    for i in comuni:
        ba = (prima[i] or {}).get("byte_per_fotogramma")
        bb = (dopo[i] or {}).get("byte_per_fotogramma")
        fb = (dopo[i] or {}).get("fps")
        if ba in (None, 0) or bb is None:
            muti.append("s%d (byte %r → %r)" % (i, ba, bb))
            continue
        cresce = bb / ba
        if cresce >= MIO.RISVEGLIO_FATTORE_BYTE:
            sveglie.append("s%d ×%.1f (%.0f → %.0f B/fot%s)"
                           % (i, cresce, ba, bb,
                              "" if fb is None else ", %.2f fot/s" % fb))
        else:
            dormienti.append("s%d ×%.1f (%.0f → %.0f B/fot)"
                             % (i, cresce, ba, bb))
    if muti:
        return _muto("⛔ NON HO MISURATO: i byte per fotogramma non si sono "
                     "letti per %s — e senza quelli «svegliata» non si giudica"
                     % ", ".join(muti))
    if dormienti:
        return _muto("⛔ NON HO MISURATO IL RISVEGLIO: %d scene su %d non hanno "
                     "sollecitato (%s, soglia ×%.0f).  ⚠ E questo NON e' "
                     "«nessun effetto»: e' che la scena non e' stata prodotta"
                     % (len(dormienti), len(comuni), " · ".join(dormienti[:3]),
                        MIO.RISVEGLIO_FATTORE_BYTE))
    return _si("⭐ tutte e %d si sono svegliate, e si vede dai FOTOGRAMMI: %s.  "
               "⛔ Il ritmo NON e' entrato in questo giudizio (§6.16: una "
               "svegliata affamata a 1,5 fot/s e' comunque svegliata)"
               % (len(sveglie), " · ".join(sveglie[:4])))


def p_sforamento_contenuto(fatti):
    """⭐ QUANTO LA RISERVA CONTIENE LO SFORAMENTO — `[M]` §6.16: ~2× con F=0,5."""
    avvio = fatti.get("avvio") or {}
    C, F = avvio.get("budget"), avvio.get("riserva")
    dom = fatti.get("domanda_dopo_mpixel_s")
    if C is None or F is None:
        return _muto("⛔ NON GIUDICO: la capacita' (%r) o la riserva (%r) non "
                     "sono dichiarate ⇒ non c'e' un tetto da confrontare"
                     % (C, F))
    if not C:
        return _muto("⛔ NON E' LA SCENA DI D5: col budget SPENTO non c'e' "
                     "nessun tetto da sforare")
    if dom is None:
        return _muto("⛔ NON GIUDICO: la domanda dopo il risveglio non e' stata "
                     "calcolata — ⚠ e uno zero al suo posto direbbe «nessuno "
                     "sforamento», che e' il verde piu' comodo che ci sia")
    tetto = C * (1.0 - F)
    if tetto <= 0:
        return _muto("⛔ NON GIUDICO: riserva %r ⇒ tetto %r" % (F, tetto))
    sfor = dom / tetto
    testo = ("%.1f Mpixel/s chiesti contro %.1f × (1 − %.2f) = %.1f ⇒ "
             "sforamento **×%.2f**" % (dom, C, F, tetto, sfor))
    if sfor > MIO.SFORAMENTO_MAX:
        return _no("⛔⛔ LA RISERVA NON CONTIENE IL RISVEGLIO: %s, oltre il ×%.1f "
                   "che questo banco tollera.  `[M]` §6.16: con riserva 0,50 lo "
                   "sforamento misurato restava **×%.1f**"
                   % (testo, MIO.SFORAMENTO_MAX, MIO.SFORAMENTO_ATTESO))
    return _si("⭐ %s — dentro il ×%.1f tollerato, e `[M]` §6.16 misurava ×%.1f.  "
               "⚠ Il budget NON evita il risveglio: lo contiene, ed e' quel che "
               "gli si chiede" % (testo, MIO.SFORAMENTO_MAX,
                                  MIO.SFORAMENTO_ATTESO))


def p_quanto_ha_perso_il_titolare(fatti):
    """⚠ RIPORTATO, NON GIUDICATO — e la ragione sta scritta accanto.

    `[M]` §6.16: chi lavorava perde il **95,9 %** e il ritardo fa **×78**.  ⛔ Un
    budget preso all'ingresso **non puo' evitarlo** (§6.9 punto 3: il regolatore
    della fase 9 vive nel padre e ferma fotogrammi **gia' codificati**).  ⇒ Dare
    rosso qui vorrebbe dire dare rosso a un prodotto corretto, ed e' la forma
    d'errore che questo banco ha piu' paura di commettere.
    """
    tit = fatti.get("titolare") or {}
    a, b = tit.get("prima"), tit.get("dopo")
    if not (B.ha_misurato(a) and B.ha_misurato(b)):
        return _muto("⛔ NON HO MISURATO: il titolare non ha un numero prima "
                     "(%s) o dopo (%s)" % ((a or {}).get("esito"),
                                           (b or {}).get("esito")))
    fa, fb = a.get("fps"), b.get("fps")
    ra, rb = a.get("ritardo_mediano_ms"), b.get("ritardo_mediano_ms")
    if fa in (None, 0) or fb is None:
        return _muto("⛔ NON HO MISURATO: il ritmo del titolare (%r → %r)"
                     % (fa, fb))
    pezzi = ["ritmo %.2f → %.2f fot/s (%+.1f %%)"
             % (fa, fb, -100 * (fa - fb) / fa)]
    if ra not in (None, 0) and rb is not None:
        pezzi.append("ritardo %.1f → %.1f ms (×%.1f)" % (ra, rb, rb / ra))
    else:
        pezzi.append("⚠ ritardo NON letto")
    return _si("`[M]` %s · ferro: %s.  ⚠ RIPORTATO, non giudicato: §6.9 punto 3 "
               "dice che un budget preso all'ingresso non puo' evitare questo, "
               "e §6.16 misurava −95,9 %% e ×78" % (" · ".join(pezzi), FERRO))


def d5_il_risveglio(fatti):
    """⛔⛔ IL RISVEGLIO — la cella che il budget NON PUO' PREVEDERE.

    `[M]` §6.16: otto ferme ammesse a **0,01 %** l'una si accendono in **19 ms**
    e chiedono il **130 %** di un motore che ne ha 100; chi lavorava perde il
    **95,9 %** del ritmo e il ritardo fa **×78**.
    ⭐ Con `riserva 0,5` lo sforamento deve restare **~2×**.

    ⛔⛔ E QUI SI MISURA **QUANTO LA RISERVA LO CONTIENE, NON CHE LO EVITI.**
        Un banco che pretendesse «nessuno sforamento» darebbe rosso a un
        prodotto corretto.
    """
    p = []
    p.append(("D5.0 la riga d'avvio dichiara riserva e budget",
              p_riga_d_avvio(fatti.get("avvio"))))
    p.append(("D5.1 ⛔ le ferme erano FERME prima",
              p_le_ferme_sono_ferme(fatti.get("prima") or {})))
    avvenuto = p_risveglio_avvenuto(fatti)
    p.append(("D5.2 ⛔⛔ il RISVEGLIO E' AVVENUTO", avvenuto))
    if avvenuto[0] is not True:
        return domanda(5, "il RISVEGLIO, e quanto la riserva lo contiene", p)

    ms = fatti.get("larghezza_ms")
    if ms is None:
        p.append(("D5.3 le scene si sono accese INSIEME",
                  _muto("⛔ NON GIUDICO: la larghezza del «tutte insieme» non "
                        "e' stata misurata")))
    elif ms > MIO.RISVEGLIO_ACCENSIONE_MS:
        p.append(("D5.3 le scene si sono accese INSIEME",
                  _no("⛔ le scene si sono accese in %.0f ms, oltre i %.0f che "
                      "questo banco chiama «insieme» ⇒ non e' un risveglio "
                      "SIMULTANEO, e la domanda diventa un'altra.  `[M]` §6.16: "
                      "19 ms" % (ms, MIO.RISVEGLIO_ACCENSIONE_MS))))
    else:
        p.append(("D5.3 le scene si sono accese INSIEME",
                  _si("⭐ %.0f ms di larghezza (`[M]` §6.16: 19 ms) — ⚠ e il "
                      "risveglio non e' un istante, e' questa finestra" % ms)))

    p.append(("D5.4 ⭐ la riserva contiene lo sforamento",
              p_sforamento_contenuto(fatti)))
    p.append(("D5.5 ⚠ quanto ha perso chi lavorava (riportato, non giudicato)",
              p_quanto_ha_perso_il_titolare(fatti)))
    return domanda(5, "il RISVEGLIO, e quanto la riserva lo contiene", p)


# ── D6 ─────────────────────────────────────────────────────────────────────
def p_i_due_motivi_diversi(fatti):
    """⛔⛔ Il cuore di D6: **due fatti diversi, due gesti diversi per l'utente**.

    ⚠ Un prodotto che mandasse `0x06` a tutti passerebbe meta' dei predicati di
      sopra e sbaglierebbe la cosa che conta: chi legge la pagina non saprebbe
      se deve **aspettare** (la macchina e' piena) o **chiedere un posto** (il
      tetto e' amministrativo).  §8.1 **D5**: i due motivi si AGGIUNGONO.
    """
    letti = {}
    for chiave in ("amministrativo", "fisico"):
        tent = (fatti.get(chiave) or {}).get("tentativi") or []
        motivi = {t.get("motivo") for t in tent if t.get("motivo") is not None}
        if len(motivi) == 1:
            letti[chiave] = motivi.pop()
    if len(letti) < 2:
        return _muto("⛔ NON GIUDICO: mi serve UN motivo letto sul filo per "
                     "ciascuno dei due bracci, e ne ho %d (%s)"
                     % (len(letti), {k: hex(v) for k, v in letti.items()}))
    if letti["amministrativo"] == letti["fisico"]:
        return _no("⛔⛔ I DUE LIMITI DANNO LO STESSO MOTIVO (%#04x): §8.1 D5 "
                   "vuole **due motivi diversi per due fatti diversi**, e `0x06` "
                   "si AGGIUNGE a `0x0E` invece di sostituirlo.  ⚠ Con un motivo "
                   "solo, l'utente non sa se deve aspettare o chiedere un posto"
                   % letti["amministrativo"])
    return _si("⭐ amministrativo %#04x · fisico %#04x — due fatti, due gesti"
               % (letti["amministrativo"], letti["fisico"]))


def d6_due_tetti(fatti):
    """⛔ IL TETTO AMMINISTRATIVO E QUELLO FISICO SONO DUE COSE — §8.1 **D5**.

    `--tetto-sessioni 3` con budget larghissimo ⇒ il quarto riceve **`0x0E`**;
    budget stretto con tetto largo ⇒ **`0x06`**.
    """
    p = []
    for chiave, atteso, altro, titolo in (
            ("amministrativo", SPEC.COD_NON_SERVIBILE, SPEC.COD_BUDGET_PIENO,
             "tetto stretto + budget largo ⇒ %#04x" % SPEC.COD_NON_SERVIBILE),
            ("fisico", SPEC.COD_BUDGET_PIENO, SPEC.COD_NON_SERVIBILE,
             "budget stretto + tetto largo ⇒ %#04x" % SPEC.COD_BUDGET_PIENO)):
        sigla = chiave[0]
        ramo = fatti.get(chiave) or {}
        if not ramo:
            p.append(("D6.%s %s" % (sigla, titolo),
                      _muto("⛔ NON HO MISURATO: il braccio «%s» non e' stato "
                            "girato" % chiave)))
            continue
        p.append(("D6.%s la riga d'avvio del braccio «%s»" % (sigla, chiave),
                  p_riga_d_avvio(ramo.get("avvio"))))
        tent = ramo.get("tentativi") or []
        morso = W.p_ha_morso(tent)
        p.append(("D6.%s il respinto e' ARRIVATO a provarci" % sigla, morso))
        if morso[0] is not True:
            continue
        p.append(("D6.%s %s" % (sigla, titolo),
                  p_motivo_atteso(tent, atteso, e_non=(altro,))))
        p.append(("D6.%s il corpo porta il dettaglio" % sigla,
                  p_corpo_non_vuoto(tent)))

    # ⭐⭐ E LA DOMANDA CHE VALE PIU' DELLE DUE: sono DIVERSI?
    p.append(("D6.z ⭐ i due motivi sono DIVERSI", p_i_due_motivi_diversi(fatti)))
    return domanda(6, "il tetto amministrativo e quello fisico sono due cose", p)


# ⭐ Le sei in un posto solo: chi ri-punta il banco su una specifica cambiata
#    guarda `SPEC` in testa e poi questa riga, e ha visto tutto.
LE_SEI = ((1, d1_col_budget_spento), (2, d2_budget_pieno_sul_filo),
          (3, d3_chi_era_dentro_non_peggiora), (4, d4_dieci_ferme_entrano),
          (5, d5_il_risveglio), (6, d6_due_tetti))


def stampa_domanda(d):
    segno = {True: "⭐ VERDE", False: "⛔ ROSSO",
             None: "⚠ NON HO MISURATO"}[d["verdetto"]]
    _log("D%d · %s   →   %s" % (d["numero"], d["titolo"], segno))
    for q in d["predicati"]:
        f = {True: _ok, False: _ko, None: _dub}[q["passa"]]
        f("%-52s %s" % (q["predicato"], q["perche"]))
    return d


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I FABBRICANTI — servono alla TARATURA e ai GUASTI, e a nient'altro
# ═══════════════════════════════════════════════════════════════════════════
#
# ⚠ Sono deliberatamente scarni: un fabbricante ricco somiglia troppo al banco
#   che deve certificare, e un guasto che passa in tutt'e due non si vede.
def _fs(fps, byte, ritardo_ms, chiavi=0, fotogrammi=None, disegni_s=8.0,
        numeri=None, esito="misurato"):
    """Una sessione finta, a valori scelti."""
    return {"esito": esito, "fps": fps, "byte_per_fotogramma": byte,
            "ritardo_mediano_ms": ritardo_ms, "chiavi": chiavi,
            "fotogrammi": fotogrammi if fotogrammi is not None
            else (int(fps * 40) if fps is not None else None),
            "disegni": {"disegni_s": disegni_s}, "numeri": numeri}


def _fav(budget=0, tetto=10, riserva=0.5, riga=None):
    """La riga d'avvio finta — ⛔ nel formato che la specifica pretende."""
    if riga is None:
        riga = ("budget: %s %s Mpixel/s · %s %s · %s %.2f"
                % (SPEC.OPZ_BUDGET, budget, SPEC.OPZ_TETTO, tetto,
                   SPEC.OPZ_RISERVA, riserva))
        # ⚠ La riga deve nominare «tetto» e «riserva» come parole, non solo
        #   come opzioni: le costanti di SPEC dicono che cosa cercare.
        riga += "  (tetto amministrativo %s, riserva %.2f)" % (tetto, riserva)
    return {"budget": budget, "tetto": tetto, "riserva": riserva, "riga": riga}


def _ft(motivo, dettaglio="domanda 870,9 su 485,0 Mpixel/s: non ci sta",
        arrivato_a="ATTACCA", dettaglio_letto=True, quanti=3):
    return [{"quale": k, "arrivato_a": arrivato_a, "motivo": motivo,
             "dettaglio": dettaglio, "dettaglio_letto": dettaglio_letto}
            for k in range(1, quanti + 1)]


def _fab_salita(fino_a=8, dirupo_da=8, negati=0, sane=8, fps_sano=38.0,
                fps_dirupo=1.5, byte=5600.0, disegni_s=20.0, primo=1000):
    """Una salita finta con il dirupo dove si vuole, e ⭐ i `numero` DISGIUNTI.

    ⛔ I `numero` disgiunti non sono un ornamento: sono cio' che rende
       impossibile leggere il conto di un gradino dal precedente, ed e' un
       guasto che si innesta rendendoli uguali (G9).
    """
    gradini, conto = [], {}
    for g in range(1, fino_a + 1):
        sess = {}
        for i in range(1, g + 1):
            crollo = g >= dirupo_da
            f = fps_dirupo if crollo else fps_sano
            r = 700.0 if crollo else 10.0
            a = conto.get(i, primo + 1000 * i)
            b = a + max(1, int(f * 40))
            conto[i] = b + 1
            sess[i] = _fs(f, byte, r, chiavi=0, disegni_s=disegni_s,
                          numeri=[a, b])
        gradini.append({"gradino": g, "negati": negati, "sessioni": sess})
    return {"avvio": _fav(budget=0), "gradini": gradini}


def _fab_tre(quanti=3, calo=0.0, ritardo_dopo=None, chiavi_dopo=0,
             torna=True, fps=38.0, ritardo=10.0, fot=1500):
    """Il «prima / durante / dopo» appaiato di D3, coi guasti a manopola."""
    dentro = {}
    for i in range(1, quanti + 1):
        a = _fs(fps, 5600.0, ritardo, chiavi=0, fotogrammi=fot)
        b = _fs(fps * (1.0 - calo), 5600.0,
                ritardo if ritardo_dopo is None else ritardo_dopo,
                chiavi=chiavi_dopo, fotogrammi=fot)
        c = _fs(fps if torna else fps * 0.5, 5600.0, ritardo, fotogrammi=fot)
        dentro[i] = {"prima": a, "durante": b, "dopo": c}
    return {"dentro": dentro,
            "finestre": {"prima": (0.0, 40.0), "durante": (45.0, 85.0),
                         "dopo": (90.0, 130.0)}}


def _fab_ferme(quante=10, respinte=(), byte=266.0, fps=0.02, calo_titolare=0.002):
    ferme = {i: _fs(fps, byte, 10.0, disegni_s=0.0) for i in range(1, quante + 1)}
    amm = {i: (i not in respinte) for i in range(1, quante + 1)}
    dec = [{"chi": "s%d" % i, "atteso": True, "ammesso": amm[i],
            "perche_oracolo": "una ferma costa 0,01 % di rcs0"}
           for i in range(1, quante + 1)]
    return {"avvio": _fav(budget=970, tetto=10, riserva=0.5), "ferme": ferme,
            "ammissioni": amm,
            "motivi": {i: SPEC.COD_BUDGET_PIENO for i in respinte},
            "decisioni": dec,
            "chi_lavora": {"prima": _fs(39.50, 5600.0, 9.9),
                           "dopo": _fs(39.50 * (1 - calo_titolare), 5600.0, 9.7)}}


def _fab_risveglio(quante=8, svegliano=None, affamate=False, ms=19.0,
                   domanda_dopo=970.0, byte_ferma=266.0, byte_sveglia=4900.0):
    """⭐ E il caso che il banco esiste per misurare: **svegliate ma AFFAMATE**.

    `[M]` §6.16: fotogrammi 18 volte piu' grandi e 1,5 fot/s.  ⛔ Con
    `affamate=True` il ritmo crolla **e il risveglio resta un risveglio**.
    """
    svegliano = quante if svegliano is None else svegliano
    prima = {i: _fs(0.02, byte_ferma, 10.0, disegni_s=0.0)
             for i in range(1, quante + 1)}
    dopo = {}
    for i in range(1, quante + 1):
        if i <= svegliano:
            dopo[i] = _fs(1.5 if affamate else 30.0, byte_sveglia, 750.0)
        else:
            dopo[i] = _fs(0.02, byte_ferma, 10.0, disegni_s=0.0)
    return {"avvio": _fav(budget=970, tetto=10, riserva=0.5),
            "prima": prima, "dopo": dopo, "larghezza_ms": ms,
            "domanda_dopo_mpixel_s": domanda_dopo,
            "titolare": {"prima": _fs(39.36, 5600.0, 9.7),
                         "dopo": _fs(1.60, 5600.0, 756.0)}}


def _fab_d6(mot_ammin=None, mot_fisico=None, vuoto=False, arrivato_a="ATTACCA"):
    mot_ammin = SPEC.COD_NON_SERVIBILE if mot_ammin is None else mot_ammin
    mot_fisico = SPEC.COD_BUDGET_PIENO if mot_fisico is None else mot_fisico
    dett = "" if vuoto else "il tetto e' 3 e dentro ce ne sono gia' 3"
    return {"amministrativo": {"avvio": _fav(budget=100000, tetto=3, riserva=0.0),
                               "tentativi": _ft(mot_ammin, dett, arrivato_a)},
            "fisico": {"avvio": _fav(budget=200, tetto=99, riserva=0.5),
                       "tentativi": _ft(mot_fisico,
                                        "" if vuoto else
                                        "domanda 124,4 su 100,0 Mpixel/s",
                                        arrivato_a)}}


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL MODO `--certifica` — ⭐ E GIRA **A SECCO**, senza la macchina e senza
#      il prodotto nuovo.  E' quel che rende questo banco utilizzabile OGGI.
# ═══════════════════════════════════════════════════════════════════════════
def certifica(anche_gli_altri=True):
    """Sano → guasto → risanato, e ⛔ **ogni guasto e' stato FATTO GIRARE**.

    ⚠ Non tocca la macchina di prova, non prende il lucchetto, non ha bisogno
      che il budget esista nel prodotto: i giudizi sono funzioni pure sui fatti,
      e i fatti qui sono fabbricati.  ⭐ L'unica cosa che esce da questo processo
      e' una traccia §11.1 scritta in `$FUORI` e riletta dal lettore VERO di
      `10-b93-pieno.py` — perche' il byte del motivo dev'essere certificato
      contro il lettore che poi leggera' davvero, non contro un'idea del
      formato.
    """
    print("== ⭐ `10-d2-budget.py --certifica` — i guasti si INNESTANO e si "
          "FANNO GIRARE\n")
    esiti, rossi = [], []

    def prova(nome, atteso, chiamata):
        """`atteso` ∈ {True, False, None} — ⛔ e `None` e' un esito, non un buco."""
        try:
            passa, perche = chiamata()
        except Exception as e:
            passa, perche = "ECCEZIONE", "%s: %s" % (type(e).__name__, e)
        bene = (passa is atteso)
        nomi = {True: "verde", False: "ROSSO", None: "non giudico"}
        esiti.append({"caso": nome, "atteso": nomi.get(atteso, atteso),
                      "visto": nomi.get(passa, passa), "ok": bene,
                      "perche": str(perche)[:400]})
        (_ok if bene else _ko)(
            "%-50s atteso %-11s → %s%s"
            % (nome, nomi[atteso], nomi.get(passa, passa),
               "" if bene else "   ⛔ « " + str(perche)[:200]))
        if not bene:
            rossi.append(nome)
        return bene

    def prova_d(nome, atteso, funzione, fatti):
        return prova(nome, atteso,
                     lambda: (funzione(fatti)["verdetto"], "; ".join(
                         "%s: %s" % (q["predicato"], q["perche"])
                         for q in funzione(fatti)["predicati"]
                         if q["passa"] is not True)))

    # ══════════════════════════════════════════════════════════════════════
    _log("0 · ⛔ IL METRO SI TARA PRIMA (`LEZIONI.md` §1.33)")
    # ── 0a-0c · il lettore del CONGEDO ritrova byte NOTI, scritti a mano ──
    # ⛔ E si usa il lettore VERO di 10-b93 e il REGISTRATORE vero del client:
    #    certificare un lettore contro un fabbricante scritto qui vorrebbe dire
    #    sbagliare tutt'e due allo stesso modo e non accorgersene mai.
    cliente = _carica("b3cliente", "01-b3-cliente.py")
    os.makedirs(FUORI, exist_ok=True)

    def leggi_finta(motivo, dettaglio):
        perc = os.path.join(FUORI, "10-d2-taratura-%02x.rcpreg" % motivo)
        W.fabbrica_traccia(perc, [(cliente.SERVER, 0x000C,
                                   W.corpo_congedo(motivo, dettaglio), 10)],
                           cliente)
        letto = W.leggi_canale_qui(perc)
        cong = [m for m in (letto.get("messaggi") or [])
                if m.get("nome") == "CONGEDO" and m.get("verso") == "server"]
        if not cong:
            return None
        c = cong[0]
        return {"quale": 1, "arrivato_a": "ATTACCA", "motivo": c["motivo"],
                "dettaglio": c["dettaglio"],
                "dettaglio_letto": c["dettaglio_letto"]}

    dett_noto = "domanda 870,9 + 124,4 su 485,0 Mpixel/s"
    t06 = leggi_finta(SPEC.COD_BUDGET_PIENO, dett_noto)
    prova("0a il lettore ritrova un %#04x NOTO sul filo" % SPEC.COD_BUDGET_PIENO,
          True, lambda: (t06 is not None
                         and t06["motivo"] == SPEC.COD_BUDGET_PIENO
                         and t06["dettaglio"] == dett_noto,
                         "letto: %s" % t06))
    t0e = leggi_finta(SPEC.COD_NON_SERVIBILE, "il tetto e' 3")
    prova("0b e ritrova anche un %#04x, non solo il primo byte"
          % SPEC.COD_NON_SERVIBILE, True,
          lambda: (t0e is not None and t0e["motivo"] == SPEC.COD_NON_SERVIBILE,
                   "letto: %s" % t0e))
    tvuoto = leggi_finta(SPEC.COD_BUDGET_PIENO, "")
    prova("0c ⚠ «corpo VUOTO» e «corpo NON LETTO» restano due fatti", True,
          lambda: (tvuoto is not None and tvuoto["dettaglio_letto"] is True
                   and tvuoto["dettaglio"] == "",
                   "letto: %s" % tvuoto))

    # ── 0d · l'ORACOLO ritrova un conto noto, e la riserva morde ──────────
    # 1920×1080 @ 60 Hz = 124,416 Mpixel/s.  Sei dentro = 746,496.
    uno = costo_mpixel_s(1920, 1080, 60)
    sei = [uno] * 6
    prova("0d l'oracolo ritrova il conto noto (C=970, F=0)", True,
          lambda: (regge(sei, uno, 970.0, 0.0, 10.0)[0],
                   regge(sei, uno, 970.0, 0.0, 10.0)[2]))
    prova("0d' e con F=0,5 lo stesso conto NON regge", False,
          lambda: (regge(sei, uno, 970.0, 0.5, 10.0)[0],
                   regge(sei, uno, 970.0, 0.5, 10.0)[2]))
    prova("0d'' il costo di una tela 1080p60 e' 124,4 Mpixel/s", True,
          lambda: (abs(uno - 124.416) < 1e-6, "costo = %.4f" % uno))

    # ── 0e · il metro del RITARDO ritrova i ms iniettati ──────────────────
    for iniettato in (5.0, 40.0, 137.0):
        g = B._fab(200, fps=30.0, ritardo_ms=iniettato)
        r = B.ritardi(g)
        prova("0e il ritardo ritrova i %.0f ms iniettati" % iniettato, True,
              lambda r=r, x=iniettato: (
                  r.get("mediano_ms") is not None and abs(r["mediano_ms"] - x) < 1.0,
                  "mediano letto: %s" % r.get("mediano_ms")))

    # ══════════════════════════════════════════════════════════════════════
    _log("1 · LE SEI DOMANDE, SANE — e D1 e' verde quando il DIFETTO C'E'")
    prova_d("1a D1 sana: l'ottavo entra con negati 0 e tutti a 1,5", True,
            d1_col_budget_spento, _fab_salita())
    prova_d("1b D2 sana: %#04x sul filo, col corpo" % SPEC.COD_BUDGET_PIENO,
            True, d2_budget_pieno_sul_filo,
            {"avvio": _fav(budget=970), "tentativi": _ft(SPEC.COD_BUDGET_PIENO),
             "decisioni": [{"chi": "s7", "atteso": False, "ammesso": False,
                            "perche_oracolo": "870,9 + 124,4 > 485,0"}]})
    prova_d("1c D3 sana: nessuno peggiora", True,
            d3_chi_era_dentro_non_peggiora, _fab_tre())
    prova_d("1d D4 sana: dieci ferme entrano tutte", True,
            d4_dieci_ferme_entrano, _fab_ferme())
    prova_d("1e D5 sana: risveglio contenuto a ×2", True, d5_il_risveglio,
            _fab_risveglio(domanda_dopo=970.0))
    prova_d("1f D6 sana: 0x0E amministrativo, 0x06 fisico", True,
            d6_due_tetti, _fab_d6())

    # ══════════════════════════════════════════════════════════════════════
    _log("2 · ⛔⛔ I GUASTI — e ciascuno e' stato FATTO GIRARE")

    # ── G1 · il budget acceso che NON rifiuta nessuno ─────────────────────
    # ⛔ E la scena e' quella VERA di questo guasto: **niente sul filo**, perche'
    #    un budget che non rifiuta nessuno non manda nessun `CONGEDO`.
    g1 = {"avvio": _fav(budget=200, tetto=99, riserva=0.5),
          "tentativi": [],
          "decisioni": [{"chi": "s7", "atteso": False, "ammesso": True,
                         "perche_oracolo":
                         "870,9 + 124,4 = 995,3 > 200 × (1 − 0,50) = 100,0"}]}
    prova_d("G1 ⛔ il budget acceso NON rifiuta nessuno ⇒ falso SI'", False,
            d2_budget_pieno_sul_filo, g1)
    g1r = {"avvio": _fav(budget=200, tetto=99, riserva=0.5),
           "tentativi": _ft(SPEC.COD_BUDGET_PIENO),
           "decisioni": [{"chi": "s7", "atteso": False, "ammesso": False,
                          "perche_oracolo": "995,3 > 100,0"}]}
    prova_d("G1 risanato: lo rifiuta, e sul filo c'e' il %#04x"
            % SPEC.COD_BUDGET_PIENO, True, d2_budget_pieno_sul_filo, g1r)

    # ── G2 · il budget che rifiuta il PRIMO (troppo stretto) ──────────────
    # ⛔ E il rosso deve portare IL NUMERO: senza, chi legge non sa di quanto.
    v, mot, perche, num = regge([], uno, 50.0, 0.5, None)
    prova("G2 ⛔ budget cosi' stretto che rifiuta il PRIMO", False,
          lambda: (v, perche))
    prova("G2' e il rosso porta IL NUMERO (domanda, tetto, capacita')", True,
          lambda: (all(x in perche for x in ("124.4", "50.0", "25.0")),
                   "«%s» · numeri: %s" % (perche, num)))
    prova("G2 risanato: con C=970 il primo entra", True,
          lambda: (regge([], uno, 970.0, 0.5, None)[0],
                   regge([], uno, 970.0, 0.5, None)[2]))

    # ── G3 · il budget che rifiuta dieci FERME ⇒ il FALSO NO ──────────────
    g3 = _fab_ferme(respinte=(7, 8, 9, 10))
    g3["decisioni"] = [dict(d, ammesso=g3["ammissioni"][k + 1])
                       for k, d in enumerate(g3["decisioni"])]
    prova_d("G3 ⛔⛔ il budget rifiuta quattro FERME ⇒ FALSO NO", False,
            d4_dieci_ferme_entrano, g3)
    prova_d("G3 risanato: nessuna respinta", True, d4_dieci_ferme_entrano,
            _fab_ferme())

    # ── G4 · chi era dentro PEGGIORA — il peggioramento e' FINTO e INNESTATO
    prova_d("G4 ⛔ chi era dentro perde il 40 %% di ritmo", False,
            d3_chi_era_dentro_non_peggiora, _fab_tre(calo=0.40))
    # ⛔⛔ E QUESTO E' IL GUASTO CHE CONTA: **solo il ritardo**, ritmo intatto,
    #     chiavi a zero.  Senza di lui D3 sarebbe verde per costruzione.
    prova_d("G4b ⛔⛔ SOLO il RITARDO peggiora (ritmo intatto, chiavi a ZERO)",
            False, d3_chi_era_dentro_non_peggiora,
            _fab_tre(calo=0.0, ritardo_dopo=760.0))
    prova_d("G4c ⛔ e la spirale di chiavi, che qui e' il TESTIMONE", False,
            d3_chi_era_dentro_non_peggiora,
            _fab_tre(calo=0.0, chiavi_dopo=900, fot=1500))
    prova_d("G4d ⛔ il danno SOPRAVVIVE alla sua causa («dopo» non torna)",
            False, d3_chi_era_dentro_non_peggiora, _fab_tre(torna=False))
    prova_d("G4 risanato", True, d3_chi_era_dentro_non_peggiora, _fab_tre())

    # ── G5 · il motivo sbagliato SUL BYTE, nei due versi ──────────────────
    prova_d("G5 ⛔ %#04x dove va %#04x (D2)"
            % (SPEC.COD_NON_SERVIBILE, SPEC.COD_BUDGET_PIENO), False,
            d2_budget_pieno_sul_filo,
            {"avvio": _fav(budget=970),
             "tentativi": _ft(SPEC.COD_NON_SERVIBILE),
             "decisioni": [{"chi": "s7", "atteso": False, "ammesso": False,
                            "perche_oracolo": "-"}]})
    prova_d("G5b ⛔ %#04x dove va %#04x (D6, braccio amministrativo)"
            % (SPEC.COD_BUDGET_PIENO, SPEC.COD_NON_SERVIBILE), False,
            d6_due_tetti, _fab_d6(mot_ammin=SPEC.COD_BUDGET_PIENO))
    prova_d("G5c ⛔⛔ lo STESSO motivo per tutt'e due i limiti", False,
            d6_due_tetti, _fab_d6(mot_ammin=SPEC.COD_BUDGET_PIENO,
                                  mot_fisico=SPEC.COD_BUDGET_PIENO))
    prova_d("G5 risanato", True, d6_due_tetti, _fab_d6())

    # ── G6 · il corpo VUOTO dove il protocollo lo pretende ────────────────
    prova_d("G6 ⛔ il corpo del CONGEDO e' VUOTO", False,
            d2_budget_pieno_sul_filo,
            {"avvio": _fav(budget=970), "tentativi": _ft(SPEC.COD_BUDGET_PIENO,
                                                         dettaglio=""),
             "decisioni": [{"chi": "s7", "atteso": False, "ammesso": False,
                            "perche_oracolo": "-"}]})
    prova("G6b ⚠ il corpo NON LETTO non e' il corpo vuoto ⇒ non giudico", None,
          lambda: p_corpo_non_vuoto(_ft(SPEC.COD_BUDGET_PIENO, "x",
                                        dettaglio_letto=False)))
    prova("G6 risanato", True,
          lambda: p_corpo_non_vuoto(_ft(SPEC.COD_BUDGET_PIENO)))

    # ── G7 · il respinto che non arriva nemmeno a provarci ────────────────
    # ⛔⛔ E DEVE DIRE «NON HO MISURATO», MAI «rifiutato correttamente»: e' la
    #     forma che in fase 9 ha prodotto nove difetti su nove.
    for dove, come in (("CIAO", "parola sbagliata"), ("niente", "server spento"),
                       ("RESPINTO", "indirizzo bannato")):
        prova_d("G7 ⚠ il respinto si ferma a «%s» (%s) ⇒ NON HO MISURATO"
                % (dove, come), None, d2_budget_pieno_sul_filo,
                {"avvio": _fav(budget=970),
                 "tentativi": _ft(SPEC.COD_BUDGET_PIENO, arrivato_a=dove),
                 "decisioni": [{"chi": "s7", "atteso": False, "ammesso": False,
                                "perche_oracolo": "-"}]})
    prova_d("G7 risanato: arrivano tutti all'ATTACCA", True,
            d2_budget_pieno_sul_filo,
            {"avvio": _fav(budget=970), "tentativi": _ft(SPEC.COD_BUDGET_PIENO),
             "decisioni": [{"chi": "s7", "atteso": False, "ammesso": False,
                            "perche_oracolo": "-"}]})

    # ── G8 · la scena che NON MORDE ───────────────────────────────────────
    prova_d("G8 ⚠ la scena non morde (byte sotto il pavimento) ⇒ non giudico",
            None, d1_col_budget_spento, _fab_salita(byte=900.0))
    # ⛔ E il caso di §6.12 n.4: byte SOPRA il pavimento, scena CONGELATA.
    #    I soli byte le avrebbero dato verde; la prendono i DISEGNI.
    prova("G8b ⛔⛔ scena CONGELATA con byte SOPRA il pavimento (E15)", None,
          lambda: p_la_scena_ha_morso({1: _fs(38.0, 5600.0, 10.0,
                                              disegni_s=0.3)}))
    prova("G8c ⚠ i disegni NON LETTI non sono «zero disegni»", None,
          lambda: p_la_scena_ha_morso({1: _fs(38.0, 5600.0, 10.0,
                                              disegni_s=None)}))
    prova("G8 risanato", True,
          lambda: p_la_scena_ha_morso({1: _fs(38.0, 5600.0, 10.0,
                                              disegni_s=20.0)}))
    # ⛔ E il verso opposto: una «ferma» che si muove.
    prova("G8d ⛔ una «ferma» che si muove (orologio ⇒ il RITMO)", False,
          lambda: p_le_ferme_sono_ferme({1: _fs(12.0, 300.0, 10.0)}))
    prova("G8e ⛔ una «ferma» che si muove (salvaschermo ⇒ i BYTE)", False,
          lambda: p_le_ferme_sono_ferme({1: _fs(0.5, 40000.0, 10.0)}))
    prova("G8 risanato (ferma)", True,
          lambda: p_le_ferme_sono_ferme({1: _fs(0.02, 266.0, 10.0)}))

    # ── G9 · il conto di un gradino letto dal PRECEDENTE ──────────────────
    sana = _fab_salita(fino_a=3, dirupo_da=99)
    guasta = _fab_salita(fino_a=3, dirupo_da=99)
    for g in guasta["gradini"]:
        for i, n in g["sessioni"].items():
            n["numeri"] = [1000, 2000]       # ⛔ lo stesso conto in ogni gradino
    prova("G9 ⛔ stessi `numero` in due gradini ⇒ ROSSO", False,
          lambda: p_ancora_dei_gradini(guasta["gradini"]))
    prova("G9 risanato: i conti sono disgiunti", True,
          lambda: p_ancora_dei_gradini(sana["gradini"]))
    prova("G9b ⚠ senza `numero` non si giudica (non e' un verde)", None,
          lambda: p_ancora_dei_gradini(
              [{"gradino": 1, "sessioni": {1: _fs(38.0, 5600.0, 10.0)}},
               {"gradino": 2, "sessioni": {1: _fs(38.0, 5600.0, 10.0)}}]))

    # ── G10 · il RISVEGLIO ────────────────────────────────────────────────
    prova_d("G10 ⚠ il risveglio NON avviene ⇒ NON HO MISURATO", None,
            d5_il_risveglio, _fab_risveglio(svegliano=0))
    prova_d("G10b ⚠ si sveglia solo META' ⇒ NON HO MISURATO", None,
            d5_il_risveglio, _fab_risveglio(svegliano=4))
    # ⭐⭐ IL CONTROLLO NEGATIVO CHE VALE PIU' DI TUTTI: svegliate e AFFAMATE.
    #     `[M]` §6.16: 1,5 fot/s e fotogrammi 18 volte piu' grandi.  ⛔ Se questo
    #     caso dicesse «non ho misurato», il banco rifiuterebbe proprio la scena
    #     per cui esiste.
    prova_d("G10c ⭐⭐ svegliate ma AFFAMATE (1,5 fot/s) ⇒ E' UN RISVEGLIO",
            True, d5_il_risveglio, _fab_risveglio(affamate=True))
    prova_d("G10d ⛔ la riserva NON contiene lo sforamento (×5)", False,
            d5_il_risveglio, _fab_risveglio(domanda_dopo=2500.0))
    prova_d("G10e ⛔ le scene non si accendono INSIEME (3 s)", False,
            d5_il_risveglio, _fab_risveglio(ms=3000.0))
    # ⚠ E la chiave si scrive per intero: `domanda_dopo` invece di
    #   `domanda_dopo_mpixel_s` **non alza** — aggiunge una chiave nuova e
    #   lascia la vecchia al suo posto, cioe' il guasto non si innesta e il
    #   caso esce verde.  `[M]` questa certificazione l'ha preso al primo giro:
    #   e' la forma «il guasto non morde» di `REVIEWER.md` E14, in casa mia.
    prova("G10f ⚠ la domanda dopo NON calcolata ⇒ non giudico (non «zero»)",
          None, lambda: p_sforamento_contenuto(
              dict(_fab_risveglio(), domanda_dopo_mpixel_s=None)))
    prova_d("G10 risanato", True, d5_il_risveglio, _fab_risveglio())

    # ── G11 · l'ORACOLO non si auto-tara (§8.1 D8) ────────────────────────
    prova("G11 ⛔ capacita' NON dichiarata ⇒ «non so», mai un numero", None,
          lambda: (regge(sei, uno, None, 0.5, 10.0)[0],
                   regge(sei, uno, None, 0.5, 10.0)[2]))
    prova("G11b ⛔ una sessione dentro senza costo ⇒ «non so», non zero", None,
          lambda: (regge([uno, None, uno], uno, 970.0, 0.5, 10.0)[0],
                   regge([uno, None, uno], uno, 970.0, 0.5, 10.0)[2]))
    prova("G11c ⛔ riserva non dichiarata ⇒ «non so»", None,
          lambda: (regge(sei, uno, 970.0, None, 10.0)[0], ""))
    prova("G11d ⛔ riserva fuori da [0,1] ⇒ «non so»", None,
          lambda: (regge(sei, uno, 970.0, 1.4, 10.0)[0], ""))
    prova("G11 risanato", True,
          lambda: (regge(sei, uno, 970.0, 0.0, 10.0)[0], ""))

    # ── G12 · ⛔⛔ LA PORTA DEL RITARDO — e il falso SI' che salva ─────────
    # `[M]` §6.9: a otto sessioni il conto sui pixel dice «c'e' posto per altre
    #  cinque» mentre tutti stanno a 1,5 fot/s.  Riprodotto coi numeri veri.
    otto_affamate = [26.63 / 8] * 8      # `[M]` §6.9: 26,63 Mpixel/s consegnati
    prova("G12 ⭐ la porta del RITARDO rifiuta dove i pixel direbbero SI'",
          False, lambda: (regge(otto_affamate, uno, 479.8, 0.0, 654.3)[0],
                          regge(otto_affamate, uno, 479.8, 0.0, 654.3)[2]))
    prova("G12b ⛔ TOLTA la porta (ritardo sano finto) ⇒ FALSO SI'", True,
          lambda: (regge(otto_affamate, uno, 479.8, 0.0, 10.0)[0],
                   "⛔ direbbe «c'e' posto» con tutti a 1,5 fot/s"))
    prova("G12c ⛔ il ritardo NON letto con gente dentro ⇒ «non so»", None,
          lambda: (regge(otto_affamate, uno, 479.8, 0.0, None)[0], ""))
    prova("G12d ⭐ ma a tabella VUOTA il ritardo mancante non e' un buco", True,
          lambda: (regge([], uno, 970.0, 0.5, None)[0], ""))

    # ── G13 · i due tetti: I6, e i due motivi ─────────────────────────────
    prova("G13 ⛔ budget SPENTO che rifiuta ⇒ I6 violato", False,
          lambda: (d1_col_budget_spento(_fab_salita(negati=2))["verdetto"], ""))
    prova("G13b ⭐ spento vuol dire spento: l'oracolo ammette sempre", True,
          lambda: (regge([uno] * 50, uno, 0.0, 0.5, 10.0)[0],
                   regge([uno] * 50, uno, 0.0, 0.5, 10.0)[2]))
    prova("G13c ⭐ ma il tetto AMMINISTRATIVO morde anche a budget spento",
          False, lambda: (regge([uno] * 10, uno, 0.0, 0.5, 10.0, tetto=10)[0],
                          regge([uno] * 10, uno, 0.0, 0.5, 10.0, tetto=10)[2]))
    prova("G13d ⭐ e il motivo atteso e' %#04x, non %#04x"
          % (SPEC.COD_NON_SERVIBILE, SPEC.COD_BUDGET_PIENO), True,
          lambda: (regge([uno] * 10, uno, 0.0, 0.5, 10.0, tetto=10)[1]
                   == SPEC.COD_NON_SERVIBILE, ""))
    prova("G13e ⭐ solo il fisico morde ⇒ %#04x" % SPEC.COD_BUDGET_PIENO, True,
          lambda: (regge([uno] * 6, uno, 970.0, 0.5, 10.0, tetto=99)[1]
                   == SPEC.COD_BUDGET_PIENO, ""))
    prova("G13f ⚠ mordono TUTT'E DUE ⇒ il banco DICHIARA di non saper "
          "scegliere", True,
          lambda: (regge([uno] * 10, uno, 100.0, 0.5, 10.0, tetto=10)[1] is None
                   and "non dice quale dei due vinca"
                   in regge([uno] * 10, uno, 100.0, 0.5, 10.0, tetto=10)[2], ""))

    # ── G14 · la riga d'avvio ─────────────────────────────────────────────
    prova("G14 ⚠ nessuna riga d'avvio ⇒ NON HO MISURATO", None,
          lambda: p_riga_d_avvio({"budget": 970, "tetto": 10, "riserva": 0.5,
                                  "riga": ""}))
    prova("G14b ⛔ la riga c'e' ma non nomina la riserva ⇒ ROSSO", False,
          lambda: p_riga_d_avvio({"budget": 970, "tetto": 10, "riserva": 0.5,
                                  "riga": "budget 970 Mpixel/s, tetto 10"}))
    prova("G14c ⚠ la riga c'e' ma i valori non si sono letti ⇒ non giudico",
          None, lambda: p_riga_d_avvio({"budget": None, "tetto": 10,
                                        "riserva": 0.5,
                                        "riga": "budget ? tetto 10 riserva 0.5"}))
    prova("G14 risanato", True, lambda: p_riga_d_avvio(_fav(budget=970)))

    # ── G15 · `None` non e' zero, e la media dei vivi non si abbassa ──────
    morta = _fab_salita()
    morta["gradini"][-1]["sessioni"][3] = {"esito": "⛔ MORTO: None, non zero"}
    prova_d("G15 ⚠ una sessione senza numero al gradino del dirupo", True,
            d1_col_budget_spento, morta)
    senza_ritmo = _fab_salita()
    for i in senza_ritmo["gradini"][-1]["sessioni"]:
        senza_ritmo["gradini"][-1]["sessioni"][i]["fps"] = None
    prova_d("G15b ⚠ nessuno ha un ritmo ⇒ non giudico (uno zero finto "
            "TROVEREBBE il dirupo)", None, d1_col_budget_spento, senza_ritmo)
    prova("G15c ⚠ `negati` non letto ⇒ non giudico, non «zero negati»", None,
          lambda: (d1_col_budget_spento(
              _fab_salita(negati=None))["verdetto"], ""))

    # ── G16 · ⛔ il banco che NON RITROVA il difetto di §6.5 ──────────────
    #    E' il rosso che dice «non sto misurando niente»: senza di lui, un
    #    banco puntato sulla macchina sbagliata sarebbe verde in silenzio.
    prova_d("G16 ⛔⛔ all'ottavo stanno tutti BENE ⇒ non sto misurando niente",
            False, d1_col_budget_spento, _fab_salita(dirupo_da=99))
    prova_d("G16b ⚠ la salita non arriva all'ottavo ⇒ NON HO MISURATO", None,
            d1_col_budget_spento, _fab_salita(fino_a=5))
    prova_d("G16c ⚠ zona di mezzo (10 fot/s): non lo distinguo", None,
            d1_col_budget_spento, _fab_salita(fps_dirupo=10.0))
    prova_d("G16 risanato", True, d1_col_budget_spento, _fab_salita())

    # ── G17 · le finestre di D3 ───────────────────────────────────────────
    sovr = _fab_tre()
    sovr["finestre"]["durante"] = (30.0, 85.0)      # ⛔ sovrapposta a «prima»
    prova_d("G17 ⛔ «prima» e «durante» si sovrappongono ⇒ ROSSO", False,
            d3_chi_era_dentro_non_peggiora, sovr)
    senza_fin = _fab_tre()
    del senza_fin["finestre"]
    prova_d("G17b ⚠ senza estremi delle finestre ⇒ non giudico", None,
            d3_chi_era_dentro_non_peggiora, senza_fin)

    # ── G18 · e la domanda «non e' la mia scena» ──────────────────────────
    prova_d("G18 ⚠ D2 col budget SPENTO ⇒ non e' la sua scena", None,
            d2_budget_pieno_sul_filo,
            {"avvio": _fav(budget=0), "tentativi": _ft(SPEC.COD_BUDGET_PIENO)})
    prova_d("G18b ⚠ D1 col budget ACCESO ⇒ non e' la sua scena", None,
            d1_col_budget_spento,
            dict(_fab_salita(), avvio=_fav(budget=970)))

    # ══════════════════════════════════════════════════════════════════════
    print("\n== %d casi · %d rossi" % (len(esiti), len(rossi)))
    for r in rossi:
        print("   ⛔ %s" % r)
    os.makedirs(FUORI, exist_ok=True)
    with open(os.path.join(FUORI, "10-d2-certifica.json"), "w") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1)
    if rossi:
        return 1
    print("== ⭐ OGNI PREDICATO E' STATO VISTO FALLIRE, E POI RISANARE")

    if anche_gli_altri:
        # ⛔ E i tre banchi importati si RIFANNO GIRARE: se un mio giro li
        #    avesse rotti, il posto in cui si vede e' questo (e non domani).
        _log("3 · ⛔ I `--certifica` DEI BANCHI IMPORTATI, rifatti girare")
        rc = 0
        for nome, funzione in (("10-b93-pieno.py", W.certifica),
                               ("10-b98-mista.py (+ 10-b92)", M.certifica)):
            _inf("→ %s" % nome)
            try:
                r = funzione()
            except Exception as e:
                _ko("⛔ %s ha alzato: %s: %s" % (nome, type(e).__name__, e))
                r = 1
            rc = rc or r
            (_ok if r == 0 else _ko)("%s → uscita %s" % (nome, r))
        return rc
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA RACCOLTA — l'unica parte che tocca la macchina di prova
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐ Il giudizio sta tutto sopra, ed e' fatto di funzioni PURE sui fatti: e'
#    quel che permette a `--certifica` di girare a secco, e a questo banco di
#    esistere **prima** del prodotto che deve giudicare.  Qui sotto si
#    raccolgono i fatti, e nient'altro.
#
# ⛔ E gli attrezzi non si riscrivono: il cliente, il lettore della traccia
#    §11.1, il ponte fra i due orologi e la salita a gradini sono di
#    `10-b93-pieno.py` e `10-b92-dieci.py`, e si CHIAMANO.
import re

RE_AVVIO_BUDGET = re.compile(
    r"%s[ =]+(-?[0-9]+(?:[.,][0-9]+)?)" % re.escape(SPEC.OPZ_BUDGET))
RE_AVVIO_TETTO = re.compile(
    r"%s[ =]+(-?[0-9]+)" % re.escape(SPEC.OPZ_TETTO))
RE_AVVIO_RISERVA = re.compile(
    r"%s[ =]+(-?[0-9]+(?:[.,][0-9]+)?)" % re.escape(SPEC.OPZ_RISERVA))


def _numero(testo):
    if testo is None:
        return None
    try:
        return float(testo.replace(",", "."))
    except ValueError:
        return None


def avvio_del_server(riga0=1):
    """⛔ LA RIGA D'AVVIO SI LEGGE NEL REGISTRO DEL SERVER, non negli argomenti
       che gli abbiamo passato.

    ⚠ Leggere gli argomenti sarebbe leggere **dove la cosa parte**: se il
      prodotto ignorasse un'opzione, o la interpretasse in un'altra unita', il
      banco non se ne accorgerebbe mai e l'oracolo girerebbe su un numero che
      il prodotto non sta usando.  §6.4 ha fatto ritirare un rilievo intero per
      questa forma.
    """
    testo = W.registro_da(riga0, None, tetto=400) or ""
    riga = ""
    for r in testo.splitlines():
        b = SPEC.PAROLA_AVVIO_BUDGET in r.lower()
        if b and (SPEC.OPZ_BUDGET in r or SPEC.PAROLA_AVVIO_RISERVA in r.lower()):
            riga = r
            break
    if not riga:
        return {"budget": None, "tetto": None, "riserva": None, "riga": "",
                "perche": "nessuna riga d'avvio che parli di budget nelle "
                          "prime 400 righe del registro"}
    m1, m2, m3 = (RE_AVVIO_BUDGET.search(riga), RE_AVVIO_TETTO.search(riga),
                  RE_AVVIO_RISERVA.search(riga))
    b = _numero(m1.group(1)) if m1 else None
    return {"budget": int(b) if b is not None and b == int(b) else b,
            "tetto": int(_numero(m2.group(1))) if m2 else None,
            "riserva": _numero(m3.group(1)) if m3 else None,
            "riga": riga}


def tentativo(utente, nome, resta=3, tetto=200):
    """UN tentativo, e ⛔ tutto quel che se ne sa e' letto **sul filo**.

    Torna il dizionario che i predicati si aspettano, con `arrivato_a`,
    `motivo` (il byte), `dettaglio`, `dettaglio_letto` e i due codici di
    chiusura.  ⚠ `None` dappertutto se il lettore non ha risposto: e' un buco
    del banco, non un rifiuto del prodotto, e i predicati lo distinguono.
    """
    rc, out, err = W.dentro(W.cliente_riga(utente, resta, registra=nome), tetto)
    testo = out + err
    canale = W.leggi_traccia_canale(nome)
    msg = canale.get("messaggi", []) or []
    nomi = [m["nome"] for m in msg]
    cong = [m for m in msg if m["nome"] == "CONGEDO" and m["verso"] == "server"]
    resp = [m for m in msg if m["nome"] == "RESPINTO"]
    if resp:
        arrivato = "RESPINTO"
    elif "ATTACCA" in nomi:
        arrivato = "ATTACCA"
    elif "CREDENZIALI" in nomi:
        arrivato = "CREDENZIALI"
    elif nomi:
        arrivato = nomi[-1]
    else:
        arrivato = None
    mw = re.search(r"\[wt\]\s+sessione chiusa dal server, codice (0x[0-9a-f]+)",
                   testo)
    return {"quale": nome, "utente": utente, "arrivato_a": arrivato,
            "motivo": cong[0]["motivo"] if cong else None,
            "dettaglio": cong[0]["dettaglio"] if cong else None,
            "dettaglio_letto": cong[0]["dettaglio_letto"] if cong else False,
            "codice_wt": int(mw.group(1), 16) if mw else None,
            "messaggi": nomi, "lettore": canale.get("esito"),
            "coda": testo[-800:]}


def opzioni_del_budget(budget=None, tetto=None, riserva=None):
    """La riga di opzioni da passare al server, **coi nomi di `SPEC`**."""
    pezzi = []
    if budget is not None:
        pezzi.append("%s %s" % (SPEC.OPZ_BUDGET, budget))
    if tetto is not None:
        pezzi.append("%s %s" % (SPEC.OPZ_TETTO, tetto))
    if riserva is not None:
        pezzi.append("%s %s" % (SPEC.OPZ_RISERVA, riserva))
    return " ".join(pezzi)


def accendi(opzioni="", max_att=None):
    """Accende il MIO server, e ⛔ **se non si accende NON si misura**.

    ⚠ Con il binario di oggi le opzioni del budget **non esistono**: il server
      le rifiuta e non parte.  ⇒ Questa funzione torna `(False, perche)`, e la
      domanda che la chiamava esce **«non ho misurato»**, non verde e non rossa.
      E' precisamente quel che deve succedere finche' il prodotto non ha il
      budget.
    """
    amb = dict(os.environ)
    amb["OPZIONI_SERVER"] = opzioni
    if max_att is not None:
        amb["MAX_ATT"] = str(max_att)
        # ⛔ Il tetto e' un `#define`: cambiarlo vuol dire RICOMPILARE.  Un
        #    `accendi` senza `porta` girerebbe sul binario di prima e il banco
        #    misurerebbe un tetto diverso da quello che dichiara.
        pp = subprocess.run(["bash", os.path.join(QUI, "10-d2-terreno.sh"),
                             "porta"], env=amb, capture_output=True, timeout=1800)
        if pp.returncode != 0:
            return (False, "⛔ NON HO MISURATO: il terreno non ha saputo mettere "
                           "il tetto a %s (uscita %d).  ⚠ Coda: %s"
                    % (max_att, pp.returncode,
                       (pp.stdout + pp.stderr).decode("utf-8", "replace")[-400:]))
    p = subprocess.run(["bash", os.path.join(QUI, "10-d2-terreno.sh"),
                        "accendi"], env=amb, capture_output=True, timeout=900)
    testo = (p.stdout + p.stderr).decode("utf-8", "replace")
    print(testo[-2000:])
    if p.returncode != 0:
        return (False, "⛔ il server NON si e' acceso con «%s» (uscita %d).  "
                       "⚠ Coda: %s" % (opzioni, p.returncode, testo[-400:]))

    # ⛔⛔ E L'USCITA ZERO NON BASTA — `[M]` 25 agosto 2026, questo banco.
    #
    #   Con `--budget-mpixel-s 1` il terreno ha stampato *«OK server 1265806
    #   sulla porta 8260»* ed e' **uscito 0**, mentre il server aveva stampato
    #   la sua guida ed era gia' morto: `ss -uln` non mostrava nessun
    #   ascoltatore sulla 8260 e l'unita' era `inactive/success`.
    #   ⇒ Un banco che si fidasse dell'uscita direbbe «acceso», poi «la tabella
    #     non si riempie», e finirebbe per accusare il prodotto di un difetto
    #     che e' un'opzione inesistente.  ⛔ E' la forma «silenzio invece di
    #     rosso» un piano piu' su, nel terreno.
    # ⇒ Si guarda l'ASCOLTATORE, il pid dell'unita', e la prima riga del
    #   registro: la guida del programma in testa e' la firma di
    #   «opzione rifiutata».
    rc, out, err = W.root(
        "ss -uln | grep -c ':%d ' ; systemctl show -p MainPID --value %s.service"
        " ; head -3 %s/registro.log" % (PORTA, UNITA, LAV))
    righe = (out or "").splitlines()
    ascolta = righe[0].strip() if righe else "0"
    pid = righe[1].strip() if len(righe) > 1 else "0"
    testa = " ".join(r.strip() for r in righe[2:5])
    if ascolta == "0" or pid in ("0", ""):
        firma = ""
        if "[opzioni]" in testa or "il server (fase" in testa:
            firma = ("  ⭐ E IL PERCHE' E' LETTO DAL PRODOTTO, non dedotto: la "
                     "testa del registro e' **la guida del programma** — cioe' "
                     "il server ha rifiutato un'opzione che non conosce, ha "
                     "stampato l'uso ed e' uscito.")
        return (False,
                "⛔ NON HO MISURATO: il server NON e' vivo dopo l'avvio con "
                "«%s» — ascoltatori sulla %d: %s · MainPID: %s.%s  ⚠ E il "
                "terreno era uscito ZERO: l'uscita non basta, si guarda "
                "l'ascoltatore" % (opzioni or "nessuna opzione", PORTA,
                                   ascolta, pid, firma))
    return (True, "acceso con «%s» — pid %s, ascolta sulla %d"
            % (opzioni or "nessuna opzione", pid, PORTA))


def spegni():
    subprocess.run(["bash", os.path.join(QUI, "10-d2-terreno.sh"), "spegni"],
                   env=dict(os.environ))


def _decisione(chi, dentro, nuovo, avvio, ritardo_ms, ammesso):
    """Una riga per `p_oracolo_contro_prodotto`, calcolata **dalla formula**."""
    atteso, _motivo, perche, _num = regge(
        dentro, nuovo, avvio.get("budget"), avvio.get("riserva"), ritardo_ms,
        tetto=avvio.get("tetto"))
    return {"chi": chi, "atteso": atteso, "ammesso": ammesso,
            "perche_oracolo": perche}


def _riempi_registrando(resta, giri=3):
    """Come `riempi_e_aspetta` di 10-b93, ma coi clienti che REGISTRANO.

    ⛔ Il suo `riempi_e_aspetta` non passa `registra`, e senza traccia non c'e'
       nessun «prima / durante / dopo» da confrontare: si saprebbe solo che cosa
       il server dice di aver mandato, che e' il lato sbagliato (§6.4).
    ⚠ E si ritenta, per la ragione che lui dichiara: un cliente che arriva
      mentre il posto del suo stesso utente e' ancora del fantasma riceve
      `0x0F` e muore, ed e' il caso normale subito dopo un giro.
    """
    for g in range(giri):
        rip = W.riempi(resta, registra=True)
        if W.aspetta_posti(rip["riga0"], tetto=45):
            return rip
        for pr in rip["proc"].values():
            try:
                pr.kill()
            except Exception:
                pass
        W.root("pkill -f '%s'; true" % W.modello_cliente("--porta %d" % PORTA))
        _dub("⚠ giro %d: la tabella non si e' riempita — aspetto che i fantasmi "
             "muoiano e riprovo" % (g + 1))
        W.aspetta_tabella_vuota()
    return None


# ── D2 e D6: i due bracci che si misurano con TRE utenti soli ──────────────
def raccogli_congedo(budget, tetto, riserva, max_att=None, quanti_dentro=2,
                     durata=30, con_finestre=False, finestra=20.0, guardia=2.0):
    """⭐ Riempie con i miei utenti, poi manda il terzo, e legge il CONGEDO.

    ⛔ Il respinto dev'essere un utente **DIVERSO** da quelli dentro, o
       `posto_prendi()` prenderebbe la strada «posto occupato» (`0x0F`) invece
       di quella del tetto: sono due rami diversi, e questo banco misura il
       secondo.  (E' la stessa ragione che 10-b93 ha scritto in testa.)
    """
    ok, perche = accendi(opzioni_del_budget(budget, tetto, riserva),
                         max_att=max_att)
    if not ok:
        return {"avvio": None, "tentativi": [], "decisioni": [],
                "non_misurato": perche}
    # ⛔ I DUE LETTORI DI TRACCIA vanno spediti PRIMA di misurare, o
    #    `leggi_traccia_canale` risponde «non ha risposto» e il banco direbbe
    #    «non ho letto il motivo» accusando il prodotto di un buco suo.
    W.spedisci_lettori(B._importa_b70())
    riga0 = W.righe_registro()
    avvio = avvio_del_server(1)
    # ⭐ Con le finestre, i clienti DENTRO registrano la propria traccia §11.1:
    #    e' l'unico modo di sapere che cosa hanno consegnato **mentre** il
    #    respinto bussava, invece di dedurlo dal registro del server.
    resta = durata + (2 * (finestra + guardia) + 30 if con_finestre else 0)
    rip = (_riempi_registrando(resta) if con_finestre
           else W.riempi_e_aspetta(resta))
    if rip is None:
        spegni()
        return {"avvio": avvio, "tentativi": [], "decisioni": [],
                "non_misurato": "⛔ NON HO MISURATO: la tabella non si e' "
                                "riempita ⇒ quel che segue misurerebbe un "
                                "server LIBERO"}
    try:
        larg, alt = (int(x) for x in W.TELA.lower().split("x"))
        costo = costo_mpixel_s(larg, alt, 60)
        dentro = [costo] * quanti_dentro
        if con_finestre:
            # ⛔ Le scene MUOVONO, o «prima» sarebbe zero e non ci sarebbe
            #    niente da confrontare: Mutter consegna solo quando qualcosa
            #    cambia.  (E' la ragione che 10-b93 scrive accanto a
            #    `scena_accendi`.)
            for u, ui in W.DENTRO:
                W.scena_accendi(u, ui, "d2-%s" % u)
            time.sleep(finestra + guardia + 2.0)
        t_ini = W.sod_adesso_sul_server()
        tent = [tentativo(W.RESPINTO[0], "d2-respinto-%02d" % k)
                for k in range(3)]
        t_fine = W.sod_adesso_sul_server()
        if con_finestre:
            time.sleep(finestra + guardia + 2.0)
        dec = [_decisione("il respinto", dentro, costo, avvio, 10.0,
                          ammesso=(t["arrivato_a"] == "SESSIONE"))
               for t in tent]
        return {"avvio": avvio, "tentativi": tent, "decisioni": dec,
                "riga0": riga0, "t_ini": t_ini, "t_fine": t_fine,
                "finestra": finestra, "guardia": guardia,
                "con_finestre": con_finestre}
    finally:
        if con_finestre:
            for _u, _ui in W.DENTRO:
                W.scena_spegni(_ui)
        for pr in (rip.get("proc") or {}).values():
            try:
                pr.kill()
            except Exception:
                pass
        W.root("pkill -f '%s'; true"
               % W.modello_cliente("--porta %d" % PORTA))
        spegni()


def misura_d2(budget=None, riserva=None):
    """⛔ D2: il budget stretto, il tetto largo, e chi arriva riceve `0x06`."""
    b = 1 if budget is None else budget          # 1 Mpixel/s: rifiuta chiunque
    f = SPEC.RISERVA_PREDEFINITA if riserva is None else riserva
    fatti = raccogli_congedo(b, 99, f)
    if fatti.get("non_misurato"):
        _dub(fatti["non_misurato"])
    return fatti


def misura_d6(sed_tetto=2, braccio="tutti"):
    """⛔ D6: i DUE bracci, e sono due giri di server distinti.

    ⭐ Il braccio **amministrativo** e' misurabile col binario di OGGI: il tetto
      e' `RCP_TETTO_SESSIONI` in `rcp.h`, e `10-d2-terreno.sh` lo abbassa col
      `sed` che **conta se ha morso** (la cura del 25 agosto: un `sed` su un
      modello che non c'e' piu' esce 0 senza sostituire, e il terreno
      dichiarava successo).
    ⛔ Il braccio **fisico** non lo e': senza `%s` non c'e' nessun limite di
      capacita' da far mordere ⇒ «non ho misurato».
    """ % SPEC.OPZ_BUDGET
    fuori = {}
    # ⭐ I due bracci si possono girare separati, e non e' una comodita': il
    #    braccio FISICO col binario di oggi **non accende nemmeno il server**,
    #    cioe' costa **zero GPU** e si puo' fare mentre un altro agente misura;
    #    quello AMMINISTRATIVO apre due sessioni grafiche vere e ⛔ **vuole il
    #    lucchetto**, anche se il numero che ne esce e' un byte sul filo.
    if braccio in ("tutti", "amministrativo"):
        _log("D6 · braccio AMMINISTRATIVO — tetto %d, budget larghissimo"
             % sed_tetto)
        fuori["amministrativo"] = raccogli_congedo(
            None, None, None, max_att=sed_tetto, quanti_dentro=sed_tetto)
        if fuori["amministrativo"].get("non_misurato"):
            _dub(fuori["amministrativo"]["non_misurato"])
    if braccio in ("tutti", "fisico"):
        _log("D6 · braccio FISICO — budget stretto, tetto largo")
        fuori["fisico"] = raccogli_congedo(1, 99, SPEC.RISERVA_PREDEFINITA)
        if fuori["fisico"].get("non_misurato"):
            _dub(fuori["fisico"]["non_misurato"])
    return fuori


# ── D1: la salita a gradini di 10-b92, e nient'altro ───────────────────────
def misura_d1(quanti=8, durata=45):
    """⛔ D1 chiama `10-b92-dieci.py`, e non ne riscrive una riga.

    ⚠ Serve il terreno dei dieci (`10-b91-terreno-dieci.sh`) e gli utenti
      `provamt*`, che sono **CONDIVISI**: il lucchetto della GPU prima, gli
      utenti dopo.
    """
    B.SCENA = "satura"
    B.B70 = B._importa_b70()
    if not B.terreno(quanti):
        return {"avvio": None, "gradini": [],
                "non_misurato": "⛔ NON HO MISURATO: il terreno di 10-b92 non "
                                "regge"}
    avvio = avvio_del_server(1)
    esiti, rossi, muti, fette, prima = B.salita(quanti, durata, False,
                                                durata * (quanti + 3))
    gradini = []
    for voce in esiti.get("gradini", []):
        sess = {}
        for i, n in (voce.get("sessioni") or {}).items():
            if not n:
                continue
            m = dict(n)
            m["ritardo_mediano_ms"] = (n.get("ritardo") or {}).get("mediano_ms")
            sess[i] = m
        gradini.append({"gradino": voce.get("gradino"),
                        "negati": (voce.get("server") or {}).get("negati"),
                        "sessioni": sess})
    return {"avvio": avvio, "gradini": gradini, "b92": esiti,
            "rossi_di_b92": rossi, "muti_di_b92": muti}




# ── D3: prima / durante / dopo, appaiato, attorno al rifiuto ───────────────
def misura_d3(budget=None, riserva=None, finestra=20.0, guardia=2.0):
    """⛔⛔ D3 misura chi era DENTRO **mentre** il respinto bussava.

    ⭐ E le tre finestre, l'ancora che le rende impossibili da confondere e il
      ponte fra i due orologi sono di `10-b93-pieno.py`: si chiamano, non si
      riscrivono.  ⚠ Il ponte usa DUE ancore indipendenti e, se non vanno
      d'accordo entro 200-300 ms, ⛔ **il banco non giudica le finestre** invece
      di indovinare l'offset.
    """
    b = 1 if budget is None else budget
    f = SPEC.RISERVA_PREDEFINITA if riserva is None else riserva
    base = raccogli_congedo(b, 99, f, con_finestre=True, finestra=finestra,
                            guardia=guardia)
    if base.get("non_misurato"):
        _dub(base["non_misurato"])
        return {"avvio": base.get("avvio"), "dentro": {}, "finestre": None,
                "non_misurato": base["non_misurato"]}
    B70 = B._importa_b70()
    dentro, estremi = {}, None
    for k, (u, _ui) in enumerate(W.DENTRO, start=1):
        canale = W.leggi_traccia_canale("dentro-%s" % u)
        _letto, giornale = W.leggi_traccia_video("dentro-%s" % u)
        righe_u = W.righe_ancora(base["riga0"], u)
        off, come = W.offset_del_cliente(canale.get("messaggi", []), righe_u,
                                         canale.get("ultimo_blocco_ms"))
        _inf("«%s»: %d fotogrammi nella traccia · %s" % (u, len(giornale), come))
        fin = W.spezza_in_finestre(giornale, off, base["t_ini"], base["t_fine"],
                                   finestra, guardia)
        if not fin:
            dentro[k] = {"prima": None, "durante": None, "dopo": None,
                         "perche": "⛔ l'offset fra i due orologi non e' stato "
                                   "misurato: %s" % come}
            continue
        guai = W.ancora_finestre(fin, base["t_ini"], base["t_fine"])
        if guai:
            dentro[k] = {"prima": None, "durante": None, "dopo": None,
                         "perche": "⛔ l'ancora si e' rifiutata: %s"
                                   % " · ".join(guai)}
            continue
        tre = {}
        for nome, righe in fin.items():
            n = B70.misura(righe, finestra, scaldata_s=0.0)
            n["ritardo_mediano_ms"] = (B.ritardi(righe) or {}).get("mediano_ms")
            tre[nome] = n
        dentro[k] = tre
        if estremi is None:
            estremi = {"prima": (base["t_ini"] - guardia - finestra,
                                 base["t_ini"] - guardia),
                       "durante": (base["t_ini"], base["t_fine"]),
                       "dopo": (base["t_fine"] + guardia,
                                base["t_fine"] + guardia + finestra)}
    return {"avvio": base.get("avvio"), "dentro": dentro, "finestre": estremi,
            "tentativi": base.get("tentativi")}


# ── D4 e D5: le miscele e il risveglio, che sono di 10-b98 ─────────────────
def _da_mista(n):
    """La fetta di `10-b98` nella forma che i miei predicati leggono.

    ⛔ Si prendono i numeri **della finestra** (`fps_finestra`,
       `byte_per_fotogramma_f`): sono gli unici che sappiano misurare una
       sessione FERMA, che in 40 s consegna **un** fotogramma.
    """
    if not n:
        return None
    return {"esito": n.get("esito"),
            "fps": n.get("fps_finestra"),
            "byte_per_fotogramma": n.get("byte_per_fotogramma_f"),
            "ritardo_mediano_ms": (n.get("ritardo_f") or {}).get("mediano_ms"),
            "chiavi": n.get("chiavi_finestra"),
            "fotogrammi": n.get("fotogrammi_finestra"),
            "disegni": {"disegni_s": 0.0},
            "numeri": n.get("numeri")}


def misura_d4(quante_ferme=10, durata=30):
    """⭐ D4: una che lavora e dieci FERME, e le dieci devono ENTRARE.

    ⛔ Serve il terreno dei dieci e gli utenti `provamt*`, che sono CONDIVISI:
       il lucchetto della GPU **prima**, gli utenti dopo.
    """
    ricetta = ["S"] + ["F"] * quante_ferme
    esiti, rossi, muti, fette, prima = M.miscela(ricetta, durata, False,
                                                 (durata + 140) * len(ricetta))
    avvio = avvio_del_server(1)
    ultimo = (esiti.get("gradini") or [{}])[-1]
    sess = ultimo.get("sessioni") or {}
    ferme = {i: _da_mista(sess.get(i)) for i in range(2, len(ricetta) + 1)}
    # ⛔ «entrata» lo dice il gradino in cui la sessione compare la PRIMA volta:
    #    se non compare mai, o non e' entrata o non l'ho misurata — e i due
    #    fatti si distinguono guardando se la salita si e' fermata li'.
    fermata = esiti.get("fermata_al_gradino")
    amm, motivi = {}, {}
    for i in range(2, len(ricetta) + 1):
        if i in (prima or {}):
            amm[i] = True
        elif fermata is not None and i >= fermata:
            amm[i] = False
            motivi[i] = "non e' entrata (la salita si e' fermata al %s)" % fermata
        else:
            amm[i] = None
    larg, alt = (int(x) for x in B.TELA.lower().split("x"))
    ferma_costo = 0.0            # `[M]` §6.16: una ferma consegna 0,05 Mpixel/s
    dec = []
    for i in sorted(amm):
        dec.append(_decisione("s%d (ferma)" % i, [costo_mpixel_s(larg, alt, 60)]
                              + [ferma_costo] * (i - 2), ferma_costo, avvio,
                              10.0, ammesso=amm[i]))
    lavora_prima = _da_mista((prima or {}).get(1))
    lavora_dopo = _da_mista(sess.get(1))
    return {"avvio": avvio, "ferme": ferme, "ammissioni": amm,
            "motivi": motivi, "decisioni": dec,
            "chi_lavora": {"prima": lavora_prima, "dopo": lavora_dopo},
            "b98": esiti, "rossi_di_b98": rossi, "muti_di_b98": muti}


def misura_d5(quante_ferme=8, durata=30, dopo_s=40):
    """⛔⛔ D5: il risveglio simultaneo, col metro a bucket di `10-b98`."""
    esiti, rossi, muti, bucket_di = M.risveglio(1, quante_ferme, durata,
                                                (durata + dopo_s) * 4 + 600,
                                                dopo_s)
    avvio = avvio_del_server(1)
    prima = {i: _da_mista(v) for i, v in (esiti.get("prima") or {}).items()
             if i != 1}
    dopo = {i: _da_mista(v) for i, v in (esiti.get("dopo") or {}).items()
            if i != 1}
    larg, alt = (int(x) for x in B.TELA.lower().split("x"))
    uno = costo_mpixel_s(larg, alt, 60)
    # ⛔⛔ E LA DOMANDA DOPO IL RISVEGLIO E' IL CASO PEGGIORE, NON IL CONSEGNATO.
    #     `[M]` §6.9 punto 3: una ferma consegna 0,05 Mpixel/s e una satura 82,0
    #     — un fattore **1 640**.  Chi contasse il consegnato direbbe che le otto
    #     svegliate chiedono ancora quasi niente, proprio mentre affamano tutti.
    #   ⇒ Una svegliata chiede quanto la sua TELA per la sua cadenza, che e'
    #     esattamente `costo(nuovo)` dell'oracolo: le due parti della
    #     disuguaglianza restano nella stessa moneta.
    quante_sveglie = sum(1 for i in dopo
                         if (dopo[i] or {}).get("byte_per_fotogramma") and
                         (prima.get(i) or {}).get("byte_per_fotogramma") and
                         dopo[i]["byte_per_fotogramma"] >=
                         MIO.RISVEGLIO_FATTORE_BYTE *
                         prima[i]["byte_per_fotogramma"])
    return {"avvio": avvio, "prima": prima, "dopo": dopo,
            "larghezza_ms": (esiti.get("risveglio") or {}).get("larghezza_ms"),
            "domanda_dopo_mpixel_s": uno * (quante_sveglie + 1),
            "titolare": {"prima": _da_mista((esiti.get("prima") or {}).get(1)),
                         "dopo": _da_mista((esiti.get("dopo") or {}).get(1))},
            "b98": esiti, "bucket": bucket_di,
            "rossi_di_b98": rossi, "muti_di_b98": muti}
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL PROGRAMMA
# ═══════════════════════════════════════════════════════════════════════════
def _oracolo_a_mano(a):
    """`oracolo` — il conto della specifica, a mano, per guardarlo.

    ⚠ Non e' una misura: e' la formula, esposta, cosi' che chi discute il
      disegno possa contraddirla senza leggere il codice.
    """
    dentro = []
    for pezzo in (a.dentro or "").split(","):
        pezzo = pezzo.strip()
        if not pezzo:
            continue
        if "x" in pezzo:
            l, r = pezzo.lower().split("x")
            if "@" in r:
                alt, cad = r.split("@")
            else:
                alt, cad = r, a.cadenza
            dentro.append(costo_mpixel_s(int(l), int(alt), float(cad)))
        else:
            dentro.append(float(pezzo))
    l, alt = (int(x) for x in a.nuovo.lower().split("x"))
    nuovo = costo_mpixel_s(l, alt, a.cadenza)
    v, motivo, perche, num = regge(dentro, nuovo, a.budget, a.riserva,
                                   a.ritardo, tetto=a.tetto)
    _log("L'ORACOLO — la formula, non una misura")
    _inf("grandezza: %s" % SPEC.GRANDEZZA)
    _inf("dentro: %s ⇒ domanda %s Mpixel/s"
         % (dentro, num.get("domanda_mpixel_s")))
    _inf("nuovo:  %s @ %s Hz ⇒ costo %.1f Mpixel/s" % (a.nuovo, a.cadenza, nuovo))
    {True: _ok, False: _ko, None: _dub}[v](
        "%s — %s" % ({True: "REGGE", False: "NON REGGE",
                      None: "NON SO"}[v], perche))
    if motivo is not None:
        _inf("il motivo atteso sul filo: %#04x" % motivo)
    _inf("⛔ e il ferro accanto al numero, sempre: %s" % FERRO)
    return 0 if v is not None else 3


def rapporto(domande):
    """⛔ Il verdetto del banco: rosso batte «non giudico», che batte verde."""
    _log("IL VERDETTO — %d domande" % len(domande))
    rossi = [d for d in domande if d["verdetto"] is False]
    muti = [d for d in domande if d["verdetto"] is None]
    for d in domande:
        f = {True: _ok, False: _ko, None: _dub}[d["verdetto"]]
        f("D%d %s" % (d["numero"], d["titolo"]))
    os.makedirs(FUORI, exist_ok=True)
    with open(os.path.join(FUORI, "10-d2-esiti.json"), "w") as f:
        json.dump(domande, f, ensure_ascii=False, indent=1, default=str)
    _inf("⛔ e il ferro accanto a ogni numero: %s" % FERRO)
    if rossi:
        return 1
    if muti:
        _dub("⛔ %d domande su %d NON HANNO NIENTE DA GIUDICARE — ⚠ e non e' un "
             "verde: e' il terzo esito" % (len(muti), len(domande)))
        return 3
    return 0


def principale():
    ap = argparse.ArgumentParser(
        description="10-d2-budget — il banco del budget, scritto PRIMA che il "
                    "budget esista.  ⛔ `--certifica` gira A SECCO.")
    ap.add_argument("passo", nargs="?", default="misura",
                    choices=["misura", "oracolo", "spegni"])
    ap.add_argument("--certifica", action="store_true",
                    help="⭐ i guasti, a secco: NON tocca la macchina di prova")
    ap.add_argument("--solo-miei", action="store_true",
                    help="con --certifica: non rifa' girare i banchi importati")
    ap.add_argument("--domanda", type=int, action="append",
                    help="quali delle sei misurare (ripetibile; def. tutte "
                         "quelle che il binario di oggi permette)")
    ap.add_argument("--quanti", type=int, default=8, help="D1: quanti gradini")
    ap.add_argument("--durata", type=int, default=45, help="D1: secondi a regime")
    ap.add_argument("--ferme", type=int, default=10,
                    help="D4: quante sessioni FERME accanto a chi lavora")
    ap.add_argument("--sveglie", type=int, default=8,
                    help="D5: quante ferme si svegliano insieme (`[M]` §6.16: 8)")
    ap.add_argument("--tetto-sed", type=int, default=2,
                    help="D6: il tetto amministrativo, messo col sed su rcp.h")
    ap.add_argument("--braccio", default="tutti",
                    choices=["tutti", "amministrativo", "fisico"],
                    help="D6: ⭐ «fisico» costa ZERO GPU (col binario di oggi "
                         "il server non parte nemmeno); «amministrativo» apre "
                         "due sessioni vere e ⛔ vuole il lucchetto")
    ap.add_argument("--senza-lucchetto", action="store_true",
                    help="⛔ solo per la messa a punto: i numeri NON valgono")
    # per il passo `oracolo`
    ap.add_argument("--dentro", default="",
                    help="es. «1920x1080,1920x1080@30» o dei Mpixel/s nudi")
    ap.add_argument("--nuovo", default="1920x1080")
    ap.add_argument("--cadenza", type=float, default=60.0)
    ap.add_argument("--budget", type=float, default=None)
    ap.add_argument("--riserva", type=float, default=SPEC.RISERVA_PREDEFINITA)
    ap.add_argument("--tetto", type=int, default=None)
    ap.add_argument("--ritardo", type=float, default=None,
                    help="il ritardo mediano di chi e' dentro, in ms")
    a = ap.parse_args()

    if a.certifica:
        return certifica(anche_gli_altri=not a.solo_miei)
    if a.passo == "oracolo":
        return _oracolo_a_mano(a)
    if a.passo == "spegni":
        spegni()
        return 0

    # ── il giro vero ──────────────────────────────────────────────────────
    _log("10-d2-budget — porta %d · albero %s · unita' %s" % (PORTA, ALB, UNITA))
    _inf("⛔ e il ferro: %s" % FERRO)
    quali = sorted(set(a.domanda or [1, 2, 4, 5, 6]))

    # ⛔ IL CONTROLLO DEL TERRENO DELLA FASE, prima di ogni misura.
    amb = dict(os.environ)
    amb.update({"CHI": IO_SONO, "PORTA": str(PORTA), "UTENTE": W.DENTRO[0][0],
                "ALBERO": ALB, "LAV": LAV, "LUCCHETTO": LUCCHETTO,
                "LUCCHETTO_MIO": "0" if a.senza_lucchetto else "1"})
    p = subprocess.run(["bash", os.path.join(QUI, "10-b0-terreno.sh")],
                       env=amb, capture_output=True, timeout=900)
    print((p.stdout + p.stderr).decode("utf-8", "replace")[-3000:])
    if p.returncode != 0 and not a.senza_lucchetto:
        _ko("⛔ 10-b0-terreno.sh esce %d: NON misuro" % p.returncode)
        return 2

    luc = None
    if not a.senza_lucchetto:
        os.environ["LUCCHETTO"] = LUCCHETTO
        luc = _carica("luc", "09-lucchetto.py")
        quanto = 900 + (a.durata + 140) * a.quanti if 1 in quali else 1800
        _inf("⛔ chiedo il lucchetto della GPU per %d s (%d min)"
             % (quanto, quanto // 60))
        try:
            luc.prendi(IO_SONO, secondi=quanto, attesa=21600)
        except Exception as e:
            _ko("⛔ NON MISURO: %s" % e)
            return 2
    else:
        _dub("⛔ SENZA LUCCHETTO: i numeri di questo giro NON valgono e non si "
             "riferiscono")

    domande = []
    try:
        if 1 in quali:
            _log("D1 · la salita col budget SPENTO")
            domande.append(stampa_domanda(
                d1_col_budget_spento(misura_d1(a.quanti, a.durata))))
        if 2 in quali:
            _log("D2 · il budget stretto e il CONGEDO sul filo")
            domande.append(stampa_domanda(d2_budget_pieno_sul_filo(misura_d2())))
        if 3 in quali:
            _log("D3 · chi era dentro, mentre il respinto bussa")
            domande.append(stampa_domanda(
                d3_chi_era_dentro_non_peggiora(misura_d3())))
        if 4 in quali:
            _log("D4 · una che lavora e %d FERME" % a.ferme)
            domande.append(stampa_domanda(
                d4_dieci_ferme_entrano(misura_d4(a.ferme, a.durata))))
        if 5 in quali:
            _log("D5 · il RISVEGLIO di %d ferme" % a.sveglie)
            domande.append(stampa_domanda(
                d5_il_risveglio(misura_d5(a.sveglie, a.durata))))
        if 6 in quali:
            domande.append(stampa_domanda(
                d6_due_tetti(misura_d6(a.tetto_sed, a.braccio))))
    finally:
        _log("⛔ LA MACCHINA SI RIMETTE COM'ERA")
        spegni()
        # ⛔⛔ SOLO I MIEI CLIENTI — §7.3: un modello globale a fine giro
        #     combaciava con 24 clienti vivi di un altro banco.  Il mio combacia
        #     con la MIA cartella di lavoro, e la classe di caratteri impedisce
        #     al modello di acchiappare la riga di comando che lo esegue.
        W.root("pkill -f -- '--registra [%s]%s/' ; true"
               % (W.DENTRO_LAV[0], W.DENTRO_LAV[1:]))
        W.root("pkill -f -- '--giornale [%s]%s/' ; true"
               % (W.DENTRO_LAV[0], W.DENTRO_LAV[1:]))
        for _u, _i in list(W.DENTRO) + [W.RESPINTO]:
            W.root("pkill -u %d -f '0[4]-b30-scena'; true" % _i)
        if luc:
            luc.molla(IO_SONO)
    return rapporto(domande)


if __name__ == "__main__":
    sys.exit(principale())
