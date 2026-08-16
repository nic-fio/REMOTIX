#!/bin/bash
#
# 02-cattura-lancia.sh — gira SUL SERVER (NIC-OS), fuori dal contenitore.
# Il banco della sotto-fase F2.2: UN fotogramma preso dalla sessione GNOME,
# con il tipo di buffer dichiarato e i PIXEL guardati.
#
#   bash /media/REMOTIX/src/02-cattura-lancia.sh compila     una volta (nel contenitore)
#   bash /media/REMOTIX/src/02-cattura-lancia.sh scena       genera la scena dichiarata
#   bash /media/REMOTIX/src/02-cattura-lancia.sh misura      un giro
#   bash /media/REMOTIX/src/02-cattura-lancia.sh elenco      gli attesi, senza misurare
#
# ===========================================================================
# ⛔ PERCHE' QUESTO BANCO ESISTE, VISTO CHE LA FASE 0 GIA' MISURA LA CATTURA
#
# `v1/banchi/banco-compositori/misura-cattura` e' certificato, riproduce i
# 36 ± 2 fotogrammi al secondo di Mutter, e resta il controllo positivo storico
# di tutto il progetto (`FASI.md` §00-ambiente).  ⛔ Ma i pixel non li guarda mai:
# legge tipo, fd, stride, danno e sequenza, e rimette il buffer in coda senza
# toccare `piano->data`.
#
# ⇒ **Un fotogramma completamente NERO passerebbe la fase 0 con il massimo dei
#   voti**: 36 al secondo, quattro buffer riciclati, danno parziale, zero salti.
#   Tutto verde, e sullo schermo il nulla.
#
# ⛔ E il nero e' esattamente il guasto che questa fase rischia:
#
#   | dove sta scritto        | che cosa dice                                  |
#   |-------------------------|------------------------------------------------|
#   | `STUDI.md` §gnome §3.1         | in headless `needs_outputs=false`: senza       |
#   |                         | `--virtual-monitor` la sessione parte **viva,  |
#   |                         | completa e nera**                              |
#   | `STUDI.md` §gnome §13, M9      | e' una prova da fare **guasta di proposito**,  |
#   |                         | per imparare che aspetto ha il guasto          |
#   | `PIANO.md`, fase 2      | *«una sessione nera e perfettamente viva e' la |
#   |                         | cosa che si scambia per un difetto di cattura, |
#   |                         | e si cerca per mezza giornata dalla parte      |
#   |                         | sbagliata»*                                    |
#
# La misura sbagliata che questo banco impedisce, detta in una riga: **«la
# cattura consegna» scritto in una tabella accanto a un fotogramma vuoto.**
#
# ===========================================================================
# ⛔ LA SCENA SI DICHIARA, E QUESTA E' DIVERSA DA QUELLA DELLA FASE 0 — CON UNA
#    RAGIONE, NON PER GUSTO
#
# `CODER.md` §3.2: la scena si dichiara e si muove sempre.  La fase 0 usava
# `weston-simple-egl -f -o`, che si muove benissimo — ma **nei pixel non e'
# riconoscibile**: un triangolo che gira non ha una firma, e F2.6 (il confronto
# fra il fotogramma catturato e quello decodificato) non avrebbe niente da
# confrontare.  Un banco di F2.2 con quella scena saprebbe dire «arrivano
# fotogrammi» e non saprebbe dire «arriva il DESKTOP».
#
# ⭐ SCENA «bandiera»: le sette barre SMPTE a tutto schermo, FERME, piu' un
#    blocco bianco che scorre in basso a ogni fotogramma.
#
#   la parte ferma   e' la firma: sta nei pixel e non nel tempo, quindi due
#                    giri diversi si possono confrontare — che e' quel che
#                    serve a un'IMMAGINE FERMA e a F2.6
#   la parte mossa   Mutter consegna un fotogramma **solo se qualcosa cambia**
#                    (`LEZIONI.md` §4 trappola 8).  Senza il blocco che scorre,
#                    su un desktop fermo non arriverebbe nulla: uno zero
#                    legittimo, e un banco muto
#   il blocco sta    cosi' la firma non dipende dall'ISTANTE in cui il
#   in un angolo     fotogramma e' stato preso
#
# ⚠ E la scena della fase 0 resta disponibile (`SCENA=tetto`), perche' e' il
#   legame con il controllo positivo storico: su di essa il giudizio dei pixel
#   si riduce a «non e' nero e non e' uniforme», e lo dice.
#
# ===========================================================================
# ⛔ L'ORDINE: PRIMA IL MONITOR VIRTUALE, POI LA SCENA — e con un EVENTO
#
# `banco.sh` della fase 0 accende la scena 2,5 secondi dopo il misuratore, con
# la ragione scritta accanto: *«senza uno schermo non c'e' dove aprirsi»*.  Qui
# l'attesa a tempo non basta, perche' il produttore deve poi sapere QUALI
# fotogrammi sono arrivati prima della scena e quali dopo — e' la separazione
# fra il fotogramma dell'avvio e quello di regime (`CODER.md` §3.5, forma E9).
#
# Quindi:  il produttore scrive `pronto` quando il flusso e' ATTIVO
#       →  questo script accende la scena e ne verifica la vita
#       →  questo script scrive `scena-accesa`
#       →  solo allora il produttore comincia a contare il regime
#
# ⭐ Non e' un'attesa: e' un evento (`LEZIONI.md` §4 trappola 9 — «non si aspetta
#    un silenzio, si aspetta un evento»).
#
# ⚠ E la stessa forma morde la fase 2 da un'altra parte, gia' misurata: in una
#   sessione GNOME senza dispositivi di input, un client aperto PRIMA che il
#   puntatore virtuale di `libei` esista non riceve nulla — `PIANO.md`, riquadro
#   «Una domanda che la fase 1 ha trovato e che morde QUI», `[M]` 10 agosto 2026.
#   Qui nessun dispositivo si crea (non e' l'area di F2.2), ma chi montera'
#   l'input dovra' infilarlo fra il `pronto` e la scena, non prima.
#
# ===========================================================================
# ⛔ ZERO E FALLIMENTO SONO DUE COSE DIVERSE — e qui sono QUATTRO
#
#   0  ⭐ VERDE: un fotogramma c'e', e' della misura chiesta, e contiene la scena
#   1  ROSSO: c'e' un fotogramma e qualcosa non torna. La marca dice cosa —
#      FOTOGRAMMA NERO · FOTOGRAMMA UNIFORME · SCENA NON RICONOSCIUTA ·
#      BYTE NON TORNANO · MISURA DIVERSA DA QUELLA CHIESTA · IL BUFFER NON E'
#      CAMBIATO
#   3  ⭐ ZERO FOTOGRAMMI, o strada DMA-BUF (pixel non leggibili da qui): non
#      c'e' niente da giudicare, e NON e' un rosso
#   2  ⛔ SONO FALLITO: la scena non parte, il flusso non e' mai stato attivo o
#      e' caduto, il binario e' piu' vecchio del sorgente, il giudice non passa
#      il proprio controllo positivo
#
# ⛔ Niente `2>/dev/null` in questo file, e nessuno stato d'uscita buttato in
#    una catena di `|`.  Le tre voci 1, 3 e 8 di «Che cosa NON ha funzionato»
#    di `FASI.md` §00-ambiente sono tre facce di quest'unica regola, e sono state
#    pagate tutte e tre in un pomeriggio.
#
# ===========================================================================
# ⛔ CHE COSA QUESTO BANCO **NON** DICE
#
#   - **niente sul ritmo.** Il produttore copia due fotogrammi da 8 MB dentro la
#     richiamata di tempo reale di PipeWire: un numero di fotogrammi al secondo
#     che uscisse da qui sarebbe falsato da noi. Il ritmo e' della fase 0
#     (36 ± 2 `[M]`) e della fase 3
#   - **niente su dove Mutter renda.** ⛔ Forma E1 di `REVIEWER.md` §2: «consegna
#     MemFd ⇒ e' in software» e «ha aperto un render node ⇒ rende in GPU» sono
#     due errori gia' pagati (`LEZIONI.md` §1.11). Qui la memoria si CHIEDE —
#     servono i pixel leggibili — quindi MemFd e' la risposta a una nostra
#     domanda, non una scoperta
#   - **niente sulla codifica.** Da qui esce BGRx a 32 bit, che e' l'unico
#     formato che Mutter consegna (`STUDI.md` §gnome §8.3: «Solo BGRx e BGRA»). La
#     conversione a 10 bit e' di F2.3
#
# ⚠ E la macchina ha DUE GPU (Intel `0000:00:02.0`, Radeon `0000:03:00.0`): un
#   buffer della scheda sbagliata non e' importabile, e il sintomo e'
#   composizione in software **senza un errore da nessuna parte**
#   (`LEZIONI.md` §4 trappola 6). ⛔ Questo banco NON lo vedrebbe: sulla strada
#   della memoria i pixel arrivano comunque. E' una `[?]` dichiarata, non una
#   cosa che il verde qui sotto assolve.
#
# ===========================================================================
set -uo pipefail

