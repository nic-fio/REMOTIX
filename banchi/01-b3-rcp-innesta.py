#!/usr/bin/env python3
"""01-b3-rcp-innesta.py — innesta RCP sopra lo strato WebTransport di B2.

    python3 01-b3-rcp-innesta.py            innesta
    python3 01-b3-rcp-innesta.py --togli    rimette l'esempio com'era

---------------------------------------------------------------------------
⛔ PERCHE' E' UN SECONDO INNESTO E NON UNA CRESCITA DEL PRIMO

`01-b2-ngtcp2-wt-innesta.py` misura una cosa sola: **quanto collante costa
WebTransport su ngtcp2+nghttp3**, ed e' il numero su cui `DECISIONI.md` §6.4 ha
scelto la libreria.  Farlo crescere con RCP dentro renderebbe quel numero
incomprensibile fra sei mesi: due misure diverse sotto la stessa etichetta,
cioe' la forma **E2**.

⭐ Qui il collante e' quasi zero apposta: **RCP vive in `banchi/rcp/`, in C, e
   non sa che sotto c'e' QUIC**.  Quel che questo innesto aggiunge all'esempio
   sono solo i fili — e il fatto che siano pochi e' la prova che il modulo si
   potra' portare nel server vero senza riscriverlo.

---------------------------------------------------------------------------
⛔ IL RITARDO FISSO E IL TEMPO CHE PASSA

`RCP.md` §4.4-bis impone un secondo prima di rispondere a `CREDENZIALI`,
**anche quando la risposta e' AMMESSO**.  Un secondo in cui il server non ha
niente da spedire: se nessun timer scatta, la risposta non parte mai.

⚠ Per questo l'ospite accende il **keep-alive di QUIC a 100 ms**: cosi' il
  percorso di scrittura viene percorso comunque, e `rcp_tempo()` ha modo di
  far scadere ritardi e tetti.  E' un filo dell'ospite, non una regola del
  protocollo — per questo sta qui e non in `rcp.c`.

⛔ E si accende in `rcp_avvia`, cioe' **quando la sessione RCP nasce**, non al
   primo byte che arriva.  `[M]` 10 agosto 2026, B6: armato solo dentro
   `rcp_passa`, il tetto del `CIAO` (§4.6 riga 1) non scadeva mai — nello
   stato «attesa-ciao» di byte non ne e' ancora arrivato nessuno, quindi
   nessuno armava niente, quindi `rcp_tempo()` non lo chiamava piu' nessuno.

---------------------------------------------------------------------------
⛔⭐ E DALL'11 AGOSTO 2026 INNESTA ANCHE IL BAN LATO OSPITE — `RCP.md` §4.4-bis

`rcp.c` sa contare i fallimenti, bannare, salvare su file, dire se un indirizzo
e' bannato e togliere un ban.  ⛔ Ma non apre socket, non legge la riga di
comando e non serve nessuna pagina: **le tre cose che §4.4-bis chiede al padrone
di casa non esistevano**, e senza di esse la regola dell'utente era scritta a
meta'.  Adesso stanno in `server.cc`, in `CORPO_OSPITE`:

    --ban-file=<PATH>        i ban si rileggono all'avvio, e ⛔ «zero ban» e
                             «non ho potuto leggere il file» si stampano
                             DIVERSI — sul secondo il server non parte
    la pagina in TCP         stessa porta dell'UDP (SPECIFICHE.md §4): a chi e'
                             bannato si serve LO STESSO, con «tentativi
                             esauriti» e le ore che mancano
    --comando-socket=<PATH>  «SBLOCCA <indirizzo>» su un socket Unix 0600 —
                             l'altra via d'uscita oltre alle dodici ore

⚠ Chi accende questo server **senza** quelle due opzioni non perde il ban: perde
  la persistenza e il comando.  Il server lo dice all'avvio, in due righe.
"""
import os
import shutil
import subprocess
import sys

ALBERO = "/srv/src/b2/ngtcp2"
ESEMPI = "/srv/src/b2/ngtcp2/examples"
SORGENTI = "/srv/src/rcp"
MARCA = "REMOTIX B3"
MARCA_B2 = "REMOTIX B2"
MARCA_B11 = "REMOTIX B11 GUASTO"

FILE_NOSTRI = ["rcp.c", "rcp.h", "autenticazione.c"]

# I file dell'esempio che questo innesto tocca: servono a `--togli` per
# VERIFICARE di aver tolto, invece di restituire 0 comunque.
#
# ⛔ `server.cc` e' entrato l'11 agosto 2026 col ban lato ospite: le tre cose
#    che §4.4-bis chiede al PADRONE DI CASA — caricare i ban all'avvio, servire
#    la pagina a chi e' bannato, togliere un ban su comando — vivono nel `main`
#    e nel ciclo degli eventi, non nel codec.  ⚠ Chi lo dimentica qui lascia
#    `--togli` a dichiarare «nessuna traccia» su un file che ne ha cento.
FILE_TOCCATI = [
    "http3_server_proto_codec.cc",
    "http3_server_proto_codec.h",
    "CMakeLists.txt",
    "server.cc",
]

