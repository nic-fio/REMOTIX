# Phase 21 — The licence

> ⛔ **Closed without building, 10 Oct 2026** (`DECISIONI.md` §10.33): no licences, REMOTIX is free.
> The plan remains as history.

*Plan written on the evening of **8 Oct 2026**; ⭐ **rewritten on 9 Oct** after the day of decisions
on the licence (class of the key, upgrade, site with customer area and panel, logins, names `LICENSE_KEY` /
`INSTALL_KEY` / `HW_FINGERPRINT`). ⛔ **To be approved by the user before any work.** ⏸ **Suspended on 9 Oct** (the user: *«per il momento sospendiamo qui il discorso
licenza. Attendiamo che finisca il lavoro di testing di remotix»*): it resumes from here, with the approval of the plan. The **rules** are in
`SPECIFICHE.md` §15 (read §15.0 first) and **are not repeated** here: this document says **how** they are done and in
what order. ⚠ The user's constraint (8 Oct): **the licence comes before the xrdp bench** (`fasi/20-le-prestazioni.md`
§3 point 4b).*

---

## 1. What is built, in one line per part

| part | what it does | where it runs | language |
|---|---|---|---|
| **1. the product** | takes the `LICENSE_KEY` from the installer, creates the `INSTALL_KEY`, checks every hour, shows the state, stops at the end; the `remotix licenza` command | on the customer's server | C, like the product; the installer in Go |
| **2. the licence service** | operations A, C, E of §3.3: activations, checks with the ticket, duplications, emails, the clock | on the **VPS**, `remotix.nicfio.it/licenze/v1/` | Go (§3.1) |
| **3. the site** | the public shop window, the request for keys, the **customer area** and the seller's **panel** (§4, §4-bis) | on the VPS: static pages served by Caddy, the live parts by the service | HTML/CSS from the mockups; Go |
| **4. the gold function** | creates the golds, outside the panel | on the VPS, a command, only via ssh | Go, in the same binary |
| **5. the payment entry** | «rinnova» · «sospendi» · «riattiva» · «nuova full venduta» | on the VPS, in the service | Go |

## 2. Part 1 — the product

### 2.1 Where it is grafted, read in the code

*`[R]` 8 Oct; lines to be reread before writing, the code moves.*

| what | where it is today | what changes |
|---|---|---|
| **the login** | `src/autenticazione.c:212` `rcp_autentica()` (PAM), called **only by the grandchild** of the helper (`src/aiutante.c:23-30`); the outcome returns to the thread in `src/rcp.c:~2490-2515` | **after** correct credentials the thread looks at the licence state **in memory**: no network at that point |
| **the refusals** | the `CONGEDO` reasons in `src/rcp.h:113-133` (`0x01`…`0x10`), the sentences in `src/pagina.html:896-999` | a new reason, first in `RCP.md`: **`0x11 LICENZA`**, with the state (expired, blocked for two copies, suspended, revoked, never activated) choosing the sentence. ⛔ No more `0x12` «un utente»: the trial has unlimited users |
| **the login page** | the form in `src/pagina.html:600-625`; the marks in `src/pagina.c:420-433` | a mark `__LICENZA__` (state and days, **harmless**: before the credentials only «Trial version — N days left» is seen); the states of `SPECIFICHE.md` §15.10; the **warnings with «ho letto»** of the working days before expiry; the copy's **short name**. ⛔ **No field for the key**: root puts it in (§15.3 point 7) |
| **the licence memory** | `/var/lib/remotix/` (`src/main.c:1768-1770`) | `/var/lib/remotix/licenza/`: the `INSTALL_KEY` (root only), the attestation, the ticket, the request in flight, the most recent time seen |
| **the session cap** | `--tetto-sessioni N` (`src/main.c:2084`), default 10 | ⛔ **the licence does not touch it**: no licence counts users |

### 2.2 The messenger: the network outside the thread

⛔ The server is **a single thread**: one network request with a slow proxy would stop all the sessions. ⇒ A
**separate process**, child of the parent like the helper, which every **hour** (and at «controlla ora»):
- writes the request **to disk before sending it** and, with no answer, sends it again **identical** (§15.4);
- signs the challenge with the `INSTALL_KEY` and presents the ticket; sends the description of the machine (§15.12);
- goes through the **proxy** (`https_proxy`, or an option in `REMOTIX_OPZIONI`);
- verifies the attestation (VPS key certified by the root, §6) and to the thread sends only the state.

**HTTPS:** ⭐ **libcurl** (proxy `CONNECT`, system certificates, compatible licence); ⚠ new dependency of the
package.

### 2.3 The `remotix licenza` command and the installer

- **The installer** (`installatore/`, Go: CLI, TUI, GUI) asks for the **`LICENSE_KEY`** and shows whoever does not have it
  the site's address; without questions: `--license-key`. It passes it to the product; if the network is missing, the installation
  finishes and says to launch `remotix licenza attiva` afterwards.
- **`remotix licenza`**, as root: `stato` · `attiva <chiave>` · `upgrade <chiave>` · `controlla` · `recupera`.
  It talks to the messenger, not to the VPS directly.

## 3. Part 2 — the licence service on the VPS

### 3.1 The language: Go

