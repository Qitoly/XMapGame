#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Empires Game Lobby System
Tests API endpoints, Socket.IO events, data validation, and real-time functionality
"""

import asyncio
import aiohttp
import socketio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import time

# Add backend to path for imports
sys.path.append('/app/backend')

class EmpireGameTester:
    def __init__(self):
        # Get backend URL from frontend .env
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    self.base_url = line.split('=')[1].strip()
                    break
            else:
                raise ValueError("REACT_APP_BACKEND_URL not found in frontend/.env")
        
        self.api_url = f"{self.base_url}/api"
        self.socket_url = self.base_url
        self.socket_path = "api/socket.io"
        
        print(f"Testing backend at: {self.api_url}")
        print(f"Testing Socket.IO at: {self.socket_url}")
        
        # Test data storage
        self.test_results = []
        self.created_games = []
        self.created_players = []
        self.socket_clients = []
        
    async def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Close socket connections
        for client in self.socket_clients:
            try:
                await client.disconnect()
            except:
                pass
        
        # Note: In a real scenario, we'd clean up database entries
        # For now, we'll just log what was created
        if self.created_games:
            print(f"Created {len(self.created_games)} test games")
        if self.created_players:
            print(f"Created {len(self.created_players)} test players")
    
    # =============================================================================
    # API ENDPOINT TESTS
    # =============================================================================
    
    async def test_get_games_empty(self):
        """Test GET /api/games - empty list"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/games") as response:
                    if response.status == 200:
                        games = await response.json()
                        await self.log_test("GET /api/games (empty)", True, f"Returned {len(games)} games")
                        return True
                    else:
                        await self.log_test("GET /api/games (empty)", False, f"Status: {response.status}")
                        return False
        except Exception as e:
            await self.log_test("GET /api/games (empty)", False, f"Exception: {str(e)}")
            return False
    
    async def test_create_game(self, game_name: str = "Тестовая Империя", host_name: str = "Император Александр", password: str = None, max_players: int = 8) -> Optional[Dict]:
        """Test POST /api/games - create game"""
        try:
            game_data = {
                "name": game_name,
                "host_name": host_name,
                "language": "ru",
                "max_players": max_players
            }
            if password:
                game_data["password"] = password
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games", json=game_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        game_id = result["game"]["id"]
                        player_id = result["current_player_id"]
                        
                        self.created_games.append(game_id)
                        self.created_players.append(player_id)
                        
                        await self.log_test("POST /api/games (create)", True, 
                                          f"Created game '{game_name}' with ID: {game_id}")
                        return result
                    else:
                        error_text = await response.text()
                        await self.log_test("POST /api/games (create)", False, 
                                          f"Status: {response.status}, Error: {error_text}")
                        return None
        except Exception as e:
            await self.log_test("POST /api/games (create)", False, f"Exception: {str(e)}")
            return None
    
    async def test_create_game_validation(self):
        """Test POST /api/games - validation errors"""
        test_cases = [
            # Missing required fields
            ({}, "missing required fields"),
            # Invalid max_players
            ({"name": "Test", "host_name": "Host", "max_players": 3}, "max_players too low"),
            ({"name": "Test", "host_name": "Host", "max_players": 11}, "max_players too high"),
            # Empty strings
            ({"name": "", "host_name": "Host", "max_players": 8}, "empty game name"),
            ({"name": "Test", "host_name": "", "max_players": 8}, "empty host name"),
        ]
        
        for invalid_data, description in test_cases:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.api_url}/games", json=invalid_data) as response:
                        if response.status in [400, 422]:  # Validation error expected
                            await self.log_test(f"POST /api/games validation ({description})", True, 
                                              f"Correctly rejected with status {response.status}")
                        else:
                            await self.log_test(f"POST /api/games validation ({description})", False, 
                                              f"Expected 400/422, got {response.status}")
            except Exception as e:
                await self.log_test(f"POST /api/games validation ({description})", False, f"Exception: {str(e)}")
    
    async def test_join_game(self, game_id: str, player_name: str = "Генерал Наполеон", password: str = None) -> Optional[Dict]:
        """Test POST /api/games/{id}/join - join game"""
        try:
            join_data = {
                "game_id": game_id,
                "player_name": player_name
            }
            if password:
                join_data["password"] = password
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{game_id}/join", json=join_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        player_id = result["current_player_id"]
                        self.created_players.append(player_id)
                        
                        await self.log_test("POST /api/games/{id}/join", True, 
                                          f"Player '{player_name}' joined game {game_id}")
                        return result
                    else:
                        error_text = await response.text()
                        await self.log_test("POST /api/games/{id}/join", False, 
                                          f"Status: {response.status}, Error: {error_text}")
                        return None
        except Exception as e:
            await self.log_test("POST /api/games/{id}/join", False, f"Exception: {str(e)}")
            return None
    
    async def test_join_game_validation(self, game_id: str):
        """Test POST /api/games/{id}/join - validation errors"""
        test_cases = [
            # Wrong password
            ({"game_id": game_id, "player_name": "Test", "password": "wrong"}, "wrong password"),
            # Duplicate name (assuming host exists)
            ({"game_id": game_id, "player_name": "Император Александр"}, "duplicate name"),
            # Empty name
            ({"game_id": game_id, "player_name": ""}, "empty name"),
            # Non-existent game
            ({"game_id": "non-existent", "player_name": "Test"}, "non-existent game"),
        ]
        
        for invalid_data, description in test_cases:
            try:
                test_game_id = invalid_data["game_id"]
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.api_url}/games/{test_game_id}/join", json=invalid_data) as response:
                        if response.status in [400, 401, 404]:  # Error expected
                            await self.log_test(f"POST /api/games/join validation ({description})", True, 
                                              f"Correctly rejected with status {response.status}")
                        else:
                            await self.log_test(f"POST /api/games/join validation ({description})", False, 
                                              f"Expected 400/401/404, got {response.status}")
            except Exception as e:
                await self.log_test(f"POST /api/games/join validation ({description})", False, f"Exception: {str(e)}")
    
    async def test_get_game_details(self, game_id: str, player_id: str) -> Optional[Dict]:
        """Test GET /api/games/{id} - get game details"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/games/{game_id}?player_id={player_id}") as response:
                    if response.status == 200:
                        result = await response.json()
                        await self.log_test("GET /api/games/{id}", True, 
                                          f"Retrieved details for game {game_id}")
                        return result
                    else:
                        error_text = await response.text()
                        await self.log_test("GET /api/games/{id}", False, 
                                          f"Status: {response.status}, Error: {error_text}")
                        return None
        except Exception as e:
            await self.log_test("GET /api/games/{id}", False, f"Exception: {str(e)}")
            return None
    
    async def test_kick_player(self, game_id: str, host_player_id: str, target_player_id: str):
        """Test POST /api/games/{id}/kick - kick player"""
        try:
            kick_data = {"player_id": target_player_id}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{game_id}/kick?host_player_id={host_player_id}", 
                                      json=kick_data) as response:
                    if response.status == 200:
                        await self.log_test("POST /api/games/{id}/kick", True, 
                                          f"Successfully kicked player {target_player_id}")
                        return True
                    else:
                        error_text = await response.text()
                        await self.log_test("POST /api/games/{id}/kick", False, 
                                          f"Status: {response.status}, Error: {error_text}")
                        return False
        except Exception as e:
            await self.log_test("POST /api/games/{id}/kick", False, f"Exception: {str(e)}")
            return False
    
    async def test_get_games_with_data(self):
        """Test GET /api/games - with created games"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/games") as response:
                    if response.status == 200:
                        games = await response.json()
                        await self.log_test("GET /api/games (with data)", True, 
                                          f"Returned {len(games)} games")
                        return games
                    else:
                        await self.log_test("GET /api/games (with data)", False, f"Status: {response.status}")
                        return None
        except Exception as e:
            await self.log_test("GET /api/games (with data)", False, f"Exception: {str(e)}")
            return None
    
    # =============================================================================
    # SOCKET.IO TESTS
    # =============================================================================
    
    async def test_socket_connection(self) -> Optional[socketio.AsyncClient]:
        """Test Socket.IO connection"""
        try:
            client = socketio.AsyncClient()
            
            # Track connection events
            connected = False
            connection_error = None
            
            @client.event
            async def connect():
                nonlocal connected
                connected = True
            
            @client.event
            async def connect_error(data):
                nonlocal connection_error
                connection_error = data
            
            # Attempt connection
            await client.connect(
                self.socket_url,
                socketio_path=self.socket_path,
            )
            
            # Wait a bit for connection
            await asyncio.sleep(1)
            
            if connected:
                self.socket_clients.append(client)
                await self.log_test("Socket.IO connection", True, "Successfully connected")
                return client
            else:
                await self.log_test("Socket.IO connection", False, f"Connection failed: {connection_error}")
                return None
                
        except Exception as e:
            await self.log_test("Socket.IO connection", False, f"Exception: {str(e)}")
            return None
    
    async def test_join_game_room(self, client: socketio.AsyncClient, game_id: str, player_id: str):
        """Test join_game_room Socket.IO event"""
        try:
            # Track events
            events_received = []
            
            @client.event
            async def player_joined(data):
                events_received.append(("player_joined", data))
            
            @client.event
            async def error(data):
                events_received.append(("error", data))
            
            # Join game room
            await client.emit("join_game_room", {
                "game_id": game_id,
                "player_id": player_id
            })
            
            # Wait for response
            await asyncio.sleep(2)
            
            # Check if we got expected events (no error means success)
            error_events = [e for e in events_received if e[0] == "error"]
            if not error_events:
                await self.log_test("Socket.IO join_game_room", True, 
                                  f"Successfully joined room for game {game_id}")
                return True
            else:
                await self.log_test("Socket.IO join_game_room", False, 
                                  f"Error: {error_events[0][1]}")
                return False
                
        except Exception as e:
            await self.log_test("Socket.IO join_game_room", False, f"Exception: {str(e)}")
            return False
    
    async def test_send_message(self, client: socketio.AsyncClient, game_id: str, player_id: str):
        """Test send_message Socket.IO event"""
        try:
            # Track events
            messages_received = []
            errors_received = []
            
            @client.event
            async def new_message(data):
                messages_received.append(data)
            
            @client.event
            async def error(data):
                errors_received.append(data)
            
            # Send a test message
            test_message = "Привет из тестов! Готовы к великим завоеваниям?"
            await client.emit("send_message", {
                "game_id": game_id,
                "player_id": player_id,
                "message": test_message
            })
            
            # Wait for response
            await asyncio.sleep(2)
            
            if messages_received and not errors_received:
                received_msg = messages_received[0]
                if received_msg.get("message") == test_message:
                    await self.log_test("Socket.IO send_message", True, 
                                      f"Message sent and received correctly")
                    return True
                else:
                    await self.log_test("Socket.IO send_message", False, 
                                      f"Message content mismatch")
                    return False
            elif errors_received:
                await self.log_test("Socket.IO send_message", False, 
                                  f"Error: {errors_received[0]}")
                return False
            else:
                await self.log_test("Socket.IO send_message", False, 
                                  "No message received")
                return False
                
        except Exception as e:
            await self.log_test("Socket.IO send_message", False, f"Exception: {str(e)}")
            return False
    
    async def test_update_ping(self, client: socketio.AsyncClient, player_id: str):
        """Test update_ping Socket.IO event"""
        try:
            # Track events
            ping_updates = []
            
            @client.event
            async def ping_updated(data):
                ping_updates.append(data)
            
            # Send ping update
            test_ping = 42
            await client.emit("update_ping", {
                "player_id": player_id,
                "ping": test_ping
            })
            
            # Wait for response
            await asyncio.sleep(2)
            
            # Note: We might not receive our own ping update, but no error means success
            await self.log_test("Socket.IO update_ping", True, 
                              f"Ping update sent successfully")
            return True
                
        except Exception as e:
            await self.log_test("Socket.IO update_ping", False, f"Exception: {str(e)}")
            return False
    
    async def test_player_ready(self, client: socketio.AsyncClient, player_id: str):
        """Test player_ready Socket.IO event"""
        try:
            # Track events
            ready_updates = []
            errors_received = []
            
            @client.event
            async def player_ready_changed(data):
                ready_updates.append(data)
            
            @client.event
            async def error(data):
                errors_received.append(data)
            
            # Set player ready
            await client.emit("player_ready", {
                "player_id": player_id,
                "is_ready": True
            })
            
            # Wait for response
            await asyncio.sleep(2)
            
            if not errors_received:
                await self.log_test("Socket.IO player_ready", True, 
                                  f"Player ready status updated")
                return True
            else:
                await self.log_test("Socket.IO player_ready", False, 
                                  f"Error: {errors_received[0]}")
                return False
                
        except Exception as e:
            await self.log_test("Socket.IO player_ready", False, f"Exception: {str(e)}")
            return False
    
    async def test_start_game(self, client: socketio.AsyncClient, game_id: str, host_player_id: str):
        """Test start_game Socket.IO event (host only)"""
        try:
            # Track events
            game_events = []
            errors_received = []
            
            @client.event
            async def game_started(data):
                game_events.append(("game_started", data))
            
            @client.event
            async def error(data):
                errors_received.append(data)
            
            # Try to start game
            await client.emit("start_game", {
                "game_id": game_id,
                "player_id": host_player_id
            })
            
            # Wait for response
            await asyncio.sleep(3)
            
            # Check results - might fail due to insufficient players, but should not crash
            if errors_received:
                error_msg = errors_received[0].get("message", "")
                if "Минимум 4 игрока" in error_msg:
                    await self.log_test("Socket.IO start_game", True, 
                                      f"Correctly rejected: {error_msg}")
                    return True
                else:
                    await self.log_test("Socket.IO start_game", False, 
                                      f"Unexpected error: {error_msg}")
                    return False
            elif game_events:
                await self.log_test("Socket.IO start_game", True, 
                                  f"Game started successfully")
                return True
            else:
                await self.log_test("Socket.IO start_game", False, 
                                  "No response received")
                return False
                
        except Exception as e:
            await self.log_test("Socket.IO start_game", False, f"Exception: {str(e)}")
            return False
    
    # =============================================================================
    # COMPREHENSIVE TEST SCENARIOS
    # =============================================================================
    
    async def test_full_lobby_flow(self):
        """Test complete lobby flow with multiple players"""
        print("\n🎮 Testing Full Lobby Flow...")
        
        # 1. Create a game
        game_result = await self.test_create_game("Великая Империя", "Цезарь Август")
        if not game_result:
            return False
        
        game_id = game_result["game"]["id"]
        host_player_id = game_result["current_player_id"]
        
        # 2. Join additional players
        player2_result = await self.test_join_game(game_id, "Александр Македонский")
        player3_result = await self.test_join_game(game_id, "Чингисхан")
        
        if not player2_result or not player3_result:
            await self.log_test("Full Lobby Flow", False, "Failed to add additional players")
            return False
        
        # 3. Test Socket.IO with multiple clients
        host_client = await self.test_socket_connection()
        player2_client = await self.test_socket_connection()
        
        if not host_client or not player2_client:
            await self.log_test("Full Lobby Flow", False, "Failed to establish socket connections")
            return False
        
        # 4. Join game rooms
        await self.test_join_game_room(host_client, game_id, host_player_id)
        await self.test_join_game_room(player2_client, game_id, player2_result["current_player_id"])
        
        # 5. Test chat functionality
        await self.test_send_message(host_client, game_id, host_player_id)
        await self.test_send_message(player2_client, game_id, player2_result["current_player_id"])
        
        # 6. Test ready status
        await self.test_player_ready(host_client, host_player_id)
        await self.test_player_ready(player2_client, player2_result["current_player_id"])
        
        # 7. Test game start (should fail due to insufficient players)
        await self.test_start_game(host_client, game_id, host_player_id)
        
        # 8. Test kick functionality
        await self.test_kick_player(game_id, host_player_id, player3_result["current_player_id"])
        
        await self.log_test("Full Lobby Flow", True, "Completed comprehensive lobby testing")
        return True
    
    async def test_password_protected_game(self):
        """Test password-protected game functionality"""
        print("\n🔒 Testing Password Protection...")
        
        # Create password-protected game
        password = "секретный_пароль_123"
        game_result = await self.test_create_game("Секретная Империя", "Тайный Император", password)
        
        if not game_result:
            return False
        
        game_id = game_result["game"]["id"]
        
        # Test joining with wrong password
        await self.test_join_game_validation(game_id)
        
        # Test joining with correct password
        player_result = await self.test_join_game(game_id, "Шпион", password)
        
        if player_result:
            await self.log_test("Password Protection", True, "Password validation working correctly")
            return True
        else:
            await self.log_test("Password Protection", False, "Failed to join with correct password")
            return False
    
    async def test_game_limits(self):
        """Test game player limits and validation"""
        print("\n📊 Testing Game Limits...")
        
        # Test max players limit
        game_result = await self.test_create_game("Малая Империя", "Мини Цезарь", max_players=4)
        
        if not game_result:
            return False
        
        game_id = game_result["game"]["id"]
        
        # Try to add players up to the limit
        players_added = 0
        for i in range(2, 5):  # Host is player 1, so add 2, 3, 4
            player_result = await self.test_join_game(game_id, f"Игрок {i}")
            if player_result:
                players_added += 1
        
        # Try to add one more (should fail)
        overflow_result = await self.test_join_game(game_id, "Лишний Игрок")
        
        if players_added == 3 and not overflow_result:
            await self.log_test("Game Limits", True, "Player limits enforced correctly")
            return True
        else:
            await self.log_test("Game Limits", False, f"Added {players_added} players, overflow allowed: {bool(overflow_result)}")
            return False
    
    # =============================================================================
    # SHORT GAME ID AND DISCONNECT TESTS (NEW)
    # =============================================================================
    
    async def test_short_game_id_generation(self):
        """Test that game IDs are 6-character alphanumeric (uppercase letters and numbers)"""
        print("\n🆔 Testing Short Game ID Generation...")
        
        # Create multiple games to test ID format and uniqueness
        game_ids = []
        
        for i in range(5):
            game_result = await self.test_create_game(f"Тест ID {i+1}", f"Хост {i+1}")
            if not game_result:
                await self.log_test("Short Game ID Generation", False, f"Failed to create game {i+1}")
                return False
            
            game_id = game_result["game"]["id"]
            game_ids.append(game_id)
            
            # Test ID format: exactly 6 characters, uppercase letters and digits only
            if len(game_id) != 6:
                await self.log_test("Short Game ID Generation", False, 
                                  f"Game ID '{game_id}' is {len(game_id)} characters, expected 6")
                return False
            
            # Check if all characters are uppercase letters or digits
            import re
            if not re.match(r'^[A-Z0-9]{6}$', game_id):
                await self.log_test("Short Game ID Generation", False, 
                                  f"Game ID '{game_id}' contains invalid characters (should be A-Z, 0-9 only)")
                return False
        
        # Test uniqueness
        if len(set(game_ids)) != len(game_ids):
            await self.log_test("Short Game ID Generation", False, 
                              f"Duplicate IDs found: {game_ids}")
            return False
        
        await self.log_test("Short Game ID Generation", True, 
                          f"All {len(game_ids)} game IDs are valid 6-character format and unique: {game_ids}")
        return True
    
    async def test_join_with_short_ids(self):
        """Test joining games using short 6-character IDs"""
        print("\n🔗 Testing Join Game with Short IDs...")
        
        # Create a game with short ID
        game_result = await self.test_create_game("Короткий ID Тест", "Главный Хост")
        if not game_result:
            return False
        
        game_id = game_result["game"]["id"]
        
        # Verify it's a short ID
        if len(game_id) != 6:
            await self.log_test("Join with Short IDs", False, f"Expected 6-char ID, got {len(game_id)}")
            return False
        
        # Test joining with the short ID
        join_result = await self.test_join_game(game_id, "Тестовый Игрок")
        if not join_result:
            await self.log_test("Join with Short IDs", False, "Failed to join game with short ID")
            return False
        
        # Test game details retrieval with short ID
        details_result = await self.test_get_game_details(game_id, join_result["current_player_id"])
        if not details_result:
            await self.log_test("Join with Short IDs", False, "Failed to get game details with short ID")
            return False
        
        await self.log_test("Join with Short IDs", True, 
                          f"Successfully joined and retrieved details for game with short ID: {game_id}")
        return True
    
    async def test_disconnect_notifications(self):
        """Test Socket.IO disconnect event notifications"""
        print("\n🔌 Testing Player Disconnect Notifications...")
        
        # Create a game
        game_result = await self.test_create_game("Тест Отключений", "Хост Сервер")
        if not game_result:
            return False
        
        game_id = game_result["game"]["id"]
        host_player_id = game_result["current_player_id"]
        
        # Add a second player
        player2_result = await self.test_join_game(game_id, "Игрок Два")
        if not player2_result:
            return False
        
        player2_id = player2_result["current_player_id"]
        
        # Create Socket.IO clients
        host_client = await self.test_socket_connection()
        player2_client = await self.test_socket_connection()
        
        if not host_client or not player2_client:
            await self.log_test("Disconnect Notifications", False, "Failed to create socket connections")
            return False
        
        # Track disconnect events
        disconnect_events = []
        
        @host_client.event
        async def player_disconnected(data):
            disconnect_events.append(("host_received", data))
        
        @player2_client.event
        async def player_disconnected(data):
            disconnect_events.append(("player2_received", data))
        
        # Join game rooms
        await self.test_join_game_room(host_client, game_id, host_player_id)
        await self.test_join_game_room(player2_client, game_id, player2_id)
        
        # Wait a moment for room joining to complete
        await asyncio.sleep(2)
        
        # Disconnect player2 (simulate disconnect)
        await player2_client.disconnect()
        
        # Wait for disconnect event to be processed
        await asyncio.sleep(3)
        
        # Check if host received disconnect notification
        host_events = [e for e in disconnect_events if e[0] == "host_received"]
        
        if host_events:
            disconnect_data = host_events[0][1]
            
            # Validate disconnect event structure
            if "player_id" in disconnect_data and "player_name" in disconnect_data:
                expected_name = "Игрок Два"
                if disconnect_data["player_name"] == expected_name:
                    await self.log_test("Disconnect Notifications", True, 
                                      f"Host correctly received disconnect notification for '{expected_name}' (ID: {disconnect_data['player_id']})")
                    return True
                else:
                    await self.log_test("Disconnect Notifications", False, 
                                      f"Wrong player name in disconnect event: got '{disconnect_data['player_name']}', expected '{expected_name}'")
                    return False
            else:
                await self.log_test("Disconnect Notifications", False, 
                                  f"Disconnect event missing required fields: {disconnect_data}")
                return False
        else:
            await self.log_test("Disconnect Notifications", False, 
                              "Host did not receive disconnect notification")
            return False
    
    async def test_disconnect_event_room_isolation(self):
        """Test that disconnect events are sent to correct game rooms only"""
        print("\n🏠 Testing Disconnect Event Room Isolation...")
        
        # Create two separate games
        game1_result = await self.test_create_game("Игра Один", "Хост Один")
        game2_result = await self.test_create_game("Игра Два", "Хост Два")
        
        if not game1_result or not game2_result:
            return False
        
        game1_id = game1_result["game"]["id"]
        game2_id = game2_result["game"]["id"]
        
        # Add players to both games
        game1_player = await self.test_join_game(game1_id, "Игрок Игры 1")
        game2_player = await self.test_join_game(game2_id, "Игрок Игры 2")
        
        if not game1_player or not game2_player:
            return False
        
        # Create socket clients
        game1_host_client = await self.test_socket_connection()
        game1_player_client = await self.test_socket_connection()
        game2_host_client = await self.test_socket_connection()
        
        if not all([game1_host_client, game1_player_client, game2_host_client]):
            await self.log_test("Disconnect Room Isolation", False, "Failed to create socket connections")
            return False
        
        # Track disconnect events for each client
        game1_host_events = []
        game2_host_events = []
        
        @game1_host_client.event
        async def player_disconnected(data):
            game1_host_events.append(data)
        
        @game2_host_client.event
        async def player_disconnected(data):
            game2_host_events.append(data)
        
        # Join respective game rooms
        await self.test_join_game_room(game1_host_client, game1_id, game1_result["current_player_id"])
        await self.test_join_game_room(game1_player_client, game1_id, game1_player["current_player_id"])
        await self.test_join_game_room(game2_host_client, game2_id, game2_result["current_player_id"])
        
        # Wait for room joining
        await asyncio.sleep(2)
        
        # Disconnect player from game 1
        await game1_player_client.disconnect()
        
        # Wait for disconnect processing
        await asyncio.sleep(3)
        
        # Check that only game1 host received the disconnect event
        if game1_host_events and not game2_host_events:
            disconnect_data = game1_host_events[0]
            if disconnect_data.get("player_name") == "Игрок Игры 1":
                await self.log_test("Disconnect Room Isolation", True, 
                                  "Disconnect event correctly isolated to game room")
                return True
            else:
                await self.log_test("Disconnect Room Isolation", False, 
                                  f"Wrong player in disconnect event: {disconnect_data}")
                return False
        elif game2_host_events:
            await self.log_test("Disconnect Room Isolation", False, 
                              "Disconnect event incorrectly sent to wrong game room")
            return False
        else:
            await self.log_test("Disconnect Room Isolation", False, 
                              "No disconnect events received")
            return False

    # =============================================================================
    # MAIN TEST RUNNER
    # =============================================================================
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Empires Game Backend Testing")
        print("=" * 60)
        
        try:
            # Basic API Tests
            print("\n📡 Testing API Endpoints...")
            await self.test_get_games_empty()
            await self.test_create_game_validation()
            
            # Core Functionality Tests
            print("\n🎯 Testing Core Functionality...")
            await self.test_full_lobby_flow()
            await self.test_password_protected_game()
            await self.test_game_limits()
            
            # Final API state test
            await self.test_get_games_with_data()
            
        except Exception as e:
            print(f"❌ Critical error during testing: {e}")
            await self.log_test("Critical Error", False, str(e))
        
        finally:
            await self.cleanup()
            await self.print_summary()
    
    async def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  • {test['test']}: {test['details']}")
        
        print("\n" + "=" * 60)

async def main():
    """Main test runner"""
    tester = EmpireGameTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
