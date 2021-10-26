#!/usr/bin/env python
"""
Assignment Creation Script.

This script takes the historic SPD data and converts it into two new CSVs: a list of
officers currently missing from OpenOversight, and a list of assignments for all
officers. The missing officers are all officers who were not part of the 2021-06-30
roster and were on the force prior to 2020.

The original upload included some assignment/job information. *That data will need to be
deleted before this insertion can run!!*. The following is the SQL needed to accomplish
this:

DELETE FROM assignments WHERE department_id = 1;
DELETE FROM jobs WHERE department_id = 1;

Alternatively, if there are no other departments to worry about:
TRUNCATE jobs, assignments RESTART IDENTITY;

Additionally, the now-defunct units can be removed with the following command:
DELETE FROM unit_types WHERE id IN (
    SELECT u.id
    FROM unit_types u
    LEFT JOIN assignments a
        ON u.id = a.unit_id
        WHERE a.id IS NULL
);
"""
import bisect
import logging
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
import pandas as pd
from assignment_correction import title_corrections, unit_corrections


log = logging.getLogger()


def find_termination(df: pd.DataFrame, roster_dates: List[str]) -> Optional[str]:
    """
    Find the last date of employment for an officer. This receives a dataframe
    per-badge, and a list of all dates we have a roster for. The value returned is
    either 1) a valid date, meaning the officer is no longer with SPD or 2) None, which
    means the officer is still employed in that position.
    """
    # Sort by date
    df = df.sort_values("date")
    # Get the most recent date for this officer
    last_date = df.iloc[-1].date
    # Get the *index* of the next date after the officer's last date
    next_date_index = bisect.bisect(roster_dates, last_date)
    if next_date_index == len(roster_dates):
        # The "next" date would be right at the end, so this officer is still employed
        end_date = None
    else:
        # The officer is no longer employed, so the next roster (the first one
        # chronologically where they *don't* show up) is set as their end date
        end_date = roster_dates[next_date_index]
    return end_date


def make_assignments(df: pd.DataFrame, end_dates: pd.Series) -> pd.DataFrame:
    """
    Create the assignment records for an officer. This receives a dataframe per-badge
    and a list of the end dates for each officer. This condenses every record we have
    across all records in known history to only the changes (in unit or title) that
    occur for an officer.
    """
    # Drop any duplicate assignment records, keep the first record that's encountered.
    # This makes sure the earliest record of their position change is maintained.
    df = df.drop_duplicates(subset=["badge", "unit_description", "title"], keep="first")
    # Get the badge for this officer
    badge = df.reset_index().iloc[0].badge
    # Sort by date ascending
    df = df.sort_values("date")
    # Get most recent name
    fn, first, middle, last = df.iloc[-1][
        ["full_name", "first_name", "middle_name", "last_name"]
    ]
    # Replace all values with that
    df[["full_name", "first_name", "middle_name", "last_name"]] = [
        fn,
        first,
        middle,
        last,
    ]
    # Some middle names are actually team names (in very old rosters), remove these
    df.loc[:, "middle_name"] = df["middle_name"].replace(r"^\(.*\)$", "", regex=True)
    # Rename columns
    df = df.rename({"date": "start_date"}, axis="columns")
    # Assume the date listed as the "start date", shift all values up one for end date.
    # This will make the start date of the next assignment be the end date of the
    # current assignment. Use the previously computed end date for this badge as the
    # last assignment's end date.
    df["end_date"] = df["start_date"].shift(-1, fill_value=end_dates.loc[badge])
    return df


def apply_correction_mapping(
    column: pd.Series, correction: Dict[str, Tuple[str, ...]]
) -> pd.Series:
    """
    Apply corrections to a column. The corrections should come in the form of
    "valid name" -> "list of names to correct". A new mapping will be generated from
    this (of "bad name" -> "good name") which can be used to replace the values in the
    column provided. Panda's `map` function will change all values not found in the
    mapping to NaN, so we fillna with the original column to retain all values.
    """
    correct_mapping = {}
    for good, bad_list in correction.items():
        if isinstance(bad_list, str):
            print(f"Error row: {good} - {bad_list}")
            continue
        for bad in bad_list:
            correct_mapping[bad] = good
    return column.map(correct_mapping).fillna(column)


