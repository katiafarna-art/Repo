"""Modulo contenente funzioni ausiliarie per interagire con file system o S3"""

import os
import re
import time
import shutil
import json
import logging
from typing import Union, Optional
from bdlpkg.providers.isp.storages.services.BucketManager import BucketManager
from core.routines.entities import get_function_name
from core.exceptions import SmartOCRException


def save_result(
    job_id: str,
    output: Union[dict, str],
    file_name: str = "output",
    extension: str = "json",
) -> bool:
    """
    Funzione che svolge la scrittura e il salvataggio di un file in locale o tramite BucketManager (su spazio S3).
    Viene restituito True se l'operazione di salvataggio va a buon fine, altrimenti viene restituito False.

    :param job_id: codice identificativo univoco utilizzato per la nomenclatura del file.
    :type job_id: str
    :param output: contenuto da salvare su file.
    :type output: (dict, str)
    :param file_name: nome del file da utilizzare nella nomenclatura per il salvataggio.
        Default a "output".
    :type file_name: (str, optional)
    :param extension: estensione del file da salvare. Default a "json".
    :type extension: (str, optional)

    :return: True se la scrittura e il salvataggio del file vanno a buon fine. Altrimenti False.
    :rtype: bool
    """
    written = True

    try:
        if not os.path.exists("./output_async_endpoint"):
            os.makedirs("./output_async_endpoint")

        job_dir = os.path.join("./output_async_endpoint", job_id)

        if not os.path.exists(job_dir):
            os.makedirs(job_dir)

        with open(
            f"./output_async_endpoint/{job_id}/{job_id}_{file_name}.{extension}", "w"
        ) as file:
            json.dump(output, file)

        if "ISP_AMBIENTE" in os.environ:
            bm = BucketManager()

            try:
                written = bm.upload_file_from_path(
                    file_path=f"./output_async_endpoint/{job_id}/{job_id}_{file_name}.{extension}",
                    destination_path=f"./{job_id}/{job_id}_{file_name}.{extension}",
                )

                shutil.rmtree(path=f"./output_async_endpoint/{job_id}")

            except Exception as e:
                logging.error(
                    f"Error saving on S3: ./{job_id}/{job_id}_{file_name}.{extension}\n\n{e}"
                )
                written = False

            finally:
                return written

    except Exception as e:
        logging.error(
            f"Error saving local file: ./{job_id}_{file_name}.{extension}\n\n{e}"
        )

    finally:
        return False


def get_result(job_id: str, file_name: str = "output") -> json:
    """
    Funzione che restituisce il contenuto di un file salvato in locale o su spazio S3.
    Nello specifico, viene restituito il contenuto di un file .json se un file .success è presente. Successivamente
    entrambi i file .json e .success vengono eliminati.
    Qual'ora fosse stato salvato un file .failure, viene restituito il contenuto di quest'ultimo. Il file .failure
    viene poi analogamente eliminato.
    Se nessuno dei file .success e .failure è presente, viene restituito il codice 204.

    :param job_id: codice identificativo univoco che compone la nomenclatura del file ricercato.
    :type job_id: str
    :param file_name: nome del file che compone la nomenclatura ricercata. Default a "output".
    :type file_name: (str, optional)

    :return: Il contenuto del file .json se il file .success è presente, altrimenti il contenuto del file .failure se
        quest'ultimo è presente. Altrimenti 204.
    :rtype: (json, int)
    """

    if "ISP_AMBIENTE" in os.environ:
        bm = BucketManager()

        str_path_output = f"./{job_id}/{job_id}_{file_name}.json"
        str_path_success = f"./{job_id}/{job_id}_{file_name}.success"
        str_path_failure = f"./{job_id}/{job_id}_{file_name}.failure"

        if bm.exists_key(str_path_output) and bm.exists_key(str_path_success):

            output = json.load(bm.download_file_in_memory(str_path_output))
            bm.delete_file(str_path_output)
            bm.delete_file(str_path_success)

        elif bm.exists_key(str_path_failure):

            output = json.load(bm.download_file_in_memory(str_path_failure))
            bm.delete_file(str_path_failure)

        else:
            output = 204

    else:
        str_path_output = f"./output_async_endpoint/{job_id}/{job_id}_{file_name}.json"
        str_path_success = (
            f"./output_async_endpoint/{job_id}/{job_id}_{file_name}.success"
        )
        str_path_failure = (
            f"./output_async_endpoint/{job_id}/{job_id}_{file_name}.failure"
        )

        if os.path.exists(str_path_output) and os.path.exists(str_path_success):

            with open(str_path_output, "r") as file:
                output = json.load(file)

            shutil.rmtree(path=f"./output_async_endpoint/{job_id}")

        elif os.path.exists(str_path_failure):

            with open(str_path_failure, "r") as file:
                output = json.load(file)

            shutil.rmtree(path=f"./output_async_endpoint/{job_id}")

        else:
            output = 204

    return output


