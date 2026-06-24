"""A-system growth. Applying dispatch rewards bumps xp/level. Kept tiny and
pure-ish so it's easy to tune; never touches B-system (community) numbers."""

XP_PER_LEVEL = 100


def level_for_xp(xp: int) -> int:
    return 1 + max(0, xp) // XP_PER_LEVEL


def apply_rewards(character, rewards: dict) -> dict:
    """Mutates the character ORM object. Returns a summary for the response."""
    gained = int(rewards.get("xp", 0))
    character.xp = (character.xp or 0) + gained
    character.level = level_for_xp(character.xp)
    return {"xp_gained": gained, "xp": character.xp, "level": character.level}
