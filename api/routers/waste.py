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

router = APIRouter()


# Waste Categories Endpoints


@router.get("/waste-categories", response_model=List[WasteCategory])
async def get_waste_categories(db=Depends(get_db)):
    """Get all waste categories"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT waste_category_id, category_name, hazard_class, disposal_method, epa_code
            FROM waste_categories
            ORDER BY category_name
        """
        )
        rows = cursor.fetchall()

        categories = []
        for row in rows:
            categories.append(
                WasteCategory(
                    waste_category_id=row[0],
                    category_name=row[1],
                    hazard_class=row[2],
                    disposal_method=row[3],
                    epa_code=row[4],
                )
            )
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/waste-categories/{category_id}", response_model=WasteCategory)
async def get_waste_category(category_id: str, db=Depends(get_db)):
    """Get a specific waste category by ID"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT waste_category_id, category_name, hazard_class, disposal_method, epa_code
            FROM waste_categories
            WHERE waste_category_id = %s
        """,
            (category_id,),
        )

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Waste category not found")

        return WasteCategory(
            waste_category_id=row[0],
            category_name=row[1],
            hazard_class=row[2],
            disposal_method=row[3],
            epa_code=row[4],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Waste Records Endpoints


@router.get("/waste-records", response_model=List[WasteRecord])
async def get_waste_records(
    location: Optional[str] = None,
    waste_category_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_db),
):
    """Get waste records with optional filtering"""
    try:
        cursor = db.cursor()

        # Build query with filters
        query = """
            SELECT waste_record_id, date_generated, location, waste_category_id,
                   quantity_kg, quantity_unit, generator_name, process_type,
                   container_type, storage_location, disposal_date, disposal_method,
                   recycler_name, cost_usd, notes, created_at, updated_at
            FROM waste_records
            WHERE 1=1
        """
        params = []

        if location:
            query += " AND location = %s"
            params.append(location)

        if waste_category_id:
            query += " AND waste_category_id = %s"
            params.append(waste_category_id)

        if start_date:
            query += " AND date_generated >= %s"
            params.append(start_date)

        if end_date:
            query += " AND date_generated <= %s"
            params.append(end_date)

        query += " ORDER BY date_generated DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        records = []
        for row in rows:
            records.append(
                WasteRecord(
                    waste_record_id=row[0],
                    date_generated=row[1],
                    location=row[2],
                    waste_category_id=row[3],
                    quantity_kg=row[4],
                    quantity_unit=row[5] or "kg",
                    generator_name=row[6],
                    process_type=row[7],
                    container_type=row[8],
                    storage_location=row[9],
                    disposal_date=row[10],
                    disposal_method=row[11],
                    recycler_name=row[12],
                    cost_usd=row[13],
                    notes=row[14],
                    created_at=row[15],
                    updated_at=row[16],
                )
            )
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/waste-records/{record_id}", response_model=WasteRecord)
async def get_waste_record(record_id: str, db=Depends(get_db)):
    """Get a specific waste record by ID"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT waste_record_id, date_generated, location, waste_category_id,
                   quantity_kg, quantity_unit, generator_name, process_type,
                   container_type, storage_location, disposal_date, disposal_method,
                   recycler_name, cost_usd, notes, created_at, updated_at
            FROM waste_records
            WHERE waste_record_id = %s
        """,
            (record_id,),
        )

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Waste record not found")

        return WasteRecord(
            waste_record_id=row[0],
            date_generated=row[1],
            location=row[2],
            waste_category_id=row[3],
            quantity_kg=row[4],
            quantity_unit=row[5] or "kg",
            generator_name=row[6],
            process_type=row[7],
            container_type=row[8],
            storage_location=row[9],
            disposal_date=row[10],
            disposal_method=row[11],
            recycler_name=row[12],
            cost_usd=row[13],
            notes=row[14],
            created_at=row[15],
            updated_at=row[16],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Recycling Opportunities Endpoints


@router.get("/recycling-opportunities", response_model=List[RecyclingOpportunity])
async def get_recycling_opportunities(
    waste_category_id: Optional[str] = None, active_only: bool = True, db=Depends(get_db)
):
    """Get recycling opportunities with optional filtering"""
    try:
        cursor = db.cursor()

        query = """
            SELECT opportunity_id, waste_category_id, opportunity_name, description,
                   recycler_contact, estimated_value_per_kg, environmental_impact, is_active, created_at
            FROM recycling_opportunities
            WHERE 1=1
        """
        params = []

        if waste_category_id:
            query += " AND waste_category_id = %s"
            params.append(waste_category_id)

        if active_only:
            query += " AND is_active = TRUE"
            params.append(True)

        query += " ORDER BY opportunity_name"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        opportunities = []
        for row in rows:
            opportunities.append(
                RecyclingOpportunity(
                    opportunity_id=row[0],
                    waste_category_id=row[1],
                    opportunity_name=row[2],
                    description=row[3],
                    recycler_contact=row[4],
                    estimated_value_per_kg=row[5],
                    environmental_impact=row[6],
                    is_active=row[7],
                    created_at=row[8],
                )
            )
        return opportunities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Pollution Prevention Opportunities Endpoints


@router.get("/pollution-prevention", response_model=List[PollutionPreventionOpportunity])
async def get_pollution_prevention_opportunities(
    task_name: Optional[str] = None,
    priority_level: Optional[str] = None,
    status: Optional[str] = None,
    db=Depends(get_db),
):
    """Get pollution prevention opportunities with optional filtering"""
    try:
        cursor = db.cursor()

        query = """
            SELECT opportunity_id, task_name, task_description, waste_category_id,
                   prevention_method, expected_reduction_percent, implementation_cost_usd,
                   payback_period_months, priority_level, responsible_party, status,
                   notes, created_at, updated_at
            FROM pollution_prevention_opportunities
            WHERE 1=1
        """
        params = []

        if task_name:
            query += " AND task_name ILIKE %s"
            params.append(f"%{task_name}%")

        if priority_level:
            query += " AND priority_level = %s"
            params.append(priority_level)

        if status:
            query += " AND status = %s"
            params.append(status)

        query += " ORDER BY priority_level DESC, expected_reduction_percent DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        opportunities = []
        for row in rows:
            opportunities.append(
                PollutionPreventionOpportunity(
                    opportunity_id=row[0],
                    task_name=row[1],
                    task_description=row[2],
                    waste_category_id=row[3],
                    prevention_method=row[4],
                    expected_reduction_percent=row[5],
                    implementation_cost_usd=row[6],
                    payback_period_months=row[7],
                    priority_level=row[8],
                    responsible_party=row[9],
                    status=row[10],
                    notes=row[11],
                    created_at=row[12],
                    updated_at=row[13],
                )
            )
        return opportunities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/pollution-prevention/{opportunity_id}", response_model=PollutionPreventionOpportunity)
async def get_pollution_prevention_opportunity(opportunity_id: str, db=Depends(get_db)):
    """Get a specific pollution prevention opportunity by ID"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT opportunity_id, task_name, task_description, waste_category_id,
                   prevention_method, expected_reduction_percent, implementation_cost_usd,
                   payback_period_months, priority_level, responsible_party, status,
                   notes, created_at, updated_at
            FROM pollution_prevention_opportunities
            WHERE opportunity_id = %s
        """,
            (opportunity_id,),
        )

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Pollution prevention opportunity not found")

        return PollutionPreventionOpportunity(
            opportunity_id=row[0],
            task_name=row[1],
            task_description=row[2],
            waste_category_id=row[3],
            prevention_method=row[4],
            expected_reduction_percent=row[5],
            implementation_cost_usd=row[6],
            payback_period_months=row[7],
            priority_level=row[8],
            responsible_party=row[9],
            status=row[10],
            notes=row[11],
            created_at=row[12],
            updated_at=row[13],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Task-Waste Relationships Endpoints


@router.get("/task-waste-relationships", response_model=List[TaskWasteRelationship])
async def get_task_waste_relationships(task_name: Optional[str] = None, db=Depends(get_db)):
    """Get task-waste relationships with optional filtering"""
    try:
        cursor = db.cursor()

        query = """
            SELECT task_name, waste_category_id, average_quantity_kg, frequency
            FROM task_waste_relationships
            WHERE 1=1
        """
        params = []

        if task_name:
            query += " AND task_name ILIKE %s"
            params.append(f"%{task_name}%")

        query += " ORDER BY task_name, average_quantity_kg DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        relationships = []
        for row in rows:
            relationships.append(
                TaskWasteRelationship(
                    task_name=row[0], waste_category_id=row[1], average_quantity_kg=row[2], frequency=row[3]
                )
            )
        return relationships
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Analytics Endpoints


@router.get("/waste-analytics/summary")
async def get_waste_summary(start_date: Optional[date] = None, end_date: Optional[date] = None, db=Depends(get_db)):
    """Get waste generation summary statistics"""
    try:
        cursor = db.cursor()

        # Build date filter
        date_filter = ""
        params = []
        if start_date:
            date_filter += " AND date_generated >= %s"
            params.append(start_date)
        if end_date:
            date_filter += " AND date_generated <= %s"
            params.append(end_date)

        # Total waste by category
        cursor.execute(
            f"""
            SELECT wc.category_name, SUM(wr.quantity_kg) as total_kg, COUNT(*) as record_count
            FROM waste_records wr
            JOIN waste_categories wc ON wr.waste_category_id = wc.waste_category_id
            WHERE 1=1 {date_filter}
            GROUP BY wc.category_name
            ORDER BY total_kg DESC
        """,
            params,
        )

        waste_by_category = []
        for row in cursor.fetchall():
            waste_by_category.append({"category": row[0], "total_kg": float(row[1]), "record_count": row[2]})

        # Total cost by disposal method
        cursor.execute(
            f"""
            SELECT disposal_method, SUM(cost_usd) as total_cost, COUNT(*) as record_count
            FROM waste_records
            WHERE disposal_method IS NOT NULL AND cost_usd IS NOT NULL {date_filter}
            GROUP BY disposal_method
            ORDER BY total_cost DESC
        """,
            params,
        )

        cost_by_method = []
        for row in cursor.fetchall():
            cost_by_method.append({"method": row[0], "total_cost": float(row[1]), "record_count": row[2]})

        # Monthly waste trends (last 12 months)
        cursor.execute(
            """
            SELECT
                DATE_TRUNC('month', date_generated) as month,
                SUM(quantity_kg) as total_kg,
                COUNT(*) as record_count
            FROM waste_records
            WHERE date_generated >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY DATE_TRUNC('month', date_generated)
            ORDER BY month
        """
        )

        monthly_trends = []
        for row in cursor.fetchall():
            monthly_trends.append(
                {"month": row[0].isoformat() if row[0] else None, "total_kg": float(row[1]), "record_count": row[2]}
            )

        return {
            "waste_by_category": waste_by_category,
            "cost_by_disposal_method": cost_by_method,
            "monthly_trends": monthly_trends,
            "date_range": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
