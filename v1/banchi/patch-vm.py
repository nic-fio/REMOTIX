#!/usr/bin/env python3
"""Aggiunge a vm.sh il comando `copia`, che porta un file dentro la VM.

Serve dalla fase 1 in avanti: il binario si costruisce nel contenitore e va
eseguito nella VM, che sono due macchine diverse per vincolo dell'utente
(§6.2 di SPECIFICA.md).  Senza questo, ogni fase si inventerebbe un trasporto.

Idempotente: se il comando c'e' gia', non fa nulla.
"""
import re
import sys

PERCORSO = "/media/REMOTIX/vm.sh"

FUNZIONE = '''
# ---------------------------------------------------------------------------
# copia: porta un file dentro la VM
#
# Il binario di REMOTIX si costruisce nel contenitore di sviluppo e si esegue
# nella VM: sono due macchine distinte per vincolo (§6.2 di SPECIFICA.md), e
# fra le due serve un trasporto. Questo e' quello, e usa la stessa chiave con
# cui `vm.sh ssh` entra.
#
#   bash vm.sh copia <locale> [destinazione]     destinazione predefinita: ~
# ---------------------------------------------------------------------------
cmd_copia() {
    local sorgente="${1:-}" destinazione="${2:-}"
    if [ -z "$sorgente" ] || [ ! -e "$sorgente" ]; then
        printf '\\n\\033[1;31mERRORE\\033[0m file da copiare mancante o inesistente: %s\\n' \\
            "${sorgente:-<nessuno>}" >&2
        return 1
    fi

    scp -q -i "$KEY" -P "$SSH_PORT" \\
        -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \\
        -o LogLevel=ERROR \\
        "$sorgente" "$VM_USER@localhost:${destinazione:-}"
    ok "copiato $(basename "$sorgente") -> ${destinazione:-~} nella VM"
}

'''


def main():
    testo = open(PERCORSO).read()

    if "cmd_copia()" in testo:
        print("vm.sh ha gia' il comando 'copia': non tocco nulla")
        return 0

    # La funzione va inserita prima dello smistamento dei comandi.
    ancora = re.search(r"^case \"\$\{1:-\}\" in", testo, re.M)
    if not ancora:
        print("non trovo lo smistamento dei comandi in vm.sh", file=sys.stderr)
        return 1
    testo = testo[: ancora.start()] + FUNZIONE.lstrip("\n") + testo[ancora.start() :]

    # La voce nello smistamento, accanto alle altre.
    testo = testo.replace(
        '    ssh)       shift; cmd_ssh       "$@" ;;',
        '    ssh)       shift; cmd_ssh       "$@" ;;\n'
        '    copia)     shift; cmd_copia     "$@" ;;',
        1,
    )

    # La riga d'uso nell'intestazione, dove un lettore la cerca.
    testo = testo.replace(
        "#   bash vm.sh ssh [cmd]  apre una shell nella VM, o vi esegue un comando",
        "#   bash vm.sh ssh [cmd]  apre una shell nella VM, o vi esegue un comando\n"
        "#   bash vm.sh copia F [D] copia un file dentro la VM (predefinito: ~)",
        1,
    )

    open(PERCORSO, "w").write(testo)
    print("aggiunto il comando 'copia' a vm.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
