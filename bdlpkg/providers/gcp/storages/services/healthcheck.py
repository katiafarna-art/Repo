import logging
from bdlpkg.providers.gcp.settings.services.gcp_config import get_settings


def get_gcp_storage_healthcheck(gcs_bucket_name: str) -> dict:
    """
    Performs a health check on Google Cloud Storage (GCS) buckets, checking their availability for each service account.

    :param gcs_bucket_name: The name of the GCS bucket to check.
    :type gcs_bucket_name: str
    :return: A dictionary containing the health check results for each service account.
    :rtype: dict

    This function retrieves the configuration for each service account, then calls the `get_gcsbucket_healthcheck` function 
    to check the status of the specified GCS bucket for each service account. 
    The results are aggregated into a dictionary, where the keys are the service account names and the values are the health check results.
    """
    _result = {}

    #Recupero settings bucket  
    _sa_settings = get_settings()["service_account"]

    for _sa in _sa_settings:
        logging.info(f"Executing healthcheck for {_sa} of type bucket GCS")
        from bdlpkg.providers.gcp.storages.services.GCSBucketManager import get_gcsbucket_healthcheck
        _result[_sa] = get_gcsbucket_healthcheck(gcs_bucket_name, _sa)
        
    return _result