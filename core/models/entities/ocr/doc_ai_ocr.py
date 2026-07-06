"""Modulo contenente la classe concreta per lo strumento ocr DocumentAI (Google, VertexAI)"""

import requests
from typing import Optional, Union, Literal
from config.parameters import DocumentAIOCRDefaultConfig, ETA_PAGE_LAI
from core.data.services import get_pdf_len
from core.models.entities.ocr.abstract_ocr import AbstractOCR, AbstractCloudService
from core.routines.entities import check_file_type
from core.routines.services import LAIUtilitiesManager

from requests.packages.urllib3.exceptions import InsecureRequestWarning  # noqa

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  # noqa


class DocumentAIOCR(AbstractOCR, AbstractCloudService):
    """
    Classe relativa all'estrazione di testo utilizzando i servizi OCR di Azure document intelligence.

    Descrizione: Questa classe consente l'estrazione di testo a partire da file immagine o pdf utilizzando uno degli
    engine OCR forniti da Azure Document Intelligence.
    Nello specifico, un oggetto DocumentIntelligenceClient (relativo alla classe definita internamente ai servizi
    azure.ai) viene definito utilizzando le credenziali di accesso alla risorsa e i nomi relativi al servizio e provider
    utilizzati.
    Vengono poi configurati eventuali ulteriori parametri, quali la lingua e, nel caso di estrazione di entità da file
    pdf, il range di pagine su cui svolgere l'estrazione.
    L'estrazione viene poi svolta richiamando il medoto *begin_analyze_document* appartenente alla classe
    DocumentIntelligenceClient della libreria azure.ai. Il metodo *result* appartenente alla classe azure LROPoller è
    poi utilizzato per restituire il risultato dell'estrazione.
    """

    model_name: str = DocumentAIOCRDefaultConfig.model_id

    def extract_text_from_img(
        self,
        token: str,
        img: bytes,
        use_case: str,
        params: Optional[dict] = None,
        interaction_mode: Literal["async", "sync"] = "async",
    ) -> Union[str, requests.Response]:
        """
        Metodo per l'estrazione del testo da file immagine utilizzando i servizi OCR di DocumentAI tramite layerai.

        :param token: token contenente le informazioni necessarie per svolgere la chiamata al modello OCR.
        :type token: str
        :param img: immagine su cui svolgere l'estrazione.
        :type img: bytes
        :param use_case: use case di riferimento assegnato tramite layerai
        :type use_case: str
        :param params:  Dizionario contenente il nome del modello da impiegare per la chiamata ai servizi Azure Document
            Intelligence. Default a None.
        :type params: (dict, optional)
        :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
        :type: Literal["async", "sync"]
        """
        model_name = self._extract_params(params=params)
        layer_ai_manager = LAIUtilitiesManager(token=token, use_case=use_case)

        payload = {
            "provider": "google",
            "use_case_id": use_case,
            "processor": model_name,
            "mime_type": "image/png",
        }

        files = {
            "analyze_document_file": (
                f"uploaded_file{check_file_type(file_content=img)}",
                img,
                "application/octet-stream",
            )
        }

        is_sync = interaction_mode == "sync"

        return self.call_api(
            token=token,
            payload=payload,
            files=files,
            lai_manager=layer_ai_manager,
            eta=ETA_PAGE_LAI,
            sync=is_sync,
        ).json()

    def extract_text_from_pdf(
        self,
        token: str,
        pdf: bytes,
        page_from: int,
        page_to: int,
        use_case: str,
        params: Optional[dict] = None,
        interaction_mode: Literal["async", "sync"] = "async",
    ) -> Union[str, requests.Response]:
        """
        Metodo per l'estrazione del testo da file pdf utilizzando i servizi OCR di DocumentAI tramite layerai.

        :param token: token contenente le informazioni necessarie per svolgere la chiamata al modello OCR.
        :type token: str
        :param pdf: immagine su cui svolgere l'estrazione.
        :type pdf: bytes
        :param page_from: pagina del file da cui partire con l'estrazione. Default a None.
        :type page_from: (int, optional)
        :param page_to: pagina del file dove interrrompere l'estrazione. Default a None.
        :type page_to: (int, optional)
        :param use_case: use case di riferimento assegnato tramite layerai
        :type use_case: str
        :param params:  Dizionario contenente il nome del modello da impiegare per la chiamata ai servizi Azure Document
            Intelligence. Default a None.
        :type params: (dict, optional)
        :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
        :type: Literal["async", "sync"]
        """
        model_name = self._extract_params(params=params)
        layer_ai_manager = LAIUtilitiesManager(token=token, use_case=use_case)

        payload = {
            "provider": "google",
            "use_case_id": use_case,
            "processor": model_name,
            "mime_type": "application/pdf",
        }

        files = {"analyze_document_file": ("uploaded_file.pdf", pdf, "application/pdf")}
        eta = ETA_PAGE_LAI * (
            (page_to - page_from + 1) if page_to else get_pdf_len(pdf)
        )
        is_sync = interaction_mode == "sync"

        return self.call_api(
            token=token,
            payload=payload,
            files=files,
            lai_manager=layer_ai_manager,
            eta=eta,
            sync=is_sync,
        ).json()
