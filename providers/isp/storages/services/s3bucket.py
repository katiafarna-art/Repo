import logging
import pathlib
import os
from typing import Optional, Union
import boto3
import botocore
from boto3.session import Session
from botocore.config import Config
from bdlpkg.providers.isp.settings.services.isp_config import get_datasource_settings
from bdlpkg.providers.isp.settings.entities.storage.s3 import S3BucketSettings, S3GSSBucketSettings
from bdlpkg.utils.bdlfile.services.bdlfile import str_to_bool
from io import BytesIO


def get_s3_resource(s3_istance_name: Optional[str] = None) -> Session.resource:
    """
    Return an s3 Session.rosource to connect to the s3 bucket configured
    :param s3_istance_name: the name od the resource name of s3
    :type s3_istance_name: Optional[String], optional
    :return: a resource to connect to s3
    :rtype: Session.resource
    """
    s3i: Union[S3BucketSettings, S3GSSBucketSettings] = get_datasource_settings("bucket", None,
                                                        s3_istance_name)
    logging.debug("Setting is " + str(s3i))
    s3_resource = None

    session = boto3.session.Session()
    logging.debug("Session is " + str(session))
    _client_config = Config(connect_timeout=60,
                            read_timeout=60,
                            max_pool_connections=2)

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/customizations/s3.html#boto3.s3.transfer.TransferConfig
    # _transfer_config = TransferConfig(use_threads=True,
    #                                   max_concurrency=2,
    #                                   max_bandwidth=None)

    s3_resource = session.resource(
        's3',
        endpoint_url=str(s3i.endpoint_url),
        aws_access_key_id=s3i.access_key_id,
        aws_secret_access_key=str(s3i.secret_access_key.get_secret_value()),
        verify=str_to_bool(s3i.verify_ssl_cert),
        config=_client_config)

    return s3_resource


def get_s3_bucket(s3_resource: Optional[Session.resource] = None,
                  bucket_name: Optional[str] = None) -> 'boto3.s3.Bucket':
    """
    Return the s3 bucket having the name passed in input, otherwise if bucket_name is null return the first bucket available
    :param s3_resource: the resource to connect to s3
    :type s3_resource: Optional[Session.resource], optional
    :param bucket_name: the name of the bucket
    :type bucket_name: Optional[String], optional
    :return: the bucket whose name is passed in input or the first bucket available if bucket_name is null
    :rtype: Bucket
    """
    bucket = None
    if not s3_resource:
        s3_resource = get_s3_resource()

    #get the first bucket available from the resource
    buckets = s3_resource.buckets.all()
    bucket_iter = iter(buckets)
    list_bucket_name = []
    for obj in bucket_iter:
        list_bucket_name.append(obj.name)
    if bucket_name is not None and bucket_name not in list_bucket_name:
        raise ValueError("Bucket {} required not exist".format(bucket_name))
    else:
        bucket = obj

    return bucket


def exists_bucket(s3_resource: Optional[Session.resource] = None,
                  bucket_name: Optional[str] = None) -> bool:
    """
    Given a bucket name, check if that bucket exists on s3
    :param s3_resource: the resource associated to s3 bucket
    :type s3_resource: Optional[Session.resource], optional 
    :param bucket_name: the name of the bucket to check
    :type bucket_name: Optional[String], optional
    :return: return True if the bucket exists, False otherwise
    :rtype: bool
    """
    if not s3_resource:
        s3_resource = get_s3_resource()

    s3_resource.meta.client.head_bucket(Bucket=bucket_name)
    logging.debug("Bucket {} exists!".format(bucket_name))
    return True


