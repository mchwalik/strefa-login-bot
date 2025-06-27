import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import time

# 🔐 Dane logowania i Telegram (NIE ZMIENIAĆ!)
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

def parse_portfel_table(html, label, suppress_summary=True):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return f"❌ Nie znaleziono tabeli w portfelu: {label}"

    rows = table.find_all("tr")
    if not rows:
        return f"ℹ️ Brak danych do wyświetlenia z {label}"

    header = [col.get_text(strip=True) for col in rows[0].find_all(["th", "td"])]
    output = [f"*📊 {label}*"]
    output.append(" | ".join(header))
    output.append("-" * 60)

    for row in rows[1:]:
        cols = row.find_all("td")
        if not cols:
            continue
        data = [col.get_text(strip=True) for col in cols]

        # Pomijaj podsumowania
        if suppress_summary:
            joined = " ".join(data).lower()
            if not data[0] or any(key in joined for key in ["wig", "całkowita wartość", "gotówka", "stopa zwrotu"]):
                continue

        output.append(" | ".join(data))

    return "\n".join(output)

def check_new_purchases(session):
    today = datetime.now().strftime("%d.%m.%Y")
    for label, url in PORTFEL_URLS.items():
        try:
            res = session.get(url)
            if res.status_code != 200:
                send_log(f"❌ Błąd pobierania {label}: HTTP {res.status_code}")
                continue

            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    date = cols[1].get_text(strip=True)
                    if date == today:
                        name = cols[0].get_text(strip=True)
                        price = cols[2].get_text(strip=True)
                        send_log(f"📢 Nowy zakup w {label}!\nSpółka: {name}\nCena: {price}\nŹródło: {url}")
        except Exception as e:
            send_log(f"❌ Błąd podczas sprawdzania zakupów w {label}:\n{e}")

def send_weekly_tables(session):
    for label, url in PORTFEL_URLS.items():
        try:
            res = session.get(url)
            if res.status_code == 200:
                msg = parse_portfel_table(res.text, label)
                send_log(msg)
            else:
                send_log(f"❌ Błąd pobierania {label}: HTTP {res.status_code}")
        except Exception as e:
            send_log(f"❌ Błąd analizowania {label}:\n{e}")

def run_schedulers():
    session = login()
    if not session:
        return

    args = sys.argv
    if "--daily" in args:
        send_log("📅 Harmonogram --daily aktywowany")
        check_new_purchases(session)

    if "--weekly" in args:
        send_log("📅 Harmonogram --weekly aktywowany")
        send_weekly_tables(session)

if __name__ == "__main__":
    send_log("🟢 Skrypt wystartował – sprawdzanie portfeli (harmonogram Railway)")
    run_schedulers()
