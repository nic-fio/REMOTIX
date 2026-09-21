/*
 * 13-w3-input-wlr.c — ⭐ L'INPUT SU WLROOTS, dal contratto al lato che riceve.
 *
 *   bash banchi/13-w3-input-wlr.sh [tutto|taglio|caduta|scorciatoia]
 *
 * Fase 13, incremento 3.  Guida `input.h` (aperto con `input_apri_wlr()`) contro
 * un labwc headless PRIVATO, e il testimone `06-b33-testimone.c` stampa quel
 * che il compositore consegna a una finestra qualunque.  ⚠ Gira sul PORTATILE
 * (labwc 0.8.3 di Trixie), non sulla macchina di prova e non in una sessione
 * XFCE intera: misura il trasporto, non il desktop.
 *
 * ⛔ Compila gli STESSI sorgenti del prodotto (`input.c`, `wlr_input.c`,
 *    `tastiera.c`, `registro.c`); i simboli di libei che `input.c` nomina e che
 *    su wlroots non si toccano sono sostituiti qui sotto da stub che tornano -1.
 *
 * Il driver scrive i passi su stderr (`== …`); il confronto col testimone si fa
 * a occhio, riga per riga — ⚠ non c'e' un verdetto automatico, ed e' detto.
 */
#include <glib.h>
#include <linux/input-event-codes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include "input.h"

/* stub dei simboli libei di input.c che su wlroots non si toccano */
void *mutter_mapping_id_pubblicato(void *s) { return NULL; }
int mutter_eis_fd(void *s) { return -1; }
int mutter_eis_riattacca(void *s, void **e) { return -1; }
int kwin_eis_fd(void *k, void **e) { return -1; }
int kwin_eis_riattacca(void *k, void **e) { return -1; }
void input_conto(const Input *in, unsigned *tasti, unsigned *pulsanti, unsigned *rp,
                 unsigned *rt, int *pronto);

static Input *in;

static void gira(int ms)
{
	for (int i = 0; i < ms / 10; i++) {
		input_gira(in);
		usleep(10000);
	}
}

#define PASSO(...) do { fprintf(stderr, "== "); fprintf(stderr, __VA_ARGS__); fprintf(stderr, "\n"); } while (0)

