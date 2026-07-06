import json
import os
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from typing_extensions import Literal
from enum import Enum
from dotenv import dotenv_values
from bdlpkg.providers.isp import ISP_AMBIENTE_LOCAL_ENV_VALUE


class SASettings(BaseSettings):
    """
    Settings class for managing Service Account (SA) configurations.

    :param sa_istance_name: The name of the service account instance.
    :type sa_istance_name: str
    :param service_account: The email associated with the service account.
    :type service_account: str
    :param project: The GCP project associated with the service account.
    :type project: str
    """
    sa_istance_name: str = Field(...)
    service_account: str = Field(...)
    project: str = Field(...)
    credentials: SecretStr = Field(...)

    @staticmethod
    def get_istance(sa_istance_name: str) -> 'SASettings':
        """
        Retrieve the Service Account settings instance based on environment configuration.

        :param sa_istance_name: The name of the service account instance.
        :type sa_istance_name: str
        :return: The service account settings.
        :rtype: SASettings
        """
        if "ISP_AMBIENTE" in os.environ and not os.environ[
                'ISP_AMBIENTE'] == ISP_AMBIENTE_LOCAL_ENV_VALUE:
            return SASettings.get_from_isp_datasource(sa_istance_name)
        else:
            return SASettings.get_from_local_env(
                sa_istance_name,
                os.path.join(
                    os.environ["DS_CONF_DIR"] if "DS_CONF_DIR" in os.environ
                    else os.environ["APP_CONF_DIR"], "sa",
                    sa_istance_name.lower(), ".env"))

    @staticmethod
    def get_from_local_env(sa_istance_name: str,
                           env_file_path: str) -> 'SASettings':
        """
        Retrieve the Service Account settings from a local environment file.

        :param sa_istance_name: The name of the service account instance.
        :type sa_istance_name: str
        :param env_file_path: The path to the environment file.
        :type env_file_path: str
        :return: The service account settings.
        :rtype: SASettings
        """
        
        _data = dotenv_values(env_file_path)
        _data_dict = json.loads(_data["credentials"])

        return SASettings(
            sa_istance_name=sa_istance_name,
            service_account=_data_dict['client_email'].split('@')[0],
            project=_data_dict['project_id'],
            credentials=_data['credentials'])

    @staticmethod
    def get_from_isp_datasource(sa_istance_name: str) -> 'SASettings':
        """
        Retrieve the Service Account settings from ISP's datasource.

        :param sa_istance_name: The name of the service account instance.
        :type sa_istance_name: str
        :return: The service account settings.
        :rtype: SASettings
        """

        _data = dotenv_values("/usr/local/.ds/ds-credential.properties")
        _data_dict = json.loads(_data[sa_istance_name])

        return SASettings(
            sa_istance_name=sa_istance_name,
            service_account=_data_dict['client_email'].split('@')[0],
            project=_data_dict['project_id'],
            credentials=_data[sa_istance_name])

class HashicorpEndpoint(str, Enum):
    """
    Enum representing Hashicorp Vault endpoints.
    
    - SYST: System test environment endpoint.
    - PROD: Production environment endpoint.
    """
    SYST = "https://core-verif-licenze-hashicorp-v1-smp00-test.cloudapps.vcptoisp001t.intesasanpaolo.com"
    PROD = "https://core-verif-licenze-hashicorp-v1-smp00-prod.cloudapps.vcptoisp000p.intesasanpaolo.com"


HashicorpServiceAccounts = Literal['sa-isp-bdl10-appl-svil-001','sa-isp-bdl10-appl-test-001','sa-isp-bdl10-appl-prod-001']