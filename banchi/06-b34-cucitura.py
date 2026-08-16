#!/usr/bin/env python3
"""06-b34-cucitura.py — ⛔ LA CUCITURA DI §5-bis.7, PRONTA DA APPLICARE.

    python3 06-b34-cucitura.py /percorso/dell/albero        applica
    python3 06-b34-cucitura.py /percorso/dell/albero --leggi  dice solo se c'e'

===========================================================================
⛔⛔ PERCHE' QUESTO FILE ESISTE INVECE DI ESSERE UNA MODIFICA
===========================================================================

`DECISIONI.md` §5-bis.7 dice che la disposizione dichiarata dal client entra
nella sessione.  ⛔ Perche' ci entri, la stringa deve attraversare **un confine
di processo**: QUIC/RCP e i byte del client stanno nel PADRE, e `libei` — cioe'
la sessione dell'utente — sta nel FIGLIO.

⇒ La catena, per intero:

    rcp.c (ATTACCA / 0x0009)          ⭐ mio
      → gancio `disposizione`
      → webtransport.c                ⛔ NON mio
      → main.c                        ⛔ NON mio
      → figli_disposizione()          ⛔ NON mio (figlio.h / figlio.c)
      → MSG_DISPOSIZIONE sul socket
      → input_disposizione()          ⭐ mio
      → org.gnome.desktop.input-sources
      → Mutter ricompila la keymap
      → DEVICE_REMOVED + DEVICE_ADDED
      → leggi_keymap()                ⭐ mio — e rilegge, come gia' misurato

⛔ **Cinque file su otto non sono miei**, e `figlio.c` lo sta modificando la
   sottofase 6.3 **adesso**.  ⇒ Le mie tre parti stanno nel deposito e
   compilano da sole; questa e' la sesta, e viene consegnata invece che
   applicata di nascosto.

⭐ E il deposito resta COERENTE senza di lei, di proposito: i due ganci sono
   **opzionali**, e `rcp.c` senza di loro scrive
   *«RIPIEGO DICHIARATO (§5-bis.7): … questo server NON ha il gancio per
   applicarla»*.  ⛔ Non tace: e' `CODER.md` §4.2 — degradare, ma dichiarando.

⚠ Questo file e' anche il modo in cui la cucitura e' stata **misurata**:
  applicata alla copia sulla macchina di prova, il banco `06-b34` gira
  end-to-end.  Senza, i casi 2 e 6 restano al colore di ieri sera.
"""
import os
import sys

