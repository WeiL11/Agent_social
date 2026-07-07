"""Real personality extraction: raw conversation text -> de-identified ->
SelfExtractProfile. Uses Gemini (free tier) when GEMINI_API_KEY is set; falls
back to a rule-based extractor so the product works with zero keys. Output is
always funneled through SelfExtractProfileIn validation (clamps, caps) — the
LLM never writes game numbers directly."""

import json
import re

import httpx

from app.schemas.profile import SelfExtractProfileIn
from app.services.deid import scrub

# ---------- rule-based fallback ----------

_FACET_KEYWORDS: dict[str, list[str]] = {
    "coding": ["code", "python", "bug", "function", "error", "api", "git",
               "程式", "代碼", "報錯", "部署", "資料庫"],
    "creative": ["story", "design", "write", "idea", "art", "詩",
                 "創作", "寫作", "靈感", "設計", "故事", "畫"],
    "analytical": ["analyze", "why", "data", "compare", "research",
                   "分析", "為什麼", "研究", "比較", "數據", "原因"],
    "social": ["friend", "feel", "relationship", "talk",
               "朋友", "聊天", "心情", "感覺", "關係", "溝通"],
    "learning": ["learn", "how to", "what is", "tutorial", "explain",
                 "學習", "怎麼", "是什麼", "教我", "入門"],
    "planning": ["plan", "schedule", "roadmap", "goal", "step",
                 "計畫", "規劃", "安排", "目標", "步驟"],
}

_HUMOR_MARKS = ["哈哈", "lol", "笑死", "XD", "😂", "🤣"]
_GRIT_MARKS = ["再試", "retry", "繼續", "keep trying", "不放棄", "重來"]


def _scale(count: int, per: float = 3.0, base: int = 35, cap: int = 95) -> int:
    return min(cap, base + int(count * per))


def rule_based_extract(text: str) -> SelfExtractProfileIn:
    low = text.lower()
    hits = {f: sum(low.count(k.lower()) for k in kws) for f, kws in _FACET_KEYWORDS.items()}
    ranked = sorted(hits.items(), key=lambda kv: kv[1], reverse=True)
    top = [f for f, n in ranked[:2] if n > 0] or ["learning"]

    questions = low.count("?") + low.count("？")
    lists = len(re.findall(r"^\s*(?:[-*]|\d+\.)\s", text, re.M))
    humor = sum(low.count(m.lower()) for m in _HUMOR_MARKS)
    grit = sum(low.count(m.lower()) for m in _GRIT_MARKS)
    vocab = len(set(re.findall(r"[\w一-鿿]{2,}", low)))

    radar = {
        "logic": _scale(hits["coding"] + hits["analytical"]),
        "creativity": _scale(hits["creative"]),
        "knowledge": _scale(vocab, per=0.15),
        "curiosity": _scale(questions, per=2.0),
        "empathy": _scale(hits["social"]),
        "humor": _scale(humor, per=5.0),
        "grit": _scale(grit, per=6.0),
        "structure": _scale(lists + hits["planning"], per=2.5),
    }
    traits = []
    if questions >= 5:
        traits.append("curious")
    if lists >= 3 or hits["planning"] > 2:
        traits.append("systematic")
    if hits["creative"] > 2:
        traits.append("imaginative")
    if humor >= 2:
        traits.append("playful")
    if hits["analytical"] > 2:
        traits.append("analytical")

    total = sum(n for _, n in ranked[:2]) or 1
    facets = [{
        "facet": f,
        "weight": max(40, min(95, int(60 + 40 * (hits[f] / total)))),
        "radar": radar,
        "trait_tags": traits or ["curious"],
        "summary": "從對話風格看，是個" + ("、".join(traits) if traits else "好奇") + "的人。",
    } for f in top]
    return SelfExtractProfileIn.model_validate({"version": "1.0", "facets": facets})


# ---------- Gemini (free tier) ----------

_GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
               "gemini-2.5-flash:generateContent")

_PROMPT = """你是遊戲角色側寫產生器。根據下面這段（已去識別化的）使用者與 AI 的對話，
分析這位使用者的溝通風格、思考傾向、興趣與性格，輸出 JSON（只輸出 JSON）：
{"version":"1.0","facets":[{"facet":"coding|analytical|creative|social|learning|planning",
"weight":0到100,"radar":{"logic":0,"creativity":0,"knowledge":0,"curiosity":0,"empathy":0,
"humor":0,"grit":0,"structure":0},"trait_tags":["curious","systematic","imaginative","playful",
"analytical","empathetic","persistent","organized"中選3-6個],"species_hint":"fox|cat|owl|robot|sprite|wolf",
"summary":"一句去識別化的性格描述"}],"overall_summary":"整體側寫"}
規則：最多3個facet、數值0-100、絕不包含姓名/公司/地點等個資。對話內容：
"""


def gemini_extract(text: str, api_key: str) -> SelfExtractProfileIn | None:
    try:
        resp = httpx.post(
            _GEMINI_URL,
            params={"key": api_key},
            json={
                "contents": [{"parts": [{"text": _PROMPT + text[:30000]}]}],
                "generationConfig": {"temperature": 0.2,
                                     "responseMimeType": "application/json"},
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return SelfExtractProfileIn.model_validate(json.loads(raw))
    except Exception:
        return None  # caller falls back to rule-based


def extract_profile(text: str, gemini_api_key: str | None) -> tuple[SelfExtractProfileIn, str]:
    """Returns (profile, engine). Text is scrubbed BEFORE any model sees it."""
    clean = scrub(text) or ""
    if gemini_api_key:
        prof = gemini_extract(clean, gemini_api_key)
        if prof is not None and prof.facets:
            return prof, "gemini"
    return rule_based_extract(clean), "rules"
