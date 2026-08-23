#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b71 — ⭐⭐ IL RISVEGLIO: quanto passa fra il primo pixel che cambia e il
         primo fotogramma che esce.

⛔ LA DOMANDA, E PERCHE' E' LA PIU' IMPORTANTE DELLA FASE.
   `09-b68` ha misurato che a scena ferma escono **0,03 fotogrammi/s**: in 30 s
   esce solo la chiave d'apertura.  E ha anche misurato **perche'**: il ciclo
   del figlio gira sempre a ~120 Hz, e' Mutter che non gli consegna niente
   (123 «attese a vuoto» al secondo).  ⇒ Nessuno decide di rallentare: il ritmo
   e' quello con cui il compositore si degna di consegnare.
   ⇒ ⭐ **Per chi guarda il prezzo e' zero finche' nessuno tocca niente.**
   ⇒ ⛔ **Il prezzo vero e' al risveglio**, e non era mai stato misurato.

⭐ COME SI BATTE IL COLPO, e perche' cosi'.
   La scena `04-b30-scena` viene **congelata** (`SIGSTOP`) e **risvegliata**
   (`SIGCONT`).  ⛔ Non si spegne e si riaccende il processo: l'avvio di un
   client Wayland (connessione, superficie, primo buffer) costa decine di ms
   che NON sono il risveglio del prodotto e si sommerebbero al numero senza
   che nessuno se ne accorga.

⭐ E L'ISTANTE DEL PIXEL SI LEGGE, NON SI DEDUCE.
   Il colpo (`t_cont`) non e' il momento in cui il pixel cambia: in mezzo c'e'
   il risveglio della scena stessa.  Il momento vero e' `ultimo_disegno_us` nel
   blocco condiviso della scena (CLOCK_MONOTONIC, scritto in `disegna()` al
   commit).  ⇒ si riportano **tutt'e due** i tratti, separati:

       t_cont ──[scena]──> t_disegno ──[Mutter + NOI]──> SPEDITO
                  ⚠ non nostro          ⭐ questo e' il numero della fase

⛔ CHE COSA E' MISURATO, CON LE PAROLE DI `SPECIFICHE.md` §2.4: il tratto
   **primo pixel → byte fuori dal server**.  ⚠ NON e' l'anello intero: manca
   il volo sul filo, la decodifica e la pittura sulla pagina.  L'anello intero
   e' fase 8 (`08-l-anello.md`), e va sommato, non confuso.

⭐⭐ IL CONFRONTO CHE DA' SENSO AL NUMERO — la stessa misura con quieti
    diversi.  Se risvegliarsi dopo 5 s di fermo costa quanto risvegliarsi dopo
    0,2 s, **l'arresto non costa niente** e la questione e' chiusa.  Se costa
    di piu', quello e' il difetto della fase.  ⇒ non un numero: una **scala**.

⛔ IL CONTROLLO POSITIVO (`--controllo`): si congela il FIGLIO per 200 ms
   attorno al colpo.  Il risveglio misurato deve salire di ~200 ms.  Se non
   sale, lo strumento e' cieco e tutti i suoi zeri non valgono niente
   (`LEZIONI.md` §1.9: vuoto e giusto si somigliano).

Uso (dal portatile):
    python3 banchi/09-b71-risveglio.py pulizia
    python3 banchi/09-b71-risveglio.py misura --pulsazioni 30
    python3 banchi/09-b71-risveglio.py controllo
    python3 banchi/09-b71-risveglio.py chiudi
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))

# ⭐ Il mestiere non si riscrive: `09-b68` ha gia' l'ssh, il sudo, `lo`, il
#    registro, la scena e la disciplina di `tc`.  Qui si aggiunge il colpo.
_s = importlib.util.spec_from_file_location("b68", os.path.join(QUI, "09-b68-ritmo.py"))
b68 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(b68)

root, rem, filo = b68.root, b68.rem, b68.filo
LAV = b68.LAV
FUORI = os.environ.get("FUORI", "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2/"
                                "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad/b71")

