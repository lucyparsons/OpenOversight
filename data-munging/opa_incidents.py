#!/usr/bin/env python
import json
import logging
from io import StringIO
from pathlib import Path
from typing import Dict

import click
import numpy as np
import pandas as pd
import requests


log = logging.getLogger(__name__)

URL = "https://data.seattle.gov/api/views/99yi-dthu/rows.csv?accessType=DOWNLOAD"


def _nan(value) -> str:
    """Create a string based off a value. If the value is NaN, return an empty string."""
    if value is None or (isinstance(value, (int, float)) and np.isnan(value)):
        return ""
    return value


def create_address(series) -> str:
    """Create a pseudo-address using the precinct, sector, and beat."""
    parts = [
        series["Incident Precinct"],
        series["Incident Sector"],
        series["Incident Beat"],
    ]
    # Some of these parts might be missing, only join the parts we have
    parts = [part for part in parts if part]
    return " - ".join(parts)


def create_description(series):
    """
    Create a description of an incident based off numerous fields. All reports within
    a case are combined, but each report receives all the information available to it.
    """
    desc = ""
    subincident_count = len(series.Allegation)
    for idx in range(subincident_count):
        # If there's only 1 report, no need to differentiate it
        count = f"{idx + 1} " if subincident_count > 1 else " "
        allegation = _nan(series["Allegation"][idx])
        if allegation:
            count += "— "
        desc += f"<h4>Allegation {count}{allegation}</h4>"
        # Build a description per report
        desc += f"""\
<b>Name:</b> {series["name"][idx]}
<b>Badge #:</b> {series["badge number"][idx]}
<b>Disposition:</b> {_nan(series["Disposition"][idx])}
<b>Discipline:</b> {_nan(series["Discipline"][idx])}
<b>Incident Type:</b> {_nan(series["Incident Type"][idx])}
<b>Finding:</b> {_nan(series["Finding"][idx])}

"""

    # These fields are common across all reports within a case
    desc += f"""\
<b>Source:</b> {_nan(series.Source)}
<b>Case Status:</b> {_nan(series["Case Status"])}
<a href="https://sea-scanners.wiki/police/opa-case-legend" target="_blank" rel="noopener noreferrer"><i>Legend</i></a>
"""
    return desc.strip()


def write_output(df: pd.DataFrame, output: Path, name: str) -> None:
    path = output.parent / f"{output.stem}__{name}.csv"
    log.info(f"Writing {len(df)} records to {path}")
    df.to_csv(path, index=False)


