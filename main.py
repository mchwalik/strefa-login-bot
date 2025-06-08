import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# === KONFIGURACJA ===
EMAIL = "twoj_email@domena.pl"
PASSWORD = "twoje_haslo"
TELEGRAM_BOT_TOKEN = "twój_token"
TELEGRAM_CHAT_ID = "twój_chat_id"

PORTFEL_URLS = {
    "Portfel Strefy Inwestorów": "https://strefainwestorow.pl/portfel_strefy_inwestorow",
    "Portfel Petard": "https://strefainwestorow.pl/portfel_petard"
}

# === TELEGRAM ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

# === LOGOWANIE ===
def login(session):
    try:
        login_url = "https://strefainwestorow.pl/user/login"
        r = session.get(login_url)
        soup = BeautifulSoup(r.text, "html.parser")
        form_build_id = soup.find("input", {"name": "form_build_id"})["value"]

        payload = {
            "name": EMAIL,
            "pass": PASSWORD,
            "form_id": "user_login_form",
            "form_build_id": form_build_id,
            "op": "Zaloguj"
        }
        resp = session.post(login_url, data=payload)
        return resp.status_code == 200
    except Exception as e:
        send_telegram_message(f"❌ Błąd logowania: {e}")
        return False

# === PARSOWANIE PORTFELA ===
def parse_portfel(session, nazwa, url):
    try:
        r = session.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")

        if not table:
            send_telegram_message(f"⚠️ Brak tabeli na stronie: {url}")
            return

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
            send_telegram_message(f"📊 {nazwa}:\n{formatted}")
        else:
            send_telegram_message(f"ℹ️ Brak danych do wyświetlenia z {url}")

    except Exception as e:
        send_telegram_message(f"❌ Błąd podczas parsowania {nazwa}: {e}")

# === GŁÓWNA FUNKCJA ===
def main():
    send_telegram_message("🟢 Skrypt wystartował – sprawdzanie portfeli.")
    with requests.Session() as session:
        if login(session):
            send_telegram_message("✅ Logowanie zakończone sukcesem!")
            for nazwa, url in PORTFEL_URLS.items():
                parse_portfel(session, nazwa, url)
        else:
            send_telegram_message("❌ Logowanie nie powiodło się.")

if __name__ == "__main__":
    main()
