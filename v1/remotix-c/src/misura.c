#include "misura.h"

#include <gio/gio.h>

#include "registro.h"

/*
 * I limiti, tutti da MS-RDPEDISP tranne l'ultimo (§7.1 di REFERENCE.md).
 *
 * Quelli sui lati li fa gia' rispettare FreeRDP prima di consegnarci il PDU
 * (`disp_server_is_monitor_layout_valid`), ma vanno riapplicati lo stesso: dal
 * Client Core Data non passa nessun controllo, e una regola scritta in un ramo
 * solo e' una regola che il ramo dimenticato non ha.
 */
#define LATO_MINIMO 200
#define LATO_MASSIMO 8192
#define MM_MINIMO 10
#define MM_MASSIMO 10000
#define SCALA_MINIMA 100
#define SCALA_MASSIMA 500

/*
 * L'intervallo di DPI credibili.
 *
 * Gli estremi non sono tondi per caso: 24 DPI e' la dichiarazione di RDM, che
 * va respinta, e 82 quella di mstsc, che va accettata.  Sotto i 30 non c'e'
 * nessuno schermo vero — nemmeno un televisore da 65 pollici a 1080p, che sta
 * sui 34 — e sopra i 600 non c'e' nessun pannello in commercio.
 */
#define DPI_MINIMO 30
#define DPI_MASSIMO 600

static uint32_t dpi_di(uint32_t pixel, uint32_t millimetri)
{
	if (!pixel || !millimetri)
		return 0;
	return (uint32_t) ((pixel * 254.0) / (millimetri * 10.0) + 0.5);
}

/*
 * Larghezza e altezza PARI.
 *
 * Non e' nella specifica: e' che un lato dispari rompe qualunque codificatore
 * 4:2:0, e i client Android mandano misure arbitrarie (§4.1 di
 * client-android.md).  Si arrotonda per DIFETTO — un pixel in meno lascia una
 * striscia non dipinta nella finestra del client, un pixel in piu' chiederebbe
 * a Mutter un desktop che nessuno ha chiesto.
 */
static uint32_t pari(uint32_t v)
{
	return v & ~1u;
}

/*
 * Il filtro comune alle due sorgenti.
 *
 * Le misure fuori intervallo sono un RIFIUTO: si dice di no e si spiega.
 * Millimetri e scala fuori intervallo, invece, si AZZERANO: sono informazione
 * accessoria, e buttare via la sessione perche' un client dichiara uno schermo
 * largo un metro sarebbe sproporzionato — e RDM lo fa.
 */
static gboolean sanifica(Misura *misura, uint32_t larghezza, uint32_t altezza, uint32_t mm_l,
                         uint32_t mm_a, uint32_t scala, uint32_t orientamento, GError **sbaglio)
{
	uint32_t dpi_l, dpi_a;

	if (larghezza < LATO_MINIMO || larghezza > LATO_MASSIMO || altezza < LATO_MINIMO ||
	    altezza > LATO_MASSIMO)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
		            "misura %ux%u fuori dai limiti di MS-RDPEDISP (%d..%d per lato)", larghezza,
		            altezza, LATO_MINIMO, LATO_MASSIMO);
		return FALSE;
	}

	misura->larghezza = pari(larghezza);
	misura->altezza = pari(altezza);
	if (misura->larghezza != larghezza || misura->altezza != altezza)
		diagnostica("misura %ux%u arrotondata a %ux%u: un lato dispari rompe il 4:2:0", larghezza,
		            altezza, misura->larghezza, misura->altezza);

	/* I millimetri passano solo se sono nell'intervallo E se il DPI che ne
	 * risulta ha senso.  Il secondo controllo e' quello che serve davvero. */
	misura->mm_larghezza = misura->mm_altezza = 0;
	if (mm_l >= MM_MINIMO && mm_l <= MM_MASSIMO && mm_a >= MM_MINIMO && mm_a <= MM_MASSIMO)
	{
		dpi_l = dpi_di(misura->larghezza, mm_l);
		dpi_a = dpi_di(misura->altezza, mm_a);
		if (dpi_l >= DPI_MINIMO && dpi_l <= DPI_MASSIMO && dpi_a >= DPI_MINIMO &&
		    dpi_a <= DPI_MASSIMO)
		{
			misura->mm_larghezza = mm_l;
			misura->mm_altezza = mm_a;
		}
		else
		{
			diagnostica("dimensione fisica scartata: %ux%u px su %ux%u mm fanno %u x %u DPI, "
			            "fuori da %d..%d",
			            misura->larghezza, misura->altezza, mm_l, mm_a, dpi_l, dpi_a, DPI_MINIMO,
			            DPI_MASSIMO);
		}
	}
	else if (mm_l || mm_a)
	{
		diagnostica("dimensione fisica scartata: %ux%u mm fuori da %d..%d", mm_l, mm_a, MM_MINIMO,
		            MM_MASSIMO);
	}

	misura->scala = (scala >= SCALA_MINIMA && scala <= SCALA_MASSIMA) ? scala : 0;

	switch (orientamento)
	{
		case ORIENTATION_LANDSCAPE:
		case ORIENTATION_PORTRAIT:
		case ORIENTATION_LANDSCAPE_FLIPPED:
		case ORIENTATION_PORTRAIT_FLIPPED:
			misura->orientamento = orientamento;
			break;
		default:
			misura->orientamento = ORIENTATION_LANDSCAPE;
			break;
	}

	return TRUE;
}

