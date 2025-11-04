# GEOP on Google Calendar

Questo progetto sincronizza il calendario accademico della piattaforma GEOP (usata da ITSAR) con il tuo Google Calendar.

Lo script è progettato per essere eseguito su un dispositivo a bassa potenza (come un Raspberry Pi Zero W) e aggiornarsi costantemente, assicurando che il tuo Google Calendar rifletta sempre gli ultimi dati di GEOP.

<p align="center">
  <img src="https://raw.githubusercontent.com/bogdancaves/GEOP-on-Google-Calendar/main/.github/assets/geop.png" alt="Calendario GEOP originale" width="45%">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="https://raw.githubusercontent.com/bogdancaves/GEOP-on-Google-Calendar/main/.github/assets/google.png" alt="Calendario Google sincronizzato" width="45%">
</p>

## Obiettivo

L'obiettivo è replicare fedelmente il calendario GEOP su Google Calendar, includendo:

  * Lezioni future
  * Dettagli su Aule e Docenti
  * Stato di Presenza/Assenza
  * Argomenti delle lezioni
  * Evidenziazione di Esami e Prime Lezioni
  * Aggiornamenti dinamici (es. cambio aula)

## Come Funziona

Il processo è diviso in quattro fasi principali:

### 1\. Reperimento Dati (`business.py`)

Lo script simula un accesso utente alla piattaforma GEOP.

1.  Apre una `requests.Session`.
2.  Esegue il login inviando le credenziali (username e password) all'endpoint `login.asp`.
3.  Una volta autenticato, effettua una richiesta POST all'endpoint `fullcalendar_events_alunno.asp` inviando l'intervallo di date desiderato.
4.  La risposta JSON grezza ricevuta da GEOP viene salvata nel file `calendar.json`.

### 2\. Parsing dei Dati (`parser.py`)

I dati grezzi di GEOP non sono puliti. Questo modulo si occupa di trasformarli.

  * **`parse_json`**: Legge il file `calendar.json`, scartando eventi non necessari come quelli con `id=0` o le "SOSPENSIONI DIDATTICHE".
  * **`parse_tooltip`**: La maggior parte delle informazioni utili (Materia, Aula, Docente, Argomento) è contenuta in una stringa HTML non formattata nel campo `tooltip`. Questa funzione usa le espressioni regolari (regex) per estrarre e strutturare questi dati in un dizionario Python pulito.
  * **`format_event`**: Converte il dizionario dell'evento pulito in un oggetto formattato secondo le specifiche dell'API di Google Calendar. Qui vengono impostati `summary` (titolo), `location`, `description` e il `colorId` (colore) dell'evento, che cambia in base allo stato (Esame, Prima Lezione, Presente, Assente).

### 3\. Integrazione Google Calendar (`calendarapi.py`)

Questo modulo gestisce tutta la comunicazione con Google.

  * **`accesso`**: Gestisce l'autenticazione OAuth 2.0. Al primo avvio, apre il browser per chiedere l'autorizzazione all'utente. Utilizza il file `credentials.json` (che devi scaricare da Google Cloud) e salva i token di accesso in `token.json` per gli accessi futuri.
  * **`read_calendar`**: Legge gli eventi *già presenti* su Google Calendar nell'intervallo di date specificato. Filtra solo gli eventi rilevanti (es. quelli che iniziano con "UFS", "UFT", "PW", "Extra Orario") e ignora i weekend.
  * **`add_calendar` / `delete_calendar` / `update_calendar`**: Funzioni di utilità per creare, eliminare e aggiornare singoli eventi sul calendario.

### 4\. Sincronizzazione (`calendarapi.py` e `main.py`)

Questa è la logica principale del progetto.

1.  **`sync_calendar`**: Esegue un confronto tra gli eventi locali (letti da `calendar.json` e processati) e gli eventi remoti (letti da Google Calendar).
      * **Aggiunta**: Se un evento è presente nel JSON ma non su Google, viene aggiunto.
      * **Eliminazione**: Se un evento è su Google ma *non* più presente nel JSON, viene eliminato.
      * **Aggiornamento**: Se un evento esiste in entrambi, lo script controlla se ci sono state modifiche. Aggiorna l'evento su Google se l'aula (`location`) è cambiata o se lo stato (`tooltip`) è passato da "Registro lezione..." a "PRESENTE" o "ASSENTE".
2.  **`main.py`**: È lo script di avvio. Contiene un loop infinito (`while True`) che riesegue l'intero processo (login, fetch, parse, sync) ogni 1800 secondi (30 minuti), mantenendo il calendario costantemente aggiornato.

## Installazione e Avvio

### 1\. Prerequisiti

  * Python 3.x
  * Credenziali di accesso per la piattaforma GEOP.
  * Un account Google.

### 2\. Setup

1.  **Clona il repository:**

    ```bash
    git clone https://github.com/bogdancaves/GEOP-on-Google-Calendar.git
    cd GEOP-on-Google-Calendar
    ```

2.  **Installa le dipendenze:**

    ```bash
    pip install -r requirements.txt
    ```

    Le dipendenze principali includono `google-api-python-client`, `google-auth-oauthlib`, `requests` e `tzdata`.

3.  **Configura l'API di Google Calendar:**

      * Vai alla [Google Cloud Console](https://console.cloud.google.com/).
      * Crea un nuovo progetto (es. "GEOP on Calendar").
      * Vai su "API e servizi" \> "Libreria" e abilita la **Google Calendar API**.
      * Vai su "API e servizi" \> "Schermata consenso OAuth", scegli "Esterno" e completa i campi richiesti (puoi inserire dati di test, è solo per uso personale). Aggiungi il tuo account Google come utente di test.
      * Vai su "API e servizi" \> "Credenziali", fai clic su "Crea credenziali" \> "ID client OAuth".
      * Scegli "Applicazione desktop" come tipo di applicazione.
      * Fai clic su "Scarica JSON". Rinomina il file scaricato in `credentials.json` e posizionalo nella cartella principale del progetto.

4.  **Configura le credenziali GEOP:**

      * Crea un nuovo file nella cartella principale chiamato `user_login.py`.
      * Questo file *non* è tracciato da Git per proteggere le tue credenziali.
      * Inserisci il seguente contenuto, sostituendo con i tuoi dati reali:


    ```python
    # user_login.py
    def username():
        return "TUA_EMAIL_GEOP"

    def password():
        return "TUA_PASSWORD_GEOP"
    ```

### 3\. Primo Avvio

1.  **Esegui lo script:**

    ```bash
    python main.py
    ```

2.  **Autorizzazione Google:**

      * Al primo avvio, lo script si fermerà e aprirà automaticamente una finestra del browser.
      * Accedi con l'account Google che hai impostato come utente di test.
      * Concedi all'applicazione i permessi per "visualizzare, modificare ed eliminare" gli eventi sul tuo calendario.
      * Dopo l'autorizzazione, lo script creerà un file `token.json` nella cartella. Questo file memorizza la tua autorizzazione, così non dovrai ripetere questo passaggio.

3.  **Fatto!**
    Lo script ora è in esecuzione. Eseguirà la prima sincronizzazione e continuerà a controllare gli aggiornamenti ogni 30 minuti.

## Struttura dei File

```
.
├── geop-on-calendar/
│   ├── main.py           # Script principale, esegue il loop di sync
│   ├── business.py       # Gestisce login e scraping da GEOP
│   ├── parser.py         # Pulisce e formatta i dati JSON
│   ├── calendarapi.py    # Gestisce l'autenticazione e le API di Google Calendar
│   ├── user_login.py     # (DA CREARE) Le tue credenziali GEOP (ignorato da Git)
│   ├── requirements.txt  # Dipendenze Python
│   ├── credentials.json  # (DA SCARICARE) Credenziali API Google
│   └── token.json        # (GENERATO) Token di accesso Google
└── ...
```