import os
from typing import List
from bdlpkg.utils.bdlfile.services.bdlfile import get_files_list_from_path, get_obj_from_path
from bdlpkg.providers.bdl.udm.entities.udm_data_model import UDMDM


def get_udmdm_dict_user(resource_name: str = "", path: str = "") -> dict:
    """
    Retrieve a UDM dictionary for the specified resource name.

    :param resource_name: The name of the resource to filter by. If empty, returns the first active UDM.
    :type resource_name: str, optional
    :param path: The path to search for UDM resources. Defaults to an empty string.
    :type path: str, optional
    :return: A dictionary representing the UDM resource if found, otherwise an empty dictionary.
    :rtype: dict
    """

    _res = get_udmdm_list(only_active=True, path=path)
    if not resource_name == "":
        _res = [e for e in _res if e["name"] == resource_name]
    return _res[0] if len(_res) > 0 else {}


def get_udmdm(resource_name: str = "", path: str = "") -> UDMDM:    #to
    """Create a UDMDM object

    Args:
        resource_name (str, optional): name defined in YAML. Defaults to "".
        path (str, optional): The UDMDM's parent directory or YAML file. Defaults to "" (i.e., default path (app/config/udm)).

    Raises:
        ValueError: UDMDM not found

    Returns:
        UDMDM: the desidered UDMDM
    """
    _udmdm_dict_user = get_udmdm_dict_user(resource_name, path)
    if not _udmdm_dict_user:
        raise ValueError(f"no {resource_name} udmdm available in {path}")
    else:
        _udmdm_dict_user["request"]["udmdm_type"] = _udmdm_dict_user[
            "resource"]["type"].lower()
        return UDMDM.model_validate(_udmdm_dict_user)    # type:ignore


def get_udmdm_list(only_active: bool = True, path: str = "") -> List[dict]:
    """Return a List of UDMDM

    Args:
        only_active (bool, optional): Only UDMDM enabled in this environment?. Defaults to True.
        path (str, optional): The UDMDM's path. Defaults to "" (i.e., default path (app/config/udm)).

    Returns:
        List[dict]: a list of UDMDM
    """

    _env = ""
    if "ISP_AMBIENTE" in os.environ:
        _env = os.environ["ISP_AMBIENTE"]

    _res = []
    for _file in get_files_list_from_path(path, extension_filter=[".yaml"]):
        for _obj in get_obj_from_path(_file):    # type:ignore
            if not (only_active and 'env' in _obj and _env != _obj["env"]):
                _res.append(_obj)

    if (only_active):
        _names = set([a["name"] for a in _res])
        for n in _names:
            _prob = [b for b in _res if b["name"] == n]
            if _prob.__len__() > 1:
                _safe = [
                    ok for ok in _prob if "env" in ok and ok["env"] == _env
                ][0]
                for _del in _prob:
                    _res.remove(_del)
                _res.append(_safe)
    return _res
