# Verifiche su Lubuntu / LXQt (box `rxu-lxqt`, porta 8824) — 18 nov 2026, sera

Pacchetto provato: `/media/REMOTIX-UBUNTU/pacchetti/unione2/remotix_1.0.0-1+ubuntu26.04_amd64.deb` (SHA-256 `5bfc4da6…`).
Lavoro di VERIFICA e diagnosi: il codice del prodotto e gli strumenti in `prove/` NON sono stati toccati.
Tutto è stato fatto sul server, solo sul box `lxqt`. Script, registri e istantanee: `/media/REMOTIX-UBUNTU/lavoro/verifiche-lxqt/`
(da qui in avanti «la mia cartella»). Orologio: le ore citate sono quelle del server (il box segna un'ora in meno: 21:19 server = 20:19 box).
Ovunque: «MISURATO» = visto con comando/istantanea; «SUPPOSTO» = ragionamento non provato direttamente.

## Riepilogo in una tabella

| Compito | Esito |
|---|---|
| A. Finestra «Lubuntu Update crashed too many times» | **DIFETTO** del programma `lubuntu-update` di Ubuntu (causa provata e riprodotta a volontà); su REMOTIX colpisce ogni 2º utente LXQt che entra mentre un altro è dentro. Cura proposta: non avviarlo nella sessione remota (come picom). |
| B. Log Out nei primi secondi; rientro subito | **FUNZIONA** (56 prove di uscita + 12 di rientro, nessuna anomalia). Nota: il pulsante «Log Out» nella pagina non esiste più (voluto dal 17 ago): si esce dal menu del desktop. |
| C. Inattività 22 minuti | **FUNZIONA** (nessun blocco schermo, schermo nero, salvaschermo). |
| D. `check-package.py` | **FUNZIONA** sul pacchetto: 7 PASS + 1 informativo + 1 BLOCKED (AppArmor assente nel contenitore). Due righe FAIL nello strumento originale sono dell'ambiente/dello strumento (copia adattata: tutto verde). In più: con `--no-install-recommends` la sessione LXQt **non nasce** e il client vede uno schermo vuoto senza messaggio (comportamento deciso come «Recommends», ma senza avviso all'utente). |

---

## A. La finestra «Lubuntu Update crashed too many times»

### A.1 Chi lancia `lubuntu-update` (MISURATO)
- `/etc/xdg/autostart/lubuntu-update-autostart.desktop` e `/etc/xdg/xdg-Lubuntu/autostart/lubuntu-update-autostart.desktop`:
  `Exec=/usr/bin/lubuntu-update`, `X-LXQt-Module=true`. Pacchetto: `lubuntu-update-notifier 1.1.1build1` (`dpkg -S`): non è di REMOTIX.
- Nella sessione (`pstree`) è un figlio diretto di `lxqt-session`. Perché è marcato «Module», `lxqt-session` lo rilancia se esce male
  e, dopo troppe uscite, mostra la finestra «Crash Report» (la stringa è dentro `/usr/bin/lxqt-session`: «`%1 crashed too many times. Its autorestart has been disabled until next login.`»).
- Ho scaricato il sorgente della stessa versione (`archive.ubuntu.com/.../lubuntu-update-notifier_1.1.1.tar.xz`, nella mia cartella `lun-src/`).

### A.2 La causa (PROVATA)
Il sorgente (`lubuntu-update/src/main.cpp`) controlla «sono già in esecuzione?» così:
```
procDetector.setProgram("/usr/bin/bash");
procDetector.setArguments(QStringList() << "-c" << "ps axo comm | grep " + procName);   // detectProc("lubuntu-update", 2)
```
`ps axo comm` elenca i processi di **tutti gli utenti**. Se ne vede almeno 2 chiamati `lubuntu-update`, il programma crede che ci sia «un'altra copia di me»
e prova a chiederle di mostrare la finestra via D-Bus **sul bus della propria sessione**; ma la copia viva è di un altro utente, quel nome sul bus
non c'è: `iface->isValid()` è falso, `return 1`. `lxqt-session` conta l'uscita con codice 1 come guasto, lo rilancia subito e, alla quinta volta, mostra la finestra.
Conseguenza: **il secondo utente che entra mentre il primo ha ancora `lubuntu-update` vivo ottiene sempre la finestra.**

Prove misurate:
1. `strace` (script `a4.py`; usato un bus di sessione privato, quindi il programma esce subito): `execve("/usr/bin/bash", ["/usr/bin/bash", "-c", "ps axo comm | grep lubuntu-update"], …)`, poi
   `The name me.lubuntu.LubuntuUpdate.window was not provided by any .service files`, `A connection to the bus can't be made`, `exit_group(1)`.
   (`ptrace` per agganciarsi a un processo vivo non è permesso nel contenitore; per questo strace solo su un avvio nuovo.)
