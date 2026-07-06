import logging
from bdlpkg.providers.isp.settings.entities.jdbc.jdbc import JDBCSettings,JDBCConnectionType
from bdlpkg.providers.isp.settings.services.isp_config import get_settings


def get_database_healthcheck() -> dict:
    """Healtcheck for all database istances

    :return: a dict with the result of connection tests for all database istances
    :rtype: dict
    """
    _result: dict = {}
    _settings = get_settings()["database"]
    for ds_type in _settings:
        _result[ds_type] = {}
        for istance_name in _settings[ds_type]:
            logging.info(f"Executing healthcheck for {istance_name} of type {ds_type}")
            if ds_type == "mongo":
                from bdlpkg.providers.isp.databases.services.mongodb import (
                    get_mongo_healthcheck,
                )

                _tmp = get_mongo_healthcheck(istance_name)
            elif ds_type == "denodo":
                from bdlpkg.providers.isp.databases.services.denodo import (
                    get_denodo_healthcheck,
                )  # inside so it doesn't break the as is - TEST: OK

                _tmp = get_denodo_healthcheck(istance_name)
            elif ds_type == "oracle":
                from bdlpkg.providers.isp.databases.services.oracledb import (
                    get_oracle_healthcheck,
                )

                _tmp = get_oracle_healthcheck(istance_name)
            elif ds_type == "postgres":
                from bdlpkg.providers.isp.databases.services.postgresdb import (
                    get_postgres_healthcheck,
                )
                _tmp = get_postgres_healthcheck(istance_name)


            _result[ds_type][istance_name] = _tmp


    # region JDBC
    _settingsJDBC = get_settings()["jdbc"]
    _result["jdbc"] = {}
    if len(_settingsJDBC) > 0:
        for ds_type in _settingsJDBC:
            _result["jdbc"][ds_type] = {}
            if ds_type == "teradata":
                from bdlpkg.providers.isp.databases.services.teradata import (
                    get_teradata_healthcheck,
                )
                for istance_name in _settingsJDBC[ds_type]:
                    logging.info(f"Executing healthcheck for {istance_name} of type {ds_type}")
                    _tmp = get_teradata_healthcheck(istance_name)
                    _result["jdbc"][ds_type][istance_name] = _tmp

    # endregion JDBC

    return _result

