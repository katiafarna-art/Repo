"""Classe astratta relativa agli EntityExtractor"""

import logging
from typing import Optional
from abc import abstractmethod, ABC

from config.input_models.entity_extraction import EntityExtractionParams
from core.models.entities.prompt_builder import dct_prompt_factory
from core.models.entities.largemodel import dct_entity_factory


class EntityExtractor(ABC):
    """
    Classe astratta relativa alla definizione degli estrattori di entitò
    """

    provider: str
    service: str

    def __init__(
        self,
        entity_extractor: str,
        prompt_builder: str,
        token: Optional[str] = None,
        use_case: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """
        Metodo di inizializzazione dell'estrattore astratto. Questo metodo valorizza gli attributi di classe associati
        al nome del modello LM da impiegare per l'estrazione, il tipo di prompt da costruire per la chiamata al modello
        e il token contenente le credenziali (indirizzo api e chiave associata) necessarie a svolgere la chiamata al
        modello.

        :param entity_extractor: modello LM per l'estrazione di entitò.
        :type entity_extractor: str
        :param prompt_builder: prompt builder per la definizione del prompt al modello LM.
        :type prompt_builder: str
        :param token: token contenente le credenziali necessarie per la chiamata al modello LM.
        :type token: (dict, optional)
        """
        self.entity_extractor_model = dct_entity_factory.get(entity_extractor)
        self.prompt_builder_model = dct_prompt_factory.get(prompt_builder)
        self.token = token
        self.use_case = use_case

    @staticmethod
    def _reorder_content(entity_extracted: dict):

        data = entity_extracted.get("entity_extracted", {})
        # Riordino se le chiavi sono del tipo "pag_"
        if isinstance(data, dict) and all(
            isinstance(k, str) and k.startswith("pag_") and k[4:].isdigit()
            for k in data
        ):
            entity_extracted["entity_extracted"] = {
                k: dict(v) if isinstance(v, dict) else v
                for k, v in sorted(data.items(), key=lambda item: int(item[0].split("_")[1]))
            }
                                  
        return entity_extracted

    def _postprocess_output(
            self,
            raw_outputs: dict,
            params: Optional[EntityExtractionParams] = None,
            language: Optional[str] = None,
            use_rag: bool = False,
            use_image_params: bool = False
    ) -> dict:
        """
        Metodo privato che esegue la post-elaborazione dell'output generato dall'estrazione delle entità.

        :param raw_outputs: Dizionario contenente l'output dell'estrazione.
        :type raw_outputs: dict
        :param params: Parametri opzionali di configurazione utilizzati durante l'estrazione. Default a None.
        :type params: (EntityExtractionParams, optional)
        :param language: Lingua del contenuto da cui sono state estratte le entità. Default a None.
        :type language: (str, optional)
        :param use_rag: Indica se utilizzare la Retrieval-Augmented Generation (RAG). Default a False.
        :type use_rag: (bool, optional)
        :param use_image_params: Indica se includere i parametri relativi alle immagini nell'output. Default a False.
        :type use_image_params: (bool, optional)

        :return: Dizionario contenente l'output post-elaborato, con le entità estratte e le informazioni aggiuntive.
            Nello specifico, il dizionario contiene le entità estratte sotto la chiave 'entity_extracted' e le
            informazioni aggiuntive relative all'estrazione sotto la chiave 'extra'.
        :rtype: dict
        """
        logging.debug(f"Postprocessing raw {self.service} output")

        metadata = {"ee_params": params.model_params.model_dump()}
        metadata["ee_params"]["model_id"] = params.original_model

        if use_rag:
            metadata["ee_params"]["embedder"] = params.embedder_id

        if language:
            metadata["ee_params"]["language"] = language

        if use_image_params:
            metadata["image_params"] = params.image_params.model_dump()
            metadata["image_params"]["greyscale"] = (
            "True" if params.image_params.greyscale is True else "False"
        )
        else:
            metadata["image_params"] = {}

        #TODO: fix quando ho template custom e alla fine ottengo più risposte perchè non entra tutto nel payload
        #TODO: fix quando ho template custom e prompt json e ottengo più risposte
      
        content = [item['message']['content'] for item in raw_outputs["choices"]] if len(raw_outputs["choices"]) > 1 \
            else raw_outputs["choices"][0]['message']['content']

        entity_extracted = {
            "entity_extracted": content,
            "extra": {
                "request_info": {
                    "provider": self.provider,
                    "service": self.service,
                },
                "execution_params": metadata,
                "total_tokens": raw_outputs["usage"]["total_tokens"],
            },
        }

        return self._reorder_content(entity_extracted=entity_extracted)

    @abstractmethod
    def extract_entity_from_image(self, img: bytes, params: EntityExtractionParams, *args, **kwargs) -> dict:
        """
        Metodo astratto per l'estrazione di entità da immagine.
        """
        pass

    @abstractmethod
    def extract_entity_from_text(self, img: bytes, params: EntityExtractionParams, *args, **kwargs) -> dict:
        """
        Metodo astratto per l'estrazione di entità da contenuto testuale.
        """
        pass

    @abstractmethod
    def extract_entity_from_pdf(self, pdf: bytes, params: EntityExtractionParams, *args, **kwargs) -> dict:
        """
        Metodo astratto per l'estrazione di entità da pdf.
        """
        pass
