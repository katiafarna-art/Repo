from enum import Enum
from typing import Dict, Union, Optional, List, Any
from typing_extensions import Literal
from pydantic import BaseModel, Field, Json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re

from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDMEnv, HTTP_VERB, UDMDataEngine
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4SqlTimeUnit
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4SqlTypes
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4FileTypes
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4ApiTypes
from bdlpkg.providers.bdl.udm.entities.udm_enum import UDMDM4MongoTypes
from bdlpkg.utils.bdlfile.entities.annotated import HttpUrl, FileUrl


class UDMDM4Mongo(BaseModel):
    """
    A model for MongoDB data requests within UDM.

    This class defines the structure for MongoDB queries, including the collection name,
    the query itself, and an optional projection for filtering the result fields.

    :param udmdm_type: The type of MongoDB request (defined by UDMDM4MongoTypes).
    :type udmdm_type: UDMDM4MongoTypes
    :param collection: The name of the MongoDB collection.
    :type collection: str
    :param query: The MongoDB query to be executed.
    :type query: dict
    :param projection: Optional projection for MongoDB, specifying which fields to include or exclude.
    :type projection: Optional[dict]
    """
    udmdm_type: UDMDM4MongoTypes
    collection: str = Field(..., title="collection name")
    query: dict = Field(..., title="query for mongo")
    projection: Optional[dict] = Field(
        {},
        title="projection for mongo",
        description="define a dict with: name: 0 or 1")


class UDMDM4SqlListMapping(BaseModel):
    """
    A model for SQL statement list mappings in UDM.

    This class defines the structure for mapping SQL statements to UDM.

    :param statement: The SQL statement to be mapped.
    :type statement: str
    :param udm_name: The name of the UDM to map.
    :type udm_name: str
    """
    statement: str
    udm_name: str = Field(..., title="reference to existing UDM")


class UDMDM4SqlNested(BaseModel):
    """
    A model for nested SQL statements in UDM.

    This class defines the structure for SQL statements that can contain nested statements.

    :param key: The key to identify nested statements.
    :type key: str
    :param statement: The SQL statement.
    :type statement: str
    :param nested_statement: Optional list of nested SQL statements.
    :type nested_statement: Optional[List[UDMDM4SqlNested]]
    """
    key: str
    statement: str = Field(..., title="statement for SQL")
    nested_statement: Optional[List['UDMDM4SqlNested']] = Field(None,
        title="nested statement for SQL")


class UDMDM4Sql(BaseModel):
    """
    A model for SQL data requests within UDM.

    This class defines the structure for SQL queries, including the SQL statement itself,
    optional nested statements, and filtering options like time units and periods.

    :param udmdm_type: The type of SQL request (defined by UDMDM4SqlTypes).
    :type udmdm_type: UDMDM4SqlTypes
    :param statement: The main SQL statement.
    :type statement: str
    :param nested_statement: Optional nested SQL statements.
    :type nested_statement: Optional[List[UDMDM4SqlNested]]
    :param timeunit: The time unit for filtering data (e.g., days, months).
    :type timeunit: Optional[UDMDM4SqlTimeUnit]
    :param periods: The number of time units for filtering data.
    :type periods: Optional[int]
    :param mapping: Optional mappings for list from existing UDM.
    :type mapping: Optional[List[UDMDM4SqlListMapping]]
    """
    udmdm_type: UDMDM4SqlTypes
    statement: str = Field(None, title="statement for SQL")
    nested_statement: Optional[List[UDMDM4SqlNested]] = Field(None,
        title="nested statement item for SQL")
    timeunit: Optional[UDMDM4SqlTimeUnit] = Field(None, title="time unit for filtering")
    periods: Optional[int] = Field(None, title="number of time unit for filtering")
    mapping: Optional[List[UDMDM4SqlListMapping]] = Field(None,
        title="mapping for list from existing UDM")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.statement = self.get_full_statement()
        if self.timeunit is not None and self.periods is not None:
            self.statement = self.get_full_ranged_statement()

    @staticmethod
    def _get_statement(statement: str,
                       nested_statments: List[UDMDM4SqlNested]) -> str:
        """
        Recursively replace placeholders in the SQL statement with the corresponding nested statements.

        This method processes nested SQL statements, replacing placeholders (keys) with their actual statements. 
        If a nested statement contains further nested statements, it recursively resolves them.

        :param statement: The SQL statement containing placeholders.
        :type statement: str
        :param nested_statements: A list of nested SQL statements.
        :type nested_statements: List[UDMDM4SqlNested]
        :return: The SQL statement with all placeholders replaced by their corresponding nested statements.
        :rtype: str
        """
        for _nested in nested_statments:
            if _nested.nested_statement is None:
                statement = statement.replace(_nested.key, _nested.statement)
            else:
                statement = statement.replace(
                    _nested.key,
                    UDMDM4Sql._get_statement(_nested.statement,
                                             _nested.nested_statement))
        return statement

    def get_full_statement(self) -> str:
        """
        Generate the full SQL statement by resolving any nested statements.

        This method processes the SQL statement by resolving any nested statements and replacing
        the placeholders with the appropriate SQL sub-statements.

        :return: The full SQL statement with all nested statements resolved.
        :rtype: str
        """
        if self.nested_statement is None:
            return self.statement
        else:
            return UDMDM4Sql._get_statement(self.statement,
                                            self.nested_statement)
        
    def get_full_ranged_statement(self):
        """
        Generate a full SQL statement with date range filters applied.

        This method modifies the SQL statement by applying date range filters based on the 
        specified time unit and periods. The start date and end date are calculated, and the 
        placeholders "START_DATE" and "END_DATE" in the SQL statement are replaced with the 
        actual date values.

        :return: The SQL statement with the date range applied.
        :rtype: str
        """
        kwargs = {self.timeunit:self.periods}
        
        if re.search("TO_DATE",self.statement):
            end_date = re.findall(r'\d+-\d+-\d+', self.statement)[0]
        else: 
            end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.strptime(end_date,'%Y-%m-%d') - relativedelta(**kwargs)).strftime('%Y-%m-%d') #start_date is function of end_date

        #Different order of parameters in Denodo date transformation function
        if self.udmdm_type != 'denodo':
            self.statement = self.statement.replace("START_DATE",f"TO_DATE('{start_date}', 'YYYY-MM-DD')")
            self.statement = self.statement.replace("END_DATE",f"TO_DATE('{end_date}', 'YYYY-MM-DD')")
        else:
            self.statement = self.statement.replace("START_DATE",f"TO_DATE('yyyy-MM-dd','{start_date}')")
            self.statement = self.statement.replace("END_DATE",f"TO_DATE('yyyy-MM-dd','{end_date}')")
        return self.statement
    


