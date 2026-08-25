#!/usr/bin/env bash
#
# ===========================================================================
# 10-b0-terreno.sh — ⛔ IL CONTROLLO DEL TERRENO DELLA FASE 10.
#
# Lo chiama OGNI banco della fase 10 **prima** di misurare, e ⛔ **fa fallire
# il banco** invece di lasciarlo partire su un terreno sporco.
#
#     Esce 0  il terreno regge, su quel che ha potuto guardare
#     Esce 1  ⛔ IL TERRENO NON REGGE: quel che ne uscirebbe non parlerebbe
#             del prodotto
#     Esce 2  ⛔ NON HO POTUTO VERIFICARE — ed e' il terzo esito, non un verde
#
# ---------------------------------------------------------------------------
# ⭐ COME LO SI CHIAMA DA UN ALTRO BANCO
#
#   CHI=10-a4 PORTA=7940 UTENTE=provadec4 \
#   ALBERO=/media/REMOTIX/src/10a4-src LAV=/media/REMOTIX/tmp/10a4 \
#     bash banchi/10-b0-terreno.sh || exit 1
#
# Le variabili d'ambiente, tutte per intero:
#
#   CHI              ⛔ OBBLIGATORIA · chi sei (la stessa sigla del lucchetto,
#                    es. `10-a7`).  Senza, «un remotix che non e' mio» non si
#                    puo' distinguere da «il mio».
#   PORTA            ⛔ OBBLIGATORIA · la porta del TUO server.
#   UTENTE           ⛔ OBBLIGATORIA · l'utente di cui il banco sta per usare
#                    il posto.
#   ALBERO           ⛔ OBBLIGATORIA · l'albero sulla macchina di prova
#                    (`/media/REMOTIX/src/…`), quello che porta `src/remotix`.
#   LAV              la cartella di lavoro   (def. /media/REMOTIX/tmp/$CHI)
#   REPO             l'albero LOCALE da cui hai spedito i sorgenti
#                    (def. la radice di questo repo)
#   MACCHINA         (def. nicfio@192.168.0.2)
#   PAROLA_SUDO      (def. nicfio) — passata sempre sullo stdin, mai in argv
#   IND              l'indirizzo da cui parti, per il ban (def. 192.168.0.2)
#   LUCCHETTO        (def. /media/REMOTIX/tmp/.lucchetto-gpu.d)
#   LUCCHETTO_MIO    ⭐ 1 se da questo giro esce un numero che riferirai: allora
#                    il lucchetto della GPU **dev'essere tuo**, e libero non
#                    basta.  0 (predefinito) per lo sviluppo e la messa a punto.
#   PORTE_AMMESSE    le porte 7xxx/8xxx di ALTRI che tolleri, separate da spazi.
#                    ⚠ Si stampano sempre: tacerle sarebbe la forma cattiva.
#   PALCO_AMMESSO    1 se il banco SI ASPETTA un palco gia' montato per UTENTE.
#                    ⚠ Si dichiara e si vede; il predefinito e' che non ci sia.
#   BAN_FILE         (def. $LAV/ban)
#   PCI_INTEGRATA    (def. 0000:00:02.0)   ⚠ l'INDIRIZZO, non `renderD128`
#   PCI_DISCRETA     (def. 0000:03:00.0)   ⚠ idem, e §4.6-quinquies la chiude
#   GRUPPO_NOGPU     (def. remotix-nogpu)
#   CARICO_MAX       (def. 6.0) — su 20 filiere
#   MEM_MIN_MB       (def. 2000)
#   IFACCIA          l'interfaccia vera    (def. enp7s0)
#
# E il modo che certifica se stesso:
#
#   bash banchi/10-b0-terreno.sh --certifica
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE, e la ragione e' stata pagata due volte in un giorno solo
#
# `banchi/01-b0-terreno.sh` e' nato l'11 agosto 2026 perche' due volte, nello
# stesso giorno, **un banco e' stato verde su un terreno che non era quello che
# credevamo** — e la prima volta che e' entrato nel giro si e' rifiutato di
# partire in mezzo secondo dicendo *«il server misura una versione che nessuno
# sta leggendo»*.  Questo file e' quello, portato alla fase 10.
#
# ⛔⛔ E LA FASE 10 HA UNA CONDIZIONE NUOVA, CHE E' LA PIU' IMPORTANTE DI TUTTE:
#      **la GPU e' UNA, e nove agenti la vogliono a turno.**  Un banco che
#      misura la GPU mentre un altro la satura non da' rosso — da' **un numero
#      plausibile e falso** (`LEZIONI.md` §1.26).  Per questo il lucchetto e'
#      il secondo controllo, non l'ultimo.
#
# ---------------------------------------------------------------------------
# ⚠⚠ CHE COSA QUESTO CONTROLLO **NON** SA VEDERE — detto prima, non dopo
#
# Un controllo che non dichiara i propri buchi e' un controllo che rassicura.
# Questi sono i suoi, e sono nove:
#
#  1. ⛔ **NON dice che il server e' CORRETTO.**  Dice che e' **quello
#     dichiarato**: i pezzi ci sono, il binario e' piu' nuovo dei sorgenti che
#     dice di portare, nessun guasto e' rimasto addosso.  Un server puo'
#     passare tutto questo ed essere pieno di difetti: e' quel che i banchi
#     cercano.  Qui si controlla soltanto che cerchino nel posto giusto.
#
#  2. ⛔ **NON vede il carico della GPU**, solo il lucchetto che lo governa.
#     `intel_gpu_top` non c'e' su questa macchina, e l'occupazione dei motori
#     si leggerebbe da `/proc/<pid>/fdinfo/<fd>` (`drm-engine-*`), che va
#     **tarata** prima di crederci.  ⇒ Un agente che misura sulla GPU **senza**
#     prendere il lucchetto e' invisibile a questo controllo: il lucchetto e'
#     una convenzione fra noi, non un vincolo del nucleo.
#
#  3. ⚠ **NON vede il ban VIVO NELLA MEMORIA di un server acceso**, solo il
#     file dei ban che sopravvive al riavvio.  §4.4-bis dice che il ban vive in
#     **due** posti; l'altro si interroga soltanto chiedendo lo sblocco, che e'
#     un atto — e un controllo del terreno **guarda**, non agisce.
#
#  4. ⚠ **NON vede un `netem` messo su un'interfaccia che non gli hai
#     nominato** (`IFACCIA=`), ne' uno strozzamento fatto altrove — sul tablet,
#     sul cavo, in un contenitore con la sua rete.
#
#  5. ⚠ **NON confronta i sorgenti che il PORTATILE non ha.**  Il confronto
#     `md5` e' locale↔remoto: un file che sta solo di la' viene **dichiarato**,
#     non giudicato, e uno che sta solo di qua e' rosso perche' il `tar` non
#     l'ha portato.
#
#  6. ⚠ **NON sa se un processo `remotix` di un altro agente sta MISURANDO o
#     sta solo acceso.**  §1.26 vieta di misurare in due, non di tenere acceso
#     il termine di paragone: per questo le porte tollerate si dichiarano da
#     fuori (`PORTE_AMMESSE`) e si **stampano**.
#
#  7. ⚠ **NON vede il carico di un altro agente che gira sul SUO portatile** —
#     un cliente `aioquic`, un browser guidato da Marionette.  Guarda la
#     macchina di prova, che e' il ferro che conta, ma la scena e' in due
#     pezzi.
#
#  8. ⚠ **NON garantisce che fra questo controllo e la misura non cambi
#     niente.**  E' una fotografia.  Il lucchetto e' l'unica parte che dura,
#     ed e' per questo che esiste.
#
#  9. ⛔ **NON vede la riga di comando con cui il server verra' acceso.**  `ldd`
#     lo legge con il `LD_LIBRARY_PATH` che i lanciatori esportano — ed e' quel
#     che lo porta a `b2`, perche' `[M]` il binario **non ha rpath**.  Un
#     lanciatore che dimenticasse quella variabile prenderebbe le librerie di
#     sistema, partirebbe benissimo e aborterebbe al primo che si collega:
#     questo controllo guarda il **binario**, non chi lo accende.
#
# 10. ⚠ **NON giudica `pagina.html` ne' `remotix.pam`**: il server li legge
#     all'AVVIO, non li compila dentro.  Uno di loro piu' nuovo del binario non
#     e' un binario stantio, e metterlo qui sarebbe un rosso puntato
#     sull'imputato sbagliato.
#
# ---------------------------------------------------------------------------
# ⛔ TRE ESITI, NON DUE — `LEZIONI.md` §1.29
#
# «None non e' zero, e *non ho letto* non e' *non e' successo niente*.»  Ogni
# predicato di questo file esce VERDE, ROSSO **oppure IGNOTO**, e un IGNOTO
# **fa fallire il banco** esattamente come un rosso: un banco che parte su
# «non ho potuto guardare» e' il banco che questo file esiste per fermare.
#
# ⛔ E la raccolta remota finisce con una riga sentinella, `FINE-RACCOLTA`:
#    un `ssh` che non risponde, un `sudo` che rifiuta, un comando troncato a
#    meta' danno tutti **uscita 0 con poche righe** — la faccia esatta di «va
#    tutto bene».  Senza sentinella, ogni predicato qui sotto sarebbe verde su
#    una macchina che non ha nemmeno risposto.
# ===========================================================================
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
REPO=${REPO:-$(cd "$QUI/.." && pwd)}

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
IND=${IND:-192.168.0.2}
LUCCHETTO=${LUCCHETTO:-/media/REMOTIX/tmp/.lucchetto-gpu.d}
LUCCHETTO_MIO=${LUCCHETTO_MIO:-0}
PORTE_AMMESSE=${PORTE_AMMESSE:-}
PALCO_AMMESSO=${PALCO_AMMESSO:-0}
PCI_INTEGRATA=${PCI_INTEGRATA:-0000:00:02.0}
PCI_DISCRETA=${PCI_DISCRETA:-0000:03:00.0}
GRUPPO_NOGPU=${GRUPPO_NOGPU:-remotix-nogpu}
CARICO_MAX=${CARICO_MAX:-6.0}
MEM_MIN_MB=${MEM_MIN_MB:-2000}
IFACCIA=${IFACCIA:-enp7s0}
SSH_TETTO=${SSH_TETTO:-25}

