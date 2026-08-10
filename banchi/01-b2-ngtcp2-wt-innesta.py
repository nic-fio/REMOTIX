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
   ngtcp2 dice esattamente quante righe sono nostre.  Non e' una stima.

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
import subprocess
import sys

ESEMPI = "/srv/src/b2/ngtcp2/examples"
MARCA = "REMOTIX B2"

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
  WtEsito wt_smista(int64_t stream_id, std::span<const uint8_t> data,
                    std::vector<uint8_t> &riunito);
  void wt_accoda(int64_t stream_id, std::span<const uint8_t> dati);

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
  // gli stream bidirezionali del client: quelli di cui non si sa ancora che
  // cosa siano, quelli che sono WebTransport, quelli che non lo sono
  std::unordered_map<int64_t, std::vector<uint8_t>> wt_incerti_;
  std::unordered_map<int64_t, int64_t> wt_streams_;
  std::unordered_map<int64_t, bool> wt_nonwt_;
  std::deque<WtUscita> wt_uscita_;
  int64_t wt_sessione_{-1};
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
            "  std::array<nghttp3_vec, 16> vec;\n\n  for (;;) {\n"
            "    // ⭐ REMOTIX B2 — se la riscrittura delle impostazioni e' andata\n"
            "    //    storta, ci si ferma: uno stream di controllo mezzo scritto\n"
            "    //    e' peggio di una connessione chiusa.\n"
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
      wt_orig =
        wt_riscrivi_impostazioni(vec.data(), static_cast<size_t>(sveccnt));
    }

    if (sveccnt <= 0 && !wt_uscita_.empty()) {
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
      wt_vec[0].base = wt_impbuf_.data();
      wt_vec[0].len = wt_impbuf_len_;
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
      if (c != wt_impbuf_len_) {
        std::println(stderr,
                     "REMOTIX B2: impostazioni scritte a meta' ({} di {})", c,
                     wt_impbuf_len_);
        wt_guasto_ = true;
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
            "        //    per lui non esiste.  I byte si buttano, E SI DICE.\n"
            "        if (wt_mio) {\n"
            "          std::println(stderr,\n"
            "                       \"REMOTIX B2: stream {} bloccato, byte buttati\",\n"
            "                       stream_id);\n"
            "          wt_uscita_.pop_front();\n"
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
            "  std::vector<uint8_t> wt_riunito;\n"
            "  switch (wt_smista(stream_id, data, wt_riunito)) {\n"
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

void ProtoCodec::wt_accoda(int64_t stream_id, std::span<const uint8_t> dati) {
  wt_uscita_.push_back(
    WtUscita{stream_id, std::vector<uint8_t>{dati.begin(), dati.end()}, 0});
}

ProtoCodec::WtEsito ProtoCodec::wt_smista(int64_t stream_id,
                                          std::span<const uint8_t> data,
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


def main():
    if "--togli" in sys.argv:
        print("== Si rimette l'esempio com'era")
        r = subprocess.run(
            ["git", "-C", "/srv/src/b2/ngtcp2", "checkout", "--", "examples"],
        )
        return r.returncode

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
    print("\n== Quante righe sono NOSTRE — il dato di DECISIONI.md §6.4")
    subprocess.run(
        ["git", "-C", "/srv/src/b2/ngtcp2", "diff", "--stat", "--", "examples"],
    )
    d = subprocess.run(
        ["git", "-C", "/srv/src/b2/ngtcp2", "diff", "-U0", "--", "examples"],
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    agg = [r[1:] for r in d if r.startswith("+") and not r.startswith("+++")]
    vuote = sum(1 for r in agg if not r.strip())
    comm = sum(1 for r in agg if r.strip().startswith("//"))
    print(f"\n   righe aggiunte : {len(agg)}")
    print(f"     vuote        : {vuote}")
    print(f"     di commento  : {comm}")
    print(f"     ⭐ di CODICE  : {len(agg) - vuote - comm}")
    print("\n   ⚠ E' lo strato WebTransport, NON un server: sotto c'e' il loro")
    print("     HTTP/3 completo.  Il numero risponde a «quanto collante resta a")
    print("     noi», che e' la domanda di §6.4 — non a «quanto pesa il server».")
    return 0


if __name__ == "__main__":
    sys.exit(main())
