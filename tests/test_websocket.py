#!/usr/bin/env python3
"""Test WebSocket streaming."""
import asyncio
import websockets
import json

async def test_stream():
    """Test streaming completion."""
    uri = "ws://localhost:8000/ws/completions"
    
    print("Connecting to WebSocket...")
    
    async with websockets.connect(uri) as websocket:
        # Send request
        request = {
            "model": "qwen-1-5b",
            "prompt": "What is machine learning? Explain briefly.",
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        await websocket.send(json.dumps(request))
        print(f"Sent request: {request['prompt']}\n")
        print("Response: ", end="", flush=True)
        
        # Receive and print tokens
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                
                if data.get("type") == "start":
                    print(f"[Model: {data['model']}]", flush=True)
                
                elif data.get("type") == "token":
                    print(data["content"], end="", flush=True)
                
                elif data.get("type") == "done":
                    print("\n\n✅ Streaming complete!")
                    break
                
                elif "error" in data:
                    print(f"\n❌ Error: {data['error']}")
                    break
                    
            except websockets.exceptions.ConnectionClosed:
                print("\n\nConnection closed")
                break

if __name__ == "__main__":
    asyncio.run(test_stream())
