# os-notif-telegram

Forward OS notifications to Telegram in real time.

Currently supports: **Windows 10 / 11**

## Requirements

- Python 3.9+

## Installation

```bash
pip install os-notif-telegram
```

## Quick Start

**1. Create a Telegram bot**

Talk to [@BotFather](https://t.me/BotFather) → `/newbot` → copy the **bot token**.

**2. Get your Chat ID**

Talk to [@userinfobot](https://t.me/userinfobot) → copy the **id** number.

**3. Configure**

```bash
os-notif-telegram setup
```

Follow the prompts to enter your bot token and chat ID.
Config is saved to `%APPDATA%\os-notif-telegram\config.json` — never committed to any repo.

**4. Start forwarding**

```bash
os-notif-telegram start
```

The program minimises to the system tray. You can close the terminal window.

## Commands

| Command | Description |
|---------|-------------|
| `os-notif-telegram setup` | Interactive setup wizard |
| `os-notif-telegram config` | Show current configuration |
| `os-notif-telegram start` | Start forwarding (system tray) |
| `os-notif-telegram start --no-tray` | Start in terminal (foreground) |
| `os-notif-telegram stop` | Stop the running forwarder |
| `os-notif-telegram status` | Show whether the forwarder is running |
| `os-notif-telegram test` | Send a test notification to verify Telegram is working |
| `os-notif-telegram --version` | Show version |

### Non-interactive setup

```bash
os-notif-telegram setup --token "YOUR_TOKEN" --chat-id "YOUR_CHAT_ID"
```

## Windows Notification Access

If you see an "Access denied" error, enable notification access:

**Settings → Privacy & security → Notifications**

Enable access for your terminal application (e.g. Windows Terminal, PowerShell).

## How it Works

- Listens to OS notification APIs
- On each new notification, extracts app name, title, and body
- Sends a formatted message to your Telegram chat via the Bot API
- Deduplicates notifications by ID and content to prevent spam

## License

MIT
