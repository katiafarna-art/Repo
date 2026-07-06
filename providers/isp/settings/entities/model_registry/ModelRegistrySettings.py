from typing import Union

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings
from bdlpkg.utils.bdlfile.entities.annotated import HttpUrl


class ModelRegistrySettings(BaseSettings):
    """
    Base class for model registry settings.

    This class defines the general settings required for connecting to a model registry,
    such as the resource name and the endpoint URL.

    :param resource_name: The name of the resource for the model registry.
    :type resource_name: str
    :param endpoint_url: The URL endpoint for the model registry.
    :type endpoint_url: HttpUrl
    """
    resource_name: str = Field(...)
    endpoint_url: HttpUrl = Field(...)

class DeterminedAIMRSettings(ModelRegistrySettings):
    """
    Settings class for the Determined AI model registry.

    This class extends the base `ModelRegistrySettings` with additional fields specific
    to Determined AI, including access credentials and SSL certificate verification settings.

    :param access_name: The username or access name for authentication.
    :type access_name: str
    :param access_key: The secret key or password for authentication, stored as a SecretStr.
    :type access_key: SecretStr
    :param verify_ssl_cert: Determines whether SSL certificate verification is enabled.
        It can be either a boolean or a string. By default, it is set to False.
        In production, HTTP is used directly for the service.
    :type verify_ssl_cert: Union[bool, str]
    """
    access_name: str = Field(...)
    access_key: SecretStr = Field(...)
    verify_ssl_cert: Union[bool,str] = Field(False, description="Verifica del SSL_Cert: di default a False, non serve quasi mai visto che sulle sandbox puoi usare il pacchetto pip_system_certs, in prod dai il service direttamente in HTTP.")
