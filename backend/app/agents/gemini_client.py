"""Defensive wrapper around the google-genai SDK for gemini-2.5-flash.

Goals:
* Use ONE model name from config (``GEMINI_MODEL``) everywhere.
* Request JSON output and high "thinking" by default, but **degrade gracefully** — if the
  installed SDK version rejects a config parameter (e.g. ``thinking_level`` vs
  ``thinking_budget``), progressively drop parameters and retry instead of crashing.
* Parse JSON robustly (strip code fences, extract the first balanced object/array).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from ..config import get_settings

logger = logging.getLogger(__name__)

_client = None


def get_client():
    global _client
    if _client is None:
        from google import genai

        s = get_settings()
        if not s.gemini_key:
            raise RuntimeError(
                "No Gemini API key configured. Set GEMINI_API_KEY (or GOOGLE_API_KEY) in backend/.env"
            )
        _client = genai.Client(api_key=s.gemini_key)
    return _client


def _generate(prompt: str, system_instruction: Optional[str], temperature: float, as_json: bool) -> str:
    from google.genai import types

    s = get_settings()
    client = get_client()

    def build(use_thinking: bool, use_system: bool, use_mime: bool, use_temp: bool):
        kw: dict[str, Any] = {}
        if use_mime and as_json:
            kw["response_mime_type"] = "application/json"
        if use_temp:
            kw["temperature"] = temperature
        if use_system and system_instruction:
            kw["system_instruction"] = system_instruction
        if use_thinking:
            kw["thinking_config"] = types.ThinkingConfig(thinking_level=s.gemini_thinking_level)
        return types.GenerateContentConfig(**kw)

    # Most featureful first; each fallback drops something that an older/newer SDK may reject.
    candidates = [
        lambda: build(True, True, True, True),
        lambda: build(False, True, True, True),    # drop thinking_config
        lambda: build(False, True, False, True),   # drop response_mime_type
        lambda: build(False, False, False, False),  # bare minimum
    ]

    last_err: Optional[Exception] = None
    for make in candidates:
        try:
            config = make()
        except Exception as e:  # config construction rejected a field
            last_err = e
            continue
        try:
            resp = client.models.generate_content(
                model=s.gemini_model, contents=prompt, config=config
            )
            return (resp.text or "").strip()
        except Exception as e:
            last_err = e
            logger.warning("Gemini call failed (%s); retrying with simpler config", e)
            continue

    raise RuntimeError(f"Gemini generate_content failed after fallbacks: {last_err}")


def _extract_balanced(text: str, open_ch: str, close_ch: str) -> Optional[str]:
    start = text.find(open_ch)
    if start == -1:
        return None
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return None


def _parse_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        snippet = _extract_balanced(text, open_ch, close_ch)
        if snippet:
            try:
                return json.loads(snippet)
            except Exception:
                continue
    raise ValueError(f"Could not parse JSON from model output: {text[:300]!r}")


def generate_json(
    prompt: str, *, system_instruction: Optional[str] = None, temperature: float = 0.2
) -> Any:
    """Run a prompt and return parsed JSON (dict or list)."""
    raw = _generate(prompt, system_instruction, temperature, as_json=True)
    return _parse_json(raw)


def generate_text(
    prompt: str, *, system_instruction: Optional[str] = None, temperature: float = 0.3
) -> str:
    """Run a prompt and return plain text (used for RAG answer synthesis)."""
    return _generate(prompt, system_instruction, temperature, as_json=False)


def _as_str_list(value: Any) -> list[str]:
    """Coerce a model field into a clean list of non-empty strings."""
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    out: list[str] = []
    for v in value:
        if isinstance(v, dict):
            v = v.get("text") or v.get("name") or v.get("value") or json.dumps(v)
        s = str(v).strip()
        if s:
            out.append(s)
    return out