class UDMDM4File(BaseModel):
    """
    A model for file-based data requests within UDM.

    This class defines the structure for requesting data from files, including the file name, 
    path, and an optional filter.

    :param udmdm_type: The type of file request (defined by UDMDM4FileTypes).
    :type udmdm_type: UDMDM4FileTypes
    :param filename: The name of the file including extensions.
    :type filename: str
    :param path: The absolute path of the file.
    :type path: Union[FileUrl, str]
    :param filter: Optional filter to apply when reading the file.
    :type filter: Optional[dict]
    """
    udmdm_type: UDMDM4FileTypes
    filename: str = Field(..., title="filename with extensions")
    path: Union[FileUrl, str] = Field(..., title="absolute path")
    filter: Optional[dict] = Field(None, title="filter")


class UDMDM4Api(BaseModel):
    """
    A model for API-based data requests within UDM.

    This class defines the structure for API requests, including the API URL, 
    payload, and HTTP verb (e.g., GET, POST).

    :param udmdm_type: The type of API request (defined by UDMDM4ApiTypes).
    :type udmdm_type: UDMDM4ApiTypes
    :param url: The URL of the API.
    :type url: HttpUrl
    :param payload: The JSON payload to send with the request.
    :type payload: Json
    :param http_verb: The HTTP verb to use (e.g., GET, POST).
    :type http_verb: HTTP_VERB
    """
    udmdm_type: UDMDM4ApiTypes
    url: HttpUrl = Field(..., title="API URL")
    payload: Json = Field(..., title="API Payload")
    http_verb: HTTP_VERB = Field(..., title="HTTP Verb")


class UDMDMResource(BaseModel):
    """
    A model representing the resource configuration for UDM.

    :param type: The type of the resource.
    :type type: str
    :param name: The name of the resource in isp-config-env.
    :type name: str
    """
    type: str = Field(..., title="type of resource")
    name: str = Field(..., title="name in isp-config-env")


class UDMDMEngine(BaseModel):
    """
    A model representing the data engine configuration for UDM.

    :param params: The parameters passed to the engine.
    :type params: dict
    :param type: The type of the data engine (e.g., PANDAS).
    :type type: UDMDataEngine
    """
    params: dict = Field({},
                         title="parameters",
                         description="parameters to be passed to the engine")
    type: UDMDataEngine = Field(UDMDataEngine.PANDAS)


class UDMDM(BaseModel):
    """
    The main model for Universal Data Model (UDM) requests.

    This class represents a UDM data model, allowing the definition of various data sources (e.g., MongoDB, SQL, API, File),
    environment configurations, and the engine responsible for processing the request. It supports different types of requests 
    via the `request` field, which is a union of multiple request types (e.g., `UDMDM4Mongo`, `UDMDM4Sql`, `UDMDM4File`, `UDMDM4Api`).

    :param name: The name of the data model.
    :type name: str
    :param env: Optional. The environment for the UDM, such as dev, test, or production. It will be overridden if a duplicate with the same name is found.
    :type env: Optional[UDMDMEnv]
    :param resource: The resource configuration, which defines the data source for the UDM (e.g., database, API).
    :type resource: UDMDMResource
    :param request: The request to be made to the data source, which can be a MongoDB query, SQL statement, file access, or API request. The type is automatically determined by the `udmdm_type` discriminator.
    :type request: Union[UDMDM4Mongo, UDMDM4Sql, UDMDM4File, UDMDM4Api]
    :param engine: The data engine responsible for processing the request, such as pandas or SQL engine. Defaults to a pandas engine.
    :type engine: UDMDMEngine
    """
    name: str = Field(..., title="name of data model")
    env: Optional[UDMDMEnv] = Field(
        default=None,
        title="environment"
    )    #sovrascrivo con l'ambiente corrente se presente un duplicato con lo stesso nome
    resource: UDMDMResource
    request: Union[UDMDM4Mongo, UDMDM4Sql, UDMDM4File,
                   UDMDM4Api] = Field(..., discriminator='udmdm_type')
    engine: UDMDMEngine = Field(UDMDMEngine())
