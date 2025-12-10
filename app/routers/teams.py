import secrets
import string
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_openid
from ..config import settings
from ..database import get_db
from ..models import Team
from ..schemas import (
    JoinTeamRequest,
    MessageResponse,
    RemoveMemberRequest,
    RenameTeamRequest,
    TeamCreate,
    TeamOut,
    TeamResponse,
    TeamsResponse,
)

router = APIRouter(prefix="/teams", tags=["teams"])


def generate_invite_code(length: int) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_team_or_404(db: Session, team_id: str) -> Team:
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


def ensure_team_member(team: Team, openid: str) -> None:
    if openid not in team.member_openids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def ensure_team_owner(team: Team, openid: str) -> None:
    if team.owner_openid != openid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner only")


def _cleanup_user_teams(db: Session, openid: str, keep_team_id: str | None = None) -> None:
    """确保用户只在一个团队中：删除自己创建的团队，退出其他团队，保留 keep_team_id。"""
    all_teams = db.scalars(select(Team)).all()
    for t in all_teams:
        if t.id == keep_team_id:
            continue
        if t.owner_openid == openid:
            db.delete(t)
        elif openid in t.member_openids:
            t.member_openids = [m for m in t.member_openids if m != openid]
    db.commit()


@router.get("", response_model=TeamsResponse)
def list_teams(
    type: Literal["created", "joined"] = Query("created"),
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    if type == "created":
        stmt = select(Team).where(Team.owner_openid == openid)
        teams = db.scalars(stmt).all()
    else:
        stmt = select(Team)
        teams = [team for team in db.scalars(stmt).all() if openid in team.member_openids]

    return TeamsResponse(teams=teams)


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: str,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    team = get_team_or_404(db, team_id)
    ensure_team_member(team, openid)
    return TeamResponse(team=team)


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    # 用户只能拥有/加入一个团队：先清理其他团队关系
    _cleanup_user_teams(db, openid)

    invite_code = payload.invite_code or generate_invite_code(settings.invite_code_length)
    team = Team(
        name=payload.name,
        owner_openid=openid,
        member_openids=[openid],
        invite_code=invite_code,
        quota=payload.quota or 5,
        created_at=datetime.now(timezone.utc),
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.post("/join", response_model=TeamOut)
def join_team(
    payload: JoinTeamRequest,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    team = db.scalar(select(Team).where(Team.invite_code == payload.invite_code))
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite code")

    if openid in team.member_openids:
        return team

    if len(team.member_openids) >= team.quota:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team quota exceeded")

    # 加入前先清理用户在其他团队的拥有/成员关系，确保只在一个团队中
    _cleanup_user_teams(db, openid, keep_team_id=team.id)

    team.member_openids.append(openid)
    db.commit()
    db.refresh(team)
    return team


@router.patch("/{team_id}/rename", response_model=TeamOut)
def rename_team(
    team_id: str,
    payload: RenameTeamRequest,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    team = get_team_or_404(db, team_id)
    ensure_team_owner(team, openid)
    team.name = payload.name
    db.commit()
    db.refresh(team)
    return team


@router.patch("/{team_id}/regenerate-invite", response_model=TeamOut)
def regenerate_invite(
    team_id: str,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    team = get_team_or_404(db, team_id)
    ensure_team_owner(team, openid)
    team.invite_code = generate_invite_code(settings.invite_code_length)
    db.commit()
    db.refresh(team)
    return team


@router.patch("/{team_id}/remove-member", response_model=TeamOut)
def remove_member(
    team_id: str,
    payload: RemoveMemberRequest,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    team = get_team_or_404(db, team_id)
    ensure_team_owner(team, openid)

    if payload.member_openid == team.owner_openid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Owner cannot be removed"
        )

    if payload.member_openid in team.member_openids:
        team.member_openids.remove(payload.member_openid)
        db.commit()
        db.refresh(team)
    return team


@router.patch("/{team_id}/leave", response_model=MessageResponse)
def leave_team(
    team_id: str,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    team = get_team_or_404(db, team_id)
    if team.owner_openid == openid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Owner cannot leave directly"
        )
    if openid in team.member_openids:
        team.member_openids.remove(openid)
        db.commit()
    return MessageResponse()

