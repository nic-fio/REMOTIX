#!/bin/bash
#
# 04-b31-certifica.sh — ⛔ IL BANCO SA VEDERE IL DIFETTO?
#
#   bash banchi/04-b31-certifica.sh
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE — `CODER.md` §4.6 e §3.3/§3.4
#
# *«Un banco verde mentre il difetto e' vivo e' la peggiore delle prove, perche'
# da' fiducia.  Se un controllo conta qualcosa, assicurati che sappia vedere il
# difetto che cerchi.»*  E `LEZIONI.md` lo ha pagato: un guasto del metro era
# **verde per costruzione** perche' il banco leggeva un contatore che il prodotto
# chiamava con un altro nome.
#
# ⇒ Qui si INNESTA il difetto in una copia di `src/rcp.c` e si pretende che
#   `04-b31-tela` diventi ROSSO.  Un guasto che resta verde e' un caso che il
#   banco non guarda, e va detto.
#
# ⛔ E si lavora su una COPIA: l'albero del prodotto non si tocca mai — e' la
#    regola dei banchi in parallelo, pagata l'11 agosto 2026 (un banco che
#    innestava sull'albero vero faceva misurare a tutti gli altri un binario
#    bugiardo per qualche minuto).
set -uo pipefail

ALBERO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LAVORO=${LAVORO:-/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2/04-b31}
CC=${CC:-gcc}
CFLAGS="-O1 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE"

rm -rf "$LAVORO"
mkdir -p "$LAVORO"

# ---------------------------------------------------------------------------
# I guasti.  Ciascuno e' una sostituzione di testo dentro `rcp.c`, e accanto
# c'e' il CASO che deve diventare rosso — dichiarato PRIMA di girare.
# ---------------------------------------------------------------------------
python3 - "$ALBERO" "$LAVORO" <<'PITONE'
import os, sys
albero, lavoro = sys.argv[1], sys.argv[2]
rcp = open(os.path.join(albero, "src/rcp.c"), encoding="utf-8").read()

