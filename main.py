import os
import requests
from bs4 import BeautifulSoup
import traceback

USERNAME = os.getenv("LOGIN_EMAIL")
PASSWORD = os.getenv("LOGIN_PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Brak danych do wysłania wiadomości na Telegram.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ Błąd wysyłania do Telegrama: {e}")

def login():
    try:
        send_telegram("🔐 Rozpoczynam logowanie przez formularz...")

        session = requests.Session()
        login_page = session.get("https://strefainwestorow.pl/user/login")
        soup = BeautifulSoup(login_page.text, "html.parser")
        form = soup.find("form", {"id": "user-login"})
        if not form:
            send_telegram("❌ Nie znaleziono formularza logowania.")
            return

        form_build_id = form.find("input", {"name": "form_build_id"})
        if not form_build_id:
            send_telegram("❌ Nie znaleziono `form_build_id` w formularzu.")
            return

        payload = {
            "name": USERNAME,
            "pass": PASSWORD,
            "form_build_id": form_build_id["value"],
            "form_id": "user_login_form",
            "op": "Zaloguj"
        }

        response = session.post("https://strefainwestorow.pl/user/login", data=payload)

        if "Wyloguj" in response.text:
            send_telegram("✅ Logowanie zakończone sukcesem!")
        else:
            send_telegram("❌ Logowanie się nie powiodło – brak 'Wyloguj' w treści strony.")
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(response.text)

    except Exception as e:
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
        send_telegram(f"❌ Wyjątek podczas logowania:\n{error_message}")

if __name__ == "__main__":
    send_telegram("🚀 Skrypt uruchomiony – rozpoczynam diagnostykę.")
    
    if not USERNAME or not PASSWORD:
        send_telegram("❌ Brak zmiennych środowiskowych `LOGIN_EMAIL` lub `LOGIN_PASSWORD`.")
    elif not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Brakuje TELEGRAM_BOT_TOKEN lub TELEGRAM_CHAT_ID – nie mogę wysyłać powiadomień.")
    else:
        login()
