from core.pipelines.entities.ocr.tesseract_text_extractor import TesseractExtractor
from core.pipelines.entities.ocr.doc_int_text_extractor import DocIntExtractorLayerAI
from core.pipelines.entities.ocr.doc_ai_text_extractor import DocAITextExtractor

dct_extractor = {
    "tesseract": TesseractExtractor,
    "document_intelligence": DocIntExtractorLayerAI,
    "document_ai": DocAITextExtractor,
}
