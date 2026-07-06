import logging
from bdlpkg.providers.isp.settings.services.isp_config import get_settings


def get_model_registry_healthcheck() -> dict:
    """Healthcheck for all model registry istances

    :return: a dict with the result of connection tests for all model registry istances
    :rtype: dict
    """
    _result = {}
    _settings = get_settings()["model_registry"]
    
    for _mr in _settings:
        logging.info(f"Executing healthcheck for {_mr} of type model_registry")
        from bdlpkg.providers.isp.model_registry.services.ModelRegistryManager import get_model_registry_healthcheck
        _result[_mr] = get_model_registry_healthcheck(_mr)
    
    return _result
