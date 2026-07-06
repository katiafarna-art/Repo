from config.input_models.entity_extraction import AzureParams, GeminiParams
from config.input_models.image_description import ImageDescriptionParams

service_to_ee_params = {
    "openai": AzureParams,
    "gemini": GeminiParams
}