INNESTI = [
    # ── 0. ⛔ L'intestazione di RCP, IN CIMA ─────────────────────────────────
    #    Il primo giro del 10 agosto la metteva insieme al corpo dei ganci, che
    #    sta a meta' file: `rcp_tempo` veniva usata alla riga 120 e dichiarata
    #    alla 1100.  Un'intestazione si mette dove si mettono le intestazioni.
    (
        "http3_server_proto_codec.cc",
        '#include "http3_server_proto_codec.h"\n',
        '#include "http3_server_proto_codec.h"\n'
        "\n"
        "// ⭐ REMOTIX B3 — il protocollo sta in C, e vive in banchi/rcp/.\n"
        'extern "C" {\n'
        '#include "rcp.h"\n'
        "bool rcp_autentica(const char *utente, const char *parola);\n"
        "}\n",
        "l'intestazione di RCP",
    ),
    # ── 1. I file nostri nella compilazione ─────────────────────────────────
    (
        "CMakeLists.txt",
        "  set(bsslserver_SOURCES\n",
        "  set(bsslserver_SOURCES\n"
        "    # ⭐ REMOTIX B3 — RCP e PAM.  Sono NOSTRI e stanno in C: l'esempio\n"
        "    #    li ospita, non li possiede.\n"
        "    rcp.c\n"
        "    autenticazione.c\n",
        "i file di RCP nella compilazione",
    ),
    (
        "CMakeLists.txt",
        "  target_link_libraries(bsslserver ${bssl_LIBS})\n",
        "  target_link_libraries(bsslserver ${bssl_LIBS} pam)\n",
        "PAM fra le librerie",
    ),
    # ── 2. Lo stato di RCP nel codec ────────────────────────────────────────
    (
        "http3_server_proto_codec.h",
        "  std::deque<WtUscita> wt_uscita_;\n"
        "  int64_t wt_sessione_{-1};\n",
        "  std::deque<WtUscita> wt_uscita_;\n"
        "  int64_t wt_sessione_{-1};\n"
        "\n"
        "  // ═══ ⭐ REMOTIX B3 — RCP sopra WebTransport ═══════════════════════\n"
        "  // ⛔ Il canale di controllo e' il PRIMO stream bidirezionale che il\n"
        "  //    client apre dentro la sessione (RCP.md §4.2), e il suo\n"
        "  //    chiudersi E' la fine della sessione.\n"
        "  struct rcp_sessione *rcp_{nullptr};\n"
        "  int64_t rcp_stream_{-1};\n"
        "  void rcp_avvia(int64_t stream_id);\n"
        "  void rcp_passa(int64_t stream_id, std::span<const uint8_t> dati);\n"
        "\n"
        "  // ⛔ RCP.md §2.5 — gli stream unidirezionali aperti dal CLIENT.  Il\n"
        "  //    canale si legge dai primi due byte, e tre dei cinque valori\n"
        "  //    sono violazioni: 0x00 (il controllo vive solo sullo stream 0),\n"
        "  //    0x03 (il video va dal server al client), 0x04 (l'audio vive\n"
        "  //    solo sui datagram).\n"
        "  std::unordered_map<int64_t, bool> wt_uni_;\n"
        "\n"
        "  // ⛔ REMOTIX B11 — la chiusura della sessione ASPETTA che la coda\n"
        "  //    d'uscita si sia svuotata: vedi `wt_chiudi_sessione`.\n"
        "  int wt_chiusura_{-1};\n"
        "  int wt_chiusura_attesa_{0};\n"
        "  WtEsito wt_smista_uni(int64_t stream_id, std::span<const uint8_t> data,\n"
        "                        std::vector<uint8_t> &riunito);\n",
        "lo stato di RCP",
    ),
    # ── 3. Il FIN nella coda d'uscita ───────────────────────────────────────
    (
        "http3_server_proto_codec.h",
        "  struct WtUscita {\n"
        "    int64_t stream_id;\n"
        "    std::vector<uint8_t> dati;\n"
        "    size_t off;\n"
        "  };\n",
        "  struct WtUscita {\n"
        "    int64_t stream_id;\n"
        "    std::vector<uint8_t> dati;\n"
        "    size_t off;\n"
        "    // ⭐ REMOTIX B3 — la capsula che chiude la sessione va spedita con\n"
        "    //    il FIN: senza, il client resta ad aspettare altri byte.\n"
        "    bool fin;\n"
        "  };\n",
        "il FIN nella coda d'uscita",
    ),
    # ── 4. Lo smistamento: il primo stream WT e' il canale di controllo ─────
    (
        "http3_server_proto_codec.cc",
        "    if (!data.empty()) {\n"
        "      wt_accoda(stream_id, data);\n"
        "      ngtcp2_conn_extend_max_stream_offset(conn_, stream_id, data.size());\n"
        "      ngtcp2_conn_extend_max_offset(conn_, data.size());\n"
        "    }\n",
        "    if (!data.empty()) {\n"
        "      // ⭐ REMOTIX B3 — sul canale di controllo i byte vanno a RCP.\n"
        "      //\n"
        "      // ⚠ Sugli altri stream resta l'eco di B2, che serviva al banco\n"
        "      //   del trasporto — ma con QUESTO innesto sopra, un secondo\n"
        "      //   stream bidirezionale del client e' una violazione di §2.5\n"
        "      //   che congeda (vedi piu' sotto).  L'eco vale quindi solo per i\n"
        "      //   byte gia' in volo mentre la sessione sta cadendo: ⛔ il banco\n"
        "      //   del trasporto di B2 si misura SENZA B3 innestato.\n"
        "      if (stream_id == rcp_stream_) {\n"
        "        rcp_passa(stream_id, data);\n"
        "      } else {\n"
        "        wt_accoda(stream_id, data);\n"
        "      }\n"
        "      ngtcp2_conn_extend_max_stream_offset(conn_, stream_id, data.size());\n"
        "      ngtcp2_conn_extend_max_offset(conn_, data.size());\n"
        "    }\n",
        "i byte del controllo verso RCP",
    ),
    (
        "http3_server_proto_codec.cc",
        "    wt_streams_[stream_id] = static_cast<int64_t>(sessione);\n"
        "    wt_incerti_.erase(stream_id);\n",
        "    wt_streams_[stream_id] = static_cast<int64_t>(sessione);\n"
        "    wt_incerti_.erase(stream_id);\n"
        "    // ⭐ REMOTIX B3 — RCP.md §4.2: il PRIMO stream bidirezionale che il\n"
        "    //    client apre nella sessione e' il canale di controllo.\n"
        "    //\n"
        "    // ⚠ E «il primo» QUI e' il primo RICONOSCIUTO, non il primo\n"
        "    //   APERTO: i due stream viaggiano in pacchetti diversi, e fra\n"
        "    //   stream diversi la rete non promette nessun ordine.  Il numero\n"
        "    //   dello stream invece l'ordine ce l'ha dentro — QUIC li numera\n"
        "    //   in ordine di apertura — ed e' quello che si guarda per dire\n"
        "    //   quale dei due era il primo (vedi il ramo qui sotto).\n"
        "    if (rcp_stream_ == -1) {\n"
        "      rcp_avvia(stream_id);\n"
        "    } else {\n"
        "      // ⛔ REMOTIX B5 — RCP.md §2.5: «il client NON DEVE aprire stream\n"
        "      //    bidirezionali oltre lo 0».  Il canale di controllo e' UNO\n"
        "      //    SOLO per tutta la sessione, e un secondo bidirezionale non\n"
        "      //    e' un canale nuovo: e' una violazione.\n"
        "      //\n"
        "      // ⚠ Senza questa riga il secondo stream finiva nell'ECO di B2 e\n"
        "      //   i byte tornavano indietro: il client avrebbe visto un server\n"
        "      //   che gli risponde, e la violazione sarebbe passata per una\n"
        "      //   funzione.\n"
        "      //\n"
        "      // ⛔ E LA DIAGNOSI NON DEVE INCOLPARE L'ORDINE D'ARRIVO.  Se\n"
        "      //    questo stream ha un numero PIU' BASSO di quello eletto, il\n"
        "      //    primo aperto era lui, e a scambiarli e' stata la rete: gli\n"
        "      //    stream bidirezionali restano due — e due e' la violazione,\n"
        "      //    comunque siano arrivati — ma «un secondo stream» detto del\n"
        "      //    numero piu' basso manda a cercare il difetto nel client,\n"
        "      //    che li' non ha sbagliato niente.\n"
        "      if (stream_id < rcp_stream_) {\n"
        "        std::println(stderr,\n"
        "                     \"REMOTIX B5: ⛔ due stream bidirezionali dal \"\n"
        "                     \"client dentro la sessione: {} e {} — e il PRIMO \"\n"
        "                     \"APERTO era il {}, arrivato per secondo: il \"\n"
        "                     \"canale di controllo e' stato eletto per ordine \"\n"
        "                     \"d'arrivo, non per numero\",\n"
        "                     rcp_stream_, stream_id, stream_id);\n"
        "      } else {\n"
        "        std::println(stderr,\n"
        "                     \"REMOTIX B5: ⛔ due stream bidirezionali dal \"\n"
        "                     \"client dentro la sessione: il controllo e' il \"\n"
        "                     \"{}, e il {} e' di troppo\",\n"
        "                     rcp_stream_, stream_id);\n"
        "      }\n"
        "      rcp_violazione(rcp_,\n"
        "                     \"due stream bidirezionali dal client dentro la \"\n"
        "                     \"sessione (§2.5)\");\n"
        "    }\n",
        "il primo stream e' il controllo",
    ),
    # ── 4-quater. ⛔ GLI STREAM UNIDIREZIONALI DEL CLIENT — §2.5 ─────────────
    #    B2 mandava a nghttp3 tutto quel che non era un bidirezionale del
    #    client, e nghttp3 di uno stream di tipo 0x54 non sa che farsene: lo
    #    scarta in silenzio.  ⛔ Il risultato era che un client poteva mandare
    #    il canale di controllo, il video o l'audio su uno stream
    #    unidirezionale e **non succedeva niente** — cioe' esattamente
    #    l'indulgenza che §3 vieta, in un punto dove nessun banco guardava.
    (
        "http3_server_proto_codec.cc",
        "  // Solo gli stream bidirezionali aperti dal client: la CONNECT estesa e gli\n"
        "  // stream WebTransport arrivano tutti di li'.\n"
        "  if ((stream_id & 0x03) != 0x00) {\n"
        "    return WtEsito::HTTP3;\n"
        "  }\n",
        "  // ⛔ REMOTIX B5 — gli unidirezionali APERTI DAL CLIENT (§2.5) passano\n"
        "  //    di qui prima di tutto: fra loro c'e' il canale di controllo di\n"
        "  //    HTTP/3 e i due di QPACK, che sono di nghttp3 e non nostri.\n"
        "  if ((stream_id & 0x03) == 0x02) {\n"
        "    return wt_smista_uni(stream_id, data, riunito);\n"
        "  }\n"
        "  // Solo gli stream bidirezionali aperti dal client: la CONNECT estesa e gli\n"
        "  // stream WebTransport arrivano tutti di li'.\n"
        "  if ((stream_id & 0x03) != 0x00) {\n"
        "    return WtEsito::HTTP3;\n"
        "  }\n",
        "gli unidirezionali del client",
    ),
    (
        "http3_server_proto_codec.cc",
        "    if (!resto.empty()) {\n      wt_accoda(stream_id, resto);\n    }\n",
        "    if (!resto.empty()) {\n"
        "      if (stream_id == rcp_stream_) {\n"
        "        rcp_passa(stream_id, resto);\n"
        "      } else {\n"
        "        wt_accoda(stream_id, resto);\n"
        "      }\n"
        "    }\n",
        "i primi byte del controllo",
    ),
    # ── 4-bis. ⛔ IL TEMPO CHE SCORRE ────────────────────────────────────────
    #    Senza questa chiamata `rcp_tempo()` non lo invoca nessuno, e il
    #    ritardo fisso di §4.4-bis non scade MAI: la stretta di mano si ferma
    #    dopo ECCOMI e il cliente va in timeout.  ⚠ Visto al primo giro del
    #    10 agosto 2026 — il modulo era giusto, il filo mancava.
    (
        "http3_server_proto_codec.cc",
        # ⚠ L'appiglio non e' piu' il testo nudo di ngtcp2: e' quel che ci ha
        #   lasciato B2, che fra la dichiarazione di `vec` e il ciclo azzera
        #   `wt_coda_bloccata_`.  ⛔ Un appiglio condiviso fra due innesti va
        #   riletto ogni volta che il primo dei due cambia, o il secondo conta
        #   zero e si ferma dando la colpa a ngtcp2.
        "  std::array<nghttp3_vec, 16> vec;\n"
        "\n"
        "  // ⭐ REMOTIX B2 — una passata di scrittura comincia qui, e la coda\n"
        "  //    nostra riparte SBLOCCATA: `wt_coda_bloccata_` vale per una\n"
        "  //    passata sola.  ⚠ Sta fuori dal ciclo apposta — azzerarlo\n"
        "  //    dentro rimetterebbe in gioco lo stesso elemento a ogni giro,\n"
        "  //    che e' precisamente il ciclo che non avanza.\n"
        "  wt_coda_bloccata_ = false;\n"
        "\n"
        "  for (;;) {\n",
        "  std::array<nghttp3_vec, 16> vec;\n"
        "\n"
        "  // ⭐ REMOTIX B2 — una passata di scrittura comincia qui, e la coda\n"
        "  //    nostra riparte SBLOCCATA: `wt_coda_bloccata_` vale per una\n"
        "  //    passata sola.  ⚠ Sta fuori dal ciclo apposta — azzerarlo\n"
        "  //    dentro rimetterebbe in gioco lo stesso elemento a ogni giro,\n"
        "  //    che e' precisamente il ciclo che non avanza.\n"
        "  wt_coda_bloccata_ = false;\n"
        "\n"
        "  // ⭐ REMOTIX B3 — il tempo di RCP scorre di qui: e' l'unico punto\n"
        "  //    percorso comunque, anche quando non c'e' niente da spedire.\n"
        "  if (rcp_) {\n"
        "    rcp_tempo(rcp_, ngtcp2_conn_get_timestamp(conn_) / NGTCP2_MILLISECONDS);\n"
        "  }\n"
        "  // ⛔ REMOTIX B11 — la capsula di chiusura parte SOLO quando la coda\n"
        "  //    d'uscita e' vuota: il `CONGEDO` deve essere gia' partito, o il\n"
        "  //    browser lo butta insieme alla sessione.\n"
        "  if (wt_chiusura_ >= 0) {\n"
        "    // ⚠ Non basta che la coda sia vuota UNA VOLTA: «consegnato a\n"
        "    //   ngtcp2» non e' «uscito sul filo».  Si aspettano cinque passate\n"
        "    //   di scrittura, che col keep-alive a 100 ms sono mezzo secondo —\n"
        "    //   niente, per un banco, e toglie di mezzo la corsa fra il\n"
        "    //   CONGEDO e la capsula che chiude la sessione.\n"
        "    //\n"
        "    // ⛔ E CHE LE CINQUE PASSATE AVVENGANO lo garantisce il keep-alive\n"
        "    //    che `wt_chiudi_sessione` arma nello stesso istante in cui\n"
        "    //    scrive `wt_chiusura_`: senza, su una violazione trovata al\n"
        "    //    primo messaggio il client tace, nessuno percorre piu' questo\n"
        "    //    punto e il contatore si ferma a uno o due per sempre.  ⚠ E'\n"
        "    //    il difetto misurato da B5 il 10 agosto 2026 — 22 su 36 —, e\n"
        "    //    il registro del server lo diceva per intero: il `congedo`\n"
        "    //    c'era, la «chiusa la sessione WebTransport» no.\n"
        "    wt_chiusura_attesa_ = wt_uscita_.empty() ? wt_chiusura_attesa_ + 1 : 0;\n"
        "    if (wt_chiusura_attesa_ >= 5) {\n"
        "      auto m = static_cast<uint8_t>(wt_chiusura_);\n"
        "      wt_chiusura_ = -1;\n"
        "      wt_chiudi_adesso(m);\n"
        "    }\n"
        "  }\n"
        "\n  for (;;) {\n",
        "il tempo che scorre",
    ),
    # ── 4-ter. ⛔ IL POSTO SI LIBERA ─────────────────────────────────────────
    #    `rcp_libera()` libera il posto nel registro delle sessioni (§8.2
    #    motivo 0x0F).  Senza questa chiamata il posto resta occupato per
    #    sempre, e ⛔ **la stretta di mano funziona UNA volta e mai piu'**:
    #    dalla seconda connessione in poi il server risponde
    #    GIA_ATTIVA_REMOTA a chiunque, compreso chi e' solo.
    #
    # ⭐ Trovato da B3 al primo giro, 10 agosto 2026 — ed e' esattamente il
    #    difetto che B3 esiste per trovare: `LEZIONI.md` §2.1 dice che in v1
    #    un certificato condiviso uccideva il server ALLA SECONDA connessione,
    #    e che una prova a collegamento singolo **resta verde per sempre**.
    #    Questa qui e' la stessa forma, in un altro punto.
    (
        "http3_server_proto_codec.cc",
        "ProtoCodec::~ProtoCodec() {\n",
        "ProtoCodec::~ProtoCodec() {\n"
        "  // ⭐ REMOTIX B3 — il posto nel registro delle sessioni si libera QUI.\n"
        "  if (rcp_) {\n"
        "    rcp_libera(rcp_);\n"
        "    rcp_ = nullptr;\n"
        "  }\n",
        "il posto che si libera",
    ),
    # ── 4-quinquies. ⛔⭐ IL POSTO SI LIBERA QUANDO FINISCE LA SESSIONE,
    #                     NON QUANDO MUORE LA CONNESSIONE — trovato da B11
    (
        "http3_server_proto_codec.cc",
        "ProtoCodec::on_stream_close(int64_t stream_id,\n"
        "                            std::optional<uint64_t> rx_app_error_code,\n"
        "                            std::optional<uint64_t> tx_app_error_code) {\n"
        "  if (!httpconn_) {\n    return {};\n  }\n",
        "ProtoCodec::on_stream_close(int64_t stream_id,\n"
        "                            std::optional<uint64_t> rx_app_error_code,\n"
        "                            std::optional<uint64_t> tx_app_error_code) {\n"
        "  // ⛔⭐ REMOTIX B3 — RCP.md §4.2: il canale di controllo si chiude, e\n"
        "  //    **il suo chiudersi E\' la fine della sessione**.  Il posto nel\n"
        "  //    registro (§8.2 motivo 0x0F) va liberato QUI — e anche quando a\n"
        "  //    chiudersi e\' lo stream della CONNECT estesa, che porta la\n"
        "  //    sessione WebTransport.\n"
        "  //\n"
        "  // ⚠ Prima il posto si liberava solo in `~ProtoCodec`, che e\' il\n"
        "  //   distruttore della CONNESSIONE.  Con `aioquic` i due istanti\n"
        "  //   coincidono — il cliente di prova chiude tutto — e B3 e\' rimasto\n"
        "  //   verde per cinque giri.  ⛔ Un BROWSER no: chiude la sessione e\n"
        "  //   **tiene viva la connessione**, e da quel momento il posto resta\n"
        "  //   occupato da una sessione che non esiste piu\'.\n"
        "  //\n"
        "  // ⭐ Trovato da B11 il 10 agosto 2026: con Chrome, SETTE `posto\n"
        "  //    NEGATO` su nove tentativi, e la pagina non vedeva altro che\n"
        "  //    silenzio.  E\' la stessa forma del difetto che B3 aveva trovato\n"
        "  //    il giorno prima — il posto che non si libera — in un altro\n"
        "  //    punto, e ⛔ **una prova con un solo tipo di client non poteva\n"
        "  //    vederla**: il difetto vive nella differenza fra i due.\n"
        "  if (rcp_ && (stream_id == rcp_stream_ || stream_id == wt_sessione_)) {\n"
        "    std::println(stderr,\n"
        "                 \"REMOTIX B3: chiuso lo stream {}: la sessione e\' finita, \"\n"
        "                 \"il posto si libera\",\n"
        "                 stream_id);\n"
        "    rcp_libera(rcp_);\n"
        "    rcp_ = nullptr;\n"
        "    rcp_stream_ = -1;\n"
        "  }\n"
        "  if (!httpconn_) {\n    return {};\n  }\n",
        "il posto che si libera con la sessione",
    ),
    # ── 5. wt_accoda con il FIN ─────────────────────────────────────────────
    (
        "http3_server_proto_codec.cc",
        "  wt_uscita_.push_back(\n"
        "    WtUscita{stream_id, std::vector<uint8_t>{dati.begin(), dati.end()}, 0});\n",
        "  wt_uscita_.push_back(\n"
        "    WtUscita{stream_id, std::vector<uint8_t>{dati.begin(), dati.end()}, 0,\n"
        "             false});\n",
        "wt_accoda con il FIN",
    ),
    (
        "http3_server_proto_codec.cc",
        "      wt_vec[0].base = u.dati.data() + u.off;\n"
        "      wt_vec[0].len = u.dati.size() - u.off;\n"
        "      wt_mio = true;\n",
        "      wt_vec[0].base = u.dati.data() + u.off;\n"
        "      wt_vec[0].len = u.dati.size() - u.off;\n"
        "      wt_mio = true;\n"
        "      // ⭐ REMOTIX B3\n"
        "      fin = u.fin ? 1 : 0;\n",
        "il FIN in scrittura",
    ),
    # ── 6. ⛔⭐ IL POSTO SI LIBERA ANCHE QUANDO A CHIUDERE E' IL SERVER ───────
    #    `RCP.md` §4.2: il canale di controllo che si chiude E' la fine della
    #    sessione.  Il verso in cui lo si chiude non cambia la regola — ma il
    #    codice conosceva un verso solo, perche' l'altro non l'aveva mai
    #    percorso nessuno.
    #
    # ⭐ Trovato da B11 il 10 agosto 2026, e SOLO su Chrome: dopo il caso in
    #    cui il server chiude il canale con un FIN, i tre casi successivi
    #    ricevevano `GIA_ATTIVA_REMOTA`.  Su Firefox il trasporto chiudeva lo
    #    stream in tempo e `on_stream_close` liberava il posto lo stesso: il
    #    difetto viveva nella DIFFERENZA fra i due motori.
    #
    # ⚠ E la pagina non poteva rimediare: §4.2 le vieta di spedire dopo la
    #   fine del canale, quindi il `CONGEDO` che libera il posto — la cura del
    #   terzo difetto di B11 — li' e' proprio quel che non deve mandare.
    (
        "http3_server_proto_codec.cc",
        "        if (u.off >= u.dati.size()) {\n"
        "          wt_uscita_.pop_front();\n"
        "        }\n",
        "        if (u.off >= u.dati.size()) {\n"
        "          // ⛔⭐ REMOTIX B3 — RCP.md §4.2: il canale di controllo che si\n"
        "          //    chiude e' la fine della sessione, ANCHE dal lato nostro.\n"
        "          //    Il posto (§8.2 motivo 0x0F) va lasciato QUI, perche' da\n"
        "          //    adesso in poi non arrivera' piu' un byte che lo liberi.\n"
        "          //\n"
        "          // ⛔ E VALE ANCHE PER LO STREAM DELLA SESSIONE.  Con la sola\n"
        "          //    condizione su `rcp_stream_` questa riga era raggiungibile\n"
        "          //    SOLTANTO col server guasto di B11 innestato: e' l'unico\n"
        "          //    che mette un FIN sul canale di controllo.  Sul server\n"
        "          //    vero il nostro FIN va sullo stream della CONNECT — che\n"
        "          //    PORTA la sessione — e i due casi sono la stessa coppia\n"
        "          //    che `on_stream_close` guarda gia' venti righe piu' su.\n"
        "          //\n"
        "          // ⚠ `congeda()` lascia il posto per conto suo su ogni congedo\n"
        "          //   (`banchi/rcp/rcp.c`), quindi qui di solito non resta\n"
        "          //   niente da fare: questa e' la rete per le chiusure che un\n"
        "          //   congedo non ce l'hanno, ed e' idempotente.\n"
        "          if (u.fin && rcp_ &&\n"
        "              (u.stream_id == rcp_stream_ || u.stream_id == wt_sessione_)) {\n"
        "            rcp_canale_chiuso(rcp_);\n"
        "          }\n"
        "          wt_uscita_.pop_front();\n"
        "        }\n",
        "il posto che si libera quando chiude il server",
    ),
    # ── 7. ⛔⭐ LA SECONDA STRADA DI §3.1, CHE FINO A OGGI NESSUNO GUARDAVA ──
    #    §3.1 punto 3: il motivo del congedo viaggia **anche** nel codice di
    #    chiusura.  B2 adesso legge la capsula che lo porta; qui si dice che
    #    cosa significa — ed e' l'unico posto che lo sa, perche' «era gia'
    #    finita» e' uno stato di RCP, non del trasporto.
    #
    # ⭐ Senza questa riga, di Firefox si sarebbe detto «non si congeda»:
    #    azzera lo stream di controllo e butta il `CONGEDO` gia' in coda — il
    #    secondo difetto trovato da B11 — e il motivo gli arriva **solo** di
    #    qui.  ⚠ Due motori, due strade, e una regola sola rispettata da
    #    tutt'e due: e' la ragione per cui §3.1 punto 3 non e' ridondanza.
    (
        "http3_server_proto_codec.cc",
        "void ProtoCodec::wt_chiusa_dal_client(uint32_t codice) { (void)codice; }\n",
        "void ProtoCodec::wt_chiusa_dal_client(uint32_t codice) {\n"
        "  // ⛔⭐ REMOTIX B3 — E PRIMA DI TUTTO SI GUARDA SE QUEL CODICE ESISTE.\n"
        "  //\n"
        "  //    RCP.md §3.1: il codice **0** significa «chiusura senza motivo»\n"
        "  //    e NON DEVE essere usato — ogni chiusura ha un motivo di §8.2.\n"
        "  //    E §3 — la regola di rigore — chiede di scrivere NEL REGISTRO\n"
        "  //    che cosa non si e' capito, non di supplire in silenzio.\n"
        "  //\n"
        "  // ⚠ Prima il codice arrivava troncato a 8 bit: una pagina che\n"
        "  //   chiudesse con `0x0100` faceva scrivere a RCP «motivo 0x00» —\n"
        "  //   cioe' il solo valore che §3.1 vieta — e i due registri della\n"
        "  //   STESSA chiusura si contraddicevano a due righe di distanza.\n"
        "  //   ⛔ E `close()` senza codice, che vale 0, era indistinguibile da\n"
        "  //     una chiusura regolare.\n"
        "  bool motivo_valido = codice >= uint32_t{RCP_CHIUSO_DALL_UTENTE} &&\n"
        "                       codice <= uint32_t{RCP_GIA_ATTIVA_REMOTA};\n"
        "  if (!motivo_valido) {\n"
        "    std::println(stderr,\n"
        "                 \"REMOTIX B3: ⛔ VIOLAZIONE §3.1 — la pagina ha chiuso \"\n"
        "                 \"la sessione col codice {:#x}, che non e' un motivo di \"\n"
        "                 \"§8.2 (0 = «senza motivo», ed e' vietato).  A verbale \"\n"
        "                 \"va ERRORE_PROTOCOLLO, e questa riga dice il codice \"\n"
        "                 \"vero: la sessione e' gia' chiusa dal client, quindi \"\n"
        "                 \"non c'e' piu' niente da congedare\",\n"
        "                 codice);\n"
        "  }\n"
        "  auto motivo = static_cast<uint8_t>(\n"
        "    motivo_valido ? codice : uint32_t{RCP_ERRORE_PROTOCOLLO});\n"
        "  // ⭐ REMOTIX B3 — RCP.md §3.1 punto 3: il motivo nel codice di\n"
        "  //    chiusura e' la seconda strada, e vale quando la prima e' chiusa.\n"
        "  if (rcp_ && rcp_e_finita(rcp_)) {\n"
        "    std::println(stderr,\n"
        "                 \"REMOTIX B3: ⭐ CONGEDO di commiato per la seconda \"\n"
        "                 \"strada di §3.1 (il codice di chiusura): motivo {:#04x} \"\n"
        "                 \"— i byte sul canale non erano piu' spedibili\",\n"
        "                 motivo);\n"
        "  }\n"
        "  // ⛔ E il POSTO si lascia adesso: §4.2, la sessione e' finita perche'\n"
        "  //    lo dice il client.  Aspettare lo smontaggio del trasporto vuol\n"
        "  //    dire tenerlo occupato addosso a chi si ricollega subito.\n"
        "  if (rcp_) {\n"
        "    rcp_chiusa_dal_client(rcp_, motivo);\n"
        "  }\n"
        "}\n",
        "il commiato che viaggia nel codice di chiusura",
    ),
    # ── 8. ⛔⭐ IL FIN DEL CLIENT SUL CANALE DI CONTROLLO — §4.2, l'altra
    #          direzione, che non aveva percorso nessuno.
    #
    #    §4.2: «un FIN su quello stream, **da una qualunque delle due parti**,
    #    chiude la sessione.  Chi lo riceve **DEVE** considerarla finita».  Il
    #    verso server→client era curato (B11, il posto che si libera); questo e'
    #    il verso client→server, ed e' la **stessa forma** del difetto: la
    #    pagina chiude la parte scrivente del canale — `writable.close()` — e
    #    tiene viva la sessione e la connessione.  ⛔ Il posto restava occupato
    #    finche' non moriva la connessione, e una connessione un browser la
    #    tiene viva.
    (
        "http3_server_proto_codec.cc",
        "void ProtoCodec::wt_fin_dal_client(int64_t stream_id) { (void)stream_id; }\n",
        "void ProtoCodec::wt_fin_dal_client(int64_t stream_id) {\n"
        "  if (!rcp_ || stream_id != rcp_stream_) {\n"
        "    return;\n"
        "  }\n"
        "  // ⚠ La riga la scriviamo QUI e non in rcp.c, perche' `rcp.c` non sa\n"
        "  //   da che parte sia arrivato il FIN: il suo registro dice «dal lato\n"
        "  //   del server», che qui sarebbe falso.  Il fatto e' lo stesso —\n"
        "  //   §4.2, la sessione e' finita — e l'effetto pure: si lascia il\n"
        "  //   posto e si resta a guardare se il client spedisce ancora, che e'\n"
        "  //   il DEVE che solo da qui si osserva.\n"
        "  std::println(stderr,\n"
        "               \"REMOTIX B3: ⛔ FIN del CLIENT sul canale di controllo \"\n"
        "               \"(stream {}): §4.2, la sessione e' finita\",\n"
        "               stream_id);\n"
        "  rcp_canale_chiuso(rcp_);\n"
        "}\n",
        "il FIN del client sul canale di controllo",
    ),
]


