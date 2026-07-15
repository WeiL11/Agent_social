"""Reply engine for talking to your OWN sprite. Gemini (persona-conditioned)
when a key is provided; otherwise a personality-flavored template. Also detects
"looking for..." intents so the frontend can offer one-tap mission creation."""

import json

import httpx

from app.core.constants import CORE_AXES, FACET_LABELS

_AXIS_NAME = {a["id"]: a["name"] for a in CORE_AXES}
_INTENT_WORDS = ["想找", "找人", "推薦", "哪裡有", "有沒有人", "幫我找", "想認識", "同好", "夥伴"]

_GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
               "gemini-2.5-flash:generateContent")


def detect_mission_intent(msg: str) -> bool:
    return any(w in msg for w in _INTENT_WORDS)


def _persona_prompt(c: dict) -> str:
    radar = c.get("radar") or {}
    tops = sorted(radar.items(), key=lambda kv: kv[1], reverse=True)[:3]
    axes = "、".join(f"{_AXIS_NAME.get(k, k)}" for k, _ in tops)
    return (
        f"你是一隻叫「{c.get('name') or '小夥伴'}」的遊戲小精靈，是主人性格的分身。"
        f"你的領域是{FACET_LABELS.get(c.get('facet'), '生活')}、強項是{axes}、"
        f"特質是{'、'.join(c.get('trait_tags') or []) or '好奇'}。人設：{c.get('persona') or ''}。"
        "用可愛、自然、口語的繁體中文回覆主人，1-2 句、不超過 60 字，"
        "像親近的小夥伴，不要說教、不要提到你是 AI。"
    )


def _gemini_reply(c: dict, history: list[dict], msg: str, api_key: str) -> str | None:
    convo = "\n".join(f"{'主人' if h['role'] == 'user' else '你'}：{h['text']}" for h in history[-10:])
    prompt = (_persona_prompt(c) + "\n\n最近的對話：\n" + convo +
              f"\n主人：{msg}\n只輸出 JSON：{{\"reply\":\"你的回覆\"}}")
    try:
        r = httpx.post(_GEMINI_URL, params={"key": api_key},
                       json={"contents": [{"parts": [{"text": prompt}]}],
                             "generationConfig": {"temperature": 0.8,
                                                  "responseMimeType": "application/json"}},
                       timeout=20.0)
        r.raise_for_status()
        data = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
        reply = str(data.get("reply") or "").strip()
        return reply[:200] or None
    except Exception:
        return None


def _template_reply(c: dict, msg: str) -> str:
    name = c.get("name") or "我"
    radar = c.get("radar") or {}
    top = max(radar.items(), key=lambda kv: kv[1])[0] if radar else "curiosity"
    flavor = {
        "logic": "讓我拆解一下…聽起來有點意思！",
        "creativity": "哇，這給了我一個靈感！",
        "knowledge": "這個我好像在哪讀過，跟我多說一點？",
        "curiosity": "欸～然後呢然後呢？",
        "empathy": "我懂你的感覺，跟我說說吧。",
        "humor": "哈哈這個我喜歡 XD",
        "grit": "不管怎樣，我們一起想辦法！",
        "structure": "我們一步一步來整理看看。",
    }.get(top, "跟我多說一點嘛！")
    base = f"{flavor}"
    if detect_mission_intent(msg):
        base += f" 對了——要不要我幫你去找？把需求交給{name}當任務吧！"
    return base


def sprite_reply(c: dict, history: list[dict], msg: str, api_key: str | None) -> dict:
    """Returns {text, suggest_mission}."""
    suggest = detect_mission_intent(msg)
    if api_key:
        out = _gemini_reply(c, history, msg, api_key)
        if out:
            if suggest:
                out += " （要我幫你去找嗎？交給我一個任務！）"
            return {"text": out, "suggest_mission": suggest}
    return {"text": _template_reply(c, msg), "suggest_mission": suggest}