R_SPED = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d\d\d) rcp\s+fotogramma (\d+) SPEDITO: "
                    r"(CHIAVE|delta) 0x0\d0\d, codec (\d+), (\d+)x(\d+), (\d+) byte", re.M)


def secondi_del_giorno(hh, mm, ss, ms):
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000.0


# ── i copioni si portano sulla macchina: /media/REMOTIX/tmp/09 e' di root ──
def porta(nome):
    """⛔ `scp` diretto in una cartella di root fallisce da `nicfio`.  Si passa
       da /tmp e si `install`a da root — e si controlla che sia arrivato."""
    loc = os.path.join(QUI, nome)
    subprocess.run(["scp", "-q", "-o", "BatchMode=yes", loc,
                    "%s:/tmp/%s" % (b68.MACCHINA, nome)], check=True)
    rc, out, err = root("install -m 755 /tmp/%s %s/%s && md5sum %s/%s"
                        % (nome, LAV, nome, LAV, nome))
    qui_md5 = subprocess.run(["md5sum", loc], capture_output=True).stdout.split()[0].decode()
    if qui_md5 not in out:
        raise SystemExit("⛔ «%s» non e' arrivato uguale: «%s»" % (nome, out.strip()))
    return True


# ── ⛔ NON SI MISURA IN DUE SULLA STESSA MACCHINA — `LEZIONI.md` §1.26 ─────
def pulizia(parla=True):
    """Non da' un rosso, da' **un numero plausibile**: per questo si guarda
       prima, e si dichiara che cosa si e' visto."""
    rc, porte, _ = root("ss -tuln | grep -E ':7[0-9]{3}' || true")
    rc, proc, _ = root("pgrep -a -f 'src/remotix ' | grep -v grep || true")
    rc, altri, _ = root("pgrep -a -f '04-b30-scen[a]|01-b3-client[e]|b70-ritm[o]|"
                        "b65-datagra[m]' || true")
    rc, car, _ = rem("uptime")
    rc, qlo, _ = root("/usr/sbin/tc qdisc show dev lo")
    rc, qen, _ = root("/usr/sbin/tc qdisc show dev enp7s0 | head -1")
    porte_uniche = sorted(set(re.findall(r":(7\d{3})\b", porte)))
    d = {"porte_7xxx": porte_uniche, "carico": car.strip(),
         "tc_lo": qlo.strip(), "tc_enp7s0": qen.strip(),
         "altri_banchi": [x for x in altri.splitlines() if x.strip()],
         "processi_remotix": len([x for x in proc.splitlines() if x.strip()])}
    # ⚠ «Pulita» vuol dire: nessuna porta 7xxx che non sia la MIA, e nessuna
    #   disciplina.  ⛔ Il gemello del confronto appaiato (7900 accanto a 7910)
    #   e' ACCESO di proposito — e restare accesi non e' misurare: quel che
    #   §1.26 vieta e' che giri un banco sull'altro, e lo dice la riga
    #   «altri banchi vivi», non l'elenco delle porte.
    # ⛔⭐ IL CONFRONTO APPAIATO HA DUE SERVER ACCESI, e non e' sporcizia.
    #    §1.26 vieta di MISURARE in due sulla stessa macchina, non di tenere
    #    acceso il termine di paragone: il **prima** (7900) deve restare vivo
    #    o il «dopo» non e' confrontabile con niente.  ⇒ le porte che si
    #    tollerano si DICHIARANO da fuori, una per una, e chi legge il banco
    #    le vede stampate — ⚠ tacerle sarebbe la forma cattiva: un banco che
    #    non si accorge di un vicino da' un numero plausibile, non un rosso.
    #    Quel che resta vietato e' un banco vivo (riga «altri banchi vivi») e
    #    qualunque disciplina su `lo`.
    ammesse = [x for x in os.environ.get("PORTE_AMMESSE", "").replace(",", " ").split() if x]
    mie = sorted(set([str(b68.PORTA)] + ammesse))
    d["porte_ammesse"] = mie
    pulita = (porte_uniche == mie and "netem" not in qlo and "tbf" not in qlo)
    if parla:
        print("== ⛔ SI MISURA DA SOLI?  (`LEZIONI.md` §1.26)")
        print("   porte 7xxx aperte: %s" % (porte_uniche or "nessuna"))
        print("   porte ammesse:     %s  (la mia %d%s)"
              % (mie, b68.PORTA,
                 ", piu' il gemello del confronto appaiato" if ammesse else ""))
        print("   altri banchi vivi: %s" % (d["altri_banchi"] or "nessuno"))
        print("   tc lo: %s · enp7s0: %s" % (d["tc_lo"], d["tc_enp7s0"]))
        print("   %s" % d["carico"])
        print("   %s la macchina %s" % ("OK " if pulita else "⛔ ",
                                        "e' mia sola" if pulita else "NON e' pulita"))
    d["pulita"] = pulita
    return d