GUASTI = [
    # (nome, che difetto e', cerca, sostituisci, casi attesi rossi)
    ("G1-risposta-subito",
     "risponde TELA(ADATTATA) senza aspettare la risposta del palco — la "
     "stesura ingenua, quella che crede all'esito della richiesta invece che "
     "ai pixel",
     "\t\t\ts->tela_volo = true;\n\t\t\ts->tela_volo_l = buona_l;",
     "\t\t\trcp_tela_adattata_ora(s, buona_l, buona_a, ora);\n"
     "\t\t\ts->tela_volo = true;\n\t\t\ts->tela_volo_l = buona_l;",
     # ⚠ SEI casi, misurati: la prima stesura ne dichiarava dieci a occhio.
     #   L'atteso si corregge sulla misura, e si dice — `LEZIONI.md` §1.11.
     [1, 3, 4, 14, 15, 16]),

    ("G2-niente-fondo",
     "il fondo dell'attesa non scatta: §7.1 vuole un TELA comunque, e senza "
     "questo il client aspetta per sempre (e trattiene fotogrammi, §6.2)",
     "\ttela_scade(s, ora);",
     "\t(void)tela_scade;",
     [4]),

    ("G3-una-risposta-per-due",
     "due ADATTA_TELA e un TELA solo: il conto del client non torna piu' a "
     "zero e la sua coda dei trattenuti cresce senza fine",
     "\t\t\t\tmanda_tela(s, 2 /* RIFIUTATA */, 3 /* NON_ORA */, s->tela_l,\n"
     "\t\t\t\t           s->tela_a);\n\t\t\t\ts->tela_volo = false;",
     "\t\t\t\ts->tela_volo = false;",
     [3, 14]),

    ("G4-riconosce-la-risposta",
     "⛔ il difetto delle due richieste incatenate: si riconosce la risposta "
     "dalla misura AVUTA invece che dalla richiesta a cui risponde, e il "
     "fotogramma della prima chiude la seconda",
     "\tif (s->tela_volo && voluta_l == s->tela_volo_l\n"
     "\t    && voluta_a == s->tela_volo_a) {\n\t\tif (avuta_l != voluta_l",
     "\tif (s->tela_volo) {\n\t\tif (avuta_l != voluta_l",
     [14]),

    ("G5-niente-tetto",
     "ADATTA_TELA non rispetta il video.misura_massima del client: si concede "
     "una tela che il suo decodificatore non regge, e lo schermo resta nero",
     "\t\t\tif (s->max_l && (buona_l > s->max_l || buona_a > s->max_a)) {",
     "\t\t\tif (false && s->max_l && (buona_l > s->max_l || buona_a > s->max_a)) {",
     [10]),

    ("G6-ri-attacco-cieco",
     "ATTACCA non chiede che misura ha il palco: al ri-attacco la tela in "
     "vigore e quella dei fotogrammi divergono, e non arriva un pixel",
     "\tif (s->g.tela_del_palco) {",
     "\tif (false && s->g.tela_del_palco) {",
     [8]),

    ("G7-nessun-troncamento",
     "la misura dispari va al palco cosi' com'e': il 4:2:0 la arrotonda in "
     "silenzio, e nasce la divergenza fra chiesto e concesso",
     "\t\t\tif (!s->g.ritela(s->g.ctx, buona_l, buona_a)) {",
     "\t\t\tif (!s->g.ritela(s->g.ctx, chiesta_l, chiesta_a)) {",
     # ⚠ Anche il 10: senza troncamento la riduzione al tetto del client passa
     #   al palco il valore grezzo invece di quello ammesso.
     [6, 10]),

    ("G8-tela-non-richiesta",
     "⛔ il difetto piu' grave della prima stesura: il palco cambia da solo e "
     "il server ADOTTA la sua misura mandando un TELA che nessuno ha chiesto — "
     "che per §6.2 fa chiudere la sessione al client",
     "\ttela_richiama_il_palco(s, ora_ms);\n}\n\nbool rcp_tela_in_volo",
     "\trcp_tela_adattata_ora(s, avuta_l, avuta_a, ora_ms);\n}\n\n"
     "bool rcp_tela_in_volo",
     # ⚠ Anche il 14: adottare senza riconoscere la richiesta fa chiudere la
     #   seconda con la risposta della prima.
     [9, 14]),

    # ⛔⭐ E QUESTO GUASTO TOCCA **DUE** RIGHE, e la ragione e' una lezione: la
    #     prima stesura ne toccava una sola e il guasto restava VERDE, perche' il
    #     secondo controllo (quello dopo il troncamento al pari) lo mascherava.
    #     ⚠ Un guasto mascherato da una difesa in piu' non e' un banco cieco —
    #     ma un banco che non se ne accorge non puo' dirlo.
    ("G9-limiti-inventati",
     "i limiti della tela non sono quelli di §4.5: si concede una tela che "
     "ATTACCA rifiuterebbe al ri-attacco",
     ["\tif (larghezza < RCP_TELA_L_MINIMA || altezza < RCP_TELA_A_MINIMA ||",
      "\tif (l < RCP_TELA_L_MINIMA || a < RCP_TELA_A_MINIMA)"],
     ["\tif (larghezza < 200u || altezza < 200u ||",
      "\tif (l < 200u || a < 200u)"],
     [17]),

    ("G10-rinuncia-taciuta",
     "il palco dice «non ce l'ho fatta» e il server tace: il client aspetta il "
     "fondo dei tre secondi per una notizia che c'era gia'",
     "\tif (!avuta_l || !avuta_a) {",
     "\tif (false && (!avuta_l || !avuta_a)) {",
     [15]),
]

righe = []
for nome, spiega, cerca, sost, rossi in GUASTI:
    # ⚠ Un guasto puo' toccare piu' righe: `cerca`/`sost` sono una stringa o una
    #   lista.  ⛔ E ogni ancora deve trovarsi UNA volta sola, o non si sa che
    #   cosa si e' innestato.
    ancore = cerca if isinstance(cerca, list) else [cerca]
    nuove = sost if isinstance(sost, list) else [sost]
    quante = [rcp.count(a) for a in ancore]
    if any(q != 1 for q in quante):
        righe.append(f"{nome}\tANCORA\t{quante}\t{spiega}")
        continue
    guasto = rcp
    for a, n in zip(ancore, nuove):
        guasto = guasto.replace(a, n)
    open(os.path.join(lavoro, nome + ".c"), "w", encoding="utf-8").write(guasto)
    righe.append(f"{nome}\t{','.join(str(r) for r in rossi)}\t0\t{spiega}")
