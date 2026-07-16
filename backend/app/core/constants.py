"""Game constants seeded into data-driven tables. The `axes` registry and
archetypes live in Postgres so live-ops can extend them without a deploy; these
are just the v1 defaults used by the seeder."""

# Core 8 radar axes (v1). Extending = add a row to the `axes` table.
CORE_AXES: list[dict] = [
    {"id": "logic", "name": "邏輯", "category": "thinking"},
    {"id": "creativity", "name": "創意", "category": "thinking"},
    {"id": "knowledge", "name": "知識", "category": "thinking"},
    {"id": "curiosity", "name": "好奇心", "category": "thinking"},
    {"id": "empathy", "name": "同理", "category": "expression"},
    {"id": "humor", "name": "幽默", "category": "expression"},
    {"id": "grit", "name": "毅力", "category": "temperament"},
    {"id": "structure", "name": "條理", "category": "action"},
]

CORE_AXIS_IDS: list[str] = [a["id"] for a in CORE_AXES]
DEFAULT_AXIS_VALUE = 50

# Facet -> archetype mapping. Each archetype biases certain axes upward.
ARCHETYPES: list[dict] = [
    {"id": "analyst", "name": "分析者", "default_species": "robot",
     "bias": {"logic": 20, "structure": 15}},
    {"id": "artist", "name": "創作者", "default_species": "sprite",
     "bias": {"creativity": 20, "humor": 10}},
    {"id": "sage", "name": "智者", "default_species": "owl",
     "bias": {"knowledge": 20, "logic": 10}},
    {"id": "empath", "name": "共感者", "default_species": "fox",
     "bias": {"empathy": 20, "humor": 10}},
    {"id": "scholar", "name": "學徒", "default_species": "cat",
     "bias": {"curiosity": 20, "knowledge": 10}},
    {"id": "strategist", "name": "策士", "default_species": "wolf",
     "bias": {"structure": 20, "grit": 10}},
]

FACET_TO_ARCHETYPE: dict[str, str] = {
    "coding": "analyst",
    "analytical": "sage",
    "creative": "artist",
    "social": "empath",
    "learning": "scholar",
    "planning": "strategist",
}
DEFAULT_ARCHETYPE = "scholar"

# Controlled vocabulary for trait tags. Unknown tags from the self-extract JSON
# are dropped (injection / garbage defense).
TRAIT_WHITELIST: set[str] = {
    "curious", "systematic", "creative", "analytical", "empathetic", "humorous",
    "persistent", "organized", "bold", "patient", "pragmatic", "playful",
    "rigorous", "imaginative", "concise", "verbose", "exploratory", "focused",
    "collaborative", "independent", "skeptical", "optimistic",
}

VALID_FACETS: set[str] = set(FACET_TO_ARCHETYPE.keys())
MAX_FACETS = 4

# Topic lexicon: canonical tag -> aliases. Used by mission parsing/matching AND
# extraction (so a runner's sprite persona actually says 跑步 and is findable).
# Growing this list = better matching, zero code change elsewhere.
TOPIC_LEXICON: dict[str, list[str]] = {
    "跑步": ["跑步", "慢跑", "路跑", "晨跑", "夜跑", "馬拉松", "跑者", "跑友", "練跑",
           "配速", "running", "jog", "marathon"],
    "健身": ["健身", "重訓", "gym", "workout", "fitness", "肌力", "深蹲"],
    "登山": ["登山", "爬山", "健行", "hiking", "百岳", "野營"],
    "自行車": ["自行車", "單車", "騎車", "cycling", "bike"],
    "游泳": ["游泳", "swim"],
    "球類": ["籃球", "羽球", "網球", "排球", "桌球", "basketball", "badminton", "tennis"],
    "瑜珈": ["瑜珈", "yoga", "冥想", "meditation", "皮拉提斯"],
    "程式": ["程式", "寫code", "coding", "python", "javascript", "typescript",
           "後端", "前端", "工程師", "developer", "debug"],
    "ai": ["ai", "claude", "chatgpt", "gpt", "gemini", "llm", "prompt", "機器學習", "深度學習"],
    "ui設計": ["ui", "ux", "介面", "設計稿", "figma", "design", "設計"],
    "寫作": ["寫作", "寫文", "部落格", "小說", "writing", "blog", "文案", "寫詩", "詩"],
    "繪畫": ["畫畫", "繪畫", "插畫", "素描", "drawing", "illustration"],
    "音樂": ["音樂", "吉他", "鋼琴", "唱歌", "樂團", "music", "guitar", "piano"],
    "攝影": ["攝影", "拍照", "photography", "相機"],
    "遊戲": ["遊戲", "電玩", "game", "gaming", "桌遊", "boardgame"],
    "旅行": ["旅行", "旅遊", "出國", "travel", "backpack", "露營", "camping"],
    "咖啡": ["咖啡", "coffee", "手沖", "咖啡廳"],
    "美食": ["美食", "料理", "烹飪", "cooking", "烘焙", "baking", "煮飯", "做菜"],
    "語言": ["日文", "英文", "韓文", "語言交換", "japanese", "english", "korean"],
    "投資": ["投資", "股票", "理財", "invest", "stock", "crypto"],
    "閱讀": ["閱讀", "讀書", "書友", "reading", "書會"],
    "寵物": ["寵物", "貓", "狗", "pet"],
    "創業": ["創業", "副業", "startup", "side project", "產品"],
    # 校園季（開學/新生/返校）
    "校園新生": ["新生", "大一", "剛進大學", "剛入學", "freshman", "迎新", "直屬"],
    "讀書會": ["讀書會", "自習", "期中考", "期末考", "唸書", "study group", "圖書館唸"],
    "選課": ["選課", "修課", "課表", "通識", "加簽", "學分"],
    "社團": ["社團", "熱舞社", "吉他社", "系隊", "校隊", "系學會", "營隊"],
    "宿舍": ["宿舍", "室友", "住宿", "外宿", "roommate"],
    "實習": ["實習", "intern", "internship", "求職", "面試", "履歷"],
    "研究所": ["研究所", "推甄", "考研", "留學", "申請學校", "gre", "toefl", "碩士"],
}

# Generic words that must not become fallback tags.
TOPIC_STOPWORDS: set[str] = {
    "一起", "想找", "夥伴", "同好", "朋友", "幫我", "我想", "最近", "開始", "有沒",
    "沒有", "大家", "可以", "希望", "喜歡", "想要", "的人", "找人", "什麼", "怎麼",
}

# Human-readable facet labels (for matchmaking reasons, etc.)
FACET_LABELS: dict[str, str] = {
    "coding": "程式",
    "analytical": "分析",
    "creative": "創作",
    "social": "社交",
    "learning": "學習",
    "planning": "規劃",
}
