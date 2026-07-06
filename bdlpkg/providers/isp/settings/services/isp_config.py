import os
import logging
import yaml
from typing import Any, Dict, List, Optional, Union
from functools import lru_cache
from bdlpkg.utils.bdlfile.services.bdlfile import _get_config_path, get_obj_from_config_path
from bdlpkg.providers.isp.settings.entities.jdbc.jdbc import JDBCSettings
from bdlpkg.providers.isp.settings.entities.messaging.mail import MailSettings
from bdlpkg.providers.isp.settings.entities.messaging.kafka import KafkaSettings
from bdlpkg.providers.isp.settings.entities.model_registry.ModelRegistrySettings import DeterminedAIMRSettings
from bdlpkg.providers.isp.settings.entities.storage.s3 import S3BucketSettings, S3GSSBucketSettings
from bdlpkg.providers.isp.settings.entities.key.key import GenericKeySettings
from bdlpkg.providers.isp.settings.entities.database.mongo import MongoSettings
from bdlpkg.providers.isp.settings.entities.database.denodo import DenodoSettings
from bdlpkg.providers.isp.settings.entities.database.oracle import OracleSettings
from bdlpkg.providers.isp.settings.entities.database.postgres import PostgresSettings

class Settings:
    """
    This class manages the configuration of various services, such as databases, messaging services, and storage,
    by loading configuration data from environment files and integrating them with settings from 'isp-config-env'.
    
    The class reads configurations for multiple services (e.g., mail, buckets, keys, JDBC, model registry),
    and organizes the settings into a structured dictionary. It also handles database configurations for MongoDB,
    Oracle, Denodo, Postgres, and messaging configurations for Kafka.

    :param _config_path: The path where configuration files are located. If not provided, it defaults to environment variables.
    :type _config_path: Optional[str]
    """

    def __init__(self, _config_path: Optional[str] = None):

        _types = ["mail", "bucket", "key", "jdbc", "model_registry"]

        self.items: Dict[str, dict] = {_type: {} for _type in _types}
        
        for _type in _types:
            for root, dirs, files in os.walk(
                    os.path.join(_config_path, _type),    #type:ignore
                    topdown=False,
                    followlinks=False,
            ):
                for name in dirs:
                    if not name[0] == ".":
                        env = os.path.join(root, name, ".env")
                        if os.path.isfile(env):
                            logging.info("Found setting in {}".format(env))
                            self._set_items(_type, name, env)

        # IXP
        self.items["ixp"] = {}
        if "ixp" in os.listdir(_get_config_path()):
            obj_config = get_obj_from_config_path(os.path.join("ixp", "config.yaml"))
            for ixi in obj_config:
                self.items["ixp"][ixi] = obj_config[ixi]

        # ISP CONFIG ENV
        # isp-config-env configuration files contain the declaration of datasources (for example name, user) but do not contain some fields (for example passwords)
        # hence, after reading these config files we are going to integrate them with settings
        _isp_config_env_configuration = self._get_datasources_configuration(
            "configuration"
        )    # all configs in isp-config-env configuration files
        if "env" in _isp_config_env_configuration:
            self.items["isp-config-env"] = _isp_config_env_configuration["env"]
        else:
            self.items["isp-config-env"] = {}

        # DATABASE
        self.items["database"] = {}
        # MONGO
        self.items["database"]["mongo"] = {}
        if "mongo" in _isp_config_env_configuration:
            for mi in _isp_config_env_configuration["mongo"]:
                self.items["database"]["mongo"][mi] = MongoSettings.get_istance(
                    mi)
        # ORACLE
        self.items["database"]["oracle"] = {}
        if "oracle" in _isp_config_env_configuration:
            for oi in _isp_config_env_configuration["oracle"]:
                self.items["database"]["oracle"][
                    oi] = OracleSettings.get_istance(oi)
        # DENODO
        self.items["database"]["denodo"] = {}
        if "denodo" in _isp_config_env_configuration:
            for di in _isp_config_env_configuration["denodo"]:
                self.items["database"]["denodo"][
                    di] = DenodoSettings.get_istance(di)
        # POSTGRES
        self.items["database"]["postgres"] = {}
        if "postgresql" in _isp_config_env_configuration:
            for pi in _isp_config_env_configuration["postgresql"]:
                self.items["database"]["postgres"][pi] = PostgresSettings.get_istance(pi)
        
        # MESSAGING
        self.items["messaging"] = {}
        # KAFKA
        self.items["messaging"]["kafka"] = {}
        if "kafka" in _isp_config_env_configuration:
            for ki in _isp_config_env_configuration["kafka"]:
                self.items["messaging"]["kafka"][ki] = KafkaSettings.get_istance(
                    ki)
                
        # S3 GSS
        if "s3" in _isp_config_env_configuration:
            for si in _isp_config_env_configuration["s3"]:
                si = si.split("-")[-1]
                self.items["bucket"][si] = S3GSSBucketSettings.get_istance(
                    si)


    def _set_items(self, _type: str, name: str, env: str) -> None:
        """
        Set individual items (e.g., mail, bucket, key, jdbc, model_registry) from the .env file.

        :param _type: The type of service (e.g., mail, jdbc).
        :type _type: str
        :param name: The name of the specific instance.
        :type name: str
        :param env: The path to the environment file.
        :type env: str
        """
        if _type == "mail":
            self.items[_type][name] = MailSettings(resource_name=name,
                                                   _env_file=env,
                                                   _env_file_encoding="utf-8")
        elif _type == "bucket":
            self.items[_type][name] = S3BucketSettings(
                resource_name=name, _env_file=env, _env_file_encoding="utf-8")                
        elif _type == "key":
            self.items[_type][name] = GenericKeySettings(
                resource_name=name, _env_file=env, _env_file_encoding="utf-8")
        elif _type == "jdbc":
            setting = JDBCSettings(resource_name=name,
                                   _env_file=env,
                                   _env_file_encoding="utf-8")
            if setting.jdbc_connection_type not in self.items[_type]:
                self.items[_type][setting.jdbc_connection_type] = {}
            self.items[_type][setting.jdbc_connection_type][name] = setting
        elif _type == "model_registry":
            # per google faremo il try di determined, se non va facciamo il try su google e se non va diamo errore. 
            setting = DeterminedAIMRSettings(resource_name=name,
                                   _env_file=env,
                                   _env_file_encoding="utf-8")
            self.items[_type][name] = setting



    @staticmethod
    def _get_yaml_from_file(filename: str) -> Any:
        """
        Load configuration from a YAML file.

        :param filename: The path to the YAML file.
        :type filename: str
        :return: Parsed YAML content as a dictionary.
        :rtype: dict
        """
        _o = {}
        if os.path.isfile(filename):
            _o = yaml.safe_load(open(filename, "r"))
        else:
            logging.warning("YAML file not found in {}".format(filename))
        return _o

    @staticmethod
    def _get_dict_from_kv_list(ds_list: List[dict], k_name: str,
                               v_name: str) -> dict:
        """
        Convert a list of dictionaries into a dictionary based on a key-value pair.
        This method takes a list of dictionaries, where each dictionary contains a key-value pair, and converts
        it into a single dictionary using the specified key (`k_name`) and value (`v_name`) fields from each dictionary.

        :param ds_list: A list of dictionaries containing the data to be converted.
        :type ds_list: List[dict]
        :param k_name: The key in each dictionary that will be used as the key in the output dictionary.
        :type k_name: str
        :param v_name: The key in each dictionary that will be used as the value in the output dictionary.
        :type v_name: str
        :return: A dictionary where the keys are the values of `k_name` and the values are from `v_name`.
        :rtype: dict

        Example:
            Input:
            [{'name': 'BIND', 'value': '0.0.0.0:8080'}, {'name': 'MAX_WORKERS', 'value': '2'}]
            
            Output:
            {'BIND': '0.0.0.0:8080', 'MAX_WORKERS': '2'}
        """
        
        _o = {}
        for conf in ds_list:
            _o[conf[k_name]] = conf[v_name]
        return _o

    @staticmethod
    def _get_dict_from_dict_list(ds_list: List[dict], k_name: str) -> dict:
        """
        Convert a list of dictionaries into a dictionary based on a key.

        This method takes a list of dictionaries and converts it into a dictionary
        using the specified key from each dictionary.

        :param ds_list: A list of dictionaries to be converted.
        :type ds_list: List[dict]
        :param k_name: The key in each dictionary to be used as the dictionary key in the output.
        :type k_name: str
        :return: A dictionary with the specified key from each dictionary in the list as the new keys.
        :rtype: dict
        """
        _o = {}
        for conf in ds_list:
            _o[conf[k_name]] = conf
        return _o

    def _get_dict_from_isp_config(self, filename: str, item: str) -> dict:
        """
        Retrieve configuration data from an ISP configuration file.

        This method reads a YAML configuration file and extracts a specific item.
        The function then converts the content into a dictionary format, handling cases
        where the "env" key contains name-value pairs and other keys contain lists of variables.

        :param filename: The path to the YAML configuration file.
        :type filename: str
        :param item: The item (e.g., "mongo", "oracle") to retrieve from the configuration file.
        :type item: str
        :return: A dictionary containing the configuration data for the specified item.
        :rtype: dict
        """
        _confs = {}
        _conf = self._get_yaml_from_file(filename)
        if item in _conf:
            for k in _conf[item]:
                if k == "env":
                    _confs[k] = self._get_dict_from_kv_list(
                        _conf[item][k], "name",
                        "value")    # in this case we have just name and value
                elif k == "s3":
                    _confs[k] = self._get_dict_from_dict_list(
                        _conf[item][k], "bucket_name"
                    )
                else:
                    _confs[k] = self._get_dict_from_dict_list(
                        _conf[item][k], "name"
                    )    # in this case we have name and a list of variables

        return _confs

    def _get_datasources_configuration(self, item: str) -> dict:
        """
        Retrieve datasource configurations from isp-config-env.

        :param item: The item name to retrieve (e.g., "mongo", "oracle").
        :type item: str
        :return: A dictionary containing the configurations.
        :rtype: dict
        """

        _confs: dict = {}

        if os.environ["MY_HOME"].endswith("app-config"):  
            _path = os.path.join(os.path.abspath(os.path.join(os.environ["MY_HOME"], "..")),"isp-config-env")  #OCP4
        else:  
            _path = os.path.join(os.environ["MY_HOME"],"isp-config-env")   #OCP3 + locale

        _configfilename = "configuration{}.yml"
        _configfile_base = os.path.join(
            _path, _configfilename.format(""))    # i.e.: "configuration.yml"

        if "ISP_AMBIENTE" in os.environ:
            _env = "-" + os.environ["ISP_AMBIENTE"]
        else:
            _env = "-svil"
        _configfile_env = os.path.join(_path, _configfilename.format(
            _env))    # for example: "configuration-svil.yml"

        _configuration_base = self._get_dict_from_isp_config(
            _configfile_base, item)
        _configuration_env = self._get_dict_from_isp_config(
            _configfile_env, item)

        # merge _configuration_env in _configuration_base
        for key in _configuration_base:
            if key in _configuration_env:
                _configuration_base[key] = {
                    **_configuration_base[key],
                    **_configuration_env[key],
                }
        for key in _configuration_env:
            if key not in _configuration_base:
                _configuration_base[key] = _configuration_env[key]

        return _configuration_base


