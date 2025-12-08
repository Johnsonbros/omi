from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Text, Float, DateTime, Boolean, JSON, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from enum import Enum

from .base import Base, TimestampMixin, UUIDMixin


class PlaceCategory(str, Enum):
    home = "home"
    work = "work"
    school = "school"
    gym = "gym"
    restaurant = "restaurant"
    shopping = "shopping"
    medical = "medical"
    family = "family"
    friend = "friend"
    other = "other"


class PlaceDB(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "places"
    
    uid: str = Column(String(64), nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    
    latitude: float = Column(Float, nullable=False)
    longitude: float = Column(Float, nullable=False)
    radius_meters: float = Column(Float, default=100.0)
    
    category: str = Column(String(32), default="other")
    address: Optional[str] = Column(String(512), nullable=True)
    
    is_auto_detected: bool = Column(Boolean, default=False)
    is_confirmed: bool = Column(Boolean, default=False)
    
    visit_count: int = Column(Integer, default=0)
    total_dwell_time_minutes: int = Column(Integer, default=0)
    
    first_visited: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    last_visited: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    
    metadata_json: Optional[dict] = Column(JSON, nullable=True)
    
    visits = relationship("PlaceVisitDB", back_populates="place", cascade="all, delete-orphan")
    triggers = relationship("PlaceTriggerDB", back_populates="place", cascade="all, delete-orphan")
    tags = relationship("PlaceTagDB", secondary="place_tag_links", back_populates="places")
    lists = relationship("PlaceListDB", secondary="place_list_members", back_populates="places")
    
    __table_args__ = (
        Index('ix_places_uid_category', 'uid', 'category'),
        Index('ix_places_uid_name', 'uid', 'name'),
    )


class PlaceVisitDB(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "place_visits"
    
    uid: str = Column(String(64), nullable=False, index=True)
    place_id: str = Column(String(36), ForeignKey("places.id", ondelete="CASCADE"), nullable=False, index=True)
    
    entered_at: datetime = Column(DateTime(timezone=True), nullable=False)
    exited_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    
    dwell_minutes: Optional[int] = Column(Integer, nullable=True)
    day_of_week: int = Column(Integer, nullable=False)
    is_routine: bool = Column(Boolean, default=False)
    
    place = relationship("PlaceDB", back_populates="visits")
    
    __table_args__ = (
        Index('ix_place_visits_uid_place_id', 'uid', 'place_id'),
        Index('ix_place_visits_entered_at', 'entered_at'),
    )


class PlaceCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    radius_meters: float = 100.0
    category: PlaceCategory = PlaceCategory.other
    address: Optional[str] = None
    is_auto_detected: bool = False
    metadata_json: Optional[dict] = None


class PlaceUpdate(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[float] = None
    category: Optional[PlaceCategory] = None
    address: Optional[str] = None
    is_confirmed: Optional[bool] = None
    metadata_json: Optional[dict] = None


class PlaceResponse(BaseModel):
    id: str
    uid: str
    name: str
    latitude: float
    longitude: float
    radius_meters: float
    category: str
    address: Optional[str] = None
    is_auto_detected: bool
    is_confirmed: bool
    visit_count: int
    total_dwell_time_minutes: int
    first_visited: Optional[datetime] = None
    last_visited: Optional[datetime] = None
    metadata_json: Optional[dict] = None
    tags: List[str] = Field(default_factory=list)
    list_ids: List[str] = Field(default_factory=list)
    trigger_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuickAddPlaceRequest(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = None
    category: PlaceCategory = PlaceCategory.other
    tags: List[str] = Field(default_factory=list)


class PlaceVisitResponse(BaseModel):
    id: str
    uid: str
    place_id: str
    entered_at: datetime
    exited_at: Optional[datetime] = None
    dwell_minutes: Optional[int] = None
    day_of_week: int
    is_routine: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PlaceTagDB(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "place_tags"
    
    uid: str = Column(String(64), nullable=False, index=True)
    name: str = Column(String(64), nullable=False)
    color: Optional[str] = Column(String(16), nullable=True)
    
    places = relationship("PlaceDB", secondary="place_tag_links", back_populates="tags")
    
    __table_args__ = (
        Index('ix_place_tags_uid_name', 'uid', 'name', unique=True),
    )


class PlaceTagLinkDB(Base):
    __tablename__ = "place_tag_links"
    
    place_id: str = Column(String(36), ForeignKey("places.id", ondelete="CASCADE"), primary_key=True)
    tag_id: str = Column(String(36), ForeignKey("place_tags.id", ondelete="CASCADE"), primary_key=True)


class TriggerType(str, Enum):
    entry = "entry"
    exit = "exit"


class TriggerAction(str, Enum):
    reminder = "reminder"
    mode_switch = "mode_switch"
    notification = "notification"
    task_create = "task_create"


class PlaceTriggerDB(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "place_triggers"
    
    uid: str = Column(String(64), nullable=False, index=True)
    place_id: str = Column(String(36), ForeignKey("places.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name: str = Column(String(255), nullable=False)
    trigger_type: str = Column(String(16), nullable=False)
    action_type: str = Column(String(32), nullable=False)
    action_payload: Optional[dict] = Column(JSON, nullable=True)
    
    enabled: bool = Column(Boolean, default=True)
    cooldown_minutes: int = Column(Integer, default=60)
    last_triggered: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    
    place = relationship("PlaceDB", back_populates="triggers")
    
    __table_args__ = (
        Index('ix_place_triggers_uid_place_id', 'uid', 'place_id'),
    )


class PlaceListDB(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "place_lists"
    
    uid: str = Column(String(64), nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    description: Optional[str] = Column(Text, nullable=True)
    icon: Optional[str] = Column(String(32), nullable=True)
    color: Optional[str] = Column(String(16), nullable=True)
    
    places = relationship("PlaceDB", secondary="place_list_members", back_populates="lists")
    
    __table_args__ = (
        Index('ix_place_lists_uid_name', 'uid', 'name', unique=True),
    )


class PlaceListMemberDB(Base):
    __tablename__ = "place_list_members"
    
    list_id: str = Column(String(36), ForeignKey("place_lists.id", ondelete="CASCADE"), primary_key=True)
    place_id: str = Column(String(36), ForeignKey("places.id", ondelete="CASCADE"), primary_key=True)
    order: int = Column(Integer, default=0)


class PlaceTagResponse(BaseModel):
    id: str
    name: str
    color: Optional[str] = None
    
    class Config:
        from_attributes = True


class PlaceTriggerResponse(BaseModel):
    id: str
    place_id: str
    name: str
    trigger_type: str
    action_type: str
    action_payload: Optional[dict] = None
    enabled: bool
    cooldown_minutes: int
    last_triggered: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PlaceTriggerCreate(BaseModel):
    name: str
    trigger_type: TriggerType
    action_type: TriggerAction
    action_payload: Optional[dict] = None
    enabled: bool = True
    cooldown_minutes: int = 60


class PlaceListResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    place_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class PlaceListCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class PlaceContext(BaseModel):
    current_place: Optional[PlaceResponse] = None
    is_at_known_place: bool = False
    place_category: Optional[str] = None
    time_at_current_place_minutes: Optional[int] = None
    nearby_places: List[PlaceResponse] = Field(default_factory=list)
    most_visited_today: Optional[str] = None
    typical_place_for_time: Optional[str] = None
    current_place_tags: List[str] = Field(default_factory=list)
    current_place_lists: List[str] = Field(default_factory=list)
