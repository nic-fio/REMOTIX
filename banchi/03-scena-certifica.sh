#!/bin/bash
#
# 03-scena-certifica.sh — ⛔ LA CERTIFICAZIONE DEL BANCO, PRIMA DELLA MISURA.
#
#   bash 03-scena-certifica.sh tutto        il giro intero
#   bash 03-scena-certifica.sh marca        i soli controlli della marca (P1..P8)
#   bash 03-scena-certifica.sh m6           ⭐ M6: sano → guasto → risanato
#   bash 03-scena-certifica.sh m8           ⭐ il `giro` di M8, riaperto
#   bash 03-scena-certifica.sh catalogo     le righe leggibili a macchina
#
# ===========================================================================
# ⛔ CHE COSA CERTIFICA, E CHE COSA **NON** CERTIFICA
#
# `LEZIONI.md` §1.2.  Ma la meta' che conta e' la seconda, e sta qui in alto
# invece che in fondo, perche' in fondo non la legge nessuno:
#
#   ⛔ **LA CATENA DI QUESTO GIRO NON E' LA CATENA VERA.**  E':
#
#        scena  =  i pixel che `03-scena.c` ha DIPINTO e consegnato al
#                  compositore  (⚠ NON una cattura PipeWire di Mutter)
#        flusso =  libx265 Main10 tutto-intra, QP 40   (⚠ NON hevc_vaapi)
#        pagina =  lo stesso flusso decodificato da ffmpeg a RGB 8 bit
#                  (⚠ NON la tela del browser riletta)
#
#   ⇒ Quel che qui si dimostra e': **la marca sopravvive alla codifica con
#     perdita e si rilegge, e con lei M6 diventa eseguibile e il controllo
#     `giro` di M8 torna applicabile.**  Quel che qui NON si dimostra e' che
#     la cattura di Mutter e la tela del browser la conservino: quelli sono
#     due anelli che questo giro non ha, e vanno misurati quando ci saranno.
#
#   ⚠ Chiamare questo «M6 chiuso sulla catena vera» sarebbe la forma E1 di
#     `REVIEWER.md`: una condizione necessaria presa per sufficiente.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PORTA=${PORTA:-7602}
LAV=${LAV:-/tmp/remotix-03-scena-$PORTA}
# ⛔⛔ TROVATO FACENDO GIRARE IL BANCO, 13 agosto 2026.  Questo script usava
#     `$DISPLAY_W` e `$SHM` senza definirle: sono di `03-scena-accendi.sh`, e
#     qui non arrivano.  `set -u` ha fatto il suo mestiere — «variabile non
#     assegnata» invece di una stringa vuota che avrebbe fatto partire la scena
#     sul display SBAGLIATO in silenzio — e i controlli P11/P12 sono usciti
#     ROSSI dichiarando «NON MISURATI», che e' l'esito giusto.
#     ⚠ E i due nomi si scrivono UNA volta: nel corpo dello script c'era gia'
#     `remotix-scena-$PORTA` copiato a mano in quattro punti, che e' il modo in
#     cui due grandezze finiscono sotto un nome solo.
DISPLAY_W=${DISPLAY_W:-remotix-scena-$PORTA}
SHM=${SHM:-remotix-scena-$PORTA}
ESITI=${ESITI:-$QUI/03-scena-esiti.jsonl}
METRO=$QUI/02-giudizio-metro.py
ACCENDI=$QUI/03-scena-accendi.sh
MARCA=$QUI/03-marca.py
QP=${QP:-40}
L=${L:-1280}
A=${A:-720}
GIRO=${GIRO:-c-$(date +%Y%m%d-%H%M%S)}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

mkdir -p "$LAV"
FALLITI=0
# ⛔ Quante righe il giro ha CHIESTO di depositare, e quante ce n'erano prima:
#    sono le due meta' di P18.  Vedi `prova_deposito()`.
DEPOSITI=0
PRIMA_DEP=0

