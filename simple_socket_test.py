#!/usr/bin/env python3
"""
Simple Socket.IO connection test
"""

import asyncio
import socketio

async def test_socket_connection():
    """Test basic Socket.IO connection"""
    try:
        client = socketio.AsyncClient()
        
        @client.event
        async def connect():
            print("✅ Socket.IO connected successfully")
            await client.disconnect()
        
        @client.event
        async def connect_error(data):
            print(f"❌ Socket.IO connection error: {data}")
        
        @client.event
        async def disconnect():
            print("🔌 Socket.IO disconnected")
        
        # Try to connect
        url = "https://a1fe7f13-64d9-4d63-9dd7-362cdd87c0c5.preview.emergentagent.com"
        print(f"Attempting to connect to: {url}")
        
        await client.connect(
            url,
            transports=['websocket', 'polling'],
            socketio_path='api/socket.io',
        )
        await asyncio.sleep(3)  # Wait for connection
        
    except Exception as e:
        print(f"❌ Exception during connection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_socket_connection())
