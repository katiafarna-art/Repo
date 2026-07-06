from typing import Any, Dict, List, Tuple, Optional

from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from bdlpkg.providers.isp.databases.services.healthcheck import \
    get_database_healthcheck
from bdlpkg.providers.gcp.databases.services.healthcheck import \
    get_gcp_database_healthcheck
from bdlpkg.providers.isp.messaging.services.healthcheck import \
    get_mails_healthcheck, get_messaging_healthcheck
from bdlpkg.providers.isp.model_registry.services.healthcheck import \
    get_model_registry_healthcheck
from bdlpkg.providers.isp.storages.services.healthcheck import \
    get_storage_healthcheck, get_metadata_healtcheck
from bdlpkg.providers.gcp.storages.services.healthcheck import \
    get_gcp_storage_healthcheck
from bdlpkg.utils.health.entities.healthcheck import HealthCheck
from bdlpkg.utils.health.services.healthcheck import healthcheck, packagescheck

router = APIRouter(default_response_class=JSONResponse)


@router.get(
    "/application",
    response_model=HealthCheck,
    status_code=status.HTTP_200_OK,
    summary="Perform health check",
    description=
    "Perform health check on application and returns information about running service.",
)
def health_check() -> Dict[str, Any]:
    return healthcheck()


@router.get(
    "/packages",
    status_code=status.HTTP_200_OK,
    summary="Get list of installed packages",
)
def packages_check() -> List[Tuple[str, str]]:
    return packagescheck()


@router.get(
    "/databases/isp",
    status_code=status.HTTP_200_OK,
    summary="Perform health check on all available ISP databases connections",
)
def health_check_dbs() -> dict:
    return get_database_healthcheck()


@router.get(
    "/databases/gcp",
    status_code=status.HTTP_200_OK,
    summary="Perform health check on all available GCP databases connections (e.g. BigQuery)",
)
def health_check_dbs() -> dict:
    return get_gcp_database_healthcheck()


@router.get(
    "/storages/isp",
    status_code=status.HTTP_200_OK,
    summary="Perform health check on all available ISP storages connections",
)
def health_check_storages() -> dict:
    return get_storage_healthcheck()


@router.get(
    "/storages/isp/metadata",
    status_code=status.HTTP_200_OK,
    summary="Perform metadata info retrieval on specified ISP S3 bucket (possibly for a specific key)"
)
def health_check_metadata(resource_name: Optional[str] = None, 
                          key: Optional[str] = None) -> dict:
    return get_metadata_healtcheck(resource_name, key)

@router.get(
    "/storages/gcp",
    status_code=status.HTTP_200_OK,
    summary="Perform health check on all available GCP storages connections (e.g. GCS)",
)
def health_check_storages(gsc_bucket_name: Optional[str]="") -> dict:
    return get_gcp_storage_healthcheck(gsc_bucket_name)


@router.get("/mail",
            status_code=status.HTTP_200_OK,
            summary="Perform health check on all available mail services")
def health_check_mail() -> dict:
    return get_mails_healthcheck()


@router.get("/messaging",
            status_code=status.HTTP_200_OK,
            summary="Perform health check on all available messaging services")
def health_check_messaging(acronimo: Optional[str]='BDL10') -> dict:
    return get_messaging_healthcheck(acronimo)


@router.get("/model_registry",
            status_code=status.HTTP_200_OK,
            summary="Perform health check on all available model registries")
def health_check_model_registry() -> dict:
    return get_model_registry_healthcheck()
