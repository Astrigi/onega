from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MemberCreate(BaseModel):
    surname: str
    first_name: str
    patronymic: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None
    email: str | None = None
    status: str = "active"


class MemberUpdate(BaseModel):
    surname: str | None = None
    first_name: str | None = None
    patronymic: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None
    email: str | None = None
    status: str | None = None


class MemberPlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plot_id: int
    ownership_share: float
    is_voting_representative: bool
    voting_waived: bool


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    surname: str
    first_name: str
    patronymic: str | None
    date_of_birth: date | None
    phone: str | None
    email: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    member_plots: list[MemberPlotOut] = []


class AddMemberPlotRequest(BaseModel):
    plot_id: int
    ownership_share: float


class LinkUserRequest(BaseModel):
    user_id: int


class VotingActionRequest(BaseModel):
    member_id: int
