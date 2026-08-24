#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b83-durate — **IL RISCHIO E' COSTANTE?**  E se sì, «bistabile» è la parola
                sbagliata.

    porta 7971 · sonda 7979… · utente `provanr8` (uid 1071)
    albero `/media/REMOTIX/src/09nr8-src` · lavoro `/media/REMOTIX/tmp/09nr8`
    unita' `remotix-7971` · ⛔ stesso binario **56c62bb0…** della campagna a 25 s

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ DA DOVE NASCE — UNA PAROLA CHE POTREBBE ESSERE SBAGLIATA
═══════════════════════════════════════════════════════════════════════════════

`[M]` 24 ago 2026, `09-b83-biforcazione.py`, **20 giri da 25 s** a `perdita-0,20`
sul binario `56c62bb02ff16019ae1b2537cf92251e`:

  · **13 giri su 20** hanno acceso la spirale (65 %);
  · le chiavi sono **zero-o-molte** (0 in 7 giri, ≥ 5 in 13, **nessuna** fra 1 e
    4) ⇒ i due rami ci sono davvero;
  · ⛔ **43 prove su 43 negative**: NIENTE nei primi 10 s distingue un ramo
    dall'altro;
  · ⭐ e si e' capito **perche'**: gli istanti d'accensione sono sparsi su tutto
    il giro — **3,1 · 3,2 · 4,3 · 4,5 · 5,3 · 8,0 · 8,8 · 9,5 · 10,5 · 11,4 ·
    18,4 · 18,6 · 24,9 s** — e **cinque su tredici cadono DOPO i dieci secondi**.
    In quei giri, nella finestra guardata, la spirale non era ancora partita.

⇒ `[?]` Da li' nasce un'ipotesi che **cambia la parola**: non due rami, ma
  **un'accensione A SENSO UNICO**, dove ogni secondo ha la sua probabilita' di
  accendersi, una volta accesa non si spegne, e i 25 secondi erano soltanto una
  moneta lanciata su **quanto a lungo si e' guardato**.

  Rischio costante stimato: **λ = 0,0529 /s** (13 accensioni su **245,6 s** di
  esposizione a regime) ⇒ tempo medio d'attesa **18,9 s**.

⛔⛔ **E QUESTO BANCO ESISTE PER PROVARE A SMENTIRLA**, non per confermarla.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ CHE COSA LA REFUTA — SCRITTO PRIMA DI GIRARE
═══════════════════════════════════════════════════════════════════════════════

⭐ La predizione, presa dal λ misurato a 25 s e **non ritoccata**:

    | durata | esposizione a regime | frazione attesa di giri andati male |
    |--------|----------------------|--------------------------------------|
    | 10 s   | 7 s                  | 1 − e^(−0,0529·7)  = **31 %**        |
    | 25 s   | 22 s                 | 1 − e^(−0,0529·22) = **69 %**  `[M]` 65 % |
    | 50 s   | 47 s                 | 1 − e^(−0,0529·47) = **92 %**        |

⛔⛔ **MA IL PUNTO NON E' UN PUNTO: E' UNA BANDA**, e chi lo dimentica rifiuta
    il modello sul rumore della sua stessa taratura.  `λ` e' stato stimato su
    **13 accensioni**: l'errore standard di `log λ` vale `1/√13 = 0,277`, quindi
    a due sigma `λ ∈ [0,031 · 0,091]`, e la predizione diventa:

        a 10 s: **19 % – 47 %**        a 50 s: **76 % – 99 %**

    ⇒ Una singola percentuale fuori dal punto **non** refuta niente.  Percio' il
      giudizio non e' un confronto con due numeri: e' la domanda giusta, che e'
      **«esiste UN SOLO λ che spiega tutte e tre le durate?»**.

── **T1 · il conto leggibile a 10 s** — binomiale esatto contro il 31 %.
── **T2 · il conto leggibile a 50 s** — binomiale esatto contro il 92 %.
   ⚠ T1 e T2 sono **le due percentuali che si leggono**, non il verdetto:
     provano un punto, non il modello.

── **T3 · ⭐⭐ IL VERDETTO — un solo λ, o uno per durata?**
   Rapporto di verosimiglianza fra il modello a **un** `λ` e quello che ne
   concede **uno per durata**, su tempi CENSURATI (chi non si accende porta
   comunque la sua esposizione).  `G² = 2(ℓ_saturo − ℓ_λ)`, e il `p` si prende
   per **simulazione sotto il modello** (20 000 campagne finte), non da una
   tavola: 2 gradi di liberta' su venti giri per durata sono pochi perche' una
   χ² asintotica dica la verita'.
     · **rosso** = ⛔ non esiste un solo λ ⇒ **il rischio NON e' costante**, e
       «un'accensione a senso unico con probabilita' fissa» e' sbagliata;
     · verde = un solo λ basta ⇒ il modello regge sulle tre durate.

── **T4 · ⭐⭐ E LA FORMA — il rischio cambia col tempo TRASCORSO?**
   Questo separa il modello dall'alternativa che il coordinatore ha nominato:
   *«una finestra di vulnerabilita' che si chiude»*.  Si divide il tempo a
   regime in tre fasce — **0-7 s · 7-22 s · 22-47 s**, che sono esattamente
   l'esposizione che ogni durata AGGIUNGE — e si confronta il **tasso per
   secondo di esposizione** in ciascuna.
     · **rosso** = i tre tassi non sono lo stesso ⇒ il rischio dipende da quanto
       tempo e' passato: se il primo e' alto e gli altri bassi e' **una finestra
       che si chiude**; se cresce, e' **un logoramento**;
     · verde = i tre tassi coincidono ⇒ senza memoria, come dice il modello.
   ⛔ E se esce rosso **NON SI FORZA UNA SPIEGAZIONE**: si riporta la curva e si
      dice che non e' costante.

