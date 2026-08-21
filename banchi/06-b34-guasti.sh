#!/bin/bash
#
# 06-b34-guasti.sh — ⛔ IL CONTROLLO POSITIVO: si innesta un guasto SU UNA
# COPIA e si pretende che il banco diventi ROSSO nel caso dichiarato prima.
#
#   sudo bash .../06-b34-guasti.sh keymap-una-volta   guasto A, poi caso2s
#   sudo bash .../06-b34-guasti.sh tasti-col-vecchio  guasto B, poi caso4
#   sudo bash .../06-b34-guasti.sh senza-cura         guasto C, poi caso7
#   sudo bash .../06-b34-guasti.sh forma-aperta       guasto D, poi caso8
#   sudo bash .../06-b34-guasti.sh sano               rimette il binario buono
#
# ===========================================================================
# ⛔ PERCHE' ESISTE — `CODER.md` §3.3 e §3.4
# ===========================================================================
#
# §3.4: *«Un banco che NON riproduce non è una prova di correttezza. È il
# rovescio della 3.3, ed è più insidioso perché il banco è verde.»*
#
# I casi 2s e 4 di `06-b34` sono usciti **verdi**.  ⛔ Un verde vale solo se lo
# strumento sa diventare rosso: finche' nessuno gliel'ha fatto fare, «il
# prodotto e' giusto» e «il banco non guarda» hanno lo stesso colore.
#
# ⇒ Qui i due guasti sono **esattamente** i due modi di sbagliare che
#   `tastiera.h:69` e `STUDI.md` §gnome §9 nominano, e per ciascuno e' scritto
#   PRIMA quale caso deve diventare rosso e con quale carattere.
#
# ===========================================================================
# ⛔ I QUATTRO GUASTI, E DOVE VIVONO
# ===========================================================================
#
# ⚠ Erano due fino al 21 agosto 2026; C e D sono nati con i casi 7 e 8, e
#   nascono **insieme a loro** — non dopo, che e' il modo in cui l'ancora del
#   guasto B era nata scaduta.
#
#  A. **`keymap-una-volta`** — in `src/tastiera.c`, che e' MIO.
#     `tastiera_apri_da_keymap()` si tiene il **primo** testo di keymap e
#     ricompila sempre quello: e' alla lettera *«la keymap si legge una volta
#     all'avvio»*, l'assunzione sbagliata che `reference-gnome/rapporti/
#     06-mutter-input.md:784` nomina come rischio.
#     ⇒ ATTESO: **il caso 2s diventa ROSSO**.  Con la sessione passata a `de`
#       si manda ancora il 44 per la `z`, e sul tedesco il 44 e' la **`y`**:
#       arriva `ayz…` invece di `azy\a`.  ⛔ Non un carattere mancante: **un
#       carattere DIVERSO**, che `RCP.md` §7.3 vieta.
#     ⚠ E si ricompila il TESTO, non si ritorna lo stesso oggetto: `input.c`
#       chiude la vecchia `Tastiera` prima di prendere la nuova, e restituire
#       lo stesso puntatore sarebbe un uso dopo la liberazione — cioe' un
#       guasto DIVERSO da quello dichiarato, che e' il modo di rendere
#       inservibile un controllo positivo.
#
#  B. **`tasti-col-vecchio`** — in `src/input.c`, che ⛔ **NON E' MIO**.
#     Qui si tocca **solo la copia**, e solo per certificare il banco: la cura,
#     se servisse, la propone il rapporto e la fa il suo padrone.
#     `dispositivo_tolto()` azzera la mappa dei tasti premuti, cioe' «i tasti
#     se ne sono andati col dispositivo».  E' la riga che `input.c:498-500`
#     dichiara di NON scrivere apposta.
#     ⇒ ATTESO: **il caso 4b diventa ROSSO**.  Il registro dice «rilascio al
#       distacco: **0**» — uno zero che si legge come *«non c'era niente
#       premuto»* — e al riattacco il Maiusc e' rimasto giu': arriva **`AZ`**
#       invece di `az`.
set -uo pipefail

SANO=${SANO:-/media/REMOTIX/src/06-t-src}
GUASTO=${GUASTO:-/media/REMOTIX/src/06-t-guasto}
BH=$SANO/banchi
TERRENO=$BH/06-b34-terreno.sh
LANCIA=$BH/06-b34-lancia.sh

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { ko "⛔ va lanciato DA ROOT"; exit 2; }

