#https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python

from io import BytesIO
from typing import Any, Optional, Tuple, List, Dict, Union
from multiprocessing import Lock

from fastapi import HTTPException, status
from bdlpkg.utils.metaclasses import Singleton
from bdlpkg.providers.isp.settings.entities.storage.s3 import S3BucketSettings
from bdlpkg.providers.isp.settings.services.isp_config import get_datasource_settings, get_settings
from bdlpkg.providers.isp.storages.services.s3bucket import delete_file, download_file, exists_key, get_keys, get_keys_metadata, get_s3_resource, upload_file, upload_file_from_path, download_file_in_memory
from builtins import bytes


class BucketManager(metaclass=Singleton):
    """
    Singleton class to abstract the managment of storage buckets.

    This class provides an abstraction for managing S3 bucket resources. It handles operations such as 
    uploading, downloading, listing, and deleting files in S3 buckets, and ensures that resources are stored 
    in memory and locked appropriately to avoid concurrency issues.

    :ivar _resources: A dictionary storing locks and S3 resources for each bucket.
    :vartype _resources: Dict[str, Tuple[Lock, Any]]
    """
    _resources: Dict[str, Tuple[Lock, Any]] = {}    #type:ignore

    def __init__(self) -> None:
        self._init_resources()

    def _init_resources(self) -> None:
        """
        Initialize the resources associate to the buckets storing them in memory
        """
        _buckets_settings = get_settings()["bucket"]
        if len(self._resources) == 0:
            for bucket in _buckets_settings:
                self._resources[bucket] = (Lock(), get_s3_resource(bucket))

    def _get_resource(
        self,
        resource_name: Optional[str] = None
    ) -> Tuple[Lock, Any]:    #type:ignore
        """
        Retrieve the resource associated to the name passed as parameter and the related lock semaphore.

        :param resource_name: the name of the s3 istance that must pair with the name on the secret. Default: the first alphabetically, defaults to None
        :type resource_name: Optional[str], optional
        :return: a tuple containing the bucket resource and the associated lock semaphore
        :rtype: Tuple[Lock, Any]
        """
        #double check presenza configurazione del bucket
        s3i: S3BucketSettings = get_datasource_settings("bucket", None,
                                                        resource_name)
        return self._resources[s3i.resource_name]

    def get_keys(self, resource_name: Optional[str] = None) -> List[str]:
        """
        Give the bucket name and a resource, return the list of keys present in the bucket
        :param resource_name: the resource connected to s3, defaults to None
        :type resource_name: Optional[str], optional
        :return: a list with all the key names present in the bucket, an empty list otherwise
        :rtype: List[str]
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return get_keys(_resource, None)
        
    def get_keys_metadata(self, resource_name: Optional[str] = None, key: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Given the bucket name and a resource, return the dict with the list of keys present in the bucket with associated last modified timestamp and size     
        
        :param resource_name: the resource connected to s3, defaults to None    
        :type resource_name: Optional[str], optional
        :param key: the key whose metadata is to be retrieved. Default: defaults to None, in this case a dict containing information on all the keys in the bucket is returned
        :type key: Optional[str], optional    
        :return: a dictionary having as keys the keys of selected bucket and values the dictionaries with metadata    
        :rtype: Dict[str, Dict[str, Any]]
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return get_keys_metadata(_resource, None, key)

    def exists_key(self, key: str, resource_name: Optional[str] = None) -> bool:
        """
        Given a bucket name, a key and a resource return if that key exists on the bucket
        :param key: the name of the file/folder to search
        :type key: str
        :param resource_name: the resource to connect to s3, defaults to None
        :type resource_name: Optional[str], optional
        :return: True if the key exists, False otherwise
        :rtype: bool
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return exists_key(key, _resource, None)

    def upload_file(self,
                    destination_key: str,
                    file_content: bytes,
                    resource_name: Optional[str] = None) -> bool:
        """
        Upload a file content in bytes on s3 bucket
        :param destination_key: the name of the file (the key) to store on s3
        :type destination_key: str
        :param file_content: the bytes content of the file
        :type file_content: bytes
        :param resource_name: the resource to connecto to s3, defaults to None
        :type resource_name: Optional[str], optional
        :return: True if the operation succeeded, False otherwise
        :rtype: bool
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return upload_file(destination_key, file_content, _resource, None)

    def upload_file_from_path(self,
                              file_path: str,
                              destination_path: Optional[str] = None,
                              resource_name: Optional[str] = None) -> bool:
        """
        :param file_path: the physical path where the file is stored
        :type file_path: str
        :param destination_path: the path on s3 where to store data. If missing, the file will be saved in the root with the original name. If the destination path contains a final extension the file will inherit the new name. 
        :type destination_path: str
        :param resource_name: the resource to connect to s3, defaults to None
        :type resource_name: Optional[str], optional
        :return: True if the operation succeeded, False otherwise
        :rtype: bool
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return upload_file_from_path(file_path, destination_path, _resource,
                                         None)

    def download_file(self,
                      download_key: str,
                      download_path: str,
                      resource_name: Optional[str] = None) -> bool:
        """
        Download a file from s3 to the path specified
        :param download_key: the name of the file (the key) on s3
        :type download_key: str
        :param download_path: the local path where download the file. The destination MUST exist.
        :type download_path: str
        :param resource_name: the resource to connect to s3, defaults to None
        :type resource_name: Optional[str], optional
        :return: True if the operation succeeded, False otherwise
        :rtype: bool
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return download_file(download_key, download_path, _resource, None)

    def download_file_in_memory(self,
                                download_key: str,
                                resource_name: Optional[str] = None) -> BytesIO:
        """
        Download a file from s3 in memory
        :param download_key: the name of the file (the key) on s3
        :type download_key: str
        :param resource_name: the resource to connect to s3, defaults to None
        :type resource_name: Optional[str], optional
        :return: a bytestream if the operation succeeded, None otherwise
        :rtype: bytes
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return download_file_in_memory(download_key, _resource, None)

    def delete_file(self,
                    delete_key: str,
                    resource_name: Optional[str] = None) -> bool:
        """
        Delete a file from s3 bucket
        :param delete_key: the name of the file (the key) on s3
        :type delete_key: str
        :param resource_name: the resource to connect to s3, defaults to None
        :type resource_name: Optional[str], optional
        :return: True if the operation succeeded, False otherwise
        :rtype: bool
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return delete_file(delete_key, _resource, None)


def get_bucket_healthcheck(
    bucket_istance_name: Optional[str] = None
) -> Dict[str, Union[str, List[str]]]:
    """
    Performe the healthcheck on the s3 bucket to check its status, 
    giving back the list of keys for each bucket

    :param bucket_istance_name: the name of the s3 istance that must pair with the name on the secret. Default: the first alphabetically, defaults to None
    :type bucket_istance_name: Optional[str], optional
    :return: a dictionary having all the keys in the s3 bucket
    :rtype: dict
    """
    result: Dict[str, Union[str, List[str]]] = {}
    try:
        bm = BucketManager()
        result["keys"] = bm.get_keys(bucket_istance_name)
    except Exception as e:
        result["error"] = str(e)

    return result

def get_metadata_info(
    bucket_istance_name: Optional[str] = None,
    key: Optional[str] = None) -> Dict[str, Union[str, Dict[str, Dict[str, Any]]]]:
    """
    Perform the healthcheck on the s3 bucket to get information about keys (last modified date and size)

    :param bucket_istance_name: the name of the s3 istance that must pair with the name on the secret. Default: the first alphabetically, defaults to None
    :type bucket_istance_name: Optional[str], optional
    :param key: the key whose metadata is to be retrieved. Default: defaults to None, in this case a dict containing information on all the keys in the bucket is returned
    :type key: Optional[str], optional
    :return: a dictionary having as keys the keys of selected bucket and values the dictionaries with metadata.
    :rtype: dict
    """
    result: Dict[str, Union[str, Dict[str, Dict[str, Any]]]] = {}
    try:
        bm = BucketManager()
        result = bm.get_keys_metadata(bucket_istance_name, key)
    except ModuleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=str(e))

    return result