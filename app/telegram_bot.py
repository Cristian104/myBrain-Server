import requests
import threading

# --- CONFIGURATION ---
BOT_TOKEN = "8420186537:AAHeaf9XcXywWBZ9mZ9tD6q9kSRxzvij3Ts"
CHAT_ID = "7585332236"


def send_telegram_message(message):
    """Sends a text message (Runs in background)."""
    def _send():
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"❌ Telegram Error: {e}")

    thread = threading.Thread(target=_send)
    thread.start()


def send_telegram_photo(caption, image_buffer):
    """Sends an image with a caption (Runs in background)."""
    def _send():
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {
            'photo': ('chart.png', image_buffer, 'image/png')
        }
        data = {
            'chat_id': CHAT_ID,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        try:
            requests.post(url, data=data, files=files)
        except Exception as e:
            print(f"❌ Telegram Photo Error: {e}")

    thread = threading.Thread(target=_send)
    thread.start()
