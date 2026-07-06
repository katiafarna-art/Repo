import os
import pandas as pd
import tempfile
from typing import Union, Dict, Any
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDataEngine, UDMDataType, UDMDM4FileTypes_s3, UDMDM4FileTypes_gcs
from bdlpkg.providers.bdl.udm.services.utils import _get_args


def _get_file_details(istance_name: str, request: dict) -> Union[str, bytes]:
    """
    Retrieve the file details, either as a local path or as an in-memory file, depending on the request.

    This function checks the `udmdm_type` in the request to determine if the file should be fetched 
    from S3, Google Cloud Storage, or a local file system. It returns the path or file content.

    :param istance_name: The name of the storage instance (e.g., S3, GCS).
    :type istance_name: str
    :param request: A dictionary containing file details such as path, filename, and storage type.
    :type request: dict
    :return: The file path or the in-memory content of the file.
    :rtype: Union[str, bytes]
    """
    _res = os.path.join(request["path"], request["filename"])
    if request["udmdm_type"] in _get_args(UDMDM4FileTypes_s3):
        from bdlpkg.providers.isp.storages.services.BucketManager import BucketManager
        _bm = BucketManager()
        _res = _bm.download_file_in_memory(_res, resource_name=istance_name)
    if request["udmdm_type"] in _get_args(UDMDM4FileTypes_gcs):
        from bdlpkg.providers.gcp.storages.services.GCSBucketManager import GCSBucketManager
        _gcsbm = GCSBucketManager()
        _res = _gcsbm.download_file_in_memory(_res, resource_name=istance_name)
    return _res    # type:ignore


def _read_obj_pandas_df(istance_name: str, request: dict,
                        **kwargs: Dict[str, Any]) -> pd.DataFrame:
    """
    Read a file from storage and return its content as a Pandas DataFrame.

    This function reads a file based on the file extension (.pkl, .pickle, or .csv) and returns the content 
    as a Pandas DataFrame. It supports loading files from local storage, S3, or GCS.

    :param istance_name: The name of the storage instance (e.g., S3, GCS).
    :type istance_name: str
    :param request: A dictionary containing file details such as path, filename, and storage type.
    :type request: dict
    :return: A Pandas DataFrame containing the file data.
    :rtype: pd.DataFrame
    :raises NotImplementedError: If the file extension is not supported.
    """
    
    params = kwargs['engine_params'] if 'engine_params' in kwargs else {}
    _, file_extension = os.path.splitext(request["filename"])
    if file_extension in (".pkl", ".pickle"):
        return pd.read_pickle(_get_file_details(istance_name, request),
                              **params)
    elif file_extension in (".csv"):
        return pd.read_csv(_get_file_details(istance_name, request), **params)
    else:
        raise NotImplementedError(
            f"file extension {file_extension} NOT supported for file {request['filename']}"
        )


