import React, { useState } from "react";
import "./App.css";
import { GameProvider } from "./contexts/GameContext";
import WelcomeScreen from "./components/WelcomeScreen";
import GameLobby from "./components/GameLobby";
import { gameAPI } from "./services/gameAPI";

function App() {
  const [gameData, setGameData] = useState(null);
  const [currentPlayer, setCurrentPlayer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCreateGame = async (createData) => {
    try {
      setLoading(true);
      setError('');
      
      const response = await gameAPI.createGame(createData);
      setGameData(response);
      
      // Устанавливаем текущего игрока как хоста
      const hostPlayer = response.players.find(p => p.is_host);
      setCurrentPlayer(hostPlayer);
      
    } catch (err) {
      setError(err.message);
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
        player_name: joinData.player_name,
        password: joinData.password
      });
      
      setGameData(response);
      
      // Находим текущего игрока
      const player = response.players.find(p => p.name === joinData.player_name);
      setCurrentPlayer(player);
      
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const handleLeaveGame = () => {
    setGameData(null);
    setCurrentPlayer(null);
    setError('');
  };

  return (
    <GameProvider>
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
    </GameProvider>
  );
}

export default App;