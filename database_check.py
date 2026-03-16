"""
database_check.py — Sprint 1 validator test
Verifies all TradeIQ tables exist and have tenant_id column.
Run with: python database_check.py
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()

REQUIRED_TABLES = [
    "users",
    "regime_context",
    "company_intel",
    "trading_scores",
    "validated_signals",
    "paper_trades",
    "personality_profiles",
    "model_weights",
]

async def run_check():
    """Check all tables exist and have tenant_id."""
    try:
        import sqlalchemy as sa
        from sqlalchemy.ext.asyncio import create_async_engine

        db_url = os.getenv("DATABASE_URL", "")
        if not db_url:
            print("ERROR: DATABASE_URL not set in .env")
            sys.exit(1)

        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

        engine = create_async_engine(db_url, echo=False)

        async with engine.connect() as conn:
            # Check each table exists and has tenant_id
            missing_tables   = []
            missing_tenant   = []

            for table in REQUIRED_TABLES:
                # Check table exists
                result = await conn.execute(sa.text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name=:t"
                ), {"t": table})
                exists = result.scalar() > 0

                if not exists:
                    missing_tables.append(table)
                    continue

                # Check tenant_id column exists
                result = await conn.execute(sa.text(
                    "SELECT COUNT(*) FROM information_schema.columns "
                    "WHERE table_schema='public' "
                    "AND table_name=:t AND column_name='tenant_id'"
                ), {"t": table})
                has_tenant = result.scalar() > 0

                if not has_tenant:
                    missing_tenant.append(table)
                else:
                    print(f"  OK  {table} — tenant_id present")

        await engine.dispose()

        if missing_tables:
            print(f"\nMISSING TABLES: {', '.join(missing_tables)}")
            print("Run the backend to create tables automatically.")
            sys.exit(1)

        if missing_tenant:
            print(f"\nMISSING TENANT_ID ON: {', '.join(missing_tenant)}")
            sys.exit(1)

        print("\nALL TABLES HAVE TENANT_ID")
        print(f"Total tables checked: {len(REQUIRED_TABLES)}")

    except ImportError:
        print("ERROR: sqlalchemy or asyncpg not installed.")
        print("Run: pip install sqlalchemy asyncpg psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_check())
