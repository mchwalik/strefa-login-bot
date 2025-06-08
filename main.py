import os
import requests
from bs4 import BeautifulSoup

# Dane z Railway (zmienne środowiskowe)
EMAIL = os.getenv("LOGIN_EMAIL")
PASSWORD = os.getenv("LOGIN_PASSWORD")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_log(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

def main():
    send_log("🔹 Rozpoczynam logowanie...")

    login_url = "https://strefainwestorow.pl/user/login"
    session = requests.Session()
    resp = session.get(login_url)
    if resp.status_code != 200:
        return send_log(f"❌ Błąd pobierania login page: {resp.status_code}")

    send_log("✅ Strona logowania pobrana.")

    soup = BeautifulSoup(resp.text, "html.parser")
    token = soup.find("input", {"name": "form_build_id"})
    form_build_id = token["value"] if token else None

    send_log(f"🎯 CSRF token: {form_build_id}" if form_build_id else "⚠️ Brak CSRF tokena")

    payload = {
        "name": EMAIL,
        "pass": PASSWORD,
        "form_id": "user_login_form",
        "op": "Zaloguj",
    }
    if form_build_id:
        payload["form_build_id"] = form_build_id

    resp2 = session.post(login_url, data=payload)
    if resp2.status_code != 200:
        return send_log(f"❌ Błąd POST login: {resp2.status_code}")

    if "Zaloguj się" in resp2.text:
        return send_log("❌ Logowanie nieudane – strona ponownie oferuje logowanie.")

    send_log("✅ Zalogowano pomyślnie!")

if __name__ == "__main__":
    main()
