import os

from dotenv import dotenv_values
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

from bdlpkg.providers.isp import ISP_AMBIENTE_LOCAL_ENV_VALUE


class DenodoSettings(BaseSettings):
    """
    Settings class for managing Denodo configurations.
    
    This class provides configuration settings for connecting to Denodo Virtual DataPort
    using the PostgreSQL ODBC driver. It supports loading settings either from local 
    environment files or from ISP data sources.

    :param resource_name: The name of the Denodo resource.
    :type resource_name: str
    :param name: The username for the Denodo connection.
    :type name: str
    :param password: The password for the Denodo connection, stored as a SecretStr.
    :type password: SecretStr
    :param hostname: The hostname of the Denodo instance.
    :type hostname: str
    :param port: The port used for the Denodo connection (default is 9996).
    :type port: int
    :param database: The name of the Denodo database.
    :type database: str
    """
    # INFO: https://community.denodo.com/docs/view/document/Virtual%20DataPort/Denodo%205.5/Virtual%20DataPort%20Developer%20Guide
    # we use PostgreSQL ODBC driver -> 3.2.2
    resource_name: str = Field(...)
    name: str = Field(...)
    password: SecretStr = Field(...)
    hostname: str = Field(...)
    port: int = Field(9996)    # default ODBC port
    database: str = Field(...)

    @staticmethod
    def get_istance(resource_name: str) -> 'DenodoSettings':
        """Return the DenodoSettings using available config data

        :param resource_name: the resource name (e.g., BDL)
        :type resource_name: str
        :return: the credential obj
        :rtype: DenodoSettings
        """
        if "ISP_AMBIENTE" in os.environ and not os.environ[
                'ISP_AMBIENTE'] == ISP_AMBIENTE_LOCAL_ENV_VALUE:

            return DenodoSettings.get_from_isp_datasource(resource_name)
        else:
            return DenodoSettings.get_from_local_env(
                resource_name,
                os.path.join(
                    os.environ["DS_CONF_DIR"] if "DS_CONF_DIR" in os.environ
                    else os.environ["APP_CONF_DIR"],
                    "database",
                    "denodo",
                    resource_name.lower(),
                    ".env",
                ),
            )

    @staticmethod
    def get_from_local_env(resource_name: str,
                           env_file_path: str) -> 'DenodoSettings':
        """Return the DenodoSettings using local config data

        :param resource_name: the resource name
        :type resource_name: str
        :param env_file_path: the path where to look at
        :type env_file_path: str
        :return: the credential obj
        :rtype: DenodoSettings
        """
        return DenodoSettings(resource_name=resource_name,
                              _env_file=env_file_path)

    @staticmethod
    def get_from_isp_datasource(resource_name: str) -> 'DenodoSettings':
        """Return the DenodoSettings using ISP config data

        :param resource_name: the resource name
        :type resource_name: str
        :return: the credential obj
        :rtype: DenodoSettings
        """
        _prefix = "DSDENODO_{}_".format(resource_name)
        _data = dotenv_values("/usr/local/.ds/ds-credential.properties")

        return DenodoSettings(
            resource_name=resource_name,
            name=_data[_prefix + "USERNAME"],
            password=_data[_prefix + "PASSWORD"],
            hostname=os.environ[_prefix + "HOSTNAME"],
            port=os.environ[_prefix + "PORT"],
            database=os.environ[_prefix + "DATABASE"],
        )