def _write_obj_pandas_df(istance_name: str, request: dict, df: object,
                         **kwargs: Dict[str, Any]) -> None:
    """
    Write a Pandas DataFrame to a file, supporting different file formats.

    This function writes a DataFrame to a file (e.g., .pkl, .pickle, .csv). 
    It supports writing to local storage, S3, or GCS depending on the request.

    :param istance_name: The name of the storage instance (e.g., S3, GCS).
    :type istance_name: str
    :param request: A dictionary containing file details such as path, filename, and storage type.
    :type request: dict
    :param df: The DataFrame to be written to the file.
    :type df: object
    :raises NotImplementedError: If the file extension is not supported.
    """

    params = kwargs['engine_params'] if 'engine_params' in kwargs else {}
    _filepath = os.path.join(request["path"], request["filename"])
    file_temp_request = request["udmdm_type"] in _get_args(UDMDM4FileTypes_s3) or request["udmdm_type"] in _get_args(UDMDM4FileTypes_gcs)

    if file_temp_request:
        _tempfile = tempfile.NamedTemporaryFile(delete=False)
        _filepath = _tempfile.name

    _, file_extension = os.path.splitext(request["filename"])
    if file_extension in (".pkl", ".pickle"):
        df.to_pickle(_filepath, **params)    # type:ignore
    elif file_extension in (".csv"):
        df.to_csv(_filepath, **params)    # type:ignore
    else:
        if file_temp_request:
            os.unlink(_tempfile.name)
        raise NotImplementedError(
            f"file extension {file_extension} NOT supported for file {request['filename']}"
        )
    if file_temp_request:
        _tempfile.close()
        if request["udmdm_type"] in _get_args(UDMDM4FileTypes_s3):
            from bdlpkg.providers.isp.storages.services.BucketManager import BucketManager
            _bm = BucketManager()
            _bm.upload_file_from_path(_tempfile.name,
                                      os.path.join(request["path"],
                                                   request["filename"]),
                                      resource_name=istance_name)
        if request["udmdm_type"] in _get_args(UDMDM4FileTypes_gcs):
            from bdlpkg.providers.gcp.storages.services.GCSBucketManager import GCSBucketManager
            _gcsbm = GCSBucketManager()
            _gcsbm.upload_file_from_path(_tempfile.name,
                                         os.path.join(request["path"],
                                                   request["filename"]),
                                         resource_name=istance_name)
        os.unlink(_tempfile.name)


def _read_obj(istance_name: str,
              request: dict,
              output_type: UDMDataType = UDMDataType.DF,
              engine: UDMDataEngine = UDMDataEngine.PANDAS,
              **kwargs: Dict[str, Any]) -> pd.DataFrame:
    """
    Read an object from storage and return it as a Pandas DataFrame or other supported format.

    This function reads data from storage (e.g., local, S3, GCS) and returns it based on the specified 
    output type and engine. Currently, it supports Pandas DataFrames.

    :param istance_name: The name of the storage instance (e.g., S3, GCS).
    :type istance_name: str
    :param request: A dictionary containing file details such as path, filename, and storage type.
    :type request: dict
    :param output_type: The output data type (default is UDMDataType.DF for DataFrame).
    :type output_type: UDMDataType
    :param engine: The engine used for reading the data (default is UDMDataEngine.PANDAS).
    :type engine: UDMDataEngine
    :return: The requested data as a Pandas DataFrame.
    :rtype: pd.DataFrame
    :raises NotImplementedError: If the output type or engine is not implemented.
    """
    if output_type == UDMDataType.DF:
        if engine == UDMDataEngine.PANDAS:
            return _read_obj_pandas_df(istance_name, request, **kwargs)
        else:
            raise NotImplementedError(
                f"engine {engine} not implemented for obj")
    else:
        raise NotImplementedError(
            f"output_type {output_type} not implemented for obj")


def _write_obj(istance_name: str,
               request: dict,
               data: object,
               input_type: UDMDataType = UDMDataType.DF,
               engine: UDMDataEngine = UDMDataEngine.PANDAS,
               **kwargs: Dict[str, Any]) -> None:
    """
    Write an object to storage, supporting different file formats and engines.

    This function writes data to storage (e.g., local, S3, GCS) based on the specified input type 
    and engine. Currently, it supports writing Pandas DataFrames.

    :param istance_name: The name of the storage instance (e.g., S3, GCS).
    :type istance_name: str
    :param request: A dictionary containing file details such as path, filename, and storage type.
    :type request: dict
    :param data: The data to be written (as a DataFrame).
    :type data: object
    :param input_type: The input data type (default is UDMDataType.DF for DataFrame).
    :type input_type: UDMDataType
    :param engine: The engine used for writing the data (default is UDMDataEngine.PANDAS).
    :type engine: UDMDataEngine
    :raises NotImplementedError: If the input type or engine is not implemented.
    """
    if input_type == UDMDataType.DF:
        if engine == UDMDataEngine.PANDAS:
            _write_obj_pandas_df(istance_name, request, data, **kwargs)
        else:
            raise NotImplementedError(
                f"engine {engine} not implemented for obj")
    else:
        raise NotImplementedError(
            f"input_type {input_type} not implemented for obj")
