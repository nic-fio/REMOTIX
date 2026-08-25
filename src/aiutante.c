/*
 * aiutante.c — il processo che interroga PAM al posto del filo unico.
 *
 * La ragione, i tre piani e l'invariante I3 stanno per esteso in `aiutante.h`.
 * Qui ci sono le scelte che si vedono solo nel codice.
 */
#include "aiutante.h"

#include "registro.h"

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

/* ⛔ Dichiarata qui e non inclusa: `autenticazione.c` non ha un'intestazione, e
 *    la stessa riga sta gia' in `webtransport.c`.  ⚠ E' l'UNICA funzione che
 *    tocca `libpam` in tutto il prodotto, e da oggi la chiama **solo il
 *    nipote**: nel processo che serve non viene piu' eseguita mai. */
bool rcp_autentica(const char *utente, const char *parola);

/* ⛔⛔ QUESTO NUMERO NON E' IL TETTO DELLE SESSIONI, E NON DEVE SEGUIRLO — 25
 *      agosto 2026, e la riga qui sopra diceva il contrario.
 *
 *      Diceva: *«non e' un numero arbitrario: e' lo stesso `MAX_ATTACCATE` di
 *      `rcp.c`»*.  ⛔ **Non lo era** — erano due letterali indipendenti — e
 *      soprattutto **non doveva esserlo**: sono due grandezze diverse.
 *
 *        · `RCP_TETTO_SESSIONI` conta gli utenti **serviti**, e una sessione
 *          dura ore;
 *        · questo conta le autenticazioni **in volo nello stesso istante**, e
 *          una pratica dura da 1,0 a 2,2 s (`[M]` B8).
 *
 *      ⇒ Con ZERO sessioni attive si possono avere diciassette pratiche in
 *        volo — bastano diciassette persone che premono «entra» insieme — e il
 *        diciassettesimo riceverebbe `CREDENZIALI_ERRATE`, ⛔ **indistinguibile
 *        da una parola sbagliata** (rilievo **R10-A7**).  E per il verso
 *        opposto: un tetto di sessioni alto non ha nessun motivo di allargare
 *        una coda che si svuota in due secondi.
 *
 * ⛔ Percio' resta un numero SUO, scritto qui, e questo riquadro esiste perche'
 *    il giorno in cui `RCP_TETTO_SESSIONI` diventera' configurabile qualcuno
 *    aprira' questo file per «allinearlo».  Non si allinea: si dimensiona sul
 *    picco di ARRIVI, che e' un'altra misura e oggi non c'e'.
 *
 * ⚠ Oltre il tetto `aiutante_chiedi` dice di no — un no e' una risposta
 *   conforme a I3, mentre una coda senza fondo sarebbe un modo di far nascere
 *   processi finche' la macchina regge. */
#define MAX_IN_VOLO 16

/* ⛔ Quanto si aspetta una risposta prima di chiamarla «no».  PAM, misurata,
 * sta fra 1,0 e 2,2 s: otto secondi sono quattro volte il caso peggiore
 * conosciuto.  ⚠ E c'e' una SECONDA rete, in `rcp.c` (`TETTO_VERDETTO`): due
 * reti indipendenti perche' questa vive nel processo che potrebbe essere
 * proprio quello guasto. */
#define SCADENZA_MS 8000

/* ⛔ Il nipote non puo' vivere per sempre: un modulo PAM che si impianta su una
 * rete che non risponde terrebbe in piedi un processo a ogni tentativo.  Venti
 * secondi, cioe' piu' della scadenza del padre: cosi' il «no» arriva sempre
 * dalla scadenza (che e' un fatto scritto nel registro) e non da un segnale. */
#define NIPOTE_ALLARME_S 20

struct richiesta {
	uint64_t pratica;
	char utente[257];
	char parola[1025];
};

struct risposta {
	uint64_t pratica;
	uint8_t esito; /* ⛔ 1 e SOLO 1 vuol dire ammesso */
};

struct volo {
	uint64_t pratica;
	uint64_t scade;
	/* ⛔ Il NOME dell'utente, e non la sua parola: quello serve al padre per
	 *    generare il figlio quando la risposta e' «si'» (`figlio.h`), questa e'
	 *    gia' azzerata da §4.4 prima che questa riga esista. */
	char utente[257];
};

