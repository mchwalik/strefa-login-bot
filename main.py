import os
import requests
from bs4 import BeautifulSoup

LOGIN_URL = "https://strefainwestorow.pl/user/login"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def send_telegram_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"❌ Błąd Telegrama [{response.status_code}]: {response.text}")
    except Exception as e:
        print(f"❌ Wyjątek przy wysyłaniu do Telegrama: {e}")

def login():
    send_telegram_message("🟢 Skrypt uruchomiony!")
    email = os.getenv("LOGIN_EMAIL")
    password = os.getenv("LOGIN_PASSWORD")
    if not email or not password:
        send_telegram_message("❌ Brakuje danych logowania (LOGIN_EMAIL, LOGIN_PASSWORD)")
        return
    try:
        session = requests.Session()
        response = session.get(LOGIN_URL, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        form = soup.find("form", {"id": "user-login-form"})
        if not form:
            send_telegram_message("❌ Nie znaleziono formularza logowania.")
            return

        form_build_id = form.find("input", {"name": "form_build_id"})
        form_id = form.find("input", {"name": "form_id"})
        honeypot = form.find("input", {"name": "honeypot_time"})

        if not all([form_build_id, form_id, honeypot]):
            send_telegram_message("❌ Nie znaleziono wymaganych ukrytych pól.")
            return

        payload = {
            "name": email,
            "pass": password,
            "form_build_id": form_build_id["value"],
            "form_id": form_id["value"],
            "honeypot_time": honeypot["value"]
        }

        post_response = session.post(LOGIN_URL, data=payload, headers=HEADERS)
        send_telegram_message(f"📡 Status logowania: {post_response.status_code}")

        if "/user/logout" in post_response.text:
            send_telegram_message("✅ Logowanie powiodło się!")
        else:
            send_telegram_message("❌ Logowanie nie powiodło się.")

    except Exception as e:
        send_telegram_message(f"❌ Wyjątek podczas logowania: {str(e)}")

if __name__ == "__main__":
    login()
