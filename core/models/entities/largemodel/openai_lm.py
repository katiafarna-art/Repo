"""Modulo contenente la classe concreta LM di Openai (Azure)"""

import json
import logging
from typing import Optional, Literal

from config.input_models.entity_extraction import EntityExtractionParams
from core.models.entities.prompt_builder import CloudPromptBuilder
from core.models.entities.largemodel.abstract_lm import AbstractLM
from core.routines.services import LAIUtilitiesManager, build_json_schema


class OpenAILMLayerAI(AbstractLM):
    """
    Classe relativa all'estrazione di entità utilizzando i servizi LM OpenAI.

    Descrizione: Questa classe consente di svolgere l'estrazione di entità a partire da contenuto testuale e da file
    immagine utilizzando i servizi LM forniti da OpenAI.
    """

    def __init__(self, params: EntityExtractionParams) -> None:
        """
        Metodo di inizilizzazione della classe OpenAILM. Tale metodo richiama l'init della classe AbstractLM
        specificando il nome del provider e del servizio OpenAI.
        """
        super().__init__(provider="azure", service="openai", params=params)

    def extract_entity_from_image(
        self,
        img: bytes,
        prompt: CloudPromptBuilder,
        pages: Optional[list] = None,
        text_extracted: Optional[dict] = None,
        use_rag: bool = False,
        token: Optional[str] = None,
        use_case: Optional[str] = None,
        interaction_mode: Literal["async", "sync"] = "async",
    ) -> dict:
        """
        Metodo per l'estrazione di entità da file immagine utilizzando i servizi LM di OpenAI. Nello specifico,
        vengono impostati l'indirizzo endpoint relativo al modello da richiamare e la chiave associata. Successivamente,
        vengono valorizzati i parametri relativi all'estrazione utilizzando quanto fornito dal'utente oppure i valori di
        default. Qualora assiame alle immagini venga fornito in input anche il testo estratto, tali immagini vengono
        correttamente associate alle diverse pagine di *text_extracted*. Se assieme al testo estratto, viene anche
        specificato il parametro use_rag = True, prima di procedere alla mappatura, vengono selezionate unicamente le
        immagini/pagine dove si stima sia più possibile trovare l'entità.
        Vengono poi definiti i payloads dei prompt per la chiamata al servizio utilizzando le immagini (e se specificato
        il testo).
        Per ogni payload viene svolta l'estrazione di entità tramite chiamata all'api associata al modello.
        I risultati relativi ai singoli payloads vengono poi agglomerati e restituiti come un unico dizionario.

        :params img: Lista di immagini su cui svolgere l'estrazione di entità.
        :type img: bytes
        :param prompt: oggetto prompt necessario alla definizione dell'input al servizio LM.
        :type prompt: OpenAIEEPromptBuilder
        :params pages: Lista delle pagine su cui svolgere l'estrazione di entità
        :type pages: list
        :param text_extracted: Testo estratto relativo alle immagini in input. Default a None.
        :type text_extracted: (dict, optional)
        :param use_rag: Parametro booleano associato all'impiego di un embedder. Default a False.
        :type use_rag: (bool, optional)
        :param token: token contenente le informazioni necessarie per svolgere la chimata al modello LM.
        :type token: (str, optional)
        :param use_case: use case di riferimento assegnato tramite layerai
        :type use_case: str
        :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
        :type interaction_mode: (Literal['sync', 'async'], optional)

        :return: la funzione restituisce il risultato dell'estrazione in un dizionario.
        :rtype: dict
        """
        is_structured = False
        emb_params = {
            "token": token,
            "use_case": use_case,
            "int_mode": interaction_mode,
        }

        payloads = self._get_vlm_payloads(
            img=img,
            pages=pages,
            text_extracted=text_extracted,
            use_rag=use_rag,
            prompt=prompt,
            emb_params=emb_params,
        )

        layer_ai_manager = LAIUtilitiesManager(token=token, use_case=use_case)
        response_format = (
            None
            if prompt.messages["response_format"] == ""
            else prompt.messages["response_format"]
        )

        if isinstance(response_format, dict):
            is_structured = True
            response_format = json.dumps(build_json_schema(response_format))

        responses = []

        for payload in payloads:

            azure_payload = payload["messages"]["messages"]

            other_payload = {
                "provider": self.provider,
                "use_case_id": use_case,
                "generation_params": {
                    "stream": False,
                    "messages": azure_payload,
                    "model": self.config_class.model_id,
                    "timeout": 900,
                    "response_format": response_format,  # "json_object",
                    "include_usage": True,
                    **self.config_class.model_params.model_dump(exclude_none=True)
                },
            }

            is_sync = interaction_mode == "sync"
            response = self.call_api(
                token=token,
                payload=other_payload,
                lai_manager=layer_ai_manager,
                sync=is_sync,
            ).json()

            if "error" in response.keys() and response["error"] is not None:
                return response

            responses.append({**response, **{"pages": payload["pages"]}})

        template = "custom" if prompt.dict_entity is None else "base"
        output = self._postprocess_chunk_layerai(
            response_list=responses,
            response_format=response_format if not is_structured else "json_object",
            template=template,
            use_case=use_case
        )

        return output

    def extract_entity_from_text(
        self,
        prompt: CloudPromptBuilder,
        text_extracted: dict,
        use_rag: bool = False,
        token: Optional[str] = None,
        use_case: str = None,
        interaction_mode: Literal["async", "sync"] = "async",
    ) -> dict:
        """
        Metodo per l'estrazione di entità da contenuto testuale utilizzando i servizi LM di OpenAI. Nello specifico,
        vengono impostati l'indirizzo endpoint relativo al modello da richiamare e la chiave associata. Successivamente,
        vengono valorizzati i parametri relativi all'estrazione utilizzando quanto fornito dal'utente oppure i valori di
        default. Qualora venga specificato il parametro use_rag = True, vengono selezionate unicamente le
        pagine relative al contenuto testuale dove si stima sia più possibile trovare l'entità.
        Vengono poi definiti i payloads dei prompt per la chiamata al servizio utilizzando il testo in input.
        Per ogni payload viene svolta l'estrazione di entità tramite chiamata all'api associata al modello.
        I risultati relativi ai singoli payloads vengono poi agglomerati e restituiti come un unico dizionario.

        :param prompt: oggetto prompt necessario alla definizione dell'input al servizio LM.
        :type prompt: OpenAIEEPromptBuilder
        :param text_extracted: Contenuto testuale su cui svolgere l'estrazione di entità.
        :type text_extracted: dict
        :param use_rag: Parametro booleano associato all'impiego di un embedder. Default a False.
        :type use_rag: (bool, optional)
        :param token: token contenente le informazioni necessarie per svolgere la chimata al modello LM.
        :type token: (str, optional)
        :param use_case: use case di riferimento assegnato tramite layerai
        :type use_case: str
        :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
        :type interaction_mode: (Literal['sync', 'async'], optional)

        :return: la funzione restituisce il risultato dell'estrazione in un dizionario.
        :rtype: dict
        """
        is_structured = False
        emb_params = {
            "token": token,
            "use_case": use_case,
            "int_mode": interaction_mode,
        }

        payloads = self._get_lm_payloads(
            text_extracted=text_extracted,
            use_rag=use_rag,
            prompt=prompt,
            emb_params=emb_params
        )
        logging.info(f"Num. of payload generated: {len(payloads)}")

        layer_ai_manager = LAIUtilitiesManager(token=token, use_case=use_case)
        responses = []
        response_format = (
            None
            if prompt.messages["response_format"] == ""
            else prompt.messages["response_format"]
        )

        if isinstance(response_format, dict):
            is_structured = True
            response_format = json.dumps(build_json_schema(response_format))

        for payload in payloads:

            azure_payload = payload["messages"]["messages"]

            other_payload = {
                "provider": self.provider,
                "use_case_id": use_case,
                "generation_params": {
                    "stream": False,
                    "messages": azure_payload,
                    "model": self.config_class.model_id,
                    "timeout": 900,
                    "response_format": response_format,
                    "include_usage": True,
                    **self.config_class.model_params.model_dump(exclude_none=True)
                },
            }

            is_sync = interaction_mode == "sync"
            response = self.call_api(
                token=token,
                payload=other_payload,
                lai_manager=layer_ai_manager,
                sync=is_sync,
            ).json()

            if "error" in response.keys() and response["error"] is not None:
                return response

            responses.append({**response, **{"pages": payload["pages"]}})

        template = "custom" if prompt.dict_entity is None else "base"
        return self._postprocess_chunk_layerai(
            response_list=responses,
            response_format=response_format if not is_structured else "json_object",
            template=template,
            use_case=use_case
        )