struct aiutante {
	int fd;         /* -1 quando lo smistatore e' morto o non e' mai nato */
	pid_t figlio;
	uint64_t prossima_pratica;
	struct volo volo[MAX_IN_VOLO];
	int nvolo;
};

/* ------------------------------------------------------------------------ */
/* IL NIPOTE — una transazione PAM sola, poi muore.                          */

static void nipote(int fd, const struct richiesta *r)
{
	struct risposta out;
	bool ok;

	/* ⛔ L'allarme si arma PRIMA di chiamare PAM: armarlo dopo sarebbe armarlo
	 *    quando il caso per cui esiste e' gia' successo. */
	alarm(NIPOTE_ALLARME_S);

	ok = rcp_autentica(r->utente, r->parola);

	out.pratica = r->pratica;
	/* ⛔ Il solo posto del programma in cui nasce un «si'», ed e' scritto in
	 *    modo che un valore diverso da `PAM_SUCCESS` non ci possa arrivare:
	 *    `rcp_autentica()` parte da `ammesso = false`. */
	out.esito = ok ? 1u : 0u;
	/* ⚠ L'esito si scrive e basta: se la `send` fallisce, il padre non
	 *   ricevera' niente e la pratica scadra' — cioe' un «no».  Non si
	 *   riprova, e non si scrive un esito «forse». */
	(void)send(fd, &out, sizeof out, MSG_NOSIGNAL);
	_exit(0);
}

/* ------------------------------------------------------------------------ */
/* LO SMISTATORE — non chiama mai PAM: legge e forca.                        */

static void smistatore(int fd)
{
	struct richiesta r;

	/* ⛔ Se il padre muore, questo processo muore con lui.  Senza, uno
	 *    spegnimento brusco del server lascerebbe un orfano attaccato a un
	 *    socket che non legge piu' nessuno — e nessun file direbbe chi e'. */
	prctl(PR_SET_PDEATHSIG, SIGTERM);

	/* ⛔ I gestori del padre non valgono qui: il padre esce dal suo ciclo
	 *    quando `si_ferma` diventa 1, e questo processo quella variabile non
	 *    la guarda mai.  Con il gestore ereditato un `SIGTERM` non lo
	 *    fermerebbe, e chi spegne il server aspetterebbe un figlio immortale. */
	signal(SIGTERM, SIG_DFL);
	signal(SIGINT, SIG_DFL);
	/* ⭐ E i nipoti si raccolgono da soli: con `SIGCHLD` a `SIG_IGN` il nucleo
	 *    non lascia zombi (POSIX 2001), e questo processo non ha nessun ciclo
	 *    di `waitpid` da dimenticare. */
	signal(SIGCHLD, SIG_IGN);

	for (;;) {
		ssize_t letti = recv(fd, &r, sizeof r, 0);
		if (letti == 0)
			_exit(0); /* il padre ha chiuso: qui non c'e' piu' niente da fare */
		if (letti < 0) {
			if (errno == EINTR)
				continue;
			_exit(1);
		}
		/* ⛔ Una richiesta di lunghezza sbagliata non si «aggiusta»: si butta,
		 *    e la pratica scadra' dal lato del padre come un no.  Indovinare
		 *    che cosa mancasse e' precisamente l'indulgenza che nasconde. */
		if (letti != (ssize_t)sizeof r) {
			memset(&r, 0, sizeof r);
			continue;
		}
		/* ⚠ E la stringa si chiude a forza: quel che e' arrivato deve essere
		 *   quel che si giudica, e un buffer senza zero finale farebbe leggere
		 *   a PAM byte che non erano nel messaggio. */
		r.utente[sizeof r.utente - 1] = 0;
		r.parola[sizeof r.parola - 1] = 0;

		pid_t p = fork();
		if (p == 0)
			nipote(fd, &r); /* non torna */
		if (p < 0) {
			/* ⛔ Non si ripiega chiamando PAM QUI: bloccherebbe lo smistatore,
			 *    e con lui tutte le altre pratiche.  Si tace, e il padre
			 *    trasformera' il silenzio in un no alla scadenza. */
		}
		/* ⛔ §4.4: la parola si azzera appena servita.  Questa e' la copia
		 *    dello smistatore, e vive il tempo di una `fork`. */
		memset(&r, 0, sizeof r);
	}
}

