"""Modulo contenente la classe astratta per gli strumenti OCR offerti dal servizio"""

import logging
import time
import requests
from abc import ABC, abstractmethod
from typing import Optional, Union
from config.parameters import RetryDefaultConfig
from core.routines.entities import session, get_function_name
from core.routines.services import LAIUtilitiesManager
from core.exceptions import SmartOCRLayeraiException, SmartOCRException


from requests.packages.urllib3.exceptions import InsecureRequestWarning  # noqa

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  # noqa


class AbstractOCR(ABC):
    """
    Classe astratta utilizzata come framework per la definizione dei diversi estrattori di testo basati su servizi OCR.
    """

    model_name: Optional[str] = None
    version: Optional[str] = None

    @abstractmethod
    def extract_text_from_img(self, *args, **kwargs):
        """
        Metodo astratto relativo all'estrazione di testo da un file immagine.
        """
        pass

    def extract_text_from_pdf(self, *args, **kwargs):
        """
        Metodo relativo all'estrazione di testo da un file PDF.
        """
        pass


class AbstractCloudService:

    mimetype_to_filetype = {"application/octet-stream": "img", "application/pdf": "pdf"}
    layerai_api: str = "analyze_document?sv=1"
    layerai_file_key: str = "analyze_document_file"
    model_name: str

    def _extract_params(self, params: Optional[dict] = None) -> str:
        """
        Metodo privato che consente di specificare il nome del modello da utilizzare per svolgere l'estrazione del
        testo.

        :param params:  Dizionario contenente il nome del modello da impiegare per la chiamata ai servizi Azure Document
            Intelligence. Default a None.
        :type params: (dict, optional)

        :return: Nome del modello da utilizzare per l'estrazione.
        :rtype: str
        """
        if not params or not isinstance(params, dict):
            return self.model_name
        else:
            model_name = params.get("model_id", self.model_name)

        return model_name

    @staticmethod
    def _configure_arguments(
        languages: Optional[Union[str, list]] = None,
        page_from: Optional[int] = None,
        page_to: Optional[int] = None,
    ) -> tuple:
        """
        Metodo privato per la configurazione dei parametri relativi alle lingue e pagine del file su cui svolgere
        l'estrazione del testo.
        Nello specifico, qualora venga fornita in input una lista di lingue, solo la prima lingua viene restituita come
        configurazione.

        :param languages: lingue del file. Default a None.
        :type languages: (Union[str, list], optional)
        :param page_from: pagina del file da cui partire con l'estrazione. Default a None.
        :type page_from: (int, optional)
        :param page_to: pagina del file dove interrrompere l'estrazione. Default a None.
        :type page_to: (int, optional)

        :return: la funzione restituisce una tupla contenente la lingua del file e il range di pagine su cui viene
            svolta l'estrazione.
        :rtype: tuple
        """
        pages, locale = None, None

        if languages:
            if isinstance(languages, str):
                locale = languages
            if isinstance(languages, list):
                locale = languages[0]

        if locale and len(locale) > 2:
            locale = locale[:2]

        if page_from and isinstance(page_from, int):
            pages = f"{page_from}-"

        if page_to and isinstance(page_to, int) and page_to >= page_from:
            pages += f"{page_to}"

        return locale, pages

    def _call_api_sync(
        self, token: str, payload: dict, files: dict, lai_manager: LAIUtilitiesManager
    ):

        max_retry = RetryDefaultConfig.max_retry_sync
        sync_started = False
        response_out = ""
        sync_response = None
        exception_text = ""

        while max_retry > 0 and not sync_started:

            try:
                sync_response = session.post(
                    f"{lai_manager.dispatcher_url}srv/sync/{self.layerai_api}",
                    params=payload,
                    files=files,
                    headers={"Authorization": f"Bearer {token}"},
                    verify=False,
                )

                if sync_response.status_code == 200:
                    logging.info("Layer - Sync execution completed")
                    response_out = sync_response
                    sync_started = True

                elif sync_response.status_code == 500:
                    logging.error(
                        f"Layer - Error response sync endpoint: {sync_response.text} \n Try Again!"
                    )
                    max_retry -= 1
                    time.sleep(RetryDefaultConfig.sleep_default)

                else:
                    sync_started = True
                    raise SmartOCRLayeraiException(
                        msg=f"Method AbstractCloudService.{get_function_name()}:"
                            f"Error response sync endpoint: {sync_response.text}.",
                        status_code=sync_response.status_code
                    )

            except Exception as e:
                if isinstance(e, SmartOCRLayeraiException):
                    raise

                exception_text = str(e)
                logging.error(
                    f"Layer - Exception occurred on response sync endpoint: {exception_text} \n Try Again!"
                )
                max_retry -= 1
                time.sleep(RetryDefaultConfig.sleep_default)

        if not sync_started:
            if sync_response is None:
                raise SmartOCRException(
                    msg=f"Method AbstractCloudService.{get_function_name()}:"
                        f" ERROR: Failed to run the sync process after all retries "
                        f"due to the following exception: {exception_text}",
                )

            else:
                raise SmartOCRLayeraiException(
                    msg=f"Method AbstractCloudService.{get_function_name()}:"
                        f" ERROR: Failed to run the sync process after all retries "
                        f"due to the following error response sync endpoint {sync_response.text}",
                    status_code=sync_response.status_code
                )

        return response_out

    def _call_api_async(
        self,
        token: str,
        payload: dict,
        files: dict,
        lai_manager: LAIUtilitiesManager,
        eta: float,
    ):

        uid = lai_manager.initiate_job()
        file, mimetype = files[self.layerai_file_key][1:]
        file_name = lai_manager.upload_file(
            uid=uid, file=file, file_type=self.mimetype_to_filetype[mimetype]
        )

        payload.update(**{"uid": uid, "file_key": file_name})

        max_retry = RetryDefaultConfig.max_retry_async
        async_started = False
        async_response = None
        exception_text = ""

        while max_retry > 0 and not async_started:

            try:
                async_response = session.post(
                    f"{lai_manager.dispatcher_url}srv/async/{self.layerai_api}",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload,
                    verify=False,
                )

                if async_response.status_code == 200:
                    logging.info(f"Layer id: {uid} - Async execution started")
                    async_started = True

                elif async_response.status_code == 500:
                    logging.error(
                        f"Layer id: {uid} - Error response async endpoint: {async_response.text}\n "
                        f"Try Again!"
                    )
                    max_retry -= 1
                    time.sleep(RetryDefaultConfig.sleep_default)

                else:
                    async_started = True
                    raise SmartOCRLayeraiException(
                        msg=f"Method AbstractCloudService.{get_function_name()}: "
                            f"Layer id: {uid} - Error response async endpoint: {async_response.text}.",
                        status_code=async_response.status_code
                    )

            except Exception as e:

                if isinstance(e, SmartOCRLayeraiException):
                    raise

                logging.error(
                    f"Layer id: {uid} - Exception occurred on response async endpoint: {str(e)}\n Try Again!"
                )
                exception_text = str(e)
                max_retry -= 1
                time.sleep(RetryDefaultConfig.sleep_default)

        if not async_started:
            if async_response is None:
                raise SmartOCRException(
                    msg=f"Method AbstractCloudService.{get_function_name()}:"
                        f"Layer id: {uid} - ERROR: Failed to start the async process after all retries! "
                        f"due to the following exception: {exception_text}",
                )
            else:
                raise SmartOCRLayeraiException(
                    msg=f"Method AbstractCloudService.{get_function_name()}:"
                        f"Layer id: {uid} - ERROR: Failed to start the async process after all retries "
                        f"due to the following error response in async endpoint {async_response.text}",
                    status_code=async_response.status_code
                )

        logging.info(
            f"Layer id: {uid} - waiting {eta} s "
            f"before starting check status and retrieve pipeline"
        )
        time.sleep(eta)

        return lai_manager.check_status_and_retrieve(uid=uid)

    def call_api(
        self,
        token: str,
        payload: dict,
        files: dict,
        lai_manager: LAIUtilitiesManager,
        eta: float,
        sync: bool,
    ):

        if sync:
            return self._call_api_sync(
                token=token, payload=payload, files=files, lai_manager=lai_manager
            )
        else:
            return self._call_api_async(
                token=token,
                payload=payload,
                files=files,
                lai_manager=lai_manager,
                eta=eta,
            )
