"""Funzioni ausiliarie utilizzate nei processi asincroni gestiti tramite Job Manager"""

import os
import time
import logging
import random
import string
from bdlpkg.utils.kube.services.ips import get_replicas_pod_info
from core.routines.entities import get_function_name
from core.exceptions import SmartOCRLayeraiException


def generate_random_string(length: int = 20) -> str:
    """
    Funzione che genere una stringa randomica di lunghezza predefinita, composta da una parte alfanumerica randomica e
    dal valore timestamp al tempo dell'esecuzione della funzione.

    :param length: lunghezza della componente alfanumerica della stringa. Default a 20.
    :type length: (int, optional)

    :return: stringa randomicamente generata
    :rtype: str

    """
    characters = string.ascii_lowercase + string.digits
    str_random = "".join(random.choices(population=characters, k=length))
    timestamp = int(time.time() * 1000)
    return f"{str_random}_{timestamp}"


def get_retrieve_address() -> str:
    """
    Funzione che restituisce l'indirizzo IP associato a un pod.

    :return: indirizzo ip del pod
    :rtype: str
    """
    str_pod_name = os.getenv("HOSTNAME", "")

    try:
        lst_replicas_info = get_replicas_pod_info()
        pod_info = next(
            (
                pod["ip"]
                for pod in lst_replicas_info
                if pod["targetRef"]["name"] == str_pod_name
            ),
            None,
        )

        if pod_info:
            return pod_info

        raise SmartOCRLayeraiException(
            f"Func {get_function_name()}: could not find pod ip address."
        )

    except Exception as e:
        logging.warning(
            f"Error while retrieving pod address: {e}. Returning empty pod-string (local only)"
        )
        return ""
