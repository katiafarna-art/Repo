import logging
from bdlpkg.providers.isp.settings.services.isp_config import get_settings
from typing import Optional


def get_storage_healthcheck() -> dict:
    """
    Perform a health check on all configured S3 storage buckets.

    This function retrieves the bucket settings from the application's configuration and performs 
    a health check on each bucket, returning the status of the keys present in each bucket.

    :return: A dictionary where the keys are the bucket names and the values are the results of the health checks.
             Each result contains either a list of keys in the bucket or an error message if the health check fails.
    :rtype: dict
    """
    _result = {}

    #Recupero settings bucket
    _settings = get_settings()["bucket"]    

    for _bucket in _settings:
        logging.info(f"Executing healthcheck for {_bucket} of type bucket s3")
        from bdlpkg.providers.isp.storages.services.BucketManager import get_bucket_healthcheck
        _result[_bucket] = get_bucket_healthcheck(_bucket)
        
    return _result


def get_metadata_healtcheck(resource_name: Optional[str] = None, key: Optional[str] = None) -> dict:
    """
    Perform metadata info retrieval on specified ISP S3 bucket (possibly for a specific key).

    This function retrieves performs retrieval of metadata for the selected bucket (according to its resource_name)
    returning information about last modification date and size.

    :param resource_name: the name of the s3 istance. Default: the first alphabetically, defaults to None
    :type resource_name: Optional[str], optional
    :param key: the key whose metadata is to be retrieved. Default: defaults to None, in this case a dict for all the keys is returned
    :type key: Optional[str], optional
    :return: A dictionary where the keys are the keys of selected bucket and the values are dictionaries containing information about last modification date and size.
             Each result contains either a dict with keys and information for each file in the bucket or an error message if the health check fails.
    :rtype: dict
    """
    _result = {}

    from bdlpkg.providers.isp.storages.services.BucketManager import get_metadata_info
    _result = get_metadata_info(resource_name, key)

    return _result