"""
AJEL Capital — SQLAlchemy Models (Phase 2)
Security note: Passwords are hashed via bcrypt, never stored in plaintext.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON, Enum as SAEnum, text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class TransactionType(str, enum.Enum):
    buy = "BUY"
    sell = "SELL"
    dividend = "DIVIDEND"
    deposit = "DEPOSIT"
    withdrawal = "WITHDRAWAL"
    stock_split = "STOCK_SPLIT"
    fee = "FEE"

class AssetType(str, enum.Enum):
    stock = "stock"
    etf = "etf"
    crypto = "crypto"
    bond = "bond"
    commodity = "commodity"
    cash = "cash"

class FeeEventType(str, enum.Enum):
    management_monthly = "management_monthly"
    management_annual = "management_annual"
    performance_5yr = "performance_5yr"


# ── Core Models ───────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    role = Column(String, default="viewer")
    two_fa_enabled = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    clients = relationship("Client", back_populates="owner")
    watchlists = relationship("Watchlist", back_populates="owner")


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    risk_profile = Column(String, default="moderate")
    aum = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ── Phase 2: Fee Structure ────────────────────────────────────────────
    initial_capital = Column(Float, default=0.0, nullable=True)
    entry_date = Column(DateTime, nullable=True)
    management_fee_pct = Column(Float, default=2.0, nullable=True)    # % annual
    performance_fee_pct = Column(Float, default=20.0, nullable=True)  # % over HWM
    hwm = Column(Float, default=0.0, nullable=True)                   # High Water Mark
    hwm_updated_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="clients")
    portfolios = relationship("Portfolio", back_populates="client", cascade="all, delete-orphan")
    fee_events = relationship("ClientFeeEvent", back_populates="client", cascade="all, delete-orphan")


class ClientFeeEvent(Base):
    """Records each fee charge for audit trail."""
    __tablename__ = "client_fee_events"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    event_type = Column(String, nullable=False)   # management_monthly, management_annual, performance_5yr
    amount = Column(Float, nullable=False)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    hwm_before = Column(Float, nullable=True)
    hwm_after = Column(Float, nullable=True)
    aum_at_charge = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="fee_events")


class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)  # NULL = personal/pool
    name = Column(String, nullable=False, default="Main Pool")
    description = Column(Text, nullable=True)
    currency = Column(String, default="USD")
    benchmark = Column(String, default="SPY")
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    client = relationship("Client", back_populates="portfolios")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioHistory(Base):
    """Daily/periodic snapshots of portfolio value for equity curve."""
    __tablename__ = "portfolio_history"
    __table_args__ = (
        Index("idx_portfolio_history_portfolio_date", "portfolio_id", "date"),
    )
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    total_value = Column(Float, default=0.0)
    cash_balance = Column(Float, default=0.0)
    portfolio = relationship("Portfolio", backref="history")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_transactions_portfolio_symbol", "portfolio_id", "symbol"),
        Index("idx_transactions_portfolio_date", "portfolio_id", "date"),
    )
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    symbol = Column(String, index=True, nullable=True)          # nullable for deposits/withdrawals
    type = Column(String, nullable=False)                        # BUY, SELL, DIVIDEND, DEPOSIT, WITHDRAWAL, STOCK_SPLIT, FEE
    asset_type = Column(String, default="stock")                 # stock, etf, crypto, bond, commodity, cash
    broker = Column(String, nullable=True)
    qty = Column(Float, nullable=True, default=0.0)              # nullable for deposits
    price = Column(Float, nullable=True, default=0.0)            # nullable for deposits
    total_amount = Column(Float, nullable=True, default=0.0)     # Phase 2: qty × price or deposit amount
    date = Column(DateTime, default=datetime.utcnow)
    fees = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    # Trading journal fields
    conviction = Column(String, nullable=True)
    emotion = Column(String, nullable=True)
    thesis = Column(Text, nullable=True)
    lesson = Column(Text, nullable=True)
    currency = Column(String, default="USD", nullable=True)
    # Phase 2b: Client Deposit Tracking
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    hwm_baseline = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    portfolio = relationship("Portfolio", back_populates="transactions")


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        Index("idx_positions_portfolio_symbol", "portfolio_id", "symbol"),
    )
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    symbol = Column(String, index=True, nullable=False)
    asset_type = Column(String, default="stock")
    qty = Column(Float, nullable=False, default=0.0)
    avg_cost = Column(Float, nullable=False, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    first_buy_date = Column(DateTime, nullable=True)
    last_transaction_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    portfolio = relationship("Portfolio", back_populates="positions")


class Watchlist(Base):
    __tablename__ = "watchlists"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    symbols = Column(Text, default="")
    owner = relationship("User", back_populates="watchlists")


class PriceCache(Base):
    __tablename__ = "price_cache"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    price = Column(Float)
    change = Column(Float, default=0.0)
    change_pct = Column(Float, default=0.0)
    prev_close = Column(Float, nullable=True)
    high_52w = Column(Float, nullable=True)
    low_52w = Column(Float, nullable=True)
    source = Column(String, default="yahoo_v8")
    fetched_at = Column(DateTime, default=datetime.utcnow)


class IntelligenceReport(Base):
    __tablename__ = "intelligence_reports"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    composite_score = Column(Float)
    technical_score = Column(Float)
    fundamental_score = Column(Float)
    macro_score = Column(Float)
    verdict = Column(String)
    sma_50 = Column(Float, nullable=True)
    sma_200 = Column(Float, nullable=True)
    rsi_14 = Column(Float, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