QUI=${QUI:-/media/REMOTIX/tmp/02-cattura}
SRC=${SRC:-/media/REMOTIX/src}
# ⭐ IL PRODUTTORE SI DICHIARA, E SONO DUE — aggiunto il 12 agosto 2026 con il
#    prodotto (P2.2).  Il banco e' nato prima del prodotto e certificava il
#    produttore scritto DENTRO di se': quel verde non diceva niente sul
#    prodotto, perche' il prodotto non esisteva ancora (`LEZIONI.md` §1.3).
#
#      PROG=$QUI/02-cattura-fotogramma  FONTE=$SRC/02-cattura-fotogramma.c
#          il produttore del banco, quello certificato il 12 agosto
#      PROG=$QUI/02-cattura-prodotto    FONTE=$SRC/02-cattura-prodotto.c
#          ⭐ IL PRODOTTO: src/cattura.c + src/mutter.c, dietro la stessa riga
#          di comando e con lo stesso manifesto
#
# ⛔ E il giudice non cambia: giudica i PIXEL, e non sa chi li ha fatti.  Due
#    produttori indipendenti sotto lo stesso giudice sono un controllo positivo
#    che nessuno dei due sarebbe da solo.
PROG=${PROG:-$QUI/02-cattura-fotogramma}
FONTE=${FONTE:-$SRC/02-cattura-fotogramma.c}
GIUDICE=$SRC/02-cattura-giudica.py
ESITI=${ESITI:-$SRC/02-cattura-esiti.jsonl}

# ⛔ LA PORTA DI QUESTO AGENTE E' LA 7512, e qui non si apre nessuna porta.
#    La riga esiste lo stesso perche' il mandato la assegna e perche' un banco
#    che non nomina la propria porta e' un banco che un giorno ne prende una
#    d'altri: sulla 7448 e sulla 7501 girano due server voluti (§4 del mandato).
PORTA_DI_QUESTO_BANCO=7512

SCENA=${SCENA:-bandiera}
LARGHEZZA=${LARGHEZZA:-1920}
ALTEZZA=${ALTEZZA:-1080}
FPS=${FPS:-60}
DOPO_SCENA=${DOPO_SCENA:-3}
SCARTA=${SCARTA:-10}
DURATA=${DURATA:-12}
STRADA=${STRADA:-memoria}
ETICHETTA=${ETICHETTA:-F2.2-$SCENA-${LARGHEZZA}x${ALTEZZA}-$STRADA}