def get_keys(s3_resource: Optional[Session.resource] = None,
             bucket_name: Optional[str] = None) -> list:
    """
    Give the bucket name and a resource, return the list of keys present in the bucket
    :param s3_resource: the resource connected to s3
    :type s3_resource: Optional[Session.resource], optional 
    :param bucket_name:
    :type bucket_name: Optional[String], optional
    :return: a list with all the key names present in the bucket, an empty list otherwise
    :rtype: list
    """
    bucket = None
    keys = []

    if not s3_resource:
        s3_resource = get_s3_resource()

    bucket = get_s3_bucket(s3_resource, bucket_name)
    for object in bucket.objects.all():
        keys.append(object.key)

    return keys


def get_keys_metadata(s3_resource: Optional[Session.resource] = None,                      
                      bucket_name: Optional[str] = None,
                      key: Optional[str] = None) -> dict:    
    """    
    Give the bucket name and a resource, return a dictionary containing the keys present in the bucket with their associated last modified time.    
    
    :param s3_resource: the resource connected to s3    
    :type s3_resource: Optional[Session.resource], optional    
    :param bucket_name:    
    :type bucket_name: Optional[String], optional
    :param key: the key whose metadata is to be retrieved   
    :type key: Optional[String], optional     
    :return: a dictionary with all the key names with associated las modified time present in the bucket, an empty dict otherwise    
    :rtype: dict    
    """    
    bucket = None    
    keys_and_time = {}    
    
    if not s3_resource:        
        s3_resource = get_s3_resource()    
        
    bucket = get_s3_bucket(s3_resource, bucket_name)    
    for object in bucket.objects.all():        
        keys_and_time.update({object.key: {"last_modified" : object.last_modified,
                                           "size" : object.size}})    
    
    if key is None:
        return keys_and_time
    else: 
        try:
            return keys_and_time[key]
        except KeyError:
            raise FileNotFoundError(f"The key {key} doesn't exist")    


def exists_key(key: str,
               s3_resource: Optional[Session.resource] = None,
               bucket_name: Optional[str] = None) -> bool:
    """
    Given a bucket name, a key and a resource return if that key exists on the bucket
    :param key: the name of the file/folder to search
    :type key: string
    :param s3_resource: the resource to connect to s3
    :type s3_resource: Optional[Session.resource], optional 
    :param bucket_name: the name of the bucket
    :type bucket_name: Optional[String], optional
    :return: True if the key exists, false otherwise
    :rtype: bool
    """

    try:
        if not s3_resource:
            s3_resource = get_s3_resource()

        bucket = get_s3_bucket(s3_resource, bucket_name)
        bucket.Object(key).get()
        return True
    except s3_resource.meta.client.exceptions.NoSuchKey as ex:    # type:ignore
        logging.debug("Key {} doesn't exist".format(key))
        return False


def upload_file_from_path(path_file: str,
                          destination_key: Optional[str] = None,
                          s3_resource: Optional[Session.resource] = None,
                          bucket_name: Optional[str] = None) -> bool:
    """
    Upload a file from a path on s3 bucket
    :param path_file: the local path where the file is stored
    :type path_file: String
    :param destination_key: the path on s3 where to store the file. Es: "model_data", "IN/DATA"
    :type destination_key: String
    :param s3_resource: the resource to connect to s3
    :type s3_resource: Optional[Session.resource], optional 
    :param bucket_name: the name of the bucket
    :type bucket_name: Optional[String], optional
    :return: True if the operation succeeded, False otherwise
    :rtype: bool
    """

    if not s3_resource:
        s3_resource = get_s3_resource()

    if destination_key is None:
        destination_key = os.path.basename(path_file)
    elif len(pathlib.Path(destination_key).suffixes) == 0:
        destination_key = destination_key + os.path.basename(path_file)

    # if destination_key is None:
    #     destination_key = path_file
    # elif len(pathlib.Path(destination_key).suffixes) == 0:
    #     destination_key = destination_key + os.path.basename(path_file)

    # destination_key = os.path.join(
    # destination_key, os.path.basename(path_file)) if type(
    #     destination_key) == str else os.path.basename(path_file)

    with open(path_file, "rb") as fp:
        return upload_file(destination_key, fp.read(), s3_resource, bucket_name)