⭐ LA SOGLIA, dichiarata prima: **0,05 / 4 = 0,0125** (Bonferroni sulle quattro
   prove).

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ QUANTI GIRI, E ⚠ CHE COSA NON POTREI DISTINGUERE
═══════════════════════════════════════════════════════════════════════════════

⭐ **Venti giri per durata**, piu' le tre già fatte a 25 s che si RILEGGONO (non
   si rimisurano: stesso binario, stesso terreno, stessa casella, stessa sonda).
   ⇒ 40 giri nuovi ≈ un'ora di macchina.

⚠⚠ **CHE COSA NON AVREI POTUTO VEDERE** — e si scrive prima:

  1. ⛔⛔ **A 50 s la prova del SI'/NO e' quasi cieca**, e va detto forte: con
     p₀ = 0,92 e venti giri, la regione che il binomiale accetta arriva
     giu' fino a **circa il 75 %**.  ⇒ Se la verita' a 50 s fosse il 78 %, T2
     **non se ne accorgerebbe**.  E' il prezzo di una predizione vicina al
     soffitto: sopra il 90 % non c'e' quasi piu' spazio per sbagliare in su.
     ⭐ **Per questo il verdetto e' T3 e non T2**: T3 non usa il si'/no, usa gli
       **ISTANTI** — e un giro da 50 s che si accende al 45esimo secondo dice
       molto piu' di «è andata male».  E' li' che stanno i gradi di liberta'.
  2. **A 10 s la scaldata pesa il triplo.**  ⚠ La prima chiave e l'apertura di
     sessione costano UGUALE a tutte le durate: a 10 s la scaldata e' il 30 %
     del giro, a 50 s il 6 %.  ⇒ L'esposizione si conta **sempre da 3 s in poi**
     (`SCALDATA`), che e' lo stesso taglio con cui `09-b70.misura()` decide le
     chiavi a regime e con cui `09-b83` fissa l'accensione.  Senza questo si
     confronterebbero due cose diverse.
     ⛔ E resta un residuo che NON so togliere: le accensioni piu' precoci
        osservate stanno a **3,1 e 3,2 s**, cioe' appiccicate al taglio.  Se
        qualcuna si accendesse davvero PRIMA dei 3 s, io la vedrei al taglio, e
        il tasso della prima fascia sarebbe gonfiato.  ⇒ **T4 potrebbe dare
        rosso sulla prima fascia per colpa del taglio**, non del prodotto, e in
        quel caso lo dico invece di chiamarlo scoperta.
  3. **Una deriva lenta del rischio** (per esempio λ che cambia del 20 % fra
     l'inizio e la fine dell'ora): quaranta giri non la separano dal rumore.
  4. ⚠ E la grana resta di **un secondo** per le righe `rete-quic`
     (`webtransport.c:4573`), ma qui non morde: l'accensione si legge dagli
     EVENTI, che portano l'ora al millesimo.

I CODICI D'USCITA
    0   CONFORME · 1 NON CONFORME (c'e' un rosso) · 2 uso/terreno/rete
    3   ⛔ NON HO NIENTE DA GIUDICARE

Uso (dal portatile):
    python3 banchi/09-b83-durate.py --certifica     ⭐ senza macchina
    python3 banchi/09-b83-durate.py giri [--giri 20]
    python3 banchi/09-b83-durate.py giudica