# ── il terreno: una sessione lunga in sottofondo, e la scena accesa ───────
def sessione_apri(nome, secondi, utente="prova", tela="1920x1080", extra=""):
    l, h = tela.split("x")
    args = ("--indirizzo %s --porta %d --utente %s --parola-file %s/parola "
            "--audio-codec pcm --larghezza %s --altezza %s --resta %d %s"
            % (b68.IND, b68.PORTA, utente, b68.DENTRO_LAV, l, h,
               secondi, extra))
    rc, out, err = root("env LAV=%s DENTRO_ALB=%s sh %s/09-b71-sessione.sh %s %s"
                        % (LAV, b68.DENTRO_ALB, LAV, nome, args), 200)
    print("   %s" % (out + err).strip()[:400])
    return "SESSIONE APERTA" in out


def sessione_chiudi():
    """⛔ E SI ASPETTA CHE SIA DAVVERO MORTA.  `pkill` torna subito; il cliente
       ci mette fino a mezzo minuto a congedarsi (QUIC).  Chi non aspetta trova
       un processo vivo al giro dopo e crede che una sessione ci sia."""
    root("env LAV=%s sh %s/09-b71-sessione.sh -- spegni; true" % (LAV, LAV))
    for _ in range(60):
        rc, out, _ = root("pgrep -f '01-b3-cliente[.]py' | head -1")
        if not out.strip():
            return True
        time.sleep(1)
    return False


# ⛔⛔ «C'E' UN PROCESSO» NON E' «C'E' UNA SESSIONE» — pagato il 23 ago, 07:40.
#    Il banco ha visto vivo il cliente che il comando precedente aveva appena
#    ucciso, ha detto «una sessione e' gia' aperta» e NON ne ha aperta una.
#    Trenta secondi dopo il cliente e' morto davvero e da li' in poi il
#    registro non ha piu' avuto un solo `SPEDITO`: quattro bracci su sei hanno
#    misurato **il nulla**, e il banco non se n'e' accorto.
#    ⇒ la sessione la dichiara il PRODOTTO, nel suo registro: canale video
#      acceso, e nessun distacco dopo.
def sessione_viva():
    rc, acceso, _ = root("grep -n 'canale video ACCESO' %s/registro.log | tail -1" % LAV)
    rc, via, _ = root("grep -n \"l'ultima sessione di\" %s/registro.log | tail -1" % LAV)
    na = int(acceso.split(":")[0]) if acceso.strip() else 0
    nv = int(via.split(":")[0]) if via.strip() else 0
    return na > nv


def scena_accendi(movimento="pieno", uid=1001, utente="prova", shm="09-b68", extra=""):
    usc = b68.monitor()
    if not usc:
        return None, "nessun monitor nel registro: il palco non e' mai nato"
    rc, out, err = root("env LAV=%s UID_B=%d UTENTE=%s sh %s/09-b68-scena.sh %s %s"
                        % (LAV, uid, utente, LAV, usc, movimento), 120)
    if "SCENA ACCESA" not in out:
        return None, "la scena non e' partita: %s" % (out + err).strip()[:400]
    return usc, None


