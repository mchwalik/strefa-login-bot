import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ===== KONFIGURACJA =====
LOGIN_EMAIL = "mchwalik@op.pl"
LOGIN_PASSWORD = "Sdkfz251"
TELEGRAM_BOT_TOKEN = "6649065956:AAG7SHayTP-oAYJKNYEvJsc62v_07dLQuXk"
TELEGRAM_CHAT_ID = "5332477911"
LOG_FILE = "log.txt"
LOGIN_URL = "https://strefainwestorow.pl/user/login"

# ===== FUNKCJE =====
def log(text):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {text}\n")

def notify_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, data=payload)
        log(f"🔔 Telegram response: {response.status_code} {response.text}")
    except Exception as e:
        log(f"❌ Błąd wysyłania Telegram: {e}")

def login():
    notify_telegram("🟢 Skrypt uruchomiony!")
    log("🟢 Skrypt uruchomiony!")
    
    session = requests.Session()
    
    try:
        response = session.get(LOGIN_URL)
        log(f"🌐 GET {LOGIN_URL} → {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")

        form = soup.find("form", {"id": "user-login"})
        if not form:
            msg = "❌ Nie znaleziono formularza logowania."
            notify_telegram(msg)
            log(msg)
            return

        form_build_id = form.find("input", {"name": "form_build_id"})
        if not form_build_id:
            msg = "❌ Nie znaleziono form_build_id."
            notify_telegram(msg)
            log(msg)
            return

        payload = {
            "name": LOGIN_EMAIL,
            "pass": LOGIN_PASSWORD,
            "form_id": "user_login_form",
            "form_build_id": form_build_id["value"]
        }

        login_response = session.post(LOGIN_URL, data=payload)
        log(f"📡 POST {LOGIN_URL} → {login_response.status_code}")

        if "Wyloguj" in login_response.text or "/user/logout" in login_response.text:
            msg = "✅ Zalogowano pomyślnie!"
        else:
            msg = "❌ Logowanie nie powiodło się."

        notify_telegram(msg)
        log(msg)

    except Exception as e:
        notify_telegram(f"❌ Wyjątek: {str(e)}")
        log(f"❌ Wyjątek: {str(e)}")

# ===== START =====
if __name__ == "__main__":
    login()
