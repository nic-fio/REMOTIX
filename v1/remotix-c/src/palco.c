#include "palco.h"

#include "superficie.h"

#include <gio/gio.h>
#include <libavutil/hwcontext.h>
#include <stdlib.h>
#include <string.h>

#include "cattura.h"
#include "compositore.h"
#include "energia.h"
#include "registro.h"
#include "sessione.h"
#include "suono.h"

/* Quanto silenzio basta per dire che il desktop ha finito di ridisegnarsi. */
#define QUIETE_RIDISEGNO_MS 300
/* Quanti fotogrammi servono prima di fidarsi del silenzio (R10). */
#define FOTOGRAMMI_PRIMA_DI_FIDARSI 2
/* E quanto si e' disposti ad aspettare in tutto, perche' un desktop che cambia
 * di continuo non tenga fermo il primo fotogramma all'infinito. */
#define ATTESA_RIDISEGNO_MS 2500

struct Palco
{
	/* Due lucchetti, con due compiti distinti: `montaggio` serializza chi monta
	 * e smonta — piu' connessioni possono chiederlo insieme — e `lucchetto`
	 * protegge il solo fotogramma, che e' l'unica cosa toccata dal thread di
	 * PipeWire.  Tenerne uno solo significherebbe che una connessione che monta
	 * blocca la cattura di quella che sta gia' disegnando. */
	GMutex montaggio;
	GMutex lucchetto;
	GCond novita;
	/* Chi usa l'input lo tiene in lettura; chi lo smonta lo prende in
	 * scrittura, e cosi' non lo si libera sotto i piedi di nessuno. */
	GRWLock uso_input;
	/* E lo stesso per il suono, per la stessa ragione: la connessione accende e
	 * spegne la cattura audio mentre la sessione puo' finire in qualunque
	 * momento. */
	GRWLock uso_suono;
	/* E per gli appunti, che oltre a tutto questo hanno un thread proprio. */
	GRWLock uso_appunti;

	TipoCompositore tipo;
	Compositore *compositore;
	Energia *energia;
	Cattura *cattura;
	Input *input;
	Suono *suono;
	Appunti *appunti;
	/* Detto una volta sola: questo compositore la misura non la cambia.  E' il
	 * caso di KWin fino alla 6.8, e ripeterlo a ogni trascinamento del bordo
	 * riempirebbe il registro di una notizia che non cambia. */
	gboolean detta_misura_fissa;

	/* La misura chiesta, cioe' quella del palco montato — e la cadenza con cui
	 * e' stato chiesto.  La cadenza si conserva perche' viaggia dentro la stessa
	 * proposta della misura: chi rinegozia la strada dei pixel deve poterla
	 * ripetere identica, o si ritroverebbe un tetto di un fotogramma al secondo
	 * senza che nulla si lamenti. */
	uint32_t larghezza, altezza;
	uint32_t fotogrammi_al_secondo;

	/* L'ultimo fotogramma, e nient'altro: di una raffica conta l'ultimo. */
	uint8_t *ultimo;
	gsize capienza;
	uint32_t passo, larghezza_arrivata, altezza_arrivata;
	guint64 generazione;
	/*
	 * Quanti fotogrammi sono arrivati per ciascuna delle due strade.
	 *
	 * Servono a una domanda sola, e non la risponde `generazione`: dopo aver
	 * cambiato strada, e' arrivato un fotogramma per quella NUOVA?
	 * `generazione` la fa avanzare anche un fotogramma della strada vecchia
	 * ancora in volo, e prenderla per buona significherebbe dichiarare riuscito
	 * un passaggio che non e' avvenuto.
	 */
	guint64 generazione_cpu;
	guint64 generazione_gpu;


	/*
	 * La stessa cosa, quando il fotogramma non passa dalla CPU: il convertitore
	 * che importa i DMA-BUF, e l'ultimo fotogramma gia' sulla scheda.
	 *
	 * ⛔ R9 VALE IDENTICA, e qui si vede bene perche' il palco e' il posto
	 *    giusto: il fotogramma conservato dev'essere qualcosa che SOPRAVVIVE al
	 *    buffer di PipeWire, che torna al suo proprietario appena la richiamata
	 *    finisce.  Conservare il DMA-BUF sarebbe tenere in ostaggio una risorsa
	 *    del compositore; conservare la superficie convertita non toglie niente
	 *    a nessuno.
	 */
	Superficie *convertitore;
	AVFrame *ultimo_gpu;
	/*
	 * La misura su cui il convertitore è stato costruito.
	 *
	 * ⛔ IL CONVERTITORE NON SI ADATTA: il suo grafo nasce con dentro la misura
	 *    del desktop e quella allineata, e un ridimensionamento le cambia
	 *    entrambe.  Tenerlo significherebbe che dopo ogni ridimensionamento
	 *    `superficie_importa` rifiuta ogni fotogramma — e chi la chiama non
	 *    saprebbe perche'.  Si confronta con la misura che ARRIVA, che e'
	 *    l'unica autorevole, e quando cambia lo si rifa'.
	 */
	uint32_t conv_larghezza, conv_altezza;

	/*
	 * La strada dei pixel, e chi la decide.
	 *
	 *   `dmabuf_permesso`  la copia zero e' compilata e non e' stata spenta a
	 *                      mano: e' una proprieta' della macchina, letta una
	 *                      volta sola;
	 *   `richieste_cpu`    quante connessioni vogliono i pixel in memoria —
	 *                      cioe' quanti client RemoteFX Progressive ci sono
	 *                      adesso.  Si conta invece di commutare perche' le
	 *                      connessioni si sovrappongono;
	 *   `in_dmabuf`        la strada che la cattura montata sta davvero
	 *                      prendendo.  E' quella che decide se il codificatore
	 *                      puo' aprirsi sulle superfici, e va letta invece di
	 *                      dedurla dalle altre due: fra il volere e l'ottenere
	 *                      c'e' una negoziazione con Mutter, che puo' dire di no.
	 */
	gboolean dmabuf_permesso;
	guint richieste_cpu;
	gboolean in_dmabuf;

	gboolean finita;
	gboolean misura_segnalata;

	/*
	 * La spia: i fotogrammi come li consegna Mutter, su disco, senza passare da
	 * RDP.
	 *
	 * ⛔ SERVE A UNA DOMANDA SOLA, ed e' quella di §5.7 di SPECIFICA.md: «GNOME
	 *    disegna male» o «il client mostra male»?  Sono due catene diverse e il
	 *    registro non le distingue — misura la seconda e tace sulla prima.
	 *
	 * Si arma da se' al RIDIMENSIONAMENTO, che e' l'istante da guardare, e si
	 * spegne da sola dopo qualche decina di fotogrammi: nessuno deve indovinare
	 * il momento giusto per accenderla.
	 */
	char *cartella_foto;
	guint foto_restanti;
	guint foto_numero;
	guint foto_numero_codifica;
	guint id_dette;
	guint id_dette_codifica;

	/*
	 * L'ANELLO: registra di continuo, e si riscrive sopra.
	 *
	 * ⛔ NASCE DA UN DIFETTO DI METODO, non di codice.  La spia su comando
	 *    (SIGUSR1) chiede a chi guarda di avvisare NEL MOMENTO in cui il difetto
	 *    accade — e un difetto che dura un secondo si racconta sempre dopo.  Con
	 *    l'anello si registra sempre un fotogramma ogni N, si tiene l'ultimo
	 *    centinaio di secondi, e chi guarda deve solo dire «e' successo alle
	 *    05:38».  Il costo e' una rilettura dalla scheda ogni N fotogrammi, e si
	 *    accende solo mentre si indaga.
	 */
	guint anello_ogni;
	guint anello_conto;
	guint anello_indice;
	FILE *anello_registro;
};

#define ANELLO_QUANTI 300

/* Quanti fotogrammi si salvano dopo un ridimensionamento: un secondo e mezzo a
 * trenta al secondo, cioe' abbastanza da contenere la transizione intera. */
#define FOTO_DOPO_RIDIMENSIONAMENTO 45

/*
 * Scrive un fotogramma BGRx come PPM.
 *
 * PPM perche' non ha bisogno di nessuna libreria: qui interessa vedere i pixel,
 * non comprimerli, e una dipendenza in piu' per una spia sarebbe un cattivo
 * affare (§2 di SPECIFICA.md, «dipendere, non riscrivere» letta al contrario:
 * quel che si butta domani non deve costare niente oggi).
 *
 * ⚠ Gira sul thread di PipeWire, che e' di tempo reale, e scrive dieci megabyte
 *   su disco.  E' accettabile perche' e' una spia che si accende a mano e si
 *   spegne da sola — ma va detto: mentre e' accesa, i tempi non si misurano.
 */
