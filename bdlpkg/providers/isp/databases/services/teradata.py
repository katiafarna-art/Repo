import logging
from typing import Optional

import sqlalchemy
from sqlalchemy.engine.base import Connection
from sqlalchemy.engine.url import URL

from bdlpkg.providers.isp.settings.entities.jdbc.jdbc import (
    JDBCConnectionType, JDBCSettings)
from bdlpkg.providers.isp.settings.services.isp_config import (
    get_datasource_settings, get_settings)


def get_teradata_connection(
    jdbc_istance_name: Optional[str] = None,
) -> Connection:
    """Return a connection to Teradata following Python Database API Specification 2.0.
        apilevel = "2.0"
        threadsafety = 2: Threads may share the module and connections. (not cursor!)
        paramstyle = 'qmark': Question mark style, e.g. ...WHERE name=? (like `denodo`)

    Further info on [Teradata's github](https://github.com/Teradata/python-driver)

    :param jdbc_istance_name: istance name used to define the mounted secret, defaults to None (the first)
    :type jdbc_istance_name: str, optional
    :return: the connector that follows DBAPI 2.0 (use `with`)
    :rtype: sqlalchemy.engine.base.Connection
    """

    teradata_settings: JDBCSettings = get_datasource_settings(
        "jdbc", "teradata", jdbc_istance_name
    )

    if teradata_settings.jdbc_connection_type is not JDBCConnectionType.teradata:
        raise TypeError(
            f" {teradata_settings.resource_name} is not a Teradata connection!"
        )

    td_url = __compose_url(teradata_settings.jdbc_host, teradata_settings.jdbc_db, 
                           teradata_settings.jdbc_user, teradata_settings.jdbc_password)
    
    obj_connection = None
    try:
        engine = sqlalchemy.create_engine(td_url)
        obj_connection = Connection(engine)
    except Exception as e:
        logging.error(
            "Exception while trying to connect to Teradata. {}".format(e))
    return obj_connection


def get_teradata_healthcheck(jdbc_istance_name: Optional[str] = None) -> dict:
    """Healtcheck for Teradata

    :param jdbc_istance_name: istance name used to define secret, defaults to None
    :type jdbc_istance_name: Optional[str], optional
    :return: Teradata's version
    :rtype: dict
    """

    # query: str = "SELECT CURRENT_TIMESTAMP AT LOCAL;"  # https://docs.teradata.com/r/kmuOwjp1zEYg98JsB8fu_A/5vnsnjwk8vS0VDvoRF7oMQ
    query: str = (
        "SELECT CURRENT_TIMESTAMP AT LOCAL;"
    )
    result = {}
    try:
        with get_teradata_connection(jdbc_istance_name) as _conn:
            rows = _conn.execute(query).fetchall()
            tmstmp = rows[0][0].strftime("%Y-%m-%d %H:%M:%S")
            # columns = _cur.description[0][0]
            result["Timestamp"] = tmstmp
    except Exception as e:
        result["Error"] = "{}".format(e)

    return result


def __compose_url(db_host: str, db_name: str, db_user: str, db_pass: str) -> URL:
    """Compose the URL for Teradata connection.

    :param db_host: The database host.
    :type db_host: str
    :param db_name: The name of the database.
    :type db_name: str
    :param db_user: The username for the database connection.
    :type db_user: str
    :param db_pass: The password for the database connection.
    :type db_pass: str (SecretStr or similar object)
    :return: A URL object for the Teradata database connection.
    :rtype: URL
    """
    drivername= "teradatasql"
    try:
        url = URL.create(drivername=drivername,
                        username=db_user,
                        password=db_pass.get_secret_value(),
                        database=db_name,
                        host=db_host)
        return url
    except Exception as ex:
        logging.error("Exception occurred in " + str(ex))
        return ""
