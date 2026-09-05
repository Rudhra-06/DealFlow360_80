"""create core master data tables

Revision ID: 003_create_core_master_data
Revises: 002_create_roles_and_users
Create Date: 2026-09-05 15:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_create_core_master_data'
down_revision: Union[str, None] = '002_create_roles_and_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. customer_tiers
    op.create_table(
        'customer_tiers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customer_tiers_name'), 'customer_tiers', ['name'], unique=True)

    # 2. customers
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('tier_id', sa.Integer(), nullable=False),
        sa.Column('billing_address', sa.Text(), nullable=True),
        sa.Column('shipping_address', sa.Text(), nullable=True),
        sa.Column('default_payment_terms_days', sa.Integer(), server_default=sa.text('30'), nullable=False),
        sa.Column('credit_limit', sa.Numeric(precision=14, scale=2), server_default=sa.text('0.00'), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default=sa.text("'USD'"), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tier_id'], ['customer_tiers.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customers_customer_code'), 'customers', ['customer_code'], unique=True)
    op.create_index(op.f('ix_customers_email'), 'customers', ['email'], unique=True)
    op.create_index(op.f('ix_customers_name'), 'customers', ['name'], unique=False)
    op.create_index(op.f('ix_customers_tier_id'), 'customers', ['tier_id'], unique=False)

    # 3. product_categories
    op.create_table(
        'product_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_categories_name'), 'product_categories', ['name'], unique=True)

    # 4. products
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('list_price', sa.Numeric(precision=14, scale=2), server_default=sa.text('0.00'), nullable=False),
        sa.Column('cost_price', sa.Numeric(precision=14, scale=2), server_default=sa.text('0.00'), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default=sa.text("'USD'"), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=20), server_default=sa.text("'EA'"), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['product_categories.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=True)
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)

    # 5. warehouses
    op.create_table(
        'warehouses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_warehouses_code'), 'warehouses', ['code'], unique=True)

    # 6. inventory
    op.create_table(
        'inventory',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('on_hand_qty', sa.Numeric(precision=14, scale=3), server_default=sa.text('0.000'), nullable=False),
        sa.Column('reserved_qty', sa.Numeric(precision=14, scale=3), server_default=sa.text('0.000'), nullable=False),
        sa.Column('reorder_level', sa.Numeric(precision=14, scale=3), server_default=sa.text('0.000'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('on_hand_qty >= 0', name='ck_inventory_on_hand_qty_nonnegative'),
        sa.CheckConstraint('reserved_qty >= 0', name='ck_inventory_reserved_qty_nonnegative'),
        sa.CheckConstraint('reorder_level >= 0', name='ck_inventory_reorder_level_nonnegative'),
        sa.CheckConstraint('reserved_qty <= on_hand_qty', name='ck_inventory_reserved_lte_on_hand'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('warehouse_id', 'product_id', name='uq_inventory_warehouse_product')
    )
    op.create_index(op.f('ix_inventory_product_id'), 'inventory', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_warehouse_id'), 'inventory', ['warehouse_id'], unique=False)


def downgrade() -> None:
    # 6. drop inventory
    op.drop_index(op.f('ix_inventory_warehouse_id'), table_name='inventory')
    op.drop_index(op.f('ix_inventory_product_id'), table_name='inventory')
    op.drop_table('inventory')

    # 5. drop warehouses
    op.drop_index(op.f('ix_warehouses_code'), table_name='warehouses')
    op.drop_table('warehouses')

    # 4. drop products
    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_index(op.f('ix_products_name'), table_name='products')
    op.drop_index(op.f('ix_products_sku'), table_name='products')
    op.drop_table('products')

    # 3. drop product_categories
    op.drop_index(op.f('ix_product_categories_name'), table_name='product_categories')
    op.drop_table('product_categories')

    # 2. drop customers
    op.drop_index(op.f('ix_customers_tier_id'), table_name='customers')
    op.drop_index(op.f('ix_customers_name'), table_name='customers')
    op.drop_index(op.f('ix_customers_email'), table_name='customers')
    op.drop_index(op.f('ix_customers_customer_code'), table_name='customers')
    op.drop_table('customers')

    # 1. drop customer_tiers
    op.drop_index(op.f('ix_customer_tiers_name'), table_name='customer_tiers')
    op.drop_table('customer_tiers')
