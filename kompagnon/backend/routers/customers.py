"""
Customer Management API routes (Post-Project).
GET /api/customers/ - List all customers
GET /api/customers/{id} - Customer detail
PATCH /api/customers/{id} - Update customer/upsell status
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
from database import Customer, Project, get_db

router = APIRouter(prefix="/api/customers", tags=["customers"])


class CustomerResponse(BaseModel):
    id: int
    project_id: int
    next_touchpoint_date: datetime = None
    next_touchpoint_type: str = None
    upsell_status: str
    upsell_package: str = None
    recurring_revenue: float
    notes: str = None
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerUpdate(BaseModel):
    next_touchpoint_date: datetime = None
    next_touchpoint_type: str = None
    upsell_status: str = None
    upsell_package: str = None
    recurring_revenue: float = None
    notes: str = None


class CustomerDetailResponse(CustomerResponse):
    company_name: str
    contact_name: str
    email: str
    website_url: str = None
    trade: str


@router.get("/", response_model=list[CustomerResponse])
def list_customers(
    upsell_status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db),
):
    """List all customers, optionally filtered by upsell status."""
    query = db.query(Customer)
    if upsell_status:
        query = query.filter(Customer.upsell_status == upsell_status)
    customers = query.offset(skip).limit(limit).all()
    return customers


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get customer detail with project/lead information."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    project = customer.project
    lead = project.lead if project else None

    return {
        "id": customer.id,
        "project_id": customer.project_id,
        "next_touchpoint_date": customer.next_touchpoint_date,
        "next_touchpoint_type": customer.next_touchpoint_type,
        "upsell_status": customer.upsell_status,
        "upsell_package": customer.upsell_package,
        "recurring_revenue": customer.recurring_revenue,
        "notes": customer.notes,
        "created_at": customer.created_at,
        "company_name": lead.company_name if lead else "N/A",
        "contact_name": lead.contact_name if lead else "N/A",
        "email": lead.email if lead else "N/A",
        "website_url": lead.website_url if lead else None,
        "trade": lead.trade if lead else "N/A",
    }


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    update: CustomerUpdate,
    db: Session = Depends(get_db),
):
    """Update customer record (typically for upsell tracking)."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if update.next_touchpoint_date is not None:
        customer.next_touchpoint_date = update.next_touchpoint_date
    if update.next_touchpoint_type is not None:
        customer.next_touchpoint_type = update.next_touchpoint_type
    if update.upsell_status is not None:
        customer.upsell_status = update.upsell_status
    if update.upsell_package is not None:
        customer.upsell_package = update.upsell_package
    if update.recurring_revenue is not None:
        customer.recurring_revenue = update.recurring_revenue
    if update.notes is not None:
        customer.notes = update.notes

    customer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(customer)
    return customer


@router.post("/{project_id}/create")
def create_customer(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Create customer record for a project (called at go-live)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if customer already exists
    existing = db.query(Customer).filter(Customer.project_id == project_id).first()
    if existing:
        return {"project_id": project_id, "customer_id": existing.id, "message": "Customer already exists"}

    try:
        customer = Customer(
            project_id=project_id,
            upsell_status="none",
            next_touchpoint_date=datetime.utcnow() + timedelta(days=30),
            next_touchpoint_type="maintenance_offer",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        return {
            "project_id": project_id,
            "customer_id": customer.id,
            "message": f"Customer created for Project {project_id}",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Customer creation failed: {str(e)}")


@router.get("/project/{project_id}/exists")
def customer_exists(project_id: int, db: Session = Depends(get_db)):
    """Check if customer exists for a project."""
    customer = db.query(Customer).filter(Customer.project_id == project_id).first()
    return {
        "project_id": project_id,
        "has_customer": customer is not None,
        "customer_id": customer.id if customer else None,
    }
