# https://tls.peet.ws/api/all tls fingerprint test
import parser
import requests
import datetime
# import logging


def get_calendar(login_payload: dict, date: dict) -> requests.Response:
    """
    Interroga l'API di GEOP per ottenere il calendario dell'utente in un intervallo di date.

    Args:
        login_payload (dict): Dizionario con le credenziali per accedere a GEOP.\n
                            Deve contenere le chiavi "username" e "password".

        date (dict): Dizionario contenente le date di inizio "start" e fine "end" in formato YYYY-MM-DD.\n
                    L'endpoint interpreta "end" come *esclusivo*: l'ultimo giorno è quello precedente.

    Returns:
        requests.Response: Oggetto Response con il calendario richiesto.\n
        La risposta viene salvata nel file calendar.json.

    Raises:
        RuntimeError: Se la richiesta di login o l'accesso al calendario falliscono.

    Example:
        login_payload = {"username": "utente", "password": "password123"}\n
        date_range = {"start": "2025-03-24", "end": "2025-03-31"}\n
        response = get_calendar(login_payload, date_range)\n
        print(response.json())  # Stampa il calendario in formato JSON   
    """

    login_url = "https://itsar.registrodiclasse.it/geopcfp2/update/login.asp"
    xhr_url = "https://itsar.registrodiclasse.it/geopcfp2/json/fullcalendar_events_alunno.asp"

    session = requests.Session()

    # post invia dati all'api - non serve l'oggetto che restituisce
    login_status = session.post(login_url, data=login_payload) 

    # nel caso che GEOP dovesse fallire
    if login_status.status_code != 200:
        raise RuntimeError(f"L'URL {login_url} ha risposto con codice di errore: {login_status.status_code}")

    response = session.post(xhr_url, data = date)
    print(response.headers.get("Content-Type")) #: text/html.
    response.encoding = 'utf-8' 

    # nel caso che le credenziali fossero sbagliate
    if response.status_code != 200:
        raise RuntimeError(
            f"L'URL {xhr_url} ha risposto con codice di errore: {response.status_code}\n"
            "Controlla la correttezza delle credenziali"
        )
    
    parser.write_json(response)

    return response


def weeks_range(n_weeks: int) -> dict:
    """
    Calcola un intervallo di date basato sulla settimana corrente e un numero di settimane.

    Args:
        n_weeks (int): Numero di settimane da aggiungere alla data di inizio.

    Returns:
        dict: Dizionario contenente le date di inizio "start" e fine "end" in formato YYYY-MM-DD.\n
            "start" è il lunedì della settimana corrente,\n 
            "end" è n_weeks dopo "start".

    Raises:
        ValueError: Se viene passato in n_weeks un valore non intero o positivo.
    """
    date_format = '%Y-%m-%d'
    max_end_date = datetime.datetime.strptime("2026-08-04", date_format).date() # aggiornato la data di scansione massima
    
    if not isinstance(n_weeks, int) or n_weeks <= 0:
        raise ValueError("n_weeks deve essere un numero intero positivo.")

    today = datetime.date.today()

    # calcola la data di inizio e di fine
    start_date = today - datetime.timedelta(days=today.weekday())
    min_end_date = start_date + datetime.timedelta(weeks=n_weeks)
    
    end_date = min(min_end_date, max_end_date)

    # formatta le date come stringhe nel formato YYYY-MM-DD
    start_str = start_date.strftime(date_format)
    end_str = end_date.strftime(date_format)

    date_range = {
        'start': start_str,
        'end': end_str,
    }
    return date_range

# maybe funzione per il login