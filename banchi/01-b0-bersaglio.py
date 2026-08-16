#!/usr/bin/env python3
"""01-b0-bersaglio.py — ⛔ IL REGISTRO DI OGNI GIRO, E LA RIGA CHE DICE CONTRO
CHE COSA HA MISURATO.

Il gemello in Python di `01-b0-bersaglio.sh`: quello sceglie e accende il
bersaglio, questo lo **scrive**.  Lo includono B5, B6, B7 e B8.

===========================================================================
⛔ PERCHE' ESISTE, E NON E' UN COMODO

*«Un registro che non dice contro quale server ha misurato mette in fila numeri
di due cose diverse»* — ed e' la forma d'errore che questo progetto paga piu'
spesso, perche' non ha nessun sintomo: i numeri sono tutti buoni, uno per uno.

⛔ E il caso concreto e' gia' sul disco.  `banchi/prodotto/b8-campioni.jsonl` e
   `b8-fatti.jsonl` sono i campioni del secondo fisso presi contro il
   **prodotto** la notte del 10 agosto 2026; `b8-fatti.jsonl` in
   `/media/REMOTIX/src/` sono quelli presi contro l'**innesto**.  Hanno lo
   stesso nome, la stessa forma, gli stessi campi — e nessuna riga, in nessuno
   dei due, dice quale server ha risposto.  Chi li mettesse insieme per avere
   «piu' campioni» calcolerebbe la mediana di due popolazioni diverse credendo
   di ridurre il rumore.

⭐ Da qui le tre cose che questo file impone, e che nessun banco puo' scordarsi:

  1. **ogni** riga porta `bersaglio`, `porta` e `giro`;
  2. la prima riga di ogni giro e' un record `giro` che porta anche
     l'**impronta vista** — cioe' quel che il registro del server dice di
     essere, non quel che il banco ha dichiarato (`LEZIONI.md` §1.9,
     corollario 5);
  3. si scrive e si **sincronizza** riga per riga: un file scritto e chiuso e'
     un fatto, una riga in un buffer e' una speranza sul momento in cui
     qualcuno la vedra' (§1.9, settima veste — e quella veste ha gia' accusato
     il codice giusto in questa fase).

===========================================================================
⛔ E IL BERSAGLIO NON E' UN'ETICHETTA: E' UN INSIEME DI FATTI

`PROFILO` tiene le differenze **note** fra i due server, misurate leggendo il
codice l'11 agosto 2026.  Un banco le legge di qui invece di scoprirle da capo,
e soprattutto invece di **non** scoprirle e dare rosso.
"""
import json
import os
import time

