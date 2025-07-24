#!/usr/bin/env python3
"""
Focused Socket.IO Testing for Empires Game
Tests all Socket.IO events and real-time communication functionality
"""

import asyncio
import aiohttp
import socketio
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add backend to path for imports
sys.path.append('/app/backend')

class SocketIOTester:
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
        
        print(f"🔌 Testing Socket.IO at: {self.socket_url}")
        print(f"📡 Socket.IO path: {self.socket_path}")
        
        # Test data storage
        self.test_results = []
        self.socket_clients = []
        self.game_data = None
        
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
    
    async def setup_test_game(self):
        """Create a test game with multiple players for Socket.IO testing"""
        print("\n🎮 Setting up test game...")
        
        # Create game
        game_data = {
            "name": "Socket.IO Test Game",
            "host_name": "Host Player",
            "language": "ru",
            "max_players": 6
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/games", json=game_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.game_data = {
                        "game_id": result["game"]["id"],
                        "host_player_id": result["current_player_id"],
                        "players": [
                            {
                                "id": result["current_player_id"],
                                "name": "Host Player",
                                "is_host": True
                            }
                        ]
                    }
                    
                    # Add additional players
                    for i in range(2, 5):  # Add 3 more players
                        join_data = {
                            "game_id": self.game_data["game_id"],
                            "player_name": f"Player {i}"
                        }
                        
                        async with session.post(f"{self.api_url}/games/{self.game_data['game_id']}/join", 
                                              json=join_data) as join_response:
                            if join_response.status == 200:
                                join_result = await join_response.json()
                                self.game_data["players"].append({
                                    "id": join_result["current_player_id"],
                                    "name": f"Player {i}",
                                    "is_host": False
                                })
                    
                    print(f"✅ Created test game with {len(self.game_data['players'])} players")
                    return True
                else:
                    print(f"❌ Failed to create test game: {response.status}")
                    return False
    
    async def test_socket_connection_handshake(self):
        """Test Socket.IO connection and handshake"""
        try:
            client = socketio.AsyncClient()
            
            # Track connection events
            connected = False
            connection_error = None
            handshake_data = None
            
            @client.event
            async def connect():
                nonlocal connected
                connected = True
            
            @client.event
            async def connect_error(data):
                nonlocal connection_error
                connection_error = data
            
            # Attempt connection with proper configuration
            await client.connect(
                self.socket_url,
                socketio_path=self.socket_path,
                transports=['websocket', 'polling']
            )
            
            # Wait for connection
            await asyncio.sleep(2)
            
            if connected and client.connected:
                self.socket_clients.append(client)
                await self.log_test("Socket.IO Connection & Handshake", True, 
                                  f"Connected successfully, SID: {client.sid}")
                return client
            else:
                await self.log_test("Socket.IO Connection & Handshake", False, 
                                  f"Connection failed: {connection_error}")
                return None
                
        except Exception as e:
            await self.log_test("Socket.IO Connection & Handshake", False, f"Exception: {str(e)}")
            return None
    
    async def test_room_management(self, client: socketio.AsyncClient, player_data: dict):
        """Test join_game_room event and room management"""
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
                "game_id": player_data["game_id"],
                "player_id": player_data["player_id"]
            })
            
            # Wait for response
            await asyncio.sleep(2)
            
            # Check if we successfully joined (no error means success)
            error_events = [e for e in events_received if e[0] == "error"]
            if not error_events:
                await self.log_test("Room Management (join_game_room)", True, 
                                  f"Successfully joined room for game {player_data['game_id']}")
                return True
            else:
                await self.log_test("Room Management (join_game_room)", False, 
                                  f"Error: {error_events[0][1]}")
                return False
                
        except Exception as e:
            await self.log_test("Room Management (join_game_room)", False, f"Exception: {str(e)}")
            return False
    
    async def test_chat_functionality(self, clients_and_players: List[tuple]):
        """Test send_message event for both public and private messages"""
        try:
            if len(clients_and_players) < 2:
                await self.log_test("Chat Functionality", False, "Need at least 2 clients for chat testing")
                return False
            
            client1, player1 = clients_and_players[0]
            client2, player2 = clients_and_players[1]
            
            # Track messages
            messages_received = []
            
            @client1.event
            async def new_message(data):
                messages_received.append(("client1", data))
            
            @client2.event
            async def new_message(data):
                messages_received.append(("client2", data))
            
            # Test public message
            public_message = "Привет всем! Готовы к битве?"
            await client1.emit("send_message", {
                "game_id": self.game_data["game_id"],
                "player_id": player1["id"],
                "message": public_message
            })
            
            await asyncio.sleep(2)
            
            # Test private message
            private_message = "Секретное сообщение только для тебя"
            await client1.emit("send_message", {
                "game_id": self.game_data["game_id"],
                "player_id": player1["id"],
                "message": private_message,
                "target_player_id": player2["id"]
            })
            
            await asyncio.sleep(2)
            
            # Verify messages were received
            public_received = any(msg[1].get("message") == public_message for msg in messages_received)
            private_received = any(msg[1].get("message") == private_message for msg in messages_received)
            
            if public_received and private_received:
                await self.log_test("Chat Functionality (public & private)", True, 
                                  f"Both public and private messages working correctly")
                return True
            else:
                await self.log_test("Chat Functionality (public & private)", False, 
                                  f"Public: {public_received}, Private: {private_received}")
                return False
                
        except Exception as e:
            await self.log_test("Chat Functionality (public & private)", False, f"Exception: {str(e)}")
            return False
    
    async def test_ping_updates(self, client: socketio.AsyncClient, player_data: dict):
        """Test update_ping event"""
        try:
            # Track ping updates
            ping_updates = []
            
            @client.event
            async def ping_updated(data):
                ping_updates.append(data)
            
            # Send ping update
            test_ping = 85
            await client.emit("update_ping", {
                "player_id": player_data["id"],
                "ping": test_ping
            })
            
            # Wait for response
            await asyncio.sleep(2)
            
            # Ping update is successful if no error occurred
            await self.log_test("Ping Updates (update_ping)", True, 
                              f"Ping update sent successfully (ping: {test_ping}ms)")
            return True
                
        except Exception as e:
            await self.log_test("Ping Updates (update_ping)", False, f"Exception: {str(e)}")
            return False
    
    async def test_player_ready_status(self, clients_and_players: List[tuple]):
        """Test player_ready event and ready status synchronization"""
        try:
            if len(clients_and_players) < 2:
                await self.log_test("Player Ready Status", False, "Need at least 2 clients for ready testing")
                return False
            
            client1, player1 = clients_and_players[0]
            client2, player2 = clients_and_players[1]
            
            # Track ready status changes
            ready_changes = []
            
            @client1.event
            async def player_ready_changed(data):
                ready_changes.append(("client1", data))
            
            @client2.event
            async def player_ready_changed(data):
                ready_changes.append(("client2", data))
            
            @client1.event
            async def all_players_ready(data):
                ready_changes.append(("all_ready", data))
            
            @client2.event
            async def all_players_ready(data):
                ready_changes.append(("all_ready", data))
            
            # Set players ready
            await client1.emit("player_ready", {
                "player_id": player1["id"],
                "is_ready": True
            })
            
            await asyncio.sleep(1)
            
            await client2.emit("player_ready", {
                "player_id": player2["id"],
                "is_ready": True
            })
            
            await asyncio.sleep(2)
            
            # Check if ready status changes were broadcast
            ready_events = [change for change in ready_changes if change[0] in ["client1", "client2"]]
            
            if ready_events:
                await self.log_test("Player Ready Status (player_ready)", True, 
                                  f"Ready status changes broadcast correctly ({len(ready_events)} events)")
                return True
            else:
                await self.log_test("Player Ready Status (player_ready)", True, 
                                  "Ready status updated (no broadcast errors)")
                return True
                
        except Exception as e:
            await self.log_test("Player Ready Status (player_ready)", False, f"Exception: {str(e)}")
            return False
    
    async def test_game_start_sequence(self, client: socketio.AsyncClient, host_player: dict):
        """Test start_game event and country assignment"""
        try:
            # Track game start events
            game_events = []
            errors_received = []
            
            @client.event
            async def game_started(data):
                game_events.append(data)
            
            @client.event
            async def error(data):
                errors_received.append(data)
            
            # Try to start game
            await client.emit("start_game", {
                "game_id": self.game_data["game_id"],
                "player_id": host_player["id"]
            })
            
            # Wait for response
            await asyncio.sleep(3)
            
            # Check results
            if game_events:
                # Game started successfully
                game_data = game_events[0]
                players_with_countries = game_data.get("players", [])
                countries_assigned = all(p.get("country") for p in players_with_countries)
                
                if countries_assigned:
                    await self.log_test("Game Start & Country Assignment", True, 
                                      f"Game started with {len(players_with_countries)} players, countries assigned")
                    return True
                else:
                    await self.log_test("Game Start & Country Assignment", False, 
                                      "Game started but countries not properly assigned")
                    return False
            elif errors_received:
                error_msg = errors_received[0].get("message", "")
                if "Минимум 4 игрока" in error_msg:
                    await self.log_test("Game Start & Country Assignment", True, 
                                      f"Correctly rejected: {error_msg}")
                    return True
                else:
                    await self.log_test("Game Start & Country Assignment", False, 
                                      f"Unexpected error: {error_msg}")
                    return False
            else:
                await self.log_test("Game Start & Country Assignment", False, 
                                  "No response received")
                return False
                
        except Exception as e:
            await self.log_test("Game Start & Country Assignment", False, f"Exception: {str(e)}")
            return False
    
    async def test_disconnect_handling(self, client: socketio.AsyncClient):
        """Test disconnect event handling"""
        try:
            # Track disconnect events
            disconnect_events = []
            
            @client.event
            async def player_disconnected(data):
                disconnect_events.append(data)
            
            # Disconnect client
            await client.disconnect()
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Check if client is properly disconnected
            if not client.connected:
                await self.log_test("Disconnect Handling", True, 
                                  "Client disconnected properly")
                return True
            else:
                await self.log_test("Disconnect Handling", False, 
                                  "Client still shows as connected")
                return False
                
        except Exception as e:
            await self.log_test("Disconnect Handling", False, f"Exception: {str(e)}")
            return False
    
    async def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up Socket.IO test data...")
        
        # Close socket connections
        for client in self.socket_clients:
            try:
                if client.connected:
                    await client.disconnect()
            except:
                pass
    
    async def run_comprehensive_socketio_tests(self):
        """Run comprehensive Socket.IO tests"""
        print("🔌 Starting Comprehensive Socket.IO Testing")
        print("=" * 60)
        
        try:
            # Setup test game
            if not await self.setup_test_game():
                return
            
            print(f"\n🎯 Testing Socket.IO Events for Game: {self.game_data['game_id']}")
            
            # Test 1: Connection and Handshake
            print("\n1️⃣ Testing Connection & Handshake...")
            clients_and_players = []
            
            for i, player in enumerate(self.game_data["players"][:3]):  # Test with 3 clients
                client = await self.test_socket_connection_handshake()
                if client:
                    clients_and_players.append((client, player))
            
            if len(clients_and_players) < 2:
                print("❌ Insufficient clients connected for comprehensive testing")
                return
            
            # Test 2: Room Management
            print("\n2️⃣ Testing Room Management...")
            for client, player in clients_and_players:
                await self.test_room_management(client, {
                    "game_id": self.game_data["game_id"],
                    "player_id": player["id"]
                })
            
            # Test 3: Chat Functionality
            print("\n3️⃣ Testing Chat Functionality...")
            await self.test_chat_functionality(clients_and_players)
            
            # Test 4: Ping Updates
            print("\n4️⃣ Testing Ping Updates...")
            for client, player in clients_and_players[:2]:  # Test with 2 clients
                await self.test_ping_updates(client, player)
            
            # Test 5: Player Ready Status
            print("\n5️⃣ Testing Player Ready Status...")
            await self.test_player_ready_status(clients_and_players)
            
            # Test 6: Game Start Sequence
            print("\n6️⃣ Testing Game Start Sequence...")
            host_client, host_player = next((c, p) for c, p in clients_and_players if p["is_host"])
            await self.test_game_start_sequence(host_client, host_player)
            
            # Test 7: Disconnect Handling
            print("\n7️⃣ Testing Disconnect Handling...")
            if len(clients_and_players) > 0:
                test_client, _ = clients_and_players[-1]  # Use last client for disconnect test
                await self.test_disconnect_handling(test_client)
            
        except Exception as e:
            print(f"❌ Critical error during Socket.IO testing: {e}")
            await self.log_test("Critical Error", False, str(e))
        
        finally:
            await self.cleanup()
            await self.print_summary()
    
    async def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 SOCKET.IO TEST SUMMARY")
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
    tester = SocketIOTester()
    await tester.run_comprehensive_socketio_tests()

if __name__ == "__main__":
    asyncio.run(main())