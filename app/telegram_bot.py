import requests
import threading

# REPLACE THESE WITH YOUR ACTUAL VALUES
BOT_TOKEN = "8420186537:AAHeaf9XcXywWBZ9mZ9tD6q9kSRxzvij3Ts"
CHAT_ID = "7585332236"


def send_telegram_message(message):
    """
    Sends a message to your Telegram via the Bot API.
    Runs in a separate thread to avoid slowing down the dashboard.
    """
    def _send():
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")

    # Fire and forget (don't make the user wait for the message to send)
    thread = threading.Thread(target=_send)
    thread.start()
