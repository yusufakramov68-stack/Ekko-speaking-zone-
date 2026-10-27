# Speaking Zone AI — Telegram bot starter

A starter Telegram bot for English practice with text chat and voice notes:
- Text message -> AI text reply
- Telegram voice note -> speech-to-text -> AI response -> generated voice reply
- `/practice` gives an IELTS-style speaking question
- `/reset` clears the user's short-term chat history

## 1. Requirements
- Python 3.10+
- A Telegram bot token from `@BotFather`
- An OpenAI API key with API access/billing enabled

## 2. Setup on Windows
Open PowerShell in this folder:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` in Notepad and replace the placeholder values with your own tokens.
Do not send these tokens to anyone or commit `.env` to GitHub.

## 3. Create your Telegram bot
1. Open Telegram and search for `@BotFather`.
2. Send `/newbot`.
3. Choose a display name and a unique username ending in `bot`.
4. Copy the token BotFather gives you.
5. Put it into `TELEGRAM_BOT_TOKEN` in `.env`.

## 4. Get an OpenAI API key
1. Open the OpenAI API platform and sign in.
2. Create an API key in the API dashboard.
3. Add billing/credits if required for your account.
4. Put the key into `OPENAI_API_KEY` in `.env`.

ChatGPT subscriptions and API billing are separate. API calls may incur charges.

## 5. Run locally
```powershell
python bot.py
```
Open your bot in Telegram, press Start, and test text and voice notes.
Keep the terminal running while you test.

## 6. Run on macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

## 7. Deploy 24/7
Deploy this folder to a VPS or Python hosting service that supports a persistent process.
Set the environment variables in the host's secret/environment settings, install requirements,
and run `python bot.py`. Do not upload your `.env` file publicly.

## Notes and limitations
- This starter stores recent conversation history in memory; restarting the bot clears it.
- It does not provide an official IELTS score. Feedback is AI-generated and approximate.
- Audio transcription, AI replies, and generated speech use paid API services depending on your account and model prices.
- API/model names and provider availability can change; if a model is unavailable for your account, choose a currently supported model in `.env`.
- Add rate limits, error monitoring, persistent storage, privacy notice, and abuse protection before inviting many users.
