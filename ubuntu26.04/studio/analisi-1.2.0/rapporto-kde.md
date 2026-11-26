# Rapporto di analisi KDE (Kubuntu 26.04: Plasma/KWin 6.6.x, sddm 0.21) — REMOTIX 1.2.0 per Ubuntu 26.04

Lavoro di SOLA LETTURA del 26 nov 2026: `diff` reali fra `ubuntu26.04/src`, `fedora45/src`, `debian13/src` (stato dei file di oggi), più lettura dei documenti
citati nell'incarico. Nessuna VM accesa, nessun server toccato, nessuna compilazione. Nessuna misura nuova: ogni «misurato» qui sotto è di un documento
già esistente, che cito.
Convenzione: **[V]** = verificato leggendo il codice di oggi o un documento di misura (citato); **[D]** = dedotto; **«non verificato»** = non so.
Righe di codice: `ubuntu26.04/src` salvo diverso avviso («Fed» = `fedora45/src`, «Deb» = `debian13/src`).

## 0. Riepilogo in una pagina

La sorpresa principale: **Ubuntu è già più avanti di Debian prima del lavoro di Debian**, e Debian ha poi ripreso da Ubuntu quasi tutto il KDE. Il confronto
file per file oggi dà questo [V]:

| File | Ubuntu ↔ Debian (righe diverse) | Ubuntu ↔ Fedora | Che cosa dice per KDE |
|---|---|---|---|
| `capture.c`, `capture.h`, `kdehost.h` | **0** | `capture.*` 0; `kdehost.h` 57 (D) | fotogramma perso (U5): già in Ubuntu |
| `kwin.c` | **31** (solo 3 testi B3, 2 commenti, 3 punti del labwc) | 525 (B3 + `kwin_output_resize` ≈500 righe = classe D) | sidecar ScreenSaver (U6) e `kwin_poke` già in Ubuntu |
| `session.c` | 1283 (quasi tutto non KDE) | 137 | KDE: solo A6, A7 e la lingua separano Ubuntu da Fedora |
| `child.c` | 222 | 345 | KDE: tutto D (KWin da solo) salvo lingua/PATH (comuni) |

| Voce | Verdetto per Kubuntu |
|---|---|
| K1 = A6, forzata su `graphical-session.target` | PORTARE COSÌ (3 righe + commenti). **Rischio nuovo, specifico di Ubuntu 6.6.7**: systemd ha già rifiutato quello stop («transaction is destructive») nei primi ~25 s di vita del desktop (studio 12-verifiche-kde D2, giro2-kde K2); la forzata non ritenta. Da provare. |
| K2 = A7, attesa di 5 s | PORTARE COSÌ (~10 righe, come Fedora e Debian). Cambia il comportamento visibile: va approvato anche per Kubuntu. |
| K3 = E2, `force_guard_on` | già come in Fedora (i riazzeramenti aggiunti ci sono già: `child.c:10529`, `10562`). Niente da fare, annotare il limite. |
| K4 = U5/U6/U7 (fotogramma perso, Ctrl+Alt+Canc, Log Out) | **GIÀ PRESENTI in Ubuntu** (anzi, è da lì che Debian le ha prese). Niente da portare; da riprovare nel giro 1.2.0. |
| K5 = B3/A9, testi «reinstalla il pacchetto» e residui «Fedora/Arch» | ADATTARE (testo): copiare il testo già scritto per Debian. Piccolo. |
| K6 = lingua dell'utente (A1/A2) su KDE | PORTARE, ma **con in più il pezzo di Debian `manager_set_locale()`**: senza, su KDE dentro labwc la lingua non arriva a Plasma (misurato su Debian, strada identica a Ubuntu). Cambio visibile grande. |
| K7 = PATH (A3) su KDE | ADATTARE: Ubuntu prende già il PATH da PAM; manca solo il ripiego con `~/.local/bin`. Piccolo. |
| K8 = controllo dell'aggancio PAM a ogni avvio (B1) su sddm | PORTARE da Debian (`remotix-pam-hook check`, script di 20 righe + 1 riga di `remotix.service`). Su Kubuntu sddm non trattiene nessuno: l'aggancio è l'unica difesa. |
| K9 = AppArmor: `org.kde.remotix.desktop` (F10 di Debian) | PORTARE (1 riga nel profilo). Trovata su Debian; il codice che legge il file è lo stesso. |
| K10 = prove KDE (`prove/`): P7/P8, `check-kde-exit.py`, `check-apparmor.py`, `hold.py`, `autologin-sddm.sh` | PORTARE da DEBIAN (non da Fedora) e adattare. Attenzione: `kwrite` NON c'è in Kubuntu di serie (ha dovuto installarlo l'agente del 18 nov). |
| K11 = D1–D4 (KWin da solo, cambio di risoluzione a caldo, plasmalogin) | NON PORTARE. Su 6.6.x manca (secondo lo studio di Fedora) `kde_output_management_v2` ≥ 22: **non misurato su 6.6.7**. Vedi §9: la misura si fa in 1 minuto e può cambiare il quadro. |
| K12 = regola polkit fwupd (A8) | PORTARE così com'è (1 riga); effetto su Kubuntu: non verificato. Comune a tutti i desktop. |

Da tenere a mente per tutto il rapporto: Ubuntu **usa il labwc nostro** (0.9.3 + wlroots 0.19.2 modificati) solo per KDE. XFCE e LXQt usano il labwc della distribuzione
(`Recommends: labwc`). Quindi ogni voce di Fedora che «toglie il labwc» NON si porta.

---

## 1. K1 — A6: chiusura FORZATA di KDE che ferma tutto il desktop (`graphical-session.target`)

### 1.1 Che cos'è
Quando un accesso locale chiude il desktop remoto e Plasma non si chiude da solo (un programma chiede «salvare?»), la strada forzata deve fermare **tutto** il
desktop insieme. Fedora ferma `graphical-session.target` invece di `plasma-workspace.target`.

