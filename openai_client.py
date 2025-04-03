import openai
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        openai.api_key = api_key

    def generate_response(self, 
                         message: str, 
                         channel_settings: Dict[str, Any],
                         context: Optional[list] = None) -> str:
        """
        Генерация ответа на сообщение с учетом настроек канала и контекста
        """
        try:
            assistant_settings = channel_settings.get('assistant_settings', {})
            
            # Формируем системный промпт
            system_prompt = assistant_settings.get('system_prompt', 
                'Ты - дружелюбный ассистент, который отвечает на сообщения в Telegram канале. '
                'Отвечай кратко и по существу. Используй контекст предыдущих сообщений для более релевантных ответов.')
            
            # Добавляем ограничения по темам и словам
            allowed_topics = assistant_settings.get('allowed_topics', [])
            forbidden_words = assistant_settings.get('forbidden_words', [])
            
            if allowed_topics:
                system_prompt += f"\nОтвечай только на темы: {', '.join(allowed_topics)}"
            if forbidden_words:
                system_prompt += f"\nНе используй слова: {', '.join(forbidden_words)}"
            
            # Формируем сообщения для контекста
            messages = [{"role": "system", "content": system_prompt}]
            
            # Добавляем предыдущие сообщения из контекста
            if context:
                messages.extend(context)
            
            # Добавляем текущее сообщение
            messages.append({"role": "user", "content": message})
            
            # Генерируем ответ
            response = openai.ChatCompletion.create(
                model=assistant_settings.get('model', 'gpt-3.5-turbo'),
                messages=messages,
                temperature=assistant_settings.get('temperature', 0.7),
                max_tokens=assistant_settings.get('max_tokens', 150)
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}")
            return "Извините, произошла ошибка при генерации ответа. Пожалуйста, попробуйте позже."

    def validate_api_key(self) -> bool:
        """
        Проверка валидности API ключа
        """
        try:
            # Пробуем сделать тестовый запрос
            openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка валидации API ключа: {e}")
            return False 