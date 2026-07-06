from typing import Optional, ClassVar
from pydantic import BaseModel, Field, model_validator, field_validator
from core.exceptions import SmartOCRInputError
from config.parameters import SplitterDefaultConfig
from config.input_models.supported_models import supported_models


class PromptParams(BaseModel):
    input: Optional[str] = None
    system_message_vlm: Optional[str] = None
    system_message_llm: Optional[str] = None
    response_format: Optional[dict | str] = None

class ImageParams(BaseModel):
    dpi: Optional[int] = SplitterDefaultConfig.dpi
    greyscale: Optional[bool] = SplitterDefaultConfig.greyscale

    @field_validator("greyscale", mode="before")  # noqa
    @classmethod
    def validate_greyscale(cls, value):
        if not value:
            return SplitterDefaultConfig.greyscale

        if value not in {"True", "False"}:
            raise SmartOCRInputError(
                "Error in extracting image configuration: if specified, 'greyscale' must be of str-type and either "
                "'True' or 'False'"
            )

        greyscale_bool = True if value.lower() == "true" else False
        return greyscale_bool


class EntityExtractionParams(BaseModel):
    use_case: str = None
    model_id: str
    original_model: str
    embedder_id: Optional[str] = "ada-embedder"
    model_params: Optional[BaseModel] = None
    prompt_params: PromptParams = Field(default_factory=PromptParams)
    image_params: ImageParams = Field(default_factory=ImageParams)
    default_model: ClassVar[str] = ""

    @model_validator(mode="before")  # noqa
    def preprocess(cls, data):
        """
        Runs BEFORE any fields are validated.
        Allows rewriting/removing fields, including 'args'.
        """

        if not isinstance(data, dict):
            return data

        # TODO validazione?
        # Extract model configuration from args["model"], if present
        args = data.pop("args", {})

        # TODO validare che model_id sia tra i modelli di supported_models?

        model_dict = args.get("model", {})
        model_id = model_dict.get("model_id", cls.default_model)

        config_class = supported_models.get(model_id)["config_class"]
        default_config = supported_models.get(model_id)["default_config"]

        model_params = {key: model_dict.get(key) or getattr(default_config, key)
                        for key in config_class.model_fields.keys()
                        if (key in model_dict or key in default_config.__annotations__)}
        data["model_params"] = config_class(**model_params)
        data["original_model"] = model_id
        data["model_id"] = supported_models.get(model_id)["model_id"]

        if "embedder" in args:
            if "embedder_id" in args["embedder"]:
                data["embedder_id"] = args["embedder"]["embedder_id"]

        if "prompt" in args:
            prompt_dict = args["prompt"]
            data["prompt_params"] = PromptParams(**prompt_dict)

        if "image" in args:
            image_dict = args["image"]
            data["image_params"] = ImageParams(**image_dict)

        return data


class AzureParams(EntityExtractionParams):
    default_model = "gpt-5.1"


class GeminiParams(EntityExtractionParams):
    default_model = "gemini-2.5-flash"
