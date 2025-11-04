import user_login as ul
import calendarapi
import business
import time

def main():
    try:
        # variabili
        login_payload = {
            "username": ul.username(),
            "password": ul.password()
        }

        date = business.weeks_range(6) # {"start": "2025-10-01", "end": "2025-12-30"}

        response = business.get_calendar(login_payload, date)

        creds = calendarapi.accesso()

        calendarapi.sync_calendar(creds, date)

    except Exception as error:
        print(f"Errore durante l'esecuzione: {error}")


if __name__ == "__main__":
    while True:
        main()
        time.sleep(1800)

