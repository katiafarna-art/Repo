import os
from pydantic import Field
from pydantic_settings import BaseSettings

from bdlpkg.providers.isp import ISP_AMBIENTE_LOCAL_ENV_VALUE

class KafkaSettings(BaseSettings):
    """
    Configuration class for Kafka producer and consumer instances, performed by providing a dict of configuration properties to the instance constructor.

    This class handles the configuration details required to create and manage Kafka instances,
    such as brokers, security settings, service names, and Kerberos authentication. It supports
    loading configurations from both local environment files and ISP data sources.

    :param resource_name: The name of the resource for the Kafka instance.
    :type resource_name: str
    :param principal: The principal used for Kerberos authentication (in the format username@real_domain).
    :type principal: str
    :param file_path: The file path to the Kerberos keytab file.
    :type file_path: str
    :param brokers: A string containing the Kafka broker addresses.
    :type brokers: str
    :param security_protocol: The security protocol used by Kafka (e.g., "SASL_SSL").
    :type security_protocol: str
    :param service_name: The Kafka service name used in Kerberos authentication.
    :type service_name: str
    :param session_timeout: The timeout for the Kafka session, in milliseconds (default is 45000).
    :type session_timeout: int
    :param mechanisms: The SASL mechanism used for authentication (default is "GSSAPI").
    :type mechanisms: str
    """
    resource_name: str = Field(...)
    principal : str = Field(...)         ## username@real_domain
    file_path : str = Field(...)
    brokers : str = Field(...)
    security_protocol : str = Field(...)
    service_name : str = Field(...)
    session_timeout: int = Field(45000)
    mechanisms: str = Field("GSSAPI")

    @staticmethod
    def get_istance(resource_name: str) -> 'KafkaSettings':
        """
        Retrieve a KafkaSettings instance using the available configuration data.

        This method checks the environment to decide whether to load settings from ISP data sources
        or from local environment files.

        :param resource_name: The name of the Kafka resource.
        :type resource_name: str
        :return: A KafkaSettings instance populated with the relevant configuration.
        :rtype: KafkaSettings
        """
        if "ISP_AMBIENTE" in os.environ and not os.environ[
                'ISP_AMBIENTE'] == ISP_AMBIENTE_LOCAL_ENV_VALUE:
            return KafkaSettings.get_from_isp_datasource(resource_name)
        else:
            return KafkaSettings.get_from_local_env(
                resource_name,
                os.path.join(
                    os.environ["DS_CONF_DIR"] if "DS_CONF_DIR" in os.environ
                    else os.environ["APP_CONF_DIR"], "messaging", "kafka",
                    resource_name.lower(), ".env"))
       
    @staticmethod
    def get_from_local_env(resource_name: str,
                           env_file_path: str) -> 'KafkaSettings':
        """
        Retrieve KafkaSettings using local environment configuration.

        This method reads from a local `.env` file to load the Kafka configuration details.

        :param resource_name: The name of the Kafka resource.
        :type resource_name: str
        :param env_file_path: The path to the local environment file.
        :type env_file_path: str
        :return: A KafkaSettings instance populated with local configuration.
        :rtype: KafkaSettings
        """
        return KafkaSettings(resource_name=resource_name,
                             _env_file=env_file_path)
    
    @staticmethod
    def get_from_isp_datasource(resource_name: str) -> 'KafkaSettings':
        """
        Retrieve KafkaSettings using ISP data sources.

        This method loads the Kafka configuration from predefined ISP environment variables, including
        Kerberos authentication details and broker settings.

        :param resource_name: The name of the Kafka resource.
        :type resource_name: str
        :return: A KafkaSettings instance populated with ISP configuration.
        :rtype: KafkaSettings
        """
        _keytab_prefix = "KEYTAB_{}_".format(resource_name)+"KERB_"
        _kafka_prefix = "KAFKA_{}_".format(resource_name)
        return KafkaSettings(
            resource_name = resource_name,
            principal = f"{os.environ[_keytab_prefix + 'USERNAME']}@{os.environ[_keytab_prefix + 'REALM_DOMAIN']}",            
            file_path = os.environ[_keytab_prefix + "FILE_PATH"],
            brokers = os.environ[_kafka_prefix + "BROKERS"],
            security_protocol = os.environ[_kafka_prefix + "SECURITY_PROTOCOL"],
            service_name = os.environ[_kafka_prefix + "SERVICE_NAME"])



