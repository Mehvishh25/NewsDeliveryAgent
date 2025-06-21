import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    CallbackContext, ConversationHandler, CallbackQueryHandler
)
from apscheduler.schedulers.background import BackgroundScheduler
import google.generativeai as genai
from newsapi import NewsApiClient
import pytz

# === CONFIG ===
TELEGRAM_TOKEN = "8180028720:AAEVGNP8DaUJzJuodpibeaPVzMEAC7EVNWw"
GEMINI_API_KEY = "AIzaSyBb0yOnYLBoicKe8SEajKCeMxqqAzneyzI"
NEWSAPI_KEY = "510a34343fbb4c04bdf0d9fd1bb24a43"
USER_DATA_FILE = "user_data.json"
ARTICLES_PER_PAGE = 5

# === STATES ===
ASK_INTERESTS = 0

# === SETUP ===
logging.basicConfig(level=logging.INFO)
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")
newsapi = NewsApiClient(api_key=NEWSAPI_KEY)
scheduler = BackgroundScheduler()
scheduler.start()

# === USER DATA ===
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

user_data = load_user_data()

# === Gemini Summarizer ===
def summarize_with_gemini(text):
    try:
        response = gemini_model.generate_content(f"Summarize this article:\n{text}")
        return response.candidates[0].content.parts[0].text.strip()
    except Exception:
        return "Summary not available."

# === News Fetcher ===
def fetch_news(interests):
    query = " ".join(interests)
    articles = newsapi.get_everything(q=query, language="en", sort_by="relevancy", page_size=30)
    return articles.get("articles", [])

def fetch_top_trends(country="in", category=None):
    return newsapi.get_top_headlines(country=country, category=category or None, page_size=10).get("articles", [])

# === Send News ===
def send_news(chat_id, context: CallbackContext, refresh=False):
    prefs = user_data.get(str(chat_id), {})
    interests = prefs.get("interests", ["technology"])
    page = 0 if refresh else prefs.get("page", 0)

    if refresh or "articles" not in prefs:
        articles = fetch_news(interests)
        prefs["articles"] = articles
        prefs["page"] = 0
        page = 0
    else:
        articles = prefs["articles"]

    start_idx = page * ARTICLES_PER_PAGE
    end_idx = start_idx + ARTICLES_PER_PAGE
    news_batch = articles[start_idx:end_idx]

    for idx, article in enumerate(news_batch):
        title = article.get("title")
        url = article.get("url")
        content = article.get("description") or article.get("content") or title
        summary = summarize_with_gemini(content)

        msg = f"*{title}*\n🔹 _{summary}_\n🔗 [Read more]({url})"
        buttons = [[InlineKeyboardButton("🧠 Full Summary", callback_data=f"fullsummary_{start_idx + idx}")]]
        context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))

    prefs["page"] = page + 1
    user_data[str(chat_id)] = prefs
    save_user_data(user_data)

    menu = [
        [InlineKeyboardButton("🔁 Refresh", callback_data="refresh")],
        [InlineKeyboardButton("➕ More News", callback_data="more")],
        [InlineKeyboardButton("🔄 Change Interests", callback_data="change")],
        [InlineKeyboardButton("📈 Top Trends Now", callback_data="trending")]
    ]
    context.bot.send_message(chat_id=chat_id, text="👇 Choose an action:", reply_markup=InlineKeyboardMarkup(menu))

# === Handlers ===
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("👋 Welcome! Please type your interests (e.g. technology sports politics):")
    return ASK_INTERESTS

def receive_interests(update: Update, context: CallbackContext) -> int:
    chat_id = str(update.effective_chat.id)
    interests = update.message.text.lower().split()
    user_data[chat_id] = {
        "interests": interests,
        "page": 0
    }
    save_user_data(user_data)
    update.message.reply_text("✅ Interests saved. Fetching your news...")
    send_news(chat_id, context, refresh=True)
    return ConversationHandler.END

def handle_button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat.id
    data = query.data

    if data == "refresh":
        send_news(chat_id, context, refresh=True)
    elif data == "more":
        send_news(chat_id, context)
    elif data == "change":
        context.bot.send_message(chat_id=chat_id, text="🔄 Type new interests:")
        return ASK_INTERESTS
    elif data == "trending":
        articles = fetch_top_trends("in")
        if not articles:
            context.bot.send_message(chat_id=chat_id, text="⚠️ No trending news available at the moment.")
            return
        for a in articles:
            title = a.get("title")
            url = a.get("url")
            content = a.get("description") or a.get("content") or title
            summary = summarize_with_gemini(content)
            msg = f"*{title}*{summary}_[Read more]({url})"
            context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", disable_web_page_preview=True)
    elif data.startswith("fullsummary_"):
        idx = int(data.split("_")[1])
        article = user_data[str(chat_id)]["articles"][idx]
        content = article.get("description") or article.get("content") or article.get("title")
        summary = summarize_with_gemini(content)
        context.bot.send_message(chat_id=chat_id, text=f"🧠 Full Summary:\n{summary}")

# === Daily News Job ===
def send_daily_news():
    for chat_id, prefs in user_data.items():
        try:
            send_news(chat_id, CallbackContext(Updater(TELEGRAM_TOKEN).dispatcher), refresh=True)
        except Exception as e:
            print(f"Failed to send daily news to {chat_id}: {e}")

scheduler.add_job(send_daily_news, "cron", hour=8, minute=0, timezone=pytz.timezone("Asia/Kolkata"))

# === Main ===
def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_INTERESTS: [MessageHandler(Filters.text & ~Filters.command, receive_interests)],
        },
        fallbacks=[]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CallbackQueryHandler(handle_button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, receive_interests))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
