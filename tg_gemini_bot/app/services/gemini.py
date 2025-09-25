
# ---- gemini api ----
from __future__ import annotations
import asyncio
from typing import Iterable, List, Tuple, AsyncGenerator, Optional

from google import genai  # type: ignore
from google.genai import types as genai_types  # type: ignore

from app import config
from app.services.memory import ChatCfg, build_memory_contents

# Client (single instance)
_client: Optional[genai.Client] = None

def client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client

def build_tools(cfg: ChatCfg):
    t = []
    if cfg.search:
        t.append({"google_search": {}})
    if cfg.code:
        t.append({"code_execution": {}})
    if cfg.url:
        t.append({"url_context": {}})
    return t

def _thinking_config(cfg: ChatCfg) -> genai_types.ThinkingConfig:
    from app.config import TH_BUDGETS, THINKING_DYNAMIC
    return genai_types.ThinkingConfig(thinking_budget=TH_BUDGETS.get(cfg.mode, THINKING_DYNAMIC))

def _gen_config(cfg: ChatCfg) -> genai_types.GenerateContentConfig:
    return genai_types.GenerateContentConfig(
        tools=build_tools(cfg),
        max_output_tokens=config.MAX_OUTPUT_TOKENS,
        thinking_config=_thinking_config(cfg),
        temperature=cfg.temp,
        top_p=cfg.top_p,
    )

def _parts_from_blobs(blobs: List[Tuple[bytes, str]]) -> List[genai_types.Part]:
    """Return parts; if total payload exceeds threshold, upload via Files API."""
    total = sum(len(b) for b, _ in blobs)
    parts: List[genai_types.Part] = []
    if total <= config.FILES_API_THRESHOLD_BYTES:
        for b, mime in blobs:
            parts.append(genai_types.Part.from_bytes(b, mime_type=mime))
        return parts

    # Large: use Files API
    cl = client()
    for b, mime in blobs:
        f = cl.files.upload(content=b, mime_type=mime)  # returns a file handle with a URI
        # Prefer using a file reference/URI part
        parts.append(genai_types.Part.from_uri(f.uri))
    return parts

def _compose_contents(prompt: str, cfg: ChatCfg, blobs: List[Tuple[bytes, str]] | None = None) -> List[genai_types.Content]:
    """Combine memory + current input into a single list of structured Content objects."""
    contents = build_memory_contents(cfg)
    user_parts: List[genai_types.Part] = []
    if prompt:
        user_parts.append(genai_types.Part.from_text(prompt))
    if blobs:
        user_parts.extend(_parts_from_blobs(blobs))
    if user_parts:
        contents.append(genai_types.Content(role="user", parts=user_parts))
    return contents

async def generate_text(prompt: str, cfg: ChatCfg) -> str:
    """Non-streaming generation (single response)."""
    def _call() -> str:
        cfg_obj = _gen_config(cfg)
        contents = _compose_contents(prompt, cfg)
        resp = client().models.generate_content(model=config.GEMINI_MODEL, contents=contents, config=cfg_obj)
        return resp.text or ""
    return await asyncio.to_thread(_call)

async def generate_multimodal(prompt: str, cfg: ChatCfg, blobs: List[Tuple[bytes, str]]) -> str:
    """Non-streaming generation with media."""
    def _call() -> str:
        cfg_obj = _gen_config(cfg)
        contents = _compose_contents(prompt, cfg, blobs=blobs)
        resp = client().models.generate_content(model=config.GEMINI_MODEL, contents=contents, config=cfg_obj)
        return resp.text or ""
    return await asyncio.to_thread(_call)

async def stream_generate(prompt: str, cfg: ChatCfg, blobs: List[Tuple[bytes, str]] | None = None) -> AsyncGenerator[str, None]:
    """
    Streaming generator yielding incremental text chunks.
    Falls back to one-shot generation if streaming is unavailable.
    """
    def _stream_call():
        cfg_obj = _gen_config(cfg)
        contents = _compose_contents(prompt, cfg, blobs=blobs)
        # Prefer stream API if available
        try:
            return client().models.generate_content_stream(model=config.GEMINI_MODEL, contents=contents, config=cfg_obj)
        except Exception:
            # Fallback: non-streaming
            return None

    stream = await asyncio.to_thread(_stream_call)
    if stream is None:
        # Fallback path
        text = await (generate_multimodal(prompt, cfg, blobs) if blobs else generate_text(prompt, cfg))
        if text:
            yield text
        return

    # Iterate streaming events
    def _iter_stream():
        try:
            for ev in stream:
                yield getattr(ev, "text", "") or ""
        except Exception:
            # Silently stop on streaming errors
            return

    for chunk in await asyncio.to_thread(lambda: list(_iter_stream())):
        if chunk:
            yield chunk
