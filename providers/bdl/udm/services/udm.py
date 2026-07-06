import os
from warnings import warn
from typing import Optional, Union, Dict, Any, List

from pydantic_core import Url

from bdlpkg.utils.metaclasses import NamedSingleton
from bdlpkg.providers.bdl.udm.services.udmdm import get_udmdm
from bdlpkg.utils.bdlfile.services.bdlfile import _get_config_path
from bdlpkg.providers.bdl.udm.entities.udm_data_model import UDMDM, UDMDM4File, UDMDM4SqlListMapping
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4FileTypes_s3, UDMDM4FileTypes_gcs, UDMDataEngine, UDMDataType
from .udm_mock import _read_mocked, _write_mocked, reset_mock_data
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4SqlTypes
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4FileTypes
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4ApiTypes
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4MongoTypes
from bdlpkg.providers.bdl.udm.services.utils import _get_args
import pandas as pd


class UDM(metaclass=NamedSingleton):
    """
    UDM - Universal Data Manager by BDL
    This tools is your glassdoor over all the data of all bdlpkg's providers

    :param resource_name: name of the UDM data model
    :type resource_name: str

    :param mocked: set to true to avoid connection to external providers, defaults to False
    :type mocked: bool, optional
    
    :param udmdm_path: set a specific path for a udmdm, default to None
    :type str: string, optional

    """

    _udmdm_request: dict
    _udmdm_name: str

    def _cache_reset(self) -> None:
        """
        Reset the cache for the most recent DataFrame.
        """
        self._latest_df: Union[None, pd.DataFrame] = None

    def delete_mock_data(self) -> None:
        """
        Delete mock data associated with the current UDM.
        """
        reset_mock_data(self._udmdm_name, self._udmdm_request)

    def _update_udmdm(self) -> None:
        """
        Update UDM attributes based on the UDM model and its request configuration.
        """
        _path = self.udmdm_path
        if _path is None:
            try:
                _path = _get_config_path("udm")
            except KeyError:
                _path = os.getcwd()
        self._udmdm = get_udmdm(self._resource_name, _path)
        self._udmdm_type = self._udmdm.resource.type
        self._udmdm_name = self._udmdm.resource.name
        self._udmdm_request = self._udmdm.request.model_dump()
        
        #map SQL statement to SQL statement of an existing UDM (aka "dependency")
        if self._udmdm_request["udmdm_type"] in _get_args(UDMDM4SqlTypes) and self._udmdm_request["mapping"] is not None and self.dependencies is not None:
            self._udmdm_request["statement"] = UDM._replace_udm_statement(self._udmdm_request["statement"],
                                                                          self.dependencies,
                                                                          self._udmdm_request["mapping"])

        #map and fill SQL statement to string, numbers or lists
        if self._udmdm_request["udmdm_type"] in _get_args(UDMDM4SqlTypes) and self.values is not None:
            self._udmdm_request["statement"] = UDM._replace_udm_items(self._udmdm_request["statement"],
                                                                      self._udmdm_request["udmdm_type"],
                                                                      self.values)
            
        self._udmdm_engine = self._udmdm.engine

    def _is_mocked(self, mocked: bool) -> bool:
        """
        Determine if the UDM should operate in mock mode.

        :param mocked: Whether mock mode is explicitly enabled.
        :type mocked: bool
        :return: True if mock mode is enabled, False otherwise.
        :rtype: bool
        """
        if not mocked:
            if "UDM_ALL_MOCKED" in os.environ:
                return True
        return mocked

    def is_mocked(self) -> bool:
        """
        Check if the current UDM is in mock mode.

        :return: True if in mock mode, False otherwise.
        :rtype: bool
        """
        return self.mocked

    def __init__(self,
                 resource_name: str,
                 mocked: bool = False,
                 udmdm_path: Optional[str] = None,
                 values: Optional[Dict[str, Any]] = None,
                 dependencies: Optional[List[object]]= None):
        self.__name__ = resource_name
        self._resource_name = resource_name
        self.mocked = self._is_mocked(mocked)
        self.udmdm_path = udmdm_path
        self.values = values
        self.dependencies = dependencies
        self._update_udmdm()

    @staticmethod
    def _replace_udm_statement(statement_in: str,
                               dependencies: List[object]=None,
                               mapping: List[UDMDM4SqlListMapping]=None) -> str:
        """Replace items in SQL query with an SQL statement taken from an existing UDM

        Args:
            statement_in (str): statement to be filled
            dependencies (list): a list of UDMs on which the current UDM depends on
            mapping (List of dict): mapping between items and existing UDM

        Returns:
            dict: statement filled with an existing UDM
        """
        statement_out = statement_in
        udm_dependencies = [dep for dep in dependencies if isinstance(dep, UDM)]
        dep_name = [dep.__name__ for dep in udm_dependencies]

        for _map in mapping:
           
            #Check if the mapping UDM belongs to dependencies
            if _map['udm_name'] in dep_name:

                #Find in dependencies the UDM named as the mapping UDM
                for udm in udm_dependencies:
                    if udm.__name__ == _map['udm_name']:
                        statement_out = statement_out.replace(_map['statement'],udm._udmdm_request["statement"])
            else:
                raise ModuleNotFoundError(
                    f"UDM with name {_map['udm_name']} not found in UDM dependencies")
        return statement_out
    
    @staticmethod
    def _replace_udm_items(statement_in: str,
                           udmdm_type: UDMDM4SqlTypes,
                           values: Dict[str, Any]=None) -> str:
        """Replace items in SQL query with a string, number or list of items (in some cases with a specified slice)

        Args:
            statement_in (str): statement to be filled
            dependencies (list): a list of UDMs on which the current UDM depends on
            mapping (List of dict): mapping between items and existing UDM

        Returns:
            dict: statement filled with an existing UDM
        """
        statement_out = statement_in
       
        for _k in values.keys():
        
            if statement_in is not None:
                #Substitution specific for SQL statements
                if _k in statement_in:
                    #The key is included in the original SQL statement
                    if _k == "min_timeout":
                        raise ValueError(
                            f"Key ""min_timeout"" not allowed in the original statement"
                        )
                    if _k.startswith("tab_"):
                        statement_out= statement_out.replace(
                            _k, values[_k])
                    if isinstance(values[_k], dict):
                        _list_items = values[_k]["items"]
        
                        # Check if list contains are mixed dtypes
                        if all(isinstance(_item, str) for _item in _list_items) or all(isinstance(_item, (int, float)) for _item in _list_items):
                            
                            # The list has to be divided into sub-lists? If yes, the division is done according 
                            # to the dimension of the slice
                            if "dim_slice" in values[_k].keys():
                                
                                import re
                                field = values[_k]["field"]
                                match = re.search(rf"{field}\s+IN\s+{_k}",statement_out,re.IGNORECASE)
                                statement_out = statement_out[:match.start()] + '(' + statement_out[match.start():] #put the open parenthesis

                                dim_slice = values[_k]["dim_slice"]    #dimension of the slice
                                _res = [_list_items[i:i+dim_slice] for i in range(0, len(_list_items), dim_slice)]
                                _str_res = f' OR {field} IN '.join([str(tuple(_nat)) for _nat in _res])
                                _str_res = _str_res + ")"  #put the close parenthesis
                                
                                statement_out = statement_out.replace(_k, _str_res)
                            else:
                                statement_out = statement_out.replace(_k, f"{str(tuple(_list_items))}")
                        else:
                            raise TypeError(
                                f"List contains different dtypes"
                            )
                    elif isinstance(values[_k], (str, int, float)):
                        statement_out = statement_out.replace(_k, f"{values[_k]}")
                    else:
                        raise NotImplementedError(
                            f"Replace method not implemented for {type(values[_k])}"
                        )
                else:
                    if _k == "min_timeout":
                        #The key is not included in the original SQL statement and it is equal to "min_timeout"
                        if udmdm_type == "denodo":
                            #Timeout handling for Denodo queries
                            #https://community.denodo.com/docs/html/browse/6.0/vdp/vql/queries_select_statement/context_clause/context_clause
                            timeout_min = values[_k]            #timeout in min
                            timeout_ms = timeout_min*60*1000    #timeout in ms (format required by DENODO CONTEXT Clause)
                            statement_out = f"{statement_out}\nCONTEXT('QUERYTIMEOUT'='{timeout_ms}')"
                        else:
                            raise NotImplementedError(
                                f"Timeout handling implemented only for Denodo queries"
                            )
        return statement_out
        
        
    @staticmethod
    def _replace_request_value(request_in: dict,
                               replace_request_value: Dict[str, Any]) -> dict:
        """Replace dicts in query (mongoDB/API support for now)

        Args:
            request_in (dict): an udmdm_request dict
            replace_request_value (dict): {a:b,...} where a: "op1.op2.op3....." and b the value to be set. op shall be Dicts or List of Dicts

        Returns:
            dict: an udmdm_request dict (a copy, the original dict is untouched)
        """
        _dict = request_in.copy()

        for _k in replace_request_value.keys():
            steps = _k.split(".")
            _tmp = _dict

            if len(steps) > 1:
                for _i_step in range(0, len(steps) - 1):
                    if isinstance(_tmp, list) and isinstance(_tmp[0], dict):
                        _index = [
                            i for i, v in enumerate(_tmp) if steps[_i_step] in v
                        ][0]    # works only in list of dict
                        _tmp = _tmp[_index][steps[_i_step]]
                    elif isinstance(_tmp, dict):
                        _tmp = _tmp[steps[_i_step]]
                    else:
                        raise AttributeError(
                            f"I can accept only Lists of Dicts or Dicts for layer {steps[_i_step]}"
                        )

                if isinstance(_tmp, dict):
                    _tmp[steps[-1]] = replace_request_value[_k]
                else:
                    raise AttributeError(
                        "Last element of the chain shall be a dict")

            else:
                # no regression - old code to be deprecated in future release?
                for k in request_in:
                    if request_in[k] is not None and _k in request_in[k]:
                        # warn(
                        #     'String replace behaviour in _replace_request_value will be deprecated in future release.',
                        #     DeprecationWarning,
                        #     stacklevel=2)
                        if type(_dict[k]) == str:
                            _dict[k] = _dict[k].replace(
                                _k, replace_request_value[_k])
                        else:
                            _dict[k][_k] = replace_request_value[_k]

        return _dict

    def read_df(self,
                engine: Optional[UDMDataEngine] = None,
                cache_data: bool = False,
                **kwargs: dict) -> pd.DataFrame:
        """Read from UDM source and return a Dataframe object

        Args:
            engine (Optional[UDMDataEngine], optional): Engine to be used. Defaults to None (i.e., Default Engine).
            cache_data (bool, optional): Use cached data?. Defaults to False.

        Notable kwargs:
            `replace_request_value`: more info @ _replace_request_value()
            the other parameters are passed directly to the engine

        Returns:
            object: a Dataframe object according to `engine`
        """
        if cache_data and self._latest_df is not None:
            return self._latest_df
        else:
            if engine is None:
                engine = self._udmdm_engine.type

            if self._udmdm_engine.params:
                kwargs['engine_params'] = self._udmdm_engine.params

            _df = self._read(output_type=UDMDataType.DF,
                             engine=engine,
                             **kwargs)
            if cache_data:
                self._latest_df = _df
            else:
                self._latest_df = None
            return _df

    def write_df(self,
                 data: object,
                 engine: Optional[UDMDataEngine] = None,
                 **kwargs: dict) -> None:
        """Write to UDM source

        Args:
            data (object): data to be written
            engine (Optional[UDMDataEngine], optional): Engine to be used. Defaults to None (i.e., Default Engine).

        Notable kwargs:
            `replace_request_value`: more info @ _replace_request_value()
            the other parameters are passed directly to the engine

        """
        if engine is None:
            engine = self._udmdm_engine.type

        if self._udmdm_engine.params:
            kwargs['engine_params'] = self._udmdm_engine.params

        self._write(data, input_type=UDMDataType.DF, engine=engine, **kwargs)

    def _read(self, output_type: UDMDataType, engine: UDMDataEngine,
              **kwargs: dict) -> pd.DataFrame:
        """
        Read data from the UDM source based on the provided request and return a DataFrame.

        :param output_type: The type of data to read (default is UDMDataType.DF).
        :type output_type: UDMDataType
        :param engine: The engine to be used for reading the data (e.g., PANDAS).
        :type engine: UDMDataEngine
        :param kwargs: Additional parameters to pass to the data engine.
        :return: A pandas DataFrame containing the read data.
        :rtype: pd.DataFrame
        """

        _request_dict = self._udmdm_request
        if "replace_request_value" in kwargs:
            _request_dict = UDM._replace_request_value(self._udmdm_request, kwargs["replace_request_value"])

        if self.mocked:
            return _read_mocked(self._udmdm_name,
                                _request_dict,
                                output_type=output_type,
                                engine=engine,
                                **kwargs)

        if self._udmdm_type in _get_args(UDMDM4MongoTypes):
            from .udm_mongo import _read_mongo as _read_udmdm
        elif self._udmdm_type in _get_args(UDMDM4FileTypes):
            from .udm_obj import _read_obj as _read_udmdm    #type:ignore
        elif self._udmdm_type in _get_args(UDMDM4SqlTypes):
            from .udm_sql import _read_sql as _read_udmdm    #type:ignore
        else:
            raise NotImplementedError(
                f"resource type {self._udmdm_type} not implemented")

        return _read_udmdm(self._udmdm_name,
                           _request_dict,
                           output_type=output_type,
                           engine=engine,
                           **kwargs)

    def _write(self, data: object, input_type: UDMDataType,
               engine: UDMDataEngine, **kwargs: dict) -> None:
        """
        Write data to the UDM source.

        :param data: The data to be written.
        :type data: object
        :param input_type: The type of data being written (e.g., UDMDataType.DF).
        :type input_type: UDMDataType
        :param engine: The engine to be used for writing the data.
        :type engine: UDMDataEngine
        :param kwargs: Additional parameters to pass to the data engine.
        """

        _request_dict = self._udmdm_request
        if "replace_request_value" in kwargs:
            _request_dict = UDM._replace_request_value(self._udmdm_request, kwargs["replace_request_value"])

        if self.mocked:
            _write_mocked(self._udmdm_name,
                          _request_dict,
                          data,
                          input_type=input_type,
                          engine=engine,
                          **kwargs)

        elif self._udmdm_type in _get_args(UDMDM4MongoTypes):
            from .udm_mongo import _write_mongo
            _write_mongo(self._udmdm_name,
                         _request_dict,
                         data=data,
                         input_type=input_type,
                         engine=engine,
                         **kwargs)    #type:ignore
        elif self._udmdm_type in _get_args(UDMDM4FileTypes):
            from .udm_obj import _write_obj
            _write_obj(self._udmdm_name,
                       _request_dict,
                       data=data,
                       input_type=input_type,
                       engine=engine,
                       **kwargs)
        else:
            raise NotImplementedError(
                f"resource type {self._udmdm_type} not implemented")

    def _delete(self, **kwargs: dict) -> None:
        """
        Delete the UDM resource based on the current UDM type.

        :param kwargs: Additional parameters for deletion.
        """
        if self.mocked:
            self.delete_mock_data(**kwargs)
        elif self._udmdm_type in _get_args(UDMDM4MongoTypes):
            from .udm_mongo import _delete_mongo
            _delete_mongo(self._udmdm_name, self._udmdm_request, **kwargs)
        elif self._udmdm_type in _get_args(UDMDM4FileTypes):
            if not self.is_available():
                return
            if self._udmdm_type in _get_args(UDMDM4FileTypes_s3):
                from bdlpkg.providers.isp.storages.services.BucketManager import BucketManager
                _bm = BucketManager()
                return _bm.delete_file(
                    os.path.join(self._udmdm_request["path"],
                                 self._udmdm_request["filename"]),
                    self._udmdm_name)
            elif self._udmdm_type in _get_args(UDMDM4FileTypes_gcs):
                from bdlpkg.providers.gcp.storages.services.GCSBucketManager import GCSBucketManager
                _gcsbm = GCSBucketManager()
                return _gcsbm.delete_file(
                    os.path.join(self._udmdm_request["path"],
                                 self._udmdm_request["filename"]),
                    self._udmdm_name)
            else:
                file_path = os.path.join(self._udmdm_request["path"],
                                         self._udmdm_request["filename"])
                os.remove(file_path)
                pass
        else:
            raise NotImplementedError(
                f"resource type {self._udmdm_type} not implemented")

    def is_available(self) -> bool:
        """Check whether or not the resource is available.

        Returns:
            bool: The resource is available?
        """
        if self._udmdm_type in _get_args(UDMDM4FileTypes):
            if self._udmdm_type in _get_args(UDMDM4FileTypes_s3):
                from bdlpkg.providers.isp.storages.services.BucketManager import BucketManager
                _bm = BucketManager()
                return _bm.exists_key(
                    os.path.join(self._udmdm_request["path"],
                                 self._udmdm_request["filename"]),
                    self._udmdm_name)
            elif self._udmdm_type in _get_args(UDMDM4FileTypes_gcs):
                from bdlpkg.providers.gcp.storages.services.GCSBucketManager import GCSBucketManager
                _gcsbm = GCSBucketManager()
                return _gcsbm.exists_blob(
                    os.path.join(self._udmdm_request["path"],
                                 self._udmdm_request["filename"]),
                    self._udmdm_name)
            else:
                file_path = os.path.join(self._udmdm_request["path"],
                                         self._udmdm_request["filename"])
                return os.path.exists(file_path)

        if self._udmdm_type in _get_args(UDMDM4MongoTypes):
            from .udm_mongo import _collection_available
            return _collection_available(self._udmdm_name, self._udmdm_request)

        if self._udmdm_type in _get_args(UDMDM4SqlTypes):
            from .udm_sql import _tables_available
            return _tables_available(self._udmdm_type, self._udmdm_name,
                                     self._udmdm_request)

        if self._udmdm_type in _get_args(UDMDM4ApiTypes):
            # https://stackoverflow.com/questions/9626535/get-protocol-host-name-from-url
            from urllib.parse import urlparse
            from urllib.request import urlopen
            # for compatibility with pydantic update get the string version of the URL
            parsed_uri = urlparse(self._udmdm_request["url"].__str__())
            result = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
            try:
                return (urlopen(result, timeout=3).getcode() < 500)
            except:
                return False

        raise NotImplementedError(
            f"resource type {self._udmdm_type} not implemented")
