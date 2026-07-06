from typing import Dict, Any
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from bdlpkg.providers.isp.settings.services.isp_config import get_settings
from bdlpkg.providers.gcp.settings.services.gcp_config import get_settings as get_gcp_settings
from bdlpkg.providers.bdl.udm.services.udm_config import get_UDM_config

router = APIRouter(default_response_class=JSONResponse)


@router.get(
    "/provider/isp",
    status_code=status.HTTP_200_OK,
    summary="Configuration from ISP provider",
    description=
    "Retrieve configuration about ISP provider connection. Such as Databases, Keys, Storage resources, etc..",
)
def isp_configuration() -> Dict[str, dict]:
    return get_settings()


@router.get(
    "/provider/gcp",
    status_code=status.HTTP_200_OK,
    summary="Configuration from GCP provider",
    description=
    "Retrieve configuration about GCP provider connection. Such as Service Account, Projects, etc..",
)
def gcp_configuration() -> Dict[str, dict]:
    return get_gcp_settings()


@router.get(
    "/provider/bdl/udm",
    status_code=status.HTTP_200_OK,
    summary="Display UDM configuration",
    description=
    "Retrieve the active UDM configuration or all the UDM elements present.",
)
def UDM_configuration(only_active: bool = True) -> Dict[str, Any]:
    return get_UDM_config(only_active=only_active)