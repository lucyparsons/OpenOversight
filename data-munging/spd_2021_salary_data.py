#!/usr/bin/env python
import logging
from io import StringIO
from pathlib import Path

import click
import pandas as pd
import requests


log = logging.getLogger()

URL = "https://data.seattle.gov/api/views/2khk-5ukd/rows.csv?accessType=DOWNLOAD"


def main(id_path: Path, output: Path):
    log.info("Starting import")
    response = requests.get(URL)
    buffer = StringIO(response.text)
    # Filter down to police department only, get only columns needed
    df = pd.read_csv(buffer).query("Department == 'Police Department'")[
        ["Last Name", "First Name", "Hourly Rate "]
    ]
    df.columns = ["last", "first", "hourly"]
    ids = pd.read_csv(
        id_path,
        usecols=["id", "first name", "last name"],
    )
    ids.columns = ["id", "last", "first"]
    # Remove Jr, IV, II, III, etc.
    df.loc[:, "last"] = df["last"].replace(
        r" ?((Jr)|(II)|(III)|(IV))\.?", "", regex=True
    )
    # Merge with prod data based on the first and last names
    merged = df.merge(ids, how="left", on=["last", "first"]).astype(
        {"id": pd.Int64Dtype()}
    )
    # Estimate yearly pay based on hourly rate
    # ASSUMED: 40 hour work week, 50 weeks a year
    merged["salary"] = merged["hourly"] * 40 * 50
    # Split off the links that don't have an OpenOversight badge associated with them
    _has_id = merged["id"].notna()
    missing = merged[~_has_id]
    missing_output = output.parent / f"{output.stem}__missing.csv"
    log.info(f"Writing {len(missing)} missing records to {missing_output}")
    missing.to_csv(missing_output, index=False)
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
    log.info(f"Writing {len(merged)} output records to {output}")
    merged.to_csv(output, index=False)
    log.info("Finished")


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
