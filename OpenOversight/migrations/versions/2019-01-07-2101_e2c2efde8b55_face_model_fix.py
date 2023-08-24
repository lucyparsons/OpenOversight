"""Fix typo in Face model

Revision ID: e2c2efde8b55
Revises: 9e2827dae28c
Create Date: 2019-01-07 21:57:48.495757

"""
from alembic import op


revision = "e2c2efde8b55"
down_revision = "9e2827dae28c"


def upgrade():
    op.alter_column(
        "faces", "fk_face_original_image_id", new_column_name="original_image_id"
    )
    op.drop_constraint(
        "faces_fk_face_original_image_id_fkey", "faces", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_face_original_image_id",
        "faces",
        "raw_images",
        ["original_image_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="SET NULL",
        use_alter=True,
    )


def downgrade():
    op.drop_constraint("fk_face_original_image_id", "faces", type_="foreignkey")
    op.create_foreign_key(
        "faces_fk_face_original_image_id_fkey",
        "faces",
        "raw_images",
        ["fk_face_original_image_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="SET NULL",
    )
    op.alter_column(
        "faces", "original_image_id", new_column_name="fk_face_original_image_id"
    )
