"""Tasks for extracting FARS data from NHTSA."""

import os
from pathlib import Path

import pandas as pd
import requests
from prefect import task, get_run_logger


FARS_BASE_URL = "https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/{year}/National/"


@task(retries=3, retry_delay_seconds=60)
def download_fars_csv(year: int, output_dir: str = "./data/raw") -> str:
    """Download the FARS accident CSV for a given year.
    
    Args:
        year: The FARS data year to download.
        output_dir: Directory to save the downloaded file.
        
    Returns:
        Path to the downloaded CSV file.
        
    Raises:
        requests.HTTPError: If the download fails after retries.
    """
    logger = get_run_logger()
    url = f"https://static.nhtsa.gov/nhtsa/downloads/FARS/{year}/National/FARS{year}NationalCSV.zip"
    
    logger.info(f"Downloading FARS data for year {year} from {url}")
    
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    
    os.makedirs(output_dir, exist_ok=True)
    zip_path = Path(output_dir) / f"FARS{year}.zip"
    
    with open(zip_path, "wb") as f:
        f.write(response.content)
    
    logger.info(f"Downloaded {zip_path} ({len(response.content)} bytes)")
    
    # Extract ZIP
    import zipfile
    extract_dir = Path(output_dir) / str(year)
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_dir)
    
    # Find accident.csv
    csv_files = list(extract_dir.glob("*accident*.csv"))
    if not csv_files:
        # Try case-insensitive search
        csv_files = [f for f in extract_dir.rglob("*.csv") if "accident" in f.name.lower()]
    
    if not csv_files:
        raise FileNotFoundError(f"No accident CSV found in extracted archive for year {year}")
    
    csv_path = csv_files[0]
    logger.info(f"Extracted accident CSV: {csv_path}")
    
    return str(csv_path)


@task
def read_accident_csv(csv_path: str) -> pd.DataFrame:
    """Read the accident CSV into a pandas DataFrame.
    
    Args:
        csv_path: Path to the accident CSV file.
        
    Returns:
        DataFrame with raw accident data.
    """
    logger = get_run_logger()
    logger.info(f"Reading accident CSV: {csv_path}")
    
    df = pd.read_csv(csv_path, encoding="latin-1", low_memory=False)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    
    return df
