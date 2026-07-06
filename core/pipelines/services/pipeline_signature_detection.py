"""Modulo contenente le pipeline di signature detection da immagini e pdf"""

from typing import Optional, Union
from config.parameters import ETA_PAGE_DEFAULT, SignatureDetectorConfig
from core.pipelines.entities.signature_detector import SignatureDetector
from core.routines.services import track_and_save_results

PIPE_TARGET_CLASS = "signature"


def detect_signature_from_image(
    img: bytes,
    params: Optional[dict] = None,
    token: Optional[Union[str, dict]] = None,
    use_case: Optional[str] = None,
    job_id: Optional[str] = None,
    expected_eta: int = ETA_PAGE_DEFAULT,
) -> dict:

    params = params or dict()
    params = params.get("args", dict())
    signature_detector_params = params.get("signature_detector", dict())
    signature_detector_model = signature_detector_params.pop(
        "model_id", SignatureDetectorConfig.pt_default
    )

    signature_detector_model = SignatureDetectorConfig.check_model(
        signature_detector_model
    )

    detector = SignatureDetector(
        signature_detector_model=signature_detector_model,
        token=token,
        use_case=use_case,
        target_class=PIPE_TARGET_CLASS,
    )

    func_kwargs = {"img": img, "params": params}

    return track_and_save_results(
        callable_func=detector.detect_signature_from_image,
        func_kwargs=func_kwargs,
        job_id=job_id,
        expected_eta=expected_eta,
    )


def detect_signature_from_pdf(
    pdf: bytes,
    page_from: int = 1,
    page_to: Optional[int] = None,
    params: Optional[dict] = None,
    token: Optional[Union[str, dict]] = None,
    use_case: Optional[str] = None,
    job_id: Optional[str] = None,
    expected_eta: int = ETA_PAGE_DEFAULT,
) -> dict:

    if not params:
        params = dict()

    params = params.get("args", dict())
    signature_detector_params = params.get("signature_detector", dict())
    signature_detector_model = signature_detector_params.pop(
        "model_id", SignatureDetectorConfig.pt_default
    )

    signature_detector_model = SignatureDetectorConfig.check_model(
        signature_detector_model
    )

    detector = SignatureDetector(
        signature_detector_model=signature_detector_model,
        token=token,
        use_case=use_case,
        target_class=PIPE_TARGET_CLASS,
    )

    func_kwargs = {
        "pdf": pdf,
        "page_from": page_from,
        "page_to": page_to,
        "params": params,
    }

    return track_and_save_results(
        callable_func=detector.detect_signature_from_pdf,
        func_kwargs=func_kwargs,
        job_id=job_id,
        expected_eta=expected_eta,
    )
