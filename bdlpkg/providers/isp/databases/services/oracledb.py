import logging
from http import client
from typing import Any, Optional

import sqlalchemy
from sqlalchemy.engine.base import Connection
from sqlalchemy.engine.url import URL

from bdlpkg.providers.isp.settings.entities.database.oracle import \
    OracleSettings
from bdlpkg.providers.isp.settings.services.isp_config import \
    get_datasource_settings


def get_oracle_client(oracle_istance_name: Optional[str] = None) -> Connection:
    """Return an object to handle connection to Oracle 

    :param oracle_istance_name: istance name used in 'configuration.yml' to define the mounted secret, defaults to None (the first)
    :type oracle_istance_name: str, optional
    :return: the Oracle client
    :rtype: sqlalchemy.engine.base.Connection
    """
    oi: OracleSettings = get_datasource_settings("database", "oracle",
                                                 oracle_istance_name)
    dsn_split = oi.url.split("@")
    dsn = dsn_split[0] if len(dsn_split) == 1 else dsn_split[1]
    or_url = __compose_url(dsn, oi.name, oi.password)

    obj_connection = None
    try:
        engine = sqlalchemy.create_engine(or_url)
        obj_connection = Connection(engine)

    except Exception as e:
        logging.error(
            "Exception while trying to connect to Oracle. {}".format(e))
    return obj_connection


def get_oracle_healthcheck(oracle_istance_name: Optional[str] = None) -> dict:
    """Healtcheck for Oracle

    :param oracle_istance_name: Oracle istance to test, defaults to None
    :type oracle_istance_name: str, optional
    :return: a dict with the result of connection tests
    :rtype: dict
    """
    oi: OracleSettings = get_datasource_settings("database", "oracle",
                                                 oracle_istance_name)

    result: dict = {}
    _client: Any = None

    try:
        _client = get_oracle_client(oracle_istance_name)
        str_qry = "select table_name from all_tables where upper(owner) = '{}'".format(
            oi.name.replace("APP", "OWN").upper())
        _rs = _client.execute(str_qry).fetchall()
        _tables = [x[0] for x in _rs]

        result["Tabelle"] = _tables

    except Exception as e:
        result["Error"] = "{}".format(e)

    finally:
        if _client is not None:
            _client.close()

    return result


def __compose_url(dsn: str, db_user: str, db_pass: str) -> URL:
    """Compose the URL for Oracle connection.

    :param dsn: The database Data Source Name.
    :type dsn: str
    :param db_user: The username for the database connection.
    :type db_user: str
    :param db_pass: The password for the database connection.
    :type db_pass: str (SecretStr or similar object)
    :return: A URL object for the Oracle database connection.
    :rtype: URL
    """
    drivername = "oracle"
    try:
        if "/" in dsn:
            url, db_name = dsn.split("/")
            db_host, db_port = url.split(":")
            url = URL.create(drivername=drivername,
                             username=db_user,
                             password=db_pass.get_secret_value(),
                             database=db_name,
                             host=db_host,
                             port=db_port)
        else:
            url = URL.create(drivername=drivername,
                             username=db_user,
                             password=db_pass.get_secret_value(),
                             host=dsn)
        return url
    except Exception as ex:
        logging.error("Exception occurred in " + str(ex))
        return ""