"""Share a character to a specific friend or via a public link/token. Public
token endpoints (no auth) back the shareable link + card image."""

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.character import Character
from app.models.social import CharacterShare, Friendship
from app.models.user import User
from app.schemas.social import SharedCharacterOut, ShareIn, ShareOut
from app.services.svg import render_card

router = APIRouter(tags=["share"])


def _are_friends(db: Session, a: uuid.UUID, b: uuid.UUID) -> bool:
    fr = db.scalar(
        select(Friendship).where(
            Friendship.status == "accepted",
            or_(
                (Friendship.requester_id == a) & (Friendship.addressee_id == b),
                (Friendship.requester_id == b) & (Friendship.addressee_id == a),
            ),
        )
    )
    return fr is not None


@router.post("/characters/{character_id}/share", response_model=ShareOut)
def share_character(character_id: uuid.UUID, body: ShareIn, request: Request,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    char = db.get(Character, character_id)
    if char is None or char.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "character not found")

    shared_with = None
    is_public = body.target == "public"
    if not is_public:
        try:
            shared_with = uuid.UUID(body.target)
        except ValueError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "target must be 'public' or a user id") from exc
        if not _are_friends(db, user.id, shared_with):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "can only share to accepted friends")

    token = secrets.token_urlsafe(12)
    share = CharacterShare(character_id=character_id, owner_id=user.id,
                           shared_with_user_id=shared_with, token=token, is_public=is_public)
    db.add(share)
    db.commit()
    base = str(request.base_url).rstrip("/")
    return ShareOut(token=token, is_public=is_public, url=f"/shared/{token}",
                    card_url=f"{base}/shared/{token}/card.svg")


def _load_share(token: str, db: Session) -> tuple[CharacterShare, Character]:
    share = db.scalar(select(CharacterShare).where(CharacterShare.token == token))
    if share is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "share not found")
    char = db.get(Character, share.character_id)
    if char is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "character gone")
    return share, char


@router.get("/shared/{token}", response_model=SharedCharacterOut)
def view_shared(token: str, db: Session = Depends(get_db)):
    _, char = _load_share(token, db)
    owner = db.get(User, char.owner_id)
    return SharedCharacterOut(
        name=char.name, species=char.species, archetype=char.archetype,
        radar=char.radar, trait_tags=char.trait_tags, persona=char.persona,
        level=char.level, owner_handle=owner.handle if owner else "",
    )


@router.get("/shared/{token}/card.svg")
def shared_card(token: str, db: Session = Depends(get_db)):
    _, char = _load_share(token, db)
    owner = db.get(User, char.owner_id)
    data = {"name": char.name, "species": char.species, "archetype": char.archetype,
            "radar": char.radar, "persona": char.persona, "appearance": char.appearance,
            "level": char.level}
    return Response(render_card(data, owner.handle if owner else ""), media_type="image/svg+xml")


@router.get("/shared", response_model=list[SharedCharacterOut])
def shared_with_me(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Characters friends have explicitly shared with me."""
    shares = db.scalars(
        select(CharacterShare).where(CharacterShare.shared_with_user_id == user.id)
    )
    out: list[SharedCharacterOut] = []
    for s in shares:
        char = db.get(Character, s.character_id)
        if char is None:
            continue
        owner = db.get(User, char.owner_id)
        out.append(SharedCharacterOut(
            name=char.name, species=char.species, archetype=char.archetype,
            radar=char.radar, trait_tags=char.trait_tags, persona=char.persona,
            level=char.level, owner_handle=owner.handle if owner else "",
        ))
    return out