"""
import argparse, importlib.util, json, math, os, random, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("FUORI", "/tmp/09-b83")


def _carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ⛔ Tutto l'isolamento (porta, utente, albero, shm, sonda) sta in `09-b83`, e si
#    prende da li': due descrizioni dello stesso isolamento in due file sono due
#    descrizioni che divergono.
B83 = _carica("b83bif", os.path.join(QUI, "09-b83-biforcazione.py"))
_ok, _ko, _dub, _inf, _log = B83._ok, B83._ko, B83._dub, B83._inf, B83._log
FUORI = B83.FUORI
CHI = "09-b83d"      # ⛔ il mio nome sul lucchetto: non e' quello di 09-b83

# ═══════════════════════════════════════════════════════════════════════════
# LE COSTANTI — in un posto solo, e ciascuna con la sua ragione
# ═══════════════════════════════════════════════════════════════════════════
SCALDATA = B83.SCENA_PRIMI_S        # 3,0 s — lo STESSO taglio di 09-b70 e 09-b83
DURATE_NUOVE = [10, 50]             # ⇒ §«CHE COSA LA REFUTA»
DURATA_VECCHIA = 25                 # ⭐ si RILEGGE dalla campagna del 24 ago
GIRI_PER_DURATA = 20
GIRI_DENOM = 2
PERDITA_CHIESTA = B83.PERDITA_CHIESTA          # 0,20 % — ⛔ non si sposta
LAMBDA_MISURATO = 0.0529            # /s — `[M]` 24 ago, e NON si ritocca
ATTESI = {10: 1.0 - math.exp(-LAMBDA_MISURATO * (10 - SCALDATA)),
          50: 1.0 - math.exp(-LAMBDA_MISURATO * (50 - SCALDATA))}
PROVE = 4
SOGLIA_P = 0.05 / PROVE             # = 0,0125
SIMULAZIONI = 20000
FASCE = [(0.0, 7.0), (7.0, 22.0), (22.0, 47.0)]
# ⭐ Le fasce non sono scelte a occhio: 7 = 10−3, 22 = 25−3, 47 = 50−3, cioe'
#    **l'esposizione che ogni durata AGGIUNGE**.  ⇒ Ogni fascia e' guardata da un
#    sottoinsieme diverso di giri, ed e' esattamente la struttura del disegno.
NOMEFILE = "09-b83-durate.json"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ DAL GIRO AL DATO DI SOPRAVVIVENZA — «quanto ha corso, e se si e' acceso»
# ═══════════════════════════════════════════════════════════════════════════
def dato(c, secondi):
    """`(x, acceso)` — `x` e' il tempo A REGIME che quel giro ha corso: fino
       all'accensione se si e' acceso, fino alla fine se no.

    ⛔ Un giro che non si accende **non e' un dato mancante**: e' un'osservazione
       censurata, e porta la sua esposizione intera.  Buttarlo vorrebbe dire
       stimare il rischio guardando solo chi e' caduto — che e' il modo classico
       di far sembrare qualunque rischio enorme.
    """
    L = float(secondi) - SCALDATA
    a = c.get("accensione_s")
    if a is not None and a <= secondi:
        return (max(0.0, min(a - SCALDATA, L)), True)
    return (L, False)


def raccogli(celle, secondi):
    return [dato(c, secondi) for c in celle if c.get("esito") == "misurato"]


def stima(gruppi):
    """`(lambda, eventi, esposizione)` — la stima di massima verosimiglianza per
       un esponenziale con censura a destra: **eventi diviso esposizione**."""
    n = sum(1 for g in gruppi.values() for x, acceso in g if acceso)
    e = sum(x for g in gruppi.values() for x, _ in g)
    return ((n / e if e > 0 else None), n, e)


def _vero(n, esp, lam):
    """La log-verosimiglianza di un gruppo: `n log λ − λ · esposizione`."""
    if lam is None or lam <= 0:
        return float("-inf") if n else 0.0
    return n * math.log(lam) - lam * esp


def g2_durate(gruppi):
    """**T3** — `G²` fra «un solo λ» e «un λ per durata».  ⭐ Piu' e' grande, piu'
       le durate chiedono rischi diversi."""
    lam, n, e = stima(gruppi)
    if lam is None or n == 0:
        return (None, None)
    saturo = 0.0
    per_durata = {}
    for d, g in gruppi.items():
        nd = sum(1 for x, a in g if a)
        ed = sum(x for x, _ in g)
        ld = (nd / ed) if ed > 0 and nd > 0 else None
        per_durata[d] = {"eventi": nd, "esposizione": round(ed, 1),
                         "lambda": (round(ld, 5) if ld else 0.0),
                         "frazione": (round(sum(1 for x, a in g if a) / float(len(g)), 3)
                                      if g else None), "giri": len(g)}
        saturo += _vero(nd, ed, ld) if ld else 0.0
    unico = sum(_vero(sum(1 for x, a in g if a), sum(x for x, _ in g), lam)
                for g in gruppi.values())
    return (2.0 * (saturo - unico), per_durata)


def g2_fasce(gruppi):
    """**T4** — `G²` fra «un solo λ» e «un λ per fascia di tempo TRASCORSO».

    ⭐ E' la prova che separa «senza memoria» da «una finestra che si chiude».
    """
    n_f = [0.0] * len(FASCE)
    e_f = [0.0] * len(FASCE)
    for secondi, g in gruppi.items():
        for x, acceso in g:
            for j, (a, b) in enumerate(FASCE):
                e_f[j] += max(0.0, min(b, x) - a)
            if acceso:
                for j, (a, b) in enumerate(FASCE):
                    if a <= x < b:
                        n_f[j] += 1
                        break
    tot_n, tot_e = sum(n_f), sum(e_f)
    if tot_e <= 0 or tot_n == 0:
        return (None, None)
    lam = tot_n / tot_e
    saturo = sum(_vero(n_f[j], e_f[j], (n_f[j] / e_f[j]) if n_f[j] else None)
                 for j in range(len(FASCE)))
    unico = sum(_vero(n_f[j], e_f[j], lam) for j in range(len(FASCE)))
    dett = [{"fascia": "%g-%g s" % FASCE[j], "eventi": int(n_f[j]),
             "esposizione": round(e_f[j], 1),
             "tasso": round(n_f[j] / e_f[j], 5) if e_f[j] else None}
            for j in range(len(FASCE))]
    return (2.0 * (saturo - unico), dett)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL `p` SI PRENDE PER SIMULAZIONE, NON DA UNA TAVOLA
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Una χ² a 2 gradi di liberta' e' un'APPROSSIMAZIONE che vale quando i conti
#    sono grandi.  Qui i conti sono sei o sette per fascia: la tavola darebbe un
#    `p` che sembra una probabilita' e non lo e'.
# ⭐ Simulare e' esatto quanto il modello: si fabbricano 20 000 campagne finte
#    **sotto il modello a un solo λ**, con le STESSE durate e la stessa censura,
#    e si conta quante volte il caso produce un `G²` grande almeno quanto quello
#    osservato.  ⚠ E il `+1` a numeratore e denominatore non e' prudenza: senza,
#    un `G²` mai superato darebbe `p = 0`, e uno zero qui vorrebbe dire
#    «impossibile», che nessuna simulazione sa.
def _p_simulato(gruppi, osservato, quale, semino=1983):
    lam, n, e = stima(gruppi)
    if lam is None or osservato is None:
        return None
    r = random.Random(semino)
    estremi = 0
    for _ in range(SIMULAZIONI):
        finti = {}
        for d, g in gruppi.items():
            L = float(d) - SCALDATA
            fila = []
            for _ in g:
                t = r.expovariate(lam)
                fila.append((t, True) if t <= L else (L, False))
            finti[d] = fila
        g2 = (g2_durate(finti) if quale == "durate" else g2_fasce(finti))[0]
        if g2 is not None and g2 >= osservato - 1e-12:
            estremi += 1
    return (estremi + 1) / float(SIMULAZIONI + 1)


def p_binomiale(k, n, p0):
    """`p` a due code, esatto: la somma delle probabilita' dei conti che sono
       **almeno tanto improbabili** quanto quello visto."""
    if n <= 0:
        return None
    def pr(i):
        return math.comb(n, i) * (p0 ** i) * ((1 - p0) ** (n - i))
    visto = pr(k)
    return min(1.0, sum(pr(i) for i in range(n + 1) if pr(i) <= visto + 1e-15))


def regione_accettata(n, p0, alfa):
    """⚠ Quali conti NON verrebbero rifiutati — cioe' **che cosa questa prova
       non sa distinguere**.  Si stampa sempre accanto al risultato."""
    buoni = [k for k in range(n + 1) if (p_binomiale(k, n, p0) or 0) > alfa]
    return (min(buoni), max(buoni)) if buoni else None


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I PREDICATI — SCRITTI PRIMA, e ne torna `(passa, perche)`
# ═══════════════════════════════════════════════════════════════════════════
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def p_frazione(secondi, k, n, atteso):
    """**T1 / T2 · IL CONTO LEGGIBILE.**  ⚠ Prova un PUNTO, non il modello: il
       verdetto e' T3."""
    if n < 5:
        return _muto("a %d s ho %d giri validi: troppo pochi per un conto"
                     % (secondi, n))
    p = p_binomiale(k, n, atteso)
    reg = regione_accettata(n, atteso, SOGLIA_P)
    coda = ("a %d s: **%d su %d = %.0f %%** contro un atteso del **%.0f %%** · "
            "p = %.4f · ⚠ questa prova accetterebbe qualunque conto fra %s e %s "
            "(cioe' fra il %.0f %% e il %.0f %%): fuori di li' non sa vedere"
            % (secondi, k, n, 100.0 * k / n, 100 * atteso, p,
               reg[0] if reg else "?", reg[1] if reg else "?",
               100.0 * reg[0] / n if reg else 0, 100.0 * reg[1] / n if reg else 0))
    if p <= SOGLIA_P:
        return _no("⛔ %s ⇒ la frazione a questa durata NON e' quella predetta "
                   "dal λ misurato a 25 s" % coda)
    return _si("%s ⇒ compatibile col λ misurato a 25 s" % coda)