gboolean misura_da_client(const rdpSettings *impostazioni, Misura *fuori, GError **sbaglio)
{
	/*
	 * Il `DeviceScaleFactor` NON si guarda: e' deprecato, esisteva solo in
	 * Windows 8.1, e il riferimento lo annota in tre punti diversi.  Quello che
	 * conta e' il `DesktopScaleFactor`.
	 */
	return sanifica(fuori, freerdp_settings_get_uint32(impostazioni, FreeRDP_DesktopWidth),
	                freerdp_settings_get_uint32(impostazioni, FreeRDP_DesktopHeight),
	                freerdp_settings_get_uint32(impostazioni, FreeRDP_DesktopPhysicalWidth),
	                freerdp_settings_get_uint32(impostazioni, FreeRDP_DesktopPhysicalHeight),
	                freerdp_settings_get_uint32(impostazioni, FreeRDP_DesktopScaleFactor),
	                freerdp_settings_get_uint16(impostazioni, FreeRDP_DesktopOrientation), sbaglio);
}

gboolean misura_da_layout(const DISPLAY_CONTROL_MONITOR_LAYOUT_PDU *pdu, Misura *fuori,
                          GError **sbaglio)
{
	const DISPLAY_CONTROL_MONITOR_LAYOUT *monitor;

	if (pdu->NumMonitors != 1)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
		            "il layout dichiara %u monitor, e REMOTIX ne serve uno solo",
		            pdu->NumMonitors);
		return FALSE;
	}

	monitor = &pdu->Monitors[0];

	/*
	 * Il primario sta a (0,0), sempre.
	 *
	 * Con un monitor solo la regola non lascia scelta: se non e' li', non c'e'
	 * nessun altro che possa esserlo, e il desktop non avrebbe origine.  Il
	 * riferimento arriva alla stessa conclusione per un'altra strada — cerca un
	 * monitor a (0,0) e fallisce se non lo trova.
	 */
	if (monitor->Left != 0 || monitor->Top != 0)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
		            "l'unico monitor e' dichiarato a (%d,%d) invece che a (0,0)", monitor->Left,
		            monitor->Top);
		return FALSE;
	}

	return sanifica(fuori, monitor->Width, monitor->Height, monitor->PhysicalWidth,
	                monitor->PhysicalHeight, monitor->DesktopScaleFactor, monitor->Orientation,
	                sbaglio);
}

gboolean misura_uguale(const Misura *a, const Misura *b)
{
	return a->larghezza == b->larghezza && a->altezza == b->altezza;
}

char *misura_descrivi(const Misura *misura)
{
	GString *testo = g_string_new(NULL);
	const char *verso = misura->orientamento == ORIENTATION_PORTRAIT           ? "verticale"
	                    : misura->orientamento == ORIENTATION_LANDSCAPE_FLIPPED ? "orizzontale capovolto"
	                    : misura->orientamento == ORIENTATION_PORTRAIT_FLIPPED  ? "verticale capovolto"
	                                                                            : "orizzontale";

	g_string_append_printf(testo, "%ux%u", misura->larghezza, misura->altezza);
	if (misura->mm_larghezza)
		g_string_append_printf(testo, ", %ux%u mm (%u DPI)", misura->mm_larghezza,
		                       misura->mm_altezza, dpi_di(misura->larghezza, misura->mm_larghezza));
	else
		g_string_append(testo, ", dimensione fisica non dichiarata");
	if (misura->scala)
		g_string_append_printf(testo, ", scala %u", misura->scala);
	g_string_append_printf(testo, ", %s", verso);

	return g_string_free(testo, FALSE);
}
