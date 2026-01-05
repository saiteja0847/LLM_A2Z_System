"""WebSocket streaming API endpoints."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError
from typing import List, Optional
import json

from ...core.registry import Registry, ModelNotFoundError
from ...core.inference import get_inference_client
from ...utils.memory import estimate_model_memory, check_memory_available


router = APIRouter()


class StreamRequest(BaseModel):
    """Streaming request model."""
    model: str
    prompt: Optional[str] = None
    messages: Optional[List[dict]] = None
    max_tokens: int = 512
    temperature: float = 0.7


@router.websocket("/completions")
async def stream_completions(websocket: WebSocket):
    """
    WebSocket endpoint for streaming completions.
    
    Client sends JSON: {"model": "...", "prompt": "...", "max_tokens": 512, "temperature": 0.7}
    Server streams tokens as they're generated.
    """
    await websocket.accept()
    
    try:
        # Receive request
        data = await websocket.receive_json()
        
        try:
            request = StreamRequest(**data)
        except ValidationError as e:
            await websocket.send_json({"error": f"Invalid request: {e}"})
            await websocket.close()
            return
        
        # Get model
        registry = Registry()
        try:
            entry = registry.get(request.model)
        except ModelNotFoundError:
            await websocket.send_json({"error": f"Model not found: {request.model}"})
            await websocket.close()
            return
        
        # Memory check
        required = estimate_model_memory(entry)
        ok, msg = check_memory_available(required)
        if not ok:
            await websocket.send_json({"error": f"Insufficient memory: {msg}"})
            await websocket.close()
            return
        
        # Load client
        try:
            client = get_inference_client(entry)
        except Exception as e:
            await websocket.send_json({"error": f"Failed to load model: {e}"})
            await websocket.close()
            return
        
        # Stream response
        try:
            # Send start message
            await websocket.send_json({"type": "start", "model": request.model})
            
            # Determine if using prompt or messages
            if request.prompt:
                # Text completion streaming
                for token in client.stream(
                    prompt=request.prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                ):
                    await websocket.send_json({"type": "token", "content": token})
            
            elif request.messages:
                # Chat completion streaming - use complete and send as single chunk
                # (Most backends don't support chat streaming yet)
                response = client.chat(
                    messages=request.messages,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                )
                await websocket.send_json({"type": "token", "content": response})
            
            else:
                await websocket.send_json({"error": "Must provide either 'prompt' or 'messages'"})
                await websocket.close()
                return
            
            # Send completion message
            await websocket.send_json({"type": "done"})
            
        except Exception as e:
            await websocket.send_json({"error": f"Generation failed: {e}"})
        
        await websocket.close()
        
    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": f"Unexpected error: {e}"})
            await websocket.close()
        except:
            pass
