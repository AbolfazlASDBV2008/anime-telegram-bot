import logging
import asyncio
import nest_asyncio  # ۱. این خط را اضافه کنید

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

nest_asyncio.apply()  # ۲. این خط را بلافاصله بعد از ایمپورت‌ها اضافه کنید

# توکن ربات خود را اینجا قرار دهید
BOT_TOKEN = "7786055414:AAFyFoAP-dLSXUa2nn8vOaD_0ubk5oaUGcE"

# ... بقیه کد شما دقیقاً مثل قبل و بدون هیچ تغییری باقی می‌ماند ...

# فعال‌سازی لاگ‌ها
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("سلام! هر فایلی را برای من فوروارد کن تا لینک دانلود مستقیم (و موقت) آن را به تو بدهم.")


async def generate_direct_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    file_to_process = (
        update.message.document
        or update.message.video
        or update.message.audio
        or (update.message.photo[-1] if update.message.photo else None)
    )

    if not file_to_process:
        await update.message.reply_text("لطفاً یک فایل ارسال کنید.")
        return

    try:
        await update.message.reply_text("در حال ساخت لینک...")
        file_info = await context.bot.get_file(file_to_process.file_id)
        
        direct_temporary_link = file_info.file_path
        
        await update.message.reply_text(
            "لینک شما آماده است. آن را کپی کرده و در دانلود منیجر خود Paste کنید:\n\n"
            f"`{direct_temporary_link}`",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"خطا در ایجاد لینک: {e}")
        await update.message.reply_text("خطایی در ایجاد لینک رخ داد.")


async def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ATTACHMENT & ~filters.COMMAND, generate_direct_link))
    print("ربات در حال اجراست...")
    await application.run_polling()


if __name__ == "__main__":
    asyncio.run(main())    """ارسال درخواست به API Jikan با مدیریت خطا."""
    url = f"https://api.jikan.moe/v4/{endpoint}"
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"خطا در اتصال به Jikan API ({url}): {e}")
        return None

def get_latest_episode_from_jikan(anime_id: int) -> int | None:
    """دریافت شماره آخرین قسمت از Jikan API."""
    page = 1
    latest_episode_num = 0
    logger.info(f"[EPISODE_FETCH] شروع جستجو برای آخرین قسمت ID: {anime_id}")
    try:
        while True:
            data = jikan_api_request(f"anime/{anime_id}/episodes?page={page}")
            if not data or not data.get('data'):
                break
            max_in_page = max(ep.get('mal_id', 0) for ep in data['data'])
            if max_in_page > latest_episode_num:
                latest_episode_num = max_in_page
            if not data.get('pagination', {}).get('has_next_page', False):
                break
            page += 1
        logger.info(f"[EPISODE_FETCH] جستجو تمام شد. نتیجه نهایی: {latest_episode_num}")
        return latest_episode_num if latest_episode_num > 0 else None
    except Exception as e:
        logger.error(f"[EPISODE_FETCH] خطا در پردازش قسمت‌ها برای ID {anime_id}: {e}")
        return None

def translate_text(text: str) -> str:
    """ترجمه متن به فارسی با مدیریت خطا."""
    if not text:
        return "خلاصه داستان موجود نیست."
    try:
        return Translator().translate(text, dest='fa').text
    except Exception as e:
        logger.error(f"خطا در ترجمه متن: {e}")
        return f"(ترجمه با خطا مواجه شد)\n\n{text}"

async def send_full_anime_details(chat_id: int, anime_id: int, context: ContextTypes.DEFAULT_TYPE, initial_message=None):
    """ارسال جزئیات کامل انیمه."""
    if initial_message:
        processing_message = initial_message
        await processing_message.edit_text("در حال دریافت جدیدترین اطلاعات...")
    else:
        processing_message = await context.bot.send_message(chat_id=chat_id, text="در حال دریافت جدیدترین اطلاعات...")
    
    full_data = jikan_api_request(f"anime/{anime_id}/full")
    if not full_data or 'data' not in full_data:
        await processing_message.edit_text("خطا: دریافت اطلاعات از API ممکن نبود.")
        return
    
    jikan_details = full_data['data']
    
    title_en = jikan_details.get('title_english') or jikan_details.get('title', 'Unknown')
    title_jp = jikan_details.get('title_japanese', '')
    title_display = f"✨ <b>{title_en}</b> ✨\n<i>{title_jp}</i>"
    
    studios = jikan_details.get('studios', [])
    studio_names = ', '.join([s['name'] for s in studios]) or "نامشخص"
    
    aired_string = jikan_details.get('aired', {}).get('string', "نامشخص")
    synopsis_en = jikan_details.get('synopsis', 'خلاصه داستان موجود نیست.')
    score_val = jikan_details.get('score', 0)
    score_fa = f"{score_val:.2f} از ۱۰" if score_val else "نامشخص"
    status_en = jikan_details.get('status', 'Not yet aired')
    status_fa = TRANSLATIONS['status'].get(status_en, status_en)
    num_episodes = jikan_details.get('episodes')
    num_episodes_fa = num_episodes if num_episodes else "نامشخص"
    
    all_genres_data = jikan_details.get('genres', []) + jikan_details.get('themes', []) + jikan_details.get('demographics', [])
    translated_genres = [TRANSLATIONS['genres'].get(g['name'].lower(), g['name']) for g in all_genres_data]
    genres_fa = ' | '.join(translated_genres) or "نامشخص"

    message_parts = [
        title_display + "\n",
        f"📊 <b>امتیاز:</b> {score_fa}",
        f"📈 <b>وضعیت:</b> {status_fa}",
        f"🏢 <b>استودیو:</b> {studio_names}",
        f"🗓️ <b>تاریخ پخش:</b> {aired_string}",
    ]

    if status_en == "Currently Airing":
        latest_episode = get_latest_episode_from_jikan(anime_id)
        if latest_episode:
            message_parts.append(f"🔥 <b>آخرین قسمت پخش شده:</b> {latest_episode}")

    message_parts.extend([
        f"🎬 <b>قسمت‌ها:</b> {num_episodes_fa}",
        f"📺 <b>نوع:</b> {jikan_details.get('type', 'نامشخص')}\n",
        f"<b>ژانرها:</b>\n{genres_fa}\n",
        f"📝 <b>خلاصه داستان:</b>\n{translate_text(synopsis_en)}"
    ])
    
    message_text = "\n".join(message_parts)
    picture_url = jikan_details.get('images', {}).get('jpg', {}).get('large_image_url', DEFAULT_IMAGE)
    
    await processing_message.delete()

    try:
        response = requests.head(picture_url, timeout=5)
        if response.status_code != 200:
            logger.warning(f"تصویر در {picture_url} در دسترس نیست، استفاده از تصویر پیش‌فرض.")
            picture_url = DEFAULT_IMAGE
        await context.bot.send_photo(chat_id=chat_id, photo=picture_url)
    except Exception as e:
        logger.error(f"خطا در ارسال تصویر برای URL {picture_url}: {e}")
        await context.bot.send_message(chat_id=chat_id, text="تصویر انیمه در دسترس نیست.")

    await context.bot.send_message(chat_id=chat_id, text=message_text, parse_mode=ParseMode.HTML)
    
    keyboard = [[
        InlineKeyboardButton("🤝 انیمه‌های مشابه", callback_data=f"rec_{anime_id}"),
        InlineKeyboardButton("👥 شخصیت‌ها", callback_data=f"char_{anime_id}")
    ]]
    if jikan_details.get('trailer', {}).get('youtube_id'):
        keyboard.append([InlineKeyboardButton("🎬 نمایش تریلر", url=jikan_details['trailer']['url'])])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text="گزینه‌های بیشتر:", reply_markup=reply_markup)