# ---------------------------------------------------------------------------
# I fotogrammi veri della scena: due giri DIVERSI, con due nomi diversi.
#
# ⛔ Due giri con lo STESSO nome hanno la stessa marca del giro, e il controllo
#    `giro` di M8 sarebbe verde per costruzione.  Due nomi diversi sono la
#    condizione perche' quel controllo possa diventare rosso — e uno strumento
#    che non puo' diventare rosso non e' uno strumento.
# ---------------------------------------------------------------------------
prepara_fotogrammi()
{
	log "1. La scena gira, e scarico i fotogrammi"
	bash "$ACCENDI" costruisci >/dev/null 2>&1 || { ko "la scena non si costruisce"; return 1; }
	bash "$ACCENDI" compositore-avvia >/dev/null 2>&1 || { ko "il compositore non parte"; return 1; }

	rm -f "$LAV"/fotogramma-*.rgb24 "$LAV"/fotogramma-*.json
	# ⛔ `--dopo 120`: NON si campiona all'avvio.  `LEZIONI.md` §1.4 — i primi
	#    fotogrammi sono l'avvio, quando tutto viene ridipinto, e la loro
	#    distribuzione non e' quella del regime.
	bash "$ACCENDI" istantanee 3 --giro "$GIRO-uno" --dopo 120 >/dev/null 2>&1
	local n; n=$(ls "$LAV"/fotogramma-*.rgb24 2>/dev/null | wc -l)
	if [ "$n" -lt 3 ]; then ko "solo $n fotogrammi scaricati, ne servono 3"; return 1; fi
	# ⛔ Il banco RICORDA che nome di giro ha fatto girare, e lo scrive.
	#    ⚠ Non lo si rilegge dai pixel: quello e' l'imputato.  E non lo si
	#    ricalcola da `$GIRO` alla prossima invocazione, o `m8` girato da solo
	#    su fotogrammi di ieri confronterebbe due nomi che non c'entrano — che
	#    e' precisamente il rosso finto che questo banco ha prodotto al primo
	#    giro, il 13 agosto 2026.
	printf '%s\n' "$GIRO" > "$LAV/giro.txt"
	ok "3 fotogrammi consecutivi del giro «$GIRO-uno»"
	ls "$LAV"/fotogramma-*.rgb24 | sed 's/^/        /'

	# ⭐ IL CONTEGGIO DEI DISEGNI DEL CLIENT, LETTO DA FUORI MENTRE GIRA.
	#    E' il controllo di §1.1 che dice di chi e' il tetto.  Si fa qui, con
	#    la scena viva, perche' a scena ferma il conto non cresce.
	log "2. ⭐ Il conteggio dei disegni del client — di chi e' il tetto?"
	bash "$ACCENDI" avvia --giro "$GIRO-conta" --secondi 6 >/dev/null 2>&1
	sleep 1
	local c1 c2 t1 t2
	c1=$(python3 "$MARCA" conta --shm "$SHM" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("disegni",-1))')
	t1=$(date +%s%N)
	sleep 3
	c2=$(python3 "$MARCA" conta --shm "$SHM" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("disegni",-1))')
	t2=$(date +%s%N)
	bash "$ACCENDI" ferma >/dev/null 2>&1
	local pieno; pieno=$(python3 "$MARCA" conta --shm "$SHM")
	echo "$pieno" | sed 's/^/        /'
	python3 - "$c1" "$c2" "$t1" "$t2" "$LAV/conteggio.json" <<'PY'
import json, sys
c1, c2, t1, t2, fuori = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
sec = (t2 - t1) / 1e9
al_secondo = (c2 - c1) / sec if sec > 0 else 0
d = {"disegni_prima": c1, "disegni_dopo": c2, "secondi": round(sec, 3),
     "disegni_al_secondo": round(al_secondo, 2), "cresciuto": c2 > c1}
json.dump(d, open(fuori, "w"), ensure_ascii=False)
print("        il client ha disegnato %d volte in %.2f s = %.1f disegni/s"
      % (c2 - c1, sec, al_secondo))
PY
	if [ "$c2" -gt "$c1" ]; then
		ok "⭐ P9 · il conto CRESCE mentre la scena gira, letto DA FUORI"
	else
		ko "⛔ P9 · il conto non cresce ($c1 → $c2): la scena non disegna"
		FALLITI=$((FALLITI+1))
	fi
	# ⛔ E il gemello negativo: a scena FERMA il conto non deve crescere.
	#    Senza, «il conto cresce» potrebbe essere un contatore che si muove da
	#    solo, e il controllo positivo non proverebbe niente.
	local f1 f2
	f1=$(python3 "$MARCA" conta --shm "$SHM" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("disegni",-1))')
	sleep 2
	f2=$(python3 "$MARCA" conta --shm "$SHM" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("disegni",-1))')
	if [ "$f1" = "$f2" ]; then
		ok "⭐ P10 · a scena FERMA il conto NON cresce ($f1 = $f2)"
	else
		ko "⛔ P10 · il conto cresce a scena ferma ($f1 → $f2): non conta i disegni"
		FALLITI=$((FALLITI+1))
	fi

	# ⛔⭐ P11/P12 — IL MONITOR SI CHIEDE, E SI VERIFICA CHE SIA QUELLO.
	#
	#    Sul palco della fase 3 i monitor virtuali sono tre, e una scena finita
	#    su quello sbagliato e' un metro puntato sul buio che pero' dichiara la
	#    mira.  ⇒ due meta', e la seconda e' quella che si dimentica:
	#      P11 il positivo: si chiede un'uscita che c'e', e il COMPOSITORE
	#          conferma con `wl_surface.enter` che la superficie e' finita li';
	#      P12 il negativo: si chiede un'uscita che NON c'e', e la scena deve
	#          FALLIRE (uscita 1) invece di ripiegarne una a caso.
	log "2-bis. ⛔ Il monitor: chiesto, e verificato dal lato che riceve"
	local prima_uscita
	prima_uscita=$(env XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" \
	    WAYLAND_DISPLAY="$DISPLAY_W" "$LAV/03-scena" --uscite 2>&1 \
	    | sed -n 's/^    «\([^»]*\)».*/\1/p' | head -1)
	if [ -z "$prima_uscita" ]; then
		ko "⛔ il compositore non offre nessuna uscita: P11 e P12 NON MISURATI"
		FALLITI=$((FALLITI+1)); return 0
	fi
	inf "la prima uscita che il compositore offre e' «$prima_uscita»"
	local r
	r=$(env XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" \
	    WAYLAND_DISPLAY="$DISPLAY_W" "$LAV/03-scena" --shm "$SHM" \
	    --giro "$GIRO-uscita" --uscita "$prima_uscita" --secondi 3 2>/dev/null)
	local conf
	conf=$(echo "$r" | python3 -c 'import json,sys; print(json.load(sys.stdin)["uscita_confermata"])' 2>/dev/null)
	if [ "$conf" = "$prima_uscita" ]; then
		ok "⭐ P11 · chiesto «$prima_uscita», il compositore CONFERMA «$conf» (wl_surface.enter)"
	else
		ko "⛔ P11 · chiesto «$prima_uscita», confermato «$conf»"
		FALLITI=$((FALLITI+1))
	fi
	env XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" \
	    WAYLAND_DISPLAY="$DISPLAY_W" "$LAV/03-scena" --shm "$SHM" \
	    --uscita "NON-ESISTE-$$" --secondi 2 >/dev/null 2>&1
	if [ $? -ne 0 ]; then
		ok "⭐ P12 · un'uscita che NON c'e' fa FALLIRE la scena, non ripiegare"
	else
		ko "⛔ P12 · con un'uscita inesistente la scena e' partita lo stesso:"
		ko "   ha scelto un monitor da se', e nessuno saprebbe quale"
		FALLITI=$((FALLITI+1))
	fi
	prova_corsa_a_vuoto
	return 0
}

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ P13..P17 — IL RILEVATORE DELLA CORSA A VUOTO
#
# Aggiunti il 13 agosto 2026, dopo che lo step 1 ha visto questa scena fare
# **540 disegni/s su un monitor a 60 Hz** dentro il suo banco (da sola: 60).
#
# ⛔ IL PUNTO CHE VIENE PRIMA DELLA CURA: quel numero non va consegnato, va
#    **accusato**.  Se la scena non aspetta piu' il `wl_surface.frame`, il conto
#    `disegni` non misura piu' i ridisegni del compositore e `attese` va a zero
#    per la ragione sbagliata ⇒ il numero su cui si appoggiano tutti gli altri
#    gruppi diventa **verde per costruzione** (`LEZIONI.md` §2.2).
#
# ⚠ E il guasto si INNESTA (`--guasto rientro`, che rimette il dispatch
#   rientrante del 13 agosto): un rilevatore certificato contro un difetto che
#   la cura ha gia' tolto non e' certificato — e' un banco verde che non
#   riproduce (`LEZIONI.md` §1.3).
# ═══════════════════════════════════════════════════════════════════════════
conta_json()   # <chiave>  → il valore, dal blocco condiviso
{
	python3 "$MARCA" conta --shm "$SHM" 2>/dev/null \
	    | python3 -c "import json,sys; print(json.load(sys.stdin).get('$1'))" 2>/dev/null
}

prova_corsa_a_vuoto()
{
	log "2-ter. ⛔⭐ La CORSA A VUOTO — sano → guasto → risanato"
	local esegui="env XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)} WAYLAND_DISPLAY=$DISPLAY_W $LAV/03-scena"

	# ── sano ────────────────────────────────────────────────────────────
	$esegui --shm "$SHM" --giro "$GIRO-sano" --secondi 5 >"$LAV/cav-sano.json" 2>/dev/null
	local f1 c1 r1
	f1=$(python3 -c "import json;print(json.load(open('$LAV/cav-sano.json'))['fidato'])")
	c1=$(python3 -c "import json;print(json.load(open('$LAV/cav-sano.json'))['callback_in_volo_massimo'])")
	r1=$(python3 -c "import json;print(round(json.load(open('$LAV/cav-sano.json'))['disegni_al_secondo']))")
	inf "sano     fidato=$f1 · callback in volo max=$c1 · $r1 disegni/s"

	# ── guasto ──────────────────────────────────────────────────────────
	# ⚠ Il guasto IGNORA `--secondi`: la ricorsione non torna mai al ciclo
	#   principale (misurato: 6 s chiesti, 146 s vissuti).  ⇒ si legge il
	#   blocco condiviso MENTRE gira e poi lo si uccide.  ⛔ E il fatto che
	#   `--secondi` non lo fermi e' esso stesso un pezzo del difetto: la morte
	#   che ne segue cade a meta' scrittura, ed e' quel che lascia il RELITTO
	#   di P14.
	$esegui --shm "$SHM" --giro "$GIRO-guasto" --guasto rientro --secondi 5 \
	    >/dev/null 2>&1 &
	local pid_guasto=$!
	sleep 6
	local f2 c2 r2 vivo_ancora=no
	kill -0 "$pid_guasto" 2>/dev/null && vivo_ancora=si
	f2=$(conta_json fidato); c2=$(conta_json callback_in_volo_massimo)
	r2=$(conta_json disegni_al_secondo)
	kill -9 "$pid_guasto" 2>/dev/null; wait "$pid_guasto" 2>/dev/null
	inf "guasto   fidato=$f2 · callback in volo max=$c2 · $r2 disegni/s"
	inf "         ⛔ e a 6 s dalla partenza con --secondi 5 e' ancora vivo: $vivo_ancora"

	# ── risanato ────────────────────────────────────────────────────────
	$esegui --shm "$SHM" --giro "$GIRO-risanato" --secondi 5 >"$LAV/cav-risanato.json" 2>/dev/null
	local f3 c3
	f3=$(python3 -c "import json;print(json.load(open('$LAV/cav-risanato.json'))['fidato'])")
	c3=$(python3 -c "import json;print(json.load(open('$LAV/cav-risanato.json'))['callback_in_volo_massimo'])")
	inf "risanato fidato=$f3 · callback in volo max=$c3"

	if [ "$f1" = "True" ] && [ "$f2" = "False" ] && [ "$f3" = "True" ] \
	   && [ "$c1" = "1" ] && [ "$c3" = "1" ] && [ "${c2:-0}" -gt 1 ]; then
		ok "⭐⭐ P13 · il rilevatore VEDE la corsa a vuoto: fidato true→false→true,"
		ok "     callback in volo 1 → $c2 → 1, e il ritmo $r1 → $r2 disegni/s"
	else
		ko "⛔ P13 · atteso fidato True/False/True e callback 1/>1/1;"
		ko "   avuto $f1/$f2/$f3 e $c1/$c2/$c3"
		FALLITI=$((FALLITI+1))
	fi
	# ⛔ E la meta' che si dimentica: il verdetto dev'essere ASSENTE nel sano.
	#    Un rilevatore che dicesse «non fidato» sempre non e' un rilevatore.
	if [ "$f1" = "True" ] && [ "$f3" = "True" ]; then
		ok "⭐ P13-bis · e nei due giri sani NON accusa (niente falsi rossi)"
	else
		ko "⛔ P13-bis · accusa anche una scena sana"
		FALLITI=$((FALLITI+1))
	fi

	# ── P14: il RELITTO ─────────────────────────────────────────────────
	# ⛔ Una scena morta a meta' scrittura lascia `seq` DISPARI per sempre.  E'
	#    la causa vera di «il blocco condiviso smette di rispondere», ed e'
	#    deterministica: nessun numero di tentativi lo trovera' mai pari.
	$esegui --shm "$SHM-relitto" --giro relitto --secondi 2 >/dev/null 2>&1
	python3 - "/dev/shm/$SHM-relitto" <<'PYREL'
import mmap, struct, sys
f = open(sys.argv[1], "r+b"); m = mmap.mmap(f.fileno(), 0)
seq = struct.unpack("<Q", m[16:24])[0]
m[16:24] = struct.pack("<Q", seq | 1)
m.flush(); m.close(); f.close()
PYREL
	local rel
	rel=$(python3 "$MARCA" conta --shm "$SHM-relitto" 2>/dev/null \
	      | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('relitto'), d.get('c_e'))")
	if [ "$rel" = "True False" ]; then
		ok "⭐ P14 · un blocco con `seq` dispari e' riconosciuto RELITTO, e non"
		ok "     scambiato per «lo scrittore e' troppo veloce»"
	else
		ko "⛔ P14 · blocco relitto non riconosciuto: «$rel»"
		FALLITI=$((FALLITI+1))
	fi
	rm -f "/dev/shm/$SHM-relitto"

	# ── P15: lo stato d'uscita porta il verdetto ────────────────────────
	#
	# ⛔⭐ E QUI IL CONTROLLO SBAGLIATO ERA IL MIO — trovato girando, 13 agosto
	#     2026, ed e' la terza volta in questo lavoro.
	#
	#     La prima stesura leggeva il blocco DOPO che la scena era uscita e
	#     pretendeva stato 0.  ⛔ Esce 2, e ha ragione il codice: i numeri di una
	#     scena che non c'e' piu' sono la sua ULTIMA fotografia, non i numeri di
	#     adesso, e consegnarli come correnti e' la misura di ieri spacciata per
	#     quella di oggi.  ⇒ i tre stati si provano su tre situazioni VERE, e
	#     una di queste e' «scena viva», che va tenuta viva apposta.
	local viva_pid
	$esegui --shm "$SHM-p15" --giro "$GIRO-p15" --secondi 25 >/dev/null 2>&1 &
	viva_pid=$!
	sleep 2
	python3 "$MARCA" conta --shm "$SHM-p15" >/dev/null 2>&1; local u_viva=$?
	python3 "$MARCA" conta --shm "non-esiste-affatto-$$" >/dev/null 2>&1; local u_no=$?
	python3 "$MARCA" conta --shm "$SHM" >/dev/null 2>&1; local u_morta=$?
	if [ "$u_viva" -eq 0 ] && [ "$u_no" -eq 1 ] && [ "$u_morta" -eq 2 ]; then
		ok "⭐ P15 · lo stato d'uscita di «conta» distingue i TRE casi:"
		ok "     scena viva=0 · blocco inesistente=1 · ⭐ scena morta=2 (non fidato)"
	else
		ko "⛔ P15 · stati d'uscita: viva=$u_viva (atteso 0), inesistente=$u_no"
		ko "   (atteso 1), morta=$u_morta (atteso 2)"
		FALLITI=$((FALLITI+1))
	fi

	# ── P16: senza numpy ────────────────────────────────────────────────
	# ⛔ Su NIC-OS numpy non c'e'.  `conta` non lo usa — legge il blocco con
	#    `struct` — e deve funzionare li' dove i banchi girano davvero.
	# ⚠ Si punta sulla scena VIVA, o si misurerebbe `fidato` invece di numpy:
	#   e' lo stesso inciampo di P15, e va evitato due volte.
	local finto="$LAV/senza-numpy"
	mkdir -p "$finto"
	printf 'raise ImportError("finto: numpy non c%s e, come su NIC-OS")\n' "'" > "$finto/numpy.py"
	if PYTHONPATH="$finto" python3 "$MARCA" conta --shm "$SHM-p15" >/dev/null 2>&1; then
		ok "⭐ P16 · «conta» funziona SENZA numpy (e' dove girano i banchi)"
	else
		ko "⛔ P16 · «conta» non funziona senza numpy"
		FALLITI=$((FALLITI+1))
	fi
	kill "$viva_pid" 2>/dev/null; wait "$viva_pid" 2>/dev/null
	rm -f "/dev/shm/$SHM-p15"
	# e il gemello: chi chiede i PIXEL senza numpy riceve una frase utile
	local msg
	msg=$(PYTHONPATH="$finto" python3 "$MARCA" leggi /dev/null --larghezza 8 --altezza 8 2>&1 | head -1)
	case "$msg" in
	*numpy*) ok "⭐ P16-bis · e chi chiede i pixel senza numpy legge PERCHE': «${msg:0:60}…»" ;;
	*)       ko "⛔ P16-bis · senza numpy il messaggio non nomina numpy: «$msg»"
	         FALLITI=$((FALLITI+1)) ;;
	esac
	return 0
}

