"""Tasks for loading data from Blob Storage into the data warehouse."""

import os

import pandas as pd
from azure.storage.blob import BlobServiceClient
from prefect import task, get_run_logger


def _get_blob_service_client():
    """Get a BlobServiceClient based on environment (dev/prod)."""
    env = os.getenv("ENV", "dev")
    api_version = os.getenv("AZURE_BLOB_API_VERSION", "2023-11-03")

    if env == "dev":
        account_name = os.getenv("AZURITE_ACCOUNT_NAME", "devstoreaccount1")
        account_key = os.getenv("AZURITE_ACCOUNT_KEY", "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==")
        endpoint = os.getenv("AZURITE_BLOB_ENDPOINT", f"http://127.0.0.1:10000/{account_name}")
        return BlobServiceClient(
            account_url=endpoint,
            credential=account_key,
            api_version=api_version,
        )
    else:
        account_name = os.getenv("AZURE_STORAGE_ACCOUNT")
        account_key = os.getenv("AZURE_STORAGE_KEY")
        from azure.identity import DefaultAzureCredential
        if account_key:
            return BlobServiceClient(
                account_url=f"https://{account_name}.blob.core.windows.net",
                credential=account_key,
                api_version=api_version,
            )
        return BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=DefaultAzureCredential(),
            api_version=api_version,
        )


@task
def download_blob_to_dataframe(
    blob_name: str,
    container_name: str = None,
) -> pd.DataFrame:
    """Download a CSV blob and return it as a pandas DataFrame.
    
    Args:
        blob_name: Name/path of the blob in the container.
        container_name: Blob container name. Defaults from env.
        
    Returns:
        DataFrame with the blob contents.
    """
    logger = get_run_logger()
    
    if container_name is None:
        container_name = os.getenv("AZURE_CONTAINER_NAME", "bronze")
    
    logger.info(f"Downloading blob {container_name}/{blob_name}")
    
    blob_service = _get_blob_service_client()
    blob_client = blob_service.get_blob_client(
        container=container_name,
        blob=blob_name,
    )
    
    downloader = blob_client.download_blob()
    csv_data = downloader.readall()
    
    import io
    df = pd.read_csv(io.BytesIO(csv_data), encoding="utf-8", low_memory=False)
    
    logger.info(f"Downloaded {len(df)} rows from blob")
    return df


@task
def load_to_warehouse(
    df: pd.DataFrame,
    table_name: str = "raw_accidents",
) -> str:
    """Load a DataFrame into the data warehouse.
    
    In dev mode, writes to DuckDB. In prod, writes to Snowflake.
    
    Args:
        df: DataFrame to load.
        table_name: Target table name.
        
    Returns:
        Confirmation message.
    """
    logger = get_run_logger()
    env = os.getenv("ENV", "dev")
    
    logger.info(f"Loading {len(df)} rows into {table_name} (env={env})")
    
    if env == "dev":
        import duckdb
        db_path = os.getenv("DUCKDB_PATH", "./data/dev.duckdb")
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        
        con = duckdb.connect(db_path)
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
        con.close()
        
        logger.info(f"Loaded data into DuckDB: {db_path}, table: {table_name}")
        return f"Loaded into DuckDB: {table_name}"
    
    else:
        import snowflake.connector
        from snowflake.connector.pandas_tools import write_pandas
        
        conn = snowflake.connector.connect(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            role=os.getenv("SNOWFLAKE_ROLE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        )
        
        success, num_chunks, num_rows, _ = write_pandas(
            conn=conn,
            df=df,
            table_name=table_name.upper(),
            auto_create_table=True,
            overwrite=True,
        )
        
        conn.close()
        
        logger.info(f"Loaded {num_rows} rows into Snowflake: {table_name}")
        return f"Loaded into Snowflake: {table_name} ({num_rows} rows)"