# --- دستورات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name
    welcome_text = (
        f"سلام {user_name}! به ربات دستیار انیمه خوش آمدی. 👋\n\n"
        "من اینجا هستم تا به تو در دنیای بی‌کران انیمه‌ها کمک کنم. تو می‌توانی:\n\n"
        "🔍 **انیمه‌ها را جستجو کنی:** با استفاده از جستجوی هوشمند، هر انیمه‌ای را فوراً پیدا کن.\n"
        "🏆 **بهترین‌ها را بشناسی:** لیست برترین انیمه‌های تاریخ را مشاهده کن.\n"
        "☀️ **به‌روز بمانی:** انیمه‌های جدید هر فصل را دنبال کن.\n\n"
        "برای دیدن لیست کامل دستورات، کافیه دستور /help را ارسال کنی."
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot_username = (await context.bot.get_me()).username
    help_text = (
        "<b>راهنمای کامل دستورات ربات:</b>\n\n"
        f"🔹 `@{bot_username} نام انیمه`\n"
        "<b>(روش اصلی)</b> برای جستجوی هوشمند و زنده هر انیمه‌ای در هر چتی.\n\n"
        "🔹 /topanime\n"
        "نمایش لیست ۱۰ انیمه برتر تاریخ از نظر امتیاز.\n\n"
        "🔹 /seasonal\n"
        "نمایش انیمه‌های محبوب در حال پخش در فصل فعلی.\n\n"
        "🔹 /randomanime\n"
        "دریافت پیشنهاد یک انیمه کاملاً تصادفی برای تماشا."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def top_anime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = await update.message.reply_text("🔝 در حال دریافت ۱۰ انیمه برتر تاریخ...")
    data = jikan_api_request("top/anime?limit=10")
    if data and data.get('data'):
        response_text = "<b>🏆 ۱۰ انیمه برتر تاریخ:</b>\n\n"
        for i, anime in enumerate(data['data']):
            response_text += f"{i+1}. {anime.get('title_english') or anime.get('title', 'Unknown')} - امتیاز: {anime.get('score', 0):.2f}\n/anime_{anime['mal_id']}\n\n"
        await message.edit_text(response_text, parse_mode=ParseMode.HTML)
    else:
        await message.edit_text("خطا در دریافت اطلاعات.")

async def seasonal_anime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = await update.message.reply_text("🏖️ در حال دریافت انیمه‌های فصل جدید...")
    data = jikan_api_request("seasons/now?limit=15")
    if data and data.get('data'):
        response_text = "<b>☀️ انیمه‌های محبوب این فصل:</b>\n\n"
        for i, anime in enumerate(data['data']):
            response_text += f"{i+1}. {anime.get('title_english') or anime.get('title', 'Unknown')}\n/anime_{anime['mal_id']}\n\n"
        await message.edit_text(response_text, parse_mode=ParseMode.HTML)
    else:
        await message.edit_text("خطا در دریافت اطلاعات.")

async def random_anime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = await update.message.reply_text("🎲 در حال انتخاب یک انیمه تصادفی...")
    data = jikan_api_request("random/anime")
    if data and data.get('data'):
        await send_full_anime_details(update.message.chat_id, data['data']['mal_id'], context, initial_message=message)
    else:
        await message.edit_text("خطا در دریافت اطلاعات.")

async def get_anime_details_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        anime_id = int(update.message.text.split('_')[1])
        await update.message.delete()
        await send_full_anime_details(update.message.chat_id, anime_id, context)
    except (IndexError, ValueError):
        await update.message.reply_text("خطا: دستور نامعتبر است.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action, anime_id_str = query.data.split('_', 1)
    chat_id = query.message.chat_id

    if action == 'rec':
        await context.bot.send_message(chat_id=chat_id, text="🔍 در حال یافتن انیمه‌های مشابه...")
        data = jikan_api_request(f"anime/{anime_id_str}/recommendations")
        if data and data.get('data'):
            message = "<b>🤝 انیمه‌های پیشنهادی مشابه:</b>\n\n"
            for i, rec in enumerate(data['data'][:5]):
                entry = rec['entry']
                message += f"{i+1}. {entry.get('title', 'Unknown')}\n/anime_{entry['mal_id']}\n\n"
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=chat_id, text="انیمه مشابهی یافت نشد.")
    
    elif action == 'char':
        await context.bot.send_message(chat_id=chat_id, text="👥 در حال دریافت لیست شخصیت‌ها...")
        data = jikan_api_request(f"anime/{anime_id_str}/characters")
        if data and data.get('data'):
            for i, item in enumerate(data['data'][:7]):
                char = item['character']
                img_url = char.get('images', {}).get('jpg', {}).get('image_url', DEFAULT_IMAGE)
                caption = f"<b>{char.get('name', 'Unknown')}</b>\n<i>{item.get('role', 'Unknown')}</i>"
                try:
                    response = requests.head(img_url, timeout=5)
                    if response.status_code != 200:
                        logger.warning(f"تصویر شخصیت در {img_url} در دسترس نیست، استفاده از تصویر پیش‌فرض.")
                        img_url = DEFAULT_IMAGE
                    await context.bot.send_photo(chat_id=chat_id, photo=img_url, caption=caption, parse_mode=ParseMode.HTML)
                except (BadRequest, TimedOut, requests.RequestException) as e:
                    logger.error(f"خطا در ارسال تصویر شخصیت برای URL {img_url}: {e}")
                    await context.bot.send_message(chat_id=chat_id, text=caption + " (عکس ناموفق بود)", parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=chat_id, text="شخصیتی یافت نشد.")

async def inline_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query.lower()
    if not query or len(query) < 3:
        await update.inline_query.answer([], cache_time=10)
        return
    
    results = []
    found_ids = set()
    
    for item in search_index:
        if query in item['search_string']:
            if item['mal_id'] in found_ids:
                continue
            description_text = f"امتیاز: {item['score']} | نوع: {item['type']}"
            results.append(
                InlineQueryResultArticle(
                    id=item['mal_id'],
                    title=item['title'],
                    thumb_url=item['picture'],
                    description=description_text,
                    input_message_content=InputTextMessageContent(f"/anime_{item['mal_id']}")
                )
            )
            found_ids.add(item['mal_id'])
            if len(results) >= 15:
                break
    
    try:
        await update.inline_query.answer(results, cache_time=5)
    except TimedOut:
        logger.warning("TimedOut در جستجوی inline.")

async def main() -> None:
    """اجرای ربات."""
    try:
        build_search_index()
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("topanime", top_anime))
        application.add_handler(CommandHandler("seasonal", seasonal_anime))
        application.add_handler(CommandHandler("randomanime", random_anime))
        application.add_handler(InlineQueryHandler(inline_search))
        application.add_handler(MessageHandler(filters.Regex(r'^/anime_\d+$'), get_anime_details_command))
        application.add_handler(CallbackQueryHandler(button_handler))

        logger.info("ربات بی‌نقص و نهایی اجرا شد!")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"خطا در اجرای ربات: {e}", exc_info=True)
        exit()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"خطا در اتصال به Jikan API ({url}): {e}")
        return None

def get_latest_episode_from_jikan(anime_id: int) -> int | None:
    page = 1
    latest_episode_num = 0
    logger.info(f"[EPISODE_FETCH] شروع جستجو برای آخرین قسمت ID: {anime_id}")
    try:
        while True:
            data = jikan_api_request(f"anime/{anime_id}/episodes?page={page}")
            if not data or not data.get('data'):
                break
            max_in_page = max(ep.get('mal_id', 0) for ep in data['data'])
            if max_in_page > latest_episode_num:
                latest_episode_num = max_in_page
            if not data.get('pagination', {}).get('has_next_page', False):
                break
            page += 1
        logger.info(f"[EPISODE_FETCH] جستجو تمام شد. نتیجه نهایی: {latest_episode_num}")
        return latest_episode_num if latest_episode_num > 0 else None
    except Exception as e:
        logger.error(f"[EPISODE_FETCH] خطا در پردازش قسمت‌ها برای ID {anime_id}: {e}")
        return None

def translate_text(text: str):
    if not text: return "خلاصه داستان موجود نیست."
    try: return Translator().translate(text, dest='fa').text
    except Exception: return f"(ترجمه با خطا مواجه شد)\n\n{text}"

async def send_full_anime_details(chat_id: int, anime_id: int, context: CallbackContext, initial_message=None):
    if initial_message:
        processing_message = initial_message
        await processing_message.edit_text("در حال دریافت جدیدترین اطلاعات...")
    else:
        processing_message = await context.bot.send_message(chat_id=chat_id, text="در حال دریافت جدیدترین اطلاعات...")
    
    full_data = jikan_api_request(f"anime/{anime_id}/full")
    if not full_data or 'data' not in full_data:
        await processing_message.edit_text("خطا: دریافت اطلاعات از API ممکن نبود.")
        return
    
    jikan_details = full_data['data']
    
    title_en = jikan_details.get('title_english') or jikan_details.get('title')
    title_jp = jikan_details.get('title_japanese', '')
    title_display = f"✨ <b>{title_en}</b> ✨\n<i>{title_jp}</i>"
    
    studios = jikan_details.get('studios', [])
    studio_names = ', '.join([s['name'] for s in studios]) or "نامشخص"
    
    aired_string = jikan_details.get('aired', {}).get('string', "نامشخص")
    synopsis_en = jikan_details.get('synopsis', 'خلاصه داستان موجود نیست.')
    score_val = jikan_details.get('score', 0)
    score_fa = f"{score_val:.2f} از ۱۰" if score_val else "نامشخص"
    status_en = jikan_details.get('status', 'Not yet aired')
    status_fa = TRANSLATIONS['status'].get(status_en, status_en)
    num_episodes = jikan_details.get('episodes')
    num_episodes_fa = num_episodes if num_episodes else "نامشخص"
    
    all_genres_data = jikan_details.get('genres', []) + jikan_details.get('themes', []) + jikan_details.get('demographics', [])
    translated_genres = [TRANSLATIONS['genres'].get(g['name'].lower(), g['name']) for g in all_genres_data]
    genres_fa = ' | '.join(translated_genres) or "نامشخص"

    message_parts = [
        title_display + "\n", f"📊 <b>امتیاز:</b> {score_fa}", f"📈 <b>وضعیت:</b> {status_fa}",
        f"🏢 <b>استودیو:</b> {studio_names}", f"🗓️ <b>تاریخ پخش:</b> {aired_string}",
    ]

    if status_en == "Currently Airing":
        latest_episode = get_latest_episode_from_jikan(anime_id)
        if latest_episode:
            message_parts.append(f"🔥 <b>آخرین قسمت پخش شده:</b> {latest_episode}")

    message_parts.extend([
        f"🎬 <b>قسمت‌ها:</b> {num_episodes_fa}", f"📺 <b>نوع:</b> {jikan_details.get('type', 'نامشخص')}\n",
        f"<b>ژانرها:</b>\n{genres_fa}\n", f"📝 <b>خلاصه داستان:</b>\n{translate_text(synopsis_en)}"
    ])
    
    message_text = "\n".join(message_parts)
    picture_url = jikan_details.get('images', {}).get('jpg', {}).get('large_image_url')
    
    await processing_message.delete()

    if picture_url:
        try: await context.bot.send_photo(chat_id=chat_id, photo=picture_url)
        except Exception: pass
    
    await context.bot.send_message(chat_id=chat_id, text=message_text, parse_mode=ParseMode.HTML)
    
    keyboard = [[
        InlineKeyboardButton("🤝 انیمه‌های مشابه", callback_data=f"rec_{anime_id}"),
        InlineKeyboardButton("👥 شخصیت‌ها", callback_data=f"char_{anime_id}")
    ]]
    if jikan_details.get('trailer', {}).get('youtube_id'):
        keyboard.append([InlineKeyboardButton("🎬 نمایش تریلر", url=jikan_details['trailer']['url'])])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text="گزینه‌های بیشتر:", reply_markup=reply_markup)

