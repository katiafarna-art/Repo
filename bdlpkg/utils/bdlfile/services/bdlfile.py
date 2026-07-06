import logging
from typing import Any, List, Dict, Optional, Union
import yaml
import os
from distutils.util import strtobool
from pathlib import Path, PurePath
from bdlpkg.utils.bdlfile.entities.bdlfile import FileBaseModel


def get_obj_from_file(file_obj: FileBaseModel,
                      check_file: bool = True) -> object:
    if check_file:
        _file = Path(file_obj.fullpath)
        if not _file.is_file():
            raise FileNotFoundError(f'{file_obj.fullpath} not found')

    if file_obj.extension == ".yaml":
        with open(file_obj.fullpath, 'rb') as file:
            _obj = yaml.load(file, Loader=yaml.FullLoader)
        return _obj
    else:
        raise ValueError(f'{file_obj.extension} not managed.')


def get_obj_from_path(path: str,
                      check_file: bool = True,
                      prefix_path: Optional[str] = None) -> object:

    if prefix_path is not None:
        path = os.path.join(prefix_path, path)

    file_obj = FileBaseModel(filename=PurePath(path).name,
                             fullpath=os.path.abspath(path),
                             extension=''.join(PurePath(path).suffixes))

    return get_obj_from_file(file_obj, check_file=check_file)


def get_obj_from_config_path(path: str, check_file: bool = True) -> Dict[Any, Any]:
    return get_obj_from_path(path, check_file, prefix_path=_get_config_path())


def get_files_list_config_path(path: str = "",
                               extension_filter: List[str] = []) -> List[str]:
    return get_files_list_from_path(_get_config_path(path), extension_filter)


def get_files_list_from_path(path: str = "",
                             extension_filter: List[str] = []) -> List[str]:
    _res: List[str] = []

    if os.path.isfile(os.path.abspath(path)):
        _res.append(os.path.abspath(path))
        return _res

    for root, dirs, files in os.walk(
            os.path.abspath(path),
            topdown=False,
            followlinks=False,
    ):
        for name in files:
            if not name[0] == ".":
                _fullname = os.path.join(root, name)
                if len(extension_filter) == 0 or os.path.splitext(
                        _fullname)[1] in extension_filter:
                    _res.append(_fullname)
    return _res


def _get_config_path(suffix_path: str = "") -> str:

    _base_path = ""
    if "MY_HOME" in os.environ:
        _base_path = os.environ["MY_HOME"]
    else:
        logging.warning("MY_HOME not found in os env. base_path now is {}")
        _base_path = "./"
    return os.path.join(_base_path, "prj/app/config", suffix_path)


def str_to_bool(value: Union[str,bool]) -> Union[bool,str]:
    try:
        if isinstance(value, str):
            return bool(strtobool(value))
        else:
            return value
    except ValueError:
        # Return input value if strtobool fails
        return value