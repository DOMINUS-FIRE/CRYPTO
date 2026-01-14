import asyncio
import json
import random
import logging
import os
import sys
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# === КОНФИГУРАЦИЯ ===
API_TOKEN = os.environ.get("API_TOKEN", "8491120802:AAHTQOxZhE41tDCrDg0yeOEBmrQA7PBy4Ms")
TARGET_CHAT_ID = os.environ.get("TARGET_CHAT_ID", "@crypto_rul_FAI")
SUBSCRIBERS_FILE = "subscribers.json"
PORT = int(os.environ.get("PORT", 10000))  # Render сам назначает порт

# === ЛОГГИРОВАНИЕ ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Проверяем обязательные переменные
if not API_TOKEN:
    logger.error("❌ API_TOKEN не установлен!")
    exit(1)

logger.info("=" * 60)
logger.info("🚀 ЗАПУСК КРИПТО-БОТА НА RENDER.COM")
logger.info(f"🔑 Токен: установлен")
logger.info(f"📢 Канал: {TARGET_CHAT_ID}")
logger.info(f"🌐 Порт для веб-сервера: {PORT}")
logger.info("=" * 60)

# === ИНИЦИАЛИЗАЦИЯ БОТА ===
try:
    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    logger.info("✅ Бот инициализирован")
except Exception as e:
    logger.error(f"❌ Ошибка инициализации бота: {e}")
    exit(1)

# === ЗАГРУЗКА ДАННЫХ ===
def load_messages():
    try:
        with open('messages.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"✅ Загружено {len(data['messages'])} сообщений")
            return data['messages']
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки messages.json: {e}")
        return []

def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            subscribers = set(data.get('subscribers', []))
            logger.info(f"✅ Загружено {len(subscribers)} подписчиков")
            return subscribers
    except Exception:
        logger.info("ℹ️ Файл subscribers.json не найден, создаю новый")
        return set()

def save_subscribers(subscribers):
    try:
        with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'subscribers': list(subscribers)}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения подписчиков: {e}")

# Загружаем данные
messages_data = load_messages()
subscribers = load_subscribers()

# === ХРАНЕНИЕ ID СООБЩЕНИЙ ===
user_last_messages = {}