# ---------------------------------------------------------------------------
# La catena: cattura → flusso HEVC Main10 → riferimento + pagina.
# ---------------------------------------------------------------------------
costruisci_catena()
{
	local sorgente=$1 base=$2
	ffmpeg -y -loglevel error -f rawvideo -pix_fmt rgb24 -s "${L}x${A}" \
	    -i "$sorgente" -pix_fmt yuv420p10le -c:v libx265 \
	    -x265-params "qp=$QP:keyint=1:log-level=none" -f hevc "$base.hevc" || return 1
	ffmpeg -y -loglevel error -i "$base.hevc" -pix_fmt rgb48le -f rawvideo \
	    "$base-riferimento.rgb48" || return 1
	ffmpeg -y -loglevel error -i "$base.hevc" -pix_fmt rgb24 -f rawvideo \
	    "$base-pagina.rgb24" || return 1
	return 0
}

dichiarazioni()
{
	cat > "$LAV/colore.json" <<JSON
{
  "cattura":     {"spazio": "RGB", "matrice": "nessuna", "gamma": "piena",
                  "nota": "⛔ NON e' una cattura di Mutter: sono i pixel XRGB8888 che 03-scena.c ha consegnato al compositore.  Gamma piena per costruzione: li scriviamo noi"},
  "codifica":    {"matrice": "bt709", "gamma": "piena", "gamma_ingresso": "piena",
                  "primarie": "bt709",
                  "nota": "libx265 Main10 tutto-intra, QP $QP"},
  "riferimento": {"matrice": "bt709", "gamma": "piena", "primarie": "bt709"},
  "pagina":      {"matrice": "bt709", "gamma": "piena", "primarie": "bt709"}
}
JSON
	python3 - "$LAV/scena.json" "$L" "$A" "$GIRO" <<'PY'
import json, sys
fuori, L, A, giro = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
json.dump({
    "nome": "03-scena", "giro": giro, "mira": False,
    "larghezza": L, "altezza": A, "zone": {},
    "perche": ("⛔ La scena e' `03-scena.c`, NON la mira di F2.6: non ha i quattro "
               "marcatori d'angolo, non ha i tre riquadri a luminanza uguale e non "
               "ha una sfumatura dichiarata.  ⇒ M4, M7 e i marcatori di M-V si "
               "dichiarano NON APPLICABILI, e il metro conta quanti dei dodici "
               "guasti questo giro non avrebbe visto.  ⭐ Quel che questa scena ha "
               "e la mira non ha: si MUOVE a ogni fotogramma, e porta il numero del "
               "fotogramma dentro i pixel — che e' la condizione di M6 e la "
               "riapertura del `giro` di M8."),
}, open(fuori, "w"), ensure_ascii=False, indent=1)
PY
}

