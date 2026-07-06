import requests
from typing import Optional
import json

from bdlpkg.providers.isp.settings.services.apigtw_config import get_jwt_token
from bdlpkg.providers.gcp.settings.entities.sa.gcp import HashicorpEndpoint

def get_sa(cred_name: str, sa: str):
    """
    Retrieves service account details from HashiCorp Vault.

    :param cred_name: The name of the credentials used to fetch the JWT token.
    :type cred_name: str
    :param sa: The service account identifier (e.g., 'sa-isp-bdl10-appl-test-001').
    :type sa: str
    :return: None
    """
    print(cred_name)
    jwt_token = get_jwt_token(cred_name)
    
    #sa-isp-bdl10-appl-test-001
    #sa-isp-bdl10-appl-svil-001
    #sa-isp-bdl10-appl-prod-001
    ambiente = "produzione" if "prod" in sa else "systemtest"
    print(ambiente)
    sa_path = f"isp_non_pci/{ambiente}/data/0z/smp00/gcp/{sa}"

    resp2 = requests.post(
        url=HashicorpEndpoint.SYS.value,
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {jwt_token}'},
        json={
            'path': sa_path},
        verify=False)

    print(resp2.status_code)
    x = resp2.json()["data"]["data"][sa]
    y = json.loads(x)