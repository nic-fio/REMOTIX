#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b71-agente — ⭐ IL BATTITORE DEL RISVEGLIO.  Gira SULLA MACCHINA, da root.

⛔ NON e' il banco: e' la meta' che deve stare vicino all'orologio.  Il banco
   (`09-b71-risveglio.py`) sta sul portatile e fa il resto; qui c'e' solo quel
   che NON si puo' fare da lontano:

     · battere il colpo (`SIGCONT` alla scena) e sapere **a che microsecondo**;
     · sorprendere il PRIMO disegno che ne nasce, leggendo `/dev/shm` a ~2 kHz.
       ⛔ Da ssh non si puo': il giro di rete e' 100 volte il numero cercato.

⭐ LO STIMOLO E' `SIGSTOP`/`SIGCONT`, e la ragione e' che NON aggiunge niente
   al conto: la scena non nasce (nessun avvio di processo, nessuna superficie
   nuova da negoziare col compositore), si limita a **riprendere a disegnare**.
   ⇒ fra «il primo pixel che cambia» e il colpo c'e' solo il risveglio di un
     processo che ha gia' tutto in mano.

⛔ E L'ISTANTE DEL PIXEL NON SI DEDUCE DAL COLPO: si legge nel blocco condiviso
   della scena (`ultimo_disegno_us`, CLOCK_MONOTONIC, scritto in `disegna()`
   riga 1367).  Il colpo e' `t_cont`; il pixel e' `t_disegno`; la differenza
   fra i due e' **della scena, non del prodotto**, e si riporta a parte.

⛔⛔ LA TRAPPOLA DEL SEQLOCK QUANDO SI CONGELA IL SUO SCRITTORE.
   `stato_pubblica()` fa seq++ / campi / seq++.  Un `SIGSTOP` puo' cadere in
   mezzo: `seq` resta DISPARI per tutta la quiete e i campi sono meta' nuovi e
   meta' vecchi — e' lo stesso «relitto» che `03-marca.py` descrive, solo che
   qui e' voluto.  ⇒ due cure:
     1. il campione di riposo si prende **a processo fermo**, senza pretendere
        `seq` pari (la memoria non cambia piu': e' ferma, non incoerente);
     2. ⛔ il primo disegno si accetta **solo se cade DOPO il colpo**.  Senza
        questa riga, la prima scrittura che la scena finisce dopo il `SIGCONT`
        (con dentro un istante di PRIMA della quiete) darebbe un risveglio
        negativo o assurdo — cioe' un numero plausibile e falso.

Uso (da root, sulla macchina):
    python3 09-b71-agente.py --shm 09-b68 --pulsazioni 30 --quiete 5.0 \
        --accensione 0.30 --uscita /media/REMOTIX/tmp/09/b71-fermo.jsonl
"""
import argparse, json, mmap, os, signal, struct, sys, time

# ⛔ Copiato alla lettera da `banchi/03-marca.py` (`FORMATO_STATO`), che e' il
#    lettore certificato.  `magia` e `versione` si controllano: un lettore
#    rimasto indietro deve prendersi un rifiuto, non numeri a caso.
FORMATO = "<4I Q 5Q 5Q 10I i 3I 64s 32s 64s 64s 4Q 4I"
TAGLIA = struct.calcsize(FORMATO)
MAGIA, VERSIONE = 0x524D5853, 2

I_SEQ, I_DISEGNI, I_COMMIT = 4, 5, 6
I_AVVIO_MONO, I_AVVIO_REALE, I_ULT_DISEGNO = 10, 11, 12
I_ULT_PRES, I_ULT_PRES_REALE = 13, 14
I_PID, I_PRES_DISP = 25, 26
I_CORSE, I_FIDATO = 34, 40


def campione(m, pretendi_pari=True, tentativi=400):
    """Un campione del blocco.  `pretendi_pari=False` serve a processo FERMO:
    la memoria non cambia piu', quindi e' stabile anche se `seq` e' dispari —
    ma i campi possono essere meta' nuovi e meta' vecchi, e chi legge lo sa."""
    for _ in range(tentativi):
        a = struct.unpack(FORMATO, m[:TAGLIA])
        if not pretendi_pari:
            return a, (a[I_SEQ] % 2 == 0)
        if a[I_SEQ] % 2 == 0:
            b = struct.unpack(FORMATO, m[:TAGLIA])
            if b[I_SEQ] == a[I_SEQ]:
                return a, True
        time.sleep(0.0002)
    return None, False


def reale_us(a, mono_us):
    """Da CLOCK_MONOTONIC a CLOCK_REALTIME con i due istanti d'avvio che la
    scena pubblica apposta.  ⚠ La deriva fra i due orologi su qualche minuto
    e' sotto il millisecondo: dichiarata, non ignorata."""
    return a[I_AVVIO_REALE] + (mono_us - a[I_AVVIO_MONO])


