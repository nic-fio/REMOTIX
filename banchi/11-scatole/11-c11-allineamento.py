#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c11 — ⭐⭐ «LE SCATOLE SONO ALLINEATE» — la maglia che guarda LA RETE
===========================================================================

    python3 11-c11-allineamento.py
    python3 11-c11-allineamento.py --certifica

⛔ Questa maglia **non prova il prodotto**: prova che i confronti fra desktop
   valgano qualcosa.  ⭐ Ed e' il guasto che l'utente ha nominato per PRIMO,
   con parole sue:

       *«affinche' i numeri siano coerenti e' necessario tenere allineati i
         container.  Se sul container gnome abbiamo remotix v1 e sul container
         kde remotix v1.2 andiamo a sbattere.»*

   ⇒ `fasi/11…` D5, e la maglia C11 di §4.2.

---------------------------------------------------------------------------
⛔⛔ E SI GUARDA QUEL CHE C'E' DENTRO, NON QUEL CHE C'E' SCRITTO NELLA RICETTA
---------------------------------------------------------------------------

La prima idea era confrontare le **ricette**.  ⛔ Non regge: le ricette sono
diverse **apposta** (ogni scatola ha il suo desktop), e un confronto che deve
prima «togliere le parti diverse» diventa un confronto su cui si discute.

⭐ Quel che conta davvero non e' che le ricette si somiglino: e' che le
  **scatole accese** siano d'accordo su tutto quel che NON e' il desktop.
  ⇒ Si chiede a ciascuna che versione ha di ogni pezzo dichiarato, e si guarda
    se rispondono la stessa cosa.  «Scritto non e' in vigore» (E1) applicato
    all'ambiente: ⛔ una ricetta ricostruita ieri e una di un mese fa possono
    avere lo stesso testo e pacchetti diversi.

---------------------------------------------------------------------------
⭐ CHE COSA DEV'ESSERE UGUALE, e perche' ciascuno
---------------------------------------------------------------------------

  la base            `debian:13` ⇒ una distribuzione diversa fa numeri diversi
  mesa / libva       ⛔ il CODIFICATORE.  Due mesa diversi e i millisecondi
                     non si confrontano piu'
  pipewire           il percorso della cattura
  ffmpeg / libav*    quel che decodifica quando si giudica un'immagine
  firefox-esr        ⛔ il bersaglio di C8: due Firefox diversi, due difetti
                     diversi
  libc / libssl      il fondo di tutto
  ⭐ IL PRODOTTO      md5 del binario: ⛔ **e' la ragione per cui esiste questa
                     maglia**.  Un binario diverso per scatola e ogni confronto
                     fra desktop e' aria fritta

⛔ E QUEL CHE **NON** DEV'ESSERE UGUALE, dichiarato: il **desktop**.  Ogni
   scatola ha il suo, ed e' il punto.  ⇒ Il pacchetto del desktop lo dice
   l'ADATTATORE, e questa maglia lo stampa senza confrontarlo.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ le scatole accese sono allineate
  1  ⛔ almeno un pezzo ha versioni diverse fra le scatole ⇒ rosso
  3  ⛔ non ho potuto guardare (podman non c'e', nessuna scatola accesa,
     una scatola non risponde) — ⛔ e NON e' un rosso
  2  il terreno non regge, o l'uso e' sbagliato