2. Seconda copia lanciata a mano dentro la sessione dello STESSO utente mentre la prima vive (`a2.py`): `rc=0`, 0,074 s (D-Bus la trova, mostra la finestra, esce bene): nessun guasto.
3. **Riproduzione a due utenti insieme** (`a5.py`): `vl1` entra (a 10 s: `vl1 78848 … /usr/bin/lubuntu-update`); poi entra `vl2`: 25 s dopo la sua istantanea mostra la finestra
   «Crash Report — **Lubuntu Update** crashed too many times. Its autorestart has been disabled until next login.» Istantanea: `a5-vl2-second.png` (il primo utente, `a5-vl1-first.png`, è pulito).
4. **Tempi dei rilanci** (`a5b.py`, campionatore nel box ogni 20 ms sui `lubuntu-update` di `vl2` mentre `vl1` ha la sessione viva ma il browser chiuso):
   ```
   20:41:03.993601854 [83611 ]
   20:41:04.054539040 [83699 ]
   20:41:04.084373270 [83749 ]
   20:41:04.143168425 [83799 ]
   20:41:04.174276823 [83826 ]
   20:41:04.234408827 []
   ```
   Cinque partenze in 0,24 s, poi nessun processo: è il limite di `lxqt-session` (5). Istantanea `a5b-vl2-second.png`.
5. Controllo del meccanismo «5 guasti ⇒ finestra» con guasti veri (`a3.py`: `kill -SEGV` ad ogni nuovo `lubuntu-update`): pid 75262, 75601, 75665, 75729, 75793 (cinque avvii), poi la finestra identica. Istantanea `a3-SEGV-vl1.png`.
6. Spiegazione del caso originale (SUPPOSTO ma coerente con il codice): `l1.py` (giro unione2) fa il Log Out solo dopo la sessione 1 (`if sess == 1:`); alla fine della sessione 2 di `nl1` chiude solo il browser (`rig.stop()`),
   la sessione di `nl1` resta viva fino alla pulizia finale dello script. Quando `bc1` entra, c'è già un `lubuntu-update` di un altro utente ⇒ finestra, in entrambe le sessioni di `bc1`. `l1b.py` (che esce sempre con Log Out prima del prossimo utente) non l'ha mai vista: coerente.

### A.3 Ipotesi del mandato
| Ipotesi | Esito |
|---|---|
| (1) più sessioni/utenti insieme | **È QUESTA** (vedi sopra), non per un lock di apt ma per il conteggio dei processi di tutti gli utenti. |
| (1b) lock di apt/dpkg tenuti | **Scartata** (`a6.py`): un mio processo ha tenuto lock esclusivi (`fcntl.lockf`, nulla scritto) su `/var/lib/apt/lists/lock`, `/var/lib/dpkg/lock-frontend`, `/var/lib/dpkg/lock`, `/var/cache/apt/archives/lock` mentre entrava un utente: `lubuntu-update` è partito a +0,2 s e per 30 s è rimasto lo stesso pid, nessuna finestra (`a6-vl1-10s.png`, `a6-vl1-30s.png`). (Un primo comando sbagliato che apriva i file senza bloccarli è finito da solo dopo 60 s.) |
| (2) seconda sessione dello stesso utente | **Non è la causa.** Con il prodotto una seconda sessione dello stesso utente è un riattacco, non un secondo `lubuntu-update`. Dopo un Log Out `lxqt-session` sparisce entro 0,3 s (prove B), quindi non c'è sovrapposizione col processo vecchio (SUPPOSTO per `lubuntu-update` in particolare: non l'ho campionato nei rientri). |
| (3) apt in corso | **Non provata** con un vero `apt`; coperta da (1b). Il programma, all'avvio, non prende lock (da `strace`: solo il controllo `ps`). |
| (4) gara all'avvio | **Scartata**: il guasto è deterministico (condizione: un altro `lubuntu-update` vivo), non una gara. |