- ⭐ **the installer is already in Go** (`installatore/go.mod`: `go 1.25`, with `vendor/`): same build
  container, same chain, a static binary just to copy to the VPS;
- the standard library already has everything needed: `net/http` with TLS, `crypto/ed25519`, `encoding/json`;
- ⛔ no framework: one binary, one systemd unit, one configuration file.

### 3.2 The database

⭐ **SQLite** in a single file (`modernc.org/sqlite`, pure Go, BSD: the binary stays static), transactional
operations, encrypted copy off the VPS every day (§15.11).

| table | what it holds |
|---|---|
| `licenze` | number `RX-…`, class (trial/full/gold), buyer, start, expiry, state, automatic renewal, payment reference |
| `chiavi` | the **encrypted fingerprint** of every `LICENSE_KEY` issued, the class, used yes/no, when it expires if never used (30 days the trial) — forever |
| `installazioni` | the public part of the `INSTALL_KEY`, the licence, the current ticket, the last answer (to give it back the same), short name, last description of the machine |
| `trial_impronte` | every `HW_FINGERPRINT` (encrypted) that has already had the trial, with its end date |
| `sdoppiamenti` | discovery, copies, RDAP, choice or block, warnings sent |
| `clienti`, `sessioni` | the customer area: email, Google login, throwaway links |
| `registro` | every operation of the panel, of the payment, of the gold and of the clock: who, when, what |

### 3.3 The service's operations

*Rewritten on the evening of **9 Oct 2026**, at the user's request (*«prima definiamo le operazioni che deve svolgere
il server e poi definiamo l'interfaccia web»*): ⛔ it supersedes the table of 8 Oct (`machine-id`, «avvii», check
every N hours). The rules are in `SPECIFICHE.md` §15 and are not repeated here: every row refers to them. ⏳ **To be approved**:
the 🔸 rows are Claude's proposals, born from the gaps §15 leaves.*

