#!/usr/bin/env python
"""
Roster update script.

This script takes the current list of officers from OpenOversight and the historic
SPD data, and produces the following:
- New officers (including and demographics where available)
- Assignments for all officers (this requires truncation)
- Salary data for the new officers

Since this completely reconstructs the assignments, **existing assignment data will
need to be deleted before this upload is run!!*
The following is the SQL needed to accomplish this:

DELETE FROM assignments WHERE department_id = 1;
DELETE FROM jobs WHERE department_id = 1;

Alternatively, if there are no other departments to worry about:
TRUNCATE jobs, assignments RESTART IDENTITY

This script can theoretically be run on future roster updates (although salary date
may need to be changed).
"""
import logging
from pathlib import Path
from typing import NamedTuple

import assignments as assignments_module
import click
import demographic_data as demographic_module
import first_employed_date as first_employed_date_module
import pandas as pd
import spd_2021_salary_data as spd_2021_salary_data_module


log = logging.getLogger(__name__)


class DataFiles(NamedTuple):
    oo_officers: Path
    historical_roster: Path
    spd_2021_salary: str = (
        "https://data.seattle.gov/api/views/2khk-5ukd/rows.csv?accessType=DOWNLOAD"
    )
    demographic_data: str = (
        "https://data.seattle.gov/api/views/i2q9-thny/rows.csv?accessType=DOWNLOAD"
    )


def _output_data(df: pd.DataFrame, output: Path, name: str) -> None:
    path = output.parent / f"{output.stem}__{name}.csv"
    log.info(f"Writing {name} data to {path}")
    df.to_csv(path, index=False)


def main(files: DataFiles, output: Path):
    log.info("Starting import")
    officers = pd.read_csv(files.oo_officers)
    hist = pd.read_csv(files.historical_roster, low_memory=False)
    # Compute assignments and any new officers
    log.info("Computing assignments and new officers")
    assignments, new_officers = assignments_module.extract_all_assignments(
        officers[["id", "badge number"]].copy(), hist
    )
    log.info("Computing first employed date")
    # For new officers, compute the first employed date
    first_employed_date = first_employed_date_module.get_first_employed(
        assignments.copy(), space_in_name=False
    )
    new_officers = new_officers.merge(
        first_employed_date, on=["id", "department_name"], how="left"
    )
    ids_for_salary = new_officers[["id", "last_name", "first_name"]].copy()
    log.info("Computing 2021 salary")
    salary_2021, _ = spd_2021_salary_data_module.match_salary_data(
        ids=ids_for_salary,
        url=files.spd_2021_salary,
        convert_id=False,
    )
    # The new officers don't include badge numbers (those are populated by
    # assignments), so we need to temporarily add it here
    log.info("Computing demographics")
    demo_match = new_officers.copy()
    demo_match["badge number"] = new_officers["id"].str.strip("#")
    demographics, _ = demographic_module.match_demographics(
        ids=demo_match,
        url=files.demographic_data,
        convert_badge=False,
    )
    new_officers = new_officers.merge(
        demographics, on=["id", "department_name"], how="left"
    )
    log.info("Writing output files")
    _output_data(new_officers, output, "officers")
    _output_data(assignments, output, "assignments")
    _output_data(salary_2021, output, "salary_2021")


@click.command()
@click.argument("oo_officers", type=click.Path(exists=True, path_type=Path))
@click.argument("historical_roster", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
def cli(
    oo_officers: Path,
    historical_roster: Path,
    output: Path,
):
    logging.basicConfig(
        format="[%(asctime)s - %(name)s - %(lineno)3d][%(levelname)s] %(message)s",
        level=logging.INFO,
    )
    files = DataFiles(
        oo_officers=oo_officers,
        historical_roster=historical_roster,
    )
    main(files, output)


if __name__ == "__main__":
    cli()
