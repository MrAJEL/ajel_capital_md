"""
AJEL Capital — Clients CRUD + Fee Engine (Phase 2)
=====================================================
Manage advisory clients, fee structure, HWM tracking, and fee events.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import logging

from database import get_db
from models.sql_models import Client, ClientFeeEvent, Portfolio, Transaction, Position, PortfolioHistory
from core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    risk_profile: str = "moderate"
    aum: float = 0.0
    notes: Optional[str] = None
    # Phase 2 fee fields
    initial_capital: Optional[float] = Field(None, ge=0)
    entry_date: Optional[str] = None
    management_fee_pct: Optional[float] = Field(2.0, ge=0, le=100)
    performance_fee_pct: Optional[float] = Field(20.0, ge=0, le=100)

class ClientResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    risk_profile: str
    aum: float
    notes: Optional[str] = None
    created_at: datetime
    # Phase 2
    initial_capital: Optional[float] = None
    entry_date: Optional[datetime] = None
    management_fee_pct: Optional[float] = None
    performance_fee_pct: Optional[float] = None
    hwm: Optional[float] = None
    hwm_updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class FeeEventResponse(BaseModel):
    id: int
    client_id: int
    event_type: str
    amount: float
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    hwm_before: Optional[float] = None
    hwm_after: Optional[float] = None
    aum_at_charge: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class ChargeFeeRequest(BaseModel):
    event_type: str      # management_monthly, management_annual, performance_5yr
    amount: float        # fee amount to charge
    notes: Optional[str] = None
    target_portfolio_id: Optional[int] = None  # which portfolio receives the fee transaction

class UpdateHWMRequest(BaseModel):
    new_hwm: float


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("/clients")
async def list_clients(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """List all clients with portfolio count."""
    clients = db.query(Client).all()
    result = []
    for c in clients:
        d = ClientResponse.model_validate(c).model_dump()
        d["portfolio_count"] = len(c.portfolios) if c.portfolios else 0
        result.append(d)
    return {"clients": result}


@router.post("/clients")
async def create_client(data: ClientCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Create a new client. Initializes HWM to initial_capital."""
    entry_dt = None
    if data.entry_date:
        try:
            entry_dt = datetime.fromisoformat(data.entry_date.replace("Z", "+00:00"))
        except ValueError:
            try:
                entry_dt = datetime.strptime(data.entry_date, "%Y-%m-%d")
            except ValueError:
                pass

    hwm_value = data.initial_capital or data.aum or 0.0

    client = Client(
        name=data.name,
        email=data.email,
        risk_profile=data.risk_profile,
        aum=data.aum,
        notes=data.notes,
        initial_capital=data.initial_capital or 0.0,
        entry_date=entry_dt,
        management_fee_pct=data.management_fee_pct if data.management_fee_pct is not None else 2.0,
        performance_fee_pct=data.performance_fee_pct if data.performance_fee_pct is not None else 20.0,
        hwm=hwm_value,
        hwm_updated_at=datetime.utcnow() if hwm_value > 0 else None,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    logger.info(f"Client created: {client.name} (id={client.id}), HWM=${hwm_value}")
    d = ClientResponse.model_validate(client).model_dump()
    d["portfolio_count"] = 0
    return d


@router.get("/clients/{client_id}")
async def get_client(client_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get client with portfolios and fee summary."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    portfolios = []
    if client.portfolios:
        for p in client.portfolios:
            portfolios.append({"id": p.id, "name": p.name, "currency": p.currency})

    # Fee summary
    fee_events = db.query(ClientFeeEvent).filter(ClientFeeEvent.client_id == client_id).all()
    total_fees_charged = sum(fe.amount for fe in fee_events)

    return {
        **ClientResponse.model_validate(client).model_dump(),
        "portfolios": portfolios,
        "portfolio_count": len(portfolios),
        "total_fees_charged": total_fees_charged,
        "fee_event_count": len(fee_events),
    }


@router.put("/clients/{client_id}")
async def update_client(client_id: int, data: ClientCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Update a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client.name = data.name
    client.email = data.email
    client.risk_profile = data.risk_profile
    client.aum = data.aum
    client.notes = data.notes
    if data.initial_capital is not None:
        client.initial_capital = data.initial_capital
    if data.management_fee_pct is not None:
        client.management_fee_pct = data.management_fee_pct
    if data.performance_fee_pct is not None:
        client.performance_fee_pct = data.performance_fee_pct
    db.commit()
    db.refresh(client)
    return ClientResponse.model_validate(client).model_dump()


@router.delete("/clients/{client_id}")
async def delete_client(client_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Delete a client and all associated portfolios."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(client)
    db.commit()
    logger.info(f"Client deleted: id={client_id}")
    return {"status": "deleted", "id": client_id}


# ── Fee Events ────────────────────────────────────────────────────────────────

@router.get("/clients/{client_id}/fee-events")
async def list_fee_events(client_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """List all fee events for a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    events = db.query(ClientFeeEvent).filter(
        ClientFeeEvent.client_id == client_id
    ).order_by(ClientFeeEvent.created_at.desc()).all()

    return {
        "fee_events": [FeeEventResponse.model_validate(e).model_dump() for e in events],
        "total_charged": sum(e.amount for e in events),
    }


@router.post("/clients/{client_id}/charge-fee")
async def charge_fee(client_id: int, data: ChargeFeeRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Charge a fee to a client. Records a ClientFeeEvent.
    For performance fees, updates the HWM to current AUM.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    valid_types = {"management_monthly", "management_annual", "performance_5yr"}
    if data.event_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"event_type must be one of {valid_types}")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    now = datetime.utcnow()
    hwm_before = client.hwm or 0
    hwm_after = hwm_before

    # For performance fee: update HWM to current AUM (reset gains)
    if data.event_type == "performance_5yr":
        hwm_after = client.aum or 0
        client.hwm = hwm_after
        client.hwm_updated_at = now

    fee_event = ClientFeeEvent(
        client_id=client_id,
        event_type=data.event_type,
        amount=data.amount,
        period_start=now,
        period_end=now,
        hwm_before=hwm_before,
        hwm_after=hwm_after,
        aum_at_charge=client.aum or 0,
        notes=data.notes,
    )
    db.add(fee_event)
    db.commit()
    db.refresh(fee_event)

    logger.info(f"Fee charged: {data.event_type} ${data.amount:.2f} for client {client.name}")
    return FeeEventResponse.model_validate(fee_event).model_dump()


@router.post("/clients/{client_id}/update-hwm")
async def update_hwm(client_id: int, data: UpdateHWMRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Update client HWM. Only allows increases (HWM can only go up)."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    current_hwm = client.hwm or 0
    if data.new_hwm <= current_hwm:
        return {"status": "no_change", "reason": "New HWM must exceed current HWM", "current_hwm": current_hwm}

    client.hwm = data.new_hwm
    client.hwm_updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client)

    logger.info(f"HWM updated for {client.name}: ${current_hwm:.2f} → ${data.new_hwm:.2f}")
    return {"status": "updated", "previous_hwm": current_hwm, "new_hwm": data.new_hwm}


@router.post("/clients/{client_id}/add-capital")
async def add_capital(client_id: int, amount: float, portfolio_id: Optional[int] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Add capital to a client's AUM without affecting fee calculations or growth tracking.
    If portfolio_id is provided, also creates a DEPOSIT transaction in that portfolio."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    old_aum = client.aum or 0
    client.aum = old_aum + amount
    # HWM must be set to max(current_hwm, new_aum) on deposits.
    # Simply adding the deposit to HWM is wrong — if client is down 50% and deposits,
    # HWM would overshoot, creating false performance fee triggers.
    new_aum = client.aum
    if client.hwm is not None:
        client.hwm = max(client.hwm or 0, new_aum)
        client.hwm_updated_at = datetime.utcnow()

    # Automatically create a DEPOSIT transaction if a target portfolio is specified
    hwm_baseline = None
    if portfolio_id:
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if portfolio:
            # Simple baseline: calculate total value of portfolio before this deposit
            # total value = sum(qty * price) + cash, or just let it be None and tracked via other metrics later.
            # We'll set baseline to the portfolio ID for now, or 0.
            hwm_baseline = 0.0 # Could calculate relative return here later

            txn = Transaction(
                portfolio_id=portfolio.id,
                client_id=client.id,
                type="DEPOSIT",
                total_amount=amount,
                date=datetime.utcnow(),
                hwm_baseline=hwm_baseline,
                notes=f"Capital addition from {client.name}"
            )
            db.add(txn)

    db.commit()
    db.refresh(client)

    logger.info(f"Capital added for {client.name}: +${amount:.2f} (AUM: ${old_aum:.2f} → ${client.aum:.2f})")
    return {
        "status": "capital_added",
        "amount": amount,
        "previous_aum": old_aum,
        "new_aum": client.aum,
        "hwm": client.hwm,
    }
