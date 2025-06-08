import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 🔐 Dane logowania i Telegram (hardcoded)
LOGIN_EMAIL = "marcin.chwalik@gmail.com"
LOGIN_PASSWORD = "Sdkfz251"
TELEGRAM_BOT_TOKEN = "7958150824:AAH4-Edu3YIQV9d-rZRHdq7rp_JI222OmGY"
TELEGRAM_CHAT_ID = "7647211011"

# ✏️ Logger do pliku
def log_local(msg):
    with open("log.txt", "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

# 📤 Logger do Telegrama
def send_log(msg):
    try:
        log_local(msg)
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg
            }
        )
    except Exception as e:
        log_local(f"❌ Błąd wysyłania do Telegrama: {e}")

# 🔐 Logowanie do strefainwestorow.pl
def login():
    send_log("🔐 Rozpoczynam logowanie...")

    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    try:
        res_get = session.get("https://strefainwestorow.pl/user/login", headers=headers)
        send_log(f"📡 Status logowania: {res_get.status_code}")
    except Exception as e:
        return send_log(f"❌ Błąd połączenia: {e}")

    if res_get.status_code != 200:
        return send_log(f"❌ Błąd pobierania formularza: HTTP {res_get.status_code}")

    soup = BeautifulSoup(res_get.text, "html.parser")
    form = soup.find("form", {"id": "user-login"})
    if not form:
        return send_log("❌ Nie znaleziono formularza logowania.")

    data = {"name": LOGIN_EMAIL, "pass": LOGIN_PASSWORD}
    for hidden in form.find_all("input", {"type": "hidden"}):
        name = hidden.get("name")
        val = hidden.get("value", "")
        if name:
            data[name] = val

    post_url = "https://strefainwestorow.pl" + form.get("action", "/user/login")
    res_post = session.post(post_url, data=data, headers=headers)
    if res_post.status_code != 200:
        return send_log(f"❌ Błąd logowania (kod HTTP {res_post.status_code})")

    if "Wyloguj" in res_post.text or "/user/logout" in res_post.text:
        send_log("✅ Logowanie zakończone sukcesem!")
    else:
        send_log("❌ Logowanie nie powiodło się – fraza 'Wyloguj' nie została znaleziona.")

if __name__ == "__main__":
    send_log("🟢 Skrypt wystartował – radę logowania.")
    login()
