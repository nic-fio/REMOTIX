#!/bin/bash
#
# Gli appunti, a fondo.
#
#   bash /media/REMOTIX/src/remotix-c/prove/fase8-appunti.sh
#
# `fase8.sh` prova che gli appunti FUNZIONANO: una riga di testo e un'immagine
# piccola, nei due versi.  Questo banco prova che funzionano ANCHE quando la
# cosa si fa scomoda, ed e' li' che stanno i difetti:
#
#   - testo lungo, che il canale deve spezzare e ricucire;
#   - accenti e caratteri fuori dal piano base (le emoji), che in UTF-16
#     diventano coppie surrogate: chi conta i caratteri invece dei byte li
#     taglia a meta';
#   - i fine riga, che di qua sono `\n` e di la' `\r\n`;
#   - l'HTML, che sul filo viaggia avvolto in un'intestazione di offset in byte:
#     sbagliarli non da' errore, incolla mezza pagina;
#   - un'immagine grande, dove il conto dell'inizio dei pixel del DIB conta
#     davvero;
#   - una raffica di copie, dove deve vincere l'ultima;
#   - la RICONNESSIONE: gli appunti sono della sessione, e chi torna deve
#     ritrovarli;
#   - un formato che non c'e', dove nessuno dei due lati deve restare appeso —
#     ed e' il difetto peggiore di tutti, perche' si presenta come un desktop
#     che si e' piantato.
#
# ⚠ VALGONO LE REGOLE DI FASE 5 E 7 SUL PILOTARE I DUE AMBIENTI, piu' una che
#   questa fase ha imparato: chi mette qualcosa negli appunti RESTA IN VITA a
#   tenerli (`wl-copy`, `xclip`), quindi va staccato; e su `enter.sh` non si
#   dirotta MAI l'uscita su /dev/null, perche' dentro c'e' un `sudo` che puo'
#   chiedere la parola d'ordine e la chiede proprio li'.
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

# ---------------------------------------------------------------------------
# Gli aiutanti, in file loro: un heredoc dentro un altro, spedito per ssh,
# misura le regole di citazione della shell invece che REMOTIX.
# ---------------------------------------------------------------------------
cat > "$BANCO_FUORI/ap-client.sh" <<CLIENT
#!/bin/bash
# Avvia il client.  Senza argomenti riusa l'Xvfb che c'e' gia'.
set -u
export XDG_RUNTIME_DIR=/tmp/rt
pkill -x xfreerdp3 2>/dev/null
pgrep -f '^Xvfb $DISPLAY_CLI' >/dev/null || {
    Xvfb $DISPLAY_CLI -screen 0 2400x1600x24 -nolisten tcp >/dev/null 2>&1 &
    sleep 2
}
cd $BANCO || exit 1
setsid nohup env DISPLAY=$DISPLAY_CLI XDG_RUNTIME_DIR=/tmp/rt xfreerdp3 \\
    /v:127.0.0.1:$PORTA /gfx:AVC420 /cert:ignore /sec:tls /u:prova /p:prova \\
    /size:$MISURA /clipboard /log-level:WARN >ap-client.log 2>&1 </dev/null &
sleep 7
pgrep -x xfreerdp3 >/dev/null && echo "   client collegato" || echo "   client NON partito"
CLIENT

cat > "$BANCO_FUORI/ap-copia.sh" <<'COPIA'
#!/bin/bash
# Mette un file negli appunti del CLIENT.  $1 = tipo X, $2 = file
set -u
pkill -x xclip 2>/dev/null
setsid nohup env DISPLAY=:110 xclip -selection clipboard -t "$1" -i "$2" >/dev/null 2>&1 &
sleep 2
echo "   il client tiene ($1)"
COPIA

cat > "$BANCO_FUORI/ap-genera.py" <<'PY'
# I testi e le immagini di prova, tutti scritti da qui: cosi' i due lati
# confrontano gli stessi byte e non due idee di quel che dovevano essere.
import struct, sys, zlib

quale = sys.argv[1]

