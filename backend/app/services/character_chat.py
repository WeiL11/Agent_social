"""Generate a SHORT auto-conversation between two creatures + a one-line summary.
Bounded by `turns` to cap cost. Two engines behind one interface:
- template (free, deterministic, always available — also the fallback)
- Gemini (when an api_key is passed in; personality-aware, unique per encounter)
Either way the transcript length is hard-capped and only JSONB-safe data is
returned; the LLM never touches game numbers."""

import json

import httpx

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


_GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
               "gemini-2.5-flash:generateContent")


def _profile_line(c: dict) -> str:
    radar = c.get("radar") or {}
    tops = sorted(radar.items(), key=lambda kv: kv[1], reverse=True)[:3]
    axes = "、".join(f"{_AXIS_NAME.get(k, k)}{v}" for k, v in tops)
    traits = "、".join(c.get("trait_tags") or []) or "無"
    facet = FACET_LABELS.get(c.get("facet"), c.get("facet") or "生活")
    return f"{_name(c)}（領域：{facet}；強項：{axes}；特質：{traits}）"


def _gemini(a: dict, b: dict, turns: int, api_key: str) -> dict | None:
    prompt = (
        f"兩隻遊戲小精靈初次相遇。A={_profile_line(a)}；B={_profile_line(b)}。\n"
        f"寫一段可愛自然的繁體中文對話，剛好 {turns * 2} 句（A、B 輪流，A 先開口），"
        "每句不超過 40 字，內容要呼應彼此的領域/強項/特質，不提個資。"
        "最後給一句 30 字內的第三人稱摘要。只輸出 JSON："
        '{"lines":[{"speaker":"A或B","text":"..."}],"summary":"..."}'
    )
    try:
        resp = httpx.post(
            _GEMINI_URL, params={"key": api_key},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0.9,
                                       "responseMimeType": "application/json"}},
            timeout=25.0,
        )
        resp.raise_for_status()
        data = json.loads(resp.json()["candidates"][0]["content"]["parts"][0]["text"])
        lines = data.get("lines") or []
        if not lines:
            return None
        cida, cidb = _cid(a), _cid(b)
        transcript = [{
            "speaker": _name(a) if ln.get("speaker") == "A" else _name(b),
            "character_id": cida if ln.get("speaker") == "A" else cidb,
            "text": str(ln.get("text", ""))[:120],
        } for ln in lines[: turns * 2]]  # hard cap length
        summary = str(data.get("summary") or "")[:80] or None
        return {"transcript": transcript, "summary": summary}
    except Exception:
        return None  # caller falls back to template


def generate_chat(a: dict, b: dict, turns: int, llm_provider: str = "none",
                  api_key: str | None = None) -> dict:
    turns = max(1, min(turns, 5))  # hard cap: keep it short
    if api_key:
        out = _gemini(a, b, turns, api_key)
        if out and out.get("summary"):
            return out
    return _templated(a, b, turns)
