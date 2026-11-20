# Installatore di prova per la live (15)

## Comando esatto, da scrivere nel terminale della live
    wget -qO- http://192.168.0.2:8830/installa.sh | sudo bash
Il server dei file (porta 8830) gira sul server di sviluppo; e in RAM: dopo un riavvio va rilanciato (istruzioni in `/media/REMOTIX-UBUNTU/live/LEGGIMI.txt`).

## Cosa fa lo script (`server/live-installa.sh`, copia sul server: `live/installa.sh`)
1. Controlli: root, Ubuntu 26.04 (se no avvisa; chiede conferma solo con terminale, da pipe prosegue), desktop trovato, rete verso l'archivio.
2. Scarica .deb e .sha256 da `SORGENTE` (predefinito http://192.168.0.2:8830), verifica lo sha256, si ferma se non coincide.
3. Controlla che `universe` sia attivo (se manca: `add-apt-repository -y universe`, altrimenti modifica `ubuntu.sources` con copia di sicurezza), `apt-get update`, verifica che labwc sia disponibile.
4. `apt-get install -y --reinstall ./remotix_...deb` (con i Recommends); in caso di errore mostra le ultime righe.
5. Crea `prova` e `prova2` (password `prova2026`) solo se non esistono.
6. `systemctl enable --now remotix` (come dice il manuale, cap. 2), poi riavvio per la rieseguibilita; attende servizio attivo e porta in ascolto. Porta letta da `/usr/share/remotix/remotix.conf` + `/etc/remotix/remotix.conf.d` (predefinita 7447). `PORTA=<n>` (solo prove nei box) scrive `10-box-port.conf`. Se ufw e attivo lo dice e mostra `sudo ufw allow REMOTIX`, senza aprirlo.
7. Riepilogo: indirizzi https per ogni IPv4, utenti, avviso certificato, tre prove (a, b, c), come disinstallare.

## Prove nei container (uscite in `/media/REMOTIX-UBUNTU/lavoro/live-prove/`)
Il box raggiunge 192.168.0.2:8830 senza modifiche (rete condivisa con l'host).
| Box | installa (esito) | pacchetto | sha binario = .deb (17b5f091...) | servizio | porta | utenti | base-check |
|---|---|---|---|---|---|---|---|
| gnome (8821) | 0 | installato | si | attivo | in ascolto | prova, prova2 | 5 PASS |
| kde (8822) | 0 | installato | si | attivo | in ascolto | idem | 5 PASS |
| xfce (8823) | 0 | installato | si | attivo | in ascolto | idem | 5 PASS |
| lxqt (8824) | 0 | installato | si | attivo | in ascolto | idem | 5 PASS |
File: `<de>-install.log`, `<de>-verifica.log`, `<de>-basecheck.log`.
- Rieseguibilita: seconda esecuzione su tutti e quattro, esito 0, servizio attivo (`<de>-rilancio*.log`).
- Errori (`errori.log`): sha256 alterato (server di prova su 8831, poi fermato) = si ferma con messaggio chiaro e non installa; server irraggiungibile = messaggio chiaro, exit 1; senza root = messaggio chiaro, exit 1.
- Extra: `universe` tolto a mano nel box xfce = lo script lo riattiva con add-apt-repository; creazione utenti nuovi provata con nomi diversi (provax/provay, poi rimossi).
- Nei box `prova` e `prova2` esistevano gia (immagine): la creazione con i nomi veri non e stata vista, solo con altri nomi.
- Due bug trovati e corretti durante le prove: `grep -q` dopo una pipe con `pipefail` dava falsi negativi (universe e labwc "mancanti").

## Cosa NON e provabile nei container
La live vera: utente live senza password con sessione grafica locale, universe non attivo di serie (qui provato solo simulandolo), schermo di accesso locale e passaggio «Cambia utente» (prova b), snap/firefox della live, rete e archivio della live, video reale (GPU).

## Stato finale
Quattro box con REMOTIX installato dallo script, servizio attivo, nessun processo di prova/prova2. Firefox reinstallato con `firefox-nei-box.sh` + `firefox-nei-box2.sh` (il primo scrive «no installation candidate», il secondo lo installa: Firefox 160.0.1 presente in tutti e quattro).
