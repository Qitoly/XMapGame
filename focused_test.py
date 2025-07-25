#!/usr/bin/env python3
"""
Focused test for Short Game ID Generation and Disconnect Events
"""

import asyncio
import aiohttp
import socketio
import json
import os
import sys
from datetime import datetime
import re

# Add backend to path for imports
sys.path.append('/app/backend')

class FocusedTester:
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
        
        self.socket_clients = []
        
    async def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    async def cleanup(self):
        """Clean up test data"""
        for client in self.socket_clients:
            try:
                await client.disconnect()
            except:
                pass
    
    async def create_game(self, game_name: str, host_name: str):
        """Create a game and return result"""
        try:
            game_data = {
                "name": game_name,
                "host_name": host_name,
                "language": "ru",
                "max_players": 8
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games", json=game_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        return None
        except Exception as e:
            print(f"Error creating game: {e}")
            return None
    
    async def join_game(self, game_id: str, player_name: str):
        """Join a game and return result"""
        try:
            join_data = {
                "game_id": game_id,
                "player_name": player_name
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{game_id}/join", json=join_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        return None
        except Exception as e:
            print(f"Error joining game: {e}")
            return None
    
    async def test_short_game_ids(self):
        """Test short game ID generation"""
        print("\n🆔 TESTING SHORT GAME ID GENERATION")
        print("=" * 50)
        
        game_ids = []
        
        # Create 10 games to test ID format and uniqueness
        for i in range(10):
            game_result = await self.create_game(f"Test Game {i+1}", f"Host {i+1}")
            if not game_result:
                await self.log_test(f"Create Game {i+1}", False, "Failed to create game")
                return False
            
            game_id = game_result["game"]["id"]
            game_ids.append(game_id)
            
            # Test ID format: exactly 6 characters, uppercase letters and digits only
            if len(game_id) != 6:
                await self.log_test("Game ID Length", False, f"ID '{game_id}' is {len(game_id)} chars, expected 6")
                return False
            
            # Check if all characters are uppercase letters or digits
            if not re.match(r'^[A-Z0-9]{6}$', game_id):
                await self.log_test("Game ID Format", False, f"ID '{game_id}' has invalid chars (should be A-Z, 0-9)")
                return False
        
        # Test uniqueness
        unique_ids = set(game_ids)
        if len(unique_ids) != len(game_ids):
            duplicates = [id for id in game_ids if game_ids.count(id) > 1]
            await self.log_test("Game ID Uniqueness", False, f"Duplicate IDs found: {duplicates}")
            return False
        
        await self.log_test("Short Game ID Generation", True, 
                          f"All {len(game_ids)} IDs are valid 6-char format and unique")
        print(f"Generated IDs: {game_ids}")
        
        # Test joining with short IDs
        test_game_id = game_ids[0]
        join_result = await self.join_game(test_game_id, "Test Player")
        if join_result:
            await self.log_test("Join with Short ID", True, f"Successfully joined game {test_game_id}")
        else:
            await self.log_test("Join with Short ID", False, f"Failed to join game {test_game_id}")
            return False
        
        return True
    
    async def test_disconnect_events(self):
        """Test disconnect event notifications"""
        print("\n🔌 TESTING DISCONNECT EVENT NOTIFICATIONS")
        print("=" * 50)
        
        # Create a game
        game_result = await self.create_game("Disconnect Test Game", "Host Player")
        if not game_result:
            await self.log_test("Create Test Game", False, "Failed to create game")
            return False
        
        game_id = game_result["game"]["id"]
        host_player_id = game_result["current_player_id"]
        
        # Add a second player
        player2_result = await self.join_game(game_id, "Player Two")
        if not player2_result:
            await self.log_test("Add Second Player", False, "Failed to add second player")
            return False
        
        player2_id = player2_result["current_player_id"]
        
        # Create Socket.IO clients
        try:
            host_client = socketio.AsyncClient()
            player2_client = socketio.AsyncClient()
            
            # Track events
            disconnect_events = []
            connection_errors = []
            
            @host_client.event
            async def connect():
                print("Host client connected")
            
            @host_client.event
            async def player_disconnected(data):
                print(f"Host received disconnect event: {data}")
                disconnect_events.append(("host", data))
            
            @host_client.event
            async def error(data):
                print(f"Host client error: {data}")
                connection_errors.append(("host", data))
            
            @player2_client.event
            async def connect():
                print("Player2 client connected")
            
            @player2_client.event
            async def error(data):
                print(f"Player2 client error: {data}")
                connection_errors.append(("player2", data))
            
            # Connect clients
            await host_client.connect(self.socket_url, socketio_path=self.socket_path)
            await player2_client.connect(self.socket_url, socketio_path=self.socket_path)
            
            self.socket_clients.extend([host_client, player2_client])
            
            # Wait for connections
            await asyncio.sleep(2)
            
            # Join game rooms
            print("Joining game rooms...")
            await host_client.emit("join_game_room", {
                "game_id": game_id,
                "player_id": host_player_id
            })
            
            await player2_client.emit("join_game_room", {
                "game_id": game_id,
                "player_id": player2_id
            })
            
            # Wait for room joining
            await asyncio.sleep(3)
            
            if connection_errors:
                await self.log_test("Socket.IO Room Joining", False, f"Errors: {connection_errors}")
                return False
            
            # Disconnect player2 to trigger disconnect event
            print("Disconnecting player2...")
            await player2_client.disconnect()
            
            # Wait for disconnect event processing
            await asyncio.sleep(5)
            
            # Check if host received disconnect notification
            if disconnect_events:
                disconnect_data = disconnect_events[0][1]
                
                # Validate event structure
                if "player_id" in disconnect_data and "player_name" in disconnect_data:
                    if disconnect_data["player_name"] == "Player Two":
                        await self.log_test("Disconnect Event Structure", True, 
                                          f"Correct event: {disconnect_data}")
                        await self.log_test("Disconnect Notifications", True, 
                                          "Host correctly received disconnect notification")
                        return True
                    else:
                        await self.log_test("Disconnect Event Content", False, 
                                          f"Wrong player name: {disconnect_data['player_name']}")
                        return False
                else:
                    await self.log_test("Disconnect Event Structure", False, 
                                      f"Missing fields in event: {disconnect_data}")
                    return False
            else:
                await self.log_test("Disconnect Notifications", False, 
                                  "Host did not receive disconnect notification")
                return False
                
        except Exception as e:
            await self.log_test("Disconnect Test Setup", False, f"Exception: {e}")
            return False
    
    async def run_focused_tests(self):
        """Run focused tests"""
        print("🎯 FOCUSED TESTING: Short Game IDs & Disconnect Events")
        print("=" * 60)
        
        try:
            # Test short game ID generation
            id_test_result = await self.test_short_game_ids()
            
            # Test disconnect events
            disconnect_test_result = await self.test_disconnect_events()
            
            # Summary
            print("\n" + "=" * 60)
            print("📊 FOCUSED TEST SUMMARY")
            print("=" * 60)
            
            if id_test_result:
                print("✅ Short Game ID Generation: WORKING")
            else:
                print("❌ Short Game ID Generation: FAILED")
            
            if disconnect_test_result:
                print("✅ Disconnect Event Notifications: WORKING")
            else:
                print("❌ Disconnect Event Notifications: FAILED")
            
        except Exception as e:
            print(f"❌ Critical error during testing: {e}")
        
        finally:
            await self.cleanup()

async def main():
    """Main test runner"""
    tester = FocusedTester()
    await tester.run_focused_tests()

if __name__ == "__main__":
    asyncio.run(main())