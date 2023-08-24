"""add incidents table

Revision ID: d86feb8fa5d1
Revises: e14a1aa4b58f
Create Date: 2018-05-04 21:03:12.925484

"""
import sqlalchemy as sa
from alembic import op


revision = "d86feb8fa5d1"
down_revision = "e14a1aa4b58f"


def upgrade():
    op.create_table(
        "license_plates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(length=8), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_license_plates_number"), "license_plates", ["number"], unique=False
    )
    op.create_index(
        op.f("ix_license_plates_state"), "license_plates", ["state"], unique=False
    )
    op.create_table(
        "links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=255), nullable=False),
        sa.Column("link_type", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_links_link_type"), "links", ["link_type"], unique=False)
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("street_name", sa.String(length=100), nullable=True),
        sa.Column("cross_street1", sa.String(length=100), nullable=True),
        sa.Column("cross_street2", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("zip_code", sa.String(length=5), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_locations_city"), "locations", ["city"], unique=False)
    op.create_index(op.f("ix_locations_state"), "locations", ["state"], unique=False)
    op.create_index(
        op.f("ix_locations_street_name"), "locations", ["street_name"], unique=False
    )
    op.create_index(
        op.f("ix_locations_zip_code"), "locations", ["zip_code"], unique=False
    )
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.Column("report_number", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["address_id"], ["locations.id"], "incidents_address_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_incidents_date"), "incidents", ["date"], unique=False)
    op.create_index(
        op.f("ix_incidents_report_number"), "incidents", ["report_number"], unique=False
    )
    op.create_table(
        "incident_license_plates",
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("link_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            "incident_license_plates_incident_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["link_id"],
            ["license_plates.id"],
            "incident_license_plates_license_plate_id_fkey",
        ),
        sa.PrimaryKeyConstraint("incident_id", "link_id"),
    )
    op.create_table(
        "incident_links",
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("link_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["incident_id"], ["incidents.id"], "incident_links_incident_id_fkey"
        ),
        sa.ForeignKeyConstraint(
            ["link_id"], ["links.id"], "incident_links_link_id_fkey"
        ),
        sa.PrimaryKeyConstraint("incident_id", "link_id"),
    )
    op.create_table(
        "officer_incidents",
        sa.Column("officer_id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["incident_id"], ["incidents.id"], "officer_incidents_officer_id_fkey"
        ),
        sa.ForeignKeyConstraint(
            ["officer_id"], ["officers.id"], "officer_incidents_incident_id_fkey"
        ),
        sa.PrimaryKeyConstraint("officer_id", "incident_id"),
    )
    op.create_table(
        "officer_links",
        sa.Column("officer_id", sa.Integer(), nullable=False),
        sa.Column("link_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["link_id"], ["links.id"], "officer_links_link_id_fkey"
        ),
        sa.ForeignKeyConstraint(
            ["officer_id"], ["officers.id"], "officer_links_officer_id_fkey"
        ),
        sa.PrimaryKeyConstraint("officer_id", "link_id"),
    )


def downgrade():
    op.drop_table("officer_links")
    op.drop_table("officer_incidents")
    op.drop_table("incident_links")
    op.drop_table("incident_license_plates")
    op.drop_index(op.f("ix_incidents_report_number"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_date"), table_name="incidents")
    op.drop_table("incidents")
    op.drop_index(op.f("ix_locations_zip_code"), table_name="locations")
    op.drop_index(op.f("ix_locations_street_name"), table_name="locations")
    op.drop_index(op.f("ix_locations_state"), table_name="locations")
    op.drop_index(op.f("ix_locations_city"), table_name="locations")
    op.drop_table("locations")
    op.drop_index(op.f("ix_links_link_type"), table_name="links")
    op.drop_table("links")
    op.drop_index(op.f("ix_license_plates_state"), table_name="license_plates")
    op.drop_index(op.f("ix_license_plates_number"), table_name="license_plates")
    op.drop_table("license_plates")
