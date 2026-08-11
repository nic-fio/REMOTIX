#!/bin/bash
# Applica al contenitore VIVO il passo 5-bis di provision.sh (R12-A.44).
set -uo pipefail
E=/media/REMOTIX/enter.sh
CRED=/media/REMOTIX/credenziali-banchi
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

crea() # $1 nome  $2 uid  $3 parola
{
  if bash $E --root "id -u $1 >/dev/null 2>&1"; then
    ok "utente '$1' gia' presente"
  else
    bash $E --root "useradd -u $2 -m -s /bin/bash $1" && ok "utente '$1' creato (uid $2)"
  fi
  bash $E --root "printf '%s:%s\n' '$1' '$3' | chpasswd"
}

crea prova 1001 parola-di-prova

if [ -f "$CRED" ] && grep -q '^prova2:' "$CRED" 2>/dev/null; then
  P2=$(sed -n 's/^prova2:[[:space:]]*//p' "$CRED" | head -1)
  inf "parola di 'prova2' riletta da $CRED"
else
  P2=$(head -c 18 /dev/urandom | base64 | tr -d '/+=' | head -c 20)
  touch "$CRED"; chmod 600 "$CRED"
  printf 'prova2: %s\n' "$P2" >> "$CRED"
  ok "parola di 'prova2' generata e scritta in $CRED (0600)"
fi
crea prova2 1002 "$P2"

echo
for u in prova prova2; do
  if bash $E --root "getent shadow $u | cut -d: -f2 | grep -q '^\\\$'"; then
    ok "$u: parola d'ordine cifrata presente in /etc/shadow"
  else
    ko "⛔ $u: NON ha una parola utilizzabile — PAM lo rifiutera'"
  fi
done
bash $E --root "getent passwd prova prova2"
ls -l "$CRED"
