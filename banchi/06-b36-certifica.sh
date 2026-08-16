#!/bin/bash
#
# 06-b36-certifica.sh — ⛔ IL BANCO DELLA TELA SUL FILO SA VEDERE IL DIFETTO?
#
#   bash banchi/06-b36-certifica.sh
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE — `CODER.md` §3.3, §3.4, §3.10, §4.6
#
# *«Un banco verde mentre il difetto e' vivo e' la peggiore delle prove, perche'
# da' fiducia.»*  ⇒ Ogni caso di `06-b36` vuole un guasto innestato **in una
# copia** di `src/rcp.c` che lo faccia diventare rosso — e rosso **li'**, non
# altrove.
#
# ⛔ LE DUE TRAPPOLE CHE `04-b31` HA GIA' PAGATO, e che qui non si ripagano:
#   1. un atteso dichiarato **a occhio**: diceva dieci casi rossi e ne accendeva
#      sei.  ⇒ Qui l'atteso si dichiara prima, si misura, e quando la misura lo
#      smentisce **si corregge dicendolo** (`LEZIONI.md` §1.11), non si allarga
#      per farlo tornare;
#   2. un guasto che resta **verde perche' un secondo controllo lo maschera**.
#      ⇒ I guasti che toccano una difesa doppia toccano **tutt'e due le righe**,
#      e la voce lo dice.
#
# ⛔ E ⚠ **L'ANCORA CHE SCADE IN SILENZIO** — la lezione del 16 agosto 2026:
#    l'ancora di `G8` in `04-b31-certifica.sh` ha smesso di trovarsi il giorno in
#    cui e' nata una funzione fra le due che nominava, e per un giorno il guasto
#    piu' grave dei dodici **non era piu' certificato da nessuno**.  ⇒ Il ramo
#    `ANCORA` qui sotto e' quel che se ne accorge, e vale **stato 1**: un
#    certificatore che non innesta non certifica.
#
# ⛔ Si lavora su una COPIA: l'albero del prodotto non si tocca mai.
set -uo pipefail

ALBERO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LAVORO=${LAVORO:-/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2/06-b36}
CC=${CC:-gcc}
CFLAGS="-O1 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE"

rm -rf "$LAVORO"
mkdir -p "$LAVORO"

python3 - "$ALBERO" "$LAVORO" <<'PITONE'
import os, sys
albero, lavoro = sys.argv[1], sys.argv[2]
rcp = open(os.path.join(albero, "src/rcp.c"), encoding="utf-8").read()

