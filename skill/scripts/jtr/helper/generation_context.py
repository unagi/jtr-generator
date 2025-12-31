"""Generation context shared by resume/career sheet generators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

from .japanese_era import JapaneseDateFormatter

DateFormat = Literal["seireki", "wareki"]


@dataclass(frozen=True)
class GenerationContext:
    date_format: DateFormat
    date_formatter: JapaneseDateFormatter


_CONTEXT: GenerationContext | None = None


def init_generation_context(options: dict[str, Any]) -> GenerationContext:
    date_format_value = options.get("date_format", "seireki")
    normalized_date_format = (
        date_format_value if date_format_value in ("seireki", "wareki") else "seireki"
    )
    date_format = cast(DateFormat, normalized_date_format)
    formatter = JapaneseDateFormatter(date_format, default_format_style="full")
    context = GenerationContext(date_format=date_format, date_formatter=formatter)
    set_generation_context(context)
    return context


def set_generation_context(context: GenerationContext) -> None:
    global _CONTEXT
    _CONTEXT = context


def get_generation_context() -> GenerationContext:
    if _CONTEXT is None:
        raise RuntimeError("Generation context is not initialized.")
    return _CONTEXT
