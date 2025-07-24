import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Users, GameController2, Globe } from 'lucide-react';

function WelcomeScreen({ onCreateGame, onJoinGame }) {
  const [playerName, setPlayerName] = useState('');
  const [mode, setMode] = useState('menu'); // 'menu', 'create', 'join'
  const [gameData, setGameData] = useState({
    name: '',
    password: '',
    language: 'ru',
    max_players: 8
  });
  const [joinData, setJoinData] = useState({
    game_id: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCreateGame = async () => {
    if (!playerName.trim() || !gameData.name.trim()) {
      setError('Пожалуйста, заполните все обязательные поля');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await onCreateGame({
        name: gameData.name,
        host_name: playerName,
        password: gameData.password || null,
        language: gameData.language,
        max_players: gameData.max_players
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleJoinGame = async () => {
    if (!playerName.trim() || !joinData.game_id.trim()) {
      setError('Пожалуйста, заполните все обязательные поля');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await onJoinGame({
        game_id: joinData.game_id,
        player_name: playerName,
        password: joinData.password || null
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const resetToMenu = () => {
    setMode('menu');
    setError('');
    setGameData({ name: '', password: '', language: 'ru', max_players: 8 });
    setJoinData({ game_id: '', password: '' });
  };

  if (mode === 'menu') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
        <div className="w-full max-w-md space-y-6">
          {/* Заголовок */}
          <div className="text-center space-y-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl text-white text-2xl font-bold">
              🏛️
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-blue-800 bg-clip-text text-transparent">
                Империи
              </h1>
              <p className="text-gray-600 mt-2">
                Стратегическая игра на 4-10 игроков
              </p>
            </div>
          </div>

          {/* Форма ввода имени */}
          <Card className="bg-white/80 backdrop-blur-sm border-white/20 shadow-xl">
            <CardHeader>
              <CardTitle className="text-center text-gray-800">
                Добро пожаловать!
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="playerName">Ваше имя</Label>
                <Input
                  id="playerName"
                  type="text"
                  placeholder="Введите ваше имя"
                  value={playerName}
                  onChange={(e) => setPlayerName(e.target.value)}
                  className="bg-white/70"
                  maxLength={20}
                />
              </div>

              {error && (
                <div className="text-red-600 text-sm text-center bg-red-50 p-2 rounded">
                  {error}
                </div>
              )}

              <div className="grid grid-cols-1 gap-3">
                <Button
                  onClick={() => setMode('create')}
                  disabled={!playerName.trim() || loading}
                  className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white"
                >
                  <GameController2 className="w-4 h-4 mr-2" />
                  Создать игру
                </Button>
                
                <Button
                  onClick={() => setMode('join')}
                  disabled={!playerName.trim() || loading}
                  variant="outline"
                  className="border-blue-200 hover:bg-blue-50"
                >
                  <Users className="w-4 h-4 mr-2" />
                  Присоединиться к игре
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Информация об игре */}
          <div className="text-center text-sm text-gray-500 space-y-1">
            <p>• Время партии: 15-30 минут</p>
            <p>• Игроков: 4-10 человек</p>
            <p>• Стратегия + дипломатия</p>
          </div>
        </div>
      </div>
    );
  }

  if (mode === 'create') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <Card className="bg-white/80 backdrop-blur-sm border-white/20 shadow-xl">
            <CardHeader>
              <CardTitle className="text-center text-gray-800 flex items-center justify-center">
                <GameController2 className="w-5 h-5 mr-2" />
                Создать новую игру
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="gameName">Название игры *</Label>
                <Input
                  id="gameName"
                  type="text"
                  placeholder="Название вашей игры"
                  value={gameData.name}
                  onChange={(e) => setGameData({ ...gameData, name: e.target.value })}
                  className="bg-white/70"
                  maxLength={50}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="gamePassword">Пароль (необязательно)</Label>
                <Input
                  id="gamePassword"
                  type="password"
                  placeholder="Оставьте пустым для открытой игры"
                  value={gameData.password}
                  onChange={(e) => setGameData({ ...gameData, password: e.target.value })}
                  className="bg-white/70"
                  maxLength={20}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="language">Язык</Label>
                  <select
                    id="language"
                    value={gameData.language}
                    onChange={(e) => setGameData({ ...gameData, language: e.target.value })}
                    className="w-full px-3 py-2 bg-white/70 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="ru">🇷🇺 Русский</option>
                    <option value="en">🇺🇸 English</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="maxPlayers">Макс. игроков</Label>
                  <select
                    id="maxPlayers"
                    value={gameData.max_players}
                    onChange={(e) => setGameData({ ...gameData, max_players: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-white/70 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {[4, 5, 6, 7, 8, 9, 10].map(num => (
                      <option key={num} value={num}>{num}</option>
                    ))}
                  </select>
                </div>
              </div>

              {error && (
                <div className="text-red-600 text-sm text-center bg-red-50 p-2 rounded">
                  {error}
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <Button
                  onClick={resetToMenu}
                  variant="outline"
                  disabled={loading}
                >
                  Назад
                </Button>
                <Button
                  onClick={handleCreateGame}
                  disabled={loading || !gameData.name.trim()}
                  className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white"
                >
                  {loading ? 'Создание...' : 'Создать'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (mode === 'join') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <Card className="bg-white/80 backdrop-blur-sm border-white/20 shadow-xl">
            <CardHeader>
              <CardTitle className="text-center text-gray-800 flex items-center justify-center">
                <Users className="w-5 h-5 mr-2" />
                Присоединиться к игре
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="gameId">ID игры *</Label>
                <Input
                  id="gameId"
                  type="text"
                  placeholder="Введите ID игры"
                  value={joinData.game_id}
                  onChange={(e) => setJoinData({ ...joinData, game_id: e.target.value })}
                  className="bg-white/70"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="joinPassword">Пароль (если требуется)</Label>
                <Input
                  id="joinPassword"
                  type="password"
                  placeholder="Пароль игры"
                  value={joinData.password}
                  onChange={(e) => setJoinData({ ...joinData, password: e.target.value })}
                  className="bg-white/70"
                />
              </div>

              {error && (
                <div className="text-red-600 text-sm text-center bg-red-50 p-2 rounded">
                  {error}
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <Button
                  onClick={resetToMenu}
                  variant="outline"
                  disabled={loading}
                >
                  Назад
                </Button>
                <Button
                  onClick={handleJoinGame}
                  disabled={loading || !joinData.game_id.trim()}
                  className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white"
                >
                  {loading ? 'Подключение...' : 'Присоединиться'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return null;
}

export default WelcomeScreen;