import json
import re
from requests import Response # importo la classe per dichiarare il tipo di oggetto che voglio riceveres


def parse_json(json_data: list) -> list:
    """
    Elabora una lista di eventi (dizionari): 
        - Estrae e formatta il campo "tooltip"
        - Scarta gli eventi con id==0 o la cui "Materia" contiene "SOSPENSIONE DIDATTICA"s.
    
    Args:
        json_data (list): Lista di dizionari che rappresentano gli eventi.
    
    Returns:
        list: Una lista di dizionari con i dati formattati.
    """
    parsed_events = []
    for event in json_data:
        # scarta l'evento se l'id è 0 o se la materia contiene "SOSPENSIONE DIDATTICA"
        if event.get("id") == 0 or event.get("title", "").strip().startswith("SOSPENSIONE DIDATTICA"):
            continue

        if "tooltip" in event:
            tooltip_text = event["tooltip"]
            parsed_tooltip = parse_tooltip(tooltip_text)
            parsed_event = {**event, **parsed_tooltip}
            parsed_events.append(parsed_event)
            
    return parsed_events


def parse_tooltip(tooltip: str) -> dict:
    """
    Formatta la stringa tooltip estraendo coppie chiave-valore per chiavi note.
    
    Args:
        tooltip (str): Il testo del tooltip contenente informazioni in formato chiave-valore.
        
    Returns:
        dict: Un dizionario con le coppie chiave-valore estratte.
    """
    result = {}

    # splitta per <br> e pulisce le righe
    lines = [line.strip() for line in tooltip.split("<br>") if line.strip()]
    
    # la prima riga è lo stato (es. "PRESENTE")
    if lines:
        result["tooltip"] = lines[0]
    
    # unisce il resto in un'unica stringa
    rest = " ".join(lines[1:])
    
    # definisce le chiavi attese da estrarre 
    expected_keys = ["Materia", "Aula", "Corsi", "Docente", "Argomento", "Modalit&agrave;"]

    # Costruisce un'espressione regolare per trovare coppie "Chiave: Valore" nel testo
    # Il pattern cerca:
    # 1. Una delle chiavi presenti in expected_keys seguita da ":"
    # 2. Il valore corrispondente, che può contenere qualsiasi carattere fino a quando:
    #    - Non incontra un'altra chiave seguita da ":" (cioè l'inizio di un'altra coppia chiave-valore)
    #    - Oppure fino alla fine della stringa ($)
    pattern = r"(" + "|".join(expected_keys) + r"):\s*(.*?)(?=\s+(?:" + "|".join(expected_keys) + r"):\s*|$)"

    # Applica il pattern per trovare tutte le coppie chiave-valore nel testo
    matches = re.findall(pattern, rest, flags=re.IGNORECASE)

    for key, value in matches:
        key = key.strip()
        value = value.strip()

        # normalizza la chiave "Modalit&agrave;" in "Modalità" e rimuove il trattino iniziale se presente
        if key.lower() == "modalit&agrave;":
            key = "Modalità"
            if value.startswith("-"):
                value = value[1:].strip()

        result[key] = value
    
    return result


def format_event(event: dict) -> dict:
    """
    Formatta i dati di un evento in un dizionario compatibile con l'API di Google Calendar.

    Args:
        event (dict): Dizionario contenente i dettagli dell'evento con le seguenti chiavi:
            - "Materia" (str):                  Nome della materia
            - "Docente" (str):                  Nome del docente
            - "Aula" (str):                     Aula in cui si tiene la lezione
            - "Modalità" (str, opzionale):      Modalità della lezione (es. "Fad MISTA")
            - "Argomento" (str, opzionale):     Argomento trattato nella lezione
            - "tooltip" (str):                  Testo che riassume lo stato dell'evento (es. "PRESENTE", "ASSENTE")
            - "start" (str):                    Data e ora di inizio dell'evento in formato ISO 8601 (es. "2025-03-25T08:40:00")
            - "end" (str):                      Data e ora di fine dell'evento in formato ISO 8601
            - "ClasseEvento" (str, opzionale):  Classe dell'evento (es. "esame", "prima_lezione", etc.)
    
    Returns:
        dict: Dizionario formattato per l'uso con l'API di Google Calendar
    """
    summary = f"{event['Materia']} - {event['Docente']}"

    if event.get('Modalità') is None:
        location = event.get('Aula')
    else:
        location = f"{event['Aula']} - {event["Modalità"]}"

    if event.get('Argomento') is None:
        description = f"{event['tooltip']} - {event['Materia']} - {event['Docente']} - {event['Aula']}"
    else:
        description = f"{event['tooltip']} - {event['Argomento']}"

    start_time = event['start']
    end_time = event['end']

    classe = event.get("ClasseEvento", "").lower()
    tooltip = event.get("tooltip", "").upper()
    
    if "esame" in classe:
        color = "3"
    elif "prima_lezione" in classe:
        color = "7"
    elif "PRESENTE" in tooltip:
        color = "10"
    elif "ASSENTE" in tooltip:
        color = "11"
    else:
        color = "8"

    event_details = {
        'summary': summary,
        'location': location,
        'description': description,
        "colorId": color,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Europe/Rome',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Europe/Rome',
        },
        "reminders": {
            "useDefault": False,
        }
    }
    return event_details


'''
'1': Sfondo azzurro (#a4bdfc), testo nero (#1d1d1d)
'2': Sfondo verde chiaro (#7ae7bf), testo nero (#1d1d1d)
'3': Sfondo lilla (#dbadff), testo nero (#1d1d1d)
'4': Sfondo rosa (#ff887c), testo nero (#1d1d1d)
'5': Sfondo giallo (#fbd75b), testo nero (#1d1d1d)
'6': Sfondo arancione chiaro (#ffb878), testo nero (#1d1d1d)
'7': Sfondo turchese (#46d6db), testo nero (#1d1d1d)
'8': Sfondo grigio chiaro (#e1e1e1), testo nero (#1d1d1d)
'9': Sfondo blu scuro (#5484ed), testo nero (#1d1d1d)
'10': Sfondo verde scuro (#51b749), testo nero (#1d1d1d)
'11': Sfondo rosso (#dc2127), testo nero (#1d1d1d)
'''


def write_json(response: Response):
    with open("calendar.json", "w", encoding="utf-8") as json_file:
        json.dump(
            parse_json(response.json()), # 
            json_file, indent=4, ensure_ascii=False
            )
        

def read_json(nome_file):
    with open(nome_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data