GUASTI = [
    # ------------------------------------------------------------------ #
    #  A · IL RIPIEGO CHE SMETTE DI DICHIARARSI                          #
    #      ⛔ Il byte sul filo resta GIUSTO in tutti e tre: cambia solo   #
    #         la riga di registro.  E' precisamente il difetto che un     #
    #         banco che conta i `TELA` non puo' vedere.                   #
    # ------------------------------------------------------------------ #
    ("H1-incapace-muto",
     "COMPOSITORE_INCAPACE si risponde ma non si DICHIARA: il byte spegne la "
     "voce nel client, e chi diagnostica non distingue piu' un ospite senza "
     "palco da un palco rotto (`SPECIFICHE.md` §6.3)",
     '\t\t\t\t       "collegato): COMPOSITORE_INCAPACE, e la tela resta %ux%u",',
     '\t\t\t\t       "collegato): non riuscito, e la tela resta %ux%u",',
     [1]),

    ("H2-ripiego-kde-muto",
     "⛔ il ripiego di `SPECIFICHE.md` §6.3 — la tela concessa diversa da quella "
     "chiesta — non si scrive nel registro.  §4.5: «il server DEVE aver scritto "
     "il ripiego nel registro»",
     '\t\t\t\treg(s, "⚠ RIPIEGO DICHIARATO (§4.5): chiesta la tela %ux%u, ma "',
     '\t\t\t\treg(s, "⚠ la tela chiesta era %ux%u, ma "',
     [2]),

    ("H3-tetto-muto",
     "la riduzione al `video.misura_massima` si fa in silenzio: due misure "
     "diverse sotto la stessa etichetta, che e' la forma E2",
     '\t\t\t\treg(s, "⚠ RIPIEGO DICHIARATO (§4.5): ADATTA_TELA %ux%u supera il "',
     '\t\t\t\treg(s, "ADATTA_TELA %ux%u supera il "',
     [3]),

    # ------------------------------------------------------------------ #
    #  B · LE COORDINATE IN VOLO — la terza eccezione dichiarata di §3    #
    # ------------------------------------------------------------------ #
    ("H4-grazia-muta",
     "⛔ la tolleranza si applica e NON si scrive.  §3 ultimo capoverso: «ogni "
     "tolleranza va scritta nel registro.  Una tolleranza silenziosa e' "
     "indistinguibile da un difetto, ed e' precisamente l'indulgenza che questa "
     "sezione esiste per togliere»",
     '\t\treg(s, "⭐ §7.1 SECONDO DI GRAZIA (%u-esima volta): input id=%u porta "',
     '\t\treg(s, "input id=%.0s%u porta "',
     # ⚠ Anche l'11: la sua seconda meta' pretende la riga sul pixel 1280.
     [6, 11]),

    ("H5-grazia-non-satura",
     "la grazia accetta la coordinata vecchia e la inietta COSI' COM'E' invece "
     "di saturarla: il puntatore finisce fuori dalla tela in vigore, e chi lo "
     "riceve o lo scarta o disegna dove non c'e' niente",
     "\t\t*sx = x < s->tela_l ? x : s->tela_l - 1;\n"
     "\t\t*sy = y < s->tela_a ? y : s->tela_a - 1;",
     "\t\t*sx = x;\n\t\t*sy = y;",
     [6, 11]),

    ("H6-grazia-eterna",
     "⛔ la grazia non scade mai: «per un secondo» diventa «per sempre», e il "
     "DEVE di §7.3 sulle coordinate non torna piu' intero — l'indulgenza "
     "generale che §3 esiste per togliere",
     "\t                     ora >= s->tela_grazia_da &&\n"
     "\t                     ora - s->tela_grazia_da <= TELA_GRAZIA;",
     "\t                     ora >= s->tela_grazia_da;",
     [7, 8]),

    ("H7-confine-stretto",
     "⭐ il confine e' `<` invece di `<=`: «per un secondo» diventa «per 999 "
     "ms», e una sessione muore per un millisecondo.  ⚠ E' il guasto piu' fine "
     "del banco: sposta UN caso solo",
     "\t                     ora - s->tela_grazia_da <= TELA_GRAZIA;",
     "\t                     ora - s->tela_grazia_da < TELA_GRAZIA;",
     [7]),

    ("H8-grazia-generale",
     "⛔ la grazia copre QUALUNQUE coordinata, non solo quelle valide sulla tela "
     "precedente: §7.1 dice «copre le coordinate della tela vecchia, non le "
     "coordinate sbagliate», e cosi' il difetto del client non si vede piu'",
     "\tif (grazia_aperta && x < s->tela_prec_l && y < s->tela_prec_a) {",
     "\tif (grazia_aperta) {",
     [9]),

    # ------------------------------------------------------------------ #
    #  C · IL PALCO CHE CAMBIA DA SE'                                     #
    # ------------------------------------------------------------------ #
    ("H9-tela-non-richiesta",
     "⛔ il difetto piu' grave della prima stesura, sui casi NUOVI: il palco "
     "cambia da solo e il server ADOTTA la sua misura mandando un `TELA` che "
     "nessuno ha chiesto — che per §6.2 fa chiudere una sessione SANA",
     "\ttela_richiama_il_palco(s, ora_ms);\n}\n\nbool rcp_tela_rimanda",
     "\trcp_tela_adattata_ora(s, avuta_l, avuta_a, ora_ms);\n}\n\n"
     "bool rcp_tela_rimanda",
     [12, 13]),

    ("H10-richiamo-alla-vecchia",
     "⛔ il palco si richiama alla tela IN VIGORE anche quando una `ADATTA_TELA` "
     "e' in volo: il server contraddice la richiesta che ha girato lui stesso, e "
     "condanna al NON_ORA un adattamento che stava per riuscire",
     "\tuint32_t verso_l = s->tela_volo ? s->tela_volo_l : s->tela_l;\n"
     "\tuint32_t verso_a = s->tela_volo ? s->tela_volo_a : s->tela_a;",
     "\tuint32_t verso_l = s->tela_l;\n\tuint32_t verso_a = s->tela_a;",
     [13]),

    # ------------------------------------------------------------------ #
    #  D · I LIMITI DI §4.5, PER LATO E AGLI ESTREMI                      #
    # ------------------------------------------------------------------ #
    ("H11-un-lato-solo",
     "il tetto si controlla su un lato solo: 1920x4322 passa, e al ri-attacco "
     "`ATTACCA` rifiuterebbe una tela che questo stesso server aveva concesso",
     "\t    larghezza > RCP_TELA_L_MASSIMA || altezza > RCP_TELA_A_MASSIMA)",
     "\t    larghezza > RCP_TELA_L_MASSIMA)",
     [14]),

    # ⛔⭐ E QUESTO TOCCA **DUE** RIGHE, per la lezione di `04-b31`: il minimo si
    #     controlla due volte (prima del troncamento al pari e dopo), e toccarne
    #     una sola lascerebbe l'altra a mascherare il guasto.
    ("H12-estremi-esclusi",
     "gli estremi di §4.5 vengono esclusi (`<=` al posto di `<`): 320x240 e "
     "7680x4320 — le due misure che l'arbitro NOMINA — si rifiutano",
     ["\tif (larghezza < RCP_TELA_L_MINIMA || altezza < RCP_TELA_A_MINIMA ||",
      "\tif (l < RCP_TELA_L_MINIMA || a < RCP_TELA_A_MINIMA)"],
     ["\tif (larghezza <= RCP_TELA_L_MINIMA || altezza <= RCP_TELA_A_MINIMA ||",
      "\tif (l <= RCP_TELA_L_MINIMA || a <= RCP_TELA_A_MINIMA)"],
     [15]),

    ("H13-una-risposta-per-tre",
     "tre `ADATTA_TELA` e un `TELA` solo: §7.1 ne vuole uno per ciascuna, e il "
     "conto che il client tiene (§6.2) non torna piu' a zero — la sua coda dei "
     "fotogrammi trattenuti cresce senza fine",
     "\t\t\t\tmanda_tela(s, 2 /* RIFIUTATA */, 3 /* NON_ORA */, s->tela_l,\n"
     "\t\t\t\t           s->tela_a);\n\t\t\t\ts->tela_volo = false;",
     "\t\t\t\ts->tela_volo = false;",
     [16]),

    # ------------------------------------------------------------------ #
    #  E · `VISTA` — «la vista e' della connessione, la tela della        #
    #      sessione»                                                      #
    # ------------------------------------------------------------------ #
    ("H14-vista-non-servita",
     "⛔ `VISTA` torna a cadere nel `default`: un client conforme che stringe la "
     "finestra del browser PERDE LA SESSIONE — alla lettera il sintomo che il "
     "rilievo R1.17 di §7.1 e' stato scritto per rendere impossibile",
     "\t\tcase T_VISTA: {",
     "\t\tcase 0x1008: {",
     [17, 18, 19, 20]),

    ("H15-vista-cambia-la-tela",
     "⛔⛔ e il difetto OPPOSTO, che e' peggio: `VISTA` fa cambiare la tela.  "
     "§7.1: «VISTA NON DEVE far cambiare la tela».  ⇒ Il desktop di chi ha solo "
     "stretto la finestra si rimpicciolisce, e SENZA nessun `TELA` — i due lati "
     "che si separano in silenzio (E2)",
     "\t\t\ts->vista_l = nuova_l;\n\t\t\ts->vista_a = nuova_a;",
     "\t\t\ts->vista_l = nuova_l;\n\t\t\ts->vista_a = nuova_a;\n"
     "\t\t\ts->tela_l = nuova_l;\n\t\t\ts->tela_a = nuova_a;",
     # ⚠ ATTESO CORRETTO SULLA MISURA, e si dice (`LEZIONI.md` §1.11): a occhio
     #   dicevo `17,18,19`, e il banco ne accende **quattro**.  Il 20 pretende
     #   che dopo `VISTA(640x360)` la tela sia ancora 1920x1080, ed e' proprio
     #   quel che questo guasto rompe: non e' un rosso di troppo, e' il caso che
     #   avevo dimenticato di contare.
     [17, 18, 19, 20]),

    ("H16-vista-letta-e-buttata",
     "`VISTA` si convalida e si scrive, ma il valore non si tiene: un campo del "
     "protocollo che il server dichiara di aver capito e non ha da nessuna parte",
     "\t\t\ts->vista_l = nuova_l;\n\t\t\ts->vista_a = nuova_a;",
     "\t\t\t(void)nuova_l;\n\t\t\t(void)nuova_a;",
     [20]),

    ("H17-zero-e-una-vista",
     "lo zero passa come vista: §7.1 dice «da 1x1 in su», e §6.0 vieta i valori "
     "sentinella impliciti — il difetto si vedrebbe piu' in la', quando qualcuno "
     "ci dividesse",
     "\t\t\tif (!nuova_l || !nuova_a) {",
     "\t\t\tif (false && (!nuova_l || !nuova_a)) {",
     [21]),

    ("H19-attacca-zero-e-una-vista",
     "in `ATTACCA` lo zero passa come vista: §7.1 dice «da 1x1 in su», e §4.5 "
     "non mette limiti al campo — ⛔ nessun banco del deposito manda mai un "
     "ATTACCA con la vista a zero, quindi senza questo guasto quel ramo sarebbe "
     "codice scritto e mai percorso",
     "\tif (!vl || !va) {",
     "\tif (false && (!vl || !va)) {",
     [23]),

    # ------------------------------------------------------------------ #
    #  F · §6.1 — LA LUNGHEZZA GIUDICATA PRIMA DEGLI EFFETTI              #
    # ------------------------------------------------------------------ #
    ("H18-lunghezza-dopo-gli-effetti",
     "⛔ `ADATTA_TELA` e `VISTA` escono da `misura_campi()`: e' il rilievo R9.4 "
     "riaperto — il messaggio si esegue PER INTERO (il palco si ridimensiona "
     "davvero) e solo dopo si congeda.  §3: «NON DEVE proseguire»",
     "\tcase T_ADATTA_TELA:\n\tcase T_VISTA:\n\t\tle_u32(&l);\n\t\tle_u32(&l);\n\t\tbreak;",
     "\tcase 0x100B:\n\tcase 0x1008:\n\t\tle_u32(&l);\n\t\tle_u32(&l);\n\t\tbreak;",
     [22]),
]