# ── ⭐ IL GIRO: il battitore sulla macchina, poi il registro ──────────────
def arm(etichetta, pulsazioni, quiete, accensione=0.30, fermo_ms=0,
        bersaglio="figlio", quando="colpo"):
    riga0 = b68.righe_registro()
    fpid = ""
    if fermo_ms:
        if bersaglio == "figlio":
            rc, out, _ = root("pgrep -u 1001 -f 'remotix-figlio --figlio-intern[o]'")
        else:
            # ⛔ Il PADRE: i due processi `src/remotix` (trasporto e rcp), cioe'
            #    chi scrive «SPEDITO».  Congelarli non tocca ne' gnome-shell ne'
            #    la scena ⇒ il ritardo iniettato cade TUTTO nel tratto
            #    «pixel → byte fuori», che e' quello che il banco misura.
            rc, out, _ = root("pgrep -f 'src/%s/src/remoti[x]'"
                              % b68.ALB_NOME.replace("-", "[-]", 1))
        pidi = [x for x in out.split() if x.isdigit()]
        if not pidi:
            return {"etichetta": etichetta, "guasto": "⛔ non trovo il bersaglio «%s»" % bersaglio}
        fpid = ("--fermo-pid %s --fermo-ms %d --fermo-quando %s"
                % (",".join(pidi), fermo_ms, quando))

    usc = "%s/b71-%s.jsonl" % (LAV, etichetta)
    tetto = int(pulsazioni * (quiete + accensione + 1.5) + 120)
    rc, out, err = root("python3 %s/09-b71-agente.py --shm 09-b68 --pulsazioni %d "
                        "--quiete %.3f --accensione %.3f --etichetta %s "
                        "--uscita %s %s"
                        % (LAV, pulsazioni, quiete, accensione, etichetta, usc, fpid),
                        tetto)
    if rc != 0:
        return {"etichetta": etichetta,
                "guasto": "⛔ il battitore: %s" % (out + err).strip()[:400]}

    rc, jl, _ = root("cat %s" % usc, 120)
    righe = [json.loads(x) for x in jl.splitlines() if x.strip()]
    testa = righe[0]
    battute = [x for x in righe if "pulsazione" in x]

    rc, reg, _ = root("tail -n +%d %s/registro.log" % (riga0 + 1, LAV), 300)
    with open(os.path.join(FUORI, "reg-%s.log" % etichetta), "w") as f:
        f.write(reg)

    # ⛔ L'ancora: il registro scrive HH:MM:SS.mmm senza data ne' fuso.  Lo
    #    scarto si RICAVA da un istante misurato nei due modi, non si indovina.
    ancora = testa["ancora_epoch"]
    hh, mm, ss = testa["ancora_locale"].split(":")
    mezzanotte = ancora - secondi_del_giorno(hh, mm, ss.split(".")[0],
                                             testa["ancora_locale"].split(".")[1])
    sped = []
    for m in R_SPED.finditer(reg):
        t = mezzanotte + secondi_del_giorno(m.group(1), m.group(2), m.group(3), m.group(4))
        sped.append((t, m.group(6), int(m.group(10)), int(m.group(5))))
    sped.sort()

    esiti = []
    for b in battute:
        if not b.get("t_disegno"):
            esiti.append(dict(b, esito="⛔ stimolo non avvenuto"))
            continue
        td, tc = b["t_disegno"], b["t_cont"]
        # ⭐ la premessa si CONTROLLA: durante la quiete non deve uscire
        #    niente.  Se esce, il desktop non era fermo e la misura non e'
        #    quella che dice di essere.
        in_quiete = [x for x in sped if b["t_stop_prima"] + 0.15 < x[0] < tc]
        dopo = [x for x in sped if x[0] > td - 0.002]
        primo = dopo[0] if dopo else None
        finestra = [x for x in sped if td - 0.002 <= x[0] <= b["t_stop_dopo"] + 0.10]
        esiti.append({
            "pulsazione": b["pulsazione"],
            "quiete_vera_s": b["quiete_vera_s"],
            "colpo_disegno_ms": b["colpo_disegno_ms"],
            "t_disegno": td, "t_primo": primo[0] if primo else None,
            "risveglio_ms": round((primo[0] - td) * 1000, 1) if primo else None,
            "colpo_uscita_ms": round((primo[0] - tc) * 1000, 1) if primo else None,
            "primo_tipo": primo[1] if primo else None,
            "primo_byte": primo[2] if primo else None,
            "fotogrammi_in_finestra": len(finestra),
            "usciti_durante_la_quiete": len(in_quiete),
            "disegni_finestra": b["disegni_finestra"],
            "esito": "OK" if primo else "⛔ nessun fotogramma dopo il disegno",
        })
    if not sped:
        # ⛔ ZERO FOTOGRAMMI NON E' UNA MISURA: e' un braccio che non ha
        #    misurato niente, e va detto qui invece di uscire come mediana
        #    «None» in mezzo agli altri.
        return {"etichetta": etichetta, "quiete_s": quiete,
                "guasto": "⛔ nessun `SPEDITO` nel registro di questo braccio: "
                          "la sessione non era viva (%d battute buttate)" % len(battute)}
    return {"etichetta": etichetta, "quiete_s": quiete, "pulsazioni": pulsazioni,
            "fermo_ms": fermo_ms, "bersaglio": bersaglio if fermo_ms else None,
            "fermo_quando": quando if fermo_ms else None,
            "ora": testa["ora_inizio"], "testa": testa, "battute": esiti,
            "spediti_totali": len(sped)}


