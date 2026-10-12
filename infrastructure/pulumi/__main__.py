"""Pulumi program to provision Azure resources for the FARS crash data pipeline."""

import pulumi
from pulumi_azure_native import resources, storage

# Configuration
config = pulumi.Config()
location = config.get("location") or "East US"
env = config.get("env") or "dev"

# Naming convention
base_name = f"farscrash{env}"

# Resource Group
resource_group = resources.ResourceGroup(
    "resourceGroup",
    resource_group_name=f"{base_name}-rg",
    location=location,
)

# Storage Account
storage_account = storage.StorageAccount(
    "storageAccount",
    account_name=f"{base_name}sa",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    sku=storage.SkuArgs(name=storage.SkuName.STANDARD_LRS),
    kind=storage.Kind.STORAGE_V2,
    allow_blob_public_access=False,
    minimum_tls_version=storage.MinimumTlsVersion.TLS1_2,
)

# Blob Container for bronze data
bronze_container = storage.BlobContainer(
    "bronzeContainer",
    account_name=storage_account.name,
    resource_group_name=resource_group.name,
    container_name="bronze",
    public_access=storage.PublicAccess.NONE,
)

# Blob Container for raw data
raw_container = storage.BlobContainer(
    "rawContainer",
    account_name=storage_account.name,
    resource_group_name=resource_group.name,
    container_name="raw",
    public_access=storage.PublicAccess.NONE,
)

# Export outputs
pulumi.export("resource_group_name", resource_group.name)
pulumi.export("storage_account_name", storage_account.name)
pulumi.export("storage_account_id", storage_account.id)
pulumi.export("bronze_container_name", bronze_container.name)
pulumi.export("raw_container_name", raw_container.name)
