import random
import sys
from distutils.util import strtobool
from typing import Optional
from urllib.parse import urlparse

from flask import current_app, url_for

from ...app.custom import add_jpeg_patch


# Call JPEG patch function
add_jpeg_patch()


def ac_can_edit_officer(officer, ac):
    if officer.department_id == ac.ac_department_id:
        return True
    return False


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


# This function is also used in the `utils/forms.py` file, so there's potential
# for a circular import scenario. Should a circular import scenario pop up,
# this function can be moved to its own file.
def get_or_create(session, model, defaults=None, **kwargs):
    if "csrf_token" in kwargs:
        kwargs.pop("csrf_token")

    # Because id is a keyword in Python, officers member is called oo_id
    if "oo_id" in kwargs:
        kwargs = {"id": kwargs["oo_id"]}

    # We need to convert empty strings to None for filter_by
    # as '' != None in the database and
    # such that we don't create fields with empty strings instead
    # of null.
    filter_params = {}
    for key, value in kwargs.items():
        if value != "":
            filter_params.update({key: value})
        else:
            filter_params.update({key: None})

    instance = model.query.filter_by(**filter_params).first()

    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in filter_params.items())
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        session.flush()
        return instance, True


def get_random_image(image_query):
    if image_query.count() > 0:
        rand = random.randrange(0, image_query.count())
        return image_query[rand]
    else:
        return None


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def normalize_gender(input_gender):
    if input_gender is None:
        return None
    normalized_genders = {
        "male": "M",
        "m": "M",
        "man": "M",
        "female": "F",
        "f": "F",
        "woman": "F",
        "nonbinary": "Other",
        "other": "Other",
    }

    return normalized_genders.get(input_gender.lower().strip())


def prompt_yes_no(prompt, default="no"):
    if default is None:
        yn = " [y/n] "
    elif default == "yes":
        yn = " [Y/n] "
    elif default == "no":
        yn = " [y/N] "
    else:
        raise ValueError("invalid default answer: {}".format(default))

    while True:
        sys.stdout.write(prompt + yn)
        choice = input().lower()
        if default is not None and choice == "":
            return strtobool(default)
        try:
            ret = strtobool(choice)
        except ValueError:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")
            continue
        return ret


def replace_list(items, obj, attr, model, db):
    """Set the objects attribute to the list of items received.

    This function take a list of items, an object, the attribute of that
    object that needs to be replaced, the model corresponding the items, and the db.

    DOES NOT SAVE TO DB.
    """
    new_list = []
    if not hasattr(obj, attr):
        raise LookupError("The object does not have the {} attribute".format(attr))

    for item in items:
        new_item, _ = get_or_create(db.session, model, **item)
        new_list.append(new_item)
    setattr(obj, attr, new_list)


def serve_image(filepath):
    if "http" in filepath:
        return filepath
    if "static" in filepath:
        return url_for("static", filename=filepath.replace("static/", "").lstrip("/"))


def str_is_true(str_):
    return strtobool(str_.lower())


def validate_redirect_url(url: Optional[str]) -> Optional[str]:
    """
    Check that a url does not redirect to another domain.
    :param url: the url to be checked
    :return: the url if validated, otherwise `None`
    """
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return None

    return url
