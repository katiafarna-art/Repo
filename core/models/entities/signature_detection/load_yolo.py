import os
from typing import Literal
from pathlib import Path
from config.parameters import PATH_PT_LOCAL, PATH_PT_S3
from ultralytics import YOLO
from config.parameters import SignatureDetectorConfig
from core.routines.entities import get_function_name
from core.data.entities import load_file_from_bucket
from core.exceptions import SmartOCRException

_model: YOLO | None = None
_DEFAULT_SOURCE: Literal["local", "S3"] = (
    "S3" if "ISP_AMBIENTE" in os.environ else "local"
)
DEFAULT_YOLO_MODEL = SignatureDetectorConfig.pt_default


def load_yolo_local(pt_model: str) -> YOLO:
    model_path = f"{PATH_PT_LOCAL}/local_models/{pt_model}"
    try:
        model = YOLO(model_path)
    except Exception as e:
        raise SmartOCRException(
            f"{get_function_name()} - YOLO model loading failed: {e}"
        )
    return model


def load_yolo_s3(pt_model: str) -> YOLO:
    try:
        if load_file_from_bucket(
            file_name=pt_model, s3_path=PATH_PT_S3, dest_path=PATH_PT_LOCAL
        ):
            model = YOLO(f"{PATH_PT_LOCAL}/{pt_model}")
        else:
            raise SmartOCRException(
                f"Method YOLOSignatureDetector.{get_function_name()}:"
                f"pytorch model loading failed."
            )
    except Exception as e:
        raise SmartOCRException(
            f"{get_function_name()} - YOLO model loading failed: {e}"
        )

    finally:
        Path(f"{PATH_PT_LOCAL}/{pt_model}").unlink(missing_ok=True)

    return model


def load_yolo(
    pt_model: str = DEFAULT_YOLO_MODEL,
    how: Literal["local", "S3"] = _DEFAULT_SOURCE,
) -> None:
    global _model
    if _model is not None:
        return
    if how == "local":
        _model = load_yolo_local(pt_model)
    else:
        _model = load_yolo_s3(pt_model)
    if _model is None:
        raise SmartOCRException(
            f"{get_function_name()} - YOLO model loading failed. No model after loading"
        )


def get_model() -> YOLO:
    load_yolo()
    return _model  # type: ignore[return-value]
