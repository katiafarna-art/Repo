from typing import Optional
from bdlpkg.providers.isp.settings.services.isp_config import get_datasource_settings
from bdlpkg.providers.isp.settings.entities.database.denodo import DenodoSettings
from socket import gethostname
import logging

import sqlalchemy
from sqlalchemy.engine.url import URL
from sqlalchemy.engine.base import Connection

def get_denodo_connection(
        denodo_istance_name: Optional[str] = None) -> Connection:
    """
    Return a client to the denodo istance - we use a PostgreSQL like ODBC driver.
    
    .. code-block::
      :linenos:
      :caption: usage
    
      from bdlpkg.provider.isp.databases.services.denodo import get_denodo_connection
      with get_denodo_connection() as _connection: # autoclose
          _connection.execute(query)
          columns = [column[0] for column in _cur.description]
          for row in _cur:
              # do something
  
    .. code-block::
      :linenos:
      :caption: Pandas example (remember to limit the query)
    
      import pandas as pd
      from provider.isp.databases.services.denodo import get_denodo_connection
      paramList = [] # list of parameters (if query contains `?`, e. g., SELECT * FROM TABLE where `FIELD` = ?)
      dfOut = None
      with get_denodo_connection() as _connection:  # autoclose
          dfOut = pd.read_sql(query, con=_connection, params=paramList)
      df.info()

    :param denodo_istance_name: The name used in `configuration.yml`. Default: the first alphabetically, defaults to None
    :type denodo_istance_name: str, optional
    :return: the connection object (None if error occurs). Remember to close the connection (remember to close it!):
            obj_connection.close()
    :rtype: sqlalchemy.engine.base.Connection
    """    

    denodo_settings: DenodoSettings = get_datasource_settings("database", "denodo", denodo_istance_name)
    
    dn_url = __compose_url(denodo_settings.hostname, denodo_settings.port, denodo_settings.database, 
                           denodo_settings.name, denodo_settings.password)
    obj_connection = None
    try:
        engine = sqlalchemy.create_engine(dn_url)
        obj_connection = Connection(engine)

    except Exception as e:
        logging.error(
            "Exception while trying to connect to Denodo. {}".format(e))
    return obj_connection


def get_denodo_healthcheck(denodo_istance_name: Optional[str] = None) -> dict:
    """Healtcheck for Denodo

    :param denodo_istance_name: Denodo istance to test (None = first), defaults to None
    :type denodo_istance_name: str, optional
    :return: a dict with the result of connection tests
    :rtype: dict
    """
    str_query_timestamp = "SELECT NOW() FROM DUAL()"
    str_query_databases = "LIST DATABASES"
    str_query_views = "LIST VIEWS"

    _connection = get_denodo_connection(denodo_istance_name)
    if _connection == None:
        return {"online": False, "timestamp": "Connection is None!"}
    try:
        # this is a cursor that become a set of rows
        db_res = _connection.execute(str_query_timestamp).fetchall()
        tmstmp = db_res[0][0].strftime("%Y-%m-%d %H:%M:%S")

        db_res = _connection.execute(str_query_databases).fetchall()
        _dbs = [x[0] for x in db_res]

        db_res = _connection.execute(str_query_views).fetchall()
        _views = [x[0] for x in db_res]

        result = {
            "online": True,
            "timestamp": f"Database online. TIMESTAMP (Denodo): {tmstmp}.",
            "databases": _dbs,
            "views": _views,
        }
    except Exception as e:
        result = {
            "online": False,
            "timestamp": "Failed with uncaught exception 🥦 " + str(e) + " 🥦",
        }
    finally:
        _connection.close()

    return result


def __compose_url(db_host: str, db_port: int, db_name: str, db_user: str, db_pass: str) -> URL:
    """Compose the URL for Denodo connection.

    :param db_host: The database host.
    :type db_host: str
    :param db_port: The port number of the database.
    :type db_port: int
    :param db_name: The name of the database.
    :type db_name: str
    :param db_user: The username for the database connection.
    :type db_user: str
    :param db_pass: The password for the database connection.
    :type db_pass: str (SecretStr or similar object)
    :return: A URL object for the Denodo database connection.
    :rtype: URL
    """
    drivername= "denodo"
    try:
        url = URL.create(drivername=drivername,
                        username=db_user,
                        password=db_pass.get_secret_value(),
                        database=db_name,
                        host=db_host,
                        port=db_port)
        return url
    except Exception as ex:
        logging.error("Exception occurred in " + str(ex))
        return ""
