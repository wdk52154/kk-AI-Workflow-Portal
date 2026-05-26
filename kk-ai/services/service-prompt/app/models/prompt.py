"""Pydantic models for Prompt Center."""

from typing import Any

from pydantic import BaseModel, Field


class PromptVariable(BaseModel):
    """A variable definition in a prompt template."""

    name: str
    required: bool = False
    description: str | None = None
    default: Any | None = None
    type: str = "string"
    example: str | None = None


class PromptTemplate(BaseModel):
    """A prompt template definition."""

    id: str
    name: str
    category: str = "uncategorized"
    version: str = "1.0.0"
    description: str | None = None
    author: str | None = None
    tags: list[str] = Field(default_factory=list)
    variables: list[PromptVariable] = Field(default_factory=list)
    template: str = ""
    messages: list[dict[str, str]] | None = None


class PromptListItem(BaseModel):
    """A single item in prompt list."""

    prompt_id: str
    name: str
    category: str
    version: str
    description: str | None = None


class PromptListResponse(BaseModel):
    """Response for prompt list."""

    items: list[PromptListItem]
    total: int


class RenderPromptRequest(BaseModel):
    """Request to render a prompt."""

    variables: dict[str, Any] = Field(default_factory=dict)


class RenderPromptResponse(BaseModel):
    """Response from prompt rendering."""

    prompt_id: str
    rendered: str
    variables_used: list[str]
    variables_missing: list[str] = Field(default_factory=list)


class RegisterPromptRequest(BaseModel):
    """Request to register a new prompt."""

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    category: str = "uncategorized"
    description: str | None = None
    variables: list[PromptVariable] = Field(default_factory=list)
    template: str = ""


class RegisterPromptResponse(BaseModel):
    """Response after registering a prompt."""

    prompt_id: str
    version: str = "1.0.0"
    status: str = "registered"


class MCPPromptArgument(BaseModel):
    """MCP-style prompt argument."""

    name: str
    description: str | None = None
    required: bool = False


class MCPPromptDetail(BaseModel):
    """MCP-style prompt detail."""

    name: str
    description: str | None = None
    arguments: list[MCPPromptArgument] = Field(default_factory=list)
