/*
 * REMOTIX — server RDP per Linux.
 *
 * Questo file resta cio' che era nella fase 1: opzioni, registro, segnali e
 * uscita pulita.  Il protocollo sta in `server.c`, la cattura del desktop in
 * `palco.c` e nei due moduli che ne dipendono, `mutter.c` e `cattura.c`.
 *
 * ⛔ Prima di toccare qualunque cosa che riguardi il protocollo, si legge
 *    REFERENCE.md — e' regola vincolante (§7.0 di SPECIFICA.md).  Le
 *    incompatibilita' raccolte li' non si manifestano come errori: si
 *    manifestano come schermo nero su un client su tre.
 */
#include <freerdp/freerdp.h>
#include <glib.h>
#include <glib-unix.h>
#include <execinfo.h>
#include <signal.h>
#include <string.h>
#include <stdlib.h>
#include <sys/types.h>

#include <freerdp/error.h>

#include "autenticazione.h"
#include "compositore.h"
#include "kwin.h"
#include "palco.h"
#include "registro.h"
#include "sentinella.h"
#include "sessione.h"
#include "server.h"
#include "uscita.h"

typedef struct
{
	GMainLoop *ciclo;
	Server *server;
	Sentinella *sentinella;
	Uscita *uscita;
	int codice_uscita;
} Remotix;

/* ------------------------------------------------------------------ *
 * Le due reazioni della fase 5
 * ------------------------------------------------------------------ */
static void sgombera(Remotix *remotix, gboolean da_chiudere);

/*
 * L'utente e' uscito dalla sessione.
 *
 * Gira sul thread di `uscita`, subito dopo che il riscontro a gnome-session e'
 * partito, e non fa altro che segnare e svegliare: il client deve cadere adesso,
 * non fra cinque secondi, e con il motivo scritto in chiaro.
 *
 * `ERRINFO_LOGOFF_BY_USER` dice esattamente cosa e' successo, ed e' il congedo
 * che fino al passaggio a FreeRDP era a debito: chi riceve solo una chiusura di
 * socket resta a fissare l'ultimo fotogramma — che dopo un logout e' uno sfondo
 * pulito, cioe' visivamente identico a un desktop vivo.
 */
static void su_uscita_sessione(gpointer dati)
{
	Remotix *remotix = dati;

	server_congeda_tutti(remotix->server, ERRINFO_LOGOFF_BY_USER,
	                     "l'utente e' uscito dalla sessione");

	/* La sessione se n'e' andata da sola: resta da smontare il palco, e lo fa
	 * un thread a parte perche' qui non si deve aspettare nulla. */
	sgombera(remotix, FALSE);
}

/*
 * Sgombera: chiude la sessione grafica remota quando ne compare una locale.
 *
 * Gira su un thread suo perche' aspetta secondi — `Logout(1)` e poi, se serve,
 * `Logout(2)` — e chi la chiama e' la sentinella, che nel frattempo deve
 * continuare a ripassare.
 *
 * ⛔ Non basta staccare il client.  Se il compositore remoto restasse in piedi,
 *    chi si siede davanti alla macchina avrebbe due sessioni grafiche a proprio
 *    nome sullo stesso `$XDG_RUNTIME_DIR`, e la seconda troverebbe il nome
 *    D-Bus `org.gnome.Shell` gia' occupato: il difetto si vedrebbe sulla
 *    sessione LOCALE che non parte, cioe' dove nessuno lo cerca.
 */
typedef struct
{
	Remotix *remotix;
	/* Vero quando la sessione va CHIUSA da noi (comparsa di una locale); falso
	 * quando se n'e' gia' andata da sola (l'utente e' uscito). */
	gboolean da_chiudere;
} Sgombero;

static gpointer thread_sgombera(gpointer dati)
{
	Sgombero *sgombero = dati;
	g_autoptr(GError) sbaglio = NULL;

	if (sgombero->da_chiudere &&
	    !sessione_termina(server_compositore(sgombero->remotix->server), &sbaglio) && sbaglio)
		avviso("sessione grafica remota non chiusa: %s", sbaglio->message);

	/* In entrambi i casi il palco va giu': gli oggetti che lo compongono
	 * appartengono a un compositore che non c'e' piu'. */
	server_smonta_palco(sgombero->remotix->server);
	g_free(sgombero);
	return NULL;
}

