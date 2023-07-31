#!/usr/bin/python

import argparse

from OpenOversight.app import create_app
from OpenOversight.app.models.database import db
from OpenOversight.app.utils.constants import KEY_ENV_DEV
from OpenOversight.tests.conftest import add_mockdata


app = create_app(KEY_ENV_DEV)
ctx = app.app_context()
ctx.push()
db.app = app


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--populate",
        action="store_true",
        help="populate the database with test data",
    )
    parser.add_argument(
        "-c",
        "--cleanup",
        action="store_true",
        help="delete all test data from the database",
    )
    args = parser.parse_args()

    if args.populate:
        print("[*] Populating database with test data...")
        add_mockdata(db.session)
        print("[*] Completed successfully!")

    if args.cleanup:
        print("[*] Cleaning up database...")
        db.drop_all()
        db.create_all()
        print("[*] Completed successfully!")
