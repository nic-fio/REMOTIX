#!/bin/bash
# ===========================================================================
# 11-accendi.sh — costruisce e accende UNA scatola della rete di sicurezza
#
#   bash 11-accendi.sh costruisci [gnome]     rifa' l'immagine dalla ricetta
#   bash 11-accendi.sh accendi    [gnome]     butta giu' e riaccende la scatola
#   bash 11-accendi.sh passo0     [gnome]     esegue il passo 0 dentro
#   bash 11-accendi.sh c1         [gnome] [n]  la sessione nasce e si vede
#   bash 11-accendi.sh c2         [gnome] [--applicazione-che-muore|--finestra-che-non-si-apre]
#   bash 11-accendi.sh c3         [gnome] [--scena-ferma|--fotogramma-ripetuto|--codificatore-fermo]
#   bash 11-accendi.sh c4         [gnome] [--senza-tasto|--scena-sorda]  il tasto arriva allo schermo
#   bash 11-accendi.sh c6         [gnome] [--uccidi-la-sessione]  si stacca e si ritrova
#   bash 11-accendi.sh c8         [gnome] [--senza-cura]  il secondo apre il browser
#   bash 11-accendi.sh c8b        [gnome] [--senza-cura]  la pagina si vede DAL CLIENTE
#   bash 11-accendi.sh c5         [gnome] [--senza-sorgente]  il suono non e' silenzio
#   bash 11-accendi.sh c7         [gnome] [--solo-distacco|--lascia-un-processo]
#   bash 11-accendi.sh c9         [gnome]     il registro dice DI CHI parla
#   bash 11-accendi.sh c10                    le copie gemelle (NON vuole la scatola)
#   bash 11-accendi.sh impronta   [gnome]     stampa l'impronta (R3)
#   bash 11-accendi.sh spegni     [gnome]
#
# ⚠ C2 · C3 · C4 · C6 · C8b girano UTILMENTE solo su gnome: il prodotto sa
#   avviare solo GNOME (`src/sessione.c:778`, tutto `src/mutter.c`).  Sulle
#   altre tre scatole danno **3** — «non ho potuto guardare» — ed e' giusto.
#
# ⛔ Si esegue SULLA MACCHINA DI PROVA, da amministratore.
# ===========================================================================
#
# ⛔⛔ I PERMESSI IN PIU', E PERCHE' CIASCUNO — nessuno per abitudine
#
# Ogni permesso che si aggiunge allontana la scatola dalla macchina vera, ⇒ e
# quindi ognuno va giustificato con quel che si rompe senza.  `[M]` 25 agosto
# 2026, misurati uno per uno al passo 0:
#
#   --systemd=always        il primo processo dev'essere `systemd`, o la
#                           domanda del passo 0 non e' nemmeno ponibile
#   --device /dev/dri       ⭐ LA SCHEDA GRAFICA VERA.  E' la ragione per cui si
#                           usano scatole e non macchine virtuali (D1)
#   --cap-add=AUDIT_CONTROL ⛔ senza, `pam_loginuid.so` (che in Debian e'
#                           `required`) fallisce e IL GESTORE D'UTENTE NON PARTE
#   --cap-add=AUDIT_WRITE   accompagna il precedente nella stessa catena PAM
#   --network=host          ⚠ NON e' una scelta: `netavark` su questa macchina
#                           non riesce ad applicare le regole di rete
#                           («nft did not return successfully»).  ⛔ E ha un
#                           PREZZO che va scritto: quattro scatole accese
#                           insieme condividono le porte dell'ospite, quindi
#                           ciascuna dovra' avere la SUA porta — o si pesteranno
#                           i piedi in un modo che somiglia a un guasto del
#                           prodotto.  ⇒ Da rivedere quando si fa C14.
#
# ⛔ E quel che NON si e' fatto, di proposito: `--privileged`.  Un permesso
#    generico avrebbe fatto passare tutto e non avrebbe insegnato niente:
#    l'elenco qui sopra e' quel che il prodotto CHIEDE DAVVERO, ed e' un
#    risultato del passo 0, non una comodita'.
# ===========================================================================
set -uo pipefail

DESKTOP=${2:-gnome}
BASE=$(cd "$(dirname "$0")" && pwd)
NOME="rete11-$DESKTOP"
IMMAGINE="rete11/$DESKTOP:p0"
RICETTA="$BASE/Contenitore.$DESKTOP"
# ⚠ Una porta per scatola: con `--network=host` le quattro scatole condividono
#   le porte dell ospite, quindi due sulla stessa porta si pesterebbero i piedi
#   in un modo che somiglia a un guasto del prodotto.
case "$DESKTOP" in
  gnome) PORTA=8511 ;;
  kde)   PORTA=8512 ;;
  xfce)  PORTA=8513 ;;
  lxqt)  PORTA=8514 ;;
  *)     PORTA=8519 ;;
