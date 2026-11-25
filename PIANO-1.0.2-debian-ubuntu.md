# Piano — adeguamento di Debian 13 e Ubuntu 26.04 alle due correzioni nate su Fedora (23 nov 2026)

Stato: **PROPOSTA, in attesa dell'OK del proprietario.** Finché non c'è l'OK non si tocca nulla in `debian13/` e
`ubuntu26.04/`. Questo file è nuovo e non sostituisce i `PIANO.md` delle due cartelle.

## 1. Obiettivo

REMOTIX deve comportarsi allo stesso modo su tutte le distribuzioni. Su Fedora sono entrate due correzioni che
Debian 13 e Ubuntu 26.04 (versione pubblicata 1.0.1) non hanno. Vanno portate anche lì, provate e pubblicate come
nuova versione (proposta: **1.0.2**), così le tre distribuzioni tornano uguali.

Le due correzioni:

- **A. Lingua della sessione remota.** Oggi il desktop remoto parte sempre in inglese «neutro». Deve partire nella
  lingua scelta dall'utente nelle Impostazioni, altrimenti in quella del sistema, come nell'accesso locale. Stessa
  regola per i formati (date, numeri) e per i percorsi dei programmi dell'utente.
- **B. Primo clic su GNOME.** Subito dopo l'accesso, il primo clic o tocco fatto senza prima muovere il mouse può
  finire sul bordo dello schermo (difetto di GNOME; sulle altre due distro è registrato come «saltuario»).
  REMOTIX lo aggira mandando due volte il primo movimento.

Che cosa NON entra: il muro SELinux, il firewall di Fedora, KDE con KWin da solo e tutto ciò che è proprio di
Fedora. Nessun'altra modifica al comportamento di Debian e Ubuntu.

## 2. Fatti di partenza (verificati oggi)

- Il codice delle due correzioni è scritto, provato e approvato dal revisore su Fedora (pacchetto `h1`). Il revisore
  giudica che si porti «tale e quale»; **su Debian e Ubuntu non è mai stato provato**.
- I tre file toccati (`src/child.c`, `src/session.c`, `src/input.c`) nelle tre cartelle sono simili ma non
  identici: va portata la modifica, non copiato il file.
- Su Debian e Ubuntu la lingua di sistema arriva già all'accesso per una strada diversa da Fedora
  (`/etc/default/locale`); la scelta dell'utente sta nello stesso posto di Fedora (AccountsService).
- **Sul server oggi non c'è più alcun banco di prova per Debian e Ubuntu**: le cartelle `/media/REMOTIX-DEBIAN` e
  `/media/REMOTIX-UBUNTU` non esistono. Ci sono le ISO di Ubuntu, Kubuntu, Xubuntu e Lubuntu 26.04.1; **le ISO di
  Debian 13 non ci sono**. Gli strumenti per ricostruire il banco sono nel repository.
- Per la 1.0.1 non fu fatto un giro completo di prove automatiche (solo le prove a mano del proprietario).
- Regole di banco: prove solo su macchine virtuali con la Radeon, nessun contenitore; la Radeon è una sola.

## 3. Decisioni che spettano al proprietario (prima di partire)

- **P1. Numero di versione.** Proposta: 1.0.2 per Debian e Ubuntu. Fedora uscirebbe allora anch'essa come 1.0.2
  (stesso comportamento, stesso numero) invece che 1.0.1. Alternativa: Fedora resta 1.0.1 con comportamento da 1.0.2.
- **P2. Come si costruiscono i pacchetti `.deb`.** La 1.0.0 e la 1.0.1 sono state costruite dentro un contenitore
  (podman), usato solo per costruire, non per provare. La regola «niente podman» è stata data per studio e prove.
  Proposta: costruire in due macchine virtuali apposite (come su Fedora), così non c'è alcun contenitore.
  Alternativa: stessa ricetta della 1.0.1 (contenitore solo per la costruzione), più veloce di circa un'ora.
