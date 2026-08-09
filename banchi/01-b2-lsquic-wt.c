/*
 * 01-b2-lsquic-wt.c — il collante WebTransport su lsquic, per il banco B2.
 *
 * =========================================================================
 * CHE COSA MISURA
 *
 * `DECISIONI.md` §6.4 sceglie la libreria QUIC, e il criterio e' «quanto
 * collante resta a noi».  Questo file E' quel collante, per la candidata
 * `lsquic`: le righe qui dentro sono il numero che B2 deve produrre.
 *
 * Si appoggia allo scheletro dei loro esempi (`bin/prog.c`, `bin/test_common.c`)
 * esattamente come fa `echo_server.c`, perche' il paragone sia onesto: si parte
 * da dove parte chiunque, non dal foglio bianco.
 *
 * =========================================================================
 * ⛔ E LA PREVISIONE CHE QUESTO PROGRAMMA DEVE FALSIFICARE
 *
 * `[R]` `lsquic_hcso_writer.c` scrive, sullo stream di controllo HTTP/3:
 *
 *     SETTINGS_ENABLE_WEBTRANSPORT   0x2b603742   <- bozza 02
 *     WEBTRANSPORT_MAX_SESSIONS      0x2b603743   <- bozza 02
 *     H3_DATAGRAM_ENABLED            0x33         <- corrente
 *     SETTINGS_ENABLE_CONNECT_PROTOCOL 0x08       <- corrente
 *
 * e NON scrive mai `SETTINGS_WT_MAX_SESSIONS` (0xc671706a), che e' quella con
 * cui un server dichiara WebTransport dalla bozza 07 in poi — cioe' quella che
 * i browser di oggi cercano.
 *
 * PREVISIONE: Chrome e Firefox non stabiliranno la sessione.
 * IL CONTRARIO: se si apre lo stesso, o i browser accettano ancora la bozza
 *               02, o ho letto male quel file — e va scritto perche'.
 *
 * ⚠ La previsione riguarda il DIALOGO, non questo file: se il browser rifiuta,
 *   non e' detto che il collante sia sbagliato.  Per distinguerli c'e' il
 *   cliente di prova, che parla la bozza corrente: se ACCETTA questa sessione
 *   mentre il browser la rifiuta, il collante e' giusto e il difetto e' nelle
 *   costanti di lsquic.  ⛔ Senza quel secondo lettore i due casi hanno lo
 *   stesso aspetto.
 * =========================================================================
 */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/queue.h>
#include <unistd.h>

#include "lsquic.h"
#include "test_common.h"
/* ⚠ `test_cert.h` dichiara un campo di tipo `struct lsquic_hash_elem` e NON
 *   include l'intestazione che lo definisce: senza questa riga il compilatore
 *   dice «field has incomplete type», che punta al file sbagliato.  Lo stesso
 *   ordine lo tiene `echo_server.c`. */
#include "../src/liblsquic/lsquic_hash.h"
#include "test_cert.h"
#include "prog.h"
#include "lsxpack_header.h"

#include "../src/liblsquic/lsquic_logger.h"

/* Il percorso e' l'identita' del protocollo (`RCP.md` §2.2): un percorso
 * diverso si rifiuta, e non si indovina. */
#define PERCORSO "/rcp/1"

struct server_ctx {
    struct sport_head    sports;
    struct prog         *prog;
};

/* -------------------------------------------------------------------------
 * Le intestazioni.
 *
 * lsquic consegna le intestazioni decodificate attraverso un'interfaccia che
 * l'applicazione deve fornire.  Ne serve il minimo: i tre pseudo-campi che
 * decidono se questa e' una sessione WebTransport per noi.
 * ------------------------------------------------------------------------- */
struct intestazioni {
    char    metodo[16];
    char    protocollo[32];
    char    percorso[128];
    struct lsxpack_header  corrente;
    char    grezzo[2048];
};

static void *
hset_crea (void *ctx, lsquic_stream_t *stream, int is_push)
{
    struct intestazioni *h = calloc(1, sizeof(*h));
    return h;
}