def _generate_patterns(file_name: str):
    """Precompile regex patterns for different file extensions."""
    return [re.compile(rf"^\./([^/]+)/\1_.*{file_name}\.{ext}$") for ext in ("json", "success", "failure")]


def _generate_output_message(failed_del: int, total_files: int, hrs_threshold: int) -> dict:
    """Generate an appropriate message based on deletion results."""
    if failed_del == 0:
        return {"text": f"Obsolete files (older than {hrs_threshold} hrs) have been successfully removed"}
    return {
        "WARNING": f"Failed to remove {failed_del} files out of {total_files} that are older than {hrs_threshold} hrs"
    }


def delete_result(
    hrs_threshold: Optional[int] = 24,
    file_name: str = "output",
) -> dict:

    if "ISP_AMBIENTE" not in os.environ:
        return {"text": "ISP_AMBIENTE not configured, cannot access s3 files"}

    bm = BucketManager()
    total_files, failed_del = 0, 0

    lst_pattern = _generate_patterns(file_name)
    threshold_time = hrs_threshold * 3600

    for _, (key, val) in bm.get_keys_metadata().items():
        if any([pattern.match(key) for pattern in lst_pattern]):
            total_files += 1
            if (time.time() - val["last_modified"].timestamp() > threshold_time) and not bm.delete_file(key):
                failed_del += 1

    return _generate_output_message(failed_del=failed_del, total_files=total_files, hrs_threshold=hrs_threshold)


def check_file(job_id: str, file_name: str = "output", extension: str = "json") -> bool:
    """
    Funzione che controlla l'esistenza di un file salvato in locale o su S3.

    :param job_id: codice identificativo univoco utilizzato per la nomenclatura del file.
    :type job_id: str
    :param file_name: nome del file ulteriormente associato alla nomenclatura del file. Default a "output".
    :type file_name: (str, optional)
    :param extension: estensione del file da ricercare. Default a "json".
    :type extension: (str, optional)

    :return: True se il file esiste, altrimenti False.
    :rtype: bool
    """
    if "ISP_AMBIENTE" in os.environ:
        bm = BucketManager()

        str_path = f"./{job_id}/{job_id}_{file_name}.{extension}"
        return True if bm.exists_key(str_path) else False

    else:
        str_path = f"./output_async_endpoint/{job_id}/{job_id}_{file_name}.{extension}"
        return True if os.path.exists(str_path) else False


def load_file_from_bucket(
    file_name: str, dest_path: str = "./", s3_path: str = "./"
) -> bool:
    loaded = True
    source_key = f"{s3_path}/{file_name}"

    if "ISP_AMBIENTE" not in os.environ:
        logging.error("ISP_AMBIENTE not defined")
        loaded = False

    if not os.path.exists(dest_path):
        try:
            os.makedirs(dest_path)
        except Exception as e:
            raise SmartOCRException(
                f"Func {get_function_name()}: "
                f"Exception while creating the local tmp dir for saving the models: {e}"
            )

    try:
        bm = BucketManager()
        loaded = bm.download_file(download_key=source_key, download_path=dest_path)

    except Exception as e:
        logging.error(f"Error loading from S3: {source_key}\n\n{e}")
        loaded = False

    finally:
        return loaded


def save_file_on_bucket(file_name: str, input_file: bytes, s3_path: str = "./") -> bool:
    if "ISP_AMBIENTE" in os.environ:
        bm = BucketManager()

    else:
        logging.error("ISP_AMBIENTE not defined")
        return False

    written = True
    destination_key = f"{s3_path}/{file_name}"

    try:
        written = bm.upload_file(
            destination_key=destination_key,
            file_content=input_file,
        )

    except Exception as e:
        logging.error(f"Error saving on S3: {destination_key}\n\n{e}")
        written = False

    finally:
        return written


def get_presigned_url_from_bucket(file_path: str, expiration_time: int = 86400) -> Union[str, None]:
    if "ISP_AMBIENTE" in os.environ:
        bm = BucketManager()

    else:
        logging.error("ISP_AMBIENTE not defined")
        return None

    try:
        presigned_url = bm.get_download_presigned_url(
            key_name=file_path,
            expire_in=expiration_time
        )

    except Exception as e:
        logging.error(f"Error while generating the presigned url for file: {file_path}\n\n{e}")
        return None

    return presigned_url
