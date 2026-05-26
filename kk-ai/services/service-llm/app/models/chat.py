"""Pydantic models for Chat Completion API."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the conversation."""

    role: Literal["system", "user", "assistant"] = Field(
        ..., description="The role of the message author"
    )
    content: str = Field(..., description="The contents of the message")


class ChatCompletionRequest(BaseModel):
    """Request body for chat completion."""

    model: str | None = Field(
        default=None,
        description="ID of the model to use. Defaults to config default.",
    )
    messages: list[ChatMessage] = Field(
        ..., description="A list of messages comprising the conversation"
    )
    temperature: float | None = Field(
        default=None, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int | None = Field(
        default=None, ge=1, description="Maximum number of tokens to generate"
    )
    stream: bool = Field(
        default=False, description="Whether to stream back partial progress"
    )
    top_p: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Nucleus sampling parameter"
    )


class ChatCompletionChoice(BaseModel):
    """A single chat completion choice."""

    index: int = 0
    message: ChatMessage | None = None
    delta: dict[str, Any] | None = None
    finish_reason: str | None = None


class ChatCompletionUsage(BaseModel):
    """Usage statistics for the completion request."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    """Response from chat completion (non-streaming)."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage
