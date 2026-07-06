from core.exceptions import SmartOCRInputError

def _build_and_validate_expected_schema(schema: dict) -> dict:
    """
    Builds the expected schema for the response format.

    Args:
        schema (dict): The schema to be used for building the expected schema.

    Returns:
        dict: The expected schema.
    """
    if not isinstance(schema, dict):
        raise SmartOCRInputError(f"Expected schema to be a dictionary, got {type(schema)} instead.")

    if not all(isinstance(key, str) for key in schema.keys()):
        raise SmartOCRInputError("All keys in the schema must be strings.")

    if not all(isinstance(value, dict) for value in schema.values()):
        raise SmartOCRInputError("All values in the schema must be dictionaries.")

    return {
        "type": "object",
        "properties": schema,
        "required": list(schema.keys()),
        "additionalProperties": False,
    }

def build_json_schema(
    schema: dict, name: str = "default_schema", strict: bool = True
) -> dict:
    """
    Builds a JSON schema with the given properties.

    Args:
        schema (dict): The properties of the schema.
        name (str): The name of the schema.
        strict (bool): Whether the schema is strict or not.

    Returns:
        dict: The JSON schema.
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": strict,
            "schema": _build_and_validate_expected_schema(schema),
        },
    }