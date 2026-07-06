from dotenv import dotenv_values
from bdlpkg.providers.isp import ISP_AMBIENTE_LOCAL_ENV_VALUE
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings
from typing import Literal
import os


class PostgresSettings(BaseSettings):
    """
    Settings class for managing PostgreSQL configurations.

    This class handles the configuration details required for connecting to a PostgreSQL database instance,
    including resource name, credentials (username, password), URL, connection pool size, and connection timeout.
    The settings can be loaded from either local environment files or ISP data sources.

    :param resource_name: The name of the PostgreSQL database resource.
    :type resource_name: str
    :param name: The username for the PostgreSQL connection.
    :type name: str
    :param password: The password for the PostgreSQL connection, stored as a SecretStr.
    :type password: SecretStr
    :param url: The PostgreSQL connection URL.
    :type url: str
    :param connection_pool_size: The size of the PostgreSQL connection pool (default is 5).
    :type connection_pool_size: int
    :param connection_timeout: The connection timeout in milliseconds (default is 10000).
    :type connection_timeout: int
    """
    resource_name: str = Field(...)
    name: str = Field(...)
    password: SecretStr = Field(...)
    url: str = Field(...)
    connection_pool_size: int = 5
    connection_timeout: int = 10000


    @staticmethod
    def get_istance(resource_name: str) -> 'PostgresSettings':
        """Return the PostgresSettings using available config data

        :param resource_name: the resource name (e.g., BDL)
        :type resource_name: str
        :return: the credential obj
        :rtype: PostgresSettings
        """
        if "ISP_AMBIENTE" in os.environ and not os.environ[
                'ISP_AMBIENTE'] == ISP_AMBIENTE_LOCAL_ENV_VALUE:
            return PostgresSettings.get_from_isp_datasource(resource_name)
        else:
            return PostgresSettings.get_from_local_env(
                resource_name,
                os.path.join(
                    os.environ["DS_CONF_DIR"] if "DS_CONF_DIR" in os.environ
                    else os.environ["APP_CONF_DIR"], "database", "postgres",
                    resource_name.lower(), ".env"))
    

    @staticmethod
    def get_from_local_env(resource_name: str,
                           env_file_path: str) -> 'PostgresSettings':
        """Return the PostgresSettings using local config data

        :param resource_name: the resource name
        :type resource_name: str
        :param env_file_path: the path where to look at
        :type env_file_path: str
        :return: the credential obj
        :rtype: PostgresSettings
        """
        return PostgresSettings(resource_name=resource_name,
                             _env_file=env_file_path)


    @staticmethod
    def get_from_isp_datasource(resource_name: str) -> 'PostgresSettings':
        """Return the PostgresSettings using ISP config data

        :param resource_name: the resource name
        :type resource_name: str
        :return: the credential obj
        :rtype: PostgresSettings
        """

        _prefix = "DSPOSTGRESQL_{}_".format(resource_name)
        _data = dotenv_values("/usr/local/.ds/ds-credential.properties")

        _url = os.environ[_prefix + "URL"].split('://')[1] if os.environ[
            _prefix + "URL"].startswith("jdbc:edb") else os.environ[_prefix + 
                                                                    "URL"]

        return PostgresSettings(
            resource_name=resource_name,
            name=_data[_prefix + "USERNAME"],
            password=_data[_prefix + "PASSWORD"],
            url=_url,
            connection_pool_size=os.environ[_prefix + "CONNECTION_POOL_SIZE"],
            connection_timeout=os.environ[_prefix + "CONNECTION_TIMEOUT"])
    

PostgresSessionAttr = Literal["any", "read-write", "read-only", "primary", "standby", "prefer-standby"]