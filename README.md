# 📰 News Delivery Agent (Autonomous AI News Curator)

An intelligent and autonomous news agent that fetches, analyzes, ranks, summarizes, and delivers the **top 10–15 most relevant news stories** to users based on their personal interests — with zero manual prompts or curation.

---

## 🚀 Features

- 🔍 **Autonomous News Curation** – Automatically fetches news using NewsAPI.
- 🧠 **AI Summarization** – Uses Gemini Pro to generate concise summaries.
- 📊 **Ranking Engine** – Ranks articles based on semantic match + recency.
- 🎯 **User Personalization** – Each user gets their own tailored feed.
- 💬 **Telegram Integration** – Delivers news via interactive Telegram bot.
- 🔁 **Inline Button Actions** – Refresh, More News, Change Interests, Top Trends.
- ⏰ **Scheduled Delivery** – Sends personalized news daily at 8:00 AM IST.

---

## 🛠 Tech Stack

- Python 3.7+
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Google Gemini API](https://makersuite.google.com/app)
- [NewsAPI](https://newsapi.org)
- APScheduler (for scheduled tasks)
- JSON (for storing user preferences)

---

## 📁 Project Structure

news-delivery-agent/
├── news_bot.py # Main bot logic
├── user_data.json # User preferences
├── requirements.txt # Dependencies
└── README.md # Documentation 