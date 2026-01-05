#!/bin/bash
# Test OpenAI-compatible endpoints

echo "======================================================================"
echo "Testing OpenAI-Compatible API"
echo "======================================================================"

echo ""
echo "[Test 1] List Models (GET /v1/models)"
echo "----------------------------------------------------------------------"
curl -s http://localhost:8000/v1/models | python3 -m json.tool
echo ""

echo "[Test 2] Chat Completion (POST /v1/chat/completions)"
echo "----------------------------------------------------------------------"
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-1-5b",
    "messages": [
      {"role": "user", "content": "Explain machine learning in one sentence."}
    ],
    "max_tokens": 50,
    "temperature": 0.3
  }' | python3 -m json.tool
echo ""

echo "[Test 3] Streaming Completion (POST /v1/chat/completions with stream=true)"
echo "----------------------------------------------------------------------"
echo "Response chunks:"
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-1-5b",
    "messages": [
      {"role": "user", "content": "What are neural networks?"}
    ],
    "max_tokens": 100,
    "temperature": 0.5,
    "stream": true
  }'
echo ""
echo ""

echo "======================================================================"
echo "✅ OpenAI-Compatible API Tests Complete"
echo "======================================================================"
echo ""
echo "Usage with OpenAI SDK:"
echo ""
echo "from openai import OpenAI"
echo "client = OpenAI(base_url='http://localhost:8000/v1', api_key='not-needed')"
echo "response = client.chat.completions.create("
echo "    model='qwen-1-5b',"
echo "    messages=[{'role': 'user', 'content': 'Hello!'}]"
echo ")"
echo ""
