"""empty message

Revision ID: 0ed957db0058
Revises: 7bb53dee8ac9
Create Date: 2018-08-11 20:31:02.265231

"""
import sqlalchemy as sa
from alembic import op


revision = "0ed957db0058"
down_revision = "2c27bfebe66e"


def upgrade():
    op.create_table(
        "descriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("text_contents", sa.Text(), nullable=True),
        sa.Column("creator_id", sa.Integer(), nullable=True),
        sa.Column("officer_id", sa.Integer(), nullable=True),
        sa.Column("date_created", sa.DateTime(), nullable=True),
        sa.Column("date_updated", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["users.id"],
            "descriptions_creator_id_fkey",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["officer_id"],
            ["officers.id"],
            "descriptions_officer_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("notes", "note", new_column_name="text_contents")


def downgrade():
    op.alter_column("notes", "text_contents", new_column_name="note")
    op.drop_table("descriptions")
