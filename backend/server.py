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

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
