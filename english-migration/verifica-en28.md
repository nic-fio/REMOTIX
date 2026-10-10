# Verifica en-28 — revisore incaricato di smentire

Affermazione sotto esame: «a parte gli identificatori e i dati sul filo riservati al programma di rinomina,
il codice di REMOTIX è inglese, e ogni banco trova ancora il testo del prodotto che cerca».
Albero: `full-english` fusa, fd405c9. Ambito: src/ (con pagina.html), installatore/ (senza vendor), packaging/, banchi/
(senza dati .jsonl/.json/.txt/.log/.csv, senza banchi/prodotto/*.html e banchi/11-scatole/pacchetti/).

**Verdetto: smentita in parte.** src/, installatore/ e packaging/ sono quasi del tutto inglesi; restano 7 frasi
che citano testo italiano che non esiste più. Nei banchi restano circa 60 verdetti in italiano maiuscolo (non elencati
in residui.md, e tradotti in un banco ma non in un altro) e circa 25 frasi italiane minuscole. Una ricerca dei banchi
non trova più niente nel prodotto (16-salita, OpenH264).

## 1. Italiano rimasto

Metodo: un tokenizzatore per linguaggio (C/Go/JS, Python, shell con heredoc, HTML con script/style/testo, conf) che separa
commenti, stringhe e codice. Tre rilevatori: parole vuote italiane (pesate, togliendo backtick, `$VAR`, `%s`, «…»),
lettere accentate e apostrofi (`e'`, `l'`), parole non inglesi (dizionario hunspell en_US) che finiscono in vocale, e
frasi italiane in MAIUSCOLO. Poi la classificazione è stata fatta a mano.

File esaminati: src 99, installatore 67, packaging 44, banchi 348.

| cartella | segnalazioni | identificatori nel codice | commenti/stringhe esaminati | difetti |
|---|---|---|---|---|
| src | 44 | 14 | 30 | **7** (+1 gemello in banchi/rcp) |
| installatore | 30 | 2 | 28 | 0 |
| packaging | 1 | 0 | 1 | 0 |
| banchi | 2661 | 128 | 278 (+2255 nei rapporti) | **circa 85** (60 maiuscoli + 25 minuscoli) |

Quel che va bene:
- `banchi/15-suite/rapporto-giro*.html` (8 file, 2255 righe): sono uscite storiche delle suite, cioè dati.
- Intenzionali: `gestore.go:416,456` (uscita di dnf/zypper), `inglese_test.go`/`lingua_test.go`, `t9-r36.sh:105`
  (`--lingua it`), i caratteri di prova accentati (tastiera.h/.c, kwin.c, 04-b25, 15-f009, 06-b34).
- Riservati al programma (residui.md): `figlio.c:1779` e `disinstalla_test.go:27` «REMOTIX alla prima connessione»;
  il token «nessuno» (`strade.go`, `certifica_test.go`, `figlio.c:5893`); `GEMELLO=nessuno`; NOMI_STATO; linea morta,
  causa=silenzio/stallo; diario audio della pagina (`16-attore.py:416-420`); stati del catalogo della pagina
  (`consegnata-E-RISERVATA…`).
- Citazione storica con traduzione accanto: `pagina.c:356`.
- Le marche dei guasti innestati (`REMOTIX B3`, `REMOTIX B11 GUASTO`, `GUASTO INNESTATO`) e i token di stato dei
  banchi (`S7: PRONTO`, `B33R: PRONTO`, `"tipo":"PRONTA"`, `"esito":"rosso"`, `NIENTE`, `ANCORA/MORTA`, `messo`).

### Difetti in src/
1. `src/rcp.c:4633` (riga di log, con il gemello `banchi/rcp/rcp.c:4633`): «rilascio al distacco: N fra tasti e
   pulsanti». Quella riga non esiste più: oggi è «RELEASE ON DETACH (%s): %d keys and buttons» (`rcp.c:4638`). È in
   residui.md ma è ancora aperto.
2. `src/rcp.c:6736` (commento, con gemello): «CIAO senza versione». Il prodotto oggi scrive «CIAO without version»
   (`rcp.c:2077`).
3. `src/webtransport.c:4113,4122-4123` (commento): `abbandonati per soglia`, `non accettati per credito mancato`. Il
   conto oggi dice «abandoned by threshold» (`webtransport.c:8184`).
4. `src/input.c:1404` (commento): «NON PARTE». Nessuna riga di log la scrive più.
5. `src/sessione.c:256` (commento): «LETTURA IGNOTA». Oggi è UNKNOWN READING.
6. `src/pagina.html:219` (commento): `ATTACCA: tela 1920×1080, vista 2560×857`. Oggi è «canvas … view».
7. `src/comando.c:97` (risposta sul socket di sblocco, con il gemello innestato in `banchi/01-b3-rcp-innesta.py:1254`):
   «NON-CAPITO riga vuota». `NON-CAPITO` è un token; «riga vuota» invece è una frase per una persona.

Non è un difetto ma manca in residui.md: `src/costruzione/costruisci-deb.sh:127-155`, le etichette dei controlli
`R13 opzioni-di-banco-nell-unita`, `R14 file-del-banco`, `R23 riproducibile` e `SI/NO` (letti con `grep ' NO'`).
Borderline: `installatore/motore/ripresa_test.go:316` «# messa a mano» (dato di prova).

### Difetti in banchi/ — verdetti in italiano maiuscolo (59 righe, non in residui.md)
Il problema è l'incoerenza: la stessa frase è tradotta in un banco e lasciata in un altro.
- «NIENTE DA GIUDICARE» resta in `07-b64-rete.py:607,721,772`, `07-b64-orecchio.py:108,231,359,365`,
  `07-b65-datagram.py:386`, `07-b42-giudice.py:41` e `09-b77-audio-riordino.py:637,659,665,1494`. Altrove è già
  diventata «NOTHING TO JUDGE»: `02-cattura-lancia.sh`, `02-filo-validatore.py`, `01-b4-validatore.py` e un'altra riga
  di `07-b42`.
- «NON GIUDICO»: `09-b81-linea-morta.py:681,802,809,865,1339,1827,2052`, `09-b76-rete-cattiva.py:577,648`,
  `09-b70-ritmo.py:527`, `07-b64-orecchio.py:112,286` («SILENZIO O QUASI — NON GIUDICO»). Viene confrontato solo in
  `09-b81:1827` (autoprova).
- «NON HO NIENTE DA GIUDICARE»: `09-b70-ritmo.py:519,608,622,629,1185,1986,2154`, `09-b76:2032`.
- «NON HO LETTO IL REGISTRO» e «NON HO LETTO any startup line» (mezza tradotta): `09-b81:525,601,888,2145`.
- `09-b79-cure.py:1271` «IL BRACCIO NON E' IN VIGORE» e `:1283` «LA REGOLA INSTALLATA NON E' QUELLA CHIESTA».
- `07-b42-giudice.py:122` «NON GIUDICABILE QUI»; `09-b84-audio-silenzio.py:845` «NON GIUDICATO».
- «NON PROVATO»: `18-scheda/18-decodifica-chrome.sh:14,55`, `19-vulkan/19-decodifica-chrome.sh:14,55`.
- Famiglia 02-cattura: «BYTE NON TORNANO», «IL BUFFER NON E' CAMBIATO», «FOTOGRAMMA NERO», «MISURA DIVERSA DA QUELLA
  CHIESTA», «QUALCOSA SI MUOVEVA E NON L'ABBIAMO DICHIARATO», «TIPO DICHIARATO». Sono in `02-cattura-giudica.py:185,269,
  424,428,536,561,607,695,762`, `02-cattura-certifica.sh:55,56,261,262` e `02-cattura-lancia.sh:100`. La tabella dei
  verdetti attesi le confronta, quindi vanno trattate come token e aggiunte a residui.md.
- `01-b0-terreno.sh:258` «DELLE COPIE» (commento).

### Difetti in banchi/ — frasi italiane minuscole
- `01-b7-congedo.py:1011-1012` «il banco B7 chiude, come farebbe l'utente» e `:1165-1166` «controllo dello stato
  iniziale di B7». Sono dettagli del CONGEDO che il banco manda sul filo, e finiscono nel log del server.
- `01-b8-cronometro.py`:
  - `:394-395` (commento) cita la pagina in italiano («I tentativi di accesso da questo indirizzo sono esauriti…»);
  - `:731-732` e `:755` (commenti) citano «PAM ha risposto: ammesso…»;
  - `:818` (stringa) «PAM ha risposto: ammesso»;
  - `:706` valori JSON «non dichiarato» e «ignota».
- `16-stress/16-salita.py:802` «rifaccio la scatola», `:850` «entrano gli utenti» (fasi mostrate), `:1120` «guardia
  dell'ospite», `:1167` «browser fuori dalla Intel» (eventi).
- `02-codifica-lancia.sh:166` SCENA «immagine nota … range limitato, ferma».
- `09-b70-ritmo.py:1960` esito «senza traccia».
- `09-b81-linea-morta.py:625,1789` «NON e' scattato»: il jsonl b04 dice che è tradotto, il file no.
- `11-scatole/11-gancio.sh:1414` maglia «C7($d) si stacca soltanto».
- `11-c7-si-chiude-e-non-resta-niente.py:563,946` «_schede in tutto».
- `11-c21-sul-bordo-la-forma-cambia.py:495-497` «e-resize di Adwaita», «clessidra piena», «mano», accanto a «text bar»
  in inglese.
- `11-c14-non-si-disturbano.py:435,601` «di un altro» (e «mia»).
- `17-t2/t2-misura.py:129` «padre %s figlio %s\ninizio»: il jsonl b17 dice che è tradotto, il file no.
- `01-b8-lancia.sh:547,624` «prima vita»/«seconda vita»: anche qui il jsonl dice tradotto e il file no. È un'etichetta,
  quindi è borderline.
- `19-vulkan/19-confronto.c:338,344,369` e `18-scheda/18-confronto.c:264` `{"esito":"non aperto"}`;
  `18-scheda/18-confronto.sh:66` e `19-vulkan/19-confronto.sh:66` `{"esito":"nessuna riga"}`. Sono valori, quindi
  borderline.
- `01-b0-terreno.sh:250-253` (commento) etichette «guasti di B12 nel codec / in rcp.c / …».

## 2. Quel che i banchi cercano, confrontato col prodotto

Ho estratto 1292 ricerche:
- Python: `in`/`not in`, `startswith`, `endswith`, `find`, `count`, `re.search`, `re.match`, `re.compile`, `re.findall`;
- shell: `grep`, `grep -E`, `grep -F`, `-e`;
- C: `strstr`;
- JS: `.includes` e `.indexOf`.

Le ho confrontate con i letterali del prodotto (stringhe C concatenate, Go, JS, HTML, più gli script) anche tramite
`%s`/`%d`. In più ho controllato le 269 ancore usate per innestare guasti (`.replace`, `re.sub`, `sed s|…|`): nessuna
manca nel prodotto.

Esito:

| esito | ricerche |
|---|---|
| trovate nel prodotto | 675 |
| troppo corte per giudicare | 117 |
| testo di un altro banco o del banco stesso | 172 |
| presenti solo in un commento | 62, tutte token di sistema o di banco (nessuna è una frase del prodotto) |
| da rivedere a mano | 266 |

Le 266 da rivedere a mano sono quasi tutte uscite di strumenti esterni (tc/netem, ffmpeg, dumpsys, journalctl, apt,
`/proc`), uscite dei banchi stessi, marche dei guasti innestati, oppure falsi negativi. I falsi negativi vengono dal
prefisso del registro (`figlio  [x]`, `cattura [x]`) e dai `%s`. Ho controllato uno per uno quelli del prodotto:
- negotiated format (`cattura.c:712`);
- loop … frames delivered (`figlio.c:9362`);
- ZERO MONITORS;
- failed attempt from;
- rete-quic;
- route %s;
- linea-morta;
- Admitted, … resumed session (`pagina.html:6113`).

Ricerche che non trovano niente nel prodotto attuale:
1. **`banchi/16-stress/16-salita.py:370` e `:475`** cercano `HEVC: .*H.264: scheda [^,]*, software OpenH264 [^ ]*`,
   «H.264: scheda no (» e «software OpenH264 si'». C'è solo la forma italiana, senza gemello inglese. Il prodotto oggi
   scrive «card %s (route requested «%s») — HEVC: … · H.264: …» (`figlio.c:5758`), e da §10.27 non ha più OpenH264.
   Risultato: con `--senza-scheda` il banco risponde sempre «the server does not declare H.264 encoding in software».
2. `banchi/02-figlio-prova.py:625` cerca «NON entra in deposito». Era un difetto già prima della traduzione: la riga è
   sparita dal prodotto con il commit 92105b5.
3. `banchi/17-t8/t8-vm.sh:106` cerca «Engine VERIFIED» e «install.sh: »; `17-t9/t9-vm.sh:118` cerca «install.sh:
   uscita» (che per giunta è in italiano). Sono banchi obsoleti: install.sh non c'è più (§10.36).
4. Non è il prodotto: `11-c16-i-documenti-non-mentono.py:123` cerca «DA QUI SI RIPRENDE» in README.md. Oggi lo trova,
   perché il documento è ancora in italiano; smetterà di trovarlo quando i documenti saranno tradotti.

Doppie forme verificate (il gemello inglese esiste nel prodotto):
- `16-classifica.py:202-222`: sessione finita, palco, figlio, sfratto, rifiuto, OURS, STRETCH, producer;
- `16-attore.py:1011` Ammesso/Admitted;
- `16-salita.py:491` tetto AMMINISTRATIVO/ADMINISTRATIVE session cap;
- `01-b8-cronometro.py:1117` (innesto B3), `15-f030:287` (xfconf), `17-t8:115` e `17-t3-prova:78` (apt).

Ho anche incrociato le ricerche con i «prima» dei jsonl: nessun lettore è rimasto sul testo vecchio senza la forma nuova
accanto.

Limiti: non coprono le ricerche fatte con stringhe raccolte in liste o costanti (`any(m in riga for m in MARCHE)`) né il
Python dentro gli heredoc. Quelle sono controllate solo in parte.

## 3. Coerenza dei jsonl

38 file, 20.914 righe. Per ogni riga: il «dopo» deve stare nel file indicato e il «prima» non deve più esserci.
Per confrontare ho tolto la concatenazione delle stringhe, gli spazi e le specifiche di formato `{x:…}` delle f-string.
Ho anche corretto i percorsi abbreviati, come «fumo.sh» o «(C innestato)».

| esito | righe |
|---|---|
| coerenti | 20.798 |
| «dopo» assente | 88 |
| «prima» ancora presente | 28 |

Le 88 con il «dopo» assente si dividono così:
- circa 60 sono righe riassuntive, non letterali: contengono «…» o « / », oppure descrizioni come «testi di --help».
  Riguardano `banchi/sonda/*`, `banchi/prodotto/resto.sh`, 13-w1, 14-f1, 16-lavori, 12-c20 e 10-f1.
- le altre sono testi riscritti più tardi in modo coerente. Esempi: «FALLBACK DECLARED» diventato «DECLARED FALLBACK»
  in input.c, tastiera.c e wlr_input.c, e letto così da 04-b25; «errore di protocollo» tolto dalla pagina.
- nessuna lascia un lettore senza testo.

Le 28 con il «prima» ancora presente: quelle vere sono `t2-misura.py:129`, `09-b81:625,1789`, `01-b8-lancia.sh:547,624`,
`01-b8-cronometro.py:731,755,818`, `rcp.c:6736`, `sessione.c:256` e `pagina.html:219`. Le restanti sono frammenti che
compaiono dentro token, per esempio «consegnati» e «fuori» del diario, `#define V_CHIAVE`, il token `VERDE` di
19-nv-macchina, «PAM ha risposto» in commento.

## Cosa fare
- In src: tradurre le 7 citazioni. Per la 1 e la 2 bisogna ricopiare i gemelli in banchi/rcp/.
- Nei banchi: decidere una volta sola i verdetti maiuscoli. O li si traduce dappertutto, o li si mette in residui.md come
  token del programma. Prima di tutto va allineato «NIENTE DA GIUDICARE».
- Aggiungere a residui.md le etichette R13/R14/R23 di costruisci-deb.sh.
- Correggere 16-salita: le ricerche OpenH264 vanno portate alla riga inglese «card … — HEVC: … · H.264: …», oppure tolte
  se `--senza-scheda` non serve più.
- Togliere o aggiornare la ricerca di 02-figlio-prova:625 e i banchi t8/t9 che usano ancora install.sh.
- Correggere le 4 righe dei jsonl che dichiarano una traduzione mai fatta: t2-misura.py:129, 09-b81:625,
  01-b8-lancia.sh:547 e :624.
