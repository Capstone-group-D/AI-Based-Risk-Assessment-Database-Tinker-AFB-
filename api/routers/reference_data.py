"""
reference_data.py — PPE Catalog and Hazard Reference Endpoints

Read-only endpoints that expose the reference tables (ppe, hazards) used by
the PPE Guide frontend page.
"""

from fastapi import APIRouter, Depends
from typing import List

from db.session import get_db
from schemas import PPEReference, HazardReference

router = APIRouter()


@router.get("/api/v1/ppe", response_model=List[PPEReference])
def list_ppe(db=Depends(get_db)):
    """Returns all PPE items from the reference catalog, sorted by category then label."""
    rows = db.execute("SELECT ppe_id, ppe_label, ppe_category FROM ppe ORDER BY ppe_category, ppe_label").fetchall()
    return [PPEReference(**row) for row in rows]


@router.get("/api/v1/hazards", response_model=List[HazardReference])
def list_hazards(db=Depends(get_db)):
    """Returns all hazards from the reference catalog, sorted by category then label."""
    rows = db.execute(
        "SELECT hazard_id, hazard_label, hazard_category FROM hazards ORDER BY hazard_category, hazard_label"
    ).fetchall()
    return [HazardReference(**row) for row in rows]