/* ------------------------------------------------------------------------ */
/* IL PADRE                                                                  */

aiutante *aiutante_accendi(void)
{
	int sv[2];
	aiutante *a;

	/* ⛔ `SOCK_SEQPACKET`: i confini dei messaggi li tiene il nucleo.  Vedi il
	 *    riquadro di `aiutante.h` — con uno stream l'inquadramento sarebbe
	 *    nostro, e un difetto li' dentro vorrebbe dire «la risposta di un
	 *    altro», cioe' I3 rotta da un errore di lettura. */
	if (socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv) != 0) {
		registro_dice(REG_AVVIO,
		              "⛔ l'aiutante di PAM NON si accende: socketpair: %s.  "
		              "Ogni autenticazione sara' un NO (invariante I3), e il "
		              "server lo dira' a ogni tentativo.",
		              strerror(errno));
		return NULL;
	}

	a = (aiutante *)calloc(1, sizeof *a);
	if (!a) {
		close(sv[0]);
		close(sv[1]);
		return NULL;
	}

	a->figlio = fork();
	if (a->figlio < 0) {
		registro_dice(REG_AVVIO,
		              "⛔ l'aiutante di PAM NON si accende: fork: %s.  Ogni "
		              "autenticazione sara' un NO (invariante I3).",
		              strerror(errno));
		close(sv[0]);
		close(sv[1]);
		free(a);
		return NULL;
	}
	if (a->figlio == 0) {
		close(sv[0]);
		smistatore(sv[1]); /* non torna */
		_exit(1);
	}

	close(sv[1]);
	a->fd = sv[0];
	a->prossima_pratica = 1;
	/* ⛔ Non bloccante: e' tutto il punto di questo file.  Una `send` che
	 *    aspetta e' un'attesa dentro il ciclo asincrono — `CODER.md` §4.4 —
	 *    cioe' il difetto spostato invece che curato. */
	fcntl(a->fd, F_SETFL, O_NONBLOCK);

	registro_dice(REG_AVVIO,
	              "⭐ aiutante di PAM acceso: pid %ld, socketpair anonimo "
	              "SEQPACKET.  Da qui in poi il ciclo poll NON chiama piu' PAM "
	              "(DECISIONI.md §1.10)",
	              (long)a->figlio);
	return a;
}

void aiutante_spegni(aiutante *a)
{
	if (!a)
		return;
	if (a->fd >= 0)
		close(a->fd);
	if (a->figlio > 0) {
		/* ⚠ Chiudere il socket basterebbe (lo smistatore legge 0 ed esce), ma
		 *   «basterebbe» non e' «l'ho fatto»: il segnale e la raccolta
		 *   rendono lo spegnimento un fatto osservabile invece di una corsa. */
		kill(a->figlio, SIGTERM);
		waitpid(a->figlio, NULL, 0);
	}
	free(a);
}

int aiutante_descrittore(const aiutante *a)
{
	return a ? a->fd : -1;
}

int aiutante_in_volo(const aiutante *a)
{
	return a ? a->nvolo : 0;
}

static void volo_togli(aiutante *a, int i)
{
	a->volo[i] = a->volo[a->nvolo - 1];
	a->nvolo--;
}

