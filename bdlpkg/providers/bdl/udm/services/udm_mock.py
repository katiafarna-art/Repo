import logging
import os
import hashlib
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDataEngine, UDMDataType
import pandas as pd

def _get_pkl_path(
    istance_name: str,
    request: dict,
    prefix: str = os.getenv("UDM_PREFIX_MOCK_DATA", default="./udmdm_mocked")
) -> str:
    """
    Generate the file path for storing mock data in a pickle file based on the instance name and request parameters.

    This function creates a SHA-1 hash from the sorted request dictionary and uses it to generate a unique 
    file name for storing mock data in a `.pkl` file. It ensures that the specified directory exists before
    returning the path.

    :param istance_name: The name of the instance for which the path is generated.
    :type istance_name: str
    :param request: A dictionary containing the request parameters.
    :type request: dict
    :param prefix: The directory prefix where the pickle file should be stored. Defaults to "./udmdm_mocked".
    :type prefix: str
    :return: The full path to the pickle file.
    :rtype: str
    """
    #https://docs.python.org/3/library/hashlib.html
    m = hashlib.sha1()
    m.update(
        str({key: value for key, value in sorted(request.items())}).encode())

    if len(prefix) > 0 and not os.path.isdir(prefix):
        os.mkdir(prefix)

    return str(os.path.join(prefix, f"{istance_name}_{m.hexdigest()}.pkl"))


def reset_mock_data(istance_name: str, request: dict) -> None:
    """
    Reset (delete) the mock data for a specific instance and request.

    This function deletes the mock data file if it exists for the given instance and request parameters.

    :param istance_name: The name of the instance for which the mock data is being reset.
    :type istance_name: str
    :param request: A dictionary containing the request parameters.
    :type request: dict
    """
    _p = _get_pkl_path(istance_name, request)
    if os.path.isfile(_p):
        os.remove(_p)


def _read_mocked_df(istance_name: str, request: dict) -> pd.DataFrame:
    """
    Read mock data from a pickle file and return it as a DataFrame.

    This function reads the mock data stored in a pickle file corresponding to the instance name and request
    parameters. If the file does not exist, it logs a warning and returns an empty DataFrame.

    :param istance_name: The name of the instance for which the data is being read.
    :type istance_name: str
    :param request: A dictionary containing the request parameters.
    :type request: dict
    :return: A DataFrame containing the mock data, or an empty DataFrame if the file doesn't exist.
    :rtype: pd.DataFrame
    """
    _p = _get_pkl_path(istance_name, request)

    if os.path.isfile(_p):
        return pd.read_pickle(_p)
    else:
        logging.warning(f"mock data file doesn't exists in {_p}")
        return pd.DataFrame()


def _write_mocked_df(istance_name: str, request: dict, df: object) -> None:
    """
    Write mock data to a pickle file as a DataFrame.

    This function writes or appends mock data (in DataFrame format) to a pickle file. If the file already
    exists, it reads the existing data, appends the new data, and then writes it back to the file.

    :param istance_name: The name of the instance for which the data is being written.
    :type istance_name: str
    :param request: A dictionary containing the request parameters.
    :type request: dict
    :param df: The DataFrame object containing the data to be written.
    :type df: object
    """
    _p = _get_pkl_path(istance_name, request)
    if os.path.isfile(_p):
        _old_df = _read_mocked_df(istance_name, request)
        result = pd.concat([_old_df, df])
        result.to_pickle(_p)
    else:
        df.to_pickle(_p)    # type:ignore


def _read_mocked(istance_name: str,
                 request: dict,
                 output_type: UDMDataType = UDMDataType.DF,
                 engine: UDMDataEngine = UDMDataEngine.PANDAS) -> pd.DataFrame:
    """
    Read mock data from storage based on the output type and engine.

    This function reads mock data based on the specified `output_type` and `engine`. 
    It currently only supports reading data as a DataFrame using the Pandas engine.

    :param istance_name: The name of the instance for which the data is being read.
    :type istance_name: str
    :param request: A dictionary containing the request parameters.
    :type request: dict
    :param output_type: The output data type (default is UDMDataType.DF for DataFrame).
    :type output_type: UDMDataType
    :param engine: The engine used for reading the data (default is UDMDataEngine.PANDAS).
    :type engine: UDMDataEngine
    :return: The requested data in the form of a DataFrame.
    :rtype: pd.DataFrame
    :raises NotImplementedError: If the output type or engine is not supported.
    """
    if output_type == UDMDataType.DF:
        if engine == UDMDataEngine.PANDAS:
            return _read_mocked_df(istance_name, request)
        else:
            raise NotImplementedError(
                f"engine {engine} not implemented for mocked")
    else:
        raise NotImplementedError(
            f"output_type {output_type} not implemented for mocked")


def _write_mocked(istance_name: str,
                  request: dict,
                  data: object,
                  input_type: UDMDataType = UDMDataType.DF,
                  engine: UDMDataEngine = UDMDataEngine.PANDAS) -> None:
    """
    Write mock data to storage based on the input type and engine.

    This function writes mock data based on the specified `input_type` and `engine`. 
    It currently only supports writing data as a DataFrame using the Pandas engine.

    :param istance_name: The name of the instance for which the data is being written.
    :type istance_name: str
    :param request: A dictionary containing the request parameters.
    :type request: dict
    :param data: The data to be written (as a DataFrame).
    :type data: object
    :param input_type: The input data type (default is UDMDataType.DF for DataFrame).
    :type input_type: UDMDataType
    :param engine: The engine used for writing the data (default is UDMDataEngine.PANDAS).
    :type engine: UDMDataEngine
    :raises NotImplementedError: If the input type or engine is not supported.
    """
    if input_type == UDMDataType.DF:
        if engine == UDMDataEngine.PANDAS:
            _write_mocked_df(istance_name, request, data)
        else:
            raise NotImplementedError(
                f"engine {engine} not implemented for mocked")
    else:
        raise NotImplementedError(
            f"input_type {input_type} not implemented for mocked")
