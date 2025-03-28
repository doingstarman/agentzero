import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class UserDatabase:
    def __init__(self):
        self.users = {
            'users': {},
            'channels': {},
            'user_states': {},
            'user_channels': {}
        }
        self.load_data()

    def load_data(self):
        """Загрузка данных из файла"""
        if os.path.exists('database.json'):
            with open('database.json', 'r', encoding='utf-8') as f:
                self.users = json.load(f)

    def save_data(self):
        """Сохранение данных в файл"""
        with open('database.json', 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=4)

    def add_user(self, user_id, username=None, first_name=None, last_name=None):
        """Добавление нового пользователя"""
        if str(user_id) not in self.users['users']:
            self.users['users'][str(user_id)] = {
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'commands_used': {},
                'openai_key': None  # Добавляем поле для хранения ключа OpenAI
            }
            self.save_data()
            return True
        return False

    def update_user_activity(self, user_id, command=None):
        """Обновление активности пользователя"""
        user_id = str(user_id)
        if user_id in self.users['users']:
            self.users['users'][user_id]['last_activity'] = datetime.now().isoformat()
            if command:
                if command not in self.users['users'][user_id]['commands_used']:
                    self.users['users'][user_id]['commands_used'][command] = 0
                self.users['users'][user_id]['commands_used'][command] += 1
            self.save_data()

    def add_channel(self, channel_id: int, channel_title: str, user_id: int, channel_username: str = None, system_prompt: str = None):
        """Добавление нового канала"""
        try:
            channel_id_str = str(channel_id)
            if channel_id_str in self.users['channels']:
                return False
            
            # Создаем базовые настройки канала
            channel_settings = {
                'auto_reply_enabled': True,
                'assistant_settings': {
                    'model': 'gpt-3.5-turbo',
                    'temperature': 0.7,
                    'max_tokens': 150,
                    'system_prompt': system_prompt or "Отвечай кратко и по существу",
                    'response_style': 'friendly'
                }
            }
            
            # Добавляем канал в базу
            self.users['channels'][channel_id_str] = {
                'id': channel_id,
                'title': channel_title,
                'username': channel_username,
                'owner_id': user_id,
                'settings': channel_settings,
                'stats': {
                    'total_messages': 0,
                    'total_replies': 0,
                    'last_activity': None
                }
            }
            
            # Добавляем канал в список каналов пользователя
            if user_id not in self.users['user_channels']:
                self.users['user_channels'][user_id] = []
            self.users['user_channels'][user_id].append(channel_id)
            
            # Сохраняем изменения
            self.save_data()
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении канала: {e}")
            return False

    def update_channel_settings(self, channel_id: int, settings: Dict[str, Any]):
        """Обновление настроек канала"""
        try:
            channel_id_str = str(channel_id)
            if channel_id_str not in self.users['channels']:
                return False
            
            channel = self.users['channels'][channel_id_str]
            
            # Обновляем настройки
            if 'assistant_settings' in settings:
                channel['settings']['assistant_settings'].update(settings['assistant_settings'])
            else:
                channel['settings'].update(settings)
            
            # Сохраняем изменения
            self.save_data()
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении настроек канала: {e}")
            return False

    def get_user_state(self, user_id):
        """Получение состояния пользователя"""
        user_id = str(user_id)
        return self.users['user_states'].get(user_id)

    def set_user_state(self, user_id, state, data=None):
        """Установка состояния пользователя"""
        user_id = str(user_id)
        self.users['user_states'][user_id] = {
            'state': state,
            'data': data or {},
            'updated_at': datetime.now().isoformat()
        }
        self.save_data()

    def clear_user_state(self, user_id):
        """Очистка состояния пользователя"""
        user_id = str(user_id)
        if user_id in self.users['user_states']:
            del self.users['user_states'][user_id]
            self.save_data()

    def get_user_channels(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение списка каналов пользователя"""
        user_id_str = str(user_id)
        channels = []
        for channel_id, channel_data in self.users['channels'].items():
            if channel_data['owner_id'] == user_id_str:
                channels.append(channel_data)
        return channels

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики пользователя"""
        user_id_str = str(user_id)
        return self.users['users'].get(user_id_str, {})

    def get_all_users(self) -> Dict[str, Any]:
        """Получение всех пользователей"""
        return self.users['users']

    def set_user_openai_key(self, user_id: int, key: str):
        """Установка ключа OpenAI для пользователя"""
        user_id_str = str(user_id)
        if user_id_str in self.users['users']:
            self.users['users'][user_id_str]['openai_key'] = key
            self.save_data()
            return True
        return False

    def get_user_openai_key(self, user_id: int) -> Optional[str]:
        """Получение ключа OpenAI пользователя"""
        user_id_str = str(user_id)
        return self.users['users'].get(user_id_str, {}).get('openai_key') 