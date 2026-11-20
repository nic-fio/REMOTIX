# Priorità del journal — 17 nov 2026

Regola (`src/log.c`): marca in testa al corpo ⛔ → err, ⚠ → warning, altro → info.
Cambiata SOLO la marca di testa; testo, logica e livelli `log_detail` invariati.
Conteggi: run completo su 4 box (rx-xfce/lxqt/gnome/kde), `journalctl -b -p err`.

| Pattern | N | File:riga | Prima → dopo | Motivo |
|---|---|---|---|---|
| the stage of «U»: bus … streams delivering | 570+119 | child.c:3406 | err → info (⚠ se c'è un fault) | rapporto di nascita, routine |
| the stage of «U» (uid) has gone | 210 | main.c:2196 | err → info | il figlio esce al logout |
| FRAME NOT SENT: delta, wants KEYFRAME | 311 | rcp.c:6275 | err → info | ogni reattach, debito keyframe |
| FRAME NOT SENT: over the §6.2 ceiling | 0 | rcp.c:6291 | err → warning | ricodificato, sessione continua |
| CLIENT FIN on the control channel | 193 | webtransport.c:7731 | err → info | chiusura normale del client |
| NO VIDEO: SESSION not sent (state …) | 49 | rcp.c:6261 | err → warning | corsa alla chiusura, rifiutato |
| NO VIDEO: no codec negotiated | 0 | rcp.c:6303 | err (resta) | violazione di protocollo |
| delta frame THROWN AWAY BEFORE THE WIRE | 43 | rcp.c:6221 | err → warning | congestione, recupero con keyframe |
| the rate DROPS | 27 | webtransport.c:5255 | err → warning | congestione, regolatore interviene |
| KEYFRAME debt … SCREEN IS FROZEN | 11 | webtransport.c:5014 | err → warning | immagine ferma, ma si cura |
| RELEASE ON DETACH: could NOT be requested | 50 | rcp.c:6545 | err → warning | tasti forse rimasti premuti |
| FIFO **NOT** OBTAINED | 147 | child.c:6060 | err → warning | audio degradato, funziona |
| no stream from KWin | 130 | child.c:8814 | err → warning | sessione non pronta, si riprova |
| no virtual monitor to capture (Mutter) | 78 | child.c:8827 | err → warning | sessione non pronta, si riprova |
| NO STAGE at birth | 115 | child.c:10257 | err → warning | si riprova, non esce |
| ZERO MONITORS (session alive) | 25 | session.c:1103 | err → warning | sessione nera, ancora viva |
| THE STAGE HAS GONE FROM UNDER OUR FEET | 7 | child.c:11978 | err → warning | desktop perso, rimonta da solo |
| KWIN IS GONE | 2 | child.c:11934 | err → warning | logout/compositor, gestito |
| COMPOSITOR CLOSED THE INPUT CHANNEL (child) | 2 | child.c:11454 | err → warning | logout/compositor, gestito |
| the compositor CLOSED the input channel | 2 | input.c:1357 | err → warning | logout/compositor, gestito |
| the audio capture detached | 129 | sound.c:184 | err → warning | audio muto, sessione continua |
| AUTH refused BEFORE PAM (not a user) | 60 | rootside.c:1208,1211 | err → warning | login sbagliato, rifiutato |
| network side did not stop: SIGKILL | 9 | rootside.c:2507 | err → warning | spegnimento forzato, gestito |
| N sessions did not finish after 4 s | 18 | main.c:4239 | err → warning | chiusura lenta, prosegue |
| «systemctl …» did not succeed | 1 | session.c:2825 | err → warning | comando fallito, non fatale |
| nested KWin: output wrong size | 19 | kwin.c:1639 | err → warning | corretto richiedendolo di nuovo |
| DEAD LINE — QUIC connection closing | 8 | transport.c:2448 | err → warning | connessione persa, si chiude |
| N more lines before the login (burst) | 69 | webtransport.c:1041,1090 | err → warning | diluizione del log, flood |
| address BANNED: minutes remain | 8 | rcp.c:4369 | err → warning | rifiuto ripetuto durante ban |
| UNBLOCKED on command | 4 | command.c:157 | err → info | azione amministrativa voluta |
| BANNED address/user (new ban) | 8 | rcp.c:2700 | err (resta) | evento di sicurezza; testo letto da webtransport.c:2601 |
| R2: N passwords refused by PAM | 4 | rootside.c:1101,1107 | err (resta) | tentativi di forzatura, da vedere |
| FROM THIS SESSION THE MACHINE CAN BE POWERED OFF | 111 | child.c:9373 | err (resta) | vedi dubbi sotto |

Totale: 33 pattern osservati; info 5, warning 24, err tenuti 4 (NO VIDEO senza codec, BANNED, R2, POWERED OFF).

## Dubbi / scelte
- POWER OFF (111): sui box risponde «CanSuspend=(no answer)»: il controllo lo conta come fallimento. Tenuto err perché
  è la cintura di sicurezza §4.7; se sui box resta, è l'ambiente (logind senza risposta), non una riga normale.
  Se si vuole `-p err` vuoto anche lì, serve una decisione sulla logica del sentinel (fuori ambito).
- Righe «sessione non pronta» (no stream, no virtual monitor, NO STAGE, ZERO MONITORS) messe warning: sono
  rette da riprova; un desktop che davvero non parte resta visibile solo come warning ripetuto.
- Il `bus ⛔ NO` dentro il corpo della riga «the stage of» non è in testa: non conta per la priorità, lasciato.

## Fuori ambito (non nostre, solo elenco)
- `pam_env(...): Unable to open env file: /etc/default/locale` (sshd, cron, remotix: 2000+): su un Debian reale
  `/etc/default/locale` esiste (creato dall'installer / `locales`, `update-locale`); manca nell'immagine dei box.
  Nota, nessuna modifica.
- rtkit-daemon `cap_set_proc() failed` e `Failed to start rtkit-daemon` (container senza capability).
- colord `Failed to set up user namespacing`, obexd/evolution, gnome-keyring `.scope` falliti, pam_unix auth failure.

## Livello warning (controllo leggero)
Non misurato a fondo (lo scopo è `-p err`). Le righe ⚠ nuove sopra sono per costruzione già a warning.
Restano da rivedere con un run nuovo: ~700 punti di codice con testa ⛔ non osservati nel run (es. encoder.c
«QUALITY DOWN» è adattamento di banda: candidato a ⚠).
