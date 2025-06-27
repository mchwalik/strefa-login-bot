import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 🔐 Dane logowania i Telegram (hardcoded – NIE ZMIENIAĆ!)
LOGIN_EMAIL = "marcin.chwalik@gmail.com"
LOGIN_PASSWORD = "Sdkfz251"
TELEGRAM_BOT_TOKEN = "7958150824:AAH4-Edu3YIQV9d-rZRHdq7rp_JI222OmGY"
TELEGRAM_CHAT_ID = "7647211011"

PORTFEL_URLS = {
    "Portfel Petard": "https://strefainwestorow.pl/portfel_petard",
    "Portfel Strefy Inwestorów": "https://strefainwestorow.pl/portfel_strefy_inwestorow"
}

def send_log(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown"
            }
        )
    except Exception as e:
        print(f"❌ Błąd wysyłania do Telegrama: {e}")

def login():
    send_log("🔐 Rozpoczynam logowanie...")

    session = requests.Session()
    res_get = session.get("https://strefainwestorow.pl/user/login")
    send_log(f"📡 Status logowania: {res_get.status_code}")
    if res_get.status_code != 200:
        send_log("❌ Błąd pobierania formularza logowania")
        return None

    soup = BeautifulSoup(res_get.text, "html.parser")
    form = soup.find("form", {"id": "user-login-form"})
    if not form:
        send_log("❌ Nie znaleziono formularza logowania.")
        return None

    data = {
        "name": LOGIN_EMAIL,
        "pass": LOGIN_PASSWORD
    }

    for hidden in form.find_all("input", {"type": "hidden"}):
        name = hidden.get("name")
        val = hidden.get("value", "")
        if name:
            data[name] = val

    post_url = "https://strefainwestorow.pl" + form.get("action", "/user/login")
    res_post = session.post(post_url, data=data)
    if res_post.status_code != 200:
        send_log("❌ Błąd przy wysyłaniu danych logowania.")
        return None

    if "Wyloguj" in res_post.text or "/user/logout" in res_post.text:
        send_log("✅ Logowanie zakończone sukcesem!")
        return session
    else:
        send_log("❌ Logowanie nie powiodło się – brak frazy 'Wyloguj'.")
        return None

def parse_portfel_table(html, label, only_today=False):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return None

    rows = table.find_all("tr")
    if not rows:
        return None

    header = [col.get_text(strip=True) for col in rows[0].find_all(["th", "td"])]
    data_rows = []

    for row in rows[1:]:
        cols = row.find_all("td")
        if not cols:
            continue
        data = [col.get_text(strip=True) for col in cols]
        if only_today:
            if len(data) >= 2 and data[1] == datetime.now().strftime("%d.%m.%Y"):
                data_rows.append(data)
        else:
            if (
                "Gotówka" in data[0]
                or "Całkowita wartość" in data[0]
                or "WIG" in data[-1]
                or "sWIG80" in data[-1]
                or "mWIG40" in data[-1]
                or "WIG20" in data[-1]
            ):
                continue
            data_rows.append(data)

    if not data_rows:
        return None

    output = [f"*📊 {label}*"]
    output.append(" | ".join(header))
    output.append("-" * 60)
    for data in data_rows:
        output.append(" | ".join(data))
    return "\n".join(output)

def run_daily(session):
    send_log("📅 Harmonogram --daily aktywowany")
    for label, url in PORTFEL_URLS.items():
        try:
            res = session.get(url)
            if res.status_code == 200:
                msg = parse_portfel_table(res.text, label, only_today=True)
                if msg:
                    send_log(msg)
            else:
                send_log(f"❌ Błąd pobierania strony {url}: HTTP {res.status_code}")
        except Exception as e:
            send_log(f"❌ Błąd przy analizie {url}:\n{e}")

def run_weekly(session):
    send_log("📅 Harmonogram --weekly aktywowany")
    for label, url in PORTFEL_URLS.items():
        try:
            res = session.get(url)
            if res.status_code == 200:
                msg = parse_portfel_table(res.text, label)
                if msg:
                    send_log(msg)
            else:
                send_log(f"❌ Błąd pobierania strony {url}: HTTP {res.status_code}")
        except Exception as e:
            send_log(f"❌ Błąd przy analizie {url}:\n{e}")

if __name__ == "__main__":
    send_log("🟢 Skrypt wystartował – sprawdzanie portfeli (harmonogram Railway)")

    session = login()
    if not session:
        sys.exit(1)

    args = sys.argv[1:]
    if "--daily" in args:
        run_daily(session)
    if "--weekly" in args:
        run_weekly(session)

    if not args:
        run_daily(session)
        run_weekly(session)