if quale == "lungo":
    riga = "REMOTIX prova di appunti lunghi, riga %05d.\n"
    testo = "".join(riga % i for i in range(2000))
    open("/tmp/ap-lungo.txt", "w", encoding="utf-8").write(testo)
    print(len(testo.encode("utf-8")))

elif quale == "strano":
    # Accenti, simboli, e due caratteri FUORI dal piano base: in UTF-16 sono
    # coppie surrogate, ed e' li' che un conto sbagliato taglia a meta'.
    testo = "perche' però: àèìòù €10 — «virgolette» 😀🎧 fine"
    open("/tmp/ap-strano.txt", "w", encoding="utf-8").write(testo)
    print(len(testo.encode("utf-8")))

elif quale == "righe":
    open("/tmp/ap-righe.txt", "w", encoding="utf-8").write("prima\nseconda\nterza\n")
    print("3")

elif quale == "html":
    open("/tmp/ap-html.txt", "w", encoding="utf-8").write(
        "<b>grassetto</b> e <i>corsivo</i>")
    print("ok")

elif quale == "grande":
    larg, alt = 320, 200
    righe = b"".join(
        b"\x00" + bytes([(x * 7) % 256, (y * 11) % 256, ((x + y) * 3) % 256, 255][k]
                        for x in range(larg) for k in range(4))
        for y in range(alt))
    def pezzo(tipo, dati):
        return (struct.pack(">I", len(dati)) + tipo + dati
                + struct.pack(">I", zlib.crc32(tipo + dati)))
    png = (b"\x89PNG\r\n\x1a\n"
           + pezzo(b"IHDR", struct.pack(">IIBBBBB", larg, alt, 8, 6, 0, 0, 0))
           + pezzo(b"IDAT", zlib.compress(righe))
           + pezzo(b"IEND", b""))
    open("/tmp/ap-grande.png", "wb").write(png)
    print("%d %d" % (larg, alt))
PY

cat > "$BANCO_FUORI/ap-confronta.py" <<'PY'
# Confronta due testi, tollerando la differenza di fine riga: e' esattamente
# quel che il protocollo cambia per strada, e non e' un errore.
import sys

a = open(sys.argv[1], encoding="utf-8", errors="replace").read()
b = open(sys.argv[2], encoding="utf-8", errors="replace").read()
a_n = a.replace("\r\n", "\n").rstrip("\n\x00")
b_n = b.replace("\r\n", "\n").rstrip("\n\x00")
if a_n == b_n:
    print("UGUALI %d" % len(b.encode("utf-8")))
else:
    # Dove divergono, che e' la sola cosa utile quando non tornano.
    n = min(len(a_n), len(b_n))
    dove = next((i for i in range(n) if a_n[i] != b_n[i]), n)
    print("DIVERSI %d %d %d %r %r"
          % (len(a_n), len(b_n), dove, a_n[dove:dove + 12], b_n[dove:dove + 12]))
PY

cat > "$BANCO_FUORI/ap-bmp.py" <<'PY'
import struct, sys
d = open(sys.argv[1], "rb").read()
if len(d) < 54 or d[:2] != b"BM":
    print("NO %d" % len(d))
else:
    print("SI %d %d %d"
          % (struct.unpack("<i", d[18:22])[0], struct.unpack("<i", d[22:26])[0],
             struct.unpack("<H", d[28:30])[0]))
PY

cat > "$BANCO_FUORI/ap-crlf.py" <<'PY'
# Il testo che il client ha ricevuto deve avere i `\r\n`: senza, quel che si
# incolla in un programma di Windows compare tutto su una riga sola.
import sys
d = open(sys.argv[1], "rb").read()
print("CRLF %d LF %d" % (d.count(b"\r\n"), d.count(b"\n") - d.count(b"\r\n")))
PY

copia "$BANCO_FUORI/ap-genera.py" /tmp >/dev/null 2>&1
copia "$BANCO_FUORI/ap-confronta.py" /tmp >/dev/null 2>&1
cnt "cp $BANCO/ap-genera.py $BANCO/ap-confronta.py $BANCO/ap-bmp.py $BANCO/ap-crlf.py /tmp/"

