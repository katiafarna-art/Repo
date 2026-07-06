from threading import Lock
from typing import Any, Dict, List, Optional, Tuple, Union

from bdlpkg.providers.isp.model_registry.services.ModelRegistryEngines import (
    MRHC_TYPE, DeterminedAIEngine, ModelRegistryEngine)
from bdlpkg.providers.isp.settings.entities.model_registry.ModelRegistrySettings import (
    DeterminedAIMRSettings, ModelRegistrySettings)
from bdlpkg.providers.isp.settings.entities.model_registry.ModelRegistryEngines import ModelRegistryEngineType
from bdlpkg.providers.isp.settings.services.isp_config import (
    get_datasource_settings, get_settings)
from bdlpkg.utils.metaclasses.singleton import Singleton


# Crea un dizionario di mapping tra type ModelRegistryEngine e type Enum
MAPPING_TYPE = {
    DeterminedAIEngine: ModelRegistryEngineType.DETERMINED
}

class ModelRegistryManager(metaclass=Singleton):
    """
    Singleton class to abstract the managment of model registries.

    This class acts as a manager for various model registry instances, initializing and managing 
    resources associated with different model registries. It provides methods to retrieve specific 
    models, all models, and the engine type for a given model registry instance.

    :ivar _resources: A dictionary storing locks and model registry engine instances for each resource name.
    :vartype _resources: Dict[str, Tuple[Lock, ModelRegistryEngine]]
    """
    _resources: Dict[str, Tuple[Lock, ModelRegistryEngine]] = {}

    def __init__(self) -> None:
        self._init_resources()

    def _init_resources(self) -> None:
        """
        Initialize the resources associate to the model registries storing them in memory
        """
        _model_registrys_settings = get_settings()["model_registry"]
        if len(self._resources) == 0:
            for mrs_name, mrs in _model_registrys_settings.items():
                # if determined
                if type(mrs) is DeterminedAIMRSettings:
                    self._resources[mrs_name] = (Lock(),
                                                 DeterminedAIEngine(mrs))

    def _get_resource(
        self,
        model_registry_istance_name: Optional[str] = None
    ) -> Tuple[Lock, ModelRegistryEngine]:    #type:ignore
        """
        Retrieve the resource associated to the name passed as parameter and the related lock semaphore.

        :param model_registry_istance_name: the name of the model registry istance that must pair with the name on the secret. Default: the first alphabetically, defaults to None
        :type model_registry_istance_name: Optional[str], optional
        :return: a tuple containing the model_registry resource and the associated lock semaphore
        :rtype: Tuple[Lock, Any]
        """
        #double check presenza configurazione del model_registry
        mri: ModelRegistrySettings = get_datasource_settings(
            "model_registry", None, model_registry_istance_name)
        return self._resources[mri.resource_name]

    def get_model(self,
                  model_name: str,
                  version: str,
                  model_registry_istance_name: Optional[str] = None) -> str:
        """Retrieve a specific model from the model registry.

        :param model_name: The name of the model to retrieve.
        :type model_name: str
        :param version: The version of the model to retrieve.
        :type version: str
        :param model_registry_istance_name: Optional instance name of the model registry to query. Defaults to None.
        :type model_registry_istance_name: str, optional
        :return: The model information as a string.
        :rtype: str
        """
        _lock, _resource = self._get_resource(model_registry_istance_name)
        with _lock:    # type:ignore
            return _resource.get_model(model_name=model_name,
                                       model_version=version)

    def get_all_models(
        self,
        model_registry_istance_name: Optional[str] = None
    ) -> MRHC_TYPE:
        """Retrieve all models from the model registry.

        :param model_registry_istance_name: Optional instance name of the model registry to query. Defaults to None.
        :type model_registry_istance_name: str, optional
        :return: A collection of all models in the model registry.
        :rtype: MRHC_TYPE
        """
        _lock, _resource = self._get_resource(model_registry_istance_name)
        with _lock:    # type:ignore
            return _resource.get_all_models()
        
    def get_engine_type(self,
                        model_registry_istance_name: Optional[str] = None) -> ModelRegistryEngineType:
        """Retrieve the type of engine used by the model registry.

        :param model_registry_istance_name: Optional instance name of the model registry to query. Defaults to None.
        :type model_registry_istance_name: str, optional
        :return: The engine type used by the model registry.
        :rtype: ModelRegistryEngineType
        :raises: Exception if no mapping is found for the engine type.
        """
        _lock, _resource = self._get_resource(model_registry_istance_name)
        with _lock:    # type:ignore
            engine_type = type(_resource)
            try:
                return MAPPING_TYPE[engine_type]
            except:
                raise(f"No mapping found for type {MAPPING_TYPE[engine_type]}")


def get_model_registry_healthcheck(
    model_registry_istance_name: Optional[str] = None) -> dict:
    """
    Performe the healthcheck on the model registry to check its status, 
    giving back the list of models for each model_registry

    :param model_registry_istance_name: the name of the model registry istance that must pair with the name on the secret. Default: the first alphabetically, defaults to None
    :type model_registry_istance_name: Optional[str], optional
    :return: a dictionary having all the models in the model registry, with specification of versions and related checkpoints
    :rtype: dict
    """
    result = {}
    try:
        mrm = ModelRegistryManager()
        result["models"] = mrm.get_all_models(model_registry_istance_name)
    except Exception as e:
        result["error"] = str(e)

    return result
