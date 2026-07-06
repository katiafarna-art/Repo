import os
from typing import Any, Dict
from bdlpkg.providers.bdl.udm.services.udmdm import get_udmdm_list


def get_UDM_config(only_active: bool = True) -> Dict[str, Any]:
    """Get UDM config

    Args:
        only_active (bool, optional): return only active UDM (i.e., env equals to this env or not indicated). Defaults to True.

    Returns:
        Dict[str, Any]: a dict for info
    """
    if "APP_CONF_DIR" in os.environ:
        _path = os.path.join(os.environ["APP_CONF_DIR"], "udm")
    else:
        _path = "./udm"

    _res = {
        "active_env": os.getenv("ISP_AMBIENTE", "ND"),
        "only_active": only_active,
        "UDM_list": get_udmdm_list(only_active=only_active, path=_path)
    }
    return _res
