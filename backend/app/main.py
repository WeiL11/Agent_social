from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_admin,
    routes_character_friends,
    routes_characters,
    routes_dispatch,
    routes_health,
    routes_matches,
    routes_me,
    routes_profiles,
    routes_render,
    routes_share,
    routes_social,
)
from app.core.config import settings

app = FastAPI(title="AI Persona Game API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_health.router)
app.include_router(routes_profiles.router)
app.include_router(routes_characters.router)
app.include_router(routes_character_friends.router)
app.include_router(routes_dispatch.router)
app.include_router(routes_render.router)
app.include_router(routes_matches.router)
app.include_router(routes_me.router)
app.include_router(routes_social.router)
app.include_router(routes_share.router)
app.include_router(routes_admin.router)