# L'ambiente della sessione, composto da zero: chi eredita il proprio ambiente
# regala a un processo grafico anche le variabili che non c'entrano
# (`CODER.md` §4.5).
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export XDG_CURRENT_DESKTOP=GNOME
export XDG_SESSION_TYPE=wayland
export LANG=C.UTF-8

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------------------
# ⛔ GLI ATTESI SI SCRIVONO PRIMA DEL GIRO — B0.4, e vale la regola nata l'11
#    agosto: chi scrive un banco lo certifica nello stesso giro.
# ---------------------------------------------------------------------------
elenco()
{
	cat <<'FINE'

  GLI ATTESI DI QUESTO BANCO, scritti PRIMA di misurare
  ────────────────────────────────────────────────────────────────────────
  scena «bandiera», 1920×1080, strada memoria:

    che cosa                          atteso                    da dove viene
    ─────────────────────────────────────────────────────────────────────────
    fotogrammi arrivati               > 0                       la scena si muove a ogni
                                                                fotogramma (trappola 8)
    tipo di buffer dichiarato         MemFd                     [?] MAI MISURATO su questa
                                                                strada: la fase 0 misurava
                                                                DMA-BUF. Si scrive quel che
                                                                esce, non quel che si spera
    misura negoziata                  1920×1080                 Mutter fa il monitor della
                                                                misura chiesta (cattura.h)
    formato negoziato                 BGRx                      STUDI.md §gnome §8.3, R32 riga per
                                                                riga: solo BGRx e BGRA
    stride                            ≥ 7680                    ⛔ si LEGGE dal chunk, mai
                                                                calcolato (cattura.h)
    byte del .raw                      stride × 1080             [?] dipende dallo stride vero
    danno sul fotogramma «primo»      pieno                     e' il ridisegno dell'avvio
    danno sul fotogramma «regime»     parziale                  fase 0: pieno 15, parziale 929
    buffer distinti riciclati         4                         R29, e la fase 0 lo conferma
    la scena si vede nel «regime»     SI'                       ⭐ e' la domanda di F2.2
    «primo» diverso da «regime»       SI'                       o il buffer e' vecchio

  ⭐ E LA DOMANDA CHE NESSUN DOCUMENTO SA RISPONDERE OGGI, e che questo giro
     decide con una misura invece che con una rilettura:

     un fotogramma con danno PARZIALE e' comunque INTERO?

       `v1/remotix-c/src/cattura.h`  dice di NO: *«Mutter ricicla i propri
                                     buffer e vi ridipinge dentro SOLO la parte
                                     cambiata; fuori da quelle regioni ci sono i
                                     pixel del fotogramma di prima»*
       `STUDI.md` §gnome §8.1               dice di SI': *«⛔ falso: blit dell'intero
                                     framebuffer, stack di clip svuotato
                                     deliberatamente»*, dopo aver riletto Mutter

     ⚠ E la posta e' alta: se avesse ragione `cattura.h`, la fase 2 consegnerebbe
       mezzo desktop e meta' schermata vecchia, senza un errore da nessuna parte.

  ⛔ E il caso opposto, scritto prima (LEZIONI.md §1.11):
     che aspetto avrebbe il CONTRARIO?

       fotogramma nero e valido   → luminanza media ≈ 0, marca FOTOGRAMMA NERO.
                                    E' quel che darebbe una sessione senza
                                    monitor virtuale: viva, completa e nera
       scena non partita          → il produttore esce 2 con «la scena non e'
                                    mai stata dichiarata accesa», non uno zero
       desktop fermo              → uscita 3, ZERO FOTOGRAMMI: legittimo
       buffer di un'altra scheda  → ⚠ questo banco NON lo vedrebbe: sulla strada
                                    della memoria i pixel arrivano comunque

FINE
}

# ---------------------------------------------------------------------------
# ⛔ IL BINARIO CHE SI ESEGUE DEVE ESSERE PIU' NUOVO DEL SORGENTE.
#
# Non si ricompila da qui — la compilazione vuole il contenitore e la parola
# d'ordine di `sudo` — ci si RIFIUTA di misurare, che e' l'unica cosa onesta.
# Il 9 agosto 2026 la fase 0 ha trovato in casa un `misura-cattura` del giorno
# prima, cioe' senza le cure scritte il giorno dopo: chi l'avesse lanciato
# avrebbe ripreso difetti che i documenti dichiarano chiusi, senza una riga che
# glielo dicesse.
# ---------------------------------------------------------------------------
controlla_binario()
{
	if [ ! -x "$PROG" ]; then
		ko "⛔ manca $PROG"
		inf "compilalo:  bash $0 compila"
		return 1
	fi
	if [ "$FONTE" -nt "$PROG" ]; then
		ko "⛔ $PROG e' PIU' VECCHIO del suo sorgente $FONTE."
		inf "Misurare adesso vorrebbe dire eseguire codice diverso da quello letto."
		inf "Ricompila:  bash $0 compila"
		return 1
	fi
	ok "il binario e' piu' nuovo del sorgente"
	return 0
}

compila()
{
	log "compilo dentro il contenitore"
	mkdir -p "$QUI" || return 1
	# ⛔ MAI UNA REDIREZIONE ATTORNO A `enter.sh`: la richiesta di parola
	#    d'ordine di `sudo` va sullo stderr, e una redirezione la mangia — il
	#    comando resta appeso per sempre, in silenzio.  Dentro le virgolette
	#    si', attorno no.  `FASI.md` §00-ambiente B3.3, pagata quattro volte.
	bash /media/REMOTIX/enter.sh "cd /srv/remotix/tmp/02-cattura && \
	    gcc -O2 -Wall -o 02-cattura-fotogramma /srv/src/02-cattura-fotogramma.c \
	        \$(pkg-config --cflags --libs libpipewire-0.3 gio-2.0 libdrm)"
	local esito=$?
	if [ $esito -ne 0 ]; then
		ko "⛔ la compilazione e' fallita (uscita $esito)"
		return 1
	fi
	ok "compilato: $PROG"
	ls -la "$PROG"
	return 0
}