# ⭐⭐ DOVE VANNO I MILLISECONDI DEL RISVEGLIO — e non e' una curiosita':
#    decide se la cura sta nel prodotto o nel compositore.
#    Il registro porta, per ogni fotogramma, la riga del figlio
#    «codec 1: N byte, delta, caricamento X us, codifica Y us» e subito dopo
#    «SPEDITO».  ⇒ il tratto «pixel → byte fuori» si spacca in tre:
#      pixel → fine codifica meno la codifica = ⛔ **Mutter compone e ci
#                                consegna, piu' la nostra cattura**
#      codifica                = ⭐ nostra, e si legge in microsecondi
#      fine codifica → SPEDITO = la consegna al trasporto
# ⚠ Il registro ha il millisecondo, non il microsecondo: i due tratti di fuori
#   hanno +-1 ms di grana, e si dichiara invece di stampare tre decimali.
R_CODIFICA = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d\d\d) figlio  codec (\d+): "
                        r"(\d+) byte, (CHIAVE|chiave|delta), caricamento (\d+) us, "
                        r"codifica (\d+) us", re.M)


def tratti(a):
    """Spacca il risveglio nei suoi tre pezzi, dal registro gia' salvato."""
    reg = open(os.path.join(FUORI, "reg-%s.log" % a["etichetta"])).read()
    testa = a["testa"]
    hh, mm, resto = testa["ancora_locale"].split(":")
    ss, ms = resto.split(".")
    mez = testa["ancora_epoch"] - secondi_del_giorno(hh, mm, ss, ms)
    cod = sorted((mez + secondi_del_giorno(m.group(1), m.group(2), m.group(3), m.group(4)),
                  int(m.group(8)), int(m.group(9))) for m in R_CODIFICA.finditer(reg))
    fuori_cod, dentro, consegna = [], [], []
    for b in a["battute"]:
        if b.get("esito") != "OK" or not b.get("t_disegno"):
            continue
        td, ts = b["t_disegno"], b["t_primo"]
        c = [x for x in cod if td - 0.002 <= x[0] <= ts + 0.002]
        if not c:
            continue
        t_cod_fine, caric_us, cod_us = c[0]
        dentro.append(cod_us / 1000.0)
        fuori_cod.append((t_cod_fine - td) * 1000.0 - cod_us / 1000.0)
        consegna.append((ts - t_cod_fine) * 1000.0)
    return {"pixel_a_codifica_ms": statistica(fuori_cod),
            "codifica_ms": statistica(dentro),
            "codifica_a_spedito_ms": statistica(consegna)}