### 1.2 Fedora
- `Fed session.c:4597-4610` (`exit_kde()`): forzata = `StopUnit(SESSION_UNIT_GRAPHICAL, "fail")` (riga 4609); commento F36 4586-4596 (misura reale: su Plasma 6.8 kwin/ksmserver/plasmashell sono `PartOf=graphical-session.target`, che se ne va ~4,5 s dopo `plasma-workspace.target`: oltre i 13 s della parte root).
- `Fed session.c:5648`: messaggio della forzata con `SESSION_UNIT_GRAPHICAL`.
- `Fed session.h:120`: `#define SESSION_UNIT_GRAPHICAL "graphical-session.target"` (in Ubuntu c'è già).

### 1.3 Ubuntu oggi [V]
- `session.h:120` ha già `SESSION_UNIT_GRAPHICAL` (aggiunto per la guardia di GNOME 50, `session.c:4556`).
- `session.c:4586-4608` `exit_kde()`: la forzata ferma ancora `SESSION_UNIT_PLASMA` (riga 4598); `session.c:5626-5636` messaggio con `SESSION_UNIT_PLASMA`.
- `session.c:5162-5174, 5287-5385` `session_kde_logout_watch()`: usa già `StopUnit("graphical-session.target", mode)` (riga 5350), scritto a mano perché su Plasma 6.6.7 `plasma-shutdown` chiede proprio quello stop (`studio/giro1-kde.md:40-42`). Quindi per Ubuntu il bersaglio `graphical-session.target` è già «di casa».
- La parte root ha già l'«ultima difesa»: `rootside.c:2412-2428` (`PL_GRACE_MS 13000`, poi la parte root ferma lo scope e l'unità KDE). Identica in Fedora e Debian (`diff` = 0). Su Fedora F36 il muro SELinux la rifiutava; su Ubuntu non c'è SELinux, e AppArmor copre solo la parte di rete [D: il profilo `remotix_network` non tocca la parte root; non verificato che nessun profilo di sistema di Ubuntu la limiti].
- Guardia `inactive_unit()` per KDE: `session.c:4486-4496` guarda solo `plasma-kwin_wayland.service` e `plasma-workspace.target` (non `graphical-session.target`), identico a Fedora.

### 1.4 Debian
Portata: `Deb session.c:3858-3870` (`StopUnit(SESSION_UNIT_GRAPHICAL,"fail")`), `session.h:136-138`, messaggio a `4899`. Verdetto di Debian: portabile ma **non necessaria** su Plasma 6.3.6 (tutto fermo in 0,37 s con il vecchio bersaglio, 0,47 s con il nuovo; `debian13/studio/analisi-1.2.0/rapporto-kde.md` §1.4) perché lì `plasma-workspace.target` è `BindsTo` di `graphical-session.target`.

### 1.5 Che cosa fare su Ubuntu
**Portare così com'è**: in `exit_kde()` cambiare `SESSION_UNIT_PLASMA` in `SESSION_UNIT_GRAPHICAL` (riga 4598), aggiornare il commento (4577-4583) e il messaggio di `really_terminate()` (5635). ~10 righe in `session.c`, niente in `session.h`. **Piccolo**.

### 1.6 Rischio specifico di Ubuntu (non presente su Debian/Fedora)
- **Il rifiuto «destructive transaction».** Su Kubuntu 6.6.7, se `xdg-desktop-portal.service` ha un job di *avvio* in coda, systemd rifiuta `StopUnit("graphical-session.target","fail")` («Transaction for graphical-session.target/stop is destructive»). Misurato: stop accettato solo al tentativo 6-8, cioè fino a ~25 s dalla nascita del desktop, con RealtimeKit che non parte nel contenitore (`studio/12-verifiche-kde.md` D2 righe «T=2, T=5b»; `studio/giro2-kde.md` K2). Sulla macchina vera il portale parte in <1 s e il caso «dovrebbe non vedersi» (SUPPOSTO nel documento).
- Oggi la forzata di `exit_kde(TRUE)` **non ritenta e non usa il modo `replace`**: se viene rifiutata ritorna FALSE → «did not exit even by force» → la parte root a 13 s ferma lo scope (ultima difesa). Con A6 il bersaglio diventa quello che systemd ha già rifiutato in laboratorio; col bersaglio di oggi (`plasma-workspace.target`) non ho trovato misure di rifiuto [D: il target workspace non ha il job del portale in coda].
- Conseguenza possibile: accesso locale di un utente il cui desktop remoto è molto giovane (<~25 s) e ha un programma che non si chiude: l'accesso passa dopo 13 s dalla parte root invece che a ~5,5 s. **Non misurato su Kubuntu con la forzata del locale.**
- Cosa fare: portare A6 e **provarla con desktop giovane** (P7/P8 lanciati entro 10 s dalla nascita). Se si vede il rifiuto, la correzione naturale (copiata da `session_kde_logout_watch`) è ritentare a ogni giro e passare a `replace` dopo qualche rifiuto: ma è un cambio di codice oltre Fedora, quindi va deciso col proprietario.
- Non so se su 6.6.7 fermare `graphical-session.target` fa diventare inattivo anche `plasma-workspace.target` in tempi brevi (su 6.3.6 sì, per `BindsTo`; su 6.6.7 non ho una misura della catena). Indizio [V]: dopo lo stop accettato da `session_kde_logout_watch` «KWin sparisce ~0,4-5 s dopo» e processi/sessioni vanno a 0/0 (`12-verifiche-kde.md` D2). Serve una `systemctl --user show -p BindsTo,PartOf,StopWhenUnneeded plasma-workspace.target graphical-session.target` sulla VM Kubuntu: non verificato.

### 1.7 Come provarla
`prove/check-prelocal.py` P7/P8 su Kubuntu (vedi §10) con tempi: forzata a ~5 s, tutto fermo ~0,5 s dopo, 0 core dump, 0 righe AppArmor. Più la variante «desktop giovane». Poi **a mano dal proprietario sulla live Kubuntu** (regola F36: sempre con programmi aperti).

