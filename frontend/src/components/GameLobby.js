import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { 
  Users, 
  Crown, 
  MessageCircle, 
  Mic, 
  MicOff, 
  Settings, 
  Copy, 
  UserMinus,
  Play,
  Clock,
  Wifi,
  Shield,
  Sword
} from 'lucide-react';
import { useGame } from '../contexts/GameContext';
import { gameUtils, gameAPI } from '../services/gameAPI';

function GameLobby({ gameData, onLeaveGame }) {
  const { 
    currentPlayer, 
    players, 
    messages, 
    isConnected,
    joinGameRoom,
    sendMessage,
    updatePing,
    setPlayerReady,
    startGame
  } = useGame();

  const [message, setMessage] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [micEnabled, setMicEnabled] = useState(false);
  const messagesEndRef = useRef(null);
  const pingIntervalRef = useRef(null);

  // Присоединяемся к комнате при загрузке
  useEffect(() => {
    if (gameData?.game?.id && currentPlayer?.id) {
      joinGameRoom(gameData.game.id, currentPlayer.id);
    }
  }, [gameData?.game?.id, currentPlayer?.id]);

  // Скроллим чат вниз при новых сообщениях
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Периодически обновляем пинг
  useEffect(() => {
    if (currentPlayer?.id) {
      const measurePing = () => {
        const start = Date.now();
        // Симулируем измерение пинга
        const ping = Math.floor(Math.random() * 100) + 20; // 20-120ms
        updatePing(currentPlayer.id, ping);
      };

      measurePing(); // Сразу измеряем
      pingIntervalRef.current = setInterval(measurePing, 5000); // Каждые 5 секунд

      return () => {
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }
      };
    }
  }, [currentPlayer?.id]);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (message.trim() && gameData?.game?.id && currentPlayer?.id) {
      sendMessage(gameData.game.id, currentPlayer.id, message.trim());
      setMessage('');
    }
  };

  const handleReadyToggle = () => {
    if (currentPlayer?.id) {
      setPlayerReady(currentPlayer.id, !currentPlayer.is_ready);
    }
  };

  const handleStartGame = () => {
    if (gameData?.game?.id && currentPlayer?.id) {
      startGame(gameData.game.id, currentPlayer.id);
    }
  };

  const copyGameId = () => {
    navigator.clipboard.writeText(gameData?.game?.id || '');
    // Можно добавить уведомление о копировании
  };

  const isHost = gameData?.is_host || false;
  const canStart = gameUtils.canStartGame(gameData?.game, players, currentPlayer?.id);
  const activePlayersCount = gameUtils.getActivePlayersCount(players);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4">
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Левая панель - Игроки */}
        <div className="lg:col-span-1 space-y-4">
          {/* Информация об игре */}
          <Card className="bg-white/80 backdrop-blur-sm border-white/20 shadow-lg">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center">
                  <Crown className="w-5 h-5 mr-2 text-yellow-500" />
                  {gameData?.game?.name}
                </CardTitle>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-xs text-gray-500">
                    {isConnected ? 'Онлайн' : 'Офлайн'}
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span>ID игры:</span>
                <div className="flex items-center space-x-1">
                  <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                    {gameData?.game?.id}
                  </code>
                  <Button size="sm" variant="ghost" onClick={copyGameId} title="Копировать ID">
                    <Copy className="w-3 h-3" />
                  </Button>
                </div>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Игроков:</span>
                <span>{activePlayersCount}/{gameData?.game?.max_players}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Язык:</span>
                <span>{gameData?.game?.language === 'ru' ? '🇷🇺 Русский' : '🇺🇸 English'}</span>
              </div>
              {gameData?.game?.has_password && (
                <div className="flex items-center justify-between text-sm">
                  <span>Защищена:</span>
                  <Shield className="w-4 h-4 text-blue-500" />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Список игроков */}
          <Card className="bg-white/80 backdrop-blur-sm border-white/20 shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center">
                <Users className="w-5 h-5 mr-2" />
                Игроки ({activePlayersCount})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {players.map((player) => {
                const pingStatus = gameUtils.getPingStatus(player.ping);
                const isCurrentPlayer = player.id === currentPlayer?.id;
                
                return (
                  <div
                    key={player.id}
                    className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
                      isCurrentPlayer 
                        ? 'bg-blue-50 border-blue-200' 
                        : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="flex flex-col items-center">
                        {player.country && (
                          <div className="text-xl mb-1" title={player.country}>
                            {player.country_flag}
                          </div>
                        )}
                        <div className="flex items-center space-x-1">
                          {player.is_host && <Crown className="w-3 h-3 text-yellow-500" />}
                          {player.is_ready && <div className="w-2 h-2 bg-green-500 rounded-full" />}
                        </div>
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium text-sm">
                            {player.name}
                            {isCurrentPlayer && ' (Вы)'}
                          </span>
                          {player.status === 'observer' && (
                            <Badge variant="secondary" className="text-xs">
                              Наблюдатель
                            </Badge>
                          )}
                        </div>
                        
                        {/* Статистика войск для начатой игры */}
                        {gameData?.game?.is_started && (
                          <div className="flex items-center space-x-2 text-xs text-gray-600 mt-1">
                            <div className="flex items-center">
                              <Sword className="w-3 h-3 mr-1 text-red-500" />
                              {player.attack_troops}
                            </div>
                            <div className="flex items-center">
                              <Shield className="w-3 h-3 mr-1 text-blue-500" />
                              {player.defense_troops}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      {/* Пинг */}
                      <div className="flex items-center space-x-1">
                        <Wifi className={`w-3 h-3 text-${pingStatus.color}-500`} />
                        <span className={`text-xs text-${pingStatus.color}-600`}>
                          {pingStatus.text}
                        </span>
                      </div>

                      {/* Микрофон (заглушка) */}
                      <div className={`p-1 rounded ${micEnabled ? 'bg-green-100' : 'bg-gray-100'}`}>
                        {micEnabled ? (
                          <Mic className="w-3 h-3 text-green-600" />
                        ) : (
                          <MicOff className="w-3 h-3 text-gray-400" />
                        )}
                      </div>

                      {/* Кнопка исключения для хоста */}
                      {isHost && !player.is_host && player.id !== currentPlayer?.id && (
                        <Button size="sm" variant="ghost" className="text-red-500 hover:text-red-700">
                          <UserMinus className="w-3 h-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Кнопки управления */}
          <Card className="bg-white/80 backdrop-blur-sm border-white/20 shadow-lg">
            <CardContent className="p-4 space-y-3">
              {!gameData?.game?.is_started && (
                <>
                  <Button
                    onClick={handleReadyToggle}
                    className={`w-full ${
                      currentPlayer?.is_ready 
                        ? 'bg-green-500 hover:bg-green-600' 
                        : 'bg-blue-500 hover:bg-blue-600'
                    } text-white`}
                  >
                    <Clock className="w-4 h-4 mr-2" />
                    {currentPlayer?.is_ready ? 'Отменить готовность' : 'Готов к игре'}
                  </Button>

                  {isHost && (
                    <Button
                      onClick={handleStartGame}
                      disabled={!canStart}
                      className="w-full bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white disabled:opacity-50"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Начать игру
                    </Button>
                  )}
                </>
              )}

              <Button
                onClick={onLeaveGame}
                variant="outline"
                className="w-full border-red-200 text-red-600 hover:bg-red-50"
              >
                Покинуть игру
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Правая панель - Чат */}
        <div className="lg:col-span-2">
          <Card className="bg-white/80 backdrop-blur-sm border-white/20 shadow-lg h-[600px] flex flex-col">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center">
                <MessageCircle className="w-5 h-5 mr-2" />
                Общий чат
              </CardTitle>
            </CardHeader>
            
            <Separator />
            
            {/* Сообщения */}
            <CardContent className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 text-sm py-8">
                  Сообщений пока нет. Начните общение!
                </div>
              ) : (
                messages.map((msg) => (
                  <div key={msg.id} className="flex items-start space-x-3">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-sm text-gray-900">
                          {msg.player_name}
                        </span>
                        <span className="text-xs text-gray-500">
                          {gameUtils.formatTime(msg.created_at)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mt-1">
                        {msg.message}
                      </p>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </CardContent>

            <Separator />

            {/* Форма ввода сообщения */}
            <div className="p-4">
              <form onSubmit={handleSendMessage} className="flex space-x-2">
                <Input
                  type="text"
                  placeholder="Введите сообщение..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="flex-1 bg-white/70"
                  maxLength={200}
                />
                <Button 
                  type="submit" 
                  disabled={!message.trim()}
                  className="bg-blue-500 hover:bg-blue-600 text-white"
                >
                  <MessageCircle className="w-4 h-4" />
                </Button>
              </form>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default GameLobby;