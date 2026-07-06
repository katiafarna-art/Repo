import os

from dotenv import dotenv_values
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

from bdlpkg.providers.isp import ISP_AMBIENTE_LOCAL_ENV_VALUE


class MongoSettings(BaseSettings):
    """
    Settings class for managing MongoDB configurations.

    This class handles the configuration details required for connecting to a MongoDB instance, 
    including the resource name, credentials (username, password), URL, connection pool sizes, 
    and connection timeout. The settings can be loaded from either local environment files or ISP data sources.

    :param resource_name: The name of the MongoDB resource.
    :type resource_name: str
    :param name: The username for the MongoDB connection.
    :type name: str
    :param password: The password for the MongoDB connection, stored as a SecretStr.
    :type password: SecretStr
    :param url: The MongoDB connection URL.
    :type url: str
    :param min_pool_size: The minimum size of the MongoDB connection pool (default is 5).
    :type min_pool_size: int
    :param max_pool_size: The maximum size of the MongoDB connection pool (default is 20).
    :type max_pool_size: int
    :param connection_timeout: The connection timeout in milliseconds (default is 5000).
    :type connection_timeout: int
    """
    resource_name: str = Field(...)
    name: str = Field(...)
    password: SecretStr = Field(...)
    url: str = Field(...)
    min_pool_size: int = 5
    max_pool_size: int = 20
    connection_timeout: int = 5000

    @staticmethod
    def get_istance(resource_name: str) -> 'MongoSettings':
        """Return the MongoSettings using available config data

        :param resource_name: the resource name (e.g., BDL)
        :type resource_name: str
        :return: the credential obj
        :rtype: MongoSettings
        """
        if "ISP_AMBIENTE" in os.environ and not os.environ[
                'ISP_AMBIENTE'] == ISP_AMBIENTE_LOCAL_ENV_VALUE:
            return MongoSettings.get_from_isp_datasource(resource_name)
        else:
            return MongoSettings.get_from_local_env(
                resource_name,
                os.path.join(
                    os.environ["DS_CONF_DIR"] if "DS_CONF_DIR" in os.environ
                    else os.environ["APP_CONF_DIR"], "database", "mongo",
                    resource_name.lower(), ".env"))

    @staticmethod
    def get_from_local_env(resource_name: str,
                           env_file_path: str) -> 'MongoSettings':
        """Return the MongoSettings using local config data

        :param resource_name: the resource name
        :type resource_name: str
        :param env_file_path: the path where to look at
        :type env_file_path: str
        :return: the credential obj
        :rtype: MongoSettings
        """
        return MongoSettings(resource_name=resource_name,
                             _env_file=env_file_path)

    @staticmethod
    def get_from_isp_datasource(resource_name: str) -> 'MongoSettings':
        """Return the MongoSettings using ISP config data

        :param resource_name: the resource name
        :type resource_name: str
        :return: the credential obj
        :rtype: MongoSettings
        """

        _prefix = "DSMONGO_{}_".format(resource_name)
        _data = dotenv_values("/usr/local/.ds/ds-credential.properties")

        _prefix_url = "" if os.environ[_prefix + "URL"].startswith(
            "mongo") else "mongodb://"

        return MongoSettings(
            resource_name=resource_name,
            name=_data[_prefix + "USERNAME"],
            password=_data[_prefix + "PASSWORD"],
            url=_prefix_url + os.environ[_prefix + "URL"],
            min_pool_size=os.environ[_prefix + "MIN_POOL_SIZE"],
            max_pool_size=os.environ[_prefix + "MAX_POOL_SIZE"],
            connection_timeout=os.environ[_prefix + "CONNECTION_TIMEOUT"])
