import requests


def send_carrier_notification(carrier_profile, message):
    token = "8163825460:AAFk8wyYGtARQcsM57UCCdHwb4knYAd7WJA"

    # Беремо ID з поля telegram_bot, як ви і задумували
    chat_id = carrier_profile.telegram_bot
    print('==============================',chat_id)
    if not chat_id:
        print(f"ID не вказано для {carrier_profile.company_name}")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Telegram error: {e}")