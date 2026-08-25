/* ===========================================================================
 * 10-b90-getto — ⭐ IL GETTO DI BANDA **NOTA**, che serve a due cose diverse
 *                e per questo esiste una volta sola.
 *
 *   1. ⛔ **TARARE IL METRO** (`LEZIONI.md` §1.33).  Si inietta un ritmo
 *      DICHIARATO per un tempo DICHIARATO e si guarda se il metro lo ritrova:
 *      pendenza e costante, come si e' fatto in fase 9 per lo sfalso
 *      audio-video.  Un metro non tarato produce numeri, non misure.
 *   2. ⭐ **MISURARE IL TETTO DEL FILO**, non dedurlo.  Una scheda che dichiara
 *      10 Gbit/s non porta 10 Gbit/s di datagrammi in spazio utente: il tetto
 *      vero e' la CPU che li impacchetta.  A ritmo zero questo getto spara
 *      quanto puo' e dice quanto e' passato davvero.
 *
 * ⛔ PERCHE' IN C E NON IN PYTHON.  Il getto deve essere **piu' veloce di quel
 *    che misura**, o misura se stesso.  Python con `sendto` in un ciclo arriva
 *    a qualche decina di Mbit/s con datagrammi da 1200 byte: sarebbe il collo,
 *    e il numero uscito sarebbe la velocita' dell'interprete con la faccia
 *    della velocita' della macchina.  `sendmmsg` manda 64 datagrammi per
 *    chiamata di sistema, e il collo torna dov'e' giusto che sia.
 *
 * ⛔ LA PORTA D'ORIGINE SI FISSA (`--porta-mia`).  Il metro di `10-b90-filo.py`
 *    separa le sessioni **per porta del cliente**: un getto che prende una
 *    porta a caso non si distingue dagli altri, e la taratura per sessione non
 *    si potrebbe fare.
 *
 * ⚠ IL LIMITE DICHIARATO: questo getto manda UDP nudo.  Non cifra, non tiene
 *   stato, non ritrasmette.  ⇒ Il suo tetto e' un **limite SUPERIORE** per
 *   QUIC, non il tetto di QUIC: la differenza fra i due e' il costo del
 *   protocollo, e va scritta come tale.
 *
 * Compilazione (DENTRO il contenitore, che e' dove sta gcc):
 *     gcc -O2 -pthread -o 10-b90-getto 10-b90-getto.c
 *
 * Uso:
 *     10-b90-getto --dest 127.0.0.1:9 --porta-mia 30001 \
 *                  --carico 1200 --mbit 20 --secondi 10 --fili 1
 *     10-b90-getto --dest 127.0.0.1:9 --porta-mia 30001 \
 *                  --carico 1200 --mbit 0  --secondi 5  --fili 4   # a tutta
 *
 * Scrive sullo stdout **una riga JSON sola**, perche' chi lo chiama e' un
 * copione e non un umano.
 * ===========================================================================
 */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#define MASSA 64 /* datagrammi per `sendmmsg` */

struct filo {
	int indice;
	const char *ip;
	int porta_dest;
	int porta_mia; /* 0 = a caso */
	int carico;
	double mbit;   /* 0 = a tutta */
	double secondi;
	/* i risultati */
	long long datagrammi;
	long long byte_carico;
	double reale_s;
	int errore;
	int errno_v;
};

static double adesso(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
}

static void dormi(double s)
{
	struct timespec t;
	if (s <= 0)
		return;
	t.tv_sec = (time_t)s;
	t.tv_nsec = (long)((s - (double)t.tv_sec) * 1e9);
	nanosleep(&t, NULL);
}

