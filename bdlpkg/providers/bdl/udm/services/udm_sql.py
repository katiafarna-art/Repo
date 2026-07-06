from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDataEngine, UDMDataType
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4MongoTypes
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4SqlTypes_denodo
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4SqlTypes_oracle
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4SqlTypes_postgres
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4SqlTypes_teradata
from bdlpkg.providers.bdl.udm.services.utils import _get_args
import pandas as pd
from typing import Dict, Any, Optional
from sqltree.tools import get_tables


def get_db_client(db_type: str,
                  db_istance_name: Optional[str] = None) -> object:
    """
    Retrieve the appropriate database client based on the database type and instance name.

    This function returns a client or connection to the specified database type. It supports multiple database types 
    such as MongoDB, Denodo, Oracle, Postgres, and Teradata.

    :param db_type: The type of the database (e.g., MongoDB, Denodo, Oracle, etc.).
    :type db_type: str
    :param db_istance_name: Optional. The name of the database instance. Defaults to None.
    :type db_istance_name: Optional[str]
    :return: The database client or connection object.
    :rtype: object
    :raises NotImplementedError: If the database type is not supported.
    """
    if db_type in _get_args(UDMDM4MongoTypes):
        from bdlpkg.providers.isp.databases.services.mongodb import get_mongo_client
        return get_mongo_client(db_istance_name)
    elif db_type in _get_args(UDMDM4SqlTypes_denodo):
        from bdlpkg.providers.isp.databases.services.denodo import get_denodo_connection
        return get_denodo_connection(db_istance_name)
    elif db_type in _get_args(UDMDM4SqlTypes_oracle):
        from bdlpkg.providers.isp.databases.services.oracledb import get_oracle_client
        return get_oracle_client(db_istance_name)
    elif db_type in _get_args(UDMDM4SqlTypes_postgres):
        from bdlpkg.providers.isp.databases.services.postgresdb import get_postgres_connection
        return get_postgres_connection(db_istance_name)
    elif db_type in _get_args(UDMDM4SqlTypes_teradata):
        from bdlpkg.providers.isp.databases.services.teradata import get_teradata_connection
        return get_teradata_connection(db_istance_name)
    else:
        raise NotImplementedError(f"no client available for db type {db_type}")


def _read_sql_pandas_df(istance_name: str, request: dict,
                        **kwargs: Dict[str, Any]) -> pd.DataFrame:
    """
    Read SQL query results and return them as a Pandas DataFrame.

    This function executes the SQL statement provided in the `request` and returns the result as a Pandas DataFrame.
    It supports passing additional parameters for SQL execution.

    :param istance_name: The name of the database instance.
    :type istance_name: str
    :param request: A dictionary containing the SQL statement to execute.
    :type request: dict
    :return: A Pandas DataFrame containing the SQL query result.
    :rtype: pd.DataFrame
    """
    _params = None

    if "params" in kwargs:
        _params = kwargs["params"]

    return pd.read_sql(sql=request["statement"],
                       con=get_db_client(request["udmdm_type"], istance_name),
                       params=_params)


def _write_sql_pandas_df(istance_name: str, request: dict, df: object,
                         **kwargs: Dict[str, Any]) -> None:
    """
    Placeholder function for writing a Pandas DataFrame to a SQL database.

    This function is not yet implemented and serves as a placeholder for future implementation.

    :param istance_name: The name of the database instance.
    :type istance_name: str
    :param request: A dictionary containing the SQL details.
    :type request: dict
    :param df: The Pandas DataFrame to be written to the database.
    :type df: object
    """
    pass


def _read_sql(istance_name: str,
              request: dict,
              output_type: UDMDataType = UDMDataType.DF,
              engine: UDMDataEngine = UDMDataEngine.PANDAS,
              **kwargs: Dict[str, Any]) -> pd.DataFrame:
    """
    Read data from a SQL database and return it as a Pandas DataFrame or other supported format.

    This function executes the SQL query specified in the `request` and returns the result as a Pandas DataFrame
    or other supported format, depending on the engine and output type.

    :param istance_name: The name of the database instance.
    :type istance_name: str
    :param request: A dictionary containing the SQL statement to execute.
    :type request: dict
    :param output_type: The type of data output (default is UDMDataType.DF for DataFrame).
    :type output_type: UDMDataType
    :param engine: The engine to be used for reading (default is UDMDataEngine.PANDAS).
    :type engine: UDMDataEngine
    :return: The query result as a Pandas DataFrame.
    :rtype: pd.DataFrame
    :raises NotImplementedError: If the output type or engine is not supported.
    """
    if output_type == UDMDataType.DF:
        if engine == UDMDataEngine.PANDAS:
            return _read_sql_pandas_df(istance_name, request, **kwargs)
        else:
            raise NotImplementedError(
                f"engine {engine} not implemented for sql")
    else:
        raise NotImplementedError(
            f"output_type {output_type} not implemented for sql")


