"""Chat functionality."""
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """
    Represents a chat message.

    Attributes:
        role: Message role (system, user, assistant)
        content: Message content
    """

    role: str
    content: str

    def to_dict(self) -> dict:
        """Convert to dictionary for API."""
        return {"role": self.role, "content": self.content}


@dataclass
class ChatResponse:
    """
    Represents a chat completion response.

    Attributes:
        model: Model name used
        content: Response content
        prompt_tokens: Number of tokens in prompt
        completion_tokens: Number of tokens in completion
        total_tokens: Total tokens used
    """

    model: str
    content: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ChatClient:
    """
    Chat interface for AI Lab models.

    Example:
        >>> client = AILabClient()
        >>> messages = [
        ...     ChatMessage(role="user", content="What is Python?")
        ... ]
        >>> response = client.chat.complete("qwen-1-5b", messages)
        >>> print(response.content)
    """

    def __init__(self, client):
        self.client = client

    def complete(
        self,
        model: str,
        messages: List[ChatMessage | Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> ChatResponse:
        """
        Generate chat completion.

        Args:
            model: Model name to use
            messages: List of ChatMessage objects or dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens to generate

        Returns:
            ChatResponse object

        Example:
            >>> response = client.chat.complete(
            ...     model="qwen-1-5b",
            ...     messages=[{"role": "user", "content": "Hello!"}],
            ...     temperature=0.8
            ... )
            >>> print(response.content)
        """
        # Convert messages to dicts if they're ChatMessage objects
        message_dicts = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                message_dicts.append(msg.to_dict())
            else:
                message_dicts.append(msg)

        payload = {
            "model": model,
            "messages": message_dicts,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = self.client.post("/api/chat/chat", json=payload)
        data = response.json()

        return ChatResponse(
            model=data.get("model", model),
            content=data["message"]["content"],
            prompt_tokens=data.get("usage", {}).get("prompt_tokens"),
            completion_tokens=data.get("usage", {}).get("completion_tokens"),
            total_tokens=data.get("usage", {}).get("total_tokens"),
        )

    def openai_complete(
        self,
        model: str,
        messages: List[ChatMessage | Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512,
        stream: bool = False,
    ) -> dict:
        """
        Generate completion using OpenAI-compatible endpoint.

        Args:
            model: Model name to use
            messages: List of ChatMessage objects or dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Enable streaming (not yet implemented)

        Returns:
            Raw OpenAI-compatible response dict

        Example:
            >>> response = client.chat.openai_complete(
            ...     model="qwen-1-5b",
            ...     messages=[{"role": "user", "content": "Hello!"}]
            ... )
            >>> print(response["choices"][0]["message"]["content"])
        """
        # Convert messages to dicts
        message_dicts = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                message_dicts.append(msg.to_dict())
            else:
                message_dicts.append(msg)

        payload = {
            "model": model,
            "messages": message_dicts,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        response = self.client.post("/v1/chat/completions", json=payload)
        return response.json()
