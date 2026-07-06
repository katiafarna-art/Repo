from requests.packages.urllib3.exceptions import InsecureRequestWarning  # noqa
from typing import Optional, Literal
from pydantic import BaseModel, model_validator
from config.input_models.supported_models import supported_models
from config.parameters.default_description_params import DEFAULT_MODEL


class ImageDescriptionParams(BaseModel):
    service: Literal["openai", "gemini"]
    model: Optional[str] = None
    language: Optional[Literal["en", "it"]] = None
    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None
    system_message: Optional[str] = None
    user_message: Optional[str] = None
    generation_params: Optional[BaseModel] = None

    @model_validator(mode="after")
    def check_model_id(self) -> None:
        self.model = self.validate_model(self.model, self.service)

        return self

    @model_validator(mode="before")
    def check_model(cls, data) -> dict:
        model_data = dict()

        model_data["service"] = data.get("service")
        model_data["model"] = data.get("model")
        model_data["language"] = data.get("language")
        model_data["system_message"] = data.get("system_message")
        model_data["user_message"] = data.get("user_message")

        model_data["language"] = cls.validate_language(data.get("language"),
                                                       data.get("system_message"),
                                                       data.get("user_message"))
        model_id = data.get("model")
        if model_id:
            model_id = model_id.value
        else:
            model_id = DEFAULT_MODEL.get(data.get("service"))

        config_class = supported_models.get(model_id)["config_class"]
        default_config = supported_models.get(model_id)["default_config"]

        model_params = {key: data.get(key) or getattr(default_config, key)
                        for key in config_class.model_fields.keys()
                        if ((key in data or key in default_config.__annotations__) and key != "max_input_tokens")}

        model_data["generation_params"] = config_class(**model_params)

        return model_data

    @staticmethod
    def validate_model(model: str, service: Literal["openai", "gemini"]) -> str:
        if not model:
            model = DEFAULT_MODEL.get(service)

        if model not in supported_models:
            raise ValueError(f"Model '{model}' is not supported")

        model = supported_models[model]["model_id"]

        accepted_prefix = "gpt" if service == "openai" else "gemini"

        if not model.startswith(accepted_prefix):
            raise ValueError(f"Model '{model}' is not an accepted {accepted_prefix} model")

        return model

    @staticmethod
    def validate_language(
            language: Optional[str],
            system_message: Optional[str],
            user_message: Optional[str]) -> Optional[str]:
        if not ((system_message and user_message) or language):
            raise ValueError("Language must be either 'en' or 'it' if either system_massage or user_message are not"
                                  " provided")
        return language
