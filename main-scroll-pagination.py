import base64, json
from typing import Annotated, Optional

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from pydantic import BaseModel
from sqlmodel import Field, Session, create_engine, SQLModel, select

class Campaign(SQLModel, table=True):
    campaign_id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    due_date: datetime | None = Field(default=None, nullable=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=True, index=True)

class CampaignCreate(SQLModel):
    name: str = Field(index=True)
    due_date: datetime | None = None

sqlite_db = "campaigns.db"
sqlite_db_url = f"sqlite:///{sqlite_db}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_db_url, connect_args=connect_args)

def create_db():
    with engine.connect() as connection:
        SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    with Session(engine) as session:
            if not session.exec(select(Campaign)).first():
                session.add_all([
                    Campaign(name="Campaign 1", due_date=datetime(2026, 5, 30, 13, 31, 44)),
                    Campaign(name="Campaign 2", due_date=datetime(2026, 5, 30, 13, 31, 44)),
                    Campaign(name="Campaign 3", due_date=datetime(2026, 5, 30, 13, 31, 44)),
                ])
                session.commit()
    yield

app = FastAPI(root_path="/api/v1", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello World"}

class CapaignsResponse(BaseModel):
    campaigns: list[Campaign]

class PaginationResponse(BaseModel):
    campaigns: list[Campaign]
    prev: str | None
    next: str | None

def encode_cursor(value):
    raw = json.dumps({"id": value})
    return base64.urlsafe_b64encode(raw.encode()).decode()

def decode_cursor(cursor):
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    data = json.loads(raw)
    return data.get("id")

@app.get("/campaigns", response_model=PaginationResponse)
async def read_campaigns(request: Request, Session: SessionDep, cursor: Optional[str] = Query(None), limit: int = Query(20, ge=1)):
    cursor_id = 0

    if cursor:
        cursor_id = decode_cursor(cursor)

    campaigns = Session.exec(select(Campaign).order_by(Campaign.created_at).where(Campaign.campaign_id > cursor_id).limit(limit+1)).all()
    base_url = str(request.url).split("?")[0]
    next_cursor = encode_cursor(campaigns[:limit][-1].campaign_id)
    next_url = f"{base_url}?cursor={next_cursor}&limit={limit}" if next_cursor else "there are no more campaigns"
    prev_url = f"{base_url}?cursor={max(0, cursor_id - limit)}&limit={limit}" if cursor_id > 0 else "there is no previous page"
    return {
        "campaigns": campaigns[:limit],
        "next": next_url,
        "prev": prev_url
    }

class CapaignResponse(BaseModel):
    campaign: Campaign

@app.get("/campaigns/{id}", response_model=CapaignResponse)
async def read_campaign(id: int, Session: SessionDep):
    campaign = Session.exec(select(Campaign).where(Campaign.campaign_id == id)).first()
    if campaign:
        return {"campaign": campaign}
    raise HTTPException(status_code=404, detail="Campaign not found")

class CapaignCreateResponse(BaseModel):
    campaign: CampaignCreate

@app.post("/campaigns", response_model=CapaignCreateResponse)
async def create_campaign(campaign: CampaignCreate, Session: SessionDep):
    new_campaign = Campaign.model_validate(campaign)
    Session.add(new_campaign)
    Session.commit()
    Session.refresh(new_campaign)
    return {"campaign": new_campaign}

@app.put("/campaigns/{id}", response_model=CapaignResponse)
async def update_campaign(id: int, campaign: CampaignCreate, Session: SessionDep):
    existing_campaign = Session.get(Campaign, id)
    if existing_campaign:
        existing_campaign.name = campaign.name
        existing_campaign.due_date = campaign.due_date
        Session.add(existing_campaign)
        Session.commit()
        Session.refresh(existing_campaign)
        return {"message": "Campaign updated", "campaign": existing_campaign}
    raise HTTPException(status_code=404, detail="Campaign not found")

@app.delete("/campaigns/{id}", status_code=204)
async def remove_campaign(id: int, Session: SessionDep):
    campaign = Session.get(Campaign, id)
    if campaign:
        Session.delete(campaign)
        Session.commit()
        return {"message": "Campaign removed"}
    raise HTTPException(status_code=404, detail="Campaign not found")
