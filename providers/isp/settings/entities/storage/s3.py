import os
from typing import Union

from dotenv import dotenv_values
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

from bdlpkg.providers.isp import ISP_AMBIENTE_LOCAL_ENV_VALUE
from bdlpkg.utils.bdlfile.entities.annotated import HttpUrl


class BaseS3BucketSettings(BaseSettings):
    """
    Base class for S3 bucket settings.
    Handles common configuration fields and validation.
    """
    resource_name: str = Field(...)
    secret_access_key: SecretStr = Field(...)
    access_key_id: str = Field(...)
    bucket_name: str = Field(...)
    

class S3BucketSettings(BaseS3BucketSettings):
    endpoint_url: HttpUrl = Field("http://ecs.intesasanpaolo.com:9020")
    verify_ssl_cert: Union[str, bool] = Field(True)


class S3GSSBucketSettings(BaseS3BucketSettings):
    endpoint_url: HttpUrl = Field("https://ecs.intesasanpaolo.com:9021")
    #verify_ssl_cert: Union[str, bool] = Field(False)
    verify_ssl_cert: Union[str, bool] = Field('/etc/ssl/certs/ca-bundle.crt')

    @staticmethod
    def get_istance(resource_name: str) -> 'S3GSSBucketSettings':
        """Return the S3GSSBucketSettings using available config data

        :param resource_name: the resource name (e.g., BDL)
        :type resource_name: str
        :return: the credential obj
        :rtype: S3GSSBucketSettings
        """
        if "ISP_AMBIENTE" in os.environ and not os.environ[
                'ISP_AMBIENTE'] == ISP_AMBIENTE_LOCAL_ENV_VALUE:
            return S3GSSBucketSettings.get_from_isp_datasource(resource_name)
        else:
            return S3GSSBucketSettings.get_from_local_env(
                resource_name,
                os.path.join(
                    os.environ["DS_CONF_DIR"] if "DS_CONF_DIR" in os.environ
                    else os.environ["APP_CONF_DIR"], "bucket",
                    resource_name.lower(), ".env"))
        
    @staticmethod
    def get_from_local_env(resource_name: str,
                           env_file_path: str) -> 'S3GSSBucketSettings':
        """Return the S3GSSBucketSettings using local config data

        :param resource_name: the resource name
        :type resource_name: str
        :param env_file_path: the path where to look at
        :type env_file_path: str
        :return: the credential obj
        :rtype: S3GSSBucketSettings
        """
        return S3GSSBucketSettings(resource_name=resource_name,
                                   _env_file=env_file_path)

    @staticmethod
    def get_from_isp_datasource(resource_name: str) -> 'S3GSSBucketSettings':
        """Return the S3GSSBucketSettings using ISP config data

        :param resource_name: the resource name
        :type resource_name: str
        :return: the credential obj
        :rtype: S3GSSBucketSettings
        """

        _data = dotenv_values("/usr/local/.ds/ds-credential.properties")

        return S3GSSBucketSettings(
            resource_name=resource_name,
            secret_access_key=_data["S3_SECRET_KEY"],
            access_key_id=os.environ["S3_ACCESS_KEY"],
            endpoint_url=os.environ["S3_CONNECTION_URI"],
            bucket_name=os.environ["S3_BUCKET_NAME"],
            verify_ssl_cert='/etc/ssl/certs/ca-bundle.crt')