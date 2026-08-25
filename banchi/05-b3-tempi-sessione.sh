#!/bin/bash
#
# 05-b3-tempi-sessione.sh — ⭐ VENTI GIRI, E OGNI FASE COL SUO CRONOMETRO.
#
#   sudo bash 05-b3-tempi-sessione.sh [giri] [larghezza] [altezza]
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE
#
# *«Sembra andare, ma al quarto login il desktop ha impiegato molti secondi.
#   Ogni volta pero' adesso non si rompe. Fai il login/logout almeno venti volte
#   e misura esattamente i tempi: poi dai log potrai capire esattamente quello
#   che accade»* — l'utente, 16 agosto 2026.
#
# ⭐ E' il mandato giusto: il difetto della CORRETTEZZA e' chiuso — il desktop
#    non si rompe piu' — e quel che resta e' un difetto di TEMPO.  ⛔ Un tempo
#    non si cura a occhio: si misura, si spezza in fasi, e si guarda quale fase
#    se lo mangia.
#
# ---------------------------------------------------------------------------
# LE QUATTRO FASI CHE SI CRONOMETRANO, e perche' proprio queste
#
#   attacco   → richiesta   quanto passa fra «sessione aperta» e «avvio la
#                           sessione grafica».  ⚠ Se e' grande, il tempo se ne
#                           va PRIMA di far nascere: e' il figlio che aspetta
#                           che la vecchia finisca (B7 di `SESSIONE.md`).
#   richiesta → palco       quanto ci mette `gnome-session` a farsi vedere e la
#                           cattura a montare.  E' il costo vero della nascita.
#   palco     → 1° fotogramma   la catena nostra: codificatore, filo.
#   ⭐ e QUANTE VOLTE la sessione e' stata avviata in quel giro: >1 vuol dire
#      che il primo avvio e' morto, ed e' li' che si perdono i secondi.
set -uo pipefail

GIRI=${1:-20}
L=${2:-2544}
A=${3:-926}
REG=/media/REMOTIX/tmp/04-vero/registro.log
ENTRA=/media/REMOTIX/enter.sh
ESITI=/tmp/05-b3-esiti.txt

[ "$(id -u)" -eq 0 ] || { echo "⛔ vuole root"; exit 2; }
: > "$ESITI"

esci_dal_desktop()
{
	runuser -u prova -- env XDG_RUNTIME_DIR=/run/user/1001 \
		DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus \
		gdbus call --session --dest org.gnome.SessionManager \
		  --object-path /org/gnome/SessionManager \
		  --method org.gnome.SessionManager.Logout 1 >/dev/null 2>&1
}

echo "== venti giri di login/logout, col cronometro su ogni fase =="
echo "   tela ${L}x${A}, $GIRI giri"
echo

for g in $(seq 1 "$GIRI"); do
	RIGHE=$(wc -l < "$REG")

	bash "$ENTRA" --root "cd /srv/src/04-vero-src/banchi && timeout 150 python3 \
	    01-b3-cliente.py --indirizzo 192.168.0.2 --porta 7700 --utente prova \
	    --parola prova2026 --larghezza $L --altezza $A --resta 100" \
	    >/tmp/05-b3-cli-$g.log 2>&1 &
	CLI=$!

	# ⛔ Non si aspetta il client: si aspetta IL FATTO.  Appena il primo
	#    fotogramma della misura giusta e' nel registro, il giro e' finito e non
	#    c'e' ragione di stare li' altri novanta secondi.
	for i in $(seq 1 120); do
		sleep 1
		tail -n +$((RIGHE + 1)) "$REG" 2>/dev/null | grep -aq "SPEDITO.*${L}x${A}" && break
	done
	kill $CLI 2>/dev/null; wait $CLI 2>/dev/null

	tail -n +$((RIGHE + 1)) "$REG" > /tmp/05-b3-giro.log 2>/dev/null

	python3 - "$g" "$L" "$A" >> "$ESITI" <<'PY'
import re, sys
giro, L, A = sys.argv[1], sys.argv[2], sys.argv[3]

def ms(t):
    h, m, s = t.split(":")
    sec, mil = s.split(".")
    return ((int(h) * 60 + int(m)) * 60 + int(sec)) * 1000 + int(mil)

