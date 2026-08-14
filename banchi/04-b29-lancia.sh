#!/bin/bash
# 04-b29 — la campagna intera della sonda S3, ⛔ **UNA CONFIGURAZIONE ALLA VOLTA**.
#
# ⛔ Non e' comodita': questo banco misura il **fuoco della finestra** e lo
#    **schermo intero**, cioe' due grandezze che esistono una sola volta su tutta
#    la scrivania.  Due giri insieme se le porterebbero via a vicenda, e i numeri
#    avrebbero lo stesso aspetto di quelli buoni.
#
# ⛔ E GIRA SUL DESKTOP VERO DELL'UTENTE, per forza: uno schermo finto non ha
#    ne' il fuoco ne' lo schermo intero — cioe' non ha nessuna delle due
#    grandezze che si misurano.  ⚠ Durante la campagna il puntatore si muove e i
#    tasti partono davvero: non e' il momento di usare la macchina.
#
# ⛔ Porte 7681 (pagina) · 7682 (debug Chrome) · 7683 (Firefox) · 7684 (Chrome in
#    finestra d'applicazione).  Le protette 7448 · 7501 · 7561 · 7571 non si
#    toccano, e questo banco non le apre mai.
#
# uso:  bash banchi/04-b29-lancia.sh [tutto|certifica|previeni|pwa|firefox-intero]
set -u
cd "$(dirname "$0")/.." || exit 1
CHE="${1:-tutto}"
S=banchi/04-b29-scorciatoie.py
E=banchi/04-b29-esiti.jsonl

# ⛔ IL CANCELLO, e viene PRIMA della misura perche' dopo sarebbe una
#    consolazione: se qualcuno tiene occupato il fuoco, non si misura niente.
if [ "${XDG_SESSION_TYPE:-}" != "wayland" ] && [ "${XDG_SESSION_TYPE:-}" != "x11" ]; then
  echo "⛔ nessuna sessione grafica: questo banco non ha niente da misurare."
  exit 3
fi
if ! busctl --user list 2>/dev/null | grep -q org.gnome.Mutter.RemoteDesktop; then
  echo "⛔ manca org.gnome.Mutter.RemoteDesktop: senza, l'iniezione non entra"
  echo "   dalla porta di una tastiera vera — e un'altra porta non vale."
  exit 3
fi

case "$CHE" in
  certifica)
    # ⛔ SI CERTIFICA PRIMA DI CREDERE (CODER.md §3.3): il controllo positivo
    #    deve arrivare, il negativo deve NON arrivare **e vedersi**.
    python3 -u "$S" chrome firefox --palchi finestra --solo-certifica \
            --esiti /var/tmp/b29/certifica.jsonl
    ;;
  tutto)
    # I cinque palchi, che sono le due leve incrociate: schermo intero (no /
    # API / F11) per lock (nessuna / vecchia / nuova).
    python3 -u "$S" chrome firefox --esiti "$E"
    ;;
  firefox-intero)
    # ⚠ Firefox 140 ESR ha voluto piu' di un colpo per andare a schermo intero:
    #    i palchi «con lock» su quel motore **non esistono** (non ha nessuna
    #    delle due forme) e il banco RIFIUTA di certificarli — che e' l'esito
    #    giusto, non un guasto.
    python3 -u "$S" firefox --palchi schermo-intero-api --esiti "$E"
    ;;
  previeni)
    # ⭐ IL SECONDO GIRO, e la differenza col primo e' la risposta che serve al
    #    prodotto: quali «consegnata E RISERVATA» si curano chiamando
    #    `preventDefault()` nella pagina, e quali no.
    python3 -u "$S" chrome firefox --previeni \
            --palchi finestra,schermo-intero-api --esiti "$E"
    ;;
  pwa)
    # ⭐ La `[R]` di `web.md` §5.1 («In Apps mode, no keys are reserved») portata
    #    a `[M]` senza un telefono: `--app=` apre la finestra d'applicazione, che
    #    e' lo stesso ramo di codice della PWA installata.
    #    ⚠ Resta `[?]` la meta' Android: non si deduce da qui.
    python3 -u "$S" chrome-app --palchi finestra,schermo-intero-api --esiti "$E"
    ;;
  *) echo "uso: $0 [tutto|certifica|previeni|pwa|firefox-intero]"; exit 2 ;;
esac

echo ""
python3 banchi/04-b29-tavola.py --esiti "$E"
