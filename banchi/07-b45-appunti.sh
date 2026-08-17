#!/usr/bin/env bash
#
# 07-b45 — IL BANCO DEGLI APPUNTI, nei due versi.  `RCP.md` §7.4, fase 7.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ L'ARBITRO NON E' `xclip`, E LA RAGIONE E' UNA MISURA — 17 agosto 2026
#
# `fasi/07-audio-e-appunti.md` §2.4 prometteva un arbitro gratis: «su GNOME la
# sponda X11 di Mutter e' incondizionata nei due versi ⇒ `xclip` funziona senza
# una nostra sessione» (`STUDI.md` §gnome §10 `[R]`).
#
# ⛔ **E' vero del CODICE di Mutter e falso delle NOSTRE sessioni.**  `[M]` 17
#    agosto 2026: `ps` dice che il compositore gira come
#
#        gnome-shell --headless --no-x11
#
#    ⇒ **XWayland non parte affatto**, quindi non c'e' nessuna sponda X11 da
#    usare, e `xclip` non ha un display a cui parlare.  ⚠ I due socket in
#    `/tmp/.X11-unix` sono AVANZI del 15 agosto: un banco che li avesse presi
#    per buoni avrebbe misurato una sessione morta e chiamato rosso il prodotto.
#
# ⭐⭐ E L'ARBITRO GIUSTO E' MIGLIORE DI QUELLO CHE AVEVAMO PROMESSO.
#
#     Le applicazioni del desktop non parlano X11: sono client Wayland, e la
#     clipboard la prendono con `wl_data_device`.  ⇒ L'arbitro e' **GTK/GDK**,
#     chiamato da `python3-gi`: un client Wayland normale, che non e' nostro e
#     che percorre **la stessa strada di un'applicazione vera** — mentre `xclip`
#     avrebbe provato una sponda che i nostri utenti non hanno.
#
# ⛔ E i DUE LATI restano due implementazioni diverse, che e' quel che conta:
#     · **GTK**, che non e' nostro e non ha mai sentito parlare di RCP;
#     · `01-b3-cliente.py`, che e' in Python e ha letto solo `RCP.md`
#       (`PIANO.md` §1.1 — il secondo lettore).
#   Il server sta in mezzo e non sa che e' un banco.
#
# ⚠ `wl-copy` C'E' sulla macchina ed e' stato scartato: parla
#   `zwlr_data_control_manager_v1`, che e' di wlroots e **su GNOME non esiste**
#   (`LEZIONI.md` §3 domanda 14).  Un arbitro che fallisce sempre darebbe rosso
#   a ogni giro, e il rosso sarebbe suo.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LE TRE REGOLE CHE VENGONO DA TRE DIFETTI VERI DI v1 — `PIANO.md` §Fase 7
#
#  1. ⛔ **I due lati si sincronizzano con MARCATORI, non con `sleep`.**
#     `LEZIONI.md` §2.3-quinquies: al banco degli appunti di KDE i due lati
#     erano sfasati di **tredici secondi** — il client copiava *prima* che la
#     sessione avesse copiato, la sessione incollava *prima* che il client
#     avesse annunciato — e il controllo dava **rosso su codice che
#     funzionava**.  ⇒ Qui ogni passo aspetta un FILE che l'altro lato scrive.
#
#  2. ⚠ **La clipboard si SVUOTA all'inizio di ogni giro.**  Stesso §2.3-
#     quinquies, il corollario: quel che resta dal giro prima viene annunciato
#     alla connessione **e sembra un risultato**.  ⇒ Ogni giro comincia
#     svuotando, e CONTROLLA di aver svuotato.
#
#  3. ⛔ **Il marcatore e' UNICO per giro**, e non e' una formalita': con la
#     stessa stringa in due giri, il testo del giro prima passa per il
#     risultato del giro dopo — la forma esatta del difetto 2, travestita.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔ PORTA, BAN-FILE, SOCKET E ALBERO PROPRI — la regola dei banchi in parallelo
#
# Il ban di §4.4-bis e' per INDIRIZZO e dura 12 ore: un banco che lo fa scattare
# mette fuori uso tutti gli altri, perche' partono tutti dallo stesso indirizzo.
# ⚠ La 7448, la 7700, la 7710 e la 7720 NON si toccano: sono di chi sta gia'
#   lavorando.  Questo banco usa la **7730**.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⏳ E QUESTO BANCO NON E' MAI STATO GIRATO — 17 agosto 2026
#
# ⛔ Va scritto qui e non altrove, perche' chi lo legge deve saperlo prima di
#    credergli: `CODER.md` §3.3 — «il banco si certifica prima della misura».
#    ⚠ In particolare **`DISPLAY` non e' stato misurato**: la sponda X11 di
#      Mutter esiste `[R]`, ma su quale numero di display la sessione headless
#      di `prova` la esponga e' `[?]`.  ⇒ Il passo 0 la CERCA, e se non la
#      trova **si ferma** invece di provare `:0` e chiamare rosso quel che e'
#      «non ho potuto guardare» (`LEZIONI.md` §1.9 regola 1).
#
# Uso:  bash banchi/07-b45-appunti.sh [--porta 7730] [--solo verso1|verso2]
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA=${PAROLA:-nicfio}
UTENTE=${UTENTE:-prova}
PAROLA_PROVA=${PAROLA_PROVA:-prova2026}
PORTA=7730
SOLO=tutto

