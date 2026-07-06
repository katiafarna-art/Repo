"""Modulo contenente funzioni ausiliarie per la generazione jwt token necessario all'interazione con il layerai"""

from base64 import b64encode
from core.routines.entities import session, get_function_name
from core.exceptions import SmartOCRLayeraiException

api_gateway_endpoints = {
    "svil": "https://tservizibe-ggai0-ai4y.syssede.systest.sanpaoloimi.com",
    "test": "https://servizibe-ggai0-ai4y.syssede.systest.sanpaoloimi.com",
    "prod": "https://servizibe-ggai0-ai4y.sede.corp.sanpaoloimi.com",
}


def encode_auth_header(client_id: str, client_secret: str) -> str:
    """
    Encodes the client ID and client secret into a Base64-encoded authorization header value.

    :param client_id: The client ID for the authentication.
    :type client_id: str
    :param client_secret: The client secret for the authentication.
    :type: str

    :return: The Base64-encoded string that represents the `client_id` and `client_secret`.
    :rtype: str
    """
    basic = b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    return basic


def get_jwt_token(client_id: str, client_secret: str, env: str = "prod") -> str:
    """
    Retrieves the jwt token from the api gateway for the provided client_id, client_secret and environment

    :param client_id: The client ID for the authentication.
    :type client_id: str
    :param client_secret: The client secret for the authentication.
    :type: str
    :param env: The environment used to determine the correct API gateway endpoint. Default a 'prod'
    :type: str

    :return: The JWT token retrieved from the API gateway, if the authentication is successful.
    :rtype: str
    """
    basic = encode_auth_header(client_id, client_secret)
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {basic}",
    }
    response = session.post(
        f"{api_gateway_endpoints[env]}/auth/oauth/v2/token",
        headers=headers,
        data={"grant_type": "gen_jwt", "scope": "ai4y0"},
        verify=False,
    )

    if response.status_code != 200:
        raise SmartOCRLayeraiException(
            msg=f"Func {get_function_name()}: error while getting JWT token - > {response.text}",
            status_code=response.status_code
        )

    return response.json()["access_token"]
