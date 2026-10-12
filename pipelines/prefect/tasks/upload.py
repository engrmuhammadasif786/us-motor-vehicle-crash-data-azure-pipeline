"""Tasks for uploading raw data to Azure Blob Storage."""

import os
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from prefect import task, get_run_logger


def _get_blob_service_client() -> BlobServiceClient:
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
def upload_csv_to_lake(
    csv_path: str,
    container_name: str = None,
    blob_prefix: str = "bronze/fars",
) -> str:
    """Upload a local CSV file to Azure Blob Storage.
    
    Args:
        csv_path: Local path to the CSV file.
        container_name: Blob container name. Defaults from env.
        blob_prefix: Prefix/path inside the container.
        
    Returns:
        The blob name of the uploaded file.
    """
    logger = get_run_logger()
    env = os.getenv("ENV", "dev")
    
    if container_name is None:
        container_name = os.getenv("AZURE_CONTAINER_NAME", "bronze")
    
    csv_path = Path(csv_path)
    year = csv_path.parent.name
    blob_name = f"{blob_prefix}/{year}/{csv_path.name}"
    
    logger.info(f"Uploading {csv_path} to {container_name}/{blob_name} (env={env})")
    
    blob_service = _get_blob_service_client()
    try:
        blob_service.create_container(name=container_name)
    except Exception:
        pass

    blob_client = blob_service.get_blob_client(
        container=container_name,
        blob=blob_name,
    )

    with open(csv_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    
    logger.info(f"Successfully uploaded to {blob_name}")
    return blob_name


@task
def upload_dataframe_to_lake(
    df,
    year: int,
    container_name: str = None,
    blob_prefix: str = "bronze/fars",
    filename: str = "accident.csv",
) -> str:
    """Upload a pandas DataFrame as CSV to Azure Blob Storage.
    
    Args:
        df: pandas DataFrame to upload.
        year: Data year for partitioning.
        container_name: Blob container name. Defaults from env.
        blob_prefix: Prefix/path inside the container.
        filename: Name of the blob file.
        
    Returns:
        The blob name of the uploaded file.
    """
    logger = get_run_logger()
    env = os.getenv("ENV", "dev")
    
    if container_name is None:
        container_name = os.getenv("AZURE_CONTAINER_NAME", "bronze")
    
    blob_name = f"{blob_prefix}/{year}/{filename}"
    
    logger.info(f"Uploading DataFrame to {container_name}/{blob_name} (env={env})")
    
    csv_buffer = df.to_csv(index=False).encode("utf-8")
    
    blob_service = _get_blob_service_client()
    try:
        blob_service.create_container(name=container_name)
    except Exception:
        pass

    blob_client = blob_service.get_blob_client(
        container=container_name,
        blob=blob_name,
    )

    blob_client.upload_blob(csv_buffer, overwrite=True)
    
    logger.info(f"Successfully uploaded to {blob_name}")
    return blob_name