def p_un_solo_lambda(g2, p, dett):
    """**T3 · ⭐⭐ IL VERDETTO.**  Esiste UN SOLO λ che spiega tutte le durate?"""
    if g2 is None or p is None:
        return _muto("non ho abbastanza accensioni per stimare un λ")
    righe = " · ".join("%s s: %d/%d accesi (%.0f %%), λ = %.4f/s"
                       % (d, v["eventi"], v["giri"], 100 * (v["frazione"] or 0),
                          v["lambda"]) for d, v in sorted(dett.items()))
    if p <= SOGLIA_P:
        return _no("⛔⛔ NON ESISTE UN SOLO λ: G² = %.2f, p = %.4f (≤ %.4f) — %s "
                   "⇒ **il rischio NON e' costante**, e «un'accensione a senso "
                   "unico con probabilita' fissa» e' la parola sbagliata"
                   % (g2, p, SOGLIA_P, righe))
    return _si("⭐⭐ UN SOLO λ BASTA per tutte le durate: G² = %.2f, p = %.4f "
               "(sopra %.4f) — %s" % (g2, p, SOGLIA_P, righe))


def p_senza_memoria(g2, p, dett):
    """**T4 · ⭐⭐ IL RISCHIO DIPENDE DA QUANTO TEMPO E' PASSATO?**"""
    if g2 is None or p is None:
        return _muto("non ho abbastanza accensioni per confrontare le fasce")
    righe = " · ".join("%s: %d accensioni in %.0f s ⇒ %.4f/s"
                       % (v["fascia"], v["eventi"], v["esposizione"],
                          v["tasso"] or 0) for v in dett)
    if p <= SOGLIA_P:
        primo = dett[0]["tasso"] or 0
        dopo = [v["tasso"] or 0 for v in dett[1:]]
        forma = ("⇒ la prima fascia corre piu' delle altre: somiglia a **una "
                 "finestra di vulnerabilita' che si chiude**"
                 if dopo and primo > max(dopo) else
                 "⇒ il rischio CRESCE col tempo trascorso: somiglia a un "
                 "**logoramento**" if dopo and primo < min(dopo) else
                 "⇒ i tassi non sono ordinati: la forma non si legge da tre "
                 "fasce")
        return _no("⛔⛔ IL RISCHIO NON E' SENZA MEMORIA: G² = %.2f, p = %.4f "
                   "(≤ %.4f) — %s %s. ⚠ E NON forzo una spiegazione: riporto la "
                   "curva. ⛔ Va anche escluso che sia il taglio della scaldata "
                   "a gonfiare la prima fascia (⇒ §«che cosa non potrei "
                   "vedere», punto 2)" % (g2, p, SOGLIA_P, righe, forma))
    return _si("⭐ IL RISCHIO E' SENZA MEMORIA: i tre tassi coincidono entro il "
               "caso — G² = %.2f, p = %.4f (sopra %.4f) — %s"
               % (g2, p, SOGLIA_P, righe))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL CONTROLLO POSITIVO
