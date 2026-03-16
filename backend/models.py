"""
models.py — All SQLAlchemy database table definitions
CRITICAL: Every table must have tenant_id for multi-tenant SaaS
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.db import Base

def new_uuid():
    return str(uuid.uuid4())

class User(Base):
    """Platform users — one per subscriber."""
    __tablename__ = "users"
    id            = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    tenant_id     = Column(UUID(as_uuid=False), nullable=False, index=True)
    email         = Column(String(255), nullable=False, unique=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RegimeContext(Base):
    """Layer 0 output — daily market regime classification."""
    __tablename__ = "regime_context"
    id                       = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    tenant_id                = Column(UUID(as_uuid=False), nullable=False, index=True)
    date                     = Column(String(10), nullable=False, index=True)
    regime                   = Column(String(50), nullable=False)
    regime_score             = Column(Integer, default=50)
    india_vix                = Column(Float, default=15.0)
    is_expiry_day            = Column(Boolean, default=False)
    is_rbi_day               = Column(Boolean, default=False)
    is_budget_day            = Column(Boolean, default=False)
    do_not_trade             = Column(Boolean, default=False)
    signal_threshold_l2      = Column(Integer, default=60)
    position_size_multiplier = Column(Float, default=1.0)
    allowed_directions       = Column(JSONB, default=list)
    regime_reason            = Column(Text, default="")
    created_at               = Column(DateTime, default=datetime.utcnow)

class CompanyIntel(Base):
    """Layer 1 output — per-company intelligence file stored in DB."""
    __tablename__ = "company_intel"
    id            = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    tenant_id     = Column(UUID(as_uuid=False), nullable=False, index=True)
    ticker        = Column(String(20), nullable=False, index=True)
    date          = Column(String(10), nullable=False, index=True)
    data_json     = Column(JSONB, default=dict)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TradingScore(Base):
    """Layer 2 output — buy and short scores per company per day."""
    __tablename__ = "trading_scores"
    id            = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    tenant_id     = Column(UUID(as_uuid=False), nullable=False, index=True)
    ticker        = Column(String(20), nullable=False, index=True)
    date          = Column(String(10), nullable=False, index=True)
    buy_score     = Column(Float, default=0.0)
    short_score   = Column(Float, default=0.0)
    signal        = Column(String(30), default="avoid")
    top_factors   = Column(JSONB, default=list)
    created_at    = Column(DateTime, default=datetime.utcnow)

class ValidatedSignal(Base):
    """Layer 3 output — technically validated trade setups."""
    __tablename__ = "validated_signals"
    id                = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    tenant_id         = Column(UUID(as_uuid=False), nullable=False, index=True)
    ticker            = Column(String(20), nullable=False, index=True)
    date              = Column(String(10), nullable=False, index=True)
    direction         = Column(String(10), default="BUY")
    confidence_score  = Column(Float, default=0.0)
    entry_low         = Column(Float, default=0.0)
    entry_high        = Column(Float, default=0.0)
    target_1          = Column(Float, default=0.0)
    target_2          = Column(Float, default=0.0)
    stop_loss         = Column(Float, default=0.0)
    risk_reward       = Column(Float, default=0.0)
    final_signal      = Column(String(30), default="AVOID")
    narrative         = Column(Text, default="")
    created_at        = Column(DateTime, default=datetime.utcnow)

class PaperTrade(Base):
    """Layer 5 output — paper trades in Learn Mode."""
    __tablename__ = "paper_trades"
    id              = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    tenant_id       = Column(UUID(as_uuid=False), nullable=False, index=True)
    ticker          = Column(String(20), nullable=False)
    direction       = Column(String(10), nullable=False)
    entry_price     = Column(Float, nullable=False)
    target_1        = Column(Float, nullable=False)
    stop_loss       = Column(Float, nullable=False)
    exit_price      = Column(Float, default=0.0)
    exit_reason     = Column(String(20), default="open")
    pnl_pct         = Column(Float, default=0.0)
    outcome         = Column(String(10), default="open")
    retrain_trigger = Column(Boolean, default=False)
    l2_score        = Column(Float, default=0.0)
    confidence      = Column(Float, default=0.0)
    trade_date      = Column(String(10), nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)
    closed_at       = Column(DateTime, nullable=True)

class PersonalityProfile(Base):
    """Layer 4 — trader personality profile, updated every 5 trades."""
    __tablename__ = "personality_profiles"
    id              = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    tenant_id       = Column(UUID(as_uuid=False), nullable=False, unique=True)
    profile_version = Column(Integer, default=1)
    profile_json    = Column(JSONB, default=dict)
    coaching_note   = Column(Text, default="")
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ModelWeight(Base):
    """Feedback loop — L2 scoring factor weights per tenant."""
    __tablename__ = "model_weights"
    id          = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    tenant_id   = Column(UUID(as_uuid=False), nullable=False, index=True)
    layer       = Column(String(10), nullable=False)
    factor_name = Column(String(50), nullable=False)
    weight      = Column(Float, default=1.0)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