# https://fastapi.tiangolo.com/advanced/settings/#creating-the-settings-only-once-with-lru_cache
@lru_cache()
def get_settings() -> Dict[str, dict]:
    """
    Load the application settings, caching the result to avoid repeated calls.
    
    This function checks for the environment variables `DS_CONF_DIR` or `APP_CONF_DIR` to determine
    the configuration path, defaulting to the current directory if not set.

    :return: A dictionary containing all configuration settings.
    :rtype: Dict[str, dict]
    """
    if "DS_CONF_DIR" in os.environ:
        s = Settings(_config_path=os.environ["DS_CONF_DIR"])
    else:
        if "APP_CONF_DIR" in os.environ:
            s = Settings(_config_path=os.environ["APP_CONF_DIR"])
        else:
            s = Settings(_config_path=".")
    return s.items


def get_datasource_settings(ds_type: str,
                            ds_istance: Union[str, None],
                            ds_istance_name: Optional[str] = None) -> Any:
    """
    Retrieve the settings for a specific datasource instance.

    :param ds_type: The type of datasource (e.g., "jdbc", "model_registry").
    :type ds_type: str
    :param ds_istance: The instance name of the datasource.
    :type ds_istance: Union[str, None]
    :param ds_istance_name: The specific name of the instance. Defaults to the first one alphabetically.
    :type ds_istance_name: Optional[str]
    :return: The settings for the requested datasource.
    :rtype: Any
    :raises NameError: If the datasource type or instance is not available.
    :raises ModuleNotFoundError: If the instance name is not found in the available configurations.
    """
    # TODO: fornire in input path e istance_name -> output: ds setting
    _settings = get_settings()

    if ds_type not in _settings:
        raise NameError(f"datasource type {ds_type} not avilable")

    if ds_istance is not None:
        if ds_istance not in _settings[ds_type]:
            raise NameError(
                f"datasource istance {ds_istance} of type {ds_type} not avilable"
            )
        _ds = _settings[ds_type][ds_istance]
    else:
        _ds = _settings[ds_type]

    if len(_ds) == 0:
        raise NameError(
            f" no configuration available for datasource istance {ds_istance} of type {ds_type}"
        )

    if ds_istance_name is not None:
        if ds_istance_name not in _ds:
            raise ModuleNotFoundError(
                f"no configuration available for {ds_istance_name} with datasource istance {ds_istance} of type {ds_type}"
            )
    else:
        ds_istance_name = sorted(_ds.keys())[0]

    return _ds[ds_istance_name]
