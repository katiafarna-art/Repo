from typing import ClassVar, Literal
from pydantic import BaseModel, field_validator


class GenericModelParams(BaseModel):
    temperature: float = 0.0
    max_output_tokens: int = 1000
    max_input_tokens: int = 100000
    input_token_upper_limit: ClassVar[int] = 100000  # TODO set according to model
    output_token_upper_limit: ClassVar[int] = 16384  # TODO set according to model

    @field_validator("max_output_tokens")
    @classmethod
    def validate_output_tokens(cls, value):
        if not (0 <= value <= cls.output_token_upper_limit):
            return cls.output_token_upper_limit
        return value

    @field_validator("max_input_tokens")
    @classmethod
    def validate_input_tokens(cls, value):
        if not (0 <= value <= cls.input_token_upper_limit):
            return cls.input_token_upper_limit
        return value

    @field_validator("temperature")  # noqa
    @classmethod
    def validate_temperature(cls, value):
        if not (0.0 <= value <= 1.0):
            return 0.0
        return value


class GPT5Params(BaseModel):
    max_completion_tokens: int = 1000
    reasoning_effort: Literal["minimal", "low", "medium", "high"] = "minimal"
    max_input_tokens: int = 100000
    input_token_upper_limit: ClassVar[int] = 4e5
    output_token_upper_limit: ClassVar[int] = 128e3

    @field_validator("max_completion_tokens")
    @classmethod
    def validate_output_tokens(cls, value):
        if not (0 <= value <= cls.output_token_upper_limit):
            return cls.output_token_upper_limit
        return value

    @field_validator("max_input_tokens")
    @classmethod
    def validate_input_tokens(cls, value):
        if not (0 <= value <= cls.input_token_upper_limit):
            return cls.input_token_upper_limit
        return value
    

class GPT51Params(BaseModel):
    max_completion_tokens: int = 1000
    reasoning_effort: Literal["none", "low", "medium", "high"] = "none"
    max_input_tokens: int = 100000
    input_token_upper_limit: ClassVar[int] = 4e5
    output_token_upper_limit: ClassVar[int] = 128e3

    @field_validator("max_completion_tokens")
    @classmethod
    def validate_output_tokens(cls, value):
        if not (0 <= value <= cls.output_token_upper_limit):
            return cls.output_token_upper_limit
        return value

    @field_validator("max_input_tokens")
    @classmethod
    def validate_input_tokens(cls, value):
        if not (0 <= value <= cls.input_token_upper_limit):
            return cls.input_token_upper_limit
        return value
