import logging
import time
from typing import Literal, Optional

from fastapi import UploadFile
from requests import Response

from config.parameters import RetryDefaultConfig
from core.exceptions import SmartOCRLayeraiException, SmartOCRException
from core.models.entities.image_desc_payload.payload_generator import PayloadGenerator
from core.models.entities.image_desc_payload.prompt_builder import PromptGenerator
from core.routines.entities import session, get_function_name
from core.routines.services import LAIUtilitiesManager


class LayerAIGenerator(object):
    """Classe che gestisce l'interazione della pipeline di image description con il LayerAI

    La classe prima di tutto si occupa di settare i parametri necessari per l'interazione con il LayerAI tramite
    l':py:class:`utilities manager <core.routines.services.LAIUtilitiesManager>`. Inoltre, espone un metodo, `call_api`
    che si occupa di effettuare la chiamata al LayerAI, che può avvenire sia in modalità sincrona che asincrona

    :param token: token cifrato per la chiamata necessario per poter effettuare la chiamata ai modelli utilizzati,
        in quanto chiave di autenticazione al LayerAI.
    :type token: str
    :param use_case: stringa identificativa dello use case, necessaria per accedere ai servizi del LayerAI.
    :type use_case: str
    """
    def __init__(self, token: str, use_case: str):
        self.token = token
        self.use_case = use_case
        self.lai_manager = LAIUtilitiesManager(token=token, use_case=use_case)

    def _call_api_sync(self, payload: dict) -> Response:
        """Metodo che si occupa di effettuare la chiamata al LayerAI in modalità sincrona.

        Il metodo prova a contattare l'endpoint di sync del LayerAI. Dopodiché a seconda del codice di risposta:

        * se 200, il metodo ritorna la risposta ottenuta dal LayerAI;
        * se 500, allora la chiamata viene ritentata, fino ad un numero di volte definito in
          `RetryDefaultConfig.max_retry_sync`;
        * In caso di altri codici di errore, viene sollevata un'eccezione di tipo
          :py:class:`SmartOCRLayeraiException <core.exceptions.SmartOCRLayeraiException>`.

        :param payload: dizionario contenente il payload da inviare al LayerAI
        :type payload: dict

        :returns: risposta ottenuta dal LayerAI
        :rtype: Response

        :raises SmartOCRLayeraiException: in caso di errori di connessione o di errori causati dal motore
        """

        max_retry = RetryDefaultConfig.max_retry_sync
        sync_started = False
        response_out = ""
        sync_response = None
        exception_text = ""

        while max_retry > 0 and not sync_started:

            try:
                sync_response = session.post(
                    url=f"{self.lai_manager.dispatcher_url}srv/sync/generate?sv=1",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json=payload,
                    stream=False,
                    verify=False,
                )

                if sync_response.status_code == 200:
                    logging.debug("Sync execution completed")
                    response_out = sync_response
                    sync_started = True

                elif sync_response.status_code == 500:
                    logging.error(
                        f"Error response sync endpoint: {sync_response.text} \n Try Again!"
                    )
                    max_retry -= 1
                    time.sleep(RetryDefaultConfig.sleep_default)

                else:
                    sync_started = True
                    raise SmartOCRLayeraiException(
                        msg=f"Method {get_function_name()}:"
                        f"Error response sync endpoint: {sync_response.text}.",
                        status_code=sync_response.status_code
                    )

            except Exception as e:

                if isinstance(e, SmartOCRLayeraiException):
                    raise

                exception_text = str(e)
                logging.error(
                    f"Exception occurred on response sync endpoint: {exception_text} \n Try Again!"
                )
                max_retry -= 1
                time.sleep(RetryDefaultConfig.sleep_default)

        if not sync_started:
            if sync_response is None:
                raise SmartOCRException(
                    msg=f"Method {get_function_name()}:"
                        f" ERROR: Failed to run the sync process after all retries due "
                        f"to the following exception: {exception_text}"
                )

            else:
                raise SmartOCRLayeraiException(
                    msg=f"Method {get_function_name()}:"
                        f" ERROR: Failed to run the sync process after all retries "
                        f"due to the following error response from sync endpoint: {sync_response.text}",
                    status_code=sync_response.status_code
                )

        return response_out

    def _call_api_async(self, payload: dict) -> Response:
        """Metodo che si occupa di effettuare la chiamata al LayerAI in modalità asincrona.

        Al fine di rendere la chiamata asincrona, il metodo prima di tutto genera un codice identificativo del job,
        chiamato uid. Tale codice verrà poi inserito all'interno del payload.
        Dopodiché viene contattato l'endpoint di async del LayerAI. A seconda del codice di risposta:

        * se 200, il metodo ritorna la risposta ottenuta dal LayerAI;
        * se 500, allora la chiamata viene ritentata, fino ad un numero di volte definito in
          `RetryDefaultConfig.max_retry_sync`;
        * In caso di altri codici di errore, viene sollevata un'eccezione di tipo
          :py:class:`SmartOCRLayeraiException <core.exceptions.SmartOCRLayeraiException>`.

        :param payload: dizionario contenente il payload da inviare al LayerAI
        :type payload: dict

        :returns: risposta ottenuta dal LayerAI
        :rtype: Response

        :raises SmartOCRLayeraiException: in caso di errori di connessione o di errori causati dal motore
        """

        uid = self.lai_manager.initiate_job()
        payload["uid"] = uid

        max_retry = RetryDefaultConfig.max_retry_async
        async_started = False
        async_response = None
        exception_text = ""

        while max_retry > 0 and not async_started:

            try:
                async_response = session.post(
                    url=f"{self.lai_manager.dispatcher_url}srv/async/generate?sv=1",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json=payload,
                    stream=False,
                    verify=False,
                )

                if async_response.status_code == 200:
                    logging.debug("Async execution started")
                    async_started = True

                elif async_response.status_code == 500:
                    logging.error(
                        f"Error response async endpoint: {async_response.text} \n Try Again!"
                    )
                    max_retry -= 1
                    time.sleep(RetryDefaultConfig.sleep_default)

                else:
                    async_started = True
                    raise SmartOCRLayeraiException(
                        msg=f"Method {get_function_name()}:"
                            f"Error response async endpoint: {async_response.text}.",
                        status_code=async_response.status_code
                    )

            except Exception as e:
                if isinstance(e, SmartOCRLayeraiException):
                    raise

                exception_text = str(e)
                logging.error(
                    f"Exception occurred on response async endpoint: {exception_text} \n Try Again!"
                )
                max_retry -= 1
                time.sleep(RetryDefaultConfig.sleep_default)

        if not async_started:
            if async_response is None:
                raise SmartOCRException(
                    msg=f"Method {get_function_name()}:"
                        f"ERROR: Failed to start the async process after all retries "
                        f"due to the following exception: {exception_text}",
                )
            else:
                raise SmartOCRLayeraiException(
                    msg=f"Method {get_function_name()}:"
                        f"ERROR: Failed to start the async process after all retries "
                        f"due to the following error response in async endpoint {async_response.text}",
                    status_code=async_response.status_code
                )

        return self.lai_manager.check_status_and_retrieve(uid=uid)  # noqa

    def call_api(self, payload: dict, sync: bool) -> Response:
        """Metodo che si occupa di effettuare la chiamata al LayerAI, sia in modalità sincrona che asincrona.

        :param payload: dizionario contenente il payload da inviare al LayerAI
        :type payload: dict
        :param sync: booleano che indica se la chiamata deve essere effettuata in modalità sincrona o asincrona
        :type sync: bool

        :returns: risposta ottenuta dal LayerAI
        :rtype: Response

        :raises SmartOCRLayeraiException: in caso di errori di connessione o di errori causati dal motore
        """

        if sync:
            return self._call_api_sync(
                payload=payload
            )

        return self._call_api_async(
            payload=payload
        )