def main(id_path: Path, historic_data_path: Path, output: Path):
    log.info("Starting import")
    ids = pd.read_csv(id_path, usecols=["id", "badge number"])
    hist = pd.read_csv(historic_data_path)
    # Get a sorted list of all the unique roster dates
    roster_dates = sorted(hist["date"].unique())
    log.info("Correcting unit/title info")
    # Correct the unit and title names
    hist.loc[:, "title"] = apply_correction_mapping(
        hist["title"], title_corrections.title_corrections
    )
    hist.loc[:, "unit_description"] = apply_correction_mapping(
        hist["unit_description"], unit_corrections.unit_corrections
    )
    log.info("Computing last known job date for officers")
    # Get the end dates for each officer
    end_dates = hist.groupby("badge").apply(
        partial(find_termination, roster_dates=roster_dates)
    )
    # Rename the columns so we can merge, and to change "id" to "ooid"
    ids.columns = ["ooid", "badge"]
    log.info("Computing assignments")
    # This is essentially a more complex "drop duplicates"
    hist_assigned = (
        hist.groupby("badge")
        .apply(partial(make_assignments, end_dates=end_dates))
        .reset_index(drop=True)
    )
    # Merge the OpenOversight IDs with the assignment data
    merged = hist_assigned.merge(ids, on="badge", how="left")
    # Replace the badge column with "#" + badge, this is needed for OO
    # In cases where we are supplying an officer that isn't in the database yet, we will
    # provide this pseudo-badge as an internal reference for the importer. It will match
    # the records in the assignments CSV to any new officers that are created with the
    # same pseudo-badge.
    merged["pseudo_badge"] = "#" + merged["badge"]
    # Convert the OOID column to a nullable interger, then to a string. If this isn't
    # done, then we get floating point numbers where we want ints.
    merged = merged.astype({"ooid": pd.Int64Dtype()}).astype({"ooid": str})
    # The string conversion gives us "<NA>" values where there should be nulls. Ah well.
    merged.loc[:, "ooid"] = merged["ooid"].replace({"<NA>": None})
    # For everywhere we *don't* have an OOID, use the pseudo-badge
    merged.loc[:, "ooid"] = merged["ooid"].fillna(merged["pseudo_badge"])
    # Remove any records where an officer *wasn't active* during 2020 or after
    recently_active_officers = set(
        end_dates[(end_dates > "2020-01-01") | end_dates.isna()].index.values
    )
    merged = merged[merged["badge"].isin(recently_active_officers)]
    # Pull out officers not currently in OO
    missing_officers = merged[merged["ooid"].str.startswith("#")].drop_duplicates(
        subset=["badge"], keep="last"
    )
    log.info("Writing output files")
    # Reduce to minimum necessary and rename columns
    missing_officers = missing_officers[
        ["last_name", "first_name", "middle_name", "ooid"]
    ].rename({"ooid": "id", "middle_name": "middle_initial"}, axis="columns")
    # Department name needed for ingestion
    missing_officers["department_name"] = "Seattle Police Department"
    missing_path = output.parent / f"{output.stem}_missing_officers.csv"
    missing_officers.to_csv(missing_path, index=False)
    # Pull out assignments
    # Reduce to minimum necessary and rename columns
    assignments = merged[
        ["ooid", "badge", "unit_description", "title", "start_date", "end_date"]
    ]
    assignments = assignments.rename(
        {"ooid": "officer_id", "badge": "badge_number", "title": "job_title"},
        axis="columns",
    )
    # Empty ID column needed for ingestion
    assignments["id"] = None
    assignments.to_csv(output, index=False)


@click.command()
@click.argument("id_path", type=click.Path(exists=True, path_type=Path))
@click.argument("historic_data_path", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
def cli(id_path: Path, historic_data_path: Path, output: Path):
    logging.basicConfig(
        format="[%(asctime)s - %(name)s - %(lineno)3d][%(levelname)s] %(message)s",
        level=logging.INFO,
    )
    main(id_path, historic_data_path, output)


if __name__ == "__main__":
    cli()