# ===========================================================================
# ⛔ LE DIFFERENZE NOTE, SCRITTE PRIMA DI MISURARE.
#
# Ogni riga ha accanto il file e la ragione: chi la trovasse falsa deve poter
# risalire in un minuto a dove l'abbiamo letta.
# ===========================================================================
PROFILO = {
    "innesto": {
        "porta": 7447,
        "eseguibile": "bsslserver (esempio di ngtcp2 + i due innesti)",
        # ⛔ B7: `RCP_SERVER_IN_CHIUSURA` (0x0C) non e' producibile.
        #    `01-b3-rcp-innesta.py` non ha nessun percorso di spegnimento —
        #    grep: zero occorrenze — quindi i motivi provocabili sono SETTE.
        "spegnimento": False,
        "motivi_provocabili": 7,
        # Dove puo' vivere un percorso di spegnimento su questo bersaglio.
        "sorgenti_spegnimento": ("rcp/rcp.c", "01-b3-rcp-innesta.py"),
        # ⭐ Il tetto d'inattivita' del trasporto si sceglie (`--timeout=Ns`).
        "idle_scelta": True,
        "idle_lungo": 120000,
        "idle_corto": 15000,
        # Le righe d'avvio sul ban, per B8.
        "r_ban_caricati": "ban caricati:",
        "r_ban_illeggibile": "NON HO POTUTO LEGGERE il file dei ban",
        "r_pagina": "pagina TCP a",
        # Se il file dei ban c'e' e non si legge, questo server parte lo stesso
        # e lo scrive.
        "ban_illeggibile_parte": True,
        # L'impronta di ogni riga del suo registro.
        "impronta": r"REMOTIX B[35]:",
        "controllo": "REMOTIX B3",
        # ⛔⭐ L'ECO DI B2, e questa riga esiste per una trappola gia' pagata
        #     DUE volte.  Il server minimo di B2 **rimanda indietro** i byte
        #     ricevuti sugli stream che il client apre — e' il «byte che torna»
        #     del gruppo 2 di `FASI.md` §01-filo-nudo.  Uno strumento che aspetta
        #     quell'eco resta appeso contro il prodotto, che l'eco non ce l'ha,
        #     e il rosso che ne esce il 10 agosto 2026 e' stato diagnosticato
        #     per ore come «difetto del certificato».
        "eco": True,
        # ⛔⭐ IL TETTO DI §7.17 — sessione WebTransport aperta e canale di
        #     controllo mai aperto, 5 s — QUESTO SERVER NON CE L'HA.
        #
        # `[M]` 11 agosto 2026, misurato da B6 in un giro di certificazione:
        # `ciao-senza-controllo` resta appeso **20 s senza che succeda niente**.
        # ⭐ E il banco aveva ragione: la cura di §7.17 e' `WT_TETTO_CANALE_NS`
        # in `src/webtransport.c`, cioe' nel PRODOTTO.  L'innesto e' l'esempio
        # di ngtcp2 con gli innesti sopra, e uno strato WebTransport suo non ce
        # l'ha — quel tetto non ha un posto dove vivere.
        # ⚠ E' la stessa forma di `spegnimento`: una proprieta' che esiste su un
        #   bersaglio solo, dichiarata invece che scoperta a ogni giro.
        # ⛔ Senza questa riga B6 non si puo' CERTIFICARE: il giro sano esce 1,
        #   e un banco che non parte dal verde non dimostra niente col guasto.
        "tetto_canale": False,
    },
    "prodotto": {
        "porta": 7448,
        "eseguibile": "remotix (src/)",
        # ⭐ `src/main.c` congeda tutte le sessioni con `SERVER_IN_CHIUSURA`
        #    prima di uscire, e aspetta fino a due secondi che i byte escano:
        #    il motivo 0x0C E' provocabile, e i provocabili diventano OTTO.
        "spegnimento": True,
        "motivi_provocabili": 8,
        # ⛔ E NON si cerca in `rcp.c`: `rcp.c` e' identico nei due server e non
        #    sa che esista un processo.  Il percorso vive in `main.c`,
        #    `trasporto.c` (`trasporto_congeda_tutte`) e `webtransport.c`
        #    (`wt_congeda`).  Un denominatore si legge dove la cosa succede.
        "sorgenti_spegnimento": ("remotix/rcp.c", "remotix/main.c",
                                 "remotix/trasporto.c", "remotix/webtransport.c"),
        # ⛔ `#define IDLE_MS 30000` in `src/trasporto.c`, e nessuna opzione lo
        #    tocca (nessun `getenv` in tutto `src/`).
        "idle_scelta": False,
        "idle_lungo": 30000,
        "idle_corto": 30000,
        "r_ban_caricati": "indirizzi caricati",
        "r_ban_illeggibile": "c'e' e NON si e' potuto leggere",
        "r_pagina": "ascolto TCP su",
        # ⛔⭐ E QUI I DUE SERVER FANNO L'OPPOSTO: il prodotto RIFIUTA di
        #     partire (`src/main.c`), perche' «non e' "zero ban", e' la
        #     protezione di §4.4-bis spenta».
        "ban_illeggibile_parte": False,
        "impronta": r"^\d\d:\d\d:\d\d\.\d\d\d (avvio|quic|wt|rcp|pagina|cert) ",
        "controllo": "REMOTIX_V2 — fase 1, il filo nudo",
        # ⛔ NESSUNA ECO.  `src/webtransport.c`, `scarta_stream_di_troppo()`:
        #    «i byte di uno stream di troppo si buttano, e NON si rimandano
        #    indietro».  ⚠ Nessuno dei quattro banchi deve **aspettare** byte di
        #    ritorno su uno stream che ha aperto lui: chi lo facesse resterebbe
        #    appeso, e la diagnosi finirebbe su qualunque cosa tranne che su
        #    questa riga.  B5 la incontra e la tollera gia' (scarta l'eco senza
        #    aspettarla): qui si dichiara, perche' un'assenza tollerata e
        #    un'assenza mai avvenuta non devono avere lo stesso aspetto.
        "eco": False,
        # ⭐ `WT_TETTO_CANALE_NS` in `src/webtransport.c`, armato
        #    all'apertura della sessione (`cb_end_headers`) e fatto
        #    valere in `wt_batti`.  `DECISIONI.md` §7.17.
        "tetto_canale": True,
    },
}


