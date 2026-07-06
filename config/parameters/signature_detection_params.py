"""Script contenente i parametri di configurazione di default per i motori YOLO adibiti a signature detection"""

import os
import logging
from dataclasses import dataclass
from bdlpkg.providers.isp.storages.services.BucketManager import BucketManager


PATH_PT_LOCAL = "./signature-detection/models"
PATH_PT_S3 = "./yolo_models/signature_detection_models/"


@dataclass
class SignatureDetectorConfig:

    pt_default = "yolov8_modello_generico.pt"
    pt_1 = "yolov8l_atto_notorio.pt"
    pt_2 = "yolov8l_certificato_morte.pt"
    pt_3 = "yolov8l_dichiarazione_sostitutiva.pt"
    pt_4 = "yolov8l_testamento.pt"

    @classmethod
    def validate_value(cls, input_value: str):

        if (
            input_value
            not in {
                key: value
                for key, value in cls.__dict__.items()
                if not str(key).startswith("__")
            }.values()
        ):
            logging.warning(
                f"{input_value} is not an available YOLO model name. Switching to default model "
                f"{cls.pt_default}"
            )
            input_value = cls.pt_default
        return input_value

    @classmethod
    def check_model(
        cls,
        model_id: str,
    ) -> str:

        if "ISP_AMBIENTE" not in os.environ:
            logging.error(
                f"ISP_AMBIENTE not defined, switching to default {cls.pt_default}"
            )
            return cls.pt_default

        bm = BucketManager()
        str_path = f"{PATH_PT_S3}/{model_id}"

        if bm.exists_key(str_path) and model_id.endswith(".pt"):
            logging.debug(f"custom model {model_id} available on s3.")
            return model_id
        else:
            logging.error(
                f"Custom model {model_id} not available on s3, switching to default {cls.pt_default}"
            )
            return cls.pt_default
