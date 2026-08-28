//! REMOTIX — server RDP per Linux.
//!
//! Il grosso del progetto vive qui, in libreria, e non nell'eseguibile: cosi'
//! gli strumenti di prova di ciascuna fase possono usare gli stessi moduli del
//! server, invece di essere codice usa e getta che dimostra qualcosa di
//! diverso da quello che poi si spedisce.

pub mod autenticazione;
pub mod cattura;
pub mod colore;
pub mod controllo;
pub mod desktop;
pub mod egfx;
pub mod h264;
pub mod palco;
pub mod portiere;
pub mod sentinella;
pub mod sessione;
pub mod screencast;
pub mod tastiera;
pub mod testcard;
pub mod tls;
pub mod uscita;