CORPO = r'''namespace {
// ⭐ REMOTIX B3 — i quattro ganci di `rcp_ganci`, che sono l'unica cosa che
//    RCP sa del mondo di sotto.  Passano da qui e nient'altro: se un giorno
//    il modulo andra' in un server vero, questi quattro si riscrivono e il
//    protocollo no.
void rcp_gancio_manda(void *ctx, const uint8_t *dati, size_t len);
void rcp_gancio_chiudi(void *ctx, uint8_t motivo);
void rcp_gancio_registra(void *ctx, const char *riga);
bool rcp_gancio_verifica(void *ctx, const char *utente, const char *parola);
} // namespace

void ProtoCodec::rcp_avvia(int64_t stream_id) {
  rcp_stream_ = stream_id;

  static const rcp_ganci ganci = {
    nullptr, rcp_gancio_manda, rcp_gancio_chiudi, rcp_gancio_registra,
    rcp_gancio_verifica,
  };
  auto g = ganci;
  g.ctx = this;

  // La provenienza serve al contatore per indirizzo di §4.4-bis e al registro.
  std::array<char, 64> da{};
  auto path = ngtcp2_conn_get_path(conn_);
  if (path && path->remote.addr) {
    util::straddr(path->remote.addr, path->remote.addrlen).copy(da.data(),
                                                               da.size() - 1);
  }

  rcp_ = rcp_apri(&g, da.data(),
                  ngtcp2_conn_get_timestamp(conn_) / NGTCP2_MILLISECONDS);

  // ══ ⛔⭐ E QUI SI ARMA L'OROLOGIO DEL PRIMO TETTO — §4.6 riga 1 ═══════════
  //
  //    `[M]` 10 agosto 2026, banco B6: `ciao-tetto` dava «non e' successo
  //    niente per 20 s».  Gli altri due tetti scattavano — 60 s e 10 s, con
  //    `TEMPO_SCADUTO` — e il primo no: un client che apre il canale di
  //    controllo e poi tace restava appeso per sempre.
  //
  // ⛔ E il difetto non era in `rcp.c`: il tetto del `CIAO` ce l'ha, in
  //    `rcp_tempo()`, accanto agli altri due.  Era che `rcp_tempo()` non lo
  //    chiamava PIU' NESSUNO.  Scorre dal percorso di scrittura, e il
  //    percorso di scrittura in silenzio lo fa passare solo il keep-alive:
  //    che veniva armato soltanto dentro `rcp_passa`, cioe' **solo quando
  //    arrivano dei byte**.  Nello stato `attesa-ciao` di byte non ne e'
  //    arrivato ancora nessuno — l'apertura del canale porta l'intestazione
  //    dello stream WebTransport e basta, e con `resto` vuoto `rcp_passa`
  //    non viene invocata affatto — quindi non lo armava nessuno.
  //
  // ⚠ E' la STESSA FORMA del difetto curato poche ore prima in
  //   `wt_chiudi_sessione`: il segnale che fa scorrere il tempo era armato in
  //   un punto che quel caso non attraversa.  ⛔ Chi mette un tetto deve
  //   accendere anche cio' che lo fara' scadere, e nell'istante in cui il
  //   tetto comincia — non alla prima occasione utile che capita dopo.
  //
  // ⭐ L'istante e' QUESTO: `rcp_apri` mette lo stato a `attesa-ciao` e
  //    `s->da_quando` a adesso.  Il cronometro del server e l'orologio che lo
  //    fa girare partono cosi' dalla stessa riga.
  //
  // ⚠ NON si spegne qui, e nemmeno all'arrivo del `CIAO`: gli altri due
  //   tetti della stretta di mano vogliono lo stesso battito, e `rcp_passa`
  //   lo rimette a ogni messaggio — 100 ms per tutta la stretta, 5 s una
  //   volta `attiva`, che e' l'unico punto in cui si allarga.  Spegnerlo
  //   prima sarebbe rifare il difetto appena curato, un tetto piu' in la'.
  //
  // ⚠ E resta un filo dell'OSPITE, come gli altri: e' il keep-alive del
  //   TRASPORTO, non un battito applicativo (§2.2 lo vieta, e questo non lo
  //   e'), e un server vero armera' un proprio timer senza mettere niente sul
  //   filo.
  if (rcp_) {
    ngtcp2_conn_set_keep_alive_timeout(conn_, 100 * NGTCP2_MILLISECONDS);
  }
  std::println(stderr, "REMOTIX B3: canale di controllo = stream {}", stream_id);
}

void ProtoCodec::rcp_passa(int64_t stream_id, std::span<const uint8_t> dati) {
  if (!rcp_) {
    return;
  }
  auto ora = ngtcp2_conn_get_timestamp(conn_) / NGTCP2_MILLISECONDS;
  if (!rcp_ricevi(rcp_, dati.data(), dati.size(), ora)) {
    return;
  }
  // ⛔ Il ritardo fisso di §4.4-bis dura un secondo, e in quel secondo il
  //    server non ha niente da spedire: senza un timer la risposta non
  //    partirebbe mai.  Il keep-alive di QUIC fa passare il percorso di
  //    scrittura ogni 100 ms — e' un filo dell'ospite, non una regola del
  //    protocollo, e per questo sta qui e non in rcp.c.
  // ⛔ Due stati vogliono un battito, e per due ragioni diverse:
  //
  //   attesa-verdetto  il ritardo fisso di §4.4-bis dura un secondo, e in
  //                    quel secondo non c'e' niente da spedire;
  //   attiva           l'OROLOGIO DEL SILENZIO di §5.3 va valutato mentre il
  //                    client tace — e mentre tace il percorso di scrittura
  //                    non lo percorre nessuno.
  //
  // ⛔ E IL PRIMO ARMO NON STA QUI: sta in `rcp_avvia`, dove la sessione RCP
  //    nasce.  Qui si arriva solo quando dei byte sono arrivati, e nello stato
  //    `attesa-ciao` non ne e' arrivato ancora nessuno: armarlo soltanto di
  //    qui lasciava il tetto del `CIAO` senza nessuno che lo facesse scadere
  //    (`[M]` 10 agosto 2026, B6).  Queste righe non ACCENDONO il battito:
  //    lo REGOLANO mano a mano che lo stato cambia.
  //
  // ⚠ E' un battito del TRASPORTO (il keep-alive di QUIC), non un battito
  //   applicativo: §2.2 vieta il secondo, e questo non lo e'.  ⛔ Resta pero'
  //   un filo dell'OSPITE: un server vero armera' un proprio timer e non
  //   mettera' niente sul filo.  Sta scritto perche' non venga ereditato per
  //   distrazione.
  auto stato = std::string_view{rcp_stato_nome(rcp_)};
  if (stato == "attesa-verdetto") {
    ngtcp2_conn_set_keep_alive_timeout(conn_, 100 * NGTCP2_MILLISECONDS);
  } else if (stato == "attiva") {
    ngtcp2_conn_set_keep_alive_timeout(conn_, 5 * NGTCP2_SECONDS);
  } else {
    // ⚠ Gli stati di mezzo della stretta di mano — `attesa-attacca` e simili:
    //   il battito resta fitto perche' la stretta non e' ancora finita.
    //
    // ⛔ E QUI C'ERA SCRITTO «anche dopo la fine il percorso di scrittura deve
    //    continuare a passare: la capsula che chiude la sessione parte di
    //    li'».  ⚠ Era FALSO, ed e' costato i quattordici casi di B5 del 10
    //    agosto 2026: dopo la fine questa riga NON si raggiunge, perche'
    //    venti righe piu' su `rcp_ricevi` restituisce false — «la sessione e'
    //    finita» — e si esce.  Il battito che fa maturare l'attesa della
    //    capsula lo arma `wt_chiudi_sessione`, che e' l'unico punto
    //    attraversato da TUTTE le strade della chiusura, comprese le due che
    //    da qui non passano affatto.
    ngtcp2_conn_set_keep_alive_timeout(conn_, 100 * NGTCP2_MILLISECONDS);
  }
}

namespace {
void rcp_gancio_manda(void *ctx, const uint8_t *dati, size_t len) {
  auto pc = static_cast<ProtoCodec *>(ctx);
  pc->wt_manda_controllo(dati, len);
}

void rcp_gancio_chiudi(void *ctx, uint8_t motivo) {
  auto pc = static_cast<ProtoCodec *>(ctx);
  pc->wt_chiudi_sessione(motivo);
}

void rcp_gancio_registra(void *ctx, const char *riga) {
  (void)ctx;
  std::println(stderr, "REMOTIX B3: {}", riga);
}

bool rcp_gancio_verifica(void *ctx, const char *utente, const char *parola) {
  (void)ctx;
  // ⚠ PAM blocca.  In un banco va bene e si dichiara; in un server vero la
  //   verifica andra' su un filo a parte, o la stretta di mano di un utente
  //   ferma quella di tutti gli altri.
  return rcp_autentica(utente, parola);
}
} // namespace

// ⛔ REMOTIX B5 — RCP.md §2.5: gli stream unidirezionali aperti dal CLIENT.
//
// ⭐ Come si riconosce il canale: «si leggono i primi due byte dello stream,
//    che sono in ogni caso un campo `tipo`».  Il byte alto dice il canale, e
//    di cinque valori leciti **tre sono violazioni quando arrivano di qui**:
//
//    0x00  controllo  ⛔ «il controllo vive solo sullo stream 0»
//    0x01  input      ✓  legale: e' l'unico unidirezionale che il client apre
//    0x02  appunti    ✓  legale, uno per trasferimento
//    0x03  video      ⛔ verso sbagliato: il video va dal server al client
//    0x04  audio      ⛔ «solo su datagram.  Su uno stream e' ERRORE_PROTOCOLLO»
//
// ⚠ E prima ancora bisogna sapere se lo stream e' NOSTRO: fra gli
//   unidirezionali del client ci sono il canale di controllo di HTTP/3 e i due
//   di QPACK, che sono di nghttp3.  Uno stream WebTransport si riconosce dal
//   suo tipo, 0x54 — che come 0x41 non sta in un byte: sul filo sono 0x40 0x54.
ProtoCodec::WtEsito ProtoCodec::wt_smista_uni(int64_t stream_id,
                                              std::span<const uint8_t> data,
                                              std::vector<uint8_t> &riunito) {
  if (wt_nonwt_.contains(stream_id)) {
    return WtEsito::HTTP3;
  }
  if (auto giudizio = wt_uni_.find(stream_id); giudizio != wt_uni_.end()) {
    // Gia' giudicato — ⚠ ma i due giudizi NON sono la stessa cosa, e il
    // commento di prima ne diceva uno solo («la sessione e' gia' caduta»), che
    // per i due canali leciti e' falso:
    //
    //   true   violazione: la sessione e' gia' caduta, e non c'e' piu' niente
    //          da servire;
    //   false  canale LECITO di §2.5 — `0x01` input, `0x02` appunti — che
    //          questa fase non serve ancora: l'input arriva alla fase 4, gli
    //          appunti alla 7.
    //
    // ⛔ Prima `wt_uni_` veniva scritto a `true` per tutt'e cinque i valori di
    //    `canale`, quindi anche per i due leciti: un client conforme apriva il
    //    canale di input, si sentiva rispondere «lecito» — e da quel momento
    //    OGNI suo byte finiva qui dentro, scartato per sempre e senza una riga
    //    di registro, sotto un commento che affermava una caduta che non c'era.
    //
    // ⚠ La tolleranza si dichiara UNA VOLTA, quando lo stream viene
    //   riconosciuto (RCP.md §3, ultima riga: «ogni tolleranza va scritta nel
    //   registro»), non a ogni pacchetto: una riga per pacchetto renderebbe il
    //   registro illeggibile, e il registro e' il testimone di B11.
    //
    // In tutt'e due i casi i byte si contano nel credito: non contarli
    // lascerebbe il client senza credito su una connessione viva (§2.3).
    if (!data.empty()) {
      ngtcp2_conn_extend_max_stream_offset(conn_, stream_id, data.size());
      ngtcp2_conn_extend_max_offset(conn_, data.size());
    }
    return WtEsito::MIO;
  }

  auto &pref = wt_incerti_[stream_id];
  pref.insert(pref.end(), data.begin(), data.end());
  if (pref.size() < 2) {
    return WtEsito::ATTENDI;
  }
  if (!(pref[0] == 0x40 && pref[1] == 0x54)) {
    // Non e' WebTransport: e' di nghttp3, e i byte vanno consegnati interi.
    riunito = pref;
    wt_incerti_.erase(stream_id);
    wt_nonwt_[stream_id] = true;
    return WtEsito::HTTP3;
  }
  uint64_t sessione = 0;
  auto n = wt_leggi_varint(&sessione, pref.data() + 2, pref.size() - 2);
  if (n == 0 || pref.size() < 2 + n + 2) {
    return WtEsito::ATTENDI; // il campo `tipo` non e' ancora tutto arrivato
  }
  auto consumati = pref.size();
  uint16_t tipo = static_cast<uint16_t>(pref[2 + n] << 8 | pref[2 + n + 1]);
  auto canale = static_cast<uint8_t>(tipo >> 8);
  wt_incerti_.erase(stream_id);
  ngtcp2_conn_extend_max_stream_offset(conn_, stream_id, consumati);
  ngtcp2_conn_extend_max_offset(conn_, consumati);

  const char *guasto = nullptr;
  switch (canale) {
  case 0x00:
    guasto = "il canale di CONTROLLO su uno stream unidirezionale: "
             "il controllo vive solo sullo stream 0 (§2.5)";
    break;
  case 0x03:
    guasto = "il canale VIDEO dal client: e' del server, verso sbagliato (§2.5)";
    break;
  case 0x04:
    guasto = "il canale AUDIO su uno stream: l'audio vive solo sui datagram "
             "(§2.5, §6.3)";
    break;
  case 0x01:
  case 0x02:
    break;
  default:
    guasto = "byte alto del tipo sconosciuto su uno stream unidirezionale (§2.5)";
    break;
  }
  // ⛔ E il giudizio si registra DOPO averlo emesso, non prima: `true` vuol
  //    dire «violazione, la sessione e' caduta», e scriverlo per tutti i
  //    canali era quel che faceva sparire i byte dei due leciti.
  wt_uni_[stream_id] = guasto != nullptr;
  std::println(stderr,
               "REMOTIX B5: stream unidirezionale {} del client, sessione {}, "
               "tipo {:#06x}, canale {:#04x} — {}",
               stream_id, sessione, tipo, canale,
               guasto ? "VIOLAZIONE"
                      : "lecito (§2.5).  ⚠ Ma questa fase non lo serve: i byte "
                        "si contano nel credito e si scartano, e questa riga "
                        "e' la tolleranza dichiarata (§3)");
  if (guasto) {
    if (rcp_) {
      rcp_violazione(rcp_, guasto);
    } else {
      // ⚠ Nessun canale di controllo ancora aperto: il `CONGEDO` non ha una
      //   strada, e resta il punto 3 di §3.1 — il motivo dentro la chiusura
      //   della sessione.  ⭐ E' il secondo condizionale di §3.1 all'opera:
      //   pretendere tutt'e tre i punti sempre darebbe rosso sul codice
      //   giusto (rilievo R3.3).
      std::println(stderr, "REMOTIX B5: ⚠ nessun canale di controllo: il motivo "
                           "viaggia solo nella chiusura della sessione");
      wt_chiudi_sessione(0x0B);
    }
  }
  return WtEsito::MIO;
}

void ProtoCodec::wt_manda_controllo(const uint8_t *dati, size_t len) {
  if (rcp_stream_ == -1) {
    return;
  }
  wt_accoda(rcp_stream_, std::span<const uint8_t>{dati, len});
}

void ProtoCodec::wt_chiudi_sessione(uint8_t motivo) {
  // ⛔ RCP.md §3.1 punto 3: si chiude la SESSIONE WebTransport con il codice
  //    d'errore applicativo pari al codice del motivo — non la connessione
  //    QUIC, che puo' reggere altro.
  //
  // In byte e' la capsula CLOSE_WEBTRANSPORT_SESSION (tipo 0x2843) sullo
  // stream della CONNECT estesa, seguita dal FIN.
  if (wt_sessione_ == -1) {
    return;
  }
  // ⛔⭐ E LA CAPSULA SI RIMANDA, invece di accodarla adesso — trovato da B11
  //    il 10 agosto 2026, con browser veri.
  //
  //    `respingi()` manda `RESPINTO` sul canale di controllo e chiude la
  //    sessione **nella riga dopo**.  I due finivano nella stessa passata di
  //    scrittura, cioe' spesso nello stesso volo di pacchetti — e il browser
  //    processa la capsula `CLOSE_WEBTRANSPORT_SESSION` **prima** dei byte
  //    dello stream, che a quel punto butta.  ⛔ La pagina non ha mai visto
  //    `RESPINTO`: ha visto **silenzio**.
  //
  // ⚠ E il punto 3 di §3.1 ha fatto il suo mestiere — il motivo e' arrivato
  //   comunque, dentro il codice di chiusura — ma il punto 2 era perduto, e
  //   §3.1 li vuole tutt'e due quando il canale e' utilizzabile.
  //
  // ⛔ E ACCODARE LA CAPSULA DIETRO AL `CONGEDO`, NELLA STESSA CODA, NON E'
  //    LA CURA: E' ESATTAMENTE IL CODICE CHE B11 HA TROVATO ROTTO.  La coda
  //    e' ordinata e serve un elemento per passata, quindi l'ordine sul filo
  //    ci sarebbe — ⚠ ma l'ordine sul filo non e' quel che manca.  I due
  //    finiscono comunque nello stesso volo, il browser processa la capsula
  //    prima di consegnare i byte dello stream alla pagina, e la pagina non
  //    vede il `CONGEDO`.  Quel che serve e' TEMPO fra i due, ed e' quel che
  //    l'attesa compra.
  //
  // ⭐ Qui si segna soltanto l'intenzione: la capsula la accoda il ciclo di
  //    scrittura quando la coda e' vuota, cioe' quando i byte del `CONGEDO`
  //    sono gia' stati consegnati a ngtcp2.
  wt_chiusura_ = motivo;
  // ⛔ E l'attesa riparte da ZERO: le cinque passate si contano da QUESTA
  //    chiusura.  Senza, una seconda chiusura sulla stessa connessione
  //    troverebbe il contatore gia' oltre il cinque e manderebbe la capsula
  //    nella stessa passata del suo `CONGEDO` — cioe' il difetto che l'attesa
  //    esiste per togliere, ricomparso al secondo giro.
  wt_chiusura_attesa_ = 0;
  // ══ ⛔⭐ REMOTIX B5 — E QUI SI ARMA L'OROLOGIO CHE FA MATURARE L'ATTESA ══
  //
  //    `[M]` 10 agosto 2026: «§3.1 punto 3 — motivo nella chiusura WT» dava
  //    22 su 36, e i quattordici mancanti erano TUTTI violazioni trovate al
  //    primo messaggio.  Nel registro del server, per `versione-2`, c'era
  //    `congedo motivo=0x0a` e NON c'era «chiusa la sessione WebTransport»:
  //    la capsula non e' mai partita.
  //
  // ⛔ E il difetto non era l'attesa: erano le passate, che non arrivavano.
  //    Il keep-alive lo armava soltanto `rcp_passa`, e solo DOPO
  //    `rcp_ricevi` — che su una violazione restituisce false, perche' la
  //    sessione e' finita.  Su una violazione al PRIMO messaggio quel punto
  //    non veniva mai raggiunto nemmeno una volta: il client non spediva
  //    piu' niente, il percorso di scrittura non veniva piu' percorso, e
  //    `wt_chiusura_attesa_` restava fermo a uno o due per sempre.  ⚠ E le
  //    altre due strade della chiusura — `wt_smista` per il secondo stream
  //    bidirezionale, `wt_smista_uni` quando un canale di controllo non c'e'
  //    ancora — da `rcp_passa` non passano affatto.
  //
  // ⭐ Per questo l'orologio si arma QUI, dove l'intenzione viene segnata:
  //    e' l'unico punto che tutte le strade attraversano, e ⛔ chi rimanda un
  //    lavoro deve accendere anche cio' che lo fara' maturare — un lavoro
  //    rimandato a una condizione che nessuno fa piu' avvenire non e'
  //    rimandato, e' perduto, e nel registro somiglia a un lavoro non
  //    chiesto.
  //
  // ⚠ L'ordine fra il `CONGEDO` e la capsula NON cambia: restano le cinque
  //   passate a coda vuota, che a 100 ms sono mezzo secondo.  Qui non si
  //   accorcia e non si toglie niente — si fa solo esistere il tempo che
  //   l'attesa gia' pretendeva.
  //
  // ⚠ E resta un filo dell'OSPITE, come gli altri tre: un server vero armera'
  //   un proprio timer e non mettera' niente sul filo (§2.2).
  ngtcp2_conn_set_keep_alive_timeout(conn_, 100 * NGTCP2_MILLISECONDS);
  std::println(stderr,
               "REMOTIX B3: chiusura della sessione RIMANDATA, codice {:#04x} "
               "(in coda: {}; keep-alive a 100 ms perche' le cinque passate "
               "maturino)",
               motivo, wt_uscita_.size());
}

void ProtoCodec::wt_chiudi_adesso(uint8_t motivo) {
  // ⛔⭐ LA CAPSULA VA DENTRO UN FRAME `DATA`, E FINO AL 10 AGOSTO USCIVA NUDA.
  //
  //    Il corpo di una CONNECT estesa e' un flusso di capsule (RFC 9297), ma
  //    in HTTP/3 il corpo di un messaggio viaggia dentro frame `DATA`: la
  //    capsula NON sta nuda sullo stream.  ⭐ E che il client le incapsuli lo
  //    dimostra il nostro stesso lato di LETTURA: `wt_capsula` la chiama
  //    `http_recv_data`, che nghttp3 invoca soltanto sul carico utile di un
  //    `DATA`.  Se le capsule non ci fossero dentro, quella funzione non
  //    sarebbe mai stata chiamata — e su Firefox e' stata chiamata `[M]`.
  //
  // ⛔ Le due direzioni non potevano essere tutt'e due giuste, e la sbagliata
  //    era questa.  Scritti nudi, i sette byte `68 43 04 00 00 00 mm` il
  //    browser li legge col proprio strato HTTP/3: `0x68` ha i due bit alti a
  //    `01`, quindi e' un intero variabile di due byte, e il tipo di frame
  //    diventa `0x2843` — che **non e' un tipo di frame HTTP/3 noto**, e RFC
  //    9114 §9 impone di IGNORARLO.  La pagina non vedeva nessuna capsula:
  //    vedeva solo il FIN che arriva subito dietro, e un FIN sullo stream
  //    della CONNECT senza `CLOSE_WEBTRANSPORT_SESSION` chiude la sessione con
  //    codice **0**.
  //
  // ⚠ Cioe' e' il `congedo:0x00` che B11 ha visto e che era stato attribuito a
  //   una corsa fra eventi: questa strada lo produce **in ogni giro**, non uno
  //   su cinque.  ⭐ La misura che distingue le due spiegazioni e' scritta nel
  //   rapporto: far chiudere il server con `0x0b` senza nessun `RESPINTO` in
  //   coda, e leggere `wt.closed` dalla pagina.
  std::array<uint8_t, 64> b{};
  size_t n = 0;
  // la busta: un frame DATA di HTTP/3, tipo 0x00, lungo quanto la capsula
  b[n++] = 0x00; // DATA
  b[n++] = 7;    // 2 byte di tipo + 1 di lunghezza + 4 di codice
  // la capsula CLOSE_WEBTRANSPORT_SESSION
  b[n++] = 0x68; // 0x2843 in intero variabile, primo byte
  b[n++] = 0x43;
  b[n++] = 4;    // lunghezza della capsula: solo il codice
  b[n++] = 0;
  b[n++] = 0;
  b[n++] = 0;
  b[n++] = motivo;
  wt_uscita_.push_back(WtUscita{
    wt_sessione_, std::vector<uint8_t>{b.data(), b.data() + n}, 0, true});
  std::println(stderr,
               "REMOTIX B3: chiusa la sessione WebTransport, codice {:#04x} "
               "({} byte: 2 di frame DATA + 7 di capsula)",
               motivo, n);
}

'''

