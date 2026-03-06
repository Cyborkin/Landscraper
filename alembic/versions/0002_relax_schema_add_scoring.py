"""relax development schema constraints, add scoring columns

Revision ID: 0002_relax_schema
Revises: 77e8c27216a6
Create Date: 2026-03-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002_relax_schema'
down_revision: Union[str, Sequence[str], None] = '77e8c27216a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Relax NOT NULL constraints and add scoring/dedup columns."""
    # --- Relax NOT NULL on existing developments columns ---
    op.alter_column('developments', 'jurisdiction',
                    existing_type=sa.String(255),
                    nullable=True)
    op.alter_column('developments', 'address_city',
                    existing_type=sa.String(255),
                    nullable=True)
    op.alter_column('developments', 'county',
                    existing_type=sa.String(100),
                    nullable=True)
    op.alter_column('developments', 'permit_type',
                    existing_type=sa.String(50),
                    nullable=True)
    op.alter_column('developments', 'permit_status',
                    existing_type=sa.String(50),
                    nullable=True)
    op.alter_column('developments', 'property_type',
                    existing_type=sa.String(50),
                    nullable=True)

    # --- Add new columns ---
    op.add_column('developments',
                  sa.Column('content_hash', sa.String(64), nullable=True))
    op.add_column('developments',
                  sa.Column('score_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('developments',
                  sa.Column('validation_status', sa.String(20), nullable=True))
    op.add_column('developments',
                  sa.Column('lead_score', sa.Integer(), nullable=True))
    op.add_column('developments',
                  sa.Column('tier', sa.String(20), nullable=True))

    # --- Indexes on new columns ---
    op.create_index(op.f('ix_developments_content_hash'), 'developments',
                    ['content_hash'], unique=True)
    op.create_index(op.f('ix_developments_tier'), 'developments',
                    ['tier'], unique=False)


def downgrade() -> None:
    """Remove scoring columns and restore NOT NULL constraints."""
    # --- Drop indexes on new columns ---
    op.drop_index(op.f('ix_developments_tier'), table_name='developments')
    op.drop_index(op.f('ix_developments_content_hash'), table_name='developments')

    # --- Drop new columns ---
    op.drop_column('developments', 'tier')
    op.drop_column('developments', 'lead_score')
    op.drop_column('developments', 'validation_status')
    op.drop_column('developments', 'score_breakdown')
    op.drop_column('developments', 'content_hash')

    # --- Restore NOT NULL on existing columns ---
    op.alter_column('developments', 'property_type',
                    existing_type=sa.String(50),
                    nullable=False)
    op.alter_column('developments', 'permit_status',
                    existing_type=sa.String(50),
                    nullable=False)
    op.alter_column('developments', 'permit_type',
                    existing_type=sa.String(50),
                    nullable=False)
    op.alter_column('developments', 'county',
                    existing_type=sa.String(100),
                    nullable=False)
    op.alter_column('developments', 'address_city',
                    existing_type=sa.String(255),
                    nullable=False)
    op.alter_column('developments', 'jurisdiction',
                    existing_type=sa.String(255),
                    nullable=False)
