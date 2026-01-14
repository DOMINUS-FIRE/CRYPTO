import asyncio
import json
import random
import logging
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# === КОНФИГУРАЦИЯ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ===
# Render.com автоматически устанавливает эти переменные
API_TOKEN = os.environ.get("API_TOKEN", "8491120802:AAHTQOxZhE41tDCrDg0yeOEBmrQA7PBy4Ms")
TARGET_CHAT_ID = os.environ.get("TARGET_CHAT_ID", "@crypto_rul_FAI")
SUBSCRIBERS_FILE = "subscribers.json"

# === ЛОГГИРОВАНИЕ ДЛЯ RENDER ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Проверяем обязательные переменные
if not API_TOKEN or API_TOKEN == "your_bot_token_here":
    logger.error("❌ API_TOKEN не установлен!")
    logger.error("Установите переменную окружения API_TOKEN на Render.com")
    exit(1)

logger.info(f"🚀 Бот запускается на Render.com")
logger.info(f"🔑 Токен: {'установлен' if API_TOKEN else 'не установлен'}")
logger.info(f"📢 Канал: {TARGET_CHAT_ID}")

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# === ЗАГРУЗКА СООБЩЕНИЙ ===
def load_messages():
    try:
        with open('messages.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data['messages']
    except FileNotFoundError:
        logger.error("Файл messages.json не найден!")
        logger.info("Создаю пустой файл сообщений...")
        # Создаем базовый файл если его нет
        base_messages = {
            "messages": [
                {
                    "id": 1,
                    "text": "🚀 <b>Бот запущен на Render.com!</b>\n\n✅ Система работает корректно\n⏰ Рассылка каждый час в 00 минут\n📍 Канал: @crypto_rul_FAI",
                    "crypto": "BITCOIN",
                    "price": 42000
                }
            ]
        }
        with open('messages.json', 'w', encoding='utf-8') as f:
            json.dump(base_messages, f, ensure_ascii=False, indent=2)
        return base_messages['messages']
    except Exception as e:
        logger.error(f"Ошибка загрузки сообщений: {e}")
        return []

messages_data = load_messages()
logger.info(f"Загружено {len(messages_data)} сообщений")

# === УПРАВЛЕНИЕ ПОДПИСЧИКАМИ ===
def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('subscribers', []))
    except FileNotFoundError:
        logger.info("Файл subscribers.json не найден, создаю новый...")
        with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'subscribers': []}, f)
        return set()
    except Exception as e:
        logger.error(f"Ошибка загрузки подписчиков: {e}")
        return set()

def save_subscribers(subscribers):
    try:
        with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'subscribers': list(subscribers)}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения подписчиков: {e}")

subscribers = load_subscribers()
logger.info(f"Загружено {len(subscribers)} подписчиков")

# === ОСТАЛЬНОЙ КОД ОСТАЕТСЯ БЕЗ ИЗМЕНЕНИЙ ===
# [Вставьте сюда весь остальной код из вашего crypto_bot.py, начиная с user_last_messages = {} и до конца]
# Просто скопируйте весь код после этой строки из вашего текущего crypto_bot.py

# ... [весь ваш существующий код команд и функций] ...

# === ХРАНЕНИЕ ID СООБЩЕНИЙ ДЛЯ ОЧИСТКИ ===
user_last_messages = {}

# === ПРИВЕТСТВЕННОЕ СООБЩЕНИЕ ===
WELCOME_MESSAGE = """📌 <b>🚀 ПРИВЕТСТВИЕ ОТ КРИПТО-БОТА №1!</b>

💰 <b>Мы - лидеры в анализе крипторынка!</b>

⏰ <b>Расписание рассылки:</b>
• Каждый час в 00 минут
• Пример: 22:00, 23:00, 00:00 и т.д.
• 📍 В канал: <b>@crypto_rul_FAI</b>
• 📨 В ЛС: только для подписчиков

🔔 <b>Команды:</b>
/start - Это сообщение
/subscribe - Подписаться на ЛС 🔔
/unsubscribe - Отписаться от ЛС 🔕
/status - Статус бота
/schedule - Расписание рассылки

<code>────────────────────</code>
<i>📌 Это сообщение закреплено</i>
<i>Сигналы идут каждый час точно по времени!</i>"""

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

