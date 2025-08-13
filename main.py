import sys
import time
import json
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

def fetch_portfel(session, label):
    url = PORTFEL_URLS[label]
    res = session.get(url, timeout=30)
    if res.status_code != 200:
        return f"❌ Błąd pobierania {label}: HTTP {res.status_code}"
    msg = parse_portfel_table(res.text, label)
    return msg or f"ℹ️ Brak danych do wyświetlenia dla: {label}"

def _parse_zawartosc_args(text: str):
    t = (text or "").strip().lower()
    parts = t.split()
    if len(parts) == 1:
        return "both"
    arg = parts[1]
    if arg.startswith("petard"):
        return "petard"
    if arg.startswith("stref"):
        return "strefa"
    return "both"

def bot_loop():
    send_log("🤖 Bot komend Telegram – start (long polling)")

    session = login()
    if not session:
        send_log("❌ Bot: logowanie nieudane – kończę.")
        return

    offset = None
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    try:
        r = requests.get(f"{base_url}/getUpdates", params={"timeout": 1}, timeout=5)
        data = r.json()
        if data.get("ok") and data.get("result"):
            offset = data["result"][-1]["update_id"] + 1
    except:
        pass

    help_text = (
        "🤖 *Komendy:*\n"
        "/petard – pokaż *Portfel Petard*\n"
        "/strefa – pokaż *Portfel Strefy Inwestorów*\n"
        "/all – pokaż *oba* portfele\n"
        "/zawartosc [petard|strefa] – sprawdź zawartość portfeli (alias: /z)\n"
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

                # 🔍 DEBUG — wysyłamy cały surowy update jako JSON
                try:
                    send_log(f"DEBUG UPDATE:\n```{json.dumps(update, indent=2, ensure_ascii=False)}```")
                except Exception as e:
                    send_log(f"❌ Błąd debugowania: {e}")

                message = update.get("message") or update.get("channel_post")
                if not message:
                    continue

                chat_id = str(message["chat"]["id"])
                if chat_id != TELEGRAM_CHAT_ID:
                    continue

                if "text" not in message:
                    continue

                text = message["text"].strip()
                if not text or not text.startswith("/"):
                    continue

                cmd = text.lower().split()[0]
                cmd = cmd.split("@")[0]  # usuń @NazwaBota

                if cmd in ["/start", "/help"]:
                    send_log(help_text, chat_id)
                elif cmd == "/petard":
                    msg = fetch_portfel(session, "Portfel Petard")
                    send_log(msg, chat_id)
                elif cmd == "/strefa":
                    msg = fetch_portfel(session, "Portfel Strefy Inwestorów")
                    send_log(msg, chat_id)
                elif cmd == "/all":
                    combined = f"{fetch_portfel(session, 'Portfel Petard')}\n\n{fetch_portfel(session, 'Portfel Strefy Inwestorów')}"
                    send_log(combined, chat_id)
                elif cmd in ["/zawartosc", "/z"]:
                    which = _parse_zawartosc_args(text)
                    if which == "both":
                        combined = f"{fetch_portfel(session, 'Portfel Petard')}\n\n{fetch_portfel(session, 'Portfel Strefy Inwestorów')}"
                        send_log(combined, chat_id)
                    elif which == "petard":
                        send_log(fetch_portfel(session, "Portfel Petard"), chat_id)
                    elif which == "strefa":
                        send_log(fetch_portfel(session, "Portfel Strefy Inwestorów"), chat_id)
                    else:
                        send_log("Nie rozpoznano parametru. Użyj: /zawartosc [petard|strefa]", chat_id)

        except Exception as e:
            send_log(f"⚠️ Bot: wyjątek w pętli:\n{e}")
            time.sleep(3)

if __name__ == "__main__":
    send_log("🟢 Skrypt wystartował – tryb debug bota aktywny")
    sys.argv.append("--bot")

    args = sys.argv[1:]

    if "--bot" in args:
        bot_loop()
        sys.exit(0)

    session = login()
    if not session:
        sys.exit(1)

    if "--daily" in args:
        run_daily(session)
    if "--weekly" in args:
        run_weekly(session)

    if not args:
        run_daily(session)
        run_weekly(session)
