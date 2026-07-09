"""enable RLS on all app tables

With Supabase, the public anon key can reach every public-schema table through
PostgREST. Our API-owned tables must not be readable/writable that way: enabling
RLS with no policies denies all PostgREST access, while our backend (table
owner) is unaffected. Future tables: enable RLS in their migration too (see
PLAYBOOK.md).

Revision ID: b2c4e6a80001
Revises: f1479a29d4b0
Create Date: 2026-07-09
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'b2c4e6a80001'
down_revision: Union[str, None] = 'f1479a29d4b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _all_tables(conn) -> list[str]:
    rows = conn.exec_driver_sql(
        "SELECT tablename FROM pg_tables "
        "WHERE schemaname='public' AND tablename <> 'alembic_version'"
    )
    return [r[0] for r in rows]


def upgrade() -> None:
    conn = op.get_bind()
    for t in _all_tables(conn):
        op.execute(f'ALTER TABLE "{t}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    conn = op.get_bind()
    for t in _all_tables(conn):
        op.execute(f'ALTER TABLE "{t}" DISABLE ROW LEVEL SECURITY')
