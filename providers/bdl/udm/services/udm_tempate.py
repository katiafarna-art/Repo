from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDataEngine, UDMDataType
from typing import Any

#TYPE -> provider da implmentare (es. mongo, denodo)


def _read_TYPE_pandas_df(istance_name: str, request: dict,
                         **kwargs: Any) -> object:
    """
    Placeholder function for reading data from a TYPE database into a Pandas DataFrame.

    This function should be implemented to read data from a specific `TYPE` provider (e.g., MongoDB, Denodo) 
    and return the result as a Pandas DataFrame.

    :param istance_name: The name of the TYPE database instance.
    :type istance_name: str
    :param request: A dictionary containing the query parameters, such as collection or table name, and filters.
    :type request: dict
    :return: The result as a Pandas DataFrame (or other format depending on implementation).
    :rtype: object
    :raises NotImplementedError: This is a placeholder and must be implemented for the specific provider.
    """
    pass


def _write_TYPE_pandas_df(istance_name: str, request: dict, df: object,
                          **kwargs: Any) -> None:
    """
    Placeholder function for writing a Pandas DataFrame to a TYPE database.

    This function should be implemented to write data from a Pandas DataFrame into a specific `TYPE` provider 
    (e.g., MongoDB, Denodo).

    :param istance_name: The name of the TYPE database instance.
    :type istance_name: str
    :param request: A dictionary containing the parameters, such as collection or table name.
    :type request: dict
    :param df: The Pandas DataFrame to write to the database.
    :type df: object
    :raises NotImplementedError: This is a placeholder and must be implemented for the specific provider.
    """
    pass


def _read_TYPE(istance_name: str,
               request: dict,
               output_type: UDMDataType = UDMDataType.DF,
               engine: UDMDataEngine = UDMDataEngine.PANDAS,
               **kwargs: Any) -> object:
    """
    Read data from a TYPE database and return it in the specified output format.

    This function reads data from a `TYPE` provider (e.g., MongoDB, Denodo) and supports different output types 
    and engines. By default, it reads into a Pandas DataFrame using the Pandas engine.

    :param istance_name: The name of the TYPE database instance.
    :type istance_name: str
    :param request: A dictionary containing query details, such as the collection or table name and filters.
    :type request: dict
    :param output_type: The type of data to output (default is UDMDataType.DF for DataFrame).
    :type output_type: UDMDataType
    :param engine: The engine to be used for reading data (default is UDMDataEngine.PANDAS).
    :type engine: UDMDataEngine
    :return: The data read from the database in the specified output format.
    :rtype: object
    :raises NotImplementedError: If the output type or engine is not implemented for the specific provider.
    """
    if output_type == UDMDataType.DF:
        if engine == UDMDataEngine.PANDAS:
            return _read_TYPE_pandas_df(istance_name, request, **kwargs)
        else:
            raise NotImplementedError(
                f"engine {engine} not implemented for TYPE")
    else:
        raise NotImplementedError(
            f"output_type {output_type} not implemented for TYPE")


def _write_TYPE(istance_name: str,
                request: dict,
                data: object,
                input_type: UDMDataType = UDMDataType.DF,
                engine: UDMDataEngine = UDMDataEngine.PANDAS,
                **kwargs: Any) -> None:
    """
    Write data to a TYPE database in the specified input format.

    This function writes data to a `TYPE` provider (e.g., MongoDB, Denodo) using different input types and engines. 
    By default, it writes data from a Pandas DataFrame using the Pandas engine.

    :param istance_name: The name of the TYPE database instance.
    :type istance_name: str
    :param request: A dictionary containing details such as the collection or table name.
    :type request: dict
    :param data: The data to write to the database (typically a Pandas DataFrame).
    :type data: object
    :param input_type: The type of input data (default is UDMDataType.DF for DataFrame).
    :type input_type: UDMDataType
    :param engine: The engine to be used for writing data (default is UDMDataEngine.PANDAS).
    :type engine: UDMDataEngine
    :raises NotImplementedError: If the input type or engine is not implemented for the specific provider.
    """
    if input_type == UDMDataType.DF:
        if engine == UDMDataEngine.PANDAS:
            _write_TYPE_pandas_df(istance_name, request, data, **kwargs)
        else:
            raise NotImplementedError(
                f"engine {engine} not implemented for TYPE")
    else:
        raise NotImplementedError(
            f"input_type {input_type} not implemented for TYPE")
