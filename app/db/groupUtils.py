import random
import string

from app.models.group import Group
from app.models.groupMember import GroupMember


def generateJoinCode():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def createGroup(db, ownerId):
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