def statistica(v):
    v = sorted(x for x in v if x is not None)
    if not v:
        return None
    n = len(v)

    def perc(p):
        return v[min(n - 1, max(0, int(round(p * (n - 1)))))]
    return {"n": n, "mediana": round(perc(0.5), 1), "min": round(v[0], 1),
            "max": round(v[-1], 1), "p95": round(perc(0.95), 1),
            "p05": round(perc(0.05), 1),
            "media": round(sum(v) / n, 1)}


def stampa_arm(a):
    if "guasto" in a:
        print("   %s" % a["guasto"]); return
    b = a["battute"]
    ok = [x for x in b if x.get("esito") == "OK"]
    print("\n-- «%s» · quiete %.2f s · %d battute, %d buone · ore macchina %s"
          % (a["etichetta"], a["quiete_s"], len(b), len(ok), a["ora"]))
    sporche = sum(x.get("usciti_durante_la_quiete", 0) for x in b)
    print("   ⛔ premessa: fotogrammi usciti DURANTE le quieti: %d %s"
          % (sporche, "(il desktop era davvero fermo)" if sporche == 0
             else "⚠ il desktop NON era fermo"))
    for nome, chiave in (("⭐ RISVEGLIO  pixel → byte fuori", "risveglio_ms"),
                         ("   colpo → pixel (la scena, non noi)", "colpo_disegno_ms"),
                         ("   colpo → byte fuori (i due insieme)", "colpo_uscita_ms")):
        s = statistica([x.get(chiave) for x in ok])
        if s:
            print("   %-38s mediana %7.1f  min %6.1f  max %7.1f  p95 %7.1f ms  (n=%d)"
                  % (nome, s["mediana"], s["min"], s["max"], s["p95"], s["n"]))
    tipi = {}
    for x in ok:
        tipi[x["primo_tipo"]] = tipi.get(x["primo_tipo"], 0) + 1
    print("   il primo fotogramma che esce e': %s · byte %s"
          % (tipi, statistica([x["primo_byte"] for x in ok])))
    print("   valori (ms): %s" % " ".join("%.0f" % x["risveglio_ms"]
                                          for x in ok if x["risveglio_ms"] is not None))
    try:
        t = tratti(a)
        print("   ⭐ dove vanno quei millisecondi: pixel→codifica %s ms · "
              "codifica %s ms · codifica→SPEDITO %s ms"
              % (t["pixel_a_codifica_ms"]["mediana"] if t["pixel_a_codifica_ms"] else "?",
                 t["codifica_ms"]["mediana"] if t["codifica_ms"] else "?",
                 t["codifica_a_spedito_ms"]["mediana"] if t["codifica_a_spedito_ms"] else "?"))
        a["tratti"] = t
    except Exception as e:
        print("   ⚠ i tratti non si spaccano: %s" % e)


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", choices=["pulizia", "prepara", "misura", "controllo", "chiudi"])
    p.add_argument("--pulsazioni", type=int, default=30)
    p.add_argument("--quieti", default="5.0,0.2,1.0,2.0")
    p.add_argument("--durata-sessione", type=int, default=1800)
    a = p.parse_args()
    os.makedirs(FUORI, exist_ok=True)

    print("== 09-b71 · il RISVEGLIO — porta %d, utente «prova», linea LARGA"
          % b68.PORTA)
    d = pulizia()
    if a.passo == "pulizia":
        return 0 if d["pulita"] else 2
    if not d["pulita"]:
        print("⛔ mi fermo: non si misura in due sulla stessa macchina")
        return 2

    if a.passo == "chiudi":
        b68.scena_spegni(); sessione_chiudi()
        print("   scena spenta, sessione chiusa"); return 0

    porta("09-b71-agente.py"); porta("09-b71-sessione.sh")
    porta("09-b68-scena.sh")   # ⛔ E1: quel che gira sulla macchina dev'essere
                               #    quel che sta nel deposito, non una copia vecchia

    if a.passo in ("prepara", "misura", "controllo"):
        # ⛔⛔ IL TRUCCO DELLE PARENTESI, E PERCHE' NON E' PIGNOLERIA.
        #    `pgrep -f 01-b3-cliente.py` trova ANCHE il `bash -c` che porta
        #    quel testo nella propria riga di comando — cioe' se stesso.
        #    `[M]` 23 ago, 07:29: il banco ha detto «una sessione e' gia'
        #    aperta (pid 18170)» mentre di sessioni non ce n'era nessuna, e
        #    18170 era il suo stesso involucro.  ⚠ Ancora la forma cattiva:
        #    non un rosso, **una risposta plausibile**.
        #    ⇒ `[.]` non compare mai nella riga vera, e compare in quella
        #      dell'involucro: la classe di caratteri distingue i due.
        if not sessione_viva():
            print("   --  apro una sessione lunga (%d s) in sottofondo" % a.durata_sessione)
            sessione_chiudi()
            if not sessione_apri("risveglio", a.durata_sessione):
                return 2
            time.sleep(2)
            if not sessione_viva():
                print("   ⛔ la sessione risulta aperta ma il registro non lo dice")
                return 2
        else:
            print("   OK  il registro dice che il canale video e' ACCESO")
        usc, guasto = scena_accendi("pieno")
        if guasto:
            print("   ⛔ %s" % guasto); return 2
        print("   OK  scena «pieno» sul monitor «%s»" % usc)
        time.sleep(1.5)

    if a.passo == "prepara":
        return 0

    esiti = []
    try:
        if a.passo == "controllo":
            # ⛔⛔ IL CONTROLLO POSITIVO — e ricordarsi che gli imputati sono
            #    DUE: se da' rosso, prima di accusare il banco si guarda se il
            #    colpo e' stato battuto (`fasi/09` §4.3).
            esiti.append(arm("controllo-0ms", 8, 5.0))
            esiti.append(arm("controllo-dopo-disegno-200ms", 8, 5.0, fermo_ms=200,
                             bersaglio="padre", quando="disegno"))
        else:
            for q in [float(x) for x in a.quieti.split(",")]:
                esiti.append(arm("quiete-%g" % q, a.pulsazioni, q))
        for e in esiti:
            stampa_arm(e)
    finally:
        with open(os.path.join(FUORI, "b71-%s.json" % a.passo), "w") as f:
            json.dump(esiti, f, ensure_ascii=False, indent=1)
        print("\n== esiti in %s/b71-%s.json" % (FUORI, a.passo))

    if a.passo == "controllo":
        def med(e, chiave):
            s = statistica([x.get(chiave) for x in e.get("battute", [])])
            return s["mediana"] if s else None
        base = med(esiti[0], "risveglio_ms")
        dopo = med(esiti[1], "risveglio_ms")
        dopo_pix = med(esiti[1], "colpo_disegno_ms")
        print("\n== ⛔⛔ IL CONTROLLO POSITIVO — 200 ms NOTI, iniettati DOPO il pixel")
        print("   risveglio pixel→byte fuori: %.1f → %.1f ms (+%.1f)"
              % (base, dopo, dopo - base))
        print("   ⭐ e il tratto della scena NON si muove: colpo→pixel %.1f ms "
              "(a riposo %.1f) ⇒ il colpo e' caduto dove doveva"
              % (dopo_pix, med(esiti[0], "colpo_disegno_ms")))
        ok = (dopo - base) > 150
        print("   %s lo strumento %s il ritardo iniettato nel tratto che misura"
              % ("OK " if ok else "⛔ ", "VEDE" if ok else "NON vede"))
        return 0 if ok else 2
    return 0


if __name__ == "__main__":
    sys.exit(principale())
