"""Modulo contenente la classe dell'estrattore di entità tramite servizi google"""

import logging
from typing import Optional, Literal

from config.input_models.entity_extraction import EntityExtractionParams
from core.models.entities.prompt_builder import AbstractPromptBuilder
from core.pipelines.entities.entity_extraction.abstract_entity_extractor import (
    EntityExtractor,
)
from core.models.services.pdf_splitter import PdfSplitter
from core.routines.entities import get_function_name
from core.exceptions import SmartOCRInvalidOutputException


class GeminiExtractor(EntityExtractor):
    """
    Classe associata alla definizione dell'estrattore di entità tramite il servizio Google.
    Questa classe fornisce metodi per configurare e utilizzare i servizi di azure document intelligence per estrarre
    entità da contenuto testuale, immagini o PDF.

    Attributi:
    provider (str): Il fornitore del servizio di estrazione. Default a "google".
    service (str): Il servizio di estrazione utilizzato. Default a "gemini".
    model_id_def (str): L'identificativo del modello linguistico utilizzato. Default "gemini-pro".
    embedder_id_def (str): L'identificativo del modello di embedding utilizzato.
    temperature_def (Union[int, float]): Il valore di temperatura utilizzato per la generazione del testo.
    max_tokens_def (int): Il numero massimo di token utilizzato nella generazione del testo.
    """

    provider: str = "google"
    service: str = "gemini"
    

    def __init__(self, token: Optional[str] = None, use_case: Optional[str] = None):
        """
        Metodo di inizializzazione dell'oggetto estrattore. Questo metodo valorizza il token, necessario alla chiamata
        dei servizi azure, il nome del modello da utilizzare per l'estrazione e il modello per la costruzione del prompt
        tramite il super()__init__() della classe astratta *TextExtractor*.

        :param token: token contenente le credenziali necessarie per la chiamata al servizio. Default a None.
                      Se non fornito, viene generato un errore.
        :type token: (str, optional)
        """
        super().__init__(
            entity_extractor="gemini-lm",
            prompt_builder="cloud-lm-prompt",
            token=token,
            use_case=use_case,
        )

    def extract_entity_from_image(
        self,
        img: list[bytes],
        params: EntityExtractionParams,
        dct_entity: Optional[str] = None,
        language: Optional[str] = None,
        text_extracted: Optional[dict] = None,
        use_rag: bool = False,
        interaction_mode: Literal["async", "sync"] = "async",
    ) -> dict:

        prompt = self.prompt_builder_model(
            dct_entity=dct_entity,
            language=language,
            prompt_params=params.prompt_params.model_dump(exclude_none=True),
            use_case=self.use_case
        )

        output = self.entity_extractor_model(params).extract_entity_from_image(
            img=img,
            prompt=prompt,
            text_extracted=text_extracted,
            use_rag=use_rag,
            token=self.token,
            use_case=self.use_case,
            interaction_mode=interaction_mode,
        )

        if "choices" not in output.keys():
            raise SmartOCRInvalidOutputException(
                f"Method {self.__class__.__name__}.{get_function_name()}:"
                f"Output not correctly formatted"
            )

        return self._postprocess_output(
            raw_outputs=output, params=params, use_rag=use_rag
        )

    def extract_entity_from_text(
        self,
        text_extracted: dict,
        params: EntityExtractionParams,
        dct_entity: Optional[str] = None,
        use_rag: bool = False,
        language: Optional[str] = None,
        interaction_mode: Literal["sync", "async"] = "async",
    ) -> dict:
        """
        Metodo che estrae entità da contenuto testuale utilizzando un modello LM.

        Questo metodo costruisce un prompt basato sulle entità da ricercare,
        configura i parametri necessari e utilizza un modello LM per l'estrazione delle entità dal testo.
        L'output viene post-elaborato prima di essere restituito.

        :param dct_entity: Dizionario contenente le entità da estrarre.
        :type dct_entity: dict
        :param text_extracted: Contenuto testuale su cui svolgere l'estrazione di entità.
        :type text_extracted: dict
        :param use_rag: Parametro che indica se utilizzare la Retrieval-Augmented Generation (RAG). Default a False.
        :type use_rag: (bool, optional)
        :param language: Lingua utilizzata per la generazione del prompt. Default a None.
        :type language: (str, optional)
        :param params: Parametri opzionali di configurazione per l'estrazione. Default a None.
        :type params: (dict, optional)
        :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
        :type interaction_mode: (Literal['sync', 'async'], optional)

        :return: Dizionario contenente le entità estratte e le informazioni aggiuntive.
        :rtype: dict

        :raises InvalidServiceOutput: Se l'output del servizio è invalido oppure se alcune chiavi non sono presenti
            nell'output.
        """

        prompt = self.prompt_builder_model(
            dct_entity=dct_entity,
            language=language,
            prompt_params=params.prompt_params.model_dump(exclude_none=True),
            use_case=self.use_case
        )

        llm_model = self.entity_extractor_model(params)

        output = llm_model.extract_entity_from_text(
            prompt=prompt,
            text_extracted=text_extracted,
            use_rag=use_rag,
            token=self.token,
            use_case=self.use_case,
            interaction_mode=interaction_mode,
        )

        if "choices" not in output.keys():
            raise SmartOCRInvalidOutputException(
                f"Method {self.__class__.__name__}.{get_function_name()}:"
                f"Output not correctly formatted"
            )

        return self._postprocess_output(
            raw_outputs=output, params=params, use_rag=use_rag
        )

    def _extract_pdf_entities(
        self,
        pdf: bytes,
        prompt: AbstractPromptBuilder,
        pdf_extractor: PdfSplitter,
        text_extracted: Optional[dict] = None,
        use_rag: bool = False,
        params: EntityExtractionParams = None,
        interaction_mode: Literal["async", "sync"] = "async",
    ) -> dict:
        """
        Metodo che estrae entità da un PDF utilizzando un modello VLM (Vision-Language Model).

        Questo metodo suddivide il file PDF in sezioni ('chunk'), converte le pagine del file in immagini, e
        successivamente svolge l'estrazion edi entità dalle immagini.
        L'output prodotto dal modello VLM viene poi post-elaborato e restituito.

        :param pdf: File pdf su cui svolgere l'estrazione di entità.
        :type pdf: bytes
        :param prompt: Costruttore di prompt da utilizzare per la generazione delle richieste.
        :type prompt: AbstractPromptBuilder
        :param pdf_extractor: Estrattore utilizzato per processare il PDF e ottenere i chunk di contenuto.
        :type pdf_extractor: PdfExtractor
        :param text_extracted: Testo già estratto dal file PDF. Default a None.
        :type text_extracted: (dict, optional)
        :param use_rag: Indica se utilizzare la Retrieval-Augmented Generation (RAG). Default a False.
        :type use_rag: (bool, optional)
        :param params: Parametri opzionali di configurazione per l'estrazione. Default a None.
        :type params: (EntityExtractionParams, optional)

        :return: Dizionario contenente le entità estratte e le informazioni aggiuntive relative all'estrazione.
        :rtype: dict

        :raises InvalidServiceOutput: Se l'output del servizio è invalido oppure se alcune chiavi non sono presenti
            nell'output.
        """
        vlm_model = self.entity_extractor_model(params)

        splitting = True

        list_img = []
        list_pages = []

        # todo: qui dentro non faccio nulla con i chunk, tanto vale passare la lista di immagini
        while splitting:
            chunk = pdf_extractor.splitter.get_next_split(
                pdf_content=pdf, return_bytes=True
            )

            if len(chunk) == 0:
                splitting = False

            else:
                list_img.extend([elem["img"] for elem in chunk])
                list_pages.extend([elem["pag"] for elem in chunk])

        output = vlm_model.extract_entity_from_image(
            img=list_img,
            prompt=prompt,
            pages=list_pages,
            text_extracted=text_extracted,
            use_rag=use_rag,
            token=self.token,
            use_case=self.use_case,
            interaction_mode=interaction_mode,
        )

        if "choices" not in output.keys():
            raise SmartOCRInvalidOutputException(
                f"Method {self.__class__.__name__}.{get_function_name()}:"
                f"Output not correctly formatted"
            )

        return self._postprocess_output(
            raw_outputs=output,
            params=params,
            use_rag=use_rag,
            use_image_params=True,
            language=prompt.messages["language"]
        )

    def extract_entity_from_pdf(
        self,
        pdf: bytes,
        params: EntityExtractionParams,
        dct_entity: Optional[str] = None,
        language: Optional[str] = None,
        page_from: int = 1,
        page_to: Optional[int] = None,
        text_extracted: Optional[dict] = None,
        use_rag: bool = False,
        interaction_mode: Literal["async", "sync"] = "async",
    ) -> dict:
        """
        Metodo che estrae entità da un file PDF utilizzando un modello LM.

        Questo metodo costruisce un prompt basato sulle entità da ricercare,
        configura i parametri necessari e utilizza un modello LM per l'estrazione delle entità dal PDF.
        L'output viene post-elaborato prima di essere restituito.


        :param pdf: File PDF su cui svolgere l'estrazione di entità.
        :type pdf: bytes
        :param dct_entity: Dizionario contenente le entità da estrarre.
        :type dct_entity: dict
        :param language: Lingua utilizzata per la generazione del prompt. Default a None.
        :type language: (str, optional)
        :param page_from: Numero della pagina del file pdf da cui iniziare l'estrazione. Default a 1.
        :type page_from: (int, optional)
        :param page_to: Numero della pagina in cui interrompere l'estrazione. Default a None (estrazione prosegue fino
            alla fine del file).
        :type page_to: (int, optional)
        :param text_extracted: Testo estratto dal file PDF. Default a None.
        :type text_extracted: (dict, optional)
        :param use_rag: Parametro che indica se utilizzare la Retrieval-Augmented Generation (RAG). Default a False.
        :type use_rag: (bool, optional)
        :param params: Parametri opzionali di configurazione per l'estrazione. Default a None.
        :type params: (EntityExtractionParams, optional)

        :return: Dizionario contenente le entità estratte e le informazioni aggiuntive.
        :rtype: dict
        """

        logging.debug("Extracting text from a PDF")
        prompt = self.prompt_builder_model(
            dct_entity=dct_entity,
            language=language,
            prompt_params=params.prompt_params.model_dump(exclude_none=True),
            use_case=self.use_case
        )

        pdf_ext = PdfSplitter(params=params.image_params.model_dump(exclude_none=True),
                              page_from=page_from,
                              page_to=page_to)

        # params = params + far qualcosa per restituire i params del PdfExtractor

        return self._extract_pdf_entities(
            pdf=pdf,
            prompt=prompt,
            pdf_extractor=pdf_ext,
            text_extracted=text_extracted,
            use_rag=use_rag,
            params=params,
            interaction_mode=interaction_mode,
        )
