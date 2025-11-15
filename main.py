import os
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from bson import ObjectId

from database import create_document, get_documents
from schemas import Registration

app = FastAPI(title="Cricket Registration API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RegistrationRequest(BaseModel):
    captain_name: str = Field(..., min_length=2)
    contact_number: str = Field(..., min_length=7, max_length=20)
    team_name: str = Field(..., min_length=2)
    players: List[str] = Field(..., min_items=8, max_items=8)

    @validator("players")
    def validate_players(cls, v):
        cleaned = [p.strip() for p in v if p and p.strip()]
        if len(cleaned) != 8:
            raise ValueError("Exactly 8 player names are required")
        return cleaned

@app.get("/")
async def root():
    return {"message": "Cricket Registration API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
    }
    try:
        docs = get_documents("registration", {}, limit=1)
        _ = len(docs)
        response["database"] = "✅ Connected"
    except Exception as e:
        response["database"] = f"❌ {str(e)[:80]}"
    return response

@app.post("/api/registrations")
async def create_registration(payload: RegistrationRequest):
    try:
        reg = Registration(
            captain_name=payload.captain_name,
            contact_number=payload.contact_number,
            team_name=payload.team_name,
            players=payload.players,
        )
        inserted_id = create_document("registration", reg)
        return {"ok": True, "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/registrations")
async def list_registrations():
    try:
        docs = get_documents("registration", {}, limit=100)
        # Convert ObjectId to string
        for d in docs:
            if isinstance(d.get("_id"), ObjectId):
                d["_id"] = str(d["_id"])
        return {"ok": True, "items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