# ===========================================================================
# ⛔⭐ IL BAN LATO OSPITE — le tre cose che §4.4-bis chiede al PADRONE DI CASA
# ===========================================================================
#
# `rcp.c` sa contare i fallimenti, bannare, salvare su file, rispondere «e'
# bannato?» e togliere un ban.  ⛔ Ma non apre socket, non legge la riga di
# comando e non serve nessuna pagina: le tre cose che seguono **non esistevano**
# fino all'11 agosto 2026, e senza di esse la regola dell'utente era scritta a
# meta'.
#
#   1. i ban si RILEGGONO all'avvio          §4.4-bis, «il ban sopravvive al
#                                            riavvio del server» — invariante I7
#   2. la PAGINA si serve lo stesso a chi     §4.4-bis, «viene visualizzata una
#      e' bannato, e dice quante ore mancano  pagina di login rifiutato»
#   3. il COMANDO DI SBLOCCO                  §4.4-bis, «si esce in due modi»
#
CORPO_OSPITE = r'''// ═══════════════════════════════════════════════════════════
// ⛔⭐ REMOTIX B3 — IL BAN LATO OSPITE (RCP.md §4.4-bis, DECISIONI.md §1.9)
//
// ⛔ PERCHE' STA QUI E NON IN `rcp.c`.  Quel file «conosce RCP.md e nient'altro:
//    non sa che sotto c'e' QUIC, non apre socket e non guarda l'orologio».  Le
//    tre cose di sotto sono tutte e tre socket, riga di comando e orologio —
//    cioe' tutte e tre del padrone di casa.  ⭐ `rcp.c` espone `rcp_ban_carica`,
//    `rcp_bannato` e `rcp_sblocca` e non sa **chi** le chiama: e' la stessa
//    linea che permettera' di portare il protocollo nel server vero senza
//    riscriverlo.
//
// ⛔ E L'OROLOGIO DEV'ESSERE LO STESSO.  `rcp_apri`/`rcp_ricevi` ricevono
//    `ngtcp2_conn_get_timestamp(conn_) / NGTCP2_MILLISECONDS`, e ngtcp2 quel
//    valore lo prende da `util::timestamp()`.  Qui non c'e' nessuna
//    connessione, quindi si chiama `util::timestamp()` direttamente: ⚠ un
//    secondo orologio con un'altra origine renderebbe le scadenze del ban
//    numeri senza senso — «restano 4 miliardi di ore» — e nessuno lo vedrebbe
//    finche' qualcuno non viene bannato davvero.
// ═══════════════════════════════════════════════════════════════════════════
#include <sys/un.h>
#include <cerrno>

extern "C" {
#include "rcp.h"
}

namespace {

// L'orologio monotono in millisecondi: LO STESSO che vede la sessione.
uint64_t remotix_ora_ms() { return util::timestamp() / NGTCP2_MILLISECONDS; }

// Le due strade del padrone di casa, dalla riga di comando.
const char *remotix_ban_file = nullptr;
const char *remotix_comando_socket = nullptr;

ev_io remotix_pagina_ev;
ev_io remotix_comando_ev;
bool remotix_pagina_accesa = false;
bool remotix_comando_acceso = false;

// ⛔ 200 ms, e il prezzo si dichiara invece di nasconderlo.  Qui la pagina e il
//    comando si servono DENTRO il ciclo degli eventi di QUIC, con una lettura e
//    una scrittura bloccanti a tempo: un client TCP che apre e tace ferma il
//    server per due decimi di secondo.  ⚠ E' accettabile in un banco e va
//    scritto qui: un server vero mettera' un `ev_io` per ogni connessione
//    accettata, o un filo a parte.  ⭐ Il motivo per cui NON lo si fa oggi e'
//    che `rcp.c` tiene la tabella dei ban in memoria statica senza nessun
//    lucchetto: un filo a parte sarebbe una corsa fra due scrittori, cioe' un
//    difetto vero comprato per evitare un ritardo finto.
const timeval REMOTIX_TETTO{0, 200000};

// ── Quel che si legge e si scrive, con un tetto e senza mai bloccare per
//    sempre.  Restituiscono false su qualunque guasto: chi chiama chiude e va
//    avanti — una connessione TCP persa non deve portarsi via il server.
bool remotix_scrivi_tutto(int fd, std::string_view dati) {
  while (!dati.empty()) {
    auto n = send(fd, dati.data(), dati.size(), MSG_NOSIGNAL);
    if (n <= 0) {
      return false;
    }
    dati.remove_prefix(static_cast<size_t>(n));
  }
  return true;
}

// ═══ 1. LA PAGINA ═══════════════════════════════════════════════════════════
//
// ⛔ §4.4-bis, e la ragione e' dell'utente: «la pagina si serve lo stesso, e
//    mostra il rifiuto — *tentativi esauriti*.  Non un errore di rete, non un
//    silenzio: chi e' stato bannato per errore e' quasi sempre il proprietario,
//    e deve poter capire che cosa gli e' successo invece di trovarsi davanti un
//    server che sembra morto per mezza giornata».
//
// ⛔ E LO STATO E' 200, ANCHE PER CHI E' BANNATO — scelta, non distrazione.
//    §4.4-bis dice «la pagina si serve lo stesso» e non dice con quale stato
//    HTTP.  Con un 403 il documento sarebbe comunque servito, ⚠ ma un proxy,
//    un'estensione o il browser stesso possono sostituire il corpo di una
//    risposta d'errore con una propria schermata — e allora la frase che
//    l'utente DEVE leggere sparisce, che e' esattamente il caso che questa
//    regola esiste per impedire.  ⭐ Il rifiuto e' dell'ACCESSO, non della
//    pagina: la pagina ha fatto il suo mestiere.
std::string remotix_pagina_html(bool bannato, const std::string &chiave,
                                uint64_t restano_ms) {
  if (!bannato) {
    return std::format(
      "<!doctype html>\n<html lang=\"it\">\n<head><meta charset=\"utf-8\">\n"
      "<title>REMOTIX — accesso</title></head>\n"
      "<body data-bannato=\"no\" data-restano-ms=\"0\">\n"
      "<h1 id=\"esito\">accesso</h1>\n"
      "<p id=\"quanto\">Questo indirizzo ({}) puo' provare a entrare.</p>\n"
      "<p>⚠ Pagina minima del banco: la pagina vera di RCP arriva con la fase "
      "successiva.  Qui c'e' la sola cosa che §4.4-bis pretende dal padrone di "
      "casa — dire se l'indirizzo e' fuori, e per quanto.</p>\n"
      "</body>\n</html>\n",
      chiave);
  }
  // ⚠ I minuti si arrotondano PER ECCESSO: dire «restano 0 ore» a chi ha
  //   ancora 59 minuti da aspettare e' peggio che non dire niente.
  auto minuti = (restano_ms + 59999) / 60000;
  auto ore = minuti / 60;
  auto resto = minuti % 60;
  return std::format(
    "<!doctype html>\n<html lang=\"it\">\n<head><meta charset=\"utf-8\">\n"
    "<title>REMOTIX — tentativi esauriti</title></head>\n"
    "<body data-bannato=\"si\" data-restano-ms=\"{}\">\n"
    "<h1 id=\"esito\">tentativi esauriti</h1>\n"
    "<p id=\"quanto\">Da questo indirizzo ({}) sono arrivati tre tentativi di "
    "accesso falliti, e per questo resta fuori.  Mancano ancora "
    "<b id=\"ore\">{}</b> ore e <b id=\"minuti\">{}</b> minuti.</p>\n"
    "<p id=\"uscite\">Si rientra in due modi: aspettando la scadenza, oppure "
    "col comando di sblocco sulla macchina che serve — che chiede l'accesso a "
    "quella macchina, ed e' la via di chi si e' bannato dal proprio "
    "telefono.</p>\n"
    "</body>\n</html>\n",
    restano_ms, chiave, ore, resto);
}

void remotix_pagina_servi(int fd, const sockaddr *sa, socklen_t salen) {
  setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &REMOTIX_TETTO, sizeof REMOTIX_TETTO);
  setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &REMOTIX_TETTO, sizeof REMOTIX_TETTO);

  // ⛔ La richiesta si LEGGE anche se non ci serve, e non e' cortesia: chiudere
  //    un socket con byte non letti nel buffer manda un RST, e il RST fa
  //    buttare al client la risposta che gli abbiamo appena scritto.  Chi e'
  //    bannato vedrebbe «connessione azzerata» — cioe' l'errore di rete che
  //    §4.4-bis vieta — e il server nel registro direbbe di aver risposto.
  std::array<char, 4096> richiesta;
  auto letti = recv(fd, richiesta.data(), richiesta.size(), 0);

  // ⛔ E L'INDIRIZZO SI CHIEDE AL NUCLEO, NELLA STESSA FORMA DELLA SESSIONE.
  //    `util::straddr()` scrive `[127.0.0.1]:55680` — con le quadre anche per
  //    IPv4 — e quella e' la chiave che `rcp.c` conta e che finisce nel file
  //    dei ban.  ⚠ Costruirla qui in un altro modo (`inet_ntop` nudo) darebbe
  //    `127.0.0.1`, che NON e' `[127.0.0.1]`: la pagina direbbe «puoi entrare»
  //    a un indirizzo bannato, e il registro del server direbbe il contrario.
  //    `[M]` la forma con le quadre e' letta nel registro, non dedotta.
  auto provenienza = util::straddr(sa, salen);
  std::array<char, 64> chiave{};
  rcp_chiave_indirizzo(provenienza.c_str(), chiave.data(), chiave.size());

  uint64_t restano = 0;
  auto fuori = rcp_bannato(provenienza.c_str(), remotix_ora_ms(), &restano);
  auto corpo = remotix_pagina_html(fuori, std::string{chiave.data()}, restano);
  auto testa = std::format("HTTP/1.1 200 OK\r\n"
                           "Content-Type: text/html; charset=utf-8\r\n"
                           "Content-Length: {}\r\n"
                           "Cache-Control: no-store\r\n"
                           "Connection: close\r\n"
                           "\r\n",
                           corpo.size());
  auto scritta = remotix_scrivi_tutto(fd, testa) && remotix_scrivi_tutto(fd, corpo);
  std::println(stderr,
               "REMOTIX B3: pagina TCP a {} (chiave {}) — {} · richiesta {} "
               "byte · risposta {} byte {}",
               provenienza, chiave.data(),
               fuori ? std::format("BANNATO, restano {} ms", restano)
                     : std::string{"non bannato"},
               letti, corpo.size(),
               scritta ? "spedita" : "⛔ NON spedita per intero");
}

void remotix_pagina_cb(struct ev_loop *loop, ev_io *w, int revents) {
  (void)loop;
  (void)revents;
  sockaddr_storage chi{};
  socklen_t quanto = sizeof chi;
  auto fd = accept(w->fd, reinterpret_cast<sockaddr *>(&chi), &quanto);
  if (fd == -1) {
    return;
  }
  remotix_pagina_servi(fd, reinterpret_cast<sockaddr *>(&chi), quanto);
  close(fd);
}

// ═══ 2. IL COMANDO DI SBLOCCO ═══════════════════════════════════════════════
//
// ⛔ PERCHE' UN SOCKET DI CONTROLLO, E NON LE ALTRE DUE FORME.  §4.4-bis chiede
//    «un comando di sblocco sul server», «la via d'uscita di chi si banna dal
//    proprio telefono», che «chiede l'unica chiave che quel caso ammette —
//    l'accesso alla macchina», e che **scriva nel registro ogni sblocco**
//    distinguendo un ban tolto da un ban mai scattato.  Tre forme erano
//    possibili e due non reggono:
//
//    ⛔ un SECONDO PROCESSO con un'opzione (`bsslserver --sblocca X`) —
//       **non funziona**, e il modo in cui non funziona e' silenzioso: il ban
//       vive nella memoria del processo che serve, e un secondo processo puo'
//       solo riscrivere il file.  Il server continuerebbe a rispondere
//       `TROPPI_TENTATIVI` fino al riavvio, e ⛔ il primo `salva_ban()` — cioe'
//       il primo ban di chiunque altro — riscriverebbe il file rimettendoci
//       dentro il ban appena tolto.  Chi ha dato il comando lo ha visto uscire
//       con zero;
//    ⛔ un SEGNALE — non porta un indirizzo.  `SIGUSR1` potrebbe togliere
//       *tutti* i ban, che e' un comando diverso da quello chiesto, e
//       soprattutto **non ha una risposta**: §4.4-bis vuole che «non era
//       bannato» e «l'ho tolto» si distinguano, e un segnale consegnato dice
//       solo che e' stato consegnato;
//    ⭐ un SOCKET DI CONTROLLO — porta l'indirizzo, agisce sul processo VIVO
//       (memoria e file nella stessa riga, per mano di `rcp_sblocca()`), e
//       **risponde**, quindi le due risposte esistono davvero.  La chiave che
//       chiede e' un file con permessi `0600` nel filesystem della macchina,
//       cioe' esattamente «l'accesso alla macchina» — e non aggiunge nessuna
//       superficie raggiungibile dalla rete: un socket di dominio Unix non ha
//       un indirizzo IP.
//
// Il protocollo e' una riga, e si legge senza strumenti:
//
//     SBLOCCA <indirizzo>   →   TOLTO <chiave>      il ban c'era e non c'e' piu'
//                           →   NON-BANNATO <chiave>  non c'era niente da togliere
//     PING                  →   PONG                 «il comando esiste?», e non
//                                                    tocca niente
//
// ⭐ `PING` non e' un ornamento: e' il denominatore di B0.3.  Un banco che
//    chiama lo sblocco fra un banco e l'altro deve poter dire «il comando c'era
//    e ha risposto», o «il ban non e' scattato» e «lo sblocco non e' mai
//    arrivato a nessuno» hanno lo stesso aspetto.
void remotix_comando_servi(int fd) {
  setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &REMOTIX_TETTO, sizeof REMOTIX_TETTO);
  setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &REMOTIX_TETTO, sizeof REMOTIX_TETTO);
  std::array<char, 256> buf{};
  auto letti = recv(fd, buf.data(), buf.size() - 1, 0);
  if (letti <= 0) {
    std::println(stderr, "REMOTIX B3: ⚠ comando vuoto sul socket di controllo "
                         "(letti {} byte): non ho tolto niente",
                 letti);
    remotix_scrivi_tutto(fd, "NON-CAPITO riga vuota\n");
    return;
  }
  std::string riga{buf.data(), static_cast<size_t>(letti)};
  while (!riga.empty() && (riga.back() == '\n' || riga.back() == '\r')) {
    riga.pop_back();
  }
  if (riga == "PING") {
    std::println(stderr, "REMOTIX B3: comando PING — il socket di sblocco e' "
                         "vivo, e non ho toccato nessun ban");
    remotix_scrivi_tutto(fd, "PONG\n");
    return;
  }
  constexpr std::string_view verbo = "SBLOCCA ";
  if (!riga.starts_with(verbo)) {
    std::println(stderr, "REMOTIX B3: ⚠ comando sconosciuto «{}»: non ho tolto "
                         "niente (le forme sono «SBLOCCA <indirizzo>» e «PING»)",
                 riga);
    remotix_scrivi_tutto(fd, std::format("NON-CAPITO {}\n", riga));
    return;
  }
  auto chiesto = riga.substr(verbo.size());
  // ⛔ La chiave la costruisce `rcp.c`, non questo file: chi comanda digita
  //    `192.168.0.2`, e nel file dei ban c'e' scritto `[192.168.0.2]`.
  std::array<char, 64> chiave{};
  rcp_chiave_indirizzo(chiesto.c_str(), chiave.data(), chiave.size());
  auto era = rcp_sblocca(chiave.data(), remotix_ora_ms());
  // ⛔ «Ogni sblocco si scrive nel registro, o un ban tolto e un ban mai
  //    scattato hanno lo stesso aspetto» (§4.4-bis).  Le due righe sono
  //    diverse, e lo e' anche la risposta a chi comanda.
  if (era) {
    std::println(stderr,
                 "REMOTIX B3: ⛔ SBLOCCATO su comando l'indirizzo {} (chiesto "
                 "«{}»): il ban c'era ed e' stato tolto, e il file dei ban e' "
                 "stato riscritto (§4.4-bis)",
                 chiave.data(), chiesto);
  } else {
    std::println(stderr,
                 "REMOTIX B3: sblocco chiesto per {} (chiesto «{}»): NON era "
                 "bannato, non ho tolto niente (§4.4-bis) — ⚠ e il conto dei "
                 "tentativi di quell'indirizzo riparte comunque da zero",
                 chiave.data(), chiesto);
  }
  remotix_scrivi_tutto(fd, std::format("{} {}\n", era ? "TOLTO" : "NON-BANNATO",
                                       chiave.data()));
}

void remotix_comando_cb(struct ev_loop *loop, ev_io *w, int revents) {
  (void)loop;
  (void)revents;
  auto fd = accept(w->fd, nullptr, nullptr);
  if (fd == -1) {
    return;
  }
  remotix_comando_servi(fd);
  close(fd);
}

// ═══ 3. L'AVVIO ═════════════════════════════════════════════════════════════
//
// ⛔ «ZERO BAN» E «NON HO POTUTO LEGGERE IL FILE» SONO DUE FATTI DIVERSI, e
//    questa e' la funzione in cui il difetto di `LEZIONI.md` §1.9 sarebbe piu'
//    caro di tutti: un errore letto come uno zero e' **la protezione spenta con
//    l'aria di non avere niente da proteggere**, cioe' l'invariante I7 persa in
//    silenzio.  Qui i fatti stampati sono TRE, e si distinguono guardando il
//    file prima di aprirlo:
//
//      il file non c'e' ancora        nessun ban, e non e' un errore
//      il file c'e' e dice zero       nessun ban, e l'ho letto
//      il file c'e' e non si legge    ⛔ NON parto
//
// ⛔ E sul terzo il server ESCE, che e' la sola scelta difendibile: servire con
//    la protezione spenta somiglia in tutto a servirla accesa, e chi ha
//    riavviato per un altro motivo non saprebbe di averla persa.  ⚠ Sugli altri
//    due guasti — la porta della pagina, il socket del comando — il server va
//    avanti: senza pagina e senza comando la protezione **c'e' ancora**, e
//    spegnere il server QUIC su cui poggiano cinque altri banchi metterebbe il
//    rosso sull'imputato sbagliato.  In tutti i casi la riga si stampa.
bool remotix_ospite_avvia(const char *addr, const char *port) {
  auto ora = remotix_ora_ms();

  if (remotix_ban_file == nullptr) {
    std::println(stderr,
                 "REMOTIX B3: ⛔ nessun --ban-file: il ban di §4.4-bis vive SOLO "
                 "IN MEMORIA, e il primo riavvio lo porta via (invariante I7). "
                 "Il conto dei tentativi funziona lo stesso, la persistenza no.");
  } else {
    struct stat st;
    auto c_era = stat(remotix_ban_file, &st) == 0;
    errno = 0;
    auto quanti = rcp_ban_carica(remotix_ban_file, ora);
    if (quanti < 0) {
      std::println(stderr,
                   "REMOTIX B3: ⛔ NON HO POTUTO LEGGERE il file dei ban «{}»: "
                   "{}.  Non e' «zero ban»: e' «non ho potuto guardare», e "
                   "servire cosi' spegnerebbe la protezione di §4.4-bis "
                   "facendola sembrare accesa.  Non parto.",
                   remotix_ban_file, strerror(errno));
      return false;
    }
    if (!c_era) {
      std::println(stderr,
                   "REMOTIX B3: ban caricati: 0 — il file «{}» non esiste "
                   "ancora, quindi nessun indirizzo e' fuori.  ⚠ Non e' un "
                   "errore: lo scrivera' il primo ban.",
                   remotix_ban_file);
    } else {
      std::println(stderr,
                   "REMOTIX B3: ban caricati: {} — dal file «{}», letto per "
                   "intero.  {}",
                   quanti, remotix_ban_file,
                   quanti == 0
                     ? "⚠ zero indirizzi fuori, e questo e' un fatto misurato: "
                       "il file c'era e l'ho letto"
                     : "Questi indirizzi restano fuori finche' non scadono o "
                       "finche' non li toglie il comando di sblocco (§4.4-bis).");
    }
  }

  // ── la porta TCP della pagina, lo STESSO NUMERO dell'UDP (SPECIFICHE.md §4)
  addrinfo suggerimenti{};
  suggerimenti.ai_flags = AI_PASSIVE;
  suggerimenti.ai_family = AF_UNSPEC;
  suggerimenti.ai_socktype = SOCK_STREAM;
  addrinfo *elenco = nullptr;
  if (auto rv = getaddrinfo(addr, port, &suggerimenti, &elenco); rv != 0) {
    std::println(stderr,
                 "REMOTIX B3: ⛔ la pagina TCP non parte: getaddrinfo({}, {}) "
                 "dice «{}».  Chi viene bannato non leggera' nessuna frase "
                 "(§4.4-bis), e il server QUIC va avanti lo stesso.",
                 addr, port, gai_strerror(rv));
  } else {
    auto fd = -1;
    for (auto p = elenco; p; p = p->ai_next) {
      fd = socket(p->ai_family, p->ai_socktype | SOCK_NONBLOCK, p->ai_protocol);
      if (fd == -1) {
        continue;
      }
      auto uno = 1;
      setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &uno, sizeof uno);
      if (bind(fd, p->ai_addr, p->ai_addrlen) == 0 && listen(fd, 16) == 0) {
        break;
      }
      close(fd);
      fd = -1;
    }
    freeaddrinfo(elenco);
    if (fd == -1) {
      std::println(stderr,
                   "REMOTIX B3: ⛔ la pagina TCP non parte: nessun indirizzo di "
                   "{}:{} si e' lasciato legare ({}).  Chi viene bannato non "
                   "leggera' nessuna frase (§4.4-bis), e il server QUIC va "
                   "avanti lo stesso.",
                   addr, port, strerror(errno));
    } else {
      ev_io_init(&remotix_pagina_ev, remotix_pagina_cb, fd, EV_READ);
      ev_io_start(EV_DEFAULT, &remotix_pagina_ev);
      remotix_pagina_accesa = true;
      std::println(stderr,
                   "REMOTIX B3: la pagina e' servita in TCP su {}:{} — ⛔ e a un "
                   "indirizzo bannato si serve LO STESSO, con «tentativi "
                   "esauriti» e le ore che mancano (§4.4-bis)",
                   addr, port);
    }
  }

  // ── il socket del comando di sblocco
  if (remotix_comando_socket == nullptr) {
    std::println(stderr,
                 "REMOTIX B3: ⛔ nessun --comando-socket: il ban si toglie SOLO "
                 "col passare delle 12 ore.  §4.4-bis ne vuole due, di strade, "
                 "e questa meta' non c'e'.");
  } else {
    // ⚠ Si toglie il file vecchio: un socket lasciato li' da un'esecuzione
    //   precedente fa fallire `bind` con EADDRINUSE, e il sintomo — «il comando
    //   non risponde» — somiglia in tutto a un server morto.
    unlink(remotix_comando_socket);
    sockaddr_un dove{};
    dove.sun_family = AF_UNIX;
    if (strlen(remotix_comando_socket) >= sizeof dove.sun_path) {
      std::println(stderr,
                   "REMOTIX B3: ⛔ il percorso del socket di comando e' troppo "
                   "lungo ({} byte, il massimo e' {}): il comando di sblocco "
                   "non ci sara'",
                   strlen(remotix_comando_socket), sizeof dove.sun_path - 1);
    } else {
      strcpy(dove.sun_path, remotix_comando_socket);
      auto fd = socket(AF_UNIX, SOCK_STREAM | SOCK_NONBLOCK, 0);
      if (fd == -1 ||
          bind(fd, reinterpret_cast<sockaddr *>(&dove), sizeof dove) != 0 ||
          listen(fd, 4) != 0) {
        std::println(stderr,
                     "REMOTIX B3: ⛔ il socket del comando di sblocco non parte "
                     "su «{}»: {}.  Il ban si potra' togliere solo aspettando "
                     "12 ore (§4.4-bis).",
                     remotix_comando_socket, strerror(errno));
        if (fd != -1) {
          close(fd);
        }
      } else {
        // ⛔ 0600, e la ragione e' la regola: la chiave che questo comando
        //    chiede e' «l'accesso alla macchina».  Un socket leggibile da
        //    chiunque la renderebbe «l'accesso a un utente qualunque della
        //    macchina», che e' una chiave diversa e piu' facile.
        if (chmod(remotix_comando_socket, 0600) != 0) {
          std::println(stderr,
                       "REMOTIX B3: ⚠ non ho potuto mettere 0600 su «{}»: {} — "
                       "il comando di sblocco c'e', ma la chiave che chiede e' "
                       "piu' larga di quel che §4.4-bis suppone",
                       remotix_comando_socket, strerror(errno));
        }
        ev_io_init(&remotix_comando_ev, remotix_comando_cb, fd, EV_READ);
        ev_io_start(EV_DEFAULT, &remotix_comando_ev);
        remotix_comando_acceso = true;
        std::println(stderr,
                     "REMOTIX B3: il comando di sblocco ascolta su «{}» (0600) "
                     "— «SBLOCCA <indirizzo>» oppure «PING»",
                     remotix_comando_socket);
      }
    }
  }

  // ⛔ E IL RIASSUNTO SI STAMPA IN UNA RIGA SOLA, con i tre fatti dentro: e' la
  //    riga che un banco legge per sapere DA CHE STATO parte (B0.1), e senza la
  //    quale «il ban non e' scattato» e «il ban non era nemmeno acceso» hanno
  //    lo stesso aspetto.
  std::println(stderr,
               "REMOTIX B3: ban lato ospite — persistenza {} · pagina TCP {} · "
               "comando di sblocco {}",
               remotix_ban_file ? remotix_ban_file : "SPENTA",
               remotix_pagina_accesa ? "accesa" : "SPENTA",
               remotix_comando_acceso ? remotix_comando_socket : "SPENTO");
  return true;
}

} // namespace

'''

