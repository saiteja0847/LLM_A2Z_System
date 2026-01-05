"""Chat and completion API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from ...core.registry import Registry, ModelNotFoundError
from ...core.inference import get_inference_client
from ...utils.memory import estimate_model_memory, check_memory_available


router = APIRouter()


# Request/Response models
class CompletionRequest(BaseModel):
    """Text completion request."""
    model: str
    prompt: str
    max_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    stop: Optional[List[str]] = None


class CompletionResponse(BaseModel):
    """Text completion response."""
    model: str
    text: str
    finish_reason: str = "stop"


class ChatMessage(BaseModel):
    """Chat message."""
    role: str  # "user", "assistant", or "system"
    content: str


class ChatRequest(BaseModel):
    """Chat completion request."""
    model: str
    messages: List[ChatMessage]
    max_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    """Chat completion response."""
    model: str
    message: ChatMessage
    finish_reason: str = "stop"


@router.post("/completions", response_model=CompletionResponse)
async def create_completion(request: CompletionRequest):
    """Generate a text completion."""
    registry = Registry()
    
    try:
        entry = registry.get(request.model)
    except ModelNotFoundError:
        raise HTTPException(status_code=404, detail=f"Model not found: {request.model}")
    
    # Memory check
    required = estimate_model_memory(entry)
    ok, msg = check_memory_available(required)
    if not ok:
        raise HTTPException(status_code=507, detail=f"Insufficient memory: {msg}")
    
    # Load client and generate
    try:
        client = get_inference_client(entry)
        text = client.complete(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop or []
        )
        
        return CompletionResponse(
            model=request.model,
            text=text,
            finish_reason="stop"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def create_chat_completion(request: ChatRequest):
    """Generate a chat completion."""
    registry = Registry()
    
    try:
        entry = registry.get(request.model)
    except ModelNotFoundError:
        raise HTTPException(status_code=404, detail=f"Model not found: {request.model}")
    
    # Memory check
    required = estimate_model_memory(entry)
    ok, msg = check_memory_available(required)
    if not ok:
        raise HTTPException(status_code=507, detail=f"Insufficient memory: {msg}")
    
    # Convert messages to dict format
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    # Load client and generate
    try:
        client = get_inference_client(entry)
        response_text = client.chat(
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return ChatResponse(
            model=request.model,
            message=ChatMessage(role="assistant", content=response_text),
            finish_reason="stop"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat inference failed: {str(e)}")
