from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.groupUtils import createGroup, joinGroup, leaveGroup, getUserGroup, getGroupDetails
from app.schemas.group import GroupResponse, GroupDetailResponse, GroupMemberResponse

router = APIRouter(prefix="/group", tags=["Group"])

def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create", response_model=GroupResponse)
def create(ownerId: str, db: Session = Depends(getDb)):
    """
    Create a new group. User must not already be in a group.
    Returns groupId and joinCode to share with friends.
    """
    try:
        group = createGroup(db, ownerId)
        
        # Get member count
        from app.models.groupMember import GroupMember
        member_count = db.query(GroupMember).filter(GroupMember.group_id == group.id).count()
        
        return GroupResponse(
            groupId=str(group.id),
            joinCode=group.join_code,
            memberCount=member_count,
            maxSize=group.max_size
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/join")
def join(joinCode: str, userId: str, db: Session = Depends(getDb)):
    """
    Join an existing group using join code.
    User must not already be in a group.
    """
    try:
        joinGroup(db, joinCode, userId)
        return {"status": "joined"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/leave")
def leave(userId: str, db: Session = Depends(getDb)):
    """
    Leave current group. If user is the last member, the group is deleted.
    """
    try:
        leaveGroup(db, userId)
        return {"status": "left"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user/{userId}", response_model=GroupDetailResponse)
def getUserCurrentGroup(userId: str, db: Session = Depends(getDb)):
    """
    Get the group that the user is currently in (if any).
    Returns 404 if user is not in any group.
    """
    try:
        group = getUserGroup(db, userId)
        if not group:
            raise HTTPException(status_code=404, detail="User is not in any group")
        
        details = getGroupDetails(db, str(group.id))
        
        members = [
            GroupMemberResponse(
                userId=str(user_id),
                name=user.name,
                email=user.email
            )
            for user_id, user in details["members"]
        ]
        
        return GroupDetailResponse(
            groupId=str(group.id),
            joinCode=group.join_code,
            members=members,
            maxSize=group.max_size
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{groupId}", response_model=GroupDetailResponse)
def getGroup(groupId: str, db: Session = Depends(getDb)):
    """
    Get group details including all members.
    """
    try:
        details = getGroupDetails(db, groupId)
        group = details["group"]
        
        members = [
            GroupMemberResponse(
                userId=str(user_id),
                name=user.name,
                email=user.email
            )
            for user_id, user in details["members"]
        ]
        
        return GroupDetailResponse(
            groupId=str(group.id),
            joinCode=group.join_code,
            members=members,
            maxSize=group.max_size
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