# ⛔ Gli innesti in `server.cc`, e sono quattro punti perche' quattro sono i
#    posti in cui un `main` scritto da altri si lascia allargare: la tabella
#    delle opzioni lunghe, lo `switch` che le legge, l'aiuto, e la riga fra
#    «il server e' pronto» e «gira».
INNESTI_OSPITE = [
    # ── il corpo, subito prima di `main` ────────────────────────────────────
    (
        "server.cc",
        "int main(int argc, char **argv) {\n",
        None,  # ⚠ riempito in `main()` con CORPO_OSPITE + l'appiglio
        "il ban lato ospite (il corpo)",
    ),
    # ── le due opzioni lunghe ───────────────────────────────────────────────
    #    ⚠ I numeri 100 e 101 stanno lontani dai 37 dell'esempio apposta: il
    #      giorno in cui ngtcp2 aggiungera' la sua opzione numero 38, due casi
    #      con lo stesso numero sarebbero un'opzione che ne esegue un'altra —
    #      e il compilatore direbbe soltanto «duplicate case value», se va bene.
    (
        "server.cc",
        '      {"gso-burst", required_argument, &flag, 37},\n',
        '      {"gso-burst", required_argument, &flag, 37},\n'
        "      // ⭐ REMOTIX B3 — RCP.md §4.4-bis, le due strade del padrone di\n"
        "      //    casa: dove stanno i ban fra un riavvio e l'altro, e da dove\n"
        "      //    si comanda di toglierne uno.\n"
        '      {"ban-file", required_argument, &flag, 100},\n'
        '      {"comando-socket", required_argument, &flag, 101},\n',
        "le due opzioni del ban",
    ),
    # ── i due casi che le leggono ───────────────────────────────────────────
    (
        "server.cc",
        "      case 36:\n"
        "        // --show-stat\n"
        "        config.show_stat = true;\n"
        "        break;\n",
        "      case 100:\n"
        "        // ⭐ REMOTIX B3 — --ban-file (RCP.md §4.4-bis)\n"
        "        remotix_ban_file = optarg;\n"
        "        break;\n"
        "      case 101:\n"
        "        // ⭐ REMOTIX B3 — --comando-socket (RCP.md §4.4-bis)\n"
        "        remotix_comando_socket = optarg;\n"
        "        break;\n"
        "      case 36:\n"
        "        // --show-stat\n"
        "        config.show_stat = true;\n"
        "        break;\n",
        "i due casi del ban",
    ),
    # ── l'aiuto ────────────────────────────────────────────────────────────
    (
        "server.cc",
        "  -h, --help  Display this help and exit.\n",
        "  --ban-file=<PATH>\n"
        "              REMOTIX B3 (RCP.md 4.4-bis): dove si tengono i ban fra\n"
        "              un riavvio e l'altro.  Senza, il ban vive solo in\n"
        "              memoria.  Se il file c'e' e non si legge, il server NON\n"
        "              parte: «zero ban» e «non ho potuto guardare» sono due\n"
        "              fatti diversi.\n"
        "  --comando-socket=<PATH>\n"
        "              REMOTIX B3 (RCP.md 4.4-bis): il socket di dominio Unix\n"
        "              (0600) da cui si comanda «SBLOCCA <indirizzo>».  E'\n"
        "              l'altra via d'uscita oltre alle dodici ore.\n"
        "  -h, --help  Display this help and exit.\n",
        "l'aiuto delle due opzioni",
    ),
    # ── e la chiamata, fra «il server e' pronto» e «gira» ───────────────────
    #    ⛔ DOPO `s.init`: prima, un fallimento del server lascerebbe aperti la
    #       porta della pagina e il socket del comando di un server che non c'e'.
    #    ⛔ E PRIMA di `ev_run`: i due `ev_io` vanno messi nel ciclo mentre il
    #       ciclo non gira ancora.
    (
        "server.cc",
        "  ev_run(EV_DEFAULT, 0);\n",
        "  // ⭐ REMOTIX B3 — RCP.md §4.4-bis: i ban dal disco, la pagina in TCP\n"
        "  //    e il comando di sblocco.  Tutte e tre cose del PADRONE DI CASA:\n"
        "  //    `rcp.c` non apre socket e non legge la riga di comando.\n"
        "  if (!remotix_ospite_avvia(addr, port)) {\n"
        "    exit(EXIT_FAILURE);\n"
        "  }\n"
        "\n"
        "  ev_run(EV_DEFAULT, 0);\n",
        "la chiamata all'avvio",
    ),
]


