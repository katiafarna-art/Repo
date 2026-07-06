import logging
from bdlpkg.providers.gcp.settings.services.gcp_config import get_settings


def get_gcp_database_healthcheck() -> dict:
    """
    Perform a health check on GCP databases, specifically BigQuery, using the configured service accounts.

    :return: A dictionary containing the health check results for each BigQuery instance, keyed by service account name.
    :rtype: dict
    """
    _result: dict = {}
    _gcp_settings = get_settings()["service_account"]
    _result["bigquery"] = {}
    for sa_istance_name in _gcp_settings:
        logging.info(f"Executing healthcheck for {sa_istance_name} of type bigquery")
        from bdlpkg.providers.gcp.databases.services.BigQuery import (
                    get_bigquery_healthcheck,
                )
        _tmp = get_bigquery_healthcheck(sa_istance_name)

        _result["bigquery"][sa_istance_name] = _tmp

    return _result