static void salva_foto(Palco *palco, const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                       uint32_t altezza)
{
	g_autofree char *percorso =
	    g_strdup_printf("%s/%06u.ppm", palco->cartella_foto, palco->foto_numero++);
	g_autofree uint8_t *riga = g_malloc((gsize) larghezza * 3);
	FILE *f = fopen(percorso, "wb");

	if (!f)
	{
		palco->foto_restanti = 0;
		errore("non riesco a scrivere %s: spia dei fotogrammi spenta", percorso);
		return;
	}
	fprintf(f, "P6\n%u %u\n255\n", larghezza, altezza);
	for (uint32_t y = 0; y < altezza; y++)
	{
		const uint8_t *sorgente = pixel + (gsize) y * passo;

		/* BGRx → RGB: il quarto byte non si guarda, ed e' proprio quello che
		 * qui non deve entrare in gioco. */
		for (uint32_t x = 0; x < larghezza; x++)
		{
			riga[x * 3 + 0] = sorgente[x * 4 + 2];
			riga[x * 3 + 1] = sorgente[x * 4 + 1];
			riga[x * 3 + 2] = sorgente[x * 4 + 0];
		}
		fwrite(riga, 1, (gsize) larghezza * 3, f);
	}
	fclose(f);
}

/*
 * La spia sulla strada della SCHEDA, e perche' e' nata solo il 7 agosto 2026.
 *
 * ⛔ `salva_foto` qui sopra e' cieca a copia zero: la chiama `su_fotogramma`,
 *    cioe' la richiamata dei pixel in memoria, e sulla strada del DMA-BUF non
 *    passa un solo byte da quella parte.  Armarla mentre la copia zero e'
 *    accesa non produce **un solo file** — e la domanda di §5.7 («la sorgente
 *    disegna male o il client mostra male?») resta senza strumento proprio
 *    sulla strada dove il difetto vive.
 *
 * Si rilegge quindi la superficie DALLA SCHEDA e se ne scrive il piano Y come
 * PGM: in bianco e nero, che per riconoscere una schermata da un'altra basta e
 * avanza, e non richiede nessuna conversione di colore.
 *
 * ⚠ Costa una lettura dalla scheda su un thread di tempo reale, ed e' molto
 *   piu' cara della sorella in memoria: mentre e' accesa i tempi non si
 *   misurano.  Per questo si arma a mano, dura poche decine di fotogrammi e si
 *   spegne da sola.
 */
static void salva_grigi_pgm(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                            uint32_t altezza, const char *percorso)
{
	FILE *f = fopen(percorso, "wb");
	g_autofree uint8_t *riga = g_malloc(larghezza);

	if (!f)
		return;
	fprintf(f, "P5\n%u %u\n255\n", larghezza, altezza);
	for (uint32_t y = 0; y < altezza; y++)
	{
		const uint8_t *s = pixel + (gsize) y * passo;

		/* BGRx → grigio approssimato: qui conta riconoscere la schermata. */
		for (uint32_t x = 0; x < larghezza; x++)
			riga[x] = (uint8_t) ((s[x * 4 + 0] + s[x * 4 + 1] + s[x * 4 + 2]) / 3);
		fwrite(riga, 1, larghezza, f);
	}
	fclose(f);
}

static void salva_superficie_pgm(Palco *palco, AVFrame *superficie, const char *percorso)
{
	AVFrame *cpu = av_frame_alloc();
	FILE *f;

	if (!cpu)
		return;
	if (av_hwframe_transfer_data(cpu, superficie, 0) < 0)
	{
		av_frame_free(&cpu);
		palco->foto_restanti = 0;
		errore("non riesco a rileggere la superficie dalla scheda: spia dei fotogrammi spenta");
		return;
	}

	f = fopen(percorso, "wb");
	if (f)
	{
		fprintf(f, "P5\n%d %d\n255\n", cpu->width, cpu->height);
		for (int y = 0; y < cpu->height; y++)
			fwrite(cpu->data[0] + (gsize) y * cpu->linesize[0], 1, (gsize) cpu->width, f);
		fclose(f);
	}
	av_frame_free(&cpu);
}

/* Un fotogramma dell'anello: nome fisso, si riscrive sopra, e una riga di
 * indice che dice a che ora e' stato preso. */
static void anello_scrivi(Palco *palco, AVFrame *superficie, const uint8_t *pixel, uint32_t passo,
                          uint32_t larghezza, uint32_t altezza)
{
	g_autofree char *percorso = NULL;
	g_autoptr(GDateTime) adesso = g_date_time_new_now_local();

	if (palco->anello_ogni == 0 || !palco->cartella_foto)
		return;
	if (++palco->anello_conto < palco->anello_ogni)
		return;
	palco->anello_conto = 0;

	percorso = g_strdup_printf("%s/anello-%03u.pgm", palco->cartella_foto,
	                           palco->anello_indice % ANELLO_QUANTI);
	if (superficie)
		salva_superficie_pgm(palco, superficie, percorso);
	else if (pixel)
		salva_grigi_pgm(pixel, passo, larghezza, altezza, percorso);
	else
		return;

	if (!palco->anello_registro)
	{
		g_autofree char *indice = g_strdup_printf("%s/anello.txt", palco->cartella_foto);
		palco->anello_registro = fopen(indice, "w");
	}
	if (palco->anello_registro)
	{
		g_autofree char *ora = g_date_time_format(adesso, "%H:%M:%S");
		fprintf(palco->anello_registro, "%03u %s.%03d\n", palco->anello_indice % ANELLO_QUANTI, ora,
		        g_date_time_get_microsecond(adesso) / 1000);
		fflush(palco->anello_registro);
	}
	palco->anello_indice++;
}

static void salva_foto_gpu(Palco *palco, AVFrame *superficie)
{
	g_autofree char *percorso =
	    g_strdup_printf("%s/%06u-scheda.pgm", palco->cartella_foto, palco->foto_numero++);

	salva_superficie_pgm(palco, superficie, percorso);
}

/*
 * L'armamento della spia, che arriva da un SEGNALE e non da un ridimensionamento.
 *
 * Il difetto da guardare non ha un istante prevedibile — lo si provoca a mano,
 * e quando si vede e' gia' passato.  `SIGUSR1` mette in conto i prossimi N
 * fotogrammi, su qualunque strada il palco stia lavorando.
 */
static gint spia_richiesta = 0;          /* la scrive il ciclo, la legge PipeWire   */
static gint spia_richiesta_codifica = 0; /* la stessa, per il thread della connessione */

void palco_spia_arma(guint quanti)
{
	g_atomic_int_set(&spia_richiesta, (gint) quanti);
	g_atomic_int_set(&spia_richiesta_codifica, (gint) quanti);
}

/*
 * La stessa fotografia, ma all'ALTRO CAPO: la superficie come la riceve il
 * codificatore, sul thread della connessione.
 *
 * ⛔ SERVE PERCHE' I DUE CAPI NON SONO LO STESSO ISTANTE.  Fra la conversione
 *    (thread di PipeWire) e la codifica (thread della connessione) passa il
 *    fotogramma conservato di R9, e quel che si conserva e' un RIFERIMENTO a
 *    una superficie: se qualcuno la riscrive nel frattempo, la spia della
 *    cattura non se ne accorge — vede il fotogramma giusto, un istante prima
 *    che diventi sbagliato.
 */
void palco_spia_superficie(Palco *palco, AVFrame *superficie)
{
	if (!palco || !superficie)
		return;
	g_mutex_lock(&palco->lucchetto);
	if (palco->id_dette_codifica < 20)
	{
		palco->id_dette_codifica++;
		diagnostica("codifica:    superficie VA %u",
		            (unsigned) (guintptr) superficie->data[3]);
	}
	if (g_atomic_int_get(&spia_richiesta_codifica) <= 0)
	{
		g_mutex_unlock(&palco->lucchetto);
		return;
	}
	if (palco->cartella_foto && g_atomic_int_add(&spia_richiesta_codifica, -1) > 0)
	{
		g_autofree char *percorso = g_strdup_printf("%s/%06u-codifica.pgm", palco->cartella_foto,
		                                            palco->foto_numero_codifica++);
		salva_superficie_pgm(palco, superficie, percorso);
	}
	g_mutex_unlock(&palco->lucchetto);
}

