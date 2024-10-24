"""add created_by and created_at columns

Revision ID: b38c133bed3c
Revises: 18f43ac4622f
Create Date: 2023-08-01 19:05:34.745077

"""

import sqlalchemy as sa
from alembic import op


revision = "b38c133bed3c"
down_revision = "18f43ac4622f"


def upgrade():
    with op.batch_alter_table("assignments", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "assignments_created_by_fkey",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("departments", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "departments_created_by_fkey",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("descriptions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "descriptions_created_by_fkey",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        """
            UPDATE descriptions
            SET created_by = creator_id
            WHERE created_by IS NULL
        """
    )

    with op.batch_alter_table("descriptions", schema=None) as batch_op:
        batch_op.drop_column("creator_id")

    with op.batch_alter_table("faces", schema=None) as batch_op:
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        batch_op.create_foreign_key(
            "faces_created_by_fkey", "users", ["created_by"], ["id"]
        )

    op.execute(
        """
            UPDATE faces
            SET created_by = user_id
            WHERE created_by IS NULL
        """
    )

    with op.batch_alter_table("faces", schema=None) as batch_op:
        batch_op.drop_column("user_id")

    with op.batch_alter_table("incident_license_plates", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )

    with op.batch_alter_table("incident_links", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )

    with op.batch_alter_table("incident_officers", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )

    with op.batch_alter_table("incidents", schema=None) as batch_op:
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("last_updated_by", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "last_updated_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )
        batch_op.create_foreign_key(
            "incidents_last_updated_by_fkey",
            "users",
            ["last_updated_by"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "incidents_created_by_fkey",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        """
            UPDATE incidents
            SET created_by = creator_id
            WHERE created_by IS NULL
        """
    )

    with op.batch_alter_table("incidents", schema=None) as batch_op:
        batch_op.drop_column("creator_id")
        batch_op.drop_column("last_updated_id")

    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "jobs_created_by_fkey", "users", ["created_by"], ["id"], ondelete="SET NULL"
        )

    with op.batch_alter_table("license_plates", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "license_plates_created_by_fkey",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("links", schema=None) as batch_op:
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        batch_op.create_foreign_key(
            "links_created_by_fkey",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        """
            UPDATE links
            SET created_by = creator_id
            WHERE created_by IS NULL
        """
    )

    with op.batch_alter_table("links", schema=None) as batch_op:
        batch_op.drop_column("creator_id")

    with op.batch_alter_table("locations", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "locations_created_by_fkey",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("notes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "notes_created_by_fkey",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        """
            UPDATE notes
            SET created_by = creator_id
            WHERE created_by IS NULL
        """
    )

    with op.batch_alter_table("notes", schema=None) as batch_op:
        batch_op.drop_column("creator_id")

    with op.batch_alter_table("officer_incidents", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )

    with op.batch_alter_table("officer_links", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )

    with op.batch_alter_table("officers", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "officers_created_by_fkey",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("raw_images", schema=None) as batch_op:
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "raw_images_created_by_fkey",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        """
            UPDATE raw_images
            SET created_by = user_id
            WHERE created_by IS NULL
        """
    )

    with op.batch_alter_table("raw_images", schema=None) as batch_op:
        batch_op.drop_column("user_id")

    with op.batch_alter_table("salaries", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "salaries_created_by_fkey",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("unit_types", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "unit_types_created_by_fkey",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("created_at")

    with op.batch_alter_table("unit_types", schema=None) as batch_op:
        batch_op.drop_constraint("unit_types_created_by_fkey", type_="foreignkey")
        batch_op.drop_column("created_by")
        batch_op.drop_column("created_at")

    with op.batch_alter_table("salaries", schema=None) as batch_op:
        batch_op.drop_constraint("salaries_created_by_fkey", type_="foreignkey")
        batch_op.drop_column("created_by")
        batch_op.drop_column("created_at")

    with op.batch_alter_table("raw_images", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=True)
        )
        batch_op.drop_constraint("raw_images_created_by_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "raw_images_user_id_fkey", "users", ["user_id"], ["id"]
        )

    op.execute(
        """
            UPDATE raw_images
            SET user_id = created_by
            WHERE user_id IS NULL
        """
    )

    with op.batch_alter_table("raw_images", schema=None) as batch_op:
        batch_op.drop_column("created_by")

    with op.batch_alter_table("officers", schema=None) as batch_op:
        batch_op.drop_constraint("officers_created_by_fkey", type_="foreignkey")
        batch_op.drop_column("created_by")
        batch_op.drop_column("created_at")

    with op.batch_alter_table("officer_links", schema=None) as batch_op:
        batch_op.drop_column("created_at")

    with op.batch_alter_table("officer_incidents", schema=None) as batch_op:
        batch_op.drop_column("created_at")

    with op.batch_alter_table("notes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("creator_id", sa.INTEGER(), autoincrement=False, nullable=True)
        )
        batch_op.drop_constraint("notes_created_by_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "notes_creator_id_fkey",
            "users",
            ["creator_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        """
            UPDATE notes
            SET creator_id = created_by
            WHERE creator_id IS NULL
        """
    )

    with op.batch_alter_table("notes", schema=None) as batch_op:
        batch_op.drop_column("created_by")

    with op.batch_alter_table("locations", schema=None) as batch_op:
        batch_op.drop_constraint("locations_created_by_fkey", type_="foreignkey")
        batch_op.drop_column("created_by")
        batch_op.drop_column("created_at")

    with op.batch_alter_table("links", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("creator_id", sa.INTEGER(), autoincrement=False, nullable=True)
        )
        batch_op.drop_constraint("links_created_by_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "links_creator_id_fkey",
            "users",
            ["creator_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        """
            UPDATE links
            SET creator_id = created_by
            WHERE creator_id IS NULL
        """
    )

    with op.batch_alter_table("links", schema=None) as batch_op:
        batch_op.drop_column("created_at")
        batch_op.drop_column("created_by")

    with op.batch_alter_table("license_plates", schema=None) as batch_op:
        batch_op.drop_constraint("license_plates_created_by_fkey", type_="foreignkey")
        batch_op.drop_column("created_by")
        batch_op.drop_column("created_at")

    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.drop_constraint("jobs_created_by_fkey", type_="foreignkey")
        batch_op.drop_column("created_by")
        batch_op.drop_column("created_at")

    with op.batch_alter_table("incidents", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "last_updated_id", sa.INTEGER(), autoincrement=False, nullable=True
            )
        )
        batch_op.add_column(
            sa.Column("creator_id", sa.INTEGER(), autoincrement=False, nullable=True)
        )
        batch_op.drop_constraint("incidents_created_by_fkey", type_="foreignkey")
        batch_op.drop_constraint("incidents_last_updated_by_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "incidents_creator_id_fkey", "users", ["creator_id"], ["id"]
        )
        batch_op.create_foreign_key(
            "incidents_last_updated_id_fkey", "users", ["last_updated_id"], ["id"]
        )

    op.execute(
        """
            UPDATE incidents
            SET creator_id = created_by
            WHERE creator_id IS NULL
        """
    )

    with op.batch_alter_table("incidents", schema=None) as batch_op:
        batch_op.drop_column("created_at")
        batch_op.drop_column("last_updated_by")
        batch_op.drop_column("last_updated_at")
        batch_op.drop_column("created_by")

    with op.batch_alter_table("incident_officers", schema=None) as batch_op:
        batch_op.drop_column("created_at")

    with op.batch_alter_table("incident_links", schema=None) as batch_op:
        batch_op.drop_column("created_at")

    with op.batch_alter_table("incident_license_plates", schema=None) as batch_op:
        batch_op.drop_column("created_at")

    with op.batch_alter_table("faces", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=True)
        )
        batch_op.drop_constraint("faces_created_by_fkey", type_="foreignkey")
        batch_op.create_foreign_key("faces_user_id_fkey", "users", ["user_id"], ["id"])

    op.execute(
        """
                UPDATE faces
                SET user_id = created_by
                WHERE user_id IS NULL
            """
    )

    with op.batch_alter_table("faces", schema=None) as batch_op:
        batch_op.drop_column("created_at")
        batch_op.drop_column("created_by")

    with op.batch_alter_table("descriptions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("creator_id", sa.INTEGER(), autoincrement=False, nullable=True)
        )
        batch_op.drop_constraint("descriptions_created_by_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "descriptions_creator_id_fkey",
            "users",
            ["creator_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        """
                UPDATE descriptions
                SET creator_id = created_by
                WHERE creator_id IS NULL
            """
    )

    with op.batch_alter_table("descriptions", schema=None) as batch_op:
        batch_op.drop_column("created_by")

    with op.batch_alter_table("departments", schema=None) as batch_op:
        batch_op.drop_constraint("departments_created_by_fkey", type_="foreignkey")
        batch_op.drop_column("created_by")
        batch_op.drop_column("created_at")

    with op.batch_alter_table("assignments", schema=None) as batch_op:
        batch_op.drop_constraint("assignments_created_by_fkey", type_="foreignkey")
        batch_op.drop_column("created_by")
        batch_op.drop_column("created_at")