# ---------------------------------------------------------------------------
#  La scena dichiarata
# ---------------------------------------------------------------------------
file_scena() { echo "$QUI/bandiera-${LARGHEZZA}x${ALTEZZA}.mp4"; }

genera_scena()
{
	local f
	f=$(file_scena)
	mkdir -p "$QUI" || return 1
	if [ -s "$f" ]; then
		ok "la scena c'e' gia': $f"
		return 0
	fi
	log "genero la scena dichiarata «bandiera» ${LARGHEZZA}x${ALTEZZA}"
	inf "sette barre SMPTE ferme (la firma) + una sfumatura a 256 livelli (i bit veri)"
	inf "+ un blocco bianco che scorre (il movimento, senza cui Mutter non consegna)"
	# ⛔ `-qp 0`: la firma sta nei pixel, e un quantizzatore che sporca le bande
	#    farebbe fallire un giudice che ha ragione.  ⚠ Il 4:2:0 resta — nessun
	#    decoder Android fa 4:4:4 (`CODER.md` §1) — ma la firma e' scelta per
	#    sopravvivergli: si controllano l'ordine e il dominio dei canali, non i
	#    valori RGB assoluti.
	# ⛔ DUE COSE IMPARATE QUI IL 12 AGOSTO 2026, E TUTT'E DUE COSTANO UN GIRO:
	#
	#  1. il modulo si scrive SENZA `mod(a,b)`.  La virgola e' il separatore dei
	#     filtri di ffmpeg e va protetta con una barra rovescia — che pero'
	#     attraversa `bash`, `ssh` e la shell remota, e in uno dei tre si perde.
	#     Sintomo: «Undefined constant or missing '('».
	#     `t*V - P*floor(t*V/P)` e' lo stesso numero senza nessuna virgola;
	#  2. ⛔ e la variabile e' `t`, NON `n`: `drawbox` non espone il numero di
	#     fotogramma, solo il tempo.  Con `n` da' lo stesso identico messaggio
	#     d'errore del punto 1 — due cause diverse sotto la stessa faccia, ed e'
	#     il motivo per cui questo commento le nomina tutte e due.
	#
	# ⚠ Il blocco corre a 720 px al secondo: a 60 fotogrammi al secondo sono 12
	#   px per fotogramma, quindi due fotogrammi consecutivi sono SEMPRE diversi
	#   — che e' quel che tiene viva la consegna di Mutter (trappola 8).
	#
	# ⛔ E LA TERZA PARTE DELLA SCENA E' UNA SFUMATURA, ed e' li' per una domanda
	#    che non e' mia ma che nasce qui: la **cucitura di F2.3**.
	#
	#    F2.3 chiama **F2.3-A** il guasto in cui *«la cattura consegna 8 bit,
	#    tutta la catena resta verde e l'etichetta continua a dire Main10»* — e
	#    nessuno se ne accorge guardando l'immagine, perche' viene bene lo
	#    stesso.  Il numero che lo smaschera e' quanti LIVELLI DISTINTI porta un
	#    fotogramma, e la frazione di multipli di 4.
	#
	#    ⛔ Ma sette barre piatte hanno una ventina di livelli in tutto **per
	#      costruzione**: su quella scena il conto dei livelli non distingue un
	#      percorso povero da uno ricco, e un rosso li' sarebbe un rosso sulla
	#      scena.  Una sfumatura da nero a bianco larga tutto lo schermo li
	#      attraversa tutti e 256: e' l'unica parte dell'immagine su cui quel
	#      conto vuol dire qualcosa.
	#
	#    ⭐ Cosi' UNA scena sola risponde a tutt'e tre le domande — c'e' il
	#       fotogramma (il movimento), e' il DESKTOP (le barre), quanti bit sono
	#       veri (la sfumatura) — e F2.3 puo' rifare lo stesso conto sullo stesso
	#       fotogramma invece che su un altro.
	local corsa=$((LARGHEZZA - 160))
	local y_sfumatura=$((ALTEZZA - 240))
	ffmpeg -nostdin -loglevel error -y \
	       -f lavfi -i "smptebars=size=${LARGHEZZA}x${ALTEZZA}:rate=60" \
	       -f lavfi -i "color=black:size=${LARGHEZZA}x100:rate=60,geq=r='floor(X*256/W)':g='floor(X*256/W)':b='floor(X*256/W)'" \
	       -filter_complex "[0][1]overlay=0:${y_sfumatura},drawbox=x='t*720-${corsa}*floor(t*720/${corsa})':y=$((ALTEZZA - 120)):w=160:h=100:color=white:t=fill" \
	       -t 30 -c:v libx264 -preset ultrafast -qp 0 -pix_fmt yuv420p "$f"
	local esito=$?
	if [ $esito -ne 0 ] || [ ! -s "$f" ]; then
		ko "⛔ ffmpeg non ha prodotto la scena (uscita $esito)"
		return 1
	fi
	ok "scena generata: $(ls -la "$f")"
	return 0
}

