import os
import logging
import yaml
from typing import Any, Dict, List, Optional
from functools import lru_cache
from bdlpkg.providers.gcp.settings.entities.sa.gcp import SASettings


class Settings:
    """
    This class is responsible for managing configuration settings for various service accounts and ISP environment configurations.

    Attributes:
    - items (dict): A dictionary that stores configurations for different types of services, such as service accounts.
    """

    def __init__(self):

        self.items: Dict[str, dict] = {}
        
        # ISP CONFIG ENV
        # isp-config-env configuration files contain the declaration of datasources (for example name, user) but do not contain some fields (for example passwords)
        # hence, after reading these config files we are going to integrate them with settings
        _isp_config_env_configuration = self._get_datasources_configuration(
            "configuration"
        )    # all configs in isp-config-env configuration files

        # SERVICE ACCOUNTS
        self.items["service_account"] = {}
        if "hashicorp-vault" in _isp_config_env_configuration:
            for hvi in _isp_config_env_configuration["hashicorp-vault"]:
                self.items["service_account"][hvi] = SASettings.get_istance(hvi)



    @staticmethod
    def _get_yaml_from_file(filename: str) -> Any:
        """
        Reads and parses a YAML file.

        :param filename: The path to the YAML file.
        :type filename: str
        :return: Parsed YAML data as a Python object.
        :rtype: Any
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
        """[summary]
        ds_dict: list of dicts
        k_name: key of the key
        v_name: key of the value
        [example]
        from: [{'name': 'BIND', 'value': '0.0.0.0:8080'}, {'name': 'MAX_WORKERS', 'value': '2'}]
        to: {'BIND': '0.0.0.0:8080', 'MAX_WORKERS': '2'}
        """
        _o = {}
        for conf in ds_list:
            _o[conf[k_name]] = conf[v_name]
        return _o

    @staticmethod
    def _get_dict_from_dict_list(ds_list: List[dict], k_name: str) -> dict:
        """
        Converts a list of dictionaries into a dictionary where keys are specified by k_name.

        :param ds_list: The list of dictionaries to convert.
        :type ds_list: List[dict]
        :param k_name: The key to use for the dictionary keys.
        :type k_name: str
        :return: A dictionary with keys from the k_name field.
        :rtype: dict
        """
        _o = {}
        for conf in ds_list:
            _o[conf[k_name]] = conf
        return _o

    def _get_dict_from_isp_config(self, filename: str, item: str) -> dict:
        """
        Retrieves configurations from ISP configuration files based on a specific item.

        :param filename: The YAML configuration file path.
        :type filename: str
        :param item: The specific item to retrieve from the configuration.
        :type item: str
        :return: A dictionary of configurations for the specified item.
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
        Retrieves the complete datasource configurations by merging the base and environment-specific configuration files.

        :param item: The specific item to retrieve from the configuration files.
        :type item: str
        :return: A merged dictionary of configurations.
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
    Retrieves and caches the settings from the configuration files.

    :return: A dictionary containing all settings.
    :rtype: dict
    """
    s = Settings()

    return s.items


def get_datasource_settings(ds_type: str,
                            ds_istance_name: Optional[str] = None) -> Any:
    """
    Retrieves the settings for a specific datasource type and instance.

    :param ds_type: The type of datasource (e.g., 'service_account').
    :type ds_type: str
    :param ds_istance_name: The optional name of a specific instance of the datasource. If not provided, the first instance is returned.
    :type ds_istance_name: Optional[str]
    :return: The settings for the requested datasource instance.
    :rtype: Any
    :raises NameError: If the datasource type or instance is not found.
    :raises ModuleNotFoundError: If the specific datasource instance is not available.
    """
    # TODO: fornire in input path e istance_name -> output: ds setting
    _settings = get_settings()

    if ds_type not in _settings:
        raise NameError(f"datasource type {ds_type} not available")
    else:
        _ds = _settings[ds_type]
    
    if len(_ds) == 0:
        raise NameError(
            f" no configuration available for datasource of type {ds_type}"
        )

    if ds_istance_name is not None:
        if ds_istance_name not in _ds:
            raise ModuleNotFoundError(
                f"no configuration available for {ds_istance_name} of type {ds_type}"
            )
    else:
        ds_istance_name = sorted(_ds.keys())[0]

    return _ds[ds_istance_name]