# Copia nella sessione, staccata: `wl-copy` resta in vita a tenere la selezione.
copia_sessione() { # $1 = tipo mime   $2 = file
    vm "pkill -x wl-copy 2>/dev/null; setsid nohup env WAYLAND_DISPLAY=wayland-0 \
        XDG_RUNTIME_DIR=/run/user/1000 wl-copy --type '$1' < '$2' >/dev/null 2>&1 & \
        sleep 2; echo '   la sessione tiene ($1)'"
}

leggi_client() { # $1 = tipo X   $2 = file dove scriverlo
    cnt "DISPLAY=$DISPLAY_CLI timeout 10 xclip -selection clipboard -t '$1' -o > '$2' 2>/dev/null; \
         echo \"   il client ha letto \$(stat -c %s '$2' 2>/dev/null || echo 0) byte\""
}

leggi_sessione() { # $1 = tipo mime   $2 = file dove scriverlo
    vm "env WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 timeout 10 \
        wl-paste --type '$1' > '$2' 2>/dev/null; \
        echo \"   la sessione ha letto \$(stat -c %s '$2' 2>/dev/null || echo 0) byte\""
}

# ===========================================================================
titolo "0. Server e client"
# ===========================================================================
vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
copia "$BIN_LOCALE" >/dev/null || exit 1
vm "bash avvia-remotix.sh --aperto" | tail -1
cnt "bash $BANCO/ap-client.sh"

REG=$(vm "cat ~/remotix.log")
if printf '%s\n' "$REG" | grep -qF "appunti collegati alla sessione"; then
    ok "il canale degli appunti si e' aperto"
else
    ko "il canale degli appunti non si e' aperto: il resto non prova niente"
    exit 1
fi

# ===========================================================================
titolo "1. Testo lungo: il canale lo spezza, e deve ricucirlo"
# ===========================================================================
QUANTI=$(vm "python3 /tmp/ap-genera.py lungo" | tr -d '[:space:]')
inf "$QUANTI byte di testo nella sessione"
copia_sessione "text/plain;charset=utf-8" /tmp/ap-lungo.txt
leggi_client UTF8_STRING /tmp/ap-lungo-dal-server.txt

# Il confronto si fa nella VM, dove c'e' l'originale: si riporta indietro il
# file letto dal client.
cnt "cp /tmp/ap-lungo-dal-server.txt $BANCO/"
copia "$BANCO_FUORI/ap-lungo-dal-server.txt" /tmp >/dev/null 2>&1
ESITO=$(vm "python3 /tmp/ap-confronta.py /tmp/ap-lungo.txt /tmp/ap-lungo-dal-server.txt")
set -- $ESITO
if [ "${1:-}" = "UGUALI" ]; then
    ok "il testo lungo e' arrivato intero: ${2:-?} byte, identico all'originale"
else
    ko "il testo lungo e' arrivato diverso: ${ESITO}"
fi

# ===========================================================================
titolo "2. Accenti e caratteri fuori dal piano base"
# ===========================================================================
# ⛔ LE EMOJI SONO IL CONTROLLO VERO.  In UTF-16 stanno su DUE unita' (coppia
#    surrogata): chi converte contando i caratteri invece dei byte le taglia a
#    meta', e il client mostra due rombi neri al posto di una faccia.
vm "python3 /tmp/ap-genera.py strano" >/dev/null
copia_sessione "text/plain;charset=utf-8" /tmp/ap-strano.txt
leggi_client UTF8_STRING /tmp/ap-strano-dal-server.txt
cnt "cp /tmp/ap-strano-dal-server.txt $BANCO/"
copia "$BANCO_FUORI/ap-strano-dal-server.txt" /tmp >/dev/null 2>&1
ESITO=$(vm "python3 /tmp/ap-confronta.py /tmp/ap-strano.txt /tmp/ap-strano-dal-server.txt")
set -- $ESITO
if [ "${1:-}" = "UGUALI" ]; then
    ok "accenti, simboli ed emoji sono tornati identici (${2:-?} byte)"
else
    ko "il testo strano e' arrivato diverso: ${ESITO}"
fi

