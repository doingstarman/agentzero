import logging
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database import UserDatabase
from openai_client import OpenAIClient

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

# Инициализация базы данных
try:
    db = UserDatabase()
    logger.info("База данных успешно инициализирована")
except Exception as e:
    logger.error(f"Ошибка при инициализации базы данных: {e}")
    raise

def get_main_menu_keyboard():
    """Создание клавиатуры главного меню"""
    keyboard = [
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data='settings'),
            InlineKeyboardButton("📊 Статистика", callback_data='stats')
        ],
        [
            InlineKeyboardButton("📢 Мои каналы", callback_data='my_channels')
        ],
        [
            InlineKeyboardButton("➕ Добавить новый канал", callback_data='add_channel')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    """Создание клавиатуры с кнопкой назад"""
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='back')]]
    return InlineKeyboardMarkup(keyboard)

def get_ready_keyboard():
    """Создание клавиатуры с кнопкой готово"""
    keyboard = [
        [InlineKeyboardButton("✅ Готово", callback_data='ready')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_channel_settings_keyboard():
    """Создание клавиатуры настроек канала"""
    keyboard = [
        [
            InlineKeyboardButton("🤖 Настройки ассистента", callback_data='assistant_settings'),
            InlineKeyboardButton("⏰ Ограничения", callback_data='restrictions')
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data='back')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_assistant_settings_keyboard():
    """Создание клавиатуры настроек ассистента"""
    keyboard = [
        [
            InlineKeyboardButton("📝 Системный промпт", callback_data='system_prompt'),
            InlineKeyboardButton("🎯 Разрешенные темы", callback_data='allowed_topics')
        ],
        [
            InlineKeyboardButton("🚫 Запрещенные слова", callback_data='forbidden_words'),
            InlineKeyboardButton("🎨 Стиль ответов", callback_data='response_style')
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data='back')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info("Получена команда /start")
        user = update.effective_user
        db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        db.update_user_activity(user.id, command='start')
        
        welcome_text = (
            "👋 Привет! Я бот-агент для управления автоответами в ваших Telegram каналах.\n\n"
            "🔸 Добавляйте каналы\n"
            "🔸 Настраивайте автоответы с помощью ИИ\n"
            "🔸 Следите за статистикой\n\n"
            "Для начала работы необходимо:\n"
            "1. Добавить канал\n"
            "2. Настроить ключ OpenAI\n"
            "3. Настроить параметры ассистента\n\n"
            "Выберите действие в меню ниже:"
        )
        
        await update.message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard())
        logger.info("Команда /start успешно обработана")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start: {e}")
        raise

# Обработчик нажатий на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info("Получено нажатие кнопки")
        query = update.callback_query
        await query.answer()
        
        if query.data == 'ready':
            user_state = db.get_user_state(query.from_user.id)
            if not user_state:
                return
                
            current_state = user_state['state']
            logger.info(f"Текущее состояние пользователя: {current_state}")
            
            if current_state == 'waiting_for_channel':
                # Переходим к запросу никнейма канала
                db.set_user_state(query.from_user.id, 'waiting_for_channel_username')
                await query.message.edit_text(
                    "Отправьте никнейм вашего канала в формате @channelname\n"
                    "Например: @mychannel",
                    reply_markup=get_back_keyboard()
                )
            elif current_state == 'waiting_for_channel_username':
                # Переходим к инструкции по добавлению бота
                channel_username = user_state['data'].get('channel_username')
                if channel_username:
                    await query.message.edit_text(
                        "📝 Инструкция по добавлению бота в канал:\n\n"
                        "1. Откройте настройки вашего канала\n"
                        "2. Перейдите в раздел 'Администраторы'\n"
                        "3. Нажмите 'Добавить администратора'\n"
                        "4. Найдите и выберите этого бота\n"
                        "5. Убедитесь, что у бота есть права на:\n"
                        "   - Просмотр сообщений\n"
                        "   - Отправка сообщений\n"
                        "   - Удаление сообщений\n\n"
                        "После этого нажмите 'Готово'",
                        reply_markup=get_ready_keyboard()
                    )
                    db.set_user_state(query.from_user.id, 'waiting_for_channel_add', user_state['data'])
            elif current_state == 'waiting_for_channel_add':
                # Переходим к настройке ответов на комментарии
                channel_username = user_state['data'].get('channel_username')
                if channel_username:
                    await query.message.edit_text(
                        "Теперь давайте настроим, как бот будет отвечать на комментарии.\n\n"
                        "Опишите, как должен отвечать бот на комментарии.\n"
                        "Например:\n"
                        "- Отвечать кратко и по существу\n"
                        "- Использовать дружелюбный тон\n"
                        "- Отвечать на русском языке\n"
                        "- Не использовать сложные термины\n\n"
                        "Отправьте ваши инструкции:",
                        reply_markup=get_back_keyboard()
                    )
                    db.set_user_state(query.from_user.id, 'waiting_for_system_prompt', user_state['data'])
            elif current_state == 'waiting_for_system_prompt':
                # Завершаем настройку
                channel_username = user_state['data'].get('channel_username')
                system_prompt = user_state['data'].get('system_prompt')
                if channel_username and system_prompt:
                    # Здесь нужно добавить логику сохранения канала и настроек
                    await query.message.edit_text(
                        f"✅ Настройка канала {channel_username} завершена!\n\n"
                        "Теперь бот будет автоматически отвечать на комментарии в вашем канале.\n"
                        "Вы можете изменить настройки в любой момент в разделе 'Мои каналы'.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    db.clear_user_state(query.from_user.id)
            return

        if query.data == 'add_channel':
            db.set_user_state(query.from_user.id, 'waiting_for_channel')
            await query.message.edit_text(
                "📝 Давайте настроим автоответы для вашего канала!\n\n"
                "В процессе настройки мы:\n"
                "1. Добавим бота в ваш канал\n"
                "2. Настроим, как бот будет отвечать на комментарии\n"
                "3. Активируем автоответчик\n\n"
                "Вы готовы начать?",
                reply_markup=get_ready_keyboard()
            )
        elif query.data == 'my_channels':
            channels = db.get_user_channels(query.from_user.id)
            if channels:
                text = "📢 Ваши каналы:\n\n"
                for channel in channels:
                    text += f"• {channel['title']}\n"
                text += "\nВыберите канал для настройки:"
                
                keyboard = []
                for channel in channels:
                    keyboard.append([InlineKeyboardButton(
                        channel['title'],
                        callback_data=f'channel_{channel["id"]}'
                    )])
                keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back')])
                
                await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                db.set_user_state(query.from_user.id, 'select_channel')
            else:
                await query.message.edit_text(
                    "У вас пока нет добавленных каналов.\n"
                    "Нажмите 'Добавить новый канал' для начала.",
                    reply_markup=get_main_menu_keyboard()
                )
                db.clear_user_state(query.from_user.id)
        elif query.data.startswith('channel_'):
            channel_id = query.data.split('_')[1]
            channel = db.users['channels'].get(channel_id)
            if channel:
                await query.message.edit_text(
                    f"Настройки канала {channel['title']}\n\n"
                    "Выберите, что хотите настроить:",
                    reply_markup=get_channel_settings_keyboard()
                )
                db.set_user_state(query.from_user.id, 'channel_settings', {'channel_id': channel_id})
        elif query.data == 'assistant_settings':
            user_state = db.get_user_state(query.from_user.id)
            if user_state and 'channel_id' in user_state['data']:
                channel_id = user_state['data']['channel_id']
                channel = db.users['channels'].get(str(channel_id))
                if channel:
                    settings = channel['settings']['assistant_settings']
                    text = (
                        f"🤖 Настройки ассистента для канала {channel['title']}\n\n"
                        f"Модель: {settings['model']}\n"
                        f"Температура: {settings['temperature']}\n"
                        f"Макс. токенов: {settings['max_tokens']}\n"
                        f"Стиль ответов: {settings['response_style']}\n\n"
                        "Выберите параметр для настройки:"
                    )
                    await query.message.edit_text(text, reply_markup=get_assistant_settings_keyboard())
                    db.set_user_state(query.from_user.id, 'setting_assistant', {'channel_id': channel_id})
        elif query.data in ['settings', 'stats']:
            await query.message.edit_text(
                "Лол, чепушила, нету фичи 😅",
                reply_markup=get_back_keyboard()
            )
        logger.info(f"Кнопка {query.data} успешно обработана")
    except Exception as e:
        logger.error(f"Ошибка при обработке нажатия кнопки: {e}")
        raise

# Обработчик пересланных сообщений (для добавления каналов)
async def handle_forwarded_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info("Получено пересланное сообщение")
        user = update.effective_user
        message = update.message
        
        # Проверяем состояние пользователя
        user_state = db.get_user_state(user.id)
        if not user_state or user_state['state'] != 'waiting_for_channel_add':
            await message.reply_text(
                "❌ Пожалуйста, сначала нажмите кнопку 'Добавить новый канал' в главном меню.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        if message.forward_from_chat and message.forward_from_chat.type in ['channel', 'group']:
            channel = message.forward_from_chat
            channel_username = user_state['data'].get('channel_username')
            if channel_username and channel.username == channel_username:
                if db.add_channel(channel.id, channel.title, user.id, channel_username):
                    await message.reply_text(
                        f"✅ Канал {channel.title} успешно добавлен!\n\n"
                        "Теперь давайте настроим, как бот будет отвечать на комментарии.\n\n"
                        "Опишите, как должен отвечать бот на комментарии.\n"
                        "Например:\n"
                        "- Отвечать кратко и по существу\n"
                        "- Использовать дружелюбный тон\n"
                        "- Отвечать на русском языке\n"
                        "- Не использовать сложные термины\n\n"
                        "Отправьте ваши инструкции:",
                        reply_markup=get_back_keyboard()
                    )
                    db.set_user_state(user.id, 'waiting_for_system_prompt')
                else:
                    await message.reply_text(
                        "❌ Этот канал уже добавлен в систему.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    db.clear_user_state(user.id)
            else:
                await message.reply_text(
                    "❌ Неверный канал. Пожалуйста, перешлите сообщение из канала с указанным никнеймом.",
                    reply_markup=get_back_keyboard()
                )
        else:
            await message.reply_text(
                "❌ Пожалуйста, перешлите сообщение из канала, который хотите добавить.",
                reply_markup=get_back_keyboard()
            )
        logger.info("Пересланное сообщение успешно обработано")
    except Exception as e:
        logger.error(f"Ошибка при обработке пересланного сообщения: {e}")
        raise

# Обработчик текстовых сообщений
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info("Получено текстовое сообщение")
        user = update.effective_user
        message = update.message
        user_state = db.get_user_state(user.id)
        
        if not user_state:
            return
        
        if user_state['state'] == 'waiting_for_channel_username':
            # Проверяем формат никнейма канала
            username = message.text.strip()
            if username.startswith('@'):
                username = username[1:]  # Убираем @ из начала
            if username and not username.startswith('@'):
                # Сохраняем никнейм и переходим к следующему шагу
                user_state['data']['channel_username'] = username
                db.set_user_state(user.id, user_state['state'], user_state['data'])
                await message.reply_text(
                    "📝 Инструкция по добавлению бота в канал:\n\n"
                    "1. Откройте настройки вашего канала\n"
                    "2. Перейдите в раздел 'Администраторы'\n"
                    "3. Нажмите 'Добавить администратора'\n"
                    "4. Найдите и выберите этого бота\n"
                    "5. Убедитесь, что у бота есть права на:\n"
                    "   - Просмотр сообщений\n"
                    "   - Отправка сообщений\n"
                    "   - Удаление сообщений\n\n"
                    "После этого нажмите 'Готово'",
                    reply_markup=get_ready_keyboard()
                )
                db.set_user_state(user.id, 'waiting_for_channel_add')
            else:
                await message.reply_text(
                    "❌ Неверный формат никнейма. Отправьте никнейм в формате @channelname\n"
                    "Например: @mychannel",
                    reply_markup=get_back_keyboard()
                )
        elif user_state['state'] == 'waiting_for_system_prompt':
            # Сохраняем системный промпт
            user_state['data']['system_prompt'] = message.text
            db.set_user_state(user.id, user_state['state'], user_state['data'])
            await message.reply_text(
                "✅ Инструкции для бота сохранены!\n\n"
                "Нажмите 'Готово', чтобы завершить настройку.",
                reply_markup=get_ready_keyboard()
            )
        logger.info("Текстовое сообщение успешно обработано")
    except Exception as e:
        logger.error(f"Ошибка при обработке текстового сообщения: {e}")
        raise

# Обработчик сообщений в каналах
async def handle_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        chat = message.chat
        
        # Проверяем, является ли чат каналом
        if chat.type not in ['channel', 'group']:
            return
            
        # Проверяем, есть ли канал в базе
        channel_id = str(chat.id)
        if channel_id not in db.users['channels']:
            return
            
        channel = db.users['channels'][channel_id]
        
        # Проверяем, включены ли автоответы
        if not channel['settings']['auto_reply_enabled']:
            return
            
        # Проверяем ограничения
        restrictions = channel['settings']['restrictions']
        current_time = datetime.now()
        
        # Проверяем время работы
        start_time = datetime.strptime(restrictions['active_hours']['start'], '%H:%M').time()
        end_time = datetime.strptime(restrictions['active_hours']['end'], '%H:%M').time()
        if not (start_time <= current_time.time() <= end_time):
            return
            
        # Получаем ключ OpenAI владельца канала
        owner_id = int(channel['owner_id'])
        openai_key = db.get_user_openai_key(owner_id)
        if not openai_key:
            return
            
        # Генерируем ответ
        client = OpenAIClient(openai_key)
        response = client.generate_response(
            message.text,
            channel['settings']
        )
        
        # Отправляем ответ
        await message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения в канале: {e}")

def main():
    try:
        logger.info("Запуск бота...")
        # Создаем приложение и передаем токен бота
        application = Application.builder().token('8083571952:AAFZDg2UfFAlhQzOd-cDapTQv7X90BDD_bg').build()

        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.FORWARDED, handle_forwarded_message))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        application.add_handler(MessageHandler(filters.ChatType.CHANNEL | filters.ChatType.GROUP, handle_channel_message))
        
        # Запускаем бота
        logger.info("Бот успешно запущен и готов к работе")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        raise

if __name__ == '__main__':
    main() 