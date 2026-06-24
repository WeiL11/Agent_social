"""Deterministic SVG rendering of the layered-component avatar, the radar chart,
and a shareable character card. Pure functions of character data => same input
gives the same image, free and instant (the layered-system payoff)."""

import math

from app.core.constants import CORE_AXES

# Per-species palette + simple body silhouette. This is the v1 "parts library";
# real art swaps these primitives for designed assets, same composition model.
_SPECIES = {
    "robot": {"body": "#7c9cbf", "accent": "#3b5b7a", "shape": "square"},
    "sprite": {"body": "#b48ed6", "accent": "#7d4fa3", "shape": "drop"},
    "owl": {"body": "#c9a26b", "accent": "#7a5a30", "shape": "round"},
    "fox": {"body": "#e08a5b", "accent": "#a85327", "shape": "round"},
    "cat": {"body": "#9bb07f", "accent": "#5f7445", "shape": "round"},
    "wolf": {"body": "#8a92a6", "accent": "#4a5266", "shape": "round"},
}
_DEFAULT = {"body": "#9aa0a6", "accent": "#5f6368", "shape": "round"}


def _body_path(shape: str, cx: float, cy: float, r: float) -> str:
    if shape == "square":
        return f'<rect x="{cx-r}" y="{cy-r}" rx="{r*0.3}" width="{r*2}" height="{r*2}"'
    if shape == "drop":
        return f'<circle cx="{cx}" cy="{cy}" r="{r}"'  # simplified
    return f'<circle cx="{cx}" cy="{cy}" r="{r}"'


def render_avatar(character: dict, size: int = 160) -> str:
    species = (character.get("species") or "").lower()
    pal = _SPECIES.get(species, _DEFAULT)
    cx = cy = size / 2
    r = size * 0.32
    appearance = character.get("appearance") or {}
    has_hair = bool(appearance.get("hair"))
    eye = "#222"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">',
        f'<rect width="{size}" height="{size}" rx="16" fill="#f5f3fa"/>',
        # body
        f'{_body_path(pal["shape"], cx, cy+8, r)} fill="{pal["body"]}" stroke="{pal["accent"]}" stroke-width="3"/>',
        # ears / top accent
        f'<circle cx="{cx-r*0.6}" cy="{cy-r*0.7+8}" r="{r*0.28}" fill="{pal["accent"]}"/>',
        f'<circle cx="{cx+r*0.6}" cy="{cy-r*0.7+8}" r="{r*0.28}" fill="{pal["accent"]}"/>',
        # eyes
        f'<circle cx="{cx-r*0.35}" cy="{cy}" r="{r*0.12}" fill="{eye}"/>',
        f'<circle cx="{cx+r*0.35}" cy="{cy}" r="{r*0.12}" fill="{eye}"/>',
        # smile
        f'<path d="M {cx-r*0.3} {cy+r*0.35} Q {cx} {cy+r*0.65} {cx+r*0.3} {cy+r*0.35}" '
        f'stroke="{eye}" stroke-width="3" fill="none" stroke-linecap="round"/>',
    ]
    if has_hair:  # a small tuft to show the "hair" layer
        parts.append(f'<path d="M {cx-r*0.2} {cy-r+6} q {r*0.2} -{r*0.4} {r*0.4} 0" '
                     f'stroke="{pal["accent"]}" stroke-width="4" fill="none"/>')
    parts.append("</svg>")
    return "".join(parts)


def render_radar(radar: dict, size: int = 220) -> str:
    axes = [a["id"] for a in CORE_AXES]
    n = len(axes)
    cx = cy = size / 2
    rad = size * 0.36
    ring = (
        '<polygon points="'
        + " ".join(
            f"{cx+rad*math.cos(2*math.pi*i/n - math.pi/2):.1f},"
            f"{cy+rad*math.sin(2*math.pi*i/n - math.pi/2):.1f}"
            for i in range(n)
        )
        + '" fill="none" stroke="#ccc" stroke-width="1"/>'
    )
    pts = []
    for i, ax in enumerate(axes):
        v = max(0, min(100, int((radar or {}).get(ax, 0)))) / 100
        ang = 2 * math.pi * i / n - math.pi / 2
        pts.append(f"{cx+rad*v*math.cos(ang):.1f},{cy+rad*v*math.sin(ang):.1f}")
    poly = f'<polygon points="{" ".join(pts)}" fill="#7c5cff55" stroke="#7c5cff" stroke-width="2"/>'
    labels = []
    for i, a in enumerate(CORE_AXES):
        ang = 2 * math.pi * i / n - math.pi / 2
        lx = cx + (rad + 14) * math.cos(ang)
        ly = cy + (rad + 14) * math.sin(ang)
        labels.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="11" fill="#555" '
            f'text-anchor="middle" dominant-baseline="middle">{a["name"]}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}">{ring}{poly}{"".join(labels)}</svg>'
    )


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_card(character: dict, owner_handle: str = "", width: int = 480, height: int = 260) -> str:
    """Composite shareable card: avatar + radar + name/persona. The artifact you
    get when you share a character to a friend or via public link."""
    name = _esc(character.get("name") or character.get("species") or "夥伴")
    persona = _esc((character.get("persona") or "")[:60])
    archetype = _esc(character.get("archetype") or "")
    avatar = render_avatar(character, size=140)
    radar = render_radar(character.get("radar") or {}, size=180)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">'
        f'<rect width="{width}" height="{height}" rx="20" fill="#ffffff" stroke="#e6e2f0" stroke-width="2"/>'
        f'<g transform="translate(16,40)">{avatar}</g>'
        f'<g transform="translate(280,30)">{radar}</g>'
        f'<text x="16" y="26" font-size="18" font-weight="700" fill="#2a2440">{name}</text>'
        f'<text x="170" y="195" font-size="12" fill="#7c5cff">{archetype} · Lv{character.get("level",1)}</text>'
        f'<text x="16" y="210" font-size="12" fill="#555">{persona}</text>'
        f'<text x="16" y="236" font-size="11" fill="#aaa">@{_esc(owner_handle)} · AI Persona Game</text>'
        f"</svg>"
    )
