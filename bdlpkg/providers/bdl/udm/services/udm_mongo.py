import pandas as pd
import os, logging
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDataEngine, UDMDataType
from bdlpkg.providers.isp.databases.services.mongodb import get_mongo_client
from bdlpkg.providers.isp import ISP_AMBIENTE_LOCAL_ENV_VALUE
from typing import Optional
"""
TODO:
    - projection: aggiungi questo parametro per fare il dizionario dei projection [DONE]
    - lista dinamica con sostituzione di keyword nel dizionario di mongo (gli passo la variabile da python) - per ora puoi modificare la richiesta... 
    - gestione rimozioni indici: per ora drop_index e inplace sono dei parametri da mandare [TO BE DISCUSSED]
"""


def _read_mongo_pandas_df(mongo_istance_name: str,
                          request: dict) -> pd.DataFrame:
    """
    Read data from a MongoDB collection and return it as a Pandas DataFrame.

    This function connects to a MongoDB instance and retrieves data from the specified collection 
    based on the query and projection provided in the `request` dictionary.

    :param mongo_istance_name: The name of the MongoDB instance.
    :type mongo_istance_name: str
    :param request: A dictionary containing the collection name, query, and projection.
    :type request: dict
    :return: A Pandas DataFrame containing the retrieved data.
    :rtype: pd.DataFrame
    """

    _client = get_mongo_client(mongo_istance_name)
    cursor = _client[_client.list_database_names()[0]][
        request['collection']].find(request['query'], request['projection'])
    return pd.DataFrame(list(cursor))


def _write_mongo_pandas_df(mongo_istance_name: str,
                           request: dict,
                           df: pd.DataFrame,
                           drop_index: Optional[bool] = True,
                           inplace: Optional[bool] = True) -> None:
    """
    Write data from a Pandas DataFrame into a MongoDB collection.

    This function inserts data from the provided DataFrame into the specified MongoDB collection. 
    The DataFrame can be written in place or a temporary copy can be created. The index can also 
    be dropped before insertion.

    :param mongo_istance_name: The name of the MongoDB instance.
    :type mongo_istance_name: str
    :param request: A dictionary containing the collection name and projection.
    :type request: dict
    :param df: The Pandas DataFrame containing the data to be inserted.
    :type df: pd.DataFrame
    :param drop_index: Whether to drop the index when writing the data, defaults to True.
    :type drop_index: Optional[bool], optional
    :param inplace: Whether to modify the DataFrame in place before inserting, defaults to True.
    :type inplace: Optional[bool], optional
    """
    if len(request["projection"]) > 0:
        logging.debug(
            "\"projection\" property from field \"request\" in udm configuration is enabled."
        )

    _client = get_mongo_client(mongo_istance_name)
    _collection = _client[_client.list_database_names()[0]][
        request["collection"]]
    if inplace:
        df.reset_index(inplace=True, drop=drop_index)
        _collection.insert_many(df.to_dict("records"))
    else:
        df_temp = df.reset_index(inplace=False, drop=drop_index)
        _collection.insert_many(df_temp.to_dict("records"))


def _read_mongo(    # type:ignore
        mongo_istance_name: str,
        request: dict,
        output_type: UDMDataType = UDMDataType.DF,
        engine: UDMDataEngine = UDMDataEngine.PANDAS,
        **kwargs) -> pd.DataFrame:
    """
    Read data from a MongoDB collection based on the specified engine and return it as a DataFrame.

    This function retrieves data from a MongoDB collection and supports different engines for reading the data.
    Currently, only the Pandas engine is implemented for returning the data as a DataFrame.

    :param mongo_istance_name: The name of the MongoDB instance.
    :type mongo_istance_name: str
    :param request: A dictionary containing the collection name, query, and projection.
    :type request: dict
    :param output_type: The type of output (default is UDMDataType.DF).
    :type output_type: UDMDataType
    :param engine: The data engine to be used for reading (default is UDMDataEngine.PANDAS).
    :type engine: UDMDataEngine
    :return: The data as a Pandas DataFrame.
    :rtype: pd.DataFrame
    :raises NotImplementedError: If the output type or engine is not implemented.
    """
    if output_type == UDMDataType.DF:
        if engine == UDMDataEngine.PANDAS:
            return _read_mongo_pandas_df(mongo_istance_name, request)
        else:
            raise NotImplementedError(
                f"engine {engine} not implemented for mongo")
    else:
        raise NotImplementedError(
            f"output_type {output_type} not implemented for mongo")


