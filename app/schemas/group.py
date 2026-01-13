from pydantic import BaseModel
from typing import Optional, List


class GroupResponse(BaseModel):
    groupId: str
    joinCode: str
    memberCount: int
    maxSize: int


class GroupMemberResponse(BaseModel):
    userId: str
    name: str
    email: str


class GroupDetailResponse(BaseModel):
    groupId: str
    joinCode: str
    members: List[GroupMemberResponse]
    maxSize: int