VERDE=$'\033[1;32m'; ROSSO=$'\033[1;31m'; GIALLO=$'\033[1;33m'
GRIGIO=$'\033[0m'; NETTO=$'\033[1m'
ok()  { printf '    %sOK%s  %s\n' "$VERDE" "$GRIGIO" "$*"; }
ko()  { printf '    %sNO%s  %s\n' "$ROSSO" "$GRIGIO" "$*"; }
dub() { printf '    %s??%s  %s\n' "$GIALLO" "$GRIGIO" "$*"; }
inf() { printf '    --  %s\n' "$*"; }
tit() { printf '\n%s%s%s\n' "$NETTO" "$*" "$GRIGIO"; }

# ── il registro degli esiti, leggibile da una macchina ─────────────────────
#    ⭐ Serve a `--certifica`: un guasto si innesta per UN predicato, e il conto
#       sano→guasto→risanato si fa su QUELLA sigla, non sul colore di tutto il
#       controllo.  Senza, un rosso qualunque farebbe passare la certificazione
#       di un predicato che non ha mai morso.
ESITI=$(mktemp) || { echo "⛔ nessun file temporaneo"; exit 2; }
trap 'rm -f "$ESITI" "${RACC:-}" "${COLL:-}"' EXIT
GUAI=0; IGNOTI=0; GUARDATI=0

verde() { GUARDATI=$((GUARDATI+1)); printf '%s\tVERDE\t%s\n' "$1" "$2" >>"$ESITI"; ok "[$1] $2"; }
rosso() { GUARDATI=$((GUARDATI+1)); GUAI=$((GUAI+1));
          printf '%s\tROSSO\t%s\n' "$1" "$2" >>"$ESITI"; ko "[$1] ⛔ $2"; }
ignoto(){ GUARDATI=$((GUARDATI+1)); IGNOTI=$((IGNOTI+1));
          printf '%s\tIGNOTO\t%s\n' "$1" "$2" >>"$ESITI"
          dub "[$1] ⛔ NON HO POTUTO VERIFICARE: $2"
          dub "     ⚠ e «non ho potuto guardare» non e' «va bene»"; }

# ===========================================================================
# --certifica: sta in fondo, ma si intercetta qui perche' rientra in questo
#              stesso file passandogli ambienti diversi.
# ===========================================================================
if [ "${1:-}" = "--certifica" ]; then
	rm -f "$ESITI"; trap - EXIT
	exec bash "$QUI/10-b0-certifica.sh" "${@:2}"
fi

# ── ⛔ LE TRE VARIABILI CHE NON HANNO UN PREDEFINITO ───────────────────────
#    Un predefinito qui sarebbe una scelta presa da chi ha scritto lo strumento
#    al posto di chi misura, e presa in silenzio: `CHI` decide che cosa vuol
#    dire «non e' mio», `PORTA` e `UTENTE` decidono di quale posto si parla.
manca=""
[ -n "${CHI:-}" ]    || manca="$manca CHI"
[ -n "${PORTA:-}" ]  || manca="$manca PORTA"
[ -n "${UTENTE:-}" ] || manca="$manca UTENTE"
[ -n "${ALBERO:-}" ] || manca="$manca ALBERO"
if [ -n "$manca" ]; then
	printf '⛔ mancano le variabili obbligatorie:%s\n' "$manca" >&2
	printf '   uso:  CHI=10-aN PORTA=79NN UTENTE=provadecN ALBERO=/media/REMOTIX/src/…-src \\\n' >&2
	printf '           bash %s\n' "$0" >&2
	exit 2
fi
LAV=${LAV:-/media/REMOTIX/tmp/$CHI}
BAN_FILE=${BAN_FILE:-$LAV/ban}

printf '\n%s== ⛔ IL TERRENO DELLA FASE 10 — %s, porta %s, utente %s%s\n' \
	"$NETTO" "$CHI" "$PORTA" "$UTENTE" "$GRIGIO"
inf "albero remoto: $ALBERO      repo locale: $REPO"
inf "lucchetto:     $LUCCHETTO   (dev'essere mio: $([ "$LUCCHETTO_MIO" = 1 ] && echo SI || echo no))"
inf "porte di altri tollerate: ${PORTE_AMMESSE:-nessuna}"

# ===========================================================================
# LA RACCOLTA REMOTA — un solo giro di ssh, e finisce con una SENTINELLA
# ===========================================================================
COLL=$(mktemp) || exit 2
cat >"$COLL" <<'RACCOLTA'
#!/usr/bin/env bash
# 10-b0-raccogli — la meta' che gira DA ROOT sulla macchina di prova.
# ⛔ Non giudica: raccoglie.  Il giudizio sta sul portatile, dove ci sono i
#    sorgenti con cui confrontare.  ⚠ E ogni riga che non ha potuto raccogliere
#    dice «-ignoto», che di la' diventa un IGNOTO e non uno zero.
export LC_ALL=C
TC=/usr/sbin/tc; [ -x "$TC" ] || TC=$(command -v tc)
r() { printf '%s\t%s\n' "$1" "$2"; }

