import logging
from pathlib import Path

import pandas as pd


log = logging.getLogger(__name__)


def write_files_with_missing(
    df: pd.DataFrame, missing: pd.DataFrame, output: Path
) -> None:
    """
    Write out two dataframes: one for the original data and one for the records which
    could not be matched to the missing data. The latter will be written to a file
    with the name "<output>__missing.csv"
    """
    missing_output = output.parent / f"{output.stem}__missing.csv"
    log.info(f"Writing {len(missing)} missing records to {missing_output}")
    missing.to_csv(missing_output, index=False)
    log.info(f"Writing {len(df)} output records to {output}")
    df.to_csv(output, index=False)
    log.info("Finished")