righe = open("/tmp/05-b3-giro.log", errors="ignore").read().splitlines()

def primo(frase, dopo=0):
    for r in righe:
        if frase in r:
            t = r.split()[0]
            if re.match(r"^\d\d:\d\d:\d\d\.\d+$", t):
                v = ms(t)
                if v >= dopo:
                    return v
    return None

# ⛔ L'ANCORA E' LA NASCITA DEL FIGLIO, NON L'`ATTACCA` — e la prima stesura
#    sbagliava: la sessione grafica si avvia appena PAM dice si', cioe' PRIMA
#    che il client mandi `ATTACCA`.  ⇒ Le differenze venivano negative, e
#    misurarle dall'attacco avrebbe nascosto proprio il pezzo piu' lungo.
# ⭐ E questa e' anche l'ancora che sente l'UTENTE: preme «Collegati», e da li'
#    conta.
attacco  = primo("figlio generato per")
if attacco is None:
    attacco = primo("sessione aperta utente=prova")
avvii    = [ms(r.split()[0]) for r in righe
            if "avvio la sessione grafica" in r
            and re.match(r"^\d\d:\d\d:\d\d\.\d+$", r.split()[0])]
palco    = primo("il nostro monitor e' Meta-0")
fotog    = None
for r in righe:
    if "SPEDITO" in r and f"{L}x{A}" in r:
        t = r.split()[0]
        if re.match(r"^\d\d:\d\d:\d\d\.\d+$", t):
            fotog = ms(t); break

attese   = sum(1 for r in righe if "non e' ancora finita" in r)
spegne   = sum(1 for r in righe if "sta SPEGNENDOSI" in r)

def d(a, b):
    return (b - a) if (a is not None and b is not None and b >= a) else -1

print("%s|%d|%d|%d|%d|%d|%d|%d" % (
    giro,
    d(attacco, avvii[0] if avvii else None),
    d(avvii[0] if avvii else None, palco),
    d(palco, fotog),
    d(attacco, fotog),
    len(avvii), attese, spegne))
PY

	R=$(tail -1 "$ESITI")
	printf "giro %-3s  login→richiesta %5s ms · richiesta→palco %6s ms · palco→1° fotogr. %5s ms · ⭐ TOTALE %6s ms · avvii %s · attese %s\n" \
	    "$(echo "$R" | cut -d'|' -f1)" "$(echo "$R" | cut -d'|' -f2)" \
	    "$(echo "$R" | cut -d'|' -f3)" "$(echo "$R" | cut -d'|' -f4)" \
	    "$(echo "$R" | cut -d'|' -f5)" "$(echo "$R" | cut -d'|' -f6)" \
	    "$(echo "$R" | cut -d'|' -f7)"

	esci_dal_desktop
	for i in $(seq 1 40); do
		pgrep -u prova gnome-shell >/dev/null 2>&1 || break
		sleep 1
	done
	sleep 2
done

echo
echo "== il riassunto =="
python3 - <<'PY'
righe = [r.split("|") for r in open("/tmp/05-b3-esiti.txt").read().splitlines() if r]
def col(i):
    v = sorted(int(r[i]) for r in righe if int(r[i]) >= 0)
    return v
def stat(nome, i):
    v = col(i)
    if not v:
        print("   %-26s nessuna misura" % nome); return
    n = len(v)
    print("   %-26s mediana %6d ms · p90 %6d ms · max %6d ms   (%d giri)"
          % (nome, v[n // 2], v[min(n - 1, int(n * 0.9))], v[-1], n))
stat("login → richiesta", 1)
stat("richiesta → palco", 2)
stat("palco → 1° fotogramma", 3)
stat("⭐ TOTALE login → desktop", 4)
avvii = [int(r[5]) for r in righe]
print()
print("   avvii della sessione per giro: %s" % " ".join(str(a) for a in avvii))
print("   ⛔ giri in cui il PRIMO avvio e' morto: %d su %d"
      % (sum(1 for a in avvii if a > 1), len(avvii)))
print("   ⚠ giri in cui si e' aspettata la sessione precedente: %d"
      % sum(1 for r in righe if int(r[6]) > 0))
PY
