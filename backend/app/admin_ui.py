"""Operations backend UI via sqladmin — auto-generated admin screens over the
models (browse/search/edit users, characters, scenarios, moderation, reports…).
Mounted at /ops, password-gated. CHANGE admin_ui_password + secret_key in prod."""

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.config import settings
from app.models.admin import AuditLog, GameConfig, ModerationItem
from app.models.catalog import Archetype, Axis
from app.models.character import Character, PersonalityProfile
from app.models.community import Report
from app.models.dispatch import Dispatch, Scenario
from app.models.message import Message
from app.models.social import Friendship
from app.models.user import User


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        if form.get("password") == settings.admin_ui_password:
            request.session["ops_admin"] = True
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("ops_admin") is True


class UserAdmin(ModelView, model=User):
    column_list = [User.handle, User.email, User.discoverable, User.is_banned, User.created_at]
    column_searchable_list = [User.handle, User.email]
    name_plural = "Users"


class CharacterAdmin(ModelView, model=Character):
    column_list = [Character.name, Character.species, Character.archetype,
                   Character.facet, Character.level, Character.xp, Character.status]
    column_searchable_list = [Character.name]


class ScenarioAdmin(ModelView, model=Scenario):
    column_list = [Scenario.key, Scenario.title, Scenario.type, Scenario.art, Scenario.active]
    column_searchable_list = [Scenario.key, Scenario.title]


class ModerationAdmin(ModelView, model=ModerationItem):
    column_list = [ModerationItem.kind, ModerationItem.ref_id, ModerationItem.status,
                   ModerationItem.created_at]


class ReportAdmin(ModelView, model=Report):
    column_list = [Report.target_type, Report.target_id, Report.status, Report.created_at]


class GameConfigAdmin(ModelView, model=GameConfig):
    column_list = [GameConfig.key, GameConfig.value]


class AuditLogAdmin(ModelView, model=AuditLog):
    column_list = [AuditLog.action, AuditLog.actor_id, AuditLog.target, AuditLog.created_at]
    can_create = can_edit = can_delete = False


# Read-only browse views.
class ProfileAdmin(ModelView, model=PersonalityProfile):
    column_list = [PersonalityProfile.facet, PersonalityProfile.source, PersonalityProfile.created_at]
    can_create = can_edit = can_delete = False


class DispatchAdmin(ModelView, model=Dispatch):
    column_list = [Dispatch.scenario_id, Dispatch.outcome, Dispatch.created_at]
    can_create = can_edit = can_delete = False


class FriendshipAdmin(ModelView, model=Friendship):
    column_list = [Friendship.requester_id, Friendship.addressee_id, Friendship.status]
    can_create = can_edit = can_delete = False


class MessageAdmin(ModelView, model=Message):
    column_list = [Message.from_user_id, Message.to_user_id, Message.created_at]
    can_create = can_edit = can_delete = False


class AxisAdmin(ModelView, model=Axis):
    column_list = [Axis.id, Axis.name, Axis.category, Axis.active]


class ArchetypeAdmin(ModelView, model=Archetype):
    column_list = [Archetype.id, Archetype.name, Archetype.default_species]


def setup_admin(app, engine) -> None:
    backend = AdminAuth(secret_key=settings.secret_key)
    admin = Admin(app, engine, authentication_backend=backend,
                  base_url="/ops", title="AI Persona Ops")
    for view in (UserAdmin, CharacterAdmin, ScenarioAdmin, ModerationAdmin, ReportAdmin,
                 GameConfigAdmin, AuditLogAdmin, ProfileAdmin, DispatchAdmin, FriendshipAdmin,
                 MessageAdmin, AxisAdmin, ArchetypeAdmin):
        admin.add_view(view)
