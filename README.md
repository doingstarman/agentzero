# Telegram Channel Auto-Reply Bot

Бот для автоматических ответов на комментарии в Telegram каналах с использованием OpenAI.

## Возможности

- Добавление бота в каналы
- Настройка автоответов с помощью OpenAI
- Настраиваемый стиль ответов
- Статистика использования
- Управление несколькими каналами

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/telegram-auto-reply-bot.git
cd telegram-auto-reply-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` и добавьте в него:
```
TELEGRAM_BOT_TOKEN=your_bot_token
```

4. Запустите бота:
```bash
python echo_bot.py
```

## Использование

1. Запустите бота командой `/start`
2. Нажмите "Добавить новый канал"
3. Следуйте инструкциям по настройке
4. Настройте стиль ответов бота
5. Готово! Бот будет автоматически отвечать на комментарии в вашем канале

## Структура проекта

- `echo_bot.py` - основной файл бота
- `database.py` - работа с базой данных
- `openai_client.py` - работа с OpenAI API
- `requirements.txt` - зависимости проекта
- `database.json` - файл базы данных

## Лицензия

MIT 