r ORA "$(date +%s)"
r CARICO "$(cut -d' ' -f1-3 /proc/loadavg 2>/dev/null || echo -ignoto)"
r CPU "$(nproc 2>/dev/null || echo -ignoto)"
r MEM_MB "$(awk '/^MemAvailable:/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo -ignoto)"

# ── porte 7xxx/8xxx in ascolto ────────────────────────────────────────────
if p=$(ss -tuln 2>/dev/null); then
	printf '%s\n' "$p" | grep -oE ':(7[0-9]{3}|8[0-9]{3})\b' | tr -d ':' | sort -u | \
		while read -r x; do r PORTA_APERTA "$x"; done
	r PORTE_LETTE si
else
	r PORTE_LETTE no
fi

# ── i processi `remotix` vivi, e DI CHI SONO ──────────────────────────────
# ⛔ Niente `pgrep -f`: si acchiapperebbe da solo (il proprio argv contiene il
#    modello).  `ps` + `awk` sul percorso, e si escludono la raccolta stessa e
#    i figli, che sono il PALCO e si contano piu' sotto.
if ps -eo pid=,user=,args= >/tmp/.10b0.$$.ps 2>/dev/null; then
	awk -v mio=$$ '
		$1 == mio { next }
		/10-b0-raccogl/ { next }
		/remotix-figlio/ { next }
		/\/remotix( |$)/ {
			pid=$1; ut=$2; $1=""; $2=""; sub(/^ +/,"");
			printf "PROC_REMOTIX\t%s|%s|%s\n", pid, ut, $0 }
	' /tmp/.10b0.$$.ps
	r PROC_LETTI "$(wc -l </tmp/.10b0.$$.ps)"
else
	r PROC_LETTI -ignoto
fi

# ── il lucchetto della GPU: si LEGGE, non si prende ───────────────────────
if [ -d "$LUCCHETTO" ]; then
	if riga=$(cat "$LUCCHETTO/chi" 2>/dev/null) && [ -n "$riga" ]; then
		r LUC_STATO preso
		r LUC_SCAD "${riga%% *}"
		r LUC_CHI  "${riga#* }"
	else
		# ⚠ La cartella c'e' ma il nome no: qualcuno l'ha appena presa e non ha
		#   ancora scritto, oppure e' morto in mezzo.  Non e' «libero».
		r LUC_STATO illeggibile
	fi
else
	r LUC_STATO libero
fi

# ── le due schede, PER INDIRIZZO PCI ──────────────────────────────────────
# ⚠ `renderD128` e `renderD129` si scambiano fra un avvio e l'altro; l'indirizzo
#   PCI no.  Si parte da li' e si arriva al nodo, mai il contrario.
nodo_di() {
	local n
	n=$(readlink -f "/dev/dri/by-path/pci-$1-render" 2>/dev/null)
	[ -n "$n" ] && [ -e "$n" ] && printf '%s\n' "$n"
}
for pci in "$PCI_INTEGRATA" "$PCI_DISCRETA"; do
	n=$(nodo_di "$pci")
	if [ -z "$n" ]; then r NODO_MANCA "$pci"; continue; fi
	s=$(stat -c '%U|%G|%a' "$n" 2>/dev/null) || s='-ignoto|-ignoto|-ignoto'
	drv=$(basename "$(readlink -f "/sys/class/drm/$(basename "$n")/device/driver" 2>/dev/null)" 2>/dev/null)
	r NODO "$pci|$n|$s|${drv:--ignoto}"
done

# ── il recinto: il gruppo senza membri ────────────────────────────────────
if g=$(getent group "$GRUPPO_NOGPU" 2>/dev/null) && [ -n "$g" ]; then
	r GRUPPO "$(printf '%s' "$g" | awk -F: '{printf "%s|%s|%s", $1, $3, $4}')"
else
	r GRUPPO_MANCA "$GRUPPO_NOGPU"
fi
if [ -f /etc/udev/rules.d/99-remotix-gpu.rules ]; then
	r UDEV presente
	r UDEV_PCI "$(grep -o 'pci-[0-9a-f:.]*' /etc/udev/rules.d/99-remotix-gpu.rules | head -1 | sed 's/^pci-//')"
else
	r UDEV assente
fi

# ── ⛔ CHI TIENE APERTA LA DISCRETA — in fase 5 il compositore l'aveva presa
#    senza che nessuno lo avesse chiesto, e una misura intera e' stata fatta
#    sulla scheda sbagliata.  ⭐ E si conta QUANTI processi si sono guardati:
#    «nessuno la tiene aperta» non e' un dato finche' non dice su quanti.
#
# ⚠ E SI SETACCIA CON UN PROCESSO SOLO, non con un `readlink` per descrittore:
#   su questa macchina ci sono ~700 processi e ~14 000 descrittori, e un
#   `readlink` a testa vorrebbe dire quattordicimila forcate — cioe' il
#   controllo del terreno che mette carico sulla macchina che sta certificando
#   scarica.  `find -lname` fa la stessa cosa dentro un processo solo.
disc=$(nodo_di "$PCI_DISCRETA")
visti=$(ls -d /proc/[0-9]*/fd 2>/dev/null | wc -l)
if [ -z "$disc" ] || [ "$visti" -eq 0 ]; then
	r FD_SCANSIONE -ignoto
else
	find /proc/[0-9]*/fd -maxdepth 1 -lname "$disc" 2>/dev/null | \
		awk -F/ '{c[$3]++} END {for (p in c) print p, c[p]}' | \
		while read -r pid n; do
			r FD_DISCRETA "$pid|$(stat -c %U "/proc/$pid" 2>/dev/null)|$(cat "/proc/$pid/comm" 2>/dev/null)|$n"
		done
	r FD_SCANSIONE "$visti"
fi

# ── i guasti di rete rimasti addosso ──────────────────────────────────────
if [ -n "$TC" ]; then
	for i in lo "$IFACCIA"; do
		if q=$("$TC" qdisc show dev "$i" 2>/dev/null); then
			r TC "$i|$(printf '%s' "$q" | tr '\n' ' ')"
		else
			r TC "$i|-ignoto"
		fi
	done
else
	r TC "lo|-ignoto"; r TC "$IFACCIA|-ignoto"
fi
r IFB "$(ip -o link show type ifb 2>/dev/null | wc -l)"

