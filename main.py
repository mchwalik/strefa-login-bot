import os
import requests
from bs4 import BeautifulSoup

# Konfiguracja — można zmienić na stałe
TELEGRAM_BOT_TOKEN = "tu_wstaw_token"
TELEGRAM_CHAT_ID = "tu_wstaw_chat_id"
LOGIN_EMAIL = "tu_wstaw_email"
LOGIN_PASSWORD = "tu_wstaw_haslo"

def log(msg):
    print(msg)
    try:
        with open(".log.txt", "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            log(f"❌ Błąd Telegrama [{response.status_code}]: {response.text}")
    except Exception as e:
        log(f"❌ Wyjątek przy wysyłce Telegrama: {str(e)}")

def login():
    send_telegram_message("🔐 Rozpoczynam logowanie...")
    log("🔐 Rozpoczynam logowanie...")

    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = session.get("https://strefainwestorow.pl/user/login", headers=headers)
        log(f"📡 Status logowania: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")

        # Podgląd HTML do logu
        html_preview = soup.prettify()[:1000]
        log("🔎 HTML PREVIEW:\n" + html_preview)

        send_telegram_message("📄 HTML podgląd wysłany do logu Railway (plik .log.txt)")

        form = soup.find("form")
        if not form:
            log("❌ Brak formularza logowania.")
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
            log("✅ Logowanie zakończone sukcesem!")
            send_telegram_message("✅ Logowanie zakończone sukcesem!")
        else:
            log("❌ Logowanie nie powiodło się.")
            send_telegram_message("❌ Logowanie nie powiodło się.")

    except Exception as e:
        log(f"❌ Błąd w login(): {str(e)}")
        send_telegram_message(f"❌ Błąd: {str(e)}")

if __name__ == "__main__":
    log("🟢 Skrypt uruchomiony!")
    send_telegram_message("🟢 Skrypt uruchomiony!")
    login()
