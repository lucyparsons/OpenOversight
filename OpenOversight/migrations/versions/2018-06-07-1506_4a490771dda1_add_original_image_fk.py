"""add_original_image_fk

Revision ID: 4a490771dda1
Revises: bd0398fe4aab
Create Date: 2018-06-07 15:32:25.524117

"""
import sqlalchemy as sa
from alembic import op


revision = "4a490771dda1"
down_revision = "8ce7926aa132"


def upgrade():
    op.add_column(
        "faces", sa.Column("fk_face_original_image_id", sa.Integer(), nullable=True)
    )
    op.drop_constraint("faces_img_id_fkey", "faces", type_="foreignkey")
    op.create_foreign_key(
        "fk_face_image_id",
        "faces",
        "raw_images",
        ["img_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
        use_alter=True,
    )
    op.create_foreign_key(
        "raw_images_original_image_id_fkey",
        "faces",
        "raw_images",
        ["fk_face_original_image_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="SET NULL",
        use_alter=True,
    )


def downgrade():
    op.drop_constraint("raw_images_original_image_id_fkey", "faces", type_="foreignkey")
    op.drop_constraint("fk_face_image_id", "faces", type_="foreignkey")
    op.create_foreign_key(
        "faces_img_id_fkey", "faces", "raw_images", ["img_id"], ["id"]
    )
    op.drop_column("faces", "fk_face_original_image_id")
