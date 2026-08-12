# Makefile — REMOTIX_V2, il server.
#
# -----------------------------------------------------------------------------
# ⛔ LE DIPENDENZE, DICHIARATE — non «quelle che c'erano sulla macchina»
#
# `LEZIONI.md` §2.5-bis: «le dipendenze installate a mano diventano invisibili
# nel giro di un giorno, e il momento in cui te ne accorgi e' sempre quello in
# cui hai bisogno che la macchina riparta».  Da cui questo elenco, e il bersaglio
# `dipendenze` che le CONTROLLA prima di compilare invece di lasciarle fallire
# venti righe dopo con un errore che non le nomina.
#
#   ngtcp2 >= 1.25            il QUIC                   (DECISIONI.md §6.4)
#   ngtcp2_crypto_ossl        il ponte verso OpenSSL    (vedi src/tls.h)
#   nghttp3 >= 1.18           l'HTTP/3
#   OpenSSL >= 3.5            TLS 1.3 con l'API QUIC nativa, e X509 per i
#                             due certificati (src/certificati.c)
#   libpam                    l'autenticazione          (SPECIFICHE.md §4.2)
#
# ⭐ E LE CINQUE DELLA FASE 2, innestate il 12 agosto 2026 dal montaggio
#    (`fasi/rapporti/P2-6-montaggio.md`).  Ciascuna nomina l'anello che la
#    porta, perche' «quale libreria serve a che cosa» e' la domanda che si fa
#    il giorno in cui una manca:
#
#   gio-2.0 >= 2.80           il bus di sessione: il monitor virtuale
#                             (`src/sessione.c`) E la sequenza ScreenCast di
#                             Mutter (`src/mutter.c`).  ⛔ UNA VOLTA SOLA:
#                             serve a due anelli, e due `pkg-config` che la
#                             nominano due volte mettono gli stessi -l due
#                             volte senza che nessuno se ne accorga
#   libpipewire-0.3           il flusso dei fotogrammi  (`src/cattura.c`)
#   libdrm                    i `DRM_FORMAT_MOD_*`: SOLO intestazioni, nessuna
#                             libreria da collegare (`src/cattura.c`)
#   libavcodec >= 61          la codifica HEVC/AV1      (`src/codificatore.c`)
#   libavutil  >= 59          i fotogrammi
#   libswscale >= 8           BGRx (dalla cattura) -> yuv420p10le, BT.709
#                             ⛔ ERA NUOVA: `apt install libswscale-dev`.
#                             `[M]` 12 ago 2026: sul contenitore della macchina
#                             di prova c'era gia' (7:7.1.5-0+deb13u1, stesso
#                             pacchetto sorgente di `libavcodec-dev`)
#
# Su Debian Trixie: `libssl-dev`, `libpam0g-dev`, `libglib2.0-dev`,
# `libpipewire-0.3-dev`, `libdrm-dev`, `libavcodec-dev`, `libavutil-dev`,
# `libswscale-dev`.  ⚠ `ngtcp2` e `nghttp3` NON
# bastano nella versione dei pacchetti (1.11 / 1.8): vanno costruiti dai
# sorgenti, ed e' quel che fa `banchi/01-b2-costruisci-ngtcp2.sh`.
#
# -----------------------------------------------------------------------------
#   make PREFISSO=/percorso/dove/stanno/ngtcp2/e/nghttp3
#
# Se `pkg-config` li trova da se', PREFISSO non serve.

CC      ?= cc
PREFISSO ?=

NOME    := remotix

# ⭐ I QUATTRO FILE DELLA FASE 2 sono in coda, e in ordine di catena: sessione
#    (il palco) → cattura+mutter (i pixel) → codificatore (i byte).  ⚠ Il
#    quinto anello, il canale video, NON compare: vive in `rcp.c`, che c'era
#    gia' — ed e' il motivo per cui nasce gia' confrontato con `banchi/rcp/`.
SORGENTI := main.c trasporto.c webtransport.c pagina.c comando.c certificati.c \
            tls.c registro.c rcp.c autenticazione.c aiutante.c \
            sessione.c cattura.c mutter.c codificatore.c
OGGETTI  := $(SORGENTI:.c=.o)