# ===========================================================================
titolo "3. I fine riga: `\\n` di qua, `\\r\\n` di la'"
# ===========================================================================
vm "python3 /tmp/ap-genera.py righe" >/dev/null
copia_sessione "text/plain;charset=utf-8" /tmp/ap-righe.txt
leggi_client UTF8_STRING /tmp/ap-righe-dal-server.txt
# ⛔ LA CONVERSIONE SI MISURA SUL FILO, NON SULLA SELEZIONE X DEL CLIENT.
#
#    Il client di FreeRDP riporta i `\r\n` a `\n` quando consegna il testo al
#    proprio X — e fa bene, quello e' il mondo Unix.  Guardando li' si
#    misurerebbe la sua conversione, non la nostra, e il banco direbbe «rotto»
#    di un codice giusto.  Quel che si puo' misurare e' il CONTO DEI BYTE che
#    abbiamo spedito: «prima\nseconda\nterza\n» sono 20 byte; con i tre
#    `\r` diventano 23 caratteri, in UTF-16 46 byte, piu' i due dello zero
#    finale: 48.  Un solo numero, e non torna se manca anche un solo `\r`.
sleep 1
REG=$(vm "cat ~/remotix.log")
BYTE=$(printf '%s\n' "$REG" | grep -F "al client," | tail -1 | grep -oE '[0-9]+ byte' | grep -oE '^[0-9]+')
if [ "${BYTE:-0}" = "48" ]; then
    ok "sul filo sono partiti 48 byte: i tre `\r\n` e lo zero finale ci sono tutti"
else
    ko "sul filo sono partiti ${BYTE:-?} byte invece di 48: i fine riga non sono stati convertiti"
fi

# E che il client li abbia riportati a `\n` per il proprio mondo si guarda lo
# stesso, ma come INFORMAZIONE: e' un fatto suo, non un controllo su di noi.
ESITO=$(cnt "python3 /tmp/ap-crlf.py /tmp/ap-righe-dal-server.txt")
inf "nella selezione X del client: $ESITO (il client riporta i fine riga al suo mondo)"

# E all'incontrario: quel che torna alla sessione non deve avere `\r`.
cnt "printf 'uno\r\ndue\r\ntre\r\n' > /tmp/ap-crlf-dal-client.txt"
cnt "bash $BANCO/ap-copia.sh UTF8_STRING /tmp/ap-crlf-dal-client.txt"
leggi_sessione "text/plain;charset=utf-8" /tmp/ap-crlf-in-sessione.txt
CR=$(vm "grep -c \$'\r' /tmp/ap-crlf-in-sessione.txt || true" | tr -d '[:space:]')
if [ "${CR:-1}" = "0" ]; then
    ok "il testo tornato alla sessione non ha ritorni carrello"
else
    ko "il testo tornato alla sessione ha ancora $CR righe con `\\r`"
fi

# ===========================================================================
titolo "4. HTML: l'intestazione con gli offset in byte"
# ===========================================================================
# Sul filo l'HTML viaggia avvolto in `CF_HTML`, che dichiara in decimale dove
# comincia e dove finisce il pezzo.  Sbagliare quei numeri non da' errore: fa
# incollare mezza pagina, o l'intestazione insieme al testo.
vm "python3 /tmp/ap-genera.py html" >/dev/null
copia_sessione "text/html" /tmp/ap-html.txt
leggi_client text/html /tmp/ap-html-dal-server.txt
CONTENUTO=$(cnt "cat /tmp/ap-html-dal-server.txt 2>/dev/null | head -c 200")
if printf '%s' "$CONTENUTO" | grep -q "<b>grassetto</b>"; then
    ok "il frammento HTML e' arrivato intero al client"
else
    ko "l'HTML non e' arrivato al client (letto: $(printf '%s' "$CONTENUTO" | head -c 80))"
fi

