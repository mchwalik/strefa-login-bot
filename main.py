import requests
from bs4 import BeautifulSoup
from datetime import datetime
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
            data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
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

    data = {"name": LOGIN_EMAIL, "pass": LOGIN_PASSWORD}
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
    output = [f"*📊 {label}*", " | ".join(header), "-" * 60]

    for row in rows[1:]:
        cols = row.find_all("td")
        if not cols or "Gotówka" in row.text or "Całkowita wartość" in row.text:
            continue
        data = [col.get_text(strip=True) for col in cols]
        output.append(" | ".join(data))

    return "\n".join(output)

def check_for_today_purchases(html, label):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    rows = table.find_all("tr")[1:]
    today = datetime.now().strftime("%d.%m.%Y")
    new_purchases = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            date_text = cols[1].get_text(strip=True)
            if date_text == today:
                company = cols[0].get_text(strip=True)
                price = cols[2].get_text(strip=True)
                new_purchases.append(f"🛒 *Nowy zakup w {label}*\nSpółka: {company}\nData: {date_text}\nCena: {price}")

    return new_purchases

def main():
    send_log("🟢 Skrypt wystartował – sprawdzanie portfeli.")
    session = login()
    if not session:
        return

    now = datetime.now()
    is_friday_17 = now.weekday() == 4 and now.hour == 17

    for label, url in PORTFEL_URLS.items():
        try:
            res = session.get(url)
            if res.status_code != 200:
                send_log(f"❌ Błąd pobierania strony {url}: HTTP {res.status_code}")
                continue

            if is_friday_17:
                msg = parse_portfel_table(res.text, label)
                send_log(msg)
            else:
                purchases = check_for_today_purchases(res.text, label)
                for purchase in purchases:
                    send_log(purchase)

        except Exception as e:
            send_log(f"❌ Błąd przy analizie {url}:\n{e}")

if __name__ == "__main__":
    main()
