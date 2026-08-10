#!/usr/bin/env python3
"""01-b2-ngtcp2-wt-innesta.py — innesta lo strato WebTransport nell'esempio di ngtcp2.

    python3 01-b2-ngtcp2-wt-innesta.py            innesta (o dice che c'e' gia')
    python3 01-b2-ngtcp2-wt-innesta.py --togli    rimette l'esempio com'era

---------------------------------------------------------------------------
⛔ PERCHE' UN INNESTO E NON UN SERVER NOSTRO

`banchi/01-b2-costruisci-ngtcp2.sh` l'ha gia' scritto, ed e' la regola di B2:
**si parte da dove parte chiunque**, cioe' dal server d'esempio del progetto.
Un server nostro dal foglio bianco misurerebbe la nostra pazienza — il ciclo
UDP, il TLS, i timer di ritrasmissione — e non la libreria.  Quel che B2 deve
misurare e' **quanto collante resta a noi PER WEBTRANSPORT**, e il modo di
misurarlo e' aggiungere quello strato a un HTTP/3 che gia' funziona e contare
le righe.

⭐ E il conto viene da se': dopo l'innesto, `git diff --stat` nell'albero di
   ngtcp2 dice quante righe sono cambiate sotto `examples/`.

⚠ **«Cambiate» non e' «nostre», e qui c'era scritto che non era una stima.**
  `git diff` non sa attribuire una riga: misura tutto quel che e' cambiato in
  quella cartella, **da chiunque**.  Vale come conto NOSTRO solo se l'albero
  era pulito prima — e per questo lo script adesso lo **guarda e lo dice**,
  invece di darlo per acquisito (`LEZIONI.md` §1.9, quarta regola: un
  denominatore si legge dove la cosa succede).
  ⚠ E una riga **modificata** compare fra le aggiunte: «aggiunte» e' un limite
  superiore di «nostre», non il loro numero esatto.

---------------------------------------------------------------------------
⛔ CHE COSA MANCA A `ngtcp2`+`nghttp3`, IN CONCRETO

Il censimento del 9 agosto diceva «le fondamenta si', lo strato no».  Adesso
si sa **quali** sono i tre buchi, perche' sono i tre punti che questo file
tocca:

  1. ⛔ **Non si puo' annunciare WebTransport.**  `nghttp3_settings` ha
     `enable_connect_protocol` e `h3_datagram` — le due che stanno negli RFC —
     e nient'altro; l'API pubblica offre `submit_request`, `submit_info`,
     `submit_response`, `submit_trailers`, `submit_shutdown_notice`, e
     **nessun modo di mettere un'impostazione arbitraria** sullo stream di
     controllo.  `SETTINGS_WT_MAX_SESSIONS`, che e' quel che i browser
     cercano, non passa di li'.  Si riscrive il SETTINGS che nghttp3 sta
     scrivendo, mentre lo scrive.

  2. ⛔ **Gli stream WebTransport vanno sottratti a nghttp3.**  Cominciano col
     tipo di frame `0x41` seguito dal numero della sessione, e nghttp3
     leggerebbe quel numero come una LUNGHEZZA.

  3. ⛔ **E i byte che tornano indietro non hanno una strada.**  nghttp3 non
     conosce quegli stream, quindi non li mettera' mai fra i vettori da
     scrivere: la coda d'uscita e' nostra.

⚠ Nessuno dei tre e' un difetto di ngtcp2 o di nghttp3: fanno HTTP/3, e
  WebTransport non e' HTTP/3.  E' esattamente il prezzo che §6.4 voleva
  conoscere prima di scegliere.

---------------------------------------------------------------------------
⛔ COME QUESTO SCRIPT EVITA DI MENTIRE

Ogni innesto ha un **appiglio**, cioe' un pezzo di codice loro che deve
comparire **una volta sola**.  Se compare zero volte o due, lo script si ferma
e dice quante ne ha trovate: e' la quarta regola di `LEZIONI.md` §1.9 — un
denominatore, non solo un risultato.  ⚠ Un innesto che «non trova l'appiglio»
e tira dritto produrrebbe un server che compila, non fa WebTransport, e non lo
dice.
"""
import os
import subprocess
import sys

ALBERO = "/srv/src/b2/ngtcp2"
ESEMPI = "/srv/src/b2/ngtcp2/examples"
MARCA = "REMOTIX B2"
MARCA_B3 = "REMOTIX B3"
MARCA_B11 = "REMOTIX B11 GUASTO"

# ⛔ I file che questo innesto tocca.  Servono a `--togli` per VERIFICARE di
#    aver tolto: lo stato d'uscita di `git` dice che git non ha protestato, non
#    che la marca sia sparita.
FILE_TOCCATI = [
    "http3_server_proto_codec.h",
    "http3_server_proto_codec.cc",
    "server.h",
    "server.cc",
    "tls_server_session_boringssl.cc",
]

# ⛔ I file che B3 copia dentro `examples/`.  Git non tocca i file non
#    tracciati, quindi dopo `--togli` restano li' e nessuno lo dice.
FILE_DI_B3 = ["rcp.c", "rcp.h", "autenticazione.c"]

# ---------------------------------------------------------------------------
# I pezzi di codice, in fondo al file per non spezzare la lettura.
# Ogni voce e': (file, appiglio, sostituto, nome leggibile)
# ---------------------------------------------------------------------------


