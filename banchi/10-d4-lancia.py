#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-d4-lancia — ⭐⭐ IL LANCIATORE DI `10-d4-stretta.c`, e il suo giudice.

⛔ Che cosa prova, in una riga: **chiudere il canale di input prima che la
   stretta di mano di `libei` sia arrivata ammazzava il figlio**, e adesso no —
   ⭐ **senza perdere la chiusura vera** su un canale maturo.

---------------------------------------------------------------------------
⭐⭐ COME SI COSTRUISCE IL ROSSO — e non e' un'opzione del prodotto

Il banco compila `banchi/10-d4-stretta.c` contro **piu' versioni di `src/input.c`**:

  · `curato`   l'albero com'e' adesso;
  · `pristino` `git show <RIF>:src/input.c` — l'albero **senza la cura**.  ⛔ E'
               il rosso vero, non una sua imitazione: e' il codice che girava;
  · i **guasti**, che sono sostituzioni di testo ESATTO sulla copia curata.  Se
    il testo non combacia — perche' `input.c` e' cambiato — l'innesto
    **fallisce** invece di indovinare dove mettere le righe.

⛔ Nessuna variabile d'ambiente e nessun interruttore di compilazione entra nel
   prodotto (`CODER.md` §2-bis): il guasto vive **solo** nella copia del banco.

---------------------------------------------------------------------------
⛔ I PREDICATI — e ciascuno ha il suo guasto, che deve farlo mordere

  P1  scena `immaturo`: il processo **VIVE** (nessun segnale).
  P2  scena `immaturo`: la finestra e' stata **attraversata davvero** —
      `stretta=no` e `vissuto_ms` >= l'attesa chiesta.  ⭐ `LEZIONI.md` §1.30:
      «non e' morto» non vale se la finestra non c'e' stata.
  P3  scena `immaturo`: il contesto e' stato **abbandonato una volta**
      (`abbandoni=1`) — cioe' la cura e' passata di li', non l'ha scansata.
  P4  scena `immaturo`: **nessun descrittore perso** (`fd_dopo <= fd_prima`).
  P5  scena `maturo`: il processo vive, `stretta=si`, `abbandoni=0`.
  P6  scena `maturo`: ⭐⭐ **la chiusura VERA funziona ancora** — il server EIS
      ha visto il distacco (`disconnesso_visto=1`) e i dispositivi virtuali
      creati sono spariti.
  P7  scena `caduta-immatura`: ⭐⭐ **la terza strada** — il compositore muore
      mentre la stretta non e' ancora arrivata.  Il processo vive, e
      `input_gira()` ha DICHIARATO il canale morto (`gira=-1`): «non e' morto»
      non basta se la caduta non e' stata nemmeno vista.

Uso:
    python3 banchi/10-d4-lancia.py                 il sano: curato, tutte le scene
    python3 banchi/10-d4-lancia.py --certifica     sano + pristino + tutti i guasti
    python3 banchi/10-d4-lancia.py --rif=HEAD~1    da dove si prende il pristino
    python3 banchi/10-d4-lancia.py --pristino=<f>  ⭐ dove non c'e' `git` (macchina di prova)
    python3 banchi/10-d4-lancia.py --attesa=<ms>   quanto si sta nella finestra

⛔ E le due meta', per la macchina di prova — il cui contenitore ha `libei` ma
   **non** `libeis`, e fuori dal contenitore non c'e' `cc`:

    python3 banchi/10-d4-lancia.py --certifica --porta-i-binari=<dir>   (compila)
    …si copiano i binari sulla macchina, e la'…
    python3 10-d4-lancia.py --certifica --gia-compilati=<dir>           (fa girare)

  ⚠ Il banco stampa l'md5 di `libei`/`libeis` da tutt'e due le parti: chi legge
    CONFRONTA, invece di fidarsi che siano la stessa libreria.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ALBERO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO = os.path.join(ALBERO, "banchi", "10-d4-stretta.c")