# ⛔⭐ QUEL CHE RESTA NEL DEPOSITO.
#
#    `$LAV` sta in /tmp e si azzera al riavvio (il rootfs di questa macchina
#    vive in RAM, `LEZIONI.md` §2.5-bis).  ⇒ l'esito di M6 e di M8 va scritto
#    ANCHE nel deposito, o dopo un riavvio resta solo il ricordo che «erano
#    verdi» — che è esattamente il tipo di riga che un documento si porta
#    dietro senza più un numero sotto.
deposita()   # <marca> <atteso> <sano> <guasto> <risanato> [quarto]
{
	# ⛔ Si contano i depositi CHIESTI, non quelli riusciti: se `03-deposita.py`
	#    fallisse, il file avrebbe una riga in meno e P18 lo direbbe.  Contare i
	#    riusciti farebbe sparire il guasto insieme alla riga.
	DEPOSITI=$((DEPOSITI+1))
	python3 "$QUI/03-deposita.py" "$ESITI" "$GIRO" "$1" "$2" "$3" "$4" "$5" "${6:-}"
}

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ P18/P19 — IL DEPOSITO SI RILEGGE.  Scritto il 13 agosto 2026 sera.
#
# ⛔ IL BUCO CHE QUESTO CHIUDE, ed era scritto nel catalogo (`01-b12-guasti.py`,
#    voce `03-deposita`): **nessuno rileggeva `03-scena-esiti.jsonl`.**  Questo
#    script leggeva gli esiti del METRO in `$LAV` — cioe' in /tmp — e il
#    deposito lo scriveva e basta.  ⇒ Il guasto di catalogo (`open(esiti,"w")`
#    invece di `"a"`: il deposito si TRONCA e resta solo l'ultima riga) lasciava
#    il giro **tutto verde**: la riga a schermo e' identica, il codice d'uscita
#    di `03-deposita.py` resta 0, e a sparire e' la STORIA — cioe' esattamente
#    la cosa per cui il file era stato scritto.
#
# ⛔⛔ E LA META' CHE SI DIMENTICA, ED E' LA RAGIONE PER CUI SERVONO DUE
#     SCRITTURE E NON UNA: con **una sola** riga depositata, «cresciuto di uno»
#     e «troncato all'ultima» danno lo STESSO numero.  Un controllo che non puo'
#     diventare rosso non e' un controllo (`LEZIONI.md` §2.2).  ⇒ sotto le due
#     scritture questo controllo dichiara **NON ESEGUITO** invece di passare:
#     «non ho guardato» e «va tutto bene» non si arrotondano.
#
# ⚠ E si contano le righe NON VUOTE, non i ritorni a capo: un file senza il
#   `\n` finale ha una riga in meno per `wc -l` e la piena per chi la legge.
# ═══════════════════════════════════════════════════════════════════════════
righe_deposito()
{
	[ -s "$ESITI" ] || { echo 0; return 0; }
	grep -c . "$ESITI" 2>/dev/null || echo 0
}