open(os.path.join(lavoro, "elenco.tsv"), "w", encoding="utf-8").write(
    "\n".join(righe) + "\n")
PITONE

printf '\n== 04-b31: certificazione del banco (i guasti innestati) ==\n\n'

# ⛔ Prima il controllo POSITIVO: il banco su `rcp.c` INTATTO deve essere verde.
#    Senza, un rosso non distingue «il guasto si vede» da «il banco e' rotto».
$CC $CFLAGS -o "$LAVORO/sano" "$ALBERO/banchi/04-b31-tela.c" "$ALBERO/src/rcp.c" \
	|| { printf '  ⛔ non compila il banco sano\n'; exit 2; }
if "$LAVORO/sano" >"$LAVORO/sano.txt" 2>&1; then
	printf '  \033[1;32mOK\033[0m  controllo POSITIVO: sul codice intatto il banco e verde\n\n'
else
	printf '  \033[1;31mNO\033[0m  il banco e ROSSO sul codice intatto: non certifica niente\n'
	tail -20 "$LAVORO/sano.txt"
	exit 2
fi

stato=0
while IFS=$'\t' read -r nome rossi _ spiega; do
	if [ "$rossi" = "ANCORA" ]; then
		printf '  \033[1;33m??\033[0m  %-22s l ancora non si trova nel codice: il guasto\n' "$nome"
		printf '        non e stato innestato — %s\n' "$spiega"
		stato=1
		continue
	fi
	# ⛔ `-I` sull'albero vero: la COPIA guasta e' solo `rcp.c`, e `rcp.h` resta
	#    quello del prodotto — il guasto sta nel comportamento, non nella firma.
	$CC $CFLAGS -I"$ALBERO/src" -o "$LAVORO/$nome" \
		"$ALBERO/banchi/04-b31-tela.c" "$LAVORO/$nome.c" 2>"$LAVORO/$nome.cc" || {
		printf '  \033[1;33m??\033[0m  %-22s il guasto non COMPILA (vedi %s)\n' \
			"$nome" "$LAVORO/$nome.cc"
		stato=1
		continue
	}
	"$LAVORO/$nome" >"$LAVORO/$nome.txt" 2>&1
	uscita=$?
	# ⛔ NON basta «e' rosso»: devono essere rossi i casi ATTESI.  Un guasto che
	#    accende un caso diverso da quello che dovrebbe e' un banco che guarda
	#    un'altra cosa — e sarebbe verde il giorno in cui serve.
	#    ⚠ Si tolgono le sequenze di colore prima di leggere i numeri: sono
	#      byte veri nel file, e un `grep` che non li conosce conta zero.
	visti=$(sed 's/\x1b\[[0-9;]*m//g' "$LAVORO/$nome.txt" \
		| sed -n 's/^  NO  \([0-9]*\) .*/\1/p' | paste -sd, -)
	if [ $uscita -ne 0 ] && [ "$visti" = "$rossi" ]; then
		printf '  \033[1;32mOK\033[0m  %-22s ROSSI i casi %s, e sono quelli attesi\n' \
			"$nome" "$visti"
	elif [ $uscita -ne 0 ]; then
		printf '  \033[1;33m??\033[0m  %-22s ROSSI i casi %s, ma erano attesi %s\n' \
			"$nome" "${visti:-nessuno}" "$rossi"
		printf '        %s\n' "$spiega"
		stato=1
	else
		printf '  \033[1;31mNO\033[0m  %-22s il guasto resta VERDE: il banco NON lo vede\n' "$nome"
		printf '        %s\n' "$spiega"
		stato=1
	fi
done < "$LAVORO/elenco.tsv"

printf '\n'
if [ $stato -eq 0 ]; then
	printf '  ⭐ tutti i guasti innestati diventano rossi: il banco vede quel che dice di vedere.\n\n'
else
	printf '  ⛔ almeno un guasto resta verde: quel caso il banco NON lo guarda.\n\n'
fi
exit $stato
