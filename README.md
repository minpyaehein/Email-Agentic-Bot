# Email-Agentic-Bot

Autonomous Python email agent that summarizes incoming emails into Myanmar (Burmese) and forwards the summaries to a Telegram bot. It focuses on identifying student-related messages (assignments, schedules, exams, official notices, etc.), summarizes them in Myanmar, and optionally notifies you via Telegram with a simple reply workflow.

## Features
- Rule-first student detection (domain + keyword/group heuristics).
- AI-backed summarization (OpenRouter models) with rule-only fallback.
- Summaries written in Myanmar (Burmese).
- Sends student-related summaries to a Telegram chat as interactive reports.
- Attachments: only filenames/metadata are read — attachment content is NOT read.
- Local SQLite DB to record every analysis for auditing and review.
- Small web config UI (Flask) to enter/save environment variables.

## Stack
- **Language(s):** Python 3.10+
- **Runtime / framework:** Plain Python scripts + Flask for the config UI
- **Notable libraries:** openai (OpenRouter client usage), python-dotenv, beautifulsoup4, flask, requests

## Repository layout (top-level)

```
.env                       # optional local env file template
README.md                  # (this file)
ai_service.py              # AI prompt building + OpenRouter client + analysis pipeline
config.py                  # Settings dataclass & helpers
config_ui.py               # Small Flask app for entering/saving env values
database.py                # SQLite init + save/query helpers
email_service.py           # IMAP fetching, parsing, attachment metadata extraction, reply sending
env_store.py               # (env cleaning / saving helpers)
main.py                    # Program entrypoint & main control loop
requirements.txt           # Python dependencies
student_email_analysis.db  # Example / sample DB (created/used at runtime)
telegram_service.py        # Telegram report builders & command processing
text_utils.py              # Text utilities, match lists, Myanmar helpers
__pycache__/               # Python caches (ignored)
```

How it fits together:
- `main.py` is the runtime loop: loads settings, starts the config UI, initializes DB, polls IMAP for Primary unread Gmail messages since the configured start date, enqueues new messages, runs rule + AI analysis, saves results to SQLite and sends Telegram reports for messages classified as student-related.
- `email_service.py` handles IMAP login, message decoding, stripping HTML, attachment filename/metadata extraction, and sending email replies when requested.
- `ai_service.py` constructs the system/user prompts and calls OpenRouter models (via OpenAI-compatible client) to obtain structured JSON analysis. If AI is unavailable or fails, a rule-only analysis is used as fallback.
- `telegram_service.py` builds the Telegram messages and processes incoming commands (view pending replies, trigger send, etc.).

## Quickstart — install & run
1. Clone the repo:
   ```
   git clone https://github.com/minpyaehein/Email-Agentic-Bot.git
   cd Email-Agentic-Bot
   ```

2. Create a Python virtual environment and install dependencies:
   ```
   python -m venv .venv
   source .venv/bin/activate     # macOS / Linux
   .venv\Scripts\activate        # Windows (PowerShell/CMD)
   pip install -r requirements.txt
   ```

3. Provide configuration (either via `.env` or the built-in Config UI). The built-in UI runs automatically (default host:port below). Open the UI in your browser to add missing values:
   - Config UI: http://127.0.0.1:5000 (defaults from code)

4. Run the agent:
   ```
   python main.py
   ```

The agent will start and print runtime information (configured model chain, database initialization, config UI link, and loop status).

## Environment variables (.env)
The agent reads configuration from environment variables. Example `.env` (create at repo root or use the Config UI):

```
# Email (Gmail)
EMAIL_USER=your.email@gmail.com
EMAIL_PASS=<GMAIL_APP_PASSWORD>

# Telegram
TELEGRAM_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=987654321

# OpenRouter (optional)
USE_OPENROUTER=true
OPENROUTER_API_KEY=or_xxx...
OPENROUTER_PRIMARY_MODEL=openai/gpt-4o
OPENROUTER_FALLBACK_MODEL_1=anthropic/claude-3.5-sonnet
OPENROUTER_FALLBACK_MODEL_2=openai/gpt-4o-mini
OPENROUTER_FALLBACK_MODEL_3=meta-llama/llama-3.1-70b-instruct

# Config UI (defaults)
CONFIG_UI_ENABLED=true
CONFIG_UI_HOST=127.0.0.1
CONFIG_UI_PORT=5000
CONFIG_UI_SECRET=student-email-agent-local-ui
```

Notes:
- For Gmail, enable IMAP on the account and use a Google App Password (recommended) rather than your normal Gmail password.
- If `USE_OPENROUTER` is true, `OPENROUTER_API_KEY` is required for AI summarization.

## Default behavior & important constraints
- The agent searches Gmail "Primary" category unread messages since SCRIPT_START_DATE (the start date is set at runtime and defaults to the current date when the script is started).
- The system aims to only notify on student-related emails (configurable). Non-student messages are recorded in the database but not always forwarded to Telegram unless `NOTIFY_NON_STUDENT` is enabled.
- Attachment content is NOT read — only attachment filenames, extensions, and counts are used in analysis and included in summaries.
- AI model chain uses OpenRouter-compatible models in precedence order; if AI fails, the rule-only analysis is used so the system still provides structured output.

## Data storage
- SQLite DB file: (default) `student_email_analysis.db` in repository root.
- Table: `email_analysis` — stores received_at, sender, subject, attachment_count, target_domain, importance, summary, action_item, deadline, provider_used, model_used, etc.
- The DB is created automatically on first run via `init_database()`.

Inspect the database with:
```
sqlite3 student_email_analysis.db
sqlite> .tables
sqlite> SELECT id, received_at, sender, subject, target_domain, importance FROM email_analysis ORDER BY received_at DESC LIMIT 20;
```

## Telegram interaction
- The bot sends a concise Myanmar summary and reply buttons for student-related messages.
- The repository contains a Telegram handler that processes commands and supports a pending-reply workflow (see `telegram_service.py` and `main.py` for implementation details).

## Troubleshooting
- IMAP login/search errors:
  - Ensure IMAP enabled in Gmail settings.
  - Use an App Password if the account uses 2FA.
  - Confirm EMAIL_USER and EMAIL_PASS values are correct.
- No Telegram notifications:
  - Confirm TELEGRAM_TOKEN and TELEGRAM_CHAT_ID are correct.
  - Check the bot has permission to send messages to the chat.
- AI analysis failing:
  - If OpenRouter calls fail, ensure OPENROUTER_API_KEY is valid and network access is available. The system falls back to rule-only analysis.
- DB save errors:
  - Confirm the running user has write permission to the repo directory or the configured DB path.

## Privacy & safety
- The agent will access your email account via IMAP and will send emails through SMTP when replying — store credentials securely (use .env or the UI).
- Attachment contents are NOT read. Only metadata (filenames, extensions, counts) are used.
- Review summaries and replies before relying on them for critical actions.

## Development notes
- Main entry: `main.py`
- Config UI: `config_ui.py` (Flask, runs in background thread)
- Email parsing and attachment metadata: `email_service.py`
- AI prompt and normalization: `ai_service.py`
- DB: `database.py`
- Text utilities, keyword lists and Myanmar helper functions: `text_utils.py`

## Contributing
Contributions, issues, and suggestions are welcome. Please open an issue describing the feature or bug and include sample emails / traces if possible (while removing any sensitive data).

---

If you'd like, I can:
- Add an example `.env.example` file to the repository.
- Create a brief troubleshooting doc with common IMAP/Gmail steps.
