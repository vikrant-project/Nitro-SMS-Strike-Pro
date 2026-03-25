# 🔥 Nitro SMS Strike Pro v2.0
> **The most advanced, high-speed SMS stress-testing and bombing engine for Telegram.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Bot-Telegram--ext-0088cc?logo=telegram)](https://github.com/python-telegram-bot/python-telegram-bot)
[![License](https://img.shields.io/badge/Status-Operational-green)](#)

---

## 🔍 What is this Code?
**Nitro SMS Strike Pro** is a professional-grade Telegram bot designed for SMS stress-testing. It allows users to send high-frequency API requests to a specific phone number to test its notification resilience. 

Built on a robust **Asynchronous I/O (asyncio)** architecture, the bot manages multiple concurrent sessions, handles premium tiered subscriptions, and features a live-updating "Battle Dashboard" for every bombing session.

---

## 🚀 Why Use It?
Manual stress testing is inefficient. This engine provides:
* **Multi-API Load Balancing:** Automatically rotates between multiple APIs to ensure maximum request throughput.
* **Live Progress Tracking:** Features a dynamic progress bar and real-time success/fail counters.
* **Tiered Subscription System:** Includes logic for Silver, Gold, and Diamond tiers with increasing session durations.
* **Admin Command Center:** A full-featured UI for managing users, approving premiums, and monitoring API health.

---

## 💎 Importance
Security researchers and developers use this tool to:
1.  **Flood-Test Notification Systems:** Ensure mobile applications can handle rapid SMS triggers.
2.  **API Resilience Analysis:** Monitor how different SMS gateways respond under heavy load.
3.  **Automated User Management:** The built-in JSON database ensures persistent user data and premium status across restarts.

---

## ⚙️ How It Works
The bot operates through a high-concurrency lifecycle:



1.  **Session Initiation:** The user provides a 10-digit target. The bot checks daily limits (Free vs Premium).
2.  **API Pool Selection:** A random active API is pulled from `apis.json`.
3.  **The Strike Loop:** An asynchronous loop triggers requests every 0.5 seconds.
4.  **Live Updates:** Every request updates the Telegram message via `edit_message_text`, showing elapsed time, remaining time, and success rates.
5.  **Health Monitoring:** Admins can trigger `/apistatus` to perform live latency and success checks on the API pool.

---

## 📊 Comparison: Why Nitro Strike?

| Feature | Standard Bombers | Nitro Strike Pro |
| :--- | :--- | :--- |
| **Concurrency** | Single-threaded (Slow) | Asyncio Coroutines (Fast) |
| **UI** | Text only | Inline Dashboard + Progress Bars |
| **API Management** | Hardcoded | Dynamic `apis.json` (Add/Remove live) |
| **Health Checks** | None | Live Latency & Status Reporting |
| **Persistence** | Data lost on restart | Atomic JSON Data Storage |

---

## 🛠️ Installation & Setup

### 1. Prerequisites
* **Python 3.10+**
* **Active Telegram Bot Token** (from @BotFather)

### 2. Clone & Install
```bash
git clone https://github.com/vikrant-project/Nitro-SMS-Strike-Pro
cd Nitro-SMS-Strike-Pro
pip install python-telegram-bot requests
```

### 3. Configuration
Open `bomber_bot.py` and set your credentials:
* `BOT_TOKEN`: Your Telegram Bot Token.
* `ADMIN_ID`: Your numerical Telegram ID.

### 4. Running the Engine
```bash
python3 bomber_bot.py
```

---

## 🎨 Professional UI Preview
* 🚀 **Battle Dashboard:** Real-time progress bars: `▰▰▰▱▱▱▱▱▱▱ 30%`.
* 💎 **Tier Selection:** Sleek inline buttons for plan upgrades.
* 🛠️ **Admin Panel:** Visual user management (Approve/Revoke) without typing long commands.

---
**Disclaimer:** This tool is for educational and authorized stress-testing purposes only. Unauthorized use against third parties is strictly prohibited. The developer is not responsible for misuse.
