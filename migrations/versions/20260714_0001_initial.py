"""initial schema

Revision ID: 20260714_0001
Revises:
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260714_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bill_cache",
        sa.Column("congress", sa.Integer(), nullable=False),
        sa.Column("bill_type", sa.String(length=20), nullable=False),
        sa.Column("bill_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=1000), nullable=False),
        sa.Column("sponsor", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("policy_area", sa.String(length=255), nullable=False),
        sa.Column("subjects_json", sa.JSON(), nullable=False),
        sa.Column("committees_json", sa.JSON(), nullable=False),
        sa.Column("actions_json", sa.JSON(), nullable=False),
        sa.Column("text_version_count", sa.Integer(), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("congress", "bill_type", "bill_number"),
    )

    op.create_table(
        "beneficiary_group",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
    )
    op.create_index(op.f("ix_beneficiary_group_name"), "beneficiary_group", ["name"], unique=True)

    op.create_table(
        "beneficiary_rule",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("match_field", sa.String(length=50), nullable=False),
        sa.Column("match_value", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["beneficiary_group.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_beneficiary_rule_group_id"), "beneficiary_rule", ["group_id"], unique=False)
    op.create_index(op.f("ix_beneficiary_rule_match_value"), "beneficiary_rule", ["match_value"], unique=False)

    op.create_table(
        "lobbying_filing",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("registrant", sa.String(length=255), nullable=False),
        sa.Column("client", sa.String(length=255), nullable=False),
        sa.Column("specific_issues_text", sa.Text(), nullable=False),
        sa.Column("filing_period", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
    )
    op.create_index(op.f("ix_lobbying_filing_external_id"), "lobbying_filing", ["external_id"], unique=True)

    op.create_table(
        "named_entity",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
    )
    op.create_index(op.f("ix_named_entity_name"), "named_entity", ["name"], unique=False)

    op.create_table(
        "bill_beneficiary",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("congress", sa.Integer(), nullable=False),
        sa.Column("bill_type", sa.String(length=20), nullable=False),
        sa.Column("bill_number", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["beneficiary_group.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["beneficiary_rule.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["congress", "bill_type", "bill_number"],
            ["bill_cache.congress", "bill_cache.bill_type", "bill_cache.bill_number"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(op.f("ix_bill_beneficiary_congress"), "bill_beneficiary", ["congress"], unique=False)
    op.create_index(op.f("ix_bill_beneficiary_bill_type"), "bill_beneficiary", ["bill_type"], unique=False)
    op.create_index(op.f("ix_bill_beneficiary_bill_number"), "bill_beneficiary", ["bill_number"], unique=False)

    op.create_table(
        "bill_lobbying_match",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("congress", sa.Integer(), nullable=False),
        sa.Column("bill_type", sa.String(length=20), nullable=False),
        sa.Column("bill_number", sa.Integer(), nullable=False),
        sa.Column("filing_id", sa.Integer(), nullable=False),
        sa.Column("match_method", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["filing_id"], ["lobbying_filing.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["congress", "bill_type", "bill_number"],
            ["bill_cache.congress", "bill_cache.bill_type", "bill_cache.bill_number"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(op.f("ix_bill_lobbying_match_congress"), "bill_lobbying_match", ["congress"], unique=False)
    op.create_index(op.f("ix_bill_lobbying_match_bill_type"), "bill_lobbying_match", ["bill_type"], unique=False)
    op.create_index(op.f("ix_bill_lobbying_match_bill_number"), "bill_lobbying_match", ["bill_number"], unique=False)
    op.create_index(op.f("ix_bill_lobbying_match_filing_id"), "bill_lobbying_match", ["filing_id"], unique=False)

    op.create_table(
        "bill_named_entity",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("congress", sa.Integer(), nullable=False),
        sa.Column("bill_type", sa.String(length=20), nullable=False),
        sa.Column("bill_number", sa.Integer(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("reviewed_by", sa.String(length=255), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["entity_id"], ["named_entity.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["congress", "bill_type", "bill_number"],
            ["bill_cache.congress", "bill_cache.bill_type", "bill_cache.bill_number"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(op.f("ix_bill_named_entity_congress"), "bill_named_entity", ["congress"], unique=False)
    op.create_index(op.f("ix_bill_named_entity_bill_type"), "bill_named_entity", ["bill_type"], unique=False)
    op.create_index(op.f("ix_bill_named_entity_bill_number"), "bill_named_entity", ["bill_number"], unique=False)
    op.create_index(op.f("ix_bill_named_entity_entity_id"), "bill_named_entity", ["entity_id"], unique=False)
    op.create_index(op.f("ix_bill_named_entity_status"), "bill_named_entity", ["status"], unique=False)

    op.create_table(
        "concentration_score",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("congress", sa.Integer(), nullable=False),
        sa.Column("bill_type", sa.String(length=20), nullable=False),
        sa.Column("bill_number", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("label", sa.String(length=20), nullable=False),
        sa.Column("computed_at", sa.DateTime(), nullable=False),
        sa.Column("entity_count", sa.Integer(), nullable=False),
        sa.Column("breadth_ratio", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["congress", "bill_type", "bill_number"],
            ["bill_cache.congress", "bill_cache.bill_type", "bill_cache.bill_number"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(op.f("ix_concentration_score_congress"), "concentration_score", ["congress"], unique=False)
    op.create_index(op.f("ix_concentration_score_bill_type"), "concentration_score", ["bill_type"], unique=False)
    op.create_index(op.f("ix_concentration_score_bill_number"), "concentration_score", ["bill_number"], unique=False)

    op.create_table(
        "usafacts_stat",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_usafacts_stat_topic"), "usafacts_stat", ["topic"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_usafacts_stat_topic"), table_name="usafacts_stat")
    op.drop_table("usafacts_stat")

    op.drop_index(op.f("ix_concentration_score_bill_number"), table_name="concentration_score")
    op.drop_index(op.f("ix_concentration_score_bill_type"), table_name="concentration_score")
    op.drop_index(op.f("ix_concentration_score_congress"), table_name="concentration_score")
    op.drop_table("concentration_score")

    op.drop_index(op.f("ix_bill_named_entity_status"), table_name="bill_named_entity")
    op.drop_index(op.f("ix_bill_named_entity_entity_id"), table_name="bill_named_entity")
    op.drop_index(op.f("ix_bill_named_entity_bill_number"), table_name="bill_named_entity")
    op.drop_index(op.f("ix_bill_named_entity_bill_type"), table_name="bill_named_entity")
    op.drop_index(op.f("ix_bill_named_entity_congress"), table_name="bill_named_entity")
    op.drop_table("bill_named_entity")

    op.drop_index(op.f("ix_bill_lobbying_match_filing_id"), table_name="bill_lobbying_match")
    op.drop_index(op.f("ix_bill_lobbying_match_bill_number"), table_name="bill_lobbying_match")
    op.drop_index(op.f("ix_bill_lobbying_match_bill_type"), table_name="bill_lobbying_match")
    op.drop_index(op.f("ix_bill_lobbying_match_congress"), table_name="bill_lobbying_match")
    op.drop_table("bill_lobbying_match")

    op.drop_index(op.f("ix_bill_beneficiary_bill_number"), table_name="bill_beneficiary")
    op.drop_index(op.f("ix_bill_beneficiary_bill_type"), table_name="bill_beneficiary")
    op.drop_index(op.f("ix_bill_beneficiary_congress"), table_name="bill_beneficiary")
    op.drop_table("bill_beneficiary")

    op.drop_index(op.f("ix_named_entity_name"), table_name="named_entity")
    op.drop_table("named_entity")

    op.drop_index(op.f("ix_lobbying_filing_external_id"), table_name="lobbying_filing")
    op.drop_table("lobbying_filing")

    op.drop_index(op.f("ix_beneficiary_rule_match_value"), table_name="beneficiary_rule")
    op.drop_index(op.f("ix_beneficiary_rule_group_id"), table_name="beneficiary_rule")
    op.drop_table("beneficiary_rule")

    op.drop_index(op.f("ix_beneficiary_group_name"), table_name="beneficiary_group")
    op.drop_table("beneficiary_group")

    op.drop_table("bill_cache")