# --- دستورات ---
async def start(update: Update, context: CallbackContext) -> None:
    user_name = update.effective_user.first_name
    welcome_text = (
        f"سلام {user_name}! به ربات دستیار انیمه خوش آمدی. 👋\n\n"
        "من اینجا هستم تا به تو در دنیای بی‌کران انیمه‌ها کمک کنم. تو می‌توانی:\n\n"
        "🔍 **انیمه‌ها را جستجو کنی:** با استفاده از جستجوی هوشمند، هر انیمه‌ای را فوراً پیدا کن.\n"
        "🏆 **بهترین‌ها را بشناسی:** لیست برترین انیمه‌های تاریخ را مشاهده کن.\n"
        "☀️ **به‌روز بمانی:** انیمه‌های جدید هر فصل را دنبال کن.\n\n"
        "برای دیدن لیست کامل دستورات، کافیه دستور /help را ارسال کنی."
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: CallbackContext) -> None:
    bot_username = context.bot.username
    help_text = (
        "<b>راهنمای کامل دستورات ربات:</b>\n\n"
        f"🔹 `@{bot_username} نام انیمه`\n"
        "<b>(روش اصلی)</b> برای جستجوی هوشمند و زنده هر انیمه‌ای در هر چتی.\n\n"
        "🔹 /topanime\n"
        "نمایش لیست ۱۰ انیمه برتر تاریخ از نظر امتیاز.\n\n"
        "🔹 /seasonal\n"
        "نمایش انیمه‌های محبوب در حال پخش در فصل فعلی.\n\n"
        "🔹 /randomanime\n"
        "دریافت پیشنهاد یک انیمه کاملاً تصادفی برای تماشا."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def top_anime(update: Update, context: CallbackContext) -> None:
    message = await update.message.reply_text("🔝 در حال دریافت ۱۰ انیمه برتر تاریخ...")
    data = jikan_api_request("top/anime?limit=10")
    if data and data.get('data'):
        response_text = "<b>🏆 ۱۰ انیمه برتر تاریخ:</b>\n\n"
        for i, anime in enumerate(data['data']):
            response_text += f"{i+1}. {anime.get('title_english') or anime.get('title')} - امتیاز: {anime.get('score', 0):.2f}\n/anime_{anime['mal_id']}\n\n"
        await message.edit_text(response_text, parse_mode=ParseMode.HTML)
    else:
        await message.edit_text("خطا در دریافت اطلاعات.")

async def seasonal_anime(update: Update, context: CallbackContext) -> None:
    message = await update.message.reply_text("🏖️ در حال دریافت انیمه‌های فصل جدید...")
    data = jikan_api_request("seasons/now?limit=15")
    if data and data.get('data'):
        response_text = "<b>☀️ انیمه‌های محبوب این فصل:</b>\n\n"
        for i, anime in enumerate(data['data']):
            response_text += f"{i+1}. {anime.get('title_english') or anime.get('title')}\n/anime_{anime['mal_id']}\n\n"
        await message.edit_text(response_text, parse_mode=ParseMode.HTML)
    else:
        await message.edit_text("خطا در دریافت اطلاعات.")

async def random_anime(update: Update, context: CallbackContext) -> None:
    message = await update.message.reply_text("🎲 در حال انتخاب یک انیمه تصادفی...")
    data = jikan_api_request("random/anime")
    if data and data.get('data'):
        await send_full_anime_details(update.message.chat_id, data['data']['mal_id'], context, initial_message=message)
    else:
        await message.edit_text("خطا در دریافت اطلاعات.")

async def get_anime_details_command(update: Update, context: CallbackContext) -> None:
    anime_id = int(update.message.text.split('_')[1])
    await update.message.delete()
    await send_full_anime_details(update.message.chat_id, anime_id, context)

async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    action, anime_id_str = query.data.split('_', 1)
    chat_id = query.message.chat_id

    if action == 'rec':
        await context.bot.send_message(chat_id=chat_id, text="🔍 در حال یافتن انیمه‌های مشابه...")
        data = jikan_api_request(f"anime/{anime_id_str}/recommendations")
        if data and data.get('data'):
            message = "<b>🤝 انیمه‌های پیشنهادی مشابه:</b>\n\n"
            for i, rec in enumerate(data['data'][:5]):
                entry = rec['entry']
                message += f"{i+1}. {entry.get('title')}\n/anime_{entry['mal_id']}\n\n"
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=chat_id, text="انیمه مشابهی یافت نشد.")
    
    elif action == 'char':
        await context.bot.send_message(chat_id=chat_id, text="👥 در حال دریافت لیست شخصیت‌ها...")
        data = jikan_api_request(f"anime/{anime_id_str}/characters")
        if data and data.get('data'):
            for i, item in enumerate(data['data'][:7]):
                char = item['character']
                img_url = char.get('images', {}).get('jpg', {}).get('image_url')
                caption = f"<b>{char['name']}</b>\n<i>{item['role']}</i>"
                if img_url:
                    try:
                        await context.bot.send_photo(chat_id=chat_id, photo=img_url, caption=caption, parse_mode=ParseMode.HTML)
                    except (BadRequest, TimedOut):
                        await context.bot.send_message(chat_id=chat_id, text=caption + " (عکس ناموفق بود)", parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=chat_id, text="شخصیتی یافت نشد.")

