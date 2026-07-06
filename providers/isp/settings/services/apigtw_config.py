import requests
import base64
from fastapi import status, HTTPException
from typing import Optional

from bdlpkg.providers.isp.settings.entities.token.jwt import APIGatewayCredentials


def get_jwt_token(cred_name: Optional[str] = None) -> str:
    """
    Return the JWT token given by API gateway
    :param cred_name: the name of the credentials name
    :type cred_name: String
    :param env: environment from which to retrieve token
    :type env: String
    :return: JWT Token
    :rtype: String
    """
    _credentials = APIGatewayCredentials.get_credentials(cred_name)

    b = base64.b64encode(
        bytes(f"{_credentials.ClientID}:{_credentials.ClientSecret.get_secret_value()}", 'utf-8'))  # bytes
    base64_str = b.decode('utf-8')  # convert bytes to string
    resp = requests.post(
        url=_credentials.Url,
        headers={'Content-Type': 'application/x-www-form-urlencoded',
                 'Authorization': f'Basic {base64_str}'},
        data={'grant_type': 'gen_jwt', 'scope': _credentials.Scope},
        verify=False)
    
    if resp.status_code == status.HTTP_200_OK:
        return resp.json()["access_token"]
    else:
        raise HTTPException(status_code=401, detail="Wrong credentials")