- **P3. Ampiezza delle prove automatiche.** Proposta: giro completo su tutti e otto i desktop (la 1.0.1 non l'ha
  avuto e qui si tocca l'ambiente di ogni sessione). Alternativa più corta: giro completo su GNOME delle due distro
  e prove di base + lingua sugli altri sei (risparmia circa 3 ore).
- **P4. Le ISO di Debian 13.** Servono quattro immagini live ufficiali (GNOME, KDE, XFCE, LXQt). Le scarico io in
  una cartella nuova del server, oppure me le indichi tu.

## 4. Fasi, agenti, tempi

Dieci agenti: **P1–P4** programmatori (Sonnet), **M1–M4** meccanici (Haiku: banco, costruzioni, giri, log),
**R1–R2** revisori (Fable). Io coordino, verifico a campione e porto a te risultati e decisioni.
«Parallelo» = più agenti insieme; «in fila» = uno alla volta perché serve la Radeon.

| Fase | Che cosa | Chi | Come | Durata |
|---|---|---|---|---|
| 0 | Ricostruire il banco: 8 macchine virtuali (4 Debian, 4 Ubuntu) + 2 di costruzione, utenti di prova, istantanea «pulito» | M1–M4 (2 macchine a testa), P1 adatta gli script | parallelo, senza Radeon | 3–4 h |
| 1 | Misure sull'accesso locale, per ciascuno degli 8 desktop: lingua, formati, percorsi che riceve la sessione; versione di GNOME e presenza del difetto del clic su Debian e Ubuntu con la 1.0.1 | P1–P4 (2 desktop a testa) | parallelo; il clic richiede la Radeon: 2 macchine in fila | 1–2 h |
| 2 | Portare le due correzioni: Debian (P1 lingua, P2 clic) e Ubuntu (P3 lingua, P4 clic) | P1–P4 | parallelo (file diversi per agente nella stessa cartella) | 1–2 h |
| 3 | Costruire i due pacchetti di prova | M1, M2 | parallelo | 0,5–1 h |
| 4 | Revisione: R1 Debian, R2 Ubuntu; correzioni agli stessi programmatori | R1, R2, P1–P4 | parallelo, 1–2 giri | 2–3 h |
| 5a | Prove senza video (installazione, aggiornamento dalla 1.0.1, rimozione pulita, lingua di sistema e dell'utente, formati, percorsi) sugli 8 desktop | M1–M4 | parallelo, senza Radeon | 1–2 h |
| 5b | Giro completo con il video vero sugli 8 desktop; desktop realmente in italiano; primo clic su GNOME | M1 guida, M2–M4 leggono i log | **in fila** (Radeon): ~40 min a desktop | 5–6 h |
| 6 | Correzioni emerse e nuovo giro solo sui desktop toccati; revisione finale | P, R, M | misto | 2–4 h |
| 7 | 8 macchine pulite con il pacchetto finale per le prove a mano | M1–M4 | preparazione parallela | 1 h |
| 8 | **Prove a mano del proprietario** sugli 8 desktop (una macchina alla volta) | proprietario | in fila | 2–3 h sue |
| 9 | Chiusura: registro dei problemi, manuali (4) con la nota sulla lingua, numero di versione, pacchetti definitivi | P1–P2 manuali, R1 revisione, M1–M2 costruzione | parallelo | 1–2 h |
| 10 | Pubblicazione (sito, GitHub, commit) | io | **solo su ordine del proprietario** | 1 h |

Le fasi 0 e 1 (misure che non richiedono il pacchetto) e l'inizio della 2 si sovrappongono: i programmatori
cominciano a portare il codice mentre i meccanici costruiscono il banco.

**Tempo totale stimato:** 14–20 ore di lavoro continuo fino alle macchine pronte per le prove a mano (fase 7);
poi le prove del proprietario e la chiusura. Partendo stasera: macchine pronte domani nel pomeriggio.
Il collo di bottiglia è la fase 5b (una sola Radeon): dieci agenti accorciano tutto il resto, non quella.

## 5. File che si toccano

- `debian13/src/child.c`, `session.c`, `input.c`; lo stesso in `ubuntu26.04/src/`.
- `debian13/docs/REGISTRO-problemi.md` e `ubuntu26.04/docs/REGISTRO-problemi.md` (voci nuove in coda).
- Manuali (`manuals/sources/`) delle due distro: una frase sulla lingua della sessione; numero di versione.
- Prove (`prove/`): un controllo nuovo «lingua della sessione» e uno «primo clic dopo l'accesso», uguali nelle tre
  cartelle.
- Nessun file cancellato o spostato. Nessun commit senza ordine.

## 6. Rischi

- **La lingua può toccare ogni sessione.** Un valore sbagliato nell'ambiente può impedire l'avvio dei programmi
  (successe in passato con una lingua ereditata male). Cura: il valore è filtrato e, se la lingua non esiste sulla
  macchina, si torna a quella neutra di oggi; prova apposita con una lingua inesistente.
- **Debian 13 ha un GNOME più vecchio.** Il difetto del clic potrebbe non esserci: la correzione è innocua, ma si
  verifica (fase 1). Se non c'è, entra comunque per avere lo stesso codice.
- **KDE su Ubuntu gira dentro labwc**, diverso da Fedora: lingua e formati vanno provati lì a parte.
- **Banco da ricostruire da zero**, e per Debian mai fatto prima su macchine virtuali con la Radeon: è la voce
  più incerta della stima (può costare mezza giornata in più).
- **Aggiornamento di macchine già in uso.** La 1.0.2 si installa sopra la 1.0.1 con le sessioni aperte: va
  provato che le sessioni vive sopravvivano e che solo le nuove prendano la lingua giusta.
- **Formati diversi dalla lingua** (per esempio testi in inglese e date all'italiana): su Fedora è stato provato un
  solo caso; qui si prova su entrambe le distro.

## 7. Criteri di completamento

1. Su ciascuno degli 8 desktop: utente con lingua scelta nelle Impostazioni ⇒ sessione remota in quella lingua,
   uguale all'accesso locale dello stesso utente; utente senza scelta ⇒ lingua del sistema; lingua inesistente ⇒
   il desktop parte comunque. Desktop visto realmente in italiano almeno su un desktop per distro.
2. Su GNOME di entrambe: il primo clic e il primo tocco da telefono dopo l'accesso cadono nel punto giusto,
   dieci volte su dieci.
3. Giro automatico (ampiezza secondo P3) senza fallimenti nuovi rispetto alla 1.0.1; i fallimenti già noti sono
   elencati uno per uno.
4. Installazione, aggiornamento dalla 1.0.1 e rimozione pulita provati su entrambe.
5. Revisore: APPROVATO su entrambe.
6. Prove a mano del proprietario riuscite sugli 8 desktop.
7. Confronto finale: per lingua, formati, percorsi e primo clic, Debian, Ubuntu e Fedora danno lo stesso risultato.

## 8. Che cosa non è ancora noto

- Se il codice di Fedora si porta davvero senza adattamenti (lo dirà la fase 1).
- Come si comportano lightdm e sddm con la lingua scelta dall'utente: su Fedora è stato provato solo con gdm.
- Lo stato delle prove automatiche esistenti su macchine virtuali Debian (finora usate su Ubuntu e Fedora).
