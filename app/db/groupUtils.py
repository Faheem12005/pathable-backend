import random
import string

from app.models.group import Group
from app.models.groupMember import GroupMember
from app.models.user import User


def generateJoinCode():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def getUserGroup(db, userId):
    """Get the group that a user is currently in (if any)"""
    membership = (
        db.query(GroupMember)
        .filter(GroupMember.user_id == userId)
        .first()
    )
    
    if not membership:
        return None
    
    group = db.query(Group).filter(Group.id == membership.group_id).first()
    return group


def isUserInGroup(db, userId):
    """Check if user is already in any group"""
    return db.query(GroupMember).filter(GroupMember.user_id == userId).first() is not None


def createGroup(db, ownerId):
    # Check if user is already in a group
    if isUserInGroup(db, ownerId):
        raise Exception("You are already in a group. Leave your current group first.")
    
    group = Group(join_code=generateJoinCode())
    db.add(group)
    db.flush()  # get group.id without commit

    member = GroupMember(
        group_id=group.id,
        user_id=ownerId
    )
    db.add(member)

    db.commit()
    db.refresh(group)
    return group


def joinGroup(db, joinCode, userId):
    # Check if user is already in a group
    if isUserInGroup(db, userId):
        raise Exception("You are already in a group. Leave your current group first.")
    
    group = db.query(Group).filter(Group.join_code == joinCode).first()
    if not group:
        raise Exception("Invalid join code")

    count = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group.id)
        .count()
    )

    if count >= group.max_size:
        raise Exception("Group full")

    db.add(GroupMember(group_id=group.id, user_id=userId))
    db.commit()


def leaveGroup(db, userId):
    """Remove user from their current group"""
    membership = (
        db.query(GroupMember)
        .filter(GroupMember.user_id == userId)
        .first()
    )
    
    if not membership:
        raise Exception("You are not in any group")
    
    groupId = membership.group_id
    
    # Remove the member
    db.delete(membership)
    
    # Check if group is now empty - if so, delete the group
    remaining = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == groupId)
        .count()
    )
    
    if remaining == 0:
        group = db.query(Group).filter(Group.id == groupId).first()
        if group:
            db.delete(group)
    
    db.commit()


def getGroupDetails(db, groupId):
    """Get group details with member information"""
    group = db.query(Group).filter(Group.id == groupId).first()
    if not group:
        raise Exception("Group not found")
    
    members = (
        db.query(GroupMember, User)
        .join(User, GroupMember.user_id == User.id)
        .filter(GroupMember.group_id == groupId)
        .all()
    )
    
    return {
        "group": group,
        "members": [(m.user_id, u) for m, u in members]
    }

