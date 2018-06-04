"""change_faces_to_thumbnails

Revision ID: 59e9993c169c
Revises: bd0398fe4aab
Create Date: 2018-06-04 19:04:23.524079

"""

from app.models import Face, db
from app.utils import get_uploaded_cropped_image


# revision identifiers, used by Alembic.
revision = '59e9993c169c'
down_revision = 'bd0398fe4aab'
branch_labels = None
depends_on = None


def upgrade():
    for face in Face.query.all():
        # import pdb; pdb.set_trace()
        if face.face_position_x \
           and face.image.filepath.split('/')[0] != 'static':
            left = face.face_position_x
            upper = face.face_position_y
            right = left + face.face_width
            lower = upper + face.face_height

            cropped_image = get_uploaded_cropped_image(face.image, (left, upper, right, lower))

            new_face = Face(
                officer_id=face.officer_id,
                img_id=cropped_image.id,
                user_id=face.user_id)

            db.session.add(cropped_image)
            db.session.add(new_face)
            db.session.delete(face)
            db.session.commit()


def downgrade():
    pass
