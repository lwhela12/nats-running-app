from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("sex", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("age BETWEEN 13 AND 95", name="ck_users_age_range"),
        sa.CheckConstraint("sex IN ('male','female','other')", name="ck_users_sex_values"),
    )

    op.create_table(
        "goals",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("distance_m", sa.Integer(), nullable=False),
        sa.Column("target_time_sec", sa.Integer(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "capability_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("comfortable_distance_m", sa.Integer(), nullable=False),
        sa.Column("comfortable_time_sec", sa.Integer(), nullable=False),
        sa.Column("projection", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goal_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("goals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('active','archived','superseded')", name="ck_plans_status_values"),
    )

    op.create_table(
        "workouts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("plan_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wdate", sa.Date(), nullable=False),
        sa.Column("wtype", sa.Text(), nullable=False),
        sa.Column("target_distance_m", sa.Integer(), nullable=True),
        sa.Column("target_duration_sec", sa.Integer(), nullable=True),
        sa.Column("target_zone", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_key", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint("wtype IN ('easy','long','tempo','interval','rest','cross')", name="ck_workouts_wtype_values"),
    )
    op.create_index("ix_workouts_plan_date", "workouts", ["plan_id", "wdate"])

    op.create_table(
        "session_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workout_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actual_distance_m", sa.Integer(), nullable=True),
        sa.Column("actual_time_sec", sa.Integer(), nullable=True),
        sa.Column("rpe", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("rpe IS NULL OR (rpe BETWEEN 1 AND 10)", name="ck_session_logs_rpe_range"),
    )

    op.create_table(
        "adaptation_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("plan_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("rule", sa.Text(), nullable=False),
        sa.Column("before_state", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("after_state", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("adaptation_events")
    op.drop_table("session_logs")
    op.drop_index("ix_workouts_plan_date", table_name="workouts")
    op.drop_table("workouts")
    op.drop_table("plans")
    op.drop_table("capability_snapshots")
    op.drop_table("goals")
    op.drop_table("users")

