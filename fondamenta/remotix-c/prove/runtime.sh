# runtime.sh — da dove si comanda la macchina di runtime.
#
# Si include con `. "$(dirname "$0")/runtime.sh"`, e definisce due cose sole:
#
#     vm "<comando>"        esegue sulla macchina di runtime
#     copia <file> [dove]   ci porta un file (predefinito: la home)
#
# ---------------------------------------------------------------------------
# ⛔ DAL 6 AGOSTO 2026 LA MACCHINA DI RUNTIME E' IL SERVER STESSO.
#
#    Deciso dall'utente (§6.2 di SPECIFICA.md): le prove che riguardano
#    l'hardware si fanno su hardware, senza un hypervisor in mezzo.  Non c'e'
#    quindi piu' nessun «altrove» in cui entrare, e `vm` esegue qui — il nome
#    resta perche' i banchi lo chiamano cosi' da sei fasi, e rinominarlo in
#    nove file per un trasloco sarebbe rumore.
#
# ⚠ LA VM RESTA RAGGIUNGIBILE con `RUNTIME=vm`, e non per nostalgia: e' la sola
#   macchina su cui esistano le misure delle fasi 2-9.  Finche' non saranno
#   rifatte sul ferro, e' il termine di paragone — e un confronto fra due
#   macchine diverse si puo' fare solo se si possono ancora interrogare
#   entrambe.
#
#     RUNTIME=vm bash prove/fase9.sh confronto
#
# ---------------------------------------------------------------------------
# ⛔ IL CONTENITORE DI SVILUPPO NON C'ENTRA E NON CAMBIA.  `cnt()` resta quello
#    che era: il client di prova (`xfreerdp3`, `Xvfb`, `xdotool`) gira li',
#    dev'essere separato da chi serve, e il contenitore condivide la rete
#    dell'host — quindi `127.0.0.1:3389` continua a essere il server, come
#    prima era la porta inoltrata della VM.
# ---------------------------------------------------------------------------
RUNTIME=${RUNTIME:-server}

case "$RUNTIME" in
server)
    vm() {
        # ⛔ SI PARTE DALLA HOME, e non e' un dettaglio di stile.
        #
        #    `vm.sh ssh` apriva una sessione, che comincia sempre nella home
        #    dell'utente; i banchi contano su questo e scrivono
        #    `bash avvia-remotix.sh --aperto` senza percorso.  Eseguendo qui,
        #    `bash -lc` eredita invece la cartella corrente del banco: lo
        #    script non si trova, il servizio resta com'era, e il sintomo
        #    arriva molto piu' tardi e travestito — il client del banco
        #    respinto perche' l'autenticazione era ancora accesa.  Misurato
        #    subito, al primo giro del trasloco.
        #
        # `-l` perche' il profilo dichiara l'ambiente del progetto, ed e' quel
        # che una sessione ssh dava gia'.  `</dev/null` per la stessa ragione
        # per cui serviva alla VM: un comando che eredita lo standard input
        # dello script non torna piu', se quello e' un terminale che non
        # finisce mai (lezione della fase 4).
        ( cd "$HOME" && bash -lc "$*" ) </dev/null
    }
    copia() {
        local f="$1" dove="${2:-$HOME}" nome
        nome=$(basename "$f")
        [ -e "$f" ] || { echo "copia: $f non esiste" >&2; return 1; }
        # ⛔ SI CANCELLA PRIMA DI COPIARE, e non e' pignoleria: sovrascrivere un
        #    binario in esecuzione da' «Text file busy» e la copia fallisce.
        #    Cancellandolo si stacca solo il nome — il processo vivo tiene il
        #    suo inode — e la copia crea un file nuovo.  Nella VM il problema
        #    non c'era perche' `scp` arrivava su una macchina dove quel binario
        #    non stava girando.
        rm -f "$dove/$nome"
        cp -f "$f" "$dove/$nome" || return 1
        chmod +x "$dove/$nome" 2>/dev/null
        return 0
    }
    ;;
vm)
    vm()    { bash "$BASE/vm.sh" ssh "$*" </dev/null; }
    copia() { bash "$BASE/vm.sh" copia "$@"; }
    ;;
*)
    echo "RUNTIME sconosciuto: $RUNTIME (server | vm)" >&2
    exit 1
    ;;
esac
