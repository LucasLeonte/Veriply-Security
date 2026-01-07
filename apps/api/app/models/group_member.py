from sqlalchemy import Column, Uuid, ForeignKey, DateTime, Enum as SQLEnum, Index
from datetime import datetime
import enum
from .base import Base


class GroupRole(str, enum.Enum):
    """Role enum for group membership with RBAC levels."""
    OWNER = "owner"                   # Group creator with full ownership rights
    GROUP_ADMIN = "group_admin"      # Full control: create/delete bots, manage members, configure KB
    MANAGER = "manager"               # Manage bots: create/update/delete bots, approve uploads
    OPERATOR = "operator"             # Submit content: upload documents, view results


class GroupMember(Base):
    """Group membership model tracking users and their roles within groups.
    
    Implements RBAC for groups with three tiers:
    - GROUP_ADMIN: full control over group, bots, and members
    - MANAGER: can create/manage bots, approve document uploads
    - OPERATOR: can upload documents and view results
    
    Fields:
      - id: UUID primary key
      - group_id: FK -> groups.id (the group)
      - user_id: FK -> users.id (the user)
      - role: enum GroupRole (permission level)
      - invited_at: timestamp when user was invited
      - invited_by_id: FK -> users.id (user who sent invitation)
    """

    __tablename__ = "group_members"

    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    group_id = Column(Uuid, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum(GroupRole, values_callable=lambda x: [e.value for e in x]), nullable=False)
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    invited_by_id = Column(Uuid, ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        Index('ix_group_members_group_id', 'group_id'),
        Index('ix_group_members_user_id', 'user_id'),
        Index('ix_group_members_group_user', 'group_id', 'user_id'),
        __import__('sqlalchemy').UniqueConstraint('group_id', 'user_id', name='uq_group_members_group_user'),
    )
