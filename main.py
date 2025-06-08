import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 🔐 Dane logowania i Telegram (hardcoded – NIE ZMIENIAĆ!)
LOGIN_EMAIL = "marcin.chwalik@gmail.com"
LOGIN_PASSWORD = "Sdkfz251"
TELEGRAM_BOT_TOKEN = "7958150824:AAH4-Edu3YIQV9d-rZRHdq7rp_JI222OmGY"
TELEGRAM_CHAT_ID = "7647211011"

def send_log(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
    except Exception as e:
        print(f"❌ Błąd wysyłania do Telegrama: {e}")

def login():
    send_log("🔐 Rozpoczynam logowanie...")

    session = requests.Session()
    res_get = session.get("https://strefainwestorow.pl/user/login")
    send_log(f"📡 Status logowania: {res_get.status_code}")

    if res_get.status_code != 200:
        send_log(f"❌ Błąd pobierania formularza: HTTP {res_get.status_code}")
        return None

    soup = BeautifulSoup(res_get.text, "html.parser")
    form = soup.find("form", {"id": "user-login-form"})
    if not form:
        send_log("❌ Nie znaleziono formularza logowania.")
        return None

    data = {"name": LOGIN_EMAIL, "pass": LOGIN_PASSWORD}
    for hidden in form.find_all("input", {"type": "hidden"}):
        name = hidden.get("name")
        val = hidden.get("value", "")
        if name:
            data[name] = val

    post_url = "https://strefainwestorow.pl" + form.get("action", "/user/login")
    res_post = session.post(post_url, data=data)

    if res_post.status_code != 200:
        send_log(f"❌ Błąd logowania (HTTP {res_post.status_code})")
        return None

    if "Wyloguj" in res_post.text or "/user/logout" in res_post.text:
        send_log("✅ Logowanie zakończone sukcesem!")
        return session
    else:
        send_log("❌ Logowanie nie powiodło się – fraza 'Wyloguj' nie została znaleziona.")
        return None

def check_portfel(session, url):
    try:
        res = session.get(url)
        if res.status_code != 200:
            return send_log(f"❌ Błąd pobierania {url} – HTTP {res.status_code}")

        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table")
        if not table:
            return send_log(f"❌ Nie znaleziono tabeli na stronie: {url}")

        today = datetime.now().strftime("%d.%m.%Y")
        rows = table.find_all("tr")[1:]

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 6:
                data = cols[5].text.strip()
                if data == today:
                    spolka = cols[0].text.strip()
                    cena = cols[3].text.strip()
                    send_log(f"📢 Nowy zakup!\nSpółka: {spolka}\nCena: {cena}\nŹródło: {url}")
    except Exception as e:
        send_log(f"❌ Błąd podczas parsowania {url}:\n{e}")
        send_log(f"📄 Fragment HTML z {url}:\n{res.text[:300]}")

if __name__ == "__main__":
    send_log("🟢 Skrypt wystartował – sprawdzanie portfeli.")
    session = login()
    if session:
        portfele = [
            "https://strefainwestorow.pl/portfel_strefy_inwestorow",
            "https://strefainwestorow.pl/portfel_petard"
        ]
        for url in portfele:
            check_portfel(session, url)