**A. The product** (the customer's server; every request is signed with the `INSTALL_KEY`)

| # | operation | what it does | §15 |
|---|---|---|---|
| A1 | **activate with the key** | the key's class decides the licence (trial, full, gold); consumes the key (once, forever), binds the licence to the `INSTALL_KEY`, gives attestation and first ticket; for the trial it also checks the fingerprint: already had ⇒ **same** end date, empty ⇒ «scrivici» | 15.3, 15.7 |
| A2 | **upgrade** | on an active installation consumes a key of a higher class (ladder ✅ trial → full → gold); `INSTALL_KEY` **renewed** (the server creates it, signed with the old one; ✅ the user, 9 Oct), same licence number, the year starts from here | 15.3 |
| A3 | **check** (every hour, and «controlla ora») | consumes the ticket and gives a new one with the attestation; gives back **the same answer** to an identical request; discovers duplication; says the state (valid, in grace, suspended, revoked, blocked, double gold) | 15.4, 15.8 |
| A4 | **state of the copy left behind** | answers without consuming tickets | 15.9 |
| A5 | **release** | the old installation signs the release for the voluntary move | 15.9 |
| A6 | **ask for recovery** | licence number + new `INSTALL_KEY` ⇒ confirmation email to the buyer; respects «uno ogni 30 giorni» | 15.9 |
| A7 | **give me the signed list** | addresses, valid keys and revocations, signed by the mother key | 15.11 |
| A8 | **describe the machine** | inside A1-A3: description of the hardware, internal IPs, name; the service keeps only the last one | 15.8, 15.12 |

**B. The buyer** (pages opened from a link in the email: the page **shows**, the button **confirms**)

| # | operation | §15 |
|---|---|---|
| B0 | **ask for a trial key**: email (mandatory), name and company (optional), ✅ the user 9 Oct ⇒ the key arrives by email (🔸 and so the email is confirmed, without a separate link). ✅ **Only from the service's site** (the user, 9 Oct); the installer only asks for the `LICENSE_KEY` | 15.7 |
| B1 | **buy a full**: from the service's page (`remotix.nicfio.it`, «Acquista»); whoever buys may not be the administrator. ⏳ The data depend on the processor. Until it exists, the seller creates it (D1) | 15.3 |
| B2 | **choose the copy** between the two active; the kept one receives a new `INSTALL_KEY`, the other stops; it also unblocks an already blocked licence | 15.8 |
| B3 | **confirm the recovery** | 15.9 |
| B4 | **automatic renewal yes/no** — 🔸 the payment processor keeps it, here only the link; ⏳ it depends on the processor | 15.6 |

**C. The payment** (with its secret key)

| # | operation | §15 |
|---|---|---|
| C1 | **renew** licence N for a year (also unblocks one expired in grace or stopped) | 15.6 |
| C2 | **suspend** · 🔸 **reactivate** (a charge rejected and then paid) | 15.10 |
| C3 | 🔸 **new full sold** ⇒ like D1, with the email to the buyer | 15.3 |

**D. The seller** (the web panel; every operation ends up in the log with who, when, why)

| # | operation | §15 |
|---|---|---|
| D1 | **create a full**: buyer's email, note ⇒ number `RX-…` and key, email to the buyer | 15.1, 15.3 |
| D2 | ⛔ **not from the panel**: the gold is created with a **dedicated function** of the service (✅ the user, 9 Oct: *«le licenze gold vengono rilasciate tramite una funzione dedicata del server delle licenze. Non seguono una strada normale»*). 🔸 A command on the VPS, reachable only via ssh with the laptop's key: whoever breaks into the panel does not create golds. Note («scatola 3») ⇒ number and key | 15.1 |
| D3 | **give a trial key by hand** (the machine without a fingerprint, or whoever needs more days) | 15.7 |
| D4 | **renew by hand** (payment outside the processor, until the processor exists) | 15.6 |
| D5 | **suspend · reactivate · revoke** | 15.1, 15.10 |
| D6 | **double gold**: look at the two copies, **disable one** | 15.1 |
| D7 | **licence blocked for 15 working days**: **unblock** or **delete for good** | 15.8 |
| D8 | **3 duplications in 90 days**: look, **revoke** or leave | 15.8 |
| D9 | **unblock the 30-day limit** (swap or recovery) | 15.8, 15.9 |
| D10 | 🔸 **key lost before use**: cancel the old one and issue a new one (keys are not kept in clear, so they cannot be resent) | 15.3 |
| D11 | 🔸 **change the buyer's email** when the customer no longer has access to the old one (normally the customer does it from the customer area), with a warning to the old address | — |
| D12 | **look**: list and search (number, email, state, last contact), the history of a licence, the copies, the log | — |
| D13 | 🔸 **the «da decidere» box**: D6, D7, D8 and the «scrivici» trials in a single place, so nothing waits in silence | — |

⛔ **Outside the panel**: everything signed by the **mother key** (certifying the VPS's key, the signed list
of revocations, §15.11). It stays a command on the laptop: if the panel were broken into, the root is not there.

**E. The service's clock** (on its own, every hour)

| # | operation | §15 |
|---|---|---|
| E1 | the expiry emails: 3rd, 2nd and last working day before (the last at 11 and at 16), then one a day at 11 during the grace period; they stop at renewal | 15.6 |
| E2 | the warning 7 days before the automatic charge | 15.6 |
| E3 | duplications: one email a day for 7 working days, then **block**; at 15 working days the licence goes into the seller's box | 15.8 |
| E4 | the links (choice, recovery) and the never-used trial keys (30 days) expire | 15.8 |
| E5 | the deletions: duplications at 6 months, the rest at 2 years | 15.12 |
| E6 | the encrypted copy off the VPS, every day | 15.11 |

## 4. Part 3 — the seller's panel

✅ **9 Oct, the user: a web interface**, a reserved part of the site (§4-bis). The operations are section D of
§3.3, the gold excluded (dedicated function via ssh). ✅ Mockup `grafica/sito-mockup/console.html`.

## 4-bis. The site `remotix.nicfio.it`

✅ **9 Oct, the user**: *«remotix.nicfio.it sarà anche la landing page del progetto, aperto al pubblico e dove si
"pubblicizza" il prodotto, in modo simile ad esempio a phonestra. Bisogna prevedere delle sotto-sezioni riservate»*.

🔸 **How it is put together**, on the same VPS and with the same scheme as the sites already there (`~/Documenti/VPS`: Caddy,
static files in `/srv/www/<sito>`, HTTPS from Let's Encrypt, the `progetti` user who publishes):
- the **public pages** are **static files**, like phonestra: no CMS, nothing to break into;
- everything dynamic is **the Go service**, behind Caddy, under paths of its own.

| section | for whom | what is there | access |
|---|---|---|---|
| **public** | everyone | the product, the performance, the prices, the documents, **«Prova gratis»** and **«Acquista»** (B0, B1) | free |
| `/licenze/v1/` | the customer's server | the requests A1-A8; it is not a page | signatures (`INSTALL_KEY`) |
| ✅ **customer area** (the user, 9 Oct: *«prevedere un'area cliente ci semplifica parecchie cose»*) | whoever bought or asked for a trial | their licences: number, class, state, expiry, active copies; **choice of the copy** (B2); **confirmation of the recovery** (B3); renew; automatic renewal yes/no (B4); email change (D11 becomes theirs) | ✅ (the user, 9 Oct) **link to the email, without a password**, which always holds: you write the email, a link arrives that is valid once and briefly, and opens the area for a few hours; plus **«Accedi con Google»** as a shortcut (the email arrives already verified). ⛔ No password, no Facebook; Microsoft not for now (the user's doubt), it can be added later. The emails of the choice and of the recovery lead **here**, not to separate pages |
| **panel** | the seller | the operations D1-D13 (not the gold, D2) | ✅ **passkey or «Accedi con Google»** (the user, 9 Oct: *«passkey e/o google»*). 🔸 The conditions: Google holds **only for the seller's account**, written in the configuration, and that account must have **two-step verification**; every operation that creates, renews, revokes or deletes sends **at once a warning to the seller** (if they did not do it, they know within a minute); if access is lost, a command via **ssh** on the VPS gives a link to register a new passkey. ⚠ With two doors the panel is as strong as the weaker: the Google account |

✅ **The whole site is in English, panel included** (the user, 9 Oct). Mockups in `grafica/sito-mockup/`. ✅ Seen and approved for now
the login page and the customer area (the user, 9 Oct: *«semplice, elegante e senza fronzoli … al momento mi sembrano ok»*).

🔸 **Two reserved parts, built together and kept separate** (the user, 9 Oct: *«ci sono due versioni della parte
riservata: quella dei clienti registrati e quella mia»*): **the pages are the same** (the sheet of a licence, its
history, the copies), and the panel adds the seller's buttons; but **entry, session and permission
checks are separate** (its own address, its own login). ⇒ Less work, and an error in the customer area does not open the
panel.

## 5. Part 4 — the payment entry

Two generic requests, `rinnova` and `sospendi`, with the licence reference. ⛔ **No processor chosen**
(§10.30: pending): when one is chosen (Polar/Paddle or Stripe), only the **translator** from its
notifications to these two requests is written. The product does not change.

## 6. The keys, and where they are

⭐ Proposal of §10.30 (8 Oct): **offline root, certified VPS key**.

| key | where it is | what it signs |
|---|---|---|
| **root** ed25519 | ⛔ **never on the VPS**: on the laptop, in `.chiavi/` (ignored by git, like the installer's D10, `fasi/17-l-installatore.md` D10) + a backup copy off the computer | only the **certificates** of the VPS keys, with expiry; and the revocations |
| **VPS key** ed25519 | on the VPS | the attestations |
| the root's public key | **inside the product**, written at build time | — |

- ⭐ **The model already exists, in the repository**: the installer's «catena A» — an offline ed25519 root that
  certifies subkeys with expiry, revocations signed by the root (commit `6773a66`: `installatore/motore/firma.go`,
  `installatore/strumenti/chiavi-a/main.go`). It was **removed** on 30 Sep with D11 (`6612256`) because
  the archive's key was enough for the installer; here it is really needed. We take it up from there, in Go for the tool
  and the VPS; in the product the verification is in C (OpenSSL).
- ⚠ If the VPS is broken into: its key is revoked and a new one is certified, **without recompiling the product**.
  If the **root** is lost, instead, a new version of the product is needed: it must be guarded with the backup copy.
- ⚠ **TEST keys and real keys**: like the installer, it is built with the test public key for the benches
  and with the real one only in the release command. A package with the test key **must not go out**: the
  release command checks it.

## 7. How it is tested, without a real VPS

- ⭐ **The fake service is the real service**, in a podman container on the laptop, with test keys, a
  **movable clock** (14 days in a minute) and a **fake mail** that collects the emails for looking at them.
- **The product finds it** with an option (`--licenze-url`), which the package never sets.
- **The cases**: new trial · trial already given to the same fingerprint (same end) · empty fingerprint («scrivici») ·
  key used twice · upgrade trial → full → gold · expiry, warnings, grace, end with the desktops alive ·
  renewal from the «pagamento» · VPS off within and beyond the 14 days · proxy (squid in a container) · fault halfway through a
  check (never a false clone) · clone with choice, without choice (block at 7 working days) and at 15 · double
  gold · recovery · VPS back to an old backup · VPS key revoked · machine clock
  behind · customer area and panel in the browser (Marionette, like the page's benches).
- ⚠ **Today's benches** take a **test gold** from the fake service, like every customer.

## 8. The steps, in order

*Redone on the evening of **9 Oct 2026** (the morning's estimate was ~122 hours). In: the site (shop window, customer area,
panel, logins with email link, Google and passkey), the gold function, the upgrade, the installer that
asks for the key, the `remotix licenza` command. Out: the key field in the page, the confirmation link
of the trial (the key by email confirms the address), the one-user limit.*

| # | step | hours |
|---|---|---|
| 0 | `RCP.md`: `0x11 LICENZA` and the licence messages | 1 |
| 1 | **the keys**: offline root, test VPS key, the signed list (addresses, keys, revocations), from catena A | 6 |
| 2 | **the message format**: binary with fixed lengths, signed; common C/Go examples; fuzzing of the two readers | 6 |
| 3 | **the service** (Go): A1-A8 (activation by class, upgrade, ticket with atomic consumption and repeatable answer, recovery, release), the trial fingerprints, the duplications with short names and RDAP, the clock E1-E6, the return to an old backup | 32 |
| 4 | **mail from the VPS**: outgoing Postfix, SPF/DKIM/DMARC, PTR, the texts in English, tests towards Gmail/Microsoft/Yahoo | 6 |
| 5 | **the public site**: the static pages from the mockups, the texts, the key request (B0) | 8 |
| 6 | **the customer area**: email link, «Accedi con Google», the licence sheet, choice of the copy, recovery, automatic renewal, email change | 14 |
| 7 | **the panel**: passkey and Google (only your account), D1-D13, the «da decidere» box, the warning at every operation, registration via ssh | 14 |
| 8 | **the gold function** (command via ssh) and **the payment entry** (renew, suspend, reactivate, new full) | 4 |
| 9 | **the product, the messenger** (separate process, libcurl, proxy, request on disk, ticket, trusted time, `HW_FINGERPRINT` with the factory strings discarded, description of the machine) | 16 |
| 10 | **the product, the login and the command** `remotix licenza`: states, end with the desktops alive, copy left behind | 10 |
| 11 | **the login page**: the states of §15.10, the warnings with «ho letto», the copy's short name | 8 |
| 12 | **the installer**: the `LICENSE_KEY` in CLI, TUI and GUI, `--license-key`, the case without network | 5 |
| 13 | **the benches** (§7) and the short suite with the test gold | 16 |
| 14 | **packages**: libcurl in the three families, the real key only in the release command | 4 |
| 15 | **the real VPS**: Caddy with the site, the service, the unit, the mail, the encrypted copies off-site | 6 |
| 16 | `SPECIFICHE.md`, `DECISIONI.md` §10.30, the **draft of the privacy notice** (to be checked by a lawyer) | 5 |
| | **total** | **~161 hours ≈ 20 working days** |

⚠ The estimate is by someone who has not yet written a line: the service (3), the messenger (9) and the customer area with the
panel (6, 7) are the points where the project's history says one errs on the low side. ⚠ Step 4 depends on
OVH (port 25, PTR). ⚠ «Accedi con Google» requires registering REMOTIX with Google (one hour, the seller's account).

## 9. What stays out

- **the real payment** (processor, VAT, invoices): pending by the user's decision (§10.30);
- **the sales contract** of the full: it is a question (§10 question 3);
- **the capacity test for the customer** (§10.30, the program next to the server): it is a job of its own, not the
  licence's; it is done later;
- ~~a **web panel** for the seller~~ ⛔ brought back in on 9 Oct at the user's request (§4);
- **the technical documentation** (with the sizing guide and the performance table, `fasi/20` §5): the
  site refers to it, but it is written separately;
- «Accedi con Microsoft»: the user's doubt, it is added later if needed;
- defences against whoever modifies the binary: §10.30 declares it, the licence keeps honest people honest.

## 10. Questions for the user, one at a time

*⚠ History (8-9 Oct): the answers flowed into `SPECIFICHE.md` §15, which prevails over this section.*

1. **The grace period if the network is missing**: how many days does the server keep letting people in without managing to talk
   to the VPS? (⚠ It must be longer than the time to put the VPS back on its feet, §10.30; and how many hours between rechecks.)
   ✅ **8 Oct: 14 days, check every 24 hours** (the user: *«ok 14 giorni»*, after proposing 3). The comparison
   that decided it: Microsoft 365 30 days, Adobe annual 99, KMS 180 — the grace period protects the customer from
   **our** faults, and 3 days would have blocked all the customers together after a weekend with the VPS down.
   The attestation is therefore valid «last successful contact + 14 days». ⭐ With a **warning to the administrator from the first
   failed check** (login page and log), with the days that remain.
2. **The grace period on missed renewal**: how many days after the full's expiry, before the «abbonamento
   scaduto, rinnova» window (§10.30, still 🔸 to be confirmed)?
   ✅ **8 Oct: 14 days** (the user: *«ok 14 giorni»*), with the warning on the login page **from 7 days before
   expiry**. A renewal that fails is almost always an expired or rejected card, and the processors
   retry on their own for one-two weeks: whoever is just changing card is not stopped.
3. **The sales contract** of the full: which text (§10.30: for the trial there is PolyForm Free Trial, for the full
   no standard text)?
   ⏳ **8 Oct: suspended** (the user), together with the payment: whoever collects decides what remains to be written (Polar or
   Paddle sell themselves and have their own purchase terms, we are left with the licence of use; with Stripe the
   seller is us). ⛔ It does not block the work: the sale waits for the payment anyway.
4. **The VPS**: provider, operating system, **domain** by which the customers reach it (needed for the HTTPS
   certificate and to be written into the product), who has access.
   - ✅ **provider: OVH** (the user, 8 Oct). ⚠ The licence database is the only thing that cannot be rebuilt
     (who paid, which machines): it must be saved **off the VPS**, every day — the case to cover is that
     of Strasbourg (fire at the OVH centre, March 2021: whoever had their copies in the same centre lost them).
   - ✅ **system: Debian 13 «trixie»** (the user, 8 Oct): the same as the test server and the laptop ⇒ the
     fake service in a container (§7) is built on the same base, and what passes there holds on the VPS.
   - ✅ **address: `remotix.nicfio.it`** (the user, 8 Oct: *«al momento appoggiamoci a remotix.nicfio.it»*), the
     licence service under a path with the version (`https://remotix.nicfio.it/licenze/v1/…`), so the
     same name can later also serve the package archive. ⚠ A dedicated domain was Claude's
     proposal (the name is written into the product, companies' firewalls authorise it by name, it ties the product
     to a personal name); `remotix.com` is already registered, `.it`/`.eu` to be checked.
     ⭐ **Mandatory in the plan, because of this choice: the signed change of address.** The service can tell the
     product, inside the signed attestation, «from now on ask X»; the product remembers it in `/var/lib/remotix`
     and moves there. A new domain tomorrow = keep the old one on for a few months, no customer to update.
   - ✅ **access: ssh** (the user, 8 Oct). The credentials in `~/VPS.ssh`, same format as `~/SERVER.ssh`
     (lines «chiave: valore»), ⛔ never in the repository. The VPS is touched only at the step of installing the
     service, after the tests on the fake service.
5. **The sessions open when the licence expires**: do they stay until exit (proposal) or are they closed?
   ✅ **8 Oct, decided with the user** (the user's idea, taken from RootSpeak; Claude's two corrections accepted: *«ok»*):
   - ⭐ **only REMOTIX is disabled, never access to the server** (ssh, local login, the system's PAM stay
     intact): the server belongs to the customer, the administrator who must renew must not be locked out, and a block
     born from a fault of ours (VPS down) must not stop other people's machines;
   - **at expiry** (= end of the grace period, not the subscription date) the **connections** are closed,
     the **desktops stay alive** with the work inside; at reconnection the licence window; after the
     renewal everyone gets back in and finds everything as it was. Nobody loses work, nobody continues without a licence;
   - **the warnings before**, with RootSpeak's behaviour (it insists, «ho letto», it never blocks) but **shown
     in REMOTIX's page** over the desktop, not with `zenity`: everyone looks at the page, it is the same on the
     four desktops (no exceptions per compositor), and RootSpeak stays a free product of its own;

     | when | who | what |
     |---|---|---|
     | from 7 days before | the administrator | log and login page: he is the one who renews |
     | last 3 days | all the connected users | **3 messages in 24 hours**, with «ho letto» |
     | at expiry | everyone | connections closed, desktops alive, licence window on return |

   - **RootSpeak's code is reused** (the user: *«il codice è mio e lo puoi riutilizzare»*; it is the user's, so it
     enters a closed product without constraints): `src/text.c` `clean_text` (cleaning of the text from control
     characters), the model of the three states and of the postponements (sent, delivered, confirmed; reminders at
     intervals) and the event log (`src/event.c`). ⚠ The delivery is **not** reused (terminals,
     `zenity`, shell hooks): with us the channel is the page. The code taken is translated to REMOTIX's names and
     conventions (Italian), with the provenance written at the head of the file.
6. **The clone discovered**: is only the seller warned, or is the second copy suspended on its own?
   ⏳ **8 Oct evening, PENDING: the user is thinking about it** (*«qui serve del tempo per pensarci su un attimo»*). Where
   we had got to:
   - ⛔ **discarded by the user**: «the first to activate keeps the slot» (live slot, heartbeat every 15 min,
     release after an hour) — *«eliminiamo il discorso della data di attivazione, e restiamo sul server fisico»*;
   - ⭐ **the user's direction**: tie to the **physical server**, taking inspiration from Microsoft and improving on it;
   - 🔸 **Claude's proposal, to be approved**: a 5-component fingerprint (`product_uuid`, motherboard
     serial, processor model, system disk serial, main network card), valid with
     **3 out of 5** and updated on its own when a piece changes; **move from the login page** without
     account or email (the old one is freed instantly, 1 every 30 days); to the VPS **only the encrypted
     fingerprints**, never the serials; a message that says **which** component changed;
   - ⚠ **the declared limit**: on virtual machines the iron is fake and is copied with the clone (Microsoft too
     uses something else there). Two roads: **(a)** accept it and declare it; **(b)** advised by Claude: with the 24-hour
     check already decided, two live copies with the same fingerprint ⇒ **only a warning to the seller**, no block.
   ⚠ If the fingerprint is chosen, `/etc/machine-id` alone (§10.30) is no longer enough and §10.30 must be rewritten.
   - 🔸 **8 Oct evening, the scheme brought by the user**: at activation the installation **generates a key
     pair**, the service binds the licence to the **public key** and returns a signed attestation (product, type,
     expiry, maximum installations, installation identifier, features); at every contact
     the installation **proves it has the private key**. Claude's judgement: ✅ it holds and is a better base
     than the fingerprint (cryptographic proof instead of declared values, no serials to the VPS, no false
     alarm if a disk changes); ⚠ but **on its own it does not stop clones**: the private key is a file and is copied with the
     disk. ⇒ **counter-proposal: the private key is born INSIDE the TPM 2.0** and cannot leave it; a disk
     copied onto another computer does not take it along. Read on 8 Oct: `/sys/class/tpm/tpm0`, version **2**, both
     on the laptop and on the test server. ⚠ Limits: without TPM (many VPSs, old machines) it falls back on
     a key in a file + 3/5 fingerprint; a cleared TPM (BIOS, motherboard change) = new installation
     ⇒ the move from the login page is needed here too; a virtual TPM can be copied with the clone
     of the virtual machine ⇒ warning (b) remains.
7. **What the full buys beyond users and duration**: are updates included while the subscription is
   active, and after expiry does the product still update?
   ✅ **9 Oct** (the user: *«una licenza full scaduta si comporta come una trial, semplicemente il sistema smette di
   funzionare»*): once the 14-day grace period is over, the expired full **stops** like the trial; the question about
   updates after expiry does not arise. Updates included while the full is active.
   - **Warnings before expiry for the trial too** (the user), like the full: administrator from 3 days before
     (the trial lasts 14), connected users 3 messages a day in the last 3 days, in the page.
   - ✅ **The check every 60 minutes, not every 24 hours** (the user). ⭐ It improves: a duplication is discovered within
     an hour and the 72 hours of the choice start earlier; the state of a revoked or renewed licence arrives at once.
     Negligible cost: 1000 customers = 24 thousand checks a day, a small VPS bears them. ⚠ Two rules that
     follow: the **grace period stays 14 days from the last successful check** (it does not change); and if the VPS does not
     answer the warning to the administrator goes out **once**, then **once a day**, not every hour. The copy
     left behind too asks for its state every hour (without consuming tickets).

> ⭐ **The licence rules in force are in `SPECIFICHE.md` §15** (9 Oct): this document stays the work plan
> and the history of the questions.

## 11. The discussion with ChatGPT: the solution agreed upon (8 Oct 2026, night)

*Asked by the user: «intavola un serrato confronto tecnico con ChatGPT … fino a quando non avete una soluzione
su cui concordate». Model **GPT-5.6 Sol**, maximum reasoning, 3 turns, closed with «CONVERGED». Cost
≈ 2.6 $ (102 thousand word-units in input, 69 thousand in output). ⛔ It is a **technical proposal agreed between two
models**, not a decision: the choices that touch commerce and the rules stay with the user (§11.3). The
transcript is not kept; here is the result.*

### 11.1 What changes compared with question 6

- ⭐ **The licence is tied to the «history» of the installation, not to the iron.** A machine is a physical server **or
  a virtual machine** (in the cloud the iron underneath is not seen and changes). ⇒ It corrects «physical server».
- ⭐ **The ratchet** (ChatGPT's proposal, in place of the «warning to the seller»): at every check (24 hours) the
  service consumes the current token and gives a new one, usable **once**. A clone starts with the same
  token: one of the two goes on, the other stays behind and is discovered. It holds on virtual machines too, where
  the iron is fake. ⛔ It is **not** the «live slot every 15 minutes» discarded by the user.
- ⭐ **Moving REMOTIX to a new server by turning off the old one works on its own**, without writing to anyone:
  it is the same history continuing. Two copies on together instead split and one stays behind.
- **No iron fingerprint nor cloud integrations in the first version** (too much work for one person; the
  ratchet covers the clones). **TPM in a second version**, as reinforcement on physical servers.

### 11.2 The design, in brief

1. At activation the installation creates a **key pair** (ed25519, a file readable only by root); the
   licence binds to the public key; every check **signs a challenge** from the service.
2. The **signed attestation** carries type, commercial expiry, end of the grace period, «valid until» (never more than
   **14 days**, checked by the product too, gold included), history and token number.
3. **Gold**: same mechanism, no commercial expiry (explicit field), revocable.
4. **Keys**: offline root → VPS key that signs only the attestations; addresses, valid keys and
   revocations in a **list signed by the root**; two backup addresses in the product. Normal HTTPS, proxy yes.
5. **Message format**: simple binary with fixed lengths, signed, with common C/Go examples and fuzzing.
6. **Never a false clone because of a fault**: the request is written to disk **before** sending it and, without
   an answer, it is sent again **identical**; the service remembers the last answer and gives it back the same.
7. Only the REMOTIX service touches the licence state; «controlla ora» goes through it.
8. **The copy left behind** (clone, or restored backup) is not extended: it works until its «valid
   until» and shows the administrator a **neutral** message («copia più vecchia, ripristinata?»).
9. **Recovery** (restore from backup, dead server): new key + licence code + **confirmation by email
   to the buyer** (the page shows, the button confirms). One every 30 days; you can unblock it by hand.
   ⛔ No local-only button: whoever clones would press it and steal the licence from the real customer.
10. **Voluntary move**: the old installation signs the release, the new one activates.
11. **If the VPS goes back to an old backup**: the customers' servers present the last proof **signed by the
    service** and it catches up; never trust numbers declared by the customer.
12. **Trial**: verified email never used **and**, if present, the exact motherboard fingerprint (UUID + serial) never
    used; reinstalling during the trial gives back the same end date.
13. **Email from the VPS without paid services** (Postfix outgoing only, SPF/DKIM/DMARC, rDNS): fine if OVH
    leaves port 25 open and allows setting the PTR, and if the tests towards Gmail/Microsoft/Yahoo pass; otherwise
    a relay is needed. ⚠ To be verified on the VPS.
14. **The VPS**: transactional operations, encrypted copies off the VPS, log of activations and
    recoveries; recovery page reachable even with the licence expired.
15. **TPM (second version)**: key born in the TPM, without touching its ownership or the PCRs; a broken TPM leads
    to recovery, never to a key secretly in a file.

### 11.3 The decisions that stay with the user

1. **«Licence tied to the history of the installation»** instead of «tied to the iron», with free moving
   by turning off the old server.
   ✅ **9 Oct: accepted** (the user: *«la tua proposta è migliorativa»*), with the three additions born from the user's
   proposal «al massimo 2 chiavi uguali attive, dopo 14 giorni la chiave si invalida» (⛔ discarded: invalidating
   the licence punishes the victim of a clone — and becomes a weapon to block a competitor — and a key
   derived from the iron reopens the false alarms and does not distinguish cloned virtual machines):
   - **two copies discovered** ⇒ **at once an email to the buyer** with the recovery link already ready, and a warning to
     the seller;
   - **within 14 days** the copy **without** the confirmation from the buyer's email is stopped; ⛔ **the licence is never
     invalidated on its own**;
   - **whoever tries again**: the same licence duplicated **3 times in 90 days** goes to the seller, who looks and
     decides whether to revoke. A person decides, not an automatism.
   ✅ **9 Oct, the full: THE CUSTOMER CHOOSES** (the user's idea, with Claude's additions accepted: *«certo»*):
   - **two active copies** ⇒ email to the buyer with the data of the two and a **link to a choice page**;
     **72 hours** to choose, reminder after 24;
   - every copy receives a **short name** («copia A · 4F7K»), shown also on its login page: on a
     cloned virtual machine the fingerprints are **identical**, and it is the name that makes them recognisable;
   - **the data for choosing, readable by a person**: short name; day and time of the discovery and of the last
     contact; **public IP** with provider, country and approximate city (from **RDAP**, the structured whois);
     **internal IPs and machine name** (two copies behind the same router have the same public IP);
     **description of the hardware** (make and model of the motherboard, processor, memory, disks) — ⚠ the encrypted
     fingerprint says nothing to a person: the description is sent, the fingerprint stays for the comparison;
   - **without a choice within 72 hours**: the copy with the most recent ticket stays, the other stops; ⛔ the licence is **never
     invalidated**; a choice arriving later still holds (one swap every 30 days);
   - **choice made** ⇒ the kept copy receives a **new key** (otherwise, with the same key, the two would
     swap places), the other stops; its desktops stay alive until shutdown;
   - ⛔ **the fingerprint describes, it does not decide**: what binds the licence stays key and ticket (changing a disk does not
     make a customer a new machine);
   - ⚠ **privacy**: IP, machine name and hardware of a copy end up in the buyer's email (also
     those of whoever cloned). It is done to prevent fraud, and must be **declared in the privacy notice** of the product.
2. **A clone can work for up to 14 days** before stopping.
3. **One trial per verified email** (as well as per machine): even a company testing on two servers uses two
   emails.
   ✅ **9 Oct, the trial simplified by the user** (it replaces the email proposal):
   - **14 days, unlimited users** (*«così un'azienda può effettivamente valutare le vere potenzialità del
     prodotto»*); once expired, REMOTIX stops and the full is needed. ⇒ The user count disappears from the program.
     ⚠ Claude advised 30 days for business products; the user's choice: 14.
   - **tied to the hardware signature** (UUID and serial of the motherboard, exact comparison), **no email**;
   - **no duplicates**: two active copies of the same trial ⇒ the trial is disabled (nobody paid, no
     victim to protect).
   - ✅ **The fingerprint is derived from several hardware elements** (the user, 9 Oct: *«l'impronta si ricava da elementi
     multipli dell'hardware»*; the client generates it, so it is always there): UUID and serial of the motherboard,
     serial of the system disk, address of the network card. The **factory strings** («To be filled by
     O.E.M.», «Not Specified», all zeros) **are discarded** before the computation: otherwise different machines
     would have the same fingerprint and an innocent customer would look like a duplicate. ⇒ In the rare case where
     nothing distinctive remains, the trial **does not start on its own**: «questa macchina non può avviare la prova
     automatica: scrivici», and the seller activates it by hand from the licence tool. **No email.**
     ⚠ Declared: a **new** virtual machine in the cloud has a new fingerprint, hence a new trial; it is
     accepted.
4. The trial stays «best effort»: throwaway emails and new virtual machines in the cloud get around it.
5. **One recovery every 30 days**, and what is enough for you to unblock it by hand.
6. **Emails sent from the VPS** with their delivery risk, and recovery by hand if an email does not arrive.
7. **The gold must still make itself heard at least every 14 days.**
   ✅ **9 Oct, the gold simplified** (the user): no expiry, no warning, no renewal; **one per
   machine** stays. Two active copies ⇒ **warning to the seller with all the details** and **the seller disables one
   of the two** (the user: *«devo avere la facoltà di disabilitare uno dei doppioni»*). Without network: **14 days**,
   like the others (the user, 9 Oct; Claude proposed 90). Rules in `SPECIFICHE.md` §15.1.
   ✅ **9 Oct: activation codes are never reused** (the user). Consequence (Claude): the recovery, which
   in the agreed design asked to paste the code again, uses instead the **licence number** (not secret) plus
   the confirmation by email; the code activates only once. `SPECIFICHE.md` §15.3.
8. For how long buyers' emails, trial fingerprints and logs are kept (privacy).
   ✅ **9 Oct: 2 years** (the user: *«almeno 2 anni»*), ⚠ but as a **ceiling, not as a minimum** (Claude's correction: under
   the GDPR personal data are kept **no longer** than necessary, and the period must be written in the privacy notice):
   - buyer's email, licences and activation log: **2 years from the end of the relationship** (last
     expiry of the full);
   - trial fingerprints: **2 years from the trial** (they serve not to give a second one);
   - data of a duplication (IP, RDAP, machine names, hardware): **6 months** from the choice, then only
     «duplication of day X, resolved like this» remains;
   - ⚠ invoices and tax documents follow the law (in Italy 10 years), but whoever collects keeps them: it is decided with the
     payment. ⛔ Claude is not a lawyer: the privacy notice must be checked before selling.
9. When to do the TPM; cloud integrations only if customers ask for them.
   ✅ **9 Oct: the TPM leaves the plan** (the user: *«non credo che possiamo farci affidamento: non tutte le VM sono
   configurate per avere il TPM»*). Consistent with the rule «no exceptions per compositor»: a protection that
   exists only on part of the machines does not hold up the design. The design holds **the same everywhere** (key in a
   file, daily ticket, customer's choice). It reopens only if duplications become a real
   problem. Cloud integrations are out too.

✅ **The estimate of §8 was redone on 9 Oct: ~122 hours** (it was ~72).