# ── l'albero: md5, date, binario ──────────────────────────────────────────
if [ -d "$ALBERO/src" ]; then
	r ALBERO_C_E si
	for f in "$ALBERO"/src/*.c "$ALBERO"/src/*.h "$ALBERO/src/Makefile"; do
		[ -f "$f" ] || continue
		r MD5 "$(basename "$f")|$(md5sum "$f" 2>/dev/null | cut -d' ' -f1)"
		r TS  "$(basename "$f")|$(stat -c %Y "$f" 2>/dev/null)"
	done
	if [ -f "$ALBERO/src/remotix" ]; then
		r BIN_MD5 "$(md5sum "$ALBERO/src/remotix" | cut -d' ' -f1)"
		r BIN_TS  "$(stat -c %Y "$ALBERO/src/remotix")"
		# ⛔⭐ E `ldd` SI LEGGE CON L'AMBIENTE CHE AVRA' IL SERVER, non nudo.
		#
		#    `[M]` 24 agosto 2026, trovato mettendo in piedi questo controllo:
		#    il binario NON porta un rpath verso `b2` — nudo risolve
		#    `libngtcp2.so.16` da `/lib/x86_64-linux-gnu`, cioe' dal SISTEMA.
		#    Quel che lo porta a `b2` e' il `LD_LIBRARY_PATH` che i lanciatori
		#    esportano prima di `systemd-run`.  ⇒ Leggere `ldd` nudo darebbe
		#    ROSSO su ogni albero sano — un rosso su codice giusto, la forma
		#    di `LEZIONI.md` §2.3 — e leggerlo SOLO con l'ambiente nasconderebbe
		#    che la scelta dipende dal lanciatore.  ⭐ Si leggono TUTT'E DUE.
		B2=/media/REMOTIX/src/b2
		if u=$(LD_LIBRARY_PATH="$B2/ngtcp2/build/lib:$B2/prefisso/lib" \
		       ldd "$ALBERO/src/remotix" 2>&1); then
			r LDD_RC 0
			# ⚠ `ldd` indenta con una TABULAZIONE, e il formato di questa
			#   raccolta e' a tabulazioni: senza `tr` la riga si spaccherebbe
			#   in due campi e il giudizio la leggerebbe a meta'.
			printf '%s\n' "$u" | grep -E 'ngtcp2|nghttp3' | \
				while read -r l; do r LDD "$(printf '%s' "$l" | tr -s ' \t' ' ')"; done
		else
			r LDD_RC "$?"
		fi
		if u=$(env -u LD_LIBRARY_PATH ldd "$ALBERO/src/remotix" 2>&1); then
			printf '%s\n' "$u" | grep -E 'ngtcp2|nghttp3' | \
				while read -r l; do r LDD_NUDO "$(printf '%s' "$l" | tr -s ' \t' ' ')"; done
		fi
	else
		r BIN_MANCA "$ALBERO/src/remotix"
	fi
	# ⛔ Il posto e' uno solo per albero — ma il posto e' uno solo se i binari
	#    sono uno solo.  Si contano e si dicono; sceglierne uno sarebbe D5.
	t=$(find "$ALBERO" -maxdepth 3 -type f -name remotix -perm -u+x 2>/dev/null)
	if [ -z "$t" ]; then r BIN_CONTA 0; else
		r BIN_CONTA "$(printf '%s\n' "$t" | wc -l)"
		printf '%s\n' "$t" | while read -r l; do r BIN_DOVE "$l"; done
	fi
else
	r ALBERO_C_E no
fi

# ── il posto dell'utente: un palco orfano non da' rosso, da' un numero ────
if id "$UTENTE" >/dev/null 2>&1; then
	r UTENTE_C_E si
	r UTENTE_PROC "$(pgrep -u "$UTENTE" -c 2>/dev/null || echo 0)"
	# ⭐ `-x`: il nome ESATTO del programma, non un modello sulla riga di
	#    comando che acchiapperebbe anche questa raccolta.
	for c in gnome-shell kwin_wayland weston sway labwc; do
		for p in $(pgrep -u "$UTENTE" -x "$c" 2>/dev/null); do
			r PALCO "$p|$c|$(tr '\0' ' ' <"/proc/$p/cmdline" 2>/dev/null)"
		done
	done
	awk -v u="$UTENTE" '$2 == u && /remotix-figlio/ {
		pid=$1; $1=""; $2=""; sub(/^ +/,"");
		printf "PALCO\t%s|remotix-figlio|%s\n", pid, $0 }' /tmp/.10b0.$$.ps 2>/dev/null
else
	r UTENTE_C_E no
fi
# I clienti: si riconoscono dalla porta, non dall'utente (girano da chi li lancia)
awk -v mio=$$ -v porta="--porta $PORTA" '
	$1 == mio { next }
	/10-b0-raccogl/ { next }
	/b3-cliente|aioquic/ && index($0, porta) {
		pid=$1; $1=""; $2=""; sub(/^ +/,"");
		printf "CLIENTE\t%s|%s\n", pid, $0 }' /tmp/.10b0.$$.ps 2>/dev/null

# ── il ban di §4.4-bis, per INDIRIZZO e per dodici ore ────────────────────
if [ -f "$BAN_FILE" ]; then
	r BAN_FILE presente
	while read -r ind fino; do
		[ -n "${ind:-}" ] && r BAN "$ind|${fino:-0}"
	done <"$BAN_FILE"
else
	r BAN_FILE assente
fi

rm -f /tmp/.10b0.$$.ps
# ⛔ LA SENTINELLA.  Senza questa riga, un ssh troncato ha la faccia di «va
#    tutto bene»: uscita 0, poche righe, nessun errore.
r FINE-RACCOLTA ok
RACCOLTA

MD5_COLL=$(md5sum "$COLL" | cut -d' ' -f1)
RACC=$(mktemp) || exit 2

AMB="LUCCHETTO='$LUCCHETTO' PCI_INTEGRATA='$PCI_INTEGRATA' PCI_DISCRETA='$PCI_DISCRETA'"
AMB="$AMB GRUPPO_NOGPU='$GRUPPO_NOGPU' IFACCIA='$IFACCIA' ALBERO='$ALBERO'"
AMB="$AMB UTENTE='$UTENTE' PORTA='$PORTA' BAN_FILE='$BAN_FILE'"

REMOTO=/tmp/10-b0-raccogli.$$.sh
if ! timeout "$SSH_TETTO" ssh -o BatchMode=yes -o ConnectTimeout=8 "$MACCHINA" \
	"cat > $REMOTO" <"$COLL"; then
	tit "== la raccolta"
	ignoto T0 "il copione non e' arrivato sulla macchina di prova (ssh muto)"
	GUARDATI=1
	printf '\n    %s⛔ NON HO POTUTO VERIFICARE NIENTE: la macchina non ha risposto.%s\n' \
		"$ROSSO" "$GRIGIO"
	exit 2
fi

# ⛔ Il copione remoto e' un FILE gia' sulla macchina, e `sudo -S` riceve solo la
#    parola: dargli lo script sullo stdin vorrebbe dire togliergli la parola.
#    ⛔ E niente `</dev/null` in coda, che vincerebbe su `sudo -S`.
if ! timeout $((SSH_TETTO * 4)) ssh -o BatchMode=yes -o ConnectTimeout=8 "$MACCHINA" \
	"test \"\$(md5sum $REMOTO | cut -d' ' -f1)\" = '$MD5_COLL' || exit 9;
	 printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' env $AMB bash $REMOTO; e=\$?;
	 rm -f $REMOTO; exit \$e" >"$RACC" 2>/dev/null; then
	:   # l'uscita la giudica la sentinella qui sotto, non lo stato
fi

tit "== la raccolta"
if ! grep -q '^FINE-RACCOLTA' "$RACC"; then
	n=$(wc -l <"$RACC")
	ignoto T0 "la raccolta remota e' TRONCATA: $n righe e nessuna sentinella"
	inf "⛔ uscita 0 con poche righe ha la faccia esatta di «va tutto bene»:"
	inf "   ssh caduto, sudo rifiutato, copione a meta'.  NON giudico niente."
	[ "$n" -gt 0 ] && sed 's/^/        /' "$RACC" | head -5
	printf '\n    %s⛔ NON HO POTUTO VERIFICARE.%s\n' "$ROSSO" "$GRIGIO"
	exit 2
fi
val() { awk -F'\t' -v k="$1" '$1==k {print $2; exit}' "$RACC"; }
tutti() { awk -F'\t' -v k="$1" '$1==k {print $2}' "$RACC"; }
ok "raccolta completa: $(wc -l <"$RACC") righe, sentinella presente"
ORA_R=$(val ORA)

# ===========================================================================
# T1 · LA MACCHINA E' SCARICA
# ===========================================================================
tit "== T1 · la macchina e' scarica?"
CAR=$(val CARICO); CPU=$(val CPU); MEM=$(val MEM_MB)
if [ -z "$CAR" ] || [ "$CAR" = "-ignoto" ]; then
	ignoto T1.1 "non ho letto /proc/loadavg"
else
	inf "carico: $CAR   (su ${CPU:-?} filiere)   memoria disponibile: ${MEM:-?} MB"
	C1=${CAR%% *}
	if awk -v a="$C1" -v b="$CARICO_MAX" 'BEGIN{exit !(a<=b)}'; then
		verde T1.1 "carico $C1 ≤ $CARICO_MAX"
	else
		rosso T1.1 "carico $C1 > $CARICO_MAX: la macchina sta gia' lavorando per un altro"
		ko "     ⚠ e un banco che misura su una macchina carica misura la SOMMA"
	fi
fi
if [ -z "$MEM" ] || [ "$MEM" = "-ignoto" ]; then
	ignoto T1.2 "non ho letto MemAvailable"
elif [ "$MEM" -ge "$MEM_MIN_MB" ]; then
	verde T1.2 "memoria disponibile ${MEM} MB ≥ $MEM_MIN_MB"
else
	rosso T1.2 "memoria disponibile ${MEM} MB < $MEM_MIN_MB"
fi

# ⛔ I processi `remotix`: NON basta contarli, bisogna dire DI CHI SONO.
PL=$(val PROC_LETTI)
if [ -z "$PL" ] || [ "$PL" = "-ignoto" ]; then
	ignoto T1.3 "non ho potuto elencare i processi (ps)"
else
	ALTRUI=0; MIEI=0
	while IFS= read -r riga; do
		[ -n "$riga" ] || continue
		pid=${riga%%|*}; resto=${riga#*|}; ut=${resto%%|*}; cmd=${resto#*|}
		mio=no
		case "$cmd" in *"$ALBERO"*) mio=si ;; esac
		case "$cmd" in *"--porta $PORTA"*) mio=si ;; esac
		if [ "$mio" = si ]; then
			MIEI=$((MIEI+1)); inf "il MIO: pid $pid ($ut)"
			continue
		fi
		# ⚠ Un `remotix` di un altro agente e' tollerato SOLO se la sua porta e'
		#   fra quelle dichiarate — e la dichiarazione si vede stampata.
		amm=no
		for p in $PORTE_AMMESSE; do
			case "$cmd" in *"--porta $p"*) amm=si ;; esac
		done
		if [ "$amm" = si ]; then
			inf "⚠ tollerato per dichiarazione: pid $pid ($ut) — $(printf '%.90s' "$cmd")"
		else
			ALTRUI=$((ALTRUI+1))
			ko "    pid $pid, utente $ut: $(printf '%.100s' "$cmd")"
		fi
	done <<<"$(tutti PROC_REMOTIX)"
	if [ "$ALTRUI" -eq 0 ]; then
		verde T1.3 "nessun «remotix» che non sia mio ($MIEI miei, su $PL processi guardati)"
	else
		rosso T1.3 "$ALTRUI processi «remotix» NON miei sono vivi: un banco che misura"
		ko "     mentre gira il server di un altro agente misura la SOMMA, e non"
		ko "     da' rosso — da' un numero plausibile (LEZIONI.md §1.26)."
		ko "     Se sono acceso di proposito, si dichiarano: PORTE_AMMESSE='…'"
	fi
fi

if [ "$(val PORTE_LETTE)" != si ]; then
	ignoto T1.4 "non ho potuto leggere le porte in ascolto (ss)"
else
	APERTE=$(tutti PORTA_APERTA | tr '\n' ' ')
	inf "porte 7xxx/8xxx in ascolto: ${APERTE:-nessuna}"
	NONMIE=""
	for p in $APERTE; do
		[ "$p" = "$PORTA" ] && continue
		amm=no; for a in $PORTE_AMMESSE; do [ "$p" = "$a" ] && amm=si; done
		[ "$amm" = si ] || NONMIE="$NONMIE $p"
	done
	if [ -z "$NONMIE" ]; then
		verde T1.4 "nessuna porta in ascolto che non sia mia o dichiarata"
	else
		rosso T1.4 "porte non mie e non dichiarate:$NONMIE"
	fi
fi

# ===========================================================================
# T2 · ⛔⛔ IL LUCCHETTO DELLA GPU — la condizione nuova della fase 10
# ===========================================================================
tit "== T2 · ⛔⛔ il lucchetto della GPU (la GPU e' UNA, e siamo in nove)"
LS=$(val LUC_STATO); LC=$(val LUC_CHI); LSC=$(val LUC_SCAD)
case "$LS" in
libero)
	verde T2.1 "il lucchetto e' libero: nessuno ha dichiarato di misurare sulla GPU"
	inf "⚠ e questo NON vuol dire che la GPU sia scarica: il lucchetto e' una"
	inf "  convenzione fra noi, non un vincolo del nucleo (buco 2 in testa al file)"
	;;
preso)
	RESTA=$(( ${LSC:-0} - ${ORA_R:-0} ))
	if [ "$LC" = "$CHI" ]; then
		if [ "$RESTA" -gt 0 ]; then
			verde T2.1 "il lucchetto e' MIO, ancora per $RESTA s"
		else
			rosso T2.1 "il lucchetto e' mio ma e' SCADUTO da $(( -RESTA )) s: il prossimo"
			ko "     che arriva lo scassina, e la mia misura non e' piu' protetta"
		fi
	elif [ "$RESTA" -gt 0 ]; then
		rosso T2.1 "il lucchetto della GPU e' di «$LC», ancora per $RESTA s: NON MISURO"
		ko "     Un carico di GPU che non e' mio non da' rosso: da' un numero"
		ko "     plausibile e falso (LEZIONI.md §1.26).  Aspetta il tuo turno."
	else
		# ⛔ Scaduto: si DICHIARA.  Chi scassina lo fa a mano e si vede.
		verde T2.1 "il lucchetto era di «$LC» ed e' SCADUTO da $(( -RESTA )) s"
		printf '    %s⚠  SCASSINABILE — e non lo faccio io, e non in silenzio.%s\n' "$GIALLO" "$GRIGIO"
		inf "  «$LC» puo' essere morto col lucchetto in mano, oppure sta ancora"
		inf "  misurando avendo sbagliato la durata: sono due cose diverse."
		inf "  A mano, e si vede:"
		inf "    LUCCHETTO=$LUCCHETTO python3 banchi/09-lucchetto.py scassina"
	fi
	;;
illeggibile)
	ignoto T2.1 "la cartella del lucchetto c'e' ma «chi» non si legge"
	inf "⚠ qualcuno l'ha appena presa e non ha ancora scritto, oppure e' morto"
	inf "  in mezzo: non e' «libero», ed e' il caso in cui NON si tira a indovinare"
	;;
*)  ignoto T2.1 "il lucchetto non l'ho potuto guardare (stato «$LS»)" ;;
esac

if [ "$LUCCHETTO_MIO" = 1 ]; then
	if [ "$LS" = preso ] && [ "$LC" = "$CHI" ] && [ "$(( ${LSC:-0} - ${ORA_R:-0} ))" -gt 0 ]; then
		verde T2.2 "da questo giro esce un numero, e il lucchetto e' mio: regolare"
	else
		rosso T2.2 "LUCCHETTO_MIO=1 ma il lucchetto NON e' mio (stato «$LS», di «${LC:-nessuno}»)"
		ko "     ⛔ Ogni giro da cui esce un numero che riferirai prende il lucchetto."
		ko "     Libero non basta: fra il controllo e la misura arriva qualcun altro."
	fi
else
	# ⛔ E il predicato si emette LO STESSO.  `[M]` 24 agosto 2026: prima
	#    esisteva solo con LUCCHETTO_MIO=1, e un predicato che compare solo a
	#    volte non si puo' certificare — la sua assenza ha la faccia di un verde.
	verde T2.2 "LUCCHETTO_MIO=0: da questo giro NON esce un numero da riferire"
	inf "⛔ e quindi i suoi numeri non valgono e non si riferiscono: e' sviluppo"
	inf "  o messa a punto.  Chi misura per davvero mette LUCCHETTO_MIO=1."
fi

# ===========================================================================
# T3 · LA GPU E' QUELLA GIUSTA
# ===========================================================================
tit "== T3 · la GPU e' quella giusta? (§4.6-quinquies)"
# ⛔⭐ E I DUE NODI SI CERCANO INDIPENDENTEMENTE, non con un `case` a due rami.
#     `[M]` 24 agosto 2026, trovato da `--certifica`: con un `case`, se i due
#     indirizzi PCI sono UGUALI il primo ramo vince e il secondo nodo resta
#     vuoto — cioe' il predicato piu' importante di questa sezione diventava
#     IGNOTO invece di guardare la scheda che gli era stata nominata.  ⚠ Non e'
#     un caso di scuola: e' esattamente come si prova il predicato («e se la
#     discreta fosse quella aperta?»), ed e' la forma E8 di `REVIEWER.md` —
#     «vuoto» e «non l'ho cercato» con la stessa faccia.
NODO_INT=$(tutti NODO | awk -F'|' -v p="$PCI_INTEGRATA" '$1==p {print; exit}')
NODO_DIS=$(tutti NODO | awk -F'|' -v p="$PCI_DISCRETA"  '$1==p {print; exit}')

if [ -z "$NODO_INT" ]; then
	ignoto T3.1 "nessun nodo di rendering all'indirizzo $PCI_INTEGRATA"
else
	n=$(printf '%s' "$NODO_INT" | cut -d'|' -f2)
	g=$(printf '%s' "$NODO_INT" | cut -d'|' -f4)
	d=$(printf '%s' "$NODO_INT" | cut -d'|' -f6)
	inf "integrata $PCI_INTEGRATA → $n  (gruppo $g, driver $d)"
	if [ "$d" = i915 ]; then
		verde T3.1 "l'integrata e' aperta e la porta il driver i915: $n"
	else
		rosso T3.1 "all'indirizzo $PCI_INTEGRATA c'e' il driver «$d», non i915"
	fi
fi

if [ -z "$NODO_DIS" ]; then
	ignoto T3.2 "nessun nodo di rendering all'indirizzo $PCI_DISCRETA"
	NODO_DIS_N=""
else
	NODO_DIS_N=$(printf '%s' "$NODO_DIS" | cut -d'|' -f2)
	gd=$(printf '%s' "$NODO_DIS" | cut -d'|' -f4)
	md=$(printf '%s' "$NODO_DIS" | cut -d'|' -f5)
	dd=$(printf '%s' "$NODO_DIS" | cut -d'|' -f6)
	inf "discreta  $PCI_DISCRETA → $NODO_DIS_N  (gruppo $gd, modo $md, driver $dd)"
	inf "regola udev: $(val UDEV)  (esclude $(val UDEV_PCI))"
	if [ "$gd" = "$GRUPPO_NOGPU" ] && [ "$md" = 660 ]; then
		verde T3.2 "la discreta e' RECINTATA: gruppo $gd, modo $md"
	else
		rosso T3.2 "la discreta NON e' piu' chiusa: gruppo «$gd», modo «$md»"
		ko "     §4.6-quinquies la chiude APPOSTA.  In fase 5 il compositore"
		ko "     l'aveva presa senza che nessuno lo avesse chiesto, e una misura"
		ko "     intera e' stata fatta sulla scheda sbagliata."
		ko "     Si rimette con:  sudo bash v1/banco/gpu-udev.sh $PCI_DISCRETA"
	fi
fi

GR=$(val GRUPPO)
if [ -z "$GR" ]; then
	rosso T3.3 "il gruppo «$GRUPPO_NOGPU» non esiste: il recinto non c'e'"
else
	membri=$(printf '%s' "$GR" | cut -d'|' -f3)
	if [ -z "$membri" ]; then
		verde T3.3 "il gruppo del recinto «$GRUPPO_NOGPU» non ha membri (gid $(printf '%s' "$GR" | cut -d'|' -f2))"
	else
		rosso T3.3 "il gruppo del recinto «$GRUPPO_NOGPU» HA MEMBRI: $membri"
		ko "     Un recinto con dentro qualcuno non e' un recinto."
	fi
fi

FDS=$(val FD_SCANSIONE)
if [ -z "$FDS" ] || [ "$FDS" = "-ignoto" ]; then
	ignoto T3.4 "non ho potuto setacciare /proc per i descrittori sulla discreta"
else
	APERTI=$(tutti FD_DISCRETA)
	if [ -z "$APERTI" ]; then
		verde T3.4 "nessun processo tiene aperta la discreta ($FDS processi setacciati)"
	else
		rosso T3.4 "qualcuno tiene aperta la DISCRETA ($NODO_DIS_N):"
		printf '%s\n' "$APERTI" | while IFS='|' read -r p u c n; do
			ko "     pid $p ($u) «$c»: $n descrittori"
		done
		ko "     ⛔ E' esattamente il caso di fase 5: nessuno l'aveva chiesto, e"
		ko "     la misura e' finita sulla scheda sbagliata."
	fi
fi

# ===========================================================================
# T4 · NESSUN GUASTO DI RETE RIMASTO ADDOSSO
# ===========================================================================
tit "== T4 · nessun guasto di rete rimasto addosso?"
SPORCHI='netem|tbf|htb|cake|police|ingress|clsact'
giudica_tc() # $1 = sigla, $2 = interfaccia
{
	local q
	q=$(tutti TC | awk -F'|' -v i="$2" '$1==i {sub(/^[^|]*\|/,""); print}')
	if [ -z "$q" ] || [ "$q" = "-ignoto" ]; then
		ignoto "$1" "non ho letto la disciplina di «$2»"
		return
	fi
	inf "$2: $(printf '%.110s' "$q")"
	local trovata
	trovata=$(printf '%s' "$q" | grep -oE "$SPORCHI" | sort -u | tr '\n' ' ')
	if [ -n "$trovata" ]; then
		rosso "$1" "«$2» porta addosso una disciplina di guasto: $trovata"
		ko "     Un netem dimenticato da un banco precedente e' la forma esatta"
		ko "     del difetto che il lucchetto esiste per impedire: non da' rosso"
		ko "     al banco che lo subisce, gli da' un numero plausibile."
		ko "     Si toglie con:  sudo tc qdisc del dev $2 root"
	else
		verde "$1" "«$2» e' pulita"
	fi
}
giudica_tc T4.1 lo
giudica_tc T4.2 "$IFACCIA"
NIFB=$(val IFB)
if [ -z "$NIFB" ]; then
	ignoto T4.3 "non ho potuto contare le interfacce ifb (wondershaper)"
elif [ "$NIFB" -eq 0 ]; then
	verde T4.3 "nessuna interfaccia «ifb»: wondershaper non e' in piedi"
else
	rosso T4.3 "$NIFB interfacce «ifb» in piedi: qualcuno ha messo wondershaper"
fi

# ===========================================================================
# T5 · ⛔⛔ IL CODICE CHE GIRA E' QUELLO CHE SI STA LEGGENDO
#        E' il controllo che ha salvato la fase 1.
# ===========================================================================
tit "== T5 · ⛔⛔ il codice che gira e' quello che sto leggendo?"

# ── T5.1 · le due copie dello stesso modulo (R12.3) ───────────────────────
#    ⛔ Meglio scoprirlo QUI che dopo un giro di ssh: `src/costruisci.sh` si
#       rifiuta di costruire se divergono, e il rifiuto arriva a 200 km.
DIV=""
for f in rcp.c rcp.h autenticazione.c; do
	if [ ! -f "$REPO/src/$f" ] || [ ! -f "$REPO/banchi/rcp/$f" ]; then
		DIV="$DIV $f(manca)"
	elif ! cmp -s "$REPO/src/$f" "$REPO/banchi/rcp/$f"; then
		DIV="$DIV $f"
	fi
done
if [ -z "$DIV" ]; then
	verde T5.1 "src/{rcp.c,rcp.h,autenticazione.c} combaciano con banchi/rcp/ (R12.3)"
else
	rosso T5.1 "le due copie dello stesso modulo DIVERGONO:$DIV"
	ko "     src/costruisci.sh si rifiutera' di costruire (rilievo R12.3), e"
	ko "     il rifiuto arriverebbe dopo un giro di ssh."
fi

if [ "$(val ALBERO_C_E)" != si ]; then
	ignoto T5.2 "l'albero «$ALBERO/src» non c'e' sulla macchina di prova"
	ignoto T5.3 "senza albero non posso confrontare binario e sorgenti"
	ignoto T5.4 "senza albero non posso contare i binari"
	ignoto T6   "senza binario non posso leggere ldd"
else
	# ── T5.2 · i sorgenti SPEDITI sono quelli che sto leggendo? ───────────
	#    ⭐ E' la riga che in fase 1 disse «il server misura una versione che
	#       nessuno sta leggendo», mezzo secondo dopo essere entrata nel giro.
	DIVERSI=0; UGUALI=0; MANCANTI=""; SOLO_LA=0; NOMI=""
	for f in "$REPO"/src/*.c "$REPO"/src/*.h; do
		b=$(basename "$f")
		rm5=$(tutti MD5 | awk -F'|' -v n="$b" '$1==n {print $2; exit}')
		lm5=$(md5sum "$f" | cut -d' ' -f1)
		if [ -z "$rm5" ]; then
			MANCANTI="$MANCANTI $b"; continue
		fi
		if [ "$rm5" = "$lm5" ]; then UGUALI=$((UGUALI+1)); else
			DIVERSI=$((DIVERSI+1)); NOMI="$NOMI $b"
			ko "     $b: qui $lm5 · di la' $rm5"
		fi
	done
	while IFS= read -r riga; do
		b=${riga%%|*}
		case "$b" in Makefile) continue ;; esac
		[ -f "$REPO/src/$b" ] || SOLO_LA=$((SOLO_LA+1))
	done <<<"$(tutti MD5)"
	if [ "$UGUALI" -eq 0 ]; then
		ignoto T5.2 "non ho confrontato NESSUN sorgente: zero non e' «combaciano»"
	elif [ -n "$MANCANTI" ]; then
		rosso T5.2 "il tar non ha portato:$MANCANTI"
		ko "     ⇒ il server compila senza file che io sto leggendo"
	elif [ "$DIVERSI" -eq 0 ]; then
		verde T5.2 "$UGUALI sorgenti su $UGUALI combaciano byte per byte col repo"
		[ "$SOLO_LA" -gt 0 ] && inf "⚠ $SOLO_LA file stanno SOLO sulla macchina: dichiarati, non giudicati"
	else
		rosso T5.2 "$DIVERSI sorgenti su $((DIVERSI+UGUALI)) NON sono quelli che sto leggendo:$NOMI"
		ko "     ⇒ il server misura una versione che nessuno sta leggendo."
	fi

	# ── T5.3 · il binario e' PIU' NUOVO di ogni sorgente ──────────────────
	BT=$(val BIN_TS)
	if [ -z "$BT" ]; then
		rosso T5.3 "il binario non c'e': $(val BIN_MANCA)"
		ko "     ⛔ Un binario che MANCA e' un guaio, non un ignoto: era il ramo"
		ko "     con cui il difetto D5 evitava di guardare qualunque cosa."
	else
		VECCHI=""; CONTATI=0
		while IFS= read -r riga; do
			[ -n "$riga" ] || continue
			b=${riga%%|*}; t=${riga#*|}
			[ -n "$t" ] || continue
			CONTATI=$((CONTATI+1))
			[ "$t" -gt "$BT" ] && VECCHI="$VECCHI $b"
		done <<<"$(tutti TS)"
		if [ "$CONTATI" -eq 0 ]; then
			ignoto T5.3 "zero date di sorgenti lette: non giudico"
		elif [ -z "$VECCHI" ]; then
			verde T5.3 "il binario e' piu' nuovo di tutti i $CONTATI sorgenti che dichiara"
			inf "md5 binario: $(val BIN_MD5)"
		else
			rosso T5.3 "il binario e' PIU' VECCHIO di:$VECCHI"
			ko "     ⇒ il server in esecuzione non contiene quei sorgenti."
			ko "     E' il caso che ha salvato la fase 1: sorgente sano, binario"
			ko "     bugiardo (R12-A.6).  Si ricostruisce prima di misurare."
		fi
	fi

	# ── T5.4 · il posto e' uno solo (la cura di D5) ───────────────────────
	BC=$(val BIN_CONTA)
	if [ -z "$BC" ]; then
		ignoto T5.4 "non ho potuto contare i binari sotto l'albero"
	elif [ "$BC" -le 1 ]; then
		verde T5.4 "un solo «remotix» eseguibile dentro l'albero"
	else
		rosso T5.4 "$BC binari «remotix» dentro lo stesso albero:"
		tutti BIN_DOVE | sed 's/^/         /'
		ko "     ⇒ non so quale sta girando, e sceglierne uno sarebbe D5 daccapo."
	fi

	# =======================================================================
	# T6 · ngtcp2 e nghttp3 vengono dal posto giusto
	# =======================================================================
	tit "== T6 · ngtcp2 e nghttp3 vengono da /media/REMOTIX/src/b2?"
	B2=/media/REMOTIX/src/b2
	LR=$(val LDD_RC)
	LIN=$(tutti LDD)
	if [ "$LR" != 0 ]; then
		ignoto T6 "ldd non ha potuto guardare il binario (uscita «${LR:-?}»)"
	elif [ -z "$LIN" ]; then
		rosso T6 "ldd non nomina ne' ngtcp2 ne' nghttp3: il binario non le lega"
		ko "     ⛔ Zero righe NON e' «vengono dal posto giusto»: e' un binario"
		ko "     che non e' il server, oppure legato in un modo che non conosco."
	else
		FUORI=0
		while IFS= read -r l; do
			[ -n "$l" ] || continue
			inf "$(printf '%.110s' "$l")"
			case "$l" in *"$B2"*) ;; *) FUORI=$((FUORI+1)) ;; esac
		done <<<"$LIN"
		if [ "$FUORI" -eq 0 ]; then
			verde T6 "tutte le $(printf '%s\n' "$LIN" | wc -l) righe vengono da $B2"
			# ⚠ E si dice SUBITO che cosa regge quel verde: senza
			#   LD_LIBRARY_PATH lo stesso binario prende quelle di SISTEMA.
			NUDO=$(tutti LDD_NUDO)
			if [ -n "$NUDO" ] && ! printf '%s' "$NUDO" | grep -q "$B2"; then
				printf '    %s⚠  e ci vengono SOLO grazie a LD_LIBRARY_PATH:%s\n' "$GIALLO" "$GRIGIO"
				inf "  nudo, questo binario risolve ngtcp2 dal SISTEMA — non ha rpath."
				inf "  ⛔ Un lanciatore che dimentica LD_LIBRARY_PATH parte benissimo e"
				inf "  aborta al primo che si collega, e questo controllo NON lo vede:"
				inf "  guarda il binario, non la riga di comando che lo accendera'."
			fi
		else
			rosso T6 "$FUORI librerie NON vengono da $B2 (vengono dal sistema)"
			ko "     ⛔ E' la trappola che fa partire il server BENISSIMO e lo fa"
			ko "     abortire al primo che si collega: il sintomo arriva molto"
			ko "     dopo l'avvio, e sembra un difetto del protocollo."
		fi
	fi
fi

# ===========================================================================
# T7 · IL POSTO E' LIBERO
# ===========================================================================
tit "== T7 · il posto di «$UTENTE» e' libero?"
inf "⛔ PIANO.md lo scrive a lettere: non si conta il tempo, si VERIFICA che il"
inf "  posto sia libero.  Un palco orfano non da' rosso: da' un numero"
inf "  plausibile, e in fase 9 stava per far accusare tre cure innocenti."
if [ "$(val UTENTE_C_E)" != si ]; then
	rosso T7.1 "l'utente «$UTENTE» non esiste sulla macchina di prova"
else
	inf "processi dell'utente in tutto: $(val UTENTE_PROC)"
	inf '  ⚠ il gestore d'"'"'utente e PipeWire ci stanno: «enable-linger» e'"'"' voluto,'
	inf "  e contarli come «posto occupato» darebbe rosso su una macchina sana"
	P=$(tutti PALCO)
	if [ -z "$P" ]; then
		verde T7.1 "nessun palco montato per «$UTENTE»: il posto e' libero"
	elif [ "$PALCO_AMMESSO" = 1 ]; then
		verde T7.1 "c'e' un palco per «$UTENTE», ed e' DICHIARATO (PALCO_AMMESSO=1)"
		printf '%s\n' "$P" | sed 's/^/         ⚠ /'
	else
		rosso T7.1 "il posto di «$UTENTE» NON e' libero — palco vivo:"
		printf '%s\n' "$P" | while IFS='|' read -r p c a; do
			ko "     pid $p «$c»: $(printf '%.80s' "$a")"
		done
		ko "     Se il palco e' voluto, si dichiara: PALCO_AMMESSO=1"
	fi
fi
C=$(tutti CLIENTE)
if [ -z "$C" ]; then
	verde T7.2 "nessun cliente vivo sulla porta $PORTA"
else
	rosso T7.2 "clienti ancora vivi sulla porta $PORTA:"
	printf '%s\n' "$C" | sed 's/^/         /'
	ko "     ⚠ pkill torna subito; un cliente QUIC ci mette fino a mezzo minuto"
	ko "     a congedarsi.  Chi non aspetta trova il posto occupato al giro dopo."
fi

# ===========================================================================
# T8 · IL BAN DELL'INDIRIZZO NON E' SCATTATO
# ===========================================================================
tit "== T8 · il ban di §4.4-bis e' scattato?"
BF=$(val BAN_FILE)
if [ "$BF" = assente ]; then
	verde T8 "nessun file dei ban in «$BAN_FILE»: nessun ban sopravvissuto"
	inf "⚠ e questo NON vede il ban vivo nella MEMORIA di un server acceso"
	inf "  (buco 3 in testa al file): §4.4-bis dice che il ban vive in due posti"
else
	MIO=""; ALTRI=0
	while IFS= read -r riga; do
		[ -n "$riga" ] || continue
		a=${riga%%|*}; f=${riga#*|}
		[ "$f" -gt "${ORA_R:-0}" ] 2>/dev/null || continue
		if [ "$a" = "$IND" ]; then MIO=$(( f - ORA_R )); else ALTRI=$((ALTRI+1)); fi
	done <<<"$(tutti BAN)"
	if [ -n "$MIO" ]; then
		rosso T8 "⛔ L'INDIRIZZO $IND E' BANNATO ancora per $MIO s ($((MIO/3600)) h)"
		ko "     Il ban e' per INDIRIZZO e dura 12 ore: ogni banco che parte da"
		ko "     qui fallira' per una ragione che non c'entra con quel che misura,"
		ko "     e il sintomo sara' «il cliente non si collega»."
		ko "     Si toglie con:"
		ko "       python3 banchi/01-b8-sblocca.py --socket $LAV/comando.sock $IND"
		ko "     ⚠ sul TUO socket: parlare col server di un altro da' NON-BANNATO"
		ko "     e lascia il ban dov'era."
	else
		verde T8 "l'indirizzo $IND non e' bannato ($ALTRI altri indirizzi nel file)"
	fi
fi

# ===========================================================================
# ⛔ IL DENOMINATORE — «tutti quelli provati sono andati bene» e' vero anche
#    quando i provati sono zero.
# ===========================================================================
printf '\n%s== quel che questo controllo ha davvero guardato%s\n' "$NETTO" "$GRIGIO"
inf "predicati giudicati: $GUARDATI"
printf '    %s%3d%s  ⛔ guai\n' "$ROSSO" "$GUAI" "$GRIGIO"
printf '    %s%3d%s  ⚠ IGNOTI (non ho potuto verificare)\n' "$GIALLO" "$IGNOTI" "$GRIGIO"
if [ -n "${ESITI_FUORI:-}" ]; then cp "$ESITI" "$ESITI_FUORI"; fi

if [ "$GUARDATI" -eq 0 ]; then
	ko "⛔ ZERO predicati: questo giro non dice niente, e «terreno buono» sarebbe"
	ko "   una bugia"
	exit 2
fi
if [ "$GUAI" -gt 0 ]; then
	printf '\n    %s⛔ IL TERRENO NON REGGE: NON misurare su questa macchina.%s\n' "$ROSSO" "$GRIGIO"
	ko "Quel che ne uscirebbe non parlerebbe del prodotto."
	exit 1
fi
if [ "$IGNOTI" -gt 0 ]; then
	printf '\n    %s⚠ il terreno regge SU QUEL CHE HO POTUTO GUARDARE%s\n' "$GIALLO" "$GRIGIO"
	inf "$IGNOTI predicati non si sono potuti verificare: non sono un verde,"
	inf "e il banco si ferma qui (LEZIONI.md §1.29)"
	exit 2
fi
printf '\n    %s⭐ il terreno regge: %d predicati su %d%s\n' "$VERDE" "$GUARDATI" "$GUARDATI" "$GRIGIO"
exit 0
