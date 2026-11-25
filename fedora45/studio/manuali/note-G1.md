# Note G1 — manuale tecnico Fedora 45, capitoli ch01–ch05 (25 nov 2026)

Scritte da chi ha riscritto i cinque capitoli. Tutto ciò che qui sotto è «non asserito nel manuale» è stato lasciato fuori o dichiarato «non verificato».

## Sezioni aggiunte, rinominate, tolte
- Nessuna sezione rinominata o tolta: nessun `rif()` esistente si rompe.
- Aggiunte (voci nuove, non rompono nulla):
  - ch01: «Requirements and what Fedora adds» (dopo «What REMOTIX is and what it promises»).
  - ch02: «The SELinux wall» (dopo «The network side and its walls»).
  - ch03: «KDE: KWin alone» (dopo «Birth of a graphical session»).
  - ch04: «Why a connection closed» (dopo «One connection from first packet to close»); dentro «Listeners, sockets and port 7447» c'è un blocco nuovo «The firewall: the firewalld service and the zones».
- Non fatte come sezioni a sé (integrate): il contesto SELinux della sessione dell'utente è la riga «5b» della tabella «The birth of a child» (ch02 §7); lingua e PATH stanno nel passo 6 della stessa tabella; la coppia `ExecStartPre … remotix-pam-hook check` sta nel paragrafo d'avvio (ch03 §1) e nella tabella dell'unità (ch03 §2).

## I tre punti più importanti
1. **Licenza.** Il manuale dice che il pacchetto Fedora non porta programmi di terzi (niente labwc/wlroots). Ma `fedora45/LICENSE.md` righe 95-102 e `fedora45/THIRD-PARTY-LICENSES` (elenco iniziale: «/usr/libexec/remotix/labwc», labwc 0.9.3, wlroots 0.19.2, `remotix-install`) dicono ancora il contrario. Decisione del proprietario: correggere quei due file (io non li ho toccati e nel manuale non cito il §8 di LICENSE.md).
2. **Difetti di sorgente non descritti come funzioni** (il manuale li dichiara «commenti stantii» solo dove serve): `fedora45/CLAUDE.md` riga «RPM packaging … to be written»; `src/local_login.c` righe 3-4 e 20 (`pam-auth-update`, «systemd 257»); `src/child.c` commento sul PATH che cita `/etc/environment` e `pam_env` come origine (su Fedora il caso normale è il ripiego `~/.local/bin:~/bin:…`); `src/session.c` chiave dconf `ubuntu-lock-on-suspend` (r.1739, effetto su Fedora non verificato); commenti di `rpm/remotix.service` (riga 6 «--without split», KillMode «the desktops … survive») e del `%post` della spec («the desktops stay alive»), e di `rpm/remotix.conf`, `remotix-no-suspend.conf`, `remotix.tmpfiles` («the engine»): contraddicono la decisione §11.56 (lo stop chiude i desktop).
3. **Cifre dei giri Fedora**: scritte come nel giornale di `PIANO.md` («gnome 52 PASS + all.sh 39 PASS; kde 76; xfce 60; lxqt 60», 23 nov; prove da chiavetta del 25 nov) e NON ricontrollate sui log (stanno sul server e in `~/remotix-prove-live/`). Il manuale le presenta «as the plan records it». Va bene finché nessuno ricontrolla; altrimenti far leggere i log al `meccanico`.

## Non verificato (nel manuale detto «has not been verified» o lasciato fuori)
- Effetto di `usermod -aG` / `render_grant` su Fedora (nodo di render 0666): detto «probabilmente niente da concedere, non verificato».
- Chiave dconf `ubuntu-lock-on-suspend` su Fedora.
- Nome del processo iniziatore di sessione GNOME 51 per il criterio di `rediscover.c` (la catena è `gdm-wayland-session → gnome-session-init-worker`); il criterio è strutturale (pid = sid, genitore fuori scope).
- Che la guardia `graphical-session.target` di GNOME 51 sia identica a quella di GNOME 50.
- Che il soccorso del logout Plasma (`session_kde_logout_watch`) scatti su Plasma 6.8; che l'esclusione di KDE dall'«early farewell» sia ancora necessaria con KWin `--virtual`.
- Che su Fedora un logind vecchio ancora in memoria non sia un caso (systemd 262): «non cercato».
- ML-KEM (`X25519MLKEM768`) e rotazione del certificato con OpenSSL 4.0; IPv6.
- Esistenza di `needrestart` nei repository Fedora e suo uso da parte di `dnf-automatic`: detto «precauzione e niente di più».
- Che `/etc/environment` manchi di serie su Fedora (dall'inventario; la prova nel codice è solo il commento di `child.c` e il ripiego).
- Esito isolato di `check-resilience.py` su Fedora (non registrato in PIANO/registro): dichiarato «not recorded».
- Contenuto riga per riga di `selinux/remotix.te`: la sezione «The SELinux wall» si appoggia a F24, F27, F28, F31, F36 e a quanto ho letto delle intestazioni del file, non a una lettura completa. Il riscontro vero va fatto in ch14.
- Conteggi «venti tipi di messaggio» (ch02 §8): non ricontati in modo certo (`#define MSG_` non esiste, sono un `enum` in `child.c`); l'insieme dei nomi `MSG_*` è identico a quello di Ubuntu (`diff`), quindi il testo è rimasto. I 29 puntatori di `rcp_hooks` sono stati ricontati sul codice di Fedora (29).

## Verifica fatta
- `python3 -m py_compile` sui cinque file: ok.
- `build.py --check tecnico-fedora` si ferma, come previsto, a `ch23_map.py` (elenco dei file mancanti/inesistenti): vedi `/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/7fd97d71-416c-4d57-a591-69957a77428b/scratchpad/manuali-G1/check.txt`.
- Controllo equivalente solo sui miei capitoli (script in scratchpad, stessa logica di `controlla()`: file e funzioni citati, variabili `REMOTIX_*`, codici `RX-`, frasi italiane, `rif()` risolti sui titoli di tutti i capitoli): nessuna contestazione.
- Grep sui miei file per apt, dpkg, .deb, debian/, ubuntu, snap, apparmor, ufw, lintian, podman, container, boxes/: restano solo citazioni volute (confronti espliciti con Debian/Ubuntu, la funzione `apparmor_exec_net()` ancora nel codice, «no containers», i file `STORIA-ubuntu-26.04.md` e `INVENTARIO-non-debian.md`, il registro D di Ubuntu).
