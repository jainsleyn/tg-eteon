
# ---- chunking (telegram-safe) ----
from typing import List
from app.config import TELEGRAM_CHUNK_SIZE, TELEGRAM_HARD_LIMIT

def chunk_text(text: str, soft_limit: int = TELEGRAM_CHUNK_SIZE, hard_limit: int = TELEGRAM_HARD_LIMIT) -> List[str]:
    if len(text) <= soft_limit:
        return [text]
    parts: List[str] = []
    cur = 0
    L = len(text)
    while cur < L:
        end = min(L, cur + soft_limit)
        # Prefer break on newline not too far from soft_limit
        break_at = text.rfind("\n", cur, end)
        if break_at == -1 or break_at < cur + int(0.5 * soft_limit):
            break_at = end
        parts.append(text[cur:break_at])
        cur = break_at
    # Safety: ensure none exceeds hard limit
    out: List[str] = []
    for p in parts:
        if len(p) <= hard_limit:
            out.append(p)
        else:
            # Split hard overflow defensively
            for i in range(0, len(p), hard_limit):
                out.append(p[i:i + hard_limit])
    return out
