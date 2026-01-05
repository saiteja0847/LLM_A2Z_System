"""OpenAI-compatible API endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal, Union
from datetime import datetime
import json
import time
import uuid

from ...core.registry import Registry
from ...core.inference import get_inference_client

router = APIRouter()
registry = Registry()


# OpenAI-compatible request models
class ChatMessage(BaseModel):
    """Chat message in OpenAI format."""
    role: Literal["system", "user", "assistant"]
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    """OpenAI chat completion request."""
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)
    n: Optional[int] = Field(default=1, ge=1, le=1)  # We only support n=1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = Field(default=512, ge=1)
    presence_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    frequency_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


# OpenAI-compatible response models
class ChatCompletionMessage(BaseModel):
    """Chat completion message."""
    role: Literal["assistant"]
    content: str


class ChatCompletionChoice(BaseModel):
    """Chat completion choice."""
    index: int
    message: ChatCompletionMessage
    finish_reason: Literal["stop", "length", "content_filter", "null"]


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """OpenAI chat completion response."""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:24]}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionChoice]
    usage: UsageInfo


class ChatCompletionStreamChoice(BaseModel):
    """Streaming choice delta."""
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[Literal["stop", "length", "content_filter"]] = None


class ChatCompletionStreamResponse(BaseModel):
    """OpenAI streaming response chunk."""
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionStreamChoice]


def count_tokens(text: str) -> int:
    """
    Rough token count estimation.

    In production, use tiktoken or model-specific tokenizer.
    For now, approximate as 1 token ≈ 4 characters.
    """
    return len(text) // 4


@router.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completion endpoint.

    Supports both streaming and non-streaming modes.
    """
    # Validate model exists
    try:
        model_entry = registry.get(request.model)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Model '{request.model}' not found")

    # Get client
    try:
        client = get_inference_client(model_entry)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

    # Convert messages to format our backend expects
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    # Handle streaming
    if request.stream:
        return StreamingResponse(
            stream_completion(
                client=client,
                messages=messages,
                request=request,
                model_entry=model_entry
            ),
            media_type="text/event-stream"
        )

    # Non-streaming completion
    try:
        # Generate response
        response_text = client.chat(
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        # Count tokens
        prompt_text = " ".join(msg.content for msg in request.messages)
        prompt_tokens = count_tokens(prompt_text)
        completion_tokens = count_tokens(response_text)

        # Build OpenAI-compatible response
        return ChatCompletionResponse(
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant",
                        content=response_text
                    ),
                    finish_reason="stop"
                )
            ],
            usage=UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


async def stream_completion(client, messages: List[dict], request: ChatCompletionRequest, model_entry):
    """
    Stream completion in OpenAI SSE format.

    Yields Server-Sent Events with chat.completion.chunk objects.
    """
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    created = int(time.time())

    try:
        # Send initial chunk with role
        initial_chunk = ChatCompletionStreamResponse(
            id=chunk_id,
            created=created,
            model=request.model,
            choices=[
                ChatCompletionStreamChoice(
                    index=0,
                    delta={"role": "assistant", "content": ""},
                    finish_reason=None
                )
            ]
        )
        yield f"data: {initial_chunk.model_dump_json()}\n\n"

        # Stream content
        for token in client.stream(
            prompt=client._format_chat(messages),
            max_tokens=request.max_tokens,
            temperature=request.temperature
        ):
            chunk = ChatCompletionStreamResponse(
                id=chunk_id,
                created=created,
                model=request.model,
                choices=[
                    ChatCompletionStreamChoice(
                        index=0,
                        delta={"content": token},
                        finish_reason=None
                    )
                ]
            )
            yield f"data: {chunk.model_dump_json()}\n\n"

        # Send final chunk
        final_chunk = ChatCompletionStreamResponse(
            id=chunk_id,
            created=created,
            model=request.model,
            choices=[
                ChatCompletionStreamChoice(
                    index=0,
                    delta={},
                    finish_reason="stop"
                )
            ]
        )
        yield f"data: {final_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        error_data = {
            "error": {
                "message": str(e),
                "type": "server_error",
                "code": 500
            }
        }
        yield f"data: {json.dumps(error_data)}\n\n"


@router.get("/v1/models")
async def list_models():
    """
    OpenAI-compatible models list endpoint.

    Returns list of available models in OpenAI format.
    """
    models = registry.list()

    return {
        "object": "list",
        "data": [
            {
                "id": model.name,
                "object": "model",
                "created": int(model.created_at.timestamp()) if model.created_at else int(time.time()),
                "owned_by": "local",
                "permission": [],
                "root": model.parent or model.name,
                "parent": model.parent
            }
            for model in models
        ]
    }
