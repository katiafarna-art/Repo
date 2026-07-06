import contextlib
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Union

DETERMINED_AVAILABLE = False

with contextlib.suppress(ImportError):
    from determined.experimental import Determined
    from determined.experimental.client import DownloadMode
    DETERMINED_AVAILABLE = True

from bdlpkg.providers.isp.settings.entities.model_registry.ModelRegistrySettings import (
    DeterminedAIMRSettings, ModelRegistrySettings)

MRHC_TYPE = List[Dict[str,Union[str,List[Dict[str,str]]]]]

class ModelRegistryEngine(ABC):
    """This Abstract class define the interface of Model Registry Engines

    This class defines the required interface for any model registry engine. It includes
    methods for retrieving all models and a specific model from a model registry, 
    which must be implemented by any subclass.
    
    :param mrs: Settings for the model registry.
    :type mrs: ModelRegistrySettings
    """

    @abstractmethod
    def __init__(self, mrs: ModelRegistrySettings) -> None:
        pass

    @abstractmethod
    def get_all_models(self) -> MRHC_TYPE:
        """Get all model available in the model registry that are visible for this account. 

        Returns:
            Dict[str,List[str]]: a dict with {name of the model:a list of model versions}
        """

        pass

    @abstractmethod
    def get_model(self, model_name: str, model_version: str) -> str:
        """Get the model

        :param model_name: model name
        :type model_name: str
        :param model_version: version of the model
        :type model_version: str
        :param model_registry_istance_name: istance of model registry, defaults to None
        :type model_registry_istance_name: Optional[str], optional
        :return: the path of the downloaded model
        :rtype: str
        """
        pass


class DeterminedAIEngine(ModelRegistryEngine):
    """
    Model registry engine for managing models in Determined AI.

    This class provides methods to interact with the Determined AI model registry,
    allowing retrieval of model information and versions. It uses the settings provided
    by `DeterminedAIMRSettings` and establishes a connection to the Determined AI cluster.

    :param mrs: The settings for the Determined AI model registry.
    :type mrs: DeterminedAIMRSettings
    :raises AttributeError: If the settings provided are not of type `DeterminedAIMRSettings` or if the model version is missing.
    """
    def __init__(self, mrs: DeterminedAIMRSettings) -> None:
        self.mrs = mrs
        if type(mrs) is not DeterminedAIMRSettings:
            raise AttributeError("Model Registry is not of type DeterminedAI")

        if not DETERMINED_AVAILABLE:
            import determined

        master = os.getenv("DET_MASTER", str(self.mrs.endpoint_url))
        user = os.getenv("DET_USER", self.mrs.access_name)
        password = os.getenv("DET_PASS", self.mrs.access_key.get_secret_value())
        cert_path = self.mrs.verify_ssl_cert or None
        no_verify = (not self.mrs.verify_ssl_cert)

        # Determined è già lui un singleton
        self.det_client = Determined(master=master,
                                     user=user,
                                     password=password,
                                     cert_path=cert_path, noverify=no_verify)

    def get_all_models(self) -> MRHC_TYPE:
        """
        Retrieve all models from the Determined AI model registry.

        :return: A list of models, each containing model name and versions.
        :rtype: MRHC_TYPE
        """
        # TODO:
        # 1. divisione per workspace {"workspace": [{"modello":[{versione:uuid},....]},{}} -> anagrafica! 
        return [
            {"model_name":_m.name,
             "versions":[{"version_name":_v.name, "model_version":str(_v.checkpoint.uuid)} for _v in _m.list_versions()]} 
            for _m in self.det_client.list_models()
        ]

    def get_model(self, model_name: str, model_version: str) -> str:
        """
        Retrieve a specific version of a model from Determined AI.

        :param model_name: The name of the model to retrieve.
        :type model_name: str
        :param model_version: The specific version of the model to retrieve.
        :type model_version: str
        :return: The path to the downloaded model checkpoint.
        :rtype: str
        :raises AttributeError: If the model version is not provided.
        :raises Warning: If the specified model version checkpoint is not found.
        """
        # Non posso usare la stringa con il nome di versione del modello perché può essere modificata... Devo tenere l'ID del checkpoint
        if model_version is None:
            raise AttributeError("Manca la versione del modello!")

        if model_version not in (
            v.checkpoint.uuid
            for v in self.det_client.get_model(model_name).list_versions()
        ):
            logging.warning(f"Model {model_name} has not checkpoint {model_version}.")

        checkpoint = self.det_client.get_checkpoint(model_version)
        return checkpoint.download(path=os.path.join(os.environ["MY_HOME"],'checkpoints',model_version),mode=DownloadMode.DIRECT)