---

## 2. K2 — A7: la chiusura gentile aspetta 5 secondi (solo KDE, solo accesso locale)

### 2.1 Che cos'è
Plasma aspetta senza limite un programma che non si chiude (nessuno può rispondere): i 10 s erano solo un ritardo dell'accesso locale. Con l'accesso locale tenuto in PAM l'attesa è di 5 s.

### 2.2 Fedora
`Fed session.c:109-113` `#define KDE_PRELOCAL_ORDERLY_MS 5000`; `4561-4579` `wait_until_done_ms(gint64 ms)` con `wait_until_done()` che la chiama con `WAIT_EXIT_MS`; `5639`: `exit_kde(FALSE) && wait_until_done_ms(force_guard_on ? KDE_PRELOCAL_ORDERLY_MS : WAIT_EXIT_MS)`.

### 2.3 Ubuntu oggi [V]
Manca. `session.c:108` (`WAIT_EXIT_MS`), `4561` (`wait_until_done()` senza parametro), `5626` (`exit_kde(FALSE) && wait_until_done()`).

### 2.4 Debian
Portata identica: `Deb session.c:113`, `3822-3840`, `4890`. Verdetto: PORTABILE COSÌ, scelta del proprietario già presa.

### 2.5 Che cosa fare su Ubuntu
**Portare così com'è** (4 punti in `session.c`: costante, `wait_until_done_ms`, `wait_until_done` che la chiama, riga del ramo KDE). `force_guard_on` c'è già (`session.c:5536`) e viene impostata dal figlio a `child.c:11128` (`session_force_unless_orphaned(ci.a == CHILDREN_EXIT_PRELOCAL)`). **Piccolo**.
Budget di tempo della parte root: 5 s + forzata + attesa < 13 s (`PL_GRACE_MS`): su Ubuntu il margine resta largo salvo il rifiuto del §1.6 [D].
Commento di `rootside.c:2428` («WAIT_EXIT_MS (10 s...)»): resta com'è su Fedora e Debian; non è codice.

### 2.6 Cambio visibile per l'utente (da approvare per Kubuntu)
Su Kubuntu, con un accesso locale, una chiusura sana che avrebbe richiesto fra 5 e 10 s viene troncata dalla forzata: il lavoro non salvato in quel caso va perso 5 s dopo anziché 10. Già deciso per KDE il 25 nov (PIANO-1.2.0 «Che cosa ha deciso il proprietario»); su Kubuntu Plasma è 6.6.7: **non verificato che Konsole con `top` blocchi il Log Out su 6.6** (su Fedora 6.8 sì, su Debian 6.3.6 no: `rapporto-kde` di Debian §1.4). Il blocco certo è un editor con testo non salvato (K3 di `giro2-kde.md`: kwrite resta in attesa fino a 120 s, poi KWin chiude da sé).

---

## 3. K3 — E2: `force_guard_on` che «resta acceso»

- Fedora: `Fed session.c:5549-5560`; non corretto, annotato.
- Ubuntu [V]: `session.c:5536-5551`, impostata a `child.c:11128`; i due punti di chiamata in più **già riazzerano** con `session_force_unless_orphaned(false)` (`child.c:10529` rifiuto scala, `10562` watch KDE).
- Debian: `Deb session.c:4800-4811`, un solo punto di chiamata; verdetto «PORTABILE COSÌ».
- Fare: **niente**. Con A7 il valore stantio influirebbe solo sul tempo 5/10 s di una chiusura fatta dopo una chiusura PRELOCAL fallita nello stesso figlio. Annotare il limite come in Fedora.

---

## 4. K4 — Ciò che è nato su Ubuntu e che Debian ha già preso: NIENTE da portare, solo da riprovare

Tutte [V] come presenti in `ubuntu26.04/src`:
| Voce | Dove (Ubuntu) | Note |
|---|---|---|
| U5 fotogramma perso (`kwin_poke`, `capture_watch_sequence`) | `kwin.c:593`, `child.c:9062, 9737, 12241`, `capture.c/h` (identici a Debian e Fedora) | misurato su KWin 6.6.7; innocuo se non scatta (interruttore di sicurezza). Debian: 0 scatti in tre avvii su 6.3.6. |
| U6 sidecar `org.freedesktop.ScreenSaver` (Ctrl+Alt+Canc) | `kwin.c:1342, 1474-1487` + fork nella strada labwc (`kwin_nested_alive`, 1488-) | difetto vero su 6.6.7 (`12-verifiche-kde.md` A.2-A.4: ServiceUnknown ⇒ schermata di uscita non appare). Parte solo nella strada labwc: nel ripiego `--virtual` non parte (vedi §11, punto 3). |
| U7a `kwin_closed()` prima del `continue` «nessuno guarda» | `child.c:11758` | caso Kubuntu «Log Out con il browser chiuso» (`12-verifiche-kde.md` C). Debian: verificato a mano, tutto sparito in 2 s. |
| U7b watch nuovo (`org.kde.Shutdown` rilasciato + `isShuttingDown`), `bool` | `session.c:5287-5385`, `child.c:10553-10567` | su 6.6.7 serve davvero (`plasma-shutdown` non ferma mai `plasma-workspace.target`, `giro1-kde.md:42`); identico a Fedora (`diff` 0 in quella zona). |
| `really_terminate()`: «nessuna sessione» = chiusura riuscita solo se le unità sono spente | `session.c:5558-5573` | identico a Fedora. |

Che cosa serve: nel giro 1.2.0 ripassare Log Out dal menu (con browser collegato e chiuso; con kwrite non salvato) e controllare 0 processi/0 sessioni. Il «giro2-kde» del 18 nov (`unione2`) è di prima di tutto il lavoro 1.2.0.

---

## 5. K5 — B3/A9: testi «reinstalla il pacchetto» e residui «Fedora/Arch»

