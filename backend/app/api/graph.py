from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from backend.app.services.impossibility_engine import impossibility_engine

router = APIRouter(prefix="/graph", tags=["Knowledge Graph & Impossibility Engine"])

@router.get("", response_model=Dict[str, Any])
def get_knowledge_graph():
    """Returns the serialized NetworkX knowledge graph for interactive UI visualization."""
    return impossibility_engine.get_full_graph_serialized()

@router.get("/impossibilities", response_model=List[Dict[str, Any]])
def get_impossibility_anomalies(
    institution_id: Optional[str] = Query(None, description="Optional target institution ID filter e.g. INST_001")
):
    """
    Executes Impossibility Engine queries:
    Detects mathematically/physically impossible claims:
    - Dual employment (same faculty full-time across multiple colleges)
    - Land parcel survey collisions (same land claimed by multiple colleges)
    - Physical capacity density violations
    """
    return impossibility_engine.detect_all_impossibilities(target_inst_id=institution_id)
