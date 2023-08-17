"""Add create and last_update columns

Revision ID: a35aa1a114fa
Revises: b38c133bed3c
Create Date: 2023-08-21 03:00:57.468190

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "a35aa1a114fa"
down_revision = "b38c133bed3c"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("assignments", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_assignments_last_updated_by_users",
            "users",
            ["last_updated_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("departments", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_departments_last_updated_by_users",
            "users",
            ["last_updated_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("descriptions", schema=None) as batch_op:
        batch_op.alter_column("updated_at", new_column_name="last_updated_at")
        # batch_op.add_column(sa.Column('last_updated_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        # batch_op.create_foreign_key(None, 'users', ['last_updated_by'], ['id'], ondelete='SET NULL')
        # batch_op.drop_column('updated_at')

    with op.batch_alter_table("faces", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        batch_op.drop_constraint("faces_created_by_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_faces_created_by_users",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_faces_last_updated_by_users",
            "users",
            ["last_updated_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_jobs_last_updated_by_users",
            "users",
            ["last_updated_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("license_plates", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_licence_plates_last_updated_by_users",
            "users",
            ["last_updated_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("links", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_links_last_updated_by_users",
            "users",
            ["last_updated_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("locations", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_locations_last_updated_by_users",
            "users",
            ["last_updated_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("notes", schema=None) as batch_op:
        batch_op.alter_column("updated_at", new_column_name="last_updated_at")
        # batch_op.add_column(sa.Column('last_updated_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        # batch_op.create_foreign_key(None, 'users', ['last_updated_by'], ['id'], ondelete='SET NULL')
        # batch_op.drop_column('updated_at')

    with op.batch_alter_table("officers", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_officers_last_updated_by_users",
            "users",
            ["last_updated_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("raw_images", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            existing_server_default=sa.text("now()"),
        )
        batch_op.drop_index("ix_raw_images_created_at")
        batch_op.create_foreign_key(
            "fk_raw_images_last_updated_by_users",
            "users",
            ["last_updated_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("salaries", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_salaries_last_updated_by_users",
            "users",
            ["last_updated_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("unit_types", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_unit_types_last_updated_by_users",
            "users",
            ["last_updated_by"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    with op.batch_alter_table("unit_types", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_unit_types_last_updated_by_users", type_="foreignkey"
        )
        batch_op.drop_column("last_updated_by")
        batch_op.drop_column("last_updated_at")

    with op.batch_alter_table("salaries", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_salaries_last_updated_by_users", type_="foreignkey"
        )
        batch_op.drop_column("last_updated_by")
        batch_op.drop_column("last_updated_at")

    with op.batch_alter_table("raw_images", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_raw_images_last_updated_by_users", type_="foreignkey"
        )
        batch_op.create_index("ix_raw_images_created_at", ["created_at"], unique=False)
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(timezone=True),
            nullable=True,
            existing_server_default=sa.text("now()"),
        )
        batch_op.drop_column("last_updated_by")
        batch_op.drop_column("last_updated_at")

    with op.batch_alter_table("officers", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_officers_last_updated_by_users", type_="foreignkey"
        )
        batch_op.drop_column("last_updated_by")
        batch_op.drop_column("last_updated_at")

    with op.batch_alter_table("notes", schema=None) as batch_op:
        batch_op.alter_column("last_updated_at", new_column_name="updated_at")
        # batch_op.add_column(sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
        # batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column("last_updated_by")
        # batch_op.drop_column('last_updated_at')

    with op.batch_alter_table("locations", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_locations_last_updated_by_users", type_="foreignkey"
        )
        batch_op.drop_column("last_updated_by")
        batch_op.drop_column("last_updated_at")

    with op.batch_alter_table("links", schema=None) as batch_op:
        batch_op.drop_constraint("fk_links_last_updated_by_users", type_="foreignkey")
        batch_op.drop_column("last_updated_by")
        batch_op.drop_column("last_updated_at")

    with op.batch_alter_table("license_plates", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_licence_plates_last_updated_by_users", type_="foreignkey"
        )
        batch_op.drop_column("last_updated_by")
        batch_op.drop_column("last_updated_at")

    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.drop_constraint("fk_jobs_last_updated_by_users", type_="foreignkey")
        batch_op.drop_column("last_updated_by")
        batch_op.drop_column("last_updated_at")

    with op.batch_alter_table("faces", schema=None) as batch_op:
        batch_op.drop_constraint("fk_faces_last_updated_by_users", type_="foreignkey")
        batch_op.drop_constraint("fk_faces_created_by_users", type_="foreignkey")
        batch_op.create_foreign_key(
            "faces_created_by_fkey", "users", ["created_by"], ["id"]
        )
        batch_op.drop_column("last_updated_by")
        batch_op.drop_column("last_updated_at")

    with op.batch_alter_table("descriptions", schema=None) as batch_op:
        batch_op.alter_column("last_updated_at", new_column_name="updated_at")
        # batch_op.add_column(sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
        # batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column("last_updated_by")
        # batch_op.drop_column('last_updated_at')

    with op.batch_alter_table("departments", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_departments_last_updated_by_users", type_="foreignkey"
        )
        batch_op.drop_column("last_updated_by")
        batch_op.drop_column("last_updated_at")

    with op.batch_alter_table("assignments", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_assignments_last_updated_by_users", type_="foreignkey"
        )
        batch_op.drop_column("last_updated_by")
        batch_op.drop_column("last_updated_at")
