#!/bin/bash
# Applies step 5-bis of provision.sh to the LIVE container (R12-A.44).
#
# ---------------------------------------------------------------------------
# ⛔ THE PASSWORD NO LONGER GOES THROUGH THE COMMAND LINE — defect **D12**,
#    cured on 12 Aug 2026.
#
# ⛔ HERE THERE WAS `bash $E --root "printf '%s:%s\n' '$1' '$3' | chpasswd"`, and the
#    password `$3` ended up **inside the string** that `bash` receives as an argument:
#    i.e. in the `argv` of `bash`, in that of `sudo` and in that of the shell
#    launched inside the container.  `/proc/<pid>/cmdline` on Linux is
#    readable by anyone, and a `ps` during the round printed it in full.
#
# ⛔⛔ And it was not the public password of the benches: the «crea prova2 …» line passed
#    the **generated** password of `prova2` — the one that `01-b10-lancia.sh` treats
#    as not to be compromised, and that for this reason goes through a `0600`
#    file there.  ⇒ The tool that CREATES it showed it to anyone, while the
#    tool that USES it protected it.  Of the two, the one that mattered was
#    this one: a password born in `ps` is already compromised when B10 reads it.
#
# ⭐ THE ROAD IS THE ONE ALREADY IN THE HOUSE (`banchi/01-b10-lancia.sh`): a `0600`
#    file written with `printf`, which is a shell **builtin** — not even
#    the writing goes through a process with the password in `argv` — read by
#    `chpasswd` with a redirection **inside** the quotes, and deleted
#    right away, plus a `trap` for the case where the round dies halfway.
#
# ⚠ A plaintext copy remains on disk for the duration of one `chpasswd`, and it is
#   declared: it is the price for not having it in `ps`, where anyone sees it.
#   The file is `0600` and lives under `$FUORI/tmp`, not in `/tmp`.
#
# ⛔ And the redirection goes INSIDE the quotes, never around `enter.sh`: outside
#    it would carry away the `sudo` password prompt, and the script
#    would hang forever in silence (`FASI.md` §00-ambiente B3.3,
#    paid for four times).
# ---------------------------------------------------------------------------
set -uo pipefail
E=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CRED=/media/REMOTIX/credenziali-banchi
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

# ⛔ A name of its own: `01-b10-lancia.sh` uses `sera-b10-parola`, and two
#    tools writing the same file would delete each other's
#    password — the same shape that gave birth to the `PREFISSO` of
#    `01-p5-accendi.sh`.
PAROLA_FUORI=$FUORI/tmp/attrezzi-utenti-chpasswd
PAROLA_DENTRO=$DENTRO/tmp/attrezzi-utenti-chpasswd

ripulisci() { rm -f "$PAROLA_FUORI"; }
trap ripulisci EXIT

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⭐ THIS TOOL CREATED `prova` AND `prova2` **BLIND** — and did not say so
#
# ⛔ The `useradd` below gave no group, while `src/provisiona.sh`
#    gave them: two places that create the same thing, and they diverged.  Whoever
#    prepared the machine with one got tenants that see, with the other
#    tenants that will never see anything — `[M]` 0 sessions out of 4, zero
#    frames in 90 s (phase 10 §7.4).
#
# ⭐ THE CURE LIVES IN ONE FILE, `attrezzi-gruppi-scheda.sh`.  ⚠ But here the
#    commands run INSIDE the `enter.sh` chroot, where that file does not exist:
#    so the file **prints itself** (`--testo`) and the text goes into the
#    string.  ⇒ The logic stays ONE, and there is no hand-written copy of it.
#
# ⚠ And the chroot has `/dev` in rbind but an `/etc/group` all of its own: reading the
#   **gid from the node** and asking for the name in there is exactly what is needed —
#   a `render` hard-coded from outside might not exist inside.
# ═══════════════════════════════════════════════════════════════════════════
GRUPPI_SCHEDA_SH=${GRUPPI_SCHEDA_SH:-$(cd "$(dirname "$0")" && pwd)/attrezzi-gruppi-scheda.sh}
[ -f "$GRUPPI_SCHEDA_SH" ] || { ko "⛔ $GRUPPI_SCHEDA_SH is missing: the tenants would be born BLIND"; exit 2; }
# ⚠ The text goes into `"$GRUPPI_SCHEDA_TESTO"`, and the shell does NOT re-expand the
#   result of an expansion: the `$`s in there arrive intact.
GRUPPI_SCHEDA_TESTO=$(bash "$GRUPPI_SCHEDA_SH" --testo)
[ -n "$GRUPPI_SCHEDA_TESTO" ] || { ko "⛔ $GRUPPI_SCHEDA_SH --testo printed nothing"; exit 2; }

