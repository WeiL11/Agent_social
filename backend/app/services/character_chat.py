"""Generate a SHORT auto-conversation between two creatures + a one-line summary.
Bounded by `turns` to cap cost. llm_provider="none" => deterministic templated
banter (free, offline); a real provider can be plugged in later behind the same
interface, still bounded + structured."""

from app.core.constants import CORE_AXES, FACET_LABELS

_AXIS_NAME = {a["id"]: a["name"] for a in CORE_AXES}


def _dominant_axis(radar: dict) -> str:
    if not radar:
        return "好奇心"
    top = max(radar.items(), key=lambda kv: kv[1])[0]
    return _AXIS_NAME.get(top, top)


def _name(c: dict) -> str:
    return c.get("name") or "小夥伴"


def _cid(c: dict) -> str | None:
    cid = c.get("id")
    return str(cid) if cid is not None else None  # JSONB-safe


def _templated(a: dict, b: dict, turns: int) -> dict:
    na, nb = _name(a), _name(b)
    fa = FACET_LABELS.get(a.get("facet"), "生活")
    fb = FACET_LABELS.get(b.get("facet"), "生活")
    axa, axb = _dominant_axis(a.get("radar") or {}), _dominant_axis(b.get("radar") or {})
    shared = sorted(set(a.get("trait_tags") or []) & set(b.get("trait_tags") or []))

    pool_a = [
        f"嗨 {nb}！我最近都在玩{fa}的東西。",
        f"我覺得我最強的是{axa}耶，你呢？",
        (f"我們都有「{shared[0]}」這個特質，難怪聊得來！" if shared
         else f"你的{axb}聽起來好厲害，可以教我嗎？"),
        "下次一起出任務吧！",
    ]
    pool_b = [
        f"{na} 你好～我比較常碰{fb}。",
        f"我大概是{axb}吧，不過{axa}也想練一下。",
        "哈哈對啊，感覺很合拍！",
        "好喔，一言為定！",
    ]
    cida, cidb = _cid(a), _cid(b)
    transcript = []
    for i in range(turns):
        transcript.append({"speaker": na, "character_id": cida, "text": pool_a[i % len(pool_a)]})
        transcript.append({"speaker": nb, "character_id": cidb, "text": pool_b[i % len(pool_b)]})

    vibe = "一拍即合" if shared else "互相好奇"
    summary = f"{na} 和 {nb} 聊了{fa}與{fb}，氣氛{vibe}。"
    return {"transcript": transcript, "summary": summary}


def generate_chat(a: dict, b: dict, turns: int, llm_provider: str = "none") -> dict:
    turns = max(1, min(turns, 5))  # hard cap: keep it short
    # llm_provider != "none" would call a bounded structured LLM here; fall back
    # to the templated banter for now (free, deterministic).
    return _templated(a, b, turns)
