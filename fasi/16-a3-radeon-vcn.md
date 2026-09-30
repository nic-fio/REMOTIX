# A3 — La Radeon rallenta la codifica a gruppi di 5 fotogrammi (dossier per gli sviluppatori del driver)

⚠ Le misure di prestazione sono state tolte con la fase 18 (cambio di architettura: i numeri non valgono più); restano in git. Decisione dell'utente del 30 set 2026.

> Stato: **aperto, fuori dall'ambito di REMOTIX** — decisione dell'utente del 29 set 2026
> («è fuori dal nostro ambito»; strada 2: documentare e segnalare, non aggirare).
> Contesto nella fase: `fasi/16-stress-e-capacita.md`, «Anomalia A3».

⚠ **Questo dossier era fatto quasi solo di misure**, prese con la codifica di allora (FFmpeg,
`h264_vaapi` su radeonsi): tempi per fotogramma, gruppi, confronti con la Intel, esperimenti, e la
bozza del rapporto per Mesa in inglese. Con la fase 18 quella catena non esiste più, e i numeri non
descrivono il prodotto. ⇒ Il dossier intero, com'era, si rilegge con
`git show 3965f23:fasi/16-a3-radeon-vcn.md`.

## Che cosa resta

- **Il fenomeno, in una riga**: sulla **AMD Radeon RX 6800** (navi21, VCN 3.0, radeonsi) la codifica
  H.264 in hardware rallentava, per un contesto di codifica alla volta, a **gruppi di esattamente
  5 fotogrammi consecutivi**; sulla Intel lo stesso lavoro non lo faceva mai.
- **Le cause nostre erano state escluse una per una con misure** (frequenza della scheda, contesa
  sugli shader, attesa della barriera del DMA-BUF, conversione EFC, riciclo dei buffer, chiavi e
  dimensione dei fotogrammi, versione di Mesa fino alla 26.1.6): il rallentamento stava **dentro la
  chiamata di codifica del VCN**.
- **La decisione**: si documenta e si segnala, non si aggira (`DECISIONI.md` §9.5). Il rapporto al
  driver è un progetto dell'utente, fuori da REMOTIX.
- ⏳ **Da rifare con la catena della fase 18** (libva diretta, senza FFmpeg): se il fenomeno c'è
  ancora, lo si misura di nuovo lì, e la riproduzione minima in C con libva — che il dossier già
  proponeva — diventa la strada naturale, perché è la stessa catena del prodotto.
