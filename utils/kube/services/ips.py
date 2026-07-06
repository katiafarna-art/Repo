import logging
import os
import httpx
from typing import List, Dict, Any, Tuple, Union

SERVICE_ACCOUNT = "/var/run/secrets/kubernetes.io/serviceaccount"


def _get_data_of_pod(_prj: str = "", _pod_name: str = "") -> Dict[Any, Any]:

    if _prj == "":
        if "ISP_AMBIENTE" in os.environ:    # build sempre in CICD, quindi OPENSHIFT_BUILD_NAMESPACE risponde "cicd"
            _prj = f"bdl10-{os.environ['ISP_AMBIENTE']}".lower()
        else:
            raise ValueError(
                "No default value available in ISP_AMBIENTE")

    if _pod_name == "":
        if "HOSTNAME" in os.environ:
            _pod_name = os.environ["HOSTNAME"].rsplit("-", 2)[0]
        else:
            raise ValueError("No default value available in HOSTNAME")

    _token = None
    _token_position = f'{SERVICE_ACCOUNT}/token'
    if os.path.isfile(_token_position):
        with open(_token_position) as f:
            _token = f.readlines()
        if _token is not None:
            _r = httpx.get(
                f'https://kubernetes.default.svc/api/v1/namespaces/{_prj}/endpoints/{_pod_name}',
                headers={"Authorization": f"Bearer {_token[0]}"},
                verify=False)
            return _r.json()

    raise ValueError(f"No token available in {_token_position}")


def _get_ips_of_pods(_dict: Dict) -> List:
    _ips: List = []
    if "subsets" in _dict:
        if len(_dict["subsets"]) > 0:
            if "addresses" in _dict["subsets"][0]:
                _l = _dict["subsets"][0]["addresses"]
                for _container in _l:
                    _ips.append(_container["ip"])
    return _ips


def get_replicas_pod_ips() -> List:
    return _get_ips_of_pods(_get_data_of_pod())


def _get_info_of_pods(_dict: Dict) -> List:
    _pods: List = []
    if "subsets" in _dict:
        if len(_dict["subsets"]) > 0:
            if "addresses" in _dict["subsets"][0]:
                _pods = _dict["subsets"][0]["addresses"]
    return _pods


def get_replicas_pod_info() -> List:
    return _get_info_of_pods(_get_data_of_pod())


def _get_k8s_token(_prj: str = "", _pod_name: str = "") -> Tuple[str, str, str]:
    """Retrieve Token from SERVICE_ACCOUNT

    Args:
        _prj (str, optional): _description_. Defaults to "".
        _pod_name (str, optional): _description_. Defaults to "".

    Returns:
        Tuple[str,str,str]: [_prj,_pod_name,_token]
    """

    if _prj == "":
        if "ISP_AMBIENTE" in os.environ:    # ora le build sono sempre in CICD, quindi OPENSHIFT_BUILD_NAMESPACE risponde "cicd" or "bdl10-cicd". Pensavo di usare ISP_AMBIENTE
            _prj = f"bdl10-{os.environ['ISP_AMBIENTE']}".lower()
        else:
            raise ValueError("No default value available in ISP_AMBIENTE")

    if _pod_name == "":
        if "HOSTNAME" in os.environ:
            _pod_name = os.environ["HOSTNAME"]
        else:
            raise ValueError("No default value available in HOSTNAME")

    # info @ https://kubernetes.io/docs/tasks/run-application/access-api-from-pod/
    _token = None
    _token_position = f'{SERVICE_ACCOUNT}/token'
    if os.path.isfile(_token_position):
        with open(_token_position) as f:
            _token = f.readlines()

        return _token, _prj, _pod_name

    raise ValueError(f"No token available in {_token_position}")


def _get_pod_conf(_prj: str = "", _pod_name: str = "") -> Dict[Any, Any]:
    """ Call v1/namespaces/{_prj}/pods/{_pod_name}

    Args:
        _prj (str, optional): namespace. Defaults to "".
        _pod_name (str, optional): pod name. Defaults to "".

    Raises:
        ValueError: Token not found

    Returns:
        Dict[Any, Any]: YAML
    """

    _token, _prj, _pod_name = _get_k8s_token(_prj, _pod_name)

    if _token is not None:
        _r = httpx.get(
            f'https://kubernetes.default.svc/api/v1/namespaces/{_prj}/pods/{_pod_name}',
            headers={"Authorization": f"Bearer {_token[0]}"},
            verify=f"{SERVICE_ACCOUNT}/ca.crt")
        return _r.json()


def get_cpu_limit() -> Union[float, int]:
    """Get the cpu limit. If not in container, return cpu_count. Float for millicores (/1000)

    Returns:
        int: limit of cpu or cpu_count
    """
    try:
        _res = _get_pod_conf(
        )['spec']['containers'][0]['resources']['limits']['cpu']

        if 'm' in _res:    # https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu
            return float(_res.replace('m', "").strip()) / 1000
        else:
            return int(_res)
    except ValueError as exp:
        logging.debug("K8s API not found. CPU limits via MT.cpu_count")
        from multiprocessing import cpu_count
        return cpu_count()
