"""create commercial configuration tables

Revision ID: 004_create_commercial_configuration
Revises: 003_create_core_master_data
Create Date: 2026-09-05 16:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_create_commercial_configuration'
down_revision: Union[str, None] = '003_create_core_master_data'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. discount_policies
    op.create_table(
        'discount_policies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('customer_tier_id', sa.Integer(), nullable=True),
        sa.Column('product_category_id', sa.Integer(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('standard_discount_pct', sa.Numeric(precision=5, scale=2), server_default=sa.text('0.00'), nullable=False),
        sa.Column('max_discount_pct', sa.Numeric(precision=5, scale=2), server_default=sa.text('0.00'), nullable=False),
        sa.Column('priority', sa.Integer(), server_default=sa.text('100'), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('standard_discount_pct >= 0 AND standard_discount_pct <= 100', name='ck_discount_policies_standard_range'),
        sa.CheckConstraint('max_discount_pct >= 0 AND max_discount_pct <= 100', name='ck_discount_policies_max_range'),
        sa.CheckConstraint('standard_discount_pct <= max_discount_pct', name='ck_discount_policies_standard_lte_max'),
        sa.CheckConstraint('product_id IS NULL OR product_category_id IS NULL', name='ck_discount_policies_not_both_product_and_category'),
        sa.CheckConstraint('effective_to IS NULL OR effective_to > effective_from', name='ck_discount_policies_effective_to_gt_from'),
        sa.ForeignKeyConstraint(['customer_tier_id'], ['customer_tiers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_category_id'], ['product_categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discount_policies_customer_tier_id'), 'discount_policies', ['customer_tier_id'], unique=False)
    op.create_index(op.f('ix_discount_policies_product_category_id'), 'discount_policies', ['product_category_id'], unique=False)
    op.create_index(op.f('ix_discount_policies_product_id'), 'discount_policies', ['product_id'], unique=False)

    # 2. approval_policies
    op.create_table(
        'approval_policies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('customer_tier_id', sa.Integer(), nullable=True),
        sa.Column('discount_above_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('margin_below_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('payment_terms_above_days', sa.Integer(), nullable=True),
        sa.Column('approval_role', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.Integer(), server_default=sa.text('100'), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('discount_above_pct IS NOT NULL OR margin_below_pct IS NOT NULL OR payment_terms_above_days IS NOT NULL', name='ck_approval_policies_at_least_one_trigger'),
        sa.CheckConstraint('payment_terms_above_days IS NULL OR payment_terms_above_days >= 0', name='ck_approval_policies_payment_terms_nonnegative'),
        sa.CheckConstraint('effective_to IS NULL OR effective_to > effective_from', name='ck_approval_policies_effective_to_gt_from'),
        sa.ForeignKeyConstraint(['customer_tier_id'], ['customer_tiers.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approval_policies_customer_tier_id'), 'approval_policies', ['customer_tier_id'], unique=False)

    # 3. billing_plans
    op.create_table(
        'billing_plans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('billing_type', sa.String(length=20), nullable=False),
        sa.Column('billing_interval_months', sa.Integer(), nullable=True),
        sa.Column('payment_due_days', sa.Integer(), server_default=sa.text('30'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('payment_due_days >= 0', name='ck_billing_plans_payment_due_days_nonnegative'),
        sa.CheckConstraint("(billing_type = 'ONE_TIME' AND billing_interval_months IS NULL) OR (billing_type = 'RECURRING' AND billing_interval_months IS NOT NULL AND billing_interval_months >= 1)", name='ck_billing_plans_type_and_interval'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_billing_plans_code'), 'billing_plans', ['code'], unique=True)


def downgrade() -> None:
    # 3. drop billing_plans
    op.drop_index(op.f('ix_billing_plans_code'), table_name='billing_plans')
    op.drop_table('billing_plans')

    # 2. drop approval_policies
    op.drop_index(op.f('ix_approval_policies_customer_tier_id'), table_name='approval_policies')
    op.drop_table('approval_policies')

    # 1. drop discount_policies
    op.drop_index(op.f('ix_discount_policies_product_id'), table_name='discount_policies')
    op.drop_index(op.f('ix_discount_policies_product_category_id'), table_name='discount_policies')
    op.drop_index(op.f('ix_discount_policies_customer_tier_id'), table_name='discount_policies')
    op.drop_table('discount_policies')
