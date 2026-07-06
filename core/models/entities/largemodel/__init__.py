from core.models.entities.largemodel.gemini_lm import GeminiLMLayerAI
from core.models.entities.largemodel.openai_lm import OpenAILMLayerAI

dct_entity_factory = dict()
dct_entity_factory["openai-lm"] = OpenAILMLayerAI
dct_entity_factory["gemini-lm"] = GeminiLMLayerAI