class ImageDescriptor(object):
    """Classe che si occupa di orchestrare l'intero processo di image description.

    :param prompt_generator: oggetto che si occupa di generare il prompt da passare al modello
    :type prompt_generator: PromptGenerator
    :param lai_generator: oggetto che si occupa di gestire l'interazione con il LayerAI
    :type lai_generator: LayerAIGenerator
    :param payload_generator: oggetto che si occupa di generare il payload da passare al LayerAI
    :type payload_generator: PayloadGenerator
    """
    def __init__(self,
                 prompt_generator: PromptGenerator,
                 lai_generator: LayerAIGenerator,
                 payload_generator: PayloadGenerator):
        self.prompt_generator = prompt_generator
        self.lai_generator = lai_generator
        self.payload_generator = payload_generator

    def describe_single_image(self, img: str, interaction_mode: str) -> Response:
        """Metodo che si occupa di descrivere una singola immagine.

        Il metodo esegue i seguenti step in sequenza:

        1. Genera il messaggio da passare al modello tramite il
           :py:class:`PromptGenerator <core.models.entities.image_desc_payload.prompt_builder.PromptGenerator>`.
        2. Genera il payload da passare al LayerAI tramite il
              :py:class:`PayloadGenerator <core.models.entities.image_desc_payload.payload_generator.PayloadGenerator>`.
        3. Effettua la chiamata al LayerAI tramite il
           :py:class:`LayerAIGenerator <core.routines.services.LAIUtilitiesManager>`, in modalità sincrona o asincrona
           a seconda del parametro `interaction_mode`.

        :param img: immagine da descrivere, codificata in base64
        :type img: str
        :param interaction_mode: modalità di interazione con il LayerAI, può essere "sync" o "async"
        :type interaction_mode: Literal["async", "sync"]

        :returns: risposta ottenuta dal LayerAI
        :rtype: Response

        :raises SmartOCRLayeraiException: in caso di errori di connessione o di errori causati dal motore
        """
        messages = self.prompt_generator.generate_messages(img)
        payload = self.payload_generator.generate_payload(messages)

        response = self.lai_generator.call_api(
            payload=payload,
            sync=interaction_mode == "sync")

        return response

    def describe_images(self,
                        files: list[str],
                        interaction_mode: Literal["async", "sync"] = "async",
                        execution_params: Optional[dict] = None
                 ) -> dict:
        """Metodo che si occupa di descrivere una lista di immagini.

        Il metodo itera sulla lista di immagini, e per ciascuna immagine chiama il metodo `describe_single_image`.
        I risultati ottenuti per ciascuna immagine sono raccolti in un dizionario, che viene poi post processato in modo
        tale da avere un formato dell'output pulito. In particolare, la risposta è un dizionario avente le seguenti
        chiavi:

        * `descriptions`: dizionario contenente le descrizioni delle immagini, con chiavi del tipo
          "image_{NUM_IMMAGINE}": descrizione
        * `extra`: dizionario contenente i parametri di esecuzione, come la temperatura e il numero di token di output

        :param files: lista di immagini da descrivere
        :type files: list[UploadFile]
        :param interaction_mode: modalità di interazione con il LayerAI, può essere "sync" o "async"
        :type interaction_mode: Literal["async", "sync"]
        :param execution_params: dizionario contenente i parametri di esecuzione, come la temperatura e il numero di
            token di output
        :type execution_params: dict, optional

        :returns: dizionario contenente le descrizioni delle immagini e i parametri di esecuzione
        :rtype: dict
        """
        output = []
        for file in files:

            response = self.describe_single_image(
                img=file,
                interaction_mode=interaction_mode).json()

            output.append(response.get("texts", [])[0])

        content = {f"image_{i + 1}": desc for i, desc in enumerate(output)}

        descriptions = {
            "descriptions": content,
            "extra": execution_params
        }

        return descriptions