/* Da chiamare col lucchetto preso, all'inizio di ogni richiamata. */
static void spia_raccogli_richiesta(Palco *palco)
{
	gint chiesti = g_atomic_int_and(&spia_richiesta, 0);

	if (chiesti <= 0)
		return;
	if (!palco->cartella_foto)
	{
		avviso("spia dei fotogrammi chiesta ma REMOTIX_FOTO non e' impostata: non salvo niente");
		return;
	}
	palco->foto_restanti = (guint) chiesti;
	informazione("spia dei fotogrammi armata: i prossimi %d finiscono in %s", chiesti,
	             palco->cartella_foto);
}

/* La strada che si vorrebbe, viste le richieste in corso. */
static gboolean dmabuf_voluto(const Palco *palco)
{
	return palco->dmabuf_permesso && palco->richieste_cpu == 0;
}

/* ------------------------------------------------------------------ *
 * Le due richiamate, chiamate DAL THREAD DI PIPEWIRE
 * ------------------------------------------------------------------ */
static void su_fotogramma(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                          uint32_t altezza, gpointer dati)
{
	Palco *palco = dati;
	gsize servono = (gsize) passo * altezza;

	g_mutex_lock(&palco->lucchetto);
	spia_raccogli_richiesta(palco);
	if (palco->capienza < servono)
	{
		g_free(palco->ultimo);
		palco->ultimo = g_malloc(servono);
		palco->capienza = servono;
	}
	if (palco->foto_restanti > 0)
	{
		palco->foto_restanti--;
		salva_foto(palco, pixel, passo, larghezza, altezza);
	}
	anello_scrivi(palco, NULL, pixel, passo, larghezza, altezza);
	memcpy(palco->ultimo, pixel, servono);
	palco->passo = passo;
	palco->larghezza_arrivata = larghezza;
	palco->altezza_arrivata = altezza;
	palco->generazione++;
	palco->generazione_cpu++;
	g_cond_broadcast(&palco->novita);
	g_mutex_unlock(&palco->lucchetto);
}

/*
 * Il fotogramma che arriva come DMA-BUF.
 *
 * Si converte SUBITO — importazione sulla scheda, deposito sulla superficie
 * allineata — e si tiene il risultato.  Il buffer di PipeWire torna al suo
 * proprietario appena si esce di qui, cioe' non si trattiene niente di chi ce
 * l'ha prestato: quel che si conserva e' roba nostra.
 *
 * ⚠ Gira sul thread di PipeWire, che e' di tempo reale: qui dentro c'e' una
 *   conversione sulla scheda e nient'altro, e soprattutto nessuna attesa.
 */
static void su_dmabuf(int fd, uint32_t offset, uint32_t passo, uint64_t modificatore,
                      uint32_t larghezza, uint32_t altezza, const CatturaRegione *danno,
                      guint quante, gpointer dati)
{
	Palco *palco = dati;
	AVFrame *fotogramma;

	/*
	 * ⛔ IL CONVERTITORE SI TOCCA CON IL LUCCHETTO PRESO, e non e' pignoleria.
	 *
	 *    Lo legge questo thread, quello di PipeWire; ma a farlo buttare via e'
	 *    il thread della connessione, quando il palco cambia misura — e la
	 *    cattura in mezzo resta viva, quindi i due possono incrociarsi.  Senza
	 *    lucchetto il sintomo sarebbe un segfault dentro libavfilter, in un
	 *    thread che non ha il nostro nome.
	 *
	 *    Il lucchetto si tiene anche durante l'importazione: sono pochi
	 *    millisecondi sulla scheda, e l'alternativa — prendere il convertitore,
	 *    lasciare il lucchetto, usarlo dopo — e' esattamente l'errore che
	 *    `palco_input_prendi` esiste per evitare.
	 */
	g_mutex_lock(&palco->lucchetto);
	spia_raccogli_richiesta(palco);

	if (palco->convertitore &&
	    (palco->conv_larghezza != larghezza || palco->conv_altezza != altezza))
	{
		/*
		 * La misura e' cambiata sotto i piedi: il grafo e' costruito su quella di
		 * prima e NON si adatta.  Tenerlo significa rifiutare ogni fotogramma da
		 * qui in avanti, cioe' perdere la copia zero per il resto della sessione
		 * — misurato il 6 agosto ridimensionando a video in corso.
		 */
		informazione("la misura e' cambiata (%ux%u → %ux%u): rifaccio il convertitore",
		             palco->conv_larghezza, palco->conv_altezza, larghezza, altezza);
		av_frame_free(&palco->ultimo_gpu);
		g_clear_pointer(&palco->convertitore, superficie_libera);
	}

	if (!palco->convertitore)
	{
		palco->convertitore =
		    superficie_nuova(larghezza, altezza, immagine_allinea_larghezza(larghezza),
		                     immagine_allinea_altezza(altezza));
		if (!palco->convertitore)
		{
			/* Non si sa importare: si dice una volta e si continua a vuoto.  La
			 * cattura non avrebbe dovuto chiedere DMA-BUF senza un consumatore,
			 * quindi se si finisce qui e' un difetto nostro, non una condizione
			 * normale. */
			g_mutex_unlock(&palco->lucchetto);
			errore("arrivano DMA-BUF ma non c'e' modo di importarli: fotogrammi persi");
			return;
		}
		palco->conv_larghezza = larghezza;
		palco->conv_altezza = altezza;
	}

	{
		/* Le due strutture sono identiche ma appartengono a moduli diversi, e
		 * nessuno dei due deve includere l'altro: si copiano, che a sedici
		 * rettangoli costa nulla. */
		SuperficieRegione regioni[16];
		guint n = MIN(quante, G_N_ELEMENTS(regioni));

		for (guint i = 0; i < n; i++)
		{
			regioni[i].x = danno[i].x;
			regioni[i].y = danno[i].y;
			regioni[i].larghezza = danno[i].larghezza;
			regioni[i].altezza = danno[i].altezza;
		}
		fotogramma = superficie_importa(palco->convertitore, fd, offset, passo, modificatore,
		                                larghezza, altezza, regioni, n);
	}
	if (!fotogramma)
	{
		g_mutex_unlock(&palco->lucchetto);
		return;
	}

	av_frame_free(&palco->ultimo_gpu);
	palco->ultimo_gpu = fotogramma;
	/* L'IDENTITA' della superficie, non il suo contenuto: se il grafo ne
	 * riusasse sempre una sola, ogni fotogramma vivrebbe nello stesso posto —
	 * e il codificatore, che lavora in differita, troverebbe li' dentro quel
	 * che ci ha messo il fotogramma dopo. */
	if (palco->id_dette < 20)
	{
		palco->id_dette++;
		diagnostica("conversione: superficie VA %u, generazione %" G_GUINT64_FORMAT,
		            (unsigned) (guintptr) fotogramma->data[3], palco->generazione_gpu + 1);
	}
	if (palco->foto_restanti > 0)
	{
		palco->foto_restanti--;
		salva_foto_gpu(palco, fotogramma);
	}
	anello_scrivi(palco, fotogramma, NULL, 0, 0, 0);
	palco->larghezza_arrivata = larghezza;
	palco->altezza_arrivata = altezza;
	palco->generazione++;
	palco->generazione_gpu++;
	g_cond_broadcast(&palco->novita);
	g_mutex_unlock(&palco->lucchetto);
}

/*
 * Lo stato dei tasti a scatto, come lo vede il compositore.
 *
 * ⚠ Gira sul thread della pompa Wayland, non sul nostro: si prende il lucchetto
 *   dell'input in lettura — che e' quel che impedisce di parlare a un oggetto
 *   appena liberato — e si accoda.  Nient'altro.
 */
static void su_lucchetti(gboolean maiusc, gboolean num, gpointer dati)
{
	Palco *palco = dati;
	Input *input = palco_input_prendi(palco);

	if (input)
		input_lucchetti_veri(input, maiusc, num);
	palco_input_lascia(palco);
}

static void su_fine(gpointer dati)
{
	Palco *palco = dati;

	/*
	 * Qui si segna e basta.  Chiamare `cattura_ferma` da dentro una richiamata
	 * di PipeWire significherebbe fermare il ciclo da dentro il ciclo: si
	 * smonta dal thread della connessione, che se ne accorge al giro dopo.
	 */
	g_mutex_lock(&palco->lucchetto);
	palco->finita = TRUE;
	g_cond_broadcast(&palco->novita);
	g_mutex_unlock(&palco->lucchetto);
}

/* ------------------------------------------------------------------ *
 * Ciclo di vita
 * ------------------------------------------------------------------ */