# ⛔ QUEL CHE NON DEVE ESSERCI E' L'INTESTAZIONE NUMERICA.
#
#    `<html><body>` e i due commenti `StartFragment`/`EndFragment` fanno parte
#    del contenuto di CF_HTML e ci stanno bene: il client li lascia passare
#    perche' li' dentro ci sono anche in Windows.  Le righe `Version:0.9` e
#    `StartHTML:` invece sono l'intestazione, e il client le toglie usando gli
#    OFFSET che abbiamo dichiarato: se comparissero nel testo incollato,
#    vorrebbe dire che quegli offset non tornano.
if printf '%s' "$CONTENUTO" | grep -qi "Version:0.9\|StartHTML:"; then
    ko "nel testo del client c'e' l'intestazione CF_HTML: gli offset non tornano"
    inf "$(printf '%s' "$CONTENUTO" | head -c 120)"
else
    ok "l'intestazione con gli offset e' stata consumata dal client, non incollata"
fi

inf "gli offset veri li giudica mstsc: qui li giudica il solo consumatore che il banco ha"

# ===========================================================================
titolo "5. Un'immagine grande: il conto dei pixel del DIB"
# ===========================================================================
MISURE=$(vm "python3 /tmp/ap-genera.py grande")
inf "PNG di prova: $MISURE"
copia_sessione "image/png" /tmp/ap-grande.png
leggi_client image/bmp /tmp/ap-grande-dal-server.bmp
ESITO=$(cnt "python3 /tmp/ap-bmp.py /tmp/ap-grande-dal-server.bmp")
set -- $ESITO
if [ "${1:-NO}" = "SI" ] && [ "${2:-0}" = "320" ] && [ "${3:-0}" = "200" ]; then
    ok "il client ha ricevuto un BMP 320x200 a ${4:-?} bit"
else
    ko "l'immagine grande non e' arrivata: $ESITO"
fi

