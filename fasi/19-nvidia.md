# Fase 19 — La codifica sempre sulla scheda: Vulkan per primo

*Aperta il **1 ottobre 2026** (`DECISIONI.md` §10.27). Requisito dell'utente: su una macchina con una scheda
capace di codificare, REMOTIX codifica **sulla scheda**, NVIDIA compresa. Oggi su NVIDIA si ripiega sul
processore (OpenH264).*

## 1. La strada (decisa il 1 ott, `DECISIONI.md` §10.27)

Si sceglie **per capacità**, all'avvio, non per marca:

| ordine | strada | oggi la usano |
|---|---|---|
| 1 | **Vulkan Video** (H.264 per Firefox, HEVC per Chrome) | AMD (RADV, `[M]` Mesa 25.0.7), NVIDIA (driver proprietario) |
| 2 | **VA-API** (`src/vadiretta.c`, com'è oggi) | Intel integrata e Arc (in Vulkan solo sperimentale, `[M]` Mesa 26.2.3) |
| — | ⛔ niente processore | senza scheda capace REMOTIX non si installa |

## 2. Il lavoro
1. La strada Vulkan (codifica H.264 e HEVC, copia zero da dmabuf, conversione dei colori sulla scheda), provata
   sulla Radeon contro VA-API: flusso dello stesso tipo, qualità e tempi non peggiori.
2. Via il ripiego software (`src/ripiego.c`, `src/colori709.c` se non serve più alla strada dalla memoria,
   OpenH264, SVT-AV1) dal prodotto, dai pacchetti, dal catalogo e dal motore dell'installatore; il controllo
   preliminare rifiuta senza una scheda capace, con la ragione.
3. **La rete anti-regressione** (parola dell'utente, 1 ott: *«bisognerà rivedere tutti i 4 DE per evitare che uno
   di loro smetta di funzionare»*): la suite completa della fase 15 gira **due volte** sulle 4 scatole (GNOME, KDE,
   XFCE, LXQt), coi browser veri in 4K — **Intel = VA-API** (niente deve rompersi di ciò che oggi è verde) e
   **Radeon = Vulkan** (la scheda passata alle scatole come nella fase 16, `--scheda amd`). Un desktop è a posto
   solo se è verde in tutti e due i giri. T10 ridotto al rifiuto pulito nelle VM; le prove complete
   dell'installatore nei contenitori con la scheda vera.
4. ❓ NVIDIA: serve una scheda vera (nel server, o macchina in affitto).

## 3. Il registro delle modifiche — per il manuale tecnico

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|

## 4-bis. La chiusura delle prove di funzionalità

Parola dell'utente (1 ott 2026): *«prima di ritenere chiusi i test di funzionalità voglio verificare di persona che
tutto sia ok»*. ⇒ Tre cancelli, in ordine: (1) la suite automatica verde in tutti e due i giri (Intel = VA-API,
Radeon = Vulkan); (2) Android sul telefono dell'utente (§5); (3) **la prova a mano dell'utente** sulle scatole
(GNOME e KDE sulla Intel, XFCE e LXQt sulla Radeon, utente `nictest`, porte 8511-8514), a server fermo. Solo dopo
il terzo la fase 19 si dichiara chiusa e il ramo `fase-19` entra in `fase-10-cure`.

## 5. Android: il telefono vero, comandato da qui

⭐ **1 ott 2026, parola dell'utente: «ti lancio l'app e il telefono è tuo»** — grazie a **Phonestra** (progetto
dell'utente) il suo telefono (Samsung S23+, Android 16, Chrome 154) è raggiungibile via adb senza fili con la
chiave già autorizzata da Phonestra: `[M]` collegamento riuscito, Chrome comandabile per intero col protocollo
DevTools (`adb forward … localabstract:chrome_devtools_remote`), tocchi veri con `adb shell input`. ⇒ Le prove
della tabella qui sotto si fanno **automatiche**, sul telefono vero, a ogni giro. Il collegamento resta sul
portatile e arriva alla suite sul server con un tunnel ssh: la chiave del telefono non lascia mai il portatile.
⛔ Solo Chrome verso le scatole; mai durante una chiamata (`dumpsys telephony.registry`, una riga per SIM); il
telefono si lascia come lo si è trovato.

*(La tabella era nata come scheda a mano dell'utente; resta come elenco delle prove.)*

### 5.1 Le prove


*Decisione dell'utente (1 ott 2026): «per android i test funzionali li faccio io». Col suo telefono, **Chrome**
(mai Firefox Android, `DECISIONI.md` §7.18), in rete locale verso le scatole del server (`https://192.168.0.2:8511`
GNOME · `8512` KDE · `8513` XFCE · `8514` LXQt), utente `nictest`. Ogni riga si segna **PASS / FAIL / BLOCKED** con
data, desktop, scheda (Intel o Radeon) e, se FAIL, una frase su cosa si è visto; entra nel registro della suite
con esecutore «utente».*

**Giro pieno**: GNOME, con la scatola sulla **Radeon** (la strada nuova, Vulkan). **Giro corto** (righe 1, 2, 6, 9):
KDE, XFCE, LXQt.

| # | prova (rif. fase 15) | cosa fare | cosa deve succedere |
|---|---|---|---|
| 1 | F-001, F-002 accesso e prima immagine | aprire l'indirizzo, accettare il certificato, entrare | modulo, poi il desktop in vista entro pochi secondi, non nero né a pezzi |
| 2 | F-031 tocco | tocco su un'icona; tocco e mezzo per trascinare una finestra | il clic arriva dove si tocca; la finestra segue il dito |
| 3 | F-007, F-009 tastiera | aprire un editor, scrivere «Prova è à @ €», Invio, cancellare | i caratteri giusti, accenti compresi |
| 4 | F-014, F-015 appunti | copiare un testo sul telefono e incollarlo nell'editor; e al contrario | il testo passa nei due versi |
| 5 | F-012, F-013 audio e video | aprire un video nel desktop remoto | immagine continua e suono sul telefono |
| 6 | F-003 aggiornamento | aprire, spostare e chiudere una finestra | lo schermo segue senza resti né ritardi visibili |
| 7 | F-018 riattacco a misura diversa | ruotare il telefono (verticale ↔ orizzontale), poi ricaricare la pagina | la tela prende la misura nuova (su KDE: resta e si riscala, eccezione) |
| 8 | F-016, F-017, F-020 stacco e rientro | chiudere Chrome di colpo, riaprirlo, rientrare | la sessione c'è ancora, con l'editor e il testo scritto |
| 9 | F-019 rete | spegnere il Wi-Fi per 20 secondi, riaccenderlo, rientrare | si rientra e la sessione c'è |
| 10 | F-021 Esci | «Esci» dal menu | la sessione finisce, la pagina torna al modulo |