Palco *palco_nuovo(TipoCompositore tipo)
{
	Palco *palco = g_new0(Palco, 1);
	const char *dmabuf = g_getenv("REMOTIX_DMABUF");

	palco->tipo = compositore_riconosci(tipo);
	informazione("compositore: %s", compositore_nome(palco->tipo));

	/*
	 * ⛔ LA COPIA ZERO NASCE SPENTA, e si accende con `REMOTIX_DMABUF=1`.
	 *
	 * Il 6 agosto era il contrario — nasceva accesa e `REMOTIX_DMABUF=0` la
	 * spegneva — perche' quel giorno funzionava.  Il 7 agosto la fase 9 si e'
	 * chiusa **rinviando la copia zero**: il buffer che Mutter presta non e' un
	 * fotogramma intero, e' un *diff*, e il client vede riapparire schermate
	 * gia' passate (R29, sesto punto).
	 *
	 * ⛔ E IL PREDEFINITO E' STATO RIBALTATO QUI, NEL CODICE, DOPO CHE LA SOLA
	 *    RIGA D'AMBIENTE NON E' BASTATA.  La fase 9 aveva dichiarato
	 *    «`REMOTIX_DMABUF=0` e' il predefinito» affidandolo a
	 *    `/etc/default/remotix` — un file che **vive in RAM** e che viene
	 *    riscritto (per cambiare la porta, per esempio).  Riscrivendolo la riga
	 *    di guardia e' sparita, e il difetto e' tornato in faccia all'utente lo
	 *    stesso giorno.
	 *
	 *    La regola che ne discende, e vale oltre questo caso: **la protezione di
	 *    un difetto noto non si affida a una riga di configurazione che si puo'
	 *    perdere.** Sta nel programma, dove per toglierla bisogna volerlo.
	 *
	 * `REMOTIX_DMABUF=1` resta perche' serve a chi riprendera' la caccia:
	 * `prove/fase9.sh copia-zero` gira lo stesso banco due volte, una per strada.
	 *
	 * ⭐ E SU KWIN IL PREDEFINITO E' L'OPPOSTO — accesa — perche' il difetto che
	 *    la tiene spenta NON C'E' e perche' senza di lei il requisito dell'utente
	 *    non si raggiunge.  Sono due fatti misurati, non una preferenza:
	 *
	 *    1. KWin consegna **fotogrammi interi**, sempre (`kde.md` §4.6): il
	 *       «diff» su buffer riciclati che ci ha fatto spegnere la copia zero su
	 *       GNOME e' di Mutter, non del modello PipeWire.  Qui resta solo da
	 *       aspettare la fence, e `cattura.c` la aspetta;
	 *    2. sulla Intel integrata, scena in movimento: **59 fotogrammi al secondo
	 *       da 720p a 4K a copia zero, contro 43,3 e 27,0 in memoria** [M, 8
	 *       agosto 2026].  I 60 a 4K che l'utente chiede si ottengono SOLO cosi':
	 *       il collo di bottiglia e' la copia, non il compositore ne' la GPU.
	 *
	 *    Da cui la decisione dell'utente dell'8 agosto: su KDE la cattura nasce a
	 *    copia zero, e non si scrive due volte.
	 */
	palco->dmabuf_permesso = (palco->tipo == COMPOSITORE_KWIN);
	if (dmabuf)
		palco->dmabuf_permesso = (*dmabuf == '1');

	/* La spia dei fotogrammi, spenta se nessuno dice dove metterli. */
	if (g_getenv("REMOTIX_FOTO"))
	{
		palco->cartella_foto = g_strdup(g_getenv("REMOTIX_FOTO"));
		if (g_getenv("REMOTIX_FOTO_OGNI"))
		{
			palco->anello_ogni = (guint) atoi(g_getenv("REMOTIX_FOTO_OGNI"));
			informazione("anello dei fotogrammi acceso: uno ogni %u, ultimi %d in %s",
			             palco->anello_ogni, ANELLO_QUANTI, palco->cartella_foto);
		}
		g_mkdir_with_parents(palco->cartella_foto, 0755);
		avviso("spia dei fotogrammi accesa: %s — si armera' a ogni ridimensionamento",
		       palco->cartella_foto);
	}

	g_mutex_init(&palco->montaggio);
	g_mutex_init(&palco->lucchetto);
	g_cond_init(&palco->novita);
	g_rw_lock_init(&palco->uso_input);
	g_rw_lock_init(&palco->uso_suono);
	g_rw_lock_init(&palco->uso_appunti);
	return palco;
}

/* Va chiamata con `montaggio` preso e `lucchetto` LIBERO: `cattura_ferma`
 * aspetta il thread di PipeWire, che potrebbe essere fermo proprio sul
 * lucchetto dentro `su_fotogramma`. */
static void smonta_interno(Palco *palco)
{
	/*
	 * L'input per primo: i suoi dispositivi virtuali appartengono alla sessione
	 * di controllo, e chiuderla sotto di lui lo lascerebbe a parlare nel vuoto.
	 *
	 * Si ferma tenendo il lucchetto in SCRITTURA, cioe' aspettando che nessuna
	 * connessione lo stia usando: fermarlo mentre qualcuno vi accoda un tasto
	 * gli libera la coda sotto le mani.
	 */
	g_rw_lock_writer_lock(&palco->uso_input);
	g_clear_pointer(&palco->input, input_ferma);
	g_rw_lock_writer_unlock(&palco->uso_input);

	/*
	 * Il suono si chiude tenendo il suo lucchetto in SCRITTURA, cioe'
	 * aspettando che nessuna connessione stia accendendo o spegnendo la propria
	 * cattura.  Da qui in poi chi chiede il suono trova NULL — ed e' il motivo
	 * per cui il puntatore non si tiene da parte, ma si richiede ogni volta.
	 */
	g_rw_lock_writer_lock(&palco->uso_suono);
	g_clear_pointer(&palco->suono, suono_chiudi);
	g_rw_lock_writer_unlock(&palco->uso_suono);

	/*
	 * Gli appunti prima della sessione di controllo che li ospita: sono metodi
	 * di QUELLA sessione, e chiuderla sotto di loro li lascerebbe a parlare con
	 * un oggetto che non esiste piu'.
	 */
	g_rw_lock_writer_lock(&palco->uso_appunti);
	g_clear_pointer(&palco->appunti, appunti_chiudi);
	g_rw_lock_writer_unlock(&palco->uso_appunti);

	g_clear_pointer(&palco->cattura, cattura_ferma);
	/* L'inibizione PRIMA del compositore: e' un oggetto di powerdevil, che vive
	 * dentro la sessione, e rilasciarla dopo significherebbe parlare a un bus che
	 * puo' non avere piu' nessuno dall'altra parte. */
	g_clear_pointer(&palco->energia, energia_rilascia);
	g_clear_pointer(&palco->compositore, compositore_chiudi);

	/*
	 * Il convertitore DOPO la cattura, e non prima: e' il thread di PipeWire a
	 * usarlo, e finche' la cattura e' viva quel thread puo' essere dentro
	 * `su_dmabuf`.  Fermata lei, non c'e' piu' nessuno che lo tocchi.
	 *
	 * Muore col palco perche' e' costruito sulla SUA misura: un palco nuovo ne
	 * vuole uno nuovo, e riusare quello vecchio significherebbe comporre un
	 * desktop dentro una superficie della misura di prima.
	 */
	g_mutex_lock(&palco->lucchetto);
	av_frame_free(&palco->ultimo_gpu);
	g_clear_pointer(&palco->convertitore, superficie_libera);
	g_mutex_unlock(&palco->lucchetto);

	g_mutex_lock(&palco->lucchetto);
	palco->larghezza = palco->altezza = 0;
	palco->finita = FALSE;
	palco->misura_segnalata = FALSE;
	/* La strada e' una proprieta' della cattura, che non c'e' piu'.  Le RICHIESTE
	 * invece restano: appartengono alle connessioni, che sono ancora la'. */
	palco->in_dmabuf = FALSE;
	/*
	 * La generazione NON si azzera, e non e' un dettaglio: un'altra connessione
	 * puo' essere in corso e avere gia' visto il fotogramma numero 500.
	 * Ripartendo da zero, per lei nulla sarebbe piu' «nuovo» e resterebbe ferma
	 * sull'immagine di prima per sempre — un difetto che si presenterebbe solo
	 * con due client sovrapposti, cioe' a intermittenza e mai a comando.
	 */
	g_mutex_unlock(&palco->lucchetto);
}

void palco_smonta(Palco *palco)
{
	if (!palco)
		return;
	g_mutex_lock(&palco->montaggio);
	if (palco->compositore)
	{
		smonta_interno(palco);
		informazione("palco smontato");
	}
	g_mutex_unlock(&palco->montaggio);
}

