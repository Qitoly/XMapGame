import React, { useState } from "react";
import "./App.css";
import { GameProvider, useGame } from "./contexts/GameContext";
import WelcomeScreen from "./components/WelcomeScreen";
import GameLobby from "./components/GameLobby";
import { gameAPI } from "./services/gameAPI";

// Внутренний компонент приложения, который имеет доступ к GameContext
function AppContent() {
  const [gameData, setGameData] = useState(null);
  const [currentPlayer, setCurrentPlayer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { setGameData: setContextGameData, setCurrentPlayer: setContextCurrentPlayer, setPlayers } = useGame();

  const handleCreateGame = async (createData) => {
    try {
      setLoading(true);
      setError('');
      
      const response = await gameAPI.createGame(createData);
      setGameData(response);
      
      // Устанавливаем текущего игрока как хоста
      const hostPlayer = response.players.find(p => p.is_host);
      setCurrentPlayer(hostPlayer);
      
      // Передаем данные в контекст
      setContextGameData(response);
      setContextCurrentPlayer(hostPlayer);
      setPlayers(response.players);
      
    } catch (err) {
      setError(err.message || err.toString() || 'Ошибка создания игры');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const handleJoinGame = async (joinData) => {
    try {
      setLoading(true);
      setError('');
      
      const response = await gameAPI.joinGame(joinData.game_id, {
        game_id: joinData.game_id,
        player_name: joinData.player_name,
        password: joinData.password
      });
      
      setGameData(response);
      
      // Находим текущего игрока
      const player = response.players.find(p => p.name === joinData.player_name);
      setCurrentPlayer(player);
      
      // Передаем данные в контекст
      setContextGameData(response);
      setContextCurrentPlayer(player);
      setPlayers(response.players);
      
    } catch (err) {
      setError(err.message || err.toString() || 'Ошибка присоединения к игре');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const handleLeaveGame = () => {
    setGameData(null);
    setCurrentPlayer(null);
    setError('');
    
    // Очищаем контекст
    setContextGameData(null);
    setContextCurrentPlayer(null);
    setPlayers([]);
  };

  return (
    <div className="App">
      {!gameData ? (
        <WelcomeScreen 
          onCreateGame={handleCreateGame}
          onJoinGame={handleJoinGame}
        />
      ) : (
        <GameLobby 
          gameData={gameData}
          onLeaveGame={handleLeaveGame}
        />
      )}
      
      {error && (
        <div className="fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50">
          {error}
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <GameProvider>
      <AppContent />
    </GameProvider>
  );
}

export default App;