"""Mission engine: parse a goal ("我想找一起跑步的人") into kind+tags, match it
against IN-PLATFORM candidates, and write the sprite's first-person report.

Matching (pure function, testable):
  ① mutual-goal: other users' active missions with overlapping tags — the
     strongest signal (you both want the same thing).
  ② sprite-match: characters whose persona/traits/facet mention the tags
     ("有這個經驗的小精靈").
  compatibility() is only a tie-break bonus. Owner identity stays hidden in
  results; connection happens through the existing wave bridge."""

import json
import re

import httpx

from app.core.constants import FACET_LABELS, TOPIC_LEXICON, TOPIC_STOPWORDS
from app.services.deid import scrub
from app.services.matchmaking import compatibility

# ---------- parsing ----------

_KIND_RULES = [
    ("find_group", ["社團", "團體", "俱樂部", "群組", "社群", "group", "club", "community", "meetup"]),
    ("find_experience", ["經驗", "分享", "心得", "案例", "怎麼做", "教學", "experience", "advice", "tips"]),
    ("find_people", ["找人", "夥伴", "朋友", "同好", "一起", "伴", "partner", "buddy", "people", "someone"]),
]

_VALID_KINDS = {"find_people", "find_group", "find_experience", "auto"}


def _cjk_bigram_fallback(text: str) -> list[str]:
    """When the lexicon misses entirely, fall back to CJK bigrams from the query
    (minus generic words) so two people asking for the same niche thing still
    overlap on raw substrings."""
    cjk = re.findall(r"[一-鿿]{2,}", text)
    grams: list[str] = []
    for chunk in cjk:
        for i in range(len(chunk) - 1):
            g = chunk[i:i + 2]
            if g not in TOPIC_STOPWORDS and g not in grams:
                grams.append(g)
    return grams[:6]


def parse_mission_rules(text: str) -> dict:
    low = text.lower()
    kind = "auto"
    for k, words in _KIND_RULES:
        if any(w in low for w in words):
            kind = k
            break
    tags = [tag for tag, aliases in TOPIC_LEXICON.items()
            if any(a in low for a in aliases)]
    # free-form english tokens as extra tags (e.g. niche tools)
    extra = [w for w in re.findall(r"[a-z][a-z0-9+#.-]{2,15}", low)
             if w not in {"the", "and", "for", "with", "want", "find", "help"}]
    for w in extra[:4]:
        if w not in tags and not any(w in als for als in TOPIC_LEXICON.values()):
            tags.append(w)
    if not tags:  # lexicon miss -> raw CJK bigrams so niche goals still overlap
        tags = _cjk_bigram_fallback(low)
    return {"kind": kind, "tags": tags[:8]}


_GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
               "gemini-2.5-flash:generateContent")


def parse_mission_gemini(text: str, api_key: str) -> dict | None:
    prompt = (
        "使用者要小精靈幫忙找同好。分析這句需求，只輸出 JSON：\n"
        '{"kind":"find_people|find_group|find_experience","tags":["最多8個主題標籤，'
        '小寫，中文或英文單詞，例如 跑步 ui設計 python"]}\n需求：' + text[:2000]
    )
    try:
        r = httpx.post(_GEMINI_URL, params={"key": api_key},
                       json={"contents": [{"parts": [{"text": prompt}]}],
                             "generationConfig": {"temperature": 0.1,
                                                  "responseMimeType": "application/json"}},
                       timeout=20.0)
        r.raise_for_status()
        data = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
        kind = data.get("kind") if data.get("kind") in _VALID_KINDS else "auto"
        tags = [str(t).lower().strip()[:20] for t in (data.get("tags") or []) if str(t).strip()][:8]
        if not tags:
            return None
        return {"kind": kind, "tags": tags}
    except Exception:
        return None


def parse_mission(text: str, api_key: str | None) -> tuple[dict, str]:
    clean = scrub(text) or ""
    if api_key:
        out = parse_mission_gemini(clean, api_key)
        if out:
            # merge rule tags so lexicon matching still works cross-user
            rules = parse_mission_rules(clean)
            merged = list(dict.fromkeys(out["tags"] + rules["tags"]))[:10]
            return {"kind": out["kind"] if out["kind"] != "auto" else rules["kind"],
                    "tags": merged}, "gemini"
    return parse_mission_rules(clean), "rules"


# ---------- matching (pure) ----------

def _char_text(c: dict) -> str:
    parts = [c.get("persona") or "", " ".join(c.get("trait_tags") or []),
             FACET_LABELS.get(c.get("facet"), c.get("facet") or "")]
    return " ".join(parts).lower()


def _tag_hits(tags: list[str], text: str) -> list[str]:
    hits = []
    for t in tags:
        aliases = TOPIC_LEXICON.get(t, [t])
        if any(a.lower() in text for a in aliases):
            hits.append(t)
    return hits


def match_mission(mission: dict, my_char: dict, other_missions: list[dict],
                  other_chars: list[dict], weights: dict, axis_ids: list[str],
                  limit: int = 10) -> list[dict]:
    """mission: {tags, query_text}. other_missions: [{tags, query_text, character:{...}}].
    other_chars: [{...character dicts...}] (strangers, discoverable). Returns
    ranked result items; at most one item per owner (best wins)."""
    tags = mission.get("tags") or []
    best_per_owner: dict[str, dict] = {}

    def consider(item: dict, owner_key: str):
        cur = best_per_owner.get(owner_key)
        if cur is None or item["score"] > cur["score"]:
            best_per_owner[owner_key] = item

    # ① mutual goals
    for om in other_missions:
        oc = om.get("character") or {}
        overlap = sorted(set(tags) & set(om.get("tags") or []))
        if not overlap:
            continue
        comp = compatibility(my_char, oc, weights, axis_ids)["score"]
        score = min(98, 55 + 12 * len(overlap) + comp // 10)
        consider({
            "type": "mutual_goal",
            "character_id": str(oc.get("id")),
            "score": score,
            "reasons": [f"對方也在找：「{(om.get('query_text') or '')[:40]}」",
                        "共同主題：" + "、".join(overlap)],
            "matched_tags": overlap,
        }, str(oc.get("owner_id")))

    # ② sprite profile matches
    for oc in other_chars:
        hits = _tag_hits(tags, _char_text(oc))
        if not hits:
            continue
        comp = compatibility(my_char, oc, weights, axis_ids)["score"]
        score = min(90, 35 + 12 * len(hits) + comp // 8)
        consider({
            "type": "sprite_match",
            "character_id": str(oc.get("id")),
            "score": score,
            "reasons": ["牠的簡介提到：" + "、".join(hits)],
            "matched_tags": hits,
        }, str(oc.get("owner_id")))

    items = sorted(best_per_owner.values(), key=lambda x: x["score"], reverse=True)
    return items[:limit]


# ---------- report ----------

def report_text(my_char_name: str, query_text: str, items: list[dict]) -> str:
    name = my_char_name or "小精靈"
    if not items:
        return (f"{name} 出去繞了一圈：關於「{query_text[:30]}」，站上暫時沒找到同好。"
                "等新朋友加入我再去看看，明天可以再讓我跑一次！")
    n = len(items)
    mutual = sum(1 for i in items if i["type"] == "mutual_goal")
    parts = [f"{name} 回報：關於「{query_text[:30]}」，我找到 {n} 個可能的同好！"]
    if mutual:
        parts.append(f"其中 {mutual} 位跟你在找同一件事（最有機會！）。")
    parts.append("喜歡的話就揮手，對方也揮手你們就能聊了。")
    return "".join(parts)
