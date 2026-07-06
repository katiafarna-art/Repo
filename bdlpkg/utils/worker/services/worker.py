import os
from subprocess import check_output
import bdlpkg.utils.worker.services as kube_services


def get_pids(name: str) -> object:
    _path = os.path.dirname(os.path.abspath(kube_services.__file__))
    print(_path, " ", os.path.join(_path, "pidof.sh"))
    return map(int,
               check_output(["/usr/bin/sh",os.path.join(_path, "pidof.sh"), name]).split())


def kill_HUP() -> None:
    _pids = get_pids("gunicorn")
    for _pid in _pids:
        os.kill(_pid, 1)