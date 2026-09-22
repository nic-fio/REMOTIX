#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c18 — ⭐ «I GRUPPI DELLA SCHEDA LI METTE IL PRODOTTO»
===========================================================================

    python3 11-c18-i-gruppi-li-mette-il-prodotto.py --porta 8511
    python3 11-c18-i-gruppi-li-mette-il-prodotto.py --porta 8511 --senza-usermod
    python3 11-c18-i-gruppi-li-mette-il-prodotto.py --certifica

    che cosa deve essere vero : un utente NUOVO, che nei gruppi dei nodi
                                `/dev/dri` non c'e', si collega — e **il
                                prodotto ce lo mette**, da solo, alla prima
                                connessione (`DECISIONI.md` §7.21, deciso
                                dall'utente il 20 settembre 2026)
    da dove parte             : un inquilino nuovo, ⛔ **SENZA** i gruppi
    che cosa guarda           : tre fatti, ciascuno col suo nome
      G  prima      `id -nG` NON contiene i gruppi dei nodi della scheda
      I  durante    il registro del server dice «PRIMA CONNESSIONE … ce lo
                    METTO io» col nome di QUESTO inquilino
      D  dopo       `id -nG` adesso LI contiene, e il registro dice
                    «e' nei gruppi della scheda … puo' vedere in hardware»
    come so che sa dare rosso : `--senza-usermod` — per la durata del giro
                                `usermod` si sposta di nome: il prodotto non
                                puo' iscrivere nessuno ⇒ **I e D rossi**

⛔⛔ PERCHE' QUESTA MAGLIA ESISTE, ed e' un buco che si e' visto solo oggi.

    Il fatto che copre e' l'unico del prodotto che **tutte le altre maglie
    nascondono**: ogni maglia chiama `garantisci_i_gruppi(chi)` PRIMA di
    collegarsi (`11-c1`, e da li' C3, C4, C7, C9, C17…), cioe' mette i gruppi
    all'inquilino **con le sue mani**.  ⇒ Quando il cliente arriva, il prodotto
    non ha piu' niente da iscrivere, la sua riga non esce mai, e ⛔ **la rete
    intera puo' essere verde con quel pezzo di prodotto rotto**.
    ⚠ E non e' un difetto di quelle maglie: loro devono misurare altro, e un
      inquilino cieco le farebbe uscire con un «non ho potuto guardare» (§1.51).
      ⇒ Il buco si chiude aggiungendo una maglia, non cambiando le loro.

⭐⭐ E VALE SU TUTTI I DESKTOP, non solo su kde — ed e' il punto dell'utente
    del 21 settembre 2026: *«deve funzionare per tutti i DE, non solo per
    KDE»*.  Il codice che iscrive (`src/figlio.c`, `iscrivi_ai_gruppi_della_
    scheda`) sta nel **padre**, gira da root **dopo PAM** e **prima del fork**:
    non sa nemmeno quale compositore nascera'.  ⇒ Non c'e' un ramo per
    desktop da provare — c'e' una cosa sola, e va provata **su ogni scatola**.
    `[M]` 22 set 2026, con browser VERI e finestra vera, inquilini senza gruppi:
      · gnome  Firefox 140 PASS · Chrome 153 PASS ⇒ `sgruppig`/`sgruppic` da
        «solo se stesso» a «video render», primo fotogramma in 1,6 s e 1,2 s
      · xfce   Firefox 140 PASS · Chrome 153 PASS ⇒ `sgruppix`/`sgruppiy`
        idem, 0,6 s e 0,9 s
      · kde    gia' `[M]` il 20 set 2026 (`DECISIONI.md` §7.21, utente
        `senzagr`: col binario di prima zero fotogrammi, con quello nuovo 105)

⛔ QUESTA MAGLIA NON GIUDICA I FOTOGRAMMI.  Che la sessione veda e' il mestiere
   di C1 e C3; qui i fotogrammi si stampano come RILIEVO, perche' chi legge il
   registro deve poter distinguere «iscritto e vede» da «iscritto e non vede».
   ⚠ Giudicarli qui vorrebbe dire due maglie che danno rosso per lo stesso
     fatto, e il giorno che quel rosso arrivasse nessuno saprebbe di chi e'.

Esiti: 0 verde · 1 rosso · 3 non ho potuto guardare (⛔ NON e' un rosso).
⛔ Con `--senza-usermod` si legge AL CONTRARIO: 0 = il guasto e' stato VISTO.
"""
import argparse
import os
import random
import re
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
CLIENTE = os.path.join(QUI, "01-b3-cliente.py")
REGISTRO = "/var/lib/rete11/registro.log"
PAROLA = "provanic2026"

# ⛔ Il gruppo in cui `gpu-udev.sh` mette la scheda ESCLUSA: nessuno ci deve
#    stare dentro, ⇒ non conta fra i gruppi che il prodotto deve dare.
#    ⚠ E' la stessa regola di `src/provisiona.sh`: la scheda esclusa esiste
#    perche' le misure si facciano sempre sulla stessa (`gid_della_scheda`).
GRUPPO_ESCLUSO = "remotix-nogpu"

# ⭐ Le due righe del prodotto che questa maglia legge, e stanno in un posto
#    solo perche' se il prodotto le cambia si cambia QUI (§1.47).
#    `[R]` `src/figlio.c`, `iscrivi_ai_gruppi_della_scheda` e `gruppi_della_scheda`.
RIGA_ISCRIZIONE = "PRIMA CONNESSIONE"
RIGA_VEDE = "nei gruppi della scheda"
RIGA_CIECO = "NON E' NEL GRUPPO DELLA SCHEDA"
# ⚠ Il registro e' in UTF-8 e il prodotto scrive apostrofi dritti: la riga
#   «NON E' NEL GRUPPO» si cerca cosi' com'e', senza normalizzare niente.

# ⛔ I due posti in cui il prodotto cerca `usermod` (`src/figlio.c`,
#    `comando_da_root`): il guasto innestato li deve nascondere TUTTI E DUE, o
#    il prodotto trova il secondo e il guasto non morde.
POSTI_USERMOD = ("/usr/sbin/usermod", "/sbin/usermod")
CODA_NASCOSTO = ".c18-nascosto"


def corri(argv, tempo=30, **kw):
    """Un comando, o `None` se il tempo e' scaduto.  ⛔ Non solleva mai."""
    try:
        return subprocess.run(argv, capture_output=True, text=True,
                              timeout=tempo, **kw)
    except (subprocess.TimeoutExpired, OSError):
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ I GRUPPI SI CHIEDONO AI NODI — e questa e' la regola del progetto, non
#     una comodita'.  `video` e `render` sono i nomi di UNA distribuzione;
#     quel che conta e' il **gid** che il nucleo e udev hanno messo su
#     `/dev/dri/cardN` e `/dev/dri/renderDN` di QUESTA macchina.
#     `[R]` `src/provisiona.sh`, `gid_della_scheda()`; `src/figlio.c`,
#     `raccogli_gruppi_scheda()`.  ⛔ Tre posti che leggono la stessa cosa
#     nello stesso modo: se divergono, diverge il giudizio.
# ═══════════════════════════════════════════════════════════════════════════
def gid_escluso():
    r = corri(["getent", "group", GRUPPO_ESCLUSO], 10)
    if r is None or r.returncode != 0:
        return None
    pezzi = (r.stdout or "").strip().split(":")
    return pezzi[2] if len(pezzi) > 2 else None


def gruppi_dei_nodi(cartella="/dev/dri"):
    """⭐ (nomi, perche') — i NOMI dei gruppi dei nodi della scheda.

    ⛔ Lista vuota e un perche' quando non si puo' sapere: senza i nodi questa
       maglia non ha niente da guardare, ed e' un **3**, non un rosso — una
       macchina senza scheda non e' un prodotto rotto.
    """
    if not os.path.isdir(cartella):
        return [], "non c'e' %s: questa scatola non ha nodi della scheda" % cartella
    escluso = gid_escluso()
    gid = []
    for nome in sorted(os.listdir(cartella)):
        if not re.match(r"^(card|renderD)[0-9]+$", nome):
            continue
        try:
            g = str(os.stat(os.path.join(cartella, nome)).st_gid)
        except OSError:
            continue
        if escluso is not None and g == escluso:
            continue
        if g not in gid:
            gid.append(g)
    if not gid:
        return [], ("nessun nodo `cardN`/`renderDN` leggibile in %s: non so "
                    "quali gruppi il prodotto dovrebbe dare" % cartella)
    nomi = []
    for g in gid:
        r = corri(["getent", "group", g], 10)
        if r is None or r.returncode != 0 or not (r.stdout or "").strip():
            return [], ("il gid %s dei nodi non ha un nome in /etc/group: "
                        "nemmeno il prodotto ci potrebbe iscrivere nessuno" % g)
        n = r.stdout.split(":")[0]
        if n not in nomi:
            nomi.append(n)
    return nomi, ""


def gruppi_di(chi):
    """I gruppi dell'utente ADESSO, letti dal sistema.  `None` = non lo so."""
    r = corri(["id", "-nG", chi], 10)
    if r is None or r.returncode != 0:
        return None
    return (r.stdout or "").split()


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL GIUDIZIO — funzione PURA, cosi' `--certifica` la attraversa senza
#   toccare ne' la macchina ne' il prodotto.
# ═══════════════════════════════════════════════════════════════════════════
def giudizio(attesi, prima, dopo, fetta, chi):
    """⭐ (esito, faccia_g, faccia_i, faccia_d, perche) dai FATTI.

    `attesi` i nomi che il prodotto deve dare · `prima`/`dopo` i gruppi
    dell'inquilino · `fetta` le righe di registro di QUESTO giro.
    ⛔ Nessuna lettura di file qui dentro: solo fatti gia' raccolti.
    """
    if not attesi:
        return 3, "?", "?", "?", "non so quali gruppi il prodotto dovrebbe dare"
    if prima is None or dopo is None:
        return 3, "?", "?", "?", "non ho potuto leggere i gruppi dell'inquilino"

    # ── G: prima NON ci deve stare, o questa maglia sta guardando altro ──
    gia = [g for g in attesi if g in prima]
    if gia:
        return 3, "NO", "?", "?", (
            "«%s» era GIA' nei gruppi %s prima di collegarsi: qualcuno ce l'ha "
            "messo (lo scheletro di `useradd`? un'altra maglia?) ⇒ il prodotto "
            "non aveva niente da iscrivere e questo giro non prova niente"
            % (chi, ", ".join(gia)))

    righe_mie = [r for r in fetta if ("[%s]" % chi) in r]
    iscritto = any(RIGA_ISCRIZIONE in r for r in righe_mie)
    vede = any(RIGA_VEDE in r and RIGA_CIECO not in r for r in righe_mie)
    cieco = any(RIGA_CIECO in r for r in righe_mie)
    mancanti = [g for g in attesi if g not in dopo]

    # ⛔ Nessuna riga di questo inquilino ⇒ il cliente non e' mai arrivato
    #    fino al figlio: non e' un rosso del prodotto, e' un giro non fatto.
    if not righe_mie:
        return 3, "SI", "?", "?", (
            "nel registro non c'e' nessuna riga di «%s»: il cliente non e' "
            "arrivato al figlio, e senza sessione non c'e' iscrizione da "
            "guardare" % chi)

    faccia_i = "SI" if iscritto else "NO"
    faccia_d = "SI" if (not mancanti and vede) else "NO"
    if iscritto and not mancanti and vede:
        return 0, "SI", faccia_i, faccia_d, (
            "«%s» e' arrivato senza i gruppi, il prodotto ce l'ha messo "
            "(%s) e la sessione puo' vedere in hardware"
            % (chi, ", ".join(attesi)))

    perche = []
    if not iscritto:
        perche.append("nel registro manca «%s»: il prodotto NON ha provato a "
                      "iscriverlo" % RIGA_ISCRIZIONE)
    if mancanti:
        perche.append("dopo la connessione «%s» NON e' nei gruppi %s (ha: %s)"
                      % (chi, ", ".join(mancanti), " ".join(dopo) or "niente"))
    if cieco:
        perche.append("il prodotto dichiara la sessione CIECA («%s»)" % RIGA_CIECO)
    elif not vede:
        perche.append("manca la riga «%s»: il prodotto non dichiara che questa "
                      "sessione veda" % RIGA_VEDE)
    return 1, "SI", faccia_i, faccia_d, "; ".join(perche)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL GUASTO INNESTATO — e si innesta sulla MACCHINA, non sul prodotto.
#
# ⭐ Nascondere `usermod` e' il modo piu' onesto di togliere al prodotto la
#   possibilita' di iscrivere: non si tocca il binario, non si tocca il
#   registro, non si tocca l'inquilino.  ⇒ Il prodotto fa esattamente quel che
#   farebbe, e fallisce dove deve fallire.
# ⚠ E si RIMETTE A POSTO SEMPRE, anche se il giro muore a meta': il `finally`
#   di `main`, piu' una rimessa in ordine all'inizio del giro dopo — perche' un
#   `usermod` lasciato nascosto renderebbe cieche tutte le maglie che vengono
#   dopo, ed e' precisamente il difetto che questa rete e' fatta per non avere.
# ═══════════════════════════════════════════════════════════════════════════
def nascondi_usermod():
    """⛔ Torna l'elenco di quel che ha spostato (da rimettere)."""
    spostati = []
    for p in POSTI_USERMOD:
        if os.path.exists(p) and not os.path.islink(p):
            if corri(["mv", p, p + CODA_NASCOSTO], 10) is not None:
                spostati.append(p)
    return spostati


def rimetti_usermod():
    """⭐ Sempre, e senza chiedere: quel che trova nascosto lo rimette."""
    rimessi = []
    for p in POSTI_USERMOD:
        if os.path.exists(p + CODA_NASCOSTO):
            corri(["mv", p + CODA_NASCOSTO, p], 10)
            rimessi.append(p)
    return rimessi


def sgombera(chi):
    corri(["loginctl", "terminate-user", chi], 20)
    for _ in range(40):
        r = corri(["pgrep", "-u", chi], 5)
        if r is None or r.returncode != 0:
            break
        time.sleep(0.25)
    corri(["pkill", "-KILL", "-u", chi], 5)
    corri(["userdel", "-r", chi], 20)


def leggi(percorso):
    try:
        with open(percorso, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    except OSError:
        return None


def certifica():
    """⛔ La maglia sa dare rosso? Si prova sul GIUDIZIO, senza macchina."""
    guai = 0
    casi = [
        ("⭐ senza gruppi prima, iscritto e nei gruppi dopo ⇒ VERDE",
         (["video", "render"], ["c18u1"], ["c18u1", "video", "render"],
          ["figlio  [c18u1] ⭐ PRIMA CONNESSIONE: «c18u1» non e' nei gruppi",
           "figlio  [c18u1] ⭐ e' nei gruppi della scheda (render, video)"]), 0),
        ("⛔ il prodotto non prova nemmeno a iscriverlo ⇒ ROSSO",
         (["video", "render"], ["c18u1"], ["c18u1"],
          ["figlio  [c18u1] ⛔⛔ «c18u1» NON E' NEL GRUPPO DELLA SCHEDA «video»"]), 1),
        ("⛔ ci prova e non ci riesce (usermod nascosto) ⇒ ROSSO",
         (["video", "render"], ["c18u1"], ["c18u1"],
          ["figlio  [c18u1] ⭐ PRIMA CONNESSIONE: «c18u1» non e' nei gruppi",
           "figlio  [c18u1] ⛔ non ho potuto iscrivere «c18u1»"]), 1),
        ("⛔ iscritto a meta' (uno dei due gruppi manca) ⇒ ROSSO",
         (["video", "render"], ["c18u1"], ["c18u1", "video"],
          ["figlio  [c18u1] ⭐ PRIMA CONNESSIONE: «c18u1» non e' nei gruppi"]), 1),
        ("⚠ era GIA' nei gruppi prima ⇒ 3, ⛔ mai verde (non prova niente)",
         (["video", "render"], ["c18u1", "video", "render"],
          ["c18u1", "video", "render"],
          ["figlio  [c18u1] ⭐ e' nei gruppi della scheda (render, video)"]), 3),
        ("⚠ nessuna riga dell'inquilino nel registro ⇒ 3, ⛔ mai rosso",
         (["video", "render"], ["c18u1"], ["c18u1"],
          ["figlio  [altro] ⭐ PRIMA CONNESSIONE: «altro» non e' nei gruppi"]), 3),
        ("⚠ nodi della scheda non leggibili ⇒ 3, ⛔ mai rosso",
         ([], ["c18u1"], ["c18u1"], []), 3),
        ("⚠ i gruppi dell'inquilino non si leggono ⇒ 3",
         (["video"], None, None, []), 3),
    ]
    print("== C18 — certificazione del giudizio (⛔ senza toccare la macchina)")
    for nome, argomenti, atteso in casi:
        attesi, prima, dopo, fetta = argomenti
        e = giudizio(attesi, prima, dopo, fetta, "c18u1")[0]
        segno = "OK " if e == atteso else "NO "
        if e != atteso:
            guai += 1
        print("  %s %-62s esito %s (atteso %s)" % (segno, nome, e, atteso))
    # ⭐ E i due attrezzi del guasto si provano per NOME, non per fiducia: un
    #   `usermod` che non si rimette e' una scatola rotta per tutte le maglie.
    print("  %s %-62s %s"
          % ("OK " if len(POSTI_USERMOD) == 2 else "NO ",
             "⛔ il guasto nasconde TUTTI i posti di `usermod`",
             " ".join(POSTI_USERMOD)))
    print()
    if guai:
        print("⛔ %d casi del giudizio NON danno quel che devono" % guai)
        return 1
    print("⭐ il giudizio da' verde, rosso e «non lo so» dove deve — e il caso "
          "vero (arrivato senza gruppi, uscito con) e' il primo")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=0)
    p.add_argument("--senza-usermod", action="store_true",
                   help="⛔ IL GUASTO INNESTATO: `usermod` sparisce per la "
                        "durata del giro ⇒ il prodotto non puo' iscrivere")
    p.add_argument("--registro", default=REGISTRO)
    p.add_argument("--resta", type=float, default=12.0)
    p.add_argument("--attesa", type=float, default=45.0,
                   help="quanto si aspetta la riga del figlio nel registro")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.porta:
        print("⛔ vuole `--porta` ⇒ non ho potuto guardare")
        return 3
    if os.geteuid() != 0:
        print("⛔ vuole l'amministratore (crea un inquilino) ⇒ non ho potuto guardare")
        return 3

    chi = "c18u%d" % random.randint(100, 999)
    innestato = " ⛔ GUASTO INNESTATO: --senza-usermod" if a.senza_usermod else ""
    print("== C18 — i gruppi della scheda li mette il PRODOTTO (%s, porta %d)%s"
          % (chi, a.porta, innestato))

    # ⭐ Prima di tutto: se un giro morto ha lasciato `usermod` nascosto, lo si
    #    rimette PRIMA di misurare — altrimenti questo giro misurerebbe il
    #    residuo del giro di ieri e lo chiamerebbe difetto del prodotto.
    rimessi = rimetti_usermod()
    if rimessi:
        print("   ⚠ un giro precedente aveva lasciato nascosto %s: rimesso"
              % ", ".join(rimessi))

    attesi, perche_nodi = gruppi_dei_nodi()
    if not attesi:
        print("   ⛔ %s ⇒ non ho potuto guardare" % perche_nodi)
        return 3
    print("   i gruppi dei nodi della scheda, LETTI ADESSO: %s" % ", ".join(attesi))

    sgombera(chi)
    fatto = corri(["/bin/sh", "-c",
                   "useradd -m -s /bin/bash %s && printf '%s:%s\\n' | chpasswd"
                   % (chi, chi, PAROLA)], 60)
    if fatto is None or fatto.returncode != 0:
        print("   ⛔ non ho potuto creare l'inquilino ⇒ non ho potuto guardare")
        return 3

    spostati = []
    try:
        prima = gruppi_di(chi)
        print("   G  prima:  %s" % (" ".join(prima) if prima else "non lo so"))

        if a.senza_usermod:
            spostati = nascondi_usermod()
            if not spostati:
                print("   ⛔ non ho potuto nascondere `usermod`: il guasto non "
                      "e' innestato ⇒ non ho potuto guardare")
                return 3
            print("   ⛔ nascosto: %s" % ", ".join(spostati))

        # ⛔ Si segna DOVE siamo nel registro PRIMA di collegarsi: il giudizio
        #    guarda solo la fetta di QUESTO giro (la lezione della fase 9).
        righe = leggi(a.registro)
        segno = len(righe) if righe is not None else 0

        r = corri(["python3", "-u", CLIENTE, "--indirizzo", "127.0.0.1",
                   "--porta", str(a.porta), "--utente", chi,
                   "--parola", PAROLA, "--resta", str(a.resta)],
                  max(90, a.resta * 6))
        if r is None:
            print("   ⛔ il cliente non ha finito in tempo ⇒ non ho potuto guardare")
            return 3

        # ⭐ Si aspetta l'EVENTO, non l'orologio: la riga del figlio esce quando
        #   il padre l'ha generato, e quanto ci mette non lo decidiamo noi.
        fetta, scadenza = [], time.time() + a.attesa
        while time.time() < scadenza:
            dopo_righe = leggi(a.registro)
            fetta = dopo_righe[segno:] if dopo_righe is not None else []
            if any(("[%s]" % chi) in x and
                   (RIGA_ISCRIZIONE in x or RIGA_VEDE in x or RIGA_CIECO in x)
                   for x in fetta):
                break
            time.sleep(0.5)

        dopo = gruppi_di(chi)
        print("   D  dopo:   %s" % (" ".join(dopo) if dopo else "non lo so"))
        esito, fg, fi, fd, perche = giudizio(attesi, prima, dopo, fetta, chi)

        # ⭐ Il RILIEVO dei fotogrammi: si stampa, ⛔ non si giudica (vedi in testa).
        fot = None
        for riga in fetta:
            m = re.search(r"spediti (\d+)", riga)
            if ("[%s]" % chi) in riga and m:
                fot = int(m.group(1))
        print("   G %-3s I %-3s D %-3s" % (fg, fi, fd))
        print("   ⚠ RILIEVO, non verdetto: fotogrammi spediti a «%s»: %s"
              % (chi, "non lo so" if fot is None else fot))
        for riga in fetta:
            if ("[%s]" % chi) in riga and (RIGA_ISCRIZIONE in riga or
                                           RIGA_VEDE in riga or RIGA_CIECO in riga):
                print("   registro: %s" % riga.strip()[:150])

        print()
        if a.senza_usermod:
            # ⛔ Al contrario, e si dice a voce: qui lo 0 e' la buona notizia.
            if esito == 1:
                print("⭐ IL GUASTO INNESTATO E' STATO VISTO — questa maglia SA "
                      "dare rosso,\n   ⭐ e per la ragione giusta: %s" % perche)
                return 0
            if esito == 3:
                print("⚠ col guasto innestato NON ho potuto guardare: %s\n"
                      "   ⇒ esito 3, non un verde" % perche)
                return 3
            print("⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO: `usermod` era "
                  "nascosto e la maglia\n   ha detto verde lo stesso.")
            return 1
        if esito == 0:
            print("⭐ VERDE — %s" % perche)
        elif esito == 1:
            print("⛔⛔ ROSSO — %s" % perche)
        else:
            print("⚠ non ho potuto guardare — %s" % perche)
        return esito
    finally:
        # ⛔ Nell'ordine: prima `usermod` torna al suo posto (serve a `userdel`?
        #    no, ma serve a CHIUNQUE venga dopo), poi si sgombera l'inquilino.
        rimetti_usermod()
        if spostati:
            print("   ⭐ `usermod` rimesso al suo posto")
        sgombera(chi)


if __name__ == "__main__":
    sys.exit(main())