# ---------------------------------------------------------------------------
# ⛔ LO SCHERMO SI DICHIARA ALLA SCENA, E POI SI VERIFICA CHE ABBIA OBBEDITO
#
# Trovato il 12 agosto 2026, al PRIMO giro vero di questo banco — e trovato
# perche' il banco e' uscito **VERDE** mentre il difetto era vivo.
#
# La sessione GNOME aveva gia' un monitor virtuale (`Meta-0`, di un altro giro);
# il nostro `RecordVirtual` ne aggiungeva un secondo (`Meta-1`); e `mpv --fs`
# andava a schermo intero sul PRIMO.  La scena era viva — `ps` diceva `Sl`, il
# registro contava i secondi, i fotogrammi decodificati scorrevano — e la nostra
# cattura riceveva **zero fotogrammi**.
#
# ⚠ La fase 0 non l'aveva mai incontrato perche' allora la sessione non aveva
#   nessun altro monitor: il monitor montato dal banco era l'unico, e qualunque
#   finestra a schermo intero ci finiva sopra per forza.  ⛔ Il difetto non era
#   nel banco della fase 0: era **nell'ipotesi che quel banco poteva permettersi
#   e questo no**.
#
# ⇒ `CODER.md` §3.9: *«quando un componente puo' decidere da se', digli cosa
#   fare — e verifica che abbia obbedito»*.  Qui il componente e' mpv, e la cosa
#   che decideva da se' era su quale schermo aprirsi.
#
# Come si sa qual e' il nostro: si guardano i monitor PRIMA di montare e DOPO, e
# il nuovo e' il nostro.  ⛔ E se non ne compare esattamente uno, non si tira a
# indovinare: si dichiara il fallimento.
# ---------------------------------------------------------------------------
elenco_monitor()
{
	gdbus call --session --dest org.gnome.Mutter.DisplayConfig \
	           --object-path /org/gnome/Mutter/DisplayConfig \
	           --method org.gnome.Mutter.DisplayConfig.GetCurrentState \
	  > "$QUI/monitor-$1.txt"
	local esito=$?
	if [ $esito -ne 0 ]; then
		# ⛔ Una lettura NEGATA non e' una lettura che dice «nessun monitor».
		echo "GUASTO-DBUS"
		return 1
	fi
	grep -o "'Meta-[0-9]*'" "$QUI/monitor-$1.txt" | tr -d "'" | sort -u
	return 0
}

# ⛔ IL MONITOR SI DICHIARA PER NOME, MAI PER INDICE E MAI PER MISURA.
#
# Chiesto da F2.1 (la sessione) e gia' pagato sul campo: sul server ci sono DUE
# monitor virtuali — `Meta-0` / **MetaVirtualMonitor** (quello della sessione,
# messo dal drop-in di F2.1) e `Meta-1` / **Virtual remote monitor** (quello che
# monta `RecordVirtual`, cioe' il nostro) — ed ⛔ **entrambi sono 1920×1080@60**.
# Li distingue solo il nome del prodotto.
#
# ⇒ Scegliere «il primo» o «quello a 1080p» e' la forma d'errore **E2**: due cose
#   diverse sotto la stessa etichetta.  Qui si prende il nome dal diff prima/dopo
#   E si controlla che il prodotto corrisponda: due strade indipendenti che
#   devono dire la stessa cosa, o non si misura.
prodotto_di()
{
	python3 - "$QUI/monitor-dopo.txt" "$1" <<'FINE'
import re, sys
testo = open(sys.argv[1]).read()
# ('Meta-1', 'MetaVendor', 'Virtual remote monitor', '0x00')
for connettore, venditore, prodotto in re.findall(
        r"\('(Meta-\d+)', '([^']*)', '([^']*)'", testo):
    if connettore == sys.argv[2]:
        print(prodotto)
        break
else:
    print("SCONOSCIUTO")
FINE
}

SCHERMO=

PRODOTTO_SCHERMO=

trova_il_nostro_schermo()
{
	local prima=$1 dopo nuovi
	dopo=$(elenco_monitor dopo) || { ko "⛔ DisplayConfig non risponde: non so su che schermo siamo"; return 1; }
	nuovi=$(comm -13 <(echo "$prima") <(echo "$dopo"))
	local quanti
	quanti=$(echo "$nuovi" | grep -c '^Meta-')
	inf "monitor prima: $(echo "$prima" | tr '\n' ' ')"
	inf "monitor dopo:  $(echo "$dopo" | tr '\n' ' ')"
	if [ "$quanti" != 1 ]; then
		ko "⛔ dopo il montaggio sono comparsi $quanti monitor nuovi, non 1."
		inf "Non tiro a indovinare quale sia il nostro: senza saperlo, la scena"
		inf "andrebbe su uno schermo che non stiamo catturando, e il banco"
		inf "misurerebbe il buio dichiarando la scena (12 agosto 2026)."
		return 1
	fi
	SCHERMO=$(echo "$nuovi" | grep '^Meta-')
	PRODOTTO_SCHERMO=$(prodotto_di "$SCHERMO")
	inf "il nome del prodotto di $SCHERMO e': «$PRODOTTO_SCHERMO»"
	# ⛔ E LA SECONDA STRADA DEVE CONFERMARE LA PRIMA.  Il nostro monitor lo
	#    monta `RecordVirtual`, e Mutter lo chiama «Virtual remote monitor»;
	#    quello della sessione si chiama «MetaVirtualMonitor».  Se il diff
	#    dicesse uno e il nome del prodotto l'altro, non si sceglie il piu'
	#    comodo: ci si ferma.
	case "$PRODOTTO_SCHERMO" in
	*"remote"*|*"Remote"*)
		ok "le due strade concordano: $SCHERMO e' il monitor che abbiamo montato noi"
		;;
	*)
		ko "⛔ il monitor comparso ($SCHERMO) si chiama «$PRODOTTO_SCHERMO», e non e'"
		inf "il nome che Mutter da' a un monitor di RecordVirtual («Virtual remote"
		inf "monitor»).  Le due strade non concordano: mi fermo invece di scegliere."
		inf "⚠ Su questo server ci sono due monitor virtuali ENTRAMBI 1920×1080@60:"
		inf "  li distingue solo il nome del prodotto (cucitura di F2.1)."
		return 1
		;;
	esac
	return 0
}

# ---------------------------------------------------------------------------
# ⛔ LO STATO DELLA SESSIONE SI GUARDA PRIMA DI OGNI CONTA, E FINISCE NELL'ESITO
#
# Chiesto da F2.1, e la ragione e' che **senza, un mio zero non ha imputato**:
# la sessione GNOME su NIC-OS ha girato dal 10 agosto con **ZERO MONITOR** —
# avviata `--headless --no-x11` senza `--virtual-monitor`, con `IsSessionRunning`
# a true, cinquanta nomi sul bus e le applicazioni accese.  ⇒ Una cattura
# puntata li' avrebbe misurato zero fotogrammi, e la colpa sarebbe finita sulla
# cattura.
#
# ⚠ E se lo strumento di F2.1 non c'e' ancora sul server, lo si DICHIARA: un
#   controllo saltato in silenzio e un controllo passato hanno lo stesso aspetto,
#   ed e' la forma E8.
STATO_SESSIONE=
guarda_la_sessione()
{
	local s=$SRC/02-sessione-stato.py
	if [ ! -r "$s" ]; then
		STATO_SESSIONE="non disponibile (manca $s, di F2.1)"
		inf "⚠ $STATO_SESSIONE — questo giro non ha il testimone della sessione"
		return 0
	fi
	python3 -u "$s" > "$QUI/sessione.txt" 2>&1
	local esito=$?
	STATO_SESSIONE="02-sessione-stato.py uscita $esito"
	sed 's/^/       /' "$QUI/sessione.txt"
	if [ $esito -ne 0 ]; then
		ko "⛔ la sessione non e' sana ($STATO_SESSIONE)"
		inf "⚠ Si rimette con: bash $SRC/02-sessione-lancia.sh sano — e NON si misura prima."
		return 1
	fi
	ok "la sessione e' sana ($STATO_SESSIONE)"
	return 0
}

avvia_scena()
{
	local f
	case $SCENA in
	bandiera)
		f=$(file_scena)
		if [ ! -s "$f" ]; then echo IGNOTA; return; fi
		# ⛔ `stdbuf -oL`: verso un file l'uscita e' bufferizzata a blocchi, e
		#    alla chiusura della scena il suo registro resta nel buffer.  Il
		#    registro vuoto sembra «la scena non ha detto niente», ed e' la
		#    voce 12 di `FASI.md` §00-ambiente.
		# ⛔ `--fs-screen-name` NON e' un dettaglio: e' la differenza fra
		#    misurare la scena e misurare il buio (vedi il riquadro qui sopra).
		stdbuf -oL mpv --no-config --fs --fs-screen-name="$SCHERMO" \
		    --loop=inf --no-audio --no-osc \
		    --no-input-default-bindings --profile=low-latency \
		    "$f" >"$QUI/scena.log" 2>&1 &
		echo $!
		;;
	tetto)
		# La scena della fase 0, tenuta per il legame col controllo positivo
		# storico.  ⛔ E si lancia con `pgrep -f`, mai `pgrep -x`: `comm` e'
		# troncato a 15 caratteri e `weston-simple-egl` ne ha 17 — difetto di
		# banco gia' pagato, `FASI.md` §00-ambiente B3 punto 1.
		#
		# ⚠ E QUI LO SCHERMO NON SI PUO' DICHIARARE: `weston-simple-egl` non ha
		#   un'opzione per scegliere l'uscita.  ⇒ Su una sessione che ha piu' di
		#   un monitor questa scena e' inaffidabile, e non e' un difetto del
		#   banco: e' un limite del client, dichiarato qui invece che scoperto
		#   guardando uno zero.
		stdbuf -oL weston-simple-egl -f -o >"$QUI/scena.log" 2>&1 &
		echo $!
		;;
	fermo)
		# ⭐ Il caso opposto, come scena: nessuno dipinge.  L'atteso e' uscita 3
		#    (ZERO FOTOGRAMMI), non un rosso e non un verde.
		echo 0
		;;
	*)
		# ⛔ E UN NOME DI SCENA SCONOSCIUTO NON E' «NESSUNA SCENA»: senza questo
		#    ramo, una lettera sbagliata darebbe una misura su uno schermo su cui
		#    non ha disegnato nessuno, con uscita 0.
		echo IGNOTA
		;;
	esac
}