prova_deposito()   # <righe-prima> <quante-scritture-ha-fatto-il-giro>
{
	log "5. ⛔⭐ IL DEPOSITO — la storia c'e' ANCORA, o e' rimasta l'ultima riga?"
	local prima=$1 scritte=$2
	local dopo; dopo=$(righe_deposito)
	inf "deposito: $ESITI"

	if [ "$scritte" -lt 2 ]; then
		ko "⛔ P18 · NON ESEGUITO: questo giro ha depositato $scritte riga/e, e con"
		ko "   meno di due «il deposito cresce» e «il deposito si tronca» danno lo"
		ko "   stesso numero.  ⇒ non e' «verde»: e' «non ho potuto guardare»."
		FALLITI=$((FALLITI+1))
		return 0
	fi

	# ── P18 · le righe di prima ci sono ancora ───────────────────────────
	local atteso=$((prima + scritte))
	if [ "$dopo" -eq "$atteso" ]; then
		ok "⭐ P18 · il deposito CRESCE in coda: $prima → $dopo righe (+$scritte),"
		ok "     e le $prima di prima ci sono ancora"
	else
		ko "⛔ P18 · il deposito e' passato da $prima a $dopo righe, e ne erano"
		ko "   attese $atteso ($prima + $scritte scritture).  Se $dopo e' minore,"
		ko "   il deposito si TRONCA invece di crescere: la storia e' sparita e"
		ko "   resta solo l'ultima riga — con la stampa a schermo identica."
		FALLITI=$((FALLITI+1))
	fi

	# ── P19 · e l'ultima riga si RILEGGE, e dice quel che il giro ha fatto ─
	# ⛔ Non basta contare: una riga illeggibile e una riga giusta si contano
	#    uguale.  ⇒ si riapre il deposito, si prende l'ULTIMA riga e si
	#    pretende che sia il giro di M8 con i suoi QUATTRO giri dentro
	#    (sano · guasto · risanato · senza-marca).  E' il conto che
	#    `03-deposita.py` scrive da se': se scendesse in silenzio sarebbe il
	#    conto gonfiato al contrario, che e' il secondo guasto del catalogo.
	local r
	r=$(python3 - "$ESITI" <<'PY'
import json, sys
righe = [x for x in open(sys.argv[1], encoding="utf-8") if x.strip()]
if not righe:
    print("VUOTO"); raise SystemExit(0)
try:
    d = json.loads(righe[-1])
except Exception as e:                                    # noqa: BLE001
    print("ILLEGGIBILE %s" % e); raise SystemExit(0)
print("%s %s %s" % (d.get("marca"), d.get("quanti_giri"),
                    "SI" if d.get("catena") else "NO"))
PY
)
	if [ "$r" = "M8/giro 4 SI" ]; then
		ok "⭐ P19 · e l'ultima riga si RILEGGE: marca «M8/giro», 4 giri dentro,"
		ok "     e con la CATENA dichiarata accanto"
	else
		ko "⛔ P19 · l'ultima riga del deposito dice «$r»,"
		ko "   atteso «M8/giro 4 SI»: il giro di M8 non e' arrivato al deposito"
		ko "   com'e' stato fatto (marca · quanti_giri · catena dichiarata)"
		FALLITI=$((FALLITI+1))
	fi
	return 0
}