# === КОМАНДЫ БОТА ===
@dp.message(Command("start"))
async def cmd_start(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    await cleanup_messages(chat_id)
    
    is_subscribed = user_id in subscribers
    welcome = WELCOME_MESSAGE.replace("ПРИВЕТСТВИЕ ОТ", f"Привет, {user_name}!")
    
    sent_message = await message.answer(welcome)
    add_to_history(chat_id, sent_message.message_id)
    
    logger.info(f"Приветствие для {user_name} ({user_id})")

@dp.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
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
    
    sent_message = await message.answer(response)
    add_to_history(chat_id, sent_message.message_id)

@dp.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    await cleanup_messages(chat_id)
    
    if user_id in subscribers:
        subscribers.discard(user_id)
        save_subscribers(subscribers)
        response = f"🔕 {user_name}, вы отписались от рассылки в ЛС."
        logger.info(f"Отписался: {user_name} ({user_id})")
    else:
        response = "ℹ️ Вы не подписаны на рассылку."
    
    sent_message = await message.answer(response)
    add_to_history(chat_id, sent_message.message_id)

@dp.message(Command("status"))
async def cmd_status(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    await cleanup_messages(chat_id)
    
    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    time_left = next_hour - now
    
    status_text = f"""📊 <b>СТАТУС БОТА</b>

🕐 Сейчас: {now.strftime('%H:%M:%S')}
⏰ Следующая рассылка: через {time_left.seconds // 60} мин
📅 Ближайшее время: {next_hour.strftime('%H:%M')}

📨 Сообщений в базе: {len(messages_data)}
👥 Подписчиков: {len(subscribers)}
🔔 Ваша подписка: {'✅ АКТИВНА' if user_id in subscribers else '❌ НЕ АКТИВНА'}

📍 Канал: @crypto_rul_FAI
📢 Рассылка: каждый час в 00 минут"""
    
    sent_message = await message.answer(status_text)
    add_to_history(chat_id, sent_message.message_id)

@dp.message(Command("schedule"))
async def cmd_schedule(message: Message):
    chat_id = message.chat.id
    
    await cleanup_messages(chat_id)
    
    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    time_left = next_hour - now
    
    # Рассчитываем ближайшие 5 часов рассылки
    schedule_times = []
    current = now.replace(minute=0, second=0, microsecond=0)
    
    for i in range(1, 6):
        next_time = current + timedelta(hours=i)
        schedule_times.append(next_time.strftime('%H:%M'))
    
    schedule_text = f"""⏰ <b>РАСПИСАНИЕ РАССЫЛКИ</b>

<code>────────────────────</code>
<b>Следующая отправка:</b>
🕐 {next_hour.strftime('%H:%M')}
⏳ Через {time_left.seconds // 60} минут {time_left.seconds % 60} секунд

<code>────────────────────</code>
<b>Ближайшие 5 рассылок:</b>
"""
    
    for i, time_str in enumerate(schedule_times, 1):
        schedule_text += f"• {time_str}\n"
    
    schedule_text += f"""
<code>────────────────────</code>
<b>Статистика:</b>
• Сообщений готово: {len(messages_data)}
• Подписчиков: {len(subscribers)}
• Время сервера: {datetime.now().strftime('%H:%M:%S')}"""
    
    sent_message = await message.answer(schedule_text)
    add_to_history(chat_id, sent_message.message_id)

# === ОТПРАВКА СООБЩЕНИЙ ПОДПИСЧИКАМ ===
async def send_to_subscribers(message_text: str):
    sent_count = 0
    failed_count = 0
    
    for user_id in list(subscribers):
        try:
            await bot.send_message(
                chat_id=user_id,
                text=message_text
            )
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"Ошибка подписчику {user_id}: {e}")
            failed_count += 1
            if "bot was blocked" in str(e).lower():
                subscribers.discard(user_id)
    
    if sent_count > 0:
        logger.info(f"Отправлено {sent_count} подписчикам")
    if failed_count > 0:
        logger.warning(f"Не удалось {failed_count} подписчикам")
    
    save_subscribers(subscribers)

# === РАССЫЛКА ПО РАСПИСАНИЮ ===
async def scheduled_broadcast():
    """Рассылка каждый час в 00 минут"""
    logger.info("⏰ Запущен планировщик рассылки")
    
    # Ждем полную инициализацию
    await asyncio.sleep(5)
    
    while True:
        try:
            now = datetime.now()
            current_minute = now.minute
            current_second = now.second
            
            # Если сейчас 00 минут - отправляем
            if current_minute == 0:
                logger.info(f"🕐 Время {now.strftime('%H:%M:%S')} - отправляю сообщение...")
                await send_hourly_message()
                # Ждем 61 минуту чтобы не отправить дважды
                await asyncio.sleep(3660)
            else:
                # Вычисляем сколько секунд осталось до следующего часа
                minutes_left = 60 - current_minute
                seconds_left = minutes_left * 60 - current_second
                
                # Ждем до следующего часа
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
        
        # Выбираем случайное сообщение
        msg = random.choice(messages_data)
        text = msg['text']
        
        # Форматируем время
        current_time = datetime.now()
        time_str = current_time.strftime('%H:%M')
        
        # Форматируем сообщение
        formatted_message = f"""
🕐 <b>КРИПТО-СИГНАЛ {time_str}</b>
<code>────────────────────</code>

{text}
        """
        
        # 1. Отправляем в канал (ВСЕГДА)
        try:
            await bot.send_message(
                chat_id=TARGET_CHAT_ID,
                text=formatted_message
            )
            logger.info(f"✅ Сообщение #{msg['id']} отправлено в канал {TARGET_CHAT_ID} в {time_str}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки в канал: {e}")
            return False
        
        # 2. Отправляем подписчикам в ЛС (только если есть подписчики)
        if subscribers:
            await send_to_subscribers(formatted_message)
            logger.info(f"✅ Сообщение отправлено {len(subscribers)} подписчикам")
        else:
            logger.info(f"ℹ️ Нет подписчиков для рассылки")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        return False

# === ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ ===
@dp.message()
async def handle_all_messages(message: Message):
    chat_id = message.chat.id
    
    if message.text and not message.text.startswith('/'):
        await cleanup_messages(chat_id)
        
        response = """🤖 <b>Я крипто-бот!</b>

Используйте команды:
/start - Приветствие
/subscribe - Подписаться на ЛС
/status - Статус бота
/schedule - Расписание

📍 Канал: @crypto_rul_FAI
⏰ Рассылка: каждый час в 00 минут"""
        
        sent_message = await message.answer(response)
        add_to_history(chat_id, sent_message.message_id)

# === ОСНОВНАЯ ФУНКЦИЯ ===
async def main():
    """Запуск бота"""
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК КРИПТО-БОТА")
    logger.info("=" * 50)
    
    if not messages_data:
        logger.error("❌ Нет сообщений! Запустите generate_messages.py")
        return
    
    logger.info(f"✅ Сообщений: {len(messages_data)}")
    logger.info(f"✅ Канал: {TARGET_CHAT_ID}")
    logger.info(f"✅ Подписчиков: {len(subscribers)}")
    
    # Запускаем планировщик
    asyncio.create_task(scheduled_broadcast())
    
    logger.info("✅ Бот запущен! Рассылка каждый час в 00 минут")
    logger.info("✅ Проверьте канал: @crypto_rul_FAI")
    logger.info("✅ Подпишитесь командой: /subscribe")
    
    # Запускаем поллинг
    await dp.start_polling(bot)

# === ТОЧКА ВХОДА ===
if __name__ == "__main__":
    asyncio.run(main())