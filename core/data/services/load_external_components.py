"""Modulo contenente funzionalità per il caricamento di dipendenze esterne tesseract e tiktoken"""

import os
import shutil
import zipfile
from bdlpkg.providers.isp.storages.services.BucketManager import BucketManager
from core.routines.entities import get_function_name
from core.exceptions import SmartOCRException


def decompress_zip(zip_file_path: str, temp_dir: str) -> None:

    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    os.remove(zip_file_path)


def move_files_up(temp_dir: str, down_dir: str, final_dir: str):

    main_folder = os.path.join(temp_dir, down_dir)
    if not os.path.isdir(final_dir):
        os.rmdir(final_dir)

    if os.path.isdir(main_folder):
        os.system(f"mv {main_folder}/* {final_dir}")

    shutil.rmtree(main_folder)


def load_tessdata():

    if "ISP_AMBIENTE" in os.environ:
        bm = BucketManager()

        download_key = "tessdata-4.1.0.zip"
        download_folder = "tessdata-4.1.0"
        download_path = "/tmp"

        if bm.exists_key(download_key):

            try:
                bm.download_file(download_key, download_path)
                zip_file_path = os.path.join(download_path, download_key)
                decompress_zip(zip_file_path, download_path)

                tesseract_dir = "/tessdata"

                move_files_up(download_path, download_folder, tesseract_dir)

            except Exception as e:
                raise SmartOCRException(
                    f"Func {get_function_name()}: Error in upload zip file {e}"
                )

        else:
            raise SmartOCRException(
                f"Func {get_function_name()} Zip file with Tesseract data not found"
            )


def load_docling_models():

    if "ISP_AMBIENTE" in os.environ:
        bm = BucketManager()

        download_key = "docling_models.zip"
        download_folder = "docling_models"
        download_path = "/tmp"

        if bm.exists_key(download_key):

            try:
                bm.download_file(download_key, download_path)
                zip_file_path = os.path.join(download_path, download_key)
                decompress_zip(zip_file_path, download_path)

                docling_models_dir = "/doclingmodels"

                move_files_up(download_path, download_folder, docling_models_dir)

            except Exception as e:
                raise SmartOCRException(
                    f"Func {get_function_name()}: Error in upload zip file {e}"
                )

        else:
            raise SmartOCRException(
                f"Func {get_function_name()} Zip file with docling models not found"
            )


def load_tiktoken_cache():

    if "ISP_AMBIENTE" in os.environ:
        bm = BucketManager()

        download_key = "9b5ad71b2ce5302211f9c61530b329a4922fc6a4"
        download_path = "/tmp/tiktoken"

        if bm.exists_key(download_key):

            try:
                os.mkdir("/tmp/tiktoken")
                bm.download_file(download_key, download_path)

            except Exception as e:
                raise SmartOCRException(
                    f"Func {get_function_name()}: Error in upload zip file {e}"
                )

        else:
            raise SmartOCRException(
                f"Func {get_function_name()}: Zip file with Tesseract data not found"
            )


if __name__ == "__main__":
    load_tessdata()
    load_docling_models()
    load_tiktoken_cache()
