"""constrain officer gender options

Revision ID: cd39b33b5360
Revises: 86eb228e4bc0
Create Date: 2020-07-13 02:45:07.533549

"""
import sqlalchemy as sa
from alembic import op


revision = "cd39b33b5360"
down_revision = "86eb228e4bc0"


def get_update_statement(normalized, options):
    template = """
    UPDATE officers
    SET gender = '{normalized}'
    WHERE LOWER(gender) in ({options});
    """
    options = ", ".join(["'" + o + "'" for o in options])
    return template.format(normalized=normalized, options=options)


def upgrade():
    conn = op.get_bind()

    genders = {
        "M": ("male", "m", "man"),
        "F": ("female", "f", "woman"),
        "Other": ("nonbinary", "other"),
    }

    update_statement = ""

    for normalized, options in genders.items():
        update_statement += get_update_statement(normalized, options)

    conn.execute(update_statement)

    null_query = """
UPDATE officers
SET gender = NULL
WHERE gender not in ('M', 'F', 'Other');
"""
    conn.execute(null_query)

    op.alter_column(
        "officers",
        "gender",
        existing_type=sa.VARCHAR(length=120),
        type_=sa.VARCHAR(length=5),
        existing_nullable=True,
    )

    op.create_check_constraint(
        "gender_options", "officers", "gender in ('M', 'F', 'Other')"
    )


def downgrade():
    op.drop_constraint("gender_options", "officers", type_="check")

    op.alter_column(
        "officers",
        "gender",
        existing_type=sa.VARCHAR(length=5),
        type_=sa.VARCHAR(length=120),
        existing_nullable=True,
    )