# (file, ancora, sostituzione, marca)
#
# ⛔⛔ LA MARCA DEV'ESSERE LA FIRMA DEL PEZZO, NON UN NOME CHE ALTRI SCRIVONO.
#     `[M]` 16 agosto 2026, e l'ho sbagliato DUE volte di fila: la marca serve a
#     non riapplicare un pezzo gia' applicato, ⛔ ma se e' una sottostringa di
#     quel che un ALTRO pezzo scrive, il primo che passa la rende «gia'
#     presente» e il secondo **non viene mai applicato**.
#     ⇒ Il sintomo e' un albero che non compila per una funzione o una
#       variabile «undeclared» — cioe' un guasto che sembra del padrone del
#       file e invece e' della cucitura.
#     ⇒ Regola: la marca e' la RIGA che quel pezzo scrive di suo — «static char
#       disposizione_in_attesa», non «disposizione_in_attesa».
# ⛔ Ogni pezzo porta la sua ANCORA verbatim: se l'ancora non c'e' piu' — perche'
#    il padrone del file l'ha cambiata — la cucitura si FERMA e lo dice, invece
#    di applicare a meta' e lasciare un albero che non compila.
PEZZI = [

    # ------------------------------------------------------------------ #
    ("src/figlio.c",
     "	MSG_INPUT = 5,        /* padre → figlio */\n",
     "	MSG_INPUT = 5,        /* padre → figlio */\n"
     "	/* ⭐⭐ §5-bis.7 — LA DISPOSIZIONE DI TASTIERA, e attraversa il confine\n"
     "	 *     per la stessa ragione dell'input: la disposizione la applica la\n"
     "	 *     SESSIONE dell'utente, che sta in questo processo, e a chiederla e'\n"
     "	 *     il client, che parla col padre.\n"
     "	 * ⛔ E ha una busta SUA invece di viaggiare dentro `MSG_INPUT` come\n"
     "	 *    `RITELA`: il nome e' una stringa di 64 byte, e infilarla nel corpo\n"
     "	 *    dell'input vorrebbe dire pagarla su OGNI movimento del mouse —\n"
     "	 *    decine al secondo — per una cosa che succede una volta per attacco.\n"
     "	 *    `CODER.md` §1-bis: ogni byte in piu' sul cammino caldo si paga in\n"
     "	 *    ritardo, ed e' il numero che pesa piu' dei fotogrammi. */\n"
     "	MSG_DISPOSIZIONE = 6, /* padre → figlio */\n",
     "MSG_DISPOSIZIONE"),

    ("src/figlio.c",
     "/* ⛔ La forma del cursore che attraversa il confine.",
     "/* ⭐ §5-bis.7: il nome di una disposizione XKB — `it`, `de(neo)`.  ⚠ 64\n"
     " *    byte piu' il NUL, che e' il tetto che `RCP.md` §4.5 pone alla\n"
     " *    stringa: la busta e' a misura fissa perche' cosi' il figlio non deve\n"
     " *    fidarsi di una lunghezza che gli arriva dal socket. */\n"
     "struct corpo_disposizione {\n"
     "	char nome[65];\n"
     "};\n"
     "\n"
     "/* ⛔ La forma del cursore che attraversa il confine.",
     "struct corpo_disposizione"),

    # il lato PADRE: la funzione che manda ------------------------------- #
    ("src/figlio.c",
     "bool figli_input(figli *f, const char *utente, uint32_t id, uint8_t azione,",
     "/* ⭐⭐ §5-bis.7 — «METTI QUESTA DISPOSIZIONE NELLA SESSIONE».\n"
     " *\n"
     " * ⛔ Il difetto che questa funzione chiude, misurato dal banco `06-b34` il\n"
     " *    16 agosto 2026: la disposizione dichiarata in `ATTACCA` veniva\n"
     " *    convalidata e SCRITTA NEL REGISTRO, e li' finiva.  Riattaccandosi a\n"
     " *    una sessione `it` dichiarando `us` arrivavano `è` e `ò`, che su `us`\n"
     " *    non esistono su nessun tasto.\n"
     " *\n"
     " * ⭐ E il danno vero non e' l'accento: le scorciatoie viaggiano come\n"
     " *    POSIZIONI (`SPECIFICHE.md` §7.3), e su una tastiera tedesca la `Z`\n"
     " *    sta dove da noi sta la `Y` — senza rinegoziare, `Ctrl+Z` arriva come\n"
     " *    `Ctrl+Y`, cioe' «rifai» invece di «annulla». */\n"
     "bool figli_disposizione(figli *f, const char *utente, const char *nome)\n"
     "{\n"
     "	struct figlio *g;\n"
     "	struct testa t;\n"
     "	struct corpo_disposizione c;\n"
     "	uint8_t busta[sizeof t + sizeof c];\n"
     "\n"
     "	if (!f || !utente || !nome || !*nome)\n"
     "		return false;\n"
     "	g = cerca(f, utente);\n"
     "	if (!g || g->fd < 0 || g->uscendo)\n"
     "		return false;\n"
     "\n"
     "	memset(&t, 0, sizeof t);\n"
     "	magia_scrivi(&t);\n"
     "	t.tipo = MSG_DISPOSIZIONE;\n"
     "	t.versione = FIGLIO_VERSIONE;\n"
     "	t.matricola = g->matricola;\n"
     "	t.uid_dichiarato = (uint32_t)g->uid;\n"
     "	t.byte = (uint32_t)sizeof c;\n"
     "	memset(&c, 0, sizeof c);\n"
     "	snprintf(c.nome, sizeof c.nome, \"%s\", nome);\n"
     "	memcpy(busta, &t, sizeof t);\n"
     "	memcpy(busta + sizeof t, &c, sizeof c);\n"
     "	if (send(g->fd, busta, sizeof busta, MSG_NOSIGNAL) != (ssize_t)sizeof busta) {\n"
     "		/* ⛔ `registro_dice` e non `dettaglio`: succede una volta per\n"
     "		 *    attacco, e se non parte l'utente resta con le scorciatoie\n"
     "		 *    sfasate — che e' precisamente il guasto che nessuno collega. */\n"
     "		registro_dice(REG_FIGLIO,\n"
     "		              \"⚠ la disposizione «%s» per «%s» NON e' partita: la \"\n"
     "		              \"sessione tiene la sua, e le scorciatoie resteranno \"\n"
     "		              \"sfasate\",\n"
     "		              nome, utente);\n"
     "		return false;\n"
     "	}\n"
     "	return true;\n"
     "}\n"
     "\n"
     "bool figli_input(figli *f, const char *utente, uint32_t id, uint8_t azione,",
     "figli_disposizione"),

    # il lato FIGLIO: chi la riceve -------------------------------------- #
    ("src/figlio.c",
     "			if (t.tipo == MSG_INPUT) {\n",
     "			if (t.tipo == MSG_DISPOSIZIONE) {\n"
     "				struct corpo_disposizione cd;\n"
     "\n"
     "				if ((size_t)letti < sizeof t + sizeof cd)\n"
     "					continue;\n"
     "				memcpy(&cd, busta + sizeof t, sizeof cd);\n"
     "				/* ⛔ Il NUL si impone NOI: la busta arriva da un socket, e\n"
     "				 *    una stringa non terminata letta come tale e' un difetto\n"
     "				 *    di memoria, non di tastiera. */\n"
     "				cd.nome[sizeof cd.nome - 1] = '\\0';\n"
     "				/* ⚠ E se il palco non c'e' ancora, si DICHIARA: «non l'ho\n"
     "				 *   applicata» e «non c'era niente da applicare» sono due\n"
     "				 *   fatti diversi (`LEZIONI.md` §1.9 regola 1). */\n"
     "				if (!palco_input) {\n"
     "					/* ⛔ NON si butta: si TIENE.  `rcp.c` la chiede quando\n"
     "					 *    `SESSIONE` e' partita, e `libei` si apre qualche\n"
     "					 *    centesimo dopo — buttarla qui vorrebbe dire che la\n"
     "					 *    cura funziona su ogni attacco tranne il PRIMO. */\n"
     "					snprintf(disposizione_in_attesa,\n"
     "					         sizeof disposizione_in_attesa, \"%s\", cd.nome);\n"
     "					registro_dice(REG_FIGLIO,\n"
     "					              \"⚠ disposizione «%s» chiesta ma il canale \"\n"
     "					              \"di input non c'e' ancora: TENUTA, si \"\n"
     "					              \"applica all'apertura del palco\",\n"
     "					              cd.nome);\n"
     "				}\n"
     "				else\n"
     "					input_disposizione(palco_input, cd.nome);\n"
     "				continue;\n"
     "			}\n"
     "			if (t.tipo == MSG_INPUT) {\n",
     "MSG_DISPOSIZIONE) {"),

    # ------------------------------------------------------------------ #
    ("src/figlio.h",
     "bool figli_input(figli *f, const char *utente, uint32_t id, uint8_t azione,",
     "/* ⭐⭐ §5-bis.7 — la disposizione dichiarata dal client entra nella\n"
     " *     sessione.  ⛔ `true` = la richiesta e' PARTITA, non «e' in vigore»:\n"
     " *     chi lo constata e' la riga «KEYMAP CAMBIATA» del figlio, dopo che\n"
     " *     Mutter ha distrutto e ricreato il dispositivo tastiera. */\n"
     "bool figli_disposizione(figli *f, const char *utente, const char *nome);\n"
     "\n"
     "bool figli_input(figli *f, const char *utente, uint32_t id, uint8_t azione,",
     "figli_disposizione"),

    # ------------------------------------------------------------------ #
    ("src/webtransport.h",
     "void wt_ritela_gancio(wt_ritela_richiesta f, void *ctx);",
     "void wt_ritela_gancio(wt_ritela_richiesta f, void *ctx);\n"
     "\n"
     "/* ⭐ §5-bis.7 — la disposizione al palco di CHI HA CHIESTO. */\n"
     "typedef bool (*wt_disposizione_richiesta)(void *ctx, const char *utente,\n"
     "                                          const char *nome);\n"
     "void wt_disposizione_gancio(wt_disposizione_richiesta f, void *ctx);",
     "wt_disposizione_gancio"),

    ("src/webtransport.c",
     "static bool gancio_ritela(void *ctx, uint32_t larghezza, uint32_t altezza)",
     "static wt_disposizione_richiesta gancio_palco_disposizione;\n"
     "static void *gancio_palco_disposizione_ctx;\n"
     "\n"
     "void wt_disposizione_gancio(wt_disposizione_richiesta f, void *ctx)\n"
     "{\n"
     "	gancio_palco_disposizione = f;\n"
     "	gancio_palco_disposizione_ctx = ctx;\n"
     "}\n"
     "\n"
     "/* ⭐⭐ §5-bis.7 — «metti questa disposizione», e va al palco di CHI HA\n"
     " *     CHIESTO.  ⛔ Invariante I3, identica alla ritela: il nome dell'utente\n"
     " *     e' quello che PAM ha ammesso su QUESTA sessione, mai un parametro che\n"
     " *     viene dal filo.  Un utente che potesse cambiare la tastiera di un\n"
     " *     altro sarebbe un difetto piccolo con una faccia grossa — il desktop\n"
     " *     dell'altro che smette di rispondere alle scorciatoie. */\n"
     "static bool gancio_disposizione(void *ctx, const char *nome)\n"
     "{\n"
     "	wt *w = (wt *)ctx;\n"
     "	const char *mio;\n"
     "\n"
     "	if (!gancio_palco_disposizione || !w->rcp)\n"
     "		return false;\n"
     "	mio = rcp_utente(w->rcp);\n"
     "	if (!mio || !mio[0])\n"
     "		return false;\n"
     "	return gancio_palco_disposizione(gancio_palco_disposizione_ctx, mio, nome);\n"
     "}\n"
     "\n"
     "/* ⭐⭐ «QUESTA MACCHINA CONOSCE QUESTA DISPOSIZIONE?» — e la risposta la da'\n"
     " *     **XKB**, non un elenco scritto a mano.\n"
     " *\n"
     " * ⛔ Il difetto che chiude, `[M]` banco `06-b34` caso 5, 16 agosto 2026:\n"
     " *    `hu`, `tr`, `gr` e `ua` esistono in `/usr/share/X11/xkb/symbols/` su\n"
     " *    questa macchina e venivano rifiutate con `SESSIONE_NON_SERVIBILE`,\n"
     " *    con la riga «disposizione sconosciuta a questa macchina» — una frase\n"
     " *    FALSA.  ⇒ Un utente ungherese non entrava.\n"
     " *\n"
     " * ⭐ E la domanda si gira a `tastiera.c`, che e' gia' l'unico posto del\n"
     " *    prodotto che sa compilare una disposizione: chiedere due volte la\n"
     " *    stessa cosa in due modi diversi produce due risposte sotto la stessa\n"
     " *    etichetta (forma E2).  ⚠ Copre anche la VARIANTE — `it(nonesiste)`\n"
     " *    non compila — che l'elenco fisso non guardava affatto. */\n"
     "static int gancio_disposizione_esiste(void *ctx, const char *nome)\n"
     "{\n"
     "	Tastiera *t;\n"
     "	char *sbaglio = NULL;\n"
     "\n"
     "	(void)ctx;\n"
     "	if (!nome || !*nome)\n"
     "		return 0;\n"
     "	t = tastiera_apri(nome, &sbaglio);\n"
     "	if (!t) {\n"
     "		free(sbaglio);\n"
     "		return 0;\n"
     "	}\n"
     "	tastiera_chiudi(t);\n"
     "	return 1;\n"
     "}\n"
     "\n"
     "static bool gancio_ritela(void *ctx, uint32_t larghezza, uint32_t altezza)",
     "gancio_disposizione_esiste"),

    ("src/webtransport.c",
     "		g.input_lettera = gancio_input_lettera;",
     "		g.input_lettera = gancio_input_lettera;\n"
     "		g.disposizione = gancio_disposizione;\n"
     "		g.disposizione_esiste = gancio_disposizione_esiste;",
     "g.disposizione = gancio_disposizione"),

    ("src/webtransport.c",
     '#include "webtransport.h"',
     '#include "webtransport.h"\n'
     '/* ⭐ §5-bis.7: la domanda «questa disposizione esiste?» la sa `tastiera.c`. */\n'
     '#include "tastiera.h"',
     '#include "tastiera.h"'),

    # ------------------------------------------------------------------ #
    ("src/main.c",
     "	wt_ritela_gancio(ritela_al_figlio, &ponte);",
     "	wt_ritela_gancio(ritela_al_figlio, &ponte);\n"
     "	wt_disposizione_gancio(disposizione_al_figlio, &ponte);",
     "wt_disposizione_gancio(disposizione_al_figlio, &ponte)"),

    ("src/main.c",
     "static bool ritela_al_figlio(void *ctx, const char *utente, uint32_t larghezza,",
     "/* ⭐ §5-bis.7 — e delega a `figli_disposizione()` come `ritela_al_figlio()`\n"
     " *    delega a `figli_ritela()`: questo file e' il ponte, non la regola. */\n"
     "static bool disposizione_al_figlio(void *ctx, const char *utente,\n"
     "                                   const char *nome)\n"
     "{\n"
     "	struct ponte *p = (struct ponte *)ctx;\n"
     "	if (!p || !p->f)\n"
     "		return false;\n"
     "	return figli_disposizione(p->f, utente, nome);\n"
     "}\n"
     "\n"
     "static bool ritela_al_figlio(void *ctx, const char *utente, uint32_t larghezza,",
     "static bool disposizione_al_figlio"),
    # ⛔⛔ LA DISPOSIZIONE CHIESTA PRIMA CHE IL PALCO ESISTA — `[M]` 16 agosto
    #     2026, e senza questi due pezzi la cura funziona su ogni attacco
    #     TRANNE IL PRIMO, che e' quello che ogni utente fa per primo.
    #
    #     Il registro lo diceva: *«disposizione «us» chiesta ma il canale di
    #     input non c'e' ancora: NON applicata»*.  `rcp.c` chiede la
    #     disposizione quando `SESSIONE` e' partita; `libei` si apre qualche
    #     centesimo dopo.  ⇒ La richiesta arrivava a `palco_input == NULL` e
    #     cadeva — dichiarata, ma caduta.
    #
    # ⇒ Si TIENE, e si applica appena il palco c'e'.  ⚠ E' la stessa forma di
    #   `RITELA`: una cosa che riguarda il palco puo' arrivare prima del palco.
    ("src/figlio.c",
     "static Input *palco_input;",
     "static Input *palco_input;\n"
     "/* ⭐ §5-bis.7: la disposizione chiesta quando il palco non c'era ancora.\n"
     " *    ⛔ Vuota = niente in attesa.  Si applica appena `input_apri()` riesce. */\n"
     "static char disposizione_in_attesa[65];",
     "static char disposizione_in_attesa"),

    ("src/figlio.c",
     "		if (palco_input)\n"
     "			registro_dice(REG_FIGLIO,\n"
     "			              \"⭐⭐ IL CANALE DI INPUT E' APERTO sulla tela %ux%u: \"",
     "		if (palco_input && disposizione_in_attesa[0]) {\n"
     "			/* ⛔ Prima di dire che il canale e' aperto: la disposizione\n"
     "			 *    chiesta all'attacco era arrivata a palco chiuso, e se non\n"
     "			 *    la si applica QUI l'utente batte i primi tasti sulla\n"
     "			 *    disposizione sbagliata — e `Ctrl+Z` fa «rifai». */\n"
     "			registro_dice(REG_FIGLIO,\n"
     "			              \"⭐ §5-bis.7: applico adesso la disposizione «%s», \"\n"
     "			              \"che era stata chiesta quando il palco non c'era \"\n"
     "			              \"ancora\",\n"
     "			              disposizione_in_attesa);\n"
     "			input_disposizione(palco_input, disposizione_in_attesa);\n"
     "			disposizione_in_attesa[0] = '\\0';\n"
     "		}\n"
     "		if (palco_input)\n"
     "			registro_dice(REG_FIGLIO,\n"
     "			              \"⭐⭐ IL CANALE DI INPUT E' APERTO sulla tela %ux%u: \"",
     "applico adesso la disposizione"),
]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    albero = sys.argv[1]
    solo_leggi = "--leggi" in sys.argv
    fatti, gia, mancanti = 0, 0, []

    for rel, ancora, nuovo, marca in PEZZI:
        percorso = os.path.join(albero, rel)
        if not os.path.isfile(percorso):
            mancanti.append(f"{rel}: il file non c'e'")
            continue
        with open(percorso, encoding="utf-8") as f:
            s = f.read()
        if marca in s:
            gia += 1
            continue
        if ancora not in s:
            # ⛔ Ci si FERMA: applicare a meta' lascia un albero che non
            #    compila, e il padrone del file si troverebbe un guasto che non
            #    ha scritto lui.
            mancanti.append(f"{rel}: ancora NON trovata → «{ancora[:60]}…»")
            continue
        if not solo_leggi:
            with open(percorso, "w", encoding="utf-8") as f:
                f.write(s.replace(ancora, nuovo, 1))
        fatti += 1

    print(f"    cuciti {fatti} · gia' presenti {gia} · non applicabili {len(mancanti)}")
    for m in mancanti:
        print(f"    ⛔ {m}")
    if mancanti:
        print("    ⛔ La cucitura NON e' completa: l'albero potrebbe non compilare.")
        print("       ⚠ Le ancore sono verbatim: se il padrone del file le ha")
        print("         cambiate, si riscrive il pezzo — non si forza.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
