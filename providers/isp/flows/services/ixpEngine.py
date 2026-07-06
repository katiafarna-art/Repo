import os
import secrets
import string
import hashlib
from typing import Any, Dict, Union
import glob
import json


from bdlpkg.providers.isp.settings.entities.flow.IXPConfig import IXPSendConfig
from bdlpkg.providers.isp.storages.services.BucketManager import BucketManager

IXP_TMP_FOLDER = "temp/ixp/"


def list_file_to_send(config: IXPSendConfig,
                      asynchronous: bool = False,
                      uuid: str = None) -> Union[Dict[str, Any],None]:
    """
    Returns a reference to the S3 resource and the list of files ready to be sent.

    :param config: The configuration to be used.
    :type config: IXPSendConfig
    :param asynchronous: Operation executed in asyncronous way, default False
    :type asynchronous: bool
    :param uuid: The Job ID, default None
    :type uuid: str
    :return: A dictionary containing the S3 resource and the list of files ready for transfer.
    :rtype: Dict[str, Any]
    """
    list_keys = BucketManager().get_keys(config.s3_config.s3_resource)
    list_files = [
        key for key in list_keys
        if key.startswith(config.s3_config.s3_output_folder)
    ]
    
    files_dict = {
        "s3_resource": config.s3_config.s3_resource,
        "list_files": list_files,
        "output_folder": config.ixp_output_folder
        }
    
    if asynchronous:
        if uuid:
            BucketManager().upload_file(f"{uuid}.json",json.dumps(files_dict),config.s3_config.s3_resource)
        else:
            raise ValueError(f"no job uuid specified")
    else:
        return files_dict


def start_job_download(filepath: str, resource_name: str, uuid: str) -> None:
    """
    Download a file from the S3 bucket.

    :param filepath: The path of the file to be downloaded.
    :type filepath: str
    :param resource_name: The name of the S3 resource.
    :type resource_name: str
    :param uuid: A unique identifier for the download session.
    :type uuid: str
    """
    if not os.path.exists(f"{IXP_TMP_FOLDER}{uuid}"):
        os.makedirs(f"{IXP_TMP_FOLDER}{uuid}", exist_ok=True)
    BucketManager().download_file(download_key=filepath,
                                 resource_name=resource_name,
                                 download_path=f"{IXP_TMP_FOLDER}{uuid}")


def split_file(filepath: str,
               partsize: int = 100 * 1024 * 1024,
               threshold: int = 1024 * 1024 * 1024) -> int:
    """
    Split the file into parts: f"{filepath}.part_{part_number}"

    :param filepath: The path of the file to be split.
    :type filepath: str
    :param partsize: The size of each part in bytes, defaults to 100 * 1024 * 1024.
    :type partsize: int, optional
    :param threshold: The size threshold above which the file will be split, defaults to 1024 * 1024 * 1024.
    :type threshold: int, optional
    :return: The number of parts the file has been split into.
    :rtype: int
    """

    filesize = os.path.getsize(filepath)
    part_number = 1
    if filesize > threshold:
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(partsize)
                if not chunk:
                    part_number = 1
                    break
                part_filepath = f"{filepath}.part_{part_number}"
                with open(part_filepath, 'wb') as part_file:
                    part_file.write(chunk)
                part_number += 1

    return part_number


def generate_random_string(n: int) -> str:
    """
    Generate a random alphanumeric string of the specified length.

    :param n: The length of the string.
    :type n: int
    :return: A randomly generated string.
    :rtype: str
    """
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(n))


def sha256_generation(filepath: str) -> str:
    """
    Compute the SHA256 hash of the specified file.

    :param filepath: The path of the file.
    :type filepath: str
    :return: The SHA256 digest of the file.
    :rtype: str
    """
    with open(filepath, 'rb') as f:
        file_data = f.read()

    sha = hashlib.sha256(file_data).hexdigest()
    f.close()

    return sha


def save_files(file: bytes, chunk_filename: str, temp_dir: str) -> None:
    """
    Save the file chunk in the temporary directory.

    :param file: The file content in bytes.
    :type file: bytes
    :param chunk_filename: The name of the file chunk.
    :type chunk_filename: str
    :param temp_dir: The path to the temporary directory.
    :type temp_dir: str
    """
    os.makedirs(temp_dir, exist_ok=True)

    filepath = os.path.join(temp_dir, chunk_filename)
    with open(filepath, 'wb') as f:
        f.write(file)


def merge_files(filename: str, temp_dir: str) -> None:
    """
    Merge all file parts into a single file.

    :param filename: The name of the final file.
    :type filename: str
    :param temp_dir: The path to the temporary directory where the parts are stored.
    :type temp_dir: str
    """


    merged_files_path = os.path.join(temp_dir, f'{filename}.zip')

    with open(merged_files_path, 'wb') as output_file:
        lst_parts = glob.glob(os.path.join(temp_dir, f'{filename}.zip_part_*'))
        lst_parts.sort()

        for part in lst_parts:
            with open(part, 'rb') as input_file:
                output_file.write(input_file.read())
