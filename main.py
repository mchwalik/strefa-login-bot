import sys
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 🔐 Dane logowania i Telegram (hardcoded – NIE ZMIENIAĆ!)
LOGIN_EMAIL = "marcin.chwalik@gmail.com"
LOGIN_PASSWORD = "Sdkfz251"
TELEGRAM_BOT_TOKEN = "7958150824:AAH4-Edu3YIQV9d-rZRHdq7rp_JI222OmGY"
TELEGRAM_CHAT_ID = "7647211011"  # do logów + dozwolony czat

PORTFEL_URLS = {
    "Portfel Petard": "https://strefainwestorow.pl/portfel_petard",
    "Portfel Strefy Inwestorów": "https://strefainwestorow.pl/portfel_strezy_inwestorow"
}

def send_log(msg, chat_id: str = TELEGRAM_CHAT_ID):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "Markdown"
            },
            timeout=20
        )
    except Exception as e:
        print(f"❌ Błąd wysyłania do Telegrama: {e}")

def login():
    send_log("🔐 Rozpoczynam logowanie...")

    session = requests.Session()
    res_get = session.get("https://strefainwestorow.pl/user/login", timeout=30)
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
    res_post = session.post(post_url, data=data, timeout=30)
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
    """
    Zwraca sformatowany markdown z tabelą.
    - only_today=True: tylko wiersze z dzisiejszą datą
    - usuwa podsumowania (Całkowita wartość, WIG, mWIG40, sWIG80, WIG20, puste pierwsze kolumny)
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return None

    rows = table.find_all("tr")
    if not rows:
        return None

    header = [col.get_text(strip=True) for col in rows[0].find_all(["th", "td"])]
    data_rows = []
    today_str = datetime.now().strftime("%d.%m.%Y")

    for row in rows[1:]:
        cols = row.find_all("td")
        if not cols:
            continue
        data = [col.get_text(strip=True) for col in cols]

        # odfiltruj podsumowania i puste wiersze
        joined = " ".join(data).lower()
        if (
            not data[0].strip()
            or "całkowita wartość" in joined
            or "gotówka" in joined
            or data[-1] in ["WIG", "WIG20", "sWIG80", "mWIG40"]
            or "wig" in data[-1].lower()
        ):
            continue

        if only_today:
            # wiersz ma schemat: [Spółka, Data zakupu, Cena kupna, ...]
            if len(data) >= 2 and data[1] == today_str:
                data_rows.append(data)
        else:
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
            res = session.get(url, timeout=30)
            if res.status_code == 200:
                msg = parse_portfel_table(res.text, label, only_today=True)
                if msg:
                    send_log(msg)
                # brak nowych — nic nie wysyłamy
            else:
                send_log(f"❌ Błąd pobierania strony {url}: HTTP {res.status_code}")
        except Exception as e:
            send_log(f"❌ Błąd przy analizie {url}:\n{e}")

def run_weekly(session):
    send_log("📅 Harmonogram --weekly aktywowany")
    for label, url in PORTFEL_URLS.items():
        try:
            res = session.get(url, timeout=30)
            if res.status_code == 200:
                msg = parse_portfel_table(res.text, label)
                if msg:
                    send_log(msg)
            else:
                send_log(f"❌ Błąd pobierania strony {url}: HTTP {res.status_code}")
        except Exception as e:
            send_log(f"❌ Błąd przy analizie {url}:\n{e}")

# ====== TRYB BOTA (komendy na Telegramie) ======

def fetch_portfel(session, label):
    url = PORTFEL_URLS[label]
    res = session.get(url, timeout=30)
    if res.status_code != 200:
        return f"❌ Błąd pobierania {label}: HTTP {res.status_code}"
    msg = parse_portfel_table(res.text, label)
    return msg or f"ℹ️ Brak danych do wyświetlenia dla: {label}"

def bot_loop():
    """
    Long-polling po Telegramie. Obsługiwane komendy:
    /petard, /strefa, /all, /help
    """
    send_log("🤖 Bot komend Telegram – start (long polling)")

    session = login()
    if not session:
        send_log("❌ Bot: logowanie nieudane – kończę.")
        return

    offset = None
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    help_text = (
        "🤖 *Komendy:*\n"
        "/petard – pokaż *Portfel Petard*\n"
        "/strefa – pokaż *Portfel Strefy Inwestorów*\n"
        "/all – pokaż *oba* portfele\n"
        "/help – pomoc\n"
    )

    while True:
        try:
            r = requests.get(
                f"{base_url}/getUpdates",
                params={"timeout": 25, "offset": offset},
                timeout=35
            )
            if r.status_code != 200:
                time.sleep(2)
                continue
            data = r.json()
            if not data.get("ok"):
                time.sleep(2)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message") or update.get("channel_post")
                if not message:
                    continue

                # Ignoruj wiadomości od botów (włącznie z własnymi)
                if message.get("from", {}).get("is_bot", False):
                    continue

                chat_id = str(message["chat"]["id"])
                text = (message.get("text") or "").strip()

                # Ogranicz do zdefiniowanego czatu (opcjonalnie – zostawiamy, bo używasz 1 czatu)
                # Jeśli chcesz, usuń poniższy warunek, aby bot odpowiadał wszędzie:
                if chat_id != TELEGRAM_CHAT_ID:
                    # ewentualnie: send_log("⛔️ Nieautoryzowany czat.", chat_id)
                    continue

                cmd = text.lower()
                if cmd == "/start" or cmd == "/help":
                    send_log(help_text, chat_id)
                elif cmd == "/petard":
                    msg = fetch_portfel(session, "Portfel Petard")
                    send_log(msg, chat_id)
                elif cmd == "/strefa":
                    msg = fetch_portfel(session, "Portfel Strefy Inwestorów")
                    send_log(msg, chat_id)
                elif cmd == "/all":
                    m1 = fetch_portfel(session, "Portfel Petard")
                    m2 = fetch_portfel(session, "Portfel Strefy Inwestorów")
                    send_log(m1, chat_id)
                    send_log(m2, chat_id)
                else:
                    # ignoruj inne wiadomości lub podeślij pomoc
                    send_log("Nieznana komenda. Napisz /help.", chat_id)

        except Exception as e:
            # krótkie odczekanie i kontynuacja pętli
            send_log(f"⚠️ Bot: wyjątek w pętli:\n{e}")
            time.sleep(3)

# ====== ENTRYPOINT ======

if __name__ == "__main__":
    # Informacja o starcie
    send_log("🟢 Bot Telegram wystartował!")
    
    # Uruchom bota
    bot_loop()
