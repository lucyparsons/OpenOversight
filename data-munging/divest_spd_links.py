#!/usr/bin/env python
import logging
from pathlib import Path

import click
import pandas as pd


log = logging.getLogger()


def main(id_path: Path, link_path: Path, output: Path):
    log.info("Starting import")
    ids = pd.read_csv(id_path, usecols=["id", "badge number"])
    links = pd.read_csv(link_path)
    # Collapse the multiple links columns into a single column list
    links["url"] = links[
        ["Links", "last updated: 8/6/2021", "Unnamed: 6"]
    ].values.tolist()
    # Make the badge column a string
    links["badge number"] = links["Badge Number"].astype(str)
    # Subset the columns at this point
    links = links[["badge number", "url"]]
    # Explode the list of links into individual rows
    links = links.explode("url", ignore_index=True)
    # Drop any rows where a link doesn't exist (this will be most)
    links = links[links["url"].notna()]
    # Join the two dataframes on badge number
    merged = links.merge(ids, how="left").astype({"id": pd.Int64Dtype()})
    # Split off the links that don't have an OpenOversight badge associated with them
    _has_id = merged["id"].notna()
    missing = merged[~_has_id]
    # Remove those missing urls
    merged = merged[_has_id][["id", "url"]]
    # Rename id to "officer_ids", used in importer:
    # https://openoversight.readthedocs.io/en/latest/advanced_csv_import.html#links-csv
    merged.columns = ["officer_ids", "url"]
    # Add the extra column info
    merged["title"] = "Divest SPD Twitter thread"
    merged["link_type"] = "Link"
    merged["author"] = "Divest SPD"
    # Modify the information for tweets not made by Divest SPD
    _not_divest = ~merged["url"].str.contains("DivestSPD")
    merged.loc[_not_divest, "title"] = "Meet SPD Twitter thread"
    merged.loc[_not_divest, "author"] = "nbd1232"
    # Add an empty id column
    merged["id"] = None
    missing_output = output.parent / f"{output.stem}__missing.csv"
    log.info(f"Writing {len(missing)} missing records to {missing_output}")
    missing.to_csv(missing_output, index=False)
    log.info(f"Writing {len(merged)} output records to {output}")
    merged.to_csv(output, index=False)
    log.info("Finished")


@click.command()
@click.argument("id_path", type=click.Path(exists=True, path_type=Path))
@click.argument("link_path", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
def cli(id_path: Path, link_path: Path, output: Path):
    logging.basicConfig(
        format="[%(asctime)s - %(name)s - %(lineno)3d][%(levelname)s] %(message)s",
        level=logging.INFO,
    )
    main(id_path, link_path, output)


if __name__ == "__main__":
    cli()