def innesti():
    return [
        # ── 1. Le intestazioni che servono ai tipi nuovi ────────────────────
        (
            "http3_server_proto_codec.h",
            "#include <vector>\n#include <expected>\n#include <optional>\n",
            "#include <vector>\n#include <expected>\n#include <optional>\n"
            "// ⭐ REMOTIX B2 — per la coda d'uscita e la classificazione degli stream\n"
            "#include <array>\n#include <deque>\n#include <span>\n"
            "#include <string>\n#include <unordered_map>\n",
            "intestazioni del codec",
        ),
        # ── 2. Lo stato dello strato WebTransport ───────────────────────────
        (
            "http3_server_proto_codec.h",
            "  Handler *handler_;\n"
            "  ngtcp2_conn *conn_;\n"
            "  ngtcp2_ccerr &last_error_;\n"
            "  nghttp3_conn *httpconn_{};\n"
            "};\n",
            """  // ═══ ⭐ REMOTIX B2 — lo strato WebTransport ══════════════════════════
  //
  // ⛔ Sta qui e non nella libreria perche' nghttp3 non ha un posto dove
  //    metterlo: fa HTTP/3, e WebTransport non e' HTTP/3.  Le righe da qui
  //    in giu' sono il collante di `DECISIONI.md` §6.4, e si contano.
  enum class WtEsito {
    MIO,     // e' roba WebTransport: l'ho gestita io
    ATTENDI, // non ho ancora abbastanza byte per decidere
    HTTP3,   // non e' WebTransport: passala a nghttp3
  };

  struct WtUscita {
    int64_t stream_id;
    std::vector<uint8_t> dati;
    size_t off;
  };

  std::expected<void, Error> wt_apri_sessione(Stream *stream);
  size_t wt_riscrivi_impostazioni(const nghttp3_vec *vec, size_t veccnt);
  // ⛔ `fin` non e' un di piu': RCP.md §4.2 dice che «un FIN su quello stream,
  //    da una qualunque delle due parti, chiude la sessione», e senza questo
  //    parametro l'informazione non entra qui in nessun modo — per gli stream
  //    che riconosciamo noi nemmeno nghttp3 la vede, perche' torniamo prima.
  WtEsito wt_smista(int64_t stream_id, std::span<const uint8_t> data, bool fin,
                    std::vector<uint8_t> &riunito);
  void wt_accoda(int64_t stream_id, std::span<const uint8_t> dati);

 public:
  // ⛔⭐ LA CAPSULA CON CUI IL CLIENT CHIUDE LA SESSIONE.
  //
  //    Una sessione WebTransport non finisce solo quando muore la
  //    connessione: il client la chiude mandando `CLOSE_WEBTRANSPORT_SESSION`
  //    (capsula 0x2843) sullo stream della CONNECT, **con un codice e una
  //    ragione dentro**.  ⚠ Fino al 10 agosto 2026 questo server non la
  //    leggeva: quei byte finivano nel corpo HTTP e nessuno li guardava.
  //
  // ⭐ E' pubblica perche' la chiama `http_recv_data`, che sta in uno spazio
  //    anonimo fuori dalla classe.
  void wt_capsula(int64_t stream_id, std::span<const uint8_t> dati);

 private:
  // ⚠ Che cosa SIGNIFICHI la chiusura del client non lo decide questo strato:
  //   qui il corpo e' vuoto, e B3 ci innesta la riga di RCP.
  //
  // ⛔ E IL CODICE ARRIVA SU 32 BIT, NON SU 8.  La capsula ne porta quattro di
  //    byte, e troncarlo al byte basso faceva entrare a verbale `0x0100` come
  //    `0x00` — cioe' come il **solo** valore che RCP.md §3.1 vieta
  //    esplicitamente («chiusura senza motivo … NON DEVE essere usato»).  Chi
  //    lo riceve controlla che sia uno dei motivi di §8.2, e se non lo e' lo
  //    dice: §3 chiede di scrivere che cosa non si e' capito, non di supplire.
  void wt_chiusa_dal_client(uint32_t codice);

  // ⛔ IL FIN DEL CLIENT SUL CANALE DI CONTROLLO.  RCP.md §4.2: «un FIN su
  //    quello stream, da una qualunque delle due parti, chiude la sessione.
  //    Chi lo riceve DEVE considerarla finita».  ⚠ Era l'unica delle due
  //    direzioni che nessuno aveva percorso: la pagina che chiude la parte
  //    scrivente del canale e tiene viva la connessione lasciava il posto del
  //    registro occupato finche' non moriva la connessione — e una connessione
  //    un browser la tiene viva.
  //
  // ⚠ Vuota qui per la stessa ragione di sopra: che cosa sia «finita» lo sa
  //   RCP, non il trasporto.  B3 ci innesta la riga.
  void wt_fin_dal_client(int64_t stream_id);

  Handler *handler_;
  ngtcp2_conn *conn_;
  ngtcp2_ccerr &last_error_;
  nghttp3_conn *httpconn_{};
  // lo stream di controllo HTTP/3: serve a riconoscerlo in scrittura, che e'
  // l'unico istante in cui si possa dire al browser che parliamo WebTransport
  int64_t wt_ctrl_id_{-1};
  bool wt_impostazioni_scritte_{false};
  bool wt_guasto_{false};
  std::array<uint8_t, 256> wt_impbuf_;
  size_t wt_impbuf_len_{0};
  // ⛔ Quanti byte del SETTINGS riscritto sono GIA' USCITI, e quanti byte di
  //    nghttp3 quel buffer sostituisce.  Servono perche' una scrittura
  //    **parziale** e' un esito normale di `ngtcp2_conn_writev_stream` — non
  //    un guasto — e prima uccideva la connessione: adesso si riprende dal
  //    punto in cui si era arrivati, come si fa da sempre per `wt_uscita_`.
  size_t wt_impbuf_off_{0};
  size_t wt_impbuf_orig_{0};
  // gli stream bidirezionali del client: quelli di cui non si sa ancora che
  // cosa siano, quelli che sono WebTransport, quelli che non lo sono
  std::unordered_map<int64_t, std::vector<uint8_t>> wt_incerti_;
  std::unordered_map<int64_t, int64_t> wt_streams_;
  std::unordered_map<int64_t, bool> wt_nonwt_;
  std::deque<WtUscita> wt_uscita_;
  int64_t wt_sessione_{-1};
  // ⛔ La coda nostra e' bloccata per QUESTA passata di scrittura: ngtcp2 ha
  //    detto STREAM_DATA_BLOCKED, e riprovare dentro la stessa passata
  //    sarebbe un ciclo che non avanza.  Si azzera in cima a `write_pkt`.
  bool wt_coda_bloccata_{false};
  // i byte della CONNECT che non compongono ancora una capsula intera
  std::vector<uint8_t> wt_capsbuf_;
  // ⛔ Quanti byte di una capsula gia' giudicata TROPPO GRANDE restano da
  //    buttare mentre passano.  RCP.md §6.1: «la lunghezza si controlla prima
  //    di allocare» — e aspettare i byte invece di allocarli e' lo stesso
  //    regalo, fatto piu' lentamente.
  uint64_t wt_capsalta_{0};
};
""",
            "lo stato dello strato WebTransport",
        ),
        # ── 3. Le due impostazioni che nghttp3 sa fare da se' ───────────────
        (
            "http3_server_proto_codec.cc",
            "  settings.qpack_max_dtable_capacity = 4096;\n"
            "  settings.qpack_blocked_streams = 100;\n",
            "  settings.qpack_max_dtable_capacity = 4096;\n"
            "  settings.qpack_blocked_streams = 100;\n"
            "\n"
            "  // ⭐ REMOTIX B2 — le due che nghttp3 sa fare da se', e sono negli RFC.\n"
            "  settings.enable_connect_protocol = 1; // RFC 9220, l'extended CONNECT\n"
            "  settings.h3_datagram = 1;             // RFC 9297 (RCP.md §2.2)\n",
            "le impostazioni che nghttp3 conosce",
        ),
        # ── 4. Il numero dello stream di controllo ──────────────────────────
        (
            "http3_server_proto_codec.cc",
            "  if (auto rv = nghttp3_conn_bind_control_stream(httpconn_, ctrl_stream_id);\n",
            "  // ⭐ REMOTIX B2 — si tiene il numero: quando nghttp3 scrivera' il suo\n"
            "  //    SETTINGS su questo stream sara' l'unica occasione di aggiungerci\n"
            "  //    le due dichiarazioni di WebTransport.\n"
            "  wt_ctrl_id_ = ctrl_stream_id;\n"
            "\n"
            "  if (auto rv = nghttp3_conn_bind_control_stream(httpconn_, ctrl_stream_id);\n",
            "il numero dello stream di controllo",
        ),
        # ── 5. La guardia in cima al ciclo di scrittura ─────────────────────
        (
            "http3_server_proto_codec.cc",
            "  std::array<nghttp3_vec, 16> vec;\n\n  for (;;) {\n",
            "  std::array<nghttp3_vec, 16> vec;\n"
            "\n"
            "  // ⭐ REMOTIX B2 — una passata di scrittura comincia qui, e la coda\n"
            "  //    nostra riparte SBLOCCATA: `wt_coda_bloccata_` vale per una\n"
            "  //    passata sola.  ⚠ Sta fuori dal ciclo apposta — azzerarlo\n"
            "  //    dentro rimetterebbe in gioco lo stesso elemento a ogni giro,\n"
            "  //    che e' precisamente il ciclo che non avanza.\n"
            "  wt_coda_bloccata_ = false;\n"
            "\n"
            "  for (;;) {\n"
            "    // ⭐ REMOTIX B2 — se la riscrittura delle impostazioni ha perso il\n"
            "    //    conto, ci si ferma: uno stream di controllo sfasato e' peggio\n"
            "    //    di una connessione chiusa.\n"
            "    // ⚠ NON e' il caso della scrittura PARZIALE, che e' un esito\n"
            "    //   normale e si riprende alla passata dopo: vedi `wt_conta`.\n"
            "    if (wt_guasto_) {\n"
            "      return NGTCP2_ERR_CALLBACK_FAILURE;\n"
            "    }\n"
            "\n",
            "la guardia del ciclo di scrittura",
        ),
        # ── 6. La scelta di che cosa scrivere ───────────────────────────────
        (
            "http3_server_proto_codec.cc",
            "    ngtcp2_ssize ndatalen;\n"
            "    auto v = vec.data();\n"
            "    auto vcnt = static_cast<size_t>(sveccnt);\n",
            """    // ═══ ⭐ REMOTIX B2 ═══════════════════════════════════════════════════
    // Due cose che nghttp3 non sa fare, e vanno fatte proprio qui:
    //   1. aggiungere le impostazioni WebTransport al SETTINGS che sta
    //      scrivendo lui — non c'e' un altro momento;
    //   2. mandare byte su uno stream che lui NON CONOSCE, che altrimenti
    //      non uscirebbe mai dalla macchina.
    std::array<nghttp3_vec, 1> wt_vec;
    size_t wt_orig = 0;
    bool wt_mio = false;

    if (sveccnt > 0 && stream_id == wt_ctrl_id_ && !wt_impostazioni_scritte_) {
      // ⛔ La riscrittura si fa UNA VOLTA SOLA.  Se la passata di prima ne ha
      //    spedito solo un pezzo (`wt_impbuf_off_ > 0`), nghttp3 ci rioffre
      //    gli stessi byte — non gli abbiamo ancora detto di averli consumati
      //    — e ricomporre il buffer da capo rispedirebbe il pezzo gia' uscito.
      if (wt_impbuf_off_ == 0) {
        wt_impbuf_orig_ =
          wt_riscrivi_impostazioni(vec.data(), static_cast<size_t>(sveccnt));
      }
      wt_orig = wt_impbuf_orig_;
    }

    // ⛔ E la coda nostra si SALTA per tutta questa passata se ngtcp2 ha gia'
    //    detto «bloccato» su di lei: vedi il ramo STREAM_DATA_BLOCKED piu'
    //    sotto.  Riprovare adesso non farebbe avanzare il ciclo.
    if (sveccnt <= 0 && !wt_coda_bloccata_ && !wt_uscita_.empty()) {
      auto &u = wt_uscita_.front();
      stream_id = u.stream_id;
      fin = 0;
      wt_vec[0].base = u.dati.data() + u.off;
      wt_vec[0].len = u.dati.size() - u.off;
      wt_mio = true;
    }

    ngtcp2_ssize ndatalen;
    auto v = vec.data();
    auto vcnt = static_cast<size_t>(sveccnt);

    if (wt_orig) {
      wt_vec[0].base = wt_impbuf_.data() + wt_impbuf_off_;
      wt_vec[0].len = wt_impbuf_len_ - wt_impbuf_off_;
      v = wt_vec.data();
      vcnt = 1;
    } else if (wt_mio) {
      v = wt_vec.data();
      vcnt = 1;
    }

    // Quanti byte DI NGHTTP3 sono stati consumati.  Se il suo buffer e' stato
    // sostituito, il numero che ngtcp2 restituisce e' il NOSTRO, e dirglielo
    // sfaserebbe i suoi conti.
    auto wt_conta = [&](ngtcp2_ssize n) -> uint64_t {
      auto c = as_unsigned(n);
      if (!wt_orig) {
        return c;
      }
      // ⛔⭐ E UNA SCRITTURA PARZIALE NON E' UN GUASTO.
      //
      //    `ndatalen` minore della lunghezza offerta e' un esito NORMALE di
      //    `ngtcp2_conn_writev_stream`: nello stream frame ci va quel che
      //    avanza nel pacchetto.  I ~24 byte del SETTINGS riscritto viaggiano
      //    nel primo volo dopo la stretta di mano, quello che porta anche
      //    HANDSHAKE_DONE, i NEW_CONNECTION_ID e l'eventuale NEW_TOKEN: con un
      //    client che annuncia `max_udp_payload_size` vicino a 1200 e una
      //    connection id di 20 byte, li' dentro 24 byte non ci stanno.
      //
      // ⛔ Prima qui MORIVA LA CONNESSIONE, mentre dieci righe piu' sotto la
      //    coda nostra la stessa scrittura parziale la gestiva con `u.off`.
      //    Due politiche opposte per lo stesso esito, nello stesso modulo.
      if (c > wt_impbuf_len_ - wt_impbuf_off_) {
        // ⛔ Questo si': ngtcp2 dichiara di aver preso PIU' di quel che gli e'
        //    stato offerto.  Non e' recuperabile e non e' distinguibile da un
        //    conto sbagliato nostro: lo stream di controllo sarebbe sfasato.
        std::println(stderr,
                     "REMOTIX B2: impostazioni, conto impossibile ({} presi su "
                     "{} offerti)",
                     c, wt_impbuf_len_ - wt_impbuf_off_);
        wt_guasto_ = true;
        return 0;
      }
      wt_impbuf_off_ += static_cast<size_t>(c);
      if (wt_impbuf_off_ < wt_impbuf_len_) {
        // Si riprende dalla passata dopo, e a nghttp3 non si dice ancora
        // niente: i suoi byte li avra' consumati soltanto quando il buffer
        // riscritto sara' uscito tutto.
        std::println(stderr,
                     "REMOTIX B2: impostazioni, {} byte su {} — il resto alla "
                     "passata dopo",
                     wt_impbuf_off_, wt_impbuf_len_);
        return 0;
      }
      wt_impostazioni_scritte_ = true;
      return wt_orig;
    };

    auto wt_avanza = [&](ngtcp2_ssize n) -> int {
      if (wt_mio) {
        auto &u = wt_uscita_.front();
        u.off += static_cast<size_t>(n);
        if (u.off >= u.dati.size()) {
          wt_uscita_.pop_front();
        }
        return 0;
      }
      return nghttp3_conn_add_write_offset(httpconn_, stream_id, wt_conta(n));
    };
""",
            "la scelta di che cosa scrivere",
        ),
        # ── 7. I due rami del blocco, che non valgono per i nostri stream ───
        (
            "http3_server_proto_codec.cc",
            "      case NGTCP2_ERR_STREAM_DATA_BLOCKED:\n"
            "        assert(ndatalen == -1);\n"
            "        nghttp3_conn_block_stream(httpconn_, stream_id);\n"
            "        continue;\n"
            "      case NGTCP2_ERR_STREAM_SHUT_WR:\n"
            "        assert(ndatalen == -1);\n"
            "        nghttp3_conn_shutdown_stream_write(httpconn_, stream_id);\n"
            "        continue;\n",
            "      case NGTCP2_ERR_STREAM_DATA_BLOCKED:\n"
            "        assert(ndatalen == -1);\n"
            "        // ⭐ REMOTIX B2 — nghttp3 non conosce gli stream WebTransport:\n"
            "        //    dirgli di bloccarne uno sarebbe un errore su uno stream che\n"
            "        //    per lui non esiste.\n"
            "        //\n"
            "        // ⛔⭐ E I BYTE NON SI BUTTANO: QUESTO E' UN CANALE AFFIDABILE.\n"
            "        //\n"
            "        //    Qui c'era `pop_front()`, che scartava l'elemento INTERO —\n"
            "        //    compreso il caso `u.off > 0`, cioe' quando una parte era\n"
            "        //    gia' uscita sul filo.  Il messaggio dopo si saldava a quei\n"
            "        //    byte monchi, e il client leggeva un `tipo`/`lunghezza`\n"
            "        //    inventato: RCP.md §6.1 gli impone di chiudere con\n"
            "        //    ERRORE_PROTOCOLLO.  ⛔ Era il SERVER a fabbricare la\n"
            "        //    violazione del client, e nel registro c'era scritto «byte\n"
            "        //    buttati» — che descriveva la perdita senza dire che aveva\n"
            "        //    corrotto lo stream, e senza avvisare RCP di niente.\n"
            "        //\n"
            "        // ⚠ E STREAM_DATA_BLOCKED non e' un guasto: e' la condizione\n"
            "        //   normale e transitoria che si scioglie col primo\n"
            "        //   MAX_STREAM_DATA.  Si salta la coda nostra per questa\n"
            "        //   passata e si riprova alla prossima — che arriva col\n"
            "        //   pacchetto che porta il credito.\n"
            "        if (wt_mio) {\n"
            "          auto &u = wt_uscita_.front();\n"
            "          std::println(stderr,\n"
            "                       \"REMOTIX B2: stream {} bloccato: {} byte RESTANO \"\n"
            "                       \"in coda ({} gia' usciti), si riprova alla \"\n"
            "                       \"passata dopo\",\n"
            "                       stream_id, u.dati.size() - u.off, u.off);\n"
            "          wt_coda_bloccata_ = true;\n"
            "          continue;\n"
            "        }\n"
            "        nghttp3_conn_block_stream(httpconn_, stream_id);\n"
            "        continue;\n"
            "      case NGTCP2_ERR_STREAM_SHUT_WR:\n"
            "        assert(ndatalen == -1);\n"
            "        if (wt_mio) {\n"
            "          wt_uscita_.pop_front();\n"
            "          continue;\n"
            "        }\n"
            "        nghttp3_conn_shutdown_stream_write(httpconn_, stream_id);\n"
            "        continue;\n",
            "i due rami del blocco",
        ),
        # ── 8. I due punti che avanzano l'offset ────────────────────────────
        (
            "http3_server_proto_codec.cc",
            "      case NGTCP2_ERR_WRITE_MORE:\n"
            "        assert(ndatalen >= 0);\n"
            "        if (auto rv = nghttp3_conn_add_write_offset(httpconn_, stream_id,\n"
            "                                                    as_unsigned(ndatalen));\n"
            "            rv != 0) {\n",
            "      case NGTCP2_ERR_WRITE_MORE:\n"
            "        assert(ndatalen >= 0);\n"
            "        // ⭐ REMOTIX B2 — passa da wt_avanza: vedi sopra\n"
            "        if (auto rv = wt_avanza(ndatalen); rv != 0) {\n",
            "l'avanzamento nel ramo WRITE_MORE",
        ),
        (
            "http3_server_proto_codec.cc",
            "    if (ndatalen >= 0) {\n"
            "      if (auto rv = nghttp3_conn_add_write_offset(httpconn_, stream_id,\n"
            "                                                  as_unsigned(ndatalen));\n"
            "          rv != 0) {\n",
            "    if (ndatalen >= 0) {\n"
            "      // ⭐ REMOTIX B2 — idem\n"
            "      if (auto rv = wt_avanza(ndatalen); rv != 0) {\n",
            "l'avanzamento finale",
        ),
        # ── 9. Lo smistamento in lettura ────────────────────────────────────
        (
            "http3_server_proto_codec.cc",
            "  if (!httpconn_) {\n    return {};\n  }\n\n"
            "  auto nconsumed = nghttp3_conn_read_stream2(\n",
            "  if (!httpconn_) {\n    return {};\n  }\n\n"
            "  // ⭐ REMOTIX B2 — gli stream WebTransport non sono affari di nghttp3:\n"
            "  //    leggerebbe 0x41 come un tipo di frame sconosciuto e poi il numero\n"
            "  //    della sessione come una LUNGHEZZA, sballando tutto il resto.\n"
            "  //    ⛔ E il FIN viaggia con loro: RCP.md §4.2 lo rende la fine\n"
            "  //       della sessione, e per uno stream che gestiamo noi qui e'\n"
            "  //       l'ULTIMO posto in cui si puo' vedere — sotto si torna\n"
            "  //       prima di `nghttp3_conn_read_stream2`, quindi nemmeno\n"
            "  //       nghttp3 lo incontra.\n"
            "  std::vector<uint8_t> wt_riunito;\n"
            "  switch (wt_smista(stream_id, data,\n"
            "                    (flags & NGTCP2_STREAM_DATA_FLAG_FIN) != 0,\n"
            "                    wt_riunito)) {\n"
            "  case WtEsito::MIO:\n"
            "  case WtEsito::ATTENDI:\n"
            "    return {};\n"
            "  case WtEsito::HTTP3:\n"
            "    if (!wt_riunito.empty()) {\n"
            "      data = std::span<const uint8_t>{wt_riunito};\n"
            "    }\n"
            "    break;\n"
            "  }\n"
            "\n"
            "  auto nconsumed = nghttp3_conn_read_stream2(\n",
            "lo smistamento in lettura",
        ),
        # ── 9-bis. ⛔⭐ LA CAPSULA CON CUI IL CLIENT CHIUDE LA SESSIONE ───────
        #    Il corpo della CONNECT non e' un corpo: e' un flusso di capsule
        #    (RFC 9297), e dentro ci viaggia `CLOSE_WEBTRANSPORT_SESSION` con
        #    il codice e la ragione.  ⚠ Qui finiva nel registro di debug e
        #    nient'altro — cioe' il server non sapeva **perche'** il client se
        #    ne fosse andato, e `RCP.md` §3.1 punto 3 fa viaggiare il motivo
        #    proprio di li'.
        #
        # ⭐ Trovato dal banco B11 il 10 agosto 2026: Firefox **azzera** lo
        #    stream di controllo buttando il `CONGEDO` gia' in coda, e il
        #    motivo arriva solo dentro la capsula.  Senza leggerla, di quel
        #    motore si sarebbe detto «non si congeda» — che e' falso.
        (
            "http3_server_proto_codec.cc",
            "  auto pc = static_cast<ProtoCodec *>(user_data);\n"
            "  pc->http_consume(stream_id, datalen);\n",
            "  auto pc = static_cast<ProtoCodec *>(user_data);\n"
            "  // ⭐ REMOTIX B2 — il corpo della CONNECT e' un flusso di capsule.\n"
            "  pc->wt_capsula(stream_id, {data, datalen});\n"
            "  pc->http_consume(stream_id, datalen);\n",
            "la capsula di chiusura in lettura",
        ),
        # ── 10. L'intestazione :protocol ────────────────────────────────────
        (
            "http3_server_proto_codec.cc",
            "  case NGHTTP3_QPACK_TOKEN__AUTHORITY:\n"
            "    stream->authority = std::string{v.base, v.base + v.len};\n"
            "    break;\n"
            "  }\n",
            "  case NGHTTP3_QPACK_TOKEN__AUTHORITY:\n"
            "    stream->authority = std::string{v.base, v.base + v.len};\n"
            "    break;\n"
            "  // ⭐ REMOTIX B2 — l'intestazione che distingue una CONNECT estesa da\n"
            "  //    una CONNECT normale (RFC 9220).\n"
            "  case NGHTTP3_QPACK_TOKEN__PROTOCOL:\n"
            "    stream->protocol = std::string{v.base, v.base + v.len};\n"
            "    break;\n"
            "  }\n",
            "l'intestazione :protocol",
        ),
        # ── 11. La CONNECT estesa ───────────────────────────────────────────
        (
            "http3_server_proto_codec.cc",
            "ProtoCodec::http_end_request_headers(Stream *stream) {\n"
            "  if (config.early_response) {\n",
            "ProtoCodec::http_end_request_headers(Stream *stream) {\n"
            "  // ⭐ REMOTIX B2 — e' qui che nasce la sessione WebTransport.\n"
            "  if (stream->method == \"CONNECT\" && stream->protocol == \"webtransport\") {\n"
            "    return wt_apri_sessione(stream);\n"
            "  }\n"
            "\n"
            "  if (config.early_response) {\n",
            "la CONNECT estesa",
        ),
        # ── 12. Il corpo dello strato ───────────────────────────────────────
        (
            "http3_server_proto_codec.cc",
            "std::expected<void, Error> ProtoCodec::setup_httpconn() {\n",
            None,  # riempito sotto da CORPO
            "il corpo dello strato WebTransport",
        ),
        # ── 13. Il campo :protocol nello Stream ─────────────────────────────
        (
            "server.h",
            "  std::string authority;\n  std::string status_resp_body;\n",
            "  std::string authority;\n"
            "  // ⭐ REMOTIX B2 — il :protocol della CONNECT estesa, e il segno che\n"
            "  //    questo stream E' la sessione (non si chiude come una richiesta)\n"
            "  std::string protocol;\n"
            "  bool wt_session{};\n"
            "  std::string status_resp_body;\n",
            "il campo :protocol",
        ),
        # ── 14. I parametri di trasporto ────────────────────────────────────
        (
            "server.cc",
            "  params.max_idle_timeout = config.timeout;\n",
            "  params.max_idle_timeout = config.timeout;\n"
            "  // ⛔ REMOTIX B2 — RCP.md §2.3: il server DEVE concedere al client\n"
            "  //    almeno **16** stream unidirezionali «in ogni momento».  Il\n"
            "  //    loro esempio ne concede 3 — quanti ne vuole HTTP/3 per il\n"
            "  //    controllo e QPACK — e con quel credito il client non\n"
            "  //    aprirebbe nemmeno lo stream di input: il sintomo sarebbe\n"
            "  //    «il desktop non risponde», non «credito esaurito».\n"
            "  //    ⚠ Trovato il 10 agosto misurando le proprieta' che restavano,\n"
            "  //      e NON dalla sessione che si apriva lo stesso: la sessione\n"
            "  //      si apre benissimo con 3.\n"
            "  if (params.initial_max_streams_uni < 16) {\n"
            "    params.initial_max_streams_uni = 16;\n"
            "  }\n"
            "  // ⭐ REMOTIX B2 — RCP.md §2.2: i datagram DEVONO essere abilitati\n"
            "  //    sulla connessione HTTP/3 (e' l'audio).  ⛔ E senza QUESTO\n"
            "  //    parametro di trasporto, annunciare SETTINGS_H3_DATAGRAM=1 e' un\n"
            "  //    errore di protocollo: il cliente di prova lo rifiuta con\n"
            "  //    «H3_DATAGRAM requires max_datagram_frame_size».\n"
            "  params.max_datagram_frame_size = 65536;\n"
            "  std::println(stderr,\n"
            "               \"REMOTIX B2: max_idle_timeout={}ms max_datagram_frame_size={} \"\n"
            "               \"streams_bidi={} streams_uni={}\",\n"
            "               params.max_idle_timeout / NGTCP2_MILLISECONDS,\n"
            "               params.max_datagram_frame_size,\n"
            "               params.initial_max_streams_bidi,\n"
            "               params.initial_max_streams_uni);\n",
            "i parametri di trasporto",
        ),
        # ── 15. ⛔ Il 0-RTT, che il loro esempio accende ─────────────────────
        (
            "tls_server_session_boringssl.cc",
            "  SSL_set_early_data_enabled(ssl_, 1);\n",
            "  // ⛔ REMOTIX B2 — RCP.md §2.3: il server NON DEVE offrire 0-RTT.\n"
            "  //\n"
            "  //    I dati 0-RTT si possono RIPETERE, e il secondo messaggio di\n"
            "  //    RCP e' `CREDENZIALI`.  Il guadagno sarebbe un giro di rete su\n"
            "  //    una sessione che dura ore.\n"
            "  //\n"
            "  // ⚠ Il loro esempio lo accende, ed e' la norma: `fasi/01-filo-nudo.md`\n"
            "  //   lo aveva PREVISTO — «le librerie QUIC lo offrono per impostazione\n"
            "  //   predefinita» — e aveva anche scritto perche' nessun banco\n"
            "  //   funzionale se ne accorgerebbe: **il sintomo non esiste**.  La\n"
            "  //   sessione si apre uguale, i byte tornano uguali.  Si vede solo\n"
            "  //   guardando i biglietti di sessione sul filo, ed e' cosi' che e'\n"
            "  //   saltato fuori il 10 agosto 2026 `[M]`.\n"
            "  SSL_set_early_data_enabled(ssl_, 0);\n",
            "il 0-RTT, spento",
        ),
    ]