bool aiutante_chiedi(aiutante *a, const char *utente, const char *parola,
                     uint64_t ora_ms, uint64_t *pratica)
{
	struct richiesta r;
	ssize_t scritti;
	uint64_t mia;

	*pratica = 0;
	if (!a || a->fd < 0 || !utente || !parola)
		return false;
	if (a->nvolo >= MAX_IN_VOLO) {
		registro_dice(REG_RCP,
		              "⛔ %d verifiche PAM gia' in volo: questa NON parte, e "
		              "chi ha chiesto ricevera' un NO (I3: il fallimento e' un "
		              "no, non un forse)",
		              a->nvolo);
		return false;
	}

	mia = a->prossima_pratica;
	memset(&r, 0, sizeof r);
	r.pratica = mia;
	/* ⛔ `snprintf` e non `strcpy`: gli intervalli li ha gia' fatti rispettare
	 *    `rcp.c` (§4.4: utente 1..256, parola 1..1024), e questo e' il secondo
	 *    muro — quello che regge anche se il primo cambia. */
	snprintf(r.utente, sizeof r.utente, "%s", utente);
	snprintf(r.parola, sizeof r.parola, "%s", parola);

	scritti = send(a->fd, &r, sizeof r, MSG_NOSIGNAL);
	/* ⛔ §4.4: la parola si azzera appena servita.  Questa e' la copia del
	 *    mittente, e vive il tempo di una `send`.  ⚠ E il numero della pratica
	 *    e' gia' al sicuro in `mia`: rileggerlo da `r` dopo il `memset` sarebbe
	 *    leggere lo zero che ci abbiamo appena messo — e la risposta non
	 *    troverebbe piu' la sua pratica in volo. */
	memset(&r, 0, sizeof r);

	if (scritti != (ssize_t)sizeof r) {
		registro_dice(REG_RCP,
		              "⛔ la domanda a PAM non e' partita (%zd byte su %zu: "
		              "%s): NON si aspetta e non si indovina — chi ha chiesto "
		              "riceve un NO",
		              scritti, sizeof r, strerror(errno));
		return false;
	}

	a->volo[a->nvolo].pratica = mia;
	a->volo[a->nvolo].scade = ora_ms + SCADENZA_MS;
	snprintf(a->volo[a->nvolo].utente, sizeof a->volo[a->nvolo].utente, "%s",
	         utente);
	a->nvolo++;
	*pratica = mia;
	a->prossima_pratica++;
	return true;
}

/* ⛔ La risposta si accetta SOLO se e' di una pratica che sta davvero in volo.
 * Una risposta per una pratica sconosciuta — o la seconda risposta per la
 * stessa — si scarta e si scrive: e' l'unico modo per cui «ho ricevuto due
 * verdetti» non diventi «vince l'ultimo». */
static bool volo_consuma(aiutante *a, uint64_t pratica, char *utente,
                         size_t cap)
{
	for (int i = 0; i < a->nvolo; i++) {
		if (a->volo[i].pratica == pratica) {
			/* ⛔ Il nome si copia PRIMA di togliere la pratica: `volo_togli()`
			 *    ci scrive sopra l'ultima della tabella, e leggerlo dopo
			 *    vorrebbe dire consegnare il nome di un altro utente — che qui
			 *    e' il difetto peggiore possibile. */
			if (utente && cap)
				snprintf(utente, cap, "%s", a->volo[i].utente);
			volo_togli(a, i);
			return true;
		}
	}
	if (utente && cap)
		utente[0] = 0;
	return false;
}

