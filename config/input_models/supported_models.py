from config.input_models.model_parameters import *
from config.input_models.default_model_params import *


supported_models = {

    "gpt-5.1":{
        "model_id": "gpt-5.1-2025-11-13",
        "config_class": GPT51Params,
        "default_config": GPT51Config,
        "img_tokens_per_tile": 140,
        "img_base_tokens": 70
    },

    "gpt-5": {
        "model_id": "gpt-5-2025-08-07",
        "config_class": GPT5Params,
        "default_config": GPT5Config,
        "img_tokens_per_tile": 140,
        "img_base_tokens": 70
    },
    "gpt-5-mini": {
        "model_id": "gpt-5-mini-2025-08-07",
        "config_class": GPT5Params,
        "default_config": GPT5Config,
        "img_tokens_per_tile": 140,
        "img_base_tokens": 70
    },
    "gpt-5-nano": {
        "model_id": "gpt-5-nano-2025-08-07",
        "config_class": GPT5Params,
        "default_config": GPT5Config,
        "img_tokens_per_tile": 140,
        "img_base_tokens": 70
    },
    "gpt-4.1-2025-04-14": {
        "model_id": "gpt-4.1-2025-04-14",
        "config_class": GenericModelParams,
        "default_config": GPT_4_1_Config,
        "img_tokens_per_tile": 170,
        "img_base_tokens": 85
    },
    "gpt-4o": {
        "model_id": "gpt-4o-2024-08-06",
        "config_class": GenericModelParams,
        "default_config": OpenaiDefaultConfig,
        "img_tokens_per_tile": 170,
        "img_base_tokens": 85
    },
    "gpt-4o-2024-11-20": {
        "model_id": "gpt-4o-2024-11-20",
        "config_class": GenericModelParams,
        "default_config": OpenaiDefaultConfig,
        "img_tokens_per_tile": 170,
        "img_base_tokens": 85
    },
    "gpt-4o-2024-08-06": {
        "model_id": "gpt-4o-2024-08-06",
        "config_class": GenericModelParams,
        "default_config": OpenaiDefaultConfig,
        "img_tokens_per_tile": 170,
        "img_base_tokens": 85
    },
    "gpt-4o-mini": {
        "model_id": "gpt-4o-mini-2024-07-18",
        "config_class": GenericModelParams,
        "default_config": OpenaiDefaultConfig,
        "img_tokens_per_tile": 5667,
        "img_base_tokens": 2833
    },

    "gemini-flash": {
        "model_id": "gemini-2.0-flash-001",
        "config_class": GenericModelParams,
        "default_config": GoogleDefaultConfig},
    "gemini-2.5-pro": {
        "model_id": "gemini-2.5-pro",
        "config_class": GenericModelParams,
        "default_config": Gemini_2_5_Config},
    "gemini-2.5-flash": {
        "model_id": "gemini-2.5-flash",
        "config_class": GenericModelParams,
        "default_config": Gemini_2_5_Config},
    "gemini-2.0-flash-001": {
        "model_id": "gemini-2.0-flash-001",
        "config_class": GenericModelParams,
        "default_config": GoogleGeminiFlashConfig},
    "gemini-2.0-flash-lite-001": {
        "model_id": "gemini-2.0-flash-lite-001",
        "config_class": GenericModelParams,
        "default_config": GoogleGeminiFlashConfig},
}