void palco_libera(Palco *palco)
{
	if (!palco)
		return;
	palco_smonta(palco);
	g_free(palco->ultimo);
	g_free(palco->cartella_foto);
	g_rw_lock_clear(&palco->uso_appunti);
	g_rw_lock_clear(&palco->uso_suono);
	g_rw_lock_clear(&palco->uso_input);
	g_cond_clear(&palco->novita);
	g_mutex_clear(&palco->lucchetto);
	g_mutex_clear(&palco->montaggio);
	g_free(palco);
}

/*
 * Aspetta che il desktop si sia RIDISEGNATO alla misura nuova (R10).
 *
 * Si raccolgono i fotogrammi finche' non smettono di arrivare, e ci si fida del
 * silenzio solo dopo il secondo: il primo dopo un cambio di misura e' quello
 * vuoto, e il silenzio fra lui e quello buono e' la trappola.
 */
static void stabilizza(Palco *palco)
{
	gint64 scadenza = g_get_monotonic_time() + (gint64) ATTESA_RIDISEGNO_MS * 1000;
	guint raccolti = 0;
	guint64 vista;

	g_mutex_lock(&palco->lucchetto);
	vista = palco->generazione;
	while (g_get_monotonic_time() < scadenza)
	{
		gint64 fine_quiete = g_get_monotonic_time() + (gint64) QUIETE_RIDISEGNO_MS * 1000;

		if (!g_cond_wait_until(&palco->novita, &palco->lucchetto, fine_quiete))
		{
			/* Silenzio. */
			if (raccolti >= FOTOGRAMMI_PRIMA_DI_FIDARSI)
				break;
			continue;
		}
		if (palco->finita)
			break;
		if (palco->generazione > vista)
		{
			raccolti += (guint) (palco->generazione - vista);
			vista = palco->generazione;
		}
		/*
		 * ⛔ RACCOLTI ABBASTANZA: SI SMETTE, SENZA ASPETTARE IL SILENZIO.
		 *
		 *    Il silenzio serviva a sapere che il ridisegno era finito, e su un
		 *    desktop fermo funziona: dopo un cambio di misura Mutter manda due
		 *    fotogrammi — il primo vuoto, il secondo buono — e poi tace.
		 *
		 *    Ma un desktop che LAVORA non tace mai.  Con un video in riproduzione
		 *    il silenzio non arriva, si va a sbattere contro il tetto, e ogni
		 *    ridimensionamento costa DUE SECONDI E MEZZO in cui al client non
		 *    parte un fotogramma.  Misurato il 6 agosto sulla sessione
		 *    dell'utente: «44 fotogrammi raccolti» in 2,5 s, e poi altri 46.
		 *
		 *    R10 di REFERENCE.md lo dice: il riferimento non aspetta un silenzio,
		 *    aspetta un EVENTO.  L'evento qui ci sono entrambi: la conferma della
		 *    misura da Mutter — che `cattura_ridimensiona` ha gia' atteso — e il
		 *    secondo fotogramma, che e' quello ridisegnato.  Il silenzio resta
		 *    solo per il caso opposto: un desktop cosi' fermo da non mandarne
		 *    nemmeno due.
		 */
		if (raccolti >= FOTOGRAMMI_PRIMA_DI_FIDARSI)
			break;
	}
	g_mutex_unlock(&palco->lucchetto);

	diagnostica("atteso il ridisegno alla misura nuova: %u fotogrammi raccolti", raccolti);
}

/* Va chiamata con `montaggio` preso e con NULLA di montato. */
static gboolean monta_interno(Palco *palco, uint32_t larghezza, uint32_t altezza,
                              uint32_t fotogrammi_al_secondo, GError **sbaglio)
{
	uint32_t negoziata_l = 0, negoziata_a = 0;
	uint32_t imposta_l = 0, imposta_a = 0;

	palco->compositore = compositore_apri(palco->tipo, sbaglio);
	if (!palco->compositore)
		return FALSE;

	/*
	 * ⛔ SU KWIN LA MISURA NON LA DECIDIAMO NOI, E VA ADOTTATA PRIMA DI CHIEDERE
	 *    LA CATTURA.
	 *
	 *    Il backend `--virtual` non sa creare uscite a richiesta e un output
	 *    virtuale ha un solo modo, immutabile: il desktop e' grande quanto il
	 *    compositore l'ha fatto (`kde.md` §5.2 e §8.1).  Chiedere la misura del
	 *    client produrrebbe una tela che non corrisponde ai fotogrammi — cioe' un
	 *    desktop che copre una parte della superficie, che e' il sintomo che il
	 *    3 agosto e' costato una caccia e una questione aperta.
	 *
	 *    E' anche la decisione dell'utente dell'8 agosto 2026: misura fissa alla
	 *    connessione, l'immagine si scala nel client.
	 */
	compositore_misura_imposta(palco->compositore, &imposta_l, &imposta_a);
	if (imposta_l && imposta_a && (imposta_l != larghezza || imposta_a != altezza))
	{
		informazione("il client chiede %ux%u ma il compositore serve %ux%u: adotto la sua",
		             larghezza, altezza, imposta_l, imposta_a);
		larghezza = imposta_l;
		altezza = imposta_a;
	}

	/*
	 * Il consumatore dei DMA-BUF si dichiara solo se lo si sa leggere: senza,
	 * la cattura non li chiede affatto e si resta sul percorso in memoria.
	 *
	 * Si passa `su_dmabuf` ogni volta che la copia zero e' permessa — cioe' si
	 * dichiara di SAPERLI leggere — e si dice separatamente se in questo momento
	 * li si VOGLIA: le due cose divergono quando c'e' gia' un client RemoteFX
	 * Progressive collegato, e un palco che si rimonta sotto di lui deve nascere
	 * in memoria invece di doverci tornare subito dopo.
	 */
	palco->cattura = cattura_avvia(compositore_nodo(palco->compositore), larghezza, altezza,
	                               fotogrammi_al_secondo, imposta_l != 0, su_fotogramma,
	                               palco->dmabuf_permesso ? su_dmabuf : NULL, su_fine, palco,
	                               sbaglio);
	if (!palco->cattura)
	{
		g_clear_pointer(&palco->compositore, compositore_chiudi);
		return FALSE;
	}
	palco->in_dmabuf = palco->dmabuf_permesso;
	if (palco->dmabuf_permesso && !dmabuf_voluto(palco))
	{
		g_autoptr(GError) sbaglio_strada = NULL;

		if (cattura_dmabuf(palco->cattura, FALSE, larghezza, altezza, fotogrammi_al_secondo,
		                   &sbaglio_strada))
			palco->in_dmabuf = FALSE;
		else
			errore("il palco nasce sulla scheda ma c'e' chi vuole i pixel in CPU (%s): "
			       "quel client non vedra' niente",
			       sbaglio_strada->message);
	}

	/*
	 * La misura DAVVERO negoziata: e' l'unica autorevole, e va adottata invece
	 * che lamentata.  Il sintomo di una tela che non le corrisponde e' un desktop
	 * che copre solo una parte della superficie — e quel sintomo, quando comparve
	 * il 3 agosto, costo' una caccia che fini' in una questione aperta.
	 */
	cattura_misura_negoziata(palco->cattura, &negoziata_l, &negoziata_a);
	if (negoziata_l && (negoziata_l != larghezza || negoziata_a != altezza))
	{
		informazione("il formato negoziato e' %ux%u invece dei %ux%u chiesti: il palco prende "
		             "quella",
		             negoziata_l, negoziata_a, larghezza, altezza);
		larghezza = negoziata_l;
		altezza = negoziata_a;
	}

	/*
	 * Il canale di input, se il compositore l'ha concesso.  Non fallisce il
	 * montaggio se manca: si degrada a sola visione, e lo si dichiara.
	 */
	{
		int fd = compositore_prendi_fd_eis(palco->compositore);

		if (fd >= 0)
		{
			g_autoptr(GError) sbaglio_input = NULL;
			Input *nuovo =
			    input_avvia(fd, compositore_mapping_id(palco->compositore),
			                palco->tipo == COMPOSITORE_KWIN, &sbaglio_input);

			g_rw_lock_writer_lock(&palco->uso_input);
			palco->input = nuovo;
			g_rw_lock_writer_unlock(&palco->uso_input);
			if (!palco->input)
				avviso("input non avviato (%s): la sessione sara' di sola visione",
				       sbaglio_input->message);
			else
				/* Lo stato vero dei lucchetti, per chi non lo manda con l'input.
				 * Su Mutter questa chiamata non fa niente, e va bene: la' arriva
				 * da libei. */
				compositore_lucchetti_ascolta(palco->compositore, su_lucchetti, palco);
		}
		else
		{
			avviso("nessun canale di input: la sessione sara' di sola visione");
		}
	}
	if (palco->input)
		input_misura(palco->input, larghezza, altezza);

	/*
	 * Il sink virtuale, e il suo posto e' QUI perche' e' della SESSIONE.
	 *
	 * Nella sessione senza monitor non esiste alcun dispositivo audio (§7.5 di
	 * REFERENCE.md, misurato): se non lo si crea, le applicazioni non hanno dove
	 * suonare e non c'e' niente da catturare — senza un errore da nessuna parte.
	 *
	 * Non fallisce il montaggio se non riesce: un desktop senza suono e' molto
	 * piu' di nessun desktop, ed e' la regola «degradare, non fallire» di §2 di
	 * SPECIFICA.md.  La cattura vera e propria la accende la connessione, quando
	 * il client avra' negoziato un formato.
	 */
	{
		g_autoptr(GError) sbaglio_suono = NULL;
		Suono *nuovo = suono_apri(&sbaglio_suono);

		g_rw_lock_writer_lock(&palco->uso_suono);
		palco->suono = nuovo;
		g_rw_lock_writer_unlock(&palco->uso_suono);
		if (!nuovo)
			avviso("sink audio non montato (%s): la sessione sara' muta",
			       sbaglio_suono->message);
	}

	/*
	 * Gli appunti della sessione, sulla STESSA sessione di controllo del palco:
	 * Mutter li espone li' (§14.1 di gnome-remote-desktop.md), e chi non ha una
	 * sessione di controllo non ha appunti.  Come per il suono, se non si
	 * accendono non si fallisce il montaggio: si degrada e si dichiara.
	 */
	{
		TipoCompositore tipo = compositore_tipo(palco->compositore);
		const char *controllo = compositore_percorso_controllo(palco->compositore);
		g_autoptr(GError) sbaglio_appunti = NULL;
		g_autoptr(GDBusConnection) bus = NULL;
		Appunti *nuovi = NULL;

		/*
		 * ⚠ Il bus serve alla sola strada di Mutter, e si chiede solo se serve:
		 *   su KWin la clipboard non passa da D-Bus, e aprire una connessione per
		 *   poi non usarla vorrebbe dire far fallire il montaggio degli appunti
		 *   per un motivo che non li riguarda.
		 */
		if (controllo)
			bus = sessione_bus(&sbaglio_appunti);

		if (controllo ? (bus != NULL) : (tipo == COMPOSITORE_KWIN))
			nuovi = appunti_apri(tipo, bus, controllo, &sbaglio_appunti);

		g_rw_lock_writer_lock(&palco->uso_appunti);
		palco->appunti = nuovi;
		g_rw_lock_writer_unlock(&palco->uso_appunti);
		if (!nuovi)
			avviso("appunti non accesi (%s): niente copia-incolla in questa sessione",
			       sbaglio_appunti ? sbaglio_appunti->message : "strada non prevista");
	}

	/*
	 * Lo schermo che non si spegne da solo.  Va preso DOPO il resto: powerdevil
	 * parte con `plasma-workspace.target`, cioe' dopo il compositore, e chiederglielo
	 * troppo presto significa chiederlo a chi non c'e' ancora.
	 */
	palco->energia = energia_inibisci(palco->tipo);

	g_mutex_lock(&palco->lucchetto);
	palco->larghezza = larghezza;
	palco->altezza = altezza;
	palco->fotogrammi_al_secondo = fotogrammi_al_secondo;
	g_mutex_unlock(&palco->lucchetto);

	informazione("palco montato: desktop %ux%u, pixel %s, input %s, suono %s, appunti %s", larghezza,
	             altezza, palco->in_dmabuf ? "sulla scheda" : "in memoria",
	             palco->input ? "acceso" : "SPENTO", palco->suono ? "pronto" : "SPENTO",
	             palco->appunti ? "accesi" : "SPENTI");
	stabilizza(palco);
	return TRUE;
}