INPUT_C = os.path.join(ALBERO, "src", "input.c")
TASTIERA_C = os.path.join(ALBERO, "src", "tastiera.c")

# ═════════════════════════════════════════════════════════════════════════════
# I GUASTI — testo ESATTO, e l'innesto fallisce se non combacia
# ═════════════════════════════════════════════════════════════════════════════
GUASTI = {
    # ⛔ IL CONTROLLO NEGATIVO PUNTUALE: il predicato dice sempre «maturo», cioe'
    #    esattamente quel che il codice faceva prima della cura.
    "sempre-maturo": (
        "\tif (in->stretta_fatta)\n\t{\n",
        "\tif (TRUE) /* GUASTO 10-d4 sempre-maturo */\n\t{\n",
    ),
    # ⛔ Il verso opposto: non si disconnette MAI.  Serve a provare che il
    #    predicato non e' decorativo — se lo fosse, il maturo resterebbe verde.
    "mai-maturo": (
        "\tif (in->stretta_fatta)\n\t{\n",
        "\tif (FALSE) /* GUASTO 10-d4 mai-maturo */\n\t{\n",
    ),
    # ⛔ Il guasto sull'EVENTO invece che sul ramo: la stretta arriva e non si
    #    segna.  Stesso danno, altro punto d'innesto.
    "senza-connect": (
        "\t\t\tin->stretta_fatta = TRUE;\n",
        "\t\t\tin->stretta_fatta = FALSE; /* GUASTO 10-d4 senza-connect */\n",
    ),
    # ⛔ Il prezzo non pagato: si abbandona il contesto e si perdono i suoi due
    #    descrittori.  ⇒ P4 deve mordere.
    "senza-chiusura-fd": (
        "\tif (epoll_di_libei >= 0)\n"
        "\t\tclose(epoll_di_libei);\n"
        "\tif (in->fd_socket >= 0)\n"
        "\t\tclose(in->fd_socket);\n",
        "\t/* GUASTO 10-d4 senza-chiusura-fd: i due descrittori si perdono */\n",
    ),
    # ⛔⛔ La guardia della TERZA STRADA tolta: si dispaccia lo stesso un canale
    #     immaturo il cui compositore e' morto.  ⇒ P7 deve mordere, e mordere
    #     vuol dire **segnale 11 dentro `ei_dispatch()`**.
    "senza-guardia-caduta": (
        "\tif (!in->stretta_fatta && in->ei && in->fd_socket >= 0)\n",
        "\tif (FALSE) /* GUASTO 10-d4 senza-guardia-caduta */\n",
    ),
}

# Che cosa ci si aspetta da ogni braccio.  ⛔ `None` = «non lo giudico».
#
# ⭐ La scena `caduta-immatura` e' la TERZA STRADA di `fasi/10-…md` §5.1 — *«il
#    palco se n'e' andato»* — e su di lei il rosso e' il piu' istruttivo della
#    fase: `[M]` senza la guardia il figlio muore **dentro `ei_dispatch()`**, e
#    non in chiusura.
ATTESI = {
    "curato": {"immaturo": "vivo", "maturo": "vivo", "caduta-immatura": "vivo"},
    "pristino": {"immaturo": "morto", "maturo": "vivo", "caduta-immatura": "morto"},
    "sempre-maturo": {"immaturo": "morto", "maturo": "vivo", "caduta-immatura": "morto"},
    "mai-maturo": {"immaturo": "vivo", "maturo": "senza-distacco", "caduta-immatura": "vivo"},
    "senza-connect": {"immaturo": "vivo", "maturo": "senza-distacco", "caduta-immatura": "vivo"},
    "senza-chiusura-fd": {
        "immaturo": "descrittori-persi",
        "maturo": "vivo",
        "caduta-immatura": "vivo",
    },
    "senza-guardia-caduta": {"immaturo": "vivo", "maturo": "vivo", "caduta-immatura": "morto"},
}