while [ $# -gt 0 ]; do
	case "$1" in
	--porta) PORTA=$2; shift 2 ;;
	--solo) SOLO=$2; shift 2 ;;
	*) echo "⛔ argomento ignoto: $1" >&2; exit 2 ;;
	esac
done

QUI=$(cd "$(dirname "$0")/.." && pwd)
LAV=/media/REMOTIX/tmp/07-appunti
GIRO=$(date +%s)

verde() { printf '   ✅ %s\n' "$*"; }
giallo() { printf '   ⚠  %s\n' "$*"; }
rosso() { printf '   ⛔ %s\n' "$*"; }

ESITI=0
FALLITI=0
conta() { ESITI=$((ESITI + 1)); [ "$1" = "no" ] && FALLITI=$((FALLITI + 1)); return 0; }

# ═══════════════════════════════════════════════════════════════════════════
# PASSO 0 — SI CERCA LA SPONDA X11, E SE NON C'E' CI SI FERMA
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ «Non ho trovato il display» e «gli appunti non funzionano» sono due fatti
#    diversi, e con lo stesso rosso sarebbero indistinguibili.  ⇒ Qui si esce
#    con un codice SUO (3), e la riga dice che cosa manca.
echo "⏳ 0/5 · cerco la sponda X11 della sessione di «$UTENTE»"
DISPLAY_TROVATO=$(ssh -o BatchMode=yes "$MACCHINA" "
  printf '%s\n' '$PAROLA' | sudo -S -p '' bash -c '
    UID_B=\$(id -u $UTENTE 2>/dev/null) || exit 1
    # ⛔ Si CHIEDE al nucleo quali socket X esistono, invece di indovinare «:0»:
    #    su una macchina con piu\" di una sessione grafica il numero cambia, e un
    #    numero indovinato darebbe «la clipboard non risponde» su una sponda
    #    perfettamente viva.
    for s in /tmp/.X11-unix/X*; do
      [ -e \"\$s\" ] || continue
      printf \":%s\n\" \"\${s##*/X}\"
    done
  ' 2>/dev/null" | head -1)

if [ -z "$DISPLAY_TROVATO" ]; then
	rosso "nessuna sponda X11 su quella macchina: /tmp/.X11-unix e' vuota."
	giallo "NON e' un rosso sugli appunti: e' «non ho potuto guardare»."
	giallo "⇒ La sessione grafica di «$UTENTE» dev'essere in piedi, e con lei"
	giallo "  XWayland.  Si accende collegandosi una volta col browser."
	exit 3
fi
verde "sponda X11: DISPLAY=$DISPLAY_TROVATO"

# La funzione che gira DENTRO la sessione dell'utente, con l'ambiente composto
# da zero (`CODER.md` §4.5).  ⚠ Stessa forma di `07-b43`, e non si reinventa.
nella_sessione() {
	local comando="$1"
	ssh -o BatchMode=yes "$MACCHINA" "
	  printf '%s\n' '$PAROLA' | sudo -S -p '' bash -c '
	    UID_B=\$(id -u $UTENTE)
	    setpriv --reuid=\"\$UID_B\" --regid=\"\$UID_B\" --init-groups \
	      env -i HOME=/home/$UTENTE USER=$UTENTE LANG=C.UTF-8 \
	      PATH=/usr/local/bin:/usr/bin:/bin \
	      XDG_RUNTIME_DIR=/run/user/\$UID_B \
	      DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/\$UID_B/bus \
	      DISPLAY=$DISPLAY_TROVATO \
	      bash -c $(printf '%q' "$comando")
	  '"
}

if ! nella_sessione 'command -v xclip >/dev/null' ; then
	rosso "«xclip» non c'e' sulla macchina di prova: l'arbitro esterno manca."
	giallo "⇒ apt-get install xclip, e si rigira.  ⛔ NON si ripiega su un"
	giallo "  secondo pezzo nostro: due nostri che vanno d'accordo non"
	giallo "  confermano niente (PIANO.md §0.4)."
	exit 3
fi
verde "xclip c'e'"

# ═══════════════════════════════════════════════════════════════════════════
# PASSO 1 — SI SVUOTA LA CLIPBOARD, E SI CONTROLLA CHE SIA VUOTA
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Regola 2.  ⚠ E il controllo NON e' un lusso: `xclip -i /dev/null` puo'
#    riuscire e lasciare la selezione com'era, e allora quel che resta dal giro
#    prima verrebbe annunciato alla connessione **e sembrerebbe un risultato**.
svuota_e_controlla() {
	nella_sessione 'printf "" | xclip -selection clipboard -i 2>/dev/null; sleep 0.3' >/dev/null 2>&1
	local resta
	resta=$(nella_sessione 'xclip -selection clipboard -o 2>/dev/null | head -c 200' 2>/dev/null)
	if [ -n "$resta" ]; then
		rosso "la clipboard NON si e' svuotata: c'e' ancora «${resta:0:60}»"
		giallo "⛔ Il giro NON parte: quel che resta verrebbe scambiato per un"
		giallo "  risultato (LEZIONI.md §2.3-quinquies)."
		return 1
	fi
	return 0
}

echo "⏳ 1/5 · svuoto la clipboard della sessione"
if ! svuota_e_controlla; then exit 4; fi
verde "clipboard vuota"

# ═══════════════════════════════════════════════════════════════════════════
# PASSO 2 — IL SERVER, SULLA SUA PORTA
# ═══════════════════════════════════════════════════════════════════════════
echo "⏳ 2/5 · accendo il server sulla $PORTA (albero e ban-file propri)"
bash "$QUI/banchi/07-b41-accendi.sh" --porta "$PORTA" --hz 0 || {
	rosso "il server non e' partito: niente da misurare"
	exit 5
}

# ═══════════════════════════════════════════════════════════════════════════
# PASSO 3 — VERSO 1: LA SESSIONE COPIA, IL CLIENTE LEGGE
# ═══════════════════════════════════════════════════════════════════════════
#
#   xclip (arbitro esterno) → Mutter → appunti.c → figlio → padre → §7.4 →
#   cliente di prova (secondo lettore di RCP.md)
#
# ⛔ E L'ORDINE E' QUESTO E NON L'ALTRO: si copia PRIMA che il cliente si
#    attacchi.  ⚠ Cosi' si prova anche la riga che conta di piu' — quella di
#    `STUDI.md` §gnome §10: `EnableClipboard` con opzioni vuote fa arrivare
#    `SelectionOwnerChanged` **subito**, ed e' cosi' che **chi si ricollega
#    ritrova gli appunti**.  Copiando dopo l'attacco, quella riga non verrebbe
#    mai provata e il difetto comparirebbe solo dall'utente.
verso1() {
	local marca="REMOTIX-b45-verso1-$GIRO"
	local esito=/tmp/07-b45-verso1.json

	echo
	echo "══ VERSO 1 · la sessione copia, il dispositivo legge ══"
	if ! svuota_e_controlla; then conta no; return; fi

	# ⛔ Il marcatore va nella clipboard PRIMA dell'attacco: vedi sopra.
	#    ⚠ `xclip` resta in vita a servire la selezione, quindi si lascia
	#      staccato dal terminale — o l'ssh non torna mai.
	nella_sessione "printf '%s' '$marca' | xclip -selection clipboard -i >/dev/null 2>&1 &
	                sleep 0.5" >/dev/null 2>&1

	local visto
	visto=$(nella_sessione 'xclip -selection clipboard -o 2>/dev/null')
	if [ "$visto" != "$marca" ]; then
		rosso "l'arbitro non ha copiato: la clipboard dice «${visto:0:60}»"
		giallo "⛔ Questo NON e' un rosso sul prodotto: e' il banco che non ha"
		giallo "  messo la scena.  I due casi hanno lo stesso sintomo, e questa"
		giallo "  riga e' quel che li separa (CODER.md §3.10)."
		conta no; return
	fi
	verde "l'arbitro ha copiato «$marca» nella sessione"

	rm -f "$esito"
	python3 "$QUI/banchi/01-b3-cliente.py" \
		--indirizzo "${MACCHINA#*@}" --porta "$PORTA" \
		--utente "$UTENTE" --parola "$PAROLA_PROVA" \
		--appunti-attendi 8 --appunti-scrivi "$esito" \
		--resta 2 2>&1 | sed 's/^/      /'

	if [ ! -f "$esito" ]; then
		rosso "il cliente di prova non ha scritto nessun esito"
		conta no; return
	fi

	python3 - "$esito" "$marca" <<'FINE'
import json, sys
e = json.load(open(sys.argv[1])); marca = sys.argv[2]
male = []
# ⛔ I TRE FATTI, E RESTANO TRE.  «Nessun annuncio», «annuncio senza testo» e
#    «testo diverso» hanno lo stesso sintomo — l'utente incolla e non trova
#    niente — e un verdetto solo li renderebbe indistinguibili.
if not e["annunci_dal_server"]:
    male.append("nessun ANNUNCIO dal server: la sessione ha copiato e il filo tace")
elif e["ricevuto"] is None:
    male.append("l'annuncio e' arrivato e il TESTO no: il tiro di §7.4 non chiude")
elif e["ricevuto"] != marca:
    male.append("il testo e' arrivato DIVERSO: «%s» invece di «%s»"
                % (e["ricevuto"][:60], marca))
# ⛔ E le violazioni bocciano anche un giro che consegna il testo giusto:
#    «funziona» non e' «e' conforme» (REVIEWER.md §5).
for v in e["violazioni"]:
    male.append("§7.4 violata: " + v)
for m in male:
    print("   ⛔ " + m)
if not male:
    n = e["annunci_dal_server"][0]
    print("   ✅ annuncio %d di %d byte, testo identico al marcatore" % (n[0], n[1]))
sys.exit(1 if male else 0)
FINE
	# ⛔ L'esito del giudice si prende SUBITO e in una variabile: `$?` dentro
	#    una sostituzione di comando e' gia' un'altra cosa, ed e' la trappola
	#    che fa dire verde a un banco rosso.
	if [ "$?" -eq 0 ]; then conta si; else conta no; fi
}

# ═══════════════════════════════════════════════════════════════════════════
# PASSO 4 — VERSO 2: IL DISPOSITIVO COPIA, LA SESSIONE INCOLLA
# ═══════════════════════════════════════════════════════════════════════════
#
#   cliente di prova → §7.4 → padre → figlio → appunti.c → Mutter →
#   xclip -o (arbitro esterno)
#
# ⛔ ED E' IL VERSO CHE SI USA DI PIU' (`DECISIONI.md` §5-ter.1: «copio un
#    indirizzo sul telefono e lo incollo nel browser remoto»), ed e' quello che
#    costa piu' lavoro: di la' il testo ce l'abbiamo gia', di qua bisogna andarlo
#    a chiedere mentre qualcuno sta aspettando.
#
# ⛔ E IL MARCATORE DI SINCRONIA E' IL FILE `--segnale`: il cliente lo scrive
#    quando la sessione e' aperta, e `xclip -o` parte SOLO dopo.  ⚠ Senza,
#    `xclip -o` chiederebbe la selezione quando nessuno la offre ancora — e la
#    risposta sarebbe vuota su codice che funziona (regola 1).
verso2() {
	local marca="REMOTIX-b45-verso2-$GIRO"
	local esito=/tmp/07-b45-verso2.json
	local segnale=/tmp/07-b45-verso2.attaccato

	echo
	echo "══ VERSO 2 · il dispositivo copia, la sessione incolla ══"
	if ! svuota_e_controlla; then conta no; return; fi

	rm -f "$esito" "$segnale"
	python3 "$QUI/banchi/01-b3-cliente.py" \
		--indirizzo "${MACCHINA#*@}" --porta "$PORTA" \
		--utente "$UTENTE" --parola "$PAROLA_PROVA" \
		--appunti-copia "$marca" --appunti-scrivi "$esito" \
		--segnale "$segnale" --resta 10 2>&1 | sed 's/^/      /' &
	local PIDCLI=$!

	# ⛔ Si aspetta il MARCATORE, non un `sleep`: regola 1.
	local i=0
	while [ ! -f "$segnale" ] && [ $i -lt 100 ]; do i=$((i + 1)); sleep 0.2; done
	if [ ! -f "$segnale" ]; then
		rosso "il cliente non si e' mai attaccato: niente da incollare"
		kill "$PIDCLI" 2>/dev/null; wait "$PIDCLI" 2>/dev/null
		conta no; return
	fi
	verde "il cliente e' attaccato e ha annunciato il suo testo"

	# ⚠ Un respiro perche' l'annuncio finisca di attraversare padre → figlio →
	#   `SetSelection`.  ⛔ E NON e' un `sleep` di sincronia fra i due lati —
	#   quello lo fa il segnale qui sopra: e' il tempo di UN passaggio noto, e
	#   il controllo che segue lo dichiara se non basta.
	sleep 1

	local letto
	letto=$(nella_sessione 'timeout 8 xclip -selection clipboard -o 2>/dev/null')

	if [ "$letto" = "$marca" ]; then
		verde "la sessione ha incollato «$letto» — identico"
		conta si
	elif [ -z "$letto" ]; then
		rosso "la sessione ha incollato IL VUOTO: il tiro non e' arrivato"
		giallo "⛔ Da guardare, in quest'ordine: il registro del figlio dice"
		giallo "  «sta incollando»?  E il padre dice «chiesto al client»?"
		conta no
	else
		rosso "la sessione ha incollato «${letto:0:60}» invece di «$marca»"
		conta no
	fi

	kill "$PIDCLI" 2>/dev/null; wait "$PIDCLI" 2>/dev/null
	if [ -f "$esito" ]; then
		python3 - "$esito" <<'FINE'
import json, sys
e = json.load(open(sys.argv[1]))
print("   · il server ha chiesto i trasferimenti: %s" % (e["chiesti_dal_server"] or "NESSUNO"))
print("   · serviti dal cliente: %d" % e["serviti_al_server"])
for v in e["violazioni"]:
    print("   ⛔ §7.4 violata: " + v)
FINE
	fi
}

echo "⏳ 3/5 · i due versi"
# ⛔ Due `if` e non `A || B && C`: in shell quella forma lega `&&` all'ULTIMO
#    confronto, quindi con `--solo verso2` avrebbe girato anche il verso 1.
#    ⚠ Un banco che gira piu' prove di quelle chieste non e' generoso: e' un
#      banco che misura una scena diversa da quella dichiarata.
if [ "$SOLO" = "tutto" ] || [ "$SOLO" = "verso1" ]; then verso1; fi
if [ "$SOLO" = "tutto" ] || [ "$SOLO" = "verso2" ]; then verso2; fi

# ═══════════════════════════════════════════════════════════════════════════
# PASSO 5 — IL REGISTRO DEL SERVER, CHE E' L'ALTRA META' DELLA DIAGNOSI
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Un banco che guarda solo il proprio esito sa DIRE che qualcosa non va e non
#    sa dire DOVE: le righe di `REG_APPUNTI` nominano il punto esatto in cui il
#    testo si e' fermato (`LEZIONI.md` §2.7 — «monitorare una sessione vera,
#    byte per byte, e' la miglior diagnosi che ci sia»).
echo
echo "⏳ 4/5 · le righe degli appunti nel registro del server"
ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA' | sudo -S -p '' grep -E 'appunti|APPUNTI' $LAV/registro.log 2>/dev/null | tail -30" \
	| sed 's/^/      /' || giallo "nessuna riga (o registro non leggibile)"

echo
echo "⏳ 5/5 · esito"
if [ "$FALLITI" = 0 ] && [ "$ESITI" -gt 0 ]; then
	printf '   ⭐⭐ VERDE — %d prove su %d\n' "$ESITI" "$ESITI"
	exit 0
fi
printf '   ⛔ ROSSO — %d falliti su %d\n' "$FALLITI" "$ESITI"
exit 1
