from core.models.entities.image_desc_payload.prompt_builder import OpenAIPromptGenerator, GeminiPromptGenerator

prompt_generators = {
    "openai": OpenAIPromptGenerator,
    "gemini": GeminiPromptGenerator
}