CORPO = r'''namespace {
// ⭐ REMOTIX B2 — un intero variabile di QUIC (RFC 9000 §16).  Serve tre volte
//    e non c'e' in nessuna delle due librerie: nghttp3 il suo se lo tiene per
//    se'.  Sedici righe che sono gia' collante.
size_t wt_scrivi_varint(uint8_t *dest, uint64_t v) {
  if (v < 64) {
    dest[0] = static_cast<uint8_t>(v);
    return 1;
  }
  if (v < 16384) {
    dest[0] = static_cast<uint8_t>(0x40 | (v >> 8));
    dest[1] = static_cast<uint8_t>(v & 0xff);
    return 2;
  }
  if (v < 1073741824) {
    dest[0] = static_cast<uint8_t>(0x80 | (v >> 24));
    dest[1] = static_cast<uint8_t>((v >> 16) & 0xff);
    dest[2] = static_cast<uint8_t>((v >> 8) & 0xff);
    dest[3] = static_cast<uint8_t>(v & 0xff);
    return 4;
  }
  dest[0] = static_cast<uint8_t>(0xc0 | (v >> 56));
  for (size_t i = 1; i < 8; ++i) {
    dest[i] = static_cast<uint8_t>((v >> (8 * (7 - i))) & 0xff);
  }
  return 8;
}

// Restituisce 0 se i byte non bastano: «non lo so ancora» e «zero» sono due
// cose diverse, e confonderle e' `LEZIONI.md` §1.9.
size_t wt_leggi_varint(uint64_t *v, const uint8_t *src, size_t len) {
  if (len == 0) {
    return 0;
  }
  size_t n = static_cast<size_t>(1) << (src[0] >> 6);
  if (len < n) {
    return 0;
  }
  *v = src[0] & 0x3f;
  for (size_t i = 1; i < n; ++i) {
    *v = (*v << 8) | src[i];
  }
  return n;
}

// ⛔ I due numeri con cui un server dichiara WebTransport, e sono DUE perche'
//    le bozze in circolazione sono due:
//
//      0x2b603742  SETTINGS_ENABLE_WEBTRANSPORT   bozza 02
//      0xc671706a  SETTINGS_WT_MAX_SESSIONS       bozza 07 e oltre
//
// ⚠ E la differenza non e' accademica: `aioquic` 1.2 — il nostro cliente di
//   prova — implementa la **02** [R] `h3/connection.py:90`, mentre i browser
//   di oggi cercano la **07**.  Un server che ne mandasse una sola
//   funzionerebbe con meta' dei nostri strumenti e non con l'altra meta', e
//   la meta' che funziona sarebbe quella sbagliata da cui trarre conclusioni.
//   Si mandano tutt'e due: un'impostazione sconosciuta si ignora.
constexpr uint64_t WT_ENABLE_WEBTRANSPORT = 0x2b603742ULL;
constexpr uint64_t WT_MAX_SESSIONS = 0xc671706aULL;

// ⛔⭐ IL TETTO DI UNA CAPSULA, E SI CONTROLLA PRIMA DI TENERE I BYTE.
//
// `RCP.md` §6.1: «un ricevente che alloca `lunghezza` byte e poi verifica ha
// gia' regalato un megabyte a chiunque sappia scrivere sei byte».  ⚠ Qui non
// si allocava: si **aspettava** — che e' lo stesso regalo fatto piu'
// lentamente, e senza nemmeno un tetto.
//
// ⭐ Il numero e' quel che serve alla sola capsula che ci riguarda:
// `CLOSE_WEBTRANSPORT_SESSION` porta un codice a 32 bit e una ragione che
// WebTransport limita a **1024 byte**.  Piu' i due interi variabili di testa,
// che al massimo sono otto ciascuno.
constexpr uint64_t WT_CAPSULA_MAX = 1024 + 4;

nghttp3_ssize wt_niente_dati(nghttp3_conn *conn, int64_t stream_id,
                             nghttp3_vec *vec, size_t veccnt, uint32_t *pflags,
                             void *user_data, void *stream_user_data) {
  (void)conn;
  (void)stream_id;
  (void)vec;
  (void)veccnt;
  (void)pflags;
  (void)user_data;
  (void)stream_user_data;
  // ⛔ Lo stream della CONNECT estesa NON si chiude: E' la sessione.  Un
  //    lettore che dicesse «ho finito» ci metterebbe sopra il FIN, e la
  //    sessione morirebbe nell'istante in cui si apre.
  return NGHTTP3_ERR_WOULDBLOCK;
}
} // namespace

size_t ProtoCodec::wt_riscrivi_impostazioni(const nghttp3_vec *vec,
                                            size_t veccnt) {
  // Quel che nghttp3 vuole scrivere: il tipo dello stream di controllo (0x00)
  // seguito dal frame SETTINGS.
  std::vector<uint8_t> orig;
  for (size_t i = 0; i < veccnt; ++i) {
    orig.insert(orig.end(), vec[i].base, vec[i].base + vec[i].len);
  }
  if (orig.size() < 3) {
    return 0;
  }

  uint64_t tipo_stream = 0;
  auto n = wt_leggi_varint(&tipo_stream, orig.data(), orig.size());
  if (n == 0 || tipo_stream != 0x00) {
    std::println(stderr,
                 "REMOTIX B2: lo stream di controllo non comincia per 0x00 "
                 "(e' {}): non tocco niente",
                 tipo_stream);
    return 0;
  }
  auto p = n;

  uint64_t tipo_frame = 0;
  n = wt_leggi_varint(&tipo_frame, orig.data() + p, orig.size() - p);
  if (n == 0 || tipo_frame != 0x04) {
    std::println(stderr, "REMOTIX B2: il primo frame non e' SETTINGS (e' {})",
                 tipo_frame);
    return 0;
  }
  p += n;

  uint64_t lung = 0;
  n = wt_leggi_varint(&lung, orig.data() + p, orig.size() - p);
  if (n == 0) {
    return 0;
  }
  p += n;

  if (p + lung != orig.size()) {
    // ⛔ C'e' altro dopo SETTINGS, oppure SETTINGS e' arrivato a pezzi.  Non
    //    si riscrive alla cieca: si dice, e si lascia stare.  Il server
    //    restera' senza WebTransport, e la misura lo vedra' subito.
    std::println(stderr,
                 "REMOTIX B2: SETTINGS non e' tutto qui ({} + {} != {})", p,
                 lung, orig.size());
    return 0;
  }

  std::array<uint8_t, 64> aggiunta;
  size_t a = 0;
  a += wt_scrivi_varint(aggiunta.data() + a, WT_ENABLE_WEBTRANSPORT);
  a += wt_scrivi_varint(aggiunta.data() + a, 1);
  a += wt_scrivi_varint(aggiunta.data() + a, WT_MAX_SESSIONS);
  a += wt_scrivi_varint(aggiunta.data() + a, 1);

  std::array<uint8_t, 16> testa;
  size_t t = 0;
  t += wt_scrivi_varint(testa.data() + t, 0x00); // tipo dello stream
  t += wt_scrivi_varint(testa.data() + t, 0x04); // SETTINGS
  t += wt_scrivi_varint(testa.data() + t, lung + a);

  if (t + lung + a > wt_impbuf_.size()) {
    std::println(stderr, "REMOTIX B2: SETTINGS troppo grande per il buffer");
    return 0;
  }

  size_t o = 0;
  for (size_t i = 0; i < t; ++i) {
    wt_impbuf_[o++] = testa[i];
  }
  for (size_t i = 0; i < lung; ++i) {
    wt_impbuf_[o++] = orig[p + i];
  }
  for (size_t i = 0; i < a; ++i) {
    wt_impbuf_[o++] = aggiunta[i];
  }
  wt_impbuf_len_ = o;

  std::println(stderr,
               "REMOTIX B2: SETTINGS riscritto — {} byte di nghttp3 + {} "
               "nostri (ENABLE_WEBTRANSPORT e WT_MAX_SESSIONS)",
               orig.size(), a);

  return orig.size();
}

// ⛔⭐ LE CAPSULE DELLA CONNECT, E LA SOLA CHE CI RIGUARDA.
//
// Il corpo di una CONNECT estesa e' un flusso di capsule (RFC 9297): varint
// tipo, varint lunghezza, corpo.  Di tutte, qui se ne guarda **una**:
// `CLOSE_WEBTRANSPORT_SESSION` (0x2843), che porta un codice a 32 bit e una
// ragione in UTF-8 — ed e' la SECONDA STRADA di `RCP.md` §3.1 punto 3, quella
// per cui il motivo arriva anche quando i byte del canale non partono.
//
// ⚠ Si accumula, perche' una capsula puo' arrivare a pezzi; e si scarta il
//   resto senza rumore, perche' un flusso di capsule sconosciute non e' un
//   errore (RFC 9297 §3.2 dice di ignorarle).
void ProtoCodec::wt_capsula(int64_t stream_id, std::span<const uint8_t> dati) {
  if (stream_id != wt_sessione_ || dati.empty()) {
    return;
  }
  // ⛔ I byte di una capsula gia' giudicata troppo grande si buttano MENTRE
  //    PASSANO, senza tenerli: e' l'unico modo di non farsi riempire la
  //    memoria da chi sa scrivere due interi variabili.
  if (wt_capsalta_ > 0) {
    uint64_t n = wt_capsalta_ < dati.size()
                   ? wt_capsalta_
                   : static_cast<uint64_t>(dati.size());
    wt_capsalta_ -= n;
    dati = dati.subspan(static_cast<size_t>(n));
    if (dati.empty()) {
      return;
    }
  }
  wt_capsbuf_.insert(wt_capsbuf_.end(), dati.begin(), dati.end());
  for (;;) {
    uint64_t tipo = 0, lung = 0;
    // ⚠ Qui il buffer non puo' crescere senza fine: un intero variabile e' al
    //   massimo 8 byte, quindi con 8 byte il tipo si legge sempre e con 16 si
    //   legge sempre anche la lunghezza.
    auto a = wt_leggi_varint(&tipo, wt_capsbuf_.data(), wt_capsbuf_.size());
    if (a == 0) {
      return;
    }
    auto b = wt_leggi_varint(&lung, wt_capsbuf_.data() + a,
                             wt_capsbuf_.size() - a);
    if (b == 0) {
      return;
    }
    // ⛔⭐ E LA LUNGHEZZA SI CONTROLLA QUI, PRIMA DI ASPETTARE I BYTE.
    //
    //    L'ingresso che questo chiude: la pagina manda, sullo stream della
    //    CONNECT, un tipo di capsula sconosciuto e una lunghezza di 2^62-1;
    //    poi manda dati, all'infinito.  Nessuna capsula si completava mai,
    //    quindi `erase` non veniva mai chiamata, `wt_capsbuf_` cresceva di
    //    ogni byte che arrivava — e `http_consume` continuava ad allargare il
    //    credito, quindi il client poteva spedire senza fine.  ⛔ Su una
    //    connessione che non ha ancora superato la stretta di mano di RCP.
    //
    // ⚠ E la variante non ostile e' altrettanto vera: una capsula legittima
    //   ma sconosciuta di mezzo gigabyte veniva bufferizzata TUTTA per poi
    //   essere scartata.  RFC 9297 §3.2 permette di saltarla senza tenerla, ed
    //   e' quel che si fa adesso.
    if (lung > WT_CAPSULA_MAX) {
      std::println(stderr,
                   "REMOTIX B2: capsula {:#x} lunga {} byte, oltre il tetto di "
                   "{}: si SALTA senza tenerla (RFC 9297 §3.2; RCP.md §6.1, la "
                   "lunghezza si controlla prima di allocare)",
                   tipo, lung, WT_CAPSULA_MAX);
      uint64_t qui = wt_capsbuf_.size() - a - b;
      uint64_t presi = qui < lung ? qui : lung;
      wt_capsalta_ = lung - presi;
      wt_capsbuf_.erase(wt_capsbuf_.begin(),
                        wt_capsbuf_.begin() +
                          static_cast<long>(a + b + static_cast<size_t>(presi)));
      if (wt_capsalta_ > 0) {
        return;
      }
      continue;
    }
    if (wt_capsbuf_.size() < a + b + lung) {
      return; // sta sotto il tetto: si puo' aspettare che arrivi tutta
    }
    const uint8_t *corpo = wt_capsbuf_.data() + a + b;
    if (tipo == 0x2843 && lung >= 4) {
      uint32_t codice = (static_cast<uint32_t>(corpo[0]) << 24) |
                        (static_cast<uint32_t>(corpo[1]) << 16) |
                        (static_cast<uint32_t>(corpo[2]) << 8) |
                        static_cast<uint32_t>(corpo[3]);
      std::string ragione{corpo + 4, corpo + lung};
      std::println(stderr,
                   "REMOTIX B2: la pagina ha CHIUSO la sessione WebTransport: "
                   "codice {:#x} «{}»",
                   codice, ragione);
      // ⛔ Il codice si consegna INTERO.  Troncarlo al byte basso faceva
      //    entrare `0x0100` a verbale come `0x00`, cioe' come il solo valore
      //    che RCP.md §3.1 vieta — e i due registri della stessa chiusura si
      //    contraddicevano a due righe di distanza.
      wt_chiusa_dal_client(codice);
    }
    wt_capsbuf_.erase(wt_capsbuf_.begin(),
                      wt_capsbuf_.begin() + static_cast<long>(a + b + lung));
  }
}

// ⚠ Vuote apposta: quel che la chiusura del client e la fine del canale
//   SIGNIFICHINO non lo sa lo strato WebTransport — lo sa il protocollo, e RCP
//   arriva con B3.
void ProtoCodec::wt_chiusa_dal_client(uint32_t codice) { (void)codice; }

void ProtoCodec::wt_fin_dal_client(int64_t stream_id) { (void)stream_id; }

void ProtoCodec::wt_accoda(int64_t stream_id, std::span<const uint8_t> dati) {
  wt_uscita_.push_back(
    WtUscita{stream_id, std::vector<uint8_t>{dati.begin(), dati.end()}, 0});
}

ProtoCodec::WtEsito ProtoCodec::wt_smista(int64_t stream_id,
                                          std::span<const uint8_t> data,
                                          bool fin,
                                          std::vector<uint8_t> &riunito) {
  // Solo gli stream bidirezionali aperti dal client: la CONNECT estesa e gli
  // stream WebTransport arrivano tutti di li'.
  if ((stream_id & 0x03) != 0x00) {
    return WtEsito::HTTP3;
  }

  if (wt_nonwt_.contains(stream_id)) {
    return WtEsito::HTTP3;
  }

  if (wt_streams_.contains(stream_id)) {
    // ⭐ Uno stream WebTransport gia' riconosciuto: il carico utile torna
    //    indietro sullo stesso stream.  E' il «byte che torna» di B2 — e
    //    «la sessione si apre» senza «i byte tornano» e' il tipo di verde
    //    che questo banco esiste per non produrre.
    if (!data.empty()) {
      wt_accoda(stream_id, data);
      ngtcp2_conn_extend_max_stream_offset(conn_, stream_id, data.size());
      ngtcp2_conn_extend_max_offset(conn_, data.size());
    }
    // ⛔ E IL FIN SI GUARDA DOPO I BYTE, non prima: gli ultimi byte sono
    //    arrivati **insieme** a lui e vanno consegnati mentre la sessione e'
    //    ancora viva, o chi li riceve li leggerebbe come byte spediti dopo la
    //    fine — cioe' come una violazione del client che non c'e' stata.
    if (fin) {
      wt_fin_dal_client(stream_id);
    }
    return WtEsito::MIO;
  }

  auto &pref = wt_incerti_[stream_id];
  pref.insert(pref.end(), data.begin(), data.end());
  if (pref.size() < 2) {
    // ⚠ E NON si allarga la finestra: quei byte non li ha ancora presi
    //    nessuno, e contarli adesso e poi di nuovo falserebbe il credito.
    return WtEsito::ATTENDI;
  }

  // ⛔ Il tipo di frame WEBTRANSPORT_STREAM e' 0x41 — ma un intero variabile
  //    non lo scrive in un byte: 0x41 vale 65, e in un byte ce ne stanno 63.
  //    Sul filo sono DUE byte, 0x40 0x41, ed e' per questo che due bastano a
  //    decidere.  Un frame HEADERS comincia per 0x01, uno DATA per 0x00.
  if (pref[0] == 0x40 && pref[1] == 0x41) {
    uint64_t sessione = 0;
    auto n = wt_leggi_varint(&sessione, pref.data() + 2, pref.size() - 2);
    if (n == 0) {
      return WtEsito::ATTENDI;
    }
    auto consumati = pref.size();
    std::vector<uint8_t> resto{pref.begin() + 2 + static_cast<long>(n),
                               pref.end()};
    wt_streams_[stream_id] = static_cast<int64_t>(sessione);
    wt_incerti_.erase(stream_id);
    std::println(stderr, "REMOTIX B2: stream {} e' WebTransport, sessione {}",
                 stream_id, sessione);
    if (!resto.empty()) {
      wt_accoda(stream_id, resto);
    }
    ngtcp2_conn_extend_max_stream_offset(conn_, stream_id, consumati);
    ngtcp2_conn_extend_max_offset(conn_, consumati);
    // ⛔ Anche qui: lo stream puo' essere riconosciuto e finito nello stesso
    //    pacchetto (RCP.md §4.2, il FIN da una qualunque delle due parti).
    if (fin) {
      wt_fin_dal_client(stream_id);
    }
    return WtEsito::MIO;
  }

  riunito = pref;
  wt_incerti_.erase(stream_id);
  wt_nonwt_[stream_id] = true;
  return WtEsito::HTTP3;
}

std::expected<void, Error> ProtoCodec::wt_apri_sessione(Stream *stream) {
  // ⛔ RCP.md §2.2: il server NON DEVE accettare una sessione WebTransport su
  //    un percorso diverso, e il rifiuto e' **404** (rilievo R1.24, che ha
  //    scelto uno dei tre stati che erano tutti leciti).  E si scrive nel
  //    registro: e' §3 applicata al primo byte.
  if (stream->uri != "/rcp/1") {
    std::println(stderr,
                 "REMOTIX B2: ⛔ sessione WebTransport RIFIUTATA, percorso {}",
                 stream->uri);
    return send_status_response(stream, 404);
  }

  auto nva = std::to_array({
    util::make_nv_nn(":status"sv, "200"sv),
    util::make_nv_nn("server"sv, NGTCP2_SERVER),
  });

  nghttp3_data_reader dr{
    .read_data = wt_niente_dati,
  };

  if (auto rv = nghttp3_conn_submit_response(httpconn_, stream->stream_id,
                                             nva.data(), nva.size(), &dr);
      rv != 0) {
    std::println(stderr, "nghttp3_conn_submit_response: {}",
                 nghttp3_strerror(rv));
    return std::unexpected{Error::HTTP3};
  }

  wt_sessione_ = stream->stream_id;
  stream->wt_session = true;
  std::println(stderr,
               "REMOTIX B2: ⭐ sessione WebTransport APERTA su {} (stream {})",
               stream->uri, stream->stream_id);

  return {};
}

'''