def leggi(percorso):
    with open(percorso, encoding="utf-8") as f:
        return f.read()


def righe_di_commento(righe):
    """⛔ UNA REGOLA SOLA PER I COMMENTI, E LA STESSA NEI TRE INNESTI.

    Qui la regola era «comincia per //, /* oppure *», e classificava come
    COMMENTO due righe di C++ vero che stanno nel corpo innestato da B2:

        *v = src[0] & 0x3f;
        *v = (*v << 8) | src[i];

    ⚠ Sono dereferenziazioni.  ⛔ Il numero «di codice» stampato di qui era
      quindi strettamente minore di quello che B2 stampa sulle stesse righe, e
      i due si presentavano con la stessa etichetta.  L'asterisco vale come
      commento solo quando continua o chiude un blocco `/* … */`.
    """
    return sum(1 for r in righe
               if r.strip().startswith(("//", "/*", "* ", "*/"))
               or r.strip() == "*")


def togli():
    # ⛔ E SI DICE LA VERITA' SU CHE COSA SI PORTA VIA.
    #
    #    Qui c'era scritto «(resta l'innesto di B2)», ed era vero soltanto per
    #    `CMakeLists.txt`.  Nei due file che contano — `http3_server_proto_codec`
    #    `.cc` e `.h` — i due innesti sono INTRECCIATI, e togliendo solo il
    #    proprio restava un albero che ⛔ **non compila**: il `.cc` continuava a
    #    chiamare `rcp_apri`, `examples/rcp.h` era stato cancellato e il
    #    CMakeLists era tornato senza `rcp.c` — con `exit 0` stampato dallo
    #    script che quello stato l'aveva appena prodotto.
    #
    # ⭐ Quindi si rimette TUTTO l'esempio, e lo si dice: si riapplicano in
    #    ordine, prima B2 e poi questo.  Un `--togli` che lascia meno di quel
    #    che il nome promette e' meglio di uno che lascia macerie e tace.
    print("== Si rimette l'esempio com'era")
    print("   ⛔ sparisce ANCHE l'innesto di B2 (e i guasti di B11, se ci sono):")
    print("      i due vivono negli stessi due file, e un albero con mezzo")
    print("      innesto NON COMPILA.  Si riapplicano in ordine —")
    print("      01-b2-ngtcp2-wt-innesta.py, poi questo.")
    r = subprocess.run(["git", "-C", ALBERO, "checkout", "--", "examples"])
    if r.returncode != 0:
        print(f"   ⛔ git checkout e' fallito (uscita {r.returncode}):"
              " non si e' tolto niente.")
        return r.returncode
    for f in FILE_NOSTRI:
        try:
            os.remove(os.path.join(ESEMPI, f))
        except FileNotFoundError:
            pass

    # ⛔ E SI VERIFICA DI AVER TOLTO — qui prima si restituiva `0` SEMPRE,
    #    qualunque cosa fosse successa.  `LEZIONI.md` §1.9, quarta regola: una
    #    misura che puo' dire «zero» deve poter dire «sono fallita».
    guai = 0
    for percorso in FILE_TOCCATI:
        testo = leggi(os.path.join(ESEMPI, percorso))
        for marca in (MARCA, MARCA_B2, MARCA_B11):
            n = testo.count(marca)
            if n:
                print(f"   NO  restano {n} righe con «{marca}» in {percorso}")
                guai += n
    for f in FILE_NOSTRI:
        if os.path.exists(os.path.join(ESEMPI, f)):
            print(f"   NO  examples/{f} e' ancora li'")
            guai += 1
    if guai:
        print("   ⛔ l'esempio NON e' com'era.")
        return 3
    print("   OK  nessuna traccia di B2, B3 o B11, e i file nostri sono via")
    return 0


