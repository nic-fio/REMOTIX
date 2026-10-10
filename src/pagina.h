/*
 * pagina.h — THE TCP LISTENER: the server's second job.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE SECOND OF THE TWO LISTENERS, WITH THE SAME PORT NUMBER
 *
 * `RCP.md` §2.4: «7447, and they are TWO listeners with the same number: UDP for
 * HTTP/3 and WebTransport, TCP for the first load of the page».  ⚠ «TCP only
 * serves to deliver the page, and HTTP/1.1 is enough for it.  From there on the
 * browser opens the WebTransport session on its own, over UDP.»
 *
 * ---------------------------------------------------------------------------
 * ⛔ AND HOW THE PAGE IS SERVED IS A PRODUCT CONSTRAINT
 *
 * `SPECIFICHE.md` §11.5: it must be delivered **cross-origin isolated** — the two
 * headers the browser demands to give the page full-resolution timers and
 * shared memory.  ⚠ «It is not a bench tuning: it changes how the server serves
 * EVERY resource of the page, and deciding it later means rewriting the way the
 * page is packaged.»
 *
 * The headers, and the third that the two imply:
 *
 *   Cross-Origin-Opener-Policy: same-origin
 *   Cross-Origin-Embedder-Policy: require-corp
 *   Cross-Origin-Resource-Policy: same-origin   ← on EVERY resource
 *
 * ⛔ The third is not an extra: with `require-corp` the browser refuses every
 *    sub-resource that does not declare it, and the symptom does not name the
 *    isolation — the resource simply does not load.  It is precisely the
 *    «changes how the server serves every resource» that §11.5 declares.
 *
 * ---------------------------------------------------------------------------
 * ⛔ AND TWO THINGS THE PAGE CARRIES, AND NO OTHER ROAD CAN CARRY
 *
 *   1. **the fingerprint of the SESSION certificate**, written inside the page
 *      (`RCP.md` §4.1-bis, `serverCertificateHashes`): it is our trust model,
 *      and the server itself serves the page precisely so that it can write
 *      the current fingerprint into it;
 *
 *   2. **the endpoint from which the page fetches the updated fingerprint** (`/impronta`).
 *      ⛔ «A tab left open for two weeks holds the fingerprint of a certificate
 *      that has been rotated in the meantime: on reconnection the browser
 *      refuses, and the symptom is *it no longer connects and does not say
 *      why*.»  ⛔ And it does NOT go through RCP: the session is not open yet,
 *      so there is no channel on which to ask.
 *
 * ---------------------------------------------------------------------------
 * ⛔ AND WHOEVER IS BANNED SEES THE PAGE ANYWAY
 *
 * `SPECIFICHE.md` §4.2: «the page loads anyway and says that the attempts are
 * exhausted.  ⛔ Never a silence: whoever is banned by mistake is almost always
 * the owner».
 */
#ifndef REMOTIX_PAGINA_H
#define REMOTIX_PAGINA_H

#include "certificati.h"

#include <openssl/ssl.h>
#include <poll.h>
#include <stdbool.h>
#include <stddef.h>

typedef struct pagina pagina;

pagina *pagina_apri(const char *indirizzo, const char *porta, SSL_CTX *ctx,
                    const char *file_html, const certificati *cert);
void pagina_chiudi(pagina *p);

void pagina_contesto(pagina *p, SSL_CTX *ctx);

/* The descriptors to watch.  Returns how many it put in. */
size_t pagina_descrittori(pagina *p, struct pollfd *dove, size_t cap);
/* To be called after the `poll`, with the same array. */
void pagina_muovi(pagina *p, struct pollfd *dove, size_t quanti);

#endif
