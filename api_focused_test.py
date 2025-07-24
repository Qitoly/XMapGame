#!/usr/bin/env python3
"""
Focused API Testing for Empires Game Backend
Tests only REST API endpoints since Socket.IO has routing issues
"""

import asyncio
import aiohttp
import json
from datetime import datetime

class APITester:
    def __init__(self):
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    self.base_url = line.split('=')[1].strip()
                    break
        
        self.api_url = f"{self.base_url}/api"
        self.test_results = []
        
    async def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    async def test_api_comprehensive(self):
        """Comprehensive API testing"""
        print("🚀 Comprehensive API Testing")
        print("=" * 50)
        
        # Test 1: Get empty games list
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/games") as response:
                if response.status == 200:
                    games = await response.json()
                    await self.log_test("GET /api/games", True, f"Returns {len(games)} games")
                else:
                    await self.log_test("GET /api/games", False, f"Status: {response.status}")
        
        # Test 2: Create a game
        game_data = {
            "name": "Тестовая Империя API",
            "host_name": "Тестовый Император",
            "language": "ru",
            "max_players": 6
        }
        
        game_result = None
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/games", json=game_data) as response:
                if response.status == 200:
                    game_result = await response.json()
                    await self.log_test("POST /api/games", True, f"Created game: {game_result['game']['name']}")
                else:
                    error = await response.text()
                    await self.log_test("POST /api/games", False, f"Status: {response.status}, Error: {error}")
        
        if not game_result:
            return
        
        game_id = game_result["game"]["id"]
        host_player_id = game_result["current_player_id"]
        
        # Test 3: Join game
        join_data = {
            "game_id": game_id,
            "player_name": "Второй Игрок"
        }
        
        player2_result = None
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/games/{game_id}/join", json=join_data) as response:
                if response.status == 200:
                    player2_result = await response.json()
                    await self.log_test("POST /api/games/{id}/join", True, "Player joined successfully")
                else:
                    error = await response.text()
                    await self.log_test("POST /api/games/{id}/join", False, f"Status: {response.status}, Error: {error}")
        
        if not player2_result:
            return
        
        player2_id = player2_result["current_player_id"]
        
        # Test 4: Get game details
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/games/{game_id}?player_id={host_player_id}") as response:
                if response.status == 200:
                    details = await response.json()
                    player_count = len(details["players"])
                    await self.log_test("GET /api/games/{id}", True, f"Retrieved game with {player_count} players")
                else:
                    error = await response.text()
                    await self.log_test("GET /api/games/{id}", False, f"Status: {response.status}, Error: {error}")
        
        # Test 5: Test validation - duplicate name
        duplicate_join = {
            "game_id": game_id,
            "player_name": "Тестовый Император"  # Same as host
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/games/{game_id}/join", json=duplicate_join) as response:
                if response.status == 400:
                    await self.log_test("Duplicate name validation", True, "Correctly rejected duplicate name")
                else:
                    await self.log_test("Duplicate name validation", False, f"Expected 400, got {response.status}")
        
        # Test 6: Test kick player
        kick_data = {"player_id": player2_id}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/games/{game_id}/kick?host_player_id={host_player_id}", json=kick_data) as response:
                if response.status == 200:
                    await self.log_test("POST /api/games/{id}/kick", True, "Player kicked successfully")
                else:
                    error = await response.text()
                    await self.log_test("POST /api/games/{id}/kick", False, f"Status: {response.status}, Error: {error}")
        
        # Test 7: Test password protection
        password_game_data = {
            "name": "Защищенная Игра",
            "host_name": "Секретный Хост",
            "password": "тайный_пароль",
            "language": "ru",
            "max_players": 8
        }
        
        password_game = None
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/games", json=password_game_data) as response:
                if response.status == 200:
                    password_game = await response.json()
                    await self.log_test("Password protected game creation", True, "Created password protected game")
                else:
                    await self.log_test("Password protected game creation", False, f"Status: {response.status}")
        
        if password_game:
            password_game_id = password_game["game"]["id"]
            
            # Test wrong password
            wrong_password_join = {
                "game_id": password_game_id,
                "player_name": "Хакер",
                "password": "неправильный_пароль"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{password_game_id}/join", json=wrong_password_join) as response:
                    if response.status == 401:
                        await self.log_test("Wrong password validation", True, "Correctly rejected wrong password")
                    else:
                        await self.log_test("Wrong password validation", False, f"Expected 401, got {response.status}")
            
            # Test correct password
            correct_password_join = {
                "game_id": password_game_id,
                "player_name": "Авторизованный Игрок",
                "password": "тайный_пароль"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{password_game_id}/join", json=correct_password_join) as response:
                    if response.status == 200:
                        await self.log_test("Correct password validation", True, "Successfully joined with correct password")
                    else:
                        await self.log_test("Correct password validation", False, f"Status: {response.status}")
        
        # Test 8: Final games list
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/games") as response:
                if response.status == 200:
                    games = await response.json()
                    await self.log_test("Final GET /api/games", True, f"Returns {len(games)} games after testing")
                else:
                    await self.log_test("Final GET /api/games", False, f"Status: {response.status}")
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 API TEST SUMMARY")
        print("=" * 50)
        
        total = len(self.test_results)
        passed = len([t for t in self.test_results if t["success"]])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  • {test['test']}: {test['details']}")

async def main():
    tester = APITester()
    await tester.test_api_comprehensive()

if __name__ == "__main__":
    asyncio.run(main())