"""Script contenente i parametri di configurazione di default per i TextExtractor adibiti a OCR"""

from dataclasses import dataclass


@dataclass
class TesseractDefaultConfig:
    config: str = ""


@dataclass
class DocumentIntelligenceDefaultConfig:
    model_id: str = "prebuilt-layout"


@dataclass()
class DocumentAIOCRDefaultConfig:
    model_id: str = "ocr-isp-bdl10-prod-eu-001"
