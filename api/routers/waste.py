from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import date
import json
from schemas import (
    WasteRecord,
    WasteCategory,
    RecyclingOpportunity,
    PollutionPreventionOpportunity,
    TaskWasteRelationship,
)
from db.session import get_db

router = APIRouter(prefix="/api/v1")


# ── Waste Categories ──────────────────────────────────────────────────────────

@router.get("/waste-categories", response_model=List[WasteCategory])
def get_waste_categories(db=Depends(get_db)):
    try:
        rows = db.execute(
            "SELECT waste_category_id, category_name, hazard_class, disposal_method, epa_code "
            "FROM waste_categories ORDER BY category_name"
        ).fetchall()
        return [
            WasteCategory(
                waste_category_id=r["waste_category_id"],
                category_name=r["category_name"],
                hazard_class=r["hazard_class"],
                disposal_method=r["disposal_method"],
                epa_code=r["epa_code"],
            )
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/waste-categories/{category_id}", response_model=WasteCategory)
def get_waste_category(category_id: str, db=Depends(get_db)):
    try:
        row = db.execute(
            "SELECT waste_category_id, category_name, hazard_class, disposal_method, epa_code "
            "FROM waste_categories WHERE waste_category_id = ?",
            (category_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Waste category not found")
        return WasteCategory(
            waste_category_id=row["waste_category_id"],
            category_name=row["category_name"],
            hazard_class=row["hazard_class"],
            disposal_method=row["disposal_method"],
            epa_code=row["epa_code"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ── Pollution Prevention (declared before /{id} routes to avoid shadowing) ───

@router.get("/pollution-prevention", response_model=List[PollutionPreventionOpportunity])
def get_pollution_prevention_opportunities(
    task_name: Optional[str] = None,
    priority_level: Optional[str] = None,
    status: Optional[str] = None,
    db=Depends(get_db),
):
    try:
        query = (
            "SELECT opportunity_id, task_name, task_description, waste_category_id, "
            "prevention_method, expected_reduction_percent, implementation_cost_usd, "
            "payback_period_months, priority_level, responsible_party, status, "
            "notes, created_at, updated_at "
            "FROM pollution_prevention_opportunities WHERE 1=1"
        )
        params: list = []

        if task_name:
            query += " AND task_name LIKE ?"
            params.append(f"%{task_name}%")
        if priority_level:
            query += " AND priority_level = ?"
            params.append(priority_level)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY CASE priority_level WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, expected_reduction_percent DESC"

        rows = db.execute(query, params).fetchall()
        return [_pp_row(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/pollution-prevention/{opportunity_id}", response_model=PollutionPreventionOpportunity)
def get_pollution_prevention_opportunity(opportunity_id: str, db=Depends(get_db)):
    try:
        row = db.execute(
            "SELECT opportunity_id, task_name, task_description, waste_category_id, "
            "prevention_method, expected_reduction_percent, implementation_cost_usd, "
            "payback_period_months, priority_level, responsible_party, status, "
            "notes, created_at, updated_at "
            "FROM pollution_prevention_opportunities WHERE opportunity_id = ?",
            (opportunity_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Pollution prevention opportunity not found")
        return _pp_row(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


def _pp_row(r) -> PollutionPreventionOpportunity:
    return PollutionPreventionOpportunity(
        opportunity_id=r["opportunity_id"],
        task_name=r["task_name"],
        task_description=r["task_description"],
        waste_category_id=r["waste_category_id"],
        prevention_method=r["prevention_method"],
        expected_reduction_percent=r["expected_reduction_percent"],
        implementation_cost_usd=r["implementation_cost_usd"],
        payback_period_months=r["payback_period_months"],
        priority_level=r["priority_level"],
        responsible_party=r["responsible_party"],
        status=r["status"],
        notes=r["notes"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


# ── Waste Records ─────────────────────────────────────────────────────────────

@router.get("/waste-records", response_model=List[WasteRecord])
def get_waste_records(
    location: Optional[str] = None,
    waste_category_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_db),
):
    try:
        query = (
            "SELECT waste_record_id, date_generated, location, waste_category_id, "
            "quantity_kg, quantity_unit, generator_name, process_type, "
            "container_type, storage_location, disposal_date, disposal_method, "
            "recycler_name, cost_usd, notes, created_at, updated_at "
            "FROM waste_records WHERE 1=1"
        )
        params: list = []

        if location:
            query += " AND location = ?"
            params.append(location)
        if waste_category_id:
            query += " AND waste_category_id = ?"
            params.append(waste_category_id)
        if start_date:
            query += " AND date_generated >= ?"
            params.append(str(start_date))
        if end_date:
            query += " AND date_generated <= ?"
            params.append(str(end_date))

        query += " ORDER BY date_generated DESC LIMIT ?"
        params.append(limit)

        rows = db.execute(query, params).fetchall()
        return [_wr_row(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/waste-records/{record_id}", response_model=WasteRecord)
def get_waste_record(record_id: str, db=Depends(get_db)):
    try:
        row = db.execute(
            "SELECT waste_record_id, date_generated, location, waste_category_id, "
            "quantity_kg, quantity_unit, generator_name, process_type, "
            "container_type, storage_location, disposal_date, disposal_method, "
            "recycler_name, cost_usd, notes, created_at, updated_at "
            "FROM waste_records WHERE waste_record_id = ?",
            (record_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Waste record not found")
        return _wr_row(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


def _wr_row(r) -> WasteRecord:
    return WasteRecord(
        waste_record_id=r["waste_record_id"],
        date_generated=r["date_generated"],
        location=r["location"],
        waste_category_id=r["waste_category_id"],
        quantity_kg=r["quantity_kg"],
        quantity_unit=r["quantity_unit"] or "kg",
        generator_name=r["generator_name"],
        process_type=r["process_type"],
        container_type=r["container_type"],
        storage_location=r["storage_location"],
        disposal_date=r["disposal_date"],
        disposal_method=r["disposal_method"],
        recycler_name=r["recycler_name"],
        cost_usd=r["cost_usd"],
        notes=r["notes"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


# ── Recycling Opportunities ───────────────────────────────────────────────────

@router.get("/recycling-opportunities", response_model=List[RecyclingOpportunity])
def get_recycling_opportunities(
    waste_category_id: Optional[str] = None,
    active_only: bool = True,
    db=Depends(get_db),
):
    try:
        query = (
            "SELECT opportunity_id, waste_category_id, opportunity_name, description, "
            "recycler_contact, estimated_value_per_kg, environmental_impact, is_active, created_at "
            "FROM recycling_opportunities WHERE 1=1"
        )
        params: list = []

        if waste_category_id:
            query += " AND waste_category_id = ?"
            params.append(waste_category_id)
        if active_only:
            query += " AND is_active = 1"

        query += " ORDER BY opportunity_name"

        rows = db.execute(query, params).fetchall()
        return [
            RecyclingOpportunity(
                opportunity_id=r["opportunity_id"],
                waste_category_id=r["waste_category_id"],
                opportunity_name=r["opportunity_name"],
                description=r["description"],
                recycler_contact=r["recycler_contact"],
                estimated_value_per_kg=r["estimated_value_per_kg"],
                environmental_impact=r["environmental_impact"],
                is_active=bool(r["is_active"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ── Task-Waste Relationships ──────────────────────────────────────────────────

@router.get("/task-waste-relationships", response_model=List[TaskWasteRelationship])
def get_task_waste_relationships(task_name: Optional[str] = None, db=Depends(get_db)):
    try:
        query = (
            "SELECT task_name, waste_category_id, average_quantity_kg, frequency "
            "FROM task_waste_relationships WHERE 1=1"
        )
        params: list = []

        if task_name:
            query += " AND task_name LIKE ?"
            params.append(f"%{task_name}%")

        query += " ORDER BY task_name, average_quantity_kg DESC"

        rows = db.execute(query, params).fetchall()
        return [
            TaskWasteRelationship(
                task_name=r["task_name"],
                waste_category_id=r["waste_category_id"],
                average_quantity_kg=r["average_quantity_kg"],
                frequency=r["frequency"],
            )
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