int main(int argc, char **argv)
{
	char *err = NULL;
	const char *scena = argc > 1 ? argv[1] : "tutto";

	in = input_apri_wlr(1280, 720, &err);
	if (!in) {
		fprintf(stderr, "APRI FALLITA: %s\n", err);
		return 1;
	}
	gira(300);

	if (!strcmp(scena, "scorciatoia")) {
		PASSO("Alt+F4 dal client: lo prende labwc (chiude la finestra)?");
		input_posizione(in, KEY_LEFTALT, 1);
		input_posizione(in, KEY_F4, 1);
		input_posizione(in, KEY_F4, 0);
		input_posizione(in, KEY_LEFTALT, 0);
		gira(500);
		input_chiudi(in);
		return 0;
	}
	if (!strcmp(scena, "taglio")) {
		PASSO("premo BTN_LEFT e Maiusc, poi TAGLIO solo il mio socket (labwc resta vivo)");
		input_puntatore(in, 100, 100);
		input_pulsante(in, BTN_LEFT, 1);
		input_posizione(in, KEY_LEFTSHIFT, 1);
		gira(100);
		shutdown(input_descrittore(in), SHUT_RDWR);
		gira(1500);
		PASSO("ora un clic fresco a 300,300: deve arrivare");
		input_puntatore(in, 300, 300);
		input_pulsante(in, BTN_LEFT, 1);
		input_pulsante(in, BTN_LEFT, 0);
		gira(300);
		input_chiudi(in);
		return 0;
	}
	if (!strcmp(scena, "caduta")) {
		PASSO("premo BTN_LEFT e aspetto che mi si uccida la connessione");
		input_puntatore(in, 100, 100);
		input_pulsante(in, BTN_LEFT, 1);
		for (int i = 0; i < 1000; i++) { /* 10 s */
			input_gira(in);
			usleep(10000);
		}
		PASSO("ora un clic: deve riattaccarsi");
		input_pulsante(in, BTN_LEFT, 1);
		input_pulsante(in, BTN_LEFT, 0);
		gira(300);
		input_chiudi(in);
		return 0;
	}

	PASSO("puntatore a 640,360 e a 1279,719 e a 5000,5000 (saturato)");
	input_puntatore(in, 640, 360);
	gira(50);
	input_puntatore(in, 1279, 719);
	gira(50);
	input_puntatore(in, 5000, 5000);
	gira(50);
	input_puntatore(in, 640, 360);
	gira(50);

	PASSO("clic sinistro; poi DOPPIONE (premuto due volte, rilasciato una)");
	input_pulsante(in, BTN_LEFT, 1);
	input_pulsante(in, BTN_LEFT, 0);
	gira(50);
	input_pulsante(in, BTN_LEFT, 1);
	input_pulsante(in, BTN_LEFT, 1);
	input_pulsante(in, BTN_LEFT, 0);
	gira(50);

	PASSO("Maiusc + A come posizioni");
	input_posizione(in, KEY_LEFTSHIFT, 1);
	input_posizione(in, KEY_A, 1);
	input_posizione(in, KEY_A, 0);
	input_posizione(in, KEY_LEFTSHIFT, 0);
	gira(50);

	PASSO("lettera 'A' e lettera '@' (disposizione di partenza)");
	fprintf(stderr, "   esito A = %d\n", input_lettera(in, 'A'));
	fprintf(stderr, "   esito @ = %d\n", input_lettera(in, '@'));
	gira(50);

	PASSO("BlocMaiusc premuto e ripetuto (doppione): deve bloccare UNA volta");
	input_posizione(in, KEY_CAPSLOCK, 1);
	input_posizione(in, KEY_CAPSLOCK, 1);
	input_posizione(in, KEY_CAPSLOCK, 1);
	input_posizione(in, KEY_CAPSLOCK, 0);
	gira(50);
	input_posizione(in, KEY_CAPSLOCK, 1);
	input_posizione(in, KEY_CAPSLOCK, 0);
	gira(50);

	PASSO("rotella: +120 (su), -120 (giu'), +60, +60, orizzontale +120");
	input_rotella(in, 0, 120);
	gira(50);
	input_rotella(in, 0, -120);
	gira(50);
	input_rotella(in, 0, 60);
	gira(50);
	input_rotella(in, 0, 60);
	gira(50);
	input_rotella(in, 120, 0);
	gira(50);

	PASSO("disposizione «de»: poi la lettera 'z' deve andare sul tasto 21 (Y di us)");
	fprintf(stderr, "   disposizione = %d\n", input_disposizione(in, "de"));
	gira(100);
	fprintf(stderr, "   esito z = %d\n", input_lettera(in, 'z'));
	gira(50);
	PASSO("disposizione «de» di nuovo: non deve rimandarla");
	fprintf(stderr, "   disposizione = %d\n", input_disposizione(in, "de"));
	PASSO("disposizione «xx(yy)»: inesistente");
	fprintf(stderr, "   disposizione = %d\n", input_disposizione(in, "xx(yy)"));
	gira(50);

	PASSO("la tela cambia 1920x1080: il centro nuovo deve cadere al centro");
	input_ritela(in, 1920, 1080);
	input_puntatore(in, 960, 540);
	gira(50);
	input_puntatore(in, 480, 270);
	gira(50);

	PASSO("Ctrl giu' e BTN_LEFT giu', poi input_chiudi SENZA rilascia_tutto");
	input_posizione(in, KEY_LEFTCTRL, 1);
	input_pulsante(in, BTN_LEFT, 1);
	gira(50);
	{
		unsigned t, p;
		int pronto;
		input_conto(in, &t, &p, NULL, NULL, &pronto);
		fprintf(stderr, "   conto: tasti %u pulsanti %u pronto %d\n", t, p, pronto);
	}
	input_chiudi(in);
	PASSO("fine");
	return 0;
}