# E ritorno, che e' il verso in cui il DIB va ricomposto in BMP.
cnt "bash $BANCO/ap-copia.sh image/bmp /tmp/ap-grande-dal-server.bmp"
leggi_sessione image/png /tmp/ap-grande-in-sessione.png
ESITO=$(vm "python3 - <<'PY'
import gi
gi.require_version('GdkPixbuf','2.0')
from gi.repository import GdkPixbuf
try:
    p = GdkPixbuf.Pixbuf.new_from_file('/tmp/ap-grande-in-sessione.png')
    print('SI %d %d' % (p.get_width(), p.get_height()))
except Exception:
    print('NO')
PY")
set -- $ESITO
if [ "${1:-NO}" = "SI" ] && [ "${2:-0}" = "320" ] && [ "${3:-0}" = "200" ]; then
    ok "e la sessione l'ha riavuta indietro 320x200"
else
    ko "l'immagine grande non e' tornata alla sessione: $ESITO"
fi

# ===========================================================================
titolo "6. Una raffica di copie: vince l'ultima"
# ===========================================================================
vm "pkill -x wl-copy 2>/dev/null; \
    for i in 1 2 3 4 5; do \
      printf \"copia numero \$i\" > /tmp/ap-raffica.txt; \
      setsid nohup env WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 \
        wl-copy < /tmp/ap-raffica.txt >/dev/null 2>&1 & \
      sleep 0.4; \
    done; sleep 2; echo '   cinque copie di fila nella sessione'"
sleep 2
LETTO=$(cnt "DISPLAY=$DISPLAY_CLI timeout 10 xclip -selection clipboard -o 2>/dev/null" | tr -d '\r')
if printf '%s' "$LETTO" | grep -qF "copia numero 5"; then
    ok "dopo cinque copie il client legge l'ultima: «$LETTO»"
else
    ko "il client legge «$LETTO» invece di «copia numero 5»"
fi

# ===========================================================================
titolo "7. Un formato che non c'e': nessuno resta appeso"
# ===========================================================================
# ⛔ IL CONTROLLO PIU' IMPORTANTE DEL BANCO, e il piu' facile da non fare.
#    Una richiesta senza risposta non si presenta come un errore: si presenta
#    come l'applicazione che sta incollando, ferma per sempre.  Qui la sessione
#    ha del TESTO, e si chiede un'IMMAGINE.
INIZIO=$(date +%s)
cnt "DISPLAY=$DISPLAY_CLI timeout 15 xclip -selection clipboard -t image/bmp -o > /tmp/ap-vuoto.bin 2>/dev/null; \
     echo \"   risposta: \$(stat -c %s /tmp/ap-vuoto.bin 2>/dev/null || echo 0) byte\""
DURATA=$(( $(date +%s) - INIZIO ))
if [ "$DURATA" -lt 14 ]; then
    ok "la richiesta di un formato assente si e' chiusa in ${DURATA}s, senza restare appesa"
else
    ko "la richiesta di un formato assente ha impiegato ${DURATA}s: qualcuno non risponde"
fi

# ===========================================================================
titolo "8. Riconnessione: gli appunti sono della SESSIONE"
# ===========================================================================
vm "pkill -x wl-copy 2>/dev/null; printf 'sopravvissuto allo stacco' > /tmp/ap-prima.txt; \
    setsid nohup env WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 \
    wl-copy < /tmp/ap-prima.txt >/dev/null 2>&1 & sleep 2; echo '   copiato prima dello stacco'"
cnt "pkill -x xfreerdp3 2>/dev/null; sleep 3; echo '   client staccato'"
cnt "bash $BANCO/ap-client.sh"
sleep 2
LETTO=$(cnt "DISPLAY=$DISPLAY_CLI timeout 10 xclip -selection clipboard -o 2>/dev/null" | tr -d '\r')
if printf '%s' "$LETTO" | grep -qF "sopravvissuto allo stacco"; then
    ok "il client che si ricollega ritrova gli appunti della sessione: «$LETTO»"
else
    ko "dopo la riconnessione il client legge «$LETTO»"
fi

REG=$(vm "cat ~/remotix.log")
APERTURE=$(printf '%s\n' "$REG" | grep -cF "appunti collegati alla sessione")
ACCENSIONI=$(printf '%s\n' "$REG" | grep -cF "appunti della sessione accesi")
if [ "$APERTURE" -ge 2 ] && [ "$ACCENSIONI" -eq 1 ]; then
    ok "due canali per due connessioni, ma UNA sola clipboard di sessione"
else
    ko "canali aperti $APERTURE, clipboard di sessione accese $ACCENSIONI: la seconda e' di troppo"
fi

# ===========================================================================
titolo "9. Il congedo non lascia richieste appese"
# ===========================================================================
cnt "pkill -x xclip 2>/dev/null; pkill -x xfreerdp3 2>/dev/null; sleep 2; echo '   client chiuso'"
REG=$(vm "cat ~/remotix.log")
if printf '%s\n' "$REG" | grep -qE "appunti: [0-9]+ trasferimenti"; then
    inf "$(printf '%s\n' "$REG" | grep -E 'appunti: [0-9]+ trasferimenti' | tail -1 | sed 's/^[^ ]* *[A-Z]* *//')"
fi
if printf '%s\n' "$REG" | grep -qF "segfault\|assertion"; then
    ko "il registro riporta un guasto grave"
else
    ok "nessun guasto nel registro"
fi

# Il palco, e con lui gli appunti, deve essere ancora in piedi.
if vm "systemctl is-active --quiet remotix.service && echo VIVO" | grep -q VIVO; then
    ok "il server e' ancora vivo dopo tutta la campagna"
else
    ko "il server e' morto durante la campagna"
fi

# ===========================================================================
titolo "Riepilogo"
# ===========================================================================
vm "pkill -x wl-copy 2>/dev/null; printf 'REMOTIX_OPZIONI=--registro diagnostica\n' | sudo tee /etc/default/remotix >/dev/null; \
    sudo systemctl restart remotix.service; sleep 2; \
    systemctl is-active --quiet remotix.service && echo RIPRISTINATO" 2>&1 | grep -q RIPRISTINATO \
    && inf "servizio rimesso in piedi con PAM" \
    || inf "ATTENZIONE: il servizio nella VM non e' ripartito"

inf "questo banco usa xfreerdp3, che e' il client indulgente: mstsc e RDM restano da provare a mano"

if [ "$GUASTI" -eq 0 ]; then
    printf '\n\033[1;32mAPPUNTI: tutti i controlli superati\033[0m\n\n'
else
    printf '\n\033[1;31mAPPUNTI: %d controlli falliti\033[0m\n\n' "$GUASTI"
fi
exit $((GUASTI > 0))
