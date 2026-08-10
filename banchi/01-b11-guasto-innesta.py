#!/usr/bin/env python3
"""01-b11-guasto-innesta.py — ⛔ IL SERVER GUASTO DI PROPOSITO, per B11.

    python3 01-b11-guasto-innesta.py            innesta i guasti
    python3 01-b11-guasto-innesta.py --togli    li toglie

⚠ Gira DENTRO il contenitore, DOPO `01-b3-rcp-innesta.py`: tocca la COPIA di
  `rcp.c` che sta in `examples/`, non l'originale in `banchi/rcp/`.

===========================================================================
⛔ PERCHE' UN SERVER GUASTO, E PERCHE' SI BUTTA

`fasi/01-filo-nudo.md`, B11, rilievo **R4.1**: la prima stesura del banco aveva
dodici violazioni verso il server e **nessuna verso la pagina**.  Ma `RCP.md`
§3 e' scritta su «un'implementazione RCP», e §9 ha un **DEVE esplicito del
client**.  ⭐ Per provare che la pagina applica §3 bisogna **mandarle qualcosa
di sbagliato**, e l'unico che puo' farlo e' un server che sbaglia apposta.

⛔ E queste righe **non restano**: un interruttore che fa mentire il server, se
   sopravvive alla fase, un giorno lo trova acceso qualcuno che non sapeva
   esistesse.  Stanno qui, in un innesto che si toglie, e `--togli` le porta
   via tutte.

===========================================================================
⭐ COME SI SCEGLIE IL GUASTO: DAL `CIAO`, NON DALLA RIGA DI COMANDO

Il guasto arriva nella capacita' **`banco.guasto`** del `CIAO`.  ⭐ Cosi' i
dodici casi girano su **un solo server acceso** e in **un solo caricamento
della pagina**: senza, ogni caso vorrebbe un riavvio, e dodici riavvii per due
motori sono ventiquattro occasioni di misurare un server diverso da quello che
si crede.

⚠ E il nome e' sconosciuto a RCP/1, quindi un server SANO lo ignora (§4.3,
  eccezione dei nomi sconosciuti): la pagina di B11 si puo' puntare anche
  contro il server vero, e li' i dodici casi devono fallire tutti — che e' il
  controllo che dice **no**.
"""
import os
import subprocess
import sys

ESEMPI = "/srv/src/b2/ngtcp2/examples"
MARCA = "REMOTIX B11 GUASTO"