esac

# ---------------------------------------------------------------------------
# ⛔⛔ I PERMESSI IN PIU' CHE CHIEDE **QUESTO** DESKTOP, e nessun altro.
#
# `[M]` 26 agosto 2026, e vale la pena leggerla: la scatola di GNOME regge con
# i permessi comuni; ⛔ quella di PLASMA no.  `/usr/bin/kwin_wayland` porta
# addosso `cap_sys_nice=ep`, e un programma con un permesso scritto sul file
# **non si puo' nemmeno avviare** se quel permesso non e' nell insieme della
# scatola: `env: kwin_wayland: Operation not permitted`.
#
# ⭐⭐ ED E' LA TESI DELLA FASE, capitata al primo tentativo: **il secondo
#     desktop ha chiesto una cosa che il primo non chiedeva.**  ⇒ Scoprirlo
#     adesso costa dieci minuti; scoprirlo dentro la fase 12, in mezzo al
#     codice nuovo, sarebbe costato mezza giornata e una diagnosi sbagliata.
#
# ⚠ E NON si da a tutti: darlo anche a GNOME vorrebbe dire provare GNOME in un
#   ambiente diverso da quello in cui gira davvero — cioe' allontanare la
#   scatola dal prodotto per comodita nostra.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ⛔⛔ E UN PERMESSO CHE VALE PER TUTTE, trovato il 27 agosto 2026 — `SYS_ADMIN`
#
# `[M]` Senza, dentro la scatola **`polkit.service` non parte** (esce `217/USER`)
# e `upower.service` ci muore dietro: **1 213 riavvii**.  ⛔ E `gnome-shell` li
# chiama in modo SINCRONO all avvio: incassa **quattro scadenze da 25 000 ms in
# fila** ⇒ per **~97 secondi Mutter non risponde a niente**, ne' D-Bus ne'
# Wayland.
#
# ⭐⭐ ED E' LA RAGIONE DEL DIFETTO CHE SEMBRAVA DEL PRODOTTO: la sessione **non
#     nasce cieca — nasce in ritardo di ~97 s**.  `[M]` gu1 98,0 s · gu2 101,0 s
#     · gu3 95,5 s, e poi `formato negoziato 1920x1080` e i fotogrammi partono.
#     ⇒ I banchi guardavano in una finestra piu' corta del fenomeno.
#
# ⚠ E questo permesso NON allontana la scatola dalla macchina vera: la
#   AVVICINA.  Sulla macchina vera `polkit` funziona; ⛔ era la scatola a essere
#   diversa, e la differenza si vedeva come un guasto del prodotto.
# ---------------------------------------------------------------------------
CAPS_COMUNI="--cap-add=SYS_ADMIN"

case "$DESKTOP" in
  kde) CAPS="$CAPS_COMUNI --cap-add=SYS_NICE" ;;
  *)   CAPS="$CAPS_COMUNI" ;;
esac

