"""create approval transaction and upsell recommendation tables

Revision ID: 006_approval_upsell
Revises: 005_quote_core
Create Date: 2026-09-05 18:47:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_approval_upsell'
down_revision: Union[str, None] = '005_quote_core'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. approval_policies extension
    op.add_column('approval_policies', sa.Column('blended_risk_above', sa.Numeric(precision=6, scale=2), nullable=True))
    op.create_check_constraint(
        'ck_approval_policies_blended_risk_range',
        'approval_policies',
        'blended_risk_above IS NULL OR (blended_risk_above >= 0 AND blended_risk_above <= 100)'
    )

    # 2. quote_approval_steps
    op.create_table(
        'quote_approval_steps',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=False),
        sa.Column('approval_round', sa.Integer(), server_default='1', nullable=False),
        sa.Column('sequence', sa.Integer(), server_default='1', nullable=False),
        sa.Column('approval_role', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('decided_by_user_id', sa.Integer(), nullable=True),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['decided_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quotation_id', 'approval_round', 'sequence', name='uq_quote_approval_round_seq')
    )
    op.create_index(op.f('ix_quote_approval_steps_quotation_id'), 'quote_approval_steps', ['quotation_id'], unique=False)
    op.create_index(op.f('ix_quote_approval_steps_decided_by_user_id'), 'quote_approval_steps', ['decided_by_user_id'], unique=False)
    op.create_index(op.f('ix_quote_approval_steps_status'), 'quote_approval_steps', ['status'], unique=False)

    # 3. quote_approval_triggers
    op.create_table(
        'quote_approval_triggers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('approval_step_id', sa.Integer(), nullable=False),
        sa.Column('approval_policy_id', sa.Integer(), nullable=True),
        sa.Column('trigger_code', sa.String(length=100), nullable=False),
        sa.Column('actual_value', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('threshold_value', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['approval_policy_id'], ['approval_policies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approval_step_id'], ['quote_approval_steps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quote_approval_triggers_approval_step_id'), 'quote_approval_triggers', ['approval_step_id'], unique=False)
    op.create_index(op.f('ix_quote_approval_triggers_approval_policy_id'), 'quote_approval_triggers', ['approval_policy_id'], unique=False)

    # 4. product_recommendation_rules
    op.create_table(
        'product_recommendation_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_product_id', sa.Integer(), nullable=False),
        sa.Column('suggested_product_id', sa.Integer(), nullable=False),
        sa.Column('affinity_score', sa.Numeric(precision=5, scale=2), server_default='1.00', nullable=False),
        sa.Column('recommended_qty', sa.Numeric(precision=14, scale=3), server_default='1.000', nullable=False),
        sa.Column('is_promoted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('promotion_label', sa.String(length=255), nullable=True),
        sa.Column('min_margin_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='100', nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('source_product_id != suggested_product_id', name='ck_product_recommendation_rules_not_self'),
        sa.CheckConstraint('recommended_qty > 0', name='ck_product_recommendation_rules_qty_gt_zero'),
        sa.CheckConstraint('affinity_score >= 0', name='ck_product_recommendation_rules_affinity_ge_zero'),
        sa.ForeignKeyConstraint(['source_product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['suggested_product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_recommendation_rules_source_product_id'), 'product_recommendation_rules', ['source_product_id'], unique=False)
    op.create_index(op.f('ix_product_recommendation_rules_suggested_product_id'), 'product_recommendation_rules', ['suggested_product_id'], unique=False)

    # 5. quotation_lines extension
    op.add_column('quotation_lines', sa.Column('recommendation_rule_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_quotation_lines_recommendation_rule_id', 'quotation_lines', 'product_recommendation_rules', ['recommendation_rule_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_quotation_lines_recommendation_rule_id'), 'quotation_lines', ['recommendation_rule_id'], unique=False)

    # 6. quote_recommendation_dismissals
    op.create_table(
        'quote_recommendation_dismissals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('quotation_id', sa.Integer(), nullable=False),
        sa.Column('recommendation_rule_id', sa.Integer(), nullable=False),
        sa.Column('dismissed_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dismissed_by_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recommendation_rule_id'], ['product_recommendation_rules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quotation_id', 'recommendation_rule_id', name='uq_quote_rule_dismissal')
    )
    op.create_index(op.f('ix_quote_recommendation_dismissals_quotation_id'), 'quote_recommendation_dismissals', ['quotation_id'], unique=False)
    op.create_index(op.f('ix_quote_recommendation_dismissals_recommendation_rule_id'), 'quote_recommendation_dismissals', ['recommendation_rule_id'], unique=False)
    op.create_index(op.f('ix_quote_recommendation_dismissals_dismissed_by_user_id'), 'quote_recommendation_dismissals', ['dismissed_by_user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_quote_recommendation_dismissals_dismissed_by_user_id'), table_name='quote_recommendation_dismissals')
    op.drop_index(op.f('ix_quote_recommendation_dismissals_recommendation_rule_id'), table_name='quote_recommendation_dismissals')
    op.drop_index(op.f('ix_quote_recommendation_dismissals_quotation_id'), table_name='quote_recommendation_dismissals')
    op.drop_table('quote_recommendation_dismissals')

    op.drop_index(op.f('ix_quotation_lines_recommendation_rule_id'), table_name='quotation_lines')
    op.drop_constraint('fk_quotation_lines_recommendation_rule_id', 'quotation_lines', type_='foreignkey')
    op.drop_column('quotation_lines', 'recommendation_rule_id')

    op.drop_index(op.f('ix_product_recommendation_rules_suggested_product_id'), table_name='product_recommendation_rules')
    op.drop_index(op.f('ix_product_recommendation_rules_source_product_id'), table_name='product_recommendation_rules')
    op.drop_table('product_recommendation_rules')

    op.drop_index(op.f('ix_quote_approval_triggers_approval_policy_id'), table_name='quote_approval_triggers')
    op.drop_index(op.f('ix_quote_approval_triggers_approval_step_id'), table_name='quote_approval_triggers')
    op.drop_table('quote_approval_triggers')

    op.drop_index(op.f('ix_quote_approval_steps_status'), table_name='quote_approval_steps')
    op.drop_index(op.f('ix_quote_approval_steps_decided_by_user_id'), table_name='quote_approval_steps')
    op.drop_index(op.f('ix_quote_approval_steps_quotation_id'), table_name='quote_approval_steps')
    op.drop_table('quote_approval_steps')

    op.drop_constraint('ck_approval_policies_blended_risk_range', 'approval_policies', type_='check')
    op.drop_column('approval_policies', 'blended_risk_above')