INNESTI = [
    # ── 1. Il campo che tiene il nome del guasto ───────────────────────────
    (
        "rcp.c",
        "\tchar audio[32];\n",
        "\tchar audio[32];\n"
        "\t/* ⚠ REMOTIX B11 GUASTO — il guasto chiesto dal client, e si butta con"
        " l'innesto. */\n"
        "\tchar guasto[64];\n",
        "il campo del guasto",
    ),
    # ── 2. La cattura, dal CIAO ────────────────────────────────────────────
    (
        "rcp.c",
        '\t\tif (strcmp(nome, "video.codec") == 0)\n',
        '\t\t/* ⚠ REMOTIX B11 GUASTO — `banco.guasto` non esiste in RCP/1: un server\n'
        '\t\t * sano la ignora come qualunque nome sconosciuto (§4.3). */\n'
        '\t\tif (strcmp(nome, "banco.guasto") == 0) {\n'
        '\t\t\tsnprintf(s->guasto, sizeof s->guasto, "%s", valore);\n'
        '\t\t\treg(s, "⚠ B11 GUASTO: guasto chiesto dal client: %s", s->guasto);\n'
        '\t\t}\n'
        '\t\tif (strcmp(nome, "video.codec") == 0)\n',
        "la cattura del guasto",
    ),
    # ── 3. ECCOMI, nelle sue tre vesti storte ──────────────────────────────
    (
        "rcp.c",
        "\tsc_u16(&w, RCP_VERSIONE);\n\tsc_u16(&w, 5); /* quante capacita' */\n",
        "\t/* ⚠ REMOTIX B11 GUASTO — tre guasti dentro ECCOMI:\n"
        "\t *   eccomi-versione-2         una versione PIU' ALTA di quella\n"
        "\t *                             chiesta: §9 obbliga il CLIENT a\n"
        "\t *                             congedare con VERSIONE_INCOMPATIBILE\n"
        "\t *   capacita-sconosciuta      un nome che non esiste: la pagina\n"
        "\t *                             DEVE ignorarlo e proseguire\n"
        "\t *   misura-massima-in-eccomi  una capacita' del CLIENT mandata dal\n"
        "\t *                             SERVER: nome conosciuto, lato\n"
        "\t *                             sbagliato, ERRORE_PROTOCOLLO */\n"
        "\tbool g_ver = strcmp(s->guasto, \"eccomi-versione-2\") == 0;\n"
        "\tbool g_ign = strcmp(s->guasto, \"capacita-sconosciuta\") == 0;\n"
        "\tbool g_lato = strcmp(s->guasto, \"misura-massima-in-eccomi\") == 0;\n"
        "\tsc_u16(&w, g_ver ? 2 : RCP_VERSIONE);\n"
        "\tsc_u16(&w, 5 + (g_ign ? 1 : 0) + (g_lato ? 1 : 0));\n",
        "i tre guasti di ECCOMI",
    ),
    (
        "rcp.c",
        '\tsc_str(&w, "banco.marca");\n\tsc_str(&w, "no");\n',
        '\tsc_str(&w, "banco.marca");\n\tsc_str(&w, "no");\n'
        '\tif (g_ign) {\n'
        '\t\tsc_str(&w, "questa.non.esiste");\n'
        '\t\tsc_str(&w, "boh");\n'
        '\t}\n'
        '\tif (g_lato) {\n'
        '\t\tsc_str(&w, "video.misura_massima");\n'
        '\t\tsc_str(&w, "3840x2160");\n'
        '\t}\n',
        "le due capacita' storte",
    ),
    # ── 4. Un tipo che non esiste, subito dopo ECCOMI ──────────────────────
    (
        "rcp.c",
        "\tmanda_eccomi(s);\n\ts->stato = S_ATTESA_CREDENZIALI;\n",
        "\tmanda_eccomi(s);\n"
        "\t/* ⚠ REMOTIX B11 GUASTO — un tipo sconosciuto sul canale di controllo: §3\n"
        "\t *   vieta di ignorarlo, e la pagina deve chiudere. */\n"
        "\tif (strcmp(s->guasto, \"tipo-sconosciuto\") == 0) {\n"
        "\t\tuint8_t niente[1] = {0};\n"
        "\t\tmanda_messaggio(s, 0x00FF, niente, 0);\n"
        "\t}\n"
        "\ts->stato = S_ATTESA_CREDENZIALI;\n",
        "il tipo sconosciuto",
    ),
    # ── 5. SESSIONE: tela dispari e desktop mentitore ──────────────────────
    (
        "rcp.c",
        '\tsc_byte(&w, 1); /* 1 = NUOVA */\n\tsc_u32(&w, tl);\n\tsc_u32(&w, ta);\n'
        '\tsc_str(&w, "sconosciuto"); /* il desktop: in fase 1 non c\'e\' compositore */\n'
        '\tif (!w.pieno)\n\t\tmanda_messaggio(s, T_SESSIONE, corpo, w.len);\n',
        '\t/* ⚠ REMOTIX B11 GUASTO — due guasti dentro SESSIONE:\n'
        '\t *   sessione-tela-dispari   la tela CONCESSA e\' dispari: la pagina\n'
        '\t *                           deve RIFIUTARE, non adattarsi\n'
        '\t *   sessione-desktop-*      un desktop che non e\' quello vero: §4.5\n'
        '\t *                           vieta alla pagina di cambiare\n'
        '\t *                           comportamento in base a questo campo */\n'
        '\tbool g_disp = strcmp(s->guasto, "sessione-tela-dispari") == 0;\n'
        '\tconst char *g_desk = "sconosciuto";\n'
        '\tif (strcmp(s->guasto, "sessione-desktop-kde") == 0)\n'
        '\t\tg_desk = "kde";\n'
        '\telse if (strcmp(s->guasto, "sessione-desktop-gnome") == 0)\n'
        '\t\tg_desk = "gnome";\n'
        '\tsc_byte(&w, 1); /* 1 = NUOVA */\n'
        '\tsc_u32(&w, g_disp ? tl + 1 : tl);\n'
        '\tsc_u32(&w, g_disp ? ta + 1 : ta);\n'
        '\tsc_str(&w, g_desk);\n'
        '\tif (!w.pieno)\n\t\tmanda_messaggio(s, T_SESSIONE, corpo, w.len);\n'
        '\t/* ⚠ REMOTIX B11 GUASTO — un CONGEDO col motivo 0x00, che §3.1 vieta. */\n'
        '\tif (strcmp(s->guasto, "congedo-motivo-zero") == 0) {\n'
        '\t\tuint8_t c0[8];\n'
        '\t\tscrittore w0 = {c0, sizeof c0, 0, false};\n'
        '\t\tsc_byte(&w0, 0);\n'
        '\t\tsc_str(&w0, "");\n'
        '\t\tmanda_messaggio(s, T_CONGEDO, c0, w0.len);\n'
        '\t}\n',
        "i guasti di SESSIONE",
    ),
    # ── 6. Un CONGEDO dopo RESPINTO, che §4.4 vieta ────────────────────────
    (
        "rcp.c",
        "\tmanda_messaggio(s, T_RESPINTO, corpo, 1);\n"
        "\ts->stato = S_FINITA;\n"
        "\ts->g.chiudi(s->g.ctx, motivo);\n",
        "\tmanda_messaggio(s, T_RESPINTO, corpo, 1);\n"
        "\t/* ⚠ REMOTIX B11 GUASTO — §4.4: dopo RESPINTO non arriva nient'altro.  Qui\n"
        "\t *   arriva, e la pagina deve accorgersene. */\n"
        "\tif (strcmp(s->guasto, \"respinto-poi-congedo\") == 0) {\n"
        "\t\tuint8_t c1[8];\n"
        "\t\tscrittore w1 = {c1, sizeof c1, 0, false};\n"
        "\t\tsc_byte(&w1, RCP_ERRORE_PROTOCOLLO);\n"
        "\t\tsc_str(&w1, \"\");\n"
        "\t\tmanda_messaggio(s, T_CONGEDO, c1, w1.len);\n"
        "\t\t/* ⛔⭐ E QUI IL GUASTO NON CHIUDE, ED E' LA DIFFERENZA FRA UNA\n"
        "\t\t *   MISURA E UN TESTA-O-CROCE.\n"
        "\t\t *\n"
        "\t\t *   La chiusura di §3.1 partirebbe subito dietro al messaggio, e\n"
        "\t\t *   correrebbe contro la risposta della pagina: il 10 agosto 2026\n"
        "\t\t *   Chrome ha perso quella corsa in un giro su cinque e ha\n"
        "\t\t *   dichiarato `congedo:0x00` invece di `0x0b`.  ⚠ Un banco che\n"
        "\t\t *   cambia verdetto fra due giri identici non misura la pagina:\n"
        "\t\t *   misura il carico della macchina.\n"
        "\t\t *\n"
        "\t\t * ⭐ Quel che questo caso vuole vedere e' la REAZIONE della pagina\n"
        "\t\t *    a un messaggio che §4.4 vieta — e per vederla bisogna\n"
        "\t\t *    lasciarle il tempo di averla.  A chiudere sara' lei, col suo\n"
        "\t\t *    `CONGEDO`; se non lo fa, resta il silenzio di §2.2. */\n"
        "\t\ts->stato = S_FINITA;\n"
        "\t\treturn;\n"
        "\t}\n"
        "\ts->stato = S_FINITA;\n"
        "\ts->g.chiudi(s->g.ctx, motivo);\n",
        "il congedo dopo il respinto",
    ),
    # ── 7. L'accessorio per l'ospite: due guasti vivono negli STREAM ───────
    (
        "rcp.c",
        "const char *rcp_utente(const rcp_sessione *s) { return s ? s->utente : \"\"; }\n",
        "const char *rcp_utente(const rcp_sessione *s) { return s ? s->utente : \"\"; }\n"
        "/* ⚠ REMOTIX B11 GUASTO — due guasti su dodici non stanno nei messaggi ma\n"
        " *   negli STREAM: un FIN sul canale di controllo e uno stream\n"
        " *   bidirezionale aperto dal server.  Quelli li sa fare solo\n"
        " *   l'ospite, e questa riga e' l'unica cosa che gli serve sapere. */\n"
        "const char *rcp_guasto(const rcp_sessione *s) { return s ? s->guasto : \"\"; }\n",
        "l'accessorio del guasto",
    ),
    # ── 8. L'ospite: il FIN e lo stream bidirezionale ──────────────────────
    (
        "http3_server_proto_codec.cc",
        "bool rcp_autentica(const char *utente, const char *parola);\n}\n",
        "bool rcp_autentica(const char *utente, const char *parola);\n"
        # ⚠ `const rcp_sessione *`, non `const struct rcp_sessione *`: rcp.h la
        #   dichiara gia' con un typedef, e in C++ ripetere `struct` su un
        #   typedef e' un errore.  Il primo giro del 10 agosto 2026 e' morto
        #   qui — e ⛔ il banco non se n'e' accorto, perche' controllava che il
        #   binario ESISTESSE invece che fosse NUOVO.
        "const char *rcp_guasto(const rcp_sessione *s); // REMOTIX B11 GUASTO\n"
        "}\n",
        "la dichiarazione del guasto",
    ),
    (
        "http3_server_proto_codec.cc",
        "  auto stato = std::string_view{rcp_stato_nome(rcp_)};\n",
        "  // ⚠ REMOTIX B11 GUASTO — i due guasti che vivono negli stream, e si\n"
        "  //   armano quando la sessione e' aperta.\n"
        "  if (rcp_ && std::string_view{rcp_stato_nome(rcp_)} == \"attiva\" &&\n"
        "      !b11_fatto_) {\n"
        "    auto g = std::string_view{rcp_guasto(rcp_)};\n"
        "    if (g == \"fin-sul-controllo\") {\n"
        "      // ⛔ §4.2: il FIN sul canale di controllo E' la fine della\n"
        "      //    sessione, e la pagina non deve piu' spedire su NESSUN\n"
        "      //    canale.  Qui non si chiude la sessione WebTransport: si\n"
        "      //    chiude solo lo stream, cosi' il banco misura la regola e\n"
        "      //    non la caduta del trasporto.\n"
        "      b11_fatto_ = true;\n"
        "      std::println(stderr, \"REMOTIX B11 GUASTO: FIN sul canale di controllo\");\n"
        "      wt_uscita_.push_back(WtUscita{rcp_stream_, {}, 0, true});\n"
        "    } else if (g == \"bidi-dal-server\") {\n"
        "      // ⛔ §2.5: «il server NON DEVE aprire stream bidirezionali».\n"
        "      b11_fatto_ = true;\n"
        "      int64_t sid = -1;\n"
        "      if (ngtcp2_conn_open_bidi_stream(conn_, &sid, nullptr) == 0) {\n"
        "        std::println(stderr,\n"
        "                     \"REMOTIX B11 GUASTO: aperto uno stream BIDIREZIONALE {} \"\n"
        "                     \"verso il client\", sid);\n"
        "        std::array<uint8_t, 3> t{0x40, 0x41, 0};\n"
        "        t[2] = static_cast<uint8_t>(wt_sessione_);\n"
        "        wt_uscita_.push_back(WtUscita{\n"
        "          sid, std::vector<uint8_t>{t.begin(), t.end()}, 0, false});\n"
        "      }\n"
        "    }\n"
        "  }\n"
        "  auto stato = std::string_view{rcp_stato_nome(rcp_)};\n",
        "i due guasti degli stream",
    ),
    (
        "http3_server_proto_codec.h",
        "  std::unordered_map<int64_t, bool> wt_uni_;\n",
        "  std::unordered_map<int64_t, bool> wt_uni_;\n"
        "  bool b11_fatto_{false}; // ⚠ REMOTIX B11 GUASTO — un guasto per sessione\n",
        "lo stato del guasto",
    ),
]


