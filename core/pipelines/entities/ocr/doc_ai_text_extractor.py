"""Modulo contenente la classe dell'estrattore di testo tramite servizi Google DocumentAI"""

from typing import Optional, Literal
import logging
from config.parameters import DocumentAIOCRDefaultConfig
from core.data.entities.utils import is_valid_params
from core.pipelines.entities.ocr.abstract_text_extractor import TextExtractor
from core.routines.entities import get_function_name
from core.exceptions import SmartOCRException


class DocAITextExtractor(TextExtractor):
    """
    Classe associata alla definizione dell'estrattore di testo tramite un OCR di Google DocumentAI.

    Questa classe fornisce metodi per configurare e utilizzare modelli OCR di azure document intelligence per estrarre
    testo da immagini o PDF.
    In particolare, permette la configurazione dei parametri delle immagini e del modello OCR utilizzato, e offre
    funzionalità di estrazione.

    Attributi:
        provider (str): Il fornitore del servizio OCR. Default a "Google".
        service (str): Il servizio OCR utilizzato. Default a "VertexAI".
        model_ocr (str): Il modello OCR utilizzato. Default a "document-ai".
    """

    provider: str = "google"
    service: str = "VertexAI"
    model_ocr: str = "document-ai"

    def __init__(self, token: dict, use_case: Optional[str] = None):
        """
        Metodo di inizializzazione dell'oggetto estrattore. Questo metodo valorizza il token, necessario alla chiamata
        dei servizi azure document intelligence, tramite il super()__init__() della classe astratta *TextExtractor*.

        :param token: token contenente le credenziali necessarie per la chiamata al servizio. Default a None.
        :type token: (dict, optional)
        :param use_case: stringa contenente l'use case di riferimento
        :type use_case: (dict, optional)
        """
        if not token:
            raise SmartOCRException(f"Method {self.__class__.__name__}.{get_function_name()}: "
                                    f"the field 'token' cannot be None.")

        super().__init__(model_ocr=self.model_ocr, token=token, use_case=use_case)

    def _configure(self, params: dict) -> dict:
        """
        Metodo privato che configura i parametri di estrazione utilizzando i valori di default e/o i valori forniti
        dall'utente.

        :param params: Dizionario contenente i parametri di configurazione forniti dall'utente.
        :type params: dict

        :return: Dizionario contenente la configurazione completa per l'estrazione con tutti i parametri correttamente
            validati e valorizzati.
        :rtype: dict
        """
        logging.debug("Extracting request configuration")
        dct_configuration = {
            "image_params": dict(),
            "ocr_params": {"model_id": DocumentAIOCRDefaultConfig.model_id},
        }

        if is_valid_params(params):
            dct_configuration["ocr_params"] = self._extract_ocr_params(params)

        return dct_configuration

    @staticmethod
    def _extract_ocr_params(params: dict):
        """
        Metodo statico che estrae il nome del modello azure. Qualora il volare non sia
        specificato tramite il parametro in input al metodo o nel caso in cui il nome specificato non sia tra le opzioni
        disponibili, viene utilizzato il valore di default associato al corrispettivo attributo di classe.

        :param params: Dizionario contenente i parametri di configurazione dell'estrazione.
        :type params: dict

        :return: Dizionario contenente i parametri valorizzati di configurazione per l'OCR.
        :rtype: dict
        """
        logging.debug("Extracting OCR configuration")

        model_id = (
            params["args"]
            .get("model", dict())
            .get("model_id", DocumentAIOCRDefaultConfig.model_id)
        )

        return {"model_id": model_id}

    @staticmethod
    def _get_page_text(full_text: str, page: dict):
        start_index = page["layout"]["text_anchor"]["text_segments"][0].get(
            "start_index", 0
        )
        if not start_index:
            start_index = 0
        end_index = page["layout"]["text_anchor"]["text_segments"][0]["end_index"]
        page_text = full_text[int(start_index) : int(end_index)]
        return page_text

    def _postprocess_output_image(
        self, raw_output: dict, params: Optional[dict] = None  # noqa
    ) -> dict:
        """
        Metodo privato che esegue la post-elaborazione dell'output generato dall'OCR per l'estrazione da immagine.

        :param raw_output: Risultato dell'estrazione OCR.
        :type raw_output: dict
        :param params: Parametri di configurazione utilizzati durante l'estrazione.
        :type params: dict
        :return: Dizionario contenente l'output post-elaborato. Nello specifico, il dizionario contiene il testo
            estratto sotto la chiave 'texts' e le informazioni aggiuntive relative all'estrazione sotto la chiave
            'extra'.
        :rtype: dict
        """
        logging.debug("Postprocessing raw OCR output")

        if not params:
            params = dict()

        keep_keys = {"styles", "pages", "paragraphs", "tables", "languages"}
        others = {
            key: value
            for key, value in raw_output["result"].items()
            if key in keep_keys
        }

        return {
            "texts": raw_output["texts"],
            "extra": {
                "request_info": {
                    "provider": self.provider,
                    "service": self.service,
                    "model": params["ocr_params"]["model_id"],
                    "model_version": "",
                },
                "execution_params": params,
                f"{params['ocr_params']['model_id']}_add_on": others,
            },
        }

    def _postprocess_output_pdf(
        self, raw_output: dict, params: Optional[dict] = None  # noqa
    ) -> dict:
        """
        Metodo privato che esegue la post-elaborazione dell'output generato dall'OCR per l'estrazione da file PDF.

        :param raw_output: Risultato dell'estrazione OCR.
        :type raw_output: dict
        :param params: Parametri di configurazione utilizzati durante l'estrazione.
        :type params: dict

        :return: Dizionario contenente l'output post-elaborato. Nello specifico, il dizionario contiene il testo
            estratto sotto la chiave 'texts' e le informazioni aggiuntive relative all'estrazione sotto la chiave
            'extra'.
        :rtype: dict
        """
        logging.debug("Postprocessing raw OCR output")

        texts = dict()
        full_text = raw_output["content"]
        raw_output = raw_output["info"]

        if not params:
            params = dict()

        for page in raw_output["pages"]:
            texts[f"pag_{page['page_number']}"] = self._get_page_text(
                full_text=full_text, page=page
            )

        keep_keys = {"styles", "pages", "paragraphs", "tables", "languages"}
        others = {key: value for key, value in raw_output.items() if key in keep_keys}

        return {
            "texts": texts,
            "extra": {
                "request_info": {
                    "provider": self.provider,
                    "service": self.service,
                    "model": params["ocr_params"]["model_id"],
                    "model_version": "",
                },
                "execution_params": params,
                f"{params['ocr_params']['model_id']}_add_on": others,
            },
        }

    def extract_text_from_image(
        self,  # noqa
        img: bytes,
        params: Optional[dict] = None,
        num_page: int = 1,
        interaction_mode: Literal["async", "sync"] = "async",
        *args,
        **kwargs,
    ) -> dict:
        """
        Metodo che estrae il testo da un'immagine tramite OCR. Nello specifico, vengono dapprima configurati i
        parametri relativi all'estrazione. Successivamente viene svolta l'estrazione
        del testo dall'immagine. Il risultato dell'estrazione viene post-elaborato e restituito dal metodo.

        :param img: Immagine su cui svolgere l'estrazione del testo.
        :type img: bytes
        :param params: Parametri di configurazione opzionali per l'estrazione. Default a None.
        :type params: (dict, optional)
        :param num_page: Numero di pagina associato all'immagine. Default a 1.
        :type num_page: (int, optional)
        :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
        :type: Literal["async", "sync"]
        :return: Dizionario contenente il testo estratto e le informazioni aggiuntive relative all'estrazione.
        :rtype: dict
        """
        logging.debug("Extracting text from an image")

        # 1. From PIL to b64
        params = self._configure(params)

        # 2. Call to Azure
        result = self.ocr_model().extract_text_from_img(
            token=self.token,
            img=img,
            params=params["ocr_params"],
            use_case=self.use_case,
            interaction_mode=interaction_mode,
        )

        texts = dict()
        texts[f"pag_{num_page}"] = result["content"]
        others = {key: value for key, value in result["info"].items()}

        return self._postprocess_output_image(
            raw_output={"texts": texts, "result": others}, params=params
        )

    def extract_text_from_pdf(
        self,  # noqa
        pdf: bytes,
        params: Optional[dict] = None,
        page_from: int = 1,
        page_to: Optional[int] = None,
        interaction_mode: Literal["async", "sync"] = "async",
        *args,
        **kwargs,
    ) -> dict:
        """
        Metodo che estrae il testo da un PDF tramite OCR. Nello specifico, vengono dapprima configurati i
        parametri relativi all'estrazione. Successivamente viene svolta l'estrazione del testo dal PDF.

        :param pdf: PDF su cui svolgere l'estrazione testo.
        :type pdf: bytes
        :param params: Parametri di configurazione opzionali per l'estrazione. Default a None.
        :type params: (dict, optional)
        :param page_from: Numero della pagina del file pdf da cui iniziare lo splitting. Default a 1.
        :type page_from: (int, optional)
        :param page_to: Numero della pagina in cui interrompere lo splitting. Default a None (splitting prosegue fino
            alla fine del file).
        :type page_to: (int, optional)
        :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
        :type: Literal["async", "sync"]
        :return: Dizionario contenente il testo estratto e le informazioni aggiuntive.
        :rtype: dict
        """
        logging.debug("Extracting text from a PDF")

        params = self._configure(params)

        result = self.ocr_model().extract_text_from_pdf(
            token=self.token,
            pdf=pdf,
            params=params["ocr_params"],
            page_from=page_from,
            page_to=page_to,
            use_case=self.use_case,
            interaction_mode=interaction_mode,
        )

        return self._postprocess_output_pdf(raw_output=result, params=params)
