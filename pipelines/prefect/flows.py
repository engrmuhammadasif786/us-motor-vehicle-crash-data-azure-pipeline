"""Main Prefect flows orchestrating the FARS crash data pipeline."""

import os
import subprocess
from typing import Optional

from prefect import flow, get_run_logger

from pipelines.prefect.tasks.extract import download_fars_csv, read_accident_csv
from pipelines.prefect.tasks.upload import upload_dataframe_to_lake
from pipelines.prefect.tasks.load import download_blob_to_dataframe, load_to_warehouse


@flow(name="fars-extract-and-upload")
def extract_and_upload(year: int = 2022) -> str:
    """Extract FARS data and upload to data lake.
    
    Args:
        year: FARS data year to process.
        
    Returns:
        Blob name of the uploaded file.
    """
    logger = get_run_logger()
    logger.info(f"Starting extract-and-upload flow for year {year}")
    
    # Download and read CSV
    csv_path = download_fars_csv(year=year)
    df = read_accident_csv(csv_path=csv_path)
    
    # Upload to lake
    blob_name = upload_dataframe_to_lake(
        df=df,
        year=year,
        container_name=os.getenv("AZURE_CONTAINER_NAME", "bronze"),
        blob_prefix="bronze/fars",
        filename="accident.csv",
    )
    
    logger.info(f"Extract-and-upload completed: {blob_name}")
    return blob_name


@flow(name="fars-load-to-warehouse")
def load_to_dwh(blob_name: str, year: int = 2022) -> str:
    """Load data from lake into the data warehouse.
    
    Args:
        blob_name: Blob name in the data lake.
        year: FARS data year (for logging).
        
    Returns:
        Load confirmation message.
    """
    logger = get_run_logger()
    logger.info(f"Starting load-to-warehouse flow for blob: {blob_name}")
    
    df = download_blob_to_dataframe(
        blob_name=blob_name,
        container_name=os.getenv("AZURE_CONTAINER_NAME", "bronze"),
    )
    
    result = load_to_warehouse(df=df, table_name="raw_accidents")
    
    logger.info(f"Load-to-warehouse completed: {result}")
    return result


@flow(name="fars-run-dbt")
def run_dbt(target: Optional[str] = None) -> str:
    """Run dbt models and tests.
    
    Args:
        target: dbt target (dev/prod). Defaults to env or 'dev'.
        
    Returns:
        dbt command output.
    """
    logger = get_run_logger()
    
    if target is None:
        target = os.getenv("DBT_TARGET", "dev")
    
    logger.info(f"Running dbt build --target {target}")
    
    result = subprocess.run(
        ["dbt", "build", "--target", target],
        cwd="dbt",
        capture_output=True,
        text=True,
        check=False,
    )
    
    logger.info(f"dbt stdout:\n{result.stdout}")
    if result.stderr:
        logger.warning(f"dbt stderr:\n{result.stderr}")
    
    result.check_returncode()
    return result.stdout


@flow(name="fars-pipeline")
def fars_pipeline(year: int = 2022, dbt_target: Optional[str] = None) -> dict:
    """End-to-end FARS data pipeline.
    
    Orchestrates: extract → upload → load → transform.
    
    Args:
        year: FARS data year to process.
        dbt_target: dbt target environment.
        
    Returns:
        Dictionary with flow results.
    """
    logger = get_run_logger()
    logger.info(f"Starting full FARS pipeline for year {year}")
    
    # Step 1 & 2: Extract and upload to lake
    blob_name = extract_and_upload(year=year)
    
    # Step 3: Load from lake to warehouse
    load_result = load_to_dwh(blob_name=blob_name, year=year)
    
    # Step 4: Transform with dbt
    dbt_result = run_dbt(target=dbt_target)
    
    logger.info("FARS pipeline completed successfully")
    
    return {
        "blob_name": blob_name,
        "load_result": load_result,
        "dbt_result": dbt_result,
    }


if __name__ == "__main__":
    import sys
    
    # Allow CLI usage: python -m pipelines.prefect.flows [year] [dbt_target]
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2022
    target = sys.argv[2] if len(sys.argv) > 2 else None
    
    fars_pipeline(year=year, dbt_target=target)
