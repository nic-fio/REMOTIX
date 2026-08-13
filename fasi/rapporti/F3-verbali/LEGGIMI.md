# I verbali dei cinque giri dell'anello — 13 agosto 2026, notte

⛔ **Stavano su `/tmp`, cioè su una tmpfs**: un riavvio li avrebbe cancellati, e con loro **la
prova del numero su cui la fase 3 si chiude**. Sono stati portati qui e compressi (12 M → 1,8 M).

⭐ **Non si possono rifare**: i giri sono finiti, le macchine sono state spente e riaccese, e il
prodotto è cambiato nel frattempo. ⇒ *Una scena che si può solo rifare non è una scena che si può
**rivedere**.*

| verbale | che cosa contiene |
|---|---|
| `verbale-E-C-software-av1` | **C** — AV1 in software, la linea di partenza (**71,86 ms**) |
| `verbale-E2-A-software-hevc` | **A** — HEVC in software (**109,77**): isola **il codec** |
| `verbale-E2-B-hardware-hevc` | **B** — HEVC in hardware sulla **copia** (**73,67**) ⚠ P1 **rosso** |
| `verbale-E-B-hardware-stessapagina` | il giro che ha smentito *«`renderD128` aperto ⇒ hardware»* |
| ⭐ `verbale-E3-deposito-hw-5punti` | **D** — il numero della fase: **78,115 ms**, albero del **deposito**, P1 **verde**, cinque punti di ritardo |

Si leggono con `zcat <file>.gz | python3 -m json.tool | less`.
