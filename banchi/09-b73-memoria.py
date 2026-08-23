#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b73 — ⛔⭐⭐ LA CURA DELLA MEMORIA, e la sola forma che la dimostra: **due
         binari appaiati**.

═══ LA DOMANDA ══════════════════════════════════════════════════════════════
Il 23 agosto 2026 alle 08:28:09 il server e' morto di `SEGV` in
`__memmove_avx_unaligned_erms` su un delta da 525 298 byte.  La causa, letta
riga per riga in `fasi/09-il-crollo.md` §4: `wt_scrivi()` liberava i byte di un
fotogramma appena ngtcp2 li aveva **serializzati**, mentre il contratto obbliga
a tenerli **fino all'ack**.  ⇒ ritrasmissione = `memcpy` da memoria liberata.

⛔ La cura e' applicata (`coda_consegna()`), **e non e' mai stata provata**.

═══ ⛔⛔ IL CONTROLLO CHE DECIDE, e senza il quale la prova non vale niente ══
«Il curato non e' morto» **non e' un risultato**: ha la stessa faccia di uno
stimolo che non stimola.  ⇒ si misura su DUE binari, con lo stesso identico
giro:

  · il **MALATO** — `/media/REMOTIX/src/09c-mal-src`, che e' l'albero curato con
    UNA sola riga rimessa com'era (`coda_uccidi()` al posto di
    `coda_consegna()`, `webtransport.c:5946`).  ⛔ **DEVE MORIRE.**  Se non
    muore, la ricetta non riproduce niente e la prova non ha dimostrato nulla:
    gli imputati diventano **due**, lo strumento e lo stimolo;
  · il **CURATO** — `/media/REMOTIX/src/09c-src`.  Deve reggere lo stesso
    stimolo, e alla chiusura il residuo di byte trattenuti dev'essere **zero**.

═══ ⭐ LO STIMOLO — perche' proprio questo ═══════════════════════════════════
`fasi/09-il-crollo.md` §4.3-4.4: il difetto e' **silenzioso** sotto la soglia
di `mmap` di glibc, e quella soglia e' **dinamica** — dopo il primo blocco
grosso liberato si alza, e il difetto torna muto.  ⇒ in 1 h 50 min di sessione
il 23 agosto c'e' stato **1 solo** blocco `mmap` su 45 005.

⭐ `MALLOC_MMAP_THRESHOLD_=32768` **dall'ambiente** spegne l'adattamento
   (`mp_.no_dyn_threshold = 1`): da li' in poi OGNI fotogramma sopra i 32 KiB
   e' `mmap`/`munmap` e il difetto e' fatale **sempre**.  Lo arma
   `09-riavvia-7920.sh`, e lo VERIFICA nell'ambiente del processo vivo.

Poi servono (a) fotogrammi grossi e (b) perdita:
  (a) il film **con la grana** a schermo intero, 2560x1080 — `[M]` 58,67 Mbit/s;
  (b) `netem loss` sulla porta 7920 di `lo`, col guardiano staccato.

═══ ⭐ LA GRANDEZZA CHE DICE SE LA CURA TIENE O PERDE MEMORIA ════════════════
`byte_in_volo_max` (`webtransport.c:567`, scritta alla chiusura): e' la PUNTA
dei byte trattenuti in attesa d'ack.  ⛔ Se **oscilla**, la cura tiene; se
**cresce per tutta la sessione**, sta trattenendo e non libera mai.
⚠ Sul malato vale sempre 0 per costruzione — non e' un risultato, e' l'assenza
  del meccanismo.