# ⛔ La copia si rifa' da zero a ogni giro: un albero guasto che si porta
#    dietro il guasto di ieri e' un albero di cui non si sa che cosa provi.
rifai_copia() {
	rm -rf "$GUASTO"
	mkdir -p "$GUASTO"
	cp -a "$SANO/src" "$GUASTO/src"
	# ⛔ E ANCHE IL GEMELLO, o il `Makefile` non compila affatto.
	#    `Makefile:96` — `GEMELLO ?= ../banchi/rcp` — pretende che `src/rcp.c`,
	#    `rcp.h` e `autenticazione.c` combacino BYTE PER BYTE con la copia di
	#    `banchi/rcp/`: sono lo stesso modulo montato due volte (R12.3).
	#    ⚠ Senza, il confronto va a finire sull'albero di QUALCUN ALTRO e il
	#      guasto non si costruisce — cioe' il controllo positivo fallisce per
	#      una ragione che non c'entra niente col guasto.
	mkdir -p "$GUASTO/banchi"
	cp -a "$SANO/banchi/rcp" "$GUASTO/banchi/rcp"
	rm -f "$GUASTO"/src/*.o "$GUASTO"/src/remotix
	ok "copia rifatta in $GUASTO (src + il gemello banchi/rcp)"
}

costruisci() {
	bash /media/REMOTIX/enter.sh --root \
		"bash /srv/src/$(basename "$GUASTO")/src/costruisci.sh > /tmp/06-b34-guasto-build.log 2>&1"
	if [ -x "$GUASTO/src/remotix" ]; then
		ok "il guasto e' COSTRUITO"
	else
		ko "⛔ il guasto NON si costruisce — e un guasto che non compila non"
		ko "   certifica niente: sarebbe un rosso del compilatore, non del banco"
		tail -20 /media/REMOTIX/devroot/tmp/06-b34-guasto-build.log 2>/dev/null | sed 's/^/        /'
		exit 3
	fi
}

# ⛔ SCRITTO NON E' IN VIGORE (forma E1): si rilegge il file e si pretende che
#    la riga innestata ci sia.  Un guasto che non e' entrato e' un banco che
#    dichiara verde il proprio controllo positivo — il peggiore dei silenzi.
verifica_innesto() {
	local file=$1 marca=$2
	if grep -q "$marca" "$file"; then
		ok "innesto verificato in $(basename "$file"): «$marca» c'e'"
	else
		ko "⛔ L'INNESTO NON E' ENTRATO in $file: il controllo positivo sarebbe"
		ko "   una prova che non prova niente"
		exit 3
	fi
}

# ⛔⛔⭐ IL CONTROLLO POSITIVO HA UN BIT — 21 agosto 2026, rilievo 4 di A9.
#
#      Questo copione finiva con `exit 0` INCONDIZIONATO dopo aver lanciato il
#      caso.  ⛔ Cioè il controllo positivo — lo strumento che esiste per dire
#      *«il banco sa diventare rosso»* — usciva **verde anche se il banco era
#      rimasto verde col guasto dentro**, che è esattamente la cosa che deve
#      scoprire.  ⚠ Il guardiano senza guardiano.
#
# ⇒ Qui il verdetto si ROVESCIA: il caso DEVE tornare != 0.  Un caso verde con
#   il guasto innestato è un fallimento DEL BANCO, e questo copione esce 1.
pretendi_rosso() {
	local caso=$1
	bash "$LANCIA" "$caso"
	local u=$?
	printf '\n'
	if [ "$u" -ne 0 ]; then
		ok "⭐ CONTROLLO POSITIVO SUPERATO: «$caso» e diventato ROSSO (uscita $u)"
		ok "   ⇒ quando torna verde sul binario sano, quel verde vale qualcosa"
		exit 0
	fi
	ko "⛔⛔ IL BANCO NON SA VEDERE IL GUASTO: «$caso» e rimasto VERDE con"
	ko "    l innesto dentro (uscita $u).  ⇒ Ogni verde che quel caso ha dato"
	ko "    finora non prova niente (CODER.md §3.4)."
	exit 1
}

accendi_con() {
	local albero=$1 come=$2
	# ⛔ LA SESSIONE TORNA SU «it» PRIMA DEL RIAVVIO, e non e' pignoleria: il
	#    figlio muore col server e RINASCE con la disposizione che la sessione
	#    ha in quell'istante.  Riacceso mentre la sessione era ancora `de`, il
	#    palco nasceva tedesco e il caso 2s non aveva nessun ricambio da
	#    reggere: `[M]` 16 agosto 2026, il controllo positivo restava VERDE col
	#    guasto vivo — cioe' `CODER.md` §3.4 dentro lo strumento che quel
	#    guasto doveva scoprire.
	bash "$TERRENO" disposizione it >/dev/null 2>&1
	bash "$TERRENO" spegni >/dev/null 2>&1
	sleep 1
	D="$albero/src" bash "$TERRENO" accendi | tail -3
	inf "acceso col binario: $come"
}

case "${1:-stato}" in
keymap-una-volta)
	log "GUASTO A — «la keymap si legge UNA VOLTA SOLA» (src/tastiera.c, MIO)"
	inf "ATTESO dichiarato PRIMA: il caso 2s diventa ROSSO, e arriva la «y»"
	inf "   dove ci va la «z» — un carattere DIVERSO, non un carattere mancante"
	rifai_copia
	python3 - "$GUASTO/src/tastiera.c" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
ancora = """	while (lunghezza > 0 && testo && testo[lunghezza - 1] == '\\0')
		lunghezza--;
"""
innesto = ancora + """
	/* ⛔⛔ GUASTO INNESTATO — 06-b34-guasti.sh «keymap-una-volta».
	 *     NON e' codice di prodotto: sta solo nell'albero della copia.
	 *
	 * Si tiene il PRIMO testo di keymap e si ricompila sempre quello, cioe'
	 * «la keymap si legge una volta all'avvio» — l'assunzione che
	 * `reference-gnome/rapporti/06-mutter-input.md:784` nomina come rischio e
	 * che `tastiera.h:69` esiste per non avere. */
	{
		static char *guasto_primo = NULL;
		static size_t guasto_lung = 0;

		if (!guasto_primo && testo && lunghezza) {
			guasto_primo = malloc(lunghezza);
			if (guasto_primo) {
				memcpy(guasto_primo, testo, lunghezza);
				guasto_lung = lunghezza;
			}
		} else if (guasto_primo) {
			testo = guasto_primo;
			lunghezza = guasto_lung;
		}
	}
"""
if ancora not in s:
    print("⛔ ancora non trovata in tastiera.c"); sys.exit(3)
open(p, "w", encoding="utf-8").write(s.replace(ancora, innesto, 1))
print("innestato")
PY
	verifica_innesto "$GUASTO/src/tastiera.c" "GUASTO INNESTATO"
	costruisci
	accendi_con "$GUASTO" "GUASTO A (keymap una volta sola)"
	sleep 2
	bash "$TERRENO" testimone >/dev/null 2>&1
	log "…e adesso il caso 2s, che DEVE diventare rosso"
	pretendi_rosso caso2s ;;

tasti-col-vecchio)
	log "GUASTO B — «i tasti se ne vanno col dispositivo» (src/input.c, NON mio)"
	inf "⛔ Si tocca SOLO la copia, e solo per certificare il banco: la cura la"
	inf "   propone il rapporto e la fa il padrone del file (sottofase 6.1)"
	inf "ATTESO dichiarato PRIMA: il caso 4b diventa ROSSO — «rilascio al"
	inf "   distacco: 0» nel registro, e al riattacco arriva «AZ» maiuscolo"
	rifai_copia
	python3 - "$GUASTO/src/input.c" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
# ⛔⛔⭐ L'ANCORA E' STATA RIFATTA — 21 agosto 2026, rilievo 2 della revisione
#      avversariale di A9, e l'ancora di prima era **NATA SCADUTA**.
#
#      Cercava `if (in->tastiera_dev == dispositivo) { ei_device_unref(...)`.
#      ⛔ Zero occorrenze: fra la graffa e l'`unref` oggi c'e' `segna_orfani()`
#      piu' otto righe di commento (`src/input.c:709`).  ⚠ La cura e il guasto
#      che doveva provarla sono entrati **nello stesso commit**, e il guasto non
#      e' mai stato rilanciato ⇒ il caso 4b — la scena di `RCP.md` §11, quella
#      col rapporto danno/costo piu' alto del documento — e' rimasto **senza
#      nessun controllo positivo**, e verde.
#
# ⭐ E l'ancora nuova e' scelta apposta perche' NON possa nascere scaduta due
#    volte: si aggancia alla riga di `segna_orfani`, che E' la cura, ⇒ il
#    giorno che la cura cambia forma l'innesto fallisce **rumorosamente** in
#    `verifica_innesto` invece di applicarsi a un punto che non c'e' piu'.
ancora = """		segna_orfani(in, in->tasti, in->tasti_orfani, MAX_TASTO, in->quanti_tasti, "tasti");
		ei_device_unref(in->tastiera_dev);
		in->tastiera_dev = NULL;
		in->tastiera_attiva = FALSE;
		in->ricambi_tastiera++;"""
innesto = """		/* ⛔⛔ GUASTO INNESTATO — 06-b34-guasti.sh «tasti-col-vecchio».
		 *     NON e' codice di prodotto: sta solo nell'albero della copia.
		 *     «I tasti se ne sono andati col dispositivo»: al posto di
		 *     `segna_orfani()` si azzera la mappa, cioe' esattamente la riga
		 *     che il commento di `input.c` dichiara di NON scrivere.
		 *   ⇒ ATTESO: nessuna riga «erano PREMUTI sul dispositivo che il
		 *     compositore ha appena tolto», nessuna riga sugli ORFANI, e
		 *     «rilascio al distacco: 0» — cioe' uno ZERO che si legge come
		 *     «non c'era niente premuto». */
		memset(in->tasti, 0, sizeof in->tasti);
		in->quanti_tasti = 0;
		ei_device_unref(in->tastiera_dev);
		in->tastiera_dev = NULL;
		in->tastiera_attiva = FALSE;
		in->ricambi_tastiera++;"""
if ancora not in s:
    print("⛔ ancora non trovata in input.c"); sys.exit(3)
open(p, "w", encoding="utf-8").write(s.replace(ancora, innesto, 1))
print("innestato")
PY
	verifica_innesto "$GUASTO/src/input.c" "GUASTO INNESTATO"
	costruisci
	accendi_con "$GUASTO" "GUASTO B (i tasti se ne vanno col dispositivo)"
	sleep 2
	bash "$TERRENO" testimone >/dev/null 2>&1
	log "…e adesso il caso 4, che DEVE diventare rosso in 4b"
	pretendi_rosso caso4 ;;

senza-cura)
	# ⛔⛔ GUASTO C — «la disposizione dichiarata NON si applica», cioe' §5-bis.7
	#     TOLTA.  ⚠ Vive in `src/rcp.c`, che qui e' una COPIA.
	#
	# ⭐ Perche' serve, e non e' una formalita': il caso 7 e' uscito VERDE su
	#    cinque disposizioni esotiche.  Finche' nessuno gli ha fatto fare rosso,
	#    «la disposizione viene rinegoziata» e «quei caratteri arrivano
	#    comunque» hanno lo stesso colore (`CODER.md` §3.4).
	log "GUASTO C — «la cura di §5-bis.7 TOLTA» (src/rcp.c, la COPIA)"
	inf "ATTESO dichiarato PRIMA: il caso 7 diventa ROSSO su TUTTE le esotiche."
	inf "   La sessione resta «it», e i caratteri esotici NON sono producibili:"
	inf "   arriva «aa» invece di «aűa», «11» invece di «1α1» — e il registro"
	inf "   scrive «U+0171 non e' producibile».  ⚠ Il canarino c'e' lo stesso,"
	inf "   quindi la prova e' ROSSA e non INVALIDA: e' esattamente la"
	inf "   distinzione che «06-b34-leggi.py» esiste per fare."
	inf "⛔ E il caso 7-neg deve restare VERDE: guasta o no, la ű su «it» non"
	inf "   arriva.  ⇒ Un controllo negativo che diventasse rosso qui direbbe"
	inf "   che stava misurando un'altra cosa."
	rifai_copia
	python3 - "$GUASTO/src/rcp.c" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
ancora = """static void applica_disposizione(rcp_sessione *s, const char *perche)
{
	if (!s->disposizione[0])
		return;
"""
innesto = """static void applica_disposizione(rcp_sessione *s, const char *perche)
{
	if (!s->disposizione[0])
		return;
	/* ⛔⛔ GUASTO INNESTATO — 06-b34-guasti.sh «senza-cura».
	 *     NON e' codice di prodotto: sta solo nell'albero della copia.
	 *     E' §5-bis.7 tolta: la disposizione dichiarata si registra e non si
	 *     chiede mai al palco.  ⚠ Il registro tace, ed e' apposta: il guasto
	 *     da riprodurre e' quello di PRIMA della cura, che era silenzioso. */
	if (1)
		return;
"""
if ancora not in s:
    print("⛔ ancora non trovata in rcp.c"); sys.exit(3)
open(p, "w", encoding="utf-8").write(s.replace(ancora, innesto, 1))
print("innestato")
PY
	verifica_innesto "$GUASTO/src/rcp.c" "GUASTO INNESTATO"
	# ⛔ E il GEMELLO va guastato allo stesso modo, o `Makefile:96` rifiuta di
	#    compilare: `src/rcp.c` e `banchi/rcp/rcp.c` devono combaciare byte per
	#    byte (R12.3).  ⚠ Senza questa riga il controllo positivo fallirebbe
	#    per una ragione che non c'entra niente col guasto.
	cp "$GUASTO/src/rcp.c" "$GUASTO/banchi/rcp/rcp.c"
	costruisci
	accendi_con "$GUASTO" "GUASTO C (§5-bis.7 tolta)"
	sleep 2
	bash "$TERRENO" testimone >/dev/null 2>&1
	log "…e adesso il caso 7, che DEVE diventare rosso"
	pretendi_rosso caso7 ;;

forma-aperta)
	# ⛔⛔ GUASTO D — «il controllo di forma non controlla niente».
	#
	# ⭐ Il caso 8 e' gia' certificato per meta' da un rosso VERO: col binario
	#    di ieri sei righe erano rosse (`de(T3)` e compagni prendevano 0x0B).
	#    ⛔ Ma l'ALTRA meta' — le righe che devono essere RIFIUTATE — non e'
	#      mai stata vista rossa, e un banco che non sa diventare rosso da
	#      quella parte non prova che la difesa ci sia ancora.
	log "GUASTO D — «la forma non si controlla» (src/rcp.c, la COPIA)"
	inf "ATTESO dichiarato PRIMA: il caso 8 diventa ROSSO sulle righe «fuori"
	inf "   forma», che prenderanno 0x0E (o apriranno) invece di 0x0B."
	inf "⛔ E «../../etc/passwd» arriverebbe dentro la macchina degli include di"
	inf "   XKB: e' precisamente la cosa che quella funzione protegge."
	rifai_copia
	python3 - "$GUASTO/src/rcp.c" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
ancora = """	/* §4.5: un nome XKB, eventualmente con la variante fra parentesi. */
	if (n < 1 || n > 64)
		return false;
"""
innesto = ancora + """	/* ⛔⛔ GUASTO INNESTATO — 06-b34-guasti.sh «forma-aperta».
	 *     NON e' codice di prodotto: sta solo nell'albero della copia.
	 *     La forma non si guarda: qualunque stringa lunga da 1 a 64 byte
	 *     passa, e la sola difesa resta quel che XKB si rifiuta di aprire. */
	return true;
"""
if ancora not in s:
    print("⛔ ancora non trovata in rcp.c"); sys.exit(3)
open(p, "w", encoding="utf-8").write(s.replace(ancora, innesto, 1))
print("innestato")
PY
	verifica_innesto "$GUASTO/src/rcp.c" "GUASTO INNESTATO"
	cp "$GUASTO/src/rcp.c" "$GUASTO/banchi/rcp/rcp.c"
	costruisci
	accendi_con "$GUASTO" "GUASTO D (la forma non si controlla)"
	sleep 2
	bash "$TERRENO" testimone >/dev/null 2>&1
	log "…e adesso il caso 8, che DEVE diventare rosso sulle «fuori forma»"
	pretendi_rosso caso8 ;;

sano)
	log "Rimetto il binario SANO"
	accendi_con "$SANO" "SANO"
	sleep 2
	bash "$TERRENO" testimone >/dev/null 2>&1
	ok "il banco e' tornato sul prodotto vero"
	exit 0 ;;

*)
	inf "usa: keymap-una-volta · tasti-col-vecchio · sano"
	exit 2 ;;
esac
