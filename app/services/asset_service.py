from sqlalchemy.orm import Session
from app.db.models import Asset
from datetime import datetime
from app.db.models import Asset, AssetRelationship

def ingest_asset(db: Session, asset_data: dict):
    """
    Takes a dictionary of asset data, checks if it exists.
    If it exists -> updates last_seen, reactivates, and merges metadata (Deduplication).
    If it is new -> inserts it into the database.
    """
    existing_asset = db.query(Asset).filter(Asset.value == asset_data["value"]).first()
    
    if existing_asset:
        # 1. Edge Case: Re-appearing assets (set back to active)
        existing_asset.last_seen = datetime.utcnow()
        existing_asset.status = "active" 
        
        # 2. Edge Case: Conflicting data (Merge strategy)
        if "asset_metadata" in asset_data:
            current_meta = existing_asset.asset_metadata or {}
            current_meta.update(asset_data["asset_metadata"])
            existing_asset.asset_metadata = current_meta
            
        # Merge tags (avoiding duplicates)
        if "tags" in asset_data:
            current_tags = set(existing_asset.tags or [])
            new_tags = set(asset_data["tags"] or [])
            existing_asset.tags = list(current_tags.union(new_tags))

        db.commit()
        db.refresh(existing_asset)
        return existing_asset, "updated"
    
    # 3. It does not exist: Create a brand new asset
    new_asset = Asset(**asset_data)
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)
    return new_asset, "created"

def create_relationship(db: Session, source_uuid, target_uuid, rel_type: str):
    """Safely creates a relationship between two assets if it doesn't already exist."""
    existing_link = db.query(AssetRelationship).filter(
        AssetRelationship.source_asset_id == source_uuid,
        AssetRelationship.target_asset_id == target_uuid,
        AssetRelationship.relationship_type == rel_type
    ).first()
    
    if not existing_link:
        new_link = AssetRelationship(
            source_asset_id=source_uuid,
            target_asset_id=target_uuid,
            relationship_type=rel_type
        )
        db.add(new_link)
        db.commit()
