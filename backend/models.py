from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import random
import string

# Функция для генерации короткого ID
def generate_short_id(length: int = 6) -> str:
    """Генерирует короткий ID из букв и цифр"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Enum для фаз игры
class GamePhase(str, Enum):
    LOBBY = "lobby"
    SETUP = "setup"  # Распределение очков атаки/защиты
    ACTION = "action"  # Фаза 1: основные действия
    SPYING = "spying"  # Фаза 2: шпионаж
    BATTLE = "battle"  # Фаза 3: расчет атак
    NEGOTIATION = "negotiation"  # Фаза 4: переговоры
    ALLIANCE = "alliance"  # Фаза 5: альянсы
    SUMMIT = "summit"  # Фаза 6: общий саммит
    SPY_REPORTS = "spy_reports"  # Фаза 7: отчеты шпионов
    FINISHED = "finished"

# Enum для языков
class Language(str, Enum):
    RU = "ru"
    EN = "en"

# Enum для статуса игрока
class PlayerStatus(str, Enum):
    ACTIVE = "active"
    OBSERVER = "observer"
    DISCONNECTED = "disconnected"

# Модель игры/комнаты
class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    host_id: str
    password: Optional[str] = None
    language: Language = Language.RU
    max_players: int = 8
    current_phase: GamePhase = GamePhase.LOBBY
    phase_end_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    is_started: bool = False

# Модель игрока
class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    name: str
    socket_id: Optional[str] = None
    country: Optional[str] = None
    country_flag: Optional[str] = None
    attack_troops: int = 0
    defense_troops: int = 0
    status: PlayerStatus = PlayerStatus.ACTIVE
    is_ready: bool = False
    is_host: bool = False
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    ping: Optional[int] = None

# Модель альянса
class Alliance(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    player1_id: str
    player2_id: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Модель шпиона
class Spy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    owner_id: str
    target_id: str
    info_type: str  # "attack", "defense", "partners"
    is_delivered: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Модель боевого лога
class BattleLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    round_number: int
    defender_id: str
    attackers: List[Dict[str, Any]]  # [{"player_id": str, "sent": int, "lost": int, "survived": int}]
    effective_defense: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Модель сообщения чата
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    player_id: str
    player_name: str
    message: str
    message_type: str = "public"  # "public", "private", "system"
    target_player_id: Optional[str] = None  # для приватных сообщений
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Модели для API запросов
class CreateGameRequest(BaseModel):
    name: str
    host_name: str
    password: Optional[str] = None
    language: Language = Language.RU
    max_players: int = Field(default=8, ge=4, le=10)

class JoinGameRequest(BaseModel):
    game_id: str
    player_name: str
    password: Optional[str] = None

class SendMessageRequest(BaseModel):
    message: str
    target_player_id: Optional[str] = None

class KickPlayerRequest(BaseModel):
    player_id: str

class UpdateGameSettingsRequest(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    language: Optional[Language] = None
    max_players: Optional[int] = Field(None, ge=4, le=10)

# Модели для ответов
class GameResponse(BaseModel):
    id: str
    name: str
    host_name: str
    has_password: bool
    language: Language
    max_players: int
    current_players: int
    current_phase: GamePhase
    is_started: bool
    created_at: datetime

class PlayerResponse(BaseModel):
    id: str
    name: str
    country: Optional[str] = None
    country_flag: Optional[str] = None
    attack_troops: int
    defense_troops: int
    status: PlayerStatus
    is_ready: bool
    is_host: bool
    ping: Optional[int] = None

class GameDetailResponse(BaseModel):
    game: GameResponse
    players: List[PlayerResponse]
    is_host: bool
    current_player_id: str

# Список стран с флагами (упрощенный список для начала)
COUNTRIES = [
    {"name": "Россия", "flag": "🇷🇺", "code": "RU"},
    {"name": "США", "flag": "🇺🇸", "code": "US"},
    {"name": "Китай", "flag": "🇨🇳", "code": "CN"},
    {"name": "Германия", "flag": "🇩🇪", "code": "DE"},
    {"name": "Франция", "flag": "🇫🇷", "code": "FR"},
    {"name": "Великобритания", "flag": "🇬🇧", "code": "GB"},
    {"name": "Япония", "flag": "🇯🇵", "code": "JP"},
    {"name": "Италия", "flag": "🇮🇹", "code": "IT"},
    {"name": "Испания", "flag": "🇪🇸", "code": "ES"},
    {"name": "Канада", "flag": "🇨🇦", "code": "CA"},
]