ok()  { printf '  \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '  \033[1;31mNO\033[0m  %s\n' "$*"; }
log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL RIMASUGLIO DI `/tmp/mozilla` — LA CURA NON STA PIU' QUI, 27 ago 2026
#
# ⛔ E' il difetto che ha reso ROSSA C2 e MUTE C3 e C4 nel primo giro
#    `--famiglia tutto` su tutt'e quattro le scatole: `/tmp/mozilla` restava al
#    PRIMO inquilino che l'aveva preso — quello di C8/C8b, che girano prima —
#    ⚠ e il sintomo era dalla parte piu' velenosa possibile: **sembrava che la
#    sessione non dipingesse**, mentre era viva, dipinta e con Firefox fermo
#    sulla scelta del profilo.
#
# ⚠ Per un giorno la cura e' stata QUI, cioe' nel pezzo che le mette in fila.
# ⛔⛔ ED ERA IL POSTO SBAGLIATO: una maglia che ha bisogno di essere «preparata
#     da fuori» e', lanciata a mano o da un altro gancio, una maglia che da' un
#     **rosso falso** — ed e' il difetto che in questa rete si paga di piu'.
#
# ⭐ Dal 27 agosto 2026 la cura e' DENTRO C2, C3 e C4 (`cura_della_provvista`,
#   che importa `applica_la_cura` di C8, cioe' le righe di `src/provisiona.sh`):
#   ogni maglia da' una `~/.cache` VERA all'inquilino che crea, ⇒ di chi sia
#   `/tmp/mozilla` non le riguarda piu'.  ⛔ E nessuna cancella il rimasuglio di
#   un'altra: in parallelo (C14) la farebbe cadere.
# ⇒ ⛔ Qui non resta niente da fare, e non ci si rimette niente: due posti che
#   fanno la stessa cosa sono due posti da cui divergere.
# ═══════════════════════════════════════════════════════════════════════════

# ⭐ C10 e' l unica maglia che NON vuole una scatola: legge dei file del deposito,
#    prima di compilare.  ⛔ Sta PRIMA del controllo dell amministratore apposta —
#    non serve essere root per leggere tre sorgenti — e ⛔ NON si esegue dentro la
#    scatola: li' `src/` non c e, e la maglia direbbe «non ho potuto guardare» per
#    sempre, che e' il cugino del rosso perpetuo (LEZIONI.md §1.49).
if [ "${1:-}" = c10 ]; then
	shift
	exec python3 "$BASE/11-c10-le-copie-gemelle.py" "$@"
fi

[ "$(id -u)" = 0 ] || { ko "va eseguito da amministratore"; exit 2; }
[ -f "$RICETTA" ] || { ko "non trovo la ricetta $RICETTA"; exit 2; }

case "${1:-}" in

costruisci)
	log "Costruisco l'immagine di $DESKTOP dalla ricetta"
	# ⚠ `--network=host` anche qui: senza, la costruzione non arriva ai
	#   pacchetti (stessa ragione di sopra, misurata il 25 agosto 2026).
	podman build --network=host -f "$RICETTA" -t "$IMMAGINE" "$BASE" || exit 1
	ok "immagine $IMMAGINE"
	;;

accendi)
	log "Accendo la scatola $NOME"
	# ⛔ `-t 0`, cioe' si ammazza invece di chiedere per favore.  `[M]` 25 agosto
	#    2026: un `podman rm -f` normale su questa scatola e' rimasto appeso
	#    **oltre quattro minuti** aspettando uno spegnimento ordinato che non
	#    arrivava, ⛔ e nel frattempo ha bloccato anche i `podman` successivi.
	# ⚠ E resta una cosa da capire, scritta invece che dimenticata: **perche' la
	#   scatola non si spegne da sola?**  Non tocca il passo 0 (la scatola e'
	#   usa-e-getta), ⛔ ma tocca C7 — «si chiude tutto e non resta niente» — e
	#   li' quella domanda diventa il bersaglio, non un fastidio.
	# ⛔ Prima si AMMAZZA, poi si toglie, poi si sostituisce comunque.
	#    `[M]` 26 agosto 2026: un `rm -f` da solo ha lasciato in piedi la scatola
	#    (spegnimento ordinato che non arriva mai), e il giro dopo e' morto con
	#    «that name is already in use» — ⛔ un rosso che non c entrava niente con
	#    quel che si stava provando.
	podman kill -s KILL "$NOME" >/dev/null 2>&1
	podman rm -f -t 0 "$NOME" >/dev/null 2>&1
	# ═══════════════════════════════════════════════════════════════════
	# ⛔⛔ `--pids-limit` — E' UNA CURA, NON UN ALLARGAMENTO PRUDENZIALE.
	#
	# `[M]` 27 agosto 2026, misurato dentro rete11-gnome mentre una sessione
	# con Firefox era viva:
	#
	#     /sys/fs/cgroup/pids.max                 = 2048   (il predefinito di podman)
	#     /sys/fs/cgroup/init.scope/pids.max      =  307   ⇐ 15% di 2048
	#     /sys/fs/cgroup/init.scope/pids.current  =  260   ⇐ Firefox e i suoi fili
	#
	# ⭐ `podman exec` mette quel che lancia in **init.scope**, e systemd dentro
	#   la scatola gli da il suo `DefaultTasksMax=15%` calcolato sul limite di
	#   podman.  ⇒ Con una sessione viva restavano **47 fili** in tutto: `[M]`
	#   python si fermava a **38** con «can't start new thread», e ⛔ **ffmpeg
	#   non riusciva piu' ad aprire il codificatore PNG**
	#   (`ff_frame_thread_encoder_init failed`, EAGAIN).
	#
	# ⛔⛔ E IL SINTOMO ERA DALLA PARTE SBAGLIATA: le maglie che guardano il
	#     pixel (C2, C3, C4, C6, C8b) uscivano **3** dicendo *«N fotogrammi sono
	#     arrivati ma ffmpeg non ne ha fatto un'immagine»* — cioe' un guasto
	#     della SCATOLA che si presentava come un limite del banco.  ⚠ E lo
	#     stesso ffmpeg, sullo stesso flusso, riusciva un minuto dopo, a
	#     sessione sgomberata: la prova che non era il flusso.
	#
	# ⇒ 16384 ⇒ init.scope arriva a **2457**, cioe' ~9 volte i 260 misurati.
	# ⭐ E NON allontana la scatola dalla macchina vera: la avvicina.  Sulla
	#   macchina vera un tetto ai fili non c e affatto.
	# ═══════════════════════════════════════════════════════════════════
	podman run -d --replace --name "$NOME" \
		--systemd=always \
		--pids-limit 16384 \
		--network=host \
		--device /dev/dri \
		--cap-add=AUDIT_WRITE \
		--cap-add=AUDIT_CONTROL \
		$CAPS \
		-v "$BASE:/rete11:ro" \
		"$IMMAGINE" >/dev/null || exit 1

	# ⛔ Si ASPETTA che il sistema dentro sia partito, non si conta fino a dieci.
	#    Una scadenza a orologio e' una scadenza che scatta quando capita.
	for _ in $(seq 1 60); do
		S=$(podman exec "$NOME" systemctl is-system-running 2>&1 | head -1)
		case "$S" in running|degraded) break ;; esac
		sleep 0.5
	done
	ok "$NOME accesa (stato interno: ${S:-ignoto})"

	# ═══════════════════════════════════════════════════════════════════
	# ⭐⭐ OGNI NODO DELLA SCHEDA DEVE AVERE, DENTRO, UN GRUPPO CON UN NOME.
	#
	# ⚠ La ricetta (`Contenitore.*`) allinea **un nodo solo**, `renderD128`.
	#   `[M]` 27 agosto 2026, macchina di prova: i nodi sono QUATTRO —
	#   `card0` e `card1` (gruppo `video`), `renderD128` (`render`, 991) e
	#   ⛔ `renderD129`, che sull ospite appartiene a `remotix-nogpu` (990),
	#   ⛔ **un gruppo che dentro la scatola non esisteva affatto**.
	#
	# ⇒ `[M]` L attrezzo `attrezzi-gruppi-scheda.sh` — che C1, C5, C6, C7 e C9
	#   adesso chiamano — guarda TUTTI i nodi e si ferma col suo codice 5,
	#   *«un gid dei nodi non ha nessun nome in /etc/group»*: ⛔ le maglie
	#   uscivano **3 in un secondo**, senza misurare niente.  ⚠ E avevano
	#   ragione: un gid senza nome e' un gruppo in cui nessuno puo' entrare.
	#
	# ⭐ Qui il nome NON e' inchiodato: si legge il gid dal NODO (`stat`) e il
	#   nome dall OSPITE (`getent`), e si crea dentro lo stesso numero con lo
	#   stesso nome.  ⛔ Se quel nome dentro e' gia' preso da un altro numero,
	#   si ripiega su `scheda<gid>` invece di fallire in silenzio.
	# ⚠ E si crea il GRUPPO soltanto: chi ci debba entrare lo decide
	#   l attrezzo, non questo file.
	# ═══════════════════════════════════════════════════════════════════
	for N in /dev/dri/card* /dev/dri/renderD*; do
		[ -e "$N" ] || continue
		G=$(stat -c %g "$N" 2>/dev/null) || continue
		[ -n "$G" ] || continue
		podman exec "$NOME" getent group "$G" >/dev/null 2>&1 && continue
		NOME_G=$(getent group "$G" 2>/dev/null | cut -d: -f1)
		[ -n "$NOME_G" ] || NOME_G="scheda$G"
		if podman exec "$NOME" groupadd -g "$G" "$NOME_G" >/dev/null 2>&1; then
			ok "gruppo $G ($NOME_G) creato dentro, per $N"
		elif podman exec "$NOME" groupadd -g "$G" "scheda$G" >/dev/null 2>&1; then
			ok "gruppo $G (scheda$G) creato dentro, per $N — il nome $NOME_G era gia preso"
		else
			ko "il gid $G di $N NON ha un nome dentro: le maglie usciranno 3"
		fi
	done

	# La prova che l'allineamento dei gruppi e' avvenuto DAVVERO — «scritto non
	# e' in vigore»: si rilegge dal nodo, non dal registro dell'unita'.
	G_NODO=$(stat -c %g /dev/dri/renderD128 2>/dev/null)
	G_DENTRO=$(podman exec "$NOME" sh -c 'id -G provanic' 2>/dev/null)
	if printf '%s\n' $G_DENTRO | grep -qx "$G_NODO"; then
		ok "l'inquilino e' nel gruppo della scheda ($G_NODO)"
	else
		ko "l'inquilino NON e' nel gruppo della scheda ($G_NODO): i suoi gruppi sono $G_DENTRO"
		ko "⛔ cosi' il compositore ripiegherebbe sul software, e i numeri sarebbero falsi"
	fi
	;;