### A.4 Succede uguale in un accesso locale Lubuntu?
SUPPOSTO (nel box non c'è un accesso locale): **sì**. Il meccanismo è tutto dentro `lubuntu-update` e `lxqt-session`, non usa nulla di REMOTIX: due utenti con una sessione locale
LXQt (cambio utente veloce) darebbero la stessa finestra al secondo. Non è quindi un difetto «nostro» ma di Lubuntu 26.04; è però il caso normale di REMOTIX (server condiviso, più utenti insieme).

### A.5 Cura proposta (NON applicata)
La regola «remoto = accesso locale meno i danni da server condiviso» indica di **non avviare `lubuntu-update` nella sessione remota**: il danno è proprio da server condiviso (conta i processi altrui);
inoltre il suo scopo (installare aggiornamenti) passa per `lxqt-sudo`, cioè una finestra di password, vietata nelle sessioni remote (regola 1.5.3).
- Dove: `src/session.c`, `lxqt_session_commands()` (≈ righe 6240-6400), accanto alla ricetta di picom (`LXQT_X11_COMPOSITORS`, riga 6231) e di `lxqt-powermanagement`.
- Attenzione: la ricetta «script in `bin-lxqt` con lo stesso nome» **da sola non basta**: l'autostart di Lubuntu chiama `Exec=/usr/bin/lubuntu-update` con percorso assoluto, il PATH non lo intercetta
  (per picom funziona perché `picom.desktop` usa il nome nudo). Servono due pezzi: (a) lo script `lubuntu-update` in `bin-lxqt` (stessa `LXQT_SCRIPT_HEAD`: nella sessione remota esce 0 con una riga `logger`, altrove `exec` del vero); (b) un file
  `lubuntu-update-autostart.desktop` nella cartella `…/remotix/xdg-lxqt/autostart/` (prima voce di `XDG_CONFIG_DIRS` della sessione, visibile nell'ambiente: `XDG_CONFIG_DIRS=/run/user/1038/remotix/xdg-lxqt:/etc/xdg/xdg-Lubuntu:…`) con `Exec=lubuntu-update` nudo e `X-LXQt-Module=true`.
  Non è `Hidden=true`: la scelta del 14 nov (niente autostart nascosto nella cartella di sessione) resta rispettata, e uno script che si autocontrolla è innocuo anche in un accesso locale che ereditasse la cartella.
- Fattibilità MISURATA con una simulazione fatta dal test (NON dal prodotto): file di autostart per-utente nella home di prova (`a7.py`), con `vqa` vivo: con `Hidden=true` (utente `vqb`) e con `Exec=… exit 0` (utente `vqc`) il secondo e il terzo utente
  non hanno alcun `lubuntu-update`, nessun ciclo, nessuna finestra (`a7-vqb.png`, `a7-vqc.png`); `vqa` resta pulito. La prova del prodotto vero va rifatta dopo la modifica con due utenti insieme.
- Costo che si accetta: nelle sessioni remote niente notifica «Updates available!» (nella 1ª istantanea di unione2 compariva); il pulsante «Lubuntu Update» nei preferiti del menu farebbe niente in remoto (decidere se va bene).

---

## B. Log Out nei primi secondi e rientro immediato

### B.0 Come ho pilotato (e che cosa manca)
- **Il pulsante «Log Out» della pagina non esiste.** In `src/page.html` la funzione `run_logout()` (invia `TERMINATE_SESSION`) è legata solo a `#confirm-yes`, e nessun controllo apre quel riquadro: la scorciatoia è stata tolta il 17 ago 2026 («se l'utente vuole uscire lo fa dal menu di sistema», righe ≈10250-10300). Quindi non l'ho provato: non c'è da provare.
- Ho provato le due strade che esistono: **(menu)** clic veri col mouse virtuale sul desktop: pulsante start in basso a sinistra → pulsante rosso di spegnimento → riquadro «LXQt Session Logout — Do you want to really logout? All unsaved work will be lost…» → «Yes» (istantanee `m1-vm1-menu.png`, `m1-vm1-leave.png`);
  **(dbus)** il gesto che usa `check-lifecycle`: `busctl --user call org.lxqt.session /LXQtSession org.lxqt.session logout`.
  Un primo tentativo di «menu» via comando `lxqt-leave` lanciato da fuori sessione era sbagliato (lo script del prodotto riconosce la sessione remota dal `cgroup` del chiamante: da fuori è il programma vero e apre la finestra di scelta): scartato, rifatto con i clic.
- «Desktop apparso» = pannello `lxqt-panel` in esecuzione E immagine del canvas non uniforme (sondato ogni 0,15 s). Il tempo del Log Out è contato da lì; per il «menu» il tempo è del primo clic, il «Yes» arriva circa 1,8 s dopo (nel registro `b1-*.log`: es. «first click at +1.2s … Yes clicked at +3.0s»).
- Utente nuovo = creato per ogni prova; utente già usato = lo stesso utente, già entrato e uscito una volta.
- Condizione di fondo: nelle prove principali un altro utente (`idl1`, la prova C) aveva la sessione viva, quindi ogni utente di prova aveva il caso A (nessun `lubuntu-update` vivo, finestra di crash presente: colonna «lu» = 0). Ho ripetuto 8 prove da soli (colonna «lu» = 1, desktop pulito): stesso risultato.
- Per ogni prova ho sondato ogni ~0,3 s: sessioni logind dell'utente (`loginctl`), `lxqt-session`, `labwc`, processi dell'utente tranne l'infrastruttura (systemd --user, dbus, pipewire…), tutti i processi, cartella `/run/user/<uid>/remotix`, `/run/user/<uid>`; più la pagina (modulo di login di nuovo visibile con «ended»).

### B.1 Uscita: risultati (MISURATI)
| Serie (registro) | Prove | Log Out a | client avvisato | `lxqt-session` sparita | processi+logind+`/run/user/<uid>/remotix` spariti |
|---|---|---|---|---|---|
| utente nuovo, dbus (`b1-nd.log`) | 12 (1, 2, 4, 8 s × 3) | 1/2/4/8 s dal desktop | 1,3-1,4 s | 0,3-0,4 s | 11,3-11,6 s (una a 16,5 s) |
| utente nuovo, menu (`b1-nm.log`) | 12 | idem (primo clic) | 1,1-1,3 s | 0,1-0,3 s | 11,2-12,0 s |
| utente già usato, dbus (`b1-ud.log`) | 12 | idem | 1,3-1,4 s | 0,3-0,6 s | 11,4-11,7 s |
| utente già usato, menu (`b1-um.log`) | 12 | idem | 1,1-1,2 s | 0,2-0,3 s | 11,2-11,4 s |
| da soli (`lu`=1), nuovo, dbus (`b1-cl.log`) | 6 (1 e 2 s × 3) | 1/2 s | 1,3-1,4 s | 0,3-0,4 s | 11,5-16,4 s (due a 16,4 s) |
| da soli, nuovo, menu (`b1-clm.log`) | 2 (1 s) | 1 s | 1,2-1,3 s | 0,2 s | 11,3-11,4 s |

- **56 prove su 56: la sessione si chiude davvero.** A fine attesa, in tutte: 0 sessioni logind, 0 processi dell'utente (nemmeno systemd --user), 0 file in `/run/user/<uid>/remotix`, `/run/user/<uid>` sparita. Nessuna prova ha richiesto di forzare nulla (`loginctl terminate-user` non è mai scattato).
- I valori a 16,4-16,5 s (3 prove su 56) sono gli unici fuori dai 11,2-12,0 s; causa non cercata (SUPPOSTO: ritardo di systemd/logind del box sotto carico: il server era usato da altri agenti, load average 3-9).
- Perché ~11,5 s e non subito (MISURATO, prova `f1.py`, utente `fin1`, journal dell'utente): `21:40:04.078473 … child [fin1] ⭐ SIGTERM: the session is over — cleaned up (… the whole in 6 ms)`; la riga seguente del journal dell'utente è `21:40:14.130445 systemd[1162]: Activating special unit exit.target...`: **10,05 s esatti** dopo. In `/etc/systemd/logind.conf` `UserStopDelaySec=10` è il valore predefinito (riga commentata). Quindi i ~10 s sono l'attesa normale di logind, non lentezza del prodotto (SUPPOSTO per la relazione; MISURATI i due fatti).
- Journal del servizio per una prova (`b1-nd.log`, `vbnd1`): `farewell reason=0x10 detail=the graphical session has ended state=active`, `RELEASE ON DETACH (farewell): request SENT to the stage`, `the canvas of the stage of «vbnd1» (1344x768) is forgotten`, `transport PINGs off … the session is over`, `closed the WebTransport session, code 0x10`, `closed stream 0: the session is over, the slot is freed`. In 12 su 12 le stesse righe.
- Journal completo di un'uscita a 2 s (`f1.py`, ora server): `21:40:03.039962 child [fin1] ⚠ THE STAGE HAS GONE FROM UNDER OUR FEET (grab 2: the wire to the compositor dropped (read_events))` → `21:40:04.058404 session [fin1] no org.lxqt.session on the bus: the LXQt session is not there` → `21:40:04.058415 child [fin1] ⭐ §7.6: the graphical session WAS THERE and now is NO LONGER — the user logged out from the desktop menu. ⛔ I am NOT making it be born again…` → `21:40:04.073222 session [fin1] ⭐ R1/R2 (the session is over (§7.6)): the user manager goes back to how it was …` → `21:40:04.078473 … SIGTERM: the session is over — cleaned up`. Il client riceve `farewell reason=0x10` a `21:40:04.058663`.

### B.2 Rientro subito dopo il Log Out (`b2.py`, utente `vbrr1`, 3 ripetizioni per tempo, MISURATO)
Ritardo contato da quando la pagina mostra di nuovo il modulo con «ended» (≈1,3 s dopo il gesto).
| Rientro dopo | Prove | Esito |
|---|---|---|
| 0,3 s | 3 | ammesso al 1º tentativo, «Admitted, new session, canvas 1344×768, desktop lxqt», tentativo intero (digitazione compresa) 3,5 s; desktop (pannello + immagine non uniforme) 0,3-0,7 s dopo l'ammissione |
| 1 s | 3 | idem; desktop 0,3-0,7 s |
| 3 s | 3 | idem; desktop 0,3 / 0,3 / 0,3 s |
| 10 s | 3 | idem; desktop 0,3 / 1,9 / 0,3 s |
- **Mai rifiutato, mai schermo vuoto prolungato.** Il «desktop» a 0,3-1,9 s dall'ammissione include il tempo di digitare nome e password con le dita virtuali (≈3 s): la prova non può dire «quanto» in meno di ~1 s, dice che non c'è attesa lunga (su GNOME c'erano fino a 27 s).
- Stato al momento del rientro (a 0,3-3 s): `S=1 P=10 A=17` (cioè il vecchio *user manager* di systemd con pipewire & co. ancora vivo, nessun `lxqt-session`, nessun `labwc`): la nuova sessione lo riusa; ID di sessione vecchia e nuova diversi (es. `c7536 c7537` → `c7537 c7544`: cambia la sessione grafica, il «manager» è lo stesso). A 10 s: 2 volte su 3 non c'era più nulla (`S=0 A=0`), 1 volta residuava `P=1`: tutte ammesse.
- Istantanee «blank» (scattate se a +4 s il desktop non era su): nessuna prodotta.

### B.3 Conclusione B: **FUNZIONA**
Quel che NON ho misurato: Log Out a meno di 1 s dal desktop; Log Out con lavoro non salvato aperto; Log Out annullato («No»); sessione con finestre aperte dall'utente. Il giudizio «presto» regge da 1 s in su.

---

## C. Inattività: 22 minuti fermi (MISURATO)
`c1.py`, utente `idl1`, entrato alle 21:56:52, desktop stabile 21:57:03; da lì **nessun input** (solo il browser collegato e istantanee del canvas, ogni 2 minuti, 12 istantanee `c1-idl1-00min.png` … `c1-idl1-22min.png`).
Per ogni punto lo script ha scritto: frame dipinti, se l'immagine è «uniforme/degenerata», processi dell'utente con nomi tipo lock/screensaver/idle/dpms/blank/powermanag, stato logind.
- Immagine: mai uniforme (310-313 colori distinti a ogni istantanea, 339 la prima), il desktop è identico a 0 e a 22 min tranne l'orologio (verificato a vista su `c1-idl1-22min.png`: sfondo, icone, pannello, icona di aggiornamenti nell'area di notifica, nessuna finestra, nessun blocco).
- Processi di blocco/salvaschermo/idle: **nessuno** a nessun controllo (elenco vuoto 12 volte su 12). `lxqt-powermanagement` non gira (la ricetta del prodotto lo sostituisce con uno script che esce); `lxqt-xscreensaver-autostart` esiste tra gli autostart di sistema ma non ha prodotto alcun processo.
- logind: `State=active IdleHint=no LockedHint=no` a ogni controllo.
- Frame: `painted` cresce di 2 ogni 2 minuti (cambia solo l'orologio).
- Alla fine: nel journal del servizio nessuna riga di lock/idle/screensaver/dpms per `idl1`; solo `DIGITAL silence: 52000 blocks not sent of 52000` (audio muto, atteso).
- Un primo tentativo (utente `vlc1`) è stato interrotto dopo 12 minuti **per un mio errore** (un mio comando di pulizia `loginctl terminate-user` con un criterio troppo largo ha chiuso anche quella sessione); registro conservato in `c1-run1-interrupted.out` (12 minuti, stesso esito); la prova valida è la seconda, di 22 minuti.
- Nota: durante i 22 minuti ho eseguito sul box le prove B con ALTRI utenti (carico locale più alto: load average 3-9 sul server).
**Conclusione C: FUNZIONA** per 22 minuti su Lubuntu/LXQt (non verificato oltre; non verificato con carico zero perché c'erano le prove B in parallelo).

---

## D. `check-package.py`

### D.1 Che cosa fa (letto da `prove/check-package.py`, 598 righe)
Non è in `all.sh`: **azzera il box** (`box.sh reset`) all'inizio e per il controllo del rifiuto, e lo lascia fresco con il pacchetto installato. Nove righe: `install` (apt install su box fresco: file attesi, `dpkg -V` pulito, servizio installato ma né abilitato né in esecuzione, utente di sistema `remotix` nologin, riga `pam_exec` di `remotix-local-login` in `common-session`, niente sulla 7447);
`first-start` (enable --now: attivo, TCP+UDP, certificati con modi sicuri, nessun errore nel journal, i due processi come da progetto); `apparmor` (profilo caricato; BLOCKED se il box non ha l'interfaccia); `remove` (utente collegato, poi `apt remove` con la sessione viva: sessioni chiuse, processi spariti, gruppi e ACL su `/dev/dri` ripristinati, servizio fermo, binario via, configurazione e `/var/lib/remotix` tenuti, riga PAM tolta, nient'altro toccato); `purge` (tutto ciò che il pacchetto/programma ha fatto sparisce, scatto «prima/dopo» di /etc, /usr, /var/lib, /run, utenti, gruppi, unità, profili, polkit, firewall); `reinstall` (installazione dopo il purge + login base); `preinst` (un account PERSONA di nome `remotix`: l'installazione deve essere rifiutata col messaggio di `preinst`, box pulito); `recommends` (informativo); `fresh-end` (box lasciato fresco, abilitato).
Prova con `--no-install-recommends`: **non è coperta** dallo strumento (vedi D.4).

### D.2 Esecuzione 1: strumento ORIGINALE, copiato nella mia cartella (`package/check-package.py`, identico; non toccato l'originale in `prove/`)
Nessuna modifica era necessaria per porte e nomi (`lib.PORTS['lxqt']=8824`, `UID_BASE['lxqt']=3200`, già Ubuntu). Uscita completa: `d-run1-original.out`; registri e diff JSON: `d-run1-logs/package-lxqt/`.
```
FAIL install - package files missing: /usr/share/doc/remotix/THIRD-PARTY-LICENSES.gz; dpkg -V remotix: missing     /usr/share/doc/remotix/THIRD-PARTY-LICENSES.gz
PASS first-start - active, tcp+udp on 8824, network side pid 2960 as remotix CapEff: 0000000000000000 NoNewPrivs: 1 Seccomp: 2; root side pid 2894 as root; …
BLOCKED apparmor - AppArmor is not available in this box (securityfs /sys/kernel/security/apparmor is not mounted in the container; kernel module parameter: Y) …
PASS remove - … session and desktop processes gone 0 s after apt returned | after remove: apt ok, user session and desktop processes gone, service inactive, binary gone, dpkg state "rc", conf/state kept (all present) …
FAIL purge - paths of the box that are gone after the purge: /etc/apparmor.d/disable (dpkg -S: apparmor: /etc/apparmor.d/disable)
PASS reinstall - apt install ok, service after install disabled/inactive (as policy), after enable page "REMOTIX" login "Admitted, new session, canvas 1344×768, desktop lxqt" …
PASS preinst - apt rc=100, message: "remotix: an account named «remotix» already exists and is a person's: uid 1500 >= UID_MIN 1000; …"
PASS recommends - info: pulled in by this install: labwc, wlr-randr, xwayland, dconf-cli; already on the box: va-driver-all, mesa-vulkan-drivers, fonts-dejavu-core; … 13 new packages in all; download 1985 kB/3537 kB …
PASS fresh-end - fresh box, remotix 1.0.0-1+ubuntu26.04 installed, service enabled and active
```
Le due righe FAIL, classificate (cause PROVATE):
1. **install — `THIRD-PARTY-LICENSES.gz` «mancante»: classe (b/d), dell'ambiente.** Il box ha `/etc/dpkg/dpkg.cfg.d/excludes` con `path-exclude=/usr/share/doc/*` (lasciando solo `copyright` e `changelog.*`): `dpkg` non scompatta quel file; nella cartella ci sono `changelog.Debian.gz` e `copyright` e `dpkg -V` segnala solo quel file. Su una macchina vera non c'è quella regola. Il file è nel `.deb` (`dpkg-deb -c`).
2. **purge — `/etc/apparmor.d/disable` «sparita»: classe (b), strumento troppo severo; innocuo.** È una cartella vuota del pacchetto `apparmor`; la fa sparire lo snippet standard di `dh_apparmor` nel `postrm` (`rmdir /etc/apparmor.d/disable`, `…/local`, `/etc/apparmor.d`, tutti con `2>/dev/null`: tolgono solo cartelle vuote) che `postrm` di remotix contiene (visibile in `dpkg-deb -e … postrm`, blocco «Automatically added by dh_apparmor/5.0.2-0ubuntu1~26.04.1»). Altro nel diff «prima/dopo il purge»: nessuno (`removed: ['/etc/apparmor.d/disable']`, `added_unowned: ['/etc/cups/subscriptions.conf', '/var/lib/udisks2']` non di remotix, 12 pacchetti di dipendenze).
   Che la cartella ricompaia con una reinstallazione del pacchetto `apparmor` è SUPPOSTO (non provato).

### D.3 Esecuzione 2: copia ADATTATA `package/check-package-ubuntu.py` (stessa cartella; `lib.py`, `package-snap.py`, `fresh.sh` copiati senza modifiche; `boxes` è un collegamento a `/media/REMOTIX-UBUNTU/albero/boxes`)
Differenze rispetto all'originale (sono tutte e sole; si vedono con `diff package/check-package.py package/check-package-ubuntu.py`):
1. `c_install`: un file sotto `/usr/share/doc/` (tranne `copyright` e `changelog*`) non è «mancante» se il box ha `path-exclude=/usr/share/doc/*`; lo dice nelle note. Altri percorsi mancanti restano FAIL.
2. `c_purge`: le cartelle vuote `/etc/apparmor.d/disable`, `…/local`, `…/force-complain`, `/etc/apparmor.d` tolte dallo snippet di `dh_apparmor` sono una NOTA, non un FAIL. Ogni altro percorso sparito resta FAIL.
Risultato (`d-check-package-ubuntu.out`): **install PASS, first-start PASS, apparmor BLOCKED, remove PASS, purge PASS, reinstall PASS, preinst PASS, recommends PASS (informativo), fresh-end PASS.**
Righe notevoli: remove: «session and desktop processes gone 0 s after apt returned», nessuna ACL residua; purge: «box as before except: 12 dependency packages (dconf-cli, labwc, libei1, libliftoff0, liboeffis1, libseat1, libsfdo0, libwlroots-0.19, libxcb-errors0, libxcb-ewmh2, wlr-randr, xwayland)»; recommends: `labwc, wlr-randr, xwayland, dconf-cli` tirati dentro da apt, 13 pacchetti nuovi, 11,7 MB.
**Non capito/non visto:** AppArmor (profilo `flags=(complain)`: compila con `apparmor_parser -Q`, ma nel contenitore non c'è `securityfs`, quindi «caricato/in vigore» non è dimostrabile qui); `prerm`/`postrm` con sudo-rs/uutils sono stati eseguiti (remove/purge verdi) ma solo con l'utente `root` del box; `needrestart` non toccato.

### D.4 In più: `apt install --no-install-recommends` (non coperto dallo strumento; `d2.py`, `d2.out`)
Box azzerato, `apt-get install -y --no-install-recommends ./x.deb`: RC=0, `labwc`, `wlr-randr`, `xwayland`, `dconf-cli` NON installati (`un`); servizio attivo, TCP+UDP su 8824. Utente `nrc1`: «Admitted, new session, canvas 1344×768, desktop lxqt» ma **il desktop non nasce in 60 s** e il canvas resta senza dimensione (`Page.captureScreenshot: Cannot take screenshot with 0 width`); nessuna finestra, nessun testo per l'utente.
Causa PROVATA: `/home/nrc1/.local/state/remotix/session.log` contiene 11 volte `sh: 1: exec: labwc: not found`; il journal del servizio dice, ogni secondo, `«nrc1»: the stage for the canvas 1344x768 is NOT there YET` e `the session manager is not on the bus yet`; e all'avvio del servizio c'è già la riga «`LXQt (lxqt-session is there) — ⛔ but labwc is NOT, and LXQt on Wayland does not bring a compositor of its own: the session cannot be born until it is installed`» (`session.c`, righe ≈590-596).
La scelta «`labwc` solo Recommends» è scritta in `debian/control` (righe 85-110: «whoever uses --no-install-recommends loses them»). Il vuoto è nella comunicazione: l'amministratore trova la riga solo nel journal, il cliente vede un canvas nero senza messaggio.
Cura proposta (non applicata, per decisione del proprietario): (a) `postinst` avvisa («labwc non installato: XFCE/LXQt non partiranno») come già per `va-driver-all`; oppure (b) `session.c` rifiuta l'ingresso con un testo per il client («il server non ha il compositor: avvisa l'amministratore») invece di ammettere e aspettare; oppure (c) Depends `labwc | …` (cambia la decisione scritta).
La scatola è stata poi riportata allo stato richiesto (D.5).

### D.5 Stato finale del box (verificato a fine lavoro)
`fresh.sh lxqt` (reset + install + enable) dopo D.4. Confronto SHA-256: binario **installato** `/usr/libexec/remotix/remotix` = `6e38a49d04ea7e66eaab7d57ab7b731ff091729a2d3870fc76d27c79c9d92cd1`; binario **dentro il .deb** (`dpkg-deb --fsys-tarfile … | tar -xO ./usr/libexec/remotix/remotix`) = `6e38a49d04ea7e66eaab7d57ab7b731ff091729a2d3870fc76d27c79c9d92cd1`: **uguali**.
`systemctl is-enabled remotix` = enabled, `is-active` = active, `dpkg-query -W remotix` = `1.0.0-1+ubuntu26.04`, 2 socket sulla 8824 (tcp e udp), `REMOTIX_PORT=8824` in `/etc/remotix/remotix.conf.d/10-box-port.conf`. Sessione di prova (`f1.py`, utente `fin1`): «Admitted, new session, canvas 1344×768, desktop lxqt», desktop su in 1,8 s, `lubuntu-update` vivo (pid 1333, utente solo), Log Out riuscito; istantanea `f1-fin1-desktop.png`.

---

## Che cosa ho creato

**Nel box `rxu-lxqt`** (il box è stato azzerato più volte da `check-package`/`fresh.sh`: tutto ciò che c'era prima — utenti `vl1`, `vl2`, `vlc1`, `vm1`, `vbt01`, `vb*`, `vq*`, `idl1`, `nrc1`, `pk*` e le loro home — NON esiste più). Oggi nel box c'è, di mio, solo:
- l'utente **`fin1`** (uid 1002) con la sua home `/home/fin1` (sessione chiusa; nessun processo);
- il pacchetto unione2 installato dallo script `fresh.sh` (era lo scopo); `/root/x.deb` copiato dal tool.
Prima degli azzeramenti avevo creato (poi spariti): `vl1`, `vl2`, `vlc1`, `vm1`, `vbt01`, `vbnd1-12`, `vbnm1-12`, `vbuud`, `vbuum`, `vbcl1-6`, `vbclm1-2`, `vbrr1`, `vqa`, `vqb`, `vqc` (con file di autostart per-utente `lubuntu-update-autostart.desktop` nelle loro home), `idl1`, `nrc1`, e gli utenti dello strumento `pkglx1`, `pkglx2`.
Nessun file di sistema modificato a mano; l'unica cosa che ho «tenuto» nel box è stata una pausa di lock apt/dpkg (processi `python3`, `/tmp/vl-hold.py`, fermati con `pkill`; ero io a non scrivere nulla).

**Sul server host, solo in `/media/REMOTIX-UBUNTU/lavoro/verifiche-lxqt/`** (72 voci di primo livello, di cui 33 immagini, ≈ 16 MB al momento della scrittura):
- librerie e script: `vlib.py`, `a1.py … a7.py`, `a5b.py`, `b1.py`, `b2.py`, `c1.py`, `d2.py`, `f1.py`, `m1.py`, `patch_pkg.py`;
- registri: `b1-nd/nm/ud/um/cl/clm.log`, `b1-nm-aborted-run.log` (serie «menu» interrotta per l'errore descritto in B.0), `b2-r1.log`, `c1.out`, `c1-run1-interrupted.out`, `clean-all.out`, `b1-all.out`, `b1-rest.out`, `d2.out`, `d-run1-original.out`, `d-check-package.out`, `d-check-package-ubuntu.out`;
- istantanee: `a1-vl1.png`, `a3-SEGV-vl1.png`, `a5-vl1-first.png`, `a5-vl2-second.png`, `a5b-vl2-second.png`, `a6-vl1-10s.png`, `a6-vl1-30s.png`, `a7-vqa-first.png`, `a7-vqb.png`, `a7-vqc.png`, `c1-idl1-00min.png … 22min.png` (+ quelle del tentativo interrotto `c1-vlc1-*`), `m1-vm1-menu.png`, `m1-vm1-leave.png`, `f1-fin1-desktop.png`;
- `lun-src/` (sorgente di lubuntu-update-notifier 1.1.1 scaricato dall'archivio Ubuntu), `x-ctl/` (script di controllo del .deb estratti con `dpkg-deb -e`);
- `package/` (copia di lavoro di `check-package.py`, `lib.py`, `package-snap.py`, `fresh.sh`, la copia adattata `check-package-ubuntu.py`, il collegamento `boxes`, i registri in `package/log/`), `d-run1-logs/` (registri dell'esecuzione 1).
Nessun commit, nessun file sotto `/media/REMOTIX-DEBIAN`, nessuna modifica a `prove/`, `src/`, `docs/`, né ad altri box. Unico nuovo file sul tablet: questo documento.

## Errori miei da dichiarare
1. Pulizia troppo larga (`loginctl terminate-user` per i nomi che iniziano con `vl`) ha chiuso la mia sessione ferma `vlc1` a metà della prova C: la prova è stata rifatta da capo con `idl1`.
2. Prima serie «menu» di B: comando sbagliato (vedi B.0), interrotta dopo la 1ª prova e rifatta con i clic veri; nessun effetto sulle altre serie.
3. Ho usato un processo di prova (`/tmp/vl-hold.py`) per tenere i lock apt; la parte dello script `a6.py` con un primo `python3 -c` che apriva i file senza bloccarli è innocua e finita da sola.
