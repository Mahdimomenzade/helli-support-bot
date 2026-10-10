import os
from threading import Thread
from bot import main as run_bot
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

def start_bot():
    run_bot()

if __name__ == "__main__":
    bot_thread = Thread(target=start_bot)
    bot_thread.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
