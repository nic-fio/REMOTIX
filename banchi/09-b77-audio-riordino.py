#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b77-audio-riordino — LA CURA DEL RIORDINO DELL'AUDIO, APPAIATA.

⛔⭐ IL FATTO DA CHIUDERE.  Il 23 agosto 2026 `src/pagina.html` ha cambiato la
    lettura di `RCP.md` §6.3.  Prima: un blocco PCM arrivato **dietro a uno piu'
    nuovo** si buttava, punto (`istante <= ultimo_istante` ⇒ `scartati_vecchi`).
    Adesso si distinguono due casi:

      · «il mio posto nel tempo e' GIA' PASSATO»  ⇒ e' consumato davvero, si
        butta  (`scartati_vecchi`, e in `suona()` `scartati_tardivi`);
      · «sono arrivato dietro a uno piu' nuovo ma il mio posto c'e' ANCORA»
        ⇒ si tiene e si suona al suo posto assoluto  (`fuori_ordine`).

    ⛔⛔ E LA META' CHE CONTA NON ERA MAI STATA VERIFICATA.  Perche' la cura
        mordesse serviva una rete **che riordina**, e non e' mai stata messa:
        c'era un solo numero, il PRIMA, scritto in `src/pagina.html` riga ~6474
        — `[M]` col `netem`, jitter ±2 ms ⇒ **purezza 0,175, 1 004 blocchi
        scartati su ~5 000**.  Questo banco e' quello che la fa mordere.

