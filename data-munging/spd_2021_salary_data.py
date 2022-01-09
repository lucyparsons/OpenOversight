#!/usr/bin/env python
import logging
from io import StringIO
from pathlib import Path

import click
import common
import pandas as pd
import requests


log = logging.getLogger(__name__)

URL = "https://data.seattle.gov/api/views/2khk-5ukd/rows.csv?accessType=DOWNLOAD"


def _lower(df: pd.DataFrame) -> list[pd.DataFrame]:
    return [df["last"].str.lower(), df["first"].str.lower()]


def match_salary_data(
    ids: pd.DataFrame,
    url: str,
    convert_id: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    response = requests.get(url)
    buffer = StringIO(response.text)
    # Filter down to police department related only, get only columns needed
    df = pd.read_csv(buffer)
    df = df[
        df["Department"].isin(["Police Department", "Commnty Sfty and Comm Ctr Dept"])
    ]
    df = df[["Last Name", "First Name", "Hourly Rate "]]
    df.columns = ["last", "first", "hourly"]
    ids.columns = ["id", "last", "first"]
    # Remove Jr, IV, II, III, etc.
    df.loc[:, "last"] = df["last"].replace(
        r" ?((Jr)|(II)|(III)|(IV))\.?", "", regex=True
    )
    # Merge with prod data based on the first and last names
    # Do a case-agnostic comparison here
    merged = df.merge(ids, how="left", left_on=_lower(df), right_on=_lower(ids))
    if convert_id:
        merged = merged.astype({"id": pd.Int64Dtype()})
    # Estimate yearly pay based on hourly rate
    # ASSUMED: 40 hour work week, 50 weeks a year
    merged["salary"] = merged["hourly"] * 40 * 50
    # Split off the links that don't have an OpenOversight badge associated with them
    _has_id = merged["id"].notna()
    missing = merged[~_has_id]
    merged = merged[_has_id]
    # Reduce columns even more
    merged = merged[["salary", "id"]]
    # Rename columns for OO
    merged.columns = ["salary", "officer_id"]
    # Add an empty id column
    merged["id"] = None
    # Set the year to 2020
    merged["year"] = 2021
    # Convert the salary from "$###,###.##" to a float
    merged.loc[:, "salary"] = (
        merged["salary"].replace(r"[\$,]", "", regex=True).astype(float)
    )
    # Set overtime pay to -1 since the year is not over
    merged["overtime_pay"] = -1
    return merged, missing


def main(id_path: Path, output: Path, url: str = URL):
    log.info("Starting import")
    ids = pd.read_csv(
        id_path,
        usecols=["id", "first name", "last name"],
    )
    merged, missing = match_salary_data(ids, url)
    common.write_files_with_missing(merged, missing, output)


@click.command()
@click.argument("id_path", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
def cli(id_path: Path, output: Path):
    logging.basicConfig(
        format="[%(asctime)s - %(name)s - %(lineno)3d][%(levelname)s] %(message)s",
        level=logging.INFO,
    )
    main(id_path, output)


if __name__ == "__main__":
    cli()
