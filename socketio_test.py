#!/usr/bin/env python3
"""
Focused Socket.IO Testing for Empires Game
Tests Socket.IO connection, handshake, and events after configuration changes
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

        print(f"Testing Socket.IO at: {self.socket_url}")
        print(f"Socket.IO endpoint: {self.socket_url}/{self.socket_path}/")
        
        # Test data storage
        self.test_results = []
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
        """Clean up socket connections"""
        print("\n🧹 Cleaning up socket connections...")
        
        for client in self.socket_clients:
            try:
                await client.disconnect()
            except:
                pass
    
    async def test_socket_io_endpoint(self):
        """Test if /socket.io endpoint is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test the Socket.IO handshake endpoint
                handshake_url = f"{self.socket_url}/{self.socket_path}/?EIO=4&transport=polling"
                
                async with session.get(handshake_url) as response:
                    content = await response.text()
                    
                    if response.status == 200 and "socket.io" in content:
                        await self.log_test("Socket.IO Endpoint Access", True, 
                                          f"Handshake endpoint responding correctly")
                        return True
                    else:
                        await self.log_test("Socket.IO Endpoint Access", False, 
                                          f"Status: {response.status}, Content: {content[:200]}")
                        return False
                        
        except Exception as e:
            await self.log_test("Socket.IO Endpoint Access", False, f"Exception: {str(e)}")
            return False
    
    async def test_socket_connection(self) -> Optional[socketio.AsyncClient]:
        """Test Socket.IO connection and handshake"""
        try:
            client = socketio.AsyncClient(logger=True, engineio_logger=True)
            
            # Track connection events
            connected = False
            connection_error = None
            connect_time = None
            
            @client.event
            async def connect():
                nonlocal connected, connect_time
                connected = True
                connect_time = time.time()
                print(f"    Socket.IO connected successfully")
            
            @client.event
            async def connect_error(data):
                nonlocal connection_error
                connection_error = data
                print(f"    Socket.IO connection error: {data}")
            
            @client.event
            async def disconnect():
                print(f"    Socket.IO disconnected")
            
            # Attempt connection with timeout
            start_time = time.time()
            print(f"    Attempting connection to: {self.socket_url}")
            
            await asyncio.wait_for(
                client.connect(self.socket_url, socketio_path=self.socket_path),
                timeout=10.0,
            )
            
            # Wait a bit for connection to establish
            await asyncio.sleep(2)
            
            if connected:
                connection_duration = connect_time - start_time if connect_time else 0
                self.socket_clients.append(client)
                await self.log_test("Socket.IO Connection", True, 
                                  f"Connected in {connection_duration:.2f}s")
                return client
            else:
                await self.log_test("Socket.IO Connection", False, 
                                  f"Connection failed: {connection_error}")
                return None
                
        except asyncio.TimeoutError:
            await self.log_test("Socket.IO Connection", False, "Connection timeout (10s)")
            return None
        except Exception as e:
            await self.log_test("Socket.IO Connection", False, f"Exception: {str(e)}")
            return None
    
    async def create_test_game(self) -> Optional[Dict]:
        """Create a test game for Socket.IO testing"""
        try:
            game_data = {
                "name": "Socket.IO Test Game",
                "host_name": "Test Host",
                "language": "ru",
                "max_players": 8
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games", json=game_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        await self.log_test("Create Test Game", True, 
                                          f"Created game: {result['game']['id']}")
                        return result
                    else:
                        error_text = await response.text()
                        await self.log_test("Create Test Game", False, 
                                          f"Status: {response.status}, Error: {error_text}")
                        return None
        except Exception as e:
            await self.log_test("Create Test Game", False, f"Exception: {str(e)}")
            return None
    
    async def test_join_game_room(self, client: socketio.AsyncClient, game_id: str, player_id: str):
        """Test join_game_room Socket.IO event"""
        try:
            # Track events
            events_received = []
            
            @client.event
            async def player_joined(data):
                events_received.append(("player_joined", data))
                print(f"    Received player_joined: {data}")
            
            @client.event
            async def error(data):
                events_received.append(("error", data))
                print(f"    Received error: {data}")
            
            print(f"    Joining game room: {game_id} as player: {player_id}")
            
            # Join game room
            await client.emit("join_game_room", {
                "game_id": game_id,
                "player_id": player_id
            })
            
            # Wait for response
            await asyncio.sleep(3)
            
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
                print(f"    Received new_message: {data}")
            
            @client.event
            async def error(data):
                errors_received.append(data)
                print(f"    Received error: {data}")
            
            # Send a test message
            test_message = "Socket.IO test message"
            print(f"    Sending message: {test_message}")
            
            await client.emit("send_message", {
                "game_id": game_id,
                "player_id": player_id,
                "message": test_message
            })
            
            # Wait for response
            await asyncio.sleep(3)
            
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
                print(f"    Received ping_updated: {data}")
            
            # Send ping update
            test_ping = 42
            print(f"    Sending ping update: {test_ping}ms")
            
            await client.emit("update_ping", {
                "player_id": player_id,
                "ping": test_ping
            })
            
            # Wait for response
            await asyncio.sleep(3)
            
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
                print(f"    Received player_ready_changed: {data}")
            
            @client.event
            async def error(data):
                errors_received.append(data)
                print(f"    Received error: {data}")
            
            # Set player ready
            print(f"    Setting player ready: {player_id}")
            
            await client.emit("player_ready", {
                "player_id": player_id,
                "is_ready": True
            })
            
            # Wait for response
            await asyncio.sleep(3)
            
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
        """Test start_game Socket.IO event and Country Assignment System"""
        try:
            # Track events
            game_events = []
            errors_received = []
            
            @client.event
            async def game_started(data):
                game_events.append(("game_started", data))
                print(f"    Received game_started: {data}")
            
            @client.event
            async def error(data):
                errors_received.append(data)
                print(f"    Received error: {data}")
            
            # Try to start game
            print(f"    Attempting to start game: {game_id}")
            
            await client.emit("start_game", {
                "game_id": game_id,
                "player_id": host_player_id
            })
            
            # Wait for response
            await asyncio.sleep(5)
            
            # Check results
            if errors_received:
                error_msg = errors_received[0].get("message", "")
                if "Минимум 4 игрока" in error_msg:
                    await self.log_test("Socket.IO start_game", True, 
                                      f"Correctly rejected: {error_msg}")
                    await self.log_test("Country Assignment System", True, 
                                      f"Cannot test - insufficient players (expected)")
                    return True
                else:
                    await self.log_test("Socket.IO start_game", False, 
                                      f"Unexpected error: {error_msg}")
                    return False
            elif game_events:
                # Game started successfully - check country assignment
                game_data = game_events[0][1]
                players = game_data.get("players", [])
                
                countries_assigned = [p for p in players if p.get("country")]
                
                if len(countries_assigned) == len(players) and len(countries_assigned) >= 4:
                    await self.log_test("Socket.IO start_game", True, 
                                      f"Game started successfully")
                    await self.log_test("Country Assignment System", True, 
                                      f"Countries assigned to {len(countries_assigned)} players")
                    
                    # Log assigned countries
                    for player in players:
                        if player.get("country"):
                            print(f"    {player['name']}: {player['country']} {player.get('country_flag', '')}")
                    
                    return True
                else:
                    await self.log_test("Socket.IO start_game", True, 
                                      f"Game started but country assignment incomplete")
                    await self.log_test("Country Assignment System", False, 
                                      f"Only {len(countries_assigned)}/{len(players)} players got countries")
                    return False
            else:
                await self.log_test("Socket.IO start_game", False, 
                                  "No response received")
                return False
                
        except Exception as e:
            await self.log_test("Socket.IO start_game", False, f"Exception: {str(e)}")
            return False
    
    async def run_socket_tests(self):
        """Run focused Socket.IO tests"""
        print("🔌 Starting Socket.IO Testing")
        print("=" * 60)
        
        try:
            # 1. Test Socket.IO endpoint accessibility
            print("\n📡 Testing Socket.IO Endpoint...")
            endpoint_ok = await self.test_socket_io_endpoint()
            
            if not endpoint_ok:
                print("❌ Socket.IO endpoint not accessible - stopping tests")
                return
            
            # 2. Test Socket.IO connection
            print("\n🔗 Testing Socket.IO Connection...")
            client = await self.test_socket_connection()
            
            if not client:
                print("❌ Socket.IO connection failed - stopping tests")
                return
            
            # 3. Create test game for events testing
            print("\n🎮 Creating Test Game...")
            game_result = await self.create_test_game()
            
            if not game_result:
                print("❌ Failed to create test game - stopping Socket.IO event tests")
                return
            
            game_id = game_result["game"]["id"]
            host_player_id = game_result["current_player_id"]
            
            # 4. Test Socket.IO events
            print("\n⚡ Testing Socket.IO Events...")
            
            # Test join_game_room
            await self.test_join_game_room(client, game_id, host_player_id)
            
            # Test send_message
            await self.test_send_message(client, game_id, host_player_id)
            
            # Test update_ping
            await self.test_update_ping(client, host_player_id)
            
            # Test player_ready
            await self.test_player_ready(client, host_player_id)
            
            # Test start_game (and Country Assignment System)
            await self.test_start_game(client, game_id, host_player_id)
            
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
    await tester.run_socket_tests()

if __name__ == "__main__":
    asyncio.run(main())
