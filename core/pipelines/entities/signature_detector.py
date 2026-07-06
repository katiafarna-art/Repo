"""Classe che implementa il SignatureDetector del servizio"""

import logging
from typing import Optional
from io import BytesIO
from PIL import Image
from config.parameters import SignatureDetectorConfig, SplitterDefaultConfig
from core.data.entities.splitter import Pdf2ImageSplitter
from core.models.entities.signature_detection import dct_signature_detector
from core.models.entities.signature_detection.load_yolo import DEFAULT_YOLO_MODEL


class SignatureDetector:
    provider: str = "isp"
    target_class: str = "signature"
    signature_detector: str = "yolo"

    def __init__(
        self,
        signature_detector_model: str = SignatureDetectorConfig.pt_default,
        token: [str, dict] = None,
        use_case: Optional[str] = None,
        target_class: Optional[str] = None,
    ):
        if signature_detector_model != DEFAULT_YOLO_MODEL:
            logging.warning(
                f"Using non generic YOLO model is no longer accepted. "
                f"Using {DEFAULT_YOLO_MODEL} instead of {signature_detector_model}"
            )
        self.signature_detector_model = dct_signature_detector.get(
            self.signature_detector
        )()
        self.signature_detector_model_name = DEFAULT_YOLO_MODEL
        self.token = token
        self.use_case = use_case

        if target_class:
            self.target_class = target_class

    @staticmethod
    def _extract_params(params: Optional[dict] = None):
        if not params:
            params = dict()

        return params.get("signature_detector", dict()), None

    def _postprocess_output_image(self, raw_output: list):

        matching_boxes = [
            labeled_box
            for labeled_box in raw_output
            if labeled_box["class"] == self.target_class
        ]

        bln_detected = True if matching_boxes else False

        bboxes = [
            {
                "coordinates": labeled_box["bbox"],
                "confidence": labeled_box["confidence"],
            }
            for labeled_box in matching_boxes
        ]

        return {
            f"{self.target_class}_detected": bln_detected,
            "count": len(matching_boxes),
            "bboxes": bboxes,
        }

    def detect_signature_from_image(
        self, img: bytes, params: Optional[dict] = None
    ) -> dict:

        signature_detector_params, _ = self._extract_params(params)
        img_pil = Image.open(BytesIO(img))
        raw_output = self.signature_detector_model.detect_signature_from_image(
            img=img_pil, params=signature_detector_params
        )
        output = self._postprocess_output_image(raw_output=raw_output["pp_response"])
        signature_detector_params["model_id"] = self.signature_detector_model_name
        signature_detector_params["confidence"] = raw_output["confidence"]
        output["extra"] = {"signature_detector_params": signature_detector_params}

        return output

    def detect_signature_from_pdf(
        self,
        pdf: bytes,
        page_from: int = 1,
        page_to: Optional[int] = None,
        params: Optional[dict] = None,
    ) -> dict:

        signature_detector_params, _ = self._extract_params(params)

        splitter = Pdf2ImageSplitter(
            dpi=SplitterDefaultConfig.dpi,
            greyscale=SplitterDefaultConfig.greyscale,
            start_page=page_from,
            end_page=page_to,
        )

        splitting = True
        output = dict()

        while splitting:
            chunk = splitter.get_next_split(pdf_content=pdf)

            if len(chunk) == 0:
                splitting = False

            else:
                for count, elem in enumerate(chunk):
                    raw_output = (
                        self.signature_detector_model.detect_signature_from_image(
                            img=elem["img"], params=signature_detector_params
                        )
                    )
                    output[f"pag_{elem['pag']}"] = self._postprocess_output_image(
                        raw_output["pp_response"]
                    )
                    if not count:
                        signature_detector_params["confidence"] = raw_output[
                            "confidence"
                        ]

        signature_detector_params["model_id"] = self.signature_detector_model_name
        output["extra"] = {"signature_detector_params": signature_detector_params}

        return output