⭐ APPAIATO VUOL DIRE DUE GIRI IDENTICI IN TUTTO TRANNE LA REGOLA.  Stesso
   `netem` (messo UNA volta e lasciato in piedi per tutt'e due), stessa durata,
   stessa scena, stesso tono, stesso server.  A cambiare c'e' solo
   `--audio-regola vecchia|nuova`.
   ⛔ Un giro solo con la cura accesa non dimostrerebbe niente: avrebbe la
      stessa faccia di un profilo che non riordina affatto.  E' la ragione per
      cui `09-riavvia-7920.sh` esiste, scritta per l'audio.

⛔ L'INTERRUTTORE E' DEL CLIENTE, e non e' mio: sta in `banchi/01-b3-cliente.py`
   (`--audio-regola vecchia|nuova`, predefinito `vecchia`).  Questo banco e'
   scritto **contro quell'interfaccia**, e all'avvio CONTROLLA che ci sia: se
   non c'e', si ferma.  ⚠ Senza il controllo, i due giri userebbero la stessa
   regola e il banco riferirebbe «nessuna differenza» — che e' la stessa faccia
   di «la cura non serve», e la conclusione opposta.

⛔ IL `netem` SU `lo` E' UNO SOLO PER TUTTA LA MACCHINA: lucchetto
   `banchi/09-lucchetto.py`, affitto corto, mollato in un `finally`.
   ⛔ `enp7s0` non si tocca MAI; i filtri `u32` sono sulla **sola porta 7931**;
   il guardiano stacca la disciplina anche se questo copione muore.

⭐ LE GRANDEZZE, E SONO TRE, PERCHE' UNA SOLA NON BASTEREBBE:

   1. **`purezza` = `consegnati / sul_filo`**, e la conta il CLIENTE.
      `sul_filo` sono i datagram conformi che la rete ha consegnato, contati
      **prima** del vaglio di §6.3; `consegnati` sono quelli che ne sono usciti.
      ⭐ E' la grandezza su cui si giudica la cura: la perdita della rete non
      entra nemmeno nel denominatore, quindi quel che resta e' **solo** quel che
      il ricevente ha deciso di buttare.
      ⛔ NON e' `purezza_pagina` (`consegnati/ricevuti`, quella con cui i banchi
      della pagina misuravano): li' lo scarto fa `continue` **prima** di
      `ricevuti++`, quindi il rapporto vale ~1,000 **con tutt'e due le regole**
      su una successione anche distrutta.  Si stampa accanto, dichiarata cieca.

   2. **`copertura`** — quanta parte della linea del tempo (dal primo all'ultimo
      `istante`) ha davvero ricevuto campioni, e la conto **io** dai blocchi.
   3. **`purezza_tono`** — quanta energia sta nella riga a 440 Hz, col giudice
      certificato di `07-b42`, dopo aver rimesso i blocchi **al loro posto**
      (`base + istante`, come fa l'ancora della pagina).

   ⛔⭐ Le ultime due sono LA SECONDA GAMBA, e non e' un lusso: `purezza` la
      calcola il cliente, che e' anche **l'oggetto della misura** — la cura sta
      li'.  Copertura e tono vengono dai CAMPIONI, e se il cliente dicesse «ho
      consegnato tutto» mentre meta' della linea del tempo e' silenzio, uno dei
      due mentirebbe e si vedrebbe.

⛔⛔ IL `[M]` «purezza 0,175» DI `pagina.html` RIGA 6474 **NON E' IL TERMINE DI
     PARAGONE**, e questo banco non ci si appoggia: la sua definizione non e'
     nota, e confrontare un numero di cui non si conosce la definizione con uno
     di cui la si conosce e' il modo piu' educato di fabbricare un trionfo.
     ⇒ Il termine di paragone e' **il giro gemello**, misurato lo stesso giorno
     sotto lo stesso `netem` con la stessa scena — e l'atteso e' un CONFINE
     dichiarato, non quel punto.

⛔ IL CONTATORE `reordered` DI `tc` NON ESISTE SU QUESTA MACCHINA — `[M]` 23
   agosto 2026: `grep -ac reordered /usr/sbin/tc` ⇒ **0** (iproute2 6.15.0).
   ⇒ La prova che il profilo riordina DAVVERO si prende in due modi, tutt'e
   due migliori del contatore perche' guardano il traffico VERO:
     · i pacchetti che il netem ha visto passare (`Sent … pkt` del nodo `40:`),
       che dice se il filtro `u32` morde — ⛔ a zero avrei misurato una rete
       sana credendola guasta;
     · `fuori_ordine` del cliente e i sorpassi contati sul JSONL, che dicono se
       quel che e' passato e' arrivato davvero fuori sequenza.

Uso (dal portatile):
    python3 banchi/09-b77-audio-riordino.py --certifica     # ⛔ prima di tutto
    python3 banchi/09-b77-audio-riordino.py terreno
    python3 banchi/09-b77-audio-riordino.py misura [--secondi 25] [--solo jitter-2]
    python3 banchi/09-b77-audio-riordino.py rimetti
"""
import argparse, base64, importlib.util, json, math, os, re, struct, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ISOLAMENTO, e si scrive PRIMA di importare qualunque cosa: i moduli che
#    stanno sotto leggono l'ambiente al momento dell'import, non alla chiamata.
#    ⚠ Metterlo dopo l'import darebbe un banco che gira sulla porta di un altro
#      e non se ne accorge — `LEZIONI.md` §1.26.
# ═══════════════════════════════════════════════════════════════════════════
PORTA = int(os.environ.get("PORTA", "7931"))
UTENTE = os.environ.get("UTENTE", "provanr2")
UID_B = int(os.environ.get("UID_B", "1031"))
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/09nr2-src")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/09nr2")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/09nr2-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/09nr2")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)
PAROLA_UTENTE = os.environ.get("PAROLA_UTENTE", "nr2-riordino-2026")
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
IND = os.environ.get("IND", "192.168.0.2")
FUORI = os.environ.get("FUORI", os.path.join(
    "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2/"
    "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad", "b77"))

# ⛔ Le porte che NON sono mie.  Si contano, non si toccano.
VIETATE = ("7900", "7910", "7920")
VIETATA_IFACE = "enp7s0"

for k, v in (("PORTA", str(PORTA)), ("UTENTE", UTENTE), ("UID_B", str(UID_B)),
             ("ALBERO", ALB), ("LAV", LAV), ("DENTRO_ALB", DENTRO_ALB),
             ("DENTRO_LAV", DENTRO_LAV), ("FUORI", FUORI), ("IND", IND),
             ("MACCHINA", MACCHINA)):
    os.environ[k] = v


def _carica(nome, file_):
    sp = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file_))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


RETE = _carica("b64rete", "07-b64-rete.py")      # root(), guasta(), tono_*, guardiano_*
LUCCHETTO = _carica("lucchetto", "09-lucchetto.py")
G42 = _carica("g42", "07-b42-giudice.py")        # il giudice del tono, certificato

FREQUENZA = 48000
CANALI = 2
PASSO_PCM_US = 5000          # §5.3: il blocco PCM e' 5 ms
HZ = 440
CHI = "09-b77"

def log(t):  print("\n\033[1m== %s\033[0m" % t)
def ok(t):   print("    \033[1;32mOK\033[0m  %s" % t)
def ko(t):   print("    \033[1;31mNO\033[0m  %s" % t)
def inf(t):  print("    --  %s" % t)


# ═══════════════════════════════════════════════════════════════════════════
# I PREDICATI — SCRITTI PRIMA, E SONO FUNZIONI, NON PROSA
#
# ⛔⛔ R13: nove attesi in prosa, stampati e mai confrontati.  Un banco cosi' non
#      puo' dare rosso: qualunque numero esca, la frase accanto resta vera «a
#      leggerla».  ⇒ Qui ogni atteso e' `(v, u) -> (passa, perche)` — `v` sono i
#      numeri della regola VECCHIA, `u` quelli della NUOVA — e `passa=None` vuol
#      dire «mi rifiuto di giudicare», che e' un esito SUO e non un verde.
#
# ⛔⛔⛔ E LA GRANDEZZA SI DICHIARA, PERCHE' CI SONO DUE «PUREZZE» E NON SONO LA
#       STESSA COSA:
#
#         · `purezza`      = **`consegnati / sul_filo`**, e la conta il cliente.
#           ⭐ `sul_filo` si conta PRIMA del vaglio: e' quanti blocchi la rete ha
#           consegnato; `consegnati` e' quanti ne sono usciti dal vaglio di §6.3.
#           ⇒ La perdita della rete non entra nemmeno nel denominatore, e questa
#           e' la grandezza su cui si giudica la cura.
#         · `purezza_tono` = quanta energia sta nella riga a 440 Hz, e la conto
#           IO dai campioni ricostruiti (`07-b42`, certificato).  ⚠ E' la
#           seconda gamba, indipendente dall'aritmetica del cliente, e su un
#           profilo con perdita **non puo' tornare a 1**.
#
# ⛔⛔ E IL `[M]` «purezza 0,175» DI `pagina.html` RIGA 6474 **NON E' UN
#      RIFERIMENTO**: la sua definizione non e' nota (col denominatore che usano
#      i banchi della pagina — `suonati/ricevuti`, `09-b74:300` — quel rapporto
#      vale ~1,000 con tutt'e due le regole, perche' lo scarto fa `continue`
#      PRIMA di `ricevuti++`).  ⇒ Confrontare un numero di cui non si conosce la
#      definizione con uno di cui la si conosce sarebbe il modo piu' educato di
#      fabbricare un trionfo.  Qui l'atteso e' un CONFINE, non quel punto.
# ═══════════════════════════════════════════════════════════════════════════
def _p(cond, perche):
    return (bool(cond), perche)


def _muto(perche):
    return (None, perche)


def _c(n, chiave):
    """⛔ `CODER.md` §3.10: «non ho letto» non e' «zero».  Un numero che manca
       torna `None` e fa TACERE il predicato, non lo fa passare."""
    return n.get(chiave)


# ── il controllo positivo: senza di lui il banco non ha diritto al verde ────
def a_crolla_con_vecchia(tetto, min_vecchi):
    """⛔⭐ IL CONTROLLO POSITIVO — «IL PROFILO MORDE?».

    Con la regola VECCHIA, ogni blocco arrivato dietro a uno piu' nuovo si
    butta.  ⇒ `purezza = consegnati/sul_filo` deve **crollare sotto un confine
    dichiarato**, e i blocchi buttati devono essere tanti.

    ⭐ IL CONFINE, E LA SUA RAGIONE.  Un blocco PCM e' **5 ms** (§5.3).  Una
       `purezza` di 0,90 vuol dire che un blocco su dieci non suona: a 200
       blocchi al secondo sono **venti buchi al secondo**, cioe' un frinire
       continuo, non un difetto occasionale.  ⇒ Sotto 0,90 il danno e'
       udibile senza discussione, e li' si mette il confine del profilo piu'
       mite; i profili piu' cattivi hanno confini piu' bassi, scritti accanto.
       ⛔ Non e' un punto: e' un confine.  Sotto `netem` il valore esatto non e'
       predicibile — un riordino sintetico a gruppi di k darebbe `1/(k+1)`
       esatto, ma il jitter non fa gruppi regolari.

    ⛔ E SE NON CROLLA, IL BANCO NON DA' ROSSO: SI RIFIUTA DI GIUDICARE.  Un
       profilo che non morde non e' un difetto della cura — e' una misura che
       non e' stata fatta.  ⚠ Ma non e' nemmeno un verde: `passa=None` ferma
       il profilo intero, ed e' quel che deve fare.

    ⭐ IL ROSSO VERO C'E' LO STESSO, ed e' la contraddizione: tanti blocchi
       buttati E la purezza alta.  Sono la stessa grandezza vista due volte, e
       se si contraddicono uno dei due conti e' sbagliato.
    """
    def f(v, u):
        pv, ve = _c(v, "purezza"), _c(v, "vecchi")
        sf = _c(v, "sul_filo")
        if pv is None or ve is None:
            return _muto("la regola vecchia non ha dato purezza/scartati_vecchi: "
                         "non giudico")
        if ve >= min_vecchi and pv > tetto:
            return _p(False,
                      "⛔ CONTRADDIZIONE: la regola vecchia dice di aver buttato "
                      "%d blocchi ma la purezza resta %.4f (sul_filo %s) — sono "
                      "la stessa grandezza vista due volte, e uno dei due conti "
                      "e' sbagliato" % (ve, pv, sf))
        if pv > tetto or ve < min_vecchi:
            return _muto("⛔ IL PROFILO NON MORDE: con la regola vecchia la "
                         "purezza doveva crollare sotto %.2f (vista %.4f) e i "
                         "blocchi buttati essere >= %d (visti %d).  ⇒ NON "
                         "GIUDICO: un verde qui non sarebbe una misura, sarebbe "
                         "un caso" % (tetto, pv, min_vecchi, ve))
        return _p(True,
                  "VECCHIA: il profilo MORDE — purezza %.4f <= %.2f e %d blocchi "
                  "buttati (>= %d) su %s arrivati sul filo"
                  % (pv, tetto, ve, min_vecchi, sf))
    return f


def a_risale_con_nuova(min_purezza=0.95):
    """La cura deve riportare a posto la frazione consegnata, e senza spostare
       il danno su `scartati_tardivi`.

    ⚠ E `scartati_tardivi` NON e' `scartati_vecchi`: un blocco arrivato troppo
      tardi **sul filo** finisce in `scartati_vecchi`; `scartati_tardivi` e' la
      rete di sicurezza DOPO il decodificatore.  Sono due casi diversi, e
      confonderli renderebbe questo predicato cieco al secondo.
    """
    def f(v, u):
        pu, ta = _c(u, "purezza"), _c(u, "tardivi")
        sf = _c(u, "sul_filo")
        if pu is None:
            return _muto("la regola nuova non ha dato la purezza: non giudico")
        if ta is None:
            return _muto("la regola nuova non ha dato scartati_tardivi: non giudico")
        tetto = max(20, int(0.01 * (sf or 0)))
        return _p(pu >= min_purezza and ta <= tetto,
                  "NUOVA: purezza >= %.2f (vista %.4f) e scartati_tardivi <= %d "
                  "(visti %d) — la rete di sicurezza dopo il decodificatore non "
                  "si e' presa il danno" % (min_purezza, pu, tetto, ta))
    return f


def a_il_tono_conferma(guadagno=0.05):
    """⭐ LA SECONDA GAMBA, DAI CAMPIONI E NON DALL'ARITMETICA DEL CLIENTE.

    `purezza` la calcola il cliente, che e' anche l'oggetto della misura: e' li'
    che sta la cura.  ⇒ Serve un numero preso ALTROVE.  Qui i blocchi si
    rimettono al loro posto nel tempo (`base + istante`, come fa l'ancora della
    pagina) e si misurano due cose sui CAMPIONI:
      · `copertura`    = quanta parte della linea del tempo ha davvero suono;
      · `purezza_tono` = quanta energia sta nella riga a 440 Hz (`07-b42`).
    ⛔ Se il cliente dice «ho consegnato tutto» e i campioni dicono che meta'
       della linea del tempo e' silenzio, uno dei due mente.
    """
    def f(v, u):
        cv, cu = _c(v, "copertura"), _c(u, "copertura")
        tv, tu = _c(v, "purezza_tono"), _c(u, "purezza_tono")
        if cv is None or cu is None:
            return _muto("la copertura non si e' misurata: non giudico")
        if tv is None or tu is None:
            return _p(cu - cv >= guadagno,
                      "⚠ senza purezza_tono: la copertura sale di >= %.2f "
                      "(%.4f → %.4f)" % (guadagno, cv, cu))
        return _p(cu - cv >= guadagno and tu > tv,
                  "IL TONO CONFERMA: copertura %.4f → %.4f (+%.4f, richiesto "
                  "%.2f) e purezza_tono %.3f → %.3f"
                  % (cv, cu, cu - cv, guadagno, tv, tu))
    return f


def a_fuori_positivo(v, u):
    """⭐⛔ IL PREDICATO CHE TIENE ONESTA LA CURA.

       `fuori_ordine` deve essere MAGGIORE DI ZERO nei profili che riordinano.
       Se fosse zero e la purezza alta, la cura non sta «recuperando i
       riordinati»: sta semplicemente **non vedendo il riordino**, e il numero
       buono sarebbe un caso — la stessa faccia di una rete che non guasta."""
    fu = _c(u, "fuori")
    if fu is None:
        return _muto("il cliente non ha detto `fuori_ordine`: non giudico")
    return _p(fu > 0,
              "NUOVA: fuori_ordine > 0 (visti %d) — la cura sta guardando "
              "riordini VERI, non una rete tranquilla" % fu)


def a_doppioni_zero(v, u):
    """⛔ Zero con tutt'e due le regole.  Se salgono, qualcuno conta due volte —
       e un blocco consegnato due volte raddoppierebbe il segnale, che §6.3 non
       ammette ed e' il modo peggiore di fallire."""
    dv, du = _c(v, "dop"), _c(u, "dop")
    if du is None:
        return _muto("il cliente non ha detto `doppioni`: non giudico")
    return _p(du == 0 and (dv in (0, None)),
              "doppioni 0 con tutt'e due (vecchia %s, nuova %s)"
              % ("-" if dv is None else dv, du))


def a_le_due_coincidono(tolleranza=0.01, min_purezza=0.98):
    """⛔ Il denominatore.  Su una linea che NON riordina le due regole devono
       dare lo stesso risultato: se differiscono gia' qui, la cura ha un difetto
       sul caso facile e nessun altro suo verde vale."""
    def f(v, u):
        pv, pu = _c(v, "purezza"), _c(u, "purezza")
        if pv is None or pu is None:
            return _muto("manca una delle due purezze: non giudico")
        return _p(abs(pv - pu) <= tolleranza and pv >= min_purezza and pu >= min_purezza,
                  "LISCIO: |%.4f - %.4f| <= %.2f e tutt'e due >= %.2f"
                  % (pv, pu, tolleranza, min_purezza))
    return f


def a_niente_riordino_sul_liscio(v, u):
    """⛔ Su `lo` senza disciplina i pacchetti non si sorpassano.  Se qui
       `fuori_ordine` sale, a riordinare e' qualcos'altro — e allora nemmeno i
       numeri dei profili guasti sono attribuibili al `netem`."""
    fu, ve = _c(u, "fuori"), _c(v, "vecchi")
    if fu is None:
        return _muto("il cliente non ha detto `fuori_ordine`: non giudico")
    return _p(fu == 0 and (ve or 0) == 0,
              "LISCIO: fuori_ordine 0 (visti %d) e scartati_vecchi 0 (visti %s)"
              % (fu, ve))


def a_perdita_dichiarata(frazione, tolleranza=0.6):
    """⚠ DOVE C'E' ANCHE PERDITA, LA PARTE PERSA SI DICHIARA — E DAI DUE CAPI.

    `purezza` non la vede, e non deve: `sul_filo` conta quel che la rete ha
    CONSEGNATO, quindi il perduto non entra nemmeno nel denominatore.  ⇒ Se non
    lo si dichiarasse a parte, un profilo col 2 % di perdita passerebbe per
    «pulito» solo perche' si guarda il numero giusto.

    ⛔⛔ E NON SI USA `mancati` DEL CLIENTE — `[M]` 23 agosto 2026, ed e' un
         rosso che il banco ha dato a se' stesso.  Su `casa-cattiva` il cliente
         diceva **2183 mancati su 4996, il 43,7 %**, con `netem` regolato al
         2 %: sembrava che il `netem` togliesse venti volte quel che gli era
         stato chiesto.

    ⭐ Non era il `netem`.  Il conto del SERVER diceva
       «2879 spediti, 0 buttati, **2134 rifiutati**»: con 40 ms di ritardo e il
       2 % di perdita la finestra di congestione di ngtcp2 si chiude, e il
       server **non mette sul filo** quei datagram.  `mancati` li conta lo
       stesso, perche' e' costruito sui salti di `istante` e un blocco mai
       spedito lascia lo stesso salto di uno perso.
       ⇒ «la rete l'ha perso» e «il server non l'ha mai spedito» davano lo
         stesso numero — che e' esattamente R13, e in un banco che guasta la
         RETE apposta e' la distinzione che serve piu' di ogni altra.

    ⇒ La perdita vera si misura fra i DUE CAPI:
           perduti sul filo = (spediti dal server) − (sul_filo del cliente)
       ⚠ E `rifiutati` si riporta a parte: non e' un difetto del `netem`, e'
         il prezzo che il trasporto paga su quella rete — e va detto.
    """
    def f(v, u):
        sp, sf = _c(u, "spediti_server"), _c(u, "sul_filo")
        if sp is None or not sf:
            return _muto("«spediti» del server o «sul filo» del cliente non si "
                         "sono letti: la perdita non si puo' attribuire")
        perduti = sp - sf
        if perduti < 0:
            return _p(False,
                      "⛔ il cliente dice di aver visto sul filo PIU' blocchi di "
                      "quanti il server ne abbia spediti (%d > %d): uno dei due "
                      "conti e' sbagliato" % (sf, sp))
        vista = perduti / float(sp)
        return _p(abs(vista - frazione) <= tolleranza * frazione + 0.005,
                  "LA PERDITA SI DICHIARA, DAI DUE CAPI: il server ne ha spediti "
                  "%d, il cliente ne ha visti sul filo %d ⇒ **%d perduti sulla "
                  "rete, il %.2f%%** (netem ne toglie il %.0f%%).  ⚠ E a parte: "
                  "%s RIFIUTATI da ngtcp2, cioe' mai messi sul filo — quelli "
                  "non sono del netem, e `mancati` del cliente (%s) li conta "
                  "insieme ai perduti"
                  % (sp, sf, perduti, vista * 100, frazione * 100,
                     _c(u, "rifiutati_server"), _c(u, "mancati")))
    return f


def a_il_tono_non_torna_a_uno(tetto=0.98):
    """⚠ E QUI LA PUREZZA DEL TONO **NON DEVE** TORNARE A 1, ed e' un atteso
       come gli altri: col 2 % di perdita restano buchi che nessuna regola del
       ricevente puo' riempire.  ⛔ Se tornasse a 1 sarebbe il giudice a essere
       cieco, non la rete a essere guarita."""
    def f(v, u):
        tu = _c(u, "purezza_tono")
        if tu is None:
            return _muto("purezza_tono non si e' misurata: non giudico")
        return _p(tu <= tetto,
                  "il tono NON torna a 1 (%.3f <= %.2f), e non deve: la perdita "
                  "lascia buchi che il ricevente non puo' riempire" % (tu, tetto))
    return f


def a_riordino_dai_due_capi(v, u):
    """⭐⭐⭐ LA SECONDA GAMBA DEL CONTROLLO POSITIVO, DALL'ALTRO CAPO DEL FILO.

    ⛔ IL DIFETTO CHE CURA.  La purezza e il conto dei sorpassi vengono tutt'e
       due dal lato del RICEVENTE — che e' anche l'oggetto della misura, perche'
       la cura sta li'.  ⇒ «la cura recupera i riordinati» e «il profilo non
       riordina, e non c'e' niente da recuperare» hanno **la stessa faccia** da
       quel lato solo.

    ⭐ Dal 23 agosto 2026 il SERVER sa dire il fatto per conto suo, e non sa
       niente della cura.  `[S]` `ngtcp2.h:3442` sul callback `lost_datagram`:
       *«the loss might be spurious, and DATAGRAM frame might be acknowledged
       later»*.  ⇒ Lo stesso `dgram_id` prima **perduto** e poi **riscontrato**
       e' un datagram **arrivato fuori sequenza**: e' `dgram_falsi`, sulla riga
       `rete-quic` del registro.

    ⚠ E IL PREZZO SI DICHIARA, o questo predicato darebbe rossi falsi.
      `dgram_falsi` puo' essere zero mentre il riordino c'e' davvero: ngtcp2
      dichiara perduto un pacchetto solo dopo **tre** pacchetti piu' nuovi
      riscontrati, e uno scambio fra vicini — che e' quel che fa un jitter di
      2 ms su blocchi da 5 ms — non arriva a tre.  ⇒ Il testimone del server e'
      **sufficiente, non necessario**.

    ⇒ La regola: basta che UNO dei tre capi veda il riordino perche' il profilo
      esista; se NESSUNO lo vede, il banco **si rifiuta di giudicare** — un
      verde li' sarebbe un caso, non una misura.
    """
    srv = _c(u, "dgram_falsi")
    srv_v = _c(v, "dgram_falsi")
    cli = _c(u, "fuori")            # il contatore della cura
    mio = _c(u, "fuori_arrivo")     # i sorpassi contati da me sul JSONL
    vec = _c(v, "vecchi")           # quel che la regola VECCHIA ha buttato
    tot_srv = None
    if srv is not None or srv_v is not None:
        tot_srv = (srv or 0) + (srv_v or 0)
    visti = [x for x in (cli, mio, vec) if x]
    if tot_srv is None and not visti and cli is None and mio is None:
        return _muto("nessun testimone del riordino si e' letto: non giudico")
    if tot_srv:
        return _p(True,
                  "IL SERVER lo conferma: %d datagram dati per persi e poi "
                  "RISCONTRATI (= fuori sequenza), e il server non sa niente "
                  "della cura · ricevente: fuori %s, sorpassi sul JSONL %s, "
                  "vecchi %s" % (tot_srv, cli, mio, vec))
    if visti:
        return _p(True,
                  "⚠ il testimone del server tace (dgram_falsi 0: ngtcp2 "
                  "dichiara perduto solo dopo 3 pacchetti piu' nuovi, e uno "
                  "scambio fra vicini non ci arriva), ⭐ ma il riordino si vede "
                  "sui DATI: fuori %s, sorpassi sul JSONL %s, vecchi %s"
                  % (cli, mio, vec))
    return _muto("NESSUNO dei tre capi vede riordino (server 0, fuori %s, "
                 "sorpassi sul JSONL %s, vecchi %s): il profilo NON MORDE, e "
                 "un verde qui sarebbe un caso" % (cli, mio, vec))


def a_capi_non_si_contraddicono(v, u):
    """⛔ E se i due capi si contraddicono, e' un fatto che vale piu' di
       tutt'e due: il server ha visto pacchetti tornare da perduti a
       riscontrati, e il ricevente non ne ha visto nemmeno uno fuori sequenza.
       Uno dei due sbaglia, e finche' non si sa quale nessun numero vale."""
    srv = _c(u, "dgram_falsi")
    cli, mio = _c(u, "fuori"), _c(u, "fuori_arrivo")
    if srv is None or (cli is None and mio is None):
        return _muto("manca un testimone: non confronto i due capi")
    if srv > 0 and (cli or 0) == 0 and (mio or 0) == 0:
        return _p(False,
                  "⛔ I DUE CAPI SI CONTRADDICONO: il server ha visto %d "
                  "datagram tornare da perduti a riscontrati, il ricevente "
                  "ZERO fuori sequenza (fuori %s, sorpassi sul JSONL %s)"
                  % (srv, cli, mio))
    return _p(True, "i due capi concordano (server %s · ricevente fuori %s, "
                    "sorpassi sul JSONL %s)" % (srv, cli, mio))


def a_netem_ha_visto(v, u):
    """⛔ Se il filtro `u32` non morde, il traffico non passa dal `netem`: avrei
       misurato una rete SANA credendola guasta, e scritto che la cura serve
       dove non c'era niente da curare.  ⚠ Non e' un rosso: e' un «non ho
       misurato», che e' un esito suo."""
    pv, pu = _c(v, "netem_pkt"), _c(u, "netem_pkt")
    if pv is None or pu is None:
        return _muto("il conto dei pacchetti del netem non si e' letto")
    if (pv + pu) <= 0:
        return _muto("il netem non ha visto NESSUN pacchetto: il filtro u32 "
                     "sulla porta %d non morde, e questo profilo non esiste" % PORTA)
    return _p(True, "il netem ha visto %d + %d pacchetti (il filtro morde)" % (pv, pu))


def a_server_ha_spedito(v, u):
    """⛔ Il cliente sa quanti datagram ha ricevuto; non sa quanti ne sono
       partiti.  Senza questo, un difetto del SERVER verrebbe attribuito al
       `netem` (R13)."""
    sv, su = _c(v, "spediti_server"), _c(u, "spediti_server")
    if sv is None or su is None:
        return _muto("il «conto finale» del server non si e' letto")
    return _p(sv > 0 and su > 0,
              "il server ha spedito %s e %s blocchi nei due giri" % (sv, su))


# ═══════════════════════════════════════════════════════════════════════════
# I PROFILI — QUELLI CHE RIORDINANO, NON QUELLI CHE STRINGONO
#
# ⛔ Il bersaglio della fase 9 non e' la banda («30 Mbit/s e' una connessione da
#    meta' anni 90»): e' la rete che perde, riordina e fa jitter.  ⇒ Qui non
#    c'e' nemmeno un `rate`.
# ⛔ `netem reorder` SENZA `delay` non fa niente — la riga di `delay 10ms` non e'
#    decorativa: senza, la percentuale di riordino e' ignorata dal kernel.
# ═══════════════════════════════════════════════════════════════════════════
PROFILI = [
    ("liscio", [],
     "il denominatore: nessun guasto, e le due regole devono coincidere",
     [a_le_due_coincidono(), a_niente_riordino_sul_liscio, a_doppioni_zero,
      a_server_ha_spedito, a_capi_non_si_contraddicono]),

    ("jitter-2", ["delay", "20ms", "2ms", "distribution", "normal"],
     "jitter ±2 ms, meno di un blocco PCM (5 ms): e' il profilo piu' MITE che "
     "riordini, e il confine del suo controllo positivo e' 0,90 — un blocco su "
     "dieci buttato sono venti buchi al secondo",
     [a_netem_ha_visto, a_server_ha_spedito, a_riordino_dai_due_capi,
      a_capi_non_si_contraddicono, a_crolla_con_vecchia(0.90, 100),
      a_risale_con_nuova(0.95), a_il_tono_conferma(), a_fuori_positivo,
      a_doppioni_zero]),

    ("jitter-5", ["delay", "20ms", "5ms", "distribution", "normal"],
     "jitter ±5 ms = un blocco intero: i sorpassi crescono, e il confine scende "
     "a 0,80",
     [a_netem_ha_visto, a_server_ha_spedito, a_riordino_dai_due_capi,
      a_capi_non_si_contraddicono, a_crolla_con_vecchia(0.80, 300),
      a_risale_con_nuova(0.95), a_il_tono_conferma(), a_fuori_positivo,
      a_doppioni_zero]),

    ("jitter-15", ["delay", "30ms", "15ms", "distribution", "normal"],
     "jitter ±15 ms = tre blocchi: con la regola vecchia l'ascolto e' rotto, e "
     "il confine scende a 0,60",
     [a_netem_ha_visto, a_server_ha_spedito, a_riordino_dai_due_capi,
      a_capi_non_si_contraddicono, a_crolla_con_vecchia(0.60, 800),
      a_risale_con_nuova(0.95), a_il_tono_conferma(), a_fuori_positivo,
      a_doppioni_zero]),

    ("riordino-25", ["delay", "10ms", "reorder", "25%", "50%"],
     "⭐ IL RIORDINO ESPLICITO, che NON e' il jitter: un pacchetto su quattro "
     "salta la coda e parte subito.  ⛔ Il `delay 10ms` e' obbligatorio, o "
     "`reorder` non fa niente",
     [a_netem_ha_visto, a_server_ha_spedito, a_riordino_dai_due_capi,
      a_capi_non_si_contraddicono, a_crolla_con_vecchia(0.90, 300),
      a_risale_con_nuova(0.95), a_il_tono_conferma(), a_fuori_positivo,
      a_doppioni_zero]),

    ("casa-cattiva", ["delay", "40ms", "20ms", "distribution", "normal",
                      "loss", "2%"],
     "⚠ QUI C'E' ANCHE PERDITA.  `purezza` non la vede — `sul_filo` conta quel "
     "che la rete ha CONSEGNATO — quindi la parte persa si dichiara a parte "
     "(`mancati`), e la purezza del TONO non deve tornare a 1",
     [a_netem_ha_visto, a_server_ha_spedito, a_riordino_dai_due_capi,
      a_capi_non_si_contraddicono, a_crolla_con_vecchia(0.80, 500),
      a_risale_con_nuova(0.95), a_perdita_dichiarata(0.02),
      a_il_tono_non_torna_a_uno(), a_fuori_positivo, a_doppioni_zero]),
]

REGOLE = ("vecchia", "nuova")


# ═══════════════════════════════════════════════════════════════════════════
# IL GIUDICE — I BLOCCHI AL LORO POSTO, COME FA L'ANCORA DELLA PAGINA
# ═══════════════════════════════════════════════════════════════════════════
def purezza_tono(campioni):
    """⭐⭐ LA PUREZZA DI `07-b42`, MA IN UN TEMPO CHE SI PUO' SPENDERE.

    `07-b42.giudica()` fa **1901 Goertzel** (100…2000 Hz) su 48 000 campioni:
    91 milioni di giri di ciclo in Python puro, cioe' ~un minuto **per
    finestra**.  ⚠ Con otto finestre per giro e dodici giri sarebbero quattro
    ore, e il lucchetto del `netem` dura quindici minuti.

    ⭐ E NON SERVE UN'APPROSSIMAZIONE, PERCHE' SONO LA STESSA COSA.  Un Goertzel
       a frequenza INTERA `f` su **esattamente 48 000 campioni** e' il termine
       `f` della DFT a 48 000 punti: il passo dei bin e' 48000/48000 = **1 Hz**,
       quindi il bin `f` cade esattamente su `f` Hz.  ⇒ Una `rfft` da' gli
       stessi 1901 moduli quadri in millisecondi.
    ⛔ E non si crede a questa uguaglianza sulla parola: `--certifica` la
       CONFRONTA con `07-b42.giudica()` su un caso vero e pretende che
       coincidano a quattro decimali.  Se numpy non c'e' o non coincidono, si
       ripiega su `07-b42` e si DICHIARA (una finestra sola).
    """
    m = len(campioni)
    if m != FREQUENZA:
        return G42.giudica([x / 32768.0 for x in campioni])
    try:
        import numpy as _np
    except ImportError:
        return G42.giudica([x / 32768.0 for x in campioni])
    x = _np.asarray(campioni, dtype=_np.float64) / 32768.0
    X = _np.fft.rfft(x)
    p = _np.abs(X[100:2001]) ** 2
    somma = float(p.sum())
    if somma <= 0:
        return {"esito": "GIUDICATO", "campioni": m, "hz": 0, "purezza": None,
                "rms": 0.0}
    k = int(p.argmax())
    return {"esito": "GIUDICATO", "campioni": m, "hz": 100 + k,
            "rms": round(float(_np.sqrt((x * x).mean())), 4),
            "purezza": round(float(p[k] / somma), 4)}


def scaletta(percorso, finestre=8, finestra_s=1):
    """⭐ La tela di silenzio e i blocchi messi a `base + istante`.

    ⛔ NON si incollano in ordine d'arrivo: sarebbe il giudizio sbagliato per
       la regola nuova, che i blocchi arretrati li TIENE — incollarli dove
       capita metterebbe il passato in mezzo al presente e accuserebbe la cura
       di un difetto che e' del giudice.

    ⚠ I buchi restano SILENZIO, e devono: un buco e' quel che si sente, e
      ricucire i bordi lo renderebbe invisibile al giudice del tono.
    """
    if not os.path.exists(percorso) or os.path.getsize(percorso) == 0:
        return {"esito": "NIENTE DA GIUDICARE — il JSONL non c'e' o e' vuoto"}
    blocchi, visti, dop = [], set(), 0
    fuori_arrivo, massimo = 0, None
    for r in open(percorso):
        r = r.strip()
        if not r:
            continue
        d = json.loads(r)
        if d.get("codec") != 2:
            continue                     # ⛔ solo PCM: l'Opus non si giudica cosi'
        ist = int(d["istante"])
        if ist in visti:
            dop += 1
            continue
        visti.add(ist)
        # ⭐ I sorpassi contati sul DATO, non sul contatore del cliente: e' la
        #    seconda gamba della prova che il profilo riordina davvero.
        if massimo is not None and ist < massimo:
            fuori_arrivo += 1
        massimo = ist if massimo is None else max(massimo, ist)
        blocchi.append((ist, base64.b64decode(d["byte"])))
    if len(blocchi) < 200:
        return {"esito": "NIENTE DA GIUDICARE — %d blocchi" % len(blocchi),
                "blocchi": len(blocchi)}
    base = min(i for i, _ in blocchi)
    fine = max(i for i, _ in blocchi)
    n_tot = int(round((fine - base) / 1e6 * FREQUENZA)) + (FREQUENZA * PASSO_PCM_US // 1000000)
    if n_tot <= 0 or n_tot > FREQUENZA * 3600:
        return {"esito": "NIENTE DA GIUDICARE — linea del tempo assurda (%d)" % n_tot}
    tela = [0] * n_tot
    pieno = bytearray(n_tot)
    for ist, b in blocchi:
        off = int(round((ist - base) / 1e6 * FREQUENZA))
        n = len(b) // (2 * CANALI)
        if n <= 0 or off < 0 or off + n > n_tot:
            continue
        v = struct.unpack("<%dh" % (n * CANALI), b[:n * CANALI * 2])
        sx = v[0::CANALI]
        for k in range(n):
            tela[off + k] = sx[k]
            pieno[off + k] = 1
    coperti = sum(pieno)
    copertura = coperti / float(n_tot)
    # ⭐ La purezza su PIU' finestre, e si prende la mediana: una finestra sola
    #   prende un caso.  ⚠ Le finestre sono equidistanti, non scelte.
    n = finestra_s * FREQUENZA
    purezze, hz_visti = [], []
    if n_tot >= n:
        posti = ([0] if finestre <= 1 else
                 [int(k * (n_tot - n) / (finestre - 1)) for k in range(finestre)])
        for i in posti:
            g = purezza_tono(tela[i:i + n])
            if g.get("purezza") is not None:
                purezze.append(g["purezza"])
                hz_visti.append(g.get("hz"))
    purezze_ord = sorted(purezze)
    med = (purezze_ord[len(purezze_ord) // 2] if purezze_ord else None)
    return {"esito": "GIUDICATO", "blocchi": len(blocchi),
            "doppioni_scaletta": dop, "fuori_arrivo": fuori_arrivo,
            "durata_s": round(n_tot / float(FREQUENZA), 3),
            "campioni_scritti": coperti, "campioni_totali": n_tot,
            "copertura": round(copertura, 5),
            "purezza_tono": None if med is None else round(med, 4),
            "purezza_tono_min": None if not purezze_ord else round(purezze_ord[0], 4),
            "purezza_tono_max": None if not purezze_ord else round(purezze_ord[-1], 4),
            "finestre": len(purezze_ord),
            "hz": hz_visti[len(hz_visti) // 2] if hz_visti else None}


# ⛔⛔ QUI C'ERA UN TERZO GIUDIZIO, E SI E' TOLTO — 23 agosto 2026.
#
#      `07-b64-orecchio.py` incolla i blocchi in ordine d'ARRIVO e ne misura la
#      purezza del tono.  Serviva a restare confrontabile col `[M]` di
#      `pagina.html` riga 6474 (purezza 0,175).  ⇒ Due ragioni per toglierlo, e
#      la prima da sola basta:
#
#        1. ⛔ quel `[M]` non e' un riferimento valido: la sua definizione non e'
#           nota (vedi il riquadro dei predicati), e confrontarsi con un numero
#           di cui non si conosce la definizione fabbrica trionfi;
#        2. ⚠ costa **un minuto per giro** (1901 Goertzel in Python puro su
#           48 000 campioni), cioe' dodici minuti DENTRO il lucchetto del
#           `netem` — che dura quindici e ha altri due agenti in coda.
#
# ⭐ E incollare in ordine d'arrivo sarebbe per giunta il giudizio SBAGLIATO per
#    la regola nuova, che i blocchi arretrati li TIENE: metterebbe il passato in
#    mezzo al presente e accuserebbe la cura di un difetto del giudice.


# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE PARLA CON LA MACCHINA DI PROVA
# ═══════════════════════════════════════════════════════════════════════════
def root(comando, tetto=300):
    return RETE.root(comando, tetto)


def netem_pacchetti():
    """I pacchetti che il nodo `netem` ha DAVVERO visto passare.

    ⛔ E' il sostituto del contatore `reordered`, che su questa macchina non
       esiste (`[M]`: iproute2 6.15.0, `grep -ac reordered /usr/sbin/tc` = 0).
       ⚠ Non dice «quanti ne ha riordinati»; dice «il filtro u32 morde», che e'
       la condizione senza la quale il profilo non esiste affatto.
    """
    rc, out, _ = root("/usr/sbin/tc -s qdisc show dev lo")
    dentro, ultimo = False, None
    for riga in out.split("\n"):
        s = riga.strip()
        if s.startswith("qdisc"):
            dentro = ("netem" in s)
            continue
        if dentro:
            m = re.search(r"Sent\s+(\d+)\s+bytes\s+(\d+)\s+pkt", s)
            if m:
                ultimo = int(m.group(2))
                dentro = False
    return ultimo


def righe_registro():
    rc, out, _ = root("wc -l < %s/registro.log 2>/dev/null || echo 0" % LAV)
    try:
        return int(out.strip())
    except Exception:
        return 0


def conti_del_server(riga0):
    """⛔ «la rete l'ha perso» e «il server non l'ha mai spedito» danno lo stesso
       numero dal lato del cliente.  Qui si legge il conto del SERVER, e solo
       da `riga0` in poi, cosi' e' di QUESTO giro."""
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'audio di .*conto "
                      "finale' | tail -1" % (riga0 + 1, LAV))
    r = out.strip()
    if not r:
        return {"esito": "NIENTE DA LEGGERE — nessun «conto finale» in questo giro"}
    m = re.search(r"(\d+) blocchi spediti, (\d+) buttati.*?(\d+) rifiutati.*?"
                  r"(\d+) RIMANDATI", r)
    if not m:
        return {"esito": "riga trovata ma illeggibile", "riga": r[:160]}
    return {"spediti": int(m.group(1)), "buttati": int(m.group(2)),
            "rifiutati": int(m.group(3)), "rimandati": int(m.group(4))}


def testimone_del_server(riga0):
    """⭐⭐ IL TESTIMONE DEL RIORDINO CHE NON SA NIENTE DELLA CURA.

    La riga `rete-quic` del registro porta, dal 23 agosto 2026:
        dgram_persi= dgram_persi_d= dgram_ok= dgram_falsi= dgram_falsi_d=
    ⛔ Si legge solo da `riga0` in poi, cosi' e' di QUESTO giro; e i contatori
       sono cumulativi PER CONNESSIONE, quindi si prende il massimo della
       finestra — non la somma, che conterebbe ogni riga da capo.
    ⚠ Se il binario e' piu' vecchio del testimone, i campi non ci sono: si
      torna `None`, non zero (`CODER.md` §3.10)."""
    rc, out, _ = root("tail -n +%d %s/registro.log 2>/dev/null | grep -a "
                      "'rete-quic ' | tail -40" % (riga0 + 1, LAV))
    righe = [r for r in out.split("\n") if "rete-quic " in r]
    if not righe:
        return {"esito": "NIENTE DA LEGGERE — nessuna riga «rete-quic» in "
                         "questo giro", "righe": 0}
    fuori = {"righe": len(righe)}
    for campo in ("dgram_persi", "dgram_ok", "dgram_falsi"):
        valori = []
        for r in righe:
            m = re.search(r"\b%s=(\d+)" % campo, r)
            if m:
                valori.append(int(m.group(1)))
        fuori[campo] = max(valori) if valori else None
    for campo in ("dgram_persi_d", "dgram_falsi_d"):
        valori = []
        for r in righe:
            m = re.search(r"\b%s=(\d+)" % campo, r)
            if m:
                valori.append(int(m.group(1)))
        # ⚠ I `_d` sono differenze fra una riga e l'altra: qui si SOMMANO.
        fuori[campo] = sum(valori) if valori else None
    if fuori.get("dgram_falsi") is None:
        fuori["esito"] = ("il binario NON ha il testimone dei datagram "
                          "(nessun `dgram_falsi=` sulla riga rete-quic)")
    return fuori


# ⛔⛔ I NOMI SI COPIANO DA COME IL CLIENTE LI STAMPA, NON DA COME SI CHIAMANO
#      DENTRO.  `01-b3-cliente.py:606` stampa:
#
#        [audio] scartati — corti 0 · tipo 0 · prefisso 0 · vecchi 1900
#        [audio] riordino — regola nuova · sul filo 5001 · ricevuti 5001 ·
#                           consegnati 4991 · PUREZZA 0.9980 (pagina 0.9980)
#        [audio] riordino — tardivi 6 · fuori 812 · rec 790 · dop 0 ·
#                           mancati 1 volte 1 · riarmi 0 · passo 5000us
#
#      ⚠ «sul filo» ha uno SPAZIO, `PUREZZA` e' maiuscola, e i quattro della
#        fase 9 si chiamano `tardivi/fuori/rec/dop`, non coi nomi lunghi della
#        pagina.  ⛔ Una regex costruita sui nomi interni non avrebbe dato un
#        errore: avrebbe dato `None` su tutto, cioe' un banco che TACE su ogni
#        predicato e non da' ne' verde ne' rosso.
DA_LEGGERE = {
    "sul_filo":       r"sul filo\s+(\d+)",
    "ricevuti":       r"·\s*ricevuti\s+(\d+)\s*·",
    "consegnati":     r"consegnati\s+(\d+)",
    "vecchi":         r"vecchi\s+(\d+)",
    "corti":          r"corti\s+(\d+)",
    "tipo":           r"tipo\s+(\d+)",
    "prefisso":       r"prefisso\s+(\d+)",
    "tardivi":        r"tardivi\s+(\d+)",
    "fuori":          r"fuori\s+(\d+)",
    "rec":            r"rec\s+(\d+)",
    "dop":            r"dop\s+(\d+)",
    "mancati":        r"mancati\s+(\d+)",
    "mancati_volte":  r"mancati\s+\d+\s+volte\s+(\d+)",
    "riarmi":         r"riarmi\s+(\d+)",
    "passo_us":       r"passo\s+(\d+)us",
}
DA_LEGGERE_DEC = {
    "purezza":        r"PUREZZA\s+([0-9]+\.[0-9]+)",
    "purezza_pagina": r"\(pagina\s+([0-9]+\.[0-9]+)\)",
}


def _num(testo, nome):
    """⛔ Si prende l'ULTIMA occorrenza — la riga dei conti arriva dopo tutte
       le altre — e un `None` vuol dire «non l'ho letto», non «zero»."""
    trovato = None
    for m in re.finditer(DA_LEGGERE.get(nome, r"\b%s\b\s+(\d+)" % re.escape(nome)),
                         testo):
        trovato = int(m.group(1))
    return trovato


def _dec(testo, nome):
    trovato = None
    for m in re.finditer(DA_LEGGERE_DEC.get(nome, r"\b%s\b\s+([0-9.]+)" % re.escape(nome)),
                         testo):
        trovato = float(m.group(1))
    return trovato


def _regola_dichiarata(testo):
    """⭐⭐ LA PROVA CHE LA REGOLA ERA IN VIGORE IN QUESTO GIRO.

    ⛔ `LEZIONI.md` E1: «scritto non e' in vigore».  Che `--audio-regola` esista
       nell'aiuto non dice che il cliente l'abbia USATA — un argomento accettato
       e ignorato darebbe due giri identici, e il banco riferirebbe «nessuna
       differenza», che e' la stessa faccia di «la cura non serve» e la
       conclusione opposta.  ⇒ Il cliente stampa `regola <nome>` sulla riga dei
       conti, e QUI si controlla che sia quella che ho chiesto."""
    trovata = None
    for m in re.finditer(r"regola\s+(vecchia|nuova)\b", testo):
        trovata = m.group(1)
    return trovata


def cliente_ha_interruttore():
    """⛔ IL CONTROLLO CHE EVITA IL VERDE FALSO PIU' PROBABILE DI QUESTO BANCO.

       Se `--audio-regola` non c'e' ancora, i due giri userebbero la stessa
       regola: il banco vedrebbe due numeri uguali e riferirebbe «nessuna
       differenza».  ⚠ E' la stessa faccia di «la cura non serve» — e la
       conclusione opposta.  ⇒ Si controlla, e se non c'e' ci si FERMA.

       ⭐ E si controlla la COPIA CHE GIRA (dentro il contenitore), non quella
          del portatile: «l'ho scritto» non e' «e' in vigore» (`LEZIONI.md` E1).
    """
    esito = {}
    locale = os.path.join(QUI, "01-b3-cliente.py")
    try:
        t = open(locale, encoding="utf-8", errors="replace").read()
        esito["portatile"] = "--audio-regola" in t
    except Exception as e:
        esito["portatile"] = False
        esito["portatile_perche"] = str(e)
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root "
                        "'python3 %s/banchi/01-b3-cliente.py --help 2>&1 | "
                        "grep -c -- --audio-regola'" % DENTRO_ALB, 180)
    conta = 0
    for r in (out + err).split("\n"):
        if r.strip().isdigit():
            conta = int(r.strip())
    esito["dentro_aiuto"] = conta > 0
    esito["dentro"] = conta > 0
    return esito


def terreno_controlla():
    """⛔ Il banco si rifiuta di misurare su un terreno che non e' il suo."""
    log("IL TERRENO — porta %d · utente %s (uid %d) · albero %s" % (PORTA, UTENTE, UID_B, ALB))
    guai = []
    rc, out, _ = root("id %s >/dev/null 2>&1 && echo si || echo no" % UTENTE)
    if "si" not in out:
        guai.append("l'utente «%s» non esiste — PORTA=%d UTENTE=%s UID_B=%d "
                    "PAROLA_UTENTE=%s ALBERO=%s LAV=%s bash banchi/07-b64-terreno.sh utente"
                    % (UTENTE, PORTA, UTENTE, UID_B, PAROLA_UTENTE, ALB, LAV))
    rc, out, _ = root("test -s %s/parola && echo si || echo no" % LAV)
    if "si" not in out:
        guai.append("manca %s/parola (0600): D12 vieta la parola in argv" % LAV)
    rc, out, _ = root("test -x %s/src/remotix && echo si || echo no" % ALB)
    if "si" not in out:
        guai.append("l'albero «%s» non ha un binario: `... bash banchi/07-b64-terreno.sh porta`" % ALB)
    rc, out, _ = root("ss -uln 2>/dev/null | grep -c ':%d ' || true" % PORTA)
    mio = out.strip()
    if mio == "0":
        guai.append("nessuno ascolta sulla %d: `... bash banchi/07-b64-terreno.sh accendi`" % PORTA)
    # ⛔ Le porte degli altri agenti si CONTANO, non si toccano.
    conto = []
    for p in VIETATE:
        rc, o, _ = root("ss -uln 2>/dev/null | grep -c ':%s ' || true" % p)
        conto.append("%s:%s" % (p, o.strip()))
    inf("porte VIETATE (si contano, non si toccano): %s" % " ".join(conto))
    inf("il mio server sulla %d: %s ascoltatore/i" % (PORTA, mio))
    rc, out, _ = root("/usr/sbin/tc qdisc show dev %s" % VIETATA_IFACE)
    inf("%s (ssh + la 7730 dell'utente) — NON si tocca: %s"
        % (VIETATA_IFACE, out.strip().split("\n")[0]))
    rc, out, _ = root("uptime")
    inf("carico: %s" % out.strip()[-42:])

    interr = cliente_ha_interruttore()
    if interr.get("dentro"):
        ok("il cliente ha `--audio-regola` (nel contenitore, letto da `--help`)")
    else:
        guai.append("⛔⛔ IL CLIENTE NON HA `--audio-regola` (portatile: %s, "
                    "contenitore: %s).  NON misuro: due giri con la stessa "
                    "regola darebbero «nessuna differenza», che e' la stessa "
                    "faccia di «la cura non serve» e la conclusione opposta"
                    % (interr.get("portatile"), interr.get("dentro")))
    for g in guai:
        ko(g)
    if not guai:
        ok("il terreno c'e', ed e' mio")
    return not guai


def giro(profilo, regola, secondi):
    """Un giro del cliente, con la regola scelta.  Torna i numeri, o `None`."""
    nome = "%s-%s" % (profilo, regola)
    j_fuori = os.path.join(FUORI, nome + ".jsonl")
    t_fuori = os.path.join(FUORI, nome + ".txt")
    for f in (j_fuori, t_fuori):
        try: os.remove(f)
        except Exception: pass
    riga0 = righe_registro()
    pkt0 = netem_pacchetti()
    t0 = time.time()
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec pcm "
              "--audio-regola %s --audio-scrivi %s/b77-%s.jsonl --resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, regola,
                 DENTRO_LAV, nome, secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 240)
    uscita = out + err
    open(t_fuori, "w").write(uscita)
    subprocess.run("ssh -o BatchMode=yes %s \"printf '%%s\\n' '%s' | sudo -S -p '' "
                   "cat %s/b77-%s.jsonl\" > %s"
                   % (RETE.MACCHINA, RETE.PAROLA_SUDO, LAV, nome, j_fuori),
                   shell=True)
    pkt1 = netem_pacchetti()
    sv = conti_del_server(riga0)
    tst = testimone_del_server(riga0)

    # ⛔ Se il cliente ha rifiutato `--audio-regola`, i suoi numeri sarebbero
    #    quelli dell'ALTRA regola: si dichiara e non si giudica.
    if "unrecognized arguments" in uscita or "invalid choice" in uscita:
        return {"esito": "IL CLIENTE HA RIFIUTATO --audio-regola %s" % regola,
                "coda": uscita[-600:]}
    # ⛔⛔ E LA REGOLA DEV'ESSERE QUELLA CHE HO CHIESTO, DETTA DAL CLIENTE.
    #     «L'ho passata» non e' «l'ha usata» (`LEZIONI.md` E1): un argomento
    #     accettato e ignorato darebbe due giri identici col nome di due.
    detta = _regola_dichiarata(uscita)
    if detta != regola:
        return {"esito": "⛔⛔ HO CHIESTO «%s» E IL CLIENTE DICE «%s»: i due "
                         "giri non sarebbero appaiati, sarebbero lo stesso giro "
                         "due volte" % (regola, detta), "coda": uscita[-600:]}

    sc = scaletta(j_fuori)
    n = {
        "profilo": profilo, "regola": regola, "secondi": round(time.time() - t0, 1),
        # ⭐ I NOMI DELLA PAGINA, che sono l'interfaccia concordata col cliente.
        #   ⛔ `sul_filo` si conta PRIMA del vaglio e `consegnati` DOPO: e' la
        #      coppia che rende `purezza` una frazione con un denominatore che
        #      non si muove con la regola.
        "sul_filo": _num(uscita, "sul_filo"),
        "consegnati": _num(uscita, "consegnati"),
        "ricevuti": _num(uscita, "ricevuti"),
        "vecchi": _num(uscita, "vecchi"),
        "corti": _num(uscita, "corti"),
        "tipo": _num(uscita, "tipo"),
        "prefisso": _num(uscita, "prefisso"),
        "tardivi": _num(uscita, "tardivi"),
        "fuori": _num(uscita, "fuori"),
        "dop": _num(uscita, "dop"),
        "rec": _num(uscita, "rec"),
        "mancati": _num(uscita, "mancati"),
        # ⛔ `purezza` = consegnati/sul_filo, e la conta il cliente.
        #   ⚠ `purezza_pagina` (suonati/ricevuti) e' CIECA — lo scarto fa
        #     `continue` prima di `ricevuti++`, quindi vale ~1 con tutt'e due le
        #     regole: si riporta solo per confronto, e dichiarata tale.
        "purezza": _dec(uscita, "purezza"),
        "purezza_pagina": _dec(uscita, "purezza_pagina"),
        "riarmi": _num(uscita, "riarmi"),
        "regola_dichiarata": _regola_dichiarata(uscita),
        "spediti_server": sv.get("spediti"),
        # ⛔ `rifiutati` = ngtcp2 non li ha messi sul filo (finestra chiusa).
        #    ⚠ Non sono perdita della rete, e confonderli con quella e' R13.
        "rifiutati_server": sv.get("rifiutati"),
        "buttati_server": sv.get("buttati"),
        "server": sv,
        # ⭐ Il testimone dell'ALTRO capo del filo, che non sa niente della cura.
        "dgram_falsi": tst.get("dgram_falsi"),
        "dgram_falsi_d": tst.get("dgram_falsi_d"),
        "dgram_persi": tst.get("dgram_persi"),
        "dgram_ok": tst.get("dgram_ok"),
        "testimone": tst,
        "netem_pkt": (None if (pkt0 is None or pkt1 is None) else max(0, pkt1 - pkt0)),
        "scaletta": sc,
        "jsonl": j_fuori,
    }
    # ⭐ E la SECONDA GAMBA, presa dai campioni e non dall'aritmetica del
    #   cliente: la copertura della linea del tempo e la purezza del TONO.
    n["purezza_tono"] = sc.get("purezza_tono")
    n["copertura"] = sc.get("copertura")
    n["blocchi"] = sc.get("blocchi")
    n["fuori_arrivo"] = sc.get("fuori_arrivo")
    # ⛔ E SE IL CLIENTE NON HA DETTO LA PUREZZA, la si RICOSTRUISCE dai suoi
    #    contatori con la stessa definizione — e si dichiara che e' ricostruita.
    #    ⚠ Non si ripiega sulla purezza del tono: e' un'altra grandezza, e
    #      scambiarle darebbe un numero plausibile con il nome sbagliato.
    if n["purezza"] is None and n.get("consegnati") and n.get("sul_filo"):
        n["purezza"] = round(n["consegnati"] / float(n["sul_filo"]), 5)
        n["purezza_ricostruita"] = True
    # ⛔⛔ E QUI SI CONTROLLA CHE I NUMERI CHE I PREDICATI LEGGERANNO CI SIANO
    #     DAVVERO — sulle chiavi del dizionario, non su quelle che credevo di
    #     leggere.  ⚠ `[M]` 23 agosto 2026: il primo giro ha stampato `vecchi -
    #     tard - fuori - rec - dop -` e il banco NON si e' fermato, perche' il
    #     controllo interrogava `_num(uscita, "vecchi")` (giusto) mentre il
    #     dizionario chiedeva `scartati_vecchi` (sbagliato).  ⇒ Un controllo che
    #     non guarda la stessa cosa del codice che protegge non protegge niente.
    OBBLIGATORI = ("sul_filo", "consegnati", "vecchi", "tardivi", "fuori",
                   "rec", "dop", "mancati", "purezza")
    manca = [k for k in OBBLIGATORI if n.get(k) is None]
    if manca:
        return {"esito": "⛔ I CONTATORI DEL CLIENTE NON SI SONO LETTI (%s): le "
                         "regex di DA_LEGGERE non agganciano piu' la sua uscita"
                         % ", ".join(manca), "coda": uscita[-900:]}
    return n


def riga_numeri(n):
    def q(x, f="%s"):
        return "-" if x is None else (f % x)
    return ("%-8s PUREZZA %s  (tono %s · cop %s · pagina %s) | filo %s cons %s "
            "vecchi %s tard %s fuori %s (jsonl %s) rec %s dop %s manc %s | "
            "netem %s pkt | srv %s spediti, dgram_falsi %s"
            % (n["regola"], q(n.get("purezza"), "%.4f"),
               q(n.get("purezza_tono"), "%.3f"), q(n.get("copertura"), "%.4f"),
               q(n.get("purezza_pagina"), "%.3f"),
               q(n.get("sul_filo")), q(n.get("consegnati")), q(n.get("vecchi")),
               q(n.get("tardivi")), q(n.get("fuori")), q(n.get("fuori_arrivo")),
               q(n.get("rec")), q(n.get("dop")), q(n.get("mancati")),
               q(n.get("netem_pkt")), q(n.get("spediti_server")),
               q(n.get("dgram_falsi"))) + " rifiut %s" % q(n.get("rifiutati_server")))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ L'AUTOPROVA: I PREDICATI DEVONO SAPER DARE ROSSO
#
# ⛔ «Un predicato mai visto fallire non e' un predicato.»  Qui si fabbricano i
#    numeri — quelli buoni e quelli cattivi — e si pretende che ogni predicato
#    dia il verdetto scritto accanto.  Se l'autoprova non e' verde, a nessun
#    numero di questo banco si crede.
# ═══════════════════════════════════════════════════════════════════════════
def _n(**kw):
    base = {"purezza": None, "purezza_tono": None, "purezza_pagina": None,
            "copertura": None, "sul_filo": None, "consegnati": None,
            "vecchi": None, "tardivi": None, "fuori": None, "fuori_arrivo": None,
            "dop": None, "rec": None, "mancati": None, "ricevuti": None,
            "netem_pkt": None, "spediti_server": None,
            "dgram_falsi": None, "dgram_falsi_d": None}
    base.update(kw)
    return base


def certifica():
    print("⭐ AUTOPROVA DEI PREDICATI — l'atteso e' scritto PRIMA, e i numeri")
    print("   sono FABBRICATI: quel che si prova qui e' che sanno dare ROSSO.\n")

    # Un giro «vecchia» su un profilo che morde, e il suo gemello curato.
    v_rotto = _n(purezza=0.62, sul_filo=5000, consegnati=3100, vecchi=1900,
                 copertura=0.62, purezza_tono=0.41, netem_pkt=12000,
                 spediti_server=5000, dgram_falsi=31, mancati=1)
    u_sano = _n(purezza=0.9982, sul_filo=5000, consegnati=4991, vecchi=3,
                tardivi=6, fuori=812, fuori_arrivo=810, dop=0, rec=790,
                mancati=1, copertura=0.9985, purezza_tono=0.997,
                netem_pkt=12100, spediti_server=5000, dgram_falsi=29)

    casi = [
        # ── il controllo positivo: «il profilo morde?» ──────────────────────
        ("controllo positivo · il profilo MORDE (purezza 0,62 · 1900 buttati)",
         a_crolla_con_vecchia(0.90, 100), v_rotto, u_sano, True),
        ("⚠ MUTO  · il profilo NON morde (purezza 0,991 · 3 buttati) ⇒ NON "
         "giudico, e non e' un verde",
         a_crolla_con_vecchia(0.90, 100),
         _n(purezza=0.991, vecchi=3, sul_filo=5000), u_sano, None),
        ("⚠ MUTO  · morde poco: purezza 0,45 ma solo 20 buttati",
         a_crolla_con_vecchia(0.90, 100),
         _n(purezza=0.45, vecchi=20, sul_filo=5000), u_sano, None),
        ("⛔ ROSSO · CONTRADDIZIONE: 1900 buttati E purezza 0,99",
         a_crolla_con_vecchia(0.90, 100),
         _n(purezza=0.99, vecchi=1900, sul_filo=5000), u_sano, False),
        ("⚠ MUTO  · la purezza della vecchia non si e' letta",
         a_crolla_con_vecchia(0.90, 100), _n(vecchi=1900), u_sano, None),

        # ── la cura risale ─────────────────────────────────────────────────
        ("la cura risale (purezza 0,9982 · tardivi 6 su 5000 sul filo)",
         a_risale_con_nuova(), v_rotto, u_sano, True),
        ("⛔ ROSSO · la cura NON risale (purezza 0,31)",
         a_risale_con_nuova(), v_rotto,
         _n(purezza=0.31, tardivi=4, sul_filo=5000), False),
        ("⛔ ROSSO · risale ma il danno si e' spostato sui tardivi (900/5000)",
         a_risale_con_nuova(), v_rotto,
         _n(purezza=0.99, tardivi=900, sul_filo=5000), False),
        ("⚠ MUTO  · la nuova non ha detto scartati_tardivi",
         a_risale_con_nuova(), v_rotto, _n(purezza=0.99, sul_filo=5000), None),

        # ── la seconda gamba: i campioni, non l'aritmetica del cliente ──────
        ("⭐ il TONO conferma (cop 0,62 → 0,9985 · tono 0,41 → 0,997)",
         a_il_tono_conferma(), v_rotto, u_sano, True),
        ("⛔ ROSSO · il cliente dice 0,998 ma i CAMPIONI dicono che la "
         "copertura non e' salita",
         a_il_tono_conferma(), _n(copertura=0.62, purezza_tono=0.41),
         _n(copertura=0.63, purezza_tono=0.42), False),
        ("⛔ ROSSO · la copertura sale ma il tono PEGGIORA",
         a_il_tono_conferma(), _n(copertura=0.62, purezza_tono=0.90),
         _n(copertura=0.99, purezza_tono=0.55), False),
        ("⚠ MUTO  · la copertura non si e' misurata",
         a_il_tono_conferma(), _n(), _n(), None),

        # ── l'onesta' della cura ───────────────────────────────────────────
        ("⭐ l'onesta' della cura: fuori_ordine 812 > 0",
         a_fuori_positivo, v_rotto, u_sano, True),
        ("⛔⭐ ROSSO · purezza 0,999 MA fuori_ordine 0: non sta curando, "
         "sta non vedendo il riordino",
         a_fuori_positivo, v_rotto,
         _n(purezza=0.999, fuori=0, tardivi=0, sul_filo=5000), False),
        ("⚠ MUTO  · il cliente non ha detto fuori_ordine",
         a_fuori_positivo, v_rotto, _n(purezza=0.999), None),

        ("doppioni 0 con tutt'e due", a_doppioni_zero, v_rotto, u_sano, True),
        ("⛔ ROSSO · 7 doppioni con la regola nuova", a_doppioni_zero, v_rotto,
         _n(dop=7), False),
        ("⛔ ROSSO · 2 doppioni con la regola vecchia", a_doppioni_zero,
         _n(dop=2), _n(dop=0), False),

        # ── il denominatore ────────────────────────────────────────────────
        ("liscio · le due regole coincidono (0,9990 / 0,9992)",
         a_le_due_coincidono(), _n(purezza=0.9990), _n(purezza=0.9992), True),
        ("⛔ ROSSO · sul caso facile le due regole DIVERGONO (0,999 / 0,60)",
         a_le_due_coincidono(), _n(purezza=0.999), _n(purezza=0.60), False),
        ("⛔ ROSSO · coincidono ma tutt'e due basse (0,40 / 0,41)",
         a_le_due_coincidono(), _n(purezza=0.40), _n(purezza=0.41), False),
        ("liscio · nessun riordino su `lo` senza disciplina",
         a_niente_riordino_sul_liscio, _n(vecchi=0), _n(fuori=0), True),
        ("⛔ ROSSO · sul liscio ci sono 40 sorpassi: a riordinare e' altro",
         a_niente_riordino_sul_liscio, _n(vecchi=0), _n(fuori=40), False),

        # ── la perdita si dichiara, e il tono non torna a 1 ─────────────────
        ("casa cattiva · la perdita dai DUE CAPI (2879 spediti, 2813 sul filo "
         "= 2,29 %)", a_perdita_dichiarata(0.02), v_rotto,
         _n(spediti_server=2879, sul_filo=2813, rifiutati_server=2134,
            mancati=2183), True),
        ("⭐⛔ ROSSO · il caso VERO del 23 agosto letto col numero SBAGLIATO: "
         "`mancati` 2183 su 4996 sarebbe il 43,7 %",
         a_perdita_dichiarata(0.437), v_rotto,
         _n(spediti_server=2879, sul_filo=2813, rifiutati_server=2134,
            mancati=2183), False),
        ("⛔ ROSSO · «2 % di perdita» ma sul filo e' arrivato TUTTO",
         a_perdita_dichiarata(0.02), v_rotto,
         _n(spediti_server=5000, sul_filo=5000), False),
        ("⛔ ROSSO · il cliente ne ha visti PIU' di quanti il server ne ha spediti",
         a_perdita_dichiarata(0.02), v_rotto,
         _n(spediti_server=4000, sul_filo=4200), False),
        ("⚠ MUTO  · «spediti» del server non si e' letto",
         a_perdita_dichiarata(0.02), v_rotto, _n(sul_filo=5000), None),
        ("col 2 % di perdita il tono NON torna a 1 (0,93)",
         a_il_tono_non_torna_a_uno(), v_rotto, _n(purezza_tono=0.93), True),
        ("⛔ ROSSO · col 2 % di perdita il tono torna a 0,999: cieco il giudice, "
         "non guarita la rete",
         a_il_tono_non_torna_a_uno(), v_rotto, _n(purezza_tono=0.999), False),

        # ── i due capi del filo ────────────────────────────────────────────
        ("⭐ i due capi: il SERVER conferma il riordino (29+31 dgram_falsi)",
         a_riordino_dai_due_capi, v_rotto, u_sano, True),
        ("⭐ il server tace ma i DATI vedono il riordino (fuori 812): verde, "
         "col prezzo dichiarato",
         a_riordino_dai_due_capi, _n(vecchi=1004, dgram_falsi=0),
         _n(dgram_falsi=0, fuori=812, fuori_arrivo=810), True),
        ("⚠ MUTO  · NESSUNO dei tre capi vede riordino: il profilo non morde",
         a_riordino_dai_due_capi, _n(vecchi=0, dgram_falsi=0),
         _n(dgram_falsi=0, fuori=0, fuori_arrivo=0, purezza=0.999), None),
        ("i due capi concordano", a_capi_non_si_contraddicono, v_rotto, u_sano, True),
        ("⛔ ROSSO · il server vede 29 riordini, il ricevente ZERO",
         a_capi_non_si_contraddicono, v_rotto,
         _n(dgram_falsi=29, fuori=0, fuori_arrivo=0), False),
        ("il liscio: nessuno dei due vede riordino", a_capi_non_si_contraddicono,
         _n(dgram_falsi=0), _n(dgram_falsi=0, fuori=0, fuori_arrivo=0), True),
        ("⚠ MUTO  · il binario non ha il testimone dei datagram",
         a_capi_non_si_contraddicono, _n(), _n(fuori=5), None),

        # ── il terreno della misura ────────────────────────────────────────
        ("il netem ha visto il traffico (12000 + 12100 pkt)",
         a_netem_ha_visto, v_rotto, u_sano, True),
        ("⚠ MUTO  · il netem non ha visto NIENTE: il filtro u32 non morde",
         a_netem_ha_visto, _n(netem_pkt=0), _n(netem_pkt=0), None),
        ("il server ha spedito nei due giri", a_server_ha_spedito, v_rotto, u_sano, True),
        ("⛔ ROSSO · il server non ha spedito: il rosso non e' della rete",
         a_server_ha_spedito, _n(spediti_server=0), _n(spediti_server=0), False),
        ("⚠ MUTO  · il «conto finale» del server non si e' letto",
         a_server_ha_spedito, _n(), _n(), None),
    ]

    verde, rossi, muti = True, 0, 0
    for nome, pred, v, u, atteso in casi:
        passa, perche = pred(v, u)
        buono = (passa is atteso) if (atteso is None or passa is None) else (passa == atteso)
        verde = verde and buono
        if atteso is False:
            rossi += 1
        if atteso is None:
            muti += 1
        print("  %-4s %-70s atteso %-5s · visto %-5s"
              % ("OK" if buono else "⛔NO", nome[:70], atteso, passa))
        if not buono:
            print("        perche': %s" % perche)

    # ═══ IL GIUDICE DEI CAMPIONI SI CERTIFICA ANCHE LUI ════════════════════
    print()
    print("⭐ IL GIUDICE DEI CAMPIONI, su audio FABBRICATO:")
    import random, tempfile
    amp = 0.5 * 32767
    tmp = tempfile.mkdtemp(prefix="b77-cert-")
    camp = FREQUENZA * PASSO_PCM_US // 1000000

    def fabbrica(percorso, buttane, mescola, seme=77):
        """Blocchi PCM da 5 ms di tono a 440 Hz, `istante` ogni 5000 us."""
        random.seed(seme)
        righe = []
        for k in range(1400):                 # 7 s
            if buttane and random.random() < buttane:
                continue                      # ⛔ il blocco NON entra: e' un buco
            n0 = k * camp
            b = bytearray()
            for i in range(camp):
                x = int(amp * math.sin(2 * math.pi * HZ * (n0 + i) / FREQUENZA))
                b += struct.pack("<hh", x, x)
            righe.append({"istante": 1000000 + k * PASSO_PCM_US, "codec": 2,
                          "byte": base64.b64encode(bytes(b)).decode()})
        if mescola:
            # ⭐ Il riordino d'ARRIVO: le righe si scambiano a coppie, e il
            #   giudice deve restare INDIFFERENTE — mette i blocchi al posto che
            #   dice l'`istante`, non quello in cui sono scritti.  ⛔ Se non
            #   fosse indifferente, accuserebbe la cura di un difetto suo.
            for i in range(0, len(righe) - 1, 2):
                righe[i], righe[i + 1] = righe[i + 1], righe[i]
        with open(percorso, "w") as f:
            for r in righe:
                f.write(json.dumps(r) + "\n")
        return percorso

    #  (nome, buttane, mescola, copertura attesa ±0,02, tono atteso [min,max])
    prove = [
        ("0-sano — tutti i blocchi, in ordine", 0.0, False, 1.00, (0.95, 1.0)),
        ("1-⭐ mescolato — stessi blocchi, ARRIVO fuori sequenza",
         0.0, True, 1.00, (0.95, 1.0)),
        ("2-⛔ 5 % dei blocchi buttati", 0.05, False, 0.95, (0.0, 0.99)),
        ("3-⛔ 20 % buttati (la regola vecchia sotto il jitter)",
         0.20, False, 0.80, (0.0, 0.90)),
        ("4-⛔ 50 % buttati", 0.50, False, 0.50, (0.0, 0.70)),
    ]
    sani = {}
    for nome, butta, mescola, cop, (pmin, pmax) in prove:
        f = fabbrica(os.path.join(tmp, nome.split(" ")[0] + ".jsonl"), butta, mescola)
        s = scaletta(f, finestre=5)
        pt, cp = s.get("purezza_tono"), s.get("copertura")
        buono = (pt is not None and pmin <= pt <= pmax
                 and cp is not None and abs(cp - cop) <= 0.02)
        verde = verde and buono
        if pmax < 0.95:
            rossi += 1
        sani[nome[0]] = (pt, cp)
        print("  %-4s %-56s cop attesa %.2f (vista %s) · tono atteso [%.2f,%.2f] "
              "(visto %s)" % ("OK" if buono else "⛔NO", nome[:56], cop, cp,
                              pmin, pmax, pt))
    # ⭐⭐ E IL CASO CHE CONTA PIU' DI TUTTI: mescolare l'ARRIVO non deve
    #    cambiare NIENTE.  Se cambiasse, il giudice punirebbe la regola nuova
    #    per il solo fatto di tenere i blocchi arretrati.
    ug = (sani.get("0") == sani.get("1"))
    verde = verde and ug
    print("  %-4s %-56s %s"
          % ("OK" if ug else "⛔NO",
             "5-⭐⭐ il giudice e' INDIFFERENTE all'ordine d'arrivo",
             "sano %s == mescolato %s" % (sani.get("0"), sani.get("1"))))

    # ═══ E LA SCORCIATOIA DEL GIUDICE SI CONFRONTA CON `07-b42` ════════════
    #  ⛔ `purezza_tono()` usa una `rfft` al posto di 1901 Goertzel.  Sono la
    #     stessa cosa solo se il bin cade sull'Hz intero — e non ci si crede
    #     sulla parola: si confronta.
    print()
    campioni = [int(amp * math.sin(2 * math.pi * HZ * k / FREQUENZA))
                + int(0.05 * amp * math.sin(2 * math.pi * 997 * k / FREQUENZA))
                for k in range(FREQUENZA)]
    veloce = purezza_tono(campioni)
    lento = G42.giudica([x / 32768.0 for x in campioni])
    uguali = (veloce.get("hz") == lento.get("hz")
              and veloce.get("purezza") is not None
              and abs(veloce["purezza"] - lento["purezza"]) <= 1e-4)
    verde = verde and uguali
    print("  %-4s %-56s rfft %s Hz / %s  ·  07-b42 %s Hz / %s"
          % ("OK" if uguali else "⛔NO",
             "6-⭐ la scorciatoia rfft == i 1901 Goertzel di 07-b42",
             veloce.get("hz"), veloce.get("purezza"),
             lento.get("hz"), lento.get("purezza")))

    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)

    # ═══ ⛔⛔ E LE REGEX SI PROVANO SULL'USCITA VERA DEL CLIENTE ════════════
    #   Una regex che non aggancia NON da' un errore: da' `None` su tutto,
    #   cioe' un banco che tace su ogni predicato.  ⚠ E' successo davvero il
    #   23 agosto 2026: la prima stesura cercava `sul_filo`, `scartati_vecchi`,
    #   `fuori_ordine` — i nomi INTERNI — e il cliente stampa `sul filo`,
    #   `vecchi`, `fuori`.  Nessun rosso: silenzio.
    print()
    print("⭐ LE REGEX, SULL'USCITA VERA DEL CLIENTE (01-b3-cliente.py:606):")
    finta = (
        "   [audio] ricevuti 5001 · 1200240 byte di carico · codec 2\n"
        "   [audio] scartati — corti 0 · tipo 0 · prefisso 0 · vecchi 1900\n"
        "   [audio] riordino — regola nuova · sul filo 5001 · ricevuti 5001 · "
        "consegnati 4991 · PUREZZA 0.9980 (pagina 0.9980)\n"
        "   [audio] riordino — tardivi 6 · fuori 812 · rec 790 · dop 0 · "
        "mancati 1 volte 3 · riarmi 2 · passo 5000us\n"
        "   [audio] blocchi scritti in /srv/remotix/tmp/09nr2/b77.jsonl (4991)\n")
    attesi = [("sul_filo", 5001), ("consegnati", 4991), ("vecchi", 1900),
              ("tardivi", 6), ("fuori", 812), ("rec", 790), ("dop", 0),
              ("mancati", 1), ("mancati_volte", 3), ("riarmi", 2),
              ("corti", 0), ("tipo", 0), ("prefisso", 0), ("passo_us", 5000)]
    for nome, atteso in attesi:
        visto = _num(finta, nome)
        buono = (visto == atteso)
        verde = verde and buono
        if not buono:
            print("  ⛔NO  %-16s atteso %-8s visto %s" % (nome, atteso, visto))
    for nome, atteso in (("purezza", 0.9980), ("purezza_pagina", 0.9980)):
        visto = _dec(finta, nome)
        buono = (visto == atteso)
        verde = verde and buono
        if not buono:
            print("  ⛔NO  %-16s atteso %-8s visto %s" % (nome, atteso, visto))
    reg = _regola_dichiarata(finta)
    verde = verde and (reg == "nuova")
    print("  %-4s tutti i %d contatori agganciati, e la regola in vigore "
          "e' «%s»" % ("OK" if reg == "nuova" else "⛔NO",
                       len(attesi) + 2, reg))
    # ⛔ E il caso negativo: un'uscita che NON porta i contatori dev'essere
    #   riconosciuta come tale, non scambiata per «tutti a zero».
    vuota = "   [audio] ricevuti 0 · 0 byte di carico · codec (nessuno)\n"
    cieca = (_num(vuota, "sul_filo") is None and _dec(vuota, "purezza") is None
             and _regola_dichiarata(vuota) is None)
    verde = verde and cieca
    rossi += 1
    print("  %-4s ⛔ e un'uscita SENZA i contatori torna `None`, non zero"
          % ("OK" if cieca else "⛔NO"))

    print()
    if verde:
        print("⭐ AUTOPROVA VERDE — %d casi, di cui %d che DEVONO dare ROSSO e "
              "%d che devono TACERE." % (len(casi) + len(prove) + 4, rossi, muti))
        print("   ⇒ i predicati sanno bocciare e sanno rifiutarsi, e ai loro")
        print("     verdi si puo' credere.")
    else:
        print("⛔ AUTOPROVA ROSSA: i predicati NON fanno quel che dicono.")
        print("   ⇒ a nessun numero di questo banco si crede.")
    return 0 if verde else 3


# ═══════════════════════════════════════════════════════════════════════════
def misura(a):
    log("09-b77 · LA CURA DEL RIORDINO DELL'AUDIO, APPAIATA")
    inf("porta %d · utente %s (uid %d) · albero %s" % (PORTA, UTENTE, UID_B, ALB))
    inf("⛔ «%s» (ssh + la 7730) NON si tocca · netem SOLO su `lo`, filtri u32 "
        "sulla sola porta %d" % (VIETATA_IFACE, PORTA))
    inf("i due giri sono identici in tutto tranne `--audio-regola`")
    os.makedirs(FUORI, exist_ok=True)

    if not terreno_controlla():
        ko("⛔ NON misuro: il terreno non e' pronto (sopra c'e' che cosa manca)")
        return 2

    profili = [p for p in PROFILI if not a.solo or a.solo in p[0]]
    if not profili:
        ko("nessun profilo si chiama «%s»" % a.solo)
        return 2

    # ⛔ IL LUCCHETTO: il `netem` su `lo` e' uno solo per tutta la macchina.
    log("IL LUCCHETTO DEL netem")
    try:
        LUCCHETTO.prendi(CHI, secondi=a.affitto, attesa=a.attesa)
    except LUCCHETTO.NonMio as e:
        ko(str(e))
        return 2

    scadenza = time.time() + a.affitto
    esiti = []
    try:
        # Il guardiano: la rete torna com'era anche se questo copione muore.
        RETE.guardiano_arma(min(a.affitto, (a.secondi + 90) * 2 * len(profili) + 300))

        log("LA SCENA — una sessione corta per far nascere il palco e il sink, "
            "poi il tono")
        if not RETE.innesca_sessione():
            ko("la sessione non si apre: NON misuro")
            return 2
        if not RETE.tono_accendi():
            ko("il tono NON suona dentro la sessione: mi fermo, invece di "
               "misurare silenzio e chiamarlo rete")
            return 2
        ok("il tono suona: il grafo ha i legami in ingresso al sink")

        for nome, regole, testo, predicati in profili:
            log("%s · %s" % (nome, testo))
            if time.time() > scadenza - (a.secondi + 90) * 2:
                ko("l'affitto del lucchetto sta per scadere: NON comincio «%s» "
                   "— meglio un profilo non misurato che uno misurato sotto il "
                   "netem di un altro" % nome)
                esiti.append({"profilo": nome, "passa": None,
                              "esito": "NON MISURATO — affitto del lucchetto agli sgoccioli"})
                break
            g_ok, q = RETE.guasta(regole)
            if not g_ok:
                ko(q)
                esiti.append({"profilo": nome, "passa": None,
                              "esito": "tc ha rifiutato la regola: %s" % q})
                break
            inf("tc: %s" % " ".join(q.split("\n")[:3])[:200])
            # ⛔ M3 si riverifica a OGNI profilo: «il tono suonava all'inizio»
            #    non e' «il tono sta suonando adesso».
            rc, out, _ = root("env UTENTE=%s UID_B=%d LAV=%s python3 "
                              "%s/banchi/07-b64-scena.py grafo"
                              % (UTENTE, UID_B, LAV, ALB))
            try:
                leg = json.loads(out).get("legami_in_ingresso", 0)
            except Exception:
                leg = -1
            inf("M3: legami in ingresso al sink = %s" % leg)
            if leg <= 0:
                ko("il tono non suona piu': NON giudico questo profilo")
                esiti.append({"profilo": nome, "passa": None,
                              "esito": "NIENTE DA GIUDICARE — il tono taceva"})
                continue

            giri = {}
            for regola in REGOLE:
                n = giro(nome, regola, a.secondi)
                giri[regola] = n
                if n.get("esito"):
                    ko("%s: %s" % (regola, n["esito"]))
                else:
                    print("    %s" % riga_numeri(n))
            v, u = giri["vecchia"], giri["nuova"]
            if v.get("esito") or u.get("esito"):
                esiti.append({"profilo": nome, "passa": None, "giri": giri,
                              "esito": "un giro non ha prodotto numeri"})
                continue

            # ⭐ E QUI GLI ATTESI SMETTONO DI ESSERE PROSA.
            verdetti = []
            for pred in predicati:
                passa, perche = pred(v, u)
                verdetti.append({"passa": passa, "perche": perche})
                print("    %s %s" % ("OK " if passa else ("⚠  " if passa is None
                                                          else "⛔ NO"), perche))
            rossi = [x for x in verdetti if x["passa"] is False]
            muti = [x for x in verdetti if x["passa"] is None]
            passa = None if (muti and not rossi) else (not rossi)
            esiti.append({"profilo": nome, "regole": regole, "testo": testo,
                          "giri": giri, "verdetti": verdetti, "passa": passa})
    finally:
        log("⛔ LA RETE SI RIMETTE COM'ERA, e si VERIFICA")
        try:
            RETE.tono_spegni()
        except Exception as e:
            ko("il tono non si e' spento: %s" % e)
        try:
            RETE.guardiano_disarma()
            RETE.rimetti()
        except Exception as e:
            ko("⛔ la rete NON si e' rimessa: %s" % e)
        LUCCHETTO.molla(CHI)

    with open(os.path.join(FUORI, "b77-esiti.json"), "w") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1)

    # ═══ LA TABELLA APPAIATA ═══════════════════════════════════════════════
    log("LA TABELLA APPAIATA — profilo × regola")
    print("    %-13s %-8s %8s %7s %7s %8s %8s %7s %6s %7s %6s %6s %7s"
          % ("profilo", "regola", "PUREZZA", "tono", "cop.", "sul_filo",
             "conseg.", "vecchi", "tard", "fuori", "rec", "dop", "srv:fal"))
    for e in esiti:
        for regola in REGOLE:
            n = (e.get("giri") or {}).get(regola)
            if not n or n.get("esito"):
                print("    %-13s %-8s   (nessun numero)" % (e["profilo"], regola))
                continue
            def q(x, f="%s"):
                return "-" if x is None else (f % x)
            print("    %-13s %-8s %8s %7s %7s %8s %8s %7s %6s %7s %6s %6s %7s"
                  % (e["profilo"], regola, q(n.get("purezza"), "%.4f"),
                     q(n.get("purezza_tono"), "%.3f"), q(n.get("copertura"), "%.4f"),
                     q(n.get("sul_filo")), q(n.get("consegnati")),
                     q(n.get("vecchi")), q(n.get("tardivi")), q(n.get("fuori")),
                     q(n.get("rec")), q(n.get("dop")), q(n.get("dgram_falsi"))))

    rossi = [e for e in esiti if e.get("passa") is False]
    muti = [e for e in esiti if e.get("passa") is None]
    log("IL VERDETTO — %d profili, %d rossi, %d non giudicati"
        % (len(esiti), len(rossi), len(muti)))
    for e in rossi:
        for x in e.get("verdetti", []):
            if x["passa"] is False:
                ko("%s: %s" % (e["profilo"], x["perche"]))
    for e in muti:
        inf("⚠ %s: %s" % (e["profilo"], e.get("esito") or "un atteso si e' rifiutato di giudicare"))
    inf("gli esiti per esteso: %s" % os.path.join(FUORI, "b77-esiti.json"))
    if rossi:
        return 1
    if muti:
        return 2      # ⚠ «non ho misurato» e' un esito SUO, non un verde
    ok("⭐ tutti i profili hanno fatto quel che era scritto prima")
    return 0


def principale():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("passo", nargs="?", default="misura",
                   choices=["misura", "terreno", "rimetti", "stato"])
    p.add_argument("--certifica", action="store_true",
                   help="⭐ l'autoprova dei predicati, con numeri fabbricati: "
                        "dimostra che sanno dare ROSSO")
    p.add_argument("--secondi", type=int, default=25,
                   help="quanto dura OGNI giro (e i giri sono due per profilo)")
    p.add_argument("--solo", default="", help="un profilo solo, per nome")
    p.add_argument("--affitto", type=int, default=900,
                   help="⛔ quanto tengo il lucchetto del netem: corto, ci sono "
                        "altri agenti in coda")
    p.add_argument("--attesa", type=int, default=2400,
                   help="quanti secondi aspetto il mio turno")
    a = p.parse_args()
    if a.certifica:
        return certifica()
    if a.passo == "terreno":
        return 0 if terreno_controlla() else 2
    if a.passo in ("rimetti", "stato"):
        log("LA RETE DELLA MACCHINA DI PROVA")
        return 0 if RETE.rimetti() else 2
    return misura(a)


if __name__ == "__main__":
    sys.exit(principale())