def upload_file(file_name: str,
                file_content: bytes,
                s3_resource: Optional[Session.resource] = None,
                bucket_name: Optional[str] = None) -> bool:
    """
    Upload a file content in bytes on s3 bucket
    :param file_name: the name of the file (the key) to store on s3
    :type file_name: String
    :param file_content: the bytes content of the file
    :type file_content: the bytes of the file content
    :param s3_resource: the resource to connecto to s3
    :type s3_resource: Optional[Session.resource], optional
    :param bucket_name: the name of the bucket
    :type bucket_name: Optional[String], optional
    :return: True if the operation succeeded, False otherwise
    :rtype: bool
    """

    if not s3_resource:
        s3_resource = get_s3_resource()

    bucket = get_s3_bucket(s3_resource, bucket_name)

    object = s3_resource.Object(bucket.name, file_name)
    result = object.put(Body=file_content)
    res = result.get('ResponseMetadata')
    if res.get('HTTPStatusCode') == 200:
        logging.info('File Uploaded Successfully')
        return True
    else:
        logging.info('File Not Uploaded')
        return False


def download_file(file_name: str,
                  path_to_down: str,
                  s3_resource: Optional[Session.resource] = None,
                  bucket_name: Optional[str] = None) -> bool:
    """
    Download a file from s3 to the path specified
    :param file_name: the name of the file (the key) on s3
    :type file_name: String
    :param path_to_down: the local path where download the file. IMPORTANT: path directory MUST exist!
    :type path_to_down: String
    :param s3_resource: the resource to connect to s3
    :type s3_resource: Optional[Session.resource], optional
    :param bucket_name: the name of the bucket where the file is
    :type bucket_name: Optional[String], optional
    :return: True if the operation succeeded, False otherwise
    :rtype: bool
    """

    try:
        if not s3_resource:
            s3_resource = get_s3_resource()

        bucket = get_s3_bucket(s3_resource, bucket_name)
        s3_resource.Bucket(bucket.name).download_file(
            file_name, os.path.join(path_to_down, os.path.basename(file_name)))
        return True
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            logging.error("The object does not exist.")
        return False


def download_file_in_memory(file_name: str,
                            s3_resource: Optional[Session.resource] = None,
                            bucket_name: Optional[str] = None) -> BytesIO:
    """
    Download a file from s3 in memory
    :param file_name: the name of the file (the key) on s3
    :type file_name: String
    :param s3_resource: the resource to connect to s3
    :type s3_resource: Optional[Session.resource], optional
    :param bucket_name: the name of the bucket where the file is
    :type bucket_name: Optional[String], optional
    :return: a bytes if the operation succeeded, None otherwise
    :rtype: bytes
    """

    if not s3_resource:
        s3_resource = get_s3_resource()

    bucket = get_s3_bucket(s3_resource, bucket_name)
    buffer = BytesIO()
    bucket.download_fileobj(file_name, buffer)
    buffer.seek(0)
    return buffer


def delete_file(file_name: str,
                s3_resource: Optional[Session.resource] = None,
                bucket_name: Optional[str] = None) -> bool:
    """
    Delete a file from s3 bucket
    :param file_name: the name of the file (the key) on s3
    :type file_name: String
    :param s3_resource: the resource to connect to s3
    :type s3_resource: Optional[Session.resource], optional 
    :param bucket_name: the name of the bucket where the file is
    :type bucket_name: Optional[String], optional
    :return: True if the operation succeeded, False otherwise
    :rtype: bool
    """

    if not s3_resource:
        s3_resource = get_s3_resource()

    bucket = get_s3_bucket(s3_resource, bucket_name)

    s3_resource.Object(bucket.name, file_name).delete()
    if not (exists_key(file_name, s3_resource, bucket.name)):
        return True
    else:
        return False