async def inline_search(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query.lower()
    if not query or len(query) < 3:
        await update.inline_query.answer([], cache_time=10)
        return
    
    results = []
    found_ids = set()
    
    for item in search_index:
        if query in item['search_string']:
            if item['mal_id'] in found_ids:
                continue

            description_text = f"امتیاز: {item['score']} | نوع: {item['type']}"
            
            results.append(
                InlineQueryResultArticle(
                    id=item['mal_id'],
                    title=item['title'],
                    thumb_url=item['picture'],
                    description=description_text,
                    input_message_content=InputTextMessageContent(f"/anime_{item['mal_id']}")
                )
            )
            found_ids.add(item['mal_id'])
            if len(results) >= 15:
                break
    
    try:
        await update.inline_query.answer(results, cache_time=5)
    except TimedOut:
        logger.warning("TimedOut در جستجوی inline.")

def main() -> None:
    build_search_index()

    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("topanime", top_anime))
    application.add_handler(CommandHandler("seasonal", seasonal_anime))
    application.add_handler(CommandHandler("randomanime", random_anime))
    application.add_handler(InlineQueryHandler(inline_search))
    application.add_handler(MessageHandler(filters.Regex(r'^/anime_\d+$'), get_anime_details_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()
    logger.info("ربات بی‌نقص و نهایی اجرا شد!")

if __name__ == '__main__':
    main()    except requests.exceptions.RequestException as e:
        logger.error(f"خطا در اتصال به Jikan API ({url}): {e}")
        return None

def get_latest_episode_from_jikan(anime_id: int) -> int | None:
    page = 1
    latest_episode_num = 0
    logger.info(f"[EPISODE_FETCH] شروع جستجو برای آخرین قسمت ID: {anime_id}")
    try:
        while True:
            data = jikan_api_request(f"anime/{anime_id}/episodes?page={page}")
            if not data or not data.get('data'):
                break
            max_in_page = max(ep.get('mal_id', 0) for ep in data['data'])
            if max_in_page > latest_episode_num:
                latest_episode_num = max_in_page
            if not data.get('pagination', {}).get('has_next_page', False):
                break
            page += 1
        logger.info(f"[EPISODE_FETCH] جستجو تمام شد. نتیجه نهایی: {latest_episode_num}")
        return latest_episode_num if latest_episode_num > 0 else None
    except Exception as e:
        logger.error(f"[EPISODE_FETCH] خطا در پردازش قسمت‌ها برای ID {anime_id}: {e}")
        return None

def translate_text(text: str):
    if not text: return "خلاصه داستان موجود نیست."
    try: return Translator().translate(text, dest='fa').text
    except Exception: return f"(ترجمه با خطا مواجه شد)\n\n{text}"

def send_full_anime_details(chat_id: int, anime_id: int, context: CallbackContext, initial_message=None):
    if initial_message:
        processing_message = initial_message
        processing_message.edit_text("در حال دریافت جدیدترین اطلاعات...")
    else:
        processing_message = context.bot.send_message(chat_id=chat_id, text="در حال دریافت جدیدترین اطلاعات...")
    
    full_data = jikan_api_request(f"anime/{anime_id}/full")
    if not full_data or 'data' not in full_data:
        processing_message.edit_text("خطا: دریافت اطلاعات از API ممکن نبود.")
        return
    
    jikan_details = full_data['data']
    
    title_en = jikan_details.get('title_english') or jikan_details.get('title')
    title_jp = jikan_details.get('title_japanese', '')
    title_display = f"✨ <b>{title_en}</b> ✨\n<i>{title_jp}</i>"
    
    studios = jikan_details.get('studios', [])
    studio_names = ', '.join([s['name'] for s in studios]) or "نامشخص"
    
    aired_string = jikan_details.get('aired', {}).get('string', "نامشخص")
    synopsis_en = jikan_details.get('synopsis', 'خلاصه داستان موجود نیست.')
    score_val = jikan_details.get('score', 0)
    score_fa = f"{score_val:.2f} از ۱۰" if score_val else "نامشخص"
    status_en = jikan_details.get('status', 'Not yet aired')
    status_fa = TRANSLATIONS['status'].get(status_en, status_en)
    num_episodes = jikan_details.get('episodes')
    num_episodes_fa = num_episodes if num_episodes else "نامشخص"
    
    all_genres_data = jikan_details.get('genres', []) + jikan_details.get('themes', []) + jikan_details.get('demographics', [])
    translated_genres = [TRANSLATIONS['genres'].get(g['name'].lower(), g['name']) for g in all_genres_data]
    genres_fa = ' | '.join(translated_genres) or "نامشخص"

    message_parts = [
        title_display + "\n", f"📊 <b>امتیاز:</b> {score_fa}", f"📈 <b>وضعیت:</b> {status_fa}",
        f"🏢 <b>استودیو:</b> {studio_names}", f"🗓️ <b>تاریخ پخش:</b> {aired_string}",
    ]

    if status_en == "Currently Airing":
        latest_episode = get_latest_episode_from_jikan(anime_id)
        if latest_episode:
            message_parts.append(f"🔥 <b>آخرین قسمت پخش شده:</b> {latest_episode}")

    message_parts.extend([
        f"🎬 <b>قسمت‌ها:</b> {num_episodes_fa}", f"📺 <b>نوع:</b> {jikan_details.get('type', 'نامشخص')}\n",
        f"<b>ژانرها:</b>\n{genres_fa}\n", f"📝 <b>خلاصه داستان:</b>\n{translate_text(synopsis_en)}"
    ])
    
    message_text = "\n".join(message_parts)
    picture_url = jikan_details.get('images', {}).get('jpg', {}).get('large_image_url')
    
    processing_message.delete()

    if picture_url:
        try: context.bot.send_photo(chat_id=chat_id, photo=picture_url)
        except Exception: pass
    
    context.bot.send_message(chat_id=chat_id, text=message_text, parse_mode=ParseMode.HTML)
    
    keyboard = [[
        InlineKeyboardButton("🤝 انیمه‌های مشابه", callback_data=f"rec_{anime_id}"),
        InlineKeyboardButton("👥 شخصیت‌ها", callback_data=f"char_{anime_id}")
    ]]
    if jikan_details.get('trailer', {}).get('youtube_id'):
        keyboard.append([InlineKeyboardButton("🎬 نمایش تریلر", url=jikan_details['trailer']['url'])])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=chat_id, text="گزینه‌های بیشتر:", reply_markup=reply_markup)

# --- دستورات ---
def start(update: Update, context: CallbackContext) -> None:
    user_name = update.effective_user.first_name
    welcome_text = (
        f"سلام {user_name}! به ربات دستیار انیمه خوش آمدی. 👋\n\n"
        "من اینجا هستم تا به تو در دنیای بی‌کران انیمه‌ها کمک کنم. تو می‌توانی:\n\n"
        "🔍 **انیمه‌ها را جستجو کنی:** با استفاده از جستجوی هوشمند، هر انیمه‌ای را فوراً پیدا کن.\n"
        "🏆 **بهترین‌ها را بشناسی:** لیست برترین انیمه‌های تاریخ را مشاهده کن.\n"
        "☀️ **به‌روز بمانی:** انیمه‌های جدید هر فصل را دنبال کن.\n\n"
        "برای دیدن لیست کامل دستورات، کافیه دستور /help را ارسال کنی."
    )
    update.message.reply_text(welcome_text)

def help_command(update: Update, context: CallbackContext) -> None:
    bot_username = context.bot.username
    help_text = (
        "<b>راهنمای کامل دستورات ربات:</b>\n\n"
        f"🔹 `@{bot_username} نام انیمه`\n"
        "<b>(روش اصلی)</b> برای جستجوی هوشمند و زنده هر انیمه‌ای در هر چتی.\n\n"
        "🔹 /topanime\n"
        "نمایش لیست ۱۰ انیمه برتر تاریخ از نظر امتیاز.\n\n"
        "🔹 /seasonal\n"
        "نمایش انیمه‌های محبوب در حال پخش در فصل فعلی.\n\n"
        "🔹 /randomanime\n"
        "دریافت پیشنهاد یک انیمه کاملاً تصادفی برای تماشا."
    )
    update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

def top_anime(update: Update, context: CallbackContext) -> None:
    message = update.message.reply_text("🔝 در حال دریافت ۱۰ انیمه برتر تاریخ...")
    data = jikan_api_request("top/anime?limit=10")
    if data and data.get('data'):
        response_text = "<b>🏆 ۱۰ انیمه برتر تاریخ:</b>\n\n"
        for i, anime in enumerate(data['data']):
            response_text += f"{i+1}. {anime.get('title_english') or anime.get('title')} - امتیاز: {anime.get('score', 0):.2f}\n/anime_{anime['mal_id']}\n\n"
        message.edit_text(response_text, parse_mode=ParseMode.HTML)
    else:
        message.edit_text("خطا در دریافت اطلاعات.")

def seasonal_anime(update: Update, context: CallbackContext) -> None:
    message = update.message.reply_text("🏖️ در حال دریافت انیمه‌های فصل جدید...")
    data = jikan_api_request("seasons/now?limit=15")
    if data and data.get('data'):
        response_text = "<b>☀️ انیمه‌های محبوب این فصل:</b>\n\n"
        for i, anime in enumerate(data['data']):
            response_text += f"{i+1}. {anime.get('title_english') or anime.get('title')}\n/anime_{anime['mal_id']}\n\n"
        message.edit_text(response_text, parse_mode=ParseMode.HTML)
    else:
        message.edit_text("خطا در دریافت اطلاعات.")

def random_anime(update: Update, context: CallbackContext) -> None:
    message = update.message.reply_text("🎲 در حال انتخاب یک انیمه تصادفی...")
    data = jikan_api_request("random/anime")
    if data and data.get('data'):
        send_full_anime_details(update.message.chat_id, data['data']['mal_id'], context, initial_message=message)
    else:
        message.edit_text("خطا در دریافت اطلاعات.")

def get_anime_details_command(update: Update, context: CallbackContext) -> None:
    anime_id = int(update.message.text.split('_')[1])
    update.message.delete()
    send_full_anime_details(update.message.chat_id, anime_id, context)

def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    action, anime_id_str = query.data.split('_', 1)
    chat_id = query.message.chat_id

    if action == 'rec':
        context.bot.send_message(chat_id=chat_id, text="🔍 در حال یافتن انیمه‌های مشابه...")
        data = jikan_api_request(f"anime/{anime_id_str}/recommendations")
        if data and data.get('data'):
            message = "<b>🤝 انیمه‌های پیشنهادی مشابه:</b>\n\n"
            for i, rec in enumerate(data['data'][:5]):
                entry = rec['entry']
                message += f"{i+1}. {entry.get('title')}\n/anime_{entry['mal_id']}\n\n"
            context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
        else:
            context.bot.send_message(chat_id=chat_id, text="انیمه مشابهی یافت نشد.")
    
    elif action == 'char':
        context.bot.send_message(chat_id=chat_id, text="👥 در حال دریافت لیست شخصیت‌ها...")
        data = jikan_api_request(f"anime/{anime_id_str}/characters")
        if data and data.get('data'):
            for i, item in enumerate(data['data'][:7]):
                char = item['character']
                img_url = char.get('images', {}).get('jpg', {}).get('image_url')
                caption = f"<b>{char['name']}</b>\n<i>{item['role']}</i>"
                if img_url:
                    try:
                        context.bot.send_photo(chat_id=chat_id, photo=img_url, caption=caption, parse_mode=ParseMode.HTML)
                    except (BadRequest, TimedOut):
                        context.bot.send_message(chat_id=chat_id, text=caption + " (عکس ناموفق بود)", parse_mode=ParseMode.HTML)
        else:
            context.bot.send_message(chat_id=chat_id, text="شخصیتی یافت نشد.")

def inline_search(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query.lower()
    if not query or len(query) < 3:
        update.inline_query.answer([], cache_time=10)
        return
    
    results = []
    found_ids = set()
    
    for item in search_index:
        if query in item['search_string']:
            if item['mal_id'] in found_ids:
                continue

            description_text = f"امتیاز: {item['score']} | نوع: {item['type']}"
            
            results.append(
                InlineQueryResultArticle(
                    id=item['mal_id'],
                    title=item['title'],
                    thumb_url=item['picture'],
                    description=description_text,
                    input_message_content=InputTextMessageContent(f"/anime_{item['mal_id']}")
                )
            )
            found_ids.add(item['mal_id'])
            if len(results) >= 15:
                break
    
    try:
        update.inline_query.answer(results, cache_time=5)
    except TimedOut:
        logger.warning("TimedOut در جستجوی inline.")

def main() -> None:
    build_search_index()

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("topanime", top_anime))
    dp.add_handler(CommandHandler("seasonal", seasonal_anime))
    dp.add_handler(CommandHandler("randomanime", random_anime))
    dp.add_handler(InlineQueryHandler(inline_search))
    dp.add_handler(MessageHandler(Filters.regex(r'^/anime_\d+$'), get_anime_details_command))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    logger.info("ربات بی‌نقص و نهایی اجرا شد!")
    updater.idle()

if __name__ == '__main__':
    main()        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"خطا در اتصال به Jikan API ({url}): {e}")
        return None

