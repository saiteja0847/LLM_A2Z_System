#!/usr/bin/env python3
"""Test script for REST API."""
import httpx
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    """Test API endpoints."""
    print("Testing AI Lab API...\n")
    
    # Test health check
    print("1. Health check...")
    response = httpx.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")
    
    # Test system status
    print("2. System status...")
    response = httpx.get(f"{BASE_URL}/api/system/status")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Memory: {data['memory']['available_gb']:.1f}GB available")
    print(f"   Models: {data['models_count']}\n")
    
    # Test list models
    print("3. List models...")
    response = httpx.get(f"{BASE_URL}/api/models/")
    print(f"   Status: {response.status_code}")
    models = response.json()
    for m in models:
        print(f"   - {m['name']} ({m['backend']}, {m['quantization']})")
    print()
    
    if models:
        model_name = models[0]['name']
        
        # Test chat completion
        print(f"4. Chat completion with {model_name}...")
        response = httpx.post(
            f"{BASE_URL}/api/chat/chat",
            json={
                "model": model_name,
                "messages": [
                    {"role": "user", "content": "What is 2+2? Answer briefly."}
                ],
                "max_tokens": 50,
                "temperature": 0.7
            },
            timeout=60.0
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data['message']['content'][:100]}...")
        else:
            print(f"   Error: {response.text}")
    
    print("\n✅ API test complete!")

if __name__ == "__main__":
    test_api()
