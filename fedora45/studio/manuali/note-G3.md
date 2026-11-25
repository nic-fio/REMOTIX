# Note G3 - capitoli tecnici ch12, ch13, ch14 (Fedora 45)

Data: 25 nov 2026. File toccati: `manuals/sources/technical-fedora45/ch12_desktops.py`, `ch13_login.py`, `ch14_security.py`. Nient'altro.

## I tre punti piu' importanti

1. **L'inventario G3 era sbagliato in due punti, e ho seguito il codice.** (a) Il PATH di ripiego della sessione remota ha `~/.local/bin:~/bin:/usr/local/bin:/usr/bin`
   (`child.c`, F34): l'inventario diceva che NON li ha. (b) `KWIN_FORCE_SW_CURSOR=1` e' impostata solo nel ramo annidato di `kwin.c` (irraggiungibile): su Fedora
   NON c'e' (l'inventario diceva che resta). Ho scritto cio' che dice il codice. Da rivedere se l'inventario viene usato da altri gruppi (ch03/ch06 di G1/G2).
2. **Il titolo di sezione e' cambiato in due punti** (vedi sotto): `rif()` di altri capitoli che puntano ai vecchi titoli ora non si risolvono. Con la mia copia
   «tollerante» del generatore (stato di oggi dei capitoli degli altri) tutti i `rif()` si risolvono; ma chi scrive ch01-ch11 e ch15-ch25 deve usare i NUOVI titoli.
3. **Difetti del sorgente da decidere (non li ho descritti come funzioni):** vedi l'elenco sotto. Il piu' visibile per l'amministratore e' il messaggio di avvio di
   `main.c:472` («Install the file of the family … .fedora, .suse, .arch») e i tre messaggi di `kwin.c` con `apt install --reinstall remotix`.

## Titoli di sezione cambiati (vecchio -> nuovo)

- ch12: «KDE Plasma: KWin nested in labwc» -> «KDE Plasma: KWin alone» (il vecchio titolo sarebbe falso; il solo `rif()` era in ch12 S1, aggiornato).
- ch14: «The AppArmor profile and its mode» -> «The SELinux module and its mode» (obbligatorio; `rif()` aggiornati in ch12 S4, S11 e ch14 S1, S3).
- Nessuna sezione aggiunta, spezzata o tolta. Tolto soltanto dentro le sezioni: il pezzo «Xubuntu has both GNOME markers», «The Ubuntu mode and its extensions»,
  tutta la parte di labwc nostro in KDE (figura, tabelle «Why KWin runs inside labwc» e «Traps», sei passi della riga di avvio), il paragrafo sui sysctl di AppArmor,
  il paragrafo «The other PAM line the package adds» (sostituito da «The line for local logins is not in this file» + una sezione di elenco su `remotix-pam-hook`
  dentro «The local-login hold»), la riga «snap policies» di polkit.
- Dipendenze: ch12 cita `rif("Removal: prerm, postrm and purge")` (ch15) e `rif("Files the package installs")` (ch13, ch14); G4 deve tenere questi due titoli.
  ch14 cita `rif("The SELinux module and its mode")` (mio) e ch12/ch14 citano `rif("KDE Plasma: KWin alone")`.

## Difetti del sorgente (NON descritti come funzioni; decisione del proprietario)

- `main.c:472`: messaggio di avvio «DOES NOT EXIST … Install the file of the family: src/remotix.pam (Debian/Ubuntu), .fedora, .suse, .arch» e frase su Fedora/Arch con `pam_deny`.
- `kwin.c:814,825,842`: «Remedy: reinstall the package (apt install --reinstall remotix)». Nel manuale: nota che dice che il rimedio vero e' `sudo dnf reinstall remotix`.
- `walls.h:43` e il commento dell'unita parlano ancora di `sudo apt install`.
- `src/remotix-remote-sessions.rules`: intestazione «five actions», il codice tratta sei (4 aggiornamenti catalogo + 2 macchina). Nel manuale: sei, con nota.
- `session.c`: `DCONF_KEYS` ha ancora la chiave `ubuntu-lock-on-suspend` (su Fedora saltata da `schema_has_key()` con una riga ⚠).
- `kwin.c`/`child.c`/`main.c`: codice di labwc-per-KDE ancora presente ma irraggiungibile (F7): il manuale lo dice e non lo descrive.
- `prove/check-package.py` e `prove/check-ban.py` sono quelli di Debian/Ubuntu (il primo parla di AppArmor e dpkg, 35 righe): non provano il muro SELinux.

## Numeri ricontati su fedora45/

- Costanti di `helper.c`, `rcp.c`, `rootside.h`, `rootside_proto.h`, `rootside.c`, `local_login.c`: tutte uguali al testo (MAX_IN_FLIGHT 16, RESERVED_FOR_KNOWN 2, EXPIRY_MS 8000,
  GRANDCHILD_ALARM_S 20, RESTART 1000/60000, STABLE_MS 60000, LOUD_AFTER 5; FIXED_DELAY 1000, REJECT_FLOOR 2500, VERDICT_CAP 12000; MAX_ATTEMPTS 256, BAN_QUOTA 160,
  UNKNOWN_LIMIT 5; RXR_AUTH 16/3/8, GRANT 30000; PL_GRACE 13000, PL_CEIL 20000, PL_HOLD 10000, PL_MAX 8, LOCAL_CEIL 25000, LX_EVERY 5000; KDE_LOGOUT 4000/3000/10;
  KDE_PRELOCAL_ORDERLY_MS 5000; CHILD_LOCALE_MAX 12; WAIT_EXIT_MS 10000; CLEAR_OUT_EXIT_WAIT_MS 2000).
- `remotix-pam-hook` 335 righe, `local_login.c` 132 righe (`wc -l`).
- Azioni della regola «no poweroff»: 19 (contate sulla lista dei nomi tra virgolette, righe 90-108; `grep -c 'login1'` da' 22 perche' conta anche i commenti).
- `prove/wall-neg-domain.py`: 25 tentativi, di cui 23 da rifiutare e 2 consentiti. Il registro F24 dice «21»: e' precedente a due aggiunte (non ho verificato quando).
- Chiavi dconf: 24 nella tabella, 21 con valore (conteggio dal sorgente: 12 `switch-to-session`, 9 altre con valore, 3 solo blocco). Su Fedora ne resterebbero 20 in vigore:
  scritto come «should be 20 … not read in a Fedora log», non come misura.

## Non verificato (scritto cosi' nel manuale, o lasciato fuori)

- Kernel e ABI Landlock di Fedora 45; contenuto di `/etc/authselect/password-auth` (nullok); `nsswitch.conf` di Fedora; `/etc/pam.d/login` e `other`; confronto riga per riga di
  `remotix.pam` con `sshd` di Fedora (fatto solo per copia, come dice l'intestazione).
- Se Plasma 6.8 ha ancora il difetto «plasma-shutdown non ferma il target»; se GNOME 51 parte nell'Overview e se `lock-warning-shown` serve ancora; estensioni GNOME di Fedora.
- `blueman`, `picom`, `lubuntu-update` su Fedora (nessun `rpm -q`); quali pannelli ha lo spin XFCE (whisker/actions).
- Tempi dei giri: usati solo quelli di `PIANO.md` e del registro, con data; non riletti sui log. I log delle prove a mano del proprietario (25 nov) non sono stati salvati per GNOME.
- Plasma Setup (`plasma-setup.service`, primo avvio): non descritto, perche' non verificato in remoto.
- Se `needrestart`/`dnf-automatic` rispetta la regola del pacchetto; versione di libei; stato della decisione sull'alternativa a F27 («far rieseguire le faccende come processo utente»).
- La prova di GDM con il gancio inserito (dialogo «Session Already Running» che non dovrebbe comparire): provata a mano solo con esito generale (GNOME OK); il dettaglio del dialogo non e' noto.

## Sul generatore

- `build.py --check` vero si ferma alla mappa dei file (`ch23_map.py`, non mio): atteso. Ho usato una copia tollerante (in scratchpad, fuori dal repository) con la mappa spenta.
  Residuo del controllo sui miei capitoli: nessuno. Restano solo contestazioni di altri capitoli (boxes/, debian/, build-deb.sh, labwc-ospite, server/vm*.sh, `./all.sh`,
  `studio/11-…`, `systemctl --user stop plasma-kwin_wayland.service` in ch15).
- Il file HTML finale `manuals/Technical Manual — Fedora 45.html` non esiste ancora: la contestazione «does not match the sources» e' generale.
