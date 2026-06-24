from app.services.deid import scrub
from app.services.svg import render_avatar, render_card, render_radar


def test_deid_scrubs_pii():
    out = scrub("mail me a@b.com or call +1 415 555 1234 key sk-abcd1234efgh")
    assert "a@b.com" not in out
    assert "[EMAIL]" in out
    assert "[PHONE]" in out
    assert "[SECRET]" in out


def test_deid_none_passthrough():
    assert scrub(None) is None


def test_svg_renders_valid_markup():
    char = {"name": "小邏輯", "species": "robot", "archetype": "analyst",
            "radar": {"logic": 80, "creativity": 40}, "persona": "p", "appearance": {"hair": "x"},
            "level": 1}
    for svg in (render_avatar(char), render_radar(char["radar"]), render_card(char, "alice")):
        assert svg.startswith("<svg")
        assert svg.rstrip().endswith("</svg>")
