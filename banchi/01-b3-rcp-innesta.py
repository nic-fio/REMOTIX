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

⚠ Per questo, quando `rcp.c` entra nello stato «attesa-verdetto», l'ospite
  accende il **keep-alive di QUIC a 100 ms**: cosi' il percorso di scrittura
  viene percorso comunque, e `rcp_tempo()` ha modo di far scadere il ritardo.
  E' un filo dell'ospite, non una regola del protocollo — per questo sta qui e
  non in `rcp.c`.
"""
import os
import shutil
import subprocess
import sys

ESEMPI = "/srv/src/b2/ngtcp2/examples"
SORGENTI = "/srv/src/rcp"
MARCA = "REMOTIX B3"

FILE_NOSTRI = ["rcp.c", "rcp.h", "autenticazione.c"]

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
        "  void rcp_passa(int64_t stream_id, std::span<const uint8_t> dati);\n",
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
        "    }\n"
        "    return WtEsito::MIO;\n",
        "    if (!data.empty()) {\n"
        "      // ⭐ REMOTIX B3 — sul canale di controllo i byte vanno a RCP;\n"
        "      //    sugli altri stream resta l'eco di B2, che serve al banco\n"
        "      //    del trasporto.\n"
        "      if (stream_id == rcp_stream_) {\n"
        "        rcp_passa(stream_id, data);\n"
        "      } else {\n"
        "        wt_accoda(stream_id, data);\n"
        "      }\n"
        "      ngtcp2_conn_extend_max_stream_offset(conn_, stream_id, data.size());\n"
        "      ngtcp2_conn_extend_max_offset(conn_, data.size());\n"
        "    }\n"
        "    return WtEsito::MIO;\n",
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
        "    if (rcp_stream_ == -1) {\n"
        "      rcp_avvia(stream_id);\n"
        "    }\n",
        "il primo stream e' il controllo",
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
        "  std::array<nghttp3_vec, 16> vec;\n\n  for (;;) {\n",
        "  std::array<nghttp3_vec, 16> vec;\n"
        "\n"
        "  // ⭐ REMOTIX B3 — il tempo di RCP scorre di qui: e' l'unico punto\n"
        "  //    percorso comunque, anche quando non c'e' niente da spedire.\n"
        "  if (rcp_) {\n"
        "    rcp_tempo(rcp_, ngtcp2_conn_get_timestamp(conn_) / NGTCP2_MILLISECONDS);\n"
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
  if (std::string_view{rcp_stato_nome(rcp_)} == "attesa-verdetto") {
    ngtcp2_conn_set_keep_alive_timeout(conn_, 100 * NGTCP2_MILLISECONDS);
  } else {
    ngtcp2_conn_set_keep_alive_timeout(conn_, UINT64_MAX);
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
  std::array<uint8_t, 64> b{};
  size_t n = 0;
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
               "REMOTIX B3: chiusa la sessione WebTransport, codice {:#04x}",
               motivo);
}

'''


def main():
    if "--togli" in sys.argv:
        print("== Si rimette l'esempio com'era (resta l'innesto di B2)")
        subprocess.run(["git", "-C", "/srv/src/b2/ngtcp2", "checkout", "--",
                        "examples/CMakeLists.txt"])
        for f in FILE_NOSTRI:
            try:
                os.remove(os.path.join(ESEMPI, f))
            except FileNotFoundError:
                pass
        print("   ⚠ i file .cc/.h toccati da B3 vanno rimessi con"
              " 01-b2-ngtcp2-wt-innesta.py --togli e riapplicati")
        return 0

    print("== L'innesto di RCP nell'esempio di ngtcp2")
    with open(os.path.join(ESEMPI, "http3_server_proto_codec.cc"),
              encoding="utf-8") as f:
        if MARCA in f.read():
            print("   ⚠ l'innesto c'e' gia': non si tocca niente.")
            return 0

    # ⛔ I nostri file si COPIANO, non si linkano: l'albero di ngtcp2 e' di
    #    qualcun altro, e un collegamento simbolico che punta fuori si rompe
    #    in silenzio il giorno in cui qualcuno lo riclona.
    for f in FILE_NOSTRI:
        shutil.copyfile(os.path.join(SORGENTI, f), os.path.join(ESEMPI, f))
    print(f"   OK  {len(FILE_NOSTRI)} file nostri copiati in examples/")

    lista = list(INNESTI) + [
        ("http3_server_proto_codec.cc",
         "std::expected<void, Error> ProtoCodec::wt_apri_sessione(Stream *stream) {\n",
         None, "il corpo dei ganci"),
    ]
    testi, guasti = {}, 0
    for percorso, appiglio, sostituto, nome in lista:
        if sostituto is None:
            sostituto = CORPO + appiglio
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
                   "  void wt_chiudi_sessione(uint8_t motivo);\n"
                   "\n"
                   " private:\n", 1)
        print("   OK  i due ganci pubblici              appiglio trovato 1 volta/e")
    else:
        print("   NO  i due ganci pubblici              appiglio NON unico")
        guasti += 1

    if guasti:
        print(f"\n   ⛔ {guasti} appigli non sono UNO: non si scrive niente.")
        return 2
    for percorso, testo in testi.items():
        with open(os.path.join(ESEMPI, percorso), "w", encoding="utf-8") as f:
            f.write(testo)
    print(f"\n   OK  {len(lista) + 1} innesti, in {len(testi)} file")

    print("\n== Quante righe sono NOSTRE — e sono DUE numeri diversi")
    d = subprocess.run(["git", "-C", "/srv/src/b2/ngtcp2", "diff", "-U0", "--",
                        "examples"], capture_output=True, text=True).stdout.splitlines()
    agg = [r[1:] for r in d if r.startswith("+") and not r.startswith("+++")]
    cod = [r for r in agg if r.strip() and not r.strip().startswith(("//", "/*", "*"))]
    print(f"   dentro l'esempio (B2 + i fili di B3): {len(agg)} righe, {len(cod)} di codice")
    for f in FILE_NOSTRI:
        with open(os.path.join(SORGENTI, f)) as fh:
            righe = fh.read().splitlines()
        cod = [r for r in righe if r.strip() and not r.strip().startswith(("*", "/*", "//"))]
        print(f"   banchi/rcp/{f:<20s} {len(righe):>4} righe, {len(cod):>4} di codice")
    print("\n   ⭐ Il secondo gruppo e' il PROTOCOLLO, e non dipende da ngtcp2:")
    print("      e' quel che si porta via se un giorno la libreria cambia.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
