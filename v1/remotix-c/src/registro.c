#include "registro.h"

#include <libavutil/log.h>

#include <stdarg.h>
#include <stdio.h>
#include <time.h>
#include <unistd.h>

static LivelloRegistro livello_attivo = REGISTRO_INFORMAZIONE;
static gboolean a_colori = FALSE;

static const struct
{
	const char *nome;
	const char *sigla;
	const char *colore;
} descrizioni[] = {
	[REGISTRO_ERRORE] = { "errore", "ERRORE", "\033[1;31m" },
	[REGISTRO_AVVISO] = { "avviso", "AVVISO", "\033[1;33m" },
	[REGISTRO_INFORMAZIONE] = { "informazione", "INFO  ", "\033[1;34m" },
	[REGISTRO_DIAGNOSTICA] = { "diagnostica", "DIAGN ", "\033[0;36m" },
	[REGISTRO_TRACCIA] = { "traccia", "TRACC ", "\033[0;90m" },
};

const char *registro_nomi_livelli(void)
{
	return "errore, avviso, informazione, diagnostica, traccia";
}

gboolean registro_livello_da_nome(const char *nome, LivelloRegistro *fuori)
{
	if (!nome || !fuori)
		return FALSE;

	for (gsize i = 0; i < G_N_ELEMENTS(descrizioni); i++)
	{
		if (g_ascii_strcasecmp(nome, descrizioni[i].nome) == 0)
		{
			*fuori = (LivelloRegistro) i;
			return TRUE;
		}
	}
	return FALSE;
}

LivelloRegistro registro_livello(void)
{
	return livello_attivo;
}

/*
 * I messaggi di GLib e delle librerie che la usano passano di qui, cosi' non
 * finiscono su un canale diverso da quello del server: due flussi separati
 * renderebbero impossibile leggere l'ordine degli eventi, che e' l'unica cosa
 * che conta quando si insegue un difetto di protocollo.
 */
static void ponte_glib(const gchar *dominio, GLogLevelFlags livello, const gchar *messaggio,
                       gpointer dati)
{
	LivelloRegistro nostro;

	if (livello & (G_LOG_LEVEL_ERROR | G_LOG_LEVEL_CRITICAL))
		nostro = REGISTRO_ERRORE;
	else if (livello & G_LOG_LEVEL_WARNING)
		nostro = REGISTRO_AVVISO;
	else if (livello & G_LOG_LEVEL_MESSAGE)
		nostro = REGISTRO_INFORMAZIONE;
	else if (livello & G_LOG_LEVEL_INFO)
		nostro = REGISTRO_DIAGNOSTICA;
	else
		nostro = REGISTRO_TRACCIA;

	if (dominio)
		registro_scrivi(nostro, "[%s] %s", dominio, messaggio);
	else
		registro_scrivi(nostro, "%s", messaggio);
}

void registro_avvia(LivelloRegistro livello)
{
	livello_attivo = livello;
	a_colori = isatty(STDERR_FILENO);
	g_log_set_default_handler(ponte_glib, NULL);
}

void registro_scrivi(LivelloRegistro livello, const char *formato, ...)
{
	if (livello > livello_attivo)
		return;

	struct timespec adesso;
	clock_gettime(CLOCK_REALTIME, &adesso);
	struct tm parti;
	localtime_r(&adesso.tv_sec, &parti);

	char orario[16];
	strftime(orario, sizeof orario, "%H:%M:%S", &parti);

	va_list argomenti;
	va_start(argomenti, formato);
	char *corpo = g_strdup_vprintf(formato, argomenti);
	va_end(argomenti);

	fprintf(stderr, "%s.%03ld  %s%s%s  %s\n", orario, adesso.tv_nsec / 1000000,
	        a_colori ? descrizioni[livello].colore : "", descrizioni[livello].sigla,
	        a_colori ? "\033[0m" : "", corpo);
	fflush(stderr);
	g_free(corpo);
}

static void da_libav(void *avcl, int livello, const char *formato, va_list argomenti)
{
	char riga[1024];
	int prefisso = 1;

	/* `AV_LOG_INFO` di quelle librerie e' molto piu' loquace del nostro: sotto
	 * l'avviso si tiene a livello diagnostica, cosi' non si perde nulla e non si
	 * riempie il registro di dettagli di codifica. */
	if (livello > av_log_get_level())
		return;

	av_log_format_line(avcl, livello, formato, argomenti, riga, sizeof riga, &prefisso);
	g_strchomp(riga);
	if (riga[0] == '\0')
		return;

	if (livello <= AV_LOG_ERROR)
		errore("libav: %s", riga);
	else if (livello <= AV_LOG_WARNING)
		avviso("libav: %s", riga);
	else
		diagnostica("libav: %s", riga);
}

void registro_aggancia_libav(void)
{
	av_log_set_level(AV_LOG_VERBOSE);
	av_log_set_callback(da_libav);
}