# ⛔ Si legge SOLO il campo che interessa, e si stampa tutto il resto: un
#    grep che non trova niente e un metro che non ha girato hanno lo stesso
#    aspetto (`LEZIONI.md` §1.9).
leggi_strumento()   # <file-esiti> <strumento>
{
	python3 - "$1" "$2" <<'PY'
import json, sys
righe = [json.loads(r) for r in open(sys.argv[1]) if r.strip()]
if not righe:
    print("VUOTO"); raise SystemExit(0)
e = righe[-1][sys.argv[2]]
print(json.dumps({"ok": e.get("ok"), "applicabile": e.get("applicabile"),
                  "controlli": e.get("controlli"),
                  "delta_db": e.get("delta_db"),
                  "psnr_ora_db": e.get("psnr_ora_db"),
                  "psnr_prima_db": e.get("psnr_prima_db")},
                 ensure_ascii=False))
PY
}

# ---------------------------------------------------------------------------
# ⭐⭐ M6 — sano → guasto → risanato
# ---------------------------------------------------------------------------
prova_m6()
{
	log "3. ⭐⭐ M6 (la freschezza) — sano → guasto → risanato"
	local f
	f=($(ls "$LAV"/fotogramma-*.rgb24 2>/dev/null))
	if [ "${#f[@]}" -lt 3 ]; then ko "servono 3 fotogrammi"; FALLITI=$((FALLITI+1)); return 1; fi
	local prima=${f[0]} ora=${f[1]}
	inf "cattura_precedente = $(basename "$prima")"
	inf "cattura            = $(basename "$ora")"

	costruisci_catena "$ora"   "$LAV/ora"   || { ko "la catena di «ora» non si costruisce"; return 1; }
	costruisci_catena "$prima" "$LAV/prima" || { ko "la catena di «prima» non si costruisce"; return 1; }
	dichiarazioni
	ok "catena: HEVC Main10 QP $QP · riferimento rgb48 · pagina rgb24"

	local es=$LAV/m6-esiti.jsonl
	: > "$es"

	# — sano —————————————————————————————————————————————————————————
	python3 "$METRO" --scena "$LAV/scena.json" \
	    --cattura "$ora" --cattura-precedente "$prima" \
	    --riferimento "$LAV/ora-riferimento.rgb48" \
	    --pagina "$LAV/ora-pagina.rgb24" \
	    --colore "$LAV/colore.json" --identita-pagina "" \
	    --giro "$GIRO-m6-sano" --scena-nome 03-scena --esiti "$es" >"$LAV/m6-sano.txt" 2>&1
	local s1; s1=$(leggi_strumento "$es" M6)
	inf "sano     M6 = $s1"

	# — guasto: LA PAGINA E' DEL GIRO PRIMA ——————————————————————————
	# ⛔ E' il guasto `F2.6/precedente` del catalogo, e questa volta il
	#    fotogramma «di prima» e' un fotogramma VERO della scena, non una
	#    mira ridisegnata con un altro seme.
	python3 "$METRO" --scena "$LAV/scena.json" \
	    --cattura "$ora" --cattura-precedente "$prima" \
	    --riferimento "$LAV/ora-riferimento.rgb48" \
	    --pagina "$LAV/prima-pagina.rgb24" \
	    --colore "$LAV/colore.json" --identita-pagina "" \
	    --giro "$GIRO-m6-guasto" --scena-nome 03-scena --esiti "$es" >"$LAV/m6-guasto.txt" 2>&1
	local s2; s2=$(leggi_strumento "$es" M6)
	inf "guasto   M6 = $s2"

	# — risanato ——————————————————————————————————————————————————————
	# ⭐ Il terzo giro e' quello che ci si dimentica: senza, «il metro vede il
	#   guasto» e «il metro e' rimasto rotto» hanno lo stesso aspetto.
	python3 "$METRO" --scena "$LAV/scena.json" \
	    --cattura "$ora" --cattura-precedente "$prima" \
	    --riferimento "$LAV/ora-riferimento.rgb48" \
	    --pagina "$LAV/ora-pagina.rgb24" \
	    --colore "$LAV/colore.json" --identita-pagina "" \
	    --giro "$GIRO-m6-risanato" --scena-nome 03-scena --esiti "$es" >"$LAV/m6-risanato.txt" 2>&1
	local s3; s3=$(leggi_strumento "$es" M6)
	inf "risanato M6 = $s3"

	local v1 v2 v3
	v1=$(echo "$s1" | python3 -c 'import json,sys; print(json.load(sys.stdin)["ok"])')
	v2=$(echo "$s2" | python3 -c 'import json,sys; print(json.load(sys.stdin)["ok"])')
	v3=$(echo "$s3" | python3 -c 'import json,sys; print(json.load(sys.stdin)["ok"])')
	if [ "$v1" = "True" ] && [ "$v2" = "False" ] && [ "$v3" = "True" ]; then
		ok "⭐⭐ M6: sano=OK · guasto=BOCCIATO · risanato=OK — lo strumento e' VIVO"
	else
		ko "⛔ M6: sano=$v1 guasto=$v2 risanato=$v3 (atteso True/False/True)"
		FALLITI=$((FALLITI+1))
	fi
	deposita "M6" "sano=ok · guasto=bocciato · risanato=ok" "$s1" "$s2" "$s3"
	cp "$es" "$LAV/m6-esiti-finale.jsonl"
	return 0
}