/*
 * Cambia misura a un palco gia' montato.  Va chiamata con `montaggio` preso.
 */
static gboolean ridimensiona_interno(Palco *palco, uint32_t larghezza, uint32_t altezza,
                                     uint32_t fotogrammi_al_secondo, GError **sbaglio)
{
	g_autoptr(GError) sbaglio_interno = NULL;
	uint32_t confermata_l = 0, confermata_a = 0;

	if (palco->larghezza == larghezza && palco->altezza == altezza)
	{
		diagnostica("il palco e' gia' %ux%u: non c'e' niente da ridimensionare", larghezza,
		            altezza);
		return TRUE;
	}

	informazione("ridimensiono il palco: %ux%u → %ux%u", palco->larghezza, palco->altezza,
	             larghezza, altezza);

	if (cattura_ridimensiona(palco->cattura, larghezza, altezza, fotogrammi_al_secondo,
	                         &confermata_l, &confermata_a, &sbaglio_interno))
	{
		/*
		 * ⛔ SI ADOTTA LA MISURA CONFERMATA, NON QUELLA CHIESTA.
		 *
		 *    Su Mutter le due coincidono sempre: il monitor virtuale si fa della
		 *    misura chiesta.  Su KWin fino alla 6.8 no — l'output ha un solo modo
		 *    e il compositore risponde con il proprio — e prendere per buona quella
		 *    chiesta significherebbe dichiarare al client una tela che i fotogrammi
		 *    non riempiono.  La richiesta si manda comunque, nella forma della
		 *    negoziazione: e' quella che su 6.8 funzionera' da se' (`kde.md` §8.2).
		 */
		if (confermata_l && (confermata_l != larghezza || confermata_a != altezza))
		{
			if (!palco->detta_misura_fissa)
			{
				palco->detta_misura_fissa = TRUE;
				avviso("questo compositore non ridimensiona lo schermo: resta %ux%u, e il "
				       "client NON la scala — aprira' una finestra di quella misura.  Per "
				       "cambiarla bisogna far finire la sessione.  Il ridimensionamento vero "
				       "arriva con KWin 6.8, per negoziazione, e questo codice e' gia' nella "
				       "forma giusta",
				       confermata_l, confermata_a);
			}
			larghezza = confermata_l;
			altezza = confermata_a;
		}

		g_mutex_lock(&palco->lucchetto);
		palco->larghezza = larghezza;
		palco->altezza = altezza;
		palco->fotogrammi_al_secondo = fotogrammi_al_secondo;
		/*
		 * Il convertitore va buttato QUI, prima di aspettare il ridisegno: cosi'
		 * il primo fotogramma della misura nuova lo ricostruisce durante
		 * `stabilizza`, e quando la connessione andra' a riaprire il codificatore
		 * ne trovera' uno gia' giusto.  Buttarlo dopo — o non buttarlo affatto —
		 * significa consegnare al codificatore superfici della misura di prima,
		 * che le rifiuta: e da li' la copia zero e' persa per il resto della
		 * sessione.  [M, 6 agosto 2026, ridimensionando a video in corso]
		 */
		av_frame_free(&palco->ultimo_gpu);
		g_clear_pointer(&palco->convertitore, superficie_libera);
		/* La spia si arma QUI: il ridimensionamento e' l'istante da guardare, e
		 * armarla da sola toglie di mezzo il problema di indovinare quando
		 * accenderla. */
		if (palco->cartella_foto)
			palco->foto_restanti = FOTO_DOPO_RIDIMENSIONAMENTO;
		/* La misura vecchia e' stata segnalata una volta e non vale piu': se la
		 * tela e il fotogramma tornassero a non corrispondere, lo si deve poter
		 * leggere di nuovo. */
		palco->misura_segnalata = FALSE;
		g_mutex_unlock(&palco->lucchetto);

		/*
		 * Le coordinate assolute del puntatore si riscalano su questa misura.
		 * Va detto subito: fra il ridimensionamento e il primo movimento del
		 * mouse non c'e' niente, e un puntatore che finisce a meta' schermo e'
		 * il genere di difetto che si attribuisce al client.
		 *
		 * La REGIONE su cui si riscala, invece, la riannuncia il compositore:
		 * Mutter ricrea il dispositivo virtuale quando il monitor cambia, e
		 * `input.c` rilegge la regione a ogni `DEVICE_ADDED`/`DEVICE_RESUMED`.
		 */
		if (palco->input)
			input_misura(palco->input, larghezza, altezza);

		stabilizza(palco);
		return TRUE;
	}

	/*
	 * Il ripiego, e va dichiarato per nome.
	 *
	 * Rimontare funziona — e' quel che si faceva fino alla fase 5 — ma costa il
	 * conto dei tasti premuti, un monitor virtuale nuovo per GNOME e un secondo
	 * riavvio del decodificatore su Android.  Nel banco della fase 6 la
	 * comparsa di questa riga e' un guasto, non un dettaglio.
	 */
	errore("ridimensionamento a caldo fallito: %s", sbaglio_interno->message);
	avviso("ripiego: rifaccio il palco da capo — si perde lo stato dell'input");
	smonta_interno(palco);
	return monta_interno(palco, larghezza, altezza, fotogrammi_al_secondo, sbaglio);
}