prodotto)
	# ⛔⛔ E IL BINARIO SI TOGLIE PRIMA DI RIMETTERLO.  `[M]` 26 agosto 2026: col
	#    server acceso, `cp` sul binario risponde **«Text file busy»** e l azione
	#    fallisce tutt intera — ⛔ un rosso che NON e' del prodotto ma dell ordine
	#    dei comandi, cioe' la forma d errore piu' velenosa: sembra un guasto.
	# ⚠ E la cura NON e' spegnere il server prima: `[M]` provato, `systemctl stop
	#   rete11-server` dentro la scatola **non torna** (resta appeso oltre due
	#   minuti) ⇒ l azione si pianta invece di fallire, che e' peggio.
	#   ⭐ Si toglie il file e lo si riscrive: togliere un eseguibile in uso e'
	#     permesso, sovrascriverlo no.  Il server vecchio continua a girare col
	#     suo inode fino al prossimo `11-accendi.sh server`, ed e' dichiarato.
	# ⛔ IL PRODOTTO SI METTE DENTRO, NON SI COSTRUISCE DENTRO (R1 del documento
	#    di fase): un binario solo, compilato una volta, copiato uguale in tutte
	#    le scatole.  Se ogni scatola si compilasse il suo, i confronti fra
	#    desktop non varrebbero niente — ed e il guasto che l utente ha nominato
	#    per primo: «se sul container GNOME abbiamo remotix v1 e sul container
	#    KDE remotix v1.2 andiamo a sbattere» (D5).
	#
	# ⛔⛔ E LE LIBRERIE VANNO PRESE DOVE LE PRENDE IL SERVER VERO.
	#     `[M]` 26 agosto 2026, e ci e costato un giro: in `/lib` della macchina
	#     c e `libngtcp2.so.16` versione 16.2.9, ma il prodotto gira con quella
	#     costruita in `src/b2/ngtcp2/build/lib`, 16.11.0.  Stesso nome, stesso
	#     «so.16», ⛔ COSA DIVERSA.
	#     ⇒ Con quella sbagliata il server PARTE, dice tutte le sue righe di
	#       avvio, ⛔ e MUORE al primo cliente con
	#       `ngtcp2_settingslen_version: Unreachable` — mentre il cliente vede
	#       soltanto «Idle timeout».  ⚠ Il sintomo era dalla parte sbagliata.
	#
	# ⚠⚠ E NIENTE APOSTROFI dentro il blocco `sh -c` qui sotto: `CODER.md` §4-bis.
	#    `[M]` 26 agosto 2026: un apostrofo in un commento ha chiuso la stringa a
	#    meta, e lo script ha eseguito i pezzi rimasti come comandi.  ⛔ `bash -n`
	#    NON lo prende, perche la sintassi resta valida.
	log "Metto il prodotto dentro $NOME"
	podman exec "$NOME" sh -c '
		set -e
		mkdir -p /opt/remotix/lib /var/lib/rete11/certificati /var/lib/rete11/rilievo
		rm -f /opt/remotix/remotix
		cp /rete11/prodotto/remotix          /opt/remotix/
		cp /rete11/prodotto/pagina.html      /opt/remotix/
		cp /rete11/prodotto/01-b3-cliente.py /opt/remotix/
		cp /rete11/11-c1-nasce-e-si-vede.py  /opt/remotix/
		cp /rete11/11-c2-una-finestra-si-apre.py /opt/remotix/
		cp /rete11/11-c2-finestra.html       /opt/remotix/
		cp /rete11/11-c3-i-fotogrammi-cambiano.py /opt/remotix/
		cp /rete11/11-c3-scena.html          /opt/remotix/
		cp /rete11/11-c4-il-tasto-arriva-allo-schermo.py /opt/remotix/
		cp /rete11/11-c6-si-stacca-e-si-ritrova.py /opt/remotix/
		cp /rete11/11-c8-il-secondo-apre-il-browser.py /opt/remotix/
		cp /rete11/11-c8b-la-pagina-si-vede-dal-cliente.py /opt/remotix/
		cp /rete11/11-c8-pagina.html         /opt/remotix/
		cp /rete11/11-c5-il-suono-non-e-silenzio.py /opt/remotix/
		cp /rete11/11-c7-si-chiude-e-non-resta-niente.py /opt/remotix/
		cp /rete11/11-c9-il-registro-dice-di-chi.py /opt/remotix/
		cp /rete11/10-f1-testimone.py        /opt/remotix/
		# ⭐⭐ L ATTREZZO DEI GRUPPI DELLA SCHEDA — 27 agosto 2026.
		# `[M]` Il difetto piu vecchio del progetto, «la sessione nasce cieca»,
		# era l inquilino NON nei gruppi dei nodi /dev/dri: 17 su 17 vedono coi
		# gruppi, 0 su 4 senza.  ⇒ C1, C5, C6, C7 e C9 chiamano questo attrezzo
		# e senza di lui escono 3 — e hanno ragione.
		# ⚠ E si TRASPORTA, non si ricopia la logica: nel deposito sta in
		#   `banchi/`, cioe un piano sopra a `$BASE`, e nella macchina di prova
		#   sta piatto in `/media/REMOTIX/rete11` come `10-f1-testimone.py`.
		#   ⛔ Un secondo montaggio non serviva e avrebbe portato dentro anche
		#   tutto il resto di quella cartella.
		cp /rete11/attrezzi-gruppi-scheda.sh /opt/remotix/
		cp /rete11/prodotto/remotix.pam      /etc/pam.d/remotix
		rm -f /opt/remotix/lib/*
		cp -a /rete11/prodotto/lib/* /opt/remotix/lib/
		echo /opt/remotix/lib > /etc/ld.so.conf.d/rete11.conf
		ldconfig 2>/dev/null || true
	' || { ko "non sono riuscito a mettere il prodotto dentro"; exit 1; }

	MANCA=$(podman exec "$NOME" sh -c 'ldd /opt/remotix/remotix | grep -c "not found"' 2>/dev/null)
	if [ "${MANCA:-9}" = 0 ]; then
		ok "il prodotto e dentro, e tutte le librerie si risolvono"
		podman exec "$NOME" sh -c 'ldd /opt/remotix/remotix | grep -E "ngtcp2|nghttp3"' | sed 's/^/      /'
	else
		ko "$MANCA librerie non si risolvono: il server morira e non si sapra perche"
		podman exec "$NOME" sh -c 'ldd /opt/remotix/remotix | grep "not found"' | sed 's/^/      /'
		exit 1
	fi
	# ⛔ E il file PAM si verifica DOPO averlo messo: «scritto non e in vigore».
	if podman exec "$NOME" test -f /etc/pam.d/remotix; then
		ok "la catena PAM del prodotto e installata"
	else
		ko "/etc/pam.d/remotix NON c e: PAM ripieghera su «other» = pam_deny, e OGNI parola giusta sara rifiutata"
		exit 1
	fi
	;;

server)
	log "Accendo il server dentro $NOME sulla porta $PORTA"
	podman exec "$NOME" sh -c "
		systemctl stop rete11-server 2>/dev/null
		systemctl reset-failed rete11-server 2>/dev/null
		rm -f /var/lib/rete11/registro.log
		systemd-run --unit=rete11-server \
			--working-directory=/opt/remotix \
			--property=StandardOutput=append:/var/lib/rete11/registro.log \
			--property=StandardError=append:/var/lib/rete11/registro.log \
			--property=KillMode=mixed \
			/opt/remotix/remotix --indirizzo 0.0.0.0 --nome 127.0.0.1 --porta $PORTA \
			--certificati /var/lib/rete11/certificati --pagina /opt/remotix/pagina.html \
			--ban-file /var/lib/rete11/ban --comando-socket /var/lib/rete11/comando.sock \
			--rilievo /var/lib/rete11/rilievo --parlantina
	" >/dev/null 2>&1

	# ⛔ Si aspetta che ASCOLTI, non che il processo esista: «acceso» vuol dire
	#    qualcuno in ascolto sulla porta — lezione della fase 10 (§1.36), dove un
	#    server col processo vivo e nessuno in ascolto passava per acceso.
	PRONTO=0
	for _ in $(seq 1 40); do
		if podman exec "$NOME" grep -q "pronto: https" /var/lib/rete11/registro.log 2>/dev/null; then
			PRONTO=1; break
		fi
		sleep 0.5
	done
	if [ "$PRONTO" = 1 ]; then
		ok "il server ascolta sulla $PORTA"
		podman exec "$NOME" grep -c "⛔" /var/lib/rete11/registro.log 2>/dev/null \
			| sed 's/^/      righe rosse nel registro di avvio: /'
	else
		ko "il server non ha detto di essere pronto in 20 s"
		podman exec "$NOME" tail -8 /var/lib/rete11/registro.log 2>/dev/null | sed 's/^/      /'
		exit 1
	fi
	;;

c1)
	log "C1 — la sessione nasce e si vede (dentro $NOME)"
	GIRI=${3:-5}
	# ⛔ NIENTE `sh -c` qui dentro, e non e un vezzo: `[M]` 26 agosto 2026, un
	#    `podman exec ... sh -c "cd … && python3 …"` annidato dentro `systemd-run`
	#    dentro `ssh` ha perso le virgolette per strada, ⛔ non ha eseguito NIENTE
	#    e ha restituito **0** — cioe un banco che non ha girato e dice «riuscito».
	# ⇒ Il programma si chiama per percorso assoluto, senza guscio in mezzo.
	shift 3 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c1-nasce-e-si-vede.py \
		--giri "$GIRI" --porta "$PORTA" "$@"
	exit $?
	;;

c2)
	log "C2 — una finestra si apre (dentro $NOME)"
	# ⛔ `--applicazione-che-muore` e `--finestra-che-non-si-apre` sono i
	#    COLLAUDI: col guasto innestato l esito si legge al contrario, e il
	#    verde diventa un rosso.
	# ⭐ Il secondo e quello che vale: l applicazione resta VIVA e non dipinge
	#    niente ⇒ il conto dei processi dice 1 come nel caso sano, e il pixel
	#    dice NO.
	# ⚠ Gira solo su gnome: il prodotto sa avviare solo GNOME.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c2-una-finestra-si-apre.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c3)
	log "C3 — i fotogrammi arrivano, e la scena CAMBIA (dentro $NOME)"
	# ⛔ `--fotogramma-ripetuto` e `--codificatore-fermo` sono i COLLAUDI.
	# ⭐ `--scena-ferma` e il controllo NEGATIVO: con la scena ferma la maglia
	#    NON deve dare rosso (a scena ferma Mutter non consegna niente, ed e un
	#    RISULTATO — src/figlio.c:3373).
	# ⚠ Gira solo su gnome: il prodotto sa avviare solo GNOME.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c3-i-fotogrammi-cambiano.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c4)
	log "C4 — il tasto arriva fino allo schermo (dentro $NOME)"
	# ⛔ `--senza-tasto` (testa) e `--scena-sorda` (coda) sono i COLLAUDI: col
	#    guasto innestato l esito si legge al contrario, e il verde diventa un rosso.
	# ⚠ Il prodotto sa avviare solo GNOME: sulle altre scatole C4 dara 3, ed e giusto.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c4-il-tasto-arriva-allo-schermo.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c6)
	log "C6 — si stacca e si ritrova (dentro $NOME)"
	# ⛔ `--uccidi-la-sessione` e il COLLAUDO: col guasto innestato l esito si
	#    legge al contrario, e il verde diventa un rosso.
	# ⚠ Gira solo su gnome: il prodotto sa avviare solo GNOME (src/sessione.c:778),
	#    e sulle altre scatole dara 3 dopo l attesa del compositore.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c6-si-stacca-e-si-ritrova.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c8)
	log "C8 — il secondo utente apre il browser (dentro $NOME)"
	# ⛔ E si passa `--senza-cura` per il COLLAUDO: col guasto innestato
	#    l esito si legge al contrario, e il verde diventa un rosso.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c8-il-secondo-apre-il-browser.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c8b)
	log "C8b — e la stessa pagina si vede DAL CLIENTE (dentro $NOME)"
	# ⛔ SOLO GNOME: il prodotto sa avviare solo lui (src/sessione.c:778).
	#    Sulle altre scatole questa maglia direbbe «non ho potuto guardare»
	#    per sempre, che e il cugino del rosso perpetuo (LEZIONI.md §1.49).
	if [ "$DESKTOP" != gnome ]; then
		log "C8b non gira su $DESKTOP: il prodotto avvia solo GNOME"
		exit 3
	fi
	# ⛔ `--senza-cura` e il COLLAUDO: l esito si legge al contrario.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u \
		/opt/remotix/11-c8b-la-pagina-si-vede-dal-cliente.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c5)
	log "C5 — il suono c e e non e silenzio (dentro $NOME)"
	# ⛔ `--senza-sorgente` e' il COLLAUDO: col guasto innestato l esito si legge
	#    al contrario, e il verde diventa un rosso.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c5-il-suono-non-e-silenzio.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c7)
	log "C7 — si chiude tutto, e non resta niente (dentro $NOME)"
	# ⛔ `--lascia-un-processo` e' il COLLAUDO.
	# ⭐ `--solo-distacco` e' il caso che NON deve dare rosso: il cliente se ne
	#    va e il palco resta in piedi (I4).
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c7-si-chiude-e-non-resta-niente.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

c9)
	log "C9 — il registro dice DI CHI parla (dentro $NOME)"
	# ⛔ La maglia apre DUE inquilini e li tiene vivi INSIEME: e' la forma forte,
	#    e con uno solo non proverebbe quel che dice.
	# ⚠ Il guasto innestato si chiede con `--togli-nome tutto`, e sfregia la
	#   COPIA in memoria della fetta: il registro sul disco non si tocca.
	shift 2 2>/dev/null || shift $#
	podman exec "$NOME" python3 -u /opt/remotix/11-c9-il-registro-dice-di-chi.py \
		--porta "$PORTA" "$@"
	exit $?
	;;

passo0)
	log "Il passo 0 dentro $NOME"
	podman exec "$NOME" bash /rete11/11-passo0.sh
	exit $?
	;;

impronta)
	# ⛔ R3 del documento di fase: l'allineamento si VERIFICA.  Qui si stampa
	#    quel che va confrontato fra le quattro scatole — ⭐ la ricetta CONTA
	#    QUANTO il binario: una scatola ricostruita che tira dentro un desktop
	#    piu' nuovo ha lo stesso binario e un ambiente diverso.
	printf 'scatola      : %s\n' "$NOME"
	printf 'immagine     : %s\n' "$(podman image inspect "$IMMAGINE" --format '{{.Id}}' 2>/dev/null | cut -c1-16)"
	printf 'ricetta (md5): %s\n' "$(md5sum "$RICETTA" | cut -c1-16)"
	# ⭐ Il pacchetto del desktop lo dice l ADATTATORE, non questo file: cosi'
	#   l impronta vale per tutti e quattro senza un solo «se il desktop e'…».
	PACCO=$(podman exec "$NOME" sh -c '. /usr/local/lib/rete11/adattatore.sh 2>/dev/null && adattatore_pacchetto' 2>/dev/null)
	printf 'desktop      : %s %s\n' "${PACCO:-ignoto}" \
	       "$(podman exec "$NOME" sh -c "dpkg-query -W -f='\${Version}' ${PACCO:-x} 2>/dev/null || echo ignoto" 2>/dev/null)"
	printf 'mesa         : %s\n' "$(podman exec "$NOME" sh -c 'dpkg-query -W -f="${Version}" mesa-va-drivers 2>/dev/null || echo ignoto' 2>/dev/null)"
	printf 'prodotto     : %s\n' "$(podman exec "$NOME" sh -c 'md5sum /opt/remotix/remotix 2>/dev/null | cut -c1-16 || echo "(non ancora dentro)"' 2>/dev/null)"
	;;

spegni)
	podman rm -f -t 0 "$NOME" >/dev/null 2>&1 && ok "$NOME spenta" || ko "non c'era"
	;;

*)
	# ⛔⛔ E L AIUTO NON SI STAMPA PIU' CONTANDO LE RIGHE.
	#    `[M]` 27 agosto 2026: qui c era `sed -n 2,16p`, e con le cinque maglie
	#    nuove il blocco d uso e diventato piu' lungo ⇒ l aiuto tagliava in
	#    silenzio le sue ultime righe, cioe' `impronta` e `spegni` sparivano
	#    dall aiuto restando nel programma.  ⚠ Un numero di riga inchiodato
	#    dentro un file che cresce e' un cartello che si stacca da solo.
	# ⇒ Adesso si stampa dalla riga 3 fino alla riga di `# ====` che chiude il
	#   blocco, qualunque sia il suo numero: il file puo' crescere quanto vuole.
	sed -n '3,/^# ====/{/^# ====/d; p;}' "$0"
	exit 2 ;;
esac