# ⛔ E il verdetto sull'eco non e' una nota: e' un numero che il banco confronta.
def eco_attesa(bersaglio):
    """Quanti stream devono riportare byte dal server.  0 sul prodotto."""
    return profilo(bersaglio)["eco"]


def profilo(nome):
    """⛔ Un bersaglio sconosciuto non ripiega su «innesto»: si ferma.

    ⚠ `controllo` sta nella grammatica (`--bersaglio {innesto,prodotto,
      controllo}`, la stessa della sonda del trasporto) e **non** in questa
      tabella: per B5, B6, B7 e B8 il server guasto di proposito verso il filo
      non esiste ancora.  ⛔ Farlo cadere su «innesto» darebbe un VERDE del caso
      sano al posto di un controllo che deve diventare rosso, che e' peggio di
      un controllo assente.
    """
    if nome == "controllo":
        raise SystemExit(
            "⛔ bersaglio «controllo»: la grammatica lo prevede, questi quattro "
            "banchi non ce l'hanno ancora.  Sarebbe il server GUASTO DI "
            "PROPOSITO, quello contro cui il banco deve diventare rosso "
            "(LEZIONI.md §1.2); oggi esiste solo verso la pagina "
            "(01-b11-guasto-innesta.py), non verso il filo.")
    if nome not in PROFILO:
        raise SystemExit(
            f"⛔ bersaglio «{nome}» sconosciuto: i valori sono "
            f"{', '.join(PROFILO)} e «controllo».  Non ripiego su nessuno — "
            f"misurerei un server dichiarandone un altro.")
    return PROFILO[nome]


def aggiungi_argomenti(p):
    """⛔ Gli stessi quattro argomenti in tutt'e quattro i banchi, e in un posto
    solo — cosi' il giorno in cui se ne aggiunge uno si aggiunge una volta.

    ⛔ `--bersaglio` e' **obbligatorio e senza predefinito**, ed e' la stessa
       forma con cui la sonda del trasporto sceglie il proprio: due convenzioni
       diverse per la stessa cosa sono il difetto delle cuciture.  ⚠ Un
       predefinito qui vorrebbe dire che un giro puo' misurare il server
       sbagliato per distrazione, e il registro lo scriverebbe come se fosse
       quello giusto.
    """
    p.add_argument("--bersaglio", required=True,
                   choices=("innesto", "prodotto", "controllo"),
                   help="⛔ obbligatorio: contro quale server si misura")
    p.add_argument("--uscita", default="",
                   help="il registro dei fatti di questo giro (.jsonl)")
    p.add_argument("--giro", default="",
                   help="l'identificatore del giro, uguale per tutte le righe")
    p.add_argument("--md5", default="",
                   help="l'impronta md5 del BINARIO misurato, per il registro")
    return p