Uso (dal portatile, con l'ambiente della 7920):
    python3 banchi/09-b73-memoria.py malato   --secondi 90 --perdita 5%
    python3 banchi/09-b73-memoria.py curato   --secondi 90 --perdita 5%
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("b68", os.path.join(QUI, "09-b68-ritmo.py"))
b68 = importlib.util.module_from_spec(_s); _s.loader.exec_module(b68)
_s2 = importlib.util.spec_from_file_location("b71", os.path.join(QUI, "09-b71-risveglio.py"))
b71 = importlib.util.module_from_spec(_s2); _s2.loader.exec_module(b71)
_s3 = importlib.util.spec_from_file_location("b72", os.path.join(QUI, "09-b72-banda.py"))
b72 = importlib.util.module_from_spec(_s3); _s3.loader.exec_module(b72)

root, rem = b68.root, b68.rem
LAV = b68.LAV
UNITA = os.environ.get("UNITA", "remotix-7920")
ALB_CURATO = os.environ.get("ALB_CURATO", "/media/REMOTIX/src/09c-src")
ALB_MALATO = os.environ.get("ALB_MALATO", "/media/REMOTIX/src/09c-mal-src")
FILM = os.environ.get("FILM", "/media/REMOTIX/tmp/09c/film-grana.webm")
FUORI = os.environ.get("FUORI", "/tmp/09-b73")
os.makedirs(FUORI, exist_ok=True)


def ora():
    return root("date '+%H:%M:%S'")[1].strip()


def pid_server():
    rc, out, _ = root("systemctl show -p MainPID --value %s.service" % UNITA)
    p = out.strip()
    return int(p) if p.isdigit() else 0


def vivo(p):
    return p and root("kill -0 %d 2>/dev/null && echo SI || echo NO" % p)[1].strip() == "SI"


def accendi(albero, extra=""):
    rc, out, err = root("env ALBERO=%s sh %s/09-riavvia-7920.sh %s" % (albero, LAV, extra), 300)
    print((out + err).rstrip())
    return "fuori da ogni sessione utente" in out


def spegni():
    root("systemctl stop %s.service 2>/dev/null; systemctl reset-failed %s.service 2>/dev/null; true"
         % (UNITA, UNITA))


def giro(quale, secondi, perdita, tela, utente, uid):
    albero = ALB_MALATO if quale == "malato" else ALB_CURATO
    d = {"quale": quale, "albero": albero, "perdita": perdita, "tela": tela,
         "secondi": secondi}

    print("\n== ⛔ SI MISURA DA SOLI?")
    d["pulizia"] = b71.pulizia()

    print("\n== il server «%s»" % quale)
    spegni()
    # ⛔ Il registro si azzera fra i due bracci: due giri nello stesso file e i
    #    conti del primo entrano nel secondo (`09-b68` §righe_registro).
    root("rm -f %s/registro.log %s/core.* ; true" % (LAV, LAV))
    if not accendi(albero):
        return dict(d, guasto="il server non e' partito")
    p0 = pid_server()
    d["pid"] = p0
    d["ora_accensione"] = ora()

    print("\n== il terreno: sessione «%s» a %s" % (utente, tela))
    if not b72.terreno(utente, tela, 3600, uid):
        return dict(d, guasto="la sessione non si e' aperta")

    print("\n== la scena: il film CON LA GRANA a schermo intero")
    b72.esci_dalla_vista(uid)
    rc, out, err = root("env LAV=%s UID_B=%d UTENTE=%s FILM=%s sh %s/09-b72-video.sh accendi"
                        % (LAV, uid, utente, FILM, LAV), 240)
    if "VIDEO ACCESO" not in out:
        return dict(d, guasto="il video non e' partito: %s" % (out + err)[:400])
    time.sleep(5)

    riga0 = b68.righe_registro()
    # ⭐ quanto e' grosso quel che passa PRIMA di stringere: se i fotogrammi non
    #   sono grossi, lo stimolo non e' quello che credo di applicare.
    time.sleep(6)
    rc, reg, _ = root("tail -n +%d %s/registro.log" % (riga0 + 1, LAV), 300)
    tg = [int(x[5]) for x in b68.R_SPED.findall(reg)]
    d["taglie_prima"] = {"n": len(tg), "max": max(tg) if tg else 0,
                         "mediana": sorted(tg)[len(tg) // 2] if tg else 0,
                         "sopra_32k": sum(1 for x in tg if x > 32768)}
    print("   fotogrammi in 6 s: %d, mediana %d byte, massimo %d, sopra 32 KiB: %d"
          % (d["taglie_prima"]["n"], d["taglie_prima"]["mediana"],
             d["taglie_prima"]["max"], d["taglie_prima"]["sopra_32k"]))

    print("\n== ⛔ LA PERDITA: netem loss %s sulla 7920 di `lo`, guardiano armato" % perdita)
    b68.guardiano_arma(secondi + 120)
    ok, q = b68.stringi(["loss", perdita])
    d["qdisc"] = q
    if not ok:
        b68.rimetti()
        return dict(d, guasto=q)
    print("   %s" % q.replace("\n", " | ")[:300])
    d["ora_perdita"] = ora()

    # ── l'attesa: si guarda se muore, e QUANDO ────────────────────────────
    t0 = time.time()
    morto_a = None
    while time.time() - t0 < secondi:
        if not vivo(p0):
            morto_a = round(time.time() - t0, 1)
            break
        time.sleep(2)
    d["morto"] = morto_a is not None
    d["morto_dopo_s"] = morto_a
    d["ora_fine"] = ora()

    print("\n== " + ("⛔ IL SERVER E' MORTO dopo %.1f s" % morto_a if morto_a
                     else "il server e' VIVO dopo %d s" % secondi))

    b68.rimetti()

    # ── che cosa dice la macchina della morte ─────────────────────────────
    rc, st, _ = root("systemctl show -p Result -p ExecMainStatus -p ExecMainCode "
                     "--value %s.service | tr '\\n' ' '" % UNITA)
    d["esito_unita"] = st.strip()
    rc, dm, _ = root("dmesg -T | tail -25")
    d["dmesg"] = [x for x in dm.splitlines() if "remotix" in x or "segfault" in x]
    rc, core, _ = root("ls -la %s/core.* 2>/dev/null || true" % LAV)
    d["core"] = core.strip()

    rc, reg, _ = root("tail -n +%d %s/registro.log" % (riga0 + 1, LAV), 300)
    with open(os.path.join(FUORI, "reg-%s.log" % quale), "w") as f:
        f.write(reg)
    d["righe_registro"] = len(reg.splitlines())
    sped = b68.R_SPED.findall(reg)
    d["spediti"] = len(sped)
    d["byte_max"] = max([int(x[5]) for x in sped], default=0)

    # ── ⭐ il residuo: `byte_in_volo_max` alla chiusura ────────────────────
    if not morto_a:
        print("\n== la chiusura pulita, per leggere il residuo")
        b71.sessione_chiudi()
        time.sleep(3)
    rc, resid, _ = root("grep -a 'byte TENUTI' %s/registro.log | tail -8" % LAV)
    d["righe_tenuti"] = resid.strip()
    print("   %s" % (resid.strip() or "(nessuna riga «byte TENUTI»)"))

    b72.spegni_tutto(uid)
    b71.sessione_chiudi()
    with open(os.path.join(FUORI, "esito-%s.json" % quale), "w") as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    return d


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", choices=["malato", "curato"])
    p.add_argument("--secondi", type=int, default=90)
    p.add_argument("--perdita", default="5%")
    p.add_argument("--tela", default="2560x1080")
    p.add_argument("--utente", default="prova2")
    p.add_argument("--uid", type=int, default=1002)
    a = p.parse_args()
    d = giro(a.passo, a.secondi, a.perdita, a.tela, a.utente, a.uid)
    print("\n" + json.dumps({k: v for k, v in d.items() if k != "pulizia"},
                            indent=1, ensure_ascii=False))


if __name__ == "__main__":
    principale()
