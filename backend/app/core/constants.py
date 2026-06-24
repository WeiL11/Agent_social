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