static void *corri(void *v)
{
	struct filo *f = v;
	int s, i;
	struct sockaddr_in dest, mio;
	struct mmsghdr msg[MASSA];
	struct iovec iov[MASSA];
	char *buf;
	double t0, t1, fine;
	/* ⭐ Il secchio: quanti byte ho «diritto» di aver mandato a questo punto.
	 *    ⛔ Non si dorme «un tot per datagramma»: `nanosleep` ha una grana di
	 *    decine di microsecondi e a 20 Mbit/s si sbaglierebbe del 50 %.  Si
	 *    guarda l'OROLOGIO e si dorme solo quando si e' in anticipo. */
	double byte_al_s, dovuti;

	f->errore = 0;
	f->datagrammi = 0;
	f->byte_carico = 0;

	s = socket(AF_INET, SOCK_DGRAM, 0);
	if (s < 0) {
		f->errore = 1;
		f->errno_v = errno;
		return NULL;
	}
	i = 4 * 1024 * 1024;
	setsockopt(s, SOL_SOCKET, SO_SNDBUF, &i, sizeof(i));

	if (f->porta_mia > 0) {
		memset(&mio, 0, sizeof(mio));
		mio.sin_family = AF_INET;
		mio.sin_addr.s_addr = htonl(INADDR_ANY);
		mio.sin_port = htons((uint16_t)(f->porta_mia + f->indice));
		if (bind(s, (struct sockaddr *)&mio, sizeof(mio)) < 0) {
			f->errore = 2;
			f->errno_v = errno;
			close(s);
			return NULL;
		}
	}

	memset(&dest, 0, sizeof(dest));
	dest.sin_family = AF_INET;
	dest.sin_port = htons((uint16_t)f->porta_dest);
	if (inet_pton(AF_INET, f->ip, &dest.sin_addr) != 1) {
		f->errore = 3;
		close(s);
		return NULL;
	}
	/* ⛔ `connect` su un socket UDP: cosi' `sendmmsg` non rifa' la rotta a ogni
	 *    datagramma, e il getto misura la rete e non la tabella di routing. */
	if (connect(s, (struct sockaddr *)&dest, sizeof(dest)) < 0) {
		f->errore = 4;
		f->errno_v = errno;
		close(s);
		return NULL;
	}

	buf = malloc((size_t)f->carico);
	if (!buf) {
		f->errore = 5;
		close(s);
		return NULL;
	}
	/* ⚠ Riempito di rumore, non di zeri: se un giorno qualcuno ci mettesse una
	 *   compressione in mezzo, gli zeri direbbero una banda che non c'e'. */
	for (i = 0; i < f->carico; i++)
		buf[i] = (char)(i * 31 + 7);

	memset(msg, 0, sizeof(msg));
	for (i = 0; i < MASSA; i++) {
		iov[i].iov_base = buf;
		iov[i].iov_len = (size_t)f->carico;
		msg[i].msg_hdr.msg_iov = &iov[i];
		msg[i].msg_hdr.msg_iovlen = 1;
	}

	byte_al_s = f->mbit > 0 ? f->mbit * 1e6 / 8.0 : 0;
	t0 = adesso();
	fine = t0 + f->secondi;

	while (adesso() < fine) {
		int n = sendmmsg(s, msg, MASSA, 0);
		if (n < 0) {
			if (errno == ENOBUFS || errno == EAGAIN || errno == EINTR) {
				/* ⚠ La coda del socket e' piena: non e' un errore, e'
				 *   il segnale che siamo al tetto.  Si respira. */
				dormi(0.0002);
				continue;
			}
			f->errore = 6;
			f->errno_v = errno;
			break;
		}
		f->datagrammi += n;
		f->byte_carico += (long long)n * f->carico;

		if (byte_al_s > 0) {
			dovuti = (adesso() - t0) * byte_al_s;
			if ((double)f->byte_carico > dovuti) {
				double avanti = ((double)f->byte_carico - dovuti) / byte_al_s;
				dormi(avanti);
			}
		}
	}
	t1 = adesso();
	f->reale_s = t1 - t0;
	free(buf);
	close(s);
	return NULL;
}

