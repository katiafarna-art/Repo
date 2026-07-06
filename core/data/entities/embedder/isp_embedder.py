"""Modulo contenente la classe concreta per l'embedder Isp"""

from typing import Optional
from config.parameters import ISPEmbedderDefaultConfig, MAPPING_MODEL_RES_EMB
from core.data.entities.embedder.abstract_embedder import AbstractEmbedder
from core.routines.services import LAIUtilitiesManager


class ISPEmbedder(AbstractEmbedder):

    def __init__(
        self,
        token: str,
        use_case: str,
        interaction_mode: str,
        chunk_size: Optional[int] = None,
    ):

        if not chunk_size:
            chunk_size = ISPEmbedderDefaultConfig.chunk_chars

        super().__init__(chunk_size=chunk_size)
        self.token = token
        self.use_case = use_case
        self.interaction_mode = interaction_mode

    def _get_embedding(self, page: str) -> list[float]:

        layer_ai_manager = LAIUtilitiesManager(token=self.token, use_case=self.use_case, version=1)

        payload = {
            "provider": "isp",
            "user_id": "user_id",
            "use_case_id": self.use_case,
            "embedding_params": {
                "model": MAPPING_MODEL_RES_EMB["isp-embedder"],
                "texts": [page],
                "encoding_format": "float",
                "timeout": 30,
            },
        }

        is_sync = self.interaction_mode == "sync"
        response = self.call_api(
            token=self.token,
            payload=payload,
            lai_manager=layer_ai_manager,
            sync=is_sync,
        ).json()

        return response["embeddings"][0] if "error" not in response else response
