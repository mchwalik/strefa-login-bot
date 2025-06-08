import requests
from bs4 import BeautifulSoup

# 🔐 Dane logowania i Telegram (hardcoded)
LOGIN_EMAIL = "marcin.chwalik@gmail.com"
LOGIN_PASSWORD = "Sdkfz251"
TELEGRAM_BOT_TOKEN = "7958150824:AAH4-Edu3YIQV9d-rZRHdq7rp_JI222OmGY"
TELEGRAM_CHAT_ID = "7647211011"

def send_log(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg
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
        return send_log(f"❌ Błąd pobierania formularza: HTTP {res_get.status_code}")

    soup = BeautifulSoup(res_get.text, "html.parser")
    form = soup.find("form", {"id": "user-login-form"})
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
        return session
    else:
        send_log("❌ Logowanie nie powiodło się – fraza 'Wyloguj' nie została znaleziona.")
        return None

def parse_portfolio(session, url):
    res = session.get(url)
    if res.status_code != 200:
        send_log(f"❌ Błąd pobierania strony {url}: HTTP {res.status_code}")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table")
    if not table:
        send_log(f"❌ Nie znaleziono tabeli na stronie {url}")
        return

    rows = table.find_all("tr")[1:]  # pomiń nagłówek
    formatted_rows = []
    for row in rows:
        cols = [col.text.strip() for col in row.find_all("td")]
        if len(cols) == 7 and not any(keyword in cols[0].upper() for keyword in ["GOTÓWKA", "CAŁKOWITA", "MWIG40", "SWIG80", "WIG", "WIG20"]):
            formatted_rows.append(
                f"{cols[0]:<12} | {cols[1]} | {cols[2]} | {cols[3]} | {cols[4]} | {cols[5]} | {cols[6]}"
            )

    if formatted_rows:
        message = "📊 Dane z portfela:\n\n" + "\n".join(formatted_rows)
        send_log(message)
    else:
        send_log(f"ℹ️ Brak danych do wyświetlenia z {url}")

if __name__ == "__main__":
    send_log("🟢 Skrypt wystartował – sprawdzanie portfeli.")
    session = login()
    if session:
        urls = [
            "https://strefainwestorow.pl/portfel_strefy_inwestorow",
            "https://strefainwestorow.pl/portfel_petard"
        ]
        for url in urls:
            parse_portfolio(session, url)
