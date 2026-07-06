import logging
import os
import pkg_resources
from socket import gethostname
from typing import Dict, Any, List, Tuple
from bdlpkg.utils.bdlfile.services.bdlfile import get_obj_from_config_path
from bdlpkg.utils.health.entities.statusenum import StatusEnum
from bdlpkg.utils.metaclasses.singleton import Singleton

app_configs: Dict[Any,
                  Any] = get_obj_from_config_path("app.yaml")    # type:ignore

# region VERSION
VERSION="ND"
try:
    from git import Git
    VERSION = Git(os.environ["MY_HOME"]).describe(
        "--always") if "MY_HOME" in os.environ else 'ND'
except Exception as e:
    if "BDL_APP_NAME" in os.environ:
        try:
            VERSION = pkg_resources.get_distribution(os.environ["BDL_APP_NAME"]).version
        except Exception as e:
            logging.debug("VERSION error")
            pass
# endregion 

def healthcheck() -> Dict[str, Any]:
    return {
        "title": app_configs["application"]["name"],
        "description": app_configs["description"],
        "version": VERSION,
        "status": StatusEnum.OK,
        "hostname": gethostname()
    }


def packagescheck() -> List[Tuple[str, str]]:
    return sorted(
        [(p.project_name, p._version) for p in pkg_resources.working_set],
        key=lambda t: t[0].lower())


class ApplicationHealth(metaclass=Singleton):

    def __init__(self) -> None:
        self._set_health(StatusEnum.UNKNOWN)

    def _set_health_msg(self, status: StatusEnum, msg: str) -> None:
        self._health_msg = status.value if msg == "" else msg

    def _set_health(self, status: StatusEnum, msg: str = "") -> None:
        self._healt = status
        self._set_health_msg(status, msg)

    def set_ok(self, msg: str = "") -> None:
        self._set_health(StatusEnum.OK, msg)

    def set_failure(self, msg: str = "") -> None:
        self._set_health(StatusEnum.FAILURE, msg)

    def set_critical(self, msg: str = "") -> None:
        self._set_health(StatusEnum.CRITICAL, msg)

    def set_reload(self, msg: str = "") -> None:
        self._set_health(StatusEnum.RELOAD, msg)

    def is_ok(self) -> bool:
        if self._healt == StatusEnum.OK:
            return True
        else:
            return False

    def get_health_status(self) -> Dict[str, Any]:
        return {"health": self._health_msg, "message": self._health_msg}
