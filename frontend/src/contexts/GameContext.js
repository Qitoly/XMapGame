import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { io } from 'socket.io-client';

// Типы действий
const GAME_ACTIONS = {
  SET_SOCKET: 'SET_SOCKET',
  SET_CURRENT_PLAYER: 'SET_CURRENT_PLAYER',
  SET_GAME_DATA: 'SET_GAME_DATA',
  SET_PLAYERS: 'SET_PLAYERS',
  SET_MESSAGES: 'SET_MESSAGES',
  ADD_MESSAGE: 'ADD_MESSAGE',
  UPDATE_PLAYER: 'UPDATE_PLAYER',
  REMOVE_PLAYER: 'REMOVE_PLAYER',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  SET_CONNECTION_STATUS: 'SET_CONNECTION_STATUS'
};

// Начальное состояние
const initialState = {
  socket: null,
  currentPlayer: null,
  gameData: null,
  players: [],
  messages: [],
  loading: false,
  error: null,
  isConnected: false
};

// Reducer
function gameReducer(state, action) {
  switch (action.type) {
    case GAME_ACTIONS.SET_SOCKET:
      return { ...state, socket: action.payload };
    case GAME_ACTIONS.SET_CURRENT_PLAYER:
      return { ...state, currentPlayer: action.payload };
    case GAME_ACTIONS.SET_GAME_DATA:
      return { ...state, gameData: action.payload };
    case GAME_ACTIONS.SET_PLAYERS:
      return { ...state, players: action.payload };
    case GAME_ACTIONS.SET_MESSAGES:
      return { ...state, messages: action.payload };
    case GAME_ACTIONS.ADD_MESSAGE:
      return { ...state, messages: [...state.messages, action.payload] };
    case GAME_ACTIONS.UPDATE_PLAYER:
      return {
        ...state,
        players: state.players.map(player =>
          player.id === action.payload.id ? { ...player, ...action.payload } : player
        )
      };
    case GAME_ACTIONS.REMOVE_PLAYER:
      return {
        ...state,
        players: state.players.filter(player => player.id !== action.payload)
      };
    case GAME_ACTIONS.SET_LOADING:
      return { ...state, loading: action.payload };
    case GAME_ACTIONS.SET_ERROR:
      return { ...state, error: action.payload };
    case GAME_ACTIONS.SET_CONNECTION_STATUS:
      return { ...state, isConnected: action.payload };
    default:
      return state;
  }
}

// Контекст
const GameContext = createContext();

