from pydantic import BaseModel, Field
from bdlpkg.utils.health.entities.statusenum import StatusEnum


class HealthCheck(BaseModel):
    title: str = Field(..., description="API title")
    description: str = Field(..., description="Brief description of the API")
    version: str = Field(..., description="API semver version number")
    status: StatusEnum = Field(..., description="API current status")
    hostname: str = Field(..., description="Current hostname")
