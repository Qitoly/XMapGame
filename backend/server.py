from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import socketio
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import random

# Импорт моделей и сервисов
from models import *
from services import redis_service, connection_manager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Socket.IO setup
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# GAME API ENDPOINTS
# =============================================================================

@api_router.get("/games", response_model=List[GameResponse])
async def get_games():
    """Получить список доступных игр"""
    try:
        games_cursor = db.games.find({"is_started": False})
        games = await games_cursor.to_list(100)
        
        result = []
        for game_data in games:
            # Подсчитываем количество игроков
            players_count = await db.players.count_documents({
                "game_id": game_data["id"],
                "status": {"$ne": PlayerStatus.DISCONNECTED}
            })
            
            # Получаем имя хоста
            host = await db.players.find_one({
                "game_id": game_data["id"],
                "is_host": True
            })
            host_name = host["name"] if host else "Unknown"
            
            game_response = GameResponse(
                id=game_data["id"],
                name=game_data["name"],
                host_name=host_name,
                has_password=bool(game_data.get("password")),
                language=game_data["language"],
                max_players=game_data["max_players"],
                current_players=players_count,
                current_phase=game_data["current_phase"],
                is_started=game_data["is_started"],
                created_at=game_data["created_at"]
            )
            result.append(game_response)
        
        return result
    except Exception as e:
        logger.error(f"Error getting games: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка игр")

@api_router.post("/games", response_model=GameDetailResponse)
async def create_game(request: CreateGameRequest):
    """Создать новую игру"""
    try:
        # Создаем игру
        game = Game(
            name=request.name,
            host_id="",  # Будет обновлен после создания игрока
            password=request.password,
            language=request.language,
            max_players=request.max_players
        )
        
        # Создаем игрока-хоста
        host = Player(
            game_id=game.id,
            name=request.host_name,
            is_host=True,
            status=PlayerStatus.ACTIVE
        )
        
        # Обновляем host_id в игре
        game.host_id = host.id
        
        # Сохраняем в базу
        await db.games.insert_one(game.dict())
        await db.players.insert_one(host.dict())
        
        # Формируем ответ
        players = [PlayerResponse(**host.dict())]
        
        game_response = GameResponse(
            id=game.id,
            name=game.name,
            host_name=host.name,
            has_password=bool(game.password),
            language=game.language,
            max_players=game.max_players,
            current_players=1,
            current_phase=game.current_phase,
            is_started=game.is_started,
            created_at=game.created_at
        )
        
        response = GameDetailResponse(
            game=game_response,
            players=players,
            is_host=True,
            current_player_id=host.id
        )
        
        logger.info(f"Created game {game.id} with host {host.name}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating game: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания игры")

@api_router.post("/games/{game_id}/join", response_model=GameDetailResponse)
async def join_game(game_id: str, request: JoinGameRequest):
    """Присоединиться к игре"""
    try:
        # Проверяем существование игры
        game_data = await db.games.find_one({"id": game_id})
        if not game_data:
            raise HTTPException(status_code=404, detail="Игра не найдена")
        
        game = Game(**game_data)
        
        # Проверяем пароль
        if game.password and game.password != request.password:
            raise HTTPException(status_code=401, detail="Неверный пароль")
        
        # Проверяем, что игра не началась
        if game.is_started:
            raise HTTPException(status_code=400, detail="Игра уже началась")
        
        # Проверяем количество игроков
        current_players = await db.players.count_documents({
            "game_id": game_id,
            "status": {"$ne": PlayerStatus.DISCONNECTED}
        })
        
        if current_players >= game.max_players:
            raise HTTPException(status_code=400, detail="Игра переполнена")
        
        # Проверяем уникальность имени
        existing_player = await db.players.find_one({
            "game_id": game_id,
            "name": request.player_name,
            "status": {"$ne": PlayerStatus.DISCONNECTED}
        })
        
        if existing_player:
            raise HTTPException(status_code=400, detail="Игрок с таким именем уже в игре")
        
        # Создаем нового игрока
        player = Player(
            game_id=game_id,
            name=request.player_name,
            status=PlayerStatus.ACTIVE
        )
        
        await db.players.insert_one(player.dict())
        
        # Получаем всех игроков для ответа
        players_data = await db.players.find({
            "game_id": game_id,
            "status": {"$ne": PlayerStatus.DISCONNECTED}
        }).to_list(100)
        
        players = [PlayerResponse(**p) for p in players_data]
        
        # Получаем имя хоста
        host = await db.players.find_one({
            "game_id": game_id,
            "is_host": True
        })
        host_name = host["name"] if host else "Unknown"
        
        game_response = GameResponse(
            id=game.id,
            name=game.name,
            host_name=host_name,
            has_password=bool(game.password),
            language=game.language,
            max_players=game.max_players,
            current_players=len(players),
            current_phase=game.current_phase,
            is_started=game.is_started,
            created_at=game.created_at
        )
        
        response = GameDetailResponse(
            game=game_response,
            players=players,
            is_host=False,
            current_player_id=player.id
        )
        
        # Уведомляем всех игроков в комнате о новом участнике
        await sio.emit("player_joined", {
            "player_id": player.id,
            "player_name": player.name,
            "status": PlayerStatus.ACTIVE,
            "is_host": False,
            "is_ready": False,
            "attack_troops": 0,
            "defense_troops": 0,
            "ping": None,
            "country": None,
            "country_flag": None
        }, room=f"game_{game_id}")
        
        logger.info(f"Player {player.name} joined game {game_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining game: {e}")
        raise HTTPException(status_code=500, detail="Ошибка присоединения к игре")

