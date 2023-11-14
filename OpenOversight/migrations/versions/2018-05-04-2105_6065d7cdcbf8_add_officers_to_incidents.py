"""add officers to incidents

Revision ID: 6065d7cdcbf8
Revises: d86feb8fa5d1
Create Date: 2018-05-04 21:05:42.060165

"""
import sqlalchemy as sa
from alembic import op


revision = "6065d7cdcbf8"
down_revision = "d86feb8fa5d1"


def upgrade():
    op.create_table(
        "incident_officers",
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("officers_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["incident_id"], ["incidents.id"], "incident_officers_incident_id_fkey"
        ),
        sa.ForeignKeyConstraint(
            ["officers_id"], ["officers.id"], "incident_officers_officers_id_fkey"
        ),
        sa.PrimaryKeyConstraint("incident_id", "officers_id"),
    )
    op.add_column(
        "incident_license_plates",
        sa.Column("license_plate_id", sa.Integer(), nullable=False),
    )
    op.drop_constraint(
        "incident_license_plates_link_id_fkey",
        "incident_license_plates",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "incident_license_plates_license_plate_id_fkey",
        "incident_license_plates",
        "license_plates",
        ["license_plate_id"],
        ["id"],
    )
    op.drop_column("incident_license_plates", "link_id")


def downgrade():
    op.add_column(
        "incident_license_plates",
        sa.Column("link_id", sa.INTEGER(), autoincrement=False, nullable=False),
    )
    op.drop_constraint(
        "incident_license_plates_license_plate_id_fkey",
        "incident_license_plates",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "incident_license_plates_link_id_fkey",
        "incident_license_plates",
        "license_plates",
        ["link_id"],
        ["id"],
    )
    op.drop_column("incident_license_plates", "license_plate_id")
    op.drop_table("incident_officers")
