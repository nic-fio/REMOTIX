/*
 * misura — la configurazione monitor che il client chiede, validata.
 *
 * Le tre sorgenti da cui puo' arrivare sono diverse nella forma e IDENTICHE
 * nelle regole (§12.1 di gnome-remote-desktop.md): Client Core Data, Client
 * Monitor Data e MS-RDPEDISP.  REMOTIX ne usa due — il Core Data alla
 * connessione e il DISP a caldo — e le fa passare per lo stesso filtro, perche'
 * una misura che il filtro respinge da un lato e accetta dall'altro e' un
 * difetto che si presenta solo ridimensionando, cioe' tardi.
 *
 * # Un monitor solo
 *
 * §3.1 di SPECIFICA.md mette il multi-monitor fuori scope.  Non e' una
 * limitazione da nascondere: si DICHIARA al client, con `MaxNumMonitors = 1`
 * nelle capacita' MS-RDPEDISP, cosi' un client corretto non ne chiede due.  Se
 * li chiede lo stesso, il rifiuto avviene prima di arrivare qui — FreeRDP
 * scarta il PDU quando `NumMonitors > MaxNumMonitors`.
 *
 * # ⛔ La dimensione fisica si giudica sul DPI, non sui millimetri
 *
 * E' l'unico punto in cui REMOTIX e' piu' severo del riferimento, e la ragione
 * e' misurata (§7.1 di REFERENCE.md, 3 agosto 2026):
 *
 *     mstsc   1080 px su  334 mm →  82 DPI   plausibile, usabile
 *     RDM      984 px su 1000 mm →  24 DPI   assurda, da scartare
 *
 * I 1000 mm di RDM passano indenni il filtro 10–10000 mm del riferimento.  Un
 * controllo sui soli millimetri, quindi, non filtra niente: il numero che dice
 * se la dichiarazione ha senso e' il rapporto fra i due.
 */
#pragma once

#include <freerdp/channels/disp.h>
#include <freerdp/freerdp.h>
#include <glib.h>
#include <stdint.h>

typedef struct
{
	uint32_t larghezza, altezza;
	/* Millimetri: zero significa «non dichiarata, o non credibile». */
	uint32_t mm_larghezza, mm_altezza;
	/* Fattore di scala in centesimi (100 = 1:1); zero = non dichiarato. */
	uint32_t scala;
	/* 0, 90, 180 o 270.  Non si applica: il client manda gia' la misura
	 * ruotata, e questo campo serve solo a poterlo dire nel registro. */
	uint32_t orientamento;
} Misura;

/*
 * Dal Client Core Data, cioe' dalla misura dichiarata alla connessione.
 * E' la misura con cui si monta il palco prima ancora che EGFX sia negoziato.
 */
gboolean misura_da_client(const rdpSettings *impostazioni, Misura *fuori, GError **sbaglio);

/* Da un DISPLAYCONTROL_MONITOR_LAYOUT arrivato sul canale MS-RDPEDISP. */
gboolean misura_da_layout(const DISPLAY_CONTROL_MONITOR_LAYOUT_PDU *pdu, Misura *fuori,
                          GError **sbaglio);

/*
 * Due misure sono «uguali» quando lo sono LARGHEZZA E ALTEZZA, e nient'altro.
 *
 * Solo quelle due costano un rimontaggio.  Un cambio di millimetri o di scala
 * non muove un pixel, e trattarlo come un ridimensionamento significherebbe
 * rifare la tela — con il riavvio del decodificatore che questo comporta su
 * Android — per nulla.
 */
gboolean misura_uguale(const Misura *a, const Misura *b);

/* Per il registro: «1282x802, 334 mm (82 DPI), scala 100, orizzontale». */
char *misura_descrivi(const Misura *misura);