# === КЛАВИАТУРЫ ===
def get_main_keyboard():
    """Клавиатура главного меню"""
    keyboard = [
        [KeyboardButton(text="📊 Статус бота")],
        [KeyboardButton(text="🔔 Подписаться на ЛС")],
        [KeyboardButton(text="🔕 Отписаться от ЛС")],
        [KeyboardButton(text="⏰ Расписание")],
        [KeyboardButton(text="ℹ️ О боте")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_back_keyboard():
    """Клавиатура с кнопкой Назад"""
    keyboard = [
        [KeyboardButton(text="🔙 Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# === ОЧИСТКА СООБЩЕНИЙ ===
async def cleanup_messages(chat_id: int):
    if chat_id in user_last_messages:
        for msg_id in user_last_messages[chat_id]:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except:
                pass
        user_last_messages[chat_id] = []

def add_to_history(chat_id: int, message_id: int):
    if chat_id not in user_last_messages:
        user_last_messages[chat_id] = []
    user_last_messages[chat_id].append(message_id)
    if len(user_last_messages[chat_id]) > 5:
        user_last_messages[chat_id] = user_last_messages[chat_id][-5:]

# === ГЛАВНОЕ МЕНЮ ===
@dp.message(Command("start"))
@dp.message(F.text == "🔙 Назад в меню")
async def show_main_menu(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    await cleanup_messages(chat_id)
    
    welcome_text = f"""🤖 <b>Привет, {user_name}!</b>

<b>🚀 КРИПТО-БОТ №1</b> - лидер в анализе крипторынка!

<b>⏰ Рассылка сигналов:</b>
• Каждый час в 00 минут
• 📍 В канал: <b>@crypto_rul_FAI</b>
• 📨 В ЛС: только для подписчиков

<b>📌 Выберите действие:</b>"""
    
    sent_message = await message.answer(welcome_text, reply_markup=get_main_keyboard())
    add_to_history(chat_id, sent_message.message_id)
    
    logger.info(f"Главное меню для {user_name} ({user_id})")

# === СТАТУС БОТА ===
@dp.message(F.text == "📊 Статус бота")
async def show_status(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    await cleanup_messages(chat_id)
    
    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    time_left = next_hour - now
    
    # Рассчитываем минуты и секунды до следующего сигнала
    total_seconds = time_left.seconds
    minutes_left = total_seconds // 60
    seconds_left = total_seconds % 60
    
    # Проверяем, если до следующего сигнала меньше минуты
    if minutes_left == 0 and seconds_left < 60:
        next_time_text = "СЕЙЧАС"
    else:
        next_time_text = f"через {minutes_left} мин {seconds_left} сек"
    
    status_text = f"""📊 <b>СТАТУС БОТА</b>

⏰ Следующая рассылка: <b>{next_time_text}</b>

📨 Сообщений в базе: <b>{len(messages_data)}</b>
👥 Подписчиков: <b>{len(subscribers)}</b>
🔔 Ваша подписка: <b>{'✅ АКТИВНА' if user_id in subscribers else '❌ НЕ АКТИВНА'}</b>

📍 Канал: @crypto_rul_FAI
📢 Рассылка: каждый час в 00 минут"""
    
    sent_message = await message.answer(status_text, reply_markup=get_back_keyboard())
    add_to_history(chat_id, sent_message.message_id)

# === ПОДПИСКА ===
@dp.message(F.text == "🔔 Подписаться на ЛС")
async def subscribe_user(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    await cleanup_messages(chat_id)
    
    if user_id in subscribers:
        response = """✅ <b>Вы уже подписаны на рассылку в ЛС!</b>

Вы уже получаете крипто-сигналы в личные сообщения.
📅 Следующая рассылка: в 00 минут следующего часа."""
    else:
        subscribers.add(user_id)
        save_subscribers(subscribers)
        response = f"""✅ <b>{user_name}, вы подписались!</b>

🔔 Теперь вы будете получать крипто-сигналы:
• В канал: @crypto_rul_FAI (всегда)
• В ЛС: каждый час в 00 минут

📅 Следующая рассылка: в 00 минут следующего часа!"""
        logger.info(f"Новый подписчик: {user_name} ({user_id})")
    
    sent_message = await message.answer(response, reply_markup=get_back_keyboard())
    add_to_history(chat_id, sent_message.message_id)

# === ОТПИСКА ===
@dp.message(F.text == "🔕 Отписаться от ЛС")
async def unsubscribe_user(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    await cleanup_messages(chat_id)
    
    if user_id in subscribers:
        subscribers.discard(user_id)
        save_subscribers(subscribers)
        response = f"""🔕 <b>{user_name}, вы отписались от рассылки в ЛС.</b>

Вы больше не будете получать крипто-сигналы в личные сообщения.
Сигналы в канале @crypto_rul_FAI продолжают идти каждый час."""
        logger.info(f"Отписался: {user_name} ({user_id})")
    else:
        response = """ℹ️ <b>Вы не подписаны на рассылку.</b>

Чтобы подписаться, нажмите кнопку "🔔 Подписаться на ЛС"."""
    
    sent_message = await message.answer(response, reply_markup=get_back_keyboard())
    add_to_history(chat_id, sent_message.message_id)

# === РАСПИСАНИЕ ===
@dp.message(F.text == "⏰ Расписание")
async def show_schedule(message: Message):
    chat_id = message.chat.id
    
    await cleanup_messages(chat_id)
    
    now = datetime.now()
    
    # Находим время следующей рассылки (следующий час в 00 минут)
    next_broadcast = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    time_left = next_broadcast - now
    
    # Рассчитываем минуты и секунды до следующего сигнала
    total_seconds = time_left.seconds
    minutes_left = total_seconds // 60
    seconds_left = total_seconds % 60
    
    if minutes_left == 0 and seconds_left < 60:
        next_time_text = "СЕЙЧАС"
    else:
        next_time_text = f"{minutes_left} мин {seconds_left} сек"
    
    # Генерируем расписание следующих 5 рассылок
    schedule_times = []
    current = next_broadcast
    
    for i in range(5):
        time_until = current - now
        total_sec = time_until.seconds
        mins = total_sec // 60
        secs = total_sec % 60
        
        if i == 0:
            schedule_times.append(f"Следующий сигнал: через {mins} мин {secs} сек")
        else:
            schedule_times.append(f"Через {i+1} час: через {mins} мин {secs} сек")
        
        current = current + timedelta(hours=1)
    
    schedule_text = f"""⏰ <b>РАСПИСАНИЕ РАССЫЛКИ</b>

<code>────────────────────</code>
<b>До следующего сигнала:</b>
⏳ {next_time_text}

<code>────────────────────</code>
<b>Ближайшие 5 рассылок:</b>
"""
    
    for i, time_str in enumerate(schedule_times, 1):
        schedule_text += f"• {time_str}\n"
    
    schedule_text += f"""
<code>────────────────────</code>
<b>Статистика:</b>
• Сообщений готово: <b>{len(messages_data)}</b>
• Подписчиков: <b>{len(subscribers)}</b>
• Частота: <b>каждый час в 00 минут</b>"""
    
    sent_message = await message.answer(schedule_text, reply_markup=get_back_keyboard())
    add_to_history(chat_id, sent_message.message_id)

# === О БОТЕ ===
@dp.message(F.text == "ℹ️ О боте")
async def show_about(message: Message):
    chat_id = message.chat.id
    
    await cleanup_messages(chat_id)
    
    about_text = """🤖 <b>О КРИПТО-БОТЕ</b>

<b>🚀 Наша миссия:</b>
Предоставлять качественные крипто-сигналы
каждый час точно по времени!

<b>📊 Что мы делаем:</b>
• Анализируем рынок 24/7
• Ищем лучшие точки входа
• Даем четкие рекомендации
• Отправляем сигналы каждый час

<b>⏰ Расписание:</b>
• Сигналы: каждый час в 00 минут
• Канал: @crypto_rul_FAI
• ЛС: для подписчиков

<b>📌 Как пользоваться:</b>
1. Подпишитесь на канал @crypto_rul_FAI
2. Нажмите "🔔 Подписаться на ЛС"
3. Получайте сигналы каждый час!

<code>────────────────────</code>
⚠️ <i>Торгуйте ответственно. Риски есть всегда!</i>"""
    
    sent_message = await message.answer(about_text, reply_markup=get_back_keyboard())
    add_to_history(chat_id, sent_message.message_id)

# === ОТПРАВКА СООБЩЕНИЙ ПОДПИСЧИКАМ ===
async def send_to_subscribers(message_text: str):
    sent_count = 0
    failed_count = 0
    
    for user_id in list(subscribers):
        try:
            await bot.send_message(chat_id=user_id, text=message_text)
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"Ошибка подписчику {user_id}: {e}")
            failed_count += 1
            if "bot was blocked" in str(e).lower():
                subscribers.discard(user_id)
    
    if sent_count > 0:
        logger.info(f"✅ Отправлено {sent_count} подписчикам")
    if failed_count > 0:
        logger.warning(f"⚠️ Не удалось {failed_count} подписчикам")
    
    save_subscribers(subscribers)

# === РАССЫЛКА ПО РАСПИСАНИЮ ===
async def scheduled_broadcast():
    """Рассылка каждый час в 00 минут"""
    logger.info("⏰ Запущен планировщик рассылки")
    
    await asyncio.sleep(5)  # Ждем инициализацию
    
    first_run = True
    
    while True:
        try:
            now = datetime.now()
            current_minute = now.minute
            current_second = now.second
            
            if current_minute == 0:
                if first_run:
                    logger.info(f"⚠️ Первый запуск в {now.strftime('%H:%M')}, пропускаю отправку")
                    first_run = False
                    seconds_to_wait = (60 - current_second) + 1
                    await asyncio.sleep(seconds_to_wait)
                    continue
                
                logger.info(f"🕐 Время {now.strftime('%H:%M:%S')} - отправляю сообщение...")
                await send_hourly_message()
                await asyncio.sleep(3660)  # Ждем 61 минуту
            else:
                first_run = False
                minutes_left = 60 - current_minute
                seconds_left = minutes_left * 60 - current_second
                logger.info(f"⏳ До следующей рассылки: {minutes_left} мин {seconds_left % 60} сек")
                await asyncio.sleep(seconds_left)
                
        except Exception as e:
            logger.error(f"❌ Ошибка в планировщике: {e}")
            await asyncio.sleep(60)

async def send_hourly_message():
    """Отправка сообщения в канал и подписчикам"""
    try:
        if not messages_data:
            logger.error("❌ Нет сообщений для отправки")
            return False
        
        msg = random.choice(messages_data)
        
        formatted_message = f"""
🚀 <b>КРИПТО-СИГНАЛ</b>
<code>────────────────────</code>

{msg['text']}
        """
        
        # Отправляем в канал
        await bot.send_message(chat_id=TARGET_CHAT_ID, text=formatted_message)
        logger.info(f"✅ Сообщение #{msg['id']} отправлено в канал {TARGET_CHAT_ID}")
        
        # Отправляем подписчикам
        if subscribers:
            await send_to_subscribers(formatted_message)
            logger.info(f"✅ Сообщение отправлено {len(subscribers)} подписчикам")
        else:
            logger.info(f"ℹ️ Нет подписчиков для рассылки")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        return False

# === ПРОСТОЙ ВЕБ-СЕРВЕР НА aiohttp ===
async def start_web_server():
    """Запуск веб-сервера для Render health check"""
    try:
        from aiohttp import web
        
        app = web.Application()
        
        async def handle_root(request):
            return web.Response(text="🤖 Crypto Bot is running!\n\nStatus: OK\nTime: " + 
                               datetime.now().strftime('%H:%M:%S'))
        
        async def handle_health(request):
            return web.json_response({
                "status": "ok",
                "bot": "running",
                "subscribers": len(subscribers),
                "messages": len(messages_data),
                "timestamp": datetime.now().isoformat()
            })
        
        app.router.add_get('/', handle_root)
        app.router.add_get('/health', handle_health)
        app.router.add_get('/healthz', handle_health)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        
        logger.info(f"🌐 Веб-сервер запущен на порту {PORT}")
        logger.info(f"✅ Health check доступен по: /health")
        
        return runner
        
    except ImportError:
        logger.warning("⚠️ aiohttp не установлен, веб-сервер не будет запущен")
        logger.info("ℹ️ Добавьте 'aiohttp' в requirements.txt")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка запуска веб-сервера: {e}")
        return None

# === ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ ===
@dp.message()
async def handle_all_messages(message: Message):
    chat_id = message.chat.id
    
    # Если сообщение не команда и не текст кнопок
    if message.text and not message.text.startswith('/'):
        # Проверяем, не является ли это кнопкой
        buttons_texts = [
            "📊 Статус бота", "🔔 Подписаться на ЛС", "🔕 Отписаться от ЛС",
            "⏰ Расписание", "ℹ️ О боте", "🔙 Назад в меню"
        ]
        
        if message.text not in buttons_texts:
            await cleanup_messages(chat_id)
            
            response = """🤖 <b>Используйте кнопки меню!</b>

Выберите действие из меню ниже:"""
            
            sent_message = await message.answer(response, reply_markup=get_main_keyboard())
            add_to_history(chat_id, sent_message.message_id)

# === ГЛАВНАЯ ФУНКЦИЯ ===
async def main():
    """Основная функция запуска"""
    logger.info("=" * 60)
    logger.info("🚀 ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ...")
    logger.info("=" * 60)
    
    if not messages_data:
        logger.error("❌ Нет сообщений! Запустите generate_messages.py")
        return
    
    # Запускаем веб-сервер
    web_runner = await start_web_server()
    
    # Запускаем планировщик рассылки
    asyncio.create_task(scheduled_broadcast())
    
    logger.info("=" * 60)
    logger.info("✅ СИСТЕМА ЗАПУЩЕНА УСПЕШНО!")
    logger.info(f"📊 Сообщений: {len(messages_data)}")
    logger.info(f"👥 Подписчиков: {len(subscribers)}")
    logger.info(f"📢 Канал: {TARGET_CHAT_ID}")
    logger.info(f"🌐 Веб-сервер: порт {PORT}")
    logger.info("⏰ Рассылка: каждый час в 00 минут")
    logger.info("=" * 60)
    
    # Запускаем поллинг бота
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка поллинга: {e}")
    finally:
        # Очистка при завершении
        if web_runner:
            await web_runner.cleanup()
        logger.info("👋 Бот завершает работу")

# === ТОЧКА ВХОДА ===
if __name__ == "__main__":
    # Обработка сигналов для корректного завершения
    import signal
    
    def signal_handler(signum, frame):
        logger.info(f"📞 Получен сигнал {signum}, завершаем работу...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Запуск
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Завершение по команде пользователя")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")