righe = []
for nome, spiega, cerca, sost, rossi in GUASTI:
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

printf '\n== 06-b36: certificazione del banco (i guasti innestati) ==\n\n'

# ⛔ Prima il controllo POSITIVO: il banco su `rcp.c` INTATTO deve essere verde.
$CC $CFLAGS -o "$LAVORO/sano" "$ALBERO/banchi/06-b36-tela-filo.c" \
	"$ALBERO/src/rcp.c" \
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
		printf '  \033[1;33m??\033[0m  %-26s l ancora non si trova nel codice: il guasto\n' "$nome"
		printf '        non e stato innestato — %s\n' "$spiega"
		stato=1
		continue
	fi
	$CC $CFLAGS -I"$ALBERO/src" -o "$LAVORO/$nome" \
		"$ALBERO/banchi/06-b36-tela-filo.c" "$LAVORO/$nome.c" 2>"$LAVORO/$nome.cc" || {
		printf '  \033[1;33m??\033[0m  %-26s il guasto non COMPILA (vedi %s)\n' \
			"$nome" "$LAVORO/$nome.cc"
		stato=1
		continue
	}
	"$LAVORO/$nome" >"$LAVORO/$nome.txt" 2>&1
	uscita=$?
	# ⛔ NON basta «e' rosso»: devono essere rossi i casi ATTESI.
	visti=$(sed 's/\x1b\[[0-9;]*m//g' "$LAVORO/$nome.txt" \
		| sed -n 's/^  NO  \([0-9]*\) .*/\1/p' | paste -sd, -)
	if [ $uscita -ne 0 ] && [ "$visti" = "$rossi" ]; then
		printf '  \033[1;32mOK\033[0m  %-26s ROSSI i casi %s, e sono quelli attesi\n' \
			"$nome" "$visti"
	elif [ $uscita -ne 0 ]; then
		printf '  \033[1;33m??\033[0m  %-26s ROSSI i casi %s, ma erano attesi %s\n' \
			"$nome" "${visti:-nessuno}" "$rossi"
		printf '        %s\n' "$spiega"
		stato=1
	else
		printf '  \033[1;31mNO\033[0m  %-26s il guasto resta VERDE: il banco NON lo vede\n' "$nome"
		printf '        %s\n' "$spiega"
		stato=1
	fi
done < "$LAVORO/elenco.tsv"

printf '\n'
if [ $stato -eq 0 ]; then
	printf '  ⭐ tutti i guasti innestati diventano rossi: il banco vede quel che dice di vedere.\n\n'
else
	printf '  ⛔ almeno un guasto resta verde o non si innesta: quel caso il banco NON lo guarda.\n\n'
fi
exit $stato
