"""Structured-output extraction: pull one JSON object from model text and validate it.

The same extraction policy applies to every model. There is no model-specific repair
and no re-prompting here; any retry policy belongs to the orchestrator and must be
applied uniformly across paths.
"""

from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

_FENCE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)


class StructuredOutputError(ValueError):
    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind  # "no_json" | "invalid_json" | "schema_mismatch"


def schema_instruction(schema: type[BaseModel]) -> str:
    """Standard instruction appended to prompts that require structured output."""
    return (
        "Respond with a single JSON object that conforms to this JSON Schema. "
        "Put it in one ```json fenced block and include nothing else outside the block.\n"
        f"```json\n{json.dumps(schema.model_json_schema(), indent=2)}\n```"
    )


def _candidates(text: str) -> list[str]:
    cands = [m.group(1) for m in _FENCE.finditer(text)]
    # Fallback: outermost {...} span in the raw text.
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        cands.append(text[start : end + 1])
    return cands


def parse_structured(text: str, schema: type[T]) -> T:
    cands = _candidates(text)
    if not cands:
        raise StructuredOutputError("no_json", "No JSON object found in model output")
    last_err: Exception | None = None
    decoded_any = False
    for c in cands:
        try:
            data = json.loads(c)
        except json.JSONDecodeError as e:
            last_err = e
            continue
        decoded_any = True
        try:
            return schema.model_validate(data)
        except ValidationError as e:
            last_err = e
    kind = "schema_mismatch" if decoded_any else "invalid_json"
    raise StructuredOutputError(kind, str(last_err))
