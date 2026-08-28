#!/bin/bash
#
# Prova della fase 8: l'audio in uscita e gli appunti.
#
#   bash /media/REMOTIX/src/remotix-c/prove/fase8.sh
#
# ⚠ QUEL CHE QUESTO BANCO PUO' DIRE, E QUEL CHE NON PUO'.
#
#   Puo' dire che il sink virtuale nasce nella sessione, che il canale si
#   negozia, che il silenzio NON viene spedito, che i campioni partono e che il
#   client li RISCONTRA — cioe' che arrivano dall'altra parte.  E dal 5 agosto
#   sa dire anche QUALE ONDA IL CLIENT SUONA (sezione 4-bis), che e' la cosa che
#   non sapeva dire quando l'audio usciva come rumore.  Per gli appunti puo'
#   dire tutto: il testo e le immagini si copiano nei due versi, e il risultato
#   si legge dall'altra parte con gli strumenti di quel lato.
#
#   Non puo' dire «si sente bene» su mstsc e su RDM: quella resta la prova
#   dell'orecchio (§9 di REFERENCE.md, la regola dei tre client).  Quel che puo'
#   fare e' dire che l'onda ricevuta dal client di prova e' la stessa che la
#   sessione ha suonato — e un difetto che passi quel controllo non e' piu' un
#   difetto di forma d'onda.
#
# ⚠ IL CONTENITORE HA BISOGNO DI UN IMPIANTO AUDIO, e non ce l'ha da solo:
#   `audio-cnt.sh` accende pipewire, wireplumber e pipewire-pulse dentro la
#   chroot e crea un sink finto «uscita».  Senza, il client di FreeRDP non
#   carica alcun backend e non riscontra niente — e il banco accuserebbe il
#   server di un difetto del banco.
set -u

BASE=/media/REMOTIX
BIN_LOCALE="$BASE/src/remotix-c/build/src/remotix"
PORTA=3389
BANCO=/srv/remotix/tmp/banco-b
BANCO_FUORI=/media/REMOTIX/tmp/banco-b
DISPLAY_CLI=:110
MISURA=${MISURA:-1280x800}

# Da dove si comanda la macchina di runtime: dal 6 agosto 2026 e' il server
# stesso (§6.2 di SPECIFICA.md).  `RUNTIME=vm` riporta i banchi sulla VM.
. "$(dirname "$0")/runtime.sh"
cnt() { bash "$BASE/enter.sh" "$@"; }

titolo() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()     { printf '    \033[1;32mOK\033[0m    %s\n' "$*"; }
ko()     { printf '    \033[1;31mNO\033[0m    %s\n' "$*"; GUASTI=$((GUASTI+1)); }
inf()    { printf '    --    %s\n' "$*"; }
GUASTI=0

[ -x "$BIN_LOCALE" ] || { echo "manca $BIN_LOCALE: costruiscilo prima"; exit 1; }
mkdir -p "$BANCO_FUORI"
bash "$BASE/enter.sh" true || exit 1

# ===========================================================================
# Gli script che girano dentro i due ambienti.
# ===========================================================================
cat > "$BANCO_FUORI/fase8-audio.sh" <<'AUDIO'
#!/bin/bash
# L'impianto audio finto del contenitore.  Senza, il client non suona.
set -u
export XDG_RUNTIME_DIR=/tmp/rt
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
if ! pgrep -x pipewire >/dev/null; then
    setsid nohup pipewire       >/tmp/pw.log 2>&1 </dev/null &
    sleep 1
    setsid nohup wireplumber    >/tmp/wp.log 2>&1 </dev/null &
    setsid nohup pipewire-pulse >/tmp/pp.log 2>&1 </dev/null &
    sleep 2
fi
wpctl status 2>/dev/null | grep -q ' USCITA' || \
    pw-cli create-node adapter '{ factory.name=support.null-audio-sink node.name=uscita node.description=USCITA media.class=Audio/Sink object.linger=true audio.position=[FL,FR] }' >/dev/null 2>&1
sleep 1
wpctl status 2>/dev/null | grep -q ' USCITA' && echo "   impianto audio del contenitore pronto" \
                                             || echo "   impianto audio NON pronto"
AUDIO

