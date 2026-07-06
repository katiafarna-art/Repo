from core.pipelines.entities.entity_extraction.azure_entity_extractor import (
    OpenaiExtractor,
)
from core.pipelines.entities.entity_extraction.google_entity_extractor import (
    GeminiExtractor,
)


dct_entity_extractor = {
    "openai": OpenaiExtractor,
    "gemini": GeminiExtractor
}