static void sgombera(Remotix *remotix, gboolean da_chiudere)
{
	Sgombero *sgombero = g_new0(Sgombero, 1);
	GThread *thread;

	sgombero->remotix = remotix;
	sgombero->da_chiudere = da_chiudere;
	thread = g_thread_new("remotix-sgombera", thread_sgombera, sgombero);
	g_thread_unref(thread);
}

static void su_sessione_locale(gboolean presente, const char *descrizione, gpointer dati)
{
	Remotix *remotix = dati;

	if (!presente)
		return;

	/* Prima il client — subito, e dichiarando perche' — poi la sessione. */
	server_congeda_tutti(remotix->server, ERRINFO_DISCONNECTED_BY_OTHER_CONNECTION,
	                     "la sessione locale ha la precedenza");
	sgombera(remotix, TRUE);
}

static gint porta = 3389;
static gchar *indirizzo = NULL;
static gchar *nome_livello = NULL;
static gchar *certificato = NULL;
static gchar *chiave = NULL;
static gint bitrate = 10000;
/*
 * ⛔ SESSANTA, NON TRENTA, E IL PERCHE' STA IN R32 DI REFERENCE.md.
 *
 *    Questo numero e' il massimo che si dichiara a PipeWire, e Mutter ne
 *    consegna circa sei decimi: dichiarandone 30 ne arrivavano 18 — i famosi
 *    diciotto fotogrammi al secondo, che per due mesi sono stati cercati nel
 *    codificatore, nel protocollo e nella rete, ed erano scritti qui.
 *
 *    Misurato il 7 agosto 2026, sulla catena intera e fino al client: da 18,7 a
 *    32,4 fotogrammi al secondo a 1080p, cioe' il MINIMO di §3.1 di
 *    SPECIFICA.md superato.  Verificato dall'utente su tutti e tre i client —
 *    xfreerdp3, mstsc (AVC420 in GPU, 29-33) e RDM (RemoteFX Progressive, 23-29).
 *
 *    Oltre i 60 non si guadagna niente: dichiarandone 120 Mutter ne consegna
 *    sempre 37.
 *
 * ⚠ E STA QUI, NON IN /etc/default/remotix.  Quel file vive in RAM e si perde a
 *   ogni riavvio: il 7 agosto la riga che teneva spenta la copia zero e' sparita
 *   cosi', e l'utente si e' ritrovato in faccia un difetto noto.  Un valore da
 *   cui dipende quel che si vede non si affida a una riga che si puo' perdere.
 */
static gint fotogrammi = 60;
static gboolean senza_autenticazione = FALSE;
static gboolean immagine_di_prova = FALSE;
static gboolean fingi_riscontri_sospesi = FALSE;
static gchar *comando_sessione = NULL;
static gchar *codificatore = NULL;
static gchar *nome_compositore = NULL;
static gboolean installa_desktop = FALSE;
static gboolean mostra_versione = FALSE;