### 5.1 Che cosa è
Il rimedio «`apt install --reinstall remotix`» non funziona per un pacchetto installato da file (nessun archivio lo offre); su Fedora ora dice «reinstall the package from its file». I residui «Fedora and Arch… `.fedora`, `.suse`, `.arch`» sono testi vecchi.

### 5.2 Ubuntu oggi [V]
- Runtime, KDE: `kwin.c:812` (RX-KDE-001), `823` (RX-KDE-002), `840` (RX-KDE-003): «reinstall the package (apt install --reinstall remotix)».
- Runtime, non KDE ma stesso lavoro: `main.c:469-473` («on Fedora and Arch it is pam_deny… .fedora, .suse, .arch»).
- Commenti: `kwin.c:763-765` («`packaging/{debian,rpm,arch}`»), `774` («Arch»); `main.c:439, 447`; `remotix.pam:1, 6, 30-39, 60, 96` («DEBIAN 13 ONLY», Fedora/openSUSE/Arch); `ubuntu26.04/CLAUDE.md:4` («Debian 13 only»).

### 5.3 Fedora e Debian
Fedora: `kwin.c:814, 825, 842`, `main.c:472` («sudo dnf reinstall ./remotix-<version>.rpm»). Debian ha già il testo giusto per un `.deb`: `Deb kwin.c:810, 821, 838` e `main.c:468`: «reinstall the package from its file (sudo apt install --reinstall ./remotix_<version>_amd64.deb)»; commenti riscritti a `Deb kwin.c:763-764, 772`.

