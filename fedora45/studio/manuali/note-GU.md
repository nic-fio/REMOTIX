# note-GU — manuale utente Fedora 45 (ch01-ch06): che cosa resta aperto

Data: 25 nov 2026. File toccati: solo `manuals/sources/user-fedora45/ch01_*.py … ch06_*.py`.
Controllo: `build.py --check utente-fedora` contesta soltanto «manuals/User Manual — Fedora 45.html does not match the sources» (il file HTML finale non e' ancora generato in `fedora45/manuals/`); nessun'altra contestazione. I `rif()` si risolvono tutti.

## Titoli di sezione cambiati, aggiunti, tolti (per chi cita con rif())

Rinominati («vecchio → nuovo»):
- Ubuntu 26.04: installing → Fedora 45: installing
- Ubuntu 26.04: the two refusals → Fedora 45: the two refusals
- Ubuntu 26.04: the firewall → Fedora 45: the firewall
- Ubuntu 26.04: the first visit and the certificate → Fedora 45: the first visit and the certificate
- Ubuntu 26.04: port, name and other settings → Fedora 45: port, name and other settings
- Ubuntu 26.04: who may connect → Fedora 45: who may connect
- Ubuntu 26.04: upgrading and removing → Fedora 45: upgrading and removing
- Known problems on Ubuntu 26.04 → Known problems on Fedora 45 (e anche il titolo della tabella)

Aggiunti:
- ch01: «Requirements» (seconda sezione, dopo «REMOTIX in short»): le quattro condizioni (codec RPM Fusion, porta firewalld, SELinux enforcing, orologio del dispositivo) e i limiti dichiarati (portachiavi, XFCE, nessuno spegnimento, KWin 6.8).
- ch02: «Fedora 45: video drivers (RPM Fusion)» (subito dopo «The steps»).

Tolti: nessuno. Tutti gli altri titoli sono invariati.

## I tre punti piu' importanti

1. **Comandi RPM Fusion**: li ho presi da `server/live-installa.sh` (e' cio' che ha preparato le macchine di prova: `rpmfusion-free-release-45`, `dnf swap mesa-va-drivers/mesa-vulkan-drivers -freeworld`, Intel: `rpmfusion-nonfree-release-45` + `intel-media-driver`, con `--allowerasing` se serve). Non li ho rieseguiti per il manuale. L'avviso del `%post` nomina solo `mesa-va-drivers-freeworld`; il manuale dice di installare entrambi i `-freeworld` come le macchine di prova.
2. **Titoli per gli altri scrittori**: i `rif()` dentro il manuale utente sono tutti aggiornati. Se il manuale tecnico cita titoli del manuale utente (per esempio «Requirements» o «Fedora 45: video drivers (RPM Fusion)»), deve usare i titoli esatti dell'elenco sopra.
3. **Cifre usate** (tutte dal PIANO.md/registro, non lette sui log): chiusura del remoto 1-2 s GNOME (F6, VM), 1,7 s XFCE, 0,7 s LXQt, KDE 5 s poi forzata, accesso locale a ~6 s (F36); 5/20/30 e 5/5/10 minuti (ricontati in `src/rcp.c`: `LIMIT`, `WINDOW_MS`); 33 layout (ricontati in `page.html`, tabella `KEYBOARDS`); tetto 10 sessioni (`RCP_SESSION_CAP`); 25 s (`LOCAL_CEIL_MS`).

## Dichiarato «non verificato» o omesso nel manuale (per decisione dello scrittore)

- Capacita': scritto «non piu' di tre persone provate insieme (test automatici, su GNOME)»: dal PIANO (two-users/three-users PASS con g6 su GNOME); non verificato su altri desktop.
- Browser: non ho trovato quale browser (Chrome/Chromium/Firefox) abbiano usato i giri automatici su Fedora; il manuale dice solo «browser su Linux» e «dal PC Linux, dal notebook Windows, da un dispositivo Android» (prove a mano del proprietario, 21-22 nov).
- Scheda Intel: il test di codifica e' riuscito sulla live (25 nov, macchina con Intel+Radeon); un desktop completo con la sola Intel non provato. Il manuale lo dice.
- Percorsi di licenza `/usr/share/licenses/remotix/LICENSE.md` e `/usr/share/doc/remotix/THIRD-PARTY-LICENSES`: dedotti da `%license` e `%doc` della spec, non confermati con `rpm -ql` sul pacchetto 1.2.0 (non ancora costruito). Stessa riserva per l'albero «Where things are» (percorsi dalla `%files`).
- GNOME 51 e l'Overview: frase attenuata («may start», «not checked again»).
- Samsung DeX: «non provato su Fedora» (il proprietario l'ha provato solo su un'altra distribuzione).
- needrestart/aggiornamenti automatici: «non verificato su Fedora» che rispettino la regola.
- I due rifiuti dell'installazione: «non provati su Fedora» (tutte le VM avevano il nodo DRM).
- Porta diversa da 7447 con SELinux enforcing: «non provato» (la regola del `.te` ammette le porte senza etichetta e le http).
- Regola firewalld per la sola rete locale (`--add-rich-rule`): OMESSA (non provata); il manuale dice solo che non e' stata provata.
- Stato di serie del firewall: scritto dai test delle macchine (studi 1-4: Workstation e KDE zona `FedoraWorkstation` con 1025-65535 aperte; XFCE e LXQt zona `public`), con l'invito a controllare la propria macchina.
- `pam_faillock`: non attivo di serie su Workstation (studio 1 §9.1); non provato insieme alla ban table di REMOTIX. Non ho scritto il comando `authselect enable-feature with-faillock` (non verificato).
- Orologio del dispositivo client: dal PIANO 22 nov («Opening handshake failed»); la causa tecnica (`notBefore` = adesso - 1 h, `certificates.c:143`) e' riletta nel codice.
- Orologi da 30 e 60 minuti con i valori veri su Fedora: «non verificato» (`check-lifecycle`/`check-resilience` esistono, i valori non sono scritti nel PIANO).
- Chiusura per abbandono su KDE e programmi lenti a chiudersi (5-10 s) su KDE: dichiarati non provati (PIANO).
- `rpm -V sddm` che segnala la modifica finche' REMOTIX e' installato: da F19 (VM).
- Rimozione e reinstallazione: provate su VM con pacchetti precedenti (l6, s13), non col 1.2.0 e non su una macchina fisica diversa dalle VM.
- Aarch64: non citato (la spec ha `ExclusiveArch: x86_64 aarch64`, ma il manuale dice x86_64 e basta).

## Difetti del SORGENTE o degli script NON descritti come funzioni (decisione del proprietario)

- `src/main.c` (~riga 472): il messaggio «the PAM service remotix DOES NOT EXIST» cita ancora «.fedora, .suse, .arch» e parla di `pam_deny`: nel manuale non l'ho citato.
- `src/walls.h` (~riga 43) cita ancora `sudo apt`; `src/remotix-remote-sessions.rules` dice «five actions» nell'intestazione ma il codice ne tratta sei (4 aggiornamenti catalogo + 2 per gli amministratori): nel manuale scrivo l'elenco delle azioni, senza il numero.
- `src/session.c` conserva la chiave `ubuntu-lock-on-suspend`: non citata.
- `prove/check-package.py` e' ancora quello Debian/Ubuntu (apparmor, dpkg): non lo cito come prova del pacchetto.
- `THIRD-PARTY-LICENSES` e `LICENSE.md`: il PIANO dice che sono gia' stati corretti il 25 nov (labwc/wlroots, remotix-install tolti); non li ho riletti.
- Il sorgente del portachiavi (D6): nessun difetto, solo limite dichiarato.