static GOptionEntry opzioni[] = {
	{ "porta", 'p', 0, G_OPTION_ARG_INT, &porta, "Porta su cui ascoltare (predefinita: 3389)",
	  "NUMERO" },
	{ "indirizzo", 'a', 0, G_OPTION_ARG_STRING, &indirizzo,
	  "Indirizzo su cui ascoltare (predefinito: tutti)", "IND" },
	{ "registro", 'r', 0, G_OPTION_ARG_STRING, &nome_livello, "Livello del registro", "LIVELLO" },
	{ "certificato", 0, 0, G_OPTION_ARG_FILENAME, &certificato,
	  "Certificato TLS in PEM (se manca, se ne genera uno)", "FILE" },
	{ "chiave", 0, 0, G_OPTION_ARG_FILENAME, &chiave, "Chiave privata TLS in PEM", "FILE" },
	{ "bitrate", 0, 0, G_OPTION_ARG_INT, &bitrate, "Bitrate video in kbit/s (predefinito: 10000)",
	  "KBIT" },
	{ "fotogrammi", 0, 0, G_OPTION_ARG_INT, &fotogrammi,
	  "Fotogrammi al secondo (predefinito: 30)", "N" },
	{ "senza-autenticazione", 0, 0, G_OPTION_ARG_NONE, &senza_autenticazione,
	  "NON autentica nessuno: solo per il banco di prova", NULL },
	{ "immagine-di-prova", 0, 0, G_OPTION_ARG_NONE, &immagine_di_prova,
	  "Manda la scena sintetica invece del desktop: isola il protocollo dalla cattura", NULL },
	{ "fingi-riscontri-sospesi", 0, 0, G_OPTION_ARG_NONE, &fingi_riscontri_sospesi,
	  "Fa come se il client smettesse di riscontrare i fotogrammi: solo per il banco", NULL },
	{ "sessione", 0, 0, G_OPTION_ARG_STRING, &comando_sessione,
	  "Comando con cui avviare la sessione grafica se manca", "COMANDO" },
	/* Il codificatore si sceglie PER NOME, a runtime (§3.1 di SPECIFICA.md).
	 * Indicandone uno non si ripiega su un altro: chi lo indica sta misurando,
	 * e un ripiego silenzioso darebbe due misure sotto la stessa etichetta. */
	{ "codificatore", 0, 0, G_OPTION_ARG_STRING, &codificatore,
	  "Chi codifica l'AVC420: auto (predefinito), h264_vaapi, h264_qsv, "
	  "h264_nvenc, libx264, freerdp",
	  "NOME" },
	/* Il compositore si RICONOSCE all'avvio (§2 di SPECIFICA.md); questo lo
	 * forza, e serve dove i due convivono sulla stessa macchina — cioe' sul
	 * banco. */
	{ "compositore", 0, 0, G_OPTION_ARG_STRING, &nome_compositore,
	  "Chi possiede schermo e input: auto (predefinito), mutter, kwin", "NOME" },
	/*
	 * ⛔ Su KDE la cattura e' dietro un permesso, e il permesso e' un file.
	 *
	 *    `zkde_screencast_unstable_v1` non viene nemmeno ANNUNCIATO a un client
	 *    che non lo dichiari in un `.desktop` installato: il sintomo e' «questo
	 *    compositore non ha il protocollo», che e' la diagnosi sbagliata.  Questa
	 *    opzione scrive il file con `Exec=` puntato al binario vero — che e'
	 *    quel che fanno KRdp, krfb e il portale di KDE (`kde.md` §3.2).
	 *
	 *    Si esegue una volta, a mano, e appartiene al confezionamento: sta qui
	 *    perche' fino alla fase 12 un confezionamento non c'e'.
	 */
	{ "installa-desktop", 0, 0, G_OPTION_ARG_NONE, &installa_desktop,
	  "Scrive il file .desktop che apre il permesso della cattura su KDE, ed esce", NULL },
	{ "versione", 'V', 0, G_OPTION_ARG_NONE, &mostra_versione, "Mostra la versione ed esce", NULL },
	/* Le opzioni del progetto sono in italiano come tutto il resto, ma
	 * «--version» e' quello che chiunque prova per primo, e PIANO.md lo indica
	 * come la prova visibile della fase 1: si accetta anche quello. */
	{ "version", 0, G_OPTION_FLAG_HIDDEN, G_OPTION_ARG_NONE, &mostra_versione, NULL, NULL },
	{ NULL, 0, 0, 0, NULL, NULL, NULL },
};

static void stampa_versione(void)
{
	g_print("REMOTIX %s\n", PACCHETTO_VERSIONE);
	g_print("  FreeRDP   %s (%s)\n", freerdp_get_version_string(), freerdp_get_build_revision());
	g_print("  GLib      %u.%u.%u\n", glib_major_version, glib_minor_version, glib_micro_version);
}

/*
 * I due segnali di arresto.
 *
 * g_unix_signal_add non esegue nulla dentro il gestore di segnale vero: mette
 * in coda una sorgente sul ciclo principale, che viene servita fra un giro e
 * l'altro.  Serve perche' qui dentro, piu' avanti, ci sara' da smontare
 * sessioni e rilasciare tasti rimasti premuti (R6 di REFERENCE.md §6.1): cose
 * che in un gestore di segnale asincrono non si possono fare.
 */
/*
 * Si dichiara QUALE segnale e' arrivato, e non e' pignoleria: quando il server
 * muore senza che nessuno glielo abbia chiesto, la prima domanda e' «chi lo ha
 * ucciso», e un registro che dice soltanto «arresto richiesto» non risponde.
 * Costato una diagnosi il 4 agosto.
 */
static gboolean su_segnale_arresto(Remotix *remotix, const char *nome)
{
	informazione("arrivato %s: chiudo", nome);
	g_main_loop_quit(remotix->ciclo);
	return G_SOURCE_REMOVE;
}