### 5.4 Fare
**Adattare**: copiare da Debian i tre messaggi di `kwin.c` e quello di `main.c` (il `diff` Ubuntu↔Debian di `kwin.c` è esattamente questo più i 3 punti del labwc, vedi §8). Il nome del file è `remotix_<version>_amd64.deb` (nome vero: `remotix_1.0.1-1+ubuntu26.04_amd64.deb`; la parte `+ubuntu26.04` fa parte del nome: scegliere se scrivere `<version>` o `<file>`). Il commento a `kwin.c:774` va corretto (non c'è più Arch). **Piccolo**.
Non toccare le note storiche `[M]` su altre distribuzioni (`authentication.c`, `card_pick.c`, ecc., come hanno fatto Debian e Fedora).

---

## 6. K6 — Lingua del desktop remoto su KDE (A1/A2)

### 6.1 Che cos'è
Oggi il desktop remoto di Kubuntu parte con `LANG=C.UTF-8` fisso. Fedora e Debian usano la lingua scelta dall'utente nelle Impostazioni (AccountsService, letta da root prima del cambio di identità), altrimenti quella di sistema, più i formati `LC_*`.

### 6.2 Fedora
`Fed child.c:1608-1710` (`child_locale_*`, `child_accounts_language`), chiamata `1983-1984`; `Fed session.c:3711-3716` (le `LC_*`/`LANGUAGE` nel composto della sessione), `4798-4799` (`OUR_VARIABLES` allargato).

### 6.3 Ubuntu oggi [V]
Manca. `session.c:1402-1440` `local_utf8()` → `"C.UTF-8"` come primo ripiego; `session.c:3699` `LANG=%s`; `OUR_VARIABLES` `session.c:4784-4800` senza `LC_*`.

### 6.4 Debian, e perché per KDE su Ubuntu serve anche il suo pezzo in più
Debian ha portato il blocco di Fedora e ha dovuto **aggiungere** `manager_set_locale()` (`Deb session.c:3584-3631`, chiamata a `3672` per KDE, XFCE, LXQt): su KDE dentro labwc `kwin_wayland` e `plasmashell` sono unità del gestore utente, nato con la lingua di sistema da `pam_systemd`, e **non** ricevono la `LANG` che il figlio mette a `startplasma-wayland`. Misura Debian: `remotix-child` con `it_IT.UTF-8`, tutto il resto con `en_US.UTF-8` (`debian13/studio/prove-1.2.0/giro2-kde.md`, «Riprova con giro5» 3b: FAIL; con la cura 3b OK dopo che il file `plasma-localerc` non vince). Ubuntu ha la **stessa architettura** (KWin dentro labwc, unità `plasma-kwin_wayland.service` con drop-in): [D] stesso difetto senza la cura. Fedora (KWin da solo) **non ha mai misurato** se la lingua arriva a Plasma (`debian13/docs/REGISTRO-problemi.md` H5).
Su KDE vince comunque il file `~/.config/plasma-localerc` dell'utente, se esiste (come in locale): non è un difetto, va scritto nel manuale (Debian F1).

### 6.5 Fare
**Portare con adattamento**: blocco di Fedora per la lettura + `manager_set_locale()` di Debian + `OUR_VARIABLES` con `LC_*`/`LANGUAGE` (così a fine sessione il gestore utente torna com'era; nella chiusura leggera per accesso locale la lingua resta lì di proposito, come in Debian). Si porta a blocchi (mai file interi: `child.c` e `session.c` di Ubuntu hanno molto altro). **Medio** (~230 righe, di cui ~190 commenti). Sul lato Ubuntu, la lingua di sistema viene da `/etc/default/locale` tramite `pam_env` del file `remotix.pam` (già presente, `pam_env envfile=/etc/default/locale`).

### 6.6 Cambio visibile (da approvare)
Grande: il desktop di Kubuntu remoto passa da inglese (C.UTF-8) a italiano (o alla lingua dell'utente), con date, numeri, tastiera dei menu. Già nel perimetro deciso (1.2.0 uguale a Fedora); da ricordare nel manuale utente.

### 6.7 Come provarla
Utente con `SetLanguage it_IT.UTF-8` in AccountsService e `plasma-localerc` presente/assente; sistema in `it_IT`; locale inesistente (il desktop deve partire lo stesso); misurare `LANG` DENTRO `kwin_wayland`, `plasmashell`, `labwc` e `systemctl --user show-environment` (non solo nel figlio: è l'errore trovato su Debian). Non verificato: `langpacks` italiani su Kubuntu (`kde-l10n`/`plasma-desktop-data`): se non installati il menu resta in inglese anche con la lingua giusta.

---

## 7. K7 — PATH come in un accesso locale (A3), per KDE

- Fedora: `Fed child.c:2025-2040` (PAM, altrimenti ripiego con `~/.local/bin:~/bin`).
- Ubuntu [V]: `child.c:1573-1582` (`child_path_ok`), `1790-1800`: il PATH viene già da `pam_env` (`/etc/environment` di Ubuntu ha `/snap/bin`, sbin, games); il ripiego è fisso e **senza** `~/.local/bin`.
- Debian: PATH fisso `/usr/local/bin:/usr/bin:/bin` (`child.c:1781`) prima, poi blocco di Fedora; misurato dopo: `PATH=/home/kd1/.local/bin:/home/kd1/bin:/usr/local/bin:/usr/bin` nel desktop KDE remoto.
- Fare: **adattare**, solo il ripiego (blocco di Fedora 2025-2040). **Piccolo**. Effetto su KDE: i comandi in `~/.local/bin` partono dal menu e da Konsole.
- Non verificato: il PATH reale di una sessione Plasma locale di Kubuntu (la `wayland-session` di sddm con `SHELL=*/bash` legge `/etc/profile` e `~/.profile`; su Debian misurato [V], su Ubuntu non verificato). Misurare `/proc/<plasmashell>/environ` di una sessione locale e confrontare.

---

## 8. K8 — Il labwc nostro e la parte del pacchetto (da lasciare com'è)

### 8.1 Ciò che Ubuntu ha e Fedora NO, e che DEVE restare [V]
1. `kwin.c:1488-1590` `kwin_nested_alive()`: labwc a `REMOTIX_LABWC` (`access(REMOTIX_LABWC, X_OK)` riga 1529), **mai** il labwc di distribuzione; senza il nostro, ripiego dichiarato `--virtual` a misura fissa (1530-1545).
2. `Makefile:128-133`: `LABWC ?= /usr/libexec/remotix/labwc` e `-DREMOTIX_LABWC`. Fedora l'ha tolto (`-lselinux` e `kde-output-*` al suo posto).
3. `kdehost.h` con `KDEHOST_MARK "remotix-kwin-host"` e `KDEHOST_OPTION "--kwin-nested"`; `main.c:2886` `--kwin-nested`. Fedora li ha sostituiti con `--kwin-virtual` + `REMOTIX_KDE_HOST=1`: **non copiare** `kdehost.h`, `main.c` (ramo `--kwin-virtual`, 2885-2891) né il `Makefile` di Fedora.
4. `session.c`: `write_dropin()` KDE con `--kwin-nested W H NODE` e la scelta della scheda (`card_node()`, `session.c:3544-3557`), che Fedora ha tolto (`Fed session.c:3927-3960`).
5. `child.c`: `kwin_host_settle()`/`kwin_host_resize()`/`kwin_host_exists()` (Fed li ha sostituiti con `kwin_output_resize()`, `kde_refused`: `Fed child.c:9214-9290, 11660`). Identici in Debian [V].
6. Pacchetto: `build/labwc-ospite/` (VERSIONS, build.sh, patch di wlroots), `debian/rules` (`LABWC_SOURCES`, `LABWC_PATH`, build e `install` di `/usr/libexec/remotix/labwc`), `debian/control` (Build-Depends da `meson` a `libpng-dev`, `Static-Built-Using: labwc (= 0.9.3), wlroots (= 0.19.2)`), `THIRD-PARTY-LICENSES` (voci labwc/wlroots: restano, SONO nel pacchetto), `LICENSE.md` §8 (vera per Ubuntu), sorgente `remotix-<versione>-labwc-source.tar.gz` da pubblicare (GPL).
7. Il motivo [V]: col labwc di Ubuntu e KWin ≥ 6.5 KWin non riceve mai «presented» (759 `presented` col nostro, 0 con quello di Ubuntu; Firefox fermo): `studio/10-kde-controprova-labwc.md`, `studio/6-kubuntu-kwin-labwc.md` §2.
8. Riconoscimento dei nomi di sessione Kubuntu: `session.c:395-400` (`kubuntu` per Kubuntu, `20-kubuntu.conf` di sddm a `458-467`). Debian li ha tolti: **non seguire Debian** in quel punto.

### 8.2 Ciò che si copia da Debian dentro `kwin.c`
Il `diff` Ubuntu↔Debian di `kwin.c` è solo: i tre messaggi B3, due commenti, e i 3 punti labwc (Debian: `g_find_program_in_path("labwc")`, `execlp`). **Per Ubuntu: prendere da Debian i tre messaggi B3 e i due commenti e basta; NON toccare i punti del labwc.**

### 8.3 Manutenzione del labwc nostro (da ricordare)
Un avviso di sicurezza serio su labwc 0.9.3 o wlroots 0.19 obbliga a un rilascio straordinario (copia statica che Ubuntu non aggiorna): `studio/6-kubuntu-kwin-labwc.md` §7. Non cambia con la 1.2.0.

### 8.4 Voci di pacchetto 1.2.0 con effetto KDE (le altre le analizza l'agente «comune»)
- `debian/remotix_network.apparmor`: riga `r` su `/usr/share/applications/org.kde.remotix.desktop` (K9 sotto).
- `debian/remotix.service`: `ExecStartPre=-…/remotix-pam-hook check` e `Environment=MESA_SHADER_CACHE_DISABLE=true` (Debian `debian/remotix.service:36-42`; `Deb debian/rules:84` installa `remotix-pam-hook`).
- `debian/remotix.postinst`: il controllo «la riga c'è già?» più preciso (Debian `postinst:27`) e `MESA_SHADER_CACHE_DISABLE` nel probe (`:38`); `prerm`: togliere la riga PAM **dopo** l'arresto del servizio (Debian `prerm:67-75`). Comuni.
- `needrestart` c'è già in Ubuntu (`diff` = 0).

---

## 9. K11 — D1–D4: «KWin da solo» e cambio di risoluzione a caldo (Fedora): NON portare, ma misurare

### 9.1 Che cosa sono
D1 `--kwin-virtual`/`REMOTIX_KDE_HOST=1`; D2 `kwin_output_resize()` con `kde_output_management_v2` ≥ 22 (`add_cvt`); D3 ciclo nascita/riaggancio con `kde_refused`; D4 plasmalogin (`Fed remotix-pam-hook`, F9).

### 9.2 Verdetto
**NON portare**: sono la strada di Fedora (KWin 6.8 da solo, nessun labwc). Su Ubuntu devono restare la strada labwc e il codice `kwin_host_*` (vedi §8.1).
Motivo, onestamente: lo studio di Fedora scrive che `kde_output_management_v2` v22 è di KWin 6.8 e che «Ubuntu 26.04 ha 6.6.7: non ci sono» (`fedora45/studio/5-kde-progetto.md:14, 82`), ma **non l'ha misurato su 6.6.7**: a Debian è stato misurato su 6.3.6 (versione **12**, registry assente: `debian13/studio/analisi-1.2.0/rapporto-kde.md` §5.1). **Non verificato su Kubuntu 6.6.7.**
D4: `plasma-login-manager` non è nell'archivio di Ubuntu 26.04; Kubuntu usa sddm 0.21.0 [V `studio/6-kubuntu-kwin-labwc.md` §8]. Da riguardare con Plasma 6.7/6.8.

### 9.3 Misura consigliata (1 minuto, VM Kubuntu già con Plasma)
`wayland-info` o l'elenco dei globali di una sessione Plasma locale: versione di `kde_output_management_v2` e presenza di `kde_output_device_registry_v2`. Se fosse ≥ 22 sarebbe una decisione del proprietario (portare il disegno «KWin da solo» anche su Ubuntu e togliere il labwc nostro), ma **non cambia l'elenco dei lavori 1.2.0** e il labwc nostro nasce per un altro difetto (fotogrammi «presented»), che con KWin da solo non c'è [D].

---

## 10. K9 e K10 — AppArmor e strumenti di prova

### 10.1 K9 — AppArmor: lettura di `org.kde.remotix.desktop` (F10 di Debian)
- Debian: il controllo dei rifiuti (`check-apparmor.py`) ha trovato su KDE righe «ALLOWED» tutte uguali: lettura di `/usr/share/applications/org.kde.remotix.desktop` (il file del permesso di cattura di KWin, controllato all'avvio da `kwin_check_permission`). Cura: `Deb debian/remotix_network.apparmor:33-35` (`/usr/share/applications/org.kde.remotix.desktop r,`).
- Ubuntu [V]: la riga **manca** in `ubuntu26.04/debian/remotix_network.apparmor`; il profilo è in `complain` (riga 25). Il codice che legge il file è lo stesso (`kwin.c:55, 798`, chiamato da `main.c:3523`). [D] stessa riga ALLOWED su Kubuntu; **non verificato** (nessuna misura su Ubuntu con `check-apparmor.py`).
- Fare: **portare così com'è** (1 riga). Nessun effetto visibile. **Piccolo**. Provare con `check-apparmor.py --box kde` a fine giro.

### 10.2 K10 — `prove/` per KDE
Stato [V]: Ubuntu ha solo P1-P6 in `check-prelocal.py` (334 righe); **non ha** `check-kde-exit.py`, `check-apparmor.py`, `hold.py`, `hold-user.py`, `banco-vm/autologin-sddm.sh`, `autologin-lightdm.sh`. Fedora e Debian hanno P7/P8 (`check-prelocal.py` 609 e 627 righe).
Base giusta: **Debian** (già adattata a `.deb`, sddm, `common-session`, AppArmor al posto di SELinux), non Fedora. Cose da cambiare partendo da Debian:
- Nomi dei display manager: Ubuntu `gdm3`, `sddm`, `lightdm` (come Debian); file di autologin di GNOME `/etc/gdm3/daemon.conf`; sessione KDE `plasma.desktop` con sddm 0.21 (`autologin-sddm.sh`).
- `TERMINALS`/`EDITORS`/`COMPOSITOR`: per KDE `kwrite --stdin` è l'editor di P8 di Debian; **`kwrite` non c'è in Kubuntu di serie** (nel box del 18 nov ha dovuto installarlo l'agente: `studio/giro2-kde.md` K3). Installarlo nella VM (come Debian per `labwc`) o ripiegare su `kate --stdin` [non verificato che Kubuntu 26.04 abbia `kate` di serie: lo dà `kubuntu-desktop`? non ho controllato].
- `COMPOSITOR["kde"]` e `check-kde-exit.py` `LEFT`: con labwc nostro nel processo (`labwc` in `pgrep`), come Debian (`debian13/prove/check-kde-exit.py:22`).
- P7 su KDE, come Debian: chiede solo che il desktop sia sparito, non che Konsole blocchi (su 6.6.7 non so se blocca).
- Porte e `lib.py`: Ubuntu 8841-8844 (SSH 2341-2344 da `server/vm-radeon.sh`).
- `check-apparmor.py` richiede `box.apparmor()` in `lib.py` (Debian lo ha; Ubuntu non: verificare `ubuntu26.04/prove/lib.py`: non letto riga per riga).
**Medio** (~6 file, copiati da Debian e ritoccati).

**DIVIETO DEL BANCO (da Debian, `COME-SI-LANCIA.md`):** nei guest Debian (kernel 6.12) la Radeon passata senza monitor deve avere `amdgpu.runpm=0`, altrimenti il server cade (quattro blocchi il 26 nov). I guest Ubuntu hanno kernel 7.0: **non verificato** se il difetto c'è; per prudenza mettere `amdgpu.runpm=0` anche lì PRIMA di dare la Radeon e guardare `journalctl -k | grep "SMU is resuming"`. P7/P8 (accesso locale vero: riavvio di sddm nella VM con la Radeon) hanno fatto cadere il server su Debian; su Debian sono girati in VM solo su GNOME, e il proprietario le ha fatte a mano sulle live. Per Ubuntu vale la stessa decisione (da confermare col proprietario).

---

## 11. K8 bis — Aggancio «il locale chiude il remoto» e sddm su Kubuntu (B1, C7)

### 11.1 Che cos'è
sddm (come lightdm) **non trattiene** l'accesso locale: il desktop locale parte sullo stesso gestore utente e sullo stesso bus in cui vive il remoto (commento `rootside.c:2400-2411`). L'aggancio PAM `remotix-local-login` (`pam_exec`, `debian/remotix.pam-config`) è quindi l'unica difesa su Kubuntu.

### 11.2 Stato [V]
- Ubuntu: `pam-auth-update` mette la riga in `common-session`; sddm, sddm-autologin includono `common-session` [V da `studio/5-sistema-ubuntu.md:118`, pacchetto sddm 0.21]; `prelocal` 6 PASS su quattro gusti (`studio/16-inventario…:647`). Il solo controllo è l'avviso del `postinst` (`remotix.postinst:46`) e il controllo di 5 s della parte root.
- Debian (B1): `remotix-pam-hook check` a ogni avvio del servizio (`debian/remotix.service:42`), script di 20 righe `debian13/src/remotix-pam-hook`, installato da `debian/rules:84`. Debian ha verificato che `sddm`, `sddm-greeter` e `sddm-autologin` includono `common-session` (anche il greeter): la riga scatta anche per l'utente `sddm`, e il programma deve ignorarlo (registro A2 di Debian).
- Contraddizione fra i documenti: lo studio di Ubuntu elenca il greeter fra gli esclusi, Debian ha misurato che lo include. Per Ubuntu **non verificato**; il programma esce comunque subito se non c'è desktop remoto di quell'utente.

### 11.3 Fare
**Portare da Debian** (non da Fedora, che usa `authselect`/`.rpmnew`): copiare `remotix-pam-hook`, la riga `ExecStartPre=-`, la riga in `debian/rules`, il `postinst` più preciso e il `prerm` riordinato (§8.4). **Medio** (è comune a tutti i desktop; qui conta per sddm).

### 11.4 Rischio
Se l'amministratore ha modificato a mano `common-session`, `pam-auth-update` rifiuta e resta la riga di avviso (come in Debian). Cambio visibile all'amministratore: a ogni avvio il servizio può riscrivere `/etc/pam.d/common-session` (con una riga di registro).

---

## 12. Altre voci con effetto particolare su KDE

- **Portafoglio (kwallet/ksecretd)** [V `studio/12-verifiche-kde.md` E]: alla prima richiesta di un segreto (qualunque app) compare la finestra «KDE Wallet Service» (crea portafoglio, poi richiesta di password): il servizio PAM `remotix` non ha `pam_kwallet5`. **Nessun albero lo ha deciso** (né Fedora, `fedora45/PIANO.md:88` lo elenca come «invariato», né Debian). Non è una voce della 1.2.0; resta aperta e va al proprietario (principio «remoto = locale meno i danni del server condiviso»). Non verificato su 6.6 con lingua cambiata ecc.
- **Regola polkit fwupd (A8)**: `remotix-remote-sessions.rules:73-79` (Fedora, 1 voce in più «org.freedesktop.fwupd.refresh-remote»). Debian l'ha inserita senza effetto (fwupd 2.0.20 non ha l'azione). Su Kubuntu: Discover o `fwupd` fanno il refresh? **non verificato**; innocua. **Portare così com'è** (comune).
- **Programmi di sfondo di KDE che abortiscono se la sessione remota viene chiusa «da fuori»** (F16 di Fedora: 27 file di errore in 25 s con `loginctl terminate-session`; causa probabile: si ferma prima l'unità di KWin): [D] con A6 (stop di tutto il gruppo insieme) il problema dovrebbe ridursi nella forzata del locale; **non misurato su Ubuntu**. Debian: `systemd-coredump` installato nelle VM e prova P7 «core dump» (G3). Fare lo stesso nel banco di Ubuntu.
- **Cambio di risoluzione / riaggancio di un'altra misura**: su Ubuntu resta `kwin_host_resize` sull'uscita del labwc nostro (`child.c:8875`, `11183`) [Debian: stesso]; Fedora ha un altro percorso. Niente da fare.
- **Cattura e input di KWin** (EIS, screencast, clipboard KDE): `clipboard_kde.c` e il resto identici fra i tre alberi o con differenze solo di classe D [V: `diff` 0].
- **kwin.c, permesso di cattura** (`org.kde.remotix.desktop`, `X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1`): ancora valido in 6.6.7 [V `studio/6-kubuntu-kwin-labwc.md` §8].
- **`session_missing_component()` (U2)** e **fine sessione detta prima (U3)**: sono già in Ubuntu e non cambiano nulla per KDE (Debian: «`session_over_early()` ESCLUDE KDE», `rapporto-kde` di Debian §8.1).
- **Manuali** (solo elenco): capitoli tecnici ch03 (chiusura forzata, 5 s), ch12 (KDE, lingua su KDE e `plasma-localerc`, PATH), ch13 (aggancio e B1), ch17 (prove, banco a VM); utente ch03 (lingua), ch04 (problemi noti). Il manuale deve dire che su Kubuntu KDE gira ancora nel labwc nostro.

---

## 13. Punti di cui chiedere l'approvazione al proprietario (cambiano il comportamento visibile su Kubuntu)

1. **K2/A7 (5 s)**: chiusura per accesso locale troncata a 5 s (prima 10). Già deciso per Fedora (25 nov) e fatto su Debian; su Kubuntu 6.6.7 la decisione va confermata esplicitamente.
2. **K1/A6**: nessun cambio di comportamento a regime, ma il bersaglio della forzata diventa quello che systemd ha già rifiutato in alcuni casi sul desktop giovane (§1.6): decidere se portarla così o con ritentativo (`replace`).
3. **K6/lingua**: il desktop passa da inglese a lingua dell'utente/di sistema.
4. **K7/PATH**: aggiunta di `~/.local/bin` e `~/bin`.
5. **K8 bis/B1**: il servizio rimette a posto `common-session` a ogni avvio.
6. **Portafoglio**: finestra «KDE Wallet» ancora presente (fuori 1.2.0, solo da decidere).
7. **Misura §9.3** e, se positiva, una discussione di strategia (KWin da solo anche su Ubuntu?): non è nel perimetro 1.2.0.

## 14. Che cosa non ho potuto verificare

- Il comportamento della forzata con `graphical-session.target` su KWin 6.6.7, il suo tempo e la catena `BindsTo`/`PartOf` del `plasma-workspace.target` di 6.6.7 (nessuna misura nei documenti di Ubuntu).
- Se Konsole con `top` blocca il Log Out su Plasma 6.6.7 (su 6.3.6 no, su 6.8 sì).
- Il PATH reale di una sessione Plasma locale su Kubuntu, la versione di `kde_output_management_v2` di KWin 6.6.7, la presenza di `kate`/`kwrite` di serie, il contenuto di `ubuntu26.04/prove/lib.py` rispetto a Debian (non letto riga per riga), l'effetto di A8 su Kubuntu.
- Che il profilo AppArmor su Ubuntu produca davvero la riga ALLOWED per `org.kde.remotix.desktop` (stesso codice; non misurato).
- Se `amdgpu.runpm=0` serve nei guest Ubuntu (kernel 7.0).
- Quanti core dump dei programmi di sfondo di KDE restano dopo una forzata con A6 (F16 di Fedora).
- Qualunque cosa che richieda il prodotto installato: nulla è stato lanciato.

## 15. Voci rimaste aperte per Ubuntu nei documenti di Debian

(`debian13/docs/REGISTRO-problemi.md` sez. F-H; `giro2-kde.md`; `rapporto-kde.md` di Debian §9.)
1. **H5**: da verificare su Fedora se la lingua dell'utente arriva al desktop KDE (mai misurato) — per Ubuntu il pezzo `manager_set_locale()` si deve provare comunque.
2. **KDE/labwc**: la strada labwc **di distribuzione** non è stata misurata da Debian nella analisi (labwc non installato nella VM); per Ubuntu la strada labwc **nostro** è quella che conta: tutte le misure di tempo di A6/A7 vanno rifatte dentro quella strada. P7/P8 di KDE «su macchina vera» (regola F36) restano da fare a mano sulla live Kubuntu.
3. **U5 (`kwin_poke`)**: Debian: «non visto scattare» su 6.3.6; su Ubuntu è dove è nato, da riprovare (contare nel registro «N holes in the numbers of the last M buffers»).
4. **U6 (sidecar)**: nel ripiego `--virtual` (labwc nostro assente) non parte: Ctrl+Alt+Canc resterebbe rotto lì (come in Debian senza labwc).
5. **H1**: `media/screen-updates` di poco oltre soglia (1,0-1,5 s contro 1,0) su GNOME, KDE, LXQt di Debian: causa non stabilita; da confrontare su Ubuntu.
6. **H2/H3**: `pkexec` su GNOME e `kbd-not-producible` su Firefox in LXQt (non KDE). Il FAIL di `kbd-not-producible` su KDE del giro1 di Debian non si è ripresentato.
7. **G1**: blocchi del server per `amdgpu.runpm=0` (§10.2).
8. **H4**: P7/P8 automatiche solo su GNOME; le altre a mano sulle live.
9. **F13**: C5 (database dconf di sistema) è una differenza dichiarata di Debian, **ma su Ubuntu c'è già** (non riguarda KDE: KDE non usa dconf per la sessione remota).
10. `giro-selinux.sh` e simili: solo Fedora, non si portano.

---

## Riepilogo (max 15 righe)

1. KDE di Ubuntu è già quasi allineato: fotogramma perso, Ctrl+Alt+Canc e Log Out «senza nessuno collegato» ci sono già (Debian li ha presi da Ubuntu).
2. Da portare da Fedora, piccolo: chiusura forzata di KDE che ferma tutto il desktop (3 righe) e attesa di 5 secondi per l'accesso locale (~10 righe).
3. Rischio nuovo su Kubuntu: systemd ha già rifiutato quello stop sul desktop appena nato; va provato con un desktop giovane e, se serve, deciso un ritentativo.
4. Da portare con adattamento: lingua dell'utente (serve anche il pezzo in più di Debian, perché KDE gira dentro labwc), `PATH`, testi «reinstalla il pacchetto».
5. Da portare da Debian: controllo dell'aggancio PAM a ogni avvio (su Kubuntu sddm non trattiene nessuno), riga AppArmor per il file `org.kde.remotix.desktop`, e le prove P7/P8.
6. Da NON portare: KWin da solo, cambio di risoluzione a caldo, plasmalogin. Il labwc nostro, il suo pacchetto e le sue licenze restano.
7. Una misura di un minuto da fare: se KWin 6.6.7 offre già il protocollo di Fedora (non misurato; probabilmente no).
8. Cambia ciò che vede l'utente di Kubuntu: attesa di 5 secondi, lingua del desktop remoto, `PATH` (serve il sì del proprietario).
9. Resta aperta la finestra del portafoglio KDE: nessuna delle tre distribuzioni l'ha decisa.
10. Nel banco: `kwrite` non c'è di serie su Kubuntu; per i guest Ubuntu mettere comunque `amdgpu.runpm=0` prima della Radeon.
11. Non verificato: tempi della forzata su Plasma 6.6.7, se Konsole con `top` blocca il Log Out, il PATH locale reale.

File: `/home/nicfio/Documenti/REMOTIX/ubuntu26.04/studio/analisi-1.2.0/rapporto-kde.md`