cat > "$BANCO_FUORI/fase8-client.sh" <<CLIENT
#!/bin/bash
set -u
export XDG_RUNTIME_DIR=/tmp/rt
pkill -x xfreerdp3 2>/dev/null
pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null; sleep 1
Xvfb $DISPLAY_CLI -screen 0 2400x1600x24 -nolisten tcp >/dev/null 2>&1 &
sleep 2
cd $BANCO || exit 1
rm -f fase8-client.log
setsid nohup env DISPLAY=$DISPLAY_CLI XDG_RUNTIME_DIR=/tmp/rt xfreerdp3 \\
    /v:127.0.0.1:$PORTA /gfx:AVC420 /cert:ignore /sec:tls /u:prova /p:prova \\
    /size:$MISURA /sound /log-level:INFO >fase8-client.log 2>&1 </dev/null &
sleep 8
pgrep -x xfreerdp3 >/dev/null && echo "   client collegato" || echo "   client NON partito"
CLIENT

cat > "$BANCO_FUORI/fase8-copia.sh" <<'COPIA'
#!/bin/bash
# Mette qualcosa negli appunti del CLIENT.  $1 = tipo, $2 = file
#
# ⚠ `xclip` RESTA IN VITA a tenere la selezione: va staccato, o la sessione che
#   lo ha avviato non si chiude piu' — la stessa regola di fase 5 sul pilotare
#   i due ambienti, qui applicata agli appunti.
set -u
pkill -x xclip 2>/dev/null
setsid nohup env DISPLAY=:110 xclip -selection clipboard -t "$1" -i "$2" >/dev/null 2>&1 &
sleep 2
echo "   il client ha copiato ($1)"
COPIA

cat > "$BANCO_FUORI/fase8-chiudi.sh" <<'CHIUDI'
#!/bin/bash
set -u
pkill -x xfreerdp3 2>/dev/null
pkill -f '^Xvfb :110' 2>/dev/null
sleep 1
echo "   banco del contenitore sgombrato"
CHIUDI


# ---------------------------------------------------------------------------
# I programmini di lettura delle immagini stanno in FILE, non in heredoc
# annidati: uno heredoc dentro un altro, spedito per ssh dentro uno script,
# misura le regole di citazione della shell invece che REMOTIX.
# ---------------------------------------------------------------------------
GENERA=/tmp/fase8-genera.py
LEGGI_BMP=/tmp/fase8-bmp.py
LEGGI_PNG=/tmp/fase8-png.py
ONDA=/tmp/fase8-onda.py
SALTI=/tmp/fase8-salti.py

# ---------------------------------------------------------------------------
# ⛔ LA REGISTRAZIONE DI QUEL CHE IL CLIENT SUONA.
#
#    E' il controllo che mancava al banco del 5 agosto, ed e' costato la
#    questione n.10: sapeva dire «i campioni partono» e «il client li
#    riscontra», ma NON «quel che esce dagli altoparlanti e' l'onda che e'
#    entrata».  Fra le due cose stava il DSP di FreeRDP, che ribaltava il segno
#    di ogni campione (R24 di REFERENCE.md) — e nessun contatore poteva vederlo.
#
#    Si registra il monitor del sink finto del contenitore, cioe' esattamente
#    quel che il client sta mandando agli altoparlanti.
# ---------------------------------------------------------------------------
cat > "$BANCO_FUORI/fase8-ascolta.sh" <<'ASCOLTA'
#!/bin/bash
# Registra il monitor del sink «uscita».  $1 = secondi, $2 = file
set -u
export XDG_RUNTIME_DIR=/tmp/rt
rm -f "$2"
timeout "$1" parec -d uscita.monitor --rate=44100 --channels=2 --format=s16le --raw > "$2" 2>/dev/null
ASCOLTA

