import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Dane logowania i Telegram (hardkodowane – nie zmieniamy!)
EMAIL = "twoj_email@domena.pl"
PASSWORD = "twoje_haslo"
TELEGRAM_BOT_TOKEN = "bot123456:ABC..."
TELEGRAM_CHAT_ID = "123456789"

LOGIN_URL = "https://strefainwestorow.pl/user/login"
PORTFEL_URLS = [
    "https://strefainwestorow.pl/portfel_strefy_inwestorow",
    "https://strefainwestorow.pl/portfel_petard"
]

session = requests.Session()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "MarkdownV2"
    })

def escape_markdown(text):
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return ''.join(f"\\{c}" if c in escape_chars else c for c in text)

def login():
    send_telegram_message("🔐 Rozpoczynam logowanie...")
    response = session.get(LOGIN_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    form = soup.find("form", {"id": "user-login-form"})
    if not form:
        send_telegram_message("❌ Nie znaleziono formularza logowania.")
        return False
    form_build_id = form.find("input", {"name": "form_build_id"})["value"]
    form_id = form.find("input", {"name": "form_id"})["value"]
    data = {
        "name": EMAIL,
        "pass": PASSWORD,
        "form_build_id": form_build_id,
        "form_id": form_id,
        "op": "Zaloguj"
    }
    post_response = session.post(LOGIN_URL, data=data)
    if post_response.url == LOGIN_URL:
        send_telegram_message("❌ Logowanie nieudane – sprawdź dane.")
        return False
    send_telegram_message("✅ Logowanie zakończone sukcesem!")
    return True

def parse_table(url):
    response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if not table:
        send_telegram_message(f"⚠️ Brak tabeli na stronie {url}")
        return

    rows = table.find_all("tr")
    parsed_rows = []
    for row in rows[1:]:
        cols = [col.text.strip() for col in row.find_all("td")]
        if len(cols) >= 7:
            parsed_rows.append(cols[:7])

    if not parsed_rows:
        send_telegram_message(f"⚠️ Brak danych w tabeli z {url}")
        return

    header = ["Spółka", "Data zakupu", "Cena kupna (średnia)", "Liczba akcji", "Cena aktualna", "Aktualna wartość pozycji", "Zysk/strata"]
    table_md = "| " + " | ".join(header) + " |\n"
    table_md += "|:" + "|:".join(["-" * len(h) for h in header]) + "|\n"
    for row in parsed_rows:
        row = [escape_markdown(cell.replace(" ", "\u00A0")) for cell in row]  # nbsp zamiast zwykłych spacji
        table_md += "| " + " | ".join(row) + " |\n"

    send_telegram_message(f"📊 Dane z portfela:

{table_md}")

def main():
    send_telegram_message("🟢 Skrypt wystartował – sprawdzanie portfeli.")
    if login():
        for url in PORTFEL_URLS:
            parse_table(url)

if __name__ == "__main__":
    main()