# -----------------------------------------------------------------------------
# ⛔⭐ LE TRE COPIE CHE DEVONO ESSERE UNA — rilievo R12.3, 10 agosto 2026 notte.
#
# `rcp.c`, `rcp.h` e `autenticazione.c` esistono in DUE cartelle di questo
# repo — qui e in `banchi/rcp/` — perche' sono lo stesso modulo montato su due
# ospiti: il server di prodotto e l'innesto nell'esempio di ngtcp2.  ⛔ Fino a
# stanotte erano identiche **per fortuna, non per costruzione**: nessun file del
# repo confrontava le due copie.
#
# Il caso concreto che nessuno avrebbe visto: si cambia `BAN_DURATA` in
# `src/rcp.c` da dodici ore a una.  Il prodotto banna un'ora; `01-b6-lancia.sh`
# resta verde perche' confronta `banchi/rcp/` con la copia compilata dentro
# `examples/`; B8 resta verde perche' accende `bsslserver`.  ⛔ Il difetto non
# cambia colore a niente.
#
# ⭐ Da cui questo controllo, che sta PRIMA della compilazione e la ferma.
#
# ⛔ E I TRE FATTI SONO TRE, non due — `LEZIONI.md` §1.9 regola 1, la faccia
#    comune di «vuoto» e «proibito»:
#
#      le copie combaciano          si compila
#      le copie DIVERGONO           ⛔ non si compila, e si stampa il `diff`
#      la copia gemella NON C'E'    ⛔ non si compila, salvo che chi costruisce
#                                   NON LO DICHIARI con GEMELLO=nessuno
#
#    ⚠ Il terzo e' quello che un controllo scritto in fretta confonde col
#      primo: «non ho trovato differenze» e «non ho potuto guardare» hanno la
#      stessa faccia, e la seconda con l'aria della prima e' un controllo
#      spento che sembra acceso.
GEMELLO ?= ../banchi/rcp
GEMELLATI := rcp.c rcp.h autenticazione.c

# ⚠ `-std=gnu11` e non `c11`: servono `accept4`, `SOCK_NONBLOCK` e i messaggi
#   ausiliari, che POSIX puro non porta.
AVVERTIMENTI := -Wall -Wextra -Wno-unused-parameter
CFLAGS   ?= -O2 -g -std=gnu11 $(AVVERTIMENTI)

# ⛔ `override`, e non `+=` semplice: chi passa `CFLAGS=` sulla riga di comando
#    — come fa `costruisci.sh`, che ci aggiunge i `-I` — cancellerebbe questa
#    riga insieme al resto, e `struct in6_pktinfo` sparirebbe con un errore che
#    non nomina nessuna opzione.
override CFLAGS += -D_GNU_SOURCE

# ⛔⭐ LE LIBRERIE DELLA FASE 2, CHIESTE A `pkg-config` UNA VOLTA SOLA.
#
# ⚠ `gio-2.0` la vogliono DUE anelli — `sessione.c` (il drop-in dell'unita'
#   della Shell e il bus) e `mutter.c` (la sequenza ScreenCast).  I due rapporti
#   la chiedono ciascuno per se': metterla due volte non e' un errore di
#   compilazione, e' un elenco che non si legge piu'.  ⇒ Qui e' nominata una
#   volta, e le due righe di sotto sono il posto unico in cui guardare.
#
# ⚠ `libdrm` sta solo nei CFLAGS: `cattura.c` ne prende i `DRM_FORMAT_MOD_*`,
#   che sono macro in `drm_fourcc.h`.  ⛔ Metterla anche nei LIBS collegherebbe
#   una libreria di cui non si usa una funzione — e il giorno in cui qualcuno
#   togliesse l'`#include` nessuno se ne accorgerebbe.
#
# ⛔ `override` per la stessa ragione della riga qui sopra: `costruisci.sh`
#    passa `CFLAGS=` sulla riga di comando per aggiungerci i `-I` di ngtcp2, e
#    un `+=` semplice sparirebbe insieme al resto.  Il sintomo sarebbe
#    `gio/gio.h: No such file`, che non nomina nessuna opzione.
F2_CFLAGS := $(shell pkg-config --cflags gio-2.0 libpipewire-0.3 libdrm)
F2_LIBS   := $(shell pkg-config --libs   gio-2.0 libpipewire-0.3)
override CFLAGS += $(F2_CFLAGS)

ifneq ($(PREFISSO),)
CFLAGS  += -I$(PREFISSO)/include
LDFLAGS += -L$(PREFISSO)/lib -Wl,-rpath,$(PREFISSO)/lib
endif

# ⛔ `ngtcp2_crypto_ossl` va PRIMA di `ngtcp2`: il linker risolve i simboli da
#    sinistra a destra, e all'incontrario mancherebbero i simboli del ponte.
# ⚠ `-lswscale` va PRIMA di `-lavutil` per la stessa ragione del ponte di
#   ngtcp2: il linker risolve da sinistra a destra.
LIBS := -lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam \
        -lavcodec -lswscale -lavutil $(F2_LIBS)

.PHONY: tutto pulisci dipendenze impronte

tutto: impronte $(NOME)

