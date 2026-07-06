"""Script contenente i parametri di configurazione di default per gli LLM adibiti a entity extraction"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class EEConfig:
    temperature: int
    max_output_tokens: int
    max_completion_tokens: int
    reasoning_effort: str
    embedder_id: str
    max_input_tokens: int
    input_token_upper_limit: int
    output_token_upper_limit: int


@dataclass
class GPT5Config:
    max_completion_tokens: int = 1000
    reasoning_effort: str = "minimal"
    max_input_tokens: int = 100000
    input_token_upper_limit: int = 4e5
    output_token_upper_limit: int = 128e3

@dataclass
class GPT51Config:
    max_completion_tokens: int = 1000
    reasoning_effort: str = "none"
    max_input_tokens: int = 100000
    input_token_upper_limit: int = 4e5
    output_token_upper_limit: int = 128e3

@dataclass
class OpenaiDefaultConfig(EEConfig):
    temperature: int = 0
    max_output_tokens: int = 1000
    max_completion_tokens: int = 1000
    reasoning_effort: str = "minimal"
    embedder_id: str = "ada-embedder"
    max_input_tokens: int = 100000
    input_token_upper_limit: int = 100000
    output_token_upper_limit: int = 16384


@dataclass
class GoogleDefaultConfig(EEConfig):
    temperature: int = 0
    max_output_tokens: int = 1000
    max_completion_tokens: int = 1000
    reasoning_effort: str = "minimal"
    embedder_id: str = "ada-embedder"
    max_input_tokens: int = 100000
    input_token_upper_limit: int = 1048576
    output_token_upper_limit: int = 8192


@dataclass
class Gemini_2_5_Config(EEConfig):
    """
    This config includes pro and flash versions since they share it.

    Source:
    * https://ai.google.dev/gemini-api/docs/models#gemini-2.5-pro
    * https://ai.google.dev/gemini-api/docs/models#gemini-2.5-flash
    """
    temperature: int = 0
    max_output_tokens: int = 1000
    max_completion_tokens: int = 1000
    reasoning_effort: str = "minimal"
    embedder_id: str = "ada-embedder"
    max_input_tokens: int = 100000
    input_token_upper_limit: int = 1048576
    output_token_upper_limit: int = 65536


@dataclass
class GoogleGeminiFlashConfig(EEConfig):
    temperature: int = 0
    max_output_tokens: int = 1000
    max_completion_tokens: int = 1000
    reasoning_effort: str = "minimal"
    embedder_id: str = "ada-embedder"
    max_input_tokens: int = 100000
    input_token_upper_limit: int = 1048576
    output_token_upper_limit: int = 8192


@dataclass
class GPT_4_1_Config(EEConfig):
    temperature: int = 0
    max_output_tokens: int = 1000
    max_completion_tokens: int = 1000
    reasoning_effort: str = "minimal"
    embedder_id: str = "ada-embedder"
    max_input_tokens: int = 100000
    input_token_upper_limit: int = 1047576
    output_token_upper_limit: int = 32768
