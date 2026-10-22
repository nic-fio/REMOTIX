# REMOTIX 1.5 — passo 0 completato (22 ott 2026)

- Ripartenza da `v1.0.0` su server pulito (192.168.0.2, /media/REMOTIX-15): repo in `repo/`, podman su disco,
  `/media/REMOTIX` → `/media/REMOTIX-15`. Ripristino dopo riavvio: `fondamenta/banco/provision-15.sh`
  (pacchetti, podman, audio utente). Prodotto per i box: `benches/11-boxes/11-assemble-product.sh`.
- La suite 15 della 1.0 non era mai stata eseguita dopo la traduzione in inglese (10-11 ott). C'erano ~90 nomi
  tradotti a metà (verbi, variabili, segnaposti, chiavi JS/JSON, id CSS) e difetti dell'ambiente nuovo
  (wlr-randr, audio dell'host, labwc nel box KDE, porta delle scene). Strumenti nuovi:
  `fondamenta/banco/lint-names.sh`, `fondamenta/banco/lint-format.py`.
- Giri della suite: 212 → 290 → 580 → 687 → **702/704 PASS** (giro 5). Unico aperto: F-011 gnome/chrome,
  riga verde sul bordo con Chrome 156 (WebGL). Il prodotto codifica e decodifica bene: la cura va nella pagina
  (punto di prodotto per la 1.5, da decidere).
- Nessuna modifica a `src/`. Prossimo: passo 1, il banco di prestazioni (3K, fino a 8 utenti) validato sulla 1.0.