# ---------------------------------------------------------------------------
# ⭐⭐ M8 — il controllo `giro`, riaperto
# ---------------------------------------------------------------------------
prova_m8()
{
	log "4. ⭐⭐ Il controllo \`giro\` di M8 — riaperto, e letto DAI PIXEL"
	local pagina=$LAV/ora-pagina.rgb24
	[ -s "$pagina" ] || { ko "manca «$pagina»: gira prima «m6»"; FALLITI=$((FALLITI+1)); return 1; }
	# ⛔ Il nome del giro e' quello che il banco HA FATTO GIRARE, non quello di
	#    adesso: senza questo, `m8` da solo confronta il giro di oggi con i
	#    pixel di ieri e da' un rosso che non e' del prodotto.
	if [ ! -s "$LAV/giro.txt" ]; then
		ko "⛔ manca «$LAV/giro.txt»: non so quale giro il banco abbia fatto"
		ko "   girare, e indovinarlo darebbe un rosso finto.  Gira «tutto»."
		FALLITI=$((FALLITI+1)); return 1
	fi
	local GIRO; GIRO=$(cat "$LAV/giro.txt")
	inf "il banco ha fatto girare «$GIRO-uno» (letto da $LAV/giro.txt)"
	local es=$LAV/m8-esiti.jsonl
	: > "$es"

	# L'identita' si COSTRUISCE dai pixel del fotogramma dipinto.
	python3 "$MARCA" identita "$pagina" --larghezza "$L" --altezza "$A" \
	    --giri "$GIRO-uno,$GIRO-due" --fuori "$LAV/identita.json" \
	    --dipinto-dopo-reset no --fin-ricevuto si --dipinto si \
	    | sed 's/^/        /' || {
		# ⛔ Il messaggio dice QUALE dei due e' successo, invece di una frase
		#    che vale per tutt'e due: «il file non si e' scritto» e «la marca
		#    non e' nei pixel» mandano a cercare in due posti diversi, e il
		#    secondo e' un difetto della CATENA, non dello strumento.
		if [ -s "$LAV/identita.json" ]; then
			ko "⛔ la marca NON e' nei pixel del fotogramma dipinto: la catena"
			ko "   l'ha persa fra il disegno e la decodifica.  L'identita' e'"
			ko "   stata scritta lo stesso, con giro=null (⇒ M8 non eseguito)."
		else
			ko "⛔ l'identita' non si e' scritta affatto: e' lo strumento"
		fi
		FALLITI=$((FALLITI+1)); return 1; }

	# — sano: il giro in corso E' quello dipinto nella scena ——————————
	python3 "$METRO" --scena "$LAV/scena.json" \
	    --cattura "$(ls "$LAV"/fotogramma-*.rgb24 | sed -n 2p)" \
	    --cattura-precedente "$(ls "$LAV"/fotogramma-*.rgb24 | sed -n 1p)" \
	    --riferimento "$LAV/ora-riferimento.rgb48" --pagina "$pagina" \
	    --colore "$LAV/colore.json" --identita-pagina "$LAV/identita.json" \
	    --giro "$GIRO-uno" --scena-nome 03-scena --esiti "$es" >"$LAV/m8-sano.txt" 2>&1
	local s1; s1=$(leggi_strumento "$es" M8)
	inf "sano     M8 = $s1"

	# — guasto: il banco gira «$GIRO-due», la scena dipinta dice «uno» ——
	# ⛔ E' il guasto che il vecchio M8 non poteva vedere: «il fotogramma e'
	#    di un altro giro» chiesto ai PIXEL invece che all'imputato.
	python3 "$METRO" --scena "$LAV/scena.json" \
	    --cattura "$(ls "$LAV"/fotogramma-*.rgb24 | sed -n 2p)" \
	    --cattura-precedente "$(ls "$LAV"/fotogramma-*.rgb24 | sed -n 1p)" \
	    --riferimento "$LAV/ora-riferimento.rgb48" --pagina "$pagina" \
	    --colore "$LAV/colore.json" --identita-pagina "$LAV/identita.json" \
	    --giro "$GIRO-due" --scena-nome 03-scena --esiti "$es" >"$LAV/m8-guasto.txt" 2>&1
	local s2; s2=$(leggi_strumento "$es" M8)
	inf "guasto   M8 = $s2"

	# — risanato ——————————————————————————————————————————————————————
	python3 "$METRO" --scena "$LAV/scena.json" \
	    --cattura "$(ls "$LAV"/fotogramma-*.rgb24 | sed -n 2p)" \
	    --cattura-precedente "$(ls "$LAV"/fotogramma-*.rgb24 | sed -n 1p)" \
	    --riferimento "$LAV/ora-riferimento.rgb48" --pagina "$pagina" \
	    --colore "$LAV/colore.json" --identita-pagina "$LAV/identita.json" \
	    --giro "$GIRO-uno" --scena-nome 03-scena --esiti "$es" >"$LAV/m8-risanato.txt" 2>&1
	local s3; s3=$(leggi_strumento "$es" M8)
	inf "risanato M8 = $s3"

	# — ⛔ E LA META' CHE SI DIMENTICA: senza marca, il controllo NON si
	#     esegue.  Se qui uscisse verde, il `giro` di M8 sarebbe di nuovo la
	#     costante che fa passare.
	python3 - "$pagina" "$LAV/senza-marca.rgb24" "$L" "$A" <<'PY'
import numpy as np, sys
p, fuori, L, A = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
img = np.fromfile(p, np.uint8)[:L*A*3].reshape(A, L, 3).copy()
# il blocco della marca coperto da un pezzo di scena preso piu' in basso
img[20:250, 20:470] = img[300:530, 20:470]
img.tofile(fuori)
PY
	python3 "$MARCA" identita "$LAV/senza-marca.rgb24" --larghezza "$L" --altezza "$A" \
	    --giri "$GIRO-uno,$GIRO-due" --fuori "$LAV/identita-senza.json" \
	    --dipinto-dopo-reset no --fin-ricevuto si --dipinto si >/dev/null 2>&1
	python3 "$METRO" --scena "$LAV/scena.json" \
	    --cattura "$(ls "$LAV"/fotogramma-*.rgb24 | sed -n 2p)" \
	    --cattura-precedente "$(ls "$LAV"/fotogramma-*.rgb24 | sed -n 1p)" \
	    --riferimento "$LAV/ora-riferimento.rgb48" --pagina "$pagina" \
	    --colore "$LAV/colore.json" --identita-pagina "$LAV/identita-senza.json" \
	    --giro "$GIRO-uno" --scena-nome 03-scena --esiti "$es" >"$LAV/m8-senza.txt" 2>&1
	local s4; s4=$(leggi_strumento "$es" M8)
	inf "senza marca  M8 = $s4"

	python3 - "$s1" "$s2" "$s3" "$s4" <<'PY'
import json, sys
sano, guasto, risanato, senza = [json.loads(x) for x in sys.argv[1:5]]
def g(d): return (d.get("controlli") or {}).get("giro")
esiti = {
  "sano: giro=True":      g(sano) is True,
  "guasto: giro=False":   g(guasto) is False,
  "risanato: giro=True":  g(risanato) is True,
  "⛔ senza marca: giro NON ESEGUITO (None)": g(senza) is None,
}
for k, v in esiti.items():
    print("    %s  %s" % ("\033[1;32mOK\033[0m " if v else "\033[1;31mNO\033[0m ", k))
raise SystemExit(0 if all(esiti.values()) else 1)
PY
	if [ $? -eq 0 ]; then
		ok "⭐⭐ il controllo \`giro\` di M8 e' VIVO: sa dire si', sa dire no, e sa dire «non ho guardato»"
	else
		ko "⛔ il controllo \`giro\` di M8 non e' vivo"
		FALLITI=$((FALLITI+1))
	fi
	deposita "M8/giro" "sano=true · guasto=false · risanato=true · senza-marca=null" \
	    "$s1" "$s2" "$s3" "$s4"
	cp "$es" "$LAV/m8-esiti-finale.jsonl"
	return 0
}