def main():
    if "--togli" in sys.argv:
        return togli()

    print("== L'innesto di RCP nell'esempio di ngtcp2")
    testo_cc = leggi(os.path.join(ESEMPI, "http3_server_proto_codec.cc"))
    if MARCA in testo_cc:
        print("   ⚠ l'innesto c'e' gia': non si tocca niente.")
        return 0

    # ⛔ E PRIMA DI TUTTO SI CHIEDE SE B2 C'E'.
    #
    #    Sei dei nostri appigli vengono da testo che ha introdotto B2: senza
    #    quell'innesto contano tutti zero, e la diagnosi che ne usciva era
    #    «gli appigli non sono UNO» — cioe' mandava a rileggere gli innesti
    #    mentre il difetto era che mancava il denominatore.  ⚠ E' la forma E6,
    #    il mittente dedotto invece che chiesto (`CODER.md` §3.7).
    if MARCA_B2 not in testo_cc:
        print(f"   ⛔ manca l'innesto di B2: «{MARCA_B2}» non compare in")
        print("      http3_server_proto_codec.cc.")
        print("      Questo innesto ci poggia sopra: si applica prima")
        print("      01-b2-ngtcp2-wt-innesta.py, poi di nuovo questo comando.")
        return 2

    lista = list(INNESTI) + [
        ("http3_server_proto_codec.cc",
         "std::expected<void, Error> ProtoCodec::wt_apri_sessione(Stream *stream) {\n",
         None, "il corpo dei ganci"),
    ] + list(INNESTI_OSPITE)
    testi, guasti = {}, 0
    for percorso, appiglio, sostituto, nome in lista:
        if sostituto is None:
            # ⚠ Due corpi, e ciascuno ha il suo file: quello dei ganci va nel
            #   codec, quello del ban lato ospite va nel `main`.  Prima qui
            #   c'era un `CORPO` solo e la scelta non esisteva.
            corpo = CORPO_OSPITE if percorso == "server.cc" else CORPO
            sostituto = corpo + appiglio
        if percorso not in testi:
            with open(os.path.join(ESEMPI, percorso), encoding="utf-8") as f:
                testi[percorso] = f.read()
        n = testi[percorso].count(appiglio)
        stato = "OK " if n == 1 else "NO "
        print(f"   {stato} {nome:34s} appiglio trovato {n} volta/e  [{percorso}]")
        if n != 1:
            guasti += 1
            continue
        testi[percorso] = testi[percorso].replace(appiglio, sostituto, 1)

    # le due dichiarazioni pubbliche dei ganci, nella classe
    a = ("  void wt_accoda(int64_t stream_id, std::span<const uint8_t> dati);\n")
    if testi["http3_server_proto_codec.h"].count(a) == 1:
        testi["http3_server_proto_codec.h"] = testi["http3_server_proto_codec.h"].replace(
            a, a + "\n"
                   " public:\n"
                   "  // ⭐ REMOTIX B3 — pubblici perche' li chiamano i ganci, che\n"
                   "  //    stanno in uno spazio anonimo fuori dalla classe: e' il\n"
                   "  //    prezzo di tenere `rcp.c` in C, e si paga in due righe.\n"
                   "  void wt_manda_controllo(const uint8_t *dati, size_t len);\n"
                   "  void wt_chiudi_adesso(uint8_t motivo);\n"
                   "  void wt_chiudi_sessione(uint8_t motivo);\n"
                   "\n"
                   " private:\n", 1)
        print("   OK  i due ganci pubblici              appiglio trovato 1 volta/e")
    else:
        print("   NO  i due ganci pubblici              appiglio NON unico")
        guasti += 1

    if guasti:
        print(f"\n   ⛔ {guasti} appigli non sono UNO: non si scrive niente,")
        print("      e nessun file e' stato copiato.")
        return 2

    # ⛔ E I FILE NOSTRI SI COPIANO SOLO ADESSO.
    #
    #    Prima venivano copiati in cima, PRIMA di guardare gli appigli: l'uscita
    #    con 2 stampava «non si scrive niente» su un albero in cui `rcp.c`,
    #    `rcp.h` e `autenticazione.c` erano gia' stati scritti — cioe' l'esito
    #    d'errore lasciava l'albero in uno stato che l'esito d'errore negava
    #    (`LEZIONI.md` §1.9).
    #
    # ⛔ I nostri file si COPIANO, non si linkano: l'albero di ngtcp2 e' di
    #    qualcun altro, e un collegamento simbolico che punta fuori si rompe
    #    in silenzio il giorno in cui qualcuno lo riclona.
    for f in FILE_NOSTRI:
        shutil.copyfile(os.path.join(SORGENTI, f), os.path.join(ESEMPI, f))
    print(f"\n   OK  {len(FILE_NOSTRI)} file nostri copiati in examples/")

    for percorso, testo in testi.items():
        with open(os.path.join(ESEMPI, percorso), "w", encoding="utf-8") as f:
            f.write(testo)
    print(f"   OK  {len(lista) + 1} innesti, in {len(testi)} file")

    print("\n== Quante righe sono cambiate — e sono DUE numeri diversi")
    d = subprocess.run(["git", "-C", ALBERO, "diff", "-U0", "--",
                        "examples"], capture_output=True, text=True).stdout.splitlines()
    agg = [r[1:] for r in d if r.startswith("+") and not r.startswith("+++")]
    vuote = sum(1 for r in agg if not r.strip())
    cod = len(agg) - vuote - righe_di_commento(agg)
    print(f"   dentro l'esempio (B2 + i fili di B3): {len(agg)} righe, {cod} di codice")
    for f in FILE_NOSTRI:
        righe = leggi(os.path.join(SORGENTI, f)).splitlines()
        vuote = sum(1 for r in righe if not r.strip())
        cod = len(righe) - vuote - righe_di_commento(righe)
        # ⚠ E il nome del posto e' quello VERO: qui si stampava
        #   `banchi/rcp/<file>` mentre si leggeva `/srv/src/rcp/<file>` — il
        #   conto era giusto e il posto no, che e' il modo piu' comodo di
        #   guardare il file sbagliato per mezz'ora.
        print(f"   {SORGENTI}/{f:<20s} {len(righe):>4} righe, {cod:>4} di codice")
    print("\n   ⭐ Il secondo gruppo e' il PROTOCOLLO, e non dipende da ngtcp2:")
    print("      e' quel che si porta via se un giorno la libreria cambia.")
    print("\n   ⚠ E la regola per dire che cos'e' un commento e' UNA SOLA, la")
    print("     stessa dei tre innesti: fino al 10 agosto erano tre diverse, e")
    print("     questa contava come commento le dereferenziazioni `*v = …`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
