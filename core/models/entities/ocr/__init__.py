from core.models.entities.ocr.tesseract_ocr import TesseractOCR
from core.models.entities.ocr.document_intelligence_ocr import DocumentIntelligenceOCR
from core.models.entities.ocr.doc_ai_ocr import DocumentAIOCR

dct_ocr_factory = dict()
dct_ocr_factory["tesseract"] = TesseractOCR
dct_ocr_factory["document-intelligence"] = DocumentIntelligenceOCR
dct_ocr_factory["document-ai"] = DocumentAIOCR
