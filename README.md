# Telegram Moderation Bot

A production-ready Telegram group moderation bot built with Python and `python-telegram-bot` v20.

## Features

- **Auto-spam detection** — automatically deletes messages containing spam links/keywords
- **Warning system** — 3 warnings trigger an automatic ban
- **Admin commands** — `/warn`, `/ban`, `/unban`, `/warns`, `/stats`
- **Persistent storage** — warning counts saved to JSON across restarts
- **Message logging** — tracks total messages processed per group

## Commands

| Command | Description | Access |
|--------|-------------|--------|
| `/start` | Show help menu | Everyone |
| `/warn` | Warn a user (reply to message) | Admins only |
| `/ban` | Ban a user (reply to message) | Admins only |
| `/unban` | Unban a user (reply to message) | Admins only |
| `/warns` | Check user's warning count | Everyone |
| `/stats` | Group statistics | Everyone |

## Setup

1. Clone the repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Get a bot token from [@BotFather](https://t.me/BotFather)
4. Set environment variable:
   ```bash
   export BOT_TOKEN=your_token_here
   ```
5. Run:
   ```bash
   python bot.py
   ```

## Deployment

Can be deployed on any VPS, Railway, Render, or as a Docker container.

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

## Tech Stack

- Python 3.11+
- python-telegram-bot 20.7 (async)
- JSON file storage
- Telegram Bot API
