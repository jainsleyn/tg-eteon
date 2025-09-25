
# ---- session memory ----
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Deque, List, Tuple
from collections import deque
import math

from google.genai import types as genai_types  # type: ignore

from app.config import MEMORY_TOKEN_LIMIT

def approx_tokens(s: str) -> int:
    """Cheap token approximator; avoids heavy dependencies."""
    return max(1, math.ceil(len(s) / 4))

@dataclass
class Msg:
    role: str   # "user" | "model"
    text: str
    toks: int

@dataclass
class ChatCfg:
    # ---- generation knobs ----
    mode: str = "dynamic"    # low|medium|high|dynamic
    temp: float = 1.0
    top_p: float = 0.8
    search: bool = True
    url: bool = False
    code: bool = False
    # ---- memory window ----
    history: Deque[Msg] = field(default_factory=deque)
    tokens_total: int = 0

    def reset(self) -> None:
        self.mode = "dynamic"
        self.temp = 1.0
        self.top_p = 0.8
        self.search = True
        self.url = False
        self.code = False
        self.history.clear()
        self.tokens_total = 0

def memory_append(cfg: ChatCfg, user_text: str, assistant_text: str) -> None:
    """Append a user+assistant turn and truncate to token limit."""
    ut = approx_tokens(user_text)
    at = approx_tokens(assistant_text)
    cfg.history.append(Msg(role="user", text=user_text, toks=ut))
    cfg.history.append(Msg(role="model", text=assistant_text, toks=at))
    cfg.tokens_total += (ut + at)
    while cfg.tokens_total > MEMORY_TOKEN_LIMIT and cfg.history:
        drop = cfg.history.popleft()
        cfg.tokens_total -= drop.toks

def build_memory_contents(cfg: ChatCfg) -> List[genai_types.Content]:
    """Return memory as a list of structured Content with roles, not concatenated strings."""
    if not cfg.history:
        return []
    contents: List[genai_types.Content] = []
    for m in cfg.history:
        contents.append(
            genai_types.Content(
                role=m.role,
                parts=[genai_types.Part.from_text(m.text)]
            )
        )
    return contents