mkdir -p "$FUORI/tmp" || { ko "⛔ cannot create $FUORI/tmp"; exit 2; }

crea() # $1 name  $2 uid  $3 password
{
  local stato
  if bash $E --root "id -u $1 >/dev/null 2>&1"; then
    ok "user '$1' already present"
  else
    bash $E --root "useradd -u $2 -m -s /bin/bash $1" && ok "user '$1' created (uid $2)"
  fi
  # ⛔ D12: the «user:password» line that `chpasswd` eats is written to a
  #    `0600` file, not to a command line.
  # ⛔ `umask` IN A SUBSHELL — the line B10 paid for with a whole
  #    round: a bare `umask 077` sticks to everything that comes after,
  #    including the commands sent inside the container.
  ( umask 077; : > "$PAROLA_FUORI" ) || { ko "⛔ cannot write $PAROLA_FUORI"; return 2; }
  chmod 600 "$PAROLA_FUORI" || return 2
  # ⛔ `printf` is a builtin: no process with the password in `argv`.
  printf '%s:%s\n' "$1" "$3" > "$PAROLA_FUORI"
  bash $E --root "chpasswd < $PAROLA_DENTRO; s=\$?; rm -f $PAROLA_DENTRO; exit \$s"
  stato=$?
  # ⛔ And it is deleted RIGHT AWAY, not at the end of the script: the window in which the
  #    file exists must be that of the `chpasswd` and not the whole round.  The
  #    `trap` is the net for when the round dies, not the normal deletion.
  rm -f "$PAROLA_FUORI"
  if [ "$stato" -eq 0 ]; then
    ok "password of '$1' set from a 0600 file — never on a command line"
  else
    ko "⛔ chpasswd for '$1' exits $stato: the password was NOT set"
    return "$stato"
  fi
  # ⭐⭐ THE CARD GROUPS, READ FROM THE NODES INSIDE THE CHROOT.
  # ⛔ And if it does not get in, this tool STOPS: a blind `prova` sends
  #    every bench that starts from here to zero frames, and nobody notices.
  bash $E --root "$GRUPPI_SCHEDA_TESTO
gruppi_scheda_dai_a $1"
  stato=$?
  [ "$stato" -eq 0 ] || ko "⛔⛔ '$1' is NOT in the card groups (exit $stato): do NOT use this user to measure"
  return "$stato"
}

# ⛔ And if 'prova' is not born healthy we exit: going on would mean leaving
#    around a tenant that the benches will use believing it good.
crea prova 1001 parola-di-prova || exit 3

if [ -f "$CRED" ] && grep -q '^prova2:' "$CRED" 2>/dev/null; then
  P2=$(sed -n 's/^prova2:[[:space:]]*//p' "$CRED" | head -1)
  inf "password of 'prova2' read back from $CRED"
else
  # ⚠ `head -c 18 /dev/urandom | base64` — none of the three sees the password in
  #   `argv`: `base64` receives it on stdin, not as an argument.
  P2=$(head -c 18 /dev/urandom | base64 | tr -d '/+=' | head -c 20)
  touch "$CRED"; chmod 600 "$CRED"
  printf 'prova2: %s\n' "$P2" >> "$CRED"
  ok "password of 'prova2' generated and written to $CRED (0600)"
fi
# ⛔ `crea` is a FUNCTION, not a program: this call creates no
#    `argv`, and the password does not leave the shell.
crea prova2 1002 "$P2" || exit 3

echo
for u in prova prova2; do
  if bash $E --root "getent shadow $u | cut -d: -f2 | grep -q '^\\\$'"; then
    ok "$u: encrypted password present in /etc/shadow"
  else
    ko "⛔ $u: has NO usable password — PAM will reject it"
  fi
done
# ⭐ And it is READ BACK from inside, which is the only place that counts (E1).
bash $E --root "$GRUPPI_SCHEDA_TESTO
for u in prova prova2; do
  m=\$(gruppi_scheda_mancanti \$u)
  if [ -z \"\$m\" ]; then echo \"    OK  ⭐ \$u is in the groups of the card nodes: \$(id -nG \$u)\"
  else echo \"    NO  ⛔⛔ \$u is NOT in the groups \$m: its session IS BORN BLIND\"; fi
done"
bash $E --root "getent passwd prova prova2"
ls -l "$CRED"