@api_router.get("/games/{game_id}", response_model=GameDetailResponse)
async def get_game_details(game_id: str, player_id: str):
    """Получить детали игры"""
    try:
        # Проверяем существование игры
        game_data = await db.games.find_one({"id": game_id})
        if not game_data:
            raise HTTPException(status_code=404, detail="Игра не найдена")
        
        game = Game(**game_data)
        
        # Проверяем, что игрок в игре
        player_data = await db.players.find_one({
            "id": player_id,
            "game_id": game_id
        })
        
        if not player_data:
            raise HTTPException(status_code=403, detail="Вы не участвуете в этой игре")
        
        # Получаем всех игроков
        players_data = await db.players.find({
            "game_id": game_id,
            "status": {"$ne": PlayerStatus.DISCONNECTED}
        }).to_list(100)
        
        players = [PlayerResponse(**p) for p in players_data]
        
        # Получаем имя хоста
        host = await db.players.find_one({
            "game_id": game_id,
            "is_host": True
        })
        host_name = host["name"] if host else "Unknown"
        
        game_response = GameResponse(
            id=game.id,
            name=game.name,
            host_name=host_name,
            has_password=bool(game.password),
            language=game.language,
            max_players=game.max_players,
            current_players=len(players),
            current_phase=game.current_phase,
            is_started=game.is_started,
            created_at=game.created_at
        )
        
        response = GameDetailResponse(
            game=game_response,
            players=players,
            is_host=player_data["is_host"],
            current_player_id=player_id
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game details: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения деталей игры")

@api_router.post("/games/{game_id}/kick")
async def kick_player(game_id: str, request: KickPlayerRequest, host_player_id: str):
    """Исключить игрока из игры (только для хоста)"""
    try:
        # Проверяем, что запрос от хоста
        host = await db.players.find_one({
            "id": host_player_id,
            "game_id": game_id,
            "is_host": True
        })
        
        if not host:
            raise HTTPException(status_code=403, detail="Только хост может исключать игроков")
        
        # Проверяем существование игрока
        player = await db.players.find_one({
            "id": request.player_id,
            "game_id": game_id
        })
        
        if not player:
            raise HTTPException(status_code=404, detail="Игрок не найден")
        
        if player["is_host"]:
            raise HTTPException(status_code=400, detail="Нельзя исключить хоста")
        
        # Помечаем игрока как отключенного
        await db.players.update_one(
            {"id": request.player_id},
            {"$set": {"status": PlayerStatus.DISCONNECTED}}
        )
        
        logger.info(f"Player {player['name']} was kicked from game {game_id}")
        return {"message": "Игрок исключен"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error kicking player: {e}")
        raise HTTPException(status_code=500, detail="Ошибка исключения игрока")

# =============================================================================
# SOCKET.IO EVENTS
# =============================================================================

@sio.event
async def connect(sid, environ):
    """Обработка подключения клиента"""
    logger.info(f"Client {sid} connected")

@sio.event
async def disconnect(sid):
    """Обработка отключения клиента"""
    logger.info(f"Client {sid} disconnected")
    
    # Ищем игрока по socket_id и помечаем как отключенного
    player = await db.players.find_one({"socket_id": sid})
    if player:
        await db.players.update_one(
            {"id": player["id"]},
            {"$set": {"status": PlayerStatus.DISCONNECTED, "socket_id": None}}
        )
        
        # Отключаем от менеджера соединений
        await connection_manager.disconnect_player(player["id"], player["game_id"])
        
        # Уведомляем других игроков в комнате
        await sio.emit("player_disconnected", {
            "player_id": player["id"],
            "player_name": player["name"]
        }, room=f"game_{player['game_id']}")

@sio.event
async def join_game_room(sid, data):
    """Присоединиться к комнате игры"""
    try:
        game_id = data.get("game_id")
        player_id = data.get("player_id")
        
        if not game_id or not player_id:
            await sio.emit("error", {"message": "Missing game_id or player_id"}, room=sid)
            return
        
        # Проверяем существование игрока
        player = await db.players.find_one({
            "id": player_id,
            "game_id": game_id
        })
        
        if not player:
            await sio.emit("error", {"message": "Player not found"}, room=sid)
            return
        
        # Обновляем socket_id игрока
        await db.players.update_one(
            {"id": player_id},
            {
                "$set": {
                    "socket_id": sid,
                    "status": PlayerStatus.ACTIVE,
                    "last_activity": datetime.utcnow()
                }
            }
        )
        
        # Присоединяем к комнате
        await sio.enter_room(sid, f"game_{game_id}")
        
        # Добавляем в менеджер соединений
        await connection_manager.connect_player(player_id, sid, game_id)
        
        # Уведомляем других игроков
        await sio.emit("player_joined", {
            "player_id": player_id,
            "player_name": player["name"],
            "status": PlayerStatus.ACTIVE
        }, room=f"game_{game_id}", skip_sid=sid)
        
        logger.info(f"Player {player['name']} joined room game_{game_id}")
        
    except Exception as e:
        logger.error(f"Error joining game room: {e}")
        await sio.emit("error", {"message": "Ошибка присоединения к комнате"}, room=sid)

@sio.event
async def send_message(sid, data):
    """Отправить сообщение в чат"""
    try:
        game_id = data.get("game_id")
        player_id = data.get("player_id")
        message = data.get("message", "").strip()
        target_player_id = data.get("target_player_id")  # Для приватных сообщений
        
        if not all([game_id, player_id, message]):
            await sio.emit("error", {"message": "Missing required fields"}, room=sid)
            return
        
        # Проверяем игрока
        player = await db.players.find_one({
            "id": player_id,
            "game_id": game_id,
            "socket_id": sid
        })
        
        if not player:
            await sio.emit("error", {"message": "Unauthorized"}, room=sid)
            return
        
        # Создаем сообщение
        chat_message = ChatMessage(
            game_id=game_id,
            player_id=player_id,
            player_name=player["name"],
            message=message,
            message_type="private" if target_player_id else "public",
            target_player_id=target_player_id
        )
        
        # Сохраняем в базу
        await db.chat_messages.insert_one(chat_message.dict())
        
        # Отправляем сообщение
        message_data = {
            "id": chat_message.id,
            "player_id": player_id,
            "player_name": player["name"],
            "message": message,
            "message_type": chat_message.message_type,
            "target_player_id": target_player_id,
            "created_at": chat_message.created_at.isoformat()
        }
        
        if target_player_id:
            # Приватное сообщение
            target_player = await db.players.find_one({"id": target_player_id})
            if target_player and target_player.get("socket_id"):
                await sio.emit("new_message", message_data, room=target_player["socket_id"])
                await sio.emit("new_message", message_data, room=sid)
        else:
            # Публичное сообщение
            await sio.emit("new_message", message_data, room=f"game_{game_id}")
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        await sio.emit("error", {"message": "Ошибка отправки сообщения"}, room=sid)

@sio.event
async def update_ping(sid, data):
    """Обновить пинг игрока"""
    try:
        player_id = data.get("player_id")
        ping = data.get("ping", 0)
        
        if not player_id:
            return
        
        # Обновляем пинг в базе
        await db.players.update_one(
            {"id": player_id, "socket_id": sid},
            {"$set": {"ping": ping, "last_activity": datetime.utcnow()}}
        )
        
        # Получаем игру игрока
        player = await db.players.find_one({"id": player_id})
        if player:
            # Уведомляем других игроков об обновлении пинга
            await sio.emit("ping_updated", {
                "player_id": player_id,
                "ping": ping
            }, room=f"game_{player['game_id']}", skip_sid=sid)
        
    except Exception as e:
        logger.error(f"Error updating ping: {e}")

@sio.event
async def player_ready(sid, data):
    """Игрок готов к началу игры"""
    try:
        player_id = data.get("player_id")
        is_ready = data.get("is_ready", True)
        
        if not player_id:
            await sio.emit("error", {"message": "Missing player_id"}, room=sid)
            return
        
        # Обновляем статус готовности
        result = await db.players.update_one(
            {"id": player_id, "socket_id": sid},
            {"$set": {"is_ready": is_ready}}
        )
        
        if result.modified_count == 0:
            await sio.emit("error", {"message": "Player not found"}, room=sid)
            return
        
        # Получаем игрока и игру
        player = await db.players.find_one({"id": player_id})
        if not player:
            return
        
        game_id = player["game_id"]
        
        # Уведомляем других игроков
        await sio.emit("player_ready_changed", {
            "player_id": player_id,
            "is_ready": is_ready
        }, room=f"game_{game_id}")
        
        # Если все игроки готовы, можно начинать игру
        total_players = await db.players.count_documents({
            "game_id": game_id,
            "status": PlayerStatus.ACTIVE
        })
        
        ready_players = await db.players.count_documents({
            "game_id": game_id,
            "status": PlayerStatus.ACTIVE,
            "is_ready": True
        })
        
        if total_players >= 4 and ready_players == total_players:
            # Все готовы к началу игры
            await sio.emit("all_players_ready", {
                "message": "Все игроки готовы! Игра может начаться."
            }, room=f"game_{game_id}")
        
    except Exception as e:
        logger.error(f"Error updating player ready status: {e}")
        await sio.emit("error", {"message": "Ошибка обновления статуса"}, room=sid)

@sio.event
async def start_game(sid, data):
    """Начать игру (только хост)"""
    try:
        game_id = data.get("game_id")
        player_id = data.get("player_id")
        
        if not all([game_id, player_id]):
            await sio.emit("error", {"message": "Missing required fields"}, room=sid)
            return
        
        # Проверяем, что это хост
        host = await db.players.find_one({
            "id": player_id,
            "game_id": game_id,
            "is_host": True,
            "socket_id": sid
        })
        
        if not host:
            await sio.emit("error", {"message": "Only host can start the game"}, room=sid)
            return
        
        # Проверяем минимальное количество игроков
        active_players = await db.players.count_documents({
            "game_id": game_id,
            "status": PlayerStatus.ACTIVE
        })
        
        if active_players < 4:
            await sio.emit("error", {"message": "Минимум 4 игрока для начала игры"}, room=sid)
            return
        
        # Назначаем страны игрокам
        players = await db.players.find({
            "game_id": game_id,
            "status": PlayerStatus.ACTIVE
        }).to_list(100)
        
        # Перемешиваем список стран
        available_countries = COUNTRIES.copy()
        random.shuffle(available_countries)
        
        # Назначаем страны
        for i, player in enumerate(players):
            if i < len(available_countries):
                country = available_countries[i]
                await db.players.update_one(
                    {"id": player["id"]},
                    {
                        "$set": {
                            "country": country["name"],
                            "country_flag": country["flag"],
                            "is_ready": False  # Сбрасываем готовность для фазы настройки
                        }
                    }
                )
        
        # Обновляем статус игры
        await db.games.update_one(
            {"id": game_id},
            {
                "$set": {
                    "current_phase": GamePhase.SETUP,
                    "is_started": True,
                    "started_at": datetime.utcnow()
                }
            }
        )
        
        # Получаем обновленных игроков
        updated_players = await db.players.find({
            "game_id": game_id,
            "status": PlayerStatus.ACTIVE
        }).to_list(100)
        
        # Уведомляем всех о начале игры
        await sio.emit("game_started", {
            "phase": GamePhase.SETUP,
            "message": "Игра началась! Распределите очки между атакой и защитой.",
            "players": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "country": p.get("country"),
                    "country_flag": p.get("country_flag")
                }
                for p in updated_players
            ]
        }, room=f"game_{game_id}")
        
        logger.info(f"Game {game_id} started with {len(players)} players")
        
    except Exception as e:
        logger.error(f"Error starting game: {e}")
        await sio.emit("error", {"message": "Ошибка начала игры"}, room=sid)

# Mount Socket.IO server under the /api/socket.io path
socket_asgi_app = socketio.ASGIApp(sio, socketio_path="/api/socket.io")

# Include the router in the main app
app.include_router(api_router)

# Configure CORS before mounting Socket.IO
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the Socket.IO app
app.mount("/api/socket.io", socket_asgi_app)

# Export the main app for uvicorn
application = app

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    await redis_service.close()