def get_latest_episode_from_jikan(anime_id: int) -> int | None:
    """آخرین شماره قسمت پخش شده برای یک انیمه را از Jikan API دریافت می‌کند."""
    page = 1
    latest_episode_num = 0
    logger.info(f"[EPISODE_FETCH] شروع جستجو برای آخرین قسمت ID: {anime_id}")
    try:
        while True:
            data = jikan_api_request(f"anime/{anime_id}/episodes?page={page}")
            if not data or not data.get('data'):
                break
            max_in_page = max(ep.get('mal_id', 0) for ep in data['data'])
            if max_in_page > latest_episode_num:
                latest_episode_num = max_in_page
            if not data.get('pagination', {}).get('has_next_page', False):
                break
            page += 1
        logger.info(f"[EPISODE_FETCH] جستجو تمام شد. نتیجه نهایی: {latest_episode_num}")
        return latest_episode_num if latest_episode_num > 0 else None
    except Exception as e:
        logger.error(f"[EPISODE_FETCH] خطا در پردازش قسمت‌ها برای ID {anime_id}: {e}")
        return None

def translate_text(text: str):
    """متن را با استفاده از deep-translator به فارسی ترجمه می‌کند."""
    if not text: return "خلاصه داستان موجود نیست."
    try:
        return GoogleTranslator(source='auto', target='fa').translate(text)
    except Exception as e:
        logger.error(f"خطا در ترجمه متن: {e}")
        return f"(ترجمه با خطا مواجه شد)\n\n{text}"

async def send_full_anime_details(chat_id: int, anime_id: int, context: ContextTypes.DEFAULT_TYPE, initial_message=None):
    """اطلاعات کامل یک انیمه را دریافت و در چت ارسال می‌کند."""
    if initial_message:
        processing_message = await initial_message.edit_text("در حال دریافت جدیدترین اطلاعات...")
    else:
        processing_message = await context.bot.send_message(chat_id=chat_id, text="در حال دریافت جدیدترین اطلاعات...")
    
    full_data = jikan_api_request(f"anime/{anime_id}/full")
    if not full_data or 'data' not in full_data:
        await processing_message.edit_text("خطا: دریافت اطلاعات از API ممکن نبود.")
        return
    
    jikan_details = full_data['data']
    
    title_en = jikan_details.get('title_english') or jikan_details.get('title')
    title_jp = jikan_details.get('title_japanese', '')
    title_display = f"✨ <b>{title_en}</b> ✨\n<i>{title_jp}</i>"
    
    studios = jikan_details.get('studios', [])
    studio_names = ', '.join([s['name'] for s in studios]) or "نامشخص"
    
    aired_string = jikan_details.get('aired', {}).get('string', "نامشخص")
    synopsis_en = jikan_details.get('synopsis', 'خلاصه داستان موجود نیست.')
    score_val = jikan_details.get('score', 0)
    score_fa = f"{score_val:.2f} از ۱۰" if score_val else "نامشخص"
    status_en = jikan_details.get('status', 'Not yet aired')
    status_fa = TRANSLATIONS['status'].get(status_en, status_en)
    num_episodes = jikan_details.get('episodes')
    num_episodes_fa = num_episodes if num_episodes else "نامشخص"
    
    all_genres_data = jikan_details.get('genres', []) + jikan_details.get('themes', []) + jikan_details.get('demographics', [])
    translated_genres = [TRANSLATIONS['genres'].get(g['name'].lower(), g['name']) for g in all_genres_data]
    genres_fa = ' | '.join(translated_genres) or "نامشخص"

    message_parts = [
        title_display + "\n", f"📊 <b>امتیاز:</b> {score_fa}", f"📈 <b>وضعیت:</b> {status_fa}",
        f"🏢 <b>استودیو:</b> {studio_names}", f"🗓️ <b>تاریخ پخش:</b> {aired_string}",
    ]

    if status_en == "Currently Airing":
        latest_episode = get_latest_episode_from_jikan(anime_id)
        if latest_episode:
            message_parts.append(f"🔥 <b>آخرین قسمت پخش شده:</b> {latest_episode}")

    message_parts.extend([
        f"🎬 <b>قسمت‌ها:</b> {num_episodes_fa}", f"📺 <b>نوع:</b> {jikan_details.get('type', 'نامشخص')}\n",
        f"<b>ژانرها:</b>\n{genres_fa}\n", f"📝 <b>خلاصه داستان:</b>\n{translate_text(synopsis_en)}"
    ])
    
    message_text = "\n".join(message_parts)
    picture_url = jikan_details.get('images', {}).get('jpg', {}).get('large_image_url')
    
    await processing_message.delete()

    if picture_url:
        try: await context.bot.send_photo(chat_id=chat_id, photo=picture_url)
        except Exception: pass
    
    await context.bot.send_message(chat_id=chat_id, text=message_text, parse_mode=constants.ParseMode.HTML)
    
    keyboard = [[
        InlineKeyboardButton("🤝 انیمه‌های مشابه", callback_data=f"rec_{anime_id}"),
        InlineKeyboardButton("👥 شخصیت‌ها", callback_data=f"char_{anime_id}")
    ]]
    if jikan_details.get('trailer', {}).get('youtube_id'):
        keyboard.append([InlineKeyboardButton("🎬 نمایش تریلر", url=jikan_details['trailer']['url'])])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text="گزینه‌های بیشتر:", reply_markup=reply_markup)

# --- دستورات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال پیام خوش‌آمدگویی."""
    user_name = update.effective_user.first_name
    welcome_text = (
        f"سلام {user_name}! به ربات دستیار انیمه خوش آمدی. 👋\n\n"
        "من اینجا هستم تا به تو در دنیای بی‌کران انیمه‌ها کمک کنم. تو می‌توانی:\n\n"
        "🔍 **انیمه‌ها را جستجو کنی:** با استفاده از جستجوی هوشمند، هر انیمه‌ای را فوراً پیدا کن.\n"
        "🏆 **بهترین‌ها را بشناسی:** لیست برترین انیمه‌های تاریخ را مشاهده کن.\n"
        "☀️ **به‌روز بمانی:** انیمه‌های جدید هر فصل را دنبال کن.\n\n"
        "برای دیدن لیست کامل دستورات، کافیه دستور /help را ارسال کنی."
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال پیام راهنما."""
    bot_username = (await context.bot.get_me()).username
    help_text = (
        "<b>راهنمای کامل دستورات ربات:</b>\n\n"
        f"🔹 `@{bot_username} نام انیمه`\n"
        "<b>(روش اصلی)</b> برای جستجوی هوشمند و زنده هر انیمه‌ای در هر چتی.\n\n"
        "🔹 /topanime\n"
        "نمایش لیست ۱۰ انیمه برتر تاریخ از نظر امتیاز.\n\n"
        "🔹 /seasonal\n"
        "نمایش انیمه‌های محبوب در حال پخش در فصل فعلی.\n\n"
        "🔹 /randomanime\n"
        "دریافت پیشنهاد یک انیمه کاملاً تصادفی برای تماشا."
    )
    await update.message.reply_text(help_text, parse_mode=constants.ParseMode.HTML)

async def top_anime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال لیست ۱۰ انیمه برتر."""
    message = await update.message.reply_text("🔝 در حال دریافت ۱۰ انیمه برتر تاریخ...")
    data = jikan_api_request("top/anime?limit=10")
    if data and data.get('data'):
        response_text = "<b>🏆 ۱۰ انیمه برتر تاریخ:</b>\n\n"
        for i, anime in enumerate(data['data']):
            response_text += f"{i+1}. {anime.get('title_english') or anime.get('title')} - امتیاز: {anime.get('score', 0):.2f}\n/anime_{anime['mal_id']}\n\n"
        await message.edit_text(response_text, parse_mode=constants.ParseMode.HTML)
    else:
        await message.edit_text("خطا در دریافت اطلاعات.")

async def seasonal_anime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال لیست انیمه‌های فصلی."""
    message = await update.message.reply_text("🏖️ در حال دریافت انیمه‌های فصل جدید...")
    data = jikan_api_request("seasons/now?limit=15")
    if data and data.get('data'):
        response_text = "<b>☀️ انیمه‌های محبوب این فصل:</b>\n\n"
        for i, anime in enumerate(data['data']):
            response_text += f"{i+1}. {anime.get('title_english') or anime.get('title')}\n/anime_{anime['mal_id']}\n\n"
        await message.edit_text(response_text, parse_mode=constants.ParseMode.HTML)
    else:
        await message.edit_text("خطا در دریافت اطلاعات.")

async def random_anime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال یک انیمه تصادفی."""
    message = await update.message.reply_text("🎲 در حال انتخاب یک انیمه تصادفی...")
    data = jikan_api_request("random/anime")
    if data and data.get('data'):
        await send_full_anime_details(update.message.chat_id, data['data']['mal_id'], context, initial_message=message)
    else:
        await message.edit_text("خطا در دریافت اطلاعات.")

async def get_anime_details_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پردازش دستور /anime_ID برای نمایش اطلاعات."""
    anime_id = int(update.message.text.split('_')[1])
    await update.message.delete()
    await send_full_anime_details(update.message.chat_id, anime_id, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پردازش دکمه‌های شیشه‌ای."""
    query = update.callback_query
    await query.answer()
    action, anime_id_str = query.data.split('_', 1)
    chat_id = query.message.chat_id

    if action == 'rec':
        await context.bot.send_message(chat_id=chat_id, text="🔍 در حال یافتن انیمه‌های مشابه...")
        data = jikan_api_request(f"anime/{anime_id_str}/recommendations")
        if data and data.get('data'):
            message = "<b>🤝 انیمه‌های پیشنهادی مشابه:</b>\n\n"
            for i, rec in enumerate(data['data'][:5]):
                entry = rec['entry']
                message += f"{i+1}. {entry.get('title')}\n/anime_{entry['mal_id']}\n\n"
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=constants.ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=chat_id, text="انیمه مشابهی یافت نشد.")
    
    elif action == 'char':
        await context.bot.send_message(chat_id=chat_id, text="👥 در حال دریافت لیست شخصیت‌ها...")
        data = jikan_api_request(f"anime/{anime_id_str}/characters")
        if data and data.get('data'):
            for i, item in enumerate(data['data'][:7]):
                char = item['character']
                img_url = char.get('images', {}).get('jpg', {}).get('image_url')
                caption = f"<b>{char['name']}</b>\n<i>{item['role']}</i>"
                if img_url:
                    try:
                        await context.bot.send_photo(chat_id=chat_id, photo=img_url, caption=caption, parse_mode=constants.ParseMode.HTML)
                    except (BadRequest, TimedOut):
                        await context.bot.send_message(chat_id=chat_id, text=caption + " (ارسال عکس ناموفق بود)", parse_mode=constants.ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=chat_id, text="شخصیتی یافت نشد.")

