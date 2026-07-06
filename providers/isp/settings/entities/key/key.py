from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings
from enum import Enum
from typing import Optional


class KeyEnum(str, Enum):
    """
    Enum representing different types of keys used in various configurations.

    :param isp_keytab: Represents an ISP keytab key.
    :type isp_keytab: str
    :param gcp_sa: Represents a Google Cloud Platform service account key.
    :type gcp_sa: str
    """
    isp_keytab = 'isp_keytab'
    gcp_sa = 'gcp_sa'


class GenericKeySettings(BaseSettings):
    """
    Settings class for managing generic key configurations.

    This class defines the structure for key-based settings, including the path to the key, 
    the type of key, and an optional associated ID. It supports multiple key types as defined 
    in the `KeyEnum` enum.

    :param resource_name: The name of the resource that the key is associated with.
    :type resource_name: str
    :param key_path: The path or secret containing the key file.
    :type key_path: SecretStr
    :param key_type: The type of the key (e.g., `isp_keytab` or `gcp_sa`).
    :type key_type: KeyEnum
    :param key_associate_id: An optional ID associated with the key, useful for additional identification or reference.
    :type key_associate_id: Optional[str]
    """
    resource_name: str
    key_path: SecretStr
    key_type: KeyEnum
    key_associate_id: Optional[str] = None