from enum import Enum
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class JDBCConnectionType(str, Enum):
    """
    Enum representing the types of JDBC connections available.

    :param teradata: Represents a Teradata JDBC connection.
    :type teradata: str
    """
    teradata = 'teradata'
class JDBCSettings(BaseSettings):
    """
    Settings class for managing JDBC database configurations.

    This class defines the necessary settings for establishing a JDBC connection,
    including the resource name, connection type, host, user credentials, and database name.

    :param resource_name: The name of the resource for the JDBC connection.
    :type resource_name: str
    :param jdbc_connection_type: The type of JDBC connection (e.g., Teradata).
    :type jdbc_connection_type: JDBCConnectionType
    :param jdbc_host: The hostname or IP address of the JDBC database.
    :type jdbc_host: str
    :param jdbc_user: The username for the JDBC connection.
    :type jdbc_user: str
    :param jdbc_password: The password for the JDBC connection, stored as a SecretStr.
    :type jdbc_password: SecretStr
    :param jdbc_db: The name of the JDBC database to connect to.
    :type jdbc_db: str
    """
    resource_name: str = Field(...)
    jdbc_connection_type: JDBCConnectionType = Field(...)
    jdbc_host: str = Field(...)
    jdbc_user: str = Field(...)
    jdbc_password: SecretStr = Field(...)
    jdbc_db: str = Field(...)
