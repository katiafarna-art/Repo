from bdlpkg.providers.isp.settings.services.isp_config import get_datasource_settings
from bdlpkg.providers.isp.settings.entities.database.postgres import PostgresSettings, PostgresSessionAttr
from bdlpkg.providers.bdl.udm.services.utils import _get_args
import sqlalchemy
from sqlalchemy import inspect
from sqlalchemy.engine.url import URL
from sqlalchemy.engine.base import Connection
from typing import Optional, Literal
import logging


def get_postgres_connection(postgres_istance_name: Optional[str] = None,
                            target_session_attr: str = "read-write") -> Connection:
    """Return a Connection object to handle connection to Postgres 

    :param postgres_istance_name: istance name used in 'configuration.yml' to define the mounted secret, defaults to None (the first)
    :type postgres_istance_name: str, optional
    :param target_session_attr: his option determines whether the session must have certain properties to be acceptable.
        https://www.postgresql.org/docs/current/libpq-connect.html
        It's typically used in combination with multiple host names to select the first acceptable alternative among several hosts. There are six modes:
            - any: any successful connection is acceptable
            - read-write (default): session must accept read-write transactions by default (that is, the server must not be in hot standby mode and the default_transaction_read_only parameter must be off)
            - read-only: session must not accept read-write transactions by default (the converse)
            - primary: server must not be in hot standby mode
            - standby: server must be in hot standby mode
            - prefer-standby: first try to find a standby server, but if none of the listed hosts is a standby server, try again in any mode
    :type target_session_attr: str
    :return: the Postgres connector
    :rtype: Connection
    """
    pi: PostgresSettings = get_datasource_settings("database", "postgres", postgres_istance_name)
    
    if target_session_attr in _get_args(PostgresSessionAttr):
        pg_url = __compose_url(pi.url, pi.name, pi.password, target_session_attr)
        engine = sqlalchemy.create_engine(pg_url)
        return Connection(engine)
    else: 
        raise ConnectionRefusedError(f"{target_session_attr} not available for Postgres connection")


def get_postgres_healthcheck(postgres_istance_name: Optional[str] = None) -> dict:
    """Healtcheck for Postgres

    :param postgres_istance_name: Postgres istance to test, defaults to None
    :type postgres_istance_name: str, optional
    :return: a dict with the result of connection tests
    :rtype: dict
    """
    try: 
        _engine = get_postgres_connection(postgres_istance_name)
        inspector = inspect(_engine)
        _schemas = inspector.get_schema_names()
        _collections = {}
        for schema in _schemas:
            _collections[schema] = inspector.get_table_names(schema=schema)

        result = {"schemas": _schemas, "collections": _collections}
    except Exception as e:
        result = {
            "online": False,
            "message": "Failed with uncaught exception 🥦 " + str(e) + " 🥦",
        }

    return result


def __compose_url(url: str, db_user: str, db_pass: str, attributes: str) -> URL:
    """Compose the URL for PostgreSQL connection.

    :param url: A string containing the host(s) and port(s) information.
    :type url: str
    :param db_user: The username for the database connection.
    :type db_user: str
    :param db_pass: The password for the database connection.
    :type db_pass: str (SecretStr or similar object)
    :param attributes: Connection attributes, like target session settings.
    :type attributes: str
    :return: A URL object for the PostgreSQL database connection.
    :rtype: URL
    """
    hosts = []
    ports = []
    drivername = "postgresql"
    database_name = None
    try:
        tokens = url.split(",")
        for tk in tokens:
            if not "?" in tk:
                host, port = tk.split(":")
                hosts.append(host)
                ports.append(port)
            else:
                first, last = tk.split("/")
                host, port = first.split(":")
                hosts.append(host)
                ports.append(port)
                database_name = last.split("?")[0]
            
        query = {'host': ','.join(hosts), 'port': ','.join(ports), 'target_session_attrs': attributes}

        url = URL.create(drivername=drivername,
                         username=db_user,
                         password=db_pass.get_secret_value(),
                         database=database_name,
                         query=query)
        return url
    except Exception as ex:
        logging.error("Exception occurred in " + str(ex))
        return ""