# ═══════════════════════════════════════════════════════════════════════════
def _finge(lam, durate, quanti, semino, lam_per_durata=None):
    r = random.Random(semino)
    g = {}
    for d in durate:
        L = float(d) - SCALDATA
        l = (lam_per_durata or {}).get(d, lam)
        g[d] = []
        for _ in range(quanti):
            t = r.expovariate(l)
            g[d].append((t, True) if t <= L else (L, False))
    return g


def certifica():
    print("⭐ CERTIFICAZIONE DEL BANCO DELLE DURATE — l'atteso e' scritto PRIMA\n")
    print("   ⛔ Nessun contatto con la macchina di prova.\n")
    verde = True
    n = [0]

    def caso(titolo, atteso, avuto):
        n[0] += 1
        passa, perche = avuto
        ok = (passa is atteso) if atteso is None else (passa == atteso)
        print("  %2d · %s" % (n[0], titolo))
        print("       atteso %-5s   avuto %-5s   %s" % (atteso, passa, perche[:180]))
        (_ok if ok else _ko)("come scritto" if ok
                             else "⛔ IL BANCO NON SA VEDERE QUEL CHE CERCA")
        return ok

    # ── il conto della predizione, che e' l'argomento ──────────────────────
    _log("⛔ LA PREDIZIONE — viene dal λ misurato, e non e' ritoccata")
    n[0] += 1
    print("  %2d · λ = %.4f/s ⇒ a 10 s il %.0f %% · a 50 s il %.0f %%"
          % (n[0], LAMBDA_MISURATO, 100 * ATTESI[10], 100 * ATTESI[50]))
    if abs(ATTESI[10] - 0.3095) < 0.002 and abs(ATTESI[50] - 0.9167) < 0.002:
        _ok("⭐ sono il 31 % e il 92 % scritti in testa")
    else:
        _ko("⛔ la predizione non e' quella dichiarata"); verde = False
    n[0] += 1
    reg10 = regione_accettata(20, ATTESI[10], SOGLIA_P)
    reg50 = regione_accettata(20, ATTESI[50], SOGLIA_P)
    print("  %2d · ⚠ quel che le due prove NON sanno distinguere: a 10 s "
          "accettano %s..%s su 20 · a 50 s %s..%s su 20"
          % (n[0], reg10[0], reg10[1], reg50[0], reg50[1]))
    if reg50[0] <= 16:
        _ok("⭐ confermato il punto 1: a 50 s la prova del si'/no e' quasi "
            "cieca verso il basso (accetta fino al %.0f %%) — per questo il "
            "verdetto e' T3" % (100.0 * reg50[0] / 20))
    else:
        _ko("⛔ la regione accettata non e' quella dichiarata"); verde = False

    # ── il dato di sopravvivenza ───────────────────────────────────────────
    _log("⛔ IL DATO DI SOPRAVVIVENZA — un giro che non si accende NON e' un "
         "dato mancante")
    prove = [("acceso a 8 s in un giro da 25 ⇒ ha corso 5 s ed e' un evento",
              dato({"esito": "misurato", "accensione_s": 8.0}, 25), (5.0, True)),
             ("mai acceso in un giro da 25 ⇒ ha corso 22 s, censurato",
              dato({"esito": "misurato", "accensione_s": None}, 25), (22.0, False)),
             ("⛔ acceso a 26,1 s in un giro da 25 ⇒ e' registro scritto DOPO: "
              "censurato a 22 s",
              dato({"esito": "misurato", "accensione_s": 26.112}, 25), (22.0, False)),
             ("un giro da 10 s: l'esposizione e' 7 s, non 10 (la scaldata pesa "
              "il 30 %)",
              dato({"esito": "misurato", "accensione_s": None}, 10), (7.0, False))]
    for titolo, avuto, atteso in prove:
        n[0] += 1
        print("  %2d · %s — atteso %s, avuto %s" % (n[0], titolo, atteso, avuto))
        if abs(avuto[0] - atteso[0]) < 1e-9 and avuto[1] == atteso[1]:
            _ok("come scritto")
        else:
            _ko("⛔ il dato di sopravvivenza non e' quello"); verde = False

    # ── la stima di λ ──────────────────────────────────────────────────────
    _log("⛔ LA STIMA DI λ — «eventi diviso esposizione», e ritrova quel che sa")
    n[0] += 1
    g = _finge(0.05, [10, 25, 50], 300, 11)
    lam, ne, es = stima(g)
    print("  %2d · fabbricati 900 giri con λ = 0,0500 ⇒ stimato %.4f (%d "
          "accensioni su %.0f s)" % (n[0], lam, ne, es))
    if abs(lam - 0.05) < 0.006:
        _ok("⭐ la stima ritrova il λ che ha generato i dati, censura compresa")
    else:
        _ko("⛔ la stima e' distorta"); verde = False
    n[0] += 1
    g_solo_accesi = {25: [(x, a) for x, a in g[25] if a]}
    lam_sbagliato, _, _ = stima(g_solo_accesi)
    print("  %2d · ⛔ e se buttassi i giri che non si accendono: λ = %.4f invece "
          "di 0,0500" % (n[0], lam_sbagliato))
    if lam_sbagliato > 0.05 * 1.5:
        _ok("⭐ buttare i censurati gonfia il rischio di piu' del 50 %: e' la "
            "ragione per cui portano la loro esposizione")
    else:
        _ko("⛔ il controllo non mostra il difetto che dice"); verde = False

    # ── T3 · un solo λ? ────────────────────────────────────────────────────
    _log("T3 · ⭐⭐ «esiste UN SOLO λ che spiega tutte le durate?»")
    g = _finge(0.05, [10, 25, 50], 20, 3)
    x, dett = g2_durate(g)
    verde &= caso("⭐ dati generati da UN SOLO λ ⇒ VERDE", True,
                  p_un_solo_lambda(x, _p_simulato(g, x, "durate", 5), dett))
    g = _finge(0.05, [10, 25, 50], 20, 4,
               lam_per_durata={10: 0.30, 25: 0.05, 50: 0.012})
    x, dett = g2_durate(g)
    verde &= caso("⛔ ogni durata col suo λ (0,30 · 0,05 · 0,012) ⇒ ROSSO",
                  False, p_un_solo_lambda(x, _p_simulato(g, x, "durate", 6), dett))
    verde &= caso("⛔ nessuna accensione ⇒ MUTO", None,
                  p_un_solo_lambda(None, None, None))

    # ── T4 · senza memoria? ────────────────────────────────────────────────
    _log("T4 · ⭐⭐ «il rischio dipende da quanto tempo e' passato?»")
    g = _finge(0.05, [10, 25, 50], 40, 7)
    x, dett = g2_fasce(g)
    verde &= caso("⭐ rischio davvero costante ⇒ VERDE (senza memoria)", True,
                  p_senza_memoria(x, _p_simulato(g, x, "fasce", 8), dett))
    # ⭐ Una FINESTRA CHE SI CHIUDE, fabbricata: quasi tutti si accendono presto,
    #   e chi sopravvive ai primi 7 s non si accende quasi piu'.
    r = random.Random(21)
    g = {}
    for d in (10, 25, 50):
        L = float(d) - SCALDATA
        fila = []
        for _ in range(40):
            t = r.expovariate(0.22) if r.random() < 0.62 else 7.0 + r.expovariate(0.004)
            fila.append((t, True) if t <= L else (L, False))
        g[d] = fila
    x, dett = g2_fasce(g)
    verde &= caso("⛔ una FINESTRA CHE SI CHIUDE ⇒ ROSSO, e la frase lo dice",
                  False, p_senza_memoria(x, _p_simulato(g, x, "fasce", 9), dett))
    n[0] += 1
    passa, perche = p_senza_memoria(x, _p_simulato(g, x, "fasce", 9), dett)
    print("  %2d · e la forma nominata: %s" % (n[0], "finestra" in perche))
    if "finestra" in perche and "NON forzo una spiegazione" in perche:
        _ok("⭐ nomina la forma E dichiara di non forzarla")
    else:
        _ko("⛔ non nomina la forma"); verde = False

    # ── T1 / T2 · i conti leggibili ────────────────────────────────────────
    _log("T1 · T2 — i conti leggibili (⚠ provano un punto, non il modello)")
    verde &= caso("a 10 s: 6 su 20 = 30 %, atteso 31 % ⇒ VERDE", True,
                  p_frazione(10, 6, 20, ATTESI[10]))
    verde &= caso("⛔ a 10 s: 19 su 20 = 95 %, atteso 31 % ⇒ ROSSO", False,
                  p_frazione(10, 19, 20, ATTESI[10]))
    verde &= caso("a 50 s: 18 su 20 = 90 %, atteso 92 % ⇒ VERDE", True,
                  p_frazione(50, 18, 20, ATTESI[50]))
    verde &= caso("⛔ a 50 s: 8 su 20 = 40 %, atteso 92 % ⇒ ROSSO", False,
                  p_frazione(50, 8, 20, ATTESI[50]))
    verde &= caso("⚠ a 50 s: 16 su 20 = 80 % ⇒ VERDE lo stesso — ed e' il "
                  "limite dichiarato al punto 1, non un successo", True,
                  p_frazione(50, 16, 20, ATTESI[50]))
    verde &= caso("⛔ quattro giri soli ⇒ MUTO", None, p_frazione(10, 1, 4, ATTESI[10]))

    print()
    if verde:
        _ok("⭐ %d casi: il banco sa dare VERDE, ROSSO e MUTO dove e' scritto"
            % n[0])
    else:
        _ko("⛔ IL BANCO NON HA DIRITTO AL VERDE")
    return 0 if verde else 1


# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE PARLA CON LA MACCHINA DI PROVA
# ═══════════════════════════════════════════════════════════════════════════
SCADENZA = [0.0]
AFFITTO = 900


def rinnova_se_serve():
    if time.time() > SCADENZA[0] - 400:
        if B83.B76.rinnova(CHI, AFFITTO):
            SCADENZA[0] = time.time() + AFFITTO
            _inf("⛔ affitto del lucchetto rinnovato per %d s" % AFFITTO)
        else:
            raise SystemExit("⛔ il lucchetto non e' piu' mio: MI FERMO")


def passo_giri(a):
    """⛔ **L'UNICA COSA CHE CAMBIA E' LA DURATA.**  Stessa casella
       `perdita-0,20`, stesso terreno, stesso binario, stessa sonda a 20 000
       pacchetti, cure spente.  E le durate si alternano a blocchi con lo zero
       in mezzo, cosi' una deriva dell'ora non si travesta da effetto della
       durata."""
    nome0, reg0, ver0 = B83.B80.casella(0.0)
    nome, reg, ver = B83.B80.casella(PERDITA_CHIESTA)
    d = {"banco": CHI, "quando": time.strftime("%F %T"), "casella": nome,
         "albero": B83.ALB, "md5": B83.impronta_binario(),
         "durate": DURATE_NUOVE, "giri_per_durata": a.giri,
         "lambda_misurato": LAMBDA_MISURATO, "attesi": ATTESI,
         "soglia_p": SOGLIA_P, "scaldata": SCALDATA,
         "apertura": [], "chiusura": [], "per_durata": {}}
    for i in range(GIRI_DENOM):
        d["apertura"].append(B83.giro(nome0, reg0, ver0, DURATA_VECCHIA,
                                      etichetta="%s · APERTURA %d/%d"
                                      % (nome0, i + 1, GIRI_DENOM)))
        B83.salva(NOMEFILE, d)
        rinnova_se_serve()
    for secondi in DURATE_NUOVE:
        d["per_durata"][str(secondi)] = []
        for i in range(a.giri):
            c = B83.giro(nome, reg, ver, secondi,
                         etichetta="%s · %d s · giro %d/%d"
                         % (nome, secondi, i + 1, a.giri))
            c["secondi"] = secondi
            d["per_durata"][str(secondi)].append(c)
            B83.salva(NOMEFILE, d)
            rinnova_se_serve()
        acc = [x.get("accensione_s") for x in d["per_durata"][str(secondi)]]
        _inf("⭐ %d s — accensioni finora: %s" % (secondi, acc))
    for i in range(GIRI_DENOM):
        d["chiusura"].append(B83.giro(nome0, reg0, ver0, DURATA_VECCHIA,
                                      etichetta="%s · CHIUSURA %d/%d"
                                      % (nome0, i + 1, GIRI_DENOM)))
        B83.salva(NOMEFILE, d)
        rinnova_se_serve()
    _inf("scritto in %s" % B83.salva(NOMEFILE, d))
    return d


