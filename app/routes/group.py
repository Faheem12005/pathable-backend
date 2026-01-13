from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.groupUtils import createGroup, joinGroup

router = APIRouter(prefix="/group")

def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create")
def create(ownerId: str, db: Session = Depends(getDb)):
    try:
        group = createGroup(db, ownerId)
        return {
            "groupId": str(group.id),
            "joinCode": group.join_code
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/join")
def join(joinCode: str, userId: str, db: Session = Depends(getDb)):
    try:
        joinGroup(db, joinCode, userId)
        return {"status": "joined"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