# ---------------------------------------------------------------------------
catalogo()
{
	# Le righe leggibili a macchina, nella forma di `01-b12-guasti.py`.
	python3 - <<'PY'
import json
righe = [
 {"nome": "F3.2/marca-positivo", "comando": "03-marca-certifica.py P1",
  "atteso_sano": "c_e=true e i tre campi esatti", "guasto_da_innestare": "—",
  "atteso_guasto": "—", "marca": "P1"},
 {"nome": "F3.2/marca-negativo", "comando": "03-marca-certifica.py P2",
  "atteso_sano": "c_e=false su sei scene senza marca",
  "guasto_da_innestare": "nessuna marca", "atteso_guasto": "c_e=false con il perche'",
  "marca": "P2"},
 {"nome": "F3.2/marca-massa", "comando": "03-marca-certifica.py P3",
  "atteso_sano": "zero falsi positivi su N scene di rumore",
  "guasto_da_innestare": "rumore binario e a blocchi 24x24",
  "atteso_guasto": "c_e=false", "marca": "P3"},
 {"nome": "F3.2/marca-codifica", "comando": "03-marca-certifica.py P4",
  "atteso_sano": "esatta fino a QP >= 40", "guasto_da_innestare": "HEVC Main10 a QP crescente",
  "atteso_guasto": "il QP a cui si perde, dichiarato", "marca": "P4"},
 {"nome": "F3.2/marca-rotta", "comando": "03-marca-certifica.py P5",
  "atteso_sano": "c_e=true", "guasto_da_innestare": "un bit invertito",
  "atteso_guasto": "c_e=false (il CRC)", "marca": "P5"},
 {"nome": "F3.2/due-pittori", "comando": "03-marca-certifica.py P6",
  "atteso_sano": "la C e la Python dicono lo stesso disegno e lo stesso istante",
  "guasto_da_innestare": "—", "atteso_guasto": "—", "marca": "P6"},
 {"nome": "F3.2/si-muove", "comando": "03-marca-certifica.py P7",
  "atteso_sano": "disegni consecutivi, istanti crescenti, pixel diversi",
  "guasto_da_innestare": "—", "atteso_guasto": "—", "marca": "P7"},
 {"nome": "F3.2/conteggio", "comando": "03-scena-certifica.sh (P9/P10)",
  "atteso_sano": "il conto cresce a scena viva",
  "guasto_da_innestare": "scena ferma", "atteso_guasto": "il conto NON cresce",
  "marca": "P9/P10"},
 {"nome": "F3.2/M6", "comando": "03-scena-certifica.sh m6",
  "atteso_sano": "M6 ok=true", "guasto_da_innestare": "la pagina e' del giro prima",
  "atteso_guasto": "M6 ok=false", "marca": "M6"},
 {"nome": "F3.2/M8-giro", "comando": "03-scena-certifica.sh m8",
  "atteso_sano": "M8.controlli.giro = true",
  "guasto_da_innestare": "il banco gira un altro nome",
  "atteso_guasto": "M8.controlli.giro = false", "marca": "M8/giro"},
 {"nome": "F3.2/M8-giro-cieco", "comando": "03-scena-certifica.sh m8",
  "atteso_sano": "—", "guasto_da_innestare": "il fotogramma non porta la marca",
  "atteso_guasto": "M8.controlli.giro = null (NON ESEGUITO, non verde)",
  "marca": "M8/giro"},
]
for r in righe:
    print(json.dumps(r, ensure_ascii=False))
PY
}

# ---------------------------------------------------------------------------
case "${1:-tutto}" in
marca)
	prepara_fotogrammi || exit 1
	python3 "$QUI/03-marca-certifica.py" --cartella "$LAV" --esiti "$ESITI" \
	    --giro "$GIRO" --rumore "${RUMORE:-3000}" || FALLITI=$((FALLITI+1))
	;;
m6)  prova_m6 ;;
m8)  prova_m8 ;;
catalogo) catalogo; exit 0 ;;
tutto)
	prepara_fotogrammi || exit 1
	log "P1..P8 · i controlli della marca"
	python3 "$QUI/03-marca-certifica.py" --cartella "$LAV" --esiti "$ESITI" \
	    --giro "$GIRO" --rumore "${RUMORE:-3000}" || FALLITI=$((FALLITI+1))
	# ⛔ Il conto si prende QUI, dopo la riga di `03-marca-certifica.py` — che
	#    il deposito se lo scrive da se', senza passare da `03-deposita.py` — e
	#    prima delle due scritture di M6 e M8.  Cosi' P18 misura esattamente le
	#    righe che `03-deposita.py` ha in mano, e non un totale in cui la sua
	#    parte si perde.
	PRIMA_DEP=$(righe_deposito)
	prova_m6
	prova_m8
	prova_deposito "$PRIMA_DEP" "$DEPOSITI"
	log "Il conto del giro «$GIRO»"
	if [ "$FALLITI" -eq 0 ]; then
		ok "⭐ tutti i controlli passati"
	else
		ko "⛔ $FALLITI blocchi di controlli falliti"
	fi
	inf "esiti  → $ESITI"
	inf "lavoro → $LAV"
	exit "$FALLITI" ;;
*)
	echo "uso: $0 {tutto|marca|m6|m8|catalogo}" >&2; exit 2 ;;
esac
exit "$FALLITI"
