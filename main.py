from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
from bs4 import BeautifulSoup
import nest_asyncio
import asyncio
from datetime import datetime

BOT_TOKEN = ""

# Список подписчиков
subscribers = []

# Применяем nest_asyncio для корректной работы с вложенными event loops
nest_asyncio.apply()

def get_featured_article():
    url = "https://en.wikipedia.org/wiki/Main_Page"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    featured_article = soup.find("div", id="mp-tfa")
    featured_article_text = featured_article.get_text().split('\n')
    featured_article_text = [str(i) for i in featured_article_text if i != '']
    article_title = featured_article_text[0]

    today_date = datetime.now().strftime("%Y-%m-%d")
    if article_title:
        title_text = [f"<i>{today_date}</i>\n", f"<b>{article_title}</b>\n"]

    text = featured_article_text[1]

    # Извлекаем первое изображение, если оно есть
    image_tag = featured_article.find("img")
    if image_tag:
        image_url = "https:" + image_tag['src']
    else:
        image_url = None
    link = None
    return f"<i>{text}</i>\n", title_text, link, image_url


# Функция отправки статьи
async def send_featured_article():
    article_text, title_text, title_link, image_url = get_featured_article()
    bot = Bot(BOT_TOKEN)

    for chat_id in subscribers:
        formatted_title = title_text[0] + title_text[1] + '\n'

        if image_url:
            # Отправляем картинку, если она есть
            await bot.send_photo(chat_id=chat_id, photo=image_url)

        # Отправляем текст статьи с заголовком
        await bot.send_message(chat_id=chat_id, text=formatted_title + article_text, parse_mode="HTML")


# Команда для подписки
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        await update.message.reply_text(
            "You have subscribed to the daily updates! You will receive the article at 8:00 AM every day."
        )
    else:
        await update.message.reply_text("You are already subscribed.")


# Команда для отписки
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        await update.message.reply_text("You have unsubscribed from the daily updates.")
    else:
        await update.message.reply_text("You are not subscribed.")


# Команда для помощи
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Available commands:\n\n"
        "/start - Start the bot and subscribe\n"
        "/subscribe - Subscribe to daily updates\n"
        "/unsubscribe - Unsubscribe from daily updates\n"
        "/today - Get today's featured article\n"
        "/help - Display this help message"
    )
    await update.message.reply_text(help_text)


# Команда для получения сегодняшней статьи
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    article_text, title_text, title_link, image_url = get_featured_article()
    title_text = title_text[0] + title_text[1] + '\n'
    if image_url:
        # Отправляем картинку, если она есть
        await update.message.reply_photo(photo=image_url)

    # Отправляем текст статьи с заголовком
    await update.message.reply_text(title_text + article_text, parse_mode="HTML")


# Планировщик для отправки статьи в 8:00
async def schedule_articles():
    while True:
        current_time = datetime.now().strftime("%H:%M")  # Текущее время
        if current_time == "08:00":
            # Отправляем статью всем подписчикам
            await send_featured_article()

        await asyncio.sleep(60)  # Проверяем каждую минуту


async def run_bot():
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавление обработчиков команд
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("start", subscribe))
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("help", help_command))

    # Создаем задачу для планировщика
    asyncio.create_task(schedule_articles())

    # Запускаем бота
    await application.run_polling()


if __name__ == "__main__":
    # Проверяем, есть ли активный event loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Если цикл уже запущен, создаем задачу для бота
        asyncio.create_task(run_bot())
    else:
        # Если цикла нет, запускаем через asyncio.run
        asyncio.run(run_bot())