def _write_mongo(    # type:ignore
        mongo_istance_name: str,
        request: dict,
        data: object,
        input_type: UDMDataType = UDMDataType.DF,
        engine: UDMDataEngine = UDMDataEngine.PANDAS,
        drop_index: Optional[bool] = True,
        inplace: Optional[bool] = True,
        **kwargs) -> None:
    """
    Write data to a MongoDB collection based on the specified engine.

    This function writes data to a MongoDB collection, supporting different engines for writing. 
    Currently, only the Pandas engine is implemented for writing DataFrame objects.

    :param mongo_istance_name: The name of the MongoDB instance.
    :type mongo_istance_name: str
    :param request: A dictionary containing the collection name and query.
    :type request: dict
    :param data: The data to be written (as a DataFrame).
    :type data: object
    :param input_type: The type of input data (default is UDMDataType.DF).
    :type input_type: UDMDataType
    :param engine: The data engine to be used for writing (default is UDMDataEngine.PANDAS).
    :type engine: UDMDataEngine
    :param drop_index: Whether to drop the index when writing the data, defaults to True.
    :type drop_index: Optional[bool], optional
    :param inplace: Whether to modify the DataFrame in place before writing, defaults to True.
    :type inplace: Optional[bool], optional
    :raises NameError: If the collection does not exist in MongoDB.
    :raises NotImplementedError: If the input type or engine is not implemented.
    """

    if not ("ISP_AMBIENTE" in os.environ
            and not os.environ['ISP_AMBIENTE'] == ISP_AMBIENTE_LOCAL_ENV_VALUE):
        if not _collection_available(mongo_istance_name, request):
            raise NameError(
                f"Collection {request['collection']} not exists in {mongo_istance_name}'s MongoDB"
            )

    if input_type == UDMDataType.DF:
        if engine == UDMDataEngine.PANDAS:
            _write_mongo_pandas_df(mongo_istance_name,
                                   request,
                                   data,
                                   drop_index=drop_index,
                                   inplace=inplace)
        else:
            raise NotImplementedError(
                f"engine {engine} not implemented for mongo")
    else:
        raise NotImplementedError(
            f"input_type {input_type} not implemented for mongo")


def _delete_mongo(mongo_istance_name: str, request: dict) -> None:
    """
    Delete data from a MongoDB collection based on the query in the request.

    This function deletes multiple documents from a MongoDB collection based on the query specified 
    in the `request` dictionary.

    :param mongo_istance_name: The name of the MongoDB instance.
    :type mongo_istance_name: str
    :param request: A dictionary containing the collection name and query.
    :type request: dict
    """
    _client = get_mongo_client(mongo_istance_name)
    _client[_client.list_database_names()[0]][
        request['collection']].delete_many(request['query'])


def _collection_available(mongo_istance_name: str, request: dict) -> bool:
    """
    Check if a MongoDB collection is available in the specified instance.

    This function verifies if the requested collection exists in the MongoDB instance.

    :param mongo_istance_name: The name of the MongoDB instance.
    :type mongo_istance_name: str
    :param request: A dictionary containing the collection name.
    :type request: dict
    :return: True if the collection exists, False otherwise.
    :rtype: bool
    """
    _client = get_mongo_client(mongo_istance_name)
    _db = _client[_client.list_database_names()[0]]
    return request['collection'] in _db.list_collection_names()
