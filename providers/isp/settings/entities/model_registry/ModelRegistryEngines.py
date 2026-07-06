from enum import Enum


class ModelRegistryEngineType(str, Enum):
    """
    Enum representing the types of model registry engines.

    This class defines the available engine types for a model registry, allowing
    for easy selection and identification of the engine used in the model registry system.

    :param DETERMINED: Represents the Determined AI engine for the model registry.
    :type DETERMINED: str
    """
    DETERMINED = 'DeterminedAIEngine'