static gboolean su_sigint(gpointer dati)
{
	return su_segnale_arresto(dati, "SIGINT");
}

/*
 * SIGUSR1 — arma la spia dei fotogrammi.
 *
 * Il difetto da fotografare non ha un istante prevedibile: lo si provoca a
 * mano, e quando lo si vede e' gia' passato.  L'armamento sul
 * ridimensionamento (fase 6) copriva l'unico istante che si sapeva predire;
 * questo copre tutti gli altri, e non richiede di indovinare il momento —
 * basta mandare il segnale mentre il difetto e' in corso.
 *
 * Quanti fotogrammi: due secondi a trenta al secondo.
 */
#define FOTO_SU_COMANDO 60

static gboolean su_sigusr1(gpointer dati)
{
	(void) dati;
	palco_spia_arma(FOTO_SU_COMANDO);
	return G_SOURCE_CONTINUE; /* la spia si riarma quante volte serve */
}

/*
 * Chi manda il SIGTERM.
 *
 * Dedurlo dal contesto non ha funzionato: il registro di sistema dice che il
 * servizio si e' «disattivato con successo» senza che nessuno lo abbia
 * fermato, dunque il colpo arriva da fuori systemd e il mittente non ha nome.
 * L'unico modo per dargliene uno e' chiederlo al nucleo: `siginfo_t.si_pid`
 * porta il pid di chi ha chiamato kill(), e `si_uid` il suo utente.
 *
 * g_unix_signal_add pero' installa un gestore proprio, senza SA_SIGINFO, che
 * quel dato lo butta.  Non lo si puo' sostituire — senza di lui il ciclo
 * principale non si accorgerebbe piu' del segnale — quindi lo si incatena: si
 * legge il gestore che glib ha appena messo, si mette il nostro davanti, e il
 * nostro finisce richiamandolo.  L'unica cosa che facciamo dentro il gestore
 * vero e' scrivere due interi: tutto il resto e' rimandato al ciclo.
 */
static volatile sig_atomic_t mittente_pid = -1;
static volatile sig_atomic_t mittente_uid = -1;
static volatile sig_atomic_t mittente_codice = -1;
static void (*gestore_glib_sigterm)(int) = NULL;

/* La pila di chiamate al momento del colpo.  `backtrace` scrive soltanto in
 * memoria gia' nostra: la traduzione in nomi, che alloca, si fa dopo, nel
 * ciclo principale.  Serve perche' il mittente e' il processo stesso, e allora
 * la domanda non e' piu' «chi», ma «da quale riga». */
static void *pila[32];
static volatile sig_atomic_t pila_quante = 0;

static void spia_sigterm(int segnale, siginfo_t *chi, void *ignoto)
{
	(void) ignoto;

	if (chi)
	{
		mittente_pid = chi->si_pid;
		mittente_uid = chi->si_uid;
		mittente_codice = chi->si_code;
	}
	pila_quante = backtrace(pila, (int) G_N_ELEMENTS(pila));

	if (gestore_glib_sigterm)
		gestore_glib_sigterm(segnale);
}

static void spia_sigterm_installa(void)
{
	struct sigaction vecchio;
	struct sigaction nuovo;

	memset(&vecchio, 0, sizeof vecchio);
	memset(&nuovo, 0, sizeof nuovo);

	/* Va chiamata DOPO g_unix_signal_add(SIGTERM, ...): e' il suo gestore che
	 * andiamo a prendere.  Se glib avesse gia' usato SA_SIGINFO — non lo fa,
	 * ma un giorno potrebbe — ci si tira indietro invece di rompere. */
	if (sigaction(SIGTERM, NULL, &vecchio) != 0)
		return;
	if (vecchio.sa_flags & SA_SIGINFO)
		return;

	gestore_glib_sigterm = vecchio.sa_handler;

	nuovo.sa_sigaction = spia_sigterm;
	nuovo.sa_mask = vecchio.sa_mask;
	nuovo.sa_flags = (vecchio.sa_flags & ~(int) SA_RESETHAND) | SA_SIGINFO;
	sigaction(SIGTERM, &nuovo, NULL);
}