// Провайдер контекста
export function GameProvider({ children }) {
  const [state, dispatch] = useReducer(gameReducer, initialState);

  // Инициализация Socket.IO соединения
  useEffect(() => {
    const backendUrl = process.env.REACT_APP_BACKEND_URL;
    const socket = io(backendUrl, {
      transports: ['websocket', 'polling'],
      forceNew: true,
      path: '/api/socket.io/',
    });

    socket.on('connect', () => {
      console.log('Socket connected:', socket.id);
      dispatch({ type: GAME_ACTIONS.SET_CONNECTION_STATUS, payload: true });
    });

    socket.on('disconnect', () => {
      console.log('Socket disconnected');
      dispatch({ type: GAME_ACTIONS.SET_CONNECTION_STATUS, payload: false });
    });

    socket.on('error', (error) => {
      console.error('Socket error:', error);
      dispatch({ type: GAME_ACTIONS.SET_ERROR, payload: error.message });
    });

    // Обработчики игровых событий
    socket.on('player_joined', (data) => {
      console.log('Player joined:', data);
      // Здесь можно обновить список игроков
    });

    socket.on('player_disconnected', (data) => {
      console.log('Player disconnected:', data);
      dispatch({ type: GAME_ACTIONS.REMOVE_PLAYER, payload: data.player_id });
    });

    socket.on('new_message', (message) => {
      dispatch({ type: GAME_ACTIONS.ADD_MESSAGE, payload: message });
    });

    socket.on('ping_updated', (data) => {
      dispatch({ 
        type: GAME_ACTIONS.UPDATE_PLAYER, 
        payload: { id: data.player_id, ping: data.ping }
      });
    });

    socket.on('player_ready_changed', (data) => {
      dispatch({ 
        type: GAME_ACTIONS.UPDATE_PLAYER, 
        payload: { id: data.player_id, is_ready: data.is_ready }
      });
      
      // Также обновляем текущего игрока если это он
      if (state.currentPlayer && state.currentPlayer.id === data.player_id) {
        dispatch({ 
          type: GAME_ACTIONS.SET_CURRENT_PLAYER, 
          payload: { ...state.currentPlayer, is_ready: data.is_ready }
        });
      }
    });

    socket.on('all_players_ready', (data) => {
      console.log('All players ready:', data.message);
    });

    socket.on('game_started', (data) => {
      console.log('Game started:', data);
      // Обновляем состояние игры
      if (state.gameData) {
        dispatch({ 
          type: GAME_ACTIONS.SET_GAME_DATA, 
          payload: { ...state.gameData, current_phase: data.phase, is_started: true }
        });
      }
      // Обновляем игроков с назначенными странами
      dispatch({ type: GAME_ACTIONS.SET_PLAYERS, payload: data.players });
    });

    dispatch({ type: GAME_ACTIONS.SET_SOCKET, payload: socket });

    return () => {
      socket.disconnect();
    };
  }, []); // Убираем state из зависимостей

  // Методы для работы с игрой
  const gameActions = {
    // Присоединиться к комнате игры
    joinGameRoom: (gameId, playerId) => {
      if (state.socket) {
        state.socket.emit('join_game_room', { game_id: gameId, player_id: playerId });
      }
    },

    // Отправить сообщение
    sendMessage: (gameId, playerId, message, targetPlayerId = null) => {
      if (state.socket) {
        state.socket.emit('send_message', {
          game_id: gameId,
          player_id: playerId,
          message,
          target_player_id: targetPlayerId
        });
      }
    },

    // Обновить пинг
    updatePing: (playerId, ping) => {
      if (state.socket) {
        state.socket.emit('update_ping', { player_id: playerId, ping });
      }
    },

    // Изменить статус готовности
    setPlayerReady: (playerId, isReady) => {
      if (state.socket) {
        state.socket.emit('player_ready', { player_id: playerId, is_ready: isReady });
      }
    },

    // Начать игру (только хост)
    startGame: (gameId, playerId) => {
      if (state.socket) {
        state.socket.emit('start_game', { game_id: gameId, player_id: playerId });
      }
    },

    // Установить данные игры
    setGameData: (gameData) => {
      dispatch({ type: GAME_ACTIONS.SET_GAME_DATA, payload: gameData });
    },

    // Установить текущего игрока
    setCurrentPlayer: (player) => {
      dispatch({ type: GAME_ACTIONS.SET_CURRENT_PLAYER, payload: player });
    },

    // Установить список игроков
    setPlayers: (players) => {
      dispatch({ type: GAME_ACTIONS.SET_PLAYERS, payload: players });
    },

    // Установить загрузку
    setLoading: (loading) => {
      dispatch({ type: GAME_ACTIONS.SET_LOADING, payload: loading });
    },

    // Установить ошибку
    setError: (error) => {
      dispatch({ type: GAME_ACTIONS.SET_ERROR, payload: error });
    },

    // Очистить ошибку
    clearError: () => {
      dispatch({ type: GAME_ACTIONS.SET_ERROR, payload: null });
    }
  };

  return (
    <GameContext.Provider value={{ ...state, ...gameActions }}>
      {children}
    </GameContext.Provider>
  );
}

// Хук для использования контекста
export function useGame() {
  const context = useContext(GameContext);
  if (!context) {
    throw new Error('useGame must be used within a GameProvider');
  }
  return context;
}