static void muore(aiutante *a, const char *perche, AiutanteVerdetto consegna,
                  void *ctx)
{
	registro_dice(REG_RCP,
	              "⛔ l'aiutante di PAM non c'e' piu' (%s): le %d verifiche in "
	              "volo diventano NO, e ogni tentativo successivo sara' un NO "
	              "(invariante I3).  ⚠ Non e' «parola sbagliata»: e' «PAM non "
	              "ha potuto giudicare», e il server non se lo tiene per se'.",
	              perche, a->nvolo);
	if (a->fd >= 0) {
		close(a->fd);
		a->fd = -1;
	}
	/* ⛔⭐ E LO SI RACCOGLIE, SUBITO — trovato il 12 agosto 2026 dal banco
	 *     `02-pam-i3.py`, che ha ammazzato l'aiutante e poi si e' sentito
	 *     rispondere «il pid e' ancora vivo dopo SIGKILL».
	 *
	 *     Non era vivo: era uno **zombie**.  Il padre non lo raccoglieva fino
	 *     a `aiutante_spegni()`, cioe' fino allo spegnimento del server, e in
	 *     `/proc` uno zombie e un processo vivo hanno **la stessa faccia**.
	 *
	 * ⚠ Il danno non era la voce di troppo nella tabella dei processi: era che
	 *   chi diagnostica — o un banco — non poteva distinguere «l'aiutante e'
	 *   morto» da «l'aiutante non muore».  E' `LEZIONI.md` §1.9 applicata ai
	 *   processi: due fatti diversi con lo stesso aspetto.
	 *
	 * ⛔ `WNOHANG`: qui si sta dentro il ciclo asincrono, e `CODER.md` §4.4
	 *    vieta di aspettare.  Se non fosse ancora finito si riprova al giro
	 *    dopo, e comunque `aiutante_spegni()` chiude il conto. */
	if (a->figlio > 0 && waitpid(a->figlio, NULL, WNOHANG) == a->figlio) {
		registro_dice(REG_RCP,
		              "⭐ e l'aiutante %ld e' stato raccolto: da adesso «morto» "
		              "e «vivo» non hanno piu' la stessa faccia in /proc",
		              (long)a->figlio);
		a->figlio = 0;
	}
	while (a->nvolo > 0) {
		uint64_t p = a->volo[0].pratica;
		char chi[257];
		snprintf(chi, sizeof chi, "%s", a->volo[0].utente);
		volo_togli(a, 0);
		if (consegna)
			consegna(ctx, p, false, chi);
	}
}

void aiutante_muovi(aiutante *a, AiutanteVerdetto consegna, void *ctx)
{
	if (!a || a->fd < 0)
		return;
	for (;;) {
		struct risposta ri;
		char chi[257];
		ssize_t letti = recv(a->fd, &ri, sizeof ri, 0);
		if (letti == 0) {
			muore(a, "il socket si e' chiuso dal suo lato", consegna, ctx);
			return;
		}
		if (letti < 0) {
			if (errno == EINTR)
				continue;
			if (errno == EAGAIN || errno == EWOULDBLOCK)
				return; /* niente altro da leggere adesso */
			muore(a, strerror(errno), consegna, ctx);
			return;
		}
		if (letti != (ssize_t)sizeof ri) {
			/* ⛔ Un messaggio della lunghezza sbagliata non si interpreta.  La
			 *    pratica restera' in volo e scadra': cioe' un no. */
			registro_dice(REG_RCP,
			              "⛔ risposta dell'aiutante lunga %zd byte invece di "
			              "%zu: SCARTATA.  La pratica scadra', e la scadenza e' "
			              "un NO",
			              letti, sizeof ri);
			continue;
		}
		if (!volo_consuma(a, ri.pratica, chi, sizeof chi)) {
			registro_dice(REG_RCP,
			              "⛔ risposta per la pratica %llu, che non e' in volo "
			              "(gia' scaduta, o gia' risposta): SCARTATA",
			              (unsigned long long)ri.pratica);
			continue;
		}
		/* ⛔⭐ QUI, E SOLO QUI, UN «SI'» PUO' ENTRARE NEL SERVER — e passa per
		 *     un confronto con `1`, non per un `!= 0`: un byte sporco, un
		 *     residuo di memoria o un 255 sono un NO. */
		if (consegna)
			consegna(ctx, ri.pratica, ri.esito == 1u, chi);
	}
}

void aiutante_scaduti(aiutante *a, uint64_t ora_ms, AiutanteVerdetto consegna,
                      void *ctx)
{
	if (!a)
		return;
	for (int i = 0; i < a->nvolo;) {
		if (ora_ms >= a->volo[i].scade) {
			uint64_t p = a->volo[i].pratica;
			char chi[257];
			snprintf(chi, sizeof chi, "%s", a->volo[i].utente);
			volo_togli(a, i);
			registro_dice(REG_RCP,
			              "⛔ la pratica %llu non ha ricevuto risposta in %d ms: "
			              "il nipote e' morto o PAM si e' impiantata.  ⭐ La "
			              "scadenza vale NO (invariante I3), e NON conta come "
			              "tentativo fallito di §4.4-bis: un difetto nostro non "
			              "banna nessuno",
			              (unsigned long long)p, SCADENZA_MS);
			if (consegna)
				consegna(ctx, p, false, chi);
		} else {
			i++;
		}
	}
}
