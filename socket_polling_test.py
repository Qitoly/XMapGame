#!/usr/bin/env python3
"""
Test Socket.IO with polling transport only
"""

import asyncio
import socketio
import aiohttp

async def test_socket_polling():
    """Test Socket.IO with polling transport"""
    try:
        # First test if the Socket.IO endpoint responds
        async with aiohttp.ClientSession() as session:
            async with session.get("https://76f48bb5-574d-4855-95cf-3fbfd8d74a74.preview.emergentagent.com/socket.io/?EIO=4&transport=polling") as response:
                print(f"Socket.IO polling endpoint status: {response.status}")
                if response.status == 200:
                    text = await response.text()
                    print(f"Response: {text[:200]}...")
                else:
                    print(f"Error response: {await response.text()}")
        
        # Now try to connect with Socket.IO client
        client = socketio.AsyncClient(logger=True, engineio_logger=True)
        
        connected = False
        
        @client.event
        async def connect():
            nonlocal connected
            connected = True
            print("✅ Socket.IO connected successfully")
        
        @client.event
        async def connect_error(data):
            print(f"❌ Socket.IO connection error: {data}")
        
        url = "https://76f48bb5-574d-4855-95cf-3fbfd8d74a74.preview.emergentagent.com"
        print(f"Attempting to connect to: {url}")
        
        await client.connect(url, transports=['polling'])
        
        # Wait for connection
        for i in range(10):
            if connected:
                break
            await asyncio.sleep(1)
            print(f"Waiting for connection... {i+1}/10")
        
        if connected:
            print("✅ Connection successful!")
            await client.disconnect()
        else:
            print("❌ Connection failed after 10 seconds")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_socket_polling())