def sorgenti_spegnimento(bersaglio, dentro="/srv/src"):
    """⛔ Dove si cerca un percorso di spegnimento, per il denominatore di B7.

    ⛔⭐ E NON E' `rcp.c`, che e' identico byte per byte nei due server e non sa
        che esista un processo: cercarlo li' direbbe «zero» su tutt'e due i
        bersagli, ed e' un denominatore letto dove la cosa NON succede
        (`LEZIONI.md` §1.9, corollario 5).  Sul prodotto il percorso vive in
        `main.c`, `trasporto.c` e `webtransport.c`.
    """
    return [f"{dentro}/{p}" for p in profilo(bersaglio)["sorgenti_spegnimento"]]


class Registro:
    """Una riga per fatto, con dentro il bersaglio, e sincronizzata subito.

    ⚠ `percorso` vuoto NON e' un errore silenzioso: il banco continua a
      misurare e a stampare, ma `dichiarato_senza_registro` diventa vero e chi
      legge il verdetto lo vede.  ⛔ Un registro assente e un registro vuoto non
      devono avere lo stesso aspetto.
    """

    def __init__(self, percorso, bersaglio, porta, giro=None, md5=None):
        self.percorso = percorso or ""
        self.bersaglio = bersaglio
        self.porta = porta
        self.giro = giro or time.strftime("%Y%m%d-%H%M%S")
        # ⛔ L'impronta md5 del BINARIO misurato, non del sorgente: e' l'unico
        #    modo di sapere, sei ore dopo, se due giri hanno misurato lo stesso
        #    programma.  ⚠ `[M]` 11 agosto 2026: il binario del prodotto era
        #    piu' vecchio dei sorgenti di un'ora, e il registro dell'ultima
        #    accensione portava una formulazione di due generazioni prima.
        self.md5 = md5 or "ignota"
        self.scritte = 0
        self.guasto = None
        self.profilo = profilo(bersaglio)

    def apri_giro(self, banco, scena, impronta_vista=None, extra=None):
        """⛔ La prima riga di ogni giro, e porta l'impronta VISTA.

        `impronta_vista` e' quel che il registro del SERVER dice di essere; se
        e' `None` vuol dire «non l'ho guardata», che non e' «combacia».
        """
        rec = {"tipo": "giro", "banco": banco, "scena": scena,
               "impronta_dichiarata": self.bersaglio,
               "impronta_vista": impronta_vista,
               "eseguibile": self.profilo["eseguibile"],
               "spegnimento": self.profilo["spegnimento"],
               "idle_scelta": self.profilo["idle_scelta"]}
        if extra:
            rec.update(extra)
        return self.scrivi(rec)

    def scrivi(self, rec):
        """⛔ Il bersaglio, la porta e il giro entrano in OGNI riga, e li mette
        questa funzione: un campo che quattro banchi devono ricordarsi di
        aggiungere e' un campo che prima o poi manca in uno dei quattro."""
        fuori = {"giro": self.giro, "bersaglio": self.bersaglio,
                 "porta": self.porta, "md5": self.md5, "quando": time.time()}
        fuori.update(rec)
        if not self.percorso:
            self.guasto = "nessun --uscita: questo giro non lascia registro"
            return False
        try:
            with open(self.percorso, "a") as f:
                f.write(json.dumps(fuori, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except OSError as e:
            # ⛔ E non si tace: un registro che non si scrive e uno che non si
            #    e' chiesto sono due fatti diversi, e il secondo e' colpa di chi
            #    lancia mentre il primo e' un disco.
            self.guasto = f"il registro «{self.percorso}» non si scrive: {e}"
            return False
        self.scritte += 1
        return True

    def riassunto(self):
        """La riga che ogni banco stampa in fondo: quante ne ha scritte e dove.

        ⛔ Con il denominatore: «ho scritto il registro» senza un numero e'
           vero anche quando le righe sono zero (`LEZIONI.md` §1.9, regola 6 —
           anche un verdetto ha un denominatore)."""
        if self.guasto:
            return f"⛔ REGISTRO: {self.guasto}  ({self.scritte} righe scritte)"
        return (f"registro del giro «{self.giro}» contro «{self.bersaglio}»: "
                f"{self.scritte} righe in {self.percorso}")