/*
 * Il volume del sink al massimo, a ogni collegamento.
 *
 * ⛔ IL SINK VIVE QUANTO IL PALCO, NON QUANTO LA CONNESSIONE — misurato l'8
 *    agosto 2026: staccato il client, il nodo restava con i volumi a 0.008 e
 *    `mute true`, e il collegamento dopo li ritrovava tali e quali.  Metterlo al
 *    massimo alla sola creazione, come si era fatto in prima battuta, non chiude
 *    niente: chi zittisce e si scollega ritrova il silenzio domani, e non ha
 *    modo di sapere perche'.
 *
 * Da cui la regola, che e' anche facile da ricordare: **ci si collega e il
 * volume e' al massimo**; se lo si abbassa resta abbassato finche' si resta.
 */
static void alza_il_volume(Palco *palco)
{
	Suono *suono = palco_suono_prendi(palco);

	if (suono)
		suono_volume_massimo(suono);
	palco_suono_lascia(palco);
}

gboolean palco_assicura(Palco *palco, uint32_t larghezza, uint32_t altezza,
                        uint32_t fotogrammi_al_secondo, GError **sbaglio)
{
	gboolean finita;
	gboolean esito;

	g_mutex_lock(&palco->montaggio);

	g_mutex_lock(&palco->lucchetto);
	finita = palco->finita;
	g_mutex_unlock(&palco->lucchetto);

	if (palco->compositore && !finita)
	{
		if (palco->larghezza == larghezza && palco->altezza == altezza)
		{
			diagnostica("palco gia' montato della misura giusta (%ux%u): si riusa", larghezza,
			            altezza);
			alza_il_volume(palco);
			g_mutex_unlock(&palco->montaggio);
			return TRUE;
		}

		/*
		 * Chi si ricollega chiedendo un'altra misura non ha bisogno di un palco
		 * nuovo: ne ha bisogno di uno RIDIMENSIONATO.
		 *
		 * Fino alla fase 5 qui si smontava e si rimontava, e il prezzo lo pagava
		 * la sessione: smontare lascia Mutter con zero schermi, e da li'
		 * `libmutter` va in asserzione fallita e le applicazioni aperte perdono
		 * la connessione Wayland (§7.3 di REFERENCE.md).  Con la fase 6 la
		 * strada c'e', ed e' la stessa del ridimensionamento a caldo: chi torna
		 * da un'altra finestra ritrova le proprie finestre dov'erano, solo
		 * disposte diversamente.
		 */
		informazione("chi si collega chiede %ux%u invece di %ux%u: ridimensiono invece di "
		             "rimontare",
		             larghezza, altezza, palco->larghezza, palco->altezza);
		esito = ridimensiona_interno(palco, larghezza, altezza, fotogrammi_al_secondo, sbaglio);
		alza_il_volume(palco);
		g_mutex_unlock(&palco->montaggio);
		return esito;
	}

	/* Si smonta PRIMA di rimontare: due monitor virtuali insieme farebbero
	 * credere a GNOME di avere due schermi. */
	if (palco->compositore)
	{
		informazione("il palco va rifatto: %ux%u (la cattura precedente si era chiusa)", larghezza,
		             altezza);
		smonta_interno(palco);
	}

	esito = monta_interno(palco, larghezza, altezza, fotogrammi_al_secondo, sbaglio);
	g_mutex_unlock(&palco->montaggio);
	return esito;
}

gboolean palco_ridimensiona(Palco *palco, uint32_t larghezza, uint32_t altezza,
                            uint32_t fotogrammi_al_secondo, GError **sbaglio)
{
	gboolean finita;
	gboolean esito;

	g_mutex_lock(&palco->montaggio);

	if (!palco->compositore)
	{
		g_mutex_unlock(&palco->montaggio);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_INITIALIZED,
		            "non c'e' nessun palco da ridimensionare");
		return FALSE;
	}

	g_mutex_lock(&palco->lucchetto);
	finita = palco->finita;
	g_mutex_unlock(&palco->lucchetto);
	if (finita)
	{
		g_mutex_unlock(&palco->montaggio);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_CLOSED,
		            "la cattura si e' chiusa: non c'e' piu' niente da ridimensionare");
		return FALSE;
	}

	esito = ridimensiona_interno(palco, larghezza, altezza, fotogrammi_al_secondo, sbaglio);
	g_mutex_unlock(&palco->montaggio);
	return esito;
}

TipoCompositore palco_compositore(Palco *palco)
{
	return palco ? palco->tipo : COMPOSITORE_AUTO;
}

void palco_misura(Palco *palco, uint32_t *larghezza, uint32_t *altezza)
{
	*larghezza = 0;
	*altezza = 0;
	if (!palco)
		return;
	g_mutex_lock(&palco->lucchetto);
	*larghezza = palco->larghezza;
	*altezza = palco->altezza;
	g_mutex_unlock(&palco->lucchetto);
}

Input *palco_input_prendi(Palco *palco)
{
	if (!palco)
		return NULL;
	g_rw_lock_reader_lock(&palco->uso_input);
	return palco->input;
}

void palco_input_lascia(Palco *palco)
{
	if (palco)
		g_rw_lock_reader_unlock(&palco->uso_input);
}

Suono *palco_suono_prendi(Palco *palco)
{
	if (!palco)
		return NULL;
	g_rw_lock_reader_lock(&palco->uso_suono);
	return palco->suono;
}

void palco_suono_lascia(Palco *palco)
{
	if (palco)
		g_rw_lock_reader_unlock(&palco->uso_suono);
}

Appunti *palco_appunti_prendi(Palco *palco)
{
	if (!palco)
		return NULL;
	g_rw_lock_reader_lock(&palco->uso_appunti);
	return palco->appunti;
}

void palco_appunti_lascia(Palco *palco)
{
	if (palco)
		g_rw_lock_reader_unlock(&palco->uso_appunti);
}

/*
 * Il contesto delle superfici su cui aprire il codificatore, o NULL se il palco
 * non sta lavorando a copia zero.
 *
 * ⛔ Il codificatore va aperto su QUESTO contesto, o rifiutera' i fotogrammi:
 *    libavcodec accetta solo superfici che vengono dal contesto con cui e'
 *    stato aperto.  E' anche il modo con cui il chiamante scopre quale strada
 *    sta prendendo il palco, senza doverlo chiedere due volte.
 */
AVBufferRef *palco_superfici(Palco *palco)
{
	AVBufferRef *ref = NULL;

	/*
	 * ⛔ IL PALCO PUO' NON ESSERCI, e questa riga e' costata un segfault.
	 *
	 *    Con `--immagine-di-prova` il server non ne crea affatto uno — la scena
	 *    la disegna in memoria e non c'e' niente da catturare — quindi qui arriva
	 *    NULL, e `allestisci_tela` chiama questa funzione per OGNI connessione
	 *    AVC420.  Il sintomo era il server che moriva subito dopo «EGFX
	 *    negoziato», con il client che vedeva `BIO_read retries exceeded`: cioe'
	 *    una caduta di rete, dalla parte sbagliata del filo.
	 *
	 *    Le sorelle di questa funzione — `palco_input_prendi`, `palco_suono_prendi`,
	 *    `palco_appunti_prendi` — il controllo ce l'hanno tutte.  Questa e' nata
	 *    dopo, con la copia zero, e se l'e' persa: e' proprio il tipo di
	 *    disallineamento che si trova solo eseguendo il banco della fase che non
	 *    si sta scrivendo.  [M, 6 agosto 2026]
	 */
	if (!palco)
		return NULL;

	g_mutex_lock(&palco->lucchetto);
	/*
	 * ⛔ SI GUARDA LA STRADA, non l'esistenza del convertitore.
	 *
	 *    Il convertitore sopravvive a un ritorno in memoria — costa poco tenerlo
	 *    e serve se si torna sulla scheda — quindi «c'e' un convertitore» non
	 *    significa piu' «arrivano fotogrammi sulla scheda».  Rispondere di si'
	 *    qui farebbe aprire il codificatore sulle superfici mentre i fotogrammi
	 *    arrivano in memoria: nessun errore, e uno schermo fermo.
	 */
	/*
	 * ⛔ E SI GUARDA ANCHE LA MISURA.  Un convertitore della misura di prima e'
	 *    peggio di nessun convertitore: il codificatore ci si aprirebbe sopra e
	 *    poi rifiuterebbe ogni fotogramma.  Se qui si risponde NULL il
	 *    codificatore nasce in CPU e il palco lo segue — degradato, ma vivo e
	 *    dichiarato.
	 */
	if (palco->in_dmabuf && palco->convertitore && palco->conv_larghezza == palco->larghezza &&
	    palco->conv_altezza == palco->altezza)
		ref = superficie_contesto(palco->convertitore);
	g_mutex_unlock(&palco->lucchetto);
	return ref;
}

