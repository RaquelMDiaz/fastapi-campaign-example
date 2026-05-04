from fastapi import FastAPI, HTTPException, Request
from datetime import datetime

app = FastAPI(root_path="/api/v1")

@app.get("/")
async def root():
    return {"message": "Hello World"}

data = [
    {
        "campaign_id": 1,
        "name": "Campaign 1",
        "due_date": "2026-05-30T13:31:44.064116",
        "created_at": datetime.now(),
    },
    {
        "campaign_id": 2,
        "name": "Campaign 2",
        "due_date": "2026-05-30T13:31:44.064116",
        "created_at": datetime.now(),
    },
    {
        "campaign_id": 3,
        "name": "Campaign 3",
        "due_date": "2026-05-30T13:31:44.064116",
        "created_at": datetime.now(),
    }
]

@app.get("/campaigns")
async def read_campaigns():
    return {"campaigns": data}

@app.get("/campaigns/{id}")
async def read_campaign(id: int):
    for campaign in data:
        if campaign["campaign_id"] == id:
            return {"campaign": campaign}
    raise HTTPException(status_code=404, detail="Campaign not found")

@app.post("/campaigns")
async def create_campaign(campaign: dict):
    campaign["campaign_id"] = len(data) + 1
    campaign["due_date"] = campaign.get("due_date")
    campaign["created_at"] = datetime.now()
    data.append(campaign)
    return {"campaign": campaign}

@app.delete("/campaigns/{id}")
async def remove_campaign(id: int):
    for campaign in data:
        if campaign["campaign_id"] == id:
            data.remove(campaign)
            return {"message": "Campaign removed"}
    raise HTTPException(status_code=404, detail="Campaign not found")

@app.put("/campaigns/{id}")
async def update_campaign(id: int, body: dict):
    for index, campaign in enumerate(data):
        if campaign["campaign_id"] == id:
            data[index] = {**campaign, **body}
            return {"message": "Campaign updated"}
    raise HTTPException(status_code=404, detail="Campaign not found")

"""
async def create_campaign(campaign: dict):
    campaign["campaign_id"] = len(data) + 1
    campaign["created_at"] = datetime.now()
    data.append(campaign)
    return {"campaign": campaign}
"""