async def inline_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پردازش جستجوی inline."""
    query = update.inline_query.query.lower()
    if not query or len(query) < 3:
        await update.inline_query.answer([], cache_time=10)
        return
    
    results = []
    found_ids = set()
    
    for item in search_index:
        if query in item['search_string']:
            if item['mal_id'] in found_ids:
                continue

            description_text = f"امتیاز: {item['score']} | نوع: {item['type']}"
            
            results.append(
                InlineQueryResultArticle(
                    id=item['mal_id'],
                    title=item['title'],
                    thumbnail_url=item['picture'],
                    description=description_text,
                    input_message_content=InputTextMessageContent(f"/anime_{item['mal_id']}")
                )
            )
            found_ids.add(item['mal_id'])
            if len(results) >= 15:
                break
    
    try:
        await update.inline_query.answer(results, cache_time=5)
    except TimedOut:
        logger.warning("TimedOut در جستجوی inline.")

def main() -> None:
    """ربات را اجرا می‌کند."""
    build_search_index()

    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("topanime", top_anime))
    application.add_handler(CommandHandler("seasonal", seasonal_anime))
    application.add_handler(CommandHandler("randomanime", random_anime))
    application.add_handler(InlineQueryHandler(inline_search))
    application.add_handler(MessageHandler(filters.Regex(r'^/anime_\d+$'), get_anime_details_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("ربات با کتابخانه‌های جدید در حال اجراست...")
    application.run_polling()

if __name__ == '__main__':
    main()        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"خطا در اتصال به Jikan API ({url}): {e}")
        return None

def get_latest_episode_from_jikan(anime_id: int) -> int | None:
    """آخرین شماره قسمت پخش شده برای یک انیمه را از Jikan API دریافت می‌کند."""
    page = 1
    latest_episode_num = 0
    logger.info(f"[EPISODE_FETCH] شروع جستجو برای آخرین قسمت ID: {anime_id}")
    try:
        while True:
            data = jikan_api_request(f"anime/{anime_id}/episodes?page={page}")
            if not data or not data.get('data'):
                break
            # شماره قسمت در Jikan v4 در فیلد mal_id قرار دارد.
            max_in_page = max(ep.get('mal_id', 0) for ep in data['data'])
            if max_in_page > latest_episode_num:
                latest_episode_num = max_in_page
            if not data.get('pagination', {}).get('has_next_page', False):
                break
            page += 1
        logger.info(f"[EPISODE_FETCH] جستجو تمام شد. نتیجه نهایی: {latest_episode_num}")
        return latest_episode_num if latest_episode_num > 0 else None
    except Exception as e:
        logger.error(f"[EPISODE_FETCH] خطا در پردازش قسمت‌ها برای ID {anime_id}: {e}")
        return None

def translate_text(text: str):
    """متن را با استفاده از deep-translator به فارسی ترجمه می‌کند."""
    if not text: return "خلاصه داستان موجود نیست."
    try:
        # استفاده از deep-translator
        return GoogleTranslator(source='auto', target='fa').translate(text)
    except Exception as e:
        logger.error(f"خطا در ترجمه متن: {e}")
        return f"(ترجمه با خطا مواجه شد)\n\n{text}"

async def send_full_anime_details(chat_id: int, anime_id: int, context: ContextTypes.DEFAULT_TYPE, initial_message=None):
    """اطلاعات کامل یک انیمه را دریافت و در چت ارسال می‌کند."""
    if initial_message:
        processing_message = await initial_message.edit_text("در حال دریافت جدیدترین اطلاعات...")
    else:
        processing_message = await context.bot.send_message(chat_id=chat_id, text="در حال دریافت جدیدترین اطلاعات...")
    
    full_data = jikan_api_request(f"anime/{anime_id}/full")
    if not full_data or 'data' not in full_data:
        await processing_message.edit_text("خطا: دریافت اطلاعات از API ممکن نبود.")
        return
    
    jikan_details = full_data['data']
    
    title_en = jikan_details.get('title_english') or jikan_details.get('title')
    title_jp = jikan_details.get('title_japanese', '')
    title_display = f"✨ <b>{title_en}</b> ✨\n<i>{title_jp}</i>"
    
    studios = jikan_details.get('studios', [])
    studio_names = ', '.join([s['name'] for s in studios]) or "نامشخص"
    
    aired_string = jikan_details.get('aired', {}).get('string', "نامشخص")
    synopsis_en = jikan_details.get('synopsis', 'خلاصه داستان موجود نیست.')
    score_val = jikan_details.get('score', 0)
    score_fa = f"{score_val:.2f} از ۱۰" if score_val else "نامشخص"
    status_en = jikan_details.get('status', 'Not yet aired')
    status_fa = TRANSLATIONS['status'].get(status_en, status_en)
    num_episodes = jikan_details.get('episodes')
    num_episodes_fa = num_episodes if num_episodes else "نامشخص"
    
    all_genres_data = jikan_details.get('genres', []) + jikan_details.get('themes', []) + jikan_details.get('demographics', [])
    translated_genres = [TRANSLATIONS['genres'].get(g['name'].lower(), g['name']) for g in all_genres_data]
    genres_fa = ' | '.join(translated_genres) or "نامشخص"

    message_parts = [
        title_display + "\n", f"📊 <b>امتیاز:</b> {score_fa}", f"📈 <b>وضعیت:</b> {status_fa}",
        f"🏢 <b>استودیو:</b> {studio_names}", f"🗓️ <b>تاریخ پخش:</b> {aired_string}",
    ]

    if status_en == "Currently Airing":
        latest_episode = get_latest_episode_from_jikan(anime_id)
        if latest_episode:
            message_parts.append(f"🔥 <b>آخرین قسمت پخش شده:</b> {latest_episode}")

    message_parts.extend([
        f"🎬 <b>قسمت‌ها:</b> {num_episodes_fa}", f"📺 <b>نوع:</b> {jikan_details.get('type', 'نامشخص')}\n",
        f"<b>ژانرها:</b>\n{genres_fa}\n", f"📝 <b>خلاصه داستان:</b>\n{translate_text(synopsis_en)}"
    ])
    
    message_text = "\n".join(message_parts)
    picture_url = jikan_details.get('images', {}).get('jpg', {}).get('large_image_url')
    
    await processing_message.delete()

    if picture_url:
        try: await context.bot.send_photo(chat_id=chat_id, photo=picture_url)
        except Exception: pass
    
    await context.bot.send_message(chat_id=chat_id, text=message_text, parse_mode=constants.ParseMode.HTML)
    
    keyboard = [[
        InlineKeyboardButton("🤝 انیمه‌های مشابه", callback_data=f"rec_{anime_id}"),
        InlineKeyboardButton("👥 شخصیت‌ها", callback_data=f"char_{anime_id}")
    ]]
    if jikan_details.get('trailer', {}).get('youtube_id'):
        keyboard.append([InlineKeyboardButton("🎬 نمایش تریلر", url=jikan_details['trailer']['url'])])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text="گزینه‌های بیشتر:", reply_markup=reply_markup)

# --- دستورات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال پیام خوش‌آمدگویی."""
    user_name = update.effective_user.first_name
    welcome_text = (
        f"سلام {user_name}! به ربات دستیار انیمه خوش آمدی. 👋\n\n"
        "من اینجا هستم تا به تو در دنیای بی‌کران انیمه‌ها کمک کنم. تو می‌توانی:\n\n"
        "🔍 **انیمه‌ها را جستجو کنی:** با استفاده از جستجوی هوشمند، هر انیمه‌ای را فوراً پیدا کن.\n"
        "🏆 **بهترین‌ها را بشناسی:** لیست برترین انیمه‌های تاریخ را مشاهده کن.\n"
        "☀️ **به‌روز بمانی:** انیمه‌های جدید هر فصل را دنبال کن.\n\n"
        "برای دیدن لیست کامل دستورات، کافیه دستور /help را ارسال کنی."
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال پیام راهنما."""
    bot_username = (await context.bot.get_me()).username
    help_text = (
        "<b>راهنمای کامل دستورات ربات:</b>\n\n"
        f"🔹 `@{bot_username} نام انیمه`\n"
        "<b>(روش اصلی)</b> برای جستجوی هوشمند و زنده هر انیمه‌ای در هر چتی.\n\n"
        "🔹 /topanime\n"
        "نمایش لیست ۱۰ انیمه برتر تاریخ از نظر امتیاز.\n\n"
        "🔹 /seasonal\n"
        "نمایش انیمه‌های محبوب در حال پخش در فصل فعلی.\n\n"
        "🔹 /randomanime\n"
        "دریافت پیشنهاد یک انیمه کاملاً تصادفی برای تماشا."
    )
    await update.message.reply_text(help_text, parse_mode=constants.ParseMode.HTML)

async def top_anime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال لیست ۱۰ انیمه برتر."""
    message = await update.message.reply_text("🔝 در حال دریافت ۱۰ انیمه برتر تاریخ...")
    data = jikan_api_request("top/anime?limit=10")
    if data and data.get('data'):
        response_text = "<b>🏆 ۱۰ انیمه برتر تاریخ:</b>\n\n"
        for i, anime in enumerate(data['data']):
            response_text += f"{i+1}. {anime.get('title_english') or anime.get('title')} - امتیاز: {anime.get('score', 0):.2f}\n/anime_{anime['mal_id']}\n\n"
        await message.edit_text(response_text, parse_mode=constants.ParseMode.HTML)
    else:
        await message.edit_text("خطا در دریافت اطلاعات.")

async def seasonal_anime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال لیست انیمه‌های فصلی."""
    message = await update.message.reply_text("🏖️ در حال دریافت انیمه‌های فصل جدید...")
    data = jikan_api_request("seasons/now?limit=15")
    if data and data.get('data'):
        response_text = "<b>☀️ انیمه‌های محبوب این فصل:</b>\n\n"
        for i, anime in enumerate(data['data']):
            response_text += f"{i+1}. {anime.get('title_english') or anime.get('title')}\n/anime_{anime['mal_id']}\n\n"
        await message.edit_text(response_text, parse_mode=constants.ParseMode.HTML)
    else:
        await message.edit_text("خطا در دریافت اطلاعات.")

async def random_anime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال یک انیمه تصادفی."""
    message = await update.message.reply_text("🎲 در حال انتخاب یک انیمه تصادفی...")
    data = jikan_api_request("random/anime")
    if data and data.get('data'):
        await send_full_anime_details(update.message.chat_id, data['data']['mal_id'], context, initial_message=message)
    else:
        await message.edit_text("خطا در دریافت اطلاعات.")

async def get_anime_details_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پردازش دستور /anime_ID برای نمایش اطلاعات."""
    anime_id = int(update.message.text.split('_')[1])
    await update.message.delete()
    await send_full_anime_details(update.message.chat_id, anime_id, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پردازش دکمه‌های شیشه‌ای."""
    query = update.callback_query
    await query.answer()
    action, anime_id_str = query.data.split('_', 1)
    chat_id = query.message.chat_id

    if action == 'rec':
        await context.bot.send_message(chat_id=chat_id, text="🔍 در حال یافتن انیمه‌های مشابه...")
        data = jikan_api_request(f"anime/{anime_id_str}/recommendations")
        if data and data.get('data'):
            message = "<b>🤝 انیمه‌های پیشنهادی مشابه:</b>\n\n"
            for i, rec in enumerate(data['data'][:5]):
                entry = rec['entry']
                message += f"{i+1}. {entry.get('title')}\n/anime_{entry['mal_id']}\n\n"
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=constants.ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=chat_id, text="انیمه مشابهی یافت نشد.")
    
    elif action == 'char':
        await context.bot.send_message(chat_id=chat_id, text="👥 در حال دریافت لیست شخصیت‌ها...")
        data = jikan_api_request(f"anime/{anime_id_str}/characters")
        if data and data.get('data'):
            for i, item in enumerate(data['data'][:7]):
                char = item['character']
                img_url = char.get('images', {}).get('jpg', {}).get('image_url')
                caption = f"<b>{char['name']}</b>\n<i>{item['role']}</i>"
                if img_url:
                    try:
                        await context.bot.send_photo(chat_id=chat_id, photo=img_url, caption=caption, parse_mode=constants.ParseMode.HTML)
                    except (BadRequest, TimedOut):
                        await context.bot.send_message(chat_id=chat_id, text=caption + " (ارسال عکس ناموفق بود)", parse_mode=constants.ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=chat_id, text="شخصیتی یافت نشد.")