/* Il nome del processo, se e' ancora vivo abbastanza da avercelo. */
static char *chi_e(pid_t pid)
{
	g_autofree char *strada = g_strdup_printf("/proc/%d/comm", (int) pid);
	g_autofree char *nome = NULL;

	if (!g_file_get_contents(strada, &nome, NULL, NULL))
		return g_strdup("gia' sparito");
	return g_strstrip(g_steal_pointer(&nome));
}

static gboolean su_sigterm(gpointer dati)
{
	pid_t pid = (pid_t) mittente_pid;

	if (pid > 0)
	{
		g_autofree char *nome = chi_e(pid);
		const char *come = (mittente_codice == SI_USER)  ? "kill() da un altro processo"
		                 : (mittente_codice == SI_TKILL) ? "raise()/pthread_kill() da dentro"
		                 : (mittente_codice == SI_QUEUE) ? "sigqueue()"
		                                                 : "origine non classificata";

		informazione("SIGTERM mandato da pid %d (%s), uid %d — si_code %d: %s",
		             (int) pid, nome, (int) mittente_uid, (int) mittente_codice, come);
	}
	else if (pid == 0)
		informazione("SIGTERM arrivato dal nucleo, non da un processo");
	else
		avviso("SIGTERM: il mittente non e' stato registrato");

	if (pila_quante > 0)
	{
		char **righe = backtrace_symbols(pila, (int) pila_quante);

		if (righe)
		{
			for (int i = 0; i < (int) pila_quante; i++)
				informazione("  pila #%d  %s", i, righe[i]);
			free(righe);
		}
	}

	return su_segnale_arresto(dati, "SIGTERM");
}

static gboolean su_sighup(gpointer dati)
{
	/* SIGHUP arriva quando muore il terminale che ci ha avviati.  Non e' un
	 * motivo per chiudere: REMOTIX deve sopravvivere alla shell che lo ha
	 * lanciato, e dalla fase 11 sara' un servizio di sistema. */
	avviso("arrivato SIGHUP: lo ignoro, il server resta in ascolto");
	return G_SOURCE_CONTINUE;
}

