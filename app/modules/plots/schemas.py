from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StreetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sort_order: int
    is_active: bool


class PlotCreate(BaseModel):
    street_id: int
    plot_number: str


class PlotUpdate(BaseModel):
    street_id: int | None = None
    plot_number: str | None = None
    is_active: bool | None = None


class PlotOwnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    member_id: int
    ownership_share: float
    is_voting_representative: bool
    voting_waived: bool


class PlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    street_id: int
    plot_number: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    member_plots: list[PlotOwnerOut] = []


class VotingRepresentativeRequest(BaseModel):
    member_id: int