# ---------------------------------------------------------------------------
#  Il giro
# ---------------------------------------------------------------------------
misura()
{
	local pronto=$QUI/pronto accesa=$QUI/scena-accesa
	local prefisso=$QUI/giro-$(date -u +%Y%m%d-%H%M%S)
	local pid_prod pid_scena stato uscita_prod uscita_giud i morta=

	mkdir -p "$QUI" || return 2
	rm -f "$pronto" "$accesa" "$QUI/scena.log"

	log "0. lo stato iniziale si dichiara E si verifica"
	controlla_binario || return 2
	if [ ! -r "$GIUDICE" ]; then ko "⛔ manca il giudice: $GIUDICE"; return 2; fi
	ok "il giudice si legge: $GIUDICE"
	if ! pgrep -f 'gnome-shell' >/dev/null; then
		ko "⛔ non c'e' nessuna gnome-shell viva: non c'e' niente da catturare"
		inf "⚠ e questo NON e' uno zero: e' l'assenza dell'imputato. La sessione e' di F2.1."
		return 2
	fi
	ok "gnome-shell e' viva (pid $(pgrep -f 'gnome-shell' | head -1))"
	guarda_la_sessione || return 2
	if [ "$SCENA" = bandiera ]; then genera_scena || return 2; fi

	log "1. gli attesi, scritti prima del giro"
	elenco

	log "2. il produttore: monta il monitor virtuale e aspetta la scena"
	# ⛔ I monitor si contano PRIMA: il nostro sara' quello che compare dopo.
	local monitor_prima
	monitor_prima=$(elenco_monitor prima)
	if [ "$monitor_prima" = GUASTO-DBUS ]; then
		ko "⛔ DisplayConfig non risponde: la sessione non e' interrogabile"
		return 2
	fi
	# ⚠ La scena «fermo» dichiara di voler misurare lo zero legittimo: li' il
	#   minimo preteso e' 0, e lo si dice invece di ottenerlo per caso.
	local minimo=1
	[ "$SCENA" = fermo ] && minimo=0
	local opzioni=(--uscita "$prefisso" --pronto "$pronto" --segnale-scena "$accesa"
	               --larghezza "$LARGHEZZA" --altezza "$ALTEZZA" --fps "$FPS"
	               --dopo-scena "$DOPO_SCENA" --scarta "$SCARTA" --durata "$DURATA"
	               --minimo-dopo-scena "$minimo" --etichetta "$ETICHETTA")
	[ "$STRADA" = dmabuf ] && opzioni+=(--dmabuf)

	"$PROG" "${opzioni[@]}" >"$QUI/produttore.txt" 2>"$QUI/produttore.log" &
	pid_prod=$!

	# ⛔ Si aspetta l'EVENTO, non un tempo: il file `pronto` lo scrive il
	#    produttore quando il flusso e' ATTIVO davvero.
	for i in $(seq 1 300); do
		[ -f "$pronto" ] && break
		if ! kill -0 $pid_prod 2>/dev/null; then break; fi
		sleep 0.1
	done
	if [ ! -f "$pronto" ]; then
		wait $pid_prod; uscita_prod=$?
		ko "⛔ il produttore non ha mai dichiarato il flusso attivo (uscita $uscita_prod)"
		sed 's/^/       /' "$QUI/produttore.log"
		return 2
	fi
	ok "flusso attivo: il monitor virtuale c'e' e la scena si puo' accendere"

	log "2-bis. su quale schermo siamo — si guarda, non si suppone"
	if ! trova_il_nostro_schermo "$monitor_prima"; then
		kill $pid_prod 2>/dev/null; wait $pid_prod 2>/dev/null
		return 2
	fi

	log "3. la scena «$SCENA», accesa DOPO il monitor e SULLO SCHERMO DICHIARATO"
	pid_scena=$(avvia_scena)
	if [ "$pid_scena" = IGNOTA ]; then
		kill $pid_prod 2>/dev/null; wait $pid_prod 2>/dev/null
		ko "⛔ '$SCENA' non e' una scena di questo banco. Sono: bandiera, tetto, fermo."
		return 2
	fi
	if [ "$pid_scena" != 0 ]; then
		sleep 1.5
		# ⛔ E NON con `kill -0`, che RIESCE sugli zombie: un figlio morto subito
		#    resta nella tabella dei processi finche' nessuno lo raccoglie, e
		#    «il pid esiste» non e' «il processo e' vivo».  Si legge lo STATO in
		#    `ps`, che dice `Z`.  Difetto di banco gia' pagato — voce 8 di
		#    `FASI.md` §00-ambiente.
		stato=$(ps -o stat= -p "$pid_scena" | tr -d ' ')
		if [ -z "$stato" ] || [ "${stato#Z}" != "$stato" ]; then
			kill $pid_prod 2>/dev/null; wait $pid_prod 2>/dev/null
			ko "⛔ la scena e' morta subito (stato '$stato'). Il registro dice:"
			sed 's/^/       /' "$QUI/scena.log"
			inf "⚠ Non e' uno zero del compositore: e' l'assenza di qualcosa da catturare."
			return 2
		fi
		ok "la scena e' viva (pid $pid_scena, stato $stato)"
	else
		ok "scena «fermo»: nessuno dipinge, e l'atteso e' uscita 3"
	fi
	echo accesa > "$accesa"

	log "4. la presa"
	# ⛔ E LA SCENA SI SORVEGLIA PER TUTTA LA PRESA, non solo al primo secondo.
	while kill -0 $pid_prod 2>/dev/null; do
		if [ "$pid_scena" != 0 ]; then
			stato=$(ps -o stat= -p "$pid_scena" | tr -d ' ')
			if [ -z "$stato" ] || [ "${stato#Z}" != "$stato" ]; then morta=si; break; fi
		fi
		sleep 0.5
	done
	if [ -n "$morta" ]; then
		kill $pid_prod 2>/dev/null; wait $pid_prod 2>/dev/null
		[ "$pid_scena" != 0 ] && kill "$pid_scena" 2>/dev/null
		ko "⛔ la scena e' morta durante la presa. Il registro dice:"
		sed 's/^/       /' "$QUI/scena.log"
		return 2
	fi
	wait $pid_prod; uscita_prod=$?
	[ "$pid_scena" != 0 ] && kill "$pid_scena" 2>/dev/null
	sleep 0.5

	sed 's/^/       /' "$QUI/produttore.log"
	cat "$QUI/produttore.txt"
	inf "il produttore e' uscito con $uscita_prod"
	if [ $uscita_prod -eq 2 ]; then
		ko "⛔ SONO FALLITO: non c'e' nessun fotogramma da giudicare"
		registra "$prefisso" "$uscita_prod" 2 "SONO FALLITO" ""
		return 2
	fi
	if [ $uscita_prod -eq 1 ]; then
		ko "⛔ l'ambiente: monitor non montato o file non scritto"
		registra "$prefisso" "$uscita_prod" 2 "AMBIENTE" ""
		return 2
	fi

	log "5. il giudizio dei pixel"
	python3 -u "$GIUDICE" --manifesto "$prefisso.json" --scena "$SCENA" \
	        --json "$prefisso-verdetto.json"
	uscita_giud=$?

	registra "$prefisso" "$uscita_prod" "$uscita_giud" \
	         "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("verdetto",""))' \
	            "$prefisso-verdetto.json")" "$prefisso-verdetto.json"

	log "6. il verdetto"
	case $uscita_giud in
	0) ok  "⭐ VERDE: un fotogramma c'e', e' quello chiesto, e contiene la scena" ;;
	1) ko  "ROSSO: il fotogramma c'e' e qualcosa non torna (le marche qui sopra)" ;;
	3) inf "⚠ NIENTE DA GIUDICARE: zero fotogrammi, o strada DMA-BUF. Non e' un rosso." ;;
	2) ko  "⛔ SONO FALLITO: il giudice non e' certificato, o i file non si leggono" ;;
	esac
	inf "gli esiti sono in $ESITI"
	return $uscita_giud
}

