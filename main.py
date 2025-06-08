import requests
from bs4 import BeautifulSoup

# 🔐 Dane logowania i Telegram (hardcoded)
LOGIN_EMAIL = "marcin.chwalik@gmail.com"
LOGIN_PASSWORD = "Sdkfz251"
TELEGRAM_BOT_TOKEN = "7958150824:AAH4-Edu3YIQV9d-rZRHdq7rp_JI222OmGY"
TELEGRAM_CHAT_ID = "7647211011"

PORTFEL_URLS = [
    "https://strefainwestorow.pl/portfel_strefy_inwestorow",
    "https://strefainwestorow.pl/portfel_petard"
]

def send_log(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg
            }
        )
    except Exception as e:
        print(f"❌ Błąd wysyłania do Telegrama: {e}")

def login_and_check():
    send_log("🔐 Rozpoczynam logowanie...")

    session = requests.Session()
    res_get = session.get("https://strefainwestorow.pl/user/login")
    send_log(f"📡 Status logowania: {res_get.status_code}")

    if res_get.status_code != 200:
        return send_log(f"❌ Błąd pobierania formularza: HTTP {res_get.status_code}")

    soup = BeautifulSoup(res_get.text, "html.parser")
    form = soup.find("form", {"id": "user-login-form"})
    if not form:
        return send_log("❌ Nie znaleziono formularza logowania.")

    data = {"name": LOGIN_EMAIL, "pass": LOGIN_PASSWORD}
    for hidden in form.find_all("input", {"type": "hidden"}):
        name = hidden.get("name")
        val = hidden.get("value", "")
        if name:
            data[name] = val

    post_url = "https://strefainwestorow.pl" + form.get("action", "/user/login")
    res_post = session.post(post_url, data=data)
    if res_post.status_code != 200:
        return send_log(f"❌ Błąd logowania (kod HTTP {res_post.status_code})")

    if "Wyloguj" not in res_post.text and "/user/logout" not in res_post.text:
        return send_log("❌ Logowanie nie powiodło się – brak frazy 'Wyloguj'.")

    send_log("✅ Logowanie zakończone sukcesem!")

    for url in PORTFEL_URLS:
        res = session.get(url)
        if res.status_code != 200:
            send_log(f"❌ Błąd pobierania portfela: {url} (HTTP {res.status_code})")
        else:
            fragment = res.text.strip()[:300]
            send_log(f"📄 Fragment HTML z {url}:
{fragment}")

if __name__ == "__main__":
    send_log("🟢 Skrypt wystartował – testuję dostęp do portfeli po logowaniu.")
    login_and_check()
