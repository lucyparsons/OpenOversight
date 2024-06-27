"""standardize datetime field names

Revision ID: 07ace5f956ca
Revises: eb0266dc8588
Create Date: 2023-07-18 20:27:19.891054

"""

from alembic import op


revision = "07ace5f956ca"
down_revision = "eb0266dc8588"


def upgrade():
    with op.batch_alter_table("descriptions", schema=None) as batch_op:
        batch_op.alter_column(
            "date_created", nullable=True, new_column_name="created_at"
        )
        batch_op.alter_column(
            "date_updated", nullable=True, new_column_name="updated_at"
        )

    with op.batch_alter_table("notes", schema=None) as batch_op:
        batch_op.alter_column(
            "date_created", nullable=True, new_column_name="created_at"
        )
        batch_op.alter_column(
            "date_updated", nullable=True, new_column_name="updated_at"
        )

    with op.batch_alter_table("raw_images", schema=None) as batch_op:
        batch_op.drop_index("ix_raw_images_date_image_inserted")
        batch_op.drop_index("ix_raw_images_date_image_taken")
        batch_op.alter_column(
            "date_image_inserted", nullable=True, new_column_name="created_at"
        )
        batch_op.alter_column(
            "date_image_taken", nullable=True, new_column_name="taken_at"
        )
        batch_op.create_index(
            batch_op.f("ix_raw_images_created_at"), ["created_at"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_raw_images_taken_at"), ["taken_at"], unique=False
        )


def downgrade():
    with op.batch_alter_table("raw_images", schema=None) as batch_op:
        batch_op.drop_index("ix_raw_images_created_at")
        batch_op.drop_index("ix_raw_images_taken_at")
        batch_op.alter_column(
            "created_at", nullable=True, new_column_name="date_image_inserted"
        )
        batch_op.alter_column(
            "taken_at", nullable=True, new_column_name="date_image_taken"
        )
        batch_op.create_index(
            "ix_raw_images_date_image_taken", ["date_image_taken"], unique=False
        )
        batch_op.create_index(
            "ix_raw_images_date_image_inserted", ["date_image_inserted"], unique=False
        )

    with op.batch_alter_table("notes", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at", nullable=True, new_column_name="date_created"
        )
        batch_op.alter_column(
            "updated_at", nullable=True, new_column_name="date_updated"
        )

    with op.batch_alter_table("descriptions", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at", nullable=True, new_column_name="date_created"
        )
        batch_op.alter_column(
            "updated_at", nullable=True, new_column_name="date_updated"
        )
