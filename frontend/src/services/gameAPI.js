import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерсептор для логирования ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API методы для работы с играми
export const gameAPI = {
  // Получить список доступных игр
  getGames: async () => {
    try {
      const response = await api.get('/games');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Ошибка получения списка игр');
    }
  },

  // Создать новую игру
  createGame: async (gameData) => {
    try {
      const response = await api.post('/games', gameData);
      return response.data;
    } catch (error) {
      let errorMessage = 'Ошибка создания игры';
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (Array.isArray(detail)) {
          // If detail is an array, extract the message from the first item
          errorMessage = detail[0]?.msg || detail[0]?.message || detail[0] || errorMessage;
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (typeof detail === 'object' && detail.message) {
          errorMessage = detail.message;
        }
      }
      
      throw new Error(errorMessage);
    }
  },

  // Присоединиться к игре
  joinGame: async (gameId, joinData) => {
    try {
      const response = await api.post(`/games/${gameId}/join`, joinData);
      return response.data;
    } catch (error) {
      let errorMessage = 'Ошибка присоединения к игре';
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (Array.isArray(detail)) {
          // If detail is an array, extract the message from the first item
          errorMessage = detail[0]?.msg || detail[0]?.message || detail[0] || errorMessage;
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (typeof detail === 'object' && detail.message) {
          errorMessage = detail.message;
        }
      }
      
      throw new Error(errorMessage);
    }
  },

  // Получить детали игры
  getGameDetails: async (gameId, playerId) => {
    try {
      const response = await api.get(`/games/${gameId}?player_id=${playerId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Ошибка получения данных игры');
    }
  },

  // Исключить игрока (только хост)
  kickPlayer: async (gameId, playerId, hostPlayerId) => {
    try {
      const response = await api.post(`/games/${gameId}/kick`, 
        { player_id: playerId },
        { params: { host_player_id: hostPlayerId } }
      );
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Ошибка исключения игрока');
    }
  },

  // Обновить настройки игры (только хост)
  updateGameSettings: async (gameId, settings, hostPlayerId) => {
    try {
      const response = await api.put(`/games/${gameId}/settings`, 
        settings,
        { params: { host_player_id: hostPlayerId } }
      );
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Ошибка обновления настроек');
    }
  }
};

// Утилиты для работы с данными
export const gameUtils = {
  // Проверить, является ли игрок хостом
  isHost: (gameData, playerId) => {
    return gameData?.players?.find(p => p.id === playerId)?.is_host || false;
  },

  // Получить игрока по ID
  getPlayerById: (players, playerId) => {
    return players?.find(p => p.id === playerId) || null;
  },

  // Проверить, готовы ли все игроки
  areAllPlayersReady: (players) => {
    return players?.length >= 4 && players?.every(p => p.is_ready) || false;
  },

  // Получить количество активных игроков
  getActivePlayersCount: (players) => {
    return players?.filter(p => p.status === 'active')?.length || 0;
  },

  // Форматировать время
  formatTime: (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ru-RU', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  },

  // Получить статус пинга
  getPingStatus: (ping) => {
    if (!ping) return { status: 'unknown', color: 'gray', text: '-' };
    if (ping < 50) return { status: 'good', color: 'green', text: `${ping}мс` };
    if (ping < 150) return { status: 'ok', color: 'yellow', text: `${ping}мс` };
    return { status: 'bad', color: 'red', text: `${ping}мс` };
  },

  // Проверить, можно ли начать игру
  canStartGame: (gameData, players, currentPlayerId) => {
    const isHost = gameUtils.isHost(gameData, currentPlayerId);
    const hasMinPlayers = gameUtils.getActivePlayersCount(players) >= 4;
    const allReady = gameUtils.areAllPlayersReady(players);
    
    return isHost && hasMinPlayers && allReady && !gameData?.is_started;
  }
};

export default api;