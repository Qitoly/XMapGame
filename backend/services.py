import redis.asyncio as redis
import json
import os
from typing import Optional, Dict, Any, List
import asyncio

class RedisService:
    def __init__(self):
        # Используем Redis URL из переменных окружения или localhost по умолчанию
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    async def set_with_expiry(self, key: str, value: Any, expiry_seconds: int = 3600):
        """Установить значение с временем жизни"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.redis.setex(key, expiry_seconds, value)
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение по ключу"""
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def delete(self, key: str):
        """Удалить ключ"""
        await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        return await self.redis.exists(key)
    
    async def set_game_timer(self, game_id: str, phase: str, duration_seconds: int):
        """Установить таймер для фазы игры"""
        key = f"game_timer:{game_id}:{phase}"
        await self.set_with_expiry(key, {"phase": phase, "game_id": game_id}, duration_seconds)
    
    async def get_game_timer(self, game_id: str, phase: str) -> Optional[Dict]:
        """Получить информацию о таймере фазы"""
        key = f"game_timer:{game_id}:{phase}"
        return await self.get(key)
    
    async def store_invitation(self, game_id: str, from_player: str, to_player: str, invitation_type: str = "alliance"):
        """Сохранить приглашение с таймером 30 секунд"""
        key = f"invitation:{game_id}:{from_player}:{to_player}:{invitation_type}"
        data = {
            "game_id": game_id,
            "from_player": from_player,
            "to_player": to_player,
            "type": invitation_type
        }
        await self.set_with_expiry(key, data, 30)  # 30 секунд
    
    async def get_invitation(self, game_id: str, from_player: str, to_player: str, invitation_type: str = "alliance") -> Optional[Dict]:
        """Получить приглашение"""
        key = f"invitation:{game_id}:{from_player}:{to_player}:{invitation_type}"
        return await self.get(key)
    
    async def remove_invitation(self, game_id: str, from_player: str, to_player: str, invitation_type: str = "alliance"):
        """Удалить приглашение"""
        key = f"invitation:{game_id}:{from_player}:{to_player}:{invitation_type}"
        await self.delete(key)
    
    async def store_player_session(self, player_id: str, game_id: str, socket_id: str):
        """Сохранить сессию игрока"""
        key = f"player_session:{player_id}"
        data = {
            "game_id": game_id,
            "socket_id": socket_id,
            "player_id": player_id
        }
        await self.set_with_expiry(key, data, 7200)  # 2 часа
    
    async def get_player_session(self, player_id: str) -> Optional[Dict]:
        """Получить сессию игрока"""
        key = f"player_session:{player_id}"
        return await self.get(key)
    
    async def remove_player_session(self, player_id: str):
        """Удалить сессию игрока"""
        key = f"player_session:{player_id}"
        await self.delete(key)
    
    async def add_to_set(self, key: str, value: str):
        """Добавить значение в множество"""
        await self.redis.sadd(key, value)
    
    async def remove_from_set(self, key: str, value: str):
        """Удалить значение из множества"""
        await self.redis.srem(key, value)
    
    async def get_set_members(self, key: str) -> List[str]:
        """Получить все элементы множества"""
        return list(await self.redis.smembers(key))
    
    async def close(self):
        """Закрыть соединение с Redis"""
        await self.redis.close()

# Создаем глобальный экземпляр
redis_service = RedisService()

# Менеджер соединений Socket.IO
class ConnectionManager:
    def __init__(self):
        # Словарь для хранения активных соединений
        # player_id -> socket_id
        self.player_connections: Dict[str, str] = {}
        # game_id -> set of player_ids
        self.game_rooms: Dict[str, set] = {}
    
    async def connect_player(self, player_id: str, socket_id: str, game_id: str):
        """Подключить игрока"""
        self.player_connections[player_id] = socket_id
        
        if game_id not in self.game_rooms:
            self.game_rooms[game_id] = set()
        self.game_rooms[game_id].add(player_id)
        
        # Сохраняем в Redis
        await redis_service.store_player_session(player_id, game_id, socket_id)
    
    async def disconnect_player(self, player_id: str, game_id: str):
        """Отключить игрока"""
        if player_id in self.player_connections:
            del self.player_connections[player_id]
        
        if game_id in self.game_rooms:
            self.game_rooms[game_id].discard(player_id)
            if not self.game_rooms[game_id]:
                del self.game_rooms[game_id]
        
        # Удаляем из Redis
        await redis_service.remove_player_session(player_id)
    
    def get_player_socket(self, player_id: str) -> Optional[str]:
        """Получить socket_id игрока"""
        return self.player_connections.get(player_id)
    
    def get_game_players(self, game_id: str) -> set:
        """Получить список игроков в игре"""
        return self.game_rooms.get(game_id, set())
    
    def is_player_connected(self, player_id: str) -> bool:
        """Проверить, подключен ли игрок"""
        return player_id in self.player_connections

# Создаем глобальный экземпляр
connection_manager = ConnectionManager()