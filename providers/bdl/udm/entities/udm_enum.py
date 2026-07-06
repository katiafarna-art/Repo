from enum import Enum
from typing_extensions import Literal


class UDMDataType(Enum):
    """
    Enum representing different types of data in UDM.

    :param DF: Represents a DataFrame type.
    :type DF: int
    """
    DF = 1


class UDMDataEngine(Enum):
    """
    Enum representing different types of data engines used for UDM.

    :param PANDAS: Represents a Pandas-based data engine.
    :type PANDAS: int
    """
    PANDAS = 1


class UDMDMEnv(str, Enum):
    """
    Enum representing different environments for UDM.

    This Enum defines the possible environments in which a UDM can operate, such as sandbox, development, test, or production.

    :param VM_SANDBOX: Virtual machine sandbox environment.
    :type VM_SANDBOX: str
    :param svil: Development environment.
    :type svil: str
    :param test: Testing environment.
    :type test: str
    :param prod: Production environment.
    :type prod: str
    :param svis: Svis environment.
    :type svis: str
    :param ptes: Ptes environment.
    :type ptes: str
    """
    VM_SANDBOX = "vm_sandbox"
    svil = "svil"
    test = "test"
    prod = "prod"
    svis = "svis"
    ptes = "ptes"


class HTTP_VERB(str, Enum):
    """
    Enum representing HTTP verbs used in API requests.

    :param GET: Represents an HTTP GET request.
    :type GET: str
    :param POST: Represents an HTTP POST request.
    :type POST: str
    """
    GET = 'GET'
    POST = 'POST'

UDMDM4SqlTimeUnit = Literal['days','months','years']
UDMDM4SqlTypes_oracle = Literal['oracle']
UDMDM4SqlTypes_denodo = Literal['denodo']
UDMDM4SqlTypes_postgres = Literal['postgres']
UDMDM4SqlTypes_teradata = Literal['teradata']
UDMDM4SqlTypes = Literal['oracle', 'denodo', 'postgres', 'teradata']
UDMDM4FileTypes = Literal['file', 's3', 'gcs', 'pickle', 'pkl', 'obj', 'csv']
UDMDM4FileTypes_s3 = Literal['s3']
UDMDM4FileTypes_gcs = Literal['gcs']
UDMDM4ApiTypes = Literal['api', 'get', 'post']
UDMDM4MongoTypes = Literal['mongo']
