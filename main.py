import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys

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

def parse_portfel_table(html, label):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return f"❌ Nie znaleziono tabeli w portfelu: {label}"

    rows = table.find_all("tr")
    header = [col.get_text(strip=True) for col in rows[0].find_all("th")]
    output = [f"*📊 {label}*"]
    output.append(" | ".join(header))
    output.append("-" * 60)

    for row in rows[1:]:
        cols = row.find_all("td")
        if not cols:
            continue
        data = [col.get_text(strip=True) for col in cols]

        # Pomijaj wiersze z podsumowaniami, np. zawierające "Gotówka", "WIG", "wartość portfela"
        if any(sub in data[0] for sub in ["Gotówka", "Całkowita", "WIG", "sWIG", "mWIG"]):
            continue

        output.append(" | ".join(data))

    return "\n".join(output)

def check_today_purchases(session):
    today = datetime.now().strftime("%d.%m.%Y")
    for label, url in PORTFEL_URLS.items():
        try:
            res = session.get(url)
            if res.status_code != 200:
                continue
            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 6:
                    data = cols[1].get_text(strip=True)
                    if data == today:
                        spol = cols[0].get_text(strip=True)
                        cena = cols[2].get_text(strip=True)
                        send_log(f"📢 *Nowy zakup!*\nSpółka: {spol}\nCena: {cena}\nŹródło: {label}")
        except Exception as e:
            send_log(f"❌ Błąd przy analizie {label}:\n{e}")

def main():
    send_log("🟢 Skrypt wystartował – sprawdzanie portfeli.")
    args = sys.argv[1:]
    if args:
        send_log(f"🧭 Wykryto tryb uruchomienia: `{args[0]}`")

    session = login()
    if not session:
        return

    if "--daily" in args:
        check_today_purchases(session)

    if "--weekly" in args:
        for label, url in PORTFEL_URLS.items():
            try:
                res = session.get(url)
                if res.status_code == 200:
                    msg = parse_portfel_table(res.text, label)
                    send_log(msg)
                else:
                    send_log(f"❌ Błąd pobierania strony {url}: HTTP {res.status_code}")
            except Exception as e:
                send_log(f"❌ Błąd przy analizie {url}:\n{e}")

    if not args:
        send_log("✅ Harmonogramy aktywne: `--daily`, `--weekly`.")

if __name__ == "__main__":
    main()
