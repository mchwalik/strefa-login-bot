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
    "Portfel Strefy Inwestorów": "https://strefainwestorow.pl/portfel_strefy_inwestorow"
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

def check_actual_portfolio(session, chat_id):
    """
    Sprawdza aktualny stan portfeli i wysyła do czatu
    """
    send_log("🔍 Sprawdzanie aktualnego stanu portfeli...", chat_id)
    
    for label, url in PORTFEL_URLS.items():
        try:
            res = session.get(url, timeout=30)
            if res.status_code == 200:
                msg = parse_portfel_table(res.text, label)
                if msg:
                    send_log(f"📊 *AKTUALNY STAN:*\n{msg}", chat_id)
                else:
                    send_log(f"ℹ️ Brak danych dla {label}", chat_id)
            else:
                send_log(f"❌ Błąd pobierania {label}: HTTP {res.status_code}", chat_id)
        except Exception as e:
            send_log(f"❌ Błąd przy sprawdzaniu {label}: {e}", chat_id)

def test_telegram_connection():
    """Test połączenia z Telegram API"""
    try:
        print("🧪 Testuję połączenie z Telegram API...")
        
        # Test 1: getMe
        r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe", timeout=10)
        print(f"📡 Status getMe: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                print(f"✅ Bot działa! Username: {bot_info.get('username')}")
                return True
            else:
                print(f"❌ Bot API błąd: {data}")
                return False
        else:
            print(f"❌ HTTP błąd: {r.status_code}")
            print(f"Response: {r.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Błąd testowania: {e}")
        return False

def bot_loop():
    """
    Long-polling po Telegramie. Obsługiwane komendy:
    /petard, /strefa, /all, /check, /help
    """
    send_log("🤖 Bot komend Telegram – start (long polling)")

    # Test połączenia najpierw
    if not test_telegram_connection():
        send_log("❌ Nie można połączyć z Telegram API - sprawdź token!")
        return

    session = login()
    if not session:
        send_log("❌ Bot: logowanie nieudane – kończę.")
        return

    send_log("🚀 Bot gotowy do odbierania komend!")
    
    offset = None
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    help_text = (
        "🤖 *Komendy:*\n"
        "/petard – pokaż *Portfel Petard*\n"
        "/strefa – pokaż *Portfel Strefy Inwestorów*\n"
        "/all – pokaż *oba* portfele\n"
        "/check – sprawdź *aktualny stan* portfeli\n"
        "/help – pomoc\n"
    )

    error_count = 0
    max_errors = 3  # zmniejszone z 5 na 3

    while True:
        try:
            print("🔄 Sprawdzam nowe wiadomości...")
            r = requests.get(
                f"{base_url}/getUpdates",
                params={"timeout": 10, "offset": offset},  # zmniejszony timeout z 25 na 10
                timeout=15  # zmniejszony z 35 na 15
            )
            
            print(f"📡 Status odpowiedzi Telegram: {r.status_code}")
            
            if r.status_code != 200:
                error_count += 1
                print(f"❌ Błędny status code: {r.status_code}")
                print(f"Response: {r.text[:200]}")
                if error_count >= max_errors:
                    send_log("❌ Zbyt wiele błędów połączenia - zatrzymuję bota")
                    break
                time.sleep(5)  # zwiększone z 2 na 5 sekund
                continue
            
            error_count = 0  # reset counter on success
            data = r.json()
            
            if not data.get("ok"):
                print(f"❌ Telegram API błąd: {data}")
                time.sleep(2)
                continue

            updates = data.get("result", [])
            print(f"📨 Otrzymano {len(updates)} aktualizacji")

            for update in updates:
                offset = update["update_id"] + 1
                print(f"🔍 Przetwarzam update ID: {offset-1}")

                message = update.get("message") or update.get("channel_post")
                if not message:
                    print("⚠️ Brak wiadomości w update")
                    continue

                # Ignore messages from bots (including this bot's own messages)
                if message.get("from", {}).get("is_bot", False):
                    print("🤖 Ignoruję wiadomość od bota")
                    continue

                chat_id = str(message["chat"]["id"])
                text = (message.get("text") or "").strip()
                
                print(f"💬 Wiadomość z chat_id {chat_id}: '{text}'")

                # Ogranicz do zdefiniowanego czatu
                if chat_id != TELEGRAM_CHAT_ID:
                    print(f"⛔ Nieautoryzowany czat: {chat_id}")
                    continue

                cmd = text.lower()
                print(f"🎯 Wykonuję komendę: {cmd}")
                
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
                elif cmd == "/check":
                    check_actual_portfolio(session, chat_id)
                else:
                    print(f"❓ Nieznana komenda: {cmd}")
                    send_log("Nieznana komenda. Napisz /help.", chat_id)

        except requests.exceptions.Timeout:
            error_count += 1
            print(f"⏰ Timeout połączenia (błąd #{error_count})")
            if error_count >= max_errors:
                send_log("❌ Zbyt wiele timeoutów - zatrzymuję bota")
                break
            time.sleep(5)
            
        except requests.exceptions.ConnectionError:
            error_count += 1
            print(f"🌐 Błąd połączenia internetowego (błąd #{error_count})")
            if error_count >= max_errors:
                send_log("❌ Brak internetu - zatrzymuję bota")
                break
            time.sleep(10)
            
        except Exception as e:
            error_count += 1
            error_msg = f"⚠️ Bot: wyjątek w pętli (błąd #{error_count}):\n{str(e)[:200]}"
            print(error_msg)
            send_log(error_msg)
            
            if error_count >= max_errors:
                send_log("❌ Zbyt wiele błędów - zatrzymuję bota")
                break
                
            time.sleep(3)

# ====== ENTRYPOINT ======

if __name__ == "__main__":
    # Informacja o starcie
    send_log("🟢 Bot Telegram wystartował!")
    
    # Uruchom tylko bota
    bot_loop()
