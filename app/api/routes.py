from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.db.database import get_db
from app.db.models import Asset
from app.services.agent import run_autonomous_security_agent
from app.services.asset_service import ingest_asset, create_relationship
from app.services.ai import (
    analyze_asset_vulnerability, 
    enrich_and_categorize_asset, 
    translate_nl_query, 
    generate_executive_report
)

# ==========================================
# 1. PYDANTIC SCHEMAS
# ==========================================
class AssetCreate(BaseModel):
    id: Optional[str] = Field(None, description="Temporary ID provided in JSON for batch linking")
    type: str = Field(..., description="The type of asset (e.g., domain, ip, repository)")
    value: str = Field(..., description="The actual value of the asset")
    source: str = Field(..., description="Where this asset was found")
    status: Optional[str] = "active"
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}
    
    # Relationship Fields
    parent: Optional[str] = Field(None, description="ID of the parent asset")
    covers: Optional[str] = Field(None, description="ID of the asset this certificate covers")

class NLQuery(BaseModel):
    query: str = Field(..., description="A natural language search query")

# ==========================================
# 2. ROUTER INITIALIZATION
# ==========================================
router = APIRouter()

# ==========================================
# 3. CORE INGESTION ENDPOINTS
# ==========================================

@router.post("/assets/", response_model=dict)
def create_single_asset(asset: AssetCreate, db: Session = Depends(get_db)):
    """Ingests a single asset."""
    # Exclude batch-specific fields for a single clean insert
    asset_data = asset.model_dump(exclude={"id", "parent", "covers"})
    asset_data["asset_metadata"] = asset_data.pop("metadata", {})

    try:
        db_asset, action = ingest_asset(db, asset_data)
        return {
            "message": f"Asset successfully {action}",
            "asset_id": str(db_asset.id),
            "action": action
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assets/batch", response_model=dict)
def batch_ingest_assets(assets: List[AssetCreate], db: Session = Depends(get_db)):
    """
    Ingests an array of assets. 
    Pass 1: Saves all assets and maps temporary JSON IDs to PostgreSQL UUIDs.
    Pass 2: Reads the parent/covers fields and creates AssetRelationships.
    """
    results = {
        "total_received": len(assets),
        "successfully_created": 0,
        "successfully_updated": 0,
        "relationships_created": 0,
        "failed": 0,
        "errors": []
    }

    id_map = {}

    # PASS 1: Ingest Assets
    for index, asset in enumerate(assets):
        try:
            asset_data = asset.model_dump(exclude={"id", "parent", "covers"})
            asset_data["asset_metadata"] = asset_data.pop("metadata", {})
            
            db_asset, action = ingest_asset(db, asset_data)
            
            if asset.id:
                id_map[asset.id] = db_asset.id
            
            if action == "created":
                results["successfully_created"] += 1
            elif action == "updated":
                results["successfully_updated"] += 1
                
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"index": index, "value": asset.value, "error": str(e)})
            db.rollback()

    # PASS 2: Establish Relationships
    for asset in assets:
        if not asset.id or asset.id not in id_map:
            continue
            
        source_uuid = id_map[asset.id]
        
        try:
            if asset.parent and asset.parent in id_map:
                create_relationship(db, source_uuid, id_map[asset.parent], "subdomain_of")
                results["relationships_created"] += 1
                
            if asset.covers and asset.covers in id_map:
                create_relationship(db, source_uuid, id_map[asset.covers], "covers")
                results["relationships_created"] += 1
                
        except Exception as e:
            results["errors"].append({"action": "relationship_linking", "value": asset.value, "error": str(e)})
            db.rollback()

    return results

# ==========================================
# 4. AI TASKS (LangChain Integrations)
# ==========================================

@router.get("/assets/{asset_id}/analyze")
def analyze_asset(asset_id: str, db: Session = Depends(get_db)):
    """Task 2: AI Security Analysis"""
    db_asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found in database")
    
    try:
        analysis_report = analyze_asset_vulnerability(
            asset_type=db_asset.type,
            asset_value=db_asset.value,
            metadata=db_asset.asset_metadata
        )
        return {
            "asset_id": str(db_asset.id),
            "asset_value": db_asset.value,
            "ai_threat_analysis": analysis_report
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"AI Analysis Failed: {str(e)}")

@router.post("/assets/{asset_id}/categorize")
def categorize_asset_endpoint(asset_id: str, db: Session = Depends(get_db)):
    """Task 3: Automated Categorization"""
    db_asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    try:
        classification = enrich_and_categorize_asset(
            asset_type=db_asset.type,
            asset_value=db_asset.value,
            metadata=db_asset.asset_metadata
        )

        updated_metadata = dict(db_asset.asset_metadata) if db_asset.asset_metadata else {}
        updated_metadata["environment"] = classification.get("environment")
        updated_metadata["inferred_category"] = classification.get("category")
        updated_metadata["criticality_rating"] = classification.get("criticality")
        db_asset.asset_metadata = updated_metadata

        existing_tags = set(db_asset.tags) if db_asset.tags else set()
        new_tags = set(classification.get("suggested_tags", []))
        db_asset.tags = list(existing_tags.union(new_tags))

        db.commit()
        db.refresh(db_asset)

        return {
            "message": "Asset automatically enriched and categorized successfully",
            "asset_id": str(db_asset.id),
            "classification_applied": classification,
            "current_stored_tags": db_asset.tags
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Categorization workflow failed: {str(e)}")

@router.post("/assets/query")
def query_assets_by_language(nl_query: NLQuery, db: Session = Depends(get_db)):
    """Task 1: Natural Language Querying"""
    try:
        filters = translate_nl_query(nl_query.query)
        if not filters:
            raise ValueError("AI could not extract valid filters from the query.")
            
        query = db.query(Asset)
        
        if filters.get("asset_type"):
            query = query.filter(Asset.type.ilike(f"%{filters['asset_type']}%"))
        if filters.get("environment"):
            query = query.filter(Asset.asset_metadata["environment"].astext == filters["environment"])
        if filters.get("criticality"):
            query = query.filter(Asset.asset_metadata["criticality_rating"].astext == filters["criticality"])
        
        # Edge Case: Limit to prevent massive loads
        results = query.limit(100).all() 
        
        return {
            "understood_filters": filters,
            "match_count": len(results),
            "assets": results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query Processing Failed: {str(e)}")

@router.get("/reports/generate")
def generate_attack_surface_report(db: Session = Depends(get_db)):
    """Task 4: Report Generation"""
    # Edge Case: Limit report scope so AI doesn't crash on tokens
    assets = db.query(Asset).limit(50).all()
    if not assets:
        raise HTTPException(status_code=404, detail="No assets in database to report on")

    asset_data = [{"type": a.type, "value": a.value, "metadata": a.asset_metadata} for a in assets]

    try:
        report = generate_executive_report(asset_data)
        return {
            "status": "success",
            "total_assets_analyzed": len(assets),
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Report Generation Failed: {str(e)}")

# ==========================================
# 5. Analyze AI Agent
# ==========================================
class AgentQuery(BaseModel):
    question: str = Field(..., description="Ask the autonomous agent a security question.")

@router.post("/agent/chat")
def chat_with_security_agent(query: AgentQuery):
    """
    Bonus Task: Autonomous Agent
    Passes a natural language question to the LLM. The LLM will autonomously
    decide to call the internal API to gather data before responding.
    """
    try:
        response = run_autonomous_security_agent(query.question)
        return {
            "status": "success",
            "agent_response": response
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Agent workflow failed: {str(e)}")
