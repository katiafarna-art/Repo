#https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python

from io import BytesIO
from typing import Any, Optional, Tuple, List, Dict, Union
from multiprocessing import Lock
from bdlpkg.utils.metaclasses import Singleton
from bdlpkg.providers.gcp.storages.services.GCSbucket import GCS
from bdlpkg.providers.gcp.settings.entities.sa.gcp import SASettings   
from bdlpkg.providers.gcp.settings.services.gcp_config import get_datasource_settings, get_settings
from builtins import bytes


class GCSBucketManager(metaclass=Singleton):
    """
    Singleton class to abstract the managment of storage buckets.
    """
    _resources: Dict[str, Tuple[Lock, Any]] = {}    #type:ignore

    def __init__(self) -> None:
        self._init_clients()

    def _init_clients(self) -> None:
        """
        Initialize the clients associate to the buckets storing them in memory
        """
        _sa_settings = get_settings()["service_account"]
        if len(self._resources) == 0:
            for sa in _sa_settings:
                self._resources[sa] = (Lock(), GCS(sa))

    def _get_resource(
        self,
        resource_name: Optional[str] = None
    ) -> Tuple[Lock, Any]:    #type:ignore
        """
        Retrieve the resource associated to the name passed as parameter and the related lock semaphore.

        :param resource_name: the name of the sa istance. Default: the first alphabetically, defaults to None
        :type resource_name: Optional[str], optional
        :return: a tuple containing the sa resource and the associated lock semaphore
        :rtype: Tuple[Lock, Any]
        """
        sai: SASettings = get_datasource_settings("service_account", resource_name)

        return self._resources[sai.sa_istance_name]

    def get_blobs(self,
                  bucket_name: str,
                  resource_name: Optional[str] = None) -> List[str]:
        """
        Give the bucket name and a resource, return the list of blobs present in the bucket
        :param bucket_name: the name of the bucket
        :type bucket_name: String
        :param resource_name: the resource connected to gcs, defaults to None
        :type resource_name: Optional[str], optional
        :return: a list with all the blob names present in the bucket, an empty list otherwise
        :rtype: List[str]
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return _resource.get_blobs(bucket_name)
    
    def exists_blob(self, bucket_name: str, blob: str, resource_name: Optional[str] = None) -> bool:
        """
        Given a bucket name, a blob and a resource return if that blob exists on the bucket
        :param bucket_name: the name of the bucket
        :type bucket_name: String
        :param blob: the name of the file/folder to search
        :type blob: str
        :param resource_name: the resource connected to gcs, defaults to None
        :type resource_name: Optional[str], optional
        :return: True if the blob exists, False otherwise
        :rtype: bool
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return _resource.exists_blob(bucket_name, blob)

    def upload_file(self,
                    bucket_name: str, 
                    destination_blob: str,
                    file_content: bytes,
                    resource_name: Optional[str] = None) -> bool:
        """
        Upload a file content in bytes on gcs bucket
        :param bucket_name: the name of the bucket
        :type bucket_name: String
        :param destination_blob: the name of the file (the blob) to store on gcs
        :type destination_blob: str
        :param file_content: the bytes content of the file
        :type file_content: bytes
        :param resource_name: the resource connected to gcs, defaults to None
        :type resource_name: Optional[str], optional
        :return: True if the operation succeeded, False otherwise
        :rtype: bool
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return _resource.upload_file(bucket_name, destination_blob, file_content)

    def upload_file_from_path(self,
                              bucket_name: str,
                              file_path: str,
                              destination_path: Optional[str] = None,
                              resource_name: Optional[str] = None) -> bool:
        """
        :param file_path: the physical path where the file is stored
        :param bucket_name: the name of the bucket
        :type bucket_name: String
        :type file_path: str
        :param destination_path: the path on gcs where to store data. If missing, the file will be saved in the root with the original name. If the destination path contains a final extension the file will inherit the new name. 
        :type destination_path: str
        :param resource_name: the resource connected to gcs, defaults to None
        :type resource_name: Optional[str], optional
        :return: True if the operation succeeded, False otherwise
        :rtype: bool
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return _resource.upload_file_from_path(bucket_name, file_path, destination_path)
    
    def download_file(self,
                      bucket_name: str,
                      download_blob: str,
                      download_path: str,
                      resource_name: Optional[str] = None) -> bool:
        """
        Download a file from gcs to the path specified
        :param bucket_name: the name of the bucket
        :type bucket_name: String
        :param download_blob: the name of the file (the blob) on gcs
        :type download_blob: str
        :param download_path: the local path where download the file. The destination MUST exist.
        :type download_path: str
        :param resource_name: the resource connected to gcs, defaults to None
        :type resource_name: Optional[str], optional
        :return: True if the operation succeeded, False otherwise
        :rtype: bool
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return _resource.download_file(bucket_name, download_blob, download_path)
    
    def download_file_in_memory(self,
                                bucket_name: str,
                                download_blob: str,
                                resource_name: Optional[str] = None) -> BytesIO:
        """
        Download a file from gcs in memory
        :param bucket_name: the name of the bucket
        :type bucket_name: String
        :param download_blob: the name of the file (the blob) on gcs
        :type download_blob: str
        :param resource_name: the resource connected to gcs, defaults to None
        :type resource_name: Optional[str], optional
        :return: a bytestream if the operation succeeded, None otherwise
        :rtype: bytes
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return _resource.download_file_in_memory(bucket_name, download_blob)
    
    def delete_file(self,
                    bucket_name: str,
                    delete_blob: str,
                    resource_name: Optional[str] = None) -> bool:
        """
        Delete a file from gcs bucket
        :param bucket_name: the name of the bucket
        :type bucket_name: String
        :param delete_blob: the name of the file (the blob) on gcs
        :type delete_blob: str
        :param resource_name: the resource connected to gcs, defaults to None
        :type resource_name: Optional[str], optional
        :return: True if the operation succeeded, False otherwise
        :rtype: bool
        """
        _lock, _resource = self._get_resource(resource_name)
        with _lock:    # type:ignore
            return _resource.delete_file(bucket_name, delete_blob)


def get_gcsbucket_healthcheck(
    bucket_name: str,
    sa_istance_name: Optional[str] = None
) -> Dict[str, Union[str, List[str]]]:
    """
    Performe the healthcheck on the gcs bucket to check its status, 
    giving back the list of blobs for each bucket

    :param bucket_name: the name of the bucket
    :type bucket_name: String
    :param sa_istance_name: the name of the GCP sa istance. Default: the first alphabetically, defaults to None
    :type sa_istance_name: Optional[str], optional
    :return: a dictionary having all the blobs in the gcs bucket
    :rtype: dict
    """
    result: Dict[str, Union[str, List[str]]] = {}
    try:
        gcsbm = GCSBucketManager()
        result["blobs"] = gcsbm.get_blobs(bucket_name,sa_istance_name)
    except Exception as e:
        result["error"] = str(e)

    return result