static struct lsxpack_header *
hset_prepara (void *hset, struct lsxpack_header *hdr, size_t spazio)
{
    struct intestazioni *h = hset;
    if (spazio > sizeof(h->grezzo))
        return NULL;                    /* ⛔ si rifiuta, non si tronca */
    if (hdr)
        lsxpack_header_prepare_decode(hdr, h->grezzo, 0, spazio);
    else {
        hdr = &h->corrente;
        memset(hdr, 0, sizeof(*hdr));
        lsxpack_header_prepare_decode(hdr, h->grezzo, 0, spazio);
    }
    return hdr;
}

/* Copia un campo dentro un buffer di misura fissa, sempre terminato. */
static void
copia (char *dove, size_t quanto, const char *da, size_t lun)
{
    if (lun >= quanto)
        lun = quanto - 1;
    memcpy(dove, da, lun);
    dove[lun] = '\0';
}

static int
hset_processa (void *hset, struct lsxpack_header *hdr)
{
    struct intestazioni *h = hset;
    const char *nome, *valore;

    if (!hdr)
        return 0;                       /* fine dell'insieme */
    nome   = lsxpack_header_get_name(hdr);
    valore = lsxpack_header_get_value(hdr);
    if (!nome || !valore)
        return 0;

    if (hdr->name_len == 7 && 0 == memcmp(nome, ":method", 7))
        copia(h->metodo, sizeof(h->metodo), valore, hdr->val_len);
    else if (hdr->name_len == 9 && 0 == memcmp(nome, ":protocol", 9))
        copia(h->protocollo, sizeof(h->protocollo), valore, hdr->val_len);
    else if (hdr->name_len == 5 && 0 == memcmp(nome, ":path", 5))
        copia(h->percorso, sizeof(h->percorso), valore, hdr->val_len);
    return 0;
}

static void
hset_scarta (void *hset)
{
    free(hset);
}

static const struct lsquic_hset_if hset_if = {
    .hsi_create_header_set  = hset_crea,
    .hsi_prepare_decode     = hset_prepara,
    .hsi_process_header     = hset_processa,
    .hsi_discard_header_set = hset_scarta,
};

/* -------------------------------------------------------------------------
 * La connessione e gli stream
 * ------------------------------------------------------------------------- */
struct lsquic_conn_ctx { int nulla; };

struct lsquic_stream_ctx {
    int     risposto;       /* la CONNECT estesa ha gia' avuto risposta */
    int     e_sessione;     /* questo stream E' la sessione WebTransport */
    char    buf[4096];
    size_t  quanto;
};

static lsquic_conn_ctx_t *
su_nuova_conn (void *ctx, lsquic_conn_t *conn)
{
    LSQ_NOTICE("connessione nuova");
    return NULL;
}

static void
su_conn_chiusa (lsquic_conn_t *conn)
{
    LSQ_NOTICE("connessione chiusa");
}

static lsquic_stream_ctx_t *
su_nuovo_stream (void *ctx, lsquic_stream_t *stream)
{
    lsquic_stream_ctx_t *st = calloc(1, sizeof(*st));
    lsquic_stream_wantread(stream, 1);
    return st;
}