def gruppi_da(d):
    """⛔ I 25 s si RILEGGONO dalla campagna del 24 agosto — stesso binario,
       stesso terreno, stessa casella, stessa sonda — e si dichiara l'`md5`."""
    g = {}
    for secondi, celle in d.get("per_durata", {}).items():
        g[int(secondi)] = raccogli(celle, int(secondi))
    vecchia = B83.leggi("09-b83-biforcazione.json")
    if vecchia and vecchia.get("celle"):
        if vecchia.get("md5") != d.get("md5"):
            _ko("⛔ la campagna a 25 s ha md5 %s e questa %s: NON le unisco, "
                "sarebbero due binari" % (vecchia.get("md5"), d.get("md5")))
        else:
            g[DURATA_VECCHIA] = raccogli(vecchia["celle"], DURATA_VECCHIA)
            _inf("⭐ rilette %d celle a %d s dalla campagna del %s (md5 %s)"
                 % (len(g[DURATA_VECCHIA]), DURATA_VECCHIA,
                    vecchia.get("quando"), vecchia.get("md5")))
    else:
        _dub("⚠ non trovo la campagna a 25 s: il confronto si fa su due durate "
             "invece che su tre, e i gradi di liberta' calano da 2 a 1")
    return g


def giudica(d):
    rossi, muti, verdi = [], [], []
    g = gruppi_da(d)
    if not g:
        _ko("⛔ nessun gruppo da giudicare")
        return (["nessun dato"], [], [])

    _log("⭐ LE TRE DURATE, e per ciascuna quanti si sono accesi")
    for secondi in sorted(g):
        fila = g[secondi]
        k = sum(1 for x, a in fila if a)
        acc = sorted(round(x + SCALDATA, 1) for x, a in fila if a)
        _inf("%2d s · %2d giri · **%2d accesi (%.0f %%)** · esposizione %.0f s · "
             "accensioni ai secondi %s"
             % (secondi, len(fila), k, 100.0 * k / len(fila) if fila else 0,
                sum(x for x, _ in fila), acc))

    # ── T1 / T2 · i conti leggibili ────────────────────────────────────────
    _log("T1 · T2 — I DUE CONTI LEGGIBILI (⚠ provano un punto, non il modello)")
    for secondi in DURATE_NUOVE:
        fila = g.get(secondi) or []
        k = sum(1 for x, a in fila if a)
        passa, perche = p_frazione(secondi, k, len(fila), ATTESI[secondi])
        (_ok if passa else (_dub if passa is None else _ko))("T · %s" % perche)
        if passa is False:
            rossi.append("T · la frazione a %d s non e' quella predetta" % secondi)
        elif passa is None:
            muti.append("T · %d s — %s" % (secondi, perche[:100]))

    # ── T3 · il verdetto ───────────────────────────────────────────────────
    _log("T3 · ⭐⭐ IL VERDETTO — esiste UN SOLO λ che spiega tutte le durate?")
    x, dett = g2_durate(g)
    p = _p_simulato(g, x, "durate")
    passa, perche = p_un_solo_lambda(x, p, dett)
    (_ok if passa else (_dub if passa is None else _ko))("T3 · %s" % perche)
    d["T3"] = {"g2": x, "p": p, "per_durata": dett}
    if passa is False:
        rossi.append("T3 · il rischio NON e' costante")
    elif passa is None:
        muti.append("T3 · %s" % perche[:120])
    else:
        verdi.append("T3 · un solo λ basta per tutte le durate")

    # ── T4 · la forma ──────────────────────────────────────────────────────
    _log("T4 · ⭐⭐ LA FORMA — il rischio dipende da quanto tempo e' passato?")
    x4, dett4 = g2_fasce(g)
    p4 = _p_simulato(g, x4, "fasce")
    passa4, perche4 = p_senza_memoria(x4, p4, dett4)
    (_ok if passa4 else (_dub if passa4 is None else _ko))("T4 · %s" % perche4)
    d["T4"] = {"g2": x4, "p": p4, "fasce": dett4}
    if passa4 is False:
        rossi.append("T4 · il rischio non e' senza memoria")
    elif passa4 is None:
        muti.append("T4 · %s" % perche4[:120])
    else:
        verdi.append("T4 · il rischio e' senza memoria")

    # ── D · il denominatore ────────────────────────────────────────────────
    _log("D · IL DENOMINATORE HA RETTO PER TUTTA L'ORA?")
    va = [c.get("fps") for c in d.get("apertura", []) if c.get("esito") == "misurato"]
    vb = [c.get("fps") for c in d.get("chiusura", []) if c.get("esito") == "misurato"]
    passa, perche = B83.B80.p_due_gruppi_uguali("zero d'apertura", va,
                                                "zero di chiusura", vb,
                                                B83.B80.METRO_MINIMO,
                                                "IL DENOMINATORE")
    (_ok if passa else (_dub if passa is None else _ko))("D · %s" % perche)
    if passa is False:
        rossi.append("D · la macchina e' derivata durante l'ora")
    elif passa is None:
        muti.append("D · %s" % perche[:100])

    # ── ⭐⭐ LA FRASE GIUSTA ────────────────────────────────────────────────
    _log("⭐⭐ LA PAROLA DA METTERE NEL DOCUMENTO")
    lam, ne, es = stima(g)
    if passa4 is False or (d["T3"]["p"] is not None and d["T3"]["p"] <= SOGLIA_P):
        _dub("⛔ NON scrivo la frase: il rischio costante non regge. ⚠ Si "
             "riporta la curva misurata e si dice che non e' costante, senza "
             "forzare una spiegazione.")
        d["frase"] = None
    elif passa4 is None or d["T3"]["p"] is None:
        _dub("⚠ non ho abbastanza per giudicare il modello: nessuna frase")
        d["frase"] = None
    else:
        d["frase"] = (
            "A 0,20 %% di perdita la spirale di chiavi non e' «bistabile»: e' "
            "un'ACCENSIONE A SENSO UNICO. Ogni secondo di sessione ha la stessa "
            "probabilita' di accenderla — `[M]` %.3f all'anno di secondo, cioe' "
            "un'attesa media di %.0f s — e una volta accesa non si spegne piu'. "
            "⇒ Che un giro «vada bene» non dice che la rete regga: dice solo che "
            "si e' guardato per poco. Una sessione di %d s si accende nel %.0f %% "
            "dei casi, una da %d s nel %.0f %%, e una da dieci minuti quasi "
            "sempre."
            % (lam, 1.0 / lam, 25, 100 * (1 - math.exp(-lam * 22)),
               50, 100 * (1 - math.exp(-lam * 47))))
        _ok("⭐⭐ %s" % d["frase"])
    d["lambda_stimato"] = lam
    d["eventi"], d["esposizione"] = ne, es
    return rossi, muti, verdi


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?", choices=["terreno", "giri", "giudica"])
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--giri", type=int, default=GIRI_PER_DURATA)
    p.add_argument("--attesa", type=int, default=9000,
                   help="⛔ il lucchetto e' di un altro: si aspetta il turno")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.passo:
        p.error("serve un passo, oppure --certifica")
    os.makedirs(FUORI, exist_ok=True)

    if a.passo == "giudica":
        B83.importa(con_macchina=False)
        d = B83.leggi(NOMEFILE)
        if not d:
            _ko("⛔ non trovo %s/%s: prima si gira «giri»" % (FUORI, NOMEFILE))
            return 2
        rossi, muti, verdi = giudica(d)
        B83.salva(NOMEFILE, d)
        return B83.verdetto(rossi, muti, verdi)

    B83.importa()
    if a.passo == "terreno":
        ok = B83.B76.spedisci_sonda()
        return 0 if (B83.B70.terreno_controlla() and ok) else 2

    _log("09-b83-durate · IL RISCHIO E' COSTANTE? — porta %d · albero %s"
         % (B83.PORTA, B83.ALB))
    print("   ⛔ l'UNICA cosa che cambia e' la durata: %s s contro %d s"
          % (DURATE_NUOVE, DURATA_VECCHIA))
    print("   ⛔ le cure restano SPENTE · casella «perdita-%.2f» · sonda a "
          "20 000 pacchetti" % PERDITA_CHIESTA)
    B83.stato_macchina()
    md5 = B83.impronta_binario()
    _inf("impronta del binario: %s" % md5)
    vecchia = B83.leggi("09-b83-biforcazione.json")
    if vecchia and vecchia.get("md5") != md5:
        _ko("⛔ NON MISURO: la campagna a 25 s ha md5 %s, questo binario %s — "
            "confronterei due binari" % (vecchia.get("md5"), md5))
        return 2
    _ok("⭐ stesso binario della campagna a 25 s: %s" % md5)
    if not B83.apparecchia():
        return 2

    quanti = 2 * a.giri + 2 * GIRI_DENOM
    # ⛔ Il lucchetto si prende con la stessa funzione di `09-b83`, ma col MIO
    #    nome: due banchi che usassero lo stesso nome si ruberebbero l'affitto.
    B83.CHI = CHI
    d = B83.con_lucchetto(quanti, max(DURATE_NUOVE), a.attesa,
                          lambda: passo_giri(a))
    if d is None:
        return 2
    rossi, muti, verdi = giudica(d)
    B83.salva(NOMEFILE, d)
    return B83.verdetto(rossi, muti, verdi)


if __name__ == "__main__":
    sys.exit(principale())