cat > "$BANCO_FUORI/fase8-tono.py" <<'PY'
import math, struct, wave
w = wave.open("/tmp/tono.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(44100)
w.writeframes(b"".join(struct.pack("<hh", v, v) for v in
    (int(3000 * math.sin(2 * math.pi * 440 * i / 44100)) for i in range(88200))))
w.close()
PY

cat > "$BANCO_FUORI/fase8-salti.py" <<'PY'
import struct, sys, os
# Cerca le DISCONTINUITA' in una registrazione di un seno noto.
#
# Un seno di 440 Hz ad ampiezza A campionato a 44100 non puo' saltare piu' di
# A*2*pi*440/44100 fra due campioni consecutivi: ~188 per A=3000.  Tutto quel
# che salta di piu' e' uno strappo — un blocco perso, un blocco doppio, o una
# giuntura fra due invii che non si allacciano.  Nessun contatore di fotogrammi
# puo' vederlo; l'orecchio lo sente come scoppiettio.
p = sys.argv[1]
if not os.path.exists(p) or os.path.getsize(p) < 4:
    print("VUOTO"); raise SystemExit
d = open(p, "rb").read()
v = struct.unpack("<%dh" % (len(d) // 2), d)
sx = v[0::2]
forti = [i for i, x in enumerate(sx) if abs(x) > 500]
if not forti:
    print("SILENZIO"); raise SystemExit
a, b = forti[0], forti[-1] + 1
t = sx[a:b]
picco = max(abs(x) for x in t)
limite = int(picco * 2 * 3.14159 * 440 / 44100 * 1.5)  # meta' di margine
salti = [i for i in range(1, len(t)) if abs(t[i] - t[i - 1]) > limite]
# I buchi: tratti di silenzio DENTRO il suono, cioe' quel che si sente come
# interruzione invece che come scoppiettio.
buchi, corrente = [], 0
for x in t:
    if abs(x) < 50:
        corrente += 1
    else:
        if corrente > 441:  # oltre 10 ms
            buchi.append(corrente)
        corrente = 0
if corrente > 441:
    buchi.append(corrente)
print("campioni %d (%.1f s)  picco %d  limite di salto %d" % (len(t), len(t) / 44100.0, picco, limite))
print("STRAPPI %d  (%.1f al secondo)" % (len(salti), len(salti) / (len(t) / 44100.0)))
if salti:
    print("  i primi, in millisecondi dall'inizio del suono: %s" %
          ", ".join("%.0f" % (i / 44.1) for i in salti[:12]))
    print("  distanza fra strappi consecutivi, in ms: %s" %
          ", ".join("%.0f" % ((salti[i] - salti[i - 1]) / 44.1) for i in range(1, min(13, len(salti)))))
print("BUCHI  %d  (durate in ms: %s)" % (len(buchi), ", ".join("%.0f" % (n / 44.1) for n in buchi[:12])))
PY

cat > "$BANCO_FUORI/fase8-onda.py" <<'PY'
import struct, sys, os
p = sys.argv[1]
if not os.path.exists(p) or os.path.getsize(p) < 4:
    print("VUOTO"); raise SystemExit
d = open(p, "rb").read()
v = struct.unpack("<%dh" % (len(d) // 2), d)
sx = v[0::2]
forti = [i for i, x in enumerate(sx) if abs(x) > 500]
if not forti:
    print("SILENZIO"); raise SystemExit
t = sx[forti[0]:forti[-1] + 1]
picco = max(abs(x) for x in t)
rms = (sum(x * x for x in t) / len(t)) ** 0.5
# La percentuale di campioni vicini al fondo scala e' il discriminante che
# nessun contatore dava: un seno di ampiezza 3000 non ne ha nemmeno uno, un
# segnale col segno ribaltato li ha TUTTI.
fondo = sum(1 for x in t if abs(x) > 10000)
print("ONDA %d %d %d" % (picco, rms, round(100.0 * fondo / len(t))))
PY

cat > "$BANCO_FUORI/fase8-genera.py" <<'PY'
import struct, zlib
larg, alt = 8, 8
righe = b"".join(
    b"\x00" + bytes([(x * 30) % 256, (y * 30) % 256, 128, 255][k]
                    for x in range(larg) for k in range(4))
    for y in range(alt))
def pezzo(tipo, dati):
    return struct.pack(">I", len(dati)) + tipo + dati + struct.pack(">I", zlib.crc32(tipo + dati))
png = (b"\x89PNG\r\n\x1a\n"
       + pezzo(b"IHDR", struct.pack(">IIBBBBB", larg, alt, 8, 6, 0, 0, 0))
       + pezzo(b"IDAT", zlib.compress(righe))
       + pezzo(b"IEND", b""))
open("/tmp/prova.png", "wb").write(png)
PY

cat > "$BANCO_FUORI/fase8-bmp.py" <<'PY'
import struct
d = open("/tmp/dal-server.bmp", "rb").read()
if len(d) < 54 or d[:2] != b"BM":
    print("NO")
else:
    off = struct.unpack("<I", d[10:14])[0]
    larg = struct.unpack("<i", d[18:22])[0]
    alt = struct.unpack("<i", d[22:26])[0]
    p = d[off:off + 3]
    print("SI %d %d %d %d %d" % (larg, alt, p[0], p[1], p[2]))
PY

cat > "$BANCO_FUORI/fase8-png.py" <<'PY'
import gi
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf
try:
    p = GdkPixbuf.Pixbuf.new_from_file("/tmp/dal-client.png")
    px = p.get_pixels()
    print("SI %d %d %d %d %d" % (p.get_width(), p.get_height(), px[0], px[1], px[2]))
except Exception:
    print("NO")
PY

copia "$BANCO_FUORI/fase8-genera.py" /tmp >/dev/null 2>&1
copia "$BANCO_FUORI/fase8-png.py" /tmp >/dev/null 2>&1
# ⛔ NIENTE `>/dev/null` SU `enter.sh`, MAI.
#
#    Dentro c'e' un `sudo` che puo' chiedere la parola d'ordine, e la chiede
#    sullo standard output: dirottandolo, la richiesta non arriva a chi
#    dovrebbe risponderle e il banco resta fermo per sempre, senza scrivere una
#    riga.  Costato due esecuzioni a vuoto, il 5 agosto 2026.
cnt "cp $BANCO/fase8-bmp.py $LEGGI_BMP; cp $BANCO/fase8-onda.py $ONDA; cp $BANCO/fase8-salti.py $SALTI"

# ===========================================================================
titolo "0. Il banco, certificato PRIMA della misura"
# ===========================================================================
# ⛔ E' la lezione della fase 0, applicata all'audio: se non si sa che
#    l'impianto del contenitore suona pulito, un suono distorto non distingue
#    un difetto del server da uno del banco.  Qui e' costato una mezza giornata
#    di sospetti sbagliati, il 5 agosto.
cnt "bash $BANCO/fase8-audio.sh"

# ⛔ E IL REGISTRATORE VA CERTIFICATO PRIMA DI CREDERGLI, per la stessa ragione:
#    un'onda storta letta da un registratore storto non distingue niente.  Si
#    suona il tono DENTRO il contenitore e lo si riregistra dal monitor: se
#    tornano picco 3000 e rms 2121, la catena parec → sink → monitor e' pulita e
#    quel che dira' del client si puo' prendere per buono.
cnt "python3 $BANCO/fase8-tono.py; echo '   tono di prova nel contenitore'"
cnt "export XDG_RUNTIME_DIR=/tmp/rt; setsid nohup bash $BANCO/fase8-ascolta.sh 5 /tmp/banco.pcm >/dev/null 2>&1 </dev/null & sleep 1; paplay /tmp/tono.wav; sleep 2; echo '   tono suonato e registrato nel contenitore'"
ESITO=$(cnt "python3 $ONDA /tmp/banco.pcm")
set -- $ESITO
if [ "${1:-VUOTO}" = "ONDA" ] && [ "${2:-0}" -ge 2900 ] && [ "${2:-0}" -le 3100 ] \
   && [ "${3:-0}" -ge 1900 ] && [ "${3:-0}" -le 2400 ]; then
    ok "il registratore del banco e' pulito: picco $2, rms $3 (attesi 3000 e 2121)"
else
    ko "il registratore del banco non torna ($ESITO): quel che dira' del client non vale"
fi

vm "python3 - <<'PY'
import math, struct, wave
w = wave.open('/tmp/tono.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(44100)
w.writeframes(b''.join(struct.pack('<hh', v, v) for v in
    (int(3000*math.sin(2*math.pi*440*i/44100)) for i in range(88200))))
w.close(); print('   tono di prova nella VM: 440 Hz, ampiezza 3000, due secondi')
PY"

# ===========================================================================
titolo "1. Il sink virtuale nasce nella sessione"
# ===========================================================================
vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
copia "$BIN_LOCALE" >/dev/null || exit 1
vm "rm -f /tmp/copia.pcm; printf 'REMOTIX_OPZIONI=--registro diagnostica --senza-autenticazione\nREMOTIX_SUONO_COPIA=/tmp/copia.pcm\n' | sudo tee /etc/default/remotix >/dev/null; rm -f ~/remotix.log; sudo systemctl restart remotix.service; sleep 3; systemctl is-active --quiet remotix.service && echo VIVO" | grep -q VIVO \
    || { echo "REMOTIX non e' partito nella VM"; exit 1; }

cnt "bash $BANCO/fase8-client.sh"

REG=$(vm "cat ~/remotix.log")
if printf '%s\n' "$REG" | grep -qF "sink audio «remotix» montato"; then
    ok "il sink virtuale e' stato creato: $(printf '%s\n' "$REG" | grep -F 'sink audio' | head -1 | sed 's/.*nodo/nodo/')"
else
    ko "nessun sink: nella sessione senza monitor non c'e' niente da catturare (§7.5)"
fi

SINK=$(vm "wpctl status | grep -c ' REMOTIX '")
if [ "${SINK:-0}" -ge 1 ]; then
    ok "la sessione lo vede come proprio dispositivo di uscita"
else
    ko "il sink non compare nel grafo della sessione"
fi

# ===========================================================================
titolo "2. Il canale audio si negozia, e sul canale DINAMICO"
# ===========================================================================
if printf '%s\n' "$REG" | grep -qF "audio negoziato:"; then
    ok "$(printf '%s\n' "$REG" | grep -F 'audio negoziato:' | head -1 | sed 's/^[^ ]* *[A-Z]* *//')"
else
    ko "il formato audio non e' stato negoziato: il client non ha risposto, o non ha formati in comune"
fi

# Quel che il client dichiara: NON risponde alla questione n.8 (si veda R21),
# ma e' il dato da avere sotto mano quando l'audio non si sente.
if printf '%s\n' "$REG" | grep -qF "formati audio del client:"; then
    inf "$(printf '%s\n' "$REG" | grep -F 'formati audio del client:' | head -1 | sed 's/^[^ ]* *[A-Z]* *//')"
fi

if printf '%s\n' "$REG" | grep -qF "formato audio negoziato con PipeWire: S16"; then
    ok "la cattura e' in S16, cioe' nel formato in cui la si legge"
else
    ko "PipeWire non ha dato S16: i campioni verrebbero letti male e l'audio sarebbe rumore"
fi

# ===========================================================================
titolo "3. ⛔ Il silenzio NON si spedisce"
# ===========================================================================
# Il monitor di un sink virtuale non tace mai: senza questo controllo REMOTIX
# manderebbe 1,4 Mbit/s di zeri per tutta la sessione — il 14% del budget.
inf "dieci secondi di desktop muto"
sleep 10
REG=$(vm "cat ~/remotix.log")
MUTI=$(printf '%s\n' "$REG" | grep -F 'audio:' | tail -1 | grep -oE '[0-9]+ di silenzio' | grep -oE '^[0-9]+')
SPED=$(printf '%s\n' "$REG" | grep -F 'audio:' | tail -1 | grep -oE '^[^ ]* *[A-Z]* *audio: [0-9]+' | grep -oE '[0-9]+$')

if [ "${MUTI:-0}" -ge 100000 ]; then
    ok "il silenzio e' stato riconosciuto e taciuto: $MUTI fotogrammi"
else
    ko "solo ${MUTI:-0} fotogrammi di silenzio taciuti: il silenzio sta partendo sul filo"
fi
# Il tetto tiene conto della CODA DI SILENZIO: mezzo secondo di zeri — 22 050
# fotogrammi a 44,1 kHz — si spedisce apposta dopo l'ultimo suono, perche'
# tacere di colpo costa uno strappo alla ripresa (R25).  Quel che il controllo
# deve escludere e' il silenzio spedito PER SEMPRE, che sono 220 000 fotogrammi
# ogni cinque secondi.
if [ "${SPED:-0}" -le 30000 ]; then
    ok "a desktop muto sono partiti solo $SPED fotogrammi (la coda del suono e mezzo secondo di silenzio, non il silenzio)"
else
    ko "a desktop muto sono partiti $SPED fotogrammi: qualcosa spedisce zeri"
fi

# ===========================================================================
titolo "4. Il suono parte, e il client lo RISCONTRA"
# ===========================================================================
# Si registra quel che il client suona MENTRE la sessione suona: la stessa
# passata serve alla sezione 4 (i contatori) e alla 4-bis (l'onda).
cnt "export XDG_RUNTIME_DIR=/tmp/rt; setsid nohup bash $BANCO/fase8-ascolta.sh 12 /tmp/ricevuto.pcm >/dev/null 2>&1 </dev/null & sleep 1; echo '   registrazione di quel che il client suona: avviata'"
vm "for i in 1 2 3; do pw-play /tmp/tono.wav; done; echo '   tono suonato tre volte (sei secondi)'"
sleep 6
REG=$(vm "cat ~/remotix.log")
SPED2=$(printf '%s\n' "$REG" | grep -F 'audio:' | tail -1 | grep -oE 'audio: [0-9]+' | grep -oE '[0-9]+')
RISC=$(printf '%s\n' "$REG" | grep -F 'audio:' | tail -1 | grep -oE '[0-9]+ blocchi riscontrati' | grep -oE '^[0-9]+')
BUTT=$(printf '%s\n' "$REG" | grep -F 'audio:' | tail -1 | grep -oE '[0-9]+ buttati' | grep -oE '^[0-9]+')

# Sei secondi di tono a 44100 sono circa 264 000 fotogrammi: se ne sono partiti
# molti meno, il suono si e' fermato per strada.
if [ "${SPED2:-0}" -ge 200000 ]; then
    ok "i fotogrammi di suono sono partiti: $SPED2 in tutto"
else
    ko "solo ${SPED2:-0} fotogrammi spediti: il suono non arriva al canale"
fi

# ⛔ IL CONTROLLO CHE PARLA DELL'ALTRO CAPO.  «Spediti» conta quel che abbiamo
#    scritto noi, e un canale che il client ignora produce lo stesso numero di
#    uno che funziona.  I riscontri li manda lui.
if [ "${RISC:-0}" -ge 20 ]; then
    ok "il client ha riscontrato $RISC blocchi: l'audio arriva dall'altra parte"
else
    ko "il client ha riscontrato ${RISC:-0} blocchi: i campioni non arrivano, o non li elabora"
fi

if [ "${BUTT:-0}" -eq 0 ]; then
    ok "nessun campione buttato: la coda regge il ritmo del ciclo"
else
    ko "$BUTT fotogrammi buttati: il ciclo non svuota la coda abbastanza in fretta"
fi

# ===========================================================================
titolo "4-bis. ⛔ Quel che il client SUONA e' l'onda che abbiamo mandato"
# ===========================================================================
# LA DOMANDA CHE HA TENUTO APERTA LA QUESTIONE n.10 PER UN GIORNO.
#
# «Spediti» e «riscontrati» dicono che i byte arrivano; non dicono che siano i
# byte giusti.  Il DSP di FreeRDP li cambiava DOPO che li avevamo consegnati e
# PRIMA che finissero nel PDU — un punto che il banco non guardava e che il
# registro non poteva raccontare (R24 di REFERENCE.md).
#
# Il discriminante e' la percentuale di campioni vicini al fondo scala: un seno
# di ampiezza 3000 non ne ha nemmeno uno; lo stesso seno col segno ribaltato li
# ha tutti.
ESITO=$(cnt "python3 $ONDA /tmp/ricevuto.pcm")
set -- $ESITO
if [ "${1:-VUOTO}" != "ONDA" ]; then
    ko "dal client non e' uscito suono ($ESITO): non c'e' niente da giudicare"
elif [ "${4:-100}" -eq 0 ] && [ "${2:-0}" -le 8000 ]; then
    ok "il client suona l'onda giusta: picco $2, rms $3, nessun campione a fondo scala"
else
    ko "il client suona rumore: picco $2, rms $3, ${4}% dei campioni a fondo scala — il segno dei campioni si e' ribaltato per strada (R24)"
fi

# ⛔ E L'ONDA GIUSTA NON BASTA: DEVE ANCHE ESSERE CONTINUA.
#
# Un seno a 440 Hz non puo' saltare piu' di ~190 per campione: ogni salto piu'
# grande e' un blocco perso o una giuntura che non si allaccia, cioe' quel che
# si sente come scoppiettio.  Con i blocchi da 5 ms che il client buttava
# (R25) erano 168 in sei secondi; sani sono meno di dieci, e due di quelli
# stanno nella sorgente — `pw-play` finisce a meta' onda.
STRAPPI=$(cnt "python3 $SALTI /tmp/ricevuto.pcm" | grep -oE 'STRAPPI [0-9]+' | grep -oE '[0-9]+')
if [ -n "${STRAPPI:-}" ] && [ "$STRAPPI" -le 12 ]; then
    ok "e la suona senza scoppiettare: $STRAPPI strappi in sei secondi (le giunture della sorgente)"
else
    ko "il client suona a scatti: ${STRAPPI:-?} strappi — il ritmo dei blocchi non regge (R25)"
fi

# ===========================================================================
titolo "5. ⛔ Quel che consegniamo al canale e' pulito"
# ===========================================================================
# La domanda che il banco deve saper distinguere quando l'audio si sente male:
# «lo mandiamo storto noi, o si storce dopo?».  Qui si guarda l'onda.
vm "python3 - <<'PY'
import struct, os
p='/tmp/copia.pcm'
if not os.path.exists(p) or os.path.getsize(p) == 0:
    print('   VUOTO'); raise SystemExit
d=open(p,'rb').read(); v=struct.unpack('<%dh'%(len(d)//2), d); sx=v[0::2]
forti=[i for i,x in enumerate(sx) if abs(x)>500]
if not forti:
    print('   SILENZIO'); raise SystemExit
t=sx[forti[0]:forti[-1]]
picco=max(abs(x) for x in t); rms=(sum(x*x for x in t)/len(t))**0.5
print('   picco %d rms %d' % (picco, rms))
PY" > /tmp/fase8-onda.txt 2>&1
ONDA=$(grep -oE 'picco [0-9]+ rms [0-9]+' /tmp/fase8-onda.txt)
PICCO=$(printf '%s' "$ONDA" | grep -oE 'picco [0-9]+' | grep -oE '[0-9]+')
RMSV=$(printf '%s' "$ONDA" | grep -oE 'rms [0-9]+' | grep -oE '[0-9]+')

# Il tono e' un seno di ampiezza 3000: rms atteso 2121, cioe' il 71% del picco.
# Un'onda distorta o satura avrebbe rms vicino al picco.
if [ -n "${PICCO:-}" ] && [ "$PICCO" -ge 2900 ] && [ "$PICCO" -le 3100 ] \
   && [ -n "${RMSV:-}" ] && [ "$RMSV" -ge 1900 ] && [ "$RMSV" -le 2300 ]; then
    ok "l'onda consegnata al canale e' quella suonata: picco $PICCO, rms $RMSV (attesi 3000 e 2121)"
else
    ko "l'onda consegnata al canale non torna: picco ${PICCO:-?}, rms ${RMSV:-?} (attesi 3000 e 2121)"
fi

# ===========================================================================
titolo "6. Gli appunti: il testo, nei due versi"
# ===========================================================================
REG=$(vm "cat ~/remotix.log")
if printf '%s\n' "$REG" | grep -qF "appunti collegati alla sessione"; then
    ok "il canale degli appunti si e' aperto"
else
    ko "il canale degli appunti non si e' aperto: niente copia-incolla"
fi

# --- la sessione copia, il client incolla ---------------------------------
vm "pkill -x wl-copy 2>/dev/null; printf 'REMOTIX prova appunti' > /tmp/da-copiare.txt; setsid nohup env WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 wl-copy < /tmp/da-copiare.txt >/dev/null 2>&1 & sleep 3; echo '   la sessione ha copiato'"
sleep 2
LETTO=$(cnt "DISPLAY=$DISPLAY_CLI timeout 10 xclip -selection clipboard -o 2>/dev/null" | tr -d '\r')
if printf '%s' "$LETTO" | grep -qF "REMOTIX prova appunti"; then
    ok "il client legge quel che la sessione ha copiato: «$LETTO»"
else
    ko "il client non legge il testo della sessione (ha letto: «$LETTO»)"
fi

# --- il client copia, la sessione incolla ---------------------------------
cnt "printf 'prova dal client' > /tmp/dal-client.txt; echo '   testo pronto nel client'"
cnt "bash $BANCO/fase8-copia.sh UTF8_STRING /tmp/dal-client.txt"
sleep 2
LETTO=$(vm "env WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 timeout 10 wl-paste 2>/dev/null" | tr -d '\r')
if printf '%s' "$LETTO" | grep -qF "prova dal client"; then
    ok "la sessione legge quel che il client ha copiato: «$LETTO»"
else
    ko "la sessione non legge il testo del client (ha letto: «$LETTO»)"
fi

# ===========================================================================
titolo "7. Gli appunti: un'immagine, andata e ritorno"
# ===========================================================================
# ⛔ LA SEZIONE CHE MISURA LA CONVERSIONE, e serve tutta.
#
#    I client RDP chiedono le immagini in CF_DIB e basta — quello di FreeRDP
#    mappa perfino image/png su CF_DIB — mentre le applicazioni di GNOME
#    copiano in PNG.  Qui si guarda che la conversione conservi misura,
#    ORIENTAMENTO e colori: un BMP si scrive dal basso verso l'alto, e chi lo
#    dimentica consegna immagini capovolte senza che nulla dia errore.
vm "python3 $GENERA > /dev/null; echo '   PNG 8x8 di prova nella sessione'"
vm "pkill -x wl-copy 2>/dev/null; setsid nohup env WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 wl-copy --type image/png < /tmp/prova.png >/dev/null 2>&1 & sleep 3; echo '   la sessione ha copiato il PNG'"
sleep 2

ESITO=$(cnt "DISPLAY=$DISPLAY_CLI timeout 10 xclip -selection clipboard -t image/bmp -o > /tmp/dal-server.bmp 2>/dev/null; python3 $LEGGI_BMP")
set -- $ESITO
if [ "${1:-NO}" = "SI" ] && [ "${2:-0}" = "8" ] && [ "${3:-0}" = "8" ]; then
    ok "il client ha ricevuto un BMP 8x8 dal PNG della sessione"
    # La prima riga del file BMP e' l'ULTIMA dell'immagine, dove il verde vale
    # 7x30 = 210.  Se esce 0 l'immagine e' capovolta; se rosso e blu sono
    # scambiati, e' l'ordine dei canali.
    if [ "${4:-0}" = "128" ] && [ "${5:-0}" = "210" ] && [ "${6:-0}" = "0" ]; then
        ok "colori e orientamento sono giusti: BGR 128,210,0 in basso a sinistra"
    else
        ko "il pixel in basso a sinistra e' BGR ${4:-?},${5:-?},${6:-?} invece di 128,210,0"
    fi
else
    ko "il client non ha ricevuto un BMP valido dalla sessione"
fi

cnt "bash $BANCO/fase8-copia.sh image/bmp /tmp/dal-server.bmp"
sleep 2
ESITO=$(vm "env WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 timeout 10 wl-paste --type image/png > /tmp/dal-client.png 2>/dev/null; python3 $LEGGI_PNG")
set -- $ESITO
if [ "${1:-NO}" = "SI" ] && [ "${2:-0}" = "8" ] && [ "${3:-0}" = "8" ]; then
    ok "la sessione ha ricevuto un PNG 8x8 dal BMP del client"
    if [ "${4:-0}" = "0" ] && [ "${5:-0}" = "0" ] && [ "${6:-0}" = "128" ]; then
        ok "e il primo pixel e' tornato quello di partenza: RGB 0,0,128"
    else
        ko "il primo pixel e' RGB ${4:-?},${5:-?},${6:-?} invece di 0,0,128"
    fi
else
    ko "la sessione non ha ricevuto un PNG valido dal client"
fi

vm "pkill -x wl-copy 2>/dev/null; echo '   appunti della sessione lasciati liberi'"
cnt "pkill -x xclip 2>/dev/null; echo '   appunti del client lasciati liberi'"

# ===========================================================================
titolo "8. Il congedo: la cattura si spegne con la connessione"
# ===========================================================================
cnt "bash $BANCO/fase8-chiudi.sh"
sleep 2
REG=$(vm "cat ~/remotix.log")
if printf '%s\n' "$REG" | grep -qF "cattura audio fermata"; then
    ok "la cattura si e' fermata quando il client se n'e' andato"
else
    ko "la cattura e' rimasta accesa: si cattura per nessuno"
fi
if printf '%s\n' "$REG" | grep -qE "audio: [0-9]+ fotogrammi spediti.*riscontrati dal client"; then
    inf "$(printf '%s\n' "$REG" | grep -E 'riscontrati dal client' | tail -1 | sed 's/^[^ ]* *[A-Z]* *//')"
fi

# Il sink invece resta: e' della sessione, non della connessione.
SINK=$(vm "wpctl status | grep -c ' REMOTIX '")
if [ "${SINK:-0}" -ge 1 ]; then
    ok "il sink e' rimasto in piedi dopo la disconnessione: appartiene alla sessione"
else
    ko "il sink e' sparito col client: le applicazioni perderebbero il dispositivo a ogni stacco"
fi

# ===========================================================================
titolo "Riepilogo"
# ===========================================================================
# ⛔ SI RIMETTE IN PIEDI IL SERVIZIO COME LO SI E' TROVATO (§8.6 di REFERENCE.md).
vm "printf 'REMOTIX_OPZIONI=--registro diagnostica\n' | sudo tee /etc/default/remotix >/dev/null; \
    sudo systemctl restart remotix.service; sleep 2; \
    systemctl is-active --quiet remotix.service && echo RIPRISTINATO" 2>&1 | grep -q RIPRISTINATO \
    && inf "servizio rimesso in piedi con PAM e senza copia dei campioni" \
    || inf "ATTENZIONE: il servizio nella VM non e' ripartito"

inf "resta la prova dell'ORECCHIO, su mstsc e su RDM: questo banco non la sostituisce"

if [ "$GUASTI" -eq 0 ]; then
    printf '\n\033[1;32mFASE 8: tutti i controlli superati\033[0m\n\n'
else
    printf '\n\033[1;31mFASE 8: %d controlli falliti\033[0m\n\n' "$GUASTI"
fi
exit $((GUASTI > 0))
