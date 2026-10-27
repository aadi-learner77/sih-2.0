"""
Knowledge Graph & Impossibility Engine API Endpoints.
Serves serialized NetworkX Institution Twin knowledge graph and
executes pluggable regulatory impossibility checks.
All outputs state 'indicator for review', adhering to non-punitive review guidelines.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.impossibility_engine import impossibility_engine
from backend.app.services.graph_builder import graph_builder

router = APIRouter(prefix="/graph", tags=["Knowledge Graph & Impossibility Engine"])


@router.get("", response_model=Dict[str, Any])
def get_knowledge_graph(
    from_db: bool = Query(False, description="Whether to reload from the database before returning"),
    db: Session = Depends(get_db)
):
    """
    Returns the serialized NetworkX Institution Twin knowledge graph
    for interactive UI visualization (nodes, edges, summary).
    """
    if from_db:
        impossibility_engine.load_graph_from_db(db)
    return impossibility_engine.get_full_graph_serialized()


@router.get("/impossibilities", response_model=List[Dict[str, Any]])
def get_impossibility_anomalies(
    institution_id: Optional[str] = Query(None, description="Optional target institution ID filter e.g. INST_001"),
    from_db: bool = Query(False, description="Whether to evaluate against database entities"),
    db: Session = Depends(get_db)
):
    """
    Executes pluggable Impossibility Engine checks on the knowledge graph:
    1. Faculty full-time at two institutions with overlapping dates (masked ID + fuzzy name/DOB)
    2. Built-up area per student below the configured norm, using claimed intake
    3. Document issued before the issuing body's creation date, or validity ending before it starts
    4. Lab equipment list inconsistent with approved programmes
    5. Same document reference number used by different institutions

    Returns findings with conflicting subgraphs (nodes+edges as JSON for UI rendering)
    and review indicator explanations.
    """
    if from_db:
        impossibility_engine.load_graph_from_db(db, target_inst_id=institution_id)

    return impossibility_engine.detect_all_impossibilities(target_inst_id=institution_id)


@router.post("/reload", response_model=Dict[str, Any])
def reload_knowledge_graph_from_db(
    target_institution_id: Optional[str] = Query(None, description="Optional institution ID filter"),
    db: Session = Depends(get_db)
):
    """
    Dynamically re-syncs the NetworkX Institution Twin graph directly from the relational database.
    """
    graph = impossibility_engine.load_graph_from_db(db, target_inst_id=target_institution_id)
    serialized = graph_builder.serialize_graph(graph)
    return {
        "status": "SUCCESS",
        "message": "Institution Twin Knowledge Graph reloaded successfully from database",
        "summary": serialized["summary"]
    }


@router.get("/checks", response_model=List[Dict[str, Any]])
def list_pluggable_checks():
    """
    Lists all registered pluggable impossibility engine checks and their metadata.
    """
    return impossibility_engine.list_checks()
