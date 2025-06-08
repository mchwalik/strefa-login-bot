import requests
from bs4 import BeautifulSoup

# 🔐 Hardkodowane dane logowania i Telegram
LOGIN_EMAIL = "marcin.chwalik@gmail.com"
LOGIN_PASSWORD = "Sdkfz251"
TELEGRAM_BOT_TOKEN = "7958150824:AAH4-Edu3YIQV9d-rZRHdq7rp_JI222OmGY"
TELEGRAM_CHAT_ID = "7647211011"

PORTFEL_URLS = {
    "Portfel Strefy Inwestorów": "https://strefainwestorow.pl/portfel_strefy_inwestorow",
    "Portfel Petard": "https://strefainwestorow.pl/portfel_petard"
}

def send_log(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
    except Exception as e:
        print(f"❌ Błąd wysyłania do Telegrama: {e}")

def login(session):
    send_log("🔐 Rozpoczynam logowanie...")
    res_get = session.get("https://strefainwestorow.pl/user/login")
    send_log(f"📡 Status logowania: {res_get.status_code}")
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
    res_post = session.post(post_url, data=data)
    if res_post.status_code != 200:
        return send_log(f"❌ Błąd logowania (kod HTTP {res_post.status_code})")

    if "Wyloguj" in res_post.text or "/user/logout" in res_post.text:
        send_log("✅ Logowanie zakończone sukcesem!")
        return True
    else:
        send_log("❌ Logowanie nie powiodło się – fraza 'Wyloguj' nie została znaleziona.")
        return False

def parse_portfel(session, nazwa, url):
    try:
        res = session.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table")
        if not table:
            return send_log(f"⚠️ Brak tabeli na stronie: {url}")

        rows = table.find_all("tr")[1:]
        lines = []
        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if not cols or "gotówka" in cols[0].lower():
                continue
            if any(tekst.lower().startswith(("całkowita", "wig", "mw", "sw", "stopa")) for tekst in cols):
                continue
            lines.append(" | ".join(cols))

        if lines:
            formatted = "\n".join(lines)
            send_log(f"📊 {nazwa}:\n{formatted}")
        else:
            send_log(f"ℹ️ Brak danych do wyświetlenia z {url}")

    except Exception as e:
        send_log(f"❌ Błąd parsowania {nazwa}: {e}")

def main():
    send_log("🟢 Skrypt wystartował – sprawdzanie portfeli.")
    with requests.Session() as session:
        if login(session):
            for nazwa, url in PORTFEL_URLS.items():
                parse_portfel(session, nazwa, url)

if __name__ == "__main__":
    main()
