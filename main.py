import requests
from bs4 import BeautifulSoup

# ⛔ UWAGA: Dane wrażliwe wpisane na stałe – NIEBEZPIECZNE na publicznym repo!
LOGIN_EMAIL = "twoj@email.com"
LOGIN_PASSWORD = "Sdkfz251"
TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ123"
TELEGRAM_CHAT_ID = "123456789"

def send_log(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Nie udało się wysłać loga na Telegram: {e}")

def login():
    try:
        session = requests.Session()
        login_page = session.get("https://strefainwestorow.pl/user/login")
        soup = BeautifulSoup(login_page.text, "html.parser")

        # Szukamy dynamicznych ukrytych pól (Drupal)
        form = soup.find("form", {"id": "user-login-form"})
        if not form:
            send_log("❌ Nie znaleziono formularza logowania.")
            return

        form_build_id = form.find("input", {"name": "form_build_id"})["value"]
        form_id = form.find("input", {"name": "form_id"})["value"]
        honeypot_time = form.find("input", {"name": "honeypot_time"})["value"]

        payload = {
            "name": LOGIN_EMAIL,
            "pass": LOGIN_PASSWORD,
            "form_id": form_id,
            "form_build_id": form_build_id,
            "honeypot_time": honeypot_time,
            "op": "Zaloguj"
        }

        response = session.post("https://strefainwestorow.pl/user/login", data=payload)

        if "Wyloguj" in response.text or "/user/logout" in response.text:
            send_log("✅ Zalogowano pomyślnie na strefainwestorow.pl")
        else:
            send_log("❌ Logowanie nieudane – brak frazy 'Wyloguj' w odpowiedzi.")
    except Exception as e:
        send_log(f"❌ Błąd w funkcji login(): {str(e)}")

if __name__ == "__main__":
    send_log("🟢 Skrypt uruchomiony!")
    login()