static void
su_lettura (lsquic_stream_t *stream, lsquic_stream_ctx_t *st)
{
    struct intestazioni *h;
    ssize_t n;

    /* ⭐ Uno stream WebTransport aperto dal client: lsquic lo riconosce da se'
     *    — e' la parte che rende questa candidata piu' corta delle altre.  Si
     *    rimandano indietro i byte, che e' quel che il banco misura. */
    if (lsquic_stream_is_webtransport_client_bidi_stream(stream))
    {
        n = lsquic_stream_read(stream, st->buf + st->quanto,
                                        sizeof(st->buf) - st->quanto);
        if (n > 0) {
            st->quanto += (size_t) n;
            LSQ_NOTICE("stream WebTransport: %zd byte, li rimando", n);
            lsquic_stream_wantread(stream, 0);
            lsquic_stream_wantwrite(stream, 1);
        } else if (n == 0) {
            lsquic_stream_shutdown(stream, 0);
        }
        return;
    }

    /* Altrimenti e' una richiesta HTTP/3: qui vive la CONNECT estesa. */
    h = lsquic_stream_get_hset(stream);
    if (!h)
    {
        n = lsquic_stream_read(stream, st->buf, sizeof(st->buf));
        if (n <= 0)
            lsquic_stream_shutdown(stream, 0);
        return;
    }

    LSQ_NOTICE("richiesta: %s %s (:protocol=%s)",
                h->metodo, h->percorso,
                h->protocollo[0] ? h->protocollo : "-");

    if (0 == strcmp(h->metodo, "CONNECT") && 0 == strcmp(h->protocollo, "webtransport"))
    {
        if (0 != strcmp(h->percorso, PERCORSO))
        {
            /* ⛔ `RCP.md` §2.2: percorso sconosciuto -> 404, e nel registro. */
            LSQ_NOTICE("percorso sconosciuto '%s' -> 404", h->percorso);
            struct lsxpack_header hh[1];
            char s404[] = ":status404";
            lsxpack_header_set_offset2(&hh[0], s404, 0, 7, 7, 3);
            struct lsquic_http_headers hdrs = { .count = 1, .headers = hh };
            lsquic_stream_send_headers(stream, &hdrs, 1);
        }
        else
        {
            struct lsxpack_header hh[1];
            char s200[] = ":status200";
            lsxpack_header_set_offset2(&hh[0], s200, 0, 7, 7, 3);
            struct lsquic_http_headers hdrs = { .count = 1, .headers = hh };
            if (0 == lsquic_stream_send_headers(stream, &hdrs, 0))
            {
                /* ⭐ La riga che dichiara a lsquic «questo stream e' la
                 *    sessione»: da qui in poi classifica gli stream WT. */
                lsquic_stream_set_webtransport_session(stream);
                st->e_sessione = 1;
                LSQ_NOTICE("⭐ SESSIONE WEBTRANSPORT ACCETTATA");
            }
            else
                LSQ_ERROR("non sono riuscito a mandare le intestazioni");
        }
    }
    else
    {
        struct lsxpack_header hh[1];
        char s400[] = ":status400";
        lsxpack_header_set_offset2(&hh[0], s400, 0, 7, 7, 3);
        struct lsquic_http_headers hdrs = { .count = 1, .headers = hh };
        lsquic_stream_send_headers(stream, &hdrs, 1);
    }
    st->risposto = 1;
    lsquic_stream_wantread(stream, 0);
    lsquic_stream_flush(stream);
}

static void
su_scrittura (lsquic_stream_t *stream, lsquic_stream_ctx_t *st)
{
    if (st->quanto)
    {
        lsquic_stream_write(stream, st->buf, st->quanto);
        st->quanto = 0;
        lsquic_stream_flush(stream);
    }
    lsquic_stream_wantwrite(stream, 0);
    lsquic_stream_wantread(stream, 1);
}

static void
su_chiusura (lsquic_stream_t *stream, lsquic_stream_ctx_t *st)
{
    free(st);
}

static const struct lsquic_stream_if stream_if = {
    .on_new_conn        = su_nuova_conn,
    .on_conn_closed     = su_conn_chiusa,
    .on_new_stream      = su_nuovo_stream,
    .on_read            = su_lettura,
    .on_write           = su_scrittura,
    .on_close           = su_chiusura,
};

int
main (int argc, char **argv)
{
    struct server_ctx ctx;
    struct prog prog;
    int opt;

    memset(&ctx, 0, sizeof(ctx));
    TAILQ_INIT(&ctx.sports);
    ctx.prog = &prog;

    prog_init(&prog, LSENG_SERVER|LSENG_HTTP, &ctx.sports, &stream_if, &ctx);
    prog.prog_api.ea_hsi_if  = &hset_if;
    prog.prog_api.ea_hsi_ctx = NULL;

    while (-1 != (opt = getopt(argc, argv, PROG_OPTS "h")))
    {
        if (opt == 'h') {
            prog_print_common_options(&prog, stdout);
            exit(0);
        }
        if (0 != prog_set_opt(&prog, opt, optarg))
            exit(1);
    }

    /* ⭐ Le due righe che accendono WebTransport in lsquic. */
    prog.prog_settings.es_webtransport_server = 1;
    prog.prog_settings.es_max_webtransport_server_streams = 16;

    if (0 != prog_prep(&prog)) {
        LSQ_ERROR("preparazione fallita");
        exit(EXIT_FAILURE);
    }
    LSQ_NOTICE("in ascolto; percorso atteso " PERCORSO);
    if (0 != prog_run(&prog))
        exit(EXIT_FAILURE);
    prog_cleanup(&prog);
    exit(EXIT_SUCCESS);
}
