from fastapi import UploadFile
from typing import Optional, Literal

from core.routines.services import track_and_save_results
from config.parameters import DEFAULT_DESCRIPTION_EXPECTED_ETA
from core.models.entities.image_desc_payload import prompt_generators
from config.input_models.image_description import ImageDescriptionParams
from core.models.entities.image_desc_payload.payload_generator import PayloadGenerator
from core.pipelines.entities.image_description.image_descriptor import LayerAIGenerator, ImageDescriptor


def get_images_description(
        img: list[UploadFile],
        service: str,
        model: str,
        token: str,
        generation_params: ImageDescriptionParams,
        language: Optional[Literal["en", "it"]] = None,
        system_message: Optional[str] = None,
        user_message: Optional[str] = None,
        use_case: Optional[str] = None,
        interaction_mode: Literal["async", "sync"] = "async",
        job_id: Optional[str] = None,
        expected_eta: int = DEFAULT_DESCRIPTION_EXPECTED_ETA,
) -> dict:
    """
    Funzione che gestisce la pipeline di descrizione di immagini utilizzando un visual language model.

    La funzione si occupa di definire gli oggetti necessari per l'esecuzione del task. In particolare:

    * prompt_generator: responsabile di definire il prompt (system + user message)
    * lai_generator: oggetto che consente l'interazione con il LayerAI
    * payload_generator: oggetto che definisce il payload complessivo da passare al LayerAI
    * descriptor: oggetto che mette in fila i diversi oggetti e le diverse operazioni necessarie all'esecuzione del task

    Nel caso in cui sia specificato il codice identificativo univoco associato all'esecuzione della pipeline, attraverso
    il parametro 'job_id', i risultati dell'estrazione sono salvati localmente in un file json. Se la scrittura del json
    va a buon fine, viene creato localmente anche un file .success.
    Se vengono riscontrati errori durante l'esecuzione dell'estrazione, tali errori sono salvati in un
    dizionario, e, se il parametro 'job_id' è specificato, anche localmente in un file .failure.

    :param img: lista di files di immagini da descrivere.
    :type img: list[UploadFile]
    :param service: Nome della famiglia di modelli utilizzata. Valori ammessi: "openai" e "gemini".
    :type service: str
    :param model: nome del modello VLM da utilizzare per l'estrazione delle descrizioni
    :type model: str
    :param language:  Lingua del testo e dell'entità definita. Questo parametro è obbligatorio se non
        vengono specificati dei prompt custom (sia system message che user message).
    :type language: ([Literal["en", "it"]], optional)
    :param generation_params: Oggetto contenente le valorizzazioni relative ai vari parametri per lo svolgimento
            dell'estrazione di entità, come `temperature` e `max_output_token`.
    :type generation_params: (ImageDescriptionParams, optional)
    :param system_message: messaggio di sistema del prompt usato. Il messaggio di sistema è
          quello che consente di definire il ruolo ed il tono del modello.
    :type system_message: (str, optional)
    :param user_message: prompt vero e proprio passato al modello. Tale messaggio consente di
          definire il task o, più in generale, cosa ci si aspetta dal modello.
    :type user_message: (str, optional)
    :param token: token cifrato per la chiamata necessario per poter effettuare la chiamata ai modelli utilizzati,
         in quanto chiave di autenticazione (e.g. Open AI).
    :type token: (str, optional)
    :param use_case: stringa identificativa dello use case, necessaria per accedere ai servizi del LayerAI.
    :type use_case: (str, optional)
    :param interaction_mode: Stringa indicante il metodo di interazione con gli endpoint del layerai ('sync' per
            interagire in modalità sincrona, 'async' per interagire in modalità asincrona). Default ad 'async'
    :type interaction_mode: (Literal["sync", "async"], optional)
    :param job_id: Stringa identificativa del processo associato all'esecuzione asincrona della pipeline. Utilizzata per
        localizzare l'output dell'esecuzione in un secondo momento (tramite endpoint di retrieve)
    :type job_id: (str, optional)
    :param expected_eta: Stima del tempo (espresso in secondi) necessario all'esecuzione della pipeline.
    :type expected_eta: (float, optional)

    :return: Nel caso l'esecuzione vada a buon fine, la funzione restituisce un dizionario contenente i risultati,
        ovvero un dizionario contenente le descrizioni delle immagini e ulteriori metadati. Nel caso siano
        riscontrati errori viene restituito un dizionario contenente l'errore riscontrato.

    """

    prompt_generator = prompt_generators[service](system_message=system_message,
                                                  user_message=user_message,
                                                  language=language)
    lai_generator = LayerAIGenerator(token=token, use_case=use_case)
    payload_generator = PayloadGenerator(generation_params=generation_params,
                                         use_case_id=use_case,
                                         provider=prompt_generator.provider,
                                         model=model)
    descriptor = ImageDescriptor(prompt_generator=prompt_generator,
                                 lai_generator=lai_generator,
                                 payload_generator=payload_generator)

    execution_params = {
        "request_info": {
            "provider": prompt_generator.provider,
            "service": service,
        },
        "execution_params": {
            "model_id": model,
            **generation_params.model_dump(exclude_unset=True)
        }
    }

    descriptor_kwargs = {
        "files": img,
        "interaction_mode": interaction_mode,
        "execution_params": execution_params,
    }

    return track_and_save_results(callable_func=descriptor.describe_images,
                                  func_kwargs=descriptor_kwargs,
                                  job_id=job_id,
                                  expected_eta=expected_eta
                                  )
