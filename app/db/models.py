import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.db.database import Base

class Asset(Base):
    __tablename__ = "assets"

    # Core fields required by the task specifications
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False) 
    value = Column(String, nullable=False, unique=True) 
    status = Column(String, default="active") 
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String, nullable=False)
    tags = Column(ARRAY(String), default=[])
    asset_metadata = Column("metadata", JSONB, default={}) 


class AssetRelationship(Base):
    __tablename__ = "asset_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # The starting asset (e.g., the Subdomain)
    source_asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    
    # The ending asset (e.g., the parent Domain)
    target_asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    
    # The type of link (e.g., 'subdomain_of', 'resolves_to')
    relationship_type = Column(String, nullable=False)
