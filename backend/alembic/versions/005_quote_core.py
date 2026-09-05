"""create quotation core tables

Revision ID: 005_quote_core
Revises: 004_commercial_config
Create Date: 2026-09-05 18:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_quote_core'
down_revision: Union[str, None] = '004_commercial_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. quotations
    op.create_table(
        'quotations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quote_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('sales_rep_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='DRAFT', nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
        sa.Column('payment_terms_days', sa.Integer(), server_default='30', nullable=False),
        sa.Column('order_discount_pct', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('gross_subtotal', sa.Numeric(precision=14, scale=2), server_default='0.00', nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=14, scale=2), server_default='0.00', nullable=False),
        sa.Column('net_total', sa.Numeric(precision=14, scale=2), server_default='0.00', nullable=False),
        sa.Column('total_cost', sa.Numeric(precision=14, scale=2), server_default='0.00', nullable=False),
        sa.Column('margin_amount', sa.Numeric(precision=14, scale=2), server_default='0.00', nullable=False),
        sa.Column('margin_pct', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('weighted_effective_discount_pct', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('blended_risk_score', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('risk_level', sa.String(length=20), server_default='GREEN', nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('order_discount_pct >= 0 AND order_discount_pct <= 100', name='ck_quotations_order_discount_range'),
        sa.CheckConstraint('payment_terms_days >= 0', name='ck_quotations_payment_terms_ge_zero'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['sales_rep_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quotations_quote_number'), 'quotations', ['quote_number'], unique=True)
    op.create_index(op.f('ix_quotations_customer_id'), 'quotations', ['customer_id'], unique=False)
    op.create_index(op.f('ix_quotations_sales_rep_id'), 'quotations', ['sales_rep_id'], unique=False)
    op.create_index(op.f('ix_quotations_status'), 'quotations', ['status'], unique=False)

    # 2. quotation_lines
    op.create_table(
        'quotation_lines',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('billing_plan_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column('unit_list_price', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('line_discount_pct', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('effective_discount_pct', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('gross_line_total', sa.Numeric(precision=14, scale=2), server_default='0.00', nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=14, scale=2), server_default='0.00', nullable=False),
        sa.Column('net_line_total', sa.Numeric(precision=14, scale=2), server_default='0.00', nullable=False),
        sa.Column('line_cost', sa.Numeric(precision=14, scale=2), server_default='0.00', nullable=False),
        sa.Column('margin_amount', sa.Numeric(precision=14, scale=2), server_default='0.00', nullable=False),
        sa.Column('margin_pct', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('resolved_discount_policy_id', sa.Integer(), nullable=True),
        sa.Column('standard_discount_pct_snapshot', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('max_discount_pct_snapshot', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('discount_overage_pct', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('risk_level', sa.String(length=20), server_default='GREEN', nullable=False),
        sa.Column('source_type', sa.String(length=50), server_default='MANUAL', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('quantity > 0', name='ck_quotation_lines_quantity_gt_zero'),
        sa.CheckConstraint('line_discount_pct >= 0 AND line_discount_pct <= 100', name='ck_quotation_lines_discount_range'),
        sa.ForeignKeyConstraint(['billing_plan_id'], ['billing_plans.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_discount_policy_id'], ['discount_policies.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quotation_lines_quotation_id'), 'quotation_lines', ['quotation_id'], unique=False)
    op.create_index(op.f('ix_quotation_lines_product_id'), 'quotation_lines', ['product_id'], unique=False)
    op.create_index(op.f('ix_quotation_lines_billing_plan_id'), 'quotation_lines', ['billing_plan_id'], unique=False)
    op.create_index(op.f('ix_quotation_lines_resolved_discount_policy_id'), 'quotation_lines', ['resolved_discount_policy_id'], unique=False)

    # 3. quote_risk_reasons
    op.create_table(
        'quote_risk_reasons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=False),
        sa.Column('quotation_line_id', sa.Integer(), nullable=True),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('actual_value', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('threshold_value', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quotation_line_id'], ['quotation_lines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quote_risk_reasons_quotation_id'), 'quote_risk_reasons', ['quotation_id'], unique=False)
    op.create_index(op.f('ix_quote_risk_reasons_quotation_line_id'), 'quote_risk_reasons', ['quotation_line_id'], unique=False)

    # 4. quote_audit_events
    op.create_table(
        'quote_audit_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=False),
        sa.Column('actor_user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('from_status', sa.String(length=50), nullable=True),
        sa.Column('to_status', sa.String(length=50), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quote_audit_events_quotation_id'), 'quote_audit_events', ['quotation_id'], unique=False)
    op.create_index(op.f('ix_quote_audit_events_actor_user_id'), 'quote_audit_events', ['actor_user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_quote_audit_events_actor_user_id'), table_name='quote_audit_events')
    op.drop_index(op.f('ix_quote_audit_events_quotation_id'), table_name='quote_audit_events')
    op.drop_table('quote_audit_events')

    op.drop_index(op.f('ix_quote_risk_reasons_quotation_line_id'), table_name='quote_risk_reasons')
    op.drop_index(op.f('ix_quote_risk_reasons_quotation_id'), table_name='quote_risk_reasons')
    op.drop_table('quote_risk_reasons')

    op.drop_index(op.f('ix_quotation_lines_resolved_discount_policy_id'), table_name='quotation_lines')
    op.drop_index(op.f('ix_quotation_lines_billing_plan_id'), table_name='quotation_lines')
    op.drop_index(op.f('ix_quotation_lines_product_id'), table_name='quotation_lines')
    op.drop_index(op.f('ix_quotation_lines_quotation_id'), table_name='quotation_lines')
    op.drop_table('quotation_lines')

    op.drop_index(op.f('ix_quotations_status'), table_name='quotations')
    op.drop_index(op.f('ix_quotations_sales_rep_id'), table_name='quotations')
    op.drop_index(op.f('ix_quotations_customer_id'), table_name='quotations')
    op.drop_index(op.f('ix_quotations_quote_number'), table_name='quotations')
    op.drop_table('quotations')