===========================================================================
"""
import argparse
import subprocess
import sys

# ⛔ L'elenco e' DICHIARATO qui e stampato in ogni esito: «allineate» e' un
#    verdetto, e un verdetto senza il suo metro e' un'opinione.
DEVE_COMBACIARE = [
    ("la base", "base"),
    ("mesa-va-drivers", "pacchetto"),
    ("va-driver-all", "pacchetto"),
    ("libva2", "pacchetto"),
    # ⚠ I nomi portano il `t64` e NON e' un dettaglio: in Debian 13 i pacchetti
    #   toccati dalla transizione del tempo a 64 bit si chiamano cosi'.  ⛔ La
    #   prima stesura chiedeva `libssl3` e `libpipewire-0.3-0`, che NON esistono
    #   ⇒ rispondeva «?» per tutti, e ⛔ «?» uguale per tutti PASSA il confronto.
    #   Cioe' tre voci su tredici non stavano guardando niente.
    ("libpipewire-0.3-0t64", "pacchetto"),
    # ⭐ Aggiunta il 26 ago 2026 con C5: `pw-play`/`pw-cli` stanno in
    #   `pipewire-bin`, ed e' da li' che C5 tira fuori il suono.  ⛔ Senza questa
    #   voce due scatole potevano avere strumenti audio diversi e C11 taceva.
    ("pipewire-bin", "pacchetto"),
    ("libavcodec61", "pacchetto"),
    ("ffmpeg", "pacchetto"),
    ("firefox-esr", "pacchetto"),
    ("libc6", "pacchetto"),
    ("libssl3t64", "pacchetto"),
    ("libei1", "pacchetto"),
    ("libpci3", "pacchetto"),
    ("il prodotto (md5)", "prodotto"),
]

DESKTOP = ("gnome", "kde", "xfce", "lxqt")


def dentro(scatola, comando):
    """⛔ Niente `sh -c` annidati: `LEZIONI.md` §1.46 — un comando che perde le
       virgolette non esegue niente e restituisce 0."""
    p = subprocess.run(["podman", "exec", scatola, "/bin/sh", "-c", comando],
                       capture_output=True, text=True, timeout=90)
    if p.returncode != 0:
        return None
    return p.stdout.strip()


def raccogli(scatola):
    """Torna il dizionario di quella scatola, o ⛔ `None` se non risponde."""
    vivo = subprocess.run(["podman", "inspect", "-f", "{{.State.Running}}", scatola],
                          capture_output=True, text=True)
    if vivo.returncode != 0 or vivo.stdout.strip() != "true":
        return None
    d = {}
    d["la base"] = dentro(scatola, "cat /etc/debian_version")
    for nome, che in DEVE_COMBACIARE:
        if che != "pacchetto":
            continue
        d[nome] = dentro(scatola, "dpkg-query -W -f='${Version}' %s 2>/dev/null "
                                  "|| echo '(non c e)'" % nome)
    d["il prodotto (md5)"] = dentro(
        scatola, "md5sum /opt/remotix/remotix 2>/dev/null | cut -c1-12 "
                 "|| echo '(non ancora dentro)'")
    # ⚠ Il desktop si STAMPA e non si confronta: e' l unica cosa che DEVE
    #   essere diversa.  E lo dice l adattatore, non questo file.
    pacco = dentro(scatola, ". /usr/local/lib/rete11/adattatore.sh 2>/dev/null "
                            "&& adattatore_pacchetto")
    d["_desktop"] = "%s %s" % (pacco or "?", dentro(
        scatola, "dpkg-query -W -f='${Version}' %s 2>/dev/null || echo ?"
                 % (pacco or "x")) or "?")
    return d


def giudica(tavola):
    """Dato {scatola: {voce: valore}}, dice quali voci NON combaciano.

    ⛔ Torna `None` se non c'e' abbastanza per giudicare: **una scatola sola
       non e' un allineamento**, e dirlo verde sarebbe la bugia piu' comoda di
       tutta questa maglia.
    """
    presenti = {n: d for n, d in tavola.items() if d}
    if len(presenti) < 2:
        return None
    guai = []
    for nome, _che in DEVE_COMBACIARE:
        valori = {}
        for scatola, d in presenti.items():
            v = d.get(nome)
            valori.setdefault(v, []).append(scatola)
        # ⚠ Una voce che NESSUNO ha (per esempio il prodotto non ancora messo
        #   dentro) e' uguale per tutti: non e' un disallineamento.
        if len(valori) > 1:
            guai.append((nome, valori))
    return guai


def certifica():
    """⛔ Si dimostra che il giudice SA dare rosso — e che sa dire «non lo so»."""
    casi = [
        ("due scatole d'accordo su tutto",
         {"a": {n: "1" for n, _ in DEVE_COMBACIARE},
          "b": {n: "1" for n, _ in DEVE_COMBACIARE}}, 0),
        ("⭐ il PRODOTTO diverso — il guasto che l'utente ha nominato per primo",
         {"a": dict({n: "1" for n, _ in DEVE_COMBACIARE},
                    **{"il prodotto (md5)": "aaaa"}),
          "b": dict({n: "1" for n, _ in DEVE_COMBACIARE},
                    **{"il prodotto (md5)": "bbbb"})}, 1),
        ("mesa diverso: i millisecondi non si confrontano piu'",
         {"a": dict({n: "1" for n, _ in DEVE_COMBACIARE},
                    **{"mesa-va-drivers": "25.0.7"}),
          "b": dict({n: "1" for n, _ in DEVE_COMBACIARE},
                    **{"mesa-va-drivers": "25.1.0"})}, 1),
        ("⛔ una scatola sola NON e' un allineamento",
         {"a": {n: "1" for n, _ in DEVE_COMBACIARE}, "b": None}, None),
        ("⛔ nessuna scatola accesa",
         {"a": None, "b": None}, None),
        ("una voce che manca a TUTTI non e' un disallineamento",
         {"a": dict({n: "1" for n, _ in DEVE_COMBACIARE},
                    **{"il prodotto (md5)": "(non ancora dentro)"}),
          "b": dict({n: "1" for n, _ in DEVE_COMBACIARE},
                    **{"il prodotto (md5)": "(non ancora dentro)"})}, 0),
    ]
    print("== certificazione del giudice di C11 ==")
    guai = 0
    for nome, tavola, atteso in casi:
        r = giudica(tavola)
        ottenuto = None if r is None else len(r)
        ok = ottenuto == atteso
        print("  %s  %-58s  disallineamenti=%s (atteso %s)"
              % ("OK " if ok else "NO ", nome,
                 "non lo so" if ottenuto is None else ottenuto,
                 "non lo so" if atteso is None else atteso))
        if not ok:
            guai += 1
    print()
    if guai:
        print("⛔ il giudice NON e' affidabile: %d casi sbagliati" % guai)
        return 1
    print("⭐ il giudice vede il disallineamento, e ⛔ non chiama «allineate» due")
    print("   scatole di cui una non c'e'")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--desktop", default=",".join(DESKTOP))
    p.add_argument("--prefisso", default="rete11-")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    # ⚠ `command` e' un builtin della shell, non un programma: cercarlo con
    #   `subprocess` da' `FileNotFoundError`.  Si chiede a podman se c e'.
    try:
        subprocess.run(["podman", "--version"], capture_output=True, timeout=30)
    except OSError:
        print("⛔ podman non c'e': ⇒ non ho potuto guardare")
        sys.exit(3)

    nomi = [a.prefisso + d for d in a.desktop.split(",") if d]
    tavola = {n: raccogli(n) for n in nomi}

    print("== C11 — le scatole sono allineate? ==")
    print("   ⛔ si guarda quel che c'e' DENTRO le scatole accese, non quel che")
    print("      c'e' scritto nelle ricette\n")
    accese = [n for n, d in tavola.items() if d]
    for n in nomi:
        d = tavola[n]
        print("   %-14s %s" % (n, ("desktop: %s" % d["_desktop"]) if d
                               else "⛔ spenta o non risponde"))
    print()

    # ⛔⛔ E PRIMA DI GIUDICARE: una voce a cui NESSUNA scatola sa rispondere
    #    e' uguale per tutti, quindi **passa** — e non ha guardato niente.
    #    `[M]` 26 agosto 2026: tre voci su tredici erano cosi (nomi sbagliati),
    #    e il verde su di loro non valeva niente.  ⇒ Si dichiara.
    mute = [nome for nome, _ in DEVE_COMBACIARE
            if all((tavola[n] or {}).get(nome) in (None, "", "?")
                   for n in nomi if tavola[n])]
    r = giudica(tavola)
    if r is None:
        print("⛔ scatole accese: %d — ⭐ e UNA SOLA non e' un allineamento."
              % len(accese))
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)

    # ⭐ La tabella si stampa SEMPRE, verde o rosso: e' quel che va confrontato
    #   fra le quattro scatole, e chi legge deve poterla vedere.
    largh = max(len(n) for n, _ in DEVE_COMBACIARE)
    print("   %-*s  %s" % (largh, "voce", "  ".join("%-16s" % n for n in accese)))
    for nome, _che in DEVE_COMBACIARE:
        valori = [tavola[n].get(nome) or "?" for n in accese]
        segno = "  " if len(set(valori)) == 1 else "⛔"
        print(" %s %-*s  %s" % (segno, largh, nome,
                                "  ".join("%-16s" % v[:16] for v in valori)))
    print()
    if mute:
        print("⚠ ⛔ %d voci a cui NESSUNA scatola sa rispondere — e una voce muta"
              % len(mute))
        print("   PASSA il confronto senza aver guardato niente:")
        for nome in mute:
            print("     · %s" % nome)
        print("   ⇒ vanno corrette, o questa maglia si racconta storie.\n")
    if r:
        print("⛔⛔ ROSSO — %d voci NON combaciano fra le scatole:" % len(r))
        for nome, valori in r:
            print("   · %s" % nome)
            for v, chi in valori.items():
                print("       %-16s  %s" % (v, ", ".join(chi)))
        print()
        print("   ⇒ finche' e' cosi', ⛔ **i confronti fra desktop non valgono**:")
        print("     un numero peggiore direbbe «e' il desktop» quando invece e'")
        print("     un'altra versione di qualcos'altro (D5).")
        return 1
    print("⭐ le %d scatole accese sono allineate su tutte le %d voci dichiarate"
          % (len(accese), len(DEVE_COMBACIARE)))
    print("⚠ e il DESKTOP e' diverso in ognuna, come dev'essere: e' il punto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