def leggi(percorso):
    """Il testo di un file di `examples/`, oppure `None` se non c'e'.

    ⛔ «Non c'e'» e «non l'ho potuto leggere» non sono la stessa cosa.  Il
       primo e' un fatto legittimo — `01-b3-rcp-innesta.py --togli` cancella
       `rcp.c` da `examples/` — il secondo e' un errore, e deve arrivare al
       banco invece di somigliare a uno zero.
    """
    try:
        with open(os.path.join(ESEMPI, percorso), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def scrivi(percorso, testo):
    with open(os.path.join(ESEMPI, percorso), "w", encoding="utf-8") as f:
        f.write(testo)


def marche_attese():
    """Quante volte la marca deve comparire in ciascun file a innesto fatto.

    ⭐ Il numero lo CALCOLA la tabella, non lo scrive una mano: e' il
       denominatore che `01-b11-guasto.sh` confronta col disco dopo la
       compilazione, e un denominatore scritto a mano invecchia col primo
       innesto che qualcuno aggiunge.
    """
    conto = {}
    for percorso, _appiglio, sostituto, _nome in INNESTI:
        conto[percorso] = conto.get(percorso, 0) + sostituto.count(MARCA)
    return conto


def togli():
    """⛔ E TOGLIE DAVVERO.

    Fino al 10 agosto 2026 questo ramo stampava tre righe e restituiva **0**
    senza aprire un file: `--togli && grep -c 'REMOTIX B11 GUASTO'
    examples/rcp.c` usciva 0 e stampava 7.  ⚠ E' il difetto gia' pagato su
    `01-b3-rcp-innesta.py --togli` — un comando che dichiara di togliere, non
    toglie, e restituisce successo — riscritto qui in forma pura.  Che nessuno
    lo chiamasse non lo rendeva innocuo: la riga d'uso in cima a questo file e'
    quel che leggera' chi lo trovera' fra sei mesi.
    """
    print("== Si tolgono i guasti di B11")
    testi, originali, tolti = {}, {}, 0
    # ⛔ In ordine INVERSO a come sono stati messi: un sostituto puo' contenere
    #    l'appiglio di un altro, e disfare al contrario e' l'unico ordine che
    #    non lascia mezzi innesti.
    for percorso, appiglio, sostituto, nome in reversed(INNESTI):
        if percorso not in testi:
            testi[percorso] = originali[percorso] = leggi(percorso)
        if testi[percorso] is None:
            print(f"   --  {nome:32s} {percorso} non c'e': niente da togliere")
            continue
        n = testi[percorso].count(sostituto)
        if n == 0:
            print(f"   --  {nome:32s} non c'era")
            continue
        testi[percorso] = testi[percorso].replace(sostituto, appiglio)
        tolti += 1
        print(f"   OK  {nome:32s} tolto {n} volta/e  [{percorso}]")

    scritti = 0
    for percorso, testo in testi.items():
        if testo is not None and testo != originali[percorso]:
            scrivi(percorso, testo)
            scritti += 1

    # ⛔ E SI VERIFICA DAL LATO CHE CONTA: il file sul disco, non l'intenzione
    #    di chi ha scritto la sostituzione.
    resti = {}
    for percorso in testi:
        testo = leggi(percorso)
        if testo and MARCA in testo:
            resti[percorso] = testo.count(MARCA)
    print(f"\n   {tolti} innesti tolti, {scritti} file riscritti")
    if resti:
        for percorso, n in resti.items():
            print(f"   NO  {percorso}: restano {n} marche «{MARCA}»")
        print("   ⛔ un server che mente di proposito NON deve sopravvivere")
        print("      alla fase: si rimettono gli innesti di B2 e di B3 da capo.")
        return 1
    print(f"   ⭐ nessuna marca «{MARCA}» nei file di examples/")
    return 0


def innesta():
    print("== I guasti di B11 — righe che NON devono sopravvivere alla fase")
    testi = {}
    for percorso in dict.fromkeys(p for p, *_ in INNESTI):
        testi[percorso] = leggi(percorso)
        if testi[percorso] is None:
            print(f"   ⛔ {percorso} non c'e' in {ESEMPI}: gli innesti di B2 e")
            print("      di B3 vanno applicati PRIMA di questo.")
            return 1
    originali = dict(testi)

    applicati, gia, guasti = 0, 0, 0
    for percorso, appiglio, sostituto, nome in INNESTI:
        # ⛔ LA GUARDIA CHIEDE SE C'E' QUESTO INNESTO, non se c'e' UNA marca.
        #
        #    Era `MARCA in testo and appiglio not in testo`, e tre innesti su
        #    undici conservano il proprio appiglio DENTRO il sostituto, per
        #    costruzione: il campo del guasto, la cattura dal `CIAO` e
        #    l'accessorio `rcp_guasto`.  Su un `rcp.c` gia' guasto l'appiglio
        #    c'era ancora, la guardia era falsa, `n` valeva 1 e l'innesto **si
        #    riapplicava**: `char guasto[64];` dichiarato due volte (errore di
        #    compilazione, cioe' un rosso senza nome), oppure — se passava — la
        #    riga «guasto chiesto dal client» scritta due volte per caso, che
        #    raddoppia i conteggi di `01-b11-lancia.sh` e addossa alla PAGINA
        #    un rosso che e' dell'innesto.
        # ⭐ Il sostituto e' l'unica cosa che sappia dire «questo innesto c'e'
        #    gia'», perche' e' esattamente quel che si e' scritto sul disco.
        if sostituto in testi[percorso]:
            gia += 1
            print(f"   ⚠  {nome:32s} c'e' gia'  [{percorso}]")
            continue
        n = testi[percorso].count(appiglio)
        stato = "OK " if n == 1 else "NO "
        print(f"   {stato} {nome:32s} appiglio trovato {n} volta/e  [{percorso}]")
        if n != 1:
            guasti += 1
            continue
        testi[percorso] = testi[percorso].replace(appiglio, sostituto, 1)
        applicati += 1

    if guasti:
        print(f"\n   ⛔ {guasti} appigli non trovati: NON si scrive niente.")
        print("      Un innesto a meta' produce un server che sbaglia in un")
        print("      modo diverso da quello che il banco crede di misurare.")
        return 1

    scritti = [p for p in testi if testi[p] != originali[p]]
    for percorso in scritti:
        scrivi(percorso, testi[percorso])

    # ⛔ E SI CONTA QUEL CHE C'E' SUL DISCO, non quel che dice la tabella.
    #
    #    `print(f"OK {len(INNESTI)} guasti innestati in {len(testi)} file")`
    #    stampava una COSTANTE (11) e il numero di file **letti**: su un albero
    #    in cui tutti gli innesti prendevano il ramo «c'e' gia'» dichiarava «OK
    #    11 guasti innestati in 3 file» con zero sostituzioni, e restituiva 0.
    #    ⚠ Un conteggio che non puo' valere zero non e' un conteggio: e' una
    #      didascalia (`LEZIONI.md` §1.9).
    attese = marche_attese()
    male = 0
    for percorso, atteso in attese.items():
        vero = (leggi(percorso) or "").count(MARCA)
        stato = "OK " if vero == atteso else "NO "
        print(f"   {stato} {percorso:34s} marche sul disco: {vero}  (attese {atteso})")
        if vero != atteso:
            male += 1
    print(f"\n   {applicati} innesti applicati, {gia} c'erano gia', su"
          f" {len(INNESTI)}; {len(scritti)} file riscritti")
    if male:
        print("   ⛔ il disco non dice quel che la tabella dichiara: non si")
        print("      accende niente, o si misura un server diverso da quello")
        print("      che il banco crede di aver costruito.")
        return 1
    # ⭐ Il numero che `01-b11-guasto.sh` confronta col disco dopo la
    #    compilazione: calcolato qui, stampato qui, e mai scritto a mano di la'.
    print(f"== B11-MARCHE-ATTESE: {sum(attese.values())}")
    print("   ⛔ e si tolgono con --togli, o rimettendo gli innesti di B2 e B3")
    return 0


def main():
    if "--togli" in sys.argv:
        return togli()
    return innesta()


if __name__ == "__main__":
    sys.exit(main())