def vivo(pid):
    return pid > 0 and os.path.exists("/proc/%d" % pid)


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--shm", default="09-b68")
    p.add_argument("--pulsazioni", type=int, default=30)
    p.add_argument("--quiete", type=float, default=5.0)
    p.add_argument("--accensione", type=float, default=0.30)
    p.add_argument("--uscita", required=True)
    p.add_argument("--etichetta", default="fermo")
    # ⭐ IL CONTROLLO POSITIVO: si congela il FIGLIO (cattura + codifica) per
    #    N ms attorno al colpo.  Se il banco sa vedere, il risveglio deve
    #    salire di ~N ms.  Se non sale, lo strumento e' cieco e i suoi numeri
    #    di prima non valgono niente.
    # ⛔⛔ E IL BERSAGLIO DEL CONGELAMENTO NON E' OVVIO — misurato, non
    #    supposto.  Congelare il FIGLIO (cattura + codifica) ha spostato
    #    `colpo → pixel` da 0,5 a 191,5 ms: cioe' ⭐ **fermando il nostro
    #    consumatore si ferma il DISEGNO dell'applicazione** — Mutter da' il
    #    `wl_surface.frame` al ritmo di chi consuma il flusso del monitor
    #    virtuale.  ⇒ il figlio NON isola il tratto «pixel → byte fuori»:
    #      per isolarlo si congela il PADRE (trasporto), che non tocca ne'
    #      il compositore ne' la scena.
    # ⛔⛔⛔ E ANCHE IL PADRE FA LA STESSA COSA — misurato, 23 ago 07:35:
    #    congelando i due processi del server, `colpo → pixel` va a 192,0 ms.
    #    ⇒ la catena **rifluisce fino al DISEGNO dell'applicazione**: padre
    #      fermo ⇒ il figlio non consegna piu' ⇒ non consuma piu' ⇒ Mutter non
    #      da' piu' il `wl_surface.frame` ⇒ la scena non disegna.
    #    ⛔ Quindi congelare **al colpo** non isola mai il tratto misurato: lo
    #      stimolo si sposta insieme allo strumento.
    # ⭐ LA CURA: si congela **DOPO** che il pixel e' cambiato
    #    (`--fermo-quando disegno`).  Il disegno e' gia' avvenuto e datato; il
    #    congelamento cade dentro il tratto «pixel → byte fuori» e in nessun
    #    altro posto.  ⇒ il risveglio DEVE salire di ~N ms, e se non sale lo
    #    strumento e' cieco.
    p.add_argument("--fermo-pid", default="", help="pid da congelare, separati da virgola")
    p.add_argument("--fermo-ms", type=int, default=0)
    p.add_argument("--fermo-quando", default="colpo", choices=["colpo", "disegno"])
    a = p.parse_args()

    percorso = "/dev/shm/" + a.shm
    if not os.path.exists(percorso):
        print(json.dumps({"guasto": "⛔ «%s» non esiste: la scena non e' partita "
                                    "o ha un altro --shm" % percorso}))
        return 2
    f = open(percorso, "r+b")
    m = mmap.mmap(f.fileno(), 0)
    a0, _ = campione(m)
    if a0 is None:
        print(json.dumps({"guasto": "⛔ il blocco «%s» non si legge: relitto "
                                    "(seq dispari e fermo)" % percorso}))
        return 2
    if a0[0] != MAGIA or a0[1] != VERSIONE:
        print(json.dumps({"guasto": "⛔ magia/versione: %08x/%d, attesi %08x/%d"
                                    % (a0[0], a0[1], MAGIA, VERSIONE)}))
        return 2
    pid = a0[I_PID]
    if not vivo(pid):
        print(json.dumps({"guasto": "⛔ la scena (pid %d) non e' viva: il blocco "
                                    "e' un relitto di un giro finito" % pid}))
        return 2
    fermi = [int(x) for x in a.fermo_pid.split(",") if x.strip()]
    if a.fermo_ms and not all(vivo(x) for x in fermi):
        print(json.dumps({"guasto": "⛔ un bersaglio del congelamento non e' vivo: %s"
                                    % fermi}))
        return 2

    fuori = open(a.uscita, "w")
    intestazione = {
        "che": "intestazione", "shm": a.shm, "pid_scena": pid,
        "pulsazioni": a.pulsazioni, "quiete_s": a.quiete,
        "accensione_s": a.accensione, "etichetta": a.etichetta,
        "fermo_ms": a.fermo_ms, "fermo_pid": fermi, "fermo_quando": a.fermo_quando,
        "presentazione_disponibile": a0[I_PRES_DISP],
        "fidato": a0[I_FIDATO], "corse_a_vuoto": a0[I_CORSE],
        "t_inizio": time.time(),
        "ora_inizio": time.strftime("%H:%M:%S", time.localtime()),
    }
    # ⭐⭐ L'ANCORA FRA I DUE OROLOGI, e senza di lei il banco non puo' fare
    #    la sottrazione che gli interessa.  Il registro del prodotto scrive
    #    `HH:MM:SS.mmm` **senza data e senza fuso**; qui si misura lo stesso
    #    istante nei due modi, cosi' chi legge ricava lo scarto invece di
    #    indovinare il fuso della macchina.  ⛔ Se lo scarto fosse sbagliato i
    #    risvegli verrebbero negativi o di ore: si vede subito, non si insinua.
    _t = time.time()
    intestazione["ancora_epoch"] = _t
    intestazione["ancora_locale"] = (time.strftime("%H:%M:%S", time.localtime(_t))
                                     + ".%03d" % int((_t % 1) * 1000))
    fuori.write(json.dumps(intestazione, ensure_ascii=False) + "\n")
    fuori.flush()

    esiti = []
    for n in range(a.pulsazioni):
        # ── 1. si spegne, e si sta fermi ──────────────────────────────────
        os.kill(pid, signal.SIGSTOP)
        t_stop = time.time()
        time.sleep(a.quiete)
        if not vivo(pid):
            fuori.write(json.dumps({"pulsazione": n, "guasto": "la scena e' morta"}) + "\n")
            break
        # ⛔ campione a processo FERMO: `seq` puo' essere dispari e va bene.
        riposo, riposo_pari = campione(m, pretendi_pari=False, tentativi=1)
        d0, u0 = riposo[I_DISEGNI], riposo[I_ULT_DISEGNO]

        # ── 2. il colpo ───────────────────────────────────────────────────
        if a.fermo_ms and a.fermo_quando == "colpo":
            for x in fermi:
                os.kill(x, signal.SIGSTOP)
        t_cont = time.time()
        os.kill(pid, signal.SIGCONT)
        if a.fermo_ms and a.fermo_quando == "colpo":
            # ⛔ I bersagli restano fermi N ms DOPO il colpo: e' il ritardo
            #    NOTO che il banco deve ritrovare nel numero.  Se non lo
            #    ritrova, lo strumento e' cieco.
            fine = t_cont + a.fermo_ms / 1000.0
            while time.time() < fine:
                time.sleep(0.0005)
            for x in fermi:
                os.kill(x, signal.SIGCONT)

        # ── 3. si sorprende il PRIMO disegno che nasce dal colpo ──────────
        t_disegno_real, mono, letture, scartati_vecchi = None, None, 0, 0
        limite = t_cont + 3.0
        while time.time() < limite:
            b = struct.unpack(FORMATO, m[:TAGLIA])
            letture += 1
            if b[I_ULT_DISEGNO] != u0 and b[I_SEQ] % 2 == 0:
                r = reale_us(b, b[I_ULT_DISEGNO]) / 1e6
                # ⛔ la riga che salva la misura: un disegno di PRIMA della
                #    quiete, pubblicato solo adesso, non e' il risveglio.
                if r > t_cont:
                    # ⭐ IL CONTROLLO POSITIVO DEL TRATTO GIUSTO: il pixel e'
                    #    gia' cambiato ed e' gia' datato.  Da qui in poi tutto
                    #    quel che si aggiunge cade DENTRO «pixel → byte fuori».
                    if a.fermo_ms and a.fermo_quando == "disegno":
                        for x in fermi:
                            os.kill(x, signal.SIGSTOP)
                        fine = time.time() + a.fermo_ms / 1000.0
                        while time.time() < fine:
                            time.sleep(0.0005)
                        for x in fermi:
                            os.kill(x, signal.SIGCONT)
                    t_disegno_real, mono = r, b[I_ULT_DISEGNO]
                    d1 = b[I_DISEGNI]
                    break
                scartati_vecchi += 1
                u0 = b[I_ULT_DISEGNO]
            time.sleep(0.0004)

        # ── 4. si lascia disegnare un po', poi si rispegne ────────────────
        time.sleep(max(0.0, a.accensione - (time.time() - t_cont)))
        fin, _ = campione(m)
        os.kill(pid, signal.SIGSTOP)
        t_stop2 = time.time()

        r = {
            "pulsazione": n, "etichetta": a.etichetta,
            "t_stop_prima": t_stop, "t_cont": t_cont,
            "quiete_vera_s": round(t_cont - t_stop, 3),
            "t_disegno": t_disegno_real,
            "colpo_disegno_ms": (round((t_disegno_real - t_cont) * 1000, 3)
                                 if t_disegno_real else None),
            "disegni_riposo": d0,
            "disegni_dopo": fin[I_DISEGNI] if fin else None,
            "disegni_finestra": (fin[I_DISEGNI] - d0) if fin else None,
            "letture": letture, "scartati_vecchi": scartati_vecchi,
            "t_stop_dopo": t_stop2,
            "seq_riposo_pari": riposo_pari,
        }
        if t_disegno_real is None:
            r["guasto"] = ("⛔ nessun disegno nuovo entro 3 s dal SIGCONT: lo "
                           "STIMOLO non e' avvenuto (non e' una misura lenta)")
        fuori.write(json.dumps(r, ensure_ascii=False) + "\n")
        fuori.flush()
        esiti.append(r)

    # ⛔ La scena si lascia ACCESA: chi ha acceso spegne, e non e' questo.
    os.kill(pid, signal.SIGCONT)
    buoni = [x for x in esiti if x.get("t_disegno")]
    coda = {"che": "coda", "battute": len(esiti), "buone": len(buoni),
            "t_fine": time.time(),
            "ora_fine": time.strftime("%H:%M:%S", time.localtime())}
    fuori.write(json.dumps(coda, ensure_ascii=False) + "\n")
    fuori.close()
    print(json.dumps({"battute": len(esiti), "buone": len(buoni),
                      "uscita": a.uscita}, ensure_ascii=False))
    return 0 if buoni else 2


if __name__ == "__main__":
    sys.exit(principale())