def leggi(percorso):
    with open(percorso, encoding="utf-8") as f:
        return f.read()


def scrivi(percorso, testo):
    with open(percorso, "w", encoding="utf-8") as f:
        f.write(testo)


def righe_di_commento(righe):
    """⛔ UNA REGOLA SOLA PER I COMMENTI, E LA STESSA NEI TRE INNESTI.

    Il 10 agosto 2026 i tre script ne avevano tre diverse sulla stessa
    grandezza — `//` qui, `//`+`/*`+`*` in B3, `*`+`/*` in quello di quiche —
    e la seconda classificava come COMMENTO due righe di C++ vero che stanno
    nel corpo innestato da questo file:

        *v = src[0] & 0x3f;
        *v = (*v << 8) | src[i];

    ⚠ Sono dereferenziazioni, e cominciano per `*`.  Qui l'asterisco vale come
      commento solo quando e' la continuazione di un blocco `/* … */`, cioe'
      quando e' seguito da uno spazio o quando chiude il blocco.
    """
    return sum(1 for r in righe
               if r.strip().startswith(("//", "/*", "* ", "*/"))
               or r.strip() == "*")


def togli():
    # ⛔ E SI DICE CHE COSA SI PORTA VIA.
    #
    #    `git checkout -- examples` rimette a posto TUTTA la cartella: se sopra
    #    c'e' l'innesto di B3, o i guasti di B11, o una prova fatta a mano,
    #    spariscono anche quelli.  Il messaggio di prima diceva soltanto «si
    #    rimette l'esempio com'era», cioe' meno di quel che il comando fa.
    print("== Si rimette l'esempio com'era")
    prima = ""
    for f in FILE_TOCCATI:
        try:
            prima += leggi(f"{ESEMPI}/{f}")
        except FileNotFoundError:
            pass
    for marca, chi in ((MARCA_B3, "l'innesto di B3"),
                       (MARCA_B11, "i guasti di B11")):
        if marca in prima:
            print(f"   ⚠ c'e' anche {chi}: sparisce insieme a questo.")
    r = subprocess.run(["git", "-C", ALBERO, "checkout", "--", "examples"])
    if r.returncode != 0:
        print(f"   ⛔ git checkout e' fallito (uscita {r.returncode}):"
              " non si e' tolto niente.")
        return r.returncode

    # ⛔ E SI VERIFICA DI AVER TOLTO.
    #
    #    Lo stato d'uscita di git dice che git non ha protestato, non che la
    #    marca sia sparita: e' la quarta regola di `LEZIONI.md` §1.9 — «zero» e
    #    «sono fallita» non devono avere la stessa faccia.  L'unica lettura che
    #    vale e' rileggere i file.  `01-b11-guasto.sh` questo controllo lo fa
    #    gia' per la propria marca; qui mancava.
    resta = 0
    for f in FILE_TOCCATI:
        try:
            n = leggi(f"{ESEMPI}/{f}").count(MARCA)
        except FileNotFoundError:
            n = 0
        if n:
            print(f"   NO  restano {n} righe con «{MARCA}» in {f}")
            resta += n
    if resta:
        print(f"   ⛔ {resta} tracce di «{MARCA}» sopravvivono:"
              " l'esempio NON e' com'era.")
        return 3
    print(f"   OK  nessuna traccia di «{MARCA}» nei {len(FILE_TOCCATI)}"
          " file toccati")

    # ⚠ E i file NON TRACCIATI git non li tocca: se B3 e' passato di qui, i
    #   suoi tre file restano orfani dentro un esempio «com'era».
    orfani = [f for f in FILE_DI_B3 if os.path.exists(f"{ESEMPI}/{f}")]
    if orfani:
        print(f"   ⚠ restano in examples/ i file di B3: {', '.join(orfani)}")
        print("     git checkout non tocca i file non tracciati; li porta via"
              " 01-b3-rcp-innesta.py --togli")
    return 0


