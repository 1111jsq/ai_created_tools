from __future__ import annotations

from typing import Any, Dict


def get_from_path(obj: Any, path: str) -> Any:
    if not path:
        return obj
    cur = obj
    for part in [p for p in str(path).split(".") if p]:
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list):
            try:
                idx = int(part)
            except Exception:
                return None
            if idx < 0 or idx >= len(cur):
                return None
            cur = cur[idx]
        else:
            return None
    return cur


def render_value(val: Any, variables: Dict[str, Any]) -> Any:
    if isinstance(val, str):
        try:
            return val.format(**variables)
        except Exception:
            return val
    if isinstance(val, dict):
        return {k: render_value(v, variables) for k, v in val.items()}
    if isinstance(val, list):
        return [render_value(v, variables) for v in val]
    return val


