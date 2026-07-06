import logging
import pathlib
import json
import os
from typing import Optional
from google.cloud.storage.client import Client as GCSClient
from google.cloud.storage.bucket import Bucket
from google.api_core.exceptions import NotFound
from bdlpkg.providers.gcp.settings.services.gcp_config import get_datasource_settings
from bdlpkg.providers.gcp.settings.entities.sa.gcp import SASettings
from io import BytesIO


class GCS:
    """
    A class to manage interactions with Google Cloud Storage (GCS) buckets. 
    """
    def __init__(self,
                 sa_istance_name: str):
        """
        Return a gcs client to connect to the gcs bucket configured
        :param sa_istance_name: the name of the resource name of sa
        :type sa_istance_name: String
        :return: a resource to connect to gcs
        :rtype: Client
        """
        sai: SASettings = get_datasource_settings("service_account", sa_istance_name)
        sa_json = json.loads(sai.credentials.get_secret_value())
        self.client = GCSClient.from_service_account_info(sa_json)


    def get_gcs_bucket(self,
                       bucket_name: str,
                       verify_list: Optional[bool] = False) -> Bucket:
        """
        Return the gcs bucket having the name passed in input, otherwise if bucket_name is null return the first bucket available
        :param bucket_name: the name of the bucket
        :type bucket_name: String
        :param verify_list: check with bucket list
        :type verify_list: Optional[Boolean], optional
        :return: the bucket whose name is passed in input or the first bucket available if bucket_name is null
        :rtype: Bucket
        """
        bucket = None

        if verify_list:
            buckets = [bucket for bucket in self.client.list_buckets()]
            list_bucket_name = []
            for obj in buckets:
                list_bucket_name.append(obj.name)

            if bucket_name not in list_bucket_name:
                logging.error("Bucket {} required not exist".format(bucket_name))
            else:
                bucket = self.client.bucket(bucket_name)
        else:
            bucket = self.client.bucket(bucket_name)
        return bucket


    def exists_bucket(self, bucket_name: str,
                      verify_list: Optional[bool] = False) -> bool:
        """
        Given a bucket name, check if that bucket exists on gcs
        :param bucket_name: the name of the bucket to check
        :type bucket_name: String
        :param verify_list: check with bucket list
        :type verify_list: Optional[Boolean], optional
        :return: return True if the bucket exists, False otherwise
        :rtype: bool
        """
        if verify_list:
            buckets = [bucket for bucket in self.client.list_buckets()]
            list_bucket_name = []
            for obj in buckets:
                list_bucket_name.append(obj.name)

            if bucket_name not in list_bucket_name:
                logging.error("Bucket {} required not exist".format(bucket_name))
                return False
            else:
                logging.debug("Bucket {} exists!".format(bucket_name))
                return True
        else:
            blobs = []
            try:
                bucket = self.client.bucket(bucket_name)
                for blob in bucket.list_blobs():
                    blobs.append(blob.name)
            except Exception:
                raise NotFound(f"Bucket {bucket_name} not found")


    def get_blobs(self, bucket_name: str)-> list:
        """
        Given the bucket name, return the list of blobs present in the bucket
        :param bucket_name: the name of the bucket
        :type bucket_name: String
        :return: a list with all the blobs names present in the bucket, an empty list otherwise
        :rtype: list
        """
        bucket = None
        blobs = []

        bucket = self.get_gcs_bucket(bucket_name)
        for blob in bucket.list_blobs():
            blobs.append(blob.name)

        return blobs


    def exists_blob(self,bucket_name: str,
                    blob_name: str)-> bool:
        """
        Given a bucket name and a blob return if that blob exists on the bucket
        :param bucket_name: the name of the bucket
        :type bucket_name: String
        :param blob: the name of the file/folder to search
        :type blob: string
        :return: True if the blob exists, false otherwise
        :rtype: bool
        """
        bucket = self.get_gcs_bucket(bucket_name)
        blob = bucket.get_blob(blob_name)

        if blob is not None:
            return True
        else:
            logging.error("Blob {} doesn't exist".format(blob_name))
            return False


    def upload_file_from_path(self,bucket_name: str,
                              path_file: str,
                              destination_blob: Optional[str] = None) -> bool:
        """
        Upload a file from a path on gcs bucket
        :param bucket_name: the name of the bucket
        :type bucket_name: String
        :param path_file: the local path where the file is stored
        :type path_file: String
        :param destination_blob: the path on gcs where to store the file. Es: "model_data", "IN/DATA"
        :type destination_blob: String
        :return: True if the operation succeeded, False otherwise
        :rtype: bool
        """
        bucket = self.get_gcs_bucket(bucket_name)

        if destination_blob is None:
            destination_blob = os.path.basename(path_file)
        elif len(pathlib.Path(destination_blob).suffixes) == 0:
            destination_blob = os.path.join(destination_blob, os.path.basename(path_file))

        try: 
            blob = bucket.blob(destination_blob)
            blob.upload_from_filename(path_file)
            return True
        except Exception as e:
            logging.error("Exception while trying to uploading to GCS. {}".format(e))
            return False    
                

    def upload_file(self, bucket_name: str,
                    file_name: str,
                    file_content: bytes)-> bool:
        """
        Upload a file content in bytes on gcs bucket
        :param bucket_name: the name of the bucket
        :type bucket_name: String
        :param file_name: the name of the file (the blob) to store on gcs
        :type file_name: String
        :param file_content: the bytes content of the file
        :type file_content: the bytes of the file content
        :return: True if the operation succeeded, False otherwise
        :rtype: bool
        """
        bucket = self.get_gcs_bucket(bucket_name)

        try:
            blob = bucket.blob(file_name)
            blob.upload_from_string(file_content)
            return True
        except Exception as e:
            logging.error("Exception while trying to uploading to GCS. {}".format(e))
            return False


    def download_file(self, bucket_name: str,
                      file_name: str,
                      path_to_down: str)-> bool:
        """
        Download a file from gcs to the path specified
        :param bucket_name: the name of the bucket where the file is
        :type bucket_name: String
        :param file_name: the name of the file (the blob) on gcs
        :type file_name: String
        :param path_to_down: the local path where download the file. IMPORTANT: path directory MUST exist!
        :type path_to_down: String
        :return: True if the operation succeeded, False otherwise
        :rtype: bool
        """
        bucket = self.get_gcs_bucket(bucket_name)
        blob = bucket.get_blob(file_name)

        try:
            blob.download_to_filename(os.path.join(path_to_down, os.path.basename(file_name)))
            return True
        except Exception as e:
            logging.error("Blob {} doesn't exist".format(file_name))
            logging.error("Exception while trying to download from GCS. {}".format(e))
            return False


    def download_file_in_memory(self,bucket_name: str,
                                file_name: str)-> BytesIO:
        """
        Download a file from gcs in memory
        :param bucket_name: the name of the bucket where the file is
        :type bucket_name: String
        :param file_name: the name of the file (the blob) on gcs
        :type file_name: String
        :return: a bytes if the operation succeeded, None otherwise
        :rtype: bytes
        """
        bucket = self.get_gcs_bucket(bucket_name)
        blob = bucket.get_blob(file_name)

        buffer = BytesIO()
        try:
            buffer = BytesIO(blob.download_as_bytes())
        except Exception as e:
            logging.error("Blob {} doesn't exist".format(file_name))
            logging.error("Exception while trying to download from GCS. {}".format(e))
            
        return buffer


    def delete_file(self,bucket_name: str,
                    file_name: str)-> bool:
        """
        Delete a file from gcs bucket
        :param bucket_name: the name of the bucket where the file is
        :type bucket_name: String
        :param file_name: the name of the file (the key) on gcs
        :type file_name: String
        :return: True if the operation succeeded, False otherwise
        :rtype: bool
        """
        bucket = self.get_gcs_bucket(bucket_name)
        blob = bucket.get_blob(file_name)

        try:
            blob.delete()
            return True
        except Exception as e:
            logging.error("Blob {} doesn't exist".format(file_name))
            logging.error("Exception while trying to delete from GCS. {}".format(e))
            return False