def main():
    if "--togli" in sys.argv:
        return togli()

    lista = innesti()
    # Il pezzo 12 e' il corpo, che sta in una costante a parte per leggibilita'.
    lista = [
        (f, a, (CORPO + a) if s is None else s, n) for (f, a, s, n) in lista
    ]

    print("== L'innesto dello strato WebTransport nell'esempio di ngtcp2")
    print(f"   albero: {ESEMPI}")
    print(f"   {len(lista)} innesti da applicare\n")

    # Gia' fatto?
    if MARCA in leggi(f"{ESEMPI}/http3_server_proto_codec.cc"):
        print("   ⚠ l'innesto c'e' gia': non si tocca niente.")
        print("     per rifarlo da capo: --togli, poi di nuovo questo comando")
        return 0

    # ⛔ IL DENOMINATORE DEL CONTO DELLE RIGHE, LETTO PRIMA DI TOCCARE NIENTE.
    #
    #    `git diff -- examples` misura tutto quel che e' cambiato in quella
    #    cartella, da chiunque: e' il conto NOSTRO solo se prima non c'era
    #    nient'altro.  Si guarda adesso, non dopo, perche' dopo la nostra
    #    modifica c'e' dentro e non si distingue piu'.
    #    ⚠ I file non tracciati (`??`) non entrano nel diff, quindi non
    #      sporcano il conto: si ignorano qui.
    sporchi = [
        r for r in subprocess.run(
            ["git", "-C", ALBERO, "status", "--porcelain", "--", "examples"],
            capture_output=True, text=True).stdout.splitlines()
        if not r.startswith("??")
    ]

    testi = {}
    guasti = 0
    for percorso, appiglio, sostituto, nome in lista:
        if percorso not in testi:
            testi[percorso] = leggi(f"{ESEMPI}/{percorso}")
        # ⛔ IL CONTROLLO CHE RENDE ONESTO TUTTO IL RESTO: l'appiglio deve
        #    comparire UNA VOLTA SOLA.  Zero vuol dire che il loro esempio e'
        #    cambiato sotto di noi; due, che si sta innestando alla cieca.
        n = testi[percorso].count(appiglio)
        stato = "OK " if n == 1 else "NO "
        print(f"   {stato} {nome:38s} appiglio trovato {n} volta/e  [{percorso}]")
        if n != 1:
            guasti += 1
            continue
        testi[percorso] = testi[percorso].replace(appiglio, sostituto, 1)

    if guasti:
        print(f"\n   ⛔ {guasti} appigli su {len(lista)} non sono UNO: non si scrive niente.")
        print("      L'esempio di ngtcp2 e' cambiato: gli innesti vanno riletti.")
        return 2

    for percorso, testo in testi.items():
        scrivi(f"{ESEMPI}/{percorso}", testo)
    print(f"\n   OK  {len(lista)} innesti su {len(lista)}, in {len(testi)} file")

    # ⭐ Il conto delle righe, che e' il dato di §6.4 e non una stima.
    #
    # ⚠ Il conto si fa QUI, in Python, e non con una pipeline di shell: il
    #   primo tentativo del 10 agosto passava `grep -c` attraverso tre shell
    #   annidate, le virgolette si sono rotte, e ha stampato «0 commenti, 0
    #   righe vuote» su un file che ne ha 85 e 42.  Un altro falso zero.
    print("\n== Quante righe sono cambiate sotto examples/ — il dato di §6.4")
    subprocess.run(
        ["git", "-C", ALBERO, "diff", "--stat", "--", "examples"],
    )
    d = subprocess.run(
        ["git", "-C", ALBERO, "diff", "-U0", "--", "examples"],
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    agg = [r[1:] for r in d if r.startswith("+") and not r.startswith("+++")]
    vuote = sum(1 for r in agg if not r.strip())
    comm = righe_di_commento(agg)
    print(f"\n   righe aggiunte : {len(agg)}")
    print(f"     vuote        : {vuote}")
    print(f"     di commento  : {comm}")
    print(f"     ⭐ di CODICE  : {len(agg) - vuote - comm}")

    # ⛔ E IL DENOMINATORE SI STAMPA ACCANTO AL NUMERO, non si sottintende.
    if sporchi:
        print("\n   ⛔ E QUESTO CONTO NON E' ATTRIBUIBILE A NOI: prima")
        print("      dell'innesto questi file erano gia' modificati —")
        for r in sporchi:
            print(f"        {r}")
        print("      git diff non sa di chi sia una riga: misura la cartella.")
    else:
        print("\n   ⭐ e l'albero era PULITO prima dell'innesto (git status)")
        print("      — che e' l'unica cosa che rende «cambiate» = «nostre».")
    print("\n   ⚠ «aggiunte» resta un limite superiore: una riga MODIFICATA")
    print("     (per esempio SSL_set_early_data_enabled a 0) compare fra le")
    print("     aggiunte, e la sua riga vecchia fra le tolte.")
    print("\n   ⚠ E' lo strato WebTransport, NON un server: sotto c'e' il loro")
    print("     HTTP/3 completo.  Il numero risponde a «quanto collante resta a")
    print("     noi», che e' la domanda di §6.4 — non a «quanto pesa il server».")
    return 0


if __name__ == "__main__":
    sys.exit(main())