def match_incidents(ids: pd.DataFrame, nid_mapping: pd.DataFrame) -> pd.DataFrame:
    """Match the OpenOversight IDs to OPA cases using the Named Employee ID mapping."""
    log.info("Fetching OPA data")
    # Get the records from the Seattle Data website
    response = requests.get(URL)
    buffer = StringIO(response.text)
    # This data uses "-" as a null value, add it to the list of acceptable null values
    complaints = pd.read_csv(buffer, na_values="-")
    # Merge with the employee ID mapping. This produces duplicates, so we drop them.
    mapped = complaints.merge(nid_mapping, how="inner").drop_duplicates()
    log.info("Combining with OO IDs")
    # Add the OpenOversight IDs to the incident list
    with_ids = mapped.merge(
        ids[["id", "badge number", "name"]],
        how="inner",
        left_on="ID #",
        right_on="badge number",
    )
    # There are a number of columns in the dataset that we don't need. These are the
    # ones we care about.
    col_to_keep = [
        "Unique Id",
        "File Number",
        "Occurred Date",
        "Incident Precinct",
        "Incident Sector",
        "Incident Beat",
        "Source",
        "Incident Type",
        "Allegation",
        "Disposition",
        "Discipline",
        "Case Status",
        "Finding",
        "badge number",
        "id",
        "name",
    ]
    # These columns will be aggregated into lists for each case
    list_cols = {
        "Incident Type",
        "Allegation",
        "Disposition",
        "Discipline",
        "Finding",
        "Unique Id",
        "badge number",
        "id",
        "name",
    }
    # These columns will be used for aggregation
    col_to_agg = ["File Number", "Occurred Date"]
    log.info("Aggregating by OPA case")
    squished = (
        # Filter by the columns to keep
        with_ids[col_to_keep]
        # Group by the aggregation columns
        .groupby(col_to_agg)
        # Determine the aggregation strategy. It will create lists for all the columns
        # we want lists for, otherwise the first value will be chosen.
        .agg(
            {
                col: (list if col in list_cols else "first")
                for col in (set(col_to_keep) - set(col_to_agg))
            }
        )
        # Reset the index since aggregation throws them all the indices
        .reset_index()
    )
    log.info("Formatting columns")
    # Convert the occurred date column to a datetime object
    squished.loc[:, "Occurred Date"] = pd.to_datetime(squished["Occurred Date"])
    # Create the address
    squished["Address"] = squished.apply(create_address, axis=1)
    # Create the description
    squished["Description"] = squished.apply(create_description, axis=1)
    log.info("Conforming to OO standard")
    # Reduce to only the fields we need
    reduced = squished[["File Number", "Occurred Date", "Address", "Description", "id"]]
    # Convert the officer IDs into a pipe separated list
    reduced["officer_ids"] = (
        reduced["id"].apply(lambda x: [str(y) for y in set(x)]).str.join("|")
    )
    # Rename the columns to what OpenOversight is expecting
    reduced.columns = [
        "report_number",
        "date",
        "street_name",
        "description",
        "id",
        "officer_ids",
    ]
    reduced.loc[:, "report_number"] = "OPA Case " + reduced["report_number"]
    # Create a pseudo-id, for use with matching links
    reduced["id"] = reduced.apply(lambda r: f"#{r.name}", axis=1)
    # Add department name and common fields
    reduced["department_name"] = "Seattle Police Department"
    reduced["city"] = "Seattle"
    reduced["state"] = "WA"
    # Some cases have a 1900-01-01 occurred date. Some of these have over 1000 reports!
    # We just discard them.
    final = reduced[reduced["date"] > "1950-01-01"]
    return final


def match_links(incidents: pd.DataFrame, opas: Dict[str, str]) -> pd.DataFrame:
    """Match the OPA links to the OpenOversight incidents."""
    log.info("Merging OPA links with incident data")
    # Convert the OPA links JSON to a dataframe
    opa_links = pd.DataFrame(opas.items(), columns=["name", "url"])
    # Reduce to the necessary columns
    prep_merge = incidents[["report_number", "id", "officer_ids"]]
    # Unify the OPA names
    prep_merge["name"] = (
        prep_merge["report_number"].str.replace("OPA Case ", "").str.replace("OPA", "")
    )
    # Merge the incidents with the OPA links
    matched_opas = opa_links.merge(prep_merge, how="inner", on="name")
    matched_opas = matched_opas[["url", "report_number", "id", "officer_ids"]]
    # Rename columns
    matched_opas.columns = ["url", "title", "incident_ids", "officer_ids"]
    matched_opas.loc[:, "title"] = "OPA Case " + matched_opas["title"]
    # Add the common fields
    matched_opas["link_type"] = "Link"
    matched_opas["author"] = "Seattle Office of Police Accountability"
    matched_opas["id"] = None
    return matched_opas


def main(id_path: Path, mapping_path: Path, opa_link_path: Path, output: Path):
    log.info("Starting import")
    ids = pd.read_csv(id_path)
    # Combine name into single field
    ids["name"] = ids["first name"] + " " + ids["last name"]
    named_employee_mapping = pd.read_csv(mapping_path)
    opa_links = json.loads(opa_link_path.read_text())
    incidents = match_incidents(ids, named_employee_mapping)
    links = match_links(incidents, opa_links)
    write_output(incidents, output, "incidents")
    write_output(links, output, "links")


@click.command()
@click.argument("id_path", type=click.Path(exists=True, path_type=Path))
@click.argument("mapping_path", type=click.Path(exists=True, path_type=Path))
@click.argument("opa_link_path", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
def cli(id_path: Path, mapping_path: Path, opa_link_path: Path, output: Path):
    logging.basicConfig(
        format="[%(asctime)s - %(name)s - %(lineno)3d][%(levelname)s] %(message)s",
        level=logging.INFO,
    )
    main(id_path, mapping_path, opa_link_path, output)


if __name__ == "__main__":
    cli()