# ---------------------------------------------------------------------------
#  Gli esiti — una riga per giro, con l'ora e la SCENA
# ---------------------------------------------------------------------------
registra()
{
	local prefisso=$1 up=$2 ug=$3 verdetto=$4 vfile=$5
	python3 - "$prefisso" "$up" "$ug" "$verdetto" "$vfile" "$SCENA" "$ETICHETTA" \
	         "$LARGHEZZA" "$ALTEZZA" "$STRADA" "$ESITI" \
	         "${SCHERMO:-ignoto}" "${PRODOTTO_SCHERMO:-ignoto}" "${STATO_SESSIONE:-non guardato}" <<'FINE'
import json, os, sys, time
(prefisso, up, ug, verdetto, vfile, scena, etichetta,
 larghezza, altezza, strada, esiti, schermo, prodotto, stato_sessione) = sys.argv[1:15]
riga = {
    "banco": "F2.2 — la cattura",
    "quando_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "macchina": "NIC-OS (192.168.0.2), sessione GNOME headless",
    "scena": scena,
    "etichetta": etichetta,
    "chiesto": {"larghezza": int(larghezza), "altezza": int(altezza), "strada": strada},
    "uscita_produttore": int(up),
    "uscita_giudice": int(ug),
    "verdetto": verdetto,
    "prefisso": prefisso,
    # ⛔ Il monitor si dichiara PER NOME e col nome del PRODOTTO: sul server ce
    #    ne sono due, entrambi 1920×1080@60, e li distingue solo quello.
    "schermo": {"connettore": schermo, "prodotto": prodotto},
    # ⛔ E lo stato della sessione sta nella riga: senza, uno zero non ha imputato.
    "stato_sessione": stato_sessione,
}
man = prefisso + ".json"
if os.path.exists(man):
    m = json.load(open(man))
    riga["negoziato"] = m.get("negoziato")
    riga["buffer"] = m.get("buffer")
    riga["fotogrammi"] = m.get("fotogrammi")
    riga["esito_produttore"] = m.get("esito")
    # ⛔ Le tre cose che F2.3 chiede DICHIARATE viaggiano nella riga di esito,
    #    non solo nel manifesto: e' la riga che il coordinatore leggera'.
    riga["consegna_a_F2_3"] = m.get("consegna_a_F2_3")
    for q in ("primo", "regime"):
        if m.get(q):
            riga[q] = {k: m[q][k] for k in ("byte", "stride", "danno", "seq",
                                            "tipo_dichiarato")}
if vfile and os.path.exists(vfile):
    v = json.load(open(vfile))
    riga["controllo_positivo_passato"] = v.get("controllo_positivo", {}).get("passato")
    riga["danno_parziale_ma_intero"] = v.get("danno_parziale_ma_intero")
    reg = v.get("fotogrammi", {}).get("regime", {}).get("misure", {})
    riga["profondita_misurata"] = reg.get("profondita")
    riga["profondita_sfumatura"] = reg.get("profondita_sfumatura")
    # ⛔ Rossi e avvisi in due campi diversi: metterli insieme sarebbe due esiti
    #    sotto la stessa etichetta (forma E2), e nel registro non si distingue
    #    piu' un banco che ha visto un difetto da uno che ha visto uno sfondo.
    riga["rilievi"] = [r["marca"] for f in v.get("fotogrammi", {}).values()
                       for r in f.get("rilievi", []) if r.get("rosso", True)]
    riga["avvisi"] = [r["marca"] for f in v.get("fotogrammi", {}).values()
                      for r in f.get("rilievi", []) if not r.get("rosso", True)]
    riga["rilievi"] += [r["marca"]
                        for r in v.get("confronto_primo_regime", {}).get("rilievi", [])]
with open(esiti, "a") as f:
    f.write(json.dumps(riga, ensure_ascii=False) + "\n")
print("    --  registrato in", esiti)
FINE
}

# ---------------------------------------------------------------------------
case "${1:-misura}" in
compila) compila ;;
scena)   genera_scena ;;
elenco)  elenco ;;
misura)  misura ;;
*)
	echo "uso: $0 [compila|scena|misura|elenco]" >&2
	echo "     SCENA=bandiera|tetto|fermo  STRADA=memoria|dmabuf  LARGHEZZA= ALTEZZA=" >&2
	exit 2
	;;
esac
uscita=$?

# ===========================================================================
# ⛔ IL CONTROLLO POSITIVO IN CODA A OGNI ESECUZIONE — come la diagnosi di
#    `lsquic` in B2.  «Questo strumento sa trovare qualcosa che c'e' di sicuro?»
#    (`LEZIONI.md` §1.9, seconda regola.)  Uno strumento che non ha mai trovato
#    niente non e' pulito: e' non certificato.
# ===========================================================================
printf '\n\033[1m== controllo positivo in coda ==\033[0m\n'
if [ -r "$GIUDICE" ]; then
	python3 -u "$GIUDICE" --solo-controllo-positivo
	cp_esito=$?
	if [ $cp_esito -ne 0 ]; then
		ko "⛔ IL GIUDICE NON E' CERTIFICATO (uscita $cp_esito): il verde qui sopra non vale."
		exit 2
	fi
	ok "il giudice trova la bandiera, chiama nero il nero, e NON chiama nero il grigio"
else
	ko "⛔ il giudice non si legge: il controllo positivo non si e' potuto fare"
	exit 2
fi

# E il controllo positivo dell'ALTRO strumento, quello che questo banco non e':
# il misuratore della fase 0 esiste ed e' eseguibile?  Se un giorno sparisse,
# questo banco resterebbe verde e il progetto perderebbe il proprio controllo
# positivo storico senza che nessuno se ne accorgesse.
STORICO=/media/REMOTIX/tmp/banco-compositori/misura-cattura
if [ -x "$STORICO" ]; then
	ok "il controllo positivo STORICO e' al suo posto: $STORICO (36 ± 2 fps [M] 9 ago)"
else
	ko "⚠ manca $STORICO: il controllo positivo storico del progetto non e' eseguibile"
fi

exit $uscita