/*
 * Aspetta che sia arrivato un fotogramma PER LA STRADA NUOVA.
 *
 * Non basta guardare `generazione`: un fotogramma della strada vecchia ancora in
 * volo la fa avanzare, e si dichiarerebbe riuscito un passaggio che non e'
 * avvenuto.  Si guarda il contatore della sola strada che interessa, preso
 * prima del cambio.
 */
static gboolean aspetta_strada_nuova(Palco *palco, gboolean sulla_scheda, guint64 partenza)
{
	gint64 scadenza = g_get_monotonic_time() + (gint64) ATTESA_RIDISEGNO_MS * 1000;
	const guint64 *conto = sulla_scheda ? &palco->generazione_gpu : &palco->generazione_cpu;
	gboolean arrivato;

	g_mutex_lock(&palco->lucchetto);
	while (*conto == partenza && !palco->finita)
	{
		if (!g_cond_wait_until(&palco->novita, &palco->lucchetto, scadenza))
			break;
	}
	arrivato = *conto > partenza;
	g_mutex_unlock(&palco->lucchetto);
	return arrivato;
}

void palco_pixel_in_cpu(Palco *palco, gboolean servono)
{
	g_autoptr(GError) sbaglio = NULL;
	gboolean vuole;
	guint64 partenza;
	uint32_t larghezza, altezza, cadenza;

	if (!palco)
		return;

	g_mutex_lock(&palco->montaggio);

	if (servono)
	{
		palco->richieste_cpu++;
	}
	else if (palco->richieste_cpu > 0)
	{
		palco->richieste_cpu--;
	}
	else
	{
		/* Piu' rilasci che richieste: e' un difetto di chi chiama, e va detto
		 * invece di far tornare i conti in silenzio. */
		errore("pixel in CPU rilasciati piu' volte di quante erano stati chiesti");
		g_mutex_unlock(&palco->montaggio);
		return;
	}

	/*
	 * Con la copia zero spenta `dmabuf_voluto` e' sempre falso e `in_dmabuf`
	 * pure: i due coincidono e si esce di qui senza toccare niente, che e'
	 * l'esito giusto — i pixel sono gia' dove il chiamante li vuole.
	 */
	vuole = dmabuf_voluto(palco);
	if (!palco->cattura || vuole == palco->in_dmabuf)
	{
		g_mutex_unlock(&palco->montaggio);
		return;
	}

	g_mutex_lock(&palco->lucchetto);
	larghezza = palco->larghezza;
	altezza = palco->altezza;
	cadenza = palco->fotogrammi_al_secondo;
	partenza = vuole ? palco->generazione_gpu : palco->generazione_cpu;
	g_mutex_unlock(&palco->lucchetto);

	informazione("porto la cattura %s: ci sono %u client che vogliono i pixel in CPU",
	             vuole ? "sulla scheda" : "in memoria", palco->richieste_cpu);

	if (!cattura_dmabuf(palco->cattura, vuole, larghezza, altezza, cadenza, &sbaglio))
	{
		/*
		 * Si tiene la strada che si ha, e lo si dice forte.  Un client che voleva
		 * i pixel in CPU e non li avra' vedra' uno schermo fermo, che senza questa
		 * riga sarebbe indistinguibile da un desktop che non cambia.
		 */
		errore("la cattura non ha cambiato strada (%s): chi voleva i pixel %s restera' com'e'",
		       sbaglio->message, vuole ? "sulla scheda" : "in memoria");
		g_mutex_unlock(&palco->montaggio);
		return;
	}

	g_mutex_lock(&palco->lucchetto);
	palco->in_dmabuf = vuole;
	if (!vuole)
	{
		/*
		 * Il fotogramma sulla scheda non serve piu' a nessuno, e tenerlo sarebbe
		 * peggio che inutile: `palco_preleva_superficie` lo riconsegnerebbe a chi
		 * si aprisse sulle superfici, sempre lo stesso, per sempre.
		 */
		av_frame_free(&palco->ultimo_gpu);
	}
	g_mutex_unlock(&palco->lucchetto);

	/*
	 * Si ASPETTA il primo fotogramma della strada nuova, e vale in ENTRAMBI i
	 * versi.  Non e' zelo: quel che il palco conserva per R9 sta su una strada
	 * sola — o e' una superficie della scheda o e' un buffer in memoria — e a chi
	 * legge dall'altra non serve a niente.  Finche' Mutter non ne manda uno nuovo
	 * non c'e' niente da disegnare, e su un desktop fermo non ne manda mai (R9,
	 * di nuovo, con una causa nuova).
	 *
	 * Se non arriva lo si dice, perche' il sintomo altrimenti sarebbe uno schermo
	 * nero senza una riga che lo spieghi.  Il fotogramma vecchio dell'altra
	 * strada, se c'e', resta ed e' meglio di niente: sara' vecchio, non sbagliato.
	 */
	if (!aspetta_strada_nuova(palco, vuole, partenza))
		avviso("nessun fotogramma %s dopo il cambio di strada: chi si collega adesso vedra' "
		       "l'ultima immagine buona, o nulla se non ce n'e' una",
		       vuole ? "sulla scheda" : "in memoria");

	g_mutex_unlock(&palco->montaggio);
}

/*
 * L'ultimo fotogramma, gia' sulla scheda e gia' della misura allineata.
 *
 * Restituisce un riferimento NUOVO, che il chiamante libera con
 * `av_frame_free`: cosi' il palco puo' sostituire il proprio senza aspettare
 * che la connessione abbia finito di codificare — e senza che nessuno dei due
 * tocchi memoria dell'altro.
 */
EsitoPalco palco_preleva_superficie(Palco *palco, AVFrame **fuori, guint64 *visto)
{
	EsitoPalco esito;

	g_mutex_lock(&palco->lucchetto);
	if (palco->generazione > *visto && palco->ultimo_gpu)
	{
		*fuori = av_frame_clone(palco->ultimo_gpu);
		*visto = palco->generazione;
		esito = *fuori ? PALCO_NUOVO : PALCO_NIENTE;
	}
	else if (palco->finita)
	{
		esito = PALCO_FINITA;
	}
	else
	{
		esito = PALCO_NIENTE;
	}
	g_mutex_unlock(&palco->lucchetto);
	return esito;
}

EsitoPalco palco_preleva(Palco *palco, Immagine *tela, guint64 *visto)
{
	EsitoPalco esito;

	g_mutex_lock(&palco->lucchetto);

	if (palco->generazione > *visto && palco->ultimo)
	{
		if (!palco->misura_segnalata &&
		    (palco->larghezza_arrivata != immagine_larghezza(tela) ||
		     palco->altezza_arrivata != immagine_altezza(tela)))
		{
			palco->misura_segnalata = TRUE;
			avviso("il fotogramma catturato e' %ux%u ma la tela e' %ux%u: la parte scoperta "
			       "resta grigia",
			       palco->larghezza_arrivata, palco->altezza_arrivata, immagine_larghezza(tela),
			       immagine_altezza(tela));
		}
		immagine_copia_fotogramma(tela, palco->ultimo, palco->passo, palco->larghezza_arrivata,
		                          palco->altezza_arrivata);
		*visto = palco->generazione;
		esito = PALCO_NUOVO;
	}
	else if (palco->finita)
	{
		esito = PALCO_FINITA;
	}
	else
	{
		/* Condizione normale: su un desktop fermo Mutter non manda nulla. */
		esito = PALCO_NIENTE;
	}

	g_mutex_unlock(&palco->lucchetto);
	return esito;
}
