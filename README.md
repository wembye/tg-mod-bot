# Telegram Moderation Bot

A production-ready Telegram group moderation bot built with Python and `python-telegram-bot` v20. Supports Russian and English, with a fully configurable admin panel.

## Features

- 🌐 **Bilingual** — Russian / English, switchable per group
- ⚠️ **Warning system** — 3 warnings trigger automatic ban
- 🔇 **Timed mute** — mute users for any number of minutes
- 🚫 **Anti-spam** — detects spam keywords + duplicate links (same link twice in 60 sec = auto-mute)
- 🌊 **Anti-flood** — 6+ messages in 5 seconds = auto-mute
- 🤬 **Custom word filter** — add/remove any words via commands, violations = auto-mute
- 🔗 **Link blocking** — toggle to allow or block all links in the group
- 👋 **Captcha** — new members must press a button within 60 sec or get kicked
- ⚙️ **Settings panel** — inline keyboard for admins to configure everything
- 🕹️ **Configurable mute durations** — set mute time separately for spam, flood, and word filter

## Commands (prefix `!`)

| Command | Description | Access |
|---------|-------------|--------|
| `!warn` | Warn a user (reply to message) | Admins |
| `!ban` | Ban a user (reply to message) | Admins |
| `!unban` | Unban a user (reply to message) | Admins |
| `!mute 10` | Mute for N minutes (reply to message) | Admins |
| `!unmute` | Remove mute (reply to message) | Admins |
| `!warns` | Check warning count (reply to message) | Everyone |
| `!stats` | Group statistics | Everyone |
| `!addword слово` | Add word to filter | Admins |
| `!delword слово` | Remove word from filter | Admins |
| `!words` | List all filtered words | Admins |
| `!settings` | Open settings panel | Admins |
| `!start` | Show help / choose language | Everyone |

## Settings Panel (`!settings`)

- 🌐 Switch language (RU / EN)
- ✅/❌ Word filter on/off
- ✅/❌ Anti-flood on/off
- ✅/❌ Captcha for new members on/off
- 🔗 Links: allowed / blocked
- ⏱ Mute duration for spam (1/5/10/20/30/60 min)
- ⏱ Mute duration for flood (1/5/10/20/30/60 min)
- ⏱ Mute duration for word filter (1/5/10/20/30/60 min)

## Setup

1. Clone the repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Get a bot token from [@BotFather](https://t.me/BotFather)
4. Set your token in `bot.py`:
   ```python
   BOT_TOKEN = "your_token_here"
   ```
5. Run:
   ```bash
   python bot.py
   ```

## Deployment (Docker)

```bash
docker build -t tg-mod-bot .
docker run -d tg-mod-bot
```

Or deploy instantly on [Railway](https://railway.app) by connecting this repo.

## Tech Stack

- Python 3.11+
- python-telegram-bot 20.7 (async)
- JSON file storage
- Telegram Bot API
- Docker-ready
