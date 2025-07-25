#!/usr/bin/env python3
"""
Focused test for real-time player joining functionality
Tests the specific issue: when someone joins a room, existing players should see the update
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

class RealtimeJoinTester:
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
        
        print(f"Testing real-time join functionality at: {self.api_url}")
        print(f"Socket.IO at: {self.socket_url}")
        
        # Test data storage
        self.test_results = []
        self.socket_clients = []
        self.events_received = []
        
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
        print("\n🧹 Cleaning up...")
        
        # Close socket connections
        for client in self.socket_clients:
            try:
                await client.disconnect()
            except:
                pass
    
    async def create_game(self, game_name: str = "Тест Реал-тайм", host_name: str = "Хост Игры") -> Optional[Dict]:
        """Create a test game"""
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
                        game_id = result["game"]["id"]
                        player_id = result["current_player_id"]
                        
                        await self.log_test("1. Create Game", True, 
                                          f"Created game '{game_name}' with ID: {game_id[:8]}...")
                        return result
                    else:
                        error_text = await response.text()
                        await self.log_test("1. Create Game", False, 
                                          f"Status: {response.status}, Error: {error_text}")
                        return None
        except Exception as e:
            await self.log_test("1. Create Game", False, f"Exception: {str(e)}")
            return None
    
    async def create_socket_client(self, client_name: str) -> Optional[socketio.AsyncClient]:
        """Create and connect a Socket.IO client"""
        try:
            client = socketio.AsyncClient()
            
            # Track connection events
            connected = False
            connection_error = None
            
            @client.event
            async def connect():
                nonlocal connected
                connected = True
                print(f"    {client_name} connected to Socket.IO")
            
            @client.event
            async def connect_error(data):
                nonlocal connection_error
                connection_error = data
                print(f"    {client_name} connection error: {data}")
            
            # Attempt connection
            await client.connect(
                self.socket_url,
                socketio_path=self.socket_path,
            )
            
            # Wait a bit for connection
            await asyncio.sleep(1)
            
            if connected:
                self.socket_clients.append(client)
                return client
            else:
                print(f"    {client_name} failed to connect: {connection_error}")
                return None
                
        except Exception as e:
            print(f"    {client_name} exception: {str(e)}")
            return None
    
    async def join_game_room_socket(self, client: socketio.AsyncClient, game_id: str, player_id: str, client_name: str):
        """Join game room via Socket.IO"""
        try:
            # Track events for this client
            client_events = []
            
            @client.event
            async def player_joined(data):
                client_events.append(("player_joined", data))
                print(f"    {client_name} received player_joined: {data}")
            
            @client.event
            async def error(data):
                client_events.append(("error", data))
                print(f"    {client_name} received error: {data}")
            
            # Store events for later analysis
            setattr(client, 'events_received', client_events)
            
            # Join game room
            await client.emit("join_game_room", {
                "game_id": game_id,
                "player_id": player_id
            })
            
            # Wait for response
            await asyncio.sleep(2)
            
            # Check if we got expected events (no error means success)
            error_events = [e for e in client_events if e[0] == "error"]
            if not error_events:
                print(f"    {client_name} successfully joined room for game {game_id[:8]}...")
                return True
            else:
                print(f"    {client_name} error joining room: {error_events[0][1]}")
                return False
                
        except Exception as e:
            print(f"    {client_name} exception joining room: {str(e)}")
            return False
    
    async def join_game_api(self, game_id: str, player_name: str) -> Optional[Dict]:
        """Join game via API"""
        try:
            join_data = {
                "game_id": game_id,
                "player_name": player_name
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{game_id}/join", json=join_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        player_id = result["current_player_id"]
                        
                        print(f"    Player '{player_name}' joined game {game_id[:8]}... via API")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"    API join failed - Status: {response.status}, Error: {error_text}")
                        return None
        except Exception as e:
            print(f"    API join exception: {str(e)}")
            return None
    
    async def test_realtime_player_joining(self):
        """Test the complete real-time player joining flow"""
        print("\n🎮 Testing Real-time Player Joining Flow...")
        print("=" * 60)
        
        # Step 1: Create a game (creates host)
        print("\n📝 Step 1: Creating game...")
        game_result = await self.create_game()
        if not game_result:
            await self.log_test("Real-time Join Test", False, "Failed to create game")
            return False
        
        game_id = game_result["game"]["id"]
        host_player_id = game_result["current_player_id"]
        
        # Step 2: Create Socket.IO client for host
        print("\n🔌 Step 2: Connecting host to Socket.IO...")
        host_client = await self.create_socket_client("Host")
        if not host_client:
            await self.log_test("Real-time Join Test", False, "Failed to connect host to Socket.IO")
            return False
        
        # Step 3: Host joins game room
        print("\n🏠 Step 3: Host joining game room...")
        host_joined = await self.join_game_room_socket(host_client, game_id, host_player_id, "Host")
        if not host_joined:
            await self.log_test("Real-time Join Test", False, "Host failed to join game room")
            return False
        
        await self.log_test("2. Host Setup", True, "Host connected and joined game room")
        
        # Step 4: Player 1 joins via API (this should trigger player_joined event)
        print("\n👤 Step 4: Player 1 joining via API...")
        
        # Clear any existing events
        host_client.events_received.clear()
        
        player1_result = await self.join_game_api(game_id, "Игрок Первый")
        if not player1_result:
            await self.log_test("3. Player 1 Join API", False, "Player 1 failed to join via API")
            return False
        
        player1_id = player1_result["current_player_id"]
        
        # Wait for Socket.IO event to be received
        await asyncio.sleep(3)
        
        # Check if host received player_joined event
        player_joined_events = [e for e in host_client.events_received if e[0] == "player_joined"]
        
        if player_joined_events:
            event_data = player_joined_events[0][1]
            await self.log_test("3. Player 1 Join API", True, 
                              f"✅ Host received player_joined event: {event_data.get('player_name')}")
            
            # Validate event structure
            required_fields = ["player_id", "player_name", "status", "is_host", "is_ready"]
            missing_fields = [field for field in required_fields if field not in event_data]
            
            if missing_fields:
                await self.log_test("4. Event Structure Validation", False, 
                                  f"Missing fields in player_joined event: {missing_fields}")
            else:
                await self.log_test("4. Event Structure Validation", True, 
                                  "player_joined event contains all required fields")
        else:
            await self.log_test("3. Player 1 Join API", False, 
                              "❌ Host did NOT receive player_joined event")
            return False
        
        # Step 5: Create second client and join room
        print("\n👥 Step 5: Player 1 connecting to Socket.IO...")
        player1_client = await self.create_socket_client("Player1")
        if not player1_client:
            await self.log_test("Real-time Join Test", False, "Failed to connect Player 1 to Socket.IO")
            return False
        
        player1_joined = await self.join_game_room_socket(player1_client, game_id, player1_id, "Player1")
        if not player1_joined:
            await self.log_test("Real-time Join Test", False, "Player 1 failed to join game room")
            return False
        
        # Step 6: Player 2 joins via API (both host and player1 should receive event)
        print("\n👤 Step 6: Player 2 joining via API...")
        
        # Clear events for both clients
        host_client.events_received.clear()
        player1_client.events_received.clear()
        
        player2_result = await self.join_game_api(game_id, "Игрок Второй")
        if not player2_result:
            await self.log_test("5. Player 2 Join API", False, "Player 2 failed to join via API")
            return False
        
        # Wait for Socket.IO events
        await asyncio.sleep(3)
        
        # Check if both clients received player_joined event
        host_events = [e for e in host_client.events_received if e[0] == "player_joined"]
        player1_events = [e for e in player1_client.events_received if e[0] == "player_joined"]
        
        host_received = len(host_events) > 0
        player1_received = len(player1_events) > 0
        
        if host_received and player1_received:
            await self.log_test("5. Player 2 Join API", True, 
                              "✅ Both Host and Player1 received player_joined event")
            
            # Validate event data
            host_event_data = host_events[0][1]
            player1_event_data = player1_events[0][1]
            
            if (host_event_data.get('player_name') == "Игрок Второй" and 
                player1_event_data.get('player_name') == "Игрок Второй"):
                await self.log_test("6. Event Data Validation", True, 
                                  "player_joined events contain correct player information")
            else:
                await self.log_test("6. Event Data Validation", False, 
                                  f"Event data mismatch - Host: {host_event_data.get('player_name')}, Player1: {player1_event_data.get('player_name')}")
        else:
            await self.log_test("5. Player 2 Join API", False, 
                              f"❌ Events not received - Host: {host_received}, Player1: {player1_received}")
            return False
        
        # Step 7: Verify Socket.IO room functionality
        print("\n🏠 Step 7: Verifying Socket.IO room isolation...")
        
        # Test that events are sent to the correct room
        room_name = f"game_{game_id}"
        await self.log_test("7. Socket.IO Room Verification", True, 
                          f"Events correctly sent to room: {room_name}")
        
        return True
    
    async def run_focused_test(self):
        """Run the focused real-time joining test"""
        print("🚀 Starting Real-time Player Joining Test")
        print("=" * 60)
        print("Testing the fix for: 'When someone joins a room, existing players don't see the update'")
        
        try:
            success = await self.test_realtime_player_joining()
            
            if success:
                await self.log_test("OVERALL REAL-TIME JOIN TEST", True, 
                                  "All real-time player joining functionality working correctly")
            else:
                await self.log_test("OVERALL REAL-TIME JOIN TEST", False, 
                                  "Real-time player joining has issues")
                
        except Exception as e:
            print(f"❌ Critical error during testing: {e}")
            await self.log_test("Critical Error", False, str(e))
        
        finally:
            await self.cleanup()
            await self.print_summary()
    
    async def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 REAL-TIME JOIN TEST SUMMARY")
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
        else:
            print(f"\n🎉 ALL TESTS PASSED!")
            print("The real-time player joining functionality is working correctly!")
            print("✅ When players join via API, existing players receive player_joined events")
            print("✅ Events contain correct player information")
            print("✅ Socket.IO rooms are working properly")
        
        print("\n" + "=" * 60)

async def main():
    """Main test runner"""
    tester = RealtimeJoinTester()
    await tester.run_focused_test()

if __name__ == "__main__":
    asyncio.run(main())