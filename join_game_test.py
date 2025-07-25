#!/usr/bin/env python3
"""
Focused test for the "Field required" issue when joining games
Tests the specific fix for JoinGameRequest validation
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Add backend to path for imports
sys.path.append('/app/backend')

class JoinGameTester:
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
        print(f"Testing backend at: {self.api_url}")
        
        # Test data storage
        self.test_results = []
        self.created_games = []
        self.created_players = []
        
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
    
    async def create_test_game(self, game_name: str = "Тестовая Игра", host_name: str = "Тестовый Хост", password: str = None):
        """Create a test game for joining tests"""
        try:
            game_data = {
                "name": game_name,
                "host_name": host_name,
                "language": "ru",
                "max_players": 8
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
                        
                        print(f"✅ Created test game: {game_id}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to create test game: Status {response.status}, Error: {error_text}")
                        return None
        except Exception as e:
            print(f"❌ Exception creating test game: {str(e)}")
            return None
    
    async def test_join_game_with_all_fields(self, game_id: str):
        """Test joining game with all required fields (game_id, player_name)"""
        try:
            join_data = {
                "game_id": game_id,
                "player_name": "Игрок Тестер"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{game_id}/join", json=join_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        player_id = result["current_player_id"]
                        self.created_players.append(player_id)
                        
                        await self.log_test("Join game with all required fields", True, 
                                          f"Successfully joined game {game_id}")
                        return True
                    else:
                        error_text = await response.text()
                        await self.log_test("Join game with all required fields", False, 
                                          f"Status: {response.status}, Error: {error_text}")
                        return False
        except Exception as e:
            await self.log_test("Join game with all required fields", False, f"Exception: {str(e)}")
            return False
    
    async def test_join_game_with_password(self, game_id: str, password: str):
        """Test joining password-protected game with correct password"""
        try:
            join_data = {
                "game_id": game_id,
                "player_name": "Игрок с Паролем",
                "password": password
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{game_id}/join", json=join_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        player_id = result["current_player_id"]
                        self.created_players.append(player_id)
                        
                        await self.log_test("Join password-protected game", True, 
                                          f"Successfully joined password-protected game")
                        return True
                    else:
                        error_text = await response.text()
                        await self.log_test("Join password-protected game", False, 
                                          f"Status: {response.status}, Error: {error_text}")
                        return False
        except Exception as e:
            await self.log_test("Join password-protected game", False, f"Exception: {str(e)}")
            return False
    
    async def test_join_game_missing_game_id(self, game_id: str):
        """Test joining game without game_id field (should fail with Field required)"""
        try:
            join_data = {
                "player_name": "Игрок без ID"
                # Missing game_id field
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{game_id}/join", json=join_data) as response:
                    if response.status == 422:  # Validation error expected
                        error_data = await response.json()
                        error_detail = str(error_data)
                        
                        # Check if it's specifically about game_id field
                        if "game_id" in error_detail and "required" in error_detail.lower():
                            await self.log_test("Missing game_id validation", True, 
                                              f"Correctly rejected missing game_id: {error_detail}")
                            return True
                        else:
                            await self.log_test("Missing game_id validation", False, 
                                              f"Wrong validation error: {error_detail}")
                            return False
                    else:
                        error_text = await response.text()
                        await self.log_test("Missing game_id validation", False, 
                                          f"Expected 422, got {response.status}: {error_text}")
                        return False
        except Exception as e:
            await self.log_test("Missing game_id validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_join_game_missing_player_name(self, game_id: str):
        """Test joining game without player_name field (should fail with Field required)"""
        try:
            join_data = {
                "game_id": game_id
                # Missing player_name field
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{game_id}/join", json=join_data) as response:
                    if response.status == 422:  # Validation error expected
                        error_data = await response.json()
                        error_detail = str(error_data)
                        
                        # Check if it's specifically about player_name field
                        if "player_name" in error_detail and "required" in error_detail.lower():
                            await self.log_test("Missing player_name validation", True, 
                                              f"Correctly rejected missing player_name: {error_detail}")
                            return True
                        else:
                            await self.log_test("Missing player_name validation", False, 
                                              f"Wrong validation error: {error_detail}")
                            return False
                    else:
                        error_text = await response.text()
                        await self.log_test("Missing player_name validation", False, 
                                          f"Expected 422, got {response.status}: {error_text}")
                        return False
        except Exception as e:
            await self.log_test("Missing player_name validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_join_game_empty_fields(self, game_id: str):
        """Test joining game with empty string fields"""
        try:
            join_data = {
                "game_id": "",  # Empty game_id
                "player_name": ""  # Empty player_name
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{game_id}/join", json=join_data) as response:
                    if response.status in [400, 422]:  # Validation error expected
                        error_data = await response.json()
                        await self.log_test("Empty fields validation", True, 
                                          f"Correctly rejected empty fields: Status {response.status}")
                        return True
                    else:
                        error_text = await response.text()
                        await self.log_test("Empty fields validation", False, 
                                          f"Expected 400/422, got {response.status}: {error_text}")
                        return False
        except Exception as e:
            await self.log_test("Empty fields validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_join_game_wrong_password(self, game_id: str):
        """Test joining password-protected game with wrong password"""
        try:
            join_data = {
                "game_id": game_id,
                "player_name": "Игрок с Неверным Паролем",
                "password": "неверный_пароль"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{game_id}/join", json=join_data) as response:
                    if response.status == 401:  # Unauthorized expected
                        await self.log_test("Wrong password validation", True, 
                                          f"Correctly rejected wrong password")
                        return True
                    else:
                        error_text = await response.text()
                        await self.log_test("Wrong password validation", False, 
                                          f"Expected 401, got {response.status}: {error_text}")
                        return False
        except Exception as e:
            await self.log_test("Wrong password validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_join_nonexistent_game(self):
        """Test joining non-existent game"""
        try:
            fake_game_id = "non-existent-game-id"
            join_data = {
                "game_id": fake_game_id,
                "player_name": "Игрок в Несуществующей Игре"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{fake_game_id}/join", json=join_data) as response:
                    if response.status == 404:  # Not found expected
                        await self.log_test("Non-existent game validation", True, 
                                          f"Correctly rejected non-existent game")
                        return True
                    else:
                        error_text = await response.text()
                        await self.log_test("Non-existent game validation", False, 
                                          f"Expected 404, got {response.status}: {error_text}")
                        return False
        except Exception as e:
            await self.log_test("Non-existent game validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_duplicate_player_name(self, game_id: str, existing_name: str):
        """Test joining game with duplicate player name"""
        try:
            join_data = {
                "game_id": game_id,
                "player_name": existing_name  # Same as host name
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/games/{game_id}/join", json=join_data) as response:
                    if response.status == 400:  # Bad request expected
                        await self.log_test("Duplicate name validation", True, 
                                          f"Correctly rejected duplicate name")
                        return True
                    else:
                        error_text = await response.text()
                        await self.log_test("Duplicate name validation", False, 
                                          f"Expected 400, got {response.status}: {error_text}")
                        return False
        except Exception as e:
            await self.log_test("Duplicate name validation", False, f"Exception: {str(e)}")
            return False
    
    async def run_join_game_tests(self):
        """Run all join game tests"""
        print("🎯 Testing Join Game Endpoint - Focus on 'Field required' Fix")
        print("=" * 70)
        
        # Test 1: Create a regular game
        print("\n1️⃣ Creating test game without password...")
        regular_game = await self.create_test_game("Обычная Игра", "Обычный Хост")
        if not regular_game:
            print("❌ Cannot continue tests - failed to create regular game")
            return
        
        regular_game_id = regular_game["game"]["id"]
        host_name = regular_game["game"]["host_name"]
        
        # Test 2: Create a password-protected game
        print("\n2️⃣ Creating password-protected test game...")
        password = "тестовый_пароль_123"
        protected_game = await self.create_test_game("Защищенная Игра", "Защищенный Хост", password)
        if not protected_game:
            print("❌ Cannot continue password tests - failed to create protected game")
            protected_game_id = None
        else:
            protected_game_id = protected_game["game"]["id"]
        
        # Test 3: Join regular game with all required fields (main fix test)
        print("\n3️⃣ Testing join with all required fields (game_id + player_name)...")
        await self.test_join_game_with_all_fields(regular_game_id)
        
        # Test 4: Join password-protected game with correct password
        if protected_game_id:
            print("\n4️⃣ Testing join password-protected game...")
            await self.test_join_game_with_password(protected_game_id, password)
        
        # Test 5: Test validation errors
        print("\n5️⃣ Testing field validation errors...")
        await self.test_join_game_missing_game_id(regular_game_id)
        await self.test_join_game_missing_player_name(regular_game_id)
        await self.test_join_game_empty_fields(regular_game_id)
        
        # Test 6: Test other validation scenarios
        print("\n6️⃣ Testing other validation scenarios...")
        await self.test_join_nonexistent_game()
        await self.test_duplicate_player_name(regular_game_id, host_name)
        
        if protected_game_id:
            await self.test_join_game_wrong_password(protected_game_id)
        
        await self.print_summary()
    
    async def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 JOIN GAME TEST SUMMARY")
        print("=" * 70)
        
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
            print(f"\n🎉 ALL TESTS PASSED! The 'Field required' issue appears to be fixed.")
        
        print("\n" + "=" * 70)

async def main():
    """Main test runner"""
    tester = JoinGameTester()
    await tester.run_join_game_tests()

if __name__ == "__main__":
    asyncio.run(main())