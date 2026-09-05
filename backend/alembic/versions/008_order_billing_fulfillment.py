"""create sales_orders, fulfillment, shipments, billing, subscriptions, credit_notes, payments tables

Revision ID: 008_order_billing_fulfillment
Revises: 007_portal_negotiation_realtime
Create Date: 2026-09-05 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '008_order_billing_fulfillment'
down_revision: Union[str, None] = '007_portal_negotiation_realtime'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add fulfillment columns to warehouses
    op.add_column('warehouses', sa.Column('fulfillment_priority', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('warehouses', sa.Column('shipping_cost_weight', sa.Numeric(precision=6, scale=2), nullable=False, server_default='1.00'))
    op.add_column('warehouses', sa.Column('base_shipping_cost', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'))

    # 2. Add proration and cancellation columns to billing_plans
    op.add_column('billing_plans', sa.Column('proration_method', sa.String(length=30), nullable=False, server_default='DAILY'))
    op.add_column('billing_plans', sa.Column('cancellation_method', sa.String(length=30), nullable=False, server_default='END_OF_PERIOD'))

    # 3. sales_orders
    op.create_table(
        'sales_orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=True),
        sa.Column('confirmed_quote_version_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('sales_rep_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='FULFILLMENT'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('payment_terms_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('gross_subtotal', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('discount_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('net_total', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_cost', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('margin_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('margin_pct', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('customer_confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('net_total >= 0', name='ck_sales_orders_net_total_ge_zero'),
        sa.ForeignKeyConstraint(['confirmed_quote_version_id'], ['quote_versions.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['sales_rep_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number'),
        sa.UniqueConstraint('quotation_id')
    )
    op.create_index(op.f('ix_sales_orders_customer_id'), 'sales_orders', ['customer_id'], unique=False)
    op.create_index(op.f('ix_sales_orders_order_number'), 'sales_orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_sales_orders_sales_rep_id'), 'sales_orders', ['sales_rep_id'], unique=False)
    op.create_index(op.f('ix_sales_orders_status'), 'sales_orders', ['status'], unique=False)

    # 4. sales_order_lines
    op.create_table(
        'sales_order_lines',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=False),
        sa.Column('source_quote_line_id', sa.Integer(), nullable=True),
        sa.Column('source_quote_version_line_id', sa.Integer(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('billing_plan_id', sa.Integer(), nullable=True),
        sa.Column('product_sku_snapshot', sa.String(length=100), nullable=False),
        sa.Column('product_name_snapshot', sa.String(length=255), nullable=False),
        sa.Column('product_description_snapshot', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('unit_list_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('line_discount_pct', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('effective_discount_pct', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('gross_line_total', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('net_line_total', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('line_cost', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('margin_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('margin_pct', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('billing_type', sa.String(length=20), nullable=False, server_default='ONE_TIME'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('quantity > 0', name='ck_sales_order_lines_quantity_gt_zero'),
        sa.CheckConstraint('unit_list_price >= 0', name='ck_sales_order_lines_unit_list_price_ge_zero'),
        sa.ForeignKeyConstraint(['billing_plan_id'], ['billing_plans.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_quote_line_id'], ['quotation_lines.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['source_quote_version_line_id'], ['quote_version_lines.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_order_lines_sales_order_id'), 'sales_order_lines', ['sales_order_id'], unique=False)

    # 5. fulfillment_plans
    op.create_table(
        'fulfillment_plans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=False),
        sa.Column('plan_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('plan_type', sa.String(length=50), nullable=False, server_default='SYSTEM_RECOMMENDED'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('estimated_shipment_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('estimated_shipping_cost', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fulfillment_plans_sales_order_id'), 'fulfillment_plans', ['sales_order_id'], unique=False)

    # 6. fulfillment_allocations
    op.create_table(
        'fulfillment_allocations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fulfillment_plan_id', sa.Integer(), nullable=False),
        sa.Column('sales_order_line_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('allocated_qty', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('reserved_qty', sa.Numeric(precision=15, scale=4), nullable=False, server_default='0.0000'),
        sa.Column('fulfilled_qty', sa.Numeric(precision=15, scale=4), nullable=False, server_default='0.0000'),
        sa.Column('estimated_shipping_cost', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('allocated_qty >= 0', name='ck_allocations_allocated_qty_ge_zero'),
        sa.CheckConstraint('reserved_qty >= 0', name='ck_allocations_reserved_qty_ge_zero'),
        sa.CheckConstraint('fulfilled_qty >= 0', name='ck_allocations_fulfilled_qty_ge_zero'),
        sa.CheckConstraint('fulfilled_qty <= allocated_qty', name='ck_allocations_fulfilled_le_allocated'),
        sa.ForeignKeyConstraint(['fulfillment_plan_id'], ['fulfillment_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sales_order_line_id'], ['sales_order_lines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fulfillment_allocations_fulfillment_plan_id'), 'fulfillment_allocations', ['fulfillment_plan_id'], unique=False)
    op.create_index(op.f('ix_fulfillment_allocations_sales_order_line_id'), 'fulfillment_allocations', ['sales_order_line_id'], unique=False)
    op.create_index(op.f('ix_fulfillment_allocations_warehouse_id'), 'fulfillment_allocations', ['warehouse_id'], unique=False)

    # 7. backorders
    op.create_table(
        'backorders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=False),
        sa.Column('sales_order_line_id', sa.Integer(), nullable=False),
        sa.Column('requested_qty', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('backordered_qty', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('fulfilled_from_backorder_qty', sa.Numeric(precision=15, scale=4), nullable=False, server_default='0.0000'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='OPEN'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('requested_qty > 0', name='ck_backorders_requested_qty_gt_zero'),
        sa.CheckConstraint('backordered_qty >= 0', name='ck_backorders_backordered_qty_ge_zero'),
        sa.CheckConstraint('fulfilled_from_backorder_qty >= 0', name='ck_backorders_fulfilled_from_backorder_ge_zero'),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sales_order_line_id'], ['sales_order_lines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backorders_sales_order_id'), 'backorders', ['sales_order_id'], unique=False)
    op.create_index(op.f('ix_backorders_sales_order_line_id'), 'backorders', ['sales_order_line_id'], unique=False)
    op.create_index(op.f('ix_backorders_status'), 'backorders', ['status'], unique=False)

    # 8. shipments
    op.create_table(
        'shipments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('shipment_number', sa.String(length=50), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PLANNED'),
        sa.Column('estimated_cost', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('actual_cost', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('shipment_number')
    )
    op.create_index(op.f('ix_shipments_sales_order_id'), 'shipments', ['sales_order_id'], unique=False)
    op.create_index(op.f('ix_shipments_shipment_number'), 'shipments', ['shipment_number'], unique=True)
    op.create_index(op.f('ix_shipments_status'), 'shipments', ['status'], unique=False)
    op.create_index(op.f('ix_shipments_warehouse_id'), 'shipments', ['warehouse_id'], unique=False)

    # 9. shipment_lines
    op.create_table(
        'shipment_lines',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('shipment_id', sa.Integer(), nullable=False),
        sa.Column('sales_order_line_id', sa.Integer(), nullable=False),
        sa.Column('fulfillment_allocation_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('quantity > 0', name='ck_shipment_lines_quantity_gt_zero'),
        sa.ForeignKeyConstraint(['fulfillment_allocation_id'], ['fulfillment_allocations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['sales_order_line_id'], ['sales_order_lines.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shipment_lines_shipment_id'), 'shipment_lines', ['shipment_id'], unique=False)

    # 10. invoices
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('invoice_type', sa.String(length=30), nullable=False, server_default='ONE_TIME'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ISSUED'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('credited_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('paid_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('balance_due', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('issue_date', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('billing_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('billing_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('total_amount >= 0', name='ck_invoices_total_amount_ge_zero'),
        sa.CheckConstraint('credited_amount >= 0', name='ck_invoices_credited_amount_ge_zero'),
        sa.CheckConstraint('paid_amount >= 0', name='ck_invoices_paid_amount_ge_zero'),
        sa.CheckConstraint('balance_due >= 0', name='ck_invoices_balance_due_ge_zero'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number')
    )
    op.create_index(op.f('ix_invoices_customer_id'), 'invoices', ['customer_id'], unique=False)
    op.create_index(op.f('ix_invoices_invoice_number'), 'invoices', ['invoice_number'], unique=True)
    op.create_index(op.f('ix_invoices_sales_order_id'), 'invoices', ['sales_order_id'], unique=False)
    op.create_index(op.f('ix_invoices_status'), 'invoices', ['status'], unique=False)

    # 10.1 invoice_lines
    op.create_table(
        'invoice_lines',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('sales_order_line_id', sa.Integer(), nullable=True),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('line_type', sa.String(length=30), nullable=False, server_default='ONE_TIME'),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('billing_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('billing_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('quantity > 0', name='ck_invoice_lines_quantity_gt_zero'),
        sa.CheckConstraint('amount >= 0', name='ck_invoice_lines_amount_ge_zero'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sales_order_line_id'], ['sales_order_lines.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_lines_invoice_id'), 'invoice_lines', ['invoice_id'], unique=False)

    # 11. subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subscription_number', sa.String(length=50), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=False),
        sa.Column('sales_order_line_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('billing_plan_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
        sa.Column('quantity', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('interval_months', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('proration_method', sa.String(length=30), nullable=False, server_default='DAILY'),
        sa.Column('cancellation_method', sa.String(length=30), nullable=False, server_default='END_OF_PERIOD'),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('next_billing_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('quantity > 0', name='ck_subscriptions_quantity_gt_zero'),
        sa.CheckConstraint('unit_price >= 0', name='ck_subscriptions_unit_price_ge_zero'),
        sa.CheckConstraint('interval_months >= 1', name='ck_subscriptions_interval_months_ge_one'),
        sa.ForeignKeyConstraint(['billing_plan_id'], ['billing_plans.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['sales_order_line_id'], ['sales_order_lines.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('subscription_number')
    )
    op.create_index(op.f('ix_subscriptions_customer_id'), 'subscriptions', ['customer_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_sales_order_id'), 'subscriptions', ['sales_order_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_status'), 'subscriptions', ['status'], unique=False)
    op.create_index(op.f('ix_subscriptions_subscription_number'), 'subscriptions', ['subscription_number'], unique=True)

    # 12. billing_schedules
    op.create_table(
        'billing_schedules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('billing_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scheduled_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='SCHEDULED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('sequence >= 1', name='ck_billing_schedules_sequence_ge_one'),
        sa.CheckConstraint('scheduled_amount >= 0', name='ck_billing_schedules_amount_ge_zero'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_billing_schedules_billing_date'), 'billing_schedules', ['billing_date'], unique=False)
    op.create_index(op.f('ix_billing_schedules_invoice_id'), 'billing_schedules', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_billing_schedules_status'), 'billing_schedules', ['status'], unique=False)
    op.create_index(op.f('ix_billing_schedules_subscription_id'), 'billing_schedules', ['subscription_id'], unique=False)

    # Add FK subscription_id to invoice_lines
    op.create_foreign_key('fk_invoice_lines_subscription', 'invoice_lines', 'subscriptions', ['subscription_id'], ['id'], ondelete='SET NULL')

    # 13. credit_notes
    op.create_table(
        'credit_notes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('credit_note_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ISSUED'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('amount > 0', name='ck_credit_notes_amount_gt_zero'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('credit_note_number')
    )
    op.create_index(op.f('ix_credit_notes_credit_note_number'), 'credit_notes', ['credit_note_number'], unique=True)
    op.create_index(op.f('ix_credit_notes_customer_id'), 'credit_notes', ['customer_id'], unique=False)
    op.create_index(op.f('ix_credit_notes_status'), 'credit_notes', ['status'], unique=False)

    # 14. credit_note_lines
    op.create_table(
        'credit_note_lines',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('credit_note_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=4), nullable=False, server_default='1.0000'),
        sa.Column('unit_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('amount > 0', name='ck_credit_note_lines_amount_gt_zero'),
        sa.ForeignKeyConstraint(['credit_note_id'], ['credit_notes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credit_note_lines_credit_note_id'), 'credit_note_lines', ['credit_note_id'], unique=False)

    # 15. payments
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('payment_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False, server_default='BANK_TRANSFER'),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('recorded_by_user_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='RECORDED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('amount > 0', name='ck_payments_amount_gt_zero'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['recorded_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_number')
    )
    op.create_index(op.f('ix_payments_customer_id'), 'payments', ['customer_id'], unique=False)
    op.create_index(op.f('ix_payments_payment_number'), 'payments', ['payment_number'], unique=True)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)

    # 16. payment_allocations
    op.create_table(
        'payment_allocations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('payment_id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('amount > 0', name='ck_payment_allocations_amount_gt_zero'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_allocations_invoice_id'), 'payment_allocations', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_payment_allocations_payment_id'), 'payment_allocations', ['payment_id'], unique=False)

    # 17. order_audit_events
    op.create_table(
        'order_audit_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=False),
        sa.Column('actor_user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('from_status', sa.String(length=50), nullable=True),
        sa.Column('to_status', sa.String(length=50), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_audit_events_created_at'), 'order_audit_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_order_audit_events_event_type'), 'order_audit_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_order_audit_events_sales_order_id'), 'order_audit_events', ['sales_order_id'], unique=False)


def downgrade() -> None:
    op.drop_table('order_audit_events')
    op.drop_table('payment_allocations')
    op.drop_table('payments')
    op.drop_table('credit_note_lines')
    op.drop_table('credit_notes')
    op.drop_constraint('fk_invoice_lines_subscription', 'invoice_lines', type_='foreignkey')
    op.drop_table('billing_schedules')
    op.drop_table('subscriptions')
    op.drop_table('invoice_lines')
    op.drop_table('invoices')
    op.drop_table('shipment_lines')
    op.drop_table('shipments')
    op.drop_table('backorders')
    op.drop_table('fulfillment_allocations')
    op.drop_table('fulfillment_plans')
    op.drop_table('sales_order_lines')
    op.drop_table('sales_orders')

    op.drop_column('billing_plans', 'cancellation_method')
    op.drop_column('billing_plans', 'proration_method')

    op.drop_column('warehouses', 'base_shipping_cost')
    op.drop_column('warehouses', 'shipping_cost_weight')
    op.drop_column('warehouses', 'fulfillment_priority')
