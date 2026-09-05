"""009_deal_health

Revision ID: 009_deal_health
Revises: 008_order_billing_fulfillment
Create Date: 2026-09-05 21:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '009_deal_health'
down_revision: Union[str, None] = '008_order_billing_fulfillment'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. deal_health_configs
    op.create_table(
        'deal_health_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), server_default='Default Health Policy', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('healthy_min_score', sa.Numeric(precision=5, scale=2), server_default='80.00', nullable=False),
        sa.Column('watch_min_score', sa.Numeric(precision=5, scale=2), server_default='60.00', nullable=False),
        sa.Column('at_risk_min_score', sa.Numeric(precision=5, scale=2), server_default='30.00', nullable=False),
        sa.Column('stalled_quote_days', sa.Integer(), server_default='5', nullable=False),
        sa.Column('approval_delay_hours', sa.Integer(), server_default='24', nullable=False),
        sa.Column('negotiation_stall_days', sa.Integer(), server_default='3', nullable=False),
        sa.Column('discount_anomaly_threshold_pct', sa.Numeric(precision=5, scale=2), server_default='10.00', nullable=False),
        sa.Column('delivery_slippage_days', sa.Integer(), server_default='2', nullable=False),
        sa.Column('backorder_age_days', sa.Integer(), server_default='3', nullable=False),
        sa.Column('invoice_overdue_days', sa.Integer(), server_default='1', nullable=False),
        sa.Column('weight_stalled_quote', sa.Numeric(precision=5, scale=2), server_default='20.00', nullable=False),
        sa.Column('weight_discount_anomaly', sa.Numeric(precision=5, scale=2), server_default='15.00', nullable=False),
        sa.Column('weight_approval_delay', sa.Numeric(precision=5, scale=2), server_default='10.00', nullable=False),
        sa.Column('weight_negotiation_stall', sa.Numeric(precision=5, scale=2), server_default='15.00', nullable=False),
        sa.Column('weight_delivery_slippage', sa.Numeric(precision=5, scale=2), server_default='20.00', nullable=False),
        sa.Column('weight_backorder', sa.Numeric(precision=5, scale=2), server_default='10.00', nullable=False),
        sa.Column('weight_invoice_overdue', sa.Numeric(precision=5, scale=2), server_default='10.00', nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deal_health_configs_is_active'), 'deal_health_configs', ['is_active'], unique=False)

    # 2. deal_health_snapshots
    op.create_table(
        'deal_health_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=True),
        sa.Column('config_id', sa.Integer(), nullable=True),
        sa.Column('health_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('health_level', sa.String(length=30), nullable=False),
        sa.Column('signal_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['config_id'], ['deal_health_configs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deal_health_snapshots_calculated_at'), 'deal_health_snapshots', ['calculated_at'], unique=False)
    op.create_index(op.f('ix_deal_health_snapshots_health_level'), 'deal_health_snapshots', ['health_level'], unique=False)
    op.create_index(op.f('ix_deal_health_snapshots_quotation_id'), 'deal_health_snapshots', ['quotation_id'], unique=False)
    op.create_index(op.f('ix_deal_health_snapshots_sales_order_id'), 'deal_health_snapshots', ['sales_order_id'], unique=False)

    # 3. deal_health_signals
    op.create_table(
        'deal_health_signals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('snapshot_id', sa.Integer(), nullable=False),
        sa.Column('signal_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=30), server_default='WARNING', nullable=False),
        sa.Column('score_penalty', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('metric_value', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('threshold_value', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('signal_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['snapshot_id'], ['deal_health_snapshots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deal_health_signals_signal_type'), 'deal_health_signals', ['signal_type'], unique=False)
    op.create_index(op.f('ix_deal_health_signals_snapshot_id'), 'deal_health_signals', ['snapshot_id'], unique=False)

    # 4. deal_alerts
    op.create_table(
        'deal_alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=True),
        sa.Column('snapshot_id', sa.Integer(), nullable=True),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=30), server_default='WARNING', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='OPEN', nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('assigned_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('occurrence_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by_user_id', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['acknowledged_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['snapshot_id'], ['deal_health_snapshots.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deal_alerts_alert_type'), 'deal_alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_deal_alerts_assigned_user_id'), 'deal_alerts', ['assigned_user_id'], unique=False)
    op.create_index(op.f('ix_deal_alerts_quotation_id'), 'deal_alerts', ['quotation_id'], unique=False)
    op.create_index(op.f('ix_deal_alerts_sales_order_id'), 'deal_alerts', ['sales_order_id'], unique=False)
    op.create_index(op.f('ix_deal_alerts_severity'), 'deal_alerts', ['severity'], unique=False)
    op.create_index(op.f('ix_deal_alerts_status'), 'deal_alerts', ['status'], unique=False)

    # 5. deal_actions
    op.create_table(
        'deal_actions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('deal_alert_id', sa.Integer(), nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='COMPLETED', nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['deal_alert_id'], ['deal_alerts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deal_actions_deal_alert_id'), 'deal_actions', ['deal_alert_id'], unique=False)
    op.create_index(op.f('ix_deal_actions_quotation_id'), 'deal_actions', ['quotation_id'], unique=False)
    op.create_index(op.f('ix_deal_actions_target_user_id'), 'deal_actions', ['target_user_id'], unique=False)

    # 6. deal_health_audit_events
    op.create_table(
        'deal_health_audit_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=True),
        sa.Column('actor_user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deal_health_audit_events_event_type'), 'deal_health_audit_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_deal_health_audit_events_quotation_id'), 'deal_health_audit_events', ['quotation_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_deal_health_audit_events_quotation_id'), table_name='deal_health_audit_events')
    op.drop_index(op.f('ix_deal_health_audit_events_event_type'), table_name='deal_health_audit_events')
    op.drop_table('deal_health_audit_events')

    op.drop_index(op.f('ix_deal_actions_target_user_id'), table_name='deal_actions')
    op.drop_index(op.f('ix_deal_actions_quotation_id'), table_name='deal_actions')
    op.drop_index(op.f('ix_deal_actions_deal_alert_id'), table_name='deal_actions')
    op.drop_table('deal_actions')

    op.drop_index(op.f('ix_deal_alerts_status'), table_name='deal_alerts')
    op.drop_index(op.f('ix_deal_alerts_severity'), table_name='deal_alerts')
    op.drop_index(op.f('ix_deal_alerts_sales_order_id'), table_name='deal_alerts')
    op.drop_index(op.f('ix_deal_alerts_quotation_id'), table_name='deal_alerts')
    op.drop_index(op.f('ix_deal_alerts_assigned_user_id'), table_name='deal_alerts')
    op.drop_index(op.f('ix_deal_alerts_alert_type'), table_name='deal_alerts')
    op.drop_table('deal_alerts')

    op.drop_index(op.f('ix_deal_health_signals_snapshot_id'), table_name='deal_health_signals')
    op.drop_index(op.f('ix_deal_health_signals_signal_type'), table_name='deal_health_signals')
    op.drop_table('deal_health_signals')

    op.drop_index(op.f('ix_deal_health_snapshots_sales_order_id'), table_name='deal_health_snapshots')
    op.drop_index(op.f('ix_deal_health_snapshots_quotation_id'), table_name='deal_health_snapshots')
    op.drop_index(op.f('ix_deal_health_snapshots_health_level'), table_name='deal_health_snapshots')
    op.drop_index(op.f('ix_deal_health_snapshots_calculated_at'), table_name='deal_health_snapshots')
    op.drop_table('deal_health_snapshots')

    op.drop_index(op.f('ix_deal_health_configs_is_active'), table_name='deal_health_configs')
    op.drop_table('deal_health_configs')