def _write_sql(istance_name: str,
               request: dict,
               data: object,
               input_type: UDMDataType = UDMDataType.DF,
               engine: UDMDataEngine = UDMDataEngine.PANDAS,
               **kwargs: Dict[str, Any]) -> None:
    """
    Write data to a SQL database from a Pandas DataFrame or other supported format.

    This function writes data to a SQL database based on the specified input type and engine.
    Currently, only writing Pandas DataFrames is supported.

    :param istance_name: The name of the database instance.
    :type istance_name: str
    :param request: A dictionary containing the SQL details.
    :type request: dict
    :param data: The data to be written (as a DataFrame).
    :type data: object
    :param input_type: The type of input data (default is UDMDataType.DF for DataFrame).
    :type input_type: UDMDataType
    :param engine: The engine to be used for writing (default is UDMDataEngine.PANDAS).
    :type engine: UDMDataEngine
    :raises NotImplementedError: If the input type or engine is not supported.
    """
    if input_type == UDMDataType.DF:
        if engine == UDMDataEngine.PANDAS:
            _write_sql_pandas_df(istance_name, request, data, **kwargs)
        else:
            raise NotImplementedError(
                f"engine {engine} not implemented for sql")
    else:
        raise NotImplementedError(
            f"input_type {input_type} not implemented for sql")


def _tables_available(db_type: str, db_istance_name: str,
                      request: dict) -> bool:
    """
    Check if the requested tables are available in the specified database.

    This function performs a health check to determine if the requested tables exist in the database
    for supported database types such as Denodo, Oracle, and Postgres.

    :param db_type: The type of the database (e.g., Denodo, Oracle, Postgres).
    :type db_type: str
    :param db_istance_name: The name of the database instance.
    :type db_istance_name: str
    :param request: A dictionary containing the SQL statement or query.
    :type request: dict
    :return: True if the tables are available, False otherwise.
    :rtype: bool
    :raises ConnectionError: If the database cannot be connected.
    :raises NotImplementedError: If the table listing is not implemented for the database type.
    """
    if db_type in _get_args(UDMDM4SqlTypes_denodo):
        from bdlpkg.providers.isp.databases.services.denodo import get_denodo_healthcheck
        _res = get_denodo_healthcheck(db_istance_name)
        if _res["online"]:
            return all(view in _res["views"]
                       for view in get_tables(request['statement']))
        else:
            raise ConnectionError(f"cannot connect to {db_type} db")

    elif db_type in _get_args(UDMDM4SqlTypes_oracle):
        from bdlpkg.providers.isp.databases.services.oracledb import get_oracle_healthcheck
        _res = get_oracle_healthcheck(db_istance_name)
        if "Tabelle" in _res:
            return all(table in _res["Tabelle"]
                       for table in get_tables(request['statement']))
        else:
            raise ConnectionError(f"cannot connect to {db_type} db")
        
    elif db_type in _get_args(UDMDM4SqlTypes_postgres):
        from bdlpkg.providers.isp.databases.services.postgresdb import get_postgres_healthcheck
        _res = get_postgres_healthcheck(db_istance_name)
        if "collections" in _res:
            schema_tables = [f'{schema}.{item}' for schema in _res['schemas'] for item in _res['collections'][schema]]
            return all(table in schema_tables
                       for table in get_tables(request['statement']))
        else:
            raise ConnectionError(f"cannot connect to {db_type} db")
    else:
        #L'healthcheck restituisce solo un timestamp. Non essendoci use cases che richiamano teradata lasciamo stare questo pezzo,
        #in quanto richiederebbe modifica all'healthcheck per arricchirlo con elenco delle tabelle presenti nel db
        #https://dataedo.com/kb/query/teradata/list-all-tables-in-all-databases
        raise NotImplementedError(
            f"list tables not implemented for {db_type} db")