def dimmi(riga=""):
    print(riga, flush=True)


def pkgconfig(che, quali):
    out = subprocess.run(["pkg-config", che] + quali, capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return out.stdout.split()


def compila(dove, sorgente_input, nome):
    """Compila il banco contro UNA versione di `input.c`.  Torna il percorso o None."""
    cflags = pkgconfig("--cflags", ["glib-2.0", "gio-2.0", "libei-1.0"])
    libs = pkgconfig("--libs", ["glib-2.0", "gio-2.0", "libei-1.0"])
    if cflags is None or libs is None:
        return None, "pkg-config non sa di glib/libei"
    uscita = os.path.join(dove, "10-d4-" + nome)
    cmd = (
        ["cc", "-O1", "-g", "-std=gnu11", "-D_GNU_SOURCE", "-w",
         # ⚠ La copia di `input.c` vive in una cartella temporanea: i suoi
         #   `#include "…"` vanno cercati in `src/`, non accanto a lei.
         "-I" + os.path.join(ALBERO, "src")]
        + cflags
        + ["-o", uscita, BANCO, sorgente_input, TASTIERA_C]
        + libs
        + ["-leis", "-lxkbcommon"]
    )
    fatto = subprocess.run(cmd, capture_output=True, text=True)
    if fatto.returncode != 0:
        return None, fatto.stderr.strip()[-1200:]
    return uscita, None


def innesta(testo, nome):
    vecchio, nuovo = GUASTI[nome]
    if testo.count(vecchio) != 1:
        return None, "il testo da sostituire compare %d volte, non 1" % testo.count(vecchio)
    return testo.replace(vecchio, nuovo), None


def gira(binario, scena, attesa=60):
    """Fa girare UNA scena.  Torna un dizionario, e `segnale` None se non e' morto."""
    fatto = subprocess.run(
        [binario, scena, "--attesa=%d" % attesa], capture_output=True, text=True, timeout=60
    )
    esito = {
        "scena": scena,
        "codice": fatto.returncode,
        "segnale": -fatto.returncode if fatto.returncode < 0 else None,
        "riga": None,
        "campi": {},
        "registro": fatto.stderr,
    }
    for r in fatto.stdout.splitlines():
        if r.startswith("10-d4 "):
            esito["riga"] = r
            for pezzo in r.split()[1:]:
                if "=" in pezzo:
                    k, v = pezzo.split("=", 1)
                    esito["campi"][k] = v
    return esito


def giudica(braccio, esiti, attesa):
    """⛔ Torna (verdetto, righe).  `verdetto` e' 'come atteso' o il perche' no."""
    righe = []
    guai = []

    im = esiti.get("immaturo")
    ma = esiti.get("maturo")
    voluto_im = ATTESI[braccio]["immaturo"]
    voluto_ma = ATTESI[braccio]["maturo"]

    # ── la scena immatura ──────────────────────────────────────────────────
    if im is None:
        guai.append("immaturo: non ho potuto misurare")
    elif voluto_im == "morto":
        if im["segnale"] != 11:
            guai.append(
                "immaturo: mi aspettavo il segnale 11 e ho avuto %s"
                % (("segnale %d" % im["segnale"]) if im["segnale"] else "codice %d" % im["codice"])
            )
        elif "ei_disconnect" not in im["registro"]:
            # ⛔ Il segnale da solo non basta: un SIGSEGV qualsiasi non e' QUESTO
            #    SIGSEGV.  La pila deve nominare la funzione che cade.
            guai.append("immaturo: segnale 11, ma la pila NON nomina ei_disconnect")
        else:
            pila = [
                x.strip()
                for x in im["registro"].splitlines()
                if "libei" in x or "10-d4" in x and "(" in x
            ]
            righe.append("  ⛔ immaturo: MORTO di segnale 11 — come atteso")
            for x in pila[:4]:
                righe.append("     %s" % x)
    else:
        if im["segnale"] is not None:
            guai.append("immaturo: morto di segnale %d, e non doveva" % im["segnale"])
        elif im["codice"] == 4:
            guai.append("immaturo: la scena NON ha morso (il canale e' maturato)")
        elif im["riga"] is None:
            guai.append("immaturo: nessuna riga di esito (codice %d)" % im["codice"])
        else:
            c = im["campi"]
            vissuto = int(c.get("vissuto_ms", -1))
            if c.get("stretta") != "no":
                guai.append("immaturo: stretta=%s — la finestra non c'era" % c.get("stretta"))
            elif vissuto < attesa:
                guai.append("immaturo: vissuto %d ms < attesa %d ms" % (vissuto, attesa))
            else:
                righe.append(
                    "  ⭐ immaturo: VIVO — finestra attraversata %d ms con stretta=no, "
                    "abbandoni=%s" % (vissuto, c.get("abbandoni"))
                )
            if voluto_im == "descrittori-persi":
                if int(c.get("fd_dopo", 0)) <= int(c.get("fd_prima", 0)):
                    guai.append(
                        "immaturo: nessun descrittore perso (%s → %s), e il guasto doveva "
                        "farne perdere" % (c.get("fd_prima"), c.get("fd_dopo"))
                    )
                else:
                    righe.append(
                        "  ⛔ immaturo: descrittori %s → %s — il guasto ha morso"
                        % (c.get("fd_prima"), c.get("fd_dopo"))
                    )
            else:
                if c.get("abbandoni") != "1":
                    guai.append(
                        "immaturo: abbandoni=%s, e la cura doveva passare di li' una volta"
                        % c.get("abbandoni")
                    )
                if int(c.get("fd_dopo", 0)) > int(c.get("fd_prima", 0)):
                    guai.append(
                        "immaturo: descrittori PERSI (%s → %s)"
                        % (c.get("fd_prima"), c.get("fd_dopo"))
                    )
                else:
                    righe.append(
                        "  ⭐ immaturo: descrittori %s → %s, nessuno perso"
                        % (c.get("fd_prima"), c.get("fd_dopo"))
                    )

    # ── la scena matura ────────────────────────────────────────────────────
    if ma is None:
        guai.append("maturo: non ho potuto misurare")
    elif ma["segnale"] is not None:
        guai.append("maturo: morto di segnale %d" % ma["segnale"])
    elif ma["codice"] == 4:
        guai.append("maturo: la scena NON ha morso (il canale non e' maturato)")
    elif ma["riga"] is None:
        guai.append("maturo: nessuna riga di esito (codice %d)" % ma["codice"])
    else:
        c = ma["campi"]
        if c.get("stretta") != "si":
            guai.append("maturo: stretta=%s" % c.get("stretta"))
        if c.get("dispositivi_creati", "0") == "0":
            guai.append("maturo: nessun dispositivo virtuale creato — la scena non morde")
        visto = c.get("disconnesso_visto") == "1"
        if voluto_ma == "senza-distacco":
            if visto:
                guai.append(
                    "maturo: il distacco si e' visto lo stesso, e il guasto doveva toglierlo"
                )
            else:
                righe.append(
                    "  ⛔ maturo: il server EIS NON ha visto il distacco — il guasto ha morso "
                    "(abbandoni=%s)" % c.get("abbandoni")
                )
        else:
            if not visto:
                guai.append("maturo: il server EIS NON ha visto il distacco: chiusura vera PERSA")
            elif c.get("abbandoni") != "0":
                guai.append("maturo: abbandoni=%s su un canale maturo" % c.get("abbandoni"))
            else:
                righe.append(
                    "  ⭐ maturo: chiusura VERA — distacco visto dal server, %s dispositivi "
                    "virtuali creati e %s chiusi, abbandoni=0"
                    % (c.get("dispositivi_creati"), c.get("dispositivi_persi"))
                )

    # ── la scena della CADUTA IMMATURA — la terza strada ───────────────────
    ca = esiti.get("caduta-immatura")
    voluto_ca = ATTESI[braccio]["caduta-immatura"]
    if ca is None:
        guai.append("caduta-immatura: non ho potuto misurare")
    elif voluto_ca == "morto":
        if ca["segnale"] != 11:
            guai.append(
                "caduta-immatura: mi aspettavo il segnale 11 e ho avuto %s"
                % (("segnale %d" % ca["segnale"]) if ca["segnale"] else "codice %d" % ca["codice"])
            )
        elif "ei_disconnect" not in ca["registro"]:
            guai.append("caduta-immatura: segnale 11, ma la pila NON nomina ei_disconnect")
        else:
            righe.append(
                "  ⛔ caduta-immatura: MORTO di segnale 11 DENTRO ei_dispatch — come atteso"
            )
            for x in [x.strip() for x in ca["registro"].splitlines() if "libei" in x][:3]:
                righe.append("     %s" % x)
    elif ca["segnale"] is not None:
        guai.append("caduta-immatura: morto di segnale %d, e non doveva" % ca["segnale"])
    elif ca["riga"] is None:
        guai.append("caduta-immatura: nessuna riga di esito (codice %d)" % ca["codice"])
    else:
        c = ca["campi"]
        if c.get("stretta") != "no":
            guai.append("caduta-immatura: stretta=%s — la scena non morde" % c.get("stretta"))
        elif c.get("gira") != "-1":
            # ⛔ Se `input_gira()` non ha dichiarato il canale morto, la caduta
            #    non e' stata nemmeno vista: non e' un verde, e' un non-evento.
            guai.append(
                "caduta-immatura: input_gira ha detto %s e non -1: la caduta non e' stata vista"
                % c.get("gira")
            )
        elif int(c.get("fd_dopo", 0)) > int(c.get("fd_prima", 0)):
            guai.append(
                "caduta-immatura: descrittori PERSI (%s → %s)"
                % (c.get("fd_prima"), c.get("fd_dopo"))
            )
        else:
            righe.append(
                "  ⭐ caduta-immatura: VIVO — il canale e' stato dichiarato morto "
                "(input_gira=-1), abbandoni=%s, descrittori %s → %s"
                % (c.get("abbandoni"), c.get("fd_prima"), c.get("fd_dopo"))
            )

    return ("come atteso" if not guai else "; ".join(guai)), righe


def prepara(dove, braccio, rif, pristino_file=None):
    """Prepara il sorgente di `input.c` per un braccio.  Torna (percorso, errore)."""
    sorgente = os.path.join(dove, "input-%s.c" % braccio)
    if braccio == "curato":
        shutil.copyfile(INPUT_C, sorgente)
        return sorgente, None
    if braccio == "pristino":
        # ⚠ Due strade, e la seconda serve DAVVERO: sulla macchina di prova
        #   l'albero arriva per `tar` e non c'e' nessun `git` a cui chiedere.
        if pristino_file:
            if not os.path.exists(pristino_file):
                return None, "il pristino «%s» non c'e'" % pristino_file
            shutil.copyfile(pristino_file, sorgente)
            return sorgente, None
        fatto = subprocess.run(
            ["git", "-C", ALBERO, "show", "%s:src/input.c" % rif], capture_output=True, text=True
        )
        if fatto.returncode != 0:
            return None, "git show %s:src/input.c: %s" % (rif, fatto.stderr.strip())
        with open(sorgente, "w") as f:
            f.write(fatto.stdout)
        return sorgente, None
    with open(INPUT_C) as f:
        testo = f.read()
    rotto, sbaglio = innesta(testo, braccio)
    if rotto is None:
        return None, sbaglio
    with open(sorgente, "w") as f:
        f.write(rotto)
    return sorgente, None


def main():
    certifica = "--certifica" in sys.argv
    rif = "HEAD"
    attesa = 60
    pristino_file = None
    # ⛔⛔ LE DUE META' — e servono per una ragione VERA, non per eleganza: sulla
    #     macchina di prova il contenitore ha `libei` ma **non** `libeis`, e fuori
    #     dal contenitore non c'e' `cc`.  ⇒ Si compila dove c'e' il compilatore e
    #     si fa girare dove sta il ferro, con gli **stessi** binari.
    #     ⚠ Le due macchine devono avere la stessa `libei`: il banco stampa l'md5
    #       da tutt'e due le parti, e chi legge confronta invece di fidarsi.
    porta = None      # --porta-i-binari=<dir>: compila e basta
    gia = None        # --gia-compilati=<dir>: fa girare e basta
    for a in sys.argv[1:]:
        if a.startswith("--rif="):
            rif = a[6:]
        elif a.startswith("--attesa="):
            attesa = int(a[9:])
        elif a.startswith("--pristino="):
            pristino_file = a[11:]
        elif a.startswith("--porta-i-binari="):
            porta = a[17:]
        elif a.startswith("--gia-compilati="):
            gia = a[16:]

    bracci = ["curato"]
    if certifica:
        bracci = ["curato", "pristino"] + list(GUASTI)

    dimmi("══ 10-d4 · la stretta di mano di libei — %d bracci, 3 scene l'uno" % len(bracci))
    dimmi("   attesa nella finestra: %d ms · pristino da: %s"
          % (attesa, pristino_file or ("git " + rif)))
    for quale in ("/lib/x86_64-linux-gnu/libei.so.1", "/lib/x86_64-linux-gnu/libeis.so.1"):
        if os.path.exists(quale):
            fatto = subprocess.run(["md5sum", os.path.realpath(quale)],
                                   capture_output=True, text=True)
            dimmi("   %s" % fatto.stdout.strip())
    dimmi()

    sani = 0
    storti = 0
    with tempfile.TemporaryDirectory(prefix="10-d4-") as dove:
        if porta:
            os.makedirs(porta, exist_ok=True)
        for braccio in bracci:
            if gia:
                binario = os.path.join(gia, "10-d4-" + braccio)
                if not os.path.exists(binario):
                    dimmi("⛔ %-18s il binario gia' compilato non c'e': %s" % (braccio, binario))
                    storti += 1
                    continue
            else:
                sorgente, sbaglio = prepara(dove, braccio, rif, pristino_file)
                if sorgente is None:
                    dimmi("⛔ %-18s NON PREPARATO: %s" % (braccio, sbaglio))
                    dimmi("   ⇒ non giudico questo braccio.")
                    storti += 1
                    continue
                binario, sbaglio = compila(porta or dove, sorgente, braccio)
                if binario is None:
                    dimmi("⛔ %-18s NON COMPILA: %s" % (braccio, sbaglio))
                    storti += 1
                    continue
                if porta:
                    dimmi("⭐ %-18s compilato: %s" % (braccio, binario))
                    continue

            esiti = {}
            for scena in ("immaturo", "maturo", "caduta-immatura"):
                try:
                    esiti[scena] = gira(binario, scena, attesa)
                except subprocess.TimeoutExpired:
                    esiti[scena] = None
            verdetto, righe = giudica(braccio, esiti, attesa)
            marca = "⭐" if verdetto == "come atteso" else "⛔"
            dimmi("%s %-18s %s" % (marca, braccio, verdetto))
            for r in righe:
                dimmi(r)
            if verdetto == "come atteso":
                sani += 1
            else:
                storti += 1
                for scena, e in esiti.items():
                    if e is None:
                        continue
                    if e["riga"]:
                        dimmi("     %s" % e["riga"])
                    coda = [
                        x
                        for x in e["registro"].splitlines()
                        if "input" in x and ("ABBANDON" in x or "staccato" in x or "stretta" in x)
                    ]
                    for x in coda[-3:]:
                        dimmi("     %s" % x)
            dimmi()

    dimmi("── bracci come attesi %d, storti %d" % (sani, storti))
    return 0 if storti == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
