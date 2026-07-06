from core.models.entities.prompt_builder.abstract_prompt_builder import (
    AbstractPromptBuilder,
)
from core.models.entities.prompt_builder.cloud_prompt_builder import CloudPromptBuilder

dct_prompt_factory = {
    "cloud-lm-prompt": CloudPromptBuilder
}