# ⛔ Il confronto delle tre copie: vedi il riquadro in cima.  Stampa sempre le
#    impronte di quel che ha confrontato, perche' «confrontato» sia un fatto
#    leggibile e non una riga verde.
impronte:
	@if [ "$(GEMELLO)" = "nessuno" ]; then \
	  printf '  ⛔ GEMELLO=nessuno: NON ho confrontato src/ con banchi/rcp/.\n'; \
	  printf '     Non e «le copie combaciano»: e «non ho guardato», e chi\n'; \
	  printf '     costruisce lo ha DICHIARATO (rilievo R12.3).\n'; \
	  exit 0; \
	fi; \
	if [ ! -d "$(GEMELLO)" ]; then \
	  printf '  ⛔ la copia gemella «%s» NON CE: non posso dimostrare che\n' "$(GEMELLO)"; \
	  printf '     src/rcp.c e banchi/rcp/rcp.c sono lo stesso modulo — e sono\n'; \
	  printf '     lo stesso modulo montato su due ospiti (R12.3).\n'; \
	  printf '     Si passa GEMELLO=<percorso>, oppure GEMELLO=nessuno per\n'; \
	  printf '     DICHIARARE di costruire senza il confronto.\n'; \
	  exit 2; \
	fi; \
	stato=0; \
	for f in $(GEMELLATI); do \
	  if [ ! -f "$(GEMELLO)/$$f" ]; then \
	    printf '  ⛔ %s/%s non esiste\n' "$(GEMELLO)" "$$f"; stato=1; continue; \
	  fi; \
	  if cmp -s "$$f" "$(GEMELLO)/$$f"; then \
	    printf '  OK  %-18s identico a %s  (%s)\n' "$$f" "$(GEMELLO)/$$f" \
	      "$$(md5sum < $$f | cut -c1-32)"; \
	  else \
	    printf '  ⛔ %s DIVERGE da %s/%s:\n' "$$f" "$(GEMELLO)" "$$f"; \
	    diff -u "$(GEMELLO)/$$f" "$$f" | head -40; \
	    stato=1; \
	  fi; \
	done; \
	if [ $$stato -ne 0 ]; then \
	  printf '  ⛔ le due copie dello STESSO modulo non combaciano: non compilo.\n'; \
	  printf '     Se il cambiamento e voluto, va portato in tutte e due — o il\n'; \
	  printf '     prodotto e il banco misureranno due codici diversi (R12.3).\n'; \
	fi; \
	exit $$stato

$(NOME): $(OGGETTI)
	$(CC) $(CFLAGS) -o $@ $(OGGETTI) $(LDFLAGS) $(LIBS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

pulisci:
	rm -f $(OGGETTI) $(NOME)

# ⛔ Il controllo delle dipendenze DICE che cosa manca, invece di far fallire il
#    compilatore su un `#include` che nessuno collega alla libreria assente.
dipendenze:
	@stato=0; \
	for h in ngtcp2/ngtcp2.h ngtcp2/ngtcp2_crypto_ossl.h nghttp3/nghttp3.h \
	         openssl/ssl.h security/pam_appl.h \
	         gio/gio.h pipewire/pipewire.h drm_fourcc.h \
	         libavcodec/avcodec.h libavutil/frame.h libswscale/swscale.h; do \
	  if printf '#include <%s>\nint main(void){return 0;}\n' "$$h" | \
	     $(CC) $(CFLAGS) -x c - -o /dev/null $(LDFLAGS) $(LIBS) 2>/dev/null; then \
	    printf '  OK  %s\n' "$$h"; \
	  else \
	    printf '  NO  %s\n' "$$h"; stato=1; \
	  fi; \
	done; \
	exit $$stato

main.o:           aiutante.h certificati.h comando.h pagina.h rcp.h registro.h \
                  tls.h trasporto.h \
                  sessione.h cattura.h mutter.h codificatore.h
trasporto.o:      trasporto.h aiutante.h registro.h webtransport.h
webtransport.o:   webtransport.h aiutante.h rcp.h registro.h
pagina.o:         pagina.h certificati.h rcp.h registro.h
comando.o:        comando.h rcp.h registro.h
certificati.o:    certificati.h registro.h
tls.o:            tls.h registro.h
registro.o:       registro.h
rcp.o:            rcp.h
# ⚠ `autenticazione.c` non include nessuna intestazione nostra, quindi questa
#   riga non ha prerequisiti — ma c'e', perche' era l'unica delle dieci a
#   mancare e un'omissione uniforme si legge meglio di una sola eccezione.
autenticazione.o:
# ⭐ `aiutante.c` — il processo che interroga PAM al posto del filo unico
#    (`DECISIONI.md` §1.10).  ⚠ NON e' fra i `GEMELLATI`: e' del PRODOTTO e
#    basta, perche' l'innesto di `banchi/rcp/` non ha un ciclo suo da liberare.
aiutante.o:       aiutante.h registro.h

# ⭐ I QUATTRO DELLA FASE 2.  ⚠ NESSUNO e' fra i `GEMELLATI`: sono del PRODOTTO
#    e basta — in `banchi/rcp/` non esistono, perche' l'innesto nell'esempio di
#    ngtcp2 non ha ne' una sessione grafica ne' un codificatore.
sessione.o:       sessione.h registro.h
cattura.o:        cattura.h registro.h
mutter.o:         mutter.h registro.h
codificatore.o:   codificatore.h registro.h
