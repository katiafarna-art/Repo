import os
from enum import Enum
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings
from typing_extensions import Literal, Union

Scopes = Literal['bdl1','ai4y0']
Environments = Literal['SYST','PROD']

class APIGatewayCredentials(BaseSettings):
    """
    Settings for API Gateway credentials.
    :param credentials_name: The resource name for the API Gateway.
    :type credentials_name: str
    :param ClientID: The client ID for authentication.
    :type ClientID: str
    :param ClientSecret: The client secret for authentication.
    :type ClientSecret: SecretStr
    :param Scope: The scope for the API Gateway. Defaults to 'bdl1'.
    :type Scope: str, optional
    """
    credentials_name: str = Field(...)
    ClientID: str = Field(...)
    ClientSecret: SecretStr = Field(...)
    Scope: Scopes = Field("bdl1")
    Env: Environments = Field("PROD")
    Url: Union[str,None] = Field(None)

    @field_validator("Env",mode="before")
    def normalize_categoria(cls, Env):
        if isinstance(Env, str):
            return Env.upper()
    
    @field_validator("Url")
    def validate_url(cls, Url, values):
        if Url is None:
            Scope = values.data["Scope"]
            Env = values.data["Env"]
            if Scope == "bdl1":
                Url = APIGatewayEndpoint_BDL[Env].value
            else:
                Url = APIGatewayEndpoint_AI4Y0[Env].value
        return Url

    @staticmethod
    def get_credentials(credentials_name: str) -> 'APIGatewayCredentials':
        """Return the APIGatewayCredentials using config data

        :param credentials_name: the resource name
        :type credentials_name: str
        :param config_path: the path where to look at for configuration
        :type config_path: str
        :return: the credential obj
        :rtype: APIGatewayCredentials
        """
        if "DS_CONF_DIR" in os.environ:
            _config_path=os.environ["DS_CONF_DIR"]
        else:
            if "APP_CONF_DIR" in os.environ:
                _config_path=os.environ["APP_CONF_DIR"]
            else:
                _config_path="."
        
        dirs = os.listdir(os.path.join(_config_path, "apigtw")) if os.path.exists(os.path.join(_config_path, "apigtw")) else []
        if len(dirs) == 0:
            raise ModuleNotFoundError(
                        f"no credentials available of type api_gateway")

        if credentials_name is None:    
            name = dirs[0]    #default name to first occurence, in case of credentials_name is None
            env = os.path.join(_config_path, "apigtw", name, ".env")
        else:
            for name in dirs:
                if credentials_name in dirs:
                    if credentials_name == name:
                        env = os.path.join(_config_path, "apigtw", name, ".env")
                        break
                else:
                    raise ModuleNotFoundError(
                        f"no credentials available for {credentials_name} of type api_gateway")

        if os.path.isfile(env):
            return APIGatewayCredentials(
                credentials_name=name, _env_file=env, _env_file_encoding="utf-8")


class APIGatewayEndpoint_BDL(str, Enum):
    """
    Enum representing the API Gateway OAuth2 token endpoints for BDL10.
    
    - SYST: System test environment endpoint.
    - PROD: Production environment endpoint.
    """
    SYST = 'https://gwad0-test.syssede.systest.sanpaoloimi.com/auth/oauth/v2/token'
    PROD = 'https://gwad0-prod.sede.corp.sanpaoloimi.com/auth/oauth/v2/token'

class APIGatewayEndpoint_AI4Y0(str, Enum):
    """
    Enum representing the API Gateway OAuth2 token endpoints for AI4Y0.
    
    - SYST: System test environment endpoint.
    - PROD: Production environment endpoint.
    """
    SYST = 'https://servizibe-ggai0-ai4y.syssede.systest.sanpaoloimi.com/auth/oauth/v2/token'
    PROD = 'https://servizibe-ggai0-ai4y.sede.corp.sanpaoloimi.com/auth/oauth/v2/token'