int main(int argc, char **argv)
{
	Remotix remotix = { .codice_uscita = EXIT_SUCCESS };
	LivelloRegistro livello = REGISTRO_INFORMAZIONE;
	TipoCompositore compositore = COMPOSITORE_AUTO;
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GOptionContext) contesto = NULL;

	contesto = g_option_context_new("- server RDP per Linux");
	g_option_context_add_main_entries(contesto, opzioni, NULL);
	{
		g_autofree char *coda =
		    g_strdup_printf("Livelli del registro: %s.", registro_nomi_livelli());
		g_option_context_set_description(contesto, coda);
	}

	if (!g_option_context_parse(contesto, &argc, &argv, &sbaglio))
	{
		g_printerr("%s\n", sbaglio->message);
		return EXIT_FAILURE;
	}

	if (mostra_versione)
	{
		stampa_versione();
		return EXIT_SUCCESS;
	}

	/* Il livello si accetta anche dall'ambiente, che e' comodo quando il server
	 * lo avvia un'unita' systemd e la riga di comando non si tocca. */
	const char *dall_ambiente = g_getenv("REMOTIX_REGISTRO");
	const char *scelto = nome_livello ? nome_livello : dall_ambiente;
	if (scelto && !registro_livello_da_nome(scelto, &livello))
	{
		g_printerr("livello di registro sconosciuto: «%s»\nQuelli accettati sono: %s.\n", scelto,
		           registro_nomi_livelli());
		return EXIT_FAILURE;
	}

	registro_avvia(livello);
	/* Da qui in poi anche libavcodec parla nel nostro registro: i suoi rifiuti
	 * li spiega a voce, e senza questo al chiamante arriva solo un numero. */
	registro_aggancia_libav();

	if (installa_desktop)
	{
		if (!kwin_installa_desktop(&sbaglio))
		{
			errore("%s", sbaglio->message);
			return EXIT_FAILURE;
		}
		return EXIT_SUCCESS;
	}

	if (nome_compositore && !compositore_tipo_da_nome(nome_compositore, &compositore))
	{
		g_printerr("compositore sconosciuto: «%s»\nQuelli accettati sono: auto, mutter, kwin.\n",
		           nome_compositore);
		return EXIT_FAILURE;
	}

	if (porta < 1 || porta > 65535)
	{
		errore("porta fuori intervallo: %d", porta);
		return EXIT_FAILURE;
	}

	informazione("REMOTIX %s — FreeRDP %s", PACCHETTO_VERSIONE, freerdp_get_version_string());
	diagnostica("livello del registro: %s", scelto ? scelto : "informazione");

	/* §3.4 — un server che non sa di chi sia la sessione che serve non deve
	 * aprire la porta.  Si dichiara all'avvio, perche' su ogni rifiuto si
	 * scriveranno tutti e due i nomi. */
	if (!senza_autenticazione)
	{
		const char *atteso = autenticazione_utente_atteso();
		if (!atteso)
		{
			errore("non riesco a stabilire di quale utente e' la sessione: non parto");
			return EXIT_FAILURE;
		}
		informazione("servo la sessione di «%s»", atteso);
	}

	{
		g_autofree char *cert_predefinito = NULL;
		g_autofree char *chiave_predefinita = NULL;
		OpzioniServer impostazioni = { 0 };

		if (!certificato || !chiave)
		{
			g_autofree char *cartella =
			    g_build_filename(g_get_user_data_dir(), "remotix", NULL);
			g_mkdir_with_parents(cartella, 0700);
			cert_predefinito = g_build_filename(cartella, "certificato.pem", NULL);
			chiave_predefinita = g_build_filename(cartella, "chiave.pem", NULL);
		}

		impostazioni.porta = (uint16_t) porta;
		impostazioni.indirizzo = indirizzo;
		impostazioni.certificato = certificato ?: cert_predefinito;
		impostazioni.chiave = chiave ?: chiave_predefinita;
		impostazioni.bitrate_kbit = (uint32_t) MAX(100, bitrate);
		impostazioni.fotogrammi_al_secondo = (uint32_t) CLAMP(fotogrammi, 1, 120);
		impostazioni.senza_autenticazione = senza_autenticazione;
		impostazioni.immagine_di_prova = immagine_di_prova;
		impostazioni.fingi_riscontri_sospesi = fingi_riscontri_sospesi;
		impostazioni.comando_sessione = comando_sessione;
		impostazioni.codificatore = codificatore;
		impostazioni.compositore = compositore;

		remotix.server = server_nuovo(&impostazioni, &sbaglio);
		if (!remotix.server)
		{
			errore("%s", sbaglio->message);
			return EXIT_FAILURE;
		}
		if (!server_avvia(remotix.server, &sbaglio))
		{
			errore("%s", sbaglio->message);
			server_libera(remotix.server);
			return EXIT_FAILURE;
		}
	}

	remotix.ciclo = g_main_loop_new(NULL, FALSE);
	g_unix_signal_add(SIGINT, su_sigint, &remotix);
	g_unix_signal_add(SIGTERM, su_sigterm, &remotix);
	g_unix_signal_add(SIGHUP, su_sighup, &remotix);
	g_unix_signal_add(SIGUSR1, su_sigusr1, &remotix);
	spia_sigterm_installa();   /* dopo glib: gli si incatena dietro */

	/*
	 * Le due sorveglianze partono DOPO il server, perche' entrambe possono
	 * reagire subito e hanno bisogno di trovarlo pronto.  La sentinella fa il
	 * suo primo controllo prima di tornare: se una sessione grafica locale c'e'
	 * gia', non deve esistere una finestra iniziale in cui si entra lo stesso.
	 */
	if (!immagine_di_prova)
	{
		remotix.sentinella = sentinella_avvia(su_sessione_locale, &remotix);
		server_sentinella(remotix.server, remotix.sentinella);
		remotix.uscita = uscita_avvia(su_uscita_sessione, &remotix,
		                              server_compositore(remotix.server));
	}

	g_main_loop_run(remotix.ciclo);

	/* Si spengono le sorveglianze PRIMA del server: reagiscono chiamandolo, e
	 * una reazione che arrivasse a server gia' liberato userebbe memoria
	 * liberata. */
	uscita_ferma(remotix.uscita);
	sentinella_ferma(remotix.sentinella);
	server_libera(remotix.server);

	/* L'uscita e' esplicita e ordinata: e' l'abitudine che in fase 5 diventera'
	 * lo smontaggio del palco e il congedo dichiarato al client (R12). */
	g_main_loop_unref(remotix.ciclo);
	g_free(indirizzo);
	g_free(certificato);
	g_free(chiave);
	g_free(nome_livello);
	g_free(comando_sessione);
	g_free(nome_compositore);
	informazione("chiuso");
	return remotix.codice_uscita;
}
