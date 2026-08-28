/*
 * nodo-kwin — chiede a KWin un flusso di cattura e stampa il nodo PipeWire.
 *
 * E' l'equivalente, per KWin, della sequenza D-Bus di Mutter: si parla
 * DIRETTAMENTE al compositore, senza passare dal portale — che e' quel che §2 di
 * SPECIFICA.md pretende («parlare direttamente ai compositor, anziche' passare
 * per i portali, quando questo evita richieste di autorizzazione a video»).
 *
 * KWin lo espone come protocollo Wayland invece che su D-Bus:
 * `zkde_screencast_unstable_v1`, che vive in `plasma-wayland-protocols`.  E'
 * dichiarato «dettaglio implementativo dell'ambiente desktop, i client normali
 * non lo usino» — vero, e per la fase 11 e' esattamente la strada da prendere:
 * un server di desktop remoto non e' un client normale.
 *
 * Due modi, come da riga di comando:
 *   (nessuno)          cattura la PRIMA uscita esistente (`stream_output`)
 *   --virtuale W H     se ne fa creare una nuova della misura chiesta
 *                      (`stream_virtual_output`) — l'analogo di `RecordVirtual`
 *
 * Il flusso vive quanto questo processo: stampa il nodo e poi resta li'.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wayland-client.h>

#include "zkde-screencast-unstable-v1-client-protocol.h"

#define PUNTATORE_METADATO 4

static struct zkde_screencast_unstable_v1 *screencast;
static struct wl_output *uscita;
static uint32_t versione_screencast;
static int finito;

static int elenca;

static void su_globale(void *dati, struct wl_registry *registro, uint32_t nome,
                       const char *interfaccia, uint32_t versione)
{
	if (elenca)
		fprintf(stderr, "  %s v%u\n", interfaccia, versione);
	if (!strcmp(interfaccia, zkde_screencast_unstable_v1_interface.name))
	{
		versione_screencast = versione < 5 ? versione : 5;
		screencast = wl_registry_bind(registro, nome, &zkde_screencast_unstable_v1_interface,
		                              versione_screencast);
	}
	else if (!strcmp(interfaccia, wl_output_interface.name) && !uscita)
	{
		uscita = wl_registry_bind(registro, nome, &wl_output_interface, 1);
	}
}

static void su_globale_via(void *dati, struct wl_registry *registro, uint32_t nome)
{
}

static const struct wl_registry_listener ascolto_registro = { su_globale, su_globale_via };

static void su_chiuso(void *dati, struct zkde_screencast_stream_unstable_v1 *flusso)
{
	fprintf(stderr, "KWin ha chiuso il flusso\n");
	finito = 1;
}

static void su_creato(void *dati, struct zkde_screencast_stream_unstable_v1 *flusso, uint32_t nodo)
{
	printf("%u\n", nodo);
	fflush(stdout);
	fprintf(stderr, "  KWin: nodo PipeWire %u\n", nodo);
}

static void su_guasto(void *dati, struct zkde_screencast_stream_unstable_v1 *flusso,
                      const char *errore)
{
	fprintf(stderr, "KWin ha rifiutato: %s\n", errore);
	finito = 1;
}

static const struct zkde_screencast_stream_unstable_v1_listener ascolto_flusso = {
	su_chiuso, su_creato, su_guasto
};

int main(int argc, char **argv)
{
	struct wl_display *display;
	struct wl_registry *registro;
	struct zkde_screencast_stream_unstable_v1 *flusso;
	int virtuale = 0, larghezza = 0, altezza = 0;

	if (argc >= 2 && !strcmp(argv[1], "--elenca"))
		elenca = 1;
	if (argc >= 4 && !strcmp(argv[1], "--virtuale"))
	{
		virtuale = 1;
		larghezza = atoi(argv[2]);
		altezza = atoi(argv[3]);
	}

	display = wl_display_connect(NULL);
	if (!display)
	{
		fprintf(stderr, "nessun display Wayland (WAYLAND_DISPLAY e' impostata?)\n");
		return 1;
	}
	registro = wl_display_get_registry(display);
	wl_registry_add_listener(registro, &ascolto_registro, NULL);
	wl_display_roundtrip(display);
	wl_display_roundtrip(display); /* il secondo giro serve agli eventi delle uscite */

	if (elenca)
		return 0;
	if (!screencast)
	{
		fprintf(stderr, "questo compositore non espone zkde_screencast_unstable_v1\n");
		return 1;
	}
	fprintf(stderr, "  zkde_screencast_unstable_v1 versione %u\n", versione_screencast);

	if (virtuale)
	{
		if (versione_screencast < 2)
		{
			fprintf(stderr, "la versione %u non ha stream_virtual_output\n", versione_screencast);
			return 1;
		}
		flusso = zkde_screencast_unstable_v1_stream_virtual_output(
		    screencast, "remotix-banco", larghezza, altezza, wl_fixed_from_int(1),
		    PUNTATORE_METADATO);
	}
	else
	{
		if (!uscita)
		{
			fprintf(stderr, "nessuna uscita da catturare\n");
			return 1;
		}
		flusso = zkde_screencast_unstable_v1_stream_output(screencast, uscita, PUNTATORE_METADATO);
	}
	zkde_screencast_stream_unstable_v1_add_listener(flusso, &ascolto_flusso, NULL);
	wl_display_roundtrip(display);

	while (!finito && wl_display_dispatch(display) != -1)
		;
	return finito ? 1 : 0;
}
