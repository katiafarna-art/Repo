"""Classe che implementa la funzionalità di signature detection basato su YOLO"""

import logging
from typing import Optional
from PIL import Image
from requests.packages.urllib3.exceptions import InsecureRequestWarning  # noqa
from core.models.entities.signature_detection.load_yolo import get_model


class YOLOSignatureDetector:
    def __init__(self) -> None:
        self.model = get_model()

    @staticmethod
    def _extract_params(params: Optional[dict] = None):
        if not params:
            params = dict()

        confidence = params.get("confidence", 0.25)

        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            logging.warning(
                f"Confidence {confidence} must be a numerical value in [0,1]. Switching to default {0.25}"
            )
            confidence = 0.25

        return confidence

    def _postprocess_response(self, response_list: list) -> dict:
        response_pp = list()

        for box in response_list[0].boxes:
            x1, y1, x2, y2, confidence, index_cls = box.data[0].tolist()
            index_cls = int(index_cls)

            dct_box = {
                "class": self.model.names[index_cls],
                "confidence": round(confidence, 2),
                "bbox": [x1, y1, x2, y2],
            }

            response_pp.append(dct_box)

        return response_pp

    def detect_signature_from_image(
        self, img: Image.Image, params: Optional[dict] = None
    ) -> dict:

        confidence_level = self._extract_params(params)

        response = self.model.predict(
            source=img, conf=confidence_level, save=False, verbose=False
        )
        return {
            "pp_response": self._postprocess_response(response_list=response),
            "confidence": confidence_level,
        }
