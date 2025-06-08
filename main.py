import os
import requests
from bs4 import BeautifulSoup

# Wpisane na sztywno dane do testów
TELEGRAM_BOT_TOKEN = "tu_wstaw_token"
TELEGRAM_CHAT_ID = "tu_wstaw_chat_id"
LOGIN_EMAIL = "tu_wstaw_email"
LOGIN_PASSWORD = "tu_wstaw_haslo"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ Błąd wysyłania do Telegrama: {e}")

def login():
    send_telegram_message("🔐 Rozpoczynam logowanie...")

    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = session.get("https://strefainwestorow.pl/user/login", headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Wyślij fragment HTML strony logowania
        html_preview = soup.prettify()[:1000]
        send_telegram_message("📄 HTML strony logowania:\n" + html_preview)

        form = soup.find("form")
        if not form:
            send_telegram_message("❌ Nie znaleziono formularza logowania.")
            return

        data = {}
        for input_tag in form.find_all("input"):
            name = input_tag.get("name")
            value = input_tag.get("value", "")
            if name:
                data[name] = value

        data["name"] = LOGIN_EMAIL
        data["pass"] = LOGIN_PASSWORD

        post_url = "https://strefainwestorow.pl" + form.get("action", "/user/login")
        login_response = session.post(post_url, data=data, headers=headers)

        if "Wyloguj" in login_response.text:
            send_telegram_message("✅ Logowanie zakończone sukcesem!")
        else:
            send_telegram_message("❌ Logowanie nie powiodło się.")

    except Exception as e:
        send_telegram_message(f"❌ Błąd: {str(e)}")

if __name__ == "__main__":
    send_telegram_message("🟢 Skrypt wystartował – próbuję logowania.")
    login()
