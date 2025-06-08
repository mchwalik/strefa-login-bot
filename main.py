import requests
from bs4 import BeautifulSoup
import time
import os

# === KONFIGURACJA ===
LOGIN_URL = "https://strefainwestorow.pl/user/login"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

USERNAME = os.getenv("LOGIN_EMAIL")  # np. "marcin.chwalik@gmail.com"
PASSWORD = os.getenv("LOGIN_PASSWORD")  # np. "Sdkfz251"

# === FUNKCJE ===

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Nie ustawiono TELEGRAM_BOT_TOKEN lub TELEGRAM_CHAT_ID")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ Nie można wysłać do Telegrama: {e}")

def login():
    send_telegram("🔐 Rozpoczynam logowanie do strefainwestorow.pl...")

    session = requests.Session()
    try:
        response = session.get(LOGIN_URL)
    except Exception as e:
        send_telegram(f"❌ Błąd pobierania strony logowania: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    form = soup.find("form", {"id": "user-login"})
    if not form:
        send_telegram("❌ Nie znaleziono formularza logowania!")
        return

    form_build_id = form.find("input", {"name": "form_build_id"})["value"]
    form_id = form.find("input", {"name": "form_id"})["value"]

    payload = {
        "name": USERNAME,
        "pass": PASSWORD,
        "form_build_id": form_build_id,
        "form_id": form_id,
        "op": "Zaloguj"
    }

    try:
        post_response = session.post(LOGIN_URL, data=payload)
    except Exception as e:
        send_telegram(f"❌ Błąd podczas wysyłania formularza: {e}")
        return

    if "Wyloguj" in post_response.text or "/user/logout" in post_response.text:
        send_telegram("✅ Zalogowano pomyślnie do strefainwestorow.pl!")
    else:
        send_telegram("❌ Logowanie nie powiodło się. Sprawdź dane logowania.")

# === START SKRYPTU ===

if __name__ == "__main__":
    print("🟢 Skrypt uruchomiony!")
    send_telegram("🚀 Skrypt uruchomiony – zaczynam procedurę logowania.")
    login()
