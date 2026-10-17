"""Browser input and model output contracts. Actual result rows come from the server."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ThreadRequest(StrictModel):
    user_id: str = Field(min_length=1, max_length=100)


class ChatRequest(ThreadRequest):
    request_id: str = Field(min_length=1, max_length=100)
    thread_id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=16000)

    @field_validator("text")
    @classmethod
    def meaningful_text(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be blank")
        return value


class Component(StrictModel):
    id: str = Field(min_length=1, max_length=100)
    type: Literal["card", "table", "line", "bar", "map", "heatmap"]
    title: str = Field(min_length=1, max_length=300)
    result_id: str = Field(min_length=1, max_length=100)
    mapping: dict


class Conflict(StrictModel):
    claim: str = Field(min_length=1, max_length=2000)
    evidence_refs: list[str] = Field(default_factory=list, max_length=30)
    status: Literal["unconfirmed", "resolved"] = "unconfirmed"


class AnswerDraft(StrictModel):
    response_kind: Literal["factual", "clarification"] = "factual"
    answer: str = Field(min_length=1, max_length=20000)
    components: list[Component] = Field(default_factory=list, max_length=6)
    citation_refs: list[str] = Field(default_factory=list, max_length=100)
    conflicts: list[Conflict] = Field(default_factory=list, max_length=20)
    limitations: list[str] = Field(default_factory=list, max_length=30)
    entity_ids: list[str] = Field(default_factory=list, max_length=200)
