"""change_faces_to_thumbnails

Revision ID: 59e9993c169c
Revises: bd0398fe4aab
Create Date: 2018-06-04 19:04:23.524079

"""
import os
import sys

from flask import current_app


# Add our Flask app to the search paths for modules
sys.path.insert(0, os.path.dirname(current_app.root_path))

from OpenOversight.app.models.database import Face, db  # noqa: E402
from OpenOversight.app.utils.cloud import crop_image  # noqa: E402


revision = "59e9993c169c"
down_revision = "4a490771dda1"


def upgrade():
    try:
        for face in Face.query.all():
            if face.face_position_x and face.image.filepath.split("/")[0] != "static":
                left = face.face_position_x
                upper = face.face_position_y
                right = left + face.face_width
                lower = upper + face.face_height

                cropped_image = crop_image(face.image, (left, upper, right, lower))

                new_face = Face(
                    officer_id=face.officer_id,
                    img_id=cropped_image.id,
                    original_image_id=face.image_id,
                    face_position_x=face.face_position_x,
                    face_position_y=face.face_position_y,
                    face_height=face.face_height,
                    face_width=face.face_width,
                    user_id=face.user_id,
                )

                db.session.add(cropped_image)
                db.session.add(new_face)
                db.session.delete(face)
                db.session.commit()
    except AttributeError:
        pass  # then skip this face


def downgrade():
    pass