int main(int argc, char **argv)
{
	char ip[64] = "127.0.0.1";
	int porta_dest = 9, porta_mia = 0, carico = 1200, fili = 1, i;
	double mbit = 0, secondi = 5;
	struct filo f[64];
	pthread_t th[64];
	long long dat = 0, byt = 0;
	double reale = 0;
	int errore = 0, errno_v = 0;

	for (i = 1; i < argc; i++) {
		if (!strcmp(argv[i], "--dest") && i + 1 < argc) {
			char *p = strchr(argv[++i], ':');
			if (!p) {
				fprintf(stderr, "⛔ --dest vuole IP:PORTA\n");
				return 2;
			}
			*p = 0;
			snprintf(ip, sizeof(ip), "%s", argv[i]);
			porta_dest = atoi(p + 1);
		} else if (!strcmp(argv[i], "--porta-mia") && i + 1 < argc) {
			porta_mia = atoi(argv[++i]);
		} else if (!strcmp(argv[i], "--carico") && i + 1 < argc) {
			carico = atoi(argv[++i]);
		} else if (!strcmp(argv[i], "--mbit") && i + 1 < argc) {
			mbit = atof(argv[++i]);
		} else if (!strcmp(argv[i], "--secondi") && i + 1 < argc) {
			secondi = atof(argv[++i]);
		} else if (!strcmp(argv[i], "--fili") && i + 1 < argc) {
			fili = atoi(argv[++i]);
		} else {
			fprintf(stderr, "⛔ non capisco «%s»\n", argv[i]);
			return 2;
		}
	}
	if (fili < 1)
		fili = 1;
	if (fili > 64)
		fili = 64;
	if (carico < 1 || carico > 60000) {
		fprintf(stderr, "⛔ --carico fuori misura\n");
		return 2;
	}

	for (i = 0; i < fili; i++) {
		memset(&f[i], 0, sizeof(f[i]));
		f[i].indice = i;
		f[i].ip = ip;
		f[i].porta_dest = porta_dest;
		f[i].porta_mia = porta_mia;
		f[i].carico = carico;
		/* ⛔ Il ritmo si DIVIDE fra i fili: `--mbit 20 --fili 4` vuol dire 20
		 *    in tutto, non 80.  Un getto che moltiplica di nascosto tarerebbe
		 *    il metro sul numero sbagliato. */
		f[i].mbit = mbit > 0 ? mbit / fili : 0;
		f[i].secondi = secondi;
	}
	for (i = 0; i < fili; i++)
		pthread_create(&th[i], NULL, corri, &f[i]);
	for (i = 0; i < fili; i++) {
		pthread_join(th[i], NULL);
		dat += f[i].datagrammi;
		byt += f[i].byte_carico;
		if (f[i].reale_s > reale)
			reale = f[i].reale_s;
		if (f[i].errore && !errore) {
			errore = f[i].errore;
			errno_v = f[i].errno_v;
		}
	}

	/* ⭐ IL NUMERO CHE SERVE A CHI TARA: quanti byte **di rete** ho fatto
	 *    passare, cioe' carico + 8 (UDP) + 20 (IP).  E' la stessa unita' che
	 *    contano `nft` e `statistics/tx_bytes` dell'interfaccia: `[M]` 24
	 *    agosto 2026, 1000 datagrammi da 1000 byte = 1 028 000 byte per
	 *    tutt'e due.  ⚠ Su un filo di RAME ci sarebbero in piu' 38 byte per
	 *    pacchetto (intestazione ethernet, FCS, preambolo e spazio fra
	 *    pacchetti) che NESSUNO dei due contatori vede. */
	printf("{\"datagrammi\":%lld,\"byte_carico\":%lld,\"byte_L3\":%lld,"
	       "\"secondi\":%.6f,\"carico\":%d,\"fili\":%d,\"mbit_chiesti\":%.6f,"
	       "\"mbit_carico\":%.6f,\"mbit_L3\":%.6f,\"errore\":%d,\"errno\":%d}\n",
	       dat, byt, byt + dat * 28LL, reale, carico, fili, mbit,
	       reale > 0 ? (double)byt * 8.0 / reale / 1e6 : 0.0,
	       reale > 0 ? (double)(byt + dat * 28LL) * 8.0 / reale / 1e6 : 0.0,
	       errore, errno_v);
	return errore ? 1 : 0;
}
