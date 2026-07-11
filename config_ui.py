import threading

from flask import Flask, request, redirect, render_template_string

from config import load_settings
from env_store import clean_env_value, save_env_updates


CONFIG_UI_HTML = """
<!doctype html>
<html lang="my">
<head>
    <meta charset="utf-8">
    <title>Email Telegram OpenRouter Config</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f5f7fb;
            padding: 24px;
            color: #222;
        }
        .card {
            max-width: 720px;
            margin: auto;
            background: white;
            border-radius: 14px;
            padding: 24px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        }
        h1 {
            margin-top: 0;
            font-size: 24px;
        }
        h2 {
            margin-top: 28px;
            font-size: 18px;
            border-bottom: 1px solid #eee;
            padding-bottom: 8px;
        }
        label {
            font-weight: bold;
            display: block;
            margin-top: 14px;
        }
        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 11px;
            margin-top: 6px;
            border: 1px solid #ccc;
            border-radius: 8px;
            box-sizing: border-box;
        }
        .status {
            background: #f0f4ff;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 18px;
            line-height: 1.7;
        }
        .success {
            background: #e8fff0;
            color: #116b2f;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 16px;
        }
        .hint {
            font-size: 13px;
            color: #666;
            margin-top: 4px;
        }
        button {
            margin-top: 22px;
            background: #2563eb;
            color: white;
            border: none;
            padding: 12px 18px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 15px;
        }
        button:hover {
            background: #1d4ed8;
        }
        .warning {
            margin-top: 16px;
            background: #fff7ed;
            border-left: 4px solid #fb923c;
            padding: 12px;
            border-radius: 8px;
            font-size: 14px;
        }
    </style>
</head>

<body>
<div class="card">
    <h1>⚙️ Email / Telegram / OpenRouter Config UI</h1>

    {% if saved %}
    <div class="success">
        ✅ Config သိမ်းပြီးပါပြီ။ Running program ထဲကို reload လုပ်ပြီးပါပြီ။
    </div>
    {% endif %}


    <form method="post">
        <h2>📧 Gmail / Email API</h2>

        <label>EMAIL_USER</label>
        <input type="text" name="EMAIL_USER" placeholder="example@gmail.com">
        <div class="hint">Gmail address ထည့်ပါ။</div>

        <label>EMAIL_PASS</label>
        <input type="password" name="EMAIL_PASS" placeholder="Gmail App Password">
        <div class="hint">Google App Password ထည့်ပါ။ Normal Gmail password မသုံးပါနဲ့။</div>

        <h2>🤖 Telegram API</h2>

        <label>TELEGRAM_TOKEN</label>
        <input type="password" name="TELEGRAM_TOKEN" placeholder="Telegram Bot Token">

        <label>TELEGRAM_CHAT_ID</label>
        <input type="text" name="TELEGRAM_CHAT_ID" placeholder="Telegram Chat ID">

        <h2>🧠 OpenRouter API</h2>

        <label>OPENROUTER_API_KEY</label>
        <input type="password" name="OPENROUTER_API_KEY" placeholder="OpenRouter API Key">

        <button type="submit">💾 Save Config</button>
    </form>
</div>
</body>
</html>
"""


def mask_status(value):
    return "✅ ထည့်ပြီး" if value else "❌ မထည့်ရသေး"


def create_config_app():
    app = Flask(__name__)
    settings = load_settings()
    app.secret_key = settings.CONFIG_UI_SECRET

    @app.route("/", methods=["GET", "POST"])
    def config_ui_home():
        if request.method == "POST":
            form_fields = [
                "EMAIL_USER",
                "EMAIL_PASS",
                "TELEGRAM_TOKEN",
                "TELEGRAM_CHAT_ID",
                "OPENROUTER_API_KEY",
            ]

            updates = {}

            for key in form_fields:
                value = clean_env_value(key, request.form.get(key, ""))

                if value:
                    updates[key] = value

            save_env_updates(updates)

            return redirect("/?saved=1")

        current = load_settings()
        saved = request.args.get("saved") == "1"

        return render_template_string(
            CONFIG_UI_HTML,
            saved=saved,
            email_user_status=mask_status(current.EMAIL_USER),
            email_pass_status=mask_status(current.EMAIL_PASS),
            telegram_token_status=mask_status(current.TELEGRAM_TOKEN),
            telegram_chat_status=mask_status(current.TELEGRAM_CHAT_ID),
            openrouter_status=mask_status(current.OPENROUTER_API_KEY),
        )

    return app


_config_ui_started = False


def start_config_ui(settings):
    global _config_ui_started

    if not settings.CONFIG_UI_ENABLED:
        return

    if _config_ui_started:
        return

    app = create_config_app()

    def run_ui():
        app.run(
            host=settings.CONFIG_UI_HOST,
            port=settings.CONFIG_UI_PORT,
            debug=False,
            use_reloader=False
        )

    thread = threading.Thread(target=run_ui, daemon=True)
    thread.start()
    _config_ui_started = True

    print(f"⚙️ Config UI running: http://{settings.CONFIG_UI_HOST}:{settings.CONFIG_UI_PORT}")