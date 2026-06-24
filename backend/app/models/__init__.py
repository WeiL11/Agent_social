"""Import all models so Base.metadata is fully populated for create_all /
Alembic autogenerate."""

from app.models.admin import AdminUser, AuditLog, GameConfig, ModerationItem
from app.models.base import Base
from app.models.catalog import Archetype, AvatarPart, Axis
from app.models.character import Character, PersonalityProfile
from app.models.community import (
    Achievement,
    Cohort,
    CommunityScore,
    EventContribution,
    Membership,
    PopulationStat,
    Report,
    Season,
    SharedEvent,
    UserAchievement,
)
from app.models.dispatch import Dispatch, Scenario
from app.models.ingestion import Upload
from app.models.social import CharacterShare, Friendship
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Axis",
    "Archetype",
    "AvatarPart",
    "PersonalityProfile",
    "Character",
    "Scenario",
    "Dispatch",
    "Upload",
    "Season",
    "CommunityScore",
    "PopulationStat",
    "SharedEvent",
    "EventContribution",
    "Achievement",
    "UserAchievement",
    "Cohort",
    "Membership",
    "Report",
    "AdminUser",
    "AuditLog",
    "ModerationItem",
    "GameConfig",
    "Friendship",
    "CharacterShare",
]
