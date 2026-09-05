"""create customer portal, versioning, negotiation and notification tables

Revision ID: 007_portal_negotiation_realtime
Revises: 006_approval_upsell
Create Date: 2026-09-05 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007_portal_negotiation_realtime'
down_revision: Union[str, None] = '006_approval_upsell'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. customer_portal_access
    op.create_table(
        'customer_portal_access',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_customer_portal_user')
    )

    # 2. quote_versions
    op.create_table(
        'quote_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='INITIAL_RELEASE'),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('status_snapshot', sa.String(length=50), nullable=False),
        sa.Column('approval_status', sa.String(length=50), nullable=False, server_default='APPROVED'),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('payment_terms_days', sa.Integer(), nullable=False),
        sa.Column('order_discount_pct', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('gross_subtotal', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('net_total', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_cost', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('margin_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('margin_pct', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('weighted_effective_discount_pct', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('blended_risk_score', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('risk_level', sa.String(length=50), nullable=False),
        sa.Column('source_negotiation_request_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quotation_id', 'version_number', name='uq_quote_version_number')
    )

    # 3. quote_version_lines
    op.create_table(
        'quote_version_lines',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quote_version_id', sa.Integer(), nullable=False),
        sa.Column('original_quote_line_id', sa.Integer(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('billing_plan_id', sa.Integer(), nullable=True),
        sa.Column('product_sku_snapshot', sa.String(length=100), nullable=False),
        sa.Column('product_name_snapshot', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('unit_list_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('line_discount_pct', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('effective_discount_pct', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('gross_line_total', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('net_line_total', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('line_cost', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('margin_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('margin_pct', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('standard_discount_pct_snapshot', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('max_discount_pct_snapshot', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('risk_level', sa.String(length=50), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='REGULAR'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['billing_plan_id'], ['billing_plans.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['original_quote_line_id'], ['quotation_lines.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['quote_version_id'], ['quote_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. quote_negotiation_requests
    op.create_table(
        'quote_negotiation_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=False),
        sa.Column('base_quote_version_id', sa.Integer(), nullable=False),
        sa.Column('requested_by_user_id', sa.Integer(), nullable=False),
        sa.Column('request_type', sa.String(length=50), nullable=False, server_default='COUNTER_OFFER'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('requested_order_discount_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('requested_payment_terms_days', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('resolution_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['base_quote_version_id'], ['quote_versions.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requested_by_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add FK source_negotiation_request_id on quote_versions
    op.create_foreign_key(
        'fk_quote_versions_source_neg_req',
        'quote_versions',
        'quote_negotiation_requests',
        ['source_negotiation_request_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # 5. quote_negotiation_line_changes
    op.create_table(
        'quote_negotiation_line_changes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('negotiation_request_id', sa.Integer(), nullable=False),
        sa.Column('quotation_line_id', sa.Integer(), nullable=False),
        sa.Column('requested_quantity', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('requested_line_discount_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['negotiation_request_id'], ['quote_negotiation_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quotation_line_id'], ['quotation_lines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. quote_negotiation_messages
    op.create_table(
        'quote_negotiation_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=False),
        sa.Column('quote_version_id', sa.Integer(), nullable=True),
        sa.Column('quotation_line_id', sa.Integer(), nullable=True),
        sa.Column('author_user_id', sa.Integer(), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False, server_default='COMMENT'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_customer_visible', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['author_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quotation_line_id'], ['quotation_lines.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['quote_version_id'], ['quote_versions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. user_devices
    op.create_table(
        'user_devices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('device_token', sa.String(length=500), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_token', name='uq_user_device_token')
    )

    # 9. Add columns & FKs to quotations
    op.add_column('quotations', sa.Column('current_version_id', sa.Integer(), nullable=True))
    op.add_column('quotations', sa.Column('latest_approved_version_id', sa.Integer(), nullable=True))
    op.add_column('quotations', sa.Column('confirmed_quote_version_id', sa.Integer(), nullable=True))
    op.add_column('quotations', sa.Column('customer_confirmed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('quotations', sa.Column('customer_confirmed_by_user_id', sa.Integer(), nullable=True))

    op.create_foreign_key('fk_quotations_current_version', 'quotations', 'quote_versions', ['current_version_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_quotations_latest_approved_version', 'quotations', 'quote_versions', ['latest_approved_version_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_quotations_confirmed_version', 'quotations', 'quote_versions', ['confirmed_quote_version_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_quotations_confirmed_user', 'quotations', 'users', ['customer_confirmed_by_user_id'], ['id'], ondelete='SET NULL')

    # 10. Add column to quote_approval_steps
    op.add_column('quote_approval_steps', sa.Column('approval_context', sa.String(length=50), nullable=False, server_default='INITIAL'))


def downgrade() -> None:
    op.drop_column('quote_approval_steps', 'approval_context')

    op.drop_constraint('fk_quotations_confirmed_user', 'quotations', type_='foreignkey')
    op.drop_constraint('fk_quotations_confirmed_version', 'quotations', type_='foreignkey')
    op.drop_constraint('fk_quotations_latest_approved_version', 'quotations', type_='foreignkey')
    op.drop_constraint('fk_quotations_current_version', 'quotations', type_='foreignkey')

    op.drop_column('quotations', 'customer_confirmed_by_user_id')
    op.drop_column('quotations', 'customer_confirmed_at')
    op.drop_column('quotations', 'confirmed_quote_version_id')
    op.drop_column('quotations', 'latest_approved_version_id')
    op.drop_column('quotations', 'current_version_id')

    op.drop_table('user_devices')
    op.drop_table('notifications')
    op.drop_table('quote_negotiation_messages')
    op.drop_table('quote_negotiation_line_changes')

    op.drop_constraint('fk_quote_versions_source_neg_req', 'quote_versions', type_='foreignkey')
    op.drop_table('quote_negotiation_requests')
    op.drop_table('quote_version_lines')
    op.drop_table('quote_versions')
    op.drop_table('customer_portal_access')
