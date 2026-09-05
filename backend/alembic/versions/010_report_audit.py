"""010_report_audit

Revision ID: 010_report_audit
Revises: 009_deal_health
Create Date: 2026-09-05 21:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '010_report_audit'
down_revision: Union[str, None] = '009_deal_health'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    export_status_enum = postgresql.ENUM('SUCCESS', 'FAILED', name='exportstatus', create_type=False)
    postgresql.ENUM('SUCCESS', 'FAILED', name='exportstatus').create(op.get_bind(), checkfirst=True)

    op.create_table(
        'report_export_audits',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(length=64), nullable=False),
        sa.Column('format', sa.String(length=16), nullable=False),
        sa.Column('filters_json', sa.JSON(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('status', export_status_enum, nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_export_audits_id'), 'report_export_audits', ['id'], unique=False)
    op.create_index(op.f('ix_report_export_audits_user_id'), 'report_export_audits', ['user_id'], unique=False)
    op.create_index(op.f('ix_report_export_audits_report_type'), 'report_export_audits', ['report_type'], unique=False)
    op.create_index(op.f('ix_report_export_audits_generated_at'), 'report_export_audits', ['generated_at'], unique=False)
    op.create_index(op.f('ix_report_export_audits_status'), 'report_export_audits', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_report_export_audits_status'), table_name='report_export_audits')
    op.drop_index(op.f('ix_report_export_audits_generated_at'), table_name='report_export_audits')
    op.drop_index(op.f('ix_report_export_audits_report_type'), table_name='report_export_audits')
    op.drop_index(op.f('ix_report_export_audits_user_id'), table_name='report_export_audits')
    op.drop_index(op.f('ix_report_export_audits_id'), table_name='report_export_audits')
    op.drop_table('report_export_audits')

    postgresql.ENUM(name='exportstatus').drop(op.get_bind(), checkfirst=True)