async def inline_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پردازش جستجوی inline."""
    query = update.inline_query.query.lower()
    if not query or len(query) < 3:
        await update.inline_query.answer([], cache_time=10)
        return
    
    results = []
    found_ids = set()
    
    for item in search_index:
        if query in item['search_string']:
            if item['mal_id'] in found_ids:
                continue

            description_text = f"امتیاز: {item['score']} | نوع: {item['type']}"
            
            results.append(
                InlineQueryResultArticle(
                    id=item['mal_id'],
                    title=item['title'],
                    thumbnail_url=item['picture'], # استفاده از thumbnail_url به جای thumb_url
                    description=description_text,
                    input_message_content=InputTextMessageContent(f"/anime_{item['mal_id']}")
                )
            )
            found_ids.add(item['mal_id'])
            if len(results) >= 15:
                break
    
    try:
        await update.inline_query.answer(results, cache_time=5)
    except TimedOut:
        logger.warning("TimedOut در جستجوی inline.")

def main() -> None:
    """ربات را اجرا می‌کند."""
    build_search_index()

    # ساخت اپلیکیشن با استفاده از توکن
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ثبت دستورات (Handlers)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("topanime", top_anime))
    application.add_handler(CommandHandler("seasonal", seasonal_anime))
    application.add_handler(CommandHandler("randomanime", random_anime))
    application.add_handler(InlineQueryHandler(inline_search))
    application.add_handler(MessageHandler(filters.Regex(r'^/anime_\d+$'), get_anime_details_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    # شروع به کار ربات
    logger.info("ربات با کتابخانه‌های جدید در حال اجراست...")
    application.run_polling()

if __name__ == '__main__':
    main()        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"خطا در اتصال به Jikan API ({url}): {e}")
        return None

def get_latest_episode_from_jikan(anime_id: int) -> int | None:
    page = 1
    latest_episode_num = 0
    logger.info(f"[EPISODE_FETCH] شروع جستجو برای آخرین قسمت ID: {anime_id}")
    try:
        while True:
            data = jikan_api_request(f"anime/{anime_id}/episodes?page={page}")
            if not data or not data.get('data'):
                break
            max_in_page = max(ep.get('mal_id', 0) for ep in data['data'])
            if max_in_page > latest_episode_num:
                latest_episode_num = max_in_page
            if not data.get('pagination', {}).get('has_next_page', False):
                break
            page += 1
        logger.info(f"[EPISODE_FETCH] جستجو تمام شد. نتیجه نهایی: {latest_episode_num}")
        return latest_episode_num if latest_episode_num > 0 else None
    except Exception as e:
        logger.error(f"[EPISODE_FETCH] خطا در پردازش قسمت‌ها برای ID {anime_id}: {e}")
        return None

def translate_text(text: str):
    if not text: return "خلاصه داستان موجود نیست."
    try: return Translator().translate(text, dest='fa').text
    except Exception: return f"(ترجمه با خطا مواجه شد)\n\n{text}"

def send_full_anime_details(chat_id: int, anime_id: int, context: CallbackContext, initial_message=None):
    if initial_message:
        processing_message = initial_message
        processing_message.edit_text("در حال دریافت جدیدترین اطلاعات...")
    else:
        processing_message = context.bot.send_message(chat_id=chat_id, text="در حال دریافت جدیدترین اطلاعات...")
    
    full_data = jikan_api_request(f"anime/{anime_id}/full")
    if not full_data or 'data' not in full_data:
        processing_message.edit_text("خطا: دریافت اطلاعات از API ممکن نبود.")
        return
    
    jikan_details = full_data['data']
    
    title_en = jikan_details.get('title_english') or jikan_details.get('title')
    title_jp = jikan_details.get('title_japanese', '')
    title_display = f"✨ <b>{title_en}</b> ✨\n<i>{title_jp}</i>"
    
    studios = jikan_details.get('studios', [])
    studio_names = ', '.join([s['name'] for s in studios]) or "نامشخص"
    
    aired_string = jikan_details.get('aired', {}).get('string', "نامشخص")
    synopsis_en = jikan_details.get('synopsis', 'خلاصه داستان موجود نیست.')
    score_val = jikan_details.get('score', 0)
    score_fa = f"{score_val:.2f} از ۱۰" if score_val else "نامشخص"
    status_en = jikan_details.get('status', 'Not yet aired')
    status_fa = TRANSLATIONS['status'].get(status_en, status_en)
    num_episodes = jikan_details.get('episodes')
    num_episodes_fa = num_episodes if num_episodes else "نامشخص"
    
    all_genres_data = jikan_details.get('genres', []) + jikan_details.get('themes', []) + jikan_details.get('demographics', [])
    translated_genres = [TRANSLATIONS['genres'].get(g['name'].lower(), g['name']) for g in all_genres_data]
    genres_fa = ' | '.join(translated_genres) or "نامشخص"

    message_parts = [
        title_display + "\n", f"📊 <b>امتیاز:</b> {score_fa}", f"📈 <b>وضعیت:</b> {status_fa}",
        f"🏢 <b>استودیو:</b> {studio_names}", f"🗓️ <b>تاریخ پخش:</b> {aired_string}",
    ]

    if status_en == "Currently Airing":
        latest_episode = get_latest_episode_from_jikan(anime_id)
        if latest_episode:
            message_parts.append(f"🔥 <b>آخرین قسمت پخش شده:</b> {latest_episode}")

    message_parts.extend([
        f"🎬 <b>قسمت‌ها:</b> {num_episodes_fa}", f"📺 <b>نوع:</b> {jikan_details.get('type', 'نامشخص')}\n",
        f"<b>ژانرها:</b>\n{genres_fa}\n", f"📝 <b>خلاصه داستان:</b>\n{translate_text(synopsis_en)}"
    ])
    
    message_text = "\n".join(message_parts)
    picture_url = jikan_details.get('images', {}).get('jpg', {}).get('large_image_url')
    
    processing_message.delete()

    if picture_url:
        try: context.bot.send_photo(chat_id=chat_id, photo=picture_url)
        except Exception: pass
    
    context.bot.send_message(chat_id=chat_id, text=message_text, parse_mode=ParseMode.HTML)
    
    keyboard = [[
        InlineKeyboardButton("🤝 انیمه‌های مشابه", callback_data=f"rec_{anime_id}"),
        InlineKeyboardButton("👥 شخصیت‌ها", callback_data=f"char_{anime_id}")
    ]]
    if jikan_details.get('trailer', {}).get('youtube_id'):
        keyboard.append([InlineKeyboardButton("🎬 نمایش تریلر", url=jikan_details['trailer']['url'])])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=chat_id, text="گزینه‌های بیشتر:", reply_markup=reply_markup)

# --- دستورات ---
def start(update: Update, context: CallbackContext) -> None:
    user_name = update.effective_user.first_name
    welcome_text = (
        f"سلام {user_name}! به ربات دستیار انیمه خوش آمدی. 👋\n\n"
        "من اینجا هستم تا به تو در دنیای بی‌کران انیمه‌ها کمک کنم. تو می‌توانی:\n\n"
        "🔍 **انیمه‌ها را جستجو کنی:** با استفاده از جستجوی هوشمند، هر انیمه‌ای را فوراً پیدا کن.\n"
        "🏆 **بهترین‌ها را بشناسی:** لیست برترین انیمه‌های تاریخ را مشاهده کن.\n"
        "☀️ **به‌روز بمانی:** انیمه‌های جدید هر فصل را دنبال کن.\n\n"
        "برای دیدن لیست کامل دستورات، کافیه دستور /help را ارسال کنی."
    )
    update.message.reply_text(welcome_text)

def help_command(update: Update, context: CallbackContext) -> None:
    bot_username = context.bot.username
    help_text = (
        "<b>راهنمای کامل دستورات ربات:</b>\n\n"
        f"🔹 `@{bot_username} نام انیمه`\n"
        "<b>(روش اصلی)</b> برای جستجوی هوشمند و زنده هر انیمه‌ای در هر چتی.\n\n"
        "🔹 /topanime\n"
        "نمایش لیست ۱۰ انیمه برتر تاریخ از نظر امتیاز.\n\n"
        "🔹 /seasonal\n"
        "نمایش انیمه‌های محبوب در حال پخش در فصل فعلی.\n\n"
        "🔹 /randomanime\n"
        "دریافت پیشنهاد یک انیمه کاملاً تصادفی برای تماشا."
    )
    update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

def top_anime(update: Update, context: CallbackContext) -> None:
    message = update.message.reply_text("🔝 در حال دریافت ۱۰ انیمه برتر تاریخ...")
    data = jikan_api_request("top/anime?limit=10")
    if data and data.get('data'):
        response_text = "<b>🏆 ۱۰ انیمه برتر تاریخ:</b>\n\n"
        for i, anime in enumerate(data['data']):
            response_text += f"{i+1}. {anime.get('title_english') or anime.get('title')} - امتیاز: {anime.get('score', 0):.2f}\n/anime_{anime['mal_id']}\n\n"
        message.edit_text(response_text, parse_mode=ParseMode.HTML)
    else:
        message.edit_text("خطا در دریافت اطلاعات.")

def seasonal_anime(update: Update, context: CallbackContext) -> None:
    message = update.message.reply_text("🏖️ در حال دریافت انیمه‌های فصل جدید...")
    data = jikan_api_request("seasons/now?limit=15")
    if data and data.get('data'):
        response_text = "<b>☀️ انیمه‌های محبوب این فصل:</b>\n\n"
        for i, anime in enumerate(data['data']):
            response_text += f"{i+1}. {anime.get('title_english') or anime.get('title')}\n/anime_{anime['mal_id']}\n\n"
        message.edit_text(response_text, parse_mode=ParseMode.HTML)
    else:
        message.edit_text("خطا در دریافت اطلاعات.")

def random_anime(update: Update, context: CallbackContext) -> None:
    message = update.message.reply_text("🎲 در حال انتخاب یک انیمه تصادفی...")
    data = jikan_api_request("random/anime")
    if data and data.get('data'):
        send_full_anime_details(update.message.chat_id, data['data']['mal_id'], context, initial_message=message)
    else:
        message.edit_text("خطا در دریافت اطلاعات.")

def get_anime_details_command(update: Update, context: CallbackContext) -> None:
    anime_id = int(update.message.text.split('_')[1])
    update.message.delete()
    send_full_anime_details(update.message.chat_id, anime_id, context)

def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    action, anime_id_str = query.data.split('_', 1)
    chat_id = query.message.chat_id

    if action == 'rec':
        context.bot.send_message(chat_id=chat_id, text="🔍 در حال یافتن انیمه‌های مشابه...")
        data = jikan_api_request(f"anime/{anime_id_str}/recommendations")
        if data and data.get('data'):
            message = "<b>🤝 انیمه‌های پیشنهادی مشابه:</b>\n\n"
            for i, rec in enumerate(data['data'][:5]):
                entry = rec['entry']
                message += f"{i+1}. {entry.get('title')}\n/anime_{entry['mal_id']}\n\n"
            context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
        else:
            context.bot.send_message(chat_id=chat_id, text="انیمه مشابهی یافت نشد.")
    
    elif action == 'char':
        context.bot.send_message(chat_id=chat_id, text="👥 در حال دریافت لیست شخصیت‌ها...")
        data = jikan_api_request(f"anime/{anime_id_str}/characters")
        if data and data.get('data'):
            for i, item in enumerate(data['data'][:7]):
                char = item['character']
                img_url = char.get('images', {}).get('jpg', {}).get('image_url')
                caption = f"<b>{char['name']}</b>\n<i>{item['role']}</i>"
                if img_url:
                    try:
                        context.bot.send_photo(chat_id=chat_id, photo=img_url, caption=caption, parse_mode=ParseMode.HTML)
                    except (BadRequest, TimedOut):
                        context.bot.send_message(chat_id=chat_id, text=caption + " (عکس ناموفق بود)", parse_mode=ParseMode.HTML)
        else:
            context.bot.send_message(chat_id=chat_id, text="شخصیتی یافت نشد.")

def inline_search(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query.lower()
    if not query or len(query) < 3:
        update.inline_query.answer([], cache_time=10)
        return
    
    results = []
    found_ids = set()
    
    for item in search_index:
        if query in item['search_string']:
            if item['mal_id'] in found_ids:
                continue

            description_text = f"امتیاز: {item['score']} | نوع: {item['type']}"
            
            results.append(
                InlineQueryResultArticle(
                    id=item['mal_id'],
                    title=item['title'],
                    thumb_url=item['picture'],
                    description=description_text,
                    input_message_content=InputTextMessageContent(f"/anime_{item['mal_id']}")
                )
            )
            found_ids.add(item['mal_id'])
            if len(results) >= 15:
                break
    
    try:
        update.inline_query.answer(results, cache_time=5)
    except TimedOut:
        logger.warning("TimedOut در جستجوی inline.")

def main() -> None:
    build_search_index()

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("topanime", top_anime))
    dp.add_handler(CommandHandler("seasonal", seasonal_anime))
    dp.add_handler(CommandHandler("randomanime", random_anime))
    dp.add_handler(InlineQueryHandler(inline_search))
    dp.add_handler(MessageHandler(Filters.regex(r'^/anime_\d+$'), get_anime_details_command))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    logger.info("ربات بی‌نقص و نهایی اجرا شد!")
    updater.idle()

if __name__ == '__main__':
    main()
