"""
AJEL Capital — Portfolio CRUD + History API Router (Phase 2)
==============================================================
Full CRUD for portfolios, transactions, and positions.
Includes equity curve history from transaction data.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import logging
import json

from data.cache import cache_get, cache_set, cache_delete
from data.market_data import MarketDataClient
import asyncio
from database import get_db
from models.sql_models import Portfolio, Transaction, Position, Client, PortfolioHistory
from core.security import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class PortfolioCreate(BaseModel):
    name: str = "My Portfolio"
    currency: str = "USD"
    benchmark: str = "SPY"
    client_id: Optional[int] = None  # None = pool/personal
    description: Optional[str] = None
    is_default: bool = False

class PortfolioResponse(BaseModel):
    id: int
    name: str
    currency: str
    benchmark: str
    client_id: Optional[int] = None
    description: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    created_at: datetime
    class Config:
        from_attributes = True

class TransactionCreate(BaseModel):
    portfolio_id: int
    symbol: Optional[str] = None       # nullable for deposits/withdrawals
    type: str                           # BUY, SELL, DIVIDEND, DEPOSIT, WITHDRAWAL, STOCK_SPLIT, FEE
    asset_type: str = "stock"
    broker: Optional[str] = None
    qty: Optional[float] = None        # nullable for deposits
    price: Optional[float] = None      # nullable for deposits
    total_amount: Optional[float] = None  # Phase 2: auto-computed or manual
    date: Optional[str] = None
    fees: float = 0.0
    notes: Optional[str] = None
    conviction: Optional[str] = None
    emotion: Optional[str] = None
    thesis: Optional[str] = None
    lesson: Optional[str] = None
    currency: str = "USD"

class TransactionResponse(BaseModel):
    id: int
    portfolio_id: Optional[int] = None
    symbol: Optional[str] = None
    type: str
    asset_type: Optional[str] = None
    broker: Optional[str] = None
    qty: Optional[float] = None
    price: Optional[float] = None
    total_amount: Optional[float] = None
    date: Optional[datetime] = None
    fees: float = 0.0
    notes: Optional[str] = None
    conviction: Optional[str] = None
    emotion: Optional[str] = None
    thesis: Optional[str] = None
    lesson: Optional[str] = None
    currency: Optional[str] = None
    class Config:
        from_attributes = True

class PositionResponse(BaseModel):
    id: int
    portfolio_id: Optional[int] = None
    symbol: str
    asset_type: str
    qty: float
    avg_cost: float
    unrealized_pnl: float
    realized_pnl: float
    first_buy_date: Optional[datetime] = None
    last_transaction_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ── Portfolio CRUD ────────────────────────────────────────────────────────────

@router.get("/portfolios")
async def list_portfolios(db: Session = Depends(get_db)):
    """List all portfolios with client name join."""
    portfolios = db.query(Portfolio).filter(Portfolio.is_active == True).all()
    result = []
    for p in portfolios:
        d = PortfolioResponse.model_validate(p).model_dump()
        # Join client name
        if p.client_id and p.client:
            d["client_name"] = p.client.name
        else:
            d["client_name"] = None
        result.append(d)
    return {"portfolios": result}


@router.post("/portfolios")
async def create_portfolio(data: PortfolioCreate, db: Session = Depends(get_db)):
    """Create a new portfolio (rejects duplicate names)."""
    existing = db.query(Portfolio).filter(Portfolio.name == data.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Portfolio '{data.name}' already exists (id={existing.id})")

    # If is_default, unmark existing defaults
    if data.is_default:
        db.query(Portfolio).filter(Portfolio.is_default == True).update({"is_default": False})

    portfolio = Portfolio(
        name=data.name,
        currency=data.currency,
        benchmark=data.benchmark,
        client_id=data.client_id,
        description=data.description,
        is_default=data.is_default,
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    logger.info(f"Portfolio created: {portfolio.name} (id={portfolio.id})")
    return PortfolioResponse.model_validate(portfolio).model_dump()


@router.get("/portfolios/{portfolio_id}")
async def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """Get a single portfolio with positions summary and weight_pct."""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    positions = db.query(Position).filter(Position.portfolio_id == portfolio_id).all()
    transactions = db.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).all()
    history_data = await get_portfolio_history(portfolio_id, db)
    history_list = history_data.get("history", [])

    # Compute weight_pct for each position
    positions_out = []
    total_value = sum(p.qty * p.avg_cost for p in positions if p.qty > 0)  # fallback without live prices
    for p in positions:
        d = PositionResponse.model_validate(p).model_dump()
        mv = p.qty * p.avg_cost  # market value at cost (live prices applied on frontend)
        d["weight_pct"] = round((mv / total_value * 100), 2) if total_value > 0 else 0
        positions_out.append(d)

    return {
        "portfolio": PortfolioResponse.model_validate(portfolio).model_dump(),
        "positions": positions_out,
        "history": history_list,
        "transaction_count": len(transactions),
    }


@router.get("/portfolios/{portfolio_id}/history")
async def get_portfolio_history(portfolio_id: int, db: Session = Depends(get_db)):
    """
    Compute equity curve from transaction history.
    Returns cumulative invested (deposits) vs cost (buys) over time.
    """
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    cache_key = f"portfolio_history_{portfolio_id}"
    cached = cache_get(cache_key)
    if cached:
        return {"history": cached}

    txns = db.query(Transaction).filter(
        Transaction.portfolio_id == portfolio_id
    ).order_by(Transaction.date.asc()).all()

    if not txns:
        return {"history": []}

    # Calculate real historical MTM portfolio value
    symbols_txns = set(t.symbol.upper() for t in txns if t.symbol and t.type in ["BUY", "SELL"])
    
    market_client = MarketDataClient()
    historical_data = {}
    
    for s in symbols_txns:
        try:
            # Sequential fetch with a tiny delay to avoid Yahoo rate limits (HTTP 429)
            await asyncio.sleep(0.3)
            data = await market_client.fetch_historical(s, period="5y", interval="1d")
            dates_dict = {}
            for c in data.get("candles", []):
                try:
                    dt = datetime.utcfromtimestamp(c["time"]).strftime("%Y-%m-%d")
                    dates_dict[dt] = c["close"]
                except Exception:
                    pass
            historical_data[s] = dates_dict
        except Exception:
            historical_data[s] = {}

    history_points = []
    current_cash = 0.0
    current_positions = {}
    cumulative_invested = 0.0
    
    txn_idx = 0
    num_txns = len(txns)
    
    from datetime import timedelta
    
    # Filter out transctions without dates safely
    valid_txns = [t for t in txns if t.date]
    if not valid_txns:
        return {"history": []}
        
    current_date = valid_txns[0].date.date()
    today = datetime.utcnow().date()
    
    latest_prices = {sym: 0.0 for sym in symbols_txns}
    
    while current_date <= today:
        daily_date_str = current_date.strftime("%Y-%m-%d")
        
        while txn_idx < num_txns and valid_txns[txn_idx].date.date() <= current_date:
            txn = valid_txns[txn_idx]
            tx_type = (txn.type or "").upper()
            amount = txn.total_amount or (abs(txn.qty or 0) * abs(txn.price or 0))
            sym = txn.symbol.upper() if txn.symbol else None
            qty = abs(txn.qty or 0)
            
            if tx_type == "DEPOSIT":
                cumulative_invested += amount
                current_cash += amount
            elif tx_type == "WITHDRAWAL":
                cumulative_invested -= amount
                current_cash -= amount
            elif tx_type == "BUY" and sym:
                current_cash -= amount
                current_positions[sym] = current_positions.get(sym, 0) + qty
                if latest_prices.get(sym, 0) == 0:
                    latest_prices[sym] = txn.price or 0
            elif tx_type == "SELL" and sym:
                current_cash += amount
                current_positions[sym] = current_positions.get(sym, 0) - qty
                if current_positions[sym] < 0:
                    current_positions[sym] = 0
            
            txn_idx += 1
            
        for sym in symbols_txns:
            if daily_date_str in historical_data.get(sym, {}):
                latest_prices[sym] = historical_data[sym][daily_date_str]
                
        # To show the true trajectory of capital, we include available cash
        # daily_value is now total NAV (cash + market value of positions)
        daily_value = current_cash
        for sym, qty in current_positions.items():
            if qty > 0:
                daily_value += qty * latest_prices.get(sym, 0.0)
                
        history_points.append({
            "date": daily_date_str,
            "invested": round(cumulative_invested, 2),
            "value": round(daily_value, 2)
        })
            
        current_date += timedelta(days=1)

    # Cache for 24h
    cache_set(cache_key, history_points, 86400)

    return {"history": history_points}


# Removed CSV import stub



@router.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """Delete a portfolio and all associated data."""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(portfolio)
    db.commit()
    logger.info(f"Portfolio deleted: id={portfolio_id}")
    return {"status": "deleted", "id": portfolio_id}


# ── Transaction CRUD ─────────────────────────────────────────────────────────

@router.get("/transactions")
async def list_transactions(
    portfolio_id: Optional[int] = Query(None),
    symbol: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """List transactions, optionally filtered by portfolio or symbol."""
    query = db.query(Transaction)
    if portfolio_id:
        query = query.filter(Transaction.portfolio_id == portfolio_id)
    if symbol:
        query = query.filter(Transaction.symbol == symbol.upper())
    
    total = query.count()
    txns = query.order_by(Transaction.date.desc()).offset(offset).limit(limit).all()
    
    return {
        "transactions": [TransactionResponse.model_validate(t).model_dump() for t in txns],
        "total": total,
        "page": (offset // limit) + 1,
        "pages": (total // limit) + (1 if total % limit > 0 else 0)
    }


@router.post("/transactions")
async def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    """
    Record a new transaction and update the corresponding position.
    Supports BUY, SELL, DIVIDEND, DEPOSIT, WITHDRAWAL, STOCK_SPLIT, FEE.
    """
    # Validate portfolio exists
    portfolio = db.query(Portfolio).filter(Portfolio.id == data.portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    tx_type = data.type.strip().upper()
    valid_types = {"BUY", "SELL", "DIVIDEND", "DEPOSIT", "WITHDRAWAL", "STOCK_SPLIT", "FEE"}
    if tx_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Type must be one of: {valid_types}")

    # Sanitize inputs
    symbol = (data.symbol or "").strip().upper() if data.symbol else None
    qty = abs(data.qty) if data.qty else 0
    price = data.price or 0

    # For BUY/SELL require symbol
    if tx_type in ("BUY", "SELL") and not symbol:
        raise HTTPException(status_code=400, detail="Symbol required for BUY/SELL")

    # Auto-compute total_amount
    total_amount = data.total_amount
    if total_amount is None or total_amount == 0:
        if qty > 0 and price > 0:
            total_amount = qty * price
        else:
            total_amount = 0

    # Parse date
    tx_date = datetime.utcnow()
    if data.date:
        try:
            tx_date = datetime.fromisoformat(data.date.replace("Z", "+00:00"))
        except ValueError:
            try:
                tx_date = datetime.strptime(data.date, "%Y-%m-%d")
            except ValueError:
                pass

    # Create transaction
    txn = Transaction(
        portfolio_id=data.portfolio_id,
        symbol=symbol,
        type=tx_type,
        asset_type=data.asset_type,
        broker=data.broker,
        qty=qty,
        price=price,
        total_amount=total_amount,
        date=tx_date,
        fees=data.fees,
        notes=data.notes,
        conviction=data.conviction,
        emotion=data.emotion,
        thesis=data.thesis,
        lesson=data.lesson,
        currency=data.currency,
    )
    db.add(txn)

    # Update position for BUY/SELL
    if tx_type in ("BUY", "SELL") and symbol:
        _update_position(db, data.portfolio_id, symbol, data.asset_type, tx_type, qty, price, tx_date)

    db.commit()
    db.refresh(txn)

    # Invalidate cache
    cache_delete(f"portfolio_history_{data.portfolio_id}")

    logger.info(f"Transaction recorded: {tx_type} {qty} {symbol or 'N/A'} @ {price}")
    return TransactionResponse.model_validate(txn).model_dump()


@router.delete("/transactions/{txn_id}")
async def delete_transaction(txn_id: int, db: Session = Depends(get_db)):
    """Delete a transaction and properly recalculate positions to prevent desync."""
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    portfolio_id = txn.portfolio_id
    db.delete(txn)
    db.commit()

    # Automatically recalculate positions if it was linked to a portfolio
    if portfolio_id:
        db.query(Position).filter(Position.portfolio_id == portfolio_id).delete()
        db.flush()
        
        remaining_txns = db.query(Transaction).filter(
            Transaction.portfolio_id == portfolio_id,
            Transaction.type.in_(["BUY", "SELL"])
        ).order_by(Transaction.date.asc()).all()

        for t in remaining_txns:
            _update_position(db, portfolio_id, t.symbol, t.asset_type, t.type, t.qty or 0, t.price or 0, t.date)
        
        db.commit()
        # Invalidate cache
        cache_delete(f"portfolio_history_{portfolio_id}")

    return {"status": "deleted", "id": txn_id}


# ── Positions ─────────────────────────────────────────────────────────────────

@router.get("/positions")
async def list_positions(
    portfolio_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """List all positions, optionally filtered by portfolio."""
    query = db.query(Position)
    if portfolio_id:
        query = query.filter(Position.portfolio_id == portfolio_id)
    positions = query.all()
    return {"positions": [PositionResponse.model_validate(p).model_dump() for p in positions]}


@router.post("/positions/recalculate/{portfolio_id}")
async def recalculate_positions(portfolio_id: int, db: Session = Depends(get_db)):
    """Rebuild all positions from transaction history (FIFO)."""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    db.query(Position).filter(Position.portfolio_id == portfolio_id).delete()
    db.flush()

    txns = db.query(Transaction).filter(
        Transaction.portfolio_id == portfolio_id,
        Transaction.type.in_(["BUY", "SELL"])
    ).order_by(Transaction.date.asc()).all()

    for txn in txns:
        _update_position(db, portfolio_id, txn.symbol, txn.asset_type, txn.type, txn.qty or 0, txn.price or 0, txn.date)

    db.commit()
    positions = db.query(Position).filter(Position.portfolio_id == portfolio_id).all()
    logger.info(f"Positions recalculated for portfolio {portfolio_id}: {len(positions)} positions")
    return {"positions": [PositionResponse.model_validate(p).model_dump() for p in positions]}


# ── Helper: Position Update Logic ─────────────────────────────────────────────

def _update_position(db: Session, portfolio_id: int, symbol: str, asset_type: str,
                     tx_type: str, qty: float, price: float, date: datetime):
    """Update or create a position based on a BUY/SELL transaction."""
    position = db.query(Position).filter(
        Position.portfolio_id == portfolio_id,
        Position.symbol == symbol,
    ).first()

    if tx_type == "BUY":
        if position:
            total_cost = (position.qty * position.avg_cost) + (qty * price)
            position.qty += qty
            position.avg_cost = total_cost / position.qty if position.qty > 0 else 0
            position.last_transaction_at = date
            db.flush()
        else:
            position = Position(
                portfolio_id=portfolio_id,
                symbol=symbol,
                asset_type=asset_type,
                qty=qty,
                avg_cost=price,
                first_buy_date=date,
                last_transaction_at=date,
            )
            db.add(position)
            db.flush()

    elif tx_type == "SELL":
        if position and position.qty > 0:
            sell_qty = min(qty, position.qty)
            realized = (price - position.avg_cost) * sell_qty
            position.realized_pnl = (position.realized_pnl or 0) + realized
            position.qty -= sell_qty
            position.last_transaction_at = date
            if position.qty <= 0.0001:
                position.qty = 0
                position.avg_